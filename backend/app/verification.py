"""Helpers for the data-verification workflow (see docs/DATA_VERIFICATION.md).

The scheme data was written from general knowledge and must be checked against official sources
before the app is shown to real people. These helpers make that check systematic:

  render_checklist()  -> a Markdown checklist built from data/schemes.json (what to check, where)
  mark_verified()     -> records that you checked a scheme, with the date and an optional note

The app shows a "demo data" banner until EVERY scheme has a last_verified date.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .rules import DATA_DIR

SCHEMES_FILE = DATA_DIR / "schemes.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_date(value: str) -> str:
    """Accept YYYY-MM-DD only, and never a date in the future (you cannot have verified it yet)."""
    try:
        day = dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Date must look like 2026-11-05, got {value!r}") from exc
    if day > dt.date.today():
        raise ValueError(f"{value} is in the future")
    return day.isoformat()


def mark_verified(ids: list[str], date: str, note: str | None = None, path: Path = SCHEMES_FILE) -> list[str]:
    """Set last_verified on the given scheme ids. Returns the ids changed. Raises on unknown ids (nothing is written)."""
    date = parse_date(date)
    data = _load(path)
    known = {s["id"]: s for s in data["schemes"]}
    unknown = [i for i in ids if i not in known]
    if unknown:
        raise KeyError(f"Unknown scheme id(s): {', '.join(unknown)}. Known: {', '.join(known)}")
    for scheme_id in ids:
        known[scheme_id]["last_verified"] = date
        if note:
            known[scheme_id]["verification_notes"] = note
    _save(path, data)
    return list(ids)


def render_checklist(path: Path = SCHEMES_FILE) -> str:
    data = _load(path)
    schemes = data["schemes"]
    done = sum(1 for s in schemes if s.get("last_verified"))
    lines = [
        "# Data verification checklist",
        "",
        "_Generated from `backend/data/schemes.json` by `backend/scripts/make_verification_checklist.py`. Do not edit by hand; edit the data and regenerate._",
        "",
        f"**Progress: {done} of {len(schemes)} schemes verified.** The app shows a \"demo data\" warning until all {len(schemes)} are done.",
        "",
        "For each scheme: open the official page, tick every item, fix `schemes.json` wherever it differs, then run",
        "`python scripts/mark_verified.py <scheme_id> --date YYYY-MM-DD`.",
        "",
    ]
    for scheme in schemes:
        status = f"verified {scheme['last_verified']}" if scheme.get("last_verified") else "NOT verified"
        lines += [
            f"## {scheme['name']['en']}  (`{scheme['id']}`) — {status}",
            "",
            f"- Official page: {scheme['source_url']}",
            f"- Apply link in the app: {scheme['apply_url']}",
        ]
        if scheme.get("verification_notes"):
            lines.append(f"- Already confirmed: {scheme['verification_notes']}")
        lines += ["- Check these facts:"] + [f"  - [ ] {item}" for item in scheme["verify"]]
        lines += ["- Check the rules the app applies:"] + [f"  - [ ] {c['text']['en']}" for c in scheme["criteria"]]
        lines += [f"  - [ ] Documents list: {', '.join(scheme['documents'])}", ""]
    lines += [
        "## Also have a native speaker review",
        "",
        "- [ ] Hindi text in `data/schemes.json`, `data/documents.json`, `app/fields.py` and `frontend/src/i18n.js`",
        "- [ ] Kannada text in the same four files",
        "",
    ]
    return "\n".join(lines)
