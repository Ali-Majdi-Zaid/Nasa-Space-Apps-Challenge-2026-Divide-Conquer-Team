"""Matching engine.

For one target site and one set of dimension weights, score every Earth
cell from 0 (nothing alike) to 1 (indistinguishable on everything that can
be tested), and say exactly which properties were tested, which only
partly, and where the analogy breaks down.

Scoring, for target value t and Earth value x of one accepted pairing:

    similarity = exp(-0.5 * ((x - t) / bandwidth)^2)

Each pairing's weight is

    dimension weight * confidence * site factor / (sum of confidence * site factor in its dimension)

so a dimension's influence is set by its weight alone, however many
variables it happens to contain. A cell's score is the weighted mean of
its similarities over the pairings it has data for.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict

import numpy as np

from .agent import AgentResult, Relationship, target_value_in_earth_units
from .io import Dataset
from .schema import can_convert, convert, convert_delta, fmt, plausibility_veto

EDGE_TOLERANCE = 1.0     # how far beyond Earth's range (in sigmas) still counts as "partial"
PARTIAL_FACTOR = 0.5     # weight multiplier for partial pairings
MIN_DATA_SHARE = 0.5     # a cell needs data for at least this share of the weight

# Units the plausibility rules expect.
_RULE_UNITS = {"mean_temperature": "degC", "surface_pressure": "kPa"}


@dataclass
class SitePair:
    """How one target column fares at one target site."""

    target_col: str
    label: str
    dimension: str
    status: str                 # match | partial | breaks_down | not_tested | not_comparable | input_only
    reason: str = ""
    rel_id: str = ""
    earth_col: str = ""
    earth_label: str = ""
    unit: str = ""
    target_value: float | None = None   # in Earth units
    confidence: float = 0.0
    bandwidth: float = 0.0
    factor: float = 0.0                 # 1 match, 0.5 partial, 0 otherwise
    scale: str = "linear"               # "log": similarity uses log10 of the values; bandwidth is in log10 units
    uncertainty: float = 0.0            # target measurement uncertainty, in Earth units
    source: str = "dataset"             # dataset | physical prior | computed | derived
    formula: str = ""
    alternates: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ScoreResult:
    total: np.ndarray                   # one score per Earth cell (NaN if too little data)
    dims: dict[str, np.ndarray]         # per-dimension scores
    sims: np.ndarray                    # cells x used pairings
    used: list[SitePair]                # pairings that entered the score
    pair_weights: np.ndarray            # weight of each used pairing (sums to 1)
    coverage: float                     # share of the mission's weight Earth can test


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


class Matcher:
    def __init__(self, dataset: Dataset, agent_result: AgentResult):
        self.ds = dataset
        self.rels = agent_result.relationships
        self._profiles: dict[str, list[SitePair]] = {}
        self._sims: dict[str, np.ndarray] = {}

    # ------------------------------------------------------- site profile
    def _site_concepts(self, target_id: str) -> dict:
        out = {}
        for col in self.ds.target_cols.values():
            unit = _RULE_UNITS.get(col.concept)
            v = self.ds.targets.loc[target_id, col.name]
            if unit and can_convert(col.unit, unit) and not np.isnan(v):
                out[col.concept] = float(convert(v, col.unit, unit))
        return out

    def _evaluate(self, rel: Relationship, target_id: str, concepts: dict):
        """Status of one accepted pairing at one site: (status, reason, value, uncertainty)."""
        raw = self.ds.targets.loc[target_id, rel.target_col]
        if np.isnan(raw):
            return "not_tested", "The target dataset has no value for this site.", None, 0.0
        tcol, ecol = self.ds.target_cols[rel.target_col], self.ds.earth_cols[rel.earth_col]
        value = target_value_in_earth_units(self.ds, rel, target_id)
        unc = convert_delta(tcol.uncertainty, tcol.unit, ecol.unit, at=raw) if tcol.uncertainty else 0.0
        veto = plausibility_veto(ecol, concepts)
        if veto:
            return "breaks_down", veto, value, unc
        lo, hi, unit = rel.earth_lo, rel.earth_hi, ecol.unit
        span = f"{fmt(lo, unit)} to {fmt(hi, unit)}"
        v, unc_t = value, unc
        if rel.scale == "log":
            if value <= 0:
                return "breaks_down", (f"The target value is {fmt(value, unit)}, but on Earth this is never zero "
                                       f"({span}). No Earth site reproduces it."), value, unc
            v, lo, hi, unc_t = np.log10(value), np.log10(lo), np.log10(hi), np.log10(1 + unc / value)
        # A measurement uncertainty widens what counts as "within reach".
        tol = EDGE_TOLERANCE * rel.sigma + unc_t
        if lo <= v <= hi:
            return "match", "", value, unc
        if lo - tol <= v <= hi + tol:
            return "partial", (f"The target value ({fmt(value, unit)}) is just beyond anything on Earth "
                               f"({span}). The most extreme Earth sites count at half weight."), value, unc
        return "breaks_down", (f"The target value ({fmt(value, unit)}) is far outside Earth’s range "
                               f"({span}). No Earth site reproduces it."), value, unc

    def profile(self, target_id: str) -> list[SitePair]:
        """One entry per target column: tested, partly tested, or why not."""
        if target_id in self._profiles:
            return self._profiles[target_id]
        concepts = self._site_concepts(target_id)
        out = []
        for tcol in self.ds.target_cols.values():
            rels = [r for r in self.rels if r.target_col == tcol.name]
            accepted = sorted((r for r in rels if r.verdict == "accepted" and r.scored), key=lambda r: -r.confidence)
            entry = SitePair(tcol.name, tcol.label, tcol.dimension, "breaks_down", source=tcol.source, formula=tcol.formula)
            if not accepted:
                last = lambda r, kinds: next((c.detail for c in reversed(r.checks) if c.outcome in kinds), "")
                inputs = [r for r in rels if r.verdict == "accepted"]
                waiting = [r for r in rels if r.verdict == "pending"]
                if inputs:
                    entry.status, entry.reason = "input_only", last(inputs[0], ("warn",))
                elif waiting:
                    entry.status, entry.reason = "not_tested", last(waiting[0], ("warn",))
                else:
                    entry.status = "not_comparable"
                    entry.reason = next((last(r, ("fail",)) for r in rels if last(r, ("fail",))), "No valid Earth counterpart.")
                out.append(entry)
                continue
            # Take the most trusted pairing that survives at this site.
            evaluated = [(r, *self._evaluate(r, target_id, concepts)) for r in accepted]
            chosen = next((ev for ev in evaluated if ev[1] in ("match", "partial")), evaluated[0])
            rel, status, reason, value, unc = chosen
            ecol = self.ds.earth_cols[rel.earth_col]
            entry.status, entry.reason, entry.target_value = status, reason, value
            entry.rel_id, entry.earth_col, entry.earth_label, entry.unit = rel.id, rel.earth_col, ecol.label, ecol.unit
            entry.confidence, entry.uncertainty, entry.scale = rel.confidence, unc, rel.scale
            unc_t = np.log10(1 + unc / value) if rel.scale == "log" and value is not None and value > 0 else unc
            entry.bandwidth = float(np.hypot(rel.bandwidth, unc_t))
            entry.factor = {"match": 1.0, "partial": PARTIAL_FACTOR}.get(status, 0.0)
            entry.alternates = [
                f"{self.ds.earth_cols[r.earth_col].label}: " + (rs or "valid, but a less trusted pairing")
                for r, st, rs, _, _ in evaluated if r is not rel]
            out.append(entry)
        self._profiles[target_id] = out
        return out

    # ------------------------------------------------------------ scoring
    def similarities(self, target_id: str):
        """(used pairings, cells x pairings similarity matrix). Independent of weights."""
        used = [p for p in self.profile(target_id) if p.factor > 0]
        if target_id not in self._sims:
            cols = []
            for p in used:
                x, t = self.ds.earth[p.earth_col].to_numpy(float), p.target_value
                if p.scale == "log":
                    with np.errstate(divide="ignore", invalid="ignore"):
                        x, t = np.where(x > 0, np.log10(x), np.nan), np.log10(t)
                cols.append(np.exp(-0.5 * ((x - t) / p.bandwidth) ** 2))
            self._sims[target_id] = np.column_stack(cols) if cols else np.zeros((len(self.ds.earth), 0))
        return used, self._sims[target_id]

    @staticmethod
    def pair_weights(used: list[SitePair], weights: dict[str, float], confidence_scale=None) -> np.ndarray:
        """Normalised weight of each used pairing under `weights`."""
        c = np.array([p.confidence * p.factor for p in used], float)
        if confidence_scale is not None:
            c = c * confidence_scale
        dims = [p.dimension for p in used]
        u = np.zeros(len(used))
        for d in set(dims):
            idx = [i for i, x in enumerate(dims) if x == d]
            if c[idx].sum() > 0:
                u[idx] = weights.get(d, 0.0) * c[idx] / c[idx].sum()
        return u / u.sum() if u.sum() > 0 else u

    @staticmethod
    def combine(sims: np.ndarray, u: np.ndarray) -> np.ndarray:
        """Weighted mean of similarities, skipping missing values."""
        valid = ~np.isnan(sims)
        have = valid @ u
        with np.errstate(invalid="ignore", divide="ignore"):
            total = (np.where(valid, sims, 0.0) @ u) / have
        total[have < MIN_DATA_SHARE] = np.nan
        return total

    def coverage(self, target_id: str, weights: dict[str, float]) -> float:
        """Share of the mission's weight that Earth can test at all."""
        prof = [p for p in self.profile(target_id) if p.status not in ("not_comparable", "input_only")]
        num = den = 0.0
        for d in {p.dimension for p in prof}:
            members = [p for p in prof if p.dimension == d]
            w = weights.get(d, 0.0)
            den += w
            num += w * sum(p.factor for p in members) / len(members)
        return num / den if den > 0 else 0.0

    def score(self, target_id: str, weights: dict[str, float]) -> ScoreResult:
        used, sims = self.similarities(target_id)
        u = self.pair_weights(used, weights)
        dims = {}
        for d in {p.dimension for p in used}:
            idx = [i for i, p in enumerate(used) if p.dimension == d]
            c = np.zeros(len(used))
            c[idx] = [used[i].confidence * used[i].factor for i in idx]
            valid = ~np.isnan(sims)
            have = valid @ c
            with np.errstate(invalid="ignore", divide="ignore"):
                dims[d] = np.where(have > 0, (np.where(valid, sims, 0.0) @ c) / have, np.nan)
        return ScoreResult(self.combine(sims, u), dims, sims, used, u, self.coverage(target_id, weights))

    def single(self, target_id: str, target_col: str) -> np.ndarray:
        """Single-property mode: similarity on one property only."""
        used, sims = self.similarities(target_id)
        for j, p in enumerate(used):
            if p.target_col == target_col:
                return sims[:, j].copy()
        raise KeyError(f"'{target_col}' is not testable on Earth for target '{target_id}'")

    def top(self, target_id: str, weights: dict[str, float], n: int = 10):
        res = self.score(target_id, weights)
        order = np.argsort(-np.nan_to_num(res.total, nan=-1.0))[:n]
        return res, order

    def explain(self, target_id: str, cell_id: str, weights: dict[str, float]) -> dict:
        """Everything behind one Earth cell's score for one target."""
        res = self.score(target_id, weights)
        i = self.ds.earth.index.get_loc(cell_id)
        used_ids = [p.target_col for p in res.used]
        rows = []
        for p in self.profile(target_id):
            row = dict(property=p.label, dimension=p.dimension, status=p.status, reason=p.reason,
                       target=p.target_value, unit=p.unit, site=None, similarity=None, weight=0.0)
            if p.target_col in used_ids:
                j = used_ids.index(p.target_col)
                x = self.ds.earth.iloc[i][p.earth_col]
                row.update(site=None if np.isnan(x) else float(x),
                           similarity=None if np.isnan(res.sims[i, j]) else float(res.sims[i, j]),
                           weight=float(res.pair_weights[j]))
            rows.append(row)
        return dict(cell_id=cell_id, score=float(res.total[i]),
                    dimensions={d: float(v[i]) for d, v in res.dims.items()}, properties=rows)
