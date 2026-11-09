import json

import pytest
from reportlab.pdfgen import canvas

from app.ingest import chunk_text, ingest_directory, scheme_for_file
from app.rules import load_schemes

IDS = [s["id"] for s in load_schemes()]


def test_chunking_respects_size_and_drops_noise():
    text = "Heading\n\n" + ("This is a sentence about eligibility. " * 60) + "\n\nShort.\n\n" + "Another real paragraph that is long enough to keep."
    chunks = chunk_text(text, max_chars=300)
    assert all(len(c) <= 300 for c in chunks) and all(len(c) >= 40 for c in chunks)
    assert "Short." not in " ".join(chunks).replace("Short. Another", "")  # tiny fragments are merged or dropped, never alone


def test_unbroken_text_is_hard_split():
    assert all(len(c) <= 100 for c in chunk_text("x" * 450, max_chars=100))


def test_file_names_map_to_the_longest_scheme_id():
    assert scheme_for_file(type("P", (), {"stem": "pm_kisan_guidelines"})(), IDS) == "pm_kisan"
    assert scheme_for_file(type("P", (), {"stem": "pmuy-faq"})(), IDS) == "pmuy"
    assert scheme_for_file(type("P", (), {"stem": "random"})(), IDS) is None
    assert scheme_for_file(type("P", (), {"stem": "pmuyfaq"})(), IDS) is None


def make_pdf(path, lines):
    c = canvas.Canvas(str(path))
    y = 800
    for line in lines:
        c.drawString(60, y, line)
        y -= 20
    c.save()


def test_ingest_txt_and_pdf_end_to_end(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "pm_kisan_notes.txt").write_text("Registered farmers must complete e-KYC before instalments are released. Land seeding is mandatory for every beneficiary.", encoding="utf-8")
    make_pdf(docs / "mudra_guide.pdf", ["Mudra loans are offered in three categories called Shishu, Kishor and Tarun for micro enterprises."])
    (docs / "unrelated.txt").write_text("nothing to see here, this file has no scheme id in its name", encoding="utf-8")
    (docs / "notes.docx").write_text("ignored", encoding="utf-8")
    out = tmp_path / "extra.jsonl"

    summary = ingest_directory(docs, output=out)
    assert summary["per_scheme"] == {"pm_kisan": 1, "mudra": 1}
    assert len(summary["skipped"]) == 1 and "unrelated.txt" in summary["skipped"][0]

    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert {r["scheme_id"] for r in rows} == {"pm_kisan", "mudra"}
    pdf_row = next(r for r in rows if r["scheme_id"] == "mudra")
    assert pdf_row["meta"] == {"file": "mudra_guide.pdf", "page": 1} and pdf_row["source_url"].startswith("https://")

    # The retrieval index picks the passages up and cites them.
    import app.retrieval as retrieval
    monkeypatch.setattr(retrieval, "EXTRA_PASSAGES", out)
    hits = retrieval.build_index().search("e-KYC land seeding mandatory", k=1, lang="en")
    assert hits and hits[0][0].origin == "ingested" and hits[0][0].scheme_id == "pm_kisan"


def test_ingest_is_idempotent(tmp_path):
    docs = tmp_path / "d"
    docs.mkdir()
    (docs / "ssy_faq.txt").write_text("The Sukanya Samriddhi account can be opened for a girl child below ten years of age.", encoding="utf-8")
    out = tmp_path / "o.jsonl"
    first = ingest_directory(docs, output=out)
    second = ingest_directory(docs, output=out)
    assert first["passages"] == second["passages"] == 1
    assert len(out.read_text(encoding="utf-8").splitlines()) == 1


def test_hindi_document_is_tagged_hindi(tmp_path):
    docs = tmp_path / "d"
    docs.mkdir()
    (docs / "pmuy_hi.txt").write_text("उज्ज्वला योजना के अंतर्गत गरीब परिवारों की महिलाओं को मुफ्त एलपीजी कनेक्शन दिया जाता है।", encoding="utf-8")
    out = tmp_path / "o.jsonl"
    ingest_directory(docs, output=out)
    assert json.loads(out.read_text(encoding="utf-8"))["lang"] == "hi"
