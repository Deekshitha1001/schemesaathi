"""Measure how well the rule-based extractor reads a person's description.

    python eval/eval_extraction.py [dev|heldout|all]

Scoring is per field. A wrong value counts twice (a wrong fact AND a missed fact), because a wrong
fact is worse than a missing one: missing facts are simply asked about, wrong facts silently change
who is told they are eligible.

  precision  of the facts the extractor returned, how many were right
  recall     of the facts actually stated, how many were found
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.extract import extract_profile  # noqa: E402


def run(cases_file: str = "extraction_cases.json", verbose: bool = False) -> dict:
    cases = json.loads((ROOT / "eval" / cases_file).read_text(encoding="utf-8"))["cases"]
    tally = {lang: {"tp": 0, "fp": 0, "fn": 0, "exact": 0, "n": 0} for lang in ("en", "hi", "kn")}
    failures = []
    for case in cases:
        got = extract_profile(case["text"])["profile"]
        want = case["expect"]
        t = tally[case["lang"]]
        t["n"] += 1
        wrong, missed, extra = [], [], []
        for field, value in want.items():
            if field not in got:
                t["fn"] += 1
                missed.append(field)
            elif got[field] != value:
                t["fn"] += 1
                t["fp"] += 1
                wrong.append((field, value, got[field]))
            else:
                t["tp"] += 1
        for field, value in got.items():
            if field not in want:
                t["fp"] += 1
                extra.append((field, value))
        if wrong or missed or extra:
            failures.append({"text": case["text"][:70], "wrong": wrong, "missed": missed, "extra": extra})
        else:
            t["exact"] += 1

    def rates(t):
        p = t["tp"] / (t["tp"] + t["fp"]) if t["tp"] + t["fp"] else 0.0
        r = t["tp"] / (t["tp"] + t["fn"]) if t["tp"] + t["fn"] else 0.0
        f = 2 * p * r / (p + r) if p + r else 0.0
        return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3), "cases_exact": f"{t['exact']}/{t['n']}"}

    total = {k: sum(t[k] for t in tally.values()) for k in ("tp", "fp", "fn", "exact", "n")}
    report = {"cases": total["n"], "overall": rates(total), "by_language": {lang: rates(t) for lang, t in tally.items()}}
    if verbose:
        report["failures"] = failures
    return report


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    files = {"dev": ["extraction_cases.json"], "heldout": ["extraction_heldout.json"], "all": ["extraction_cases.json", "extraction_heldout.json"]}[which]
    for name in files:
        if (ROOT / "eval" / name).exists():
            print(f"--- {name}")
            print(json.dumps(run(name, verbose=True), indent=1, ensure_ascii=False))
