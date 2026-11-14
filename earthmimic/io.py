"""Dataset loading and validation.

A data folder holds five files:

    earth_cells.csv     one row per Earth location: cell_id, lat, lon, [region], variables...
    earth_meta.json     metadata for each Earth variable column
    targets.csv         one row per Moon/Mars site: target_id, body, name, [description], lat, lon, variables...
    targets_meta.json   metadata for each target variable column
    known_analogs.csv   (optional) cell_id, name, body - sites already used as analogs

The demo generator writes exactly this layout, so real data only has to
follow the same shape.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .schema import DIMENSIONS, Column, columns_from_meta


@dataclass
class Dataset:
    earth: pd.DataFrame             # indexed by cell_id
    earth_cols: dict[str, Column]
    targets: pd.DataFrame           # indexed by target_id
    target_cols: dict[str, Column]
    known: pd.DataFrame             # cell_id, name, body
    synthetic: bool


def _check_meta(cols: dict[str, Column], frame: pd.DataFrame, what: str) -> None:
    for c in cols.values():
        if c.name not in frame.columns:
            raise ValueError(f"{what}: metadata describes column '{c.name}' but the CSV has no such column")
        if c.dimension not in DIMENSIONS:
            raise ValueError(f"{what}: column '{c.name}' has unknown dimension '{c.dimension}'. "
                             f"Use one of: {', '.join(DIMENSIONS)}")
        if not pd.api.types.is_numeric_dtype(frame[c.name]):
            raise ValueError(f"{what}: column '{c.name}' must be numeric")


def load(data_dir: str | Path) -> Dataset:
    d = Path(data_dir)
    earth = pd.read_csv(d / "earth_cells.csv")
    targets = pd.read_csv(d / "targets.csv")
    for frame, key, what in ((earth, "cell_id", "earth_cells.csv"), (targets, "target_id", "targets.csv")):
        for col in (key, "lat", "lon"):
            if col not in frame.columns:
                raise ValueError(f"{what} is missing the required column '{col}'")
        if frame[key].duplicated().any():
            raise ValueError(f"{what}: '{key}' values must be unique")
    for col in ("body", "name"):
        if col not in targets.columns:
            raise ValueError(f"targets.csv is missing the required column '{col}'")
    if "region" not in earth.columns:
        earth["region"] = ""
    if "description" not in targets.columns:
        targets["description"] = ""

    earth_cols = columns_from_meta(json.loads((d / "earth_meta.json").read_text(encoding="utf-8")))
    target_cols = columns_from_meta(json.loads((d / "targets_meta.json").read_text(encoding="utf-8")))
    _check_meta(earth_cols, earth, "earth_meta.json")
    _check_meta(target_cols, targets, "targets_meta.json")

    known_path = d / "known_analogs.csv"
    if known_path.exists():
        known = pd.read_csv(known_path)
        missing = set(known["cell_id"]) - set(earth["cell_id"])
        if missing:
            raise ValueError(f"known_analogs.csv refers to unknown cell ids: {sorted(missing)[:5]}")
    else:
        known = pd.DataFrame(columns=["cell_id", "name", "body"])

    return Dataset(
        earth=earth.set_index("cell_id"),
        earth_cols=earth_cols,
        targets=targets.set_index("target_id"),
        target_cols=target_cols,
        known=known,
        synthetic=(d / "SYNTHETIC_DATA.txt").exists(),
    )
