"""Data cleaning.

Turns a folder of raw tables into a folder the rest of the pipeline can
trust, and writes down everything it changed. The rules, in order:

1. Text that should be a number ("n/a", "--") becomes a missing value.
2. Sentinel codes used by data products for "no data" (-9999, 1e20, ...)
   become missing values.
3. Rows without a usable id or with impossible coordinates are dropped.
   Earth longitudes given as 0..360 are rewritten as -180..180.
4. Exact duplicate rows are dropped.
5. Rows that share an id but disagree are merged (numeric columns are
   averaged, ignoring missing values) and the id is recorded.
6. Values that cannot be physical (a fraction above 1, a temperature below
   absolute zero, ...) become missing values.
7. Extreme outliers are flagged but left alone: an extreme value may be
   exactly the analog we are looking for.

Missing values are never filled in. The matching engine skips them and
the agent refuses columns that are too sparse.

The cleaning report (`cleaning_report.json`) lists every rule that fired,
per column, with counts and examples, plus a SHA-256 hash of each input
file so results can be traced back to the exact data they came from.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from .schema import Column, bounds_for, columns_from_meta

SENTINELS = (-9999.0, -999.0, -32768.0, 9999.0, 99999.0, 1e20, 1e30, 9.96921e36)
OUTLIER_Z = 6.0  # robust z-score beyond which a value is flagged


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class _Log:
    def __init__(self, table: str):
        self.table, self.entries = table, []

    def add(self, rule: str, action: str, count: int, column: str = "", examples=()):
        if count:
            self.entries.append(dict(table=self.table, rule=rule, column=column, action=action,
                                     count=int(count), examples=[str(e) for e in list(examples)[:5]]))


def clean_table(df: pd.DataFrame, cols: dict[str, Column], id_col: str, table: str,
                normalise_lon: bool) -> tuple[pd.DataFrame, list[dict]]:
    """Clean one table. Returns the cleaned table and the log entries."""
    log = _Log(table)
    df = df.copy()
    numeric = ["lat", "lon"] + [c for c in cols if c in df.columns]

    # 1. not-a-number text
    for c in numeric:
        if not pd.api.types.is_numeric_dtype(df[c]):
            coerced = pd.to_numeric(df[c], errors="coerce")
            bad = coerced.isna() & df[c].notna() & (df[c].astype(str).str.strip() != "")
            log.add("Text where a number belongs", "set to missing", bad.sum(), c, df.loc[bad, c].unique())
            df[c] = coerced
        df[c] = df[c].astype(float)

    # 2. sentinel codes
    for c in numeric:
        hit = df[c].isin(SENTINELS)
        log.add("No-data sentinel code", "set to missing", hit.sum(), c, df.loc[hit, c].unique())
        df.loc[hit, c] = np.nan

    # 3. ids and coordinates
    df[id_col] = df[id_col].astype("string").str.strip()
    bad_id = df[id_col].isna() | (df[id_col] == "")
    log.add("Missing id", "row dropped", bad_id.sum(), id_col)
    df = df[~bad_id]
    if normalise_lon:
        wrap = (df["lon"] > 180) & (df["lon"] <= 360)
        log.add("Longitude given as 0 to 360", "rewritten as -180 to 180", wrap.sum(), "lon", df.loc[wrap, id_col])
        df.loc[wrap, "lon"] = df.loc[wrap, "lon"] - 360
    lon_hi = 180 if normalise_lon else 360
    bad_xy = df["lat"].isna() | df["lon"].isna() | (df["lat"].abs() > 90) | (df["lon"] < -180) | (df["lon"] > lon_hi)
    log.add("Missing or impossible coordinates", "row dropped", bad_xy.sum(), "lat/lon", df.loc[bad_xy, id_col])
    df = df[~bad_xy]

    # 4. exact duplicates
    dup = df.duplicated(keep="first")
    log.add("Exact duplicate row", "row dropped", dup.sum(), examples=df.loc[dup, id_col].unique())
    df = df[~dup]

    # 5. same id, different values
    clash = df[id_col].duplicated(keep=False)
    if clash.any():
        ids = df.loc[clash, id_col].unique()
        log.add("Same id with conflicting values", "merged (numeric columns averaged)", len(ids), id_col, ids)
        agg = {c: ("mean" if c in numeric else "first") for c in df.columns if c != id_col}
        merged = df[clash].groupby(id_col, sort=False).agg(agg).reset_index()
        df = pd.concat([df[~clash], merged], ignore_index=True)[list(df.columns)]

    # 6. physically impossible values
    for name, col in cols.items():
        if name not in df.columns:
            continue
        lo, hi = bounds_for(col)
        bad = pd.Series(False, index=df.index)
        if lo is not None:
            bad |= df[name] < lo
        if hi is not None:
            bad |= df[name] > hi
        log.add("Physically impossible value", "set to missing", bad.sum(), name,
                df.loc[bad, name].round(4).unique())
        df.loc[bad, name] = np.nan

    # 7. outliers: flag, never change
    for name in cols:
        if name not in df.columns:
            continue
        x = df[name].to_numpy(float)
        med = np.nanmedian(x) if np.isfinite(x).any() else np.nan
        mad = np.nanmedian(np.abs(x - med)) * 1.4826 if np.isfinite(med) else 0.0
        if mad > 0 and np.isfinite(x).sum() >= 30:
            far = np.abs(x - med) / mad > OUTLIER_Z
            # If many values are "extreme" the column is skewed or zero-heavy, not full of outliers.
            if far.sum() <= 0.02 * len(x):
                log.add("Extreme outlier", "flagged, value kept", far.sum(), name, df.loc[far, id_col])

    return df.reset_index(drop=True), log.entries


def clean_folder(raw_dir: str | Path, out_dir: str | Path) -> dict:
    """Clean a raw data folder into `out_dir`. Returns the cleaning report."""
    raw, out = Path(raw_dir), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    earth_cols = columns_from_meta(json.loads((raw / "earth_meta.json").read_text(encoding="utf-8")))
    target_cols = columns_from_meta(json.loads((raw / "targets_meta.json").read_text(encoding="utf-8")))

    report = dict(raw_folder=str(raw), files=[], tables=[], changes=[], columns=[])
    for name in ("earth_cells.csv", "targets.csv", "earth_meta.json", "targets_meta.json", "known_analogs.csv"):
        if (raw / name).exists():
            report["files"].append(dict(name=name, sha256=_sha256(raw / name), bytes=(raw / name).stat().st_size))

    earth_raw = pd.read_csv(raw / "earth_cells.csv")
    earth, log = clean_table(earth_raw, earth_cols, "cell_id", "Earth cells", normalise_lon=True)
    report["changes"] += log
    report["tables"].append(dict(table="Earth cells", rows_in=len(earth_raw), rows_out=len(earth)))

    targets_raw = pd.read_csv(raw / "targets.csv")
    targets, log = clean_table(targets_raw, target_cols, "target_id", "Target sites", normalise_lon=False)
    report["changes"] += log
    report["tables"].append(dict(table="Target sites", rows_in=len(targets_raw), rows_out=len(targets)))

    for table, frame, cols in (("Earth cells", earth, earth_cols), ("Target sites", targets, target_cols)):
        for c in cols.values():
            if c.name in frame.columns:
                report["columns"].append(dict(table=table, column=c.name, label=c.label, unit=c.unit, source=c.source,
                                              version=c.version, uncertainty=c.uncertainty,
                                              missing=round(float(frame[c.name].isna().mean()), 4)))

    earth.to_csv(out / "earth_cells.csv", index=False)
    targets.to_csv(out / "targets.csv", index=False)
    for name in ("earth_meta.json", "targets_meta.json", "SYNTHETIC_DATA.txt", "demo_fixture.json"):
        if (raw / name).exists():
            shutil.copy(raw / name, out / name)
    if (raw / "known_analogs.csv").exists():
        known = pd.read_csv(raw / "known_analogs.csv")
        gone = ~known["cell_id"].astype(str).isin(set(earth["cell_id"]))
        if gone.any():
            report["changes"].append(dict(table="Known analogs", rule="Refers to a cell that was dropped", column="cell_id",
                                          action="row dropped", count=int(gone.sum()),
                                          examples=[str(v) for v in known.loc[gone, "cell_id"][:5]]))
        known[~gone].to_csv(out / "known_analogs.csv", index=False)

    report["total_changes"] = int(sum(c["count"] for c in report["changes"]))
    (out / "cleaning_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    return report
