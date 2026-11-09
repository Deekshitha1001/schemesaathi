"""Measure retrieval quality on eval/retrieval_cases.json.

    python eval/eval_retrieval.py [dev|heldout|all]   # TF-IDF (default, offline)
    EMBEDDING_BACKEND=sentence-transformers python eval/eval_retrieval.py

Metrics
  hit@1 / hit@3   the expected scheme is the top-1 / in the top-3 schemes
  MRR             mean reciprocal rank of the expected scheme
  off-topic OK    off-topic questions correctly return NO passages (so the app can say "I don't know")
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.retrieval import build_index  # noqa: E402


def ranked_schemes(index, query: str, lang: str) -> list[str]:
    scores = index.scheme_scores(query, lang)
    return [sid for sid, _ in sorted(scores.items(), key=lambda kv: -kv[1])]


def run(verbose: bool = False, cases_file: str = "retrieval_cases.json") -> dict:
    backend = os.environ.get("EMBEDDING_BACKEND", "tfidf")
    index = build_index(backend, os.environ.get("EMBEDDING_MODEL"))
    cases = json.loads((ROOT / "eval" / cases_file).read_text(encoding="utf-8"))["cases"]

    on_topic = [c for c in cases if c["expect"]]
    off_topic = [c for c in cases if not c["expect"]]

    stats = {lang: {"n": 0, "hit1": 0, "hit3": 0, "rr": 0.0} for lang in ("en", "hi", "kn")}
    misses = []
    for case in on_topic:
        ranking = ranked_schemes(index, case["q"], case["lang"])
        s = stats[case["lang"]]
        s["n"] += 1
        if case["expect"] in ranking:
            rank = ranking.index(case["expect"]) + 1
            s["rr"] += 1 / rank
            s["hit1"] += rank == 1
            s["hit3"] += rank <= 3
        if not ranking or ranking[0] != case["expect"]:
            misses.append((case["q"], case["expect"], ranking[:3]))

    rejected = 0
    leaked = []
    for case in off_topic:
        hits = index.search(case["q"], k=3, lang=case["lang"])
        if not hits:
            rejected += 1
        else:
            leaked.append((case["q"], hits[0][0].id, round(hits[0][1], 3)))

    total = {k: sum(s[k] for s in stats.values()) for k in ("n", "hit1", "hit3", "rr")}
    report = {
        "backend": index.embedder.name,
        "on_topic_cases": total["n"],
        "hit@1": round(total["hit1"] / total["n"], 3),
        "hit@3": round(total["hit3"] / total["n"], 3),
        "MRR": round(total["rr"] / total["n"], 3),
        "off_topic_cases": len(off_topic),
        "off_topic_rejected": round(rejected / len(off_topic), 3),
        "by_language": {
            lang: {"n": s["n"], "hit@1": round(s["hit1"] / s["n"], 3) if s["n"] else None}
            for lang, s in stats.items()
        },
    }
    if verbose:
        report["misses"] = misses
        report["off_topic_leaks"] = leaked
    return report


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    files = {"dev": ["retrieval_cases.json"], "heldout": ["retrieval_heldout.json"], "all": ["retrieval_cases.json", "retrieval_heldout.json"]}[which]
    for name in files:
        print(f"--- {name}")
        print(json.dumps(run(verbose=True, cases_file=name), indent=2, ensure_ascii=False))
