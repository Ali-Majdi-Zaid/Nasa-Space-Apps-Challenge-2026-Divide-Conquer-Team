"""Language-model access for the proposer.

`anthropic_complete()` returns a function that sends one prompt to the
Claude API and returns the text of the reply. It uses only the standard
library. Set ANTHROPIC_API_KEY, and EARTHMIMIC_MODEL to the model you want.

`CachedProposer` wraps any proposer and saves its proposals to a file. As
long as the column metadata is unchanged the saved proposals are reused,
so results are reproducible and the pipeline still runs with no internet.
If the model cannot be reached and nothing is cached, it falls back to the
rule-based proposer and says so in the log.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

from .agent import Proposal, RuleProposer

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-5-5"


def anthropic_complete(model: str | None = None, api_key: str | None = None,
                       max_tokens: int = 4000, timeout: float = 120.0) -> Callable[[str], str]:
    model = model or os.environ.get("EARTHMIMIC_MODEL", DEFAULT_MODEL)
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Set the ANTHROPIC_API_KEY environment variable to use the language-model proposer.")

    def complete(prompt: str) -> str:
        body = json.dumps({"model": model, "max_tokens": max_tokens,
                           "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request(API_URL, data=body, method="POST", headers={
            "x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as err:
            detail = err.read().decode(errors="replace")[:300]
            raise RuntimeError(f"The model API returned HTTP {err.code} for model '{model}'. "
                               f"Check the key and EARTHMIMIC_MODEL. Details: {detail}") from err
        return "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")

    return complete


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_DEFAULT_MODEL = "gemini-3.8-flash"


def gemini_complete(model: str | None = None, api_key: str | None = None,
                    timeout: float = 120.0) -> Callable[[str], str]:
    """Like anthropic_complete, for Google's Gemini API (which has a free tier).

    Set GEMINI_API_KEY (free at aistudio.google.com), and EARTHMIMIC_MODEL
    to override the model.
    """
    model = model or os.environ.get("EARTHMIMIC_MODEL", GEMINI_DEFAULT_MODEL)
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Set the GEMINI_API_KEY environment variable (free key at aistudio.google.com).")

    def complete(prompt: str) -> str:
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
        req = urllib.request.Request(GEMINI_URL.format(model=model), data=body, method="POST", headers={
            "x-goog-api-key": api_key, "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as err:
            detail = err.read().decode(errors="replace")[:300]
            raise RuntimeError(f"The Gemini API returned HTTP {err.code} for model '{model}'. "
                               f"Check the key and EARTHMIMIC_MODEL. Details: {detail}") from err
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts)

    return complete


def default_complete() -> Callable[[str], str]:
    """Whichever provider has a key in the environment: Anthropic first, then Gemini."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return anthropic_complete()
    if os.environ.get("GEMINI_API_KEY"):
        return gemini_complete()
    raise RuntimeError("Set ANTHROPIC_API_KEY, or GEMINI_API_KEY (free key at aistudio.google.com), "
                       "to use the language-model features.")


class EquationAdvisor:
    """Reviews the fixed equation library against the dataset's metadata.

    The model can only do two things, both visible in the run log: set an
    equation aside (with a reason) or attach a caution to it. It cannot add
    an equation, change a formula, or touch a confidence - the library is
    the only source of physics, and the agent's deterministic checks still
    decide everything that is scored. If the model is unreachable or replies
    with nonsense, the review is empty and the pipeline behaves exactly as
    it does without a reviewer.
    """

    PROMPT = (
        "You are reviewing which equations from a fixed physics library apply cleanly to a dataset.\n"
        "You may ONLY reference equations by the exact names listed below. You cannot propose new "
        "equations or modify formulas.\n\nEquation library:\n{library}\n\n"
        "Measurement notes on the dataset columns the equations would use:\n{notes}\n\n"
        "For each equation, decide whether its assumptions hold for these measurements. Set an "
        "equation aside only for a concrete physical mismatch (wrong measurement height, invalid "
        "regime, broken assumption), not out of general caution. Reply with JSON only: a list of "
        'objects {{"name": str, "apply": bool, "caution": one sentence or ""}}.'
    )

    def __init__(self, complete: Callable[[str], str], cache_path: str | Path):
        self.complete, self.path = complete, Path(cache_path)
        self.note = ""

    def review(self, derived_list, target_cols, earth_cols) -> dict[str, dict]:
        lib = "\n".join(f"- {d.column.name}: {d.column.label}. Formula: {d.column.formula}. "
                        f"Inputs: {', '.join(d.inputs)}. Source: {d.citation}" for d in derived_list)
        concepts = {c for d in derived_list for c in d.inputs}
        notes = "\n".join(f"- {c.name} ({c.label}, {c.unit}): {c.note or 'no caveats recorded'}"
                          for cols in (target_cols, earth_cols) for c in cols.values()
                          if c.concept in concepts)
        key = hashlib.sha1((lib + notes).encode()).hexdigest()
        cache = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
        if key in cache:
            self.note = "Equation review reused from the cache (library and metadata unchanged)."
            return cache[key]
        valid = {d.column.name for d in derived_list}
        out = {}
        try:
            reply = self.complete(self.PROMPT.format(library=lib, notes=notes))
            text = reply.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            for item in json.loads(text):
                name = str(item.get("name", ""))
                if name in valid:   # anything outside the library is ignored
                    out[name] = dict(apply=bool(item.get("apply", True)),
                                     caution=str(item.get("caution", ""))[:300])
        except Exception as err:   # no internet, bad key, malformed reply: run without a review
            self.note = f"Equation reviewer failed ({err}); all library equations considered as usual."
            return {}
        cache[key] = out
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(cache, indent=1), encoding="utf-8")
        set_aside = sum(1 for v in out.values() if not v["apply"])
        self.note = (f"Language model reviewed {len(out)} library equations: "
                     f"{set_aside} set aside, {sum(1 for v in out.values() if v['caution'])} with cautions.")
        return out


class CachedProposer:
    def __init__(self, proposer, cache_path: str | Path, fallback=None):
        self.proposer, self.path = proposer, Path(cache_path)
        self.fallback = fallback or RuleProposer()
        self.note = ""   # what happened on the last call, for the run log

    @staticmethod
    def _key(target_cols, earth_cols) -> str:
        meta = [[c.to_dict() for c in cols.values()] for cols in (target_cols, earth_cols)]
        return hashlib.sha1(json.dumps(meta, sort_keys=True).encode()).hexdigest()

    def propose(self, target_cols, earth_cols) -> list[Proposal]:
        key = self._key(target_cols, earth_cols)
        cache = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
        if key in cache:
            self.note = "Language-model proposals reused from the cache (metadata unchanged)."
            return [Proposal(**p) for p in cache[key]]
        try:
            proposals = self.proposer.propose(target_cols, earth_cols)
        except Exception as err:  # no internet, bad key, malformed reply: keep the pipeline running
            self.note = f"Language-model proposer failed ({err}); used the rule-based proposer instead."
            return self.fallback.propose(target_cols, earth_cols)
        cache[key] = [dict(target_col=p.target_col, earth_col=p.earth_col, prior=p.prior, rationale=p.rationale)
                      for p in proposals]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(cache, indent=1), encoding="utf-8")
        self.note = f"Language model proposed {len(proposals)} pairings (saved to the cache)."
        return proposals
