"""Field-campaign routing: the cost-coverage curve.

The test plan answers "what is the smallest set of sites that covers every
testable requirement?". A campaign planner needs one more axis: cost. Two
costs matter and they pull in different directions. Equipment that needs
real set-up (a drill rig, a habitat mock-up) makes every extra site
expensive, so fewer stops win. Portable instruments make travel the cost,
so shorter routes win.

Rather than blending the two with made-up weights, this module keeps them
separate: for each number of sites k = 1, 2, ... it finds the k sites that
cover the most requirements, and among those the shortest route from an
optional starting point. The result is a curve - coverage and kilometres
per stop count - and the reader picks the row that matches their
equipment.
"""
from __future__ import annotations

from itertools import combinations, permutations

import numpy as np

from . import planner
from .matching import Matcher, haversine_km

MAX_SUBSETS = 500_000   # enumeration budget per k; beyond this the search turns greedy


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


def curve(matcher: Matcher, target_id: str, tiebreak: np.ndarray, start: tuple[float, float] | None = None,
          tolerance: float = 1.0, max_sites: int = 5) -> dict:
    """Cost-coverage curve for one target.

    Returns {start, rows: [{k, covered, labels, km, stops}]}, where each row
    is the best k-site campaign: most requirements covered, and among ties
    the shortest route (from `start` if given, else free-floating).
    """
    reqs, _ = planner.requirements(matcher, target_id, tolerance)
    passes = planner.pass_matrix(matcher, reqs)
    lats = matcher.ds.earth["lat"].to_numpy(float)
    lons = matcher.ds.earth["lon"].to_numpy(float)
    ids = matcher.ds.earth.index
    tb = np.nan_to_num(tiebreak, nan=-1.0)
    out = dict(start=list(start) if start else None, rows=[], requirements=[r.label for r in reqs], masks=[],
               scores=[None if np.isnan(v) else round(float(v), 3) for v in np.asarray(tiebreak, dtype=float)],
               profiles=0)   # scores: overall match of each cell (0-1); profiles: distinct pass/fail patterns
    if not reqs:
        return out

    # One representative cell per distinct set of passes. Among cells with the
    # same passes prefer the closest to the start (cheapest to reach), then the
    # best-scoring, so the route search only ever sees useful candidates.
    weights = 1 << np.arange(len(reqs), dtype=object)
    rep: dict[int, int] = {}
    for i, row in enumerate(passes):
        m = int(sum(w for w, ok in zip(weights, row) if ok))
        out["masks"].append(m)   # bit j set when this cell passes requirement j (the map page routes from these)
        if not m:
            continue
        if m not in rep:
            rep[m] = i
        else:
            j = rep[m]
            if start is not None:
                di = haversine_km(start[0], start[1], lats[i], lons[i])
                dj = haversine_km(start[0], start[1], lats[j], lons[j])
                if (di, -tb[i]) < (dj, -tb[j]):
                    rep[m] = i
            elif tb[i] > tb[j]:
                rep[m] = i
    masks = list(rep)
    out["profiles"] = len(masks)
    goal = 0
    for m in masks:
        goal |= m
    max_cover = bin(goal).count("1")

    popcount = lambda m: bin(m).count("1")
    for k in range(1, max_sites + 1):
        best = None   # (covered, -km, order)
        budget = MAX_SUBSETS
        n_cand = 0
        stats: dict[int, list] = {}   # covered -> [how many combos reach it, their two shortest routes]
        for combo in combinations(range(len(masks)), min(k, len(masks))):
            budget -= 1
            if budget < 0:
                break
            n_cand += 1
            union = 0
            for i in combo:
                union |= masks[i]
            covered = popcount(union)
            if best and covered < best[0]:
                continue
            idx = [rep[masks[i]] for i in combo]
            order, km = _best_order(idx, lats, lons, start)
            st = stats.setdefault(covered, [0, []])
            st[0] += 1
            st[1] = sorted(st[1] + [km])[:2]
            if best is None or (covered, -km) > (best[0], -best[1]):
                best = (covered, km, order, union)
        exact = budget >= 0
        if budget < 0:   # greedy fallback: grow the best (k-1)-route by its best extension
            prev = out["rows"][-1] if out["rows"] else None
            # extend the previous row's stops with the cell that adds the most coverage
            have = 0
            stops = [s["index"] for s in (prev["stops"] if prev else [])]
            for s in stops:
                have |= int(sum(w for w, ok in zip(weights, passes[s]) if ok))
            addable = [(popcount(m | have), i) for i, m in enumerate(masks) if rep[m] not in stops]
            if addable:
                _, i = max(addable)
                stops = stops + [rep[masks[i]]]
            order, km = _best_order(stops, lats, lons, start)
            union = 0
            for s in order:
                union |= int(sum(w for w, ok in zip(weights, passes[s]) if ok))
            best = (popcount(union), km, order, union)
            stats = {}
        covered, km, order, union = best
        st = stats.get(covered, [1, [km]])
        runner = st[1][1] if len(st[1]) > 1 else None
        out["rows"].append(dict(
            k=len(order), covered=covered,
            labels=[reqs[j].label for j in range(len(reqs)) if union >> j & 1],
            km=round(km, 0),
            stops=[dict(cell_id=ids[i], index=int(i), lat=round(lats[i], 2), lon=round(lons[i], 2))
                   for i in order],
            # the evidence for "best": every way of choosing k profiles was examined (unless exact is False),
            # `ties` of them reach this coverage, and the next shortest of those is `runner_up_km` long
            candidates=n_cand, ties=int(st[0]), runner_up_km=None if runner is None else round(runner, 0), exact=exact))
        if covered >= max_cover:
            break   # more sites cannot cover more; the curve is complete
    return out
