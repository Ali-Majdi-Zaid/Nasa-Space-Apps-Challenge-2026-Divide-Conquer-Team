"""End-to-end run: agent -> matching -> validation -> report and dashboard."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np

from . import astronomy, benchmark as bm, campaign, campaign_map, cleaning as cl, derived, planner
from .agent import Check, RelationshipAgent
from .io import Dataset, load
from .matching import MIN_DATA_SHARE, Matcher
from .presets import PRESETS
from .schema import DIMENSIONS
from .sensitivity import stability
from .store import SqliteStore

MAX_RUNS = 8   # agent runs per pipeline call, each with its own tool-call budget
TOP_K = 10
N_RUNS = 300
MIN_KM = 500.0
_DASHBOARD = Path(__file__).resolve().parent.parent / "dashboard"


def _clean(values, digits=4):
    """JSON-safe list: NaN -> None, rounded."""
    return [None if (v is None or np.isnan(v)) else round(float(v), digits) for v in values]


_SOURCE_TAGS = [("NASA POWER", "NASA POWER climatology"), ("Diviner", "LRO Diviner"), ("MOLA", "MGS MOLA topography"),
                ("terrain", "Terrain tiles"), ("InSight", "InSight TWINS/PS (PDS)"), ("REMS", "MSL REMS (PDS)"),
                ("MEDA", "Mars 2020 MEDA (PDS)"), ("Phoenix", "Phoenix MET (PDS)"), ("Viking", "Viking Lander 1 (PDS)")]


def data_sources(ds: Dataset) -> list[str]:
    """Short names of the datasets behind the columns, from their provenance strings."""
    text = " ".join(c.version for c in list(ds.earth_cols.values()) + list(ds.target_cols.values())).lower()
    return [name for key, name in _SOURCE_TAGS if key.lower() in text]


def build_payload(ds: Dataset, agent_result, matcher: Matcher, runs=None, cleaning=None, start=None) -> dict:
    """Everything the dashboard needs, including the data to re-score live."""
    profiles = {tid: matcher.profile(tid) for tid in ds.targets.index}
    used_cols = sorted({p.earth_col for prof in profiles.values() for p in prof if p.factor > 0})
    known_name = dict(zip(ds.known["cell_id"], ds.known["name"]))
    known_body = dict(zip(ds.known["cell_id"], ds.known["body"])) if "body" in ds.known.columns else {}

    rels = []
    for r in agent_result.relationships:
        d = r.to_dict()
        t = ds.target_cols.get(r.target_col)
        d["target_label"] = t.label if t else r.target_col
        d["earth_label"] = ds.earth_cols[r.earth_col].label if r.earth_col in ds.earth_cols else "No counterpart"
        d["target_source"] = t.source if t else ""
        d["target_note"] = t.note if t else ""
        d["formula"] = t.formula if t else ""
        rels.append(d)

    bench = {}
    for key, preset in PRESETS.items():
        b = bm.known_analog_benchmark(matcher, preset["weights"])
        bench[key] = dict(rows=b.to_dict("records"), summary=bm.benchmark_summary(b, len(ds.earth)))

    # Low-Sun rehearsal windows depend only on latitude; quarter-degree steps are plenty.
    lat_key = np.round(ds.earth["lat"].to_numpy(float) * 4) / 4
    windows = {k: astronomy.rehearsal_window(k) for k in np.unique(lat_key)}

    balanced = PRESETS["balanced"]["weights"]
    targets = []
    for tid, row in ds.targets.iterrows():
        total = matcher.score(tid, balanced).total
        test_plan = planner.plan(matcher, tid, total).to_dict()
        targets.append(dict(id=tid, body=row["body"], name=row["name"], description=row["description"],
                            lat=float(row["lat"]), lon=float(row["lon"]),
                            profile=[p.to_dict() for p in profiles[tid]], plan=test_plan,
                            campaign=campaign.curve(matcher, tid, total, start)))

    return dict(
        synthetic=ds.synthetic,
        data_sources=data_sources(ds),
        generated=date.today().isoformat(),
        dims=DIMENSIONS,
        presets=PRESETS,
        params=dict(min_data_share=MIN_DATA_SHARE, top_k=TOP_K, n_runs=N_RUNS, min_km=MIN_KM,
                    concentration=30.0, confidence_jitter=0.2,
                    grazing_lo=astronomy.GRAZING_LO, grazing_hi=astronomy.GRAZING_HI),
        agent=dict(used=sum(r["used"] for r in runs or []) or agent_result.tool_calls_used,
                   max=agent_result.max_tool_calls, runs=runs or [], log=agent_result.log, relationships=rels),
        cleaning=cleaning,
        earth=dict(
            ids=list(ds.earth.index), lat=_clean(ds.earth["lat"], 2), lon=_clean(ds.earth["lon"], 2),
            region=list(ds.earth["region"].fillna("")),
            known=[known_name.get(c) for c in ds.earth.index],
            known_body=[known_body.get(c) for c in ds.earth.index],
            dist_known=[None if np.isinf(v) else round(float(v)) for v in bm.distance_to_known(matcher)],
            window=dict(peak_hours=[windows[k]["peak_hours"] for k in lat_key],
                        peak_date=[windows[k]["peak_date"] for k in lat_key],
                        days_6h=[windows[k]["days_6h"] for k in lat_key]),
            cols={c: _clean(ds.earth[c], 5) for c in used_cols}),
        targets=targets,
        benchmark=bench,
    )


def _cell_name(ds: Dataset, cell_id: str, known_name: dict) -> str:
    row = ds.earth.loc[cell_id]
    where = f"{abs(row['lat']):.1f}°{'N' if row['lat'] >= 0 else 'S'}, {abs(row['lon']):.1f}°{'E' if row['lon'] >= 0 else 'W'}"
    label = known_name.get(cell_id) or row["region"] or "Earth cell"
    return f"{label} ({where})"


def build_report(ds: Dataset, agent_result, matcher: Matcher, runs=None, cleaning=None, start=None) -> str:
    known_name = dict(zip(ds.known["cell_id"], ds.known["name"]))
    L = ["# EarthMimic run report", ""]
    if ds.synthetic:
        L += ["> **Synthetic demo data.** Every number below comes from generated placeholder data, "
              "not from measurements. It shows how the system behaves, not real findings. "
              "(Sun-geometry values are computed from latitude and are real.)", ""]
    L += [f"Earth cells: {len(ds.earth)}. Targets: {len(ds.targets)}.", ""]

    if cleaning:
        L += ["## Data cleaning", ""]
        for t in cleaning["tables"]:
            L.append(f"- {t['table']}: {t['rows_in']} rows in, {t['rows_out']} rows out.")
        L += ["", "| Table | Rule | Column | Count | Action |", "|---|---|---|---|---|"]
        for c in cleaning["changes"]:
            L.append(f"| {c['table']} | {c['rule']} | {c['column'] or '-'} | {c['count']} | {c['action']} |")
        L.append("")

    L += ["## Relationship agent", ""]
    for r in runs or []:
        L.append(f"- Run {r['run']}: {r['used']} of {r['max']} tool calls used.")
    L += ["", "| Target column | Earth column | Status | Confidence | Deciding check |", "|---|---|---|---|---|"]
    for r in agent_result.relationships:
        decide = next((c for c in r.checks if c.outcome == "fail"), None) or \
                 next((c for c in reversed(r.checks) if c.outcome == "warn"), None)
        status = r.verdict + ("" if r.scored else " (input only)")
        L.append(f"| {r.target_col} | {r.earth_col or '-'} | {status} | "
                 f"{r.confidence:.2f} | {decide.detail if decide else 'All checks passed.'} |")
    L.append("")

    bal = PRESETS["balanced"]["weights"]
    b = bm.known_analog_benchmark(matcher, bal)
    s = bm.benchmark_summary(b, len(ds.earth))
    L += ["## Known-analog check (balanced weights)", ""]
    if s["n"]:
        L += [f"{s['in_top_5_percent']} of {s['n']} known analogs rank in the top 5% of Earth cells "
              f"(random ranking would give about {s['expected_by_chance']}). "
              f"Median percentile: {s['median_percentile']:.1f}.", "",
              "| Known analog | Best target | Rank | Percentile |", "|---|---|---|---|"]
        for _, r in b.iterrows():
            L.append(f"| {r['name']} | {ds.targets.loc[r['best_target'], 'name']} | {r['rank']} | {r['percentile']:.1f} |")
    else:
        L.append("No known analogs were supplied.")
    L.append("")

    for tid, t in ds.targets.iterrows():
        prof = matcher.profile(tid)
        res, order = matcher.top(tid, bal, 5)
        stab = stability(matcher, tid, bal, n_runs=N_RUNS, top_k=TOP_K)
        L += [f"## {t['body']}: {t['name']}", "", t["description"], "",
              f"Earth can test {res.coverage:.0%} of this site's properties (balanced weights).", ""]
        broken = [p for p in prof if p.status == "breaks_down"]
        partial = [p for p in prof if p.status == "partial"]
        if broken:
            L += ["Where the analogy breaks down:", ""] + [f"- **{p.label}.** {p.reason}" for p in broken] + [""]
        if partial:
            L += ["Only partly reproducible:", ""] + [f"- **{p.label}.** {p.reason}" for p in partial] + [""]
        if not res.used:
            L += ["Nothing about this site can be tested on Earth with the current data, so no sites are ranked.", ""]
        else:
            L += ["| Rank | Earth site | Score | Stays in top 10 | Strongest dimension |", "|---|---|---|---|---|"]
            for n, i in enumerate(order, 1):
                if np.isnan(res.total[i]):
                    continue
                cid = ds.earth.index[i]
                dim = max(res.dims, key=lambda d: np.nan_to_num(res.dims[d][i], nan=-1))
                st = stab["stability"].get(cid, 0.0)
                L.append(f"| {n} | {_cell_name(ds, cid, known_name)} | {res.total[i]:.3f} | {st:.0%} | {DIMENSIONS[dim]} |")
            cand = bm.unrecognized_candidates(matcher, tid, bal, top_n=3, min_km=MIN_KM)
            L += ["", f"Best candidates more than {MIN_KM:.0f} km from any known analog: "
                  + "; ".join(f"{_cell_name(ds, c, {})} at {r['score']:.3f}" for c, r in cand.iterrows()) + ".", ""]

        pl = planner.plan(matcher, tid, res.total)
        n_req = len(pl.requirements)
        if n_req:
            coverable = n_req - len(pl.uncovered)
            L += [f"Test plan: {n_req} requirements can be tested on Earth. The best single site passes "
                  f"{len(pl.best_single['covers'])}. {len(pl.sites)} site(s) together pass {coverable}"
                  + (" (smallest possible set)." if pl.exact else " (greedy estimate)."), ""]
            for site in pl.sites:
                L.append(f"- {_cell_name(ds, site['cell_id'], known_name)}: "
                         + ", ".join(pl.requirements[j].label.lower() for j in site["covers"]))
            L.append("")
            curve = campaign.curve(matcher, tid, res.total, start)
            if curve["rows"]:
                where = (f"from {start[0]:.1f}, {start[1]:.1f}" if start else "free-floating route")
                L += [f"Field campaign ({where}): best coverage and shortest route per number of sites. "
                      "Heavy equipment favours fewer sites; portable equipment favours fewer kilometres.", "",
                      "| Sites | Requirements covered | Route km | Stops in order |", "|---|---|---|---|"]
                for row in curve["rows"]:
                    stops = " -> ".join(_cell_name(ds, s["cell_id"], known_name) for s in row["stops"])
                    L.append(f"| {row['k']} | {row['covered']} of {n_req} | {row['km']:,.0f} | {stops} |")
                L.append("")
    return "\n".join(L)


def build_dashboard(payload: dict) -> str:
    template = (_DASHBOARD / "template.html").read_text(encoding="utf-8")
    scoring = (_DASHBOARD / "scoring.js").read_text(encoding="utf-8")
    land = json.dumps(json.loads((_DASHBOARD / "land.json").read_text(encoding="utf-8"))["rings"], separators=(",", ":"))
    data = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    return template.replace("/*__SCORING_JS__*/", scoring).replace("__LAND__", land).replace("__PAYLOAD__", data)


def run(data_dir: str | Path, out_dir: str | Path, max_tool_calls: int = 15, proposer=None,
        raw_dir: str | Path | None = None, fresh_store: bool = False, advisor=None, start=None) -> dict:
    """Run the whole pipeline.

    If `raw_dir` is given it is cleaned into `data_dir` first. The agent
    runs repeatedly (each run with its own tool-call budget) until nothing
    is waiting on budget and no new derived variable appears.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cleaning = cl.clean_folder(raw_dir, data_dir) if raw_dir else None
    report_path = Path(data_dir) / "cleaning_report.json"
    if cleaning is None and report_path.exists():
        cleaning = json.loads(report_path.read_text(encoding="utf-8"))

    ds = load(data_dir)
    setup_log = astronomy.add_columns(ds)

    review = advisor.review(derived.DERIVED, ds.target_cols, ds.earth_cols) if advisor else None
    if advisor and advisor.note:
        setup_log.append(advisor.note)

    store_path = out / "relationships.sqlite"
    if fresh_store and store_path.exists():
        store_path.unlink()
    store = SqliteStore(store_path)
    agent = RelationshipAgent(ds, proposer=proposer, max_tool_calls=max_tool_calls)
    runs = []
    for _ in range(MAX_RUNS):
        run_no = store.new_run()
        agent_result = agent.run(store, run_no)
        new_columns = derived.add_derived(ds, agent_result.accepted(), review)
        runs.append(dict(run=run_no, used=agent_result.tool_calls_used, max=max_tool_calls,
                         log=(setup_log if not runs else []) + agent_result.log + new_columns))
        if not new_columns and not agent_result.waiting_on_budget():
            break
    store.close()

    # A raw column replaced by a derived one stays as an input but is no longer scored.
    for concept, why in derived.superseded_concepts(ds, agent_result.accepted()).items():
        for r in agent_result.relationships:
            t = ds.target_cols.get(r.target_col)
            if r.verdict == "accepted" and t and t.concept == concept and t.source != "derived":
                r.scored = False
                r.checks.append(Check("Superseded by a derived variable", "warn", why))

    matcher = Matcher(ds, agent_result)
    payload = build_payload(ds, agent_result, matcher, runs, cleaning, start)
    payload["campaign_map"] = True   # the dashboard embeds campaign_map.html
    (out / "relationships.json").write_text(json.dumps(payload["agent"], indent=1), encoding="utf-8")
    (out / "results.json").write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    (out / "report.md").write_text(build_report(ds, agent_result, matcher, runs, cleaning, start), encoding="utf-8")
    (out / "dashboard.html").write_text(build_dashboard(payload), encoding="utf-8")
    (out / "campaign_map.html").write_text(campaign_map.build(payload), encoding="utf-8")
    return dict(dataset=ds, agent=agent_result, matcher=matcher, payload=payload, out=out, runs=runs, cleaning=cleaning)
