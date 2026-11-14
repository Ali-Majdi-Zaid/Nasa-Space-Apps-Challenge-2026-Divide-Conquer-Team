"""Sensitivity analysis.

The dimension weights and the pairing confidences are judgment calls, so a
ranking that only holds for one exact choice of them is not evidence. This
module re-scores every cell many times with the weights and confidences
randomly perturbed, and reports how often each site stays in the top K.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .matching import Matcher


def stability(matcher: Matcher, target_id: str, weights: dict[str, float], n_runs: int = 300,
              top_k: int = 10, concentration: float = 30.0, confidence_jitter: float = 0.2,
              seed: int = 0) -> pd.DataFrame:
    """Rank stability under perturbed weights.

    Dimension weights are redrawn from a Dirichlet distribution centred on
    the chosen weights (`concentration` controls how tightly), and each
    pairing's confidence is scaled by a random factor within
    +/- `confidence_jitter`.

    Returns one row per cell that reached the top K at least once:
    `stability` (share of runs in the top K) and the 5th-95th percentile
    of its rank.
    """
    rng = np.random.default_rng(seed)
    used, sims = matcher.similarities(target_id)
    if not used:   # nothing about this target can be tested, so there is no ranking to be stable
        return pd.DataFrame(columns=["stability", "rank_p05", "rank_p95"])
    n = len(matcher.ds.earth)
    dims = [d for d, w in weights.items() if w > 0]
    base = np.array([weights[d] for d in dims], float)
    base = base / base.sum()

    hits = np.zeros(n)
    ranks = np.empty((n_runs, n), dtype=np.int32)
    for r in range(n_runs):
        w = dict(zip(dims, rng.dirichlet(base * concentration)))
        scale = rng.uniform(1 - confidence_jitter, 1 + confidence_jitter, len(used))
        total = matcher.combine(sims, matcher.pair_weights(used, w, scale))
        order = np.argsort(-np.nan_to_num(total, nan=-1.0))
        ranks[r, order] = np.arange(1, n + 1)
        hits[order[:top_k]] += 1

    keep = np.where(hits > 0)[0]
    out = pd.DataFrame({
        "stability": hits[keep] / n_runs,
        "rank_p05": np.percentile(ranks[:, keep], 5, axis=0).astype(int),
        "rank_p95": np.percentile(ranks[:, keep], 95, axis=0).astype(int),
    }, index=matcher.ds.earth.index[keep])
    return out.sort_values("stability", ascending=False)
