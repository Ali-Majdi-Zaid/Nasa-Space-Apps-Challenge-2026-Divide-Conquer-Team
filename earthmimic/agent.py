"""Relationship agent.

The agent answers one question: which column of the Moon/Mars dataset is
*actually* comparable with which column of the Earth dataset?

It works in two stages.

1. A proposer suggests candidate pairings. The built-in `RuleProposer`
   uses the concept tags in the metadata. `LLMProposer` asks a language
   model instead. Proposals are only suggestions.
2. Every proposal is validated by deterministic checks that the proposer
   cannot influence. Metadata checks are free. Checks that read the data
   cost one tool call per pairing, and a run stops when its budget (15 by
   default) is spent. Acceptance is automatic: there is no human approval
   step.

Every pairing ends in one of three states:

    accepted  passed every check; may be used for matching
    denied    failed a check that more data cannot fix
    pending   not enough evidence yet (too little data, or the budget ran
              out); re-checked first on the next run

Results are kept in a relationship store (see store.py). A pairing whose
data and metadata have not changed since it was last decided is reused
from the store without spending a tool call.

Each pairing is a `Relationship` record - the "relationship card" shown
in the dashboard - listing every check and its outcome.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Callable, Protocol

import numpy as np

from .io import Dataset
from .schema import Column, can_convert, concept_prior, convert, fmt

MAX_MISSING = 0.30          # Earth columns with more missing data than this stay pending
MIN_VALUES = 30             # fewer Earth values than this is not enough evidence
LOG_RATIO = 50.0            # positive columns spanning more than this ratio are compared on a log scale
CHECKS_VERSION = "3"        # bump when the checks change, so stored results are re-validated
REDUNDANT_RHO = 0.90        # |Spearman| above this counts as the same signal
BANDWIDTH_FACTOR = 0.75     # similarity bandwidth, in robust standard deviations


@dataclass
class Proposal:
    target_col: str
    earth_col: str
    prior: float            # proposer's belief the pairing is meaningful, 0..1
    rationale: str


@dataclass
class Check:
    name: str
    outcome: str            # "pass", "warn" or "fail"
    detail: str


@dataclass
class Relationship:
    id: str
    target_col: str
    earth_col: str
    dimension: str
    verdict: str            # "accepted", "denied" or "pending"
    confidence: float = 0.0
    rationale: str = ""
    conversion: str = ""    # e.g. "K -> degC"
    bandwidth: float = 0.0  # similarity bandwidth in Earth units
    sigma: float = 0.0      # robust spread of the Earth column
    earth_lo: float = 0.0   # 0.5th percentile of the Earth column
    earth_hi: float = 0.0   # 99.5th percentile
    scale: str = "linear"   # "log" when values span orders of magnitude; sigma and bandwidth are then in log10 units
    checks: list[Check] = field(default_factory=list)
    scored: bool = True     # False when kept only as an input to a derived variable
    origin: str = "checked" # "checked" this run, or "reused" from the store
    decided_in_run: int = 0
    pending_reason: str = ""  # "budget" or "evidence"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Relationship":
        d = dict(d)
        d["checks"] = [Check(**c) for c in d.get("checks", [])]
        return cls(**d)


class Proposer(Protocol):
    def propose(self, target_cols: dict[str, Column], earth_cols: dict[str, Column]) -> list[Proposal]: ...


class RuleProposer:
    """Pairs columns whose concept tags are identical or registered as related."""

    def propose(self, target_cols, earth_cols):
        out = []
        for t in target_cols.values():
            for e in earth_cols.values():
                prior = concept_prior(t.concept, e.concept)
                if prior > 0:
                    why = ("Both columns measure the same thing." if prior == 1.0 else
                           f"'{t.concept}' is registered as related to '{e.concept}' (prior {prior:.1f}).")
                    out.append(Proposal(t.name, e.name, prior, why))
        return out


class LLMProposer:
    """Asks a language model which columns correspond.

    `complete` is any function that takes a prompt string and returns the
    model's text reply, so this works with whichever provider you use.
    The model must answer with JSON; anything it gets wrong (unknown
    columns, mismatched quantities) is caught by the agent's checks.
    """

    PROMPT = (
        "You are pairing columns between two planetary datasets.\n"
        "Target (Moon/Mars) columns:\n{targets}\n\nEarth columns:\n{earth}\n\n"
        "List every pair of columns that measure the same physical property, or where the Earth "
        "column is a defensible stand-in for the target column. Reply with JSON only: a list of "
        'objects {{"target_col": str, "earth_col": str, "prior": number between 0 and 1, '
        '"rationale": one sentence}}.'
    )

    def __init__(self, complete: Callable[[str], str]):
        self.complete = complete

    @staticmethod
    def _describe(cols):
        return "\n".join(f"- {c.name}: {c.label} [{c.unit}] {c.note}".rstrip() for c in cols.values())

    def propose(self, target_cols, earth_cols):
        reply = self.complete(self.PROMPT.format(targets=self._describe(target_cols),
                                                 earth=self._describe(earth_cols)))
        text = reply.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        out = []
        for item in json.loads(text):
            try:
                prior = min(1.0, max(0.0, float(item.get("prior", 0.5))))
                out.append(Proposal(str(item["target_col"]), str(item["earth_col"]), prior,
                                    str(item.get("rationale", ""))))
            except (KeyError, TypeError, ValueError):
                continue  # a malformed entry is simply not a proposal
        return out


@dataclass
class AgentResult:
    relationships: list[Relationship]
    tool_calls_used: int
    max_tool_calls: int
    log: list[str]
    run: int = 0

    def accepted(self) -> list[Relationship]:
        return [r for r in self.relationships if r.verdict == "accepted"]

    def waiting_on_budget(self) -> bool:
        return any(r.verdict == "pending" and r.pending_reason == "budget" for r in self.relationships)


def robust_sigma(x: np.ndarray) -> float:
    """Spread that ignores outliers; falls back for zero-heavy columns."""
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return 0.0
    q25, q75 = np.percentile(x, [25, 75])
    s = (q75 - q25) / 1.349
    if s <= 0:
        s = float(np.std(x))
    return float(s)


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    ok = ~(np.isnan(a) | np.isnan(b))
    if ok.sum() < 10:
        return 0.0
    ra = np.argsort(np.argsort(a[ok])).astype(float)
    rb = np.argsort(np.argsort(b[ok])).astype(float)
    if ra.std() == 0 or rb.std() == 0:
        return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


class RelationshipAgent:
    def __init__(self, dataset: Dataset, proposer: Proposer | None = None, max_tool_calls: int = 15):
        self.ds = dataset
        self.proposer = proposer or RuleProposer()
        self.max_tool_calls = max_tool_calls

    def fingerprint(self, target_col: str, earth_col: str) -> str:
        """Changes whenever the data or metadata behind a pairing changes."""
        h = hashlib.sha1(CHECKS_VERSION.encode())
        t, e = self.ds.target_cols[target_col], self.ds.earth_cols[earth_col]
        h.update(json.dumps([t.to_dict(), e.to_dict()], sort_keys=True).encode())
        h.update(np.round(self.ds.earth[earth_col].to_numpy(float), 6).tobytes())
        h.update(np.round(self.ds.targets[target_col].to_numpy(float), 6).tobytes())
        return h.hexdigest()

    # ------------------------------------------------------------ stage 1
    def _screen(self, p: Proposal) -> Relationship:
        """Metadata-only checks. These never touch the data and are free."""
        rid = f"{p.target_col}__{p.earth_col}"
        t, e = self.ds.target_cols.get(p.target_col), self.ds.earth_cols.get(p.earth_col)
        rel = Relationship(rid, p.target_col, p.earth_col, t.dimension if t else "", "denied",
                           rationale=p.rationale)
        if t is None or e is None:
            missing = p.target_col if t is None else p.earth_col
            rel.checks.append(Check("Columns exist", "fail", f"Column '{missing}' is not in the dataset."))
            return rel
        rel.checks.append(Check("Columns exist", "pass", "Both columns are present in the datasets."))

        if not (t.comparable and e.comparable):
            which = t if not t.comparable else e
            rel.checks.append(Check("Comparable across bodies", "fail",
                                    f"{which.label} depends on a local reference. {which.note}".strip()))
            return rel
        rel.checks.append(Check("Comparable across bodies", "pass", "Neither column depends on a local reference."))

        if t.quantity != e.quantity:
            rel.checks.append(Check("Same physical quantity", "fail",
                                    f"Target is a {t.quantity}; Earth column is a {e.quantity}."))
            return rel
        rel.checks.append(Check("Same physical quantity", "pass", f"Both are a {t.quantity}."))

        if t.concept and e.concept:
            table = concept_prior(t.concept, e.concept)
            if table == 0:
                rel.checks.append(Check("Concepts agree", "fail",
                                        f"The columns are tagged as different things ('{t.concept}' and "
                                        f"'{e.concept}') with no registered relation between them."))
                return rel
            p.prior = min(p.prior, table)  # a proposer cannot claim more than the registry allows

        if not can_convert(t.unit, e.unit):
            rel.checks.append(Check("Units", "fail", f"No conversion registered from {t.unit} to {e.unit}."))
            return rel
        if t.unit == e.unit:
            rel.checks.append(Check("Units", "pass", f"Both in {e.unit}."))
        else:
            rel.conversion = f"{t.unit} -> {e.unit}"
            rel.checks.append(Check("Units", "pass", f"Target converted from {t.unit} to {e.unit}."))
        if t.source == "derived":
            rel.checks.append(Check("Same formula on both sides", "pass", f"Both computed as: {t.formula}."))
        rel.verdict = "screened"
        return rel

    # ------------------------------------------------------------ stage 2
    def _investigate(self, rel: Relationship, prior: float, accepted: list[Relationship]) -> None:
        """Data checks for one pairing. Counts as one tool call."""
        x = self.ds.earth[rel.earth_col].to_numpy(float)
        confidence = prior
        if prior < 1.0:
            rel.checks.append(Check("Concept match", "warn",
                                    f"Related but not identical concepts; confidence starts at {prior:.2f}."))
        else:
            rel.checks.append(Check("Concept match", "pass", "Identical concepts."))

        def wait(name, detail):
            rel.checks.append(Check(name, "warn", detail + " Kept pending and re-checked when more data arrives."))
            rel.verdict, rel.pending_reason = "pending", "evidence"

        missing = float(np.isnan(x).mean())
        have = int((~np.isnan(x)).sum())
        if have < MIN_VALUES:
            return wait("Earth data completeness", f"Only {have} Earth cells have a value (at least {MIN_VALUES} needed).")
        if missing > MAX_MISSING:
            return wait("Earth data completeness",
                        f"{missing:.0%} of Earth cells have no value (limit {MAX_MISSING:.0%}).")
        rel.checks.append(Check("Earth data completeness", "pass" if missing < 0.10 else "warn",
                                f"{missing:.1%} of Earth cells have no value."))
        confidence *= 1.0 - missing

        if self.ds.targets[rel.target_col].isna().all():
            return wait("Target data present", "No target site has a value for this column yet.")

        sigma = robust_sigma(x)
        if sigma <= 0:
            rel.checks.append(Check("Tells sites apart", "fail",
                                    "The Earth column is constant, so it cannot distinguish one site from another."))
            rel.verdict = "denied"
            return
        lo, hi = np.nanpercentile(x, [0.5, 99.5])
        unit = self.ds.earth_cols[rel.earth_col].unit
        rel.checks.append(Check("Tells sites apart", "pass",
                                f"Earth values span {fmt(lo, unit)} to {fmt(hi, unit)} "
                                f"(typical spread {fmt(sigma, unit)})."))
        if np.nanmin(x) > 0 and hi / lo >= LOG_RATIO:
            # A fixed difference means little when values span orders of magnitude:
            # 1 vs 2 is as different as 100 vs 200. Compare ratios instead.
            rel.scale, sigma = "log", robust_sigma(np.log10(x))
            rel.checks.append(Check("Scale", "pass",
                                    f"Earth values span a factor of {hi / lo:.0f}, so sites are compared by ratio "
                                    "(logarithmic scale) rather than by difference."))
        rel.sigma, rel.bandwidth = sigma, BANDWIDTH_FACTOR * sigma
        rel.earth_lo, rel.earth_hi = float(lo), float(hi)

        twin = None
        replaces = set(self.ds.earth_cols[rel.earth_col].supersedes)
        for other in accepted:
            if self.ds.earth_cols[other.earth_col].concept in replaces:
                continue  # this column replaces that one, so it is not a second copy of it
            if other.dimension == rel.dimension and other.earth_col != rel.earth_col:
                rho = _spearman(x, self.ds.earth[other.earth_col].to_numpy(float))
                if abs(rho) >= REDUNDANT_RHO:
                    twin = (other.earth_col, rho)
                    break
        if twin:
            confidence *= 0.5
            rel.checks.append(Check("Not a duplicate signal", "warn",
                                    f"Moves almost in step with '{twin[0]}' (rank correlation {twin[1]:+.2f}); "
                                    "counted at half weight so the same signal is not counted twice."))
        else:
            rel.checks.append(Check("Not a duplicate signal", "pass",
                                    "No already-accepted column in this dimension carries the same signal."))

        rel.confidence = round(float(confidence), 3)
        rel.verdict = "accepted"

    # ---------------------------------------------------------------- run
    def run(self, store=None, run_no: int = 1) -> AgentResult:
        """One agent run: at most `max_tool_calls` data investigations."""
        log: list[str] = []
        proposals = self.proposer.propose(self.ds.target_cols, self.ds.earth_cols)
        if getattr(self.proposer, "note", ""):
            log.append(self.proposer.note)
        log.append(f"Proposer suggested {len(proposals)} candidate pairings.")

        # A target column nobody proposed a partner for is still reported.
        proposed_targets = {p.target_col for p in proposals}
        relationships: list[Relationship] = []
        for t in self.ds.target_cols.values():
            if t.name not in proposed_targets:
                rel = Relationship(f"{t.name}__none", t.name, "", t.dimension, "denied", decided_in_run=run_no)
                rel.checks.append(Check("Earth counterpart", "fail", "No Earth column was proposed as a counterpart."))
                relationships.append(rel)

        seen, queue, accepted, reused = set(), [], [], 0
        for p in proposals:
            if (p.target_col, p.earth_col) in seen:
                continue
            seen.add((p.target_col, p.earth_col))
            rel = self._screen(p)
            rel.decided_in_run = run_no
            if rel.verdict != "screened":
                relationships.append(rel)
                log.append(f"Screened out {rel.target_col} ~ {rel.earth_col}: {rel.checks[-1].detail}")
                continue
            fp = self.fingerprint(rel.target_col, rel.earth_col)
            old = store.get(rel.id) if store else None
            if old and old["fingerprint"] == fp and old["verdict"] in ("accepted", "denied"):
                kept = Relationship.from_dict(old["payload"])
                kept.origin = "reused"
                relationships.append(kept)
                if kept.verdict == "accepted":
                    accepted.append(kept)
                reused += 1
                continue
            relationships.append(rel)
            was_pending = bool(old and old["verdict"] == "pending")
            priority = self.ds.target_cols[p.target_col].priority * p.prior + (1000 if was_pending else 0)
            queue.append((priority, p, rel, fp))
        if reused:
            log.append(f"Reused {reused} decisions from the relationship store (data unchanged).")

        queue.sort(key=lambda item: -item[0])  # stable: ties keep proposal order
        used = 0
        for _, p, rel, fp in queue:
            if used >= self.max_tool_calls:
                rel.verdict, rel.pending_reason = "pending", "budget"
                rel.checks.append(Check("Investigated", "warn",
                                        f"This run’s budget of {self.max_tool_calls} tool calls ran out before "
                                        "this lower-priority pairing was reached. It goes first in the next run."))
                log.append(f"Budget exhausted before {rel.target_col} ~ {rel.earth_col}; left pending.")
            else:
                used += 1
                self._investigate(rel, p.prior, accepted)
                if rel.verdict == "accepted":
                    accepted.append(rel)
                log.append(f"Tool call {used}: {rel.target_col} ~ {rel.earth_col} -> {rel.verdict}"
                           + (f" (confidence {rel.confidence:.2f})" if rel.verdict == "accepted" else ""))
            if store:
                store.put(rel, fp, run_no)

        n = {v: sum(r.verdict == v for r in relationships) for v in ("accepted", "pending", "denied")}
        log.append(f"Run {run_no} finished: {n['accepted']} accepted, {n['pending']} pending, {n['denied']} denied; "
                   f"{used} of {self.max_tool_calls} tool calls used.")
        return AgentResult(relationships, used, self.max_tool_calls, log, run_no)


def target_value_in_earth_units(ds: Dataset, rel: Relationship, target_id: str) -> float:
    t, e = ds.target_cols[rel.target_col], ds.earth_cols[rel.earth_col]
    return float(convert(ds.targets.loc[target_id, rel.target_col], t.unit, e.unit))
