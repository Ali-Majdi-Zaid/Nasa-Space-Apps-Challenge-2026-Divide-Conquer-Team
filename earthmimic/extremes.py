"""Stress tests: Earth's extremes as proving grounds.

Matching asks "where on Earth is most like the landing site?". Engineers
also ask a blunter question: "where on Earth is harsh enough to break my
equipment before the Moon or Mars does?". A dust storm, a volcano's fresh
lava, the coldest plateau: none of them looks like the landing site as a
whole, but each pushes one kind of stress as far as Earth can push it.

For each hazard this module finds the harshest places on Earth and says,
for every target, which world is harsher:

* Harsher on Earth: equipment can be over-tested here. If it survives the
  Earth site, it has margin at the target.
* About as harsh: a realistic rehearsal.
* Harsher at the target: Earth only takes you part of the way; the rest
  needs a chamber.

Hazards come from the same NASA columns the matching uses, plus recorded
natural events (volcanic eruptions, dust storms) from NASA EONET, the
Earth Observatory Natural Event Tracker.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from .io import Dataset
from .matching import haversine_km

EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events?category={cat}&status=all&limit=3000"
EONET_VERSION = "NASA EONET v3 (Earth Observatory Natural Event Tracker)"
CATEGORIES = {"volcanoes": "Volcanic eruption", "dustHaze": "Dust storm"}
NEAR_KM = 300.0     # an event counts for a cell when it happened within this distance
TOP_N = 5
SAME_SHARE = 0.1    # two worlds are "about as harsh" when they differ by under this share of Earth's own range
DRY_MM_DAY = 1.0    # the dust hazard only ranks places drier than this

# key, label, Earth column, harsh direction (+1 high, -1 low), what it stresses, why it matters off-world
HAZARDS = [
    ("cold", "Deep cold", "temp_mean_c", -1, "batteries, lubricants, seals, electronics",
     "Cold stiffens seals, drains batteries and makes metals brittle."),
    ("cycling", "Day-night temperature swings", "temp_swing_c", +1, "joints, solder, coatings, anything that expands and shrinks",
     "Repeated heating and cooling fatigues materials faster than steady cold."),
    ("dust", "Airborne dust", "dust_aod", +1, "solar panels, optics, filters, seals",
     "Dust dims solar panels, scratches optics and works its way into mechanisms. Ranked among dry places only, "
     "so the haze is desert dust and not city smog."),
    ("wind", "Wind force", "wind_pressure_pa", +1, "structures, antennas, tethers, dust covers",
     "The push of the wind on a surface, which also decides how much dust it can lift."),
    ("uv", "Ultraviolet light", "uvb_wm2", +1, "plastics, coatings, suit fabrics, cables",
     "UV-B breaks down polymers and paints. Neither the Moon nor Mars has an ozone layer."),
    ("dry", "Extreme dryness", "precip_mm_day", -1, "dust handling, static electricity, water recycling",
     "Bone-dry ground behaves like regolith: loose, clingy and electrostatically charged."),
    ("rough", "Broken, steep ground", "roughness_deg", +1, "wheels, suspension, navigation, landing legs",
     "How abruptly the slope changes underfoot or under a wheel."),
    ("frozen", "Frozen ground", "frozen_ground_share", +1, "drills, excavators, ice sampling",
     "Ice-cemented ground is as hard as rock and is what a resource mission must dig."),
    ("thin_air", "Thin air", "pressure_kpa", -1, "cooling, rotors, parachutes, breathing systems",
     "Less air means less cooling, less lift and less drag."),
]
VOLCANIC = ("volcanic", "Volcanic ground", "mobility on lava and ash, sampling tools, regolith handling",
            "Fresh basalt lava and ash are the closest thing on Earth to lunar and Martian regolith: both worlds' plains are "
            "volcanic basalt.")


# ----------------------------------------------------------------- NASA EONET
def fetch_events(cache_dir: str | Path, get, log=print) -> list[dict]:
    """Volcanic eruptions and dust storms recorded by NASA EONET, one entry per named place.

    Replies are cached in `cache_dir`, so reruns need no network. Returns
    [{cat, kind, title, lat, lon, n, last}], where n counts the recorded events at that place.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    places: dict[tuple, dict] = {}
    for cat, kind in CATEGORIES.items():
        cache = cache_dir / f"{cat}.json"
        if cache.exists():
            reply = json.loads(cache.read_text(encoding="utf-8"))
        else:
            try:
                reply = get(EONET_URL.format(cat=cat))
            except Exception as err:   # no network, or the service is down: the stress tests simply go without events
                log(f"  warning: NASA EONET did not answer for {cat} ({err}); continuing without these events")
                continue
            cache.write_text(json.dumps(reply), encoding="utf-8")
        for ev in (reply.get("events") or []) if isinstance(reply, dict) else []:
            for g in ev.get("geometry") or []:
                xy = _centre(g)
                if xy is None:
                    continue
                title = str(ev.get("title", "")).strip()
                key = (cat, title)
                p = places.setdefault(key, dict(cat=cat, kind=kind, title=title, lat=0.0, lon=0.0, n=0, last=""))
                p["lat"] += xy[1]
                p["lon"] += xy[0]
                p["n"] += 1
                p["last"] = max(p["last"], str(g.get("date", ""))[:10])
    out = []
    for p in places.values():
        p["lat"], p["lon"] = round(p["lat"] / p["n"], 3), round(p["lon"] / p["n"], 3)
        out.append(p)
    return sorted(out, key=lambda p: (p["cat"], -p["n"], p["title"]))


def _centre(geometry: dict):
    """[lon, lat] of a point, or the mean corner of a polygon."""
    c = geometry.get("coordinates")
    try:
        if geometry.get("type") == "Point":
            return float(c[0]), float(c[1])
        ring = np.array(c[0], float)
        return float(ring[:, 0].mean()), float(ring[:, 1].mean())
    except (TypeError, ValueError, IndexError):
        return None


def load_events(data_dir: str | Path) -> list[dict]:
    path = Path(data_dir) / "events.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


# -------------------------------------------------------------- the stress tests
def _fmt_site(ds: Dataset, i: int, known: dict) -> str:
    cid = ds.earth.index[i]
    return known.get(cid) or ds.earth["region"].iloc[i] or cid


def _nearby(events: list[dict], cat: str, lats: np.ndarray, lons: np.ndarray):
    """Per cell: how many events of `cat` were recorded within NEAR_KM, and the most active place among them."""
    counts, names = np.zeros(len(lats), int), [""] * len(lats)
    best = np.zeros(len(lats), int)
    for ev in events:
        if ev["cat"] != cat:
            continue
        near = haversine_km(lats, lons, ev["lat"], ev["lon"]) <= NEAR_KM
        counts[near] += ev["n"]
        for i in np.flatnonzero(near & (ev["n"] > best)):
            best[i], names[i] = ev["n"], ev["title"]
    return counts, names


def build(ds: Dataset, targets: list[dict], events: list[dict]) -> dict:
    """Everything the Stress tests view needs. `targets` is the payload's target list (with profiles)."""
    known = dict(zip(ds.known["cell_id"], ds.known["name"]))
    lats, lons = ds.earth["lat"].to_numpy(float), ds.earth["lon"].to_numpy(float)
    hazards = []
    for key, label, col, direction, tests, why in HAZARDS:
        if col not in ds.earth.columns or col not in ds.earth_cols:
            continue
        x = ds.earth[col].to_numpy(float)
        if key == "dust" and "precip_mm_day" in ds.earth.columns:
            # Aerosol optical depth counts every particle in the air, city smog and smoke included.
            # Keeping only dry places (under about 365 mm of rain a year) leaves the ones where it is mineral dust.
            x = np.where(ds.earth["precip_mm_day"].to_numpy(float) < DRY_MM_DAY, x, np.nan)
        if np.isnan(x).all():
            continue
        order = np.argsort(np.where(np.isnan(x), -np.inf, direction * x))[::-1][:TOP_N]
        extreme = float(x[order[0]])
        per_target = {}
        for t in targets:
            p = next((p for p in t["profile"] if p.get("earth_col") == col and p.get("target_value") is not None), None)
            if p is None:
                continue
            # "About as harsh" means within a tenth of the range Earth itself spans. That is stricter than the
            # matching band on purpose: a stress test must not call Earth harsh enough when it clearly is not.
            tv = float(p["target_value"])
            lo, hi = np.nanpercentile(x, [0.5, 99.5])
            if p.get("scale") == "log" and extreme > 0 and tv > 0 and lo > 0:
                gap, bw = direction * (math.log10(extreme) - math.log10(tv)), SAME_SHARE * (math.log10(hi) - math.log10(lo))
            else:
                gap, bw = direction * (extreme - tv), SAME_SHARE * (hi - lo)
            verdict = "earth" if gap > bw else "target" if gap < -bw else "same"
            # The Earth site that reproduces this landing site's value most closely: the place to rehearse
            # this one stress for this one site. When the target is harsher than all of Earth it is the extreme itself.
            if p.get("scale") == "log" and tv > 0:
                with np.errstate(divide="ignore", invalid="ignore"):
                    dist = np.abs(np.where(x > 0, np.log10(x), np.nan) - math.log10(tv))
            else:
                dist = np.abs(x - tv)
            j = int(np.nanargmin(dist)) if not np.isnan(dist).all() else int(order[0])
            per_target[t["id"]] = dict(value=round(tv, 4), verdict=verdict,
                                       site=dict(index=j, name=_fmt_site(ds, j, known), value=round(float(x[j]), 4)))
        hazards.append(dict(key=key, label=label, col=col, unit=ds.earth_cols[col].unit, direction=direction, tests=tests, why=why,
                            extreme=round(extreme, 4),
                            top=[dict(index=int(i), name=_fmt_site(ds, int(i), known), value=round(float(x[i]), 4)) for i in order],
                            targets=per_target))

    counts, names = _nearby(events, "volcanoes", lats, lons)
    if counts.any():
        key, label, tests, why = VOLCANIC
        order = [int(i) for i in np.argsort(-counts)[:TOP_N] if counts[i] > 0]
        hazards.append(dict(key=key, label=label, col="", unit="eruptions", direction=1, tests=tests, why=why,
                            extreme=int(counts[order[0]]), events=True,
                            top=[dict(index=i, name=_fmt_site(ds, i, known), value=int(counts[i]), near=names[i]) for i in order],
                            targets={}))
    dust_counts, dust_names = _nearby(events, "dustHaze", lats, lons)
    for h in hazards:      # name a recorded storm next to a dusty site, when NASA logged one nearby
        if h["key"] == "dust":
            for s in h["top"]:
                if dust_counts[s["index"]]:
                    s["near"] = dust_names[s["index"]]
    return dict(hazards=hazards, events=events, near_km=NEAR_KM,
                source=EONET_VERSION if events else "",
                n_volcano=sum(1 for e in events if e["cat"] == "volcanoes"),
                n_dust=sum(1 for e in events if e["cat"] == "dustHaze"))
