"""Shared definitions for EarthMimic.

Nothing in here is tied to a particular dataset. Datasets describe their
own columns in a small JSON metadata file (see README, "Plugging in real
data"); this module only knows about analog dimensions, units, and the
physical rules the agent enforces.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

# The analog dimensions the challenge asks teams to consider.
DIMENSIONS = {
    "terrain": "Terrain and topography",
    "thermal": "Temperature extremes",
    "illumination": "Light and darkness",
    "water": "Water and ice",
    "dust": "Dust and wind",
    "geology": "Geology and surface materials",
    "habitability": "Biology and habitability",
    "physics": "Atmosphere and planetary physics",
}


@dataclass(frozen=True)
class Column:
    """Metadata for one dataset column."""

    name: str
    label: str
    dimension: str          # key of DIMENSIONS
    quantity: str           # physical quantity, e.g. "temperature"
    unit: str
    concept: str = ""       # what is measured, e.g. "ground_ice"; "" if untagged
    comparable: bool = True  # False if tied to an arbitrary reference (a datum)
    priority: int = 5       # agent investigates higher priorities first
    source: str = "dataset"  # "dataset", "physical prior", "computed" or "derived"
    note: str = ""
    uncertainty: float = 0.0  # 1-sigma measurement uncertainty, in this column's unit
    version: str = ""       # dataset name and version, for provenance
    formula: str = ""       # for derived columns: how the value is computed
    valid_min: float | None = None  # overrides the default physical bounds
    valid_max: float | None = None
    supersedes: tuple = ()  # concepts whose raw pairing this (derived) column replaces

    def to_dict(self) -> dict:
        return asdict(self)


def columns_from_meta(meta: list[dict]) -> dict[str, Column]:
    return {m["name"]: Column(**m) for m in meta}


# ---------------------------------------------------------------- units
# (from_unit, to_unit) -> conversion. The agent refuses to pair columns
# whose units differ unless a conversion is registered here.
UNIT_CONVERSIONS = {
    ("K", "degC"): lambda x: x - 273.15,
    ("degC", "K"): lambda x: x + 273.15,
    ("Pa", "kPa"): lambda x: x / 1000.0,
    ("kPa", "Pa"): lambda x: x * 1000.0,
    ("percent", "fraction"): lambda x: x / 100.0,
    ("fraction", "percent"): lambda x: x * 100.0,
    ("km", "m"): lambda x: x * 1000.0,
    ("m", "km"): lambda x: x / 1000.0,
    # A temperature *difference* is the same number in K and degC.
    ("K_delta", "degC_delta"): lambda x: x,
    ("degC_delta", "K_delta"): lambda x: x,
}


_PRETTY_UNITS = {
    "degC": "°C", "degC_delta": "°C", "K_delta": "K", "deg": "°", "fraction": "", "unitless": "",
    "index": "", "m_per_s": "m/s", "per_1000km2": "per 1000 km²", "days_per_year": "days/yr",
    "share_of_year": "% of the year", "mm_per_day": "mm/day", "W_per_m2": "W/m²", "kPa": "kPa", "m": "m",
}


def pretty_unit(unit: str) -> str:
    """Unit as shown to people, e.g. 'degC' -> '°C'."""
    return _PRETTY_UNITS.get(unit, unit)


def fmt(value: float, unit: str) -> str:
    """A value with its unit, e.g. '-58 °C'."""
    u = pretty_unit(unit)
    if unit == "share_of_year":
        return f"{100 * value:.3g}{u}"
    number = f"{value:.3g}"
    return number + (u if u == "°" else f" {u}" if u else "")


def convert_delta(delta: float, from_unit: str, to_unit: str, at: float = 0.0) -> float:
    """Convert a difference (e.g. an uncertainty) rather than an absolute value."""
    return abs(float(convert(at + delta, from_unit, to_unit)) - float(convert(at, from_unit, to_unit)))


def convert(value, from_unit: str, to_unit: str):
    """Convert `value`; raises KeyError if no conversion is registered."""
    if from_unit == to_unit:
        return value
    return UNIT_CONVERSIONS[(from_unit, to_unit)](value)


def can_convert(from_unit: str, to_unit: str) -> bool:
    return from_unit == to_unit or (from_unit, to_unit) in UNIT_CONVERSIONS


# ------------------------------------------------------ concept pairing
# How strongly a target concept is expected to correspond to an Earth
# concept when the names differ. Identical concepts score 1.0. This table
# is what the rule-based proposer uses; an LLM proposer can replace it.
RELATED_CONCEPTS = {
    # Orbital hydrogen measurements mostly trace buried ice at Moon/Mars
    # temperatures, and only loosely trace liquid soil water.
    ("subsurface_water", "ground_ice"): 0.9,
    ("subsurface_water", "soil_moisture"): 0.5,
    # Where on the Moon ice survives within a metre of the surface, against how much of the year
    # Earth's ground is frozen a metre down. Both ask "is ice stable at this depth?", but one is a
    # share of area and the other a share of time, so the pairing is trusted only partly.
    ("shallow_ice_stability", "frozen_ground"): 0.6,
    # The hottest the ground gets in a year vs the mean daily high of the warmest month:
    # both describe the warm extreme, but the second is an average and reads lower.
    ("annual_max_temperature", "warmest_month_high"): 0.6,
}


def concept_prior(target_concept: str, earth_concept: str) -> float:
    if not target_concept or not earth_concept:
        return 0.0  # untagged columns are never paired by the rule proposer
    if target_concept == earth_concept:
        return 1.0
    return RELATED_CONCEPTS.get((target_concept, earth_concept), 0.0)


# ------------------------------------------------- physical plausibility
# Site-level rules. Each rule can veto a pairing for one target site even
# when the pairing is statistically fine. `site` maps concept -> value in
# Earth units for that target.
def _rule_liquid_water(earth_col: Column, site: dict) -> str | None:
    t = site.get("mean_temperature")
    if earth_col.concept == "soil_moisture" and t is not None and t < -10:
        return (f"Liquid soil water cannot persist at the target’s mean "
                f"temperature ({t:.0f} °C), so soil moisture is not a valid stand-in.")
    return None


def _rule_needs_atmosphere(earth_col: Column, site: dict) -> str | None:
    p = site.get("surface_pressure")
    if earth_col.dimension == "dust" and p is not None and p < 0.01:
        return ("The target has no atmosphere, so wind and airborne dust do not "
                "exist there. No Earth site reproduces that.")
    return None


PLAUSIBILITY_RULES = [_rule_liquid_water, _rule_needs_atmosphere]


def plausibility_veto(earth_col: Column, site: dict) -> str | None:
    for rule in PLAUSIBILITY_RULES:
        reason = rule(earth_col, site)
        if reason:
            return reason
    return None


# ------------------------------------------------------------- bodies
# Constants used by derived variables and the illumination model.
BODIES = {
    "Earth": dict(gas_constant=287.05, obliquity_deg=23.44, solar_constant_wm2=1361.0),  # dry air, J/(kg K)
    "Mars": dict(gas_constant=188.92, obliquity_deg=25.19, solar_constant_wm2=586.2),    # CO2 atmosphere; 1361 / 1.524^2
    "Moon": dict(gas_constant=None, obliquity_deg=1.54, solar_constant_wm2=1361.0),      # no atmosphere
}

# ------------------------------------------------- physical value bounds
# Values outside these cannot be real measurements. Keyed by (quantity, unit);
# a column's metadata can override them with valid_min / valid_max.
PHYSICAL_BOUNDS = {
    ("temperature", "K"): (0.0, None),
    ("temperature", "degC"): (-273.15, None),
    ("temperature_delta", "K_delta"): (0.0, None),
    ("temperature_delta", "degC_delta"): (0.0, None),
    ("pressure", "Pa"): (0.0, None),
    ("pressure", "kPa"): (0.0, None),
    ("fraction", "fraction"): (0.0, 1.0),
    ("fraction", "percent"): (0.0, 100.0),
    ("angle", "deg"): (0.0, 90.0),
    ("speed", "m_per_s"): (0.0, None),
    ("duration", "days_per_year"): (0.0, 366.0),
    ("optical_depth", "unitless"): (0.0, None),
    ("areal_density", "per_1000km2"): (0.0, None),
    ("uv_index", "index"): (0.0, None),
    ("ndvi", "unitless"): (-1.0, 1.0),
    ("precipitation_rate", "mm_per_day"): (0.0, None),
}


def bounds_for(col: Column):
    lo, hi = PHYSICAL_BOUNDS.get((col.quantity, col.unit), (None, None))
    return (col.valid_min if col.valid_min is not None else lo,
            col.valid_max if col.valid_max is not None else hi)
