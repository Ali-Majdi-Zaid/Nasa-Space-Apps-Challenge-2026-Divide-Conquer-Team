"""Readable names for unnamed Earth grid cells.

A grid cell that nobody named arrives labelled only by its latitude band
("Tropics", "Northern mid-latitudes"), which says nothing about what is
there. This module describes each such cell from its own measurements
(temperature, precipitation, elevation, slope, albedo: all from the NASA
sources already in the table) and adds a coarse geographic area, giving
names like "Cold arid high plateau, Central and East Asia".

Named sites and known analogs keep their names. The area is a rough box
lookup for orientation only; nothing is scored on it.
"""
from __future__ import annotations

import numpy as np

from .io import Dataset

BANDS = {"", "Arctic", "Antarctic", "Tropics", "Northern mid-latitudes", "Southern mid-latitudes"}

# (name, lat_min, lat_max, lon_min, lon_max); first match wins.
_AREAS = [
    ("Antarctica", -90, -60, -180, 180),
    ("Iceland", 63, 67, -25, -13),
    ("Greenland", 59, 84, -73, -11),
    ("Alaska and Yukon", 54, 72, -170, -125),
    ("Arctic Canada", 60, 84, -125, -60),
    ("North America", 7, 60, -170, -52),
    ("South America", -57, 13, -82, -34),
    ("Svalbard and Arctic Europe", 70, 82, 5, 40),
    ("Europe", 36, 72, -11, 40),
    ("Arabia and the Middle East", 12, 40, 35, 62),
    ("Sahara and North Africa", 15, 37, -18, 35),
    ("Africa", -35, 15, -18, 52),
    ("Siberia", 50, 82, 40, 180),
    ("Central and East Asia", 25, 50, 62, 150),
    ("South and Southeast Asia", -10, 25, 62, 150),
    ("Australia and Oceania", -50, 0, 110, 180),
]


def area(lat: float, lon: float) -> str:
    for name, la0, la1, lo0, lo1 in _AREAS:
        if la0 <= lat <= la1 and lo0 <= lon <= lo1:
            return name
    return ""


def _get(row, name):
    v = row.get(name, np.nan)
    return float(v) if v is not None and not (isinstance(v, float) and np.isnan(v)) else np.nan


def describe(row) -> str:
    """Climate and landform of one cell, from its measurements ('' if there is too little to go on)."""
    t, p = _get(row, "temp_mean_c"), _get(row, "precip_mm_day")
    elev, slope, alb = _get(row, "elevation_m"), _get(row, "slope_deg"), _get(row, "albedo")
    if np.isnan(t):
        return ""
    if alb >= 0.6 and t <= -10:
        return "Polar ice sheet" if (np.isnan(slope) or slope < 1.5) else "Glaciated mountains"
    heat = "Polar" if t < -10 else "Cold" if t < 5 else "Temperate" if t < 18 else "Hot"
    wet = "" if np.isnan(p) else ("hyper-arid" if p < 0.25 else "arid" if p < 0.7 else "semi-arid" if p < 1.5 else "humid")
    if np.isnan(elev) and np.isnan(slope):
        form = "land"
    elif slope >= 2.0:
        form = "high mountains" if elev >= 2500 else "mountains"
    elif elev >= 2500:
        form = "high plateau"
    elif slope >= 0.7:
        form = "hills"
    elif wet in ("hyper-arid", "arid"):
        form = "desert plain"
    else:
        form = "plain"
    return " ".join(w for w in (heat, wet, form) if w)


def name_cells(ds: Dataset) -> int:
    """Replace latitude-band labels with descriptive names. Returns how many cells were renamed."""
    n = 0
    regions = ds.earth["region"].fillna("").astype(str).tolist()
    for k, (cell_id, row) in enumerate(ds.earth.iterrows()):
        if regions[k] not in BANDS:
            continue
        what, where = describe(row), area(float(row["lat"]), float(row["lon"]))
        if what:
            regions[k] = f"{what}, {where}" if where else what
            n += 1
    ds.earth["region"] = regions
    return n
