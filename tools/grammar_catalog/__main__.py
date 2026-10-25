"""Source catalogue, proposal search and explicit-premise conditional routing."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .catalog import CatalogError, build_catalog
from .retrieval import RetrievalError, SearchIndex
from .routing import evaluate_candidates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    cat = sub.add_parser("catalog", help="Replay sources and emit the catalogue")
    cat.add_argument("--summary", action="store_true")
    cat.add_argument("--output", type=Path)
    find = sub.add_parser("search", help="Return source-linked proposals, not a licensed parse")
    find.add_argument("query")
    find.add_argument("--kind", choices=("rule", "passage", "item"))
    find.add_argument("--limit", type=int, default=10)
    find.add_argument("--output", type=Path)
    route = sub.add_parser("route", help="Evaluate supplied frames with complete inventory fallback")
    route.add_argument("query")
    route.add_argument("--frames", type=Path, required=True)
    route.add_argument("--budget", type=int)
    route.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "catalog":
            result = build_catalog()
            if args.summary:
                result = {k: result[k] for k in ("schema", "authority", "coverage", "inputs")}
        else:
            index = SearchIndex()
            found = index.search(args.query, kind=(args.kind if args.command == "search" else "rule"),
                                 limit=(args.limit if args.command == "search" else 10))
            if args.command == "search":
                result = found
            else:
                frames = json.loads(args.frames.read_text(encoding="utf-8"))
                result = evaluate_candidates(index, [r["id"] for r in found["candidates"]], frames,
                                             budget=args.budget)
                result["retrieval"] = found
        text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0
    except (CatalogError, RetrievalError, OSError, ValueError) as exc:
        print(json.dumps({"status": "INPUT_OR_SOURCE_ERROR", "message": str(exc),
                          "grants_language_license": False}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
