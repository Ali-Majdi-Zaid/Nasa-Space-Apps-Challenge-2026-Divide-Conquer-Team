"""Validation against known analogs, and discovery beyond them.

Two questions:

1. Does the engine rank sites that scientists already use as analogs near
   the top, without being told about them? (A sanity check on validity.)
2. Which top-ranked sites are *not* near any known analog? Those are the
   unrecognized candidates the challenge asks for.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .matching import Matcher, haversine_km


def known_analog_benchmark(matcher: Matcher, weights: dict[str, float]) -> pd.DataFrame:
    """For each known analog: its best rank across the targets of its body.

    `percentile` is the share of Earth cells it outranks (100 = top).
    """
    ds = matcher.ds
    rows = []
    for _, k in ds.known.iterrows():
        i = ds.earth.index.get_loc(k["cell_id"])
        best = None
        for tid in ds.targets.index[ds.targets["body"] == k["body"]]:
            raw = matcher.score(tid, weights).total
            if np.isnan(raw).all():
                continue   # nothing testable for this target: no ranking to place the site in
            total = np.nan_to_num(raw, nan=-1.0)
            rank = int((total > total[i]).sum()) + 1
            if best is None or rank < best["rank"]:
                best = dict(cell_id=k["cell_id"], name=k["name"], body=k["body"], best_target=tid,
                            rank=rank, score=float(total[i]),
                            percentile=100.0 * (1 - (rank - 1) / len(total)))
        if best:
            rows.append(best)
    return pd.DataFrame(rows)


def benchmark_summary(bench: pd.DataFrame, n_cells: int) -> dict:
    if bench.empty:
        return dict(n=0)
    top5 = int((bench["rank"] <= max(1, round(0.05 * n_cells))).sum())
    return dict(n=len(bench), in_top_5_percent=top5, median_percentile=float(bench["percentile"].median()),
                # What random ranking would achieve, for comparison.
                expected_by_chance=round(0.05 * len(bench), 2))


def distance_to_known(matcher: Matcher) -> np.ndarray:
    """Distance (km) from every Earth cell to the nearest known analog."""
    ds = matcher.ds
    if ds.known.empty:
        return np.full(len(ds.earth), np.inf)
    k = ds.earth.loc[ds.known["cell_id"]]
    d = haversine_km(ds.earth["lat"].to_numpy()[:, None], ds.earth["lon"].to_numpy()[:, None],
                     k["lat"].to_numpy()[None, :], k["lon"].to_numpy()[None, :])
    return d.min(axis=1)


def unrecognized_candidates(matcher: Matcher, target_id: str, weights: dict[str, float],
                            top_n: int = 10, min_km: float = 500.0) -> pd.DataFrame:
    """Top-scoring cells farther than `min_km` from every known analog."""
    ds = matcher.ds
    total = matcher.score(target_id, weights).total
    far = distance_to_known(matcher) >= min_km
    order = [i for i in np.argsort(-np.nan_to_num(total, nan=-1.0)) if far[i] and not np.isnan(total[i])][:top_n]
    out = ds.earth.iloc[order][["lat", "lon", "region"]].copy()
    out["score"] = total[order]
    return out
