#!/usr/bin/env python3
"""Regenerate docs/DATA_VERIFICATION.md from data/schemes.json.

    python scripts/make_verification_checklist.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.verification import render_checklist  # noqa: E402

OUT = ROOT.parent / "docs" / "DATA_VERIFICATION.md"

if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render_checklist(), encoding="utf-8")
    print(f"Wrote {OUT}")
