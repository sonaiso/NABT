#!/usr/bin/env python3
"""Retrieve exact pinned dictionary heading blocks, or audit their partition."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nabt.source_lexicon import SourceLexicon, SourceIdentityError


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("maqayis", "lisan"), default="maqayis")
    parser.add_argument("--file", type=Path, help="Exact source bytes; identity is checked")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--root", help="Exact source heading; no normalization")
    action.add_argument("--list-headings", action="store_true", help="List all heading spans and review statuses")
    args = parser.parse_args()
    default = (ROOT / "evidence/classical_language/sources/maqayis.txt" if args.source == "maqayis"
               else ROOT / "artifacts/local/lisan.txt")
    try:
        index = SourceLexicon.load(args.source, args.file or default)
        result = index.lookup_exact(args.root) if args.root is not None else index.inventory()
        if args.list_headings:
            result["headings"] = [asdict(block) for block in index.blocks]
    except FileNotFoundError:
        result = {"status": "SOURCE_UNAVAILABLE", "source_id": args.source}
    except SourceIdentityError as exc:
        result = {"status": "SOURCE_IDENTITY_MISMATCH", "error": str(exc)}
    except ValueError as exc:
        result = {"status": "INVALID_INPUT", "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get("status") in {"SOURCE_UNAVAILABLE", "SOURCE_IDENTITY_MISMATCH", "INVALID_INPUT"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
