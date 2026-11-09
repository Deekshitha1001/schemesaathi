#!/usr/bin/env python3
"""Record that you verified scheme(s) against the official source.

    python scripts/mark_verified.py pm_kisan pmuy --date 2026-11-05
    python scripts/mark_verified.py pm_kisan --date 2026-11-05 --note "Checked pmkisan.gov.in FAQ, amount and exclusions"

Only run this AFTER you have checked every item for the scheme in docs/DATA_VERIFICATION.md.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.verification import mark_verified  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ids", nargs="+", help="scheme id(s) from data/schemes.json")
    parser.add_argument("--date", required=True, help="the day you verified, YYYY-MM-DD")
    parser.add_argument("--note", help="what you checked and where (kept in the data file)")
    args = parser.parse_args(argv)
    try:
        changed = mark_verified(args.ids, args.date, args.note)
    except (KeyError, ValueError) as exc:
        print(f"Error: {exc.args[0]}", file=sys.stderr)
        return 2
    print(f"Marked as verified on {args.date}: {', '.join(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
