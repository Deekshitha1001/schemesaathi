"""Deterministic eligibility engine.

Why rules in code and not "ask the LLM if this person qualifies"?
An LLM can sound sure and be wrong. Eligibility is a yes/no question about
published criteria, so it is computed here, and the result can be explained
line by line and unit-tested.

Each criterion evaluates to one of:
    pass     the profile satisfies it
    soft     the profile satisfies a rough *indicator* only (criterion has soft=true)
    unknown  the profile does not say (the app asks the user)
    fail     the profile contradicts it

Scheme status:
    not_eligible  at least one criterion fails
    likely        nothing fails, but something is unknown or only a rough indicator
    eligible      every criterion passes
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

PASS, SOFT, UNKNOWN, FAIL = "pass", "soft", "unknown", "fail"
# When several alternatives are allowed (any_of) the best outcome wins.
_ANY_OF_RANK = {PASS: 3, SOFT: 2, UNKNOWN: 1, FAIL: 0}

STATUS_ORDER = {"eligible": 0, "likely": 1, "not_eligible": 2}


@lru_cache(maxsize=1)
def load_schemes() -> list[dict]:
    with open(DATA_DIR / "schemes.json", encoding="utf-8") as fh:
        return json.load(fh)["schemes"]


@lru_cache(maxsize=1)
def load_documents() -> dict[str, dict[str, str]]:
    with open(DATA_DIR / "documents.json", encoding="utf-8") as fh:
        return json.load(fh)


def scheme_by_id(scheme_id: str) -> dict | None:
    return next((s for s in load_schemes() if s["id"] == scheme_id), None)


def _compare(op: str, actual, expected) -> bool:
    if op == "is_true":
        return actual is True
    if op == "is_false":
        return actual is False
    if op == "eq":
        return actual == expected
    if op == "in":
        return actual in expected
    if op == "gte":
        return actual >= expected
    if op == "lte":
        return actual <= expected
    if op == "between":
        return expected[0] <= actual <= expected[1]
    raise ValueError(f"Unknown rule op: {op}")


def check_rule(rule: dict, profile: dict) -> str:
    """Evaluate one simple rule against a profile."""
    actual = profile.get(rule["field"])
    if actual is None:
        return UNKNOWN
    try:
        ok = _compare(rule["op"], actual, rule.get("value"))
    except TypeError:  # e.g. comparing text with a number
        return UNKNOWN
    if not ok:
        return FAIL
    return SOFT if rule.get("soft") else PASS


def check_criterion(criterion: dict, profile: dict) -> tuple[str, list[str]]:
    """Evaluate one criterion (simple or any_of). Returns (result, fields_still_unknown)."""
    if "any_of" in criterion:
        results = [(check_rule(r, profile), r["field"]) for r in criterion["any_of"]]
        best = max(results, key=lambda item: _ANY_OF_RANK[item[0]])[0]
        missing = [field for res, field in results if res == UNKNOWN] if best == UNKNOWN else []
        return best, missing
    result = check_rule(criterion, profile)
    return result, ([criterion["field"]] if result == UNKNOWN else [])


def evaluate_scheme(scheme: dict, profile: dict) -> dict:
    """Evaluate every criterion of a scheme and derive an overall status."""
    checks, missing = [], []
    for criterion in scheme["criteria"]:
        result, unknown_fields = check_criterion(criterion, profile)
        checks.append({"text": criterion["text"], "result": result})
        for field in unknown_fields:
            if field not in missing:
                missing.append(field)

    results = {c["result"] for c in checks}
    if FAIL in results:
        status = "not_eligible"
    elif UNKNOWN in results or SOFT in results:
        status = "likely"
    else:
        status = "eligible"

    return {
        "id": scheme["id"],
        "status": status,
        "checks": checks,
        "missing_fields": missing if status != "not_eligible" else [],
    }


def evaluate_all(profile: dict) -> list[dict]:
    """Evaluate every scheme. Order: eligible, likely, not_eligible; stable within a group."""
    results = [evaluate_scheme(s, profile) for s in load_schemes()]
    return sorted(results, key=lambda r: STATUS_ORDER[r["status"]])


def next_questions(results: list[dict], limit: int = 6) -> list[str]:
    """Fields worth asking about next: the ones that unblock the most schemes first."""
    counts: dict[str, int] = {}
    for result in results:
        for field in result["missing_fields"]:
            counts[field] = counts.get(field, 0) + 1
    return [f for f, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))][:limit]
