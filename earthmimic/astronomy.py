"""Sun geometry, computed rather than downloaded.

Where the Sun sits in the sky depends only on latitude, the body's axial
tilt and the time of year, so these values are real for every location on
Earth, the Moon and Mars without any dataset. Two simplifications: the
orbit is treated as circular, and terrain shadowing and atmospheric
refraction are ignored. A measured value in the dataset takes precedence
over the computed one.

Why it matters: near the lunar south pole the Sun never climbs more than a
couple of degrees, so light always rakes across the surface and shadows
are long. That lighting is a major hazard for navigation and landing.
Earth only produces it at certain latitudes on certain dates, and this
module says where and when.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from .io import Dataset
from .schema import BODIES, Column

GRAZING_LO, GRAZING_HI = 0.0, 5.0   # degrees above the horizon
_N_DAYS, _N_STEPS = 360, 288        # year and day resolution (1 deg of orbit, 5 minutes)

COLUMN = dict(
    name="grazing_sun_share", label="Time with the Sun low on the horizon", dimension="illumination",
    quantity="fraction", unit="share_of_year", concept="grazing_sun", source="computed", priority=8,
    note=f"Share of the year the Sun is {GRAZING_LO:.0f} to {GRAZING_HI:.0f} degrees above the horizon. "
         "Computed from latitude and axial tilt; ignores terrain shadowing and refraction.",
    formula="sin(elevation) = sin(lat) sin(decl) + cos(lat) cos(decl) cos(hour angle), "
            "with sin(decl) = sin(tilt) sin(orbit angle)")


def elevation_grid(lat_deg: float, obliquity_deg: float) -> np.ndarray:
    """Sun elevation in degrees, shape (days of year, steps of day)."""
    orbit = np.radians(np.arange(_N_DAYS) * 360.0 / _N_DAYS)            # 0 = northward equinox
    decl = np.arcsin(np.sin(np.radians(obliquity_deg)) * np.sin(orbit))[:, None]
    hour = np.radians(np.arange(_N_STEPS) * 360.0 / _N_STEPS)[None, :]
    lat = np.radians(lat_deg)
    s = np.sin(lat) * np.sin(decl) + np.cos(lat) * np.cos(decl) * np.cos(hour)
    return np.degrees(np.arcsin(np.clip(s, -1, 1)))


def grazing_share(lat_deg: float, obliquity_deg: float) -> float:
    """Share of the year the Sun sits between GRAZING_LO and GRAZING_HI degrees."""
    e = elevation_grid(lat_deg, obliquity_deg)
    return float(((e >= GRAZING_LO) & (e <= GRAZING_HI)).mean())


INSOLATION_COLUMN = dict(
    name="insolation_wm2", label="Mean solar energy flux", dimension="illumination",
    quantity="irradiance", unit="W_per_m2", concept="mean_insolation", source="computed", priority=7,
    note="Annual-mean solar power per square metre of level ground, above any atmosphere. "
         "Computed from latitude, axial tilt and the body's distance from the Sun; "
         "ignores atmosphere, terrain shadowing and orbital eccentricity.",
    formula="solar constant x mean over the year and day of max(0, sin(elevation))")


def mean_insolation(lat_deg: float, obliquity_deg: float, solar_constant_wm2: float) -> float:
    """Annual-mean top-of-atmosphere insolation on a horizontal surface, W/m^2."""
    e = elevation_grid(lat_deg, obliquity_deg)
    return float(solar_constant_wm2 * np.clip(np.sin(np.radians(e)), 0, None).mean())


def rehearsal_window(lat_deg: float, obliquity_deg: float = BODIES["Earth"]["obliquity_deg"]) -> dict:
    """When a site gets the most low-Sun hours per day.

    Returns the peak hours per day, the calendar date of the first peak
    (Earth dates, counted from the March equinox), and how many days a year
    offer at least six such hours.
    """
    e = elevation_grid(lat_deg, obliquity_deg)
    hours = ((e >= GRAZING_LO) & (e <= GRAZING_HI)).mean(axis=1) * 24.0
    peak = int(np.argmax(hours))
    when = date(2001, 3, 20) + timedelta(days=round(peak * 365.25 / _N_DAYS))
    return dict(peak_hours=round(float(hours[peak]), 1), peak_date=f"{when.day} {when.strftime('%B')}",
                days_6h=int(round((hours >= 6).sum() * 365.25 / _N_DAYS)))


def _sun_value(spec: dict, lat_deg: float, body: str) -> float:
    b = BODIES[body]
    if spec["name"] == INSOLATION_COLUMN["name"]:
        return mean_insolation(lat_deg, b["obliquity_deg"], b["solar_constant_wm2"])
    return grazing_share(lat_deg, b["obliquity_deg"])


def add_columns(ds: Dataset) -> list[str]:
    """Add the computed Sun-geometry columns to both tables. Returns log lines."""
    log = []
    lat_key = np.round(ds.earth["lat"].to_numpy(float) * 4) / 4      # quarter-degree is plenty
    for spec in (COLUMN, INSOLATION_COLUMN):
        name = spec["name"]
        table = {k: _sun_value(spec, k, "Earth") for k in np.unique(lat_key)}
        if name not in ds.earth.columns:
            ds.earth[name] = [table[k] for k in lat_key]
            ds.earth_cols[name] = Column(**spec)
            log.append(f"Computed '{name}' for {len(ds.earth)} Earth cells from latitude.")

        measured = ds.targets[name] if name in ds.targets.columns else pd.Series(np.nan, index=ds.targets.index)
        values, n_computed = [], 0
        for tid, row in ds.targets.iterrows():
            if not np.isnan(measured[tid]):
                values.append(float(measured[tid]))       # a measured value wins
            elif row["body"] in BODIES:
                values.append(_sun_value(spec, row["lat"], row["body"]))
                n_computed += 1
            else:
                values.append(np.nan)
        ds.targets[name] = values
        ds.target_cols.setdefault(name, Column(**spec))
        log.append(f"Computed '{name}' for {n_computed} target sites from latitude and axial tilt; "
                   f"{len(values) - n_computed} used a supplied value.")
    return log
