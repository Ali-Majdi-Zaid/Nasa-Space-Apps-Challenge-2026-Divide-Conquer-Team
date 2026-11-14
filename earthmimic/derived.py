"""Derived variables.

Some raw columns cannot be compared fairly between worlds even though
they have the same name and unit. A 6 m/s wind on Mars pushes on a rover
about a hundred times more weakly than a 6 m/s wind on Earth, because the
air is that much thinner. The fair comparison is on a quantity derived
from physics that means the same thing everywhere.

Each derived variable is computed the same way on both sides, from input
columns whose pairings the agent has already accepted, and then goes
through the agent's checks like any other column. A derived variable may
*supersede* a raw one: the raw column is kept as an input but no longer
scored.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .agent import Relationship
from .io import Dataset
from .schema import BODIES, Column, can_convert, convert

# Units the formulas expect, per input concept.
_INPUT_UNITS = {"mean_temperature": "degC", "diurnal_swing": "degC_delta",
                "surface_pressure": "kPa", "wind_speed": "m_per_s"}

TRIPLE_POINT_KPA = 0.6117   # below this pressure liquid water cannot exist


def _daily_high(v, gas_constant):
    return v["mean_temperature"] + v["diurnal_swing"] / 2


def _daily_low(v, gas_constant):
    return v["mean_temperature"] - v["diurnal_swing"] / 2


def _liquid_window(v, gas_constant):
    """Degrees between freezing and boiling at the site's pressure (0 if none).

    Boiling point from the Magnus equation for saturation vapour pressure
    over water, e_s = 0.61094 exp(17.625 T / (T + 243.04)) kPa, inverted.
    """
    p = np.asarray(v["surface_pressure"], float)
    with np.errstate(divide="ignore", invalid="ignore"):
        x = np.log(p / 0.61094)
        boil = 243.04 * x / (17.625 - x)
    return np.where(p > TRIPLE_POINT_KPA, np.clip(boil, 0, None), 0.0) + 0 * p  # keeps NaN where p is NaN


def _thaw_share(v, gas_constant):
    """Share of the day above freezing, assuming a sinusoidal diurnal cycle.

    With mean m and half-swing b, the fraction of the cycle where
    m + b sin(t) > 0 is arccos(-m/b) / pi, clamped to [0, 1].
    """
    m = np.asarray(v["mean_temperature"], float)
    b = np.asarray(v["diurnal_swing"], float) / 2.0
    with np.errstate(divide="ignore", invalid="ignore"):
        frac = np.arccos(np.clip(np.where(b > 0, -m / b, np.sign(-m)), -1, 1)) / np.pi
    return frac


def _wind_pressure(v, gas_constant):
    """Dynamic pressure q = 0.5 rho v^2, with rho = P / (R T) (ideal gas)."""
    p_pa = np.asarray(v["surface_pressure"], float) * 1000.0
    t_k = np.asarray(v["mean_temperature"], float) + 273.15
    speed = np.asarray(v["wind_speed"], float)
    if gas_constant is None:                      # no atmosphere: nothing to push
        return 0.0 * (p_pa + t_k + speed)
    return 0.5 * p_pa / (gas_constant * t_k) * speed**2


@dataclass(frozen=True)
class Derived:
    column: Column
    inputs: tuple[str, ...]            # input concepts
    fn: Callable
    why_supersede: str = ""            # shown on the raw pairing that column.supersedes replaces
    citation: str = ""                 # where the formula comes from; every entry must have one


DERIVED = [
    Derived(Column("daily_high_c", "Typical daily high", "thermal", "temperature", "degC", "daily_high",
                   source="derived", priority=7, formula="mean temperature + half the day-night swing"),
            ("mean_temperature", "diurnal_swing"), _daily_high,
            citation="Arithmetic identity for a periodic signal."),
    Derived(Column("daily_low_c", "Typical daily low", "thermal", "temperature", "degC", "daily_low",
                   source="derived", priority=7, formula="mean temperature - half the day-night swing"),
            ("mean_temperature", "diurnal_swing"), _daily_low,
            citation="Arithmetic identity for a periodic signal."),
    Derived(Column("liquid_window_c", "Liquid-water temperature window", "water", "temperature_delta", "degC_delta",
                   "liquid_water_window", source="derived", priority=7,
                   note="How many degrees above freezing water stays liquid before it boils at the site's pressure.",
                   formula="boiling point from the Magnus equation at surface pressure; 0 below the triple point (0.61 kPa)"),
            ("surface_pressure",), _liquid_window,
            citation="Magnus saturation vapour pressure fit: Alduchov & Eskridge (1996), J. Appl. Meteorol. 35, 601-609."),
    Derived(Column("thaw_share", "Share of the day above freezing", "water", "fraction", "fraction", "thaw_share",
                   source="derived", priority=7,
                   note="How much of a typical day the air sits above 0 degC, so ice or frost could start to melt.",
                   formula="arccos(-mean / half swing) / pi for a sinusoidal day, clamped to [0, 1]"),
            ("mean_temperature", "diurnal_swing"), _thaw_share,
            citation="Exact time-above-threshold of a sinusoid; first-order model of the diurnal temperature cycle."),
    Derived(Column("wind_pressure_pa", "Wind force on surfaces", "dust", "pressure", "Pa", "wind_dynamic_pressure",
                   source="derived", priority=7,
                   note="Dynamic pressure of the wind: what it actually exerts on dust grains, rovers and structures.",
                   formula="0.5 x air density x wind speed squared, with density = pressure / (gas constant x temperature)",
                   supersedes=("wind_speed",)),
            ("surface_pressure", "mean_temperature", "wind_speed"), _wind_pressure,
            why_supersede="Wind speed alone ignores how thin the air is, so the same speed means very different "
                          "forces on different worlds. Sites are compared on wind force instead.",
            citation="Dynamic pressure q = 1/2 rho v^2 with ideal-gas density; standard aerodynamics."),
]


def _by_concept(cols: dict[str, Column], concept: str) -> Column | None:
    return next((c for c in cols.values() if c.concept == concept and c.source != "derived"), None)


def add_derived(ds: Dataset, accepted: list[Relationship], review: dict | None = None) -> list[str]:
    """Add every derived column whose inputs are now validated. Returns log lines.

    `review` is an optional {equation name: {"apply": bool, "caution": str}}
    from a physics reviewer (e.g. a language model). The reviewer can only
    set aside or annotate equations from this library - never add or change
    one - and every set-aside is logged so nothing disappears silently.

    Safe to call repeatedly: columns already present are skipped.
    """
    log = []
    paired = {(ds.target_cols[r.target_col].concept, ds.earth_cols[r.earth_col].concept)
              for r in accepted if r.target_col in ds.target_cols and r.earth_col in ds.earth_cols}
    for d in DERIVED:
        name = d.column.name
        if name in ds.earth_cols:
            continue
        if not all((c, c) in paired for c in d.inputs):
            continue  # an input pairing has not been accepted (yet)
        dec = (review or {}).get(name)
        if dec and not dec.get("apply", True):
            log.append(f"Equation '{name}' set aside by the physics reviewer: "
                       f"{dec.get('caution') or 'no reason given'}")
            continue
        e_in, t_in = {}, {}
        for concept in d.inputs:
            ecol, tcol, unit = _by_concept(ds.earth_cols, concept), _by_concept(ds.target_cols, concept), _INPUT_UNITS[concept]
            if not (ecol and tcol and can_convert(ecol.unit, unit) and can_convert(tcol.unit, unit)):
                break
            e_in[concept] = convert(ds.earth[ecol.name].to_numpy(float), ecol.unit, unit)
            t_in[concept] = convert(ds.targets[tcol.name].to_numpy(float), tcol.unit, unit)
        else:
            ds.earth[name] = d.fn(e_in, BODIES["Earth"]["gas_constant"])
            values = np.full(len(ds.targets), np.nan)
            for i, body in enumerate(ds.targets["body"]):
                if body in BODIES:
                    row = {k: v[i:i + 1] for k, v in t_in.items()}
                    values[i] = np.asarray(d.fn(row, BODIES[body]["gas_constant"]), float).ravel()[0]
            ds.targets[name] = values
            ds.earth_cols[name] = d.column
            ds.target_cols[name] = d.column
            log.append(f"Derived '{name}' ({d.column.label}) from {', '.join(d.inputs)}. [{d.citation}]")
            if dec and dec.get("caution"):
                log.append(f"Physics reviewer note on '{name}': {dec['caution']}")
    return log


def superseded_concepts(ds: Dataset, accepted: list[Relationship]) -> dict[str, str]:
    """concept -> reason, for raw concepts replaced by an accepted derived variable."""
    ok = {r.earth_col for r in accepted}
    return {c: d.why_supersede for d in DERIVED if d.column.name in ok for c in d.column.supersedes}
