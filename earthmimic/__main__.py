"""Command line entry point.

    python -m earthmimic fetch --out RAW                     download real NASA data into a raw data folder
    python -m earthmimic demo                                generate synthetic raw data, clean it, run everything
    python -m earthmimic clean --raw RAW --out CLEAN         clean a raw data folder
    python -m earthmimic run --data CLEAN --out OUT          run on a cleaned data folder
    python -m earthmimic run --raw RAW --data CLEAN --out OUT   clean, then run
    add --llm to let a language model propose the column pairings
"""
import argparse
from pathlib import Path

from . import cleaning, demo_data, pipeline


def _proposer(use_llm: bool, out: str):
    if not use_llm:
        return None
    from .agent import LLMProposer
    from .llm import CachedProposer, default_complete
    return CachedProposer(LLMProposer(default_complete()), Path(out) / "llm_proposals.json")


def _start(text: str | None):
    if not text:
        return None
    lat, lon = (float(x) for x in text.split(","))
    return (lat, lon)


def _advisor(use_llm: bool, out: str):
    if not use_llm:
        return None
    from .llm import EquationAdvisor, default_complete
    return EquationAdvisor(default_complete(), Path(out) / "llm_equation_review.json")


def main():
    ap = argparse.ArgumentParser(prog="earthmimic", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demo", help="generate synthetic demo data, clean it and run the pipeline")
    d.add_argument("--raw", default="data/demo_raw")
    d.add_argument("--data", default="data/demo")
    d.add_argument("--out", default="out")
    d.add_argument("--cells", type=int, default=1500)
    d.add_argument("--seed", type=int, default=7)
    f = sub.add_parser("fetch", help="download real NASA data (Diviner, MOLA, POWER) into a raw data folder")
    f.add_argument("--out", default="data/real_raw")
    f.add_argument("--grid-step", type=float, default=10.0, help="spacing in degrees of the default Earth grid")
    f.add_argument("--skip", nargs="*", default=[], choices=["moon", "mars", "terrain"], help="sources to leave out")
    f.add_argument("--no-verify-ssl", action="store_true",
                   help="skip security-certificate checks (last resort if downloads fail with a certificate error)")
    c = sub.add_parser("clean", help="clean a raw data folder")
    c.add_argument("--raw", required=True)
    c.add_argument("--out", required=True)
    r = sub.add_parser("run", help="run the pipeline on a data folder")
    r.add_argument("--data", required=True, help="cleaned data folder (written to if --raw is given)")
    r.add_argument("--raw", help="raw data folder to clean first")
    r.add_argument("--out", default="out")
    r.add_argument("--fresh", action="store_true", help="forget stored relationship decisions and re-check everything")
    for p in (d, r):
        p.add_argument("--budget", type=int, default=15, help="agent tool calls per run")
        p.add_argument("--llm", action="store_true", help="use a language model to propose pairings")
        p.add_argument("--start", help='campaign starting point as "lat,lon", e.g. "33.3,44.4"')
    a = ap.parse_args()

    if a.cmd == "fetch":
        from . import ingest
        if a.no_verify_ssl:
            ingest.set_ssl_verification(False)
            print("Warning: security-certificate checks are off for this run.")
        try:
            out = ingest.fetch(a.out, grid_step=a.grid_step, skip=tuple(a.skip))
        except ingest.CertificateProblem as err:
            raise SystemExit(f"\n{err}")
        print(f"\nNext: python -m earthmimic run --raw {out} --data data/real --out out")
        return

    if a.cmd == "clean":
        report = cleaning.clean_folder(a.raw, a.out)
        for t in report["tables"]:
            print(f"{t['table']}: {t['rows_in']} rows in, {t['rows_out']} rows out")
        for ch in report["changes"]:
            print(f"  {ch['count']:>5}  {ch['rule']}" + (f" [{ch['column']}]" if ch["column"] else "") + f" -> {ch['action']}")
        print(f"\nWrote {a.out}/cleaning_report.json")
        return

    if a.cmd == "demo":
        demo_data.generate_raw(a.raw, n_cells=a.cells, seed=a.seed)
        result = pipeline.run(a.data, a.out, a.budget, _proposer(a.llm, a.out), raw_dir=a.raw, fresh_store=True,
                              advisor=_advisor(a.llm, a.out), start=_start(a.start))
    else:
        result = pipeline.run(a.data, a.out, a.budget, _proposer(a.llm, a.out), raw_dir=a.raw, fresh_store=a.fresh,
                              advisor=_advisor(a.llm, a.out), start=_start(a.start))
    if result["cleaning"]:
        print(f"Cleaning: {result['cleaning']['total_changes']} changes or flags recorded.")
    for run in result["runs"]:
        for line in run["log"]:
            print(line)
    print(f"\nWrote {result['out']}/report.md, dashboard.html, campaign_map.html, results.json, relationships.json, relationships.sqlite")


if __name__ == "__main__":
    main()
