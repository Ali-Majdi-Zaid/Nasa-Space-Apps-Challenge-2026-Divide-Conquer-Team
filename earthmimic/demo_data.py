"""Synthetic demo data.

EVERYTHING THIS MODULE WRITES IS MADE UP. It exists so the whole pipeline
can be run and inspected before the real datasets arrive. Values are
loosely shaped like real planetary data (cold poles, dry deserts, and so
on) but must never be presented as measurements.

The generator also *plants* a few Earth cells that resemble each target:
some are listed as "known analogs" (to exercise the benchmark) and some
are left unlisted (to check the engine surfaces unrecognized candidates).
The planted cells are recorded in `demo_fixture.json` and used only by
the tests. With real data nothing is planted.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

EARTH_META = [
    dict(name="slope_deg", label="Mean slope", dimension="terrain", quantity="angle", unit="deg", concept="slope"),
    dict(name="roughness_m", label="Surface roughness", dimension="terrain", quantity="length", unit="m", concept="roughness"),
    dict(name="crater_density", label="Crater density", dimension="terrain", quantity="areal_density", unit="per_1000km2", concept="crater_density"),
    dict(name="temp_mean_c", label="Mean surface temperature", dimension="thermal", quantity="temperature", unit="degC", concept="mean_temperature"),
    dict(name="temp_swing_c", label="Day-night temperature swing", dimension="thermal", quantity="temperature_delta", unit="degC_delta", concept="diurnal_swing"),
    dict(name="dark_days", label="Days per year without sunlight", dimension="illumination", quantity="duration", unit="days_per_year", concept="dark_days"),
    dict(name="noon_sun_deg", label="Mean noon sun elevation", dimension="illumination", quantity="angle", unit="deg", concept="noon_sun_elevation"),
    dict(name="ice_fraction", label="Ground ice fraction", dimension="water", quantity="fraction", unit="fraction", concept="ground_ice"),
    dict(name="soil_moisture", label="Soil moisture", dimension="water", quantity="fraction", unit="fraction", concept="soil_moisture"),
    dict(name="wind_ms", label="Mean wind speed", dimension="dust", quantity="speed", unit="m_per_s", concept="wind_speed"),
    dict(name="dust_aod", label="Dust optical depth", dimension="dust", quantity="optical_depth", unit="unitless", concept="dust_optical_depth"),
    dict(name="basalt_fraction", label="Basaltic surface fraction", dimension="geology", quantity="fraction", unit="fraction", concept="basalt"),
    dict(name="fines_fraction", label="Fine-grained surface fraction", dimension="geology", quantity="fraction", unit="fraction", concept="fine_regolith"),
    dict(name="uv_index", label="Surface UV index", dimension="habitability", quantity="uv_index", unit="index", concept="uv"),
    dict(name="ndvi", label="Vegetation index (NDVI)", dimension="habitability", quantity="ndvi", unit="unitless", concept="vegetation"),
    dict(name="pressure_kpa", label="Surface pressure", dimension="physics", quantity="pressure", unit="kPa", concept="surface_pressure"),
    dict(name="elevation_m", label="Elevation", dimension="terrain", quantity="length", unit="m", concept="elevation", comparable=False,
         note="Measured from sea level."),
]

# Target columns deliberately use different names and units from the Earth
# columns (Kelvin, Pascal, percent), the way real mission products do.
TARGET_META = [
    dict(name="slope_deg", label="Mean slope", dimension="terrain", quantity="angle", unit="deg", concept="slope", priority=9),
    dict(name="rms_roughness_m", label="RMS surface roughness", dimension="terrain", quantity="length", unit="m", concept="roughness", priority=8),
    dict(name="craters_per_1000km2", label="Crater density", dimension="terrain", quantity="areal_density", unit="per_1000km2", concept="crater_density", priority=6),
    dict(name="surf_temp_mean_K", label="Mean surface temperature", dimension="thermal", quantity="temperature", unit="K", concept="mean_temperature", priority=9, uncertainty=5.0),
    dict(name="diurnal_amp_K", label="Day-night temperature swing", dimension="thermal", quantity="temperature_delta", unit="K_delta", concept="diurnal_swing", priority=8),
    dict(name="dark_days_per_year", label="Days per year without sunlight", dimension="illumination", quantity="duration", unit="days_per_year", concept="dark_days", priority=8),
    dict(name="noon_sun_elev_deg", label="Mean noon sun elevation", dimension="illumination", quantity="angle", unit="deg", concept="noon_sun_elevation", priority=7),
    dict(name="weh_fraction", label="Water-equivalent hydrogen", dimension="water", quantity="fraction", unit="fraction", concept="subsurface_water", priority=9, uncertainty=0.01),
    dict(name="wind_ms", label="Mean wind speed", dimension="dust", quantity="speed", unit="m_per_s", concept="wind_speed", priority=6),
    dict(name="dust_tau", label="Dust optical depth", dimension="dust", quantity="optical_depth", unit="unitless", concept="dust_optical_depth", priority=6, uncertainty=0.1),
    dict(name="basalt_abundance_pct", label="Basalt abundance", dimension="geology", quantity="fraction", unit="percent", concept="basalt", priority=8),
    dict(name="fines_fraction", label="Fine-grained regolith fraction", dimension="geology", quantity="fraction", unit="fraction", concept="fine_regolith", priority=7),
    dict(name="uv_index", label="Surface UV index", dimension="habitability", quantity="uv_index", unit="index", concept="uv", priority=4),
    dict(name="ndvi", label="Vegetation index (NDVI)", dimension="habitability", quantity="ndvi", unit="unitless", concept="vegetation", priority=5,
         source="physical prior", note="Nothing grows on the Moon or Mars. Declared as 0, not measured."),
    dict(name="surf_pressure_Pa", label="Surface pressure", dimension="physics", quantity="pressure", unit="Pa", concept="surface_pressure", priority=7),
    dict(name="elevation_m", label="Elevation", dimension="terrain", quantity="length", unit="m", concept="elevation", comparable=False, priority=1,
         note="Measured from each body’s own reference datum."),
]

# id, body, name, description, lat, lon, then values in TARGET_META order.
_TARGETS = [
    ("moon-ridge", "Moon", "South-pole ridge", "Sunlit ridge beside permanently shadowed craters; candidate base site.", -89.5, 222.0,
     [14, 3.5, 350, 110, 45, 75, 1.6, 0.02, 0, 0, 15, 0.80, 30, 0, 0, 1500]),
    ("moon-shadow", "Moon", "Shadowed crater floor", "Permanently shadowed floor where water ice may be trapped.", -88.0, 45.0,
     [6, 2.0, 300, 45, 5, 365, 0.0, 0.08, 0, 0, 10, 0.85, 0, 0, 0, -2800]),
    ("moon-mare", "Moon", "Mare lava-tube field", "Basalt plain with pits that may open into lava tubes.", 14.0, 303.0,
     [3, 1.2, 120, 255, 280, 0, 76, 0.002, 0, 0, 95, 0.60, 32, 0, 0, -1900]),
    ("mars-delta", "Mars", "Ancient delta crater", "Dried river delta inside an impact crater; habitability target.", 18.4, 77.6,
     [5, 1.5, 35, 215, 70, 0, 71.6, 0.04, 6, 0.5, 70, 0.45, 22, 0, 700, -2600]),
    ("mars-ice", "Mars", "Mid-latitude ice plain", "Flat plain with shallow buried ice; candidate human landing zone.", 39.8, 202.0,
     [1, 0.4, 12, 200, 55, 0, 50.2, 0.55, 5, 0.4, 50, 0.60, 16, 0, 800, -3900]),
    ("mars-volcano", "Mars", "Volcanic flank with skylights", "Lava flows with collapse pits that may lead to caves.", 1.5, 239.0,
     [4, 2.5, 8, 220, 80, 0, 88.5, 0.01, 8, 0.6, 98, 0.30, 26, 0, 350, 6500]),
]

# Land-ish boxes so the demo map has a recognisable shape.
_BOXES = [
    # name, lat0, lat1, lon0, lon1, weight, aridity bias, elevation bias (m)
    ("North America", 15, 70, -160, -55, 3, 0.00, 0),
    ("South America", -54, 11, -80, -36, 2, -0.05, 0),
    ("Africa", -34, 36, -17, 50, 3, 0.20, 0),
    ("Europe", 36, 70, -10, 40, 1.5, -0.20, 0),
    ("Asia", 8, 75, 40, 145, 4, 0.05, 300),
    ("Australia", -38, -12, 113, 153, 1, 0.25, 0),
    ("Antarctica", -86, -67, -180, 180, 2, 0.30, 1500),
    ("High Arctic", 66, 83, -110, 60, 1.5, 0.20, 200),
]

# (target id, listed as known analog?, name, lat, lon)
_PLANTS = [
    ("moon-ridge", True, "High-Arctic impact structure", 75.4, -89.7),
    ("moon-ridge", False, None, -80.2, 157.0),
    ("moon-ridge", False, None, 80.1, 22.5),
    ("moon-shadow", False, None, -84.5, 63.0),
    ("moon-mare", True, "Volcanic island lava-tube field", 19.5, -155.5),
    ("moon-mare", False, None, 25.4, 39.8),
    ("mars-delta", True, "Hyper-arid coastal plateau", -24.5, -69.3),
    ("mars-delta", False, None, 37.6, 91.5),
    ("mars-delta", False, None, 26.8, 13.4),
    ("mars-ice", True, "Polar dry valley", -77.5, 162.0),
    ("mars-ice", False, None, 71.2, 129.0),
    ("mars-volcano", True, "Sub-Arctic lava field", 64.9, -17.3),
    ("mars-volcano", False, None, 13.6, 40.6),
]
# Variables copied from the target onto a planted cell (when Earth can
# reach the value). Latitude-driven variables are left as generated.
_PLANT_MAP = {
    "slope_deg": "slope_deg", "rms_roughness_m": "roughness_m", "weh_fraction": "ice_fraction",
    "basalt_abundance_pct": "basalt_fraction", "fines_fraction": "fines_fraction", "ndvi": "ndvi",
    "wind_ms": "wind_ms", "dust_tau": "dust_aod", "diurnal_amp_K": "temp_swing_c",
}


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def _physical(rng, lat, arid, volc, elev):
    """Earth-like variables from latitude and a few latent factors."""
    n = len(lat)
    abslat = np.abs(lat)
    temp = 29 - 0.0105 * abslat**2 - 6.0 * elev / 1000 + rng.normal(0, 2.5, n)
    swing = np.clip(6 + 22 * arid + 2 * elev / 1000 + rng.normal(0, 2.5, n), 2, None)
    dark = np.where(abslat > 66.5, np.clip((abslat - 66.5) * 7.2 + rng.normal(0, 4, n), 0, None), 0.0)
    sun = np.clip(90 - abslat + rng.normal(0, 0.5, n), 0, 90)
    ice = _sigmoid(-(temp + 8) / 4) * rng.uniform(0.4, 1.0, n) * (1 - 0.6 * arid)
    moist = np.clip(0.45 * (1 - arid) * _sigmoid((temp + 3) / 3) + rng.normal(0, 0.03, n), 0, 0.6)
    wind = rng.gamma(4, 1.3, n) + np.where(abslat > 66, 2.0, 0.0)
    dust = np.clip(0.04 + 0.5 * arid * _sigmoid(temp / 5) + 0.08 * arid + rng.normal(0, 0.04, n), 0, None)
    basalt = np.clip(volc + rng.normal(0, 0.03, n), 0, 1)
    fines = np.clip(0.25 + 0.4 * arid + rng.normal(0, 0.12, n), 0, 1)
    uv = np.clip(13 * np.cos(np.radians(lat)) * (1 + 0.08 * elev / 1000) + rng.normal(0, 0.6, n), 0, None)
    ndvi = np.clip(0.85 * (1 - arid) ** 1.3 * _sigmoid((temp + 2) / 5) + rng.normal(0, 0.04, n), 0, 0.95)
    pressure = 101.3 * np.exp(-elev / 8400)
    slope = np.clip(rng.gamma(1.6, 4, n), 0, 40)
    rough = 0.2 + 0.18 * slope + rng.gamma(1.5, 0.4, n)
    crater = np.where(rng.random(n) < 0.03, rng.exponential(0.6, n), 0.0)
    return pd.DataFrame({
        "slope_deg": slope, "roughness_m": rough, "crater_density": crater,
        "temp_mean_c": temp, "temp_swing_c": swing, "dark_days": dark, "noon_sun_deg": sun,
        "ice_fraction": ice, "soil_moisture": moist, "wind_ms": wind, "dust_aod": dust,
        "basalt_fraction": basalt, "fines_fraction": fines, "uv_index": uv, "ndvi": ndvi,
        "pressure_kpa": pressure, "elevation_m": elev,
    })


def _on_land(lat, lon):
    """True where a point falls inside the land outlines shipped with the dashboard."""
    path = Path(__file__).resolve().parent.parent / "dashboard" / "land.json"
    rings = json.loads(path.read_text(encoding="utf-8"))["rings"]
    inside = np.zeros(len(lat), bool)
    for ring in rings:
        xs, ys = np.array(ring[0::2]) / 10.0, np.array(ring[1::2]) / 10.0
        for shift in (-360.0, 0.0, 360.0):          # outlines may run past the date line
            x = xs + shift
            if x.max() < -180 or x.min() > 180:
                continue
            hit = np.zeros(len(lat), bool)
            for x0, y0, x1, y1 in zip(x[:-1], ys[:-1], x[1:], ys[1:]):
                if y0 == y1:
                    continue
                cross = ((y0 > lat) != (y1 > lat)) & (lon < x0 + (lat - y0) * (x1 - x0) / (y1 - y0))
                hit ^= cross
            inside ^= hit
    return inside


def _earth_cells(rng, n):
    w = np.array([b[5] for b in _BOXES], float)
    idx = np.empty(0, int); lat = np.empty(0); lon = np.empty(0)
    while len(idx) < n:                              # keep drawing until enough points fall on land
        i = rng.choice(len(_BOXES), size=2 * n, p=w / w.sum())
        la = np.array([rng.uniform(_BOXES[k][1], _BOXES[k][2]) for k in i])
        lo = np.array([rng.uniform(_BOXES[k][3], _BOXES[k][4]) for k in i])
        keep = _on_land(la, lo)
        idx, lat, lon = np.concatenate([idx, i[keep]]), np.concatenate([lat, la[keep]]), np.concatenate([lon, lo[keep]])
    idx, lat, lon = idx[:n], lat[:n], lon[:n]
    region = [_BOXES[i][0] for i in idx]
    arid = np.clip(rng.beta(2, 2, n) + np.array([_BOXES[i][6] for i in idx]), 0, 1)
    volc = rng.beta(0.45, 1.5, n)
    elev = np.clip(rng.gamma(1.5, 500, n) + np.array([_BOXES[i][7] for i in idx]), 0, 5500)
    df = _physical(rng, lat, arid, volc, elev)
    df.insert(0, "region", region)
    df.insert(0, "lon", lon)
    df.insert(0, "lat", lat)
    return df


def _region_of(lat, lon):
    for name, la0, la1, lo0, lo1, *_ in _BOXES:
        if la0 <= lat <= la1 and lo0 <= lon <= lo1:
            return name
    return "Other"


def generate(out_dir: str | Path, n_cells: int = 1500, seed: int = 7) -> Path:
    """Write the demo datasets into `out_dir` and return that path."""
    from .schema import convert  # local import keeps module import cheap

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    earth = _earth_cells(rng, n_cells)
    tcols = [m["name"] for m in TARGET_META]
    tunit = {m["name"]: m["unit"] for m in TARGET_META}
    eunit = {m["name"]: m["unit"] for m in EARTH_META}
    lo, hi = earth.min(numeric_only=True), earth.max(numeric_only=True)

    planted, known_rows = [], []
    for tid, is_known, name, lat, lon in _PLANTS:
        tvals = dict(zip(tcols, next(t for t in _TARGETS if t[0] == tid)[6]))
        arid = 0.85 if tvals["ndvi"] == 0 else 0.5
        cell = _physical(rng, np.array([lat]), np.array([arid]), np.array([0.1]), np.array([600.0]))
        for tcol, ecol in _PLANT_MAP.items():
            v = convert(tvals[tcol], tunit[tcol], eunit[ecol])
            if lo[ecol] <= v <= hi[ecol]:  # only what Earth can actually reach
                spread = 0.04 * (hi[ecol] - lo[ecol])
                cell.loc[0, ecol] = float(np.clip(v + rng.normal(0, spread * 0.3), lo[ecol], hi[ecol]))
        cell.insert(0, "region", _region_of(lat, lon))
        cell.insert(0, "lon", lon)
        cell.insert(0, "lat", lat)
        earth = pd.concat([earth, cell], ignore_index=True)
        planted.append(dict(row=len(earth) - 1, target=tid, known=is_known))
        if is_known:
            known_rows.append(dict(row=len(earth) - 1, name=name,
                                   body=next(t for t in _TARGETS if t[0] == tid)[1], target=tid))

    # A little missing data, as real products always have.
    natural = np.arange(len(earth)) < n_cells  # planted cells stay complete
    for col, frac in (("dust_aod", 0.04), ("basalt_fraction", 0.03), ("fines_fraction", 0.05)):
        earth.loc[natural & (rng.random(len(earth)) < frac), col] = np.nan

    earth.insert(0, "cell_id", [f"E{i:04d}" for i in range(len(earth))])
    for p in planted:
        p["cell_id"] = earth.loc[p.pop("row"), "cell_id"]
    known = pd.DataFrame(known_rows)
    known["cell_id"] = [earth.loc[r, "cell_id"] for r in known.pop("row")]

    targets = pd.DataFrame(
        [dict(target_id=t[0], body=t[1], name=t[2], description=t[3], lat=t[4], lon=t[5], **dict(zip(tcols, t[6])))
         for t in _TARGETS])

    earth.round(4).to_csv(out / "earth_cells.csv", index=False)
    targets.to_csv(out / "targets.csv", index=False)
    known[["cell_id", "name", "body", "target"]].to_csv(out / "known_analogs.csv", index=False)
    stamp = lambda meta: [dict(m, version="synthetic demo v1") for m in meta]
    (out / "earth_meta.json").write_text(json.dumps(stamp(EARTH_META), indent=1), encoding="utf-8")
    (out / "targets_meta.json").write_text(json.dumps(stamp(TARGET_META), indent=1), encoding="utf-8")
    (out / "demo_fixture.json").write_text(json.dumps(planted, indent=1), encoding="utf-8")
    (out / "SYNTHETIC_DATA.txt").write_text(
        "Every value in this folder is synthetic placeholder data generated by\n"
        "earthmimic/demo_data.py. It is not a measurement of Earth, the Moon or Mars.\n", encoding="utf-8")
    return out


def generate_raw(out_dir: str | Path, n_cells: int = 1500, seed: int = 7) -> Path:
    """Write the demo datasets with realistic defects, for the cleaning stage.

    Starts from `generate` and then damages the tables the way real data
    products are damaged: duplicates, sentinel codes, impossible values,
    bad coordinates, text in numeric columns, 0..360 longitudes.
    """
    out = generate(out_dir, n_cells=n_cells, seed=seed)
    rng = np.random.default_rng(seed + 1)
    earth = pd.read_csv(out / "earth_cells.csv")
    planted = {p["cell_id"] for p in json.loads((out / "demo_fixture.json").read_text(encoding="utf-8"))}
    natural = np.array([i for i, c in enumerate(earth["cell_id"]) if c not in planted])
    pick = iter(rng.permutation(natural))
    take = lambda k: [next(pick) for _ in range(k)]

    for col in ("temp_mean_c", "wind_ms", "dust_aod", "uv_index"):
        earth.loc[take(5), col] = -9999.0
    earth.loc[take(4), "ice_fraction"] = 1.7
    earth.loc[take(3), "slope_deg"] = -4.0
    earth.loc[take(2), "temp_mean_c"] = -400.0
    earth.loc[take(4), "lat"] = 123.0
    west = [i for i in take(40) if earth.loc[i, "lon"] < 0][:6]
    earth.loc[west, "lon"] = earth.loc[west, "lon"] + 360
    earth["wind_ms"] = earth["wind_ms"].astype(object)
    earth.loc[take(2), "wind_ms"] = "ERR"

    exact = earth.loc[take(12)]
    clash = earth.loc[take(5)].copy()
    clash["slope_deg"] = clash["slope_deg"] + 0.4
    earth = pd.concat([earth, exact, clash], ignore_index=True)
    earth.to_csv(out / "earth_cells.csv", index=False)

    targets = pd.read_csv(out / "targets.csv")
    pd.concat([targets, targets.iloc[[1]]], ignore_index=True).to_csv(out / "targets.csv", index=False)
    return out
