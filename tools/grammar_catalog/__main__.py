"""Source catalogue, proposal search and explicit-premise conditional routing."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .catalog import CatalogError, build_catalog
from .retrieval import RetrievalError, SearchIndex
from .routing import evaluate_candidates
from tools.evidence_lifecycle_v1 import ResourceLimit


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
    operations = sub.add_parser("operations", help="Source-derived operation cards and hybrid proposal retrieval")
    operations.add_argument("query", nargs="?")
    operations.add_argument("--limit", type=int, default=5)
    operations.add_argument("--output", type=Path)
    rag = sub.add_parser("rag", help="Retrieve, execute installed owners and emit a source-linked answer")
    rag.add_argument("--request", type=Path, required=True)
    rag.add_argument("--verify", type=Path, help="Replay this receipt against the independent --request")
    rag.add_argument("--output", type=Path)
    sub.add_parser("rag-worker", help=argparse.SUPPRESS)
    from .awamil_cli import arguments as awamil_arguments
    awamil_arguments(sub.add_parser("awamil", help="Source-qualified factors, relation matrix, curriculum and learned retrieval"))
    from .irab_cli import arguments as irab_arguments
    irab_arguments(sub.add_parser("irab", help="Source-backed case and relation views with full owner replay"))
    args = parser.parse_args()
    try:
        if args.command == "irab":
            from .irab_cli import run as irab_run
            result = irab_run(args)
        elif args.command == "awamil":
            from .awamil_cli import run as awamil_run
            result = awamil_run(args)
        elif args.command in ("operations", "rag", "rag-worker"):
            from . import operation_rag as rag_owner
            from .operations import OperationSearchIndex
            from tools.evidence_lifecycle_v1 import strict_loads
            if args.command == "operations":
                index = OperationSearchIndex()
                result = index.search(args.query, args.limit) if args.query else index.catalog()
            elif args.command == "rag-worker":
                payload = strict_loads(sys.stdin.buffer.read(rag_owner.MAX_REQUEST + 1), maximum_bytes=rag_owner.MAX_REQUEST)
                result = rag_owner.worker(payload)
            else:
                with args.request.open("rb") as stream:
                    request = rag_owner.request_from_bytes(stream.read(rag_owner.MAX_REQUEST + 1))
                if args.verify:
                    with args.verify.open("rb") as stream:
                        report = strict_loads(stream.read(rag_owner.MAX_RESULT + 1),
                                              maximum_bytes=rag_owner.MAX_RESULT, report=True)
                    result = rag_owner.verify(report, expected_request=request)
                else:
                    result = rag_owner.run(request)
        elif args.command == "catalog":
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
        if getattr(args, "output", None):
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        if args.command == "rag":
            if args.verify:
                return 0 if result["valid"] else 2
            return 0 if result["status"] in ("EXECUTED", "OWNER_ERROR") else 3
        if args.command in ("awamil", "irab") and args.verify:
            return 0 if result["valid"] else 2
        return 0
    except (ResourceLimit, MemoryError) as exc:
        print(json.dumps({"status": "RESOURCE_LIMIT", "message": str(exc),
                          "grants_language_license": False}, ensure_ascii=False))
        return 3
    except (CatalogError, RetrievalError, OSError, ValueError) as exc:
        print(json.dumps({"status": "INPUT_OR_SOURCE_ERROR", "message": str(exc),
                          "grants_language_license": False}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
