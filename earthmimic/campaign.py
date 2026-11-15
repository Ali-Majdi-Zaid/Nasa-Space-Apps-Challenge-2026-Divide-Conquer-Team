"""Field-campaign routing: the cost-coverage curve.

The test plan answers "what is the smallest set of sites that covers every
testable requirement?". A campaign planner needs one more axis: cost. Two
costs matter and they pull in different directions. Equipment that needs
real set-up (a drill rig, a habitat mock-up) makes every extra site
expensive, so fewer stops win. Portable instruments make travel the cost,
so shorter routes win.

Rather than blending the two with made-up weights, this module keeps them
separate: for each number of sites k = 1, 2, ... it finds the best k-site
campaign and the shortest route through it from an optional starting
point. The result is a curve - coverage and kilometres per stop count -
and the reader picks the row that matches their equipment.

"Best" is decided in this order:

1. most requirements covered (passed by at least one stop);
2. most requirements confirmed (passed by two or more stops, so a result
   at one site can be checked against an independent second site);
3. highest overall match of the stops to the target.

Stops are drawn only from the best-matching Earth sites (the candidate
pool), plus the best-matching site for each requirement so nothing
coverable is lost. A campaign therefore never detours to a poor analog
just because it happens to tick a box, and the curve keeps growing while
an extra stop still covers or confirms something.
"""
from __future__ import annotations

from itertools import combinations, permutations

import numpy as np

from . import planner
from .matching import Matcher, haversine_km

MAX_SUBSETS = 500_000   # enumeration budget per k; beyond this the search turns greedy
POOL_SIZE = 24          # stops are chosen among this many best-matching sites (plus one per requirement)


def _route_km(order, lats, lons, start):
    """Length of the open path start -> order[0] -> ... -> order[-1] (start optional)."""
    km = 0.0
    prev = start
    for i in order:
        if prev is not None:
            km += haversine_km(prev[0], prev[1], lats[i], lons[i])
        prev = (lats[i], lons[i])
    return km


def _best_order(idx, lats, lons, start):
    """Shortest visiting order for up to ~6 sites, by trying every permutation."""
    best, best_km = list(idx), float("inf")
    for perm in permutations(idx):
        km = _route_km(perm, lats, lons, start)
        if km < best_km:
            best, best_km = list(perm), km
    return best, best_km


def candidate_pool(passes: np.ndarray, tb: np.ndarray, size: int = POOL_SIZE) -> list[int]:
    """Cells a campaign may stop at: the best-matching ones that pass something, plus the best passer of each requirement."""
    useful = np.flatnonzero(passes.any(axis=1))
    ranked = sorted(useful, key=lambda i: -tb[i])
    pool = list(ranked[:size])
    for j in range(passes.shape[1]):
        col = [i for i in ranked if passes[i, j]]
        if col and col[0] not in pool:
            pool.append(col[0])
    return [int(i) for i in pool]


def _tally(masks):
    """(requirements passed by at least one mask, requirements passed by two or more), as bit sets."""
    once = twice = 0
    for m in masks:
        twice |= once & m
        once |= m
    return once, twice


def curve(matcher: Matcher, target_id: str, tiebreak: np.ndarray, start: tuple[float, float] | None = None,
          tolerance: float = 1.0, max_sites: int = 5) -> dict:
    """Cost-coverage curve for one target.

    Returns {start, rows: [{k, covered, confirmed, labels, km, legs, mean_score, stops}]}. Each row is the
    best k-site campaign (see the module text for "best"), visited in the shortest order from `start`
    if given, else free-floating.
    """
    reqs, _ = planner.requirements(matcher, target_id, tolerance)
    passes = planner.pass_matrix(matcher, reqs)
    lats = matcher.ds.earth["lat"].to_numpy(float)
    lons = matcher.ds.earth["lon"].to_numpy(float)
    ids = matcher.ds.earth.index
    tb = np.nan_to_num(tiebreak, nan=-1.0)
    out = dict(start=list(start) if start else None, rows=[], requirements=[r.label for r in reqs], masks=[],
               scores=[None if np.isnan(v) else round(float(v), 3) for v in np.asarray(tiebreak, dtype=float)],
               profiles=0, pool=[])   # scores: overall match of each cell (0-1); pool: the cells a campaign may stop at
    if not reqs:
        return out

    weights = 1 << np.arange(len(reqs), dtype=object)
    cell_mask = [int(sum(w for w, ok in zip(weights, row) if ok)) for row in passes]
    out["masks"] = cell_mask   # bit j set when this cell passes requirement j
    pool = candidate_pool(passes, tb)
    out["pool"], out["profiles"] = pool, len(pool)
    if not pool:
        return out
    popcount = lambda m: bin(m).count("1")

    def key(combo):
        once, twice = _tally([cell_mask[i] for i in combo])
        return popcount(once), popcount(twice), sum(tb[i] for i in combo)

    prev_key, chosen = None, []
    for k in range(1, min(max_sites, len(pool)) + 1):
        best, best_key, n_cand, exact = None, None, 0, True
        for combo in combinations(pool, k):
            n_cand += 1
            if n_cand > MAX_SUBSETS:
                exact = False
                break
            kk = key(combo)
            if best_key is None or kk > best_key:
                best, best_key = combo, kk
        if not exact:   # greedy fallback: grow the previous campaign by its best extension
            n_cand = 0
            best = max((tuple(chosen) + (i,) for i in pool if i not in chosen), key=key)
            best_key = key(best)
        # An extra stop must cover or confirm something new; otherwise the curve is complete.
        if prev_key is not None and best_key[:2] <= prev_key[:2]:
            break
        prev_key, chosen = best_key, list(best)
        order, km = _best_order(list(best), lats, lons, start)
        once, twice = _tally([cell_mask[i] for i in order])
        legs, prev = [], start
        for i in order:
            legs.append(None if prev is None else round(float(haversine_km(prev[0], prev[1], lats[i], lons[i])), 0))
            prev = (lats[i], lons[i])
        scores = [float(tb[i]) for i in order if tb[i] >= 0]
        out["rows"].append(dict(
            k=len(order), covered=popcount(once), confirmed=popcount(twice),
            labels=[reqs[j].label for j in range(len(reqs)) if once >> j & 1],
            km=round(km, 0), legs=legs, mean_score=round(sum(scores) / len(scores), 3) if scores else None,
            stops=[dict(cell_id=ids[i], index=int(i), lat=round(lats[i], 2), lon=round(lons[i], 2)) for i in order],
            candidates=n_cand, exact=exact))
    return out
