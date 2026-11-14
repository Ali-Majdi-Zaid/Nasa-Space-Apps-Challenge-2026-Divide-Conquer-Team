"""Real-data ingestion.

Downloads three open NASA sources and turns them into the raw data folder
the rest of the pipeline reads (earth_cells.csv, targets.csv and their
metadata). Run it on a machine with internet access:

    python -m earthmimic fetch --out data/real_raw
    python -m earthmimic run --raw data/real_raw --data data/real --out out

Sources, each read according to its published label or API documentation:

Moon    LRO Diviner South Polar Resource Product (PDS, LRO-L-DLRE-5-PRP-V2.0).
        One fixed-width ASCII table, 605 MB, 2.88 million surface triangles
        with modelled annual-average and maximum temperature and the depth
        at which water ice is stable.
Mars    MGS MOLA gridded topography, 16 pixels per degree (PDS,
        MGS-M-MOLA-5-MEGDR-L3-V1.0, megt90n000eb.img). 33 MB of big-endian
        16-bit integers, 2880 lines by 5760 samples, simple cylindrical.
Earth   NASA POWER climatology API (MERRA-2 and CERES long-term means),
        one request per location, no login; and elevation tiles from AWS
        Open Data (built from SRTM and other open elevation models) for
        slope and relief, measured over the same baseline as the Mars grid.
Mars    A few climate values per site (temperature, day-night swing,
climate pressure, wind, dust) entered by hand from the Mars Climate Database
        into sites/mars_climate.csv, because it has no documented data API.

Target sites and Earth locations are listed in editable CSV files (see
`write_default_site_files`). Site values are aggregated over a radius
around each site, never read from a single pixel.

What this does not cover yet: surface composition and mineralogy, radar,
and vegetation. Properties without data on both sides are reported
by the pipeline as having no counterpart; they are never invented.
"""
from __future__ import annotations

import json
import math
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

PDS = "https://pds-geosciences.wustl.edu"
SOURCES = {
    "diviner_prp_south": dict(
        url=f"{PDS}/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_prp/dlre_prp_south.tab",
        file="dlre_prp_south.tab", bytes=604_800_210,
        version="LRO Diviner Polar Resource Product v2 (LRO-L-DLRE-5-PRP-V2.0)"),
    "mola_megt16": dict(
        url=f"{PDS}/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg016/megt90n000eb.img",
        file="megt90n000eb.img", bytes=33_177_600,
        version="MGS MOLA MEGDR 16 px/deg topography (MGS-M-MOLA-5-MEGDR-L3-V1.0)"),
    "grs_h2o": dict(
        url=f"{PDS}/ody/ody-m-grs-5-elements-v1/odgm_xxxx/data/smoothed/h2o_sr_5x5.tab",
        file="h2o_sr_5x5.tab", bytes=186_624,
        version="Mars Odyssey GRS element concentration maps (ODY-M-GRS-5-ELEMENTS-V1.0), smoothed 5x5 deg"),
}
POWER_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
POWER_VERSION = "NASA POWER climatology API (MERRA-2 / CERES long-term means)"

MOON_RADIUS_KM, MARS_RADIUS_KM = 1737.4, 3396.0


# -------------------------------------------------------------- connections
class CertificateProblem(RuntimeError):
    """Python could not verify a server's security certificate."""


_VERIFY_SSL = True


def set_ssl_verification(on: bool) -> None:
    global _VERIFY_SSL
    _VERIFY_SSL = on


def _ssl_context() -> ssl.SSLContext:
    """Best available certificate checking.

    Some servers do not send their full certificate chain. Browsers and the
    operating system fill the gap; Python's default checker does not. The
    `truststore` package makes Python use the operating system's checker.
    """
    if not _VERIFY_SSL:
        return ssl._create_unverified_context()
    try:
        import truststore
        return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except ImportError:
        pass
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _is_certificate_error(err: Exception) -> bool:
    return isinstance(err, ssl.SSLCertVerificationError) or \
        isinstance(getattr(err, "reason", None), ssl.SSLCertVerificationError)


def _open(req: urllib.request.Request, timeout: float, save_as: Path | None = None):
    """urlopen with the best certificate checking and a readable error if it still fails."""
    try:
        return urllib.request.urlopen(req, timeout=timeout, context=_ssl_context())
    except (urllib.error.URLError, ssl.SSLError) as err:
        if not _is_certificate_error(err):
            raise
        host = urllib.parse.urlparse(req.full_url).netloc
        manual = (f"\n  2. Or download the file in your browser from\n       {req.full_url}\n"
                  f"     and save it as\n       {save_as}\n     then run the same command again."
                  if save_as else "")
        raise CertificateProblem(
            f"Python could not verify the security certificate of {host}.\n"
            "This is a problem between Python and the server, not with EarthMimic. To fix it:\n"
            "  1. Run:  python -m pip install truststore\n"
            "     then run the same command again. Python will then check certificates the way Windows does."
            + manual +
            f"\n  {'3' if save_as else '2'}. Last resort: add --no-verify-ssl to the command to skip the check "
            "(the data is public; downloaded file sizes are still verified).") from None


# ------------------------------------------------------------------ download
def download(url: str, dest: Path, expected_bytes: int | None = None, log=print) -> Path:
    """Download `url` to `dest`, resuming a partial file and skipping a complete one."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    have = dest.stat().st_size if dest.exists() else 0
    if expected_bytes and have == expected_bytes:
        log(f"  already downloaded: {dest.name}")
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": "EarthMimic/0.2"})
    if have and expected_bytes and have < expected_bytes:
        req.add_header("Range", f"bytes={have}-")
    else:
        have = 0
    with _open(req, 120, save_as=dest.resolve()) as resp:
        resuming = have and resp.status == 206
        if not resuming:
            have = 0
        total = expected_bytes or (int(resp.headers.get("Content-Length", 0)) + have)
        with open(dest, "ab" if resuming else "wb") as f:
            done, last = have, time.time()
            while chunk := resp.read(1 << 20):
                f.write(chunk)
                done += len(chunk)
                if time.time() - last > 5:
                    log(f"  {dest.name}: {done / 1e6:.0f} of {total / 1e6:.0f} MB")
                    last = time.time()
    if expected_bytes and dest.stat().st_size != expected_bytes:
        raise IOError(f"{dest.name} is {dest.stat().st_size} bytes, expected {expected_bytes}. "
                      "Run the command again to resume the download.")
    return dest


# ---------------------------------------------------------------- site files
# Coordinates are approximate starting points. Check them against the IAU
# Gazetteer of Planetary Nomenclature (Moon) and mission pages (Mars) and
# edit the CSV files; nothing else needs to change.
_MOON_SITES = [
    ("moon-shackleton-rim", "Shackleton crater rim", -89.45, 137.0, 5, "Rim of Shackleton crater near the south pole."),
    ("moon-connecting-ridge", "Shackleton to de Gerlache ridge", -89.45, 222.7, 5, "Sunlit ridge between Shackleton and de Gerlache craters."),
    ("moon-shackleton-floor", "Shackleton crater floor", -89.67, 129.8, 4, "Permanently shadowed crater floor."),
    ("moon-malapert", "Malapert massif", -86.0, 357.1, 8, "High massif with long sunlight and Earth visibility."),
    ("moon-haworth", "Haworth crater", -87.45, 354.8, 10, "Large permanently shadowed crater."),
    ("moon-cabeus", "Cabeus crater", -85.3, 317.9, 10, "Shadowed crater where LCROSS detected water."),
    ("moon-faustini", "Faustini crater", -87.2, 84.3, 10, "Permanently shadowed crater."),
]
_MARS_SITES = [
    ("mars-jezero", "Jezero crater (Perseverance)", 18.44, 77.45, 25, "Ancient river delta in an impact crater."),
    ("mars-gale", "Gale crater (Curiosity)", -4.59, 137.44, 25, "Crater floor at the foot of a layered mountain."),
    ("mars-elysium", "Elysium Planitia (InSight)", 4.50, 135.62, 25, "Smooth volcanic plain."),
    ("mars-chryse", "Chryse Planitia (Viking 1)", 22.27, 312.05, 25, "Outflow-channel plain."),
    ("mars-vastitas", "Vastitas Borealis (Phoenix)", 68.22, 234.25, 25, "High-latitude plain with shallow ground ice."),
    ("mars-arcadia", "Arcadia Planitia", 40.0, 200.0, 25, "Mid-latitude plain with shallow ice; candidate human landing zone."),
]
# Earth sites already used as analogs (approximate coordinates).
_KNOWN_EARTH = [
    ("Atacama Desert", -24.5, -69.25, "Mars"), ("McMurdo Dry Valleys", -77.5, 162.0, "Mars"),
    ("Haughton crater, Devon Island", 75.38, -89.67, "Mars"), ("Askja, Iceland", 65.05, -16.75, "Moon"),
    ("Mauna Kea, Hawaii", 19.82, -155.47, "Mars"), ("Rio Tinto, Spain", 37.72, -6.55, "Mars"),
    ("Utah desert (MDRS)", 38.41, -110.79, "Mars"), ("Dallol, Ethiopia", 14.24, 40.30, "Mars"),
    ("Svalbard", 78.2, 15.6, "Mars"), ("Qaidam Basin", 38.0, 93.0, "Mars"),
]


def write_default_site_files(folder: Path, grid_step: float = 10.0) -> None:
    """Write editable site lists (only where they do not exist yet)."""
    folder.mkdir(parents=True, exist_ok=True)
    cols = ["target_id", "name", "lat", "lon", "radius_km", "description"]
    for name, body, rows in (("moon_sites.csv", "Moon", _MOON_SITES), ("mars_sites.csv", "Mars", _MARS_SITES)):
        if not (folder / name).exists():
            df = pd.DataFrame(rows, columns=cols)
            df.insert(1, "body", body)
            df.to_csv(folder / name, index=False)
    if not (folder / "earth_sites.csv").exists():
        rows = [dict(cell_id=f"K{i:02d}", lat=la, lon=lo, region="", known_analog=n, known_for=b)
                for i, (n, la, lo, b) in enumerate(_KNOWN_EARTH)]
        lats = np.arange(-85, 85.01, grid_step)
        k = 0
        for la in lats:  # fewer longitudes near the poles so cells cover similar areas
            n_lon = max(1, int(round(360 / grid_step * math.cos(math.radians(la)))))
            for lo in np.linspace(-180, 180, n_lon, endpoint=False):
                rows.append(dict(cell_id=f"G{k:04d}", lat=round(float(la), 2), lon=round(float(lo), 2),
                                 region="", known_analog="", known_for=""))
                k += 1
        pd.DataFrame(rows).to_csv(folder / "earth_sites.csv", index=False)


# ----------------------------------------------------------------- geometry
def _distance_km(lat1, lon1, lat2, lon2, radius_km):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return radius_km * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


# ------------------------------------------------------------ Moon: Diviner
# Byte layout from the product label (dlre_prp_south.xml): 210-byte records,
# one header record, 15 ASCII_Real fields. (name, first byte counted from 1, length)
PRP_RECORD_BYTES = 210
PRP_FIELDS = [("tri1_x", 1, 12), ("tri1_y", 15, 12), ("tri1_z", 29, 12), ("tri2_x", 43, 12), ("tri2_y", 57, 12),
              ("tri2_z", 71, 12), ("tri3_x", 85, 12), ("tri3_y", 99, 12), ("tri3_z", 113, 12),
              ("tri_clon", 127, 15), ("tri_clat", 144, 15), ("tri_calt", 161, 15),
              ("temp_avg", 178, 8), ("temp_max", 188, 8), ("ice_depth", 198, 11)]
_PRP_DTYPE = np.dtype({"names": [f[0] for f in PRP_FIELDS], "formats": [f"S{f[2]}" for f in PRP_FIELDS],
                       "offsets": [f[1] - 1 for f in PRP_FIELDS], "itemsize": PRP_RECORD_BYTES})
PRP_ICE_INVALID = -999.0     # "ice not stable within 2.87 m"
SHALLOW_ICE_M = 1.0


def _triangle_slope_deg(c: dict) -> np.ndarray:
    """Slope of each triangle: angle between its normal and the local vertical."""
    v1 = np.column_stack([c["tri1_x"], c["tri1_y"], c["tri1_z"]])
    v2 = np.column_stack([c["tri2_x"], c["tri2_y"], c["tri2_z"]])
    v3 = np.column_stack([c["tri3_x"], c["tri3_y"], c["tri3_z"]])
    normal = np.cross(v2 - v1, v3 - v1)
    up = (v1 + v2 + v3) / 3
    cosang = np.abs((normal * up).sum(axis=1)) / (np.linalg.norm(normal, axis=1) * np.linalg.norm(up, axis=1))
    return np.degrees(np.arccos(np.clip(cosang, -1, 1)))


def read_diviner_prp(path: Path, sites: pd.DataFrame, chunk_records: int = 200_000, log=print) -> pd.DataFrame:
    """Aggregate the Diviner polar resource table over a radius around each site."""
    keep = {tid: [] for tid in sites["target_id"]}
    with open(path, "rb") as f:
        f.seek(PRP_RECORD_BYTES)  # skip the column-heading record
        n = 0
        while raw := f.read(chunk_records * PRP_RECORD_BYTES):
            raw = raw[: len(raw) // PRP_RECORD_BYTES * PRP_RECORD_BYTES]
            rec = np.frombuffer(raw, dtype=_PRP_DTYPE)
            c = {name: rec[name].astype(float) for name, _, _ in PRP_FIELDS}
            slope = _triangle_slope_deg(c)
            for _, s in sites.iterrows():
                d = _distance_km(s["lat"], s["lon"], c["tri_clat"], c["tri_clon"], MOON_RADIUS_KM)
                m = d <= s["radius_km"]
                if m.any():
                    keep[s["target_id"]].append(np.column_stack(
                        [c["temp_avg"][m], c["temp_max"][m], c["ice_depth"][m], c["tri_calt"][m], slope[m]]))
            n += len(rec)
            if n % (5 * chunk_records) == 0:
                log(f"  Diviner table: {n:,} triangles read")
    rows = []
    for _, s in sites.iterrows():
        parts = keep[s["target_id"]]
        if not parts:
            log(f"  warning: no Diviner triangles within {s['radius_km']} km of {s['name']}; values left empty")
            rows.append(dict(target_id=s["target_id"], n_samples=0))
            continue
        a = np.vstack(parts)
        ice = a[:, 2]
        rows.append(dict(
            target_id=s["target_id"], n_samples=len(a),
            surf_temp_mean_K=float(a[:, 0].mean()),
            surf_temp_max_K=float(a[:, 1].max()),
            # Share of the area where water ice is stable within the top metre.
            shallow_ice_share=float(((ice != PRP_ICE_INVALID) & (ice <= SHALLOW_ICE_M)).mean()),
            slope_deg=float(a[:, 4].mean()),
            roughness_deg=float(a[:, 4].std()),
            relief_m=float(a[:, 3].std() * 1000.0),
            elevation_m=float(a[:, 3].mean() * 1000.0),
            surf_pressure_Pa=0.0))   # physical prior: the Moon has no atmosphere
    return pd.DataFrame(rows)


# --------------------------------------------------------------- Mars: MOLA
# From megt90n000eb.lbl: 2880 lines x 5760 samples, MSB_INTEGER 16 bit, metres,
# simple cylindrical, 16 px/deg, latitude 90 to -90, east longitude from 0.
MOLA_LINES, MOLA_SAMPLES, MOLA_PPD = 2880, 5760, 16
MARS_REFERENCE_PA, MARS_SCALE_HEIGHT_M = 610.0, 10_800.0


def read_mola(path: Path, sites: pd.DataFrame, log=print) -> pd.DataFrame:
    """Elevation, slope and relief around each Mars site from the MOLA grid."""
    size = Path(path).stat().st_size
    if size != MOLA_LINES * MOLA_SAMPLES * 2:
        raise IOError(f"{path} is {size} bytes; expected {MOLA_LINES * MOLA_SAMPLES * 2} for the 16 px/deg MOLA grid")
    grid = np.memmap(path, dtype=">i2", mode="r", shape=(MOLA_LINES, MOLA_SAMPLES))
    km_per_px = MARS_RADIUS_KM * math.pi / 180 / MOLA_PPD
    rows = []
    for _, s in sites.iterrows():
        lon = s["lon"] % 360
        half = int(math.ceil(s["radius_km"] / km_per_px)) + 2
        i0 = int((90 - s["lat"]) * MOLA_PPD)
        j0 = int(lon * MOLA_PPD)
        ii = np.clip(np.arange(i0 - half, i0 + half + 1), 0, MOLA_LINES - 1)
        jj = np.arange(j0 - half, j0 + half + 1) % MOLA_SAMPLES          # wraps around 0/360
        z = np.asarray(grid[np.ix_(ii, jj)], dtype=float)
        lat = 90 - (ii + 0.5) / MOLA_PPD
        lon_px = (jj + 0.5) / MOLA_PPD
        dy = km_per_px * 1000.0
        dx = dy * max(math.cos(math.radians(s["lat"])), 0.05)
        gy, gx = np.gradient(z, dy, dx)
        slope = np.degrees(np.arctan(np.hypot(gx, gy)))
        d = _distance_km(s["lat"], lon, lat[:, None], lon_px[None, :], MARS_RADIUS_KM)
        m = d <= s["radius_km"]
        elev = float(z[m].mean())
        rows.append(dict(
            target_id=s["target_id"], n_samples=int(m.sum()),
            slope_deg=float(slope[m].mean()), roughness_deg=float(slope[m].std()),
            relief_m=float(z[m].std()), elevation_m=elev,
            # Estimate, not a measurement: pressure falls off exponentially with height above the datum.
            surf_pressure_Pa=float(MARS_REFERENCE_PA * math.exp(-elev / MARS_SCALE_HEIGHT_M))))
    log(f"  MOLA grid: {len(rows)} sites sampled")
    return pd.DataFrame(rows)


# ------------------------------------------------- Mars: Odyssey GRS water map
GRS_MISSING = 9999.999


def read_grs_h2o(path: Path, sites: pd.DataFrame, log=print) -> pd.DataFrame:
    """Water-equivalent hydrogen (weight fraction) at each Mars site.

    The map is 5x5 degree bins, so this is the regional value around the
    site, not a local measurement. Values sense roughly the top metre.
    """
    a = np.loadtxt(path)                     # lat, east lon, wt%, sigma, sigma with CFS
    rows = []
    for _, s in sites.iterrows():
        lon = s["lon"] % 360
        d = np.abs(a[:, 0] - s["lat"]) + np.abs((a[:, 1] - lon + 180) % 360 - 180)
        best = a[np.argmin(d)]
        val = np.nan if best[2] >= GRS_MISSING else best[2] / 100.0   # weight percent -> fraction
        rows.append(dict(target_id=s["target_id"], subsurface_h2o_share=val))
    log(f"  GRS water map: {sum(1 for r in rows if not np.isnan(r['subsurface_h2o_share']))} of {len(rows)} sites in coverage")
    return pd.DataFrame(rows)


# ------------------------------------------------------------- Earth: POWER
POWER_PARAMETERS = ["TS", "T2M", "T2M_MAX", "T2M_MIN", "T2M_RANGE", "WS10M", "PS", "GWETTOP",
                    "ALLSKY_SFC_UV_INDEX", "PRECTOTCORR", "ALLSKY_SRF_ALB", "AOD_55"]
POWER_FILL = -999.0
_MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def power_url(lat: float, lon: float, parameters: list[str]) -> str:
    query = urllib.parse.urlencode(dict(parameters=",".join(parameters), community="AG",
                                        longitude=f"{lon:.4f}", latitude=f"{lat:.4f}", format="JSON"), safe=",")
    return f"{POWER_URL}?{query}"


def _get_json(url: str, retries: int = 4) -> dict:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EarthMimic/0.2"})
            with _open(req, 60) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as err:
            if err.code in (400, 404, 422):      # a bad request will not get better by retrying
                raise
            last = err
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
            last = err
        time.sleep(2 ** attempt)
    raise IOError(f"NASA POWER request failed after {retries} attempts: {last}")


def parse_power(payload: dict) -> dict:
    """Flatten one POWER climatology reply into {name: value}; fill values become NaN."""
    try:
        params = payload["properties"]["parameter"]
    except (KeyError, TypeError) as err:
        raise ValueError("Unexpected NASA POWER reply: no properties.parameter block. "
                         f"Top-level keys: {list(payload)[:8]}") from err
    out = {}
    for name, months in params.items():
        clean = {k: (np.nan if v is None or float(v) == POWER_FILL else float(v)) for k, v in months.items()}
        monthly = [clean[m] for m in _MONTHS if m in clean and not np.isnan(clean[m])]
        annual = clean.get("ANN", np.nan)
        out[name] = annual if not np.isnan(annual) else (float(np.mean(monthly)) if monthly else np.nan)
        if monthly:
            out[name + "_MONTH_MAX"], out[name + "_MONTH_MIN"] = max(monthly), min(monthly)
    return out


def working_power_parameters(lat: float, lon: float, wanted: list[str], get=_get_json, log=print) -> list[str]:
    """Find which parameter names the service accepts, so one unknown name cannot sink every request."""
    try:
        get(power_url(lat, lon, wanted))
        return list(wanted)
    except urllib.error.HTTPError:
        pass
    ok = []
    for p in wanted:
        try:
            get(power_url(lat, lon, [p]))
            ok.append(p)
        except urllib.error.HTTPError:
            log(f"  NASA POWER does not accept parameter '{p}'; skipped")
    return ok


def fetch_power(sites: pd.DataFrame, cache_dir: Path, get=_get_json, pause: float = 0.3, log=print) -> pd.DataFrame:
    """One climatology request per Earth location, cached on disk so reruns are free."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    params, rows = None, []
    for k, (_, s) in enumerate(sites.iterrows(), 1):
        cache = cache_dir / f"{s['lat']:+.2f}_{s['lon']:+.2f}.json"
        if cache.exists():
            payload = json.loads(cache.read_text(encoding="utf-8"))
        else:
            if params is None:
                params = working_power_parameters(s["lat"], s["lon"], POWER_PARAMETERS, get, log)
            try:
                payload = get(power_url(s["lat"], s["lon"], params))
            except (IOError, urllib.error.HTTPError) as err:
                log(f"  warning: no data for {s['cell_id']} ({err}); left empty")
                rows.append(dict(cell_id=s["cell_id"]))
                continue
            cache.write_text(json.dumps(payload), encoding="utf-8")
            time.sleep(pause)
        rows.append(dict(cell_id=s["cell_id"], **parse_power(payload)))
        if k % 50 == 0:
            log(f"  NASA POWER: {k} of {len(sites)} locations")
    return pd.DataFrame(rows)


# ------------------------------------------------------- Earth: terrain tiles
# Elevation tiles on AWS Open Data ("Terrain Tiles"), built from SRTM and other
# open elevation models. Web Mercator PNG tiles; elevation in metres is
# (red * 256 + green + blue / 256) - 32768.
TERRAIN_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
TERRAIN_VERSION = "Terrain Tiles on AWS Open Data (terrarium; SRTM, GMTED and others)"
EARTH_CIRCUMFERENCE_KM = 40075.016686
TERRAIN_BASELINE_KM = 3.7      # match the MOLA grid spacing so slopes are measured over the same distance
TERRAIN_MAX_LAT = 84.0         # Web Mercator stops near 85 degrees


def _unfilter(rows: bytes, width_bytes: int, bpp: int, height: int) -> bytearray:
    """Undo PNG scanline filtering (filter types 0 to 4)."""
    out, prev, pos = bytearray(), bytearray(width_bytes), 0
    for _ in range(height):
        kind, line = rows[pos], bytearray(rows[pos + 1:pos + 1 + width_bytes])
        pos += 1 + width_bytes
        if kind == 1:
            for i in range(bpp, width_bytes):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif kind == 2:
            for i in range(width_bytes):
                line[i] = (line[i] + prev[i]) & 255
        elif kind == 3:
            for i in range(width_bytes):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif kind == 4:
            for i in range(width_bytes):
                a = line[i - bpp] if i >= bpp else 0
                b, c = prev[i], (prev[i - bpp] if i >= bpp else 0)
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        elif kind != 0:
            raise ValueError(f"unknown PNG filter type {kind}")
        out += line
        prev = line
    return out


def _decode_png_builtin(data: bytes) -> np.ndarray:
    """Minimal PNG reader (8-bit RGB/RGBA/grey, or palette). Returns height x width x 3, uint8."""
    import struct
    import zlib
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file")
    pos, idat, palette, header = 8, b"", None, None
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            palette = np.frombuffer(body, np.uint8).reshape(-1, 3)
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
    w, h, depth, colour, _, _, interlace = header
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(colour)
    if interlace or channels is None or (depth != 8 and colour != 3) or depth > 8:
        raise ValueError(f"unsupported PNG layout (bit depth {depth}, colour type {colour}, interlace {interlace})")
    width_bytes = (w * channels * depth + 7) // 8
    raw = np.frombuffer(bytes(_unfilter(zlib.decompress(idat), width_bytes, max(1, channels * depth // 8), h)),
                        np.uint8).reshape(h, width_bytes)
    if colour == 3:
        idx = raw if depth == 8 else np.unpackbits(raw, axis=1).reshape(h, -1, depth)[:, :w].dot(
            1 << np.arange(depth - 1, -1, -1))
        return palette[idx[:, :w]]
    px = raw.reshape(h, w, channels)
    return np.repeat(px[:, :, :1], 3, axis=2) if colour in (0, 4) else px[:, :, :3]


def decode_png(data: bytes) -> np.ndarray:
    """PNG bytes to a height x width x 3 uint8 array (Pillow if installed, else the built-in reader)."""
    try:
        import io
        from PIL import Image
        return np.asarray(Image.open(io.BytesIO(data)).convert("RGB"))
    except ImportError:
        return _decode_png_builtin(data)


def terrarium_to_metres(rgb: np.ndarray) -> np.ndarray:
    rgb = rgb.astype(float)
    return rgb[:, :, 0] * 256 + rgb[:, :, 1] + rgb[:, :, 2] / 256 - 32768


def _get_bytes(url: str, retries: int = 4) -> bytes:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EarthMimic/0.2"})
            with _open(req, 60) as resp:
                return resp.read()
        except urllib.error.HTTPError as err:
            if err.code in (403, 404):
                raise
            last = err
        except (urllib.error.URLError, TimeoutError) as err:
            last = err
        time.sleep(2 ** attempt)
    raise IOError(f"download failed after {retries} attempts: {last}")


def terrain_zoom(lat: float) -> int:
    """Zoom level whose pixels are closest to TERRAIN_BASELINE_KM on the ground at this latitude."""
    z = math.log2(EARTH_CIRCUMFERENCE_KM * math.cos(math.radians(lat)) / (256 * TERRAIN_BASELINE_KM))
    return int(min(8, max(2, round(z))))


def terrain_stats(lat: float, lon: float, radius_km: float, cache_dir: Path, get_bytes=_get_bytes) -> dict:
    """Mean slope, relief and elevation within `radius_km` of a point on Earth."""
    if abs(lat) > TERRAIN_MAX_LAT:
        return {}
    z = terrain_zoom(lat)
    n = 2 ** z
    px_km = EARTH_CIRCUMFERENCE_KM * math.cos(math.radians(lat)) / (256 * n)
    fx = (lon + 180) / 360 * n * 256                                              # global pixel coordinates
    fy = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n * 256
    half = int(math.ceil(radius_km / px_km)) + 2
    x0, x1, y0, y1 = int(fx) - half, int(fx) + half, max(0, int(fy) - half), min(n * 256 - 1, int(fy) + half)
    tiles = {}
    for ty in range(y0 // 256, y1 // 256 + 1):
        for tx in range(x0 // 256, x1 // 256 + 1):
            name = cache_dir / f"{z}_{tx % n}_{ty}.png"
            if not name.exists():
                cache_dir.mkdir(parents=True, exist_ok=True)
                name.write_bytes(get_bytes(TERRAIN_URL.format(z=z, x=tx % n, y=ty)))
            tiles[(tx, ty)] = terrarium_to_metres(decode_png(name.read_bytes()))
    rows = [np.hstack([tiles[(tx, ty)] for tx in range(x0 // 256, x1 // 256 + 1)]) for ty in range(y0 // 256, y1 // 256 + 1)]
    mosaic = np.vstack(rows)
    oy, ox = (y0 // 256) * 256, (x0 // 256) * 256
    win = mosaic[y0 - oy:y1 - oy + 1, x0 - ox:x1 - ox + 1]
    gy, gx = np.gradient(win, px_km * 1000.0)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
    inside = np.hypot((xx + 0.5 - fx), (yy + 0.5 - fy)) * px_km <= radius_km
    return dict(slope_deg=float(slope[inside].mean()), roughness_deg=float(slope[inside].std()),
                relief_m=float(win[inside].std()), elevation_m=float(win[inside].mean()))


def fetch_terrain(sites: pd.DataFrame, cache_dir: Path, radius_km: float = 25.0, get_bytes=_get_bytes, log=print) -> pd.DataFrame:
    rows = []
    for k, (_, s) in enumerate(sites.iterrows(), 1):
        try:
            rows.append(dict(cell_id=s["cell_id"], **terrain_stats(s["lat"], s["lon"], radius_km, cache_dir, get_bytes)))
        except (IOError, urllib.error.HTTPError, ValueError) as err:
            log(f"  warning: no terrain for {s['cell_id']} ({err}); left empty")
            rows.append(dict(cell_id=s["cell_id"]))
        if k % 50 == 0:
            log(f"  terrain tiles: {k} of {len(sites)} locations")
    return pd.DataFrame(rows)


# -------------------------------------------------- Mars climate (filled by hand)
# The Mars Climate Database (LMD, with ESA and CNES) has a public web interface but no
# documented data API, so these few values per site are entered by hand from it.
MARS_CLIMATE_COLUMNS = ["surf_temp_mean_K", "temp_swing_K", "surf_pressure_Pa", "wind_ms", "dust_tau"]
MARS_CLIMATE_HELP = (
    "# Fill in annual-mean values per site from the Mars Climate Database web interface "
    "(www-mars.lmd.jussieu.fr), then rerun fetch. Leave a cell empty if unknown.\n"
    "# surf_temp_mean_K = surface temperature; temp_swing_K = daily max minus daily min surface temperature; "
    "surf_pressure_Pa = surface pressure; wind_ms = near-surface wind speed; dust_tau = dust column visible optical depth.\n"
    "# Put the database version and scenario you used in the source column.\n")


def write_mars_climate_template(path: Path, mars_sites: pd.DataFrame) -> None:
    if not path.exists():
        df = mars_sites[["target_id", "name"]].copy()
        for c in MARS_CLIMATE_COLUMNS + ["source"]:
            df[c] = ""
        path.write_text(MARS_CLIMATE_HELP + df.to_csv(index=False), encoding="utf-8")


def read_mars_climate(path: Path) -> tuple[pd.DataFrame, str]:
    """Hand-entered Mars climate values, and the source text to cite (empty frame if nothing is filled in)."""
    if not path.exists():
        return pd.DataFrame(), ""
    df = pd.read_csv(path, comment="#")
    for c in MARS_CLIMATE_COLUMNS:
        df[c] = pd.to_numeric(df.get(c), errors="coerce")
    df = df[df[MARS_CLIMATE_COLUMNS].notna().any(axis=1)]
    source = "; ".join(sorted({str(v) for v in df.get("source", pd.Series(dtype=str)).dropna() if str(v).strip()}))
    return df[["target_id"] + MARS_CLIMATE_COLUMNS], source or "Mars Climate Database web interface (version not recorded)"


# ------------------------------------------------------------ assemble folder
def _meta(name, label, dimension, quantity, unit, concept, version, **extra):
    return dict(name=name, label=label, dimension=dimension, quantity=quantity, unit=unit,
                concept=concept, version=version, **extra)


def earth_table(sites: pd.DataFrame, power: pd.DataFrame, terrain: pd.DataFrame | None = None,
                drop_ocean: bool = True) -> tuple[pd.DataFrame, list[dict]]:
    """Earth cells and their metadata from POWER values and terrain tiles."""
    p = power.set_index("cell_id").reindex(sites["cell_id"])
    if terrain is not None and len(terrain):
        p = p.join(terrain.set_index("cell_id").reindex(sites["cell_id"]))
    get = lambda col: p[col].to_numpy(float) if col in p.columns else np.full(len(p), np.nan)
    skin = get("TS")
    out = pd.DataFrame({
        "cell_id": sites["cell_id"].to_numpy(), "lat": sites["lat"].to_numpy(), "lon": sites["lon"].to_numpy(),
        "region": sites.get("region", pd.Series("", index=sites.index)).fillna("").to_numpy(),
        "temp_mean_c": np.where(np.isnan(skin), get("T2M"), skin),
        "warm_month_high_c": get("T2M_MAX_MONTH_MAX"),
        "temp_swing_c": get("T2M_RANGE"),
        "wind_ms": get("WS10M"),
        "pressure_kpa": get("PS"),
        "soil_wetness": get("GWETTOP"),
        "uv_index": get("ALLSKY_SFC_UV_INDEX"),
        "precip_mm_day": get("PRECTOTCORR"),
        "albedo": get("ALLSKY_SRF_ALB"),
        "dust_aod": get("AOD_55"),
        "slope_deg": get("slope_deg"),
        "roughness_deg": get("roughness_deg"),
        "relief_m": get("relief_m"),
        "elevation_m": get("elevation_m"),
    })
    band = lambda la: ("Arctic" if la >= 66.5 else "Antarctic" if la <= -66.5 else "Tropics" if abs(la) < 23.5
                       else "Northern mid-latitudes" if la > 0 else "Southern mid-latitudes")
    out["region"] = [r or band(la) for r, la in zip(out["region"], out["lat"])]
    if drop_ocean and out["soil_wetness"].notna().any():
        # Soil wetness is only defined over land, so a location without it is open water.
        out = out[out["soil_wetness"].notna()].reset_index(drop=True)
    v = POWER_VERSION
    meta = [
        _meta("temp_mean_c", "Mean surface temperature", "thermal", "temperature", "degC", "mean_temperature", v),
        _meta("warm_month_high_c", "Warmest-month daily high", "thermal", "temperature", "degC", "warmest_month_high", v,
              note="Mean daily maximum air temperature of the warmest month."),
        _meta("temp_swing_c", "Day-night temperature swing", "thermal", "temperature_delta", "degC_delta", "diurnal_swing", v),
        _meta("wind_ms", "Mean wind speed at 10 m", "dust", "speed", "m_per_s", "wind_speed", v),
        _meta("pressure_kpa", "Surface pressure", "physics", "pressure", "kPa", "surface_pressure", v),
        _meta("soil_wetness", "Surface soil wetness", "water", "fraction", "fraction", "soil_moisture", v),
        _meta("uv_index", "Surface UV index", "habitability", "uv_index", "index", "uv", v),
        _meta("precip_mm_day", "Precipitation", "water", "precipitation_rate", "mm_per_day", "precipitation", v),
        _meta("albedo", "Surface albedo", "geology", "fraction", "fraction", "albedo", v),
        _meta("dust_aod", "Aerosol optical depth", "dust", "optical_depth", "unitless", "dust_optical_depth", v,
              note="All airborne particles at 550 nm, not dust alone."),
        _meta("slope_deg", "Mean slope", "terrain", "angle", "deg", "slope", TERRAIN_VERSION,
              note=f"Slope over a baseline of about {TERRAIN_BASELINE_KM} km, within 25 km of the location."),
        _meta("roughness_deg", "Terrain roughness", "terrain", "angle", "deg", "slope_variability", TERRAIN_VERSION,
              note="Spread (standard deviation) of slope within 25 km of the location: how broken the ground is, "
                   "as opposed to how steep it is on average."),
        _meta("relief_m", "Relief within the site", "terrain", "length", "m", "relief", TERRAIN_VERSION,
              note="Standard deviation of elevation within 25 km of the location."),
        _meta("elevation_m", "Elevation", "terrain", "length", "m", "elevation", TERRAIN_VERSION, comparable=False,
              note="Measured from sea level."),
    ]
    meta = [m for m in meta if out[m["name"]].notna().any()]
    return out[["cell_id", "lat", "lon", "region"] + [m["name"] for m in meta]], meta


def targets_table(moon_sites, moon, mars_sites, mars, mars_climate=None, climate_source="") -> tuple[pd.DataFrame, list[dict]]:
    measured_pressure = set()
    if mars is not None and mars_climate is not None and len(mars_climate):
        mars = mars.merge(mars_climate, on="target_id", how="left", suffixes=("", "_mcd"))
        if "surf_pressure_Pa_mcd" in mars.columns:   # a database value replaces the estimate from elevation
            measured_pressure = set(mars.loc[mars["surf_pressure_Pa_mcd"].notna(), "target_id"])
            mars["surf_pressure_Pa"] = mars["surf_pressure_Pa_mcd"].fillna(mars["surf_pressure_Pa"])
            mars = mars.drop(columns=["surf_pressure_Pa_mcd"])
    frames = []
    for sites, values in ((moon_sites, moon), (mars_sites, mars)):
        if sites is not None and values is not None and len(values):
            frames.append(sites.drop(columns=["radius_km"]).merge(values.drop(columns=["n_samples"]), on="target_id"))
    t = pd.concat(frames, ignore_index=True)
    dv, mv = SOURCES["diviner_prp_south"]["version"], SOURCES["mola_megt16"]["version"]
    both = f"{dv}; {mv}"
    cs = climate_source
    temp_src = f"{dv}; {cs}" if cs else dv
    meta = [
        _meta("surf_temp_mean_K", "Mean surface temperature", "thermal", "temperature", "K", "mean_temperature", temp_src,
              priority=9, note="Moon: modelled annual average at 2 cm depth." + (" Mars: annual mean from the climate database." if cs else "")),
        _meta("temp_swing_K", "Day-night temperature swing", "thermal", "temperature_delta", "K_delta", "diurnal_swing", cs, priority=8),
        _meta("wind_ms", "Mean wind speed", "dust", "speed", "m_per_s", "wind_speed", cs, priority=6),
        _meta("dust_tau", "Dust optical depth", "dust", "optical_depth", "unitless", "dust_optical_depth", cs, priority=6),
        _meta("surf_temp_max_K", "Annual maximum surface temperature", "thermal", "temperature", "K",
              "annual_max_temperature", dv, priority=8),
        _meta("shallow_ice_share", "Area with ice stable in the top metre", "water", "fraction", "fraction",
              "shallow_ice_stability", dv, priority=9,
              note="Share of the site where water ice would survive within 1 m of the surface."),
        _meta("subsurface_h2o_share", "Water in the shallow subsurface", "water", "fraction", "fraction",
              "subsurface_water", SOURCES["grs_h2o"]["version"], priority=7,
              note="Water-equivalent hydrogen in roughly the top metre, as a weight fraction, from Odyssey "
                   "GRS neutron data. 5x5 degree bins, so a regional value around the site."),
        _meta("slope_deg", "Mean slope", "terrain", "angle", "deg", "slope", both, priority=9,
              note="Moon: slope of the Diviner surface triangles. Mars: slope over a 3.7 km baseline. Baselines differ."),
        _meta("roughness_deg", "Terrain roughness", "terrain", "angle", "deg", "slope_variability", both, priority=7,
              note="Spread (standard deviation) of slope inside the site radius: how broken the ground is. "
                   "Moon: across Diviner surface triangles. Mars: across MOLA grid cells. Baselines differ."),
        _meta("relief_m", "Relief within the site", "terrain", "length", "m", "relief", both, priority=6,
              note="Standard deviation of elevation inside the site radius."),
        _meta("surf_pressure_Pa", "Surface pressure", "physics", "pressure", "Pa", "surface_pressure",
              f"{mv}; {cs}" if measured_pressure else mv, priority=7, uncertainty=90.0,
              note=("Mars: from the climate database where entered, otherwise estimated " if measured_pressure else "Mars: estimated ")
                   + "from MOLA elevation as 610 Pa x exp(-elevation / 10.8 km); it also varies by "
                   "roughly a quarter over the Martian year. Moon: set to 0 (no atmosphere), a physical prior."),
        _meta("elevation_m", "Elevation", "terrain", "length", "m", "elevation", both, priority=1, comparable=False,
              note="Measured from each body’s own reference surface."),
    ]
    meta = [m for m in meta if m["name"] in t.columns and t[m["name"]].notna().any()]
    return t[["target_id", "body", "name", "description", "lat", "lon"] + [m["name"] for m in meta]], meta


def fetch(out_dir: str | Path, config_dir: str | Path | None = None, downloads_dir: str | Path | None = None,
          grid_step: float = 10.0, skip: tuple[str, ...] = (), get=_get_json, get_bytes=_get_bytes,
          pause: float = 0.3, log=print) -> Path:
    """Build a raw data folder from the real sources. Returns the folder."""
    out = Path(out_dir)
    cfg = Path(config_dir) if config_dir else out / "sites"
    dl = Path(downloads_dir) if downloads_dir else out / "downloads"
    out.mkdir(parents=True, exist_ok=True)
    write_default_site_files(cfg, grid_step)
    log(f"Site lists: {cfg} (edit these and rerun to change sites)")

    moon_sites = mars_sites = moon = mars = None
    if "moon" not in skip:
        moon_sites = pd.read_csv(cfg / "moon_sites.csv")
        src = SOURCES["diviner_prp_south"]
        log("Moon: LRO Diviner south polar resource product (605 MB)")
        moon = read_diviner_prp(download(src["url"], dl / src["file"], src["bytes"], log), moon_sites, log=log)
    if "mars" not in skip:
        mars_sites = pd.read_csv(cfg / "mars_sites.csv")
        src = SOURCES["mola_megt16"]
        log("Mars: MOLA 16 px/deg topography (33 MB)")
        mars = read_mola(download(src["url"], dl / src["file"], src["bytes"], log), mars_sites, log=log)
        src = SOURCES["grs_h2o"]
        log("Mars: Odyssey GRS subsurface water map (0.2 MB)")
        grs = read_grs_h2o(download(src["url"], dl / src["file"], src["bytes"], log), mars_sites, log=log)
        mars = mars.merge(grs, on="target_id", how="left")
        write_mars_climate_template(cfg / "mars_climate.csv", mars_sites)
    climate, climate_source = read_mars_climate(cfg / "mars_climate.csv")
    if len(climate):
        log(f"Mars climate: hand-entered values for {len(climate)} sites ({climate_source})")
    elif "mars" not in skip:
        log(f"Mars climate: {cfg / 'mars_climate.csv'} is empty. Fill it in to compare temperature, wind and dust.")
    targets, t_meta = targets_table(moon_sites, moon, mars_sites, mars, climate, climate_source)

    earth_sites = pd.read_csv(cfg / "earth_sites.csv")
    log(f"Earth: NASA POWER climatology for {len(earth_sites)} locations (cached in {dl / 'power'})")
    power = fetch_power(earth_sites, dl / "power", get, pause, log)
    terrain = None
    if "terrain" not in skip:
        land = earth_sites[earth_sites["cell_id"].isin(power.loc[power.get("GWETTOP", pd.Series(dtype=float)).notna(), "cell_id"])] \
            if "GWETTOP" in power.columns and power["GWETTOP"].notna().any() else earth_sites
        log(f"Earth: terrain tiles for {len(land)} land locations (cached in {dl / 'terrain'})")
        terrain = fetch_terrain(land, dl / "terrain", get_bytes=get_bytes, log=log)
    earth, e_meta = earth_table(earth_sites, power, terrain)

    earth.to_csv(out / "earth_cells.csv", index=False)
    targets.to_csv(out / "targets.csv", index=False)
    (out / "earth_meta.json").write_text(json.dumps(e_meta, indent=1), encoding="utf-8")
    (out / "targets_meta.json").write_text(json.dumps(t_meta, indent=1), encoding="utf-8")
    known = earth_sites[earth_sites["known_analog"].fillna("") != ""]
    known = known[known["cell_id"].isin(earth["cell_id"])]
    known.rename(columns={"known_analog": "name", "known_for": "body"})[["cell_id", "name", "body"]].to_csv(
        out / "known_analogs.csv", index=False)
    log(f"Wrote {len(earth)} Earth cells and {len(targets)} target sites to {out}")
    return out
