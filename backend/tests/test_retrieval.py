import json
import sys
from pathlib import Path

import pytest

from app.retrieval import build_index, content_words

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))
import eval_retrieval  # noqa: E402


def top_scheme(index, query, lang):
    scores = index.scheme_scores(query, lang)
    return max(scores, key=scores.get) if scores else None


@pytest.mark.parametrize("query,lang,scheme", [
    ("How much money does PM-KISAN give to farmers?", "en", "pm_kisan"),
    ("free LPG gas connection for poor women", "en", "pmuy"),
    ("गरीब महिलाओं को मुफ्त गैस कनेक्शन", "hi", "pmuy"),
    ("ಹೆಣ್ಣು ಮಗುವಿಗೆ ಉಳಿತಾಯ ಖಾತೆ", "kn", "ssy"),
])
def test_finds_the_right_scheme_in_each_language(service, query, lang, scheme):
    assert top_scheme(service.index, query, lang) == scheme


@pytest.mark.parametrize("query,lang", [
    ("what is the weather in paris", "en"),
    ("tell me a joke", "en"),
    ("मौसम कैसा है", "hi"),
    ("ಬಿರಿಯಾನಿ ಮಾಡುವುದು ಹೇಗೆ", "kn"),
])
def test_off_topic_questions_return_nothing(service, query, lang):
    assert service.index.search(query, k=3, lang=lang) == []


def test_results_stay_in_the_requested_language(service):
    hits = service.index.search("pension", k=5, lang="hi")
    assert all(p.lang == "hi" for p, _ in hits)


def test_scheme_filter(service):
    hits = service.index.search("how to apply", k=5, lang="en", scheme_ids={"mudra"})
    assert hits and all(p.scheme_id == "mudra" for p, _ in hits)


def test_every_passage_has_a_source():
    index = build_index()
    assert all(p.source_url.startswith("https://") and p.section and p.text for p in index.passages)
    assert len(index.passages) == 12 * 4 * 3  # schemes x sections x languages


def test_stopwords_are_dropped_and_plurals_folded():
    assert content_words("What is the weather in Paris?") == ["weather", "paris"]
    assert content_words("farmers get 6000") == ["farmer"]


def test_empty_query_returns_nothing(service):
    assert service.index.search("   ", k=3) == []


def test_ingested_passages_are_loaded_and_cited(tmp_path, monkeypatch):
    import app.retrieval as retrieval
    extra = tmp_path / "extra.jsonl"
    extra.write_text(json.dumps({
        "id": "pm_kisan:ingested:0", "scheme_id": "pm_kisan", "section": "ingested", "lang": "en",
        "text": "PM-KISAN operational guidelines paragraph about e-KYC and land seeding.", "source_url": "https://pmkisan.gov.in",
    }) + "\n", encoding="utf-8")
    monkeypatch.setattr(retrieval, "EXTRA_PASSAGES", extra)
    index = retrieval.build_index()
    hits = index.search("e-KYC land seeding guidelines", k=1, lang="en")
    assert hits and hits[0][0].origin == "ingested"


# --- quality floors on the evaluation sets ----------------------------------------------------

def test_retrieval_quality_floor_on_both_sets():
    for name, floor in (("retrieval_cases.json", 0.95), ("retrieval_heldout.json", 0.80)):
        report = eval_retrieval.run(cases_file=name)
        assert report["hit@3"] >= floor, (name, report)
        assert report["off_topic_rejected"] >= 0.5, (name, report)
