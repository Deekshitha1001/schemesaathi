#!/usr/bin/env python3
"""CLI: ingest official scheme documents into data/passages_extra.jsonl.

    python scripts/ingest_documents.py ./official_docs
    python scripts/ingest_documents.py ./official_docs --source-url https://example.gov.in/guidelines

Then restart the API. Check the effect with:  python eval/eval_retrieval.py
Only ingest documents you are allowed to use; keep the source URL accurate, because the app shows it as the citation.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingest import ingest_directory  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", type=Path, help="folder with .pdf / .txt / .md files named <scheme_id>_*.ext")
    parser.add_argument("--source-url", help="citation URL to use instead of the scheme's default portal")
    args = parser.parse_args(argv)
    if not args.folder.is_dir():
        print(f"Not a folder: {args.folder}", file=sys.stderr)
        return 2
    summary = ingest_directory(args.folder, source_url=args.source_url)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["passages"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
