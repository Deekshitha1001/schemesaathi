"""Turn official scheme documents (PDF / text / Markdown) into citable passages.

The built-in passages are a structured SUMMARY written for this project. To make the app quote the
official wording instead, put the documents in a folder and run:

    python scripts/ingest_documents.py ./official_docs

File names decide which scheme a file belongs to: they must START with a scheme id from
data/schemes.json, e.g. ``pm_kisan_guidelines.pdf`` or ``pmuy-faq.txt``. Each file becomes several
passages (about 800 characters, split on paragraphs) saved to data/passages_extra.jsonl. The retrieval
index loads that file automatically and marks those passages ``origin: "ingested"``.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .rules import DATA_DIR, load_schemes
from .service import detect_lang

SUPPORTED = {".txt", ".md", ".pdf"}
OUTPUT = DATA_DIR / "passages_extra.jsonl"


def read_pages(path: Path) -> list[tuple[int | None, str]]:
    """Return [(page_number_or_None, text)] for a file."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader  # lazy: only needed for PDFs

        reader = PdfReader(str(path))
        return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]
    if suffix in (".txt", ".md"):
        return [(None, path.read_text(encoding="utf-8", errors="replace"))]
    raise ValueError(f"Unsupported file type: {path.suffix}")


def chunk_text(text: str, max_chars: int = 800, min_chars: int = 40) -> list[str]:
    """Split on blank lines, then merge paragraphs up to max_chars; split oversized paragraphs by sentence."""
    text = re.sub(r"[ \t]+", " ", text.replace("\r", ""))
    paragraphs = [re.sub(r"\s*\n\s*", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    pieces: list[str] = []
    for para in paragraphs:
        if len(para) <= max_chars:
            pieces.append(para)
            continue
        current = ""
        for sentence in re.split(r"(?<=[.!?।])\s+", para):
            while len(sentence) > max_chars:  # no sentence boundary at all: hard split
                pieces.append(sentence[:max_chars])
                sentence = sentence[max_chars:]
            if current and len(current) + 1 + len(sentence) > max_chars:
                pieces.append(current)
                current = sentence
            else:
                current = f"{current} {sentence}".strip()
        if current:
            pieces.append(current)

    chunks: list[str] = []
    buffer = ""
    for piece in pieces:
        if not piece:
            continue
        if buffer and len(buffer) + 1 + len(piece) > max_chars:
            chunks.append(buffer)
            buffer = piece
        else:
            buffer = f"{buffer} {piece}".strip()
    if buffer:
        chunks.append(buffer)
    return [c for c in chunks if len(c) >= min_chars]


def scheme_for_file(path: Path, scheme_ids: list[str]) -> str | None:
    """Longest scheme id that the file name starts with (so 'pm_jay' does not capture 'pm_jay_extra' wrongly)."""
    stem = path.stem.lower().replace("-", "_")
    matches = [sid for sid in scheme_ids if stem == sid or stem.startswith(sid + "_")]
    return max(matches, key=len) if matches else None


def ingest_directory(folder: Path, source_url: str | None = None, output: Path | None = None) -> dict:
    """Ingest every supported file in `folder`. Returns a summary; writes the JSONL output file."""
    output = output or OUTPUT
    schemes = {s["id"]: s for s in load_schemes()}
    rows: dict[str, dict] = {}
    skipped: list[str] = []
    per_scheme: dict[str, int] = {}

    for path in sorted(Path(folder).iterdir()):
        if path.suffix.lower() not in SUPPORTED:
            continue
        scheme_id = scheme_for_file(path, list(schemes))
        if scheme_id is None:
            skipped.append(f"{path.name}: file name must start with a scheme id ({', '.join(schemes)})")
            continue
        url = source_url or schemes[scheme_id]["source_url"]
        for page, text in read_pages(path):
            for chunk in chunk_text(text):
                digest = hashlib.sha1(chunk.encode("utf-8")).hexdigest()[:10]
                lang = detect_lang(chunk)
                pid = f"{scheme_id}:ingested:{lang}:{digest}"
                rows[pid] = {
                    "id": pid,
                    "scheme_id": scheme_id,
                    "section": "official-document",
                    "lang": lang,
                    "text": chunk,
                    "source_url": url,
                    "meta": {"file": path.name, **({"page": page} if page else {})},
                }
                per_scheme[scheme_id] = per_scheme.get(scheme_id, 0) + 1

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as fh:
        for row in rows.values():
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"passages": len(rows), "per_scheme": per_scheme, "skipped": skipped, "output": str(output)}
