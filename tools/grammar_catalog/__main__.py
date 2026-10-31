"""Source catalogue, proposal search and explicit-premise conditional routing."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nabt.errors import NabtError

from .catalog import CatalogError, build_catalog
from .retrieval import RetrievalError, SearchIndex
from .routing import (build_routing_report, read_routing_document,
                      routing_document_text, verify_routing_report)


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
    route.add_argument("--legacy", action="store_true", help="Emit the original v1 routing report")
    route.add_argument("--output", type=Path)
    verify = sub.add_parser("verify-route", help="Replay a v2 route from separately supplied inputs")
    verify.add_argument("report", type=Path)
    verify.add_argument("--query", required=True)
    verify.add_argument("--frames", type=Path, required=True)
    verify.add_argument("--budget", type=int)
    verify.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "catalog":
            result = build_catalog()
            if args.summary:
                result = {k: result[k] for k in ("schema", "authority", "coverage", "inputs")}
        elif args.command == "verify-route":
            report = read_routing_document(args.report)
            frames = read_routing_document(args.frames)
            result = verify_routing_report(report, query=args.query, frames_by_rule=frames,
                                           budget=args.budget)
        else:
            if args.command == "search":
                index = SearchIndex()
                result = index.search(args.query, kind=args.kind, limit=args.limit)
            else:
                frames = read_routing_document(args.frames)
                index = SearchIndex()
                result = build_routing_report(index, args.query, frames, budget=args.budget,
                                              report_version=1 if args.legacy else 2)
        is_route = args.command in ("route", "verify-route")
        text = (routing_document_text(result) if is_route else
                json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            if is_route:
                with args.output.open("x", encoding="utf-8") as handle:
                    handle.write(text)
            else:
                args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0
    except NabtError as exc:
        result = exc.as_dict()
        result["grants_language_license"] = False
        print(json.dumps(result, ensure_ascii=False))
        return 3 if exc.code == "RESOURCE_LIMIT" else 2
    except (CatalogError, RetrievalError, OSError, ValueError) as exc:
        print(json.dumps({"status": "INPUT_OR_SOURCE_ERROR", "message": str(exc),
                          "grants_language_license": False}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
