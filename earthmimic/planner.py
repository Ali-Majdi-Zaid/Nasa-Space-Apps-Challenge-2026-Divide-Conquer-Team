"""Test mode: requirements and the smallest set of sites that covers them.

Science mode asks "how alike is this place overall?". Test mode asks the
question an engineer planning a field campaign asks: "which properties of
the target do I need to reproduce, does a given site reproduce each one
(yes or no), and what is the smallest set of sites that together
reproduces all of them?"

A requirement is a tolerance band around the target value of one property.
A site passes it when its value falls inside the band. No single site
usually passes everything, so the planner finds the minimum number of
sites whose passes, combined, cover every requirement that any Earth site
can pass at all.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from itertools import combinations

import numpy as np

from .matching import Matcher
from .schema import bounds_for

MAX_COMBINATIONS = 2_000_000   # beyond this the exact search hands over to a greedy one


@dataclass
class Requirement:
    target_col: str
    label: str
    earth_col: str
    unit: str
    target: float
    lo: float
    hi: float
    n_pass: int = 0          # how many Earth cells pass it


@dataclass
class Plan:
    requirements: list[Requirement]
    untestable: list[dict]                  # properties no Earth site can reproduce, with reasons
    uncovered: list[int]                    # requirement indices no cell in the data passes
    sites: list[dict] = field(default_factory=list)   # [{cell_id, index, covers: [requirement indices]}]
    best_single: dict | None = None         # the one site that passes the most requirements
    exact: bool = True                      # False if the greedy fallback was used

    def to_dict(self) -> dict:
        return asdict(self)


def requirements(matcher: Matcher, target_id: str, tolerance: float = 1.0) -> tuple[list[Requirement], list[dict]]:
    """Requirements for one target: target value +/- `tolerance` bandwidths per testable property."""
    reqs, untestable = [], []
    for p in matcher.profile(target_id):
        if p.factor > 0:
            half = tolerance * p.bandwidth
            if p.scale == "log":   # a band of ratios around the target
                lo, hi = p.target_value / 10**half, p.target_value * 10**half
            else:
                lo, hi = p.target_value - half, p.target_value + half
            floor, ceil = bounds_for(matcher.ds.earth_cols[p.earth_col])   # never ask for the impossible
            lo = lo if floor is None else max(lo, floor)
            hi = hi if ceil is None else min(hi, ceil)
            reqs.append(Requirement(p.target_col, p.label, p.earth_col, p.unit, p.target_value, lo, hi))
        elif p.status == "breaks_down":
            untestable.append(dict(label=p.label, reason=p.reason))
    return reqs, untestable


def pass_matrix(matcher: Matcher, reqs: list[Requirement]) -> np.ndarray:
    """cells x requirements, True where the cell's value is inside the band. Missing data fails."""
    cols = []
    for r in reqs:
        x = matcher.ds.earth[r.earth_col].to_numpy(float)
        with np.errstate(invalid="ignore"):
            cols.append((x >= r.lo) & (x <= r.hi))
    return np.column_stack(cols) if cols else np.zeros((len(matcher.ds.earth), 0), bool)


def _minimum_cover(masks: list[int], goal: int, max_sites: int):
    """Smallest combination of masks whose union is `goal`. Returns (combos, exact)."""
    budget = MAX_COMBINATIONS
    for k in range(1, max_sites + 1):
        found = []
        for combo in combinations(range(len(masks)), k):
            budget -= 1
            if budget < 0:
                return None, False
            union = 0
            for i in combo:
                union |= masks[i]
            if union == goal:
                found.append(combo)
        if found:
            return found, True
    return None, True


def plan(matcher: Matcher, target_id: str, tiebreak: np.ndarray, tolerance: float = 1.0, max_sites: int = 5) -> Plan:
    """Fewest sites covering every coverable requirement.

    `tiebreak` is an overall score per cell (higher is better), used to
    choose between cells with identical passes and between equally small plans.
    """
    reqs, untestable = requirements(matcher, target_id, tolerance)
    passes = pass_matrix(matcher, reqs)
    for j, r in enumerate(reqs):
        r.n_pass = int(passes[:, j].sum())
    result = Plan(reqs, untestable, [j for j, r in enumerate(reqs) if r.n_pass == 0])
    if not reqs:
        return result

    ids = matcher.ds.earth.index
    tb = np.nan_to_num(tiebreak, nan=-1.0)
    weights = 1 << np.arange(len(reqs), dtype=object)
    cell_mask = [int(sum(w for w, ok in zip(weights, row) if ok)) for row in passes]
    covers = lambda m: [j for j in range(len(reqs)) if m >> j & 1]

    counts = passes.sum(axis=1)
    best = int(np.lexsort((-tb, -counts))[0])
    result.best_single = dict(cell_id=ids[best], index=best, covers=covers(cell_mask[best]))

    # One representative cell per distinct set of passes (the best-scoring one)...
    rep: dict[int, int] = {}
    for i, m in enumerate(cell_mask):
        if m and (m not in rep or tb[i] > tb[rep[m]]):
            rep[m] = i
    # ...and drop sets that are contained in a larger set: they can never be needed.
    masks = [m for m in rep if not any(m != o and m & o == m for o in rep)]
    goal = 0
    for m in masks:
        goal |= m

    combos, exact = _minimum_cover(masks, goal, max_sites)
    if combos:
        chosen = max(combos, key=lambda c: sum(tb[rep[masks[i]]] for i in c))
        picked = [masks[i] for i in chosen]
    else:  # greedy fallback: repeatedly take the set covering the most still-uncovered requirements
        result.exact = False
        picked, left = [], goal
        while left:
            m = max(masks, key=lambda m: (bin(m & left).count("1"), tb[rep[m]]))
            picked.append(m)
            left &= ~m
    picked.sort(key=lambda m: -bin(m).count("1"))
    result.sites = [dict(cell_id=ids[rep[m]], index=rep[m], covers=covers(m)) for m in picked]
    return result
