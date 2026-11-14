// EarthMimic scoring, mirrored from earthmimic/matching.py and
// earthmimic/sensitivity.py so the dashboard can re-score live when the
// weights change. tests/test_earthmimic.py checks both give the same scores.
var EM = (function () {
  "use strict";

  // Pairings of this target that enter the score (match or partial).
  function usedPairs(target) {
    return target.profile.filter(function (p) { return p.factor > 0; });
  }

  // One Float64Array of similarities per used pairing; NaN where Earth has no value.
  function similarities(earthCols, used) {
    return used.map(function (p) {
      var x = earthCols[p.earth_col], out = new Float64Array(x.length);
      for (var i = 0; i < x.length; i++) {
        if (x[i] === null) { out[i] = NaN; continue; }
        var z;
        if (p.scale === "log") {
          if (!(x[i] > 0)) { out[i] = NaN; continue; }
          z = (Math.log10(x[i]) - Math.log10(p.target_value)) / p.bandwidth;
        } else z = (x[i] - p.target_value) / p.bandwidth;
        out[i] = Math.exp(-0.5 * z * z);
      }
      return out;
    });
  }

  // Normalised weight of each used pairing. `scale` optionally jitters confidences.
  function pairWeights(used, weights, scale) {
    var c = used.map(function (p, i) { return p.confidence * p.factor * (scale ? scale[i] : 1); });
    var sumByDim = {};
    used.forEach(function (p, i) { sumByDim[p.dimension] = (sumByDim[p.dimension] || 0) + c[i]; });
    var u = used.map(function (p, i) {
      var s = sumByDim[p.dimension];
      return s > 0 ? (weights[p.dimension] || 0) * c[i] / s : 0;
    });
    var total = u.reduce(function (a, b) { return a + b; }, 0);
    return total > 0 ? u.map(function (v) { return v / total; }) : u;
  }

  // Weighted mean of similarities per cell, skipping missing values.
  function combine(sims, u, minShare) {
    var n = sims.length ? sims[0].length : 0, out = new Float64Array(n);
    for (var i = 0; i < n; i++) {
      var num = 0, have = 0;
      for (var j = 0; j < sims.length; j++) {
        var s = sims[j][i];
        if (s === s) { num += u[j] * s; have += u[j]; }
      }
      out[i] = have >= minShare && have > 0 ? num / have : NaN;
    }
    return out;
  }

  // Per-dimension score of one cell.
  function dimScores(sims, used, i) {
    var num = {}, den = {};
    used.forEach(function (p, j) {
      var s = sims[j][i], c = p.confidence * p.factor;
      if (s === s) {
        num[p.dimension] = (num[p.dimension] || 0) + c * s;
        den[p.dimension] = (den[p.dimension] || 0) + c;
      }
    });
    var out = {};
    Object.keys(den).forEach(function (d) { if (den[d] > 0) out[d] = num[d] / den[d]; });
    return out;
  }

  // Share of the mission's weight Earth can test at all.
  function coverage(profile, weights) {
    var groups = {};
    profile.forEach(function (p) {
      if (p.status === "not_comparable" || p.status === "input_only") return;
      (groups[p.dimension] = groups[p.dimension] || []).push(p.factor);
    });
    var num = 0, den = 0;
    Object.keys(groups).forEach(function (d) {
      var w = weights[d] || 0, f = groups[d];
      den += w;
      num += w * f.reduce(function (a, b) { return a + b; }, 0) / f.length;
    });
    return den > 0 ? num / den : 0;
  }

  // Indices sorted best first; NaN scores last.
  function ranking(total) {
    var idx = Array.from({ length: total.length }, function (_, i) { return i; });
    var key = function (i) { return total[i] === total[i] ? total[i] : -1; };
    idx.sort(function (a, b) { return key(b) - key(a); });
    return idx;
  }

  // ---- seeded random numbers for the sensitivity analysis
  function rng(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function normal(rand) {
    var u = 0, v = 0;
    while (u === 0) u = rand();
    while (v === 0) v = rand();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }
  function gamma(rand, shape) {  // Marsaglia-Tsang
    if (shape < 1) return gamma(rand, shape + 1) * Math.pow(rand() || 1e-12, 1 / shape);
    var d = shape - 1 / 3, c = 1 / Math.sqrt(9 * d);
    for (;;) {
      var x = normal(rand), v = 1 + c * x;
      if (v <= 0) continue;
      v = v * v * v;
      var u = rand() || 1e-12;
      if (Math.log(u) < 0.5 * x * x + d - d * v + d * Math.log(v)) return d * v;
    }
  }

  // Share of perturbed runs in which each cell lands in the top K.
  function stability(sims, used, weights, opts) {
    var rand = rng(opts.seed || 1), n = sims.length ? sims[0].length : 0;
    var hits = new Float64Array(n);
    var dims = Object.keys(weights).filter(function (d) { return weights[d] > 0; });
    var sum = dims.reduce(function (a, d) { return a + weights[d]; }, 0);
    if (!dims.length || !used.length) return hits;
    for (var r = 0; r < opts.n_runs; r++) {
      var w = {}, g = 0;
      dims.forEach(function (d) { w[d] = gamma(rand, opts.concentration * weights[d] / sum); g += w[d]; });
      dims.forEach(function (d) { w[d] /= g; });
      var scale = used.map(function () { return 1 + opts.confidence_jitter * (2 * rand() - 1); });
      var order = ranking(combine(sims, pairWeights(used, w, scale), opts.min_data_share));
      for (var k = 0; k < opts.top_k && k < n; k++) hits[order[k]] += 1;
    }
    for (var i = 0; i < n; i++) hits[i] /= opts.n_runs;
    return hits;
  }

  return { usedPairs: usedPairs, similarities: similarities, pairWeights: pairWeights, combine: combine,
           dimScores: dimScores, coverage: coverage, ranking: ranking, stability: stability };
})();
if (typeof module !== "undefined") module.exports = EM;
