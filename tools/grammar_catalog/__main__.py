"""Source catalogue, proposal search and native-required conditional routing."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .catalog import CatalogError, build_catalog
from .retrieval import RetrievalError, SearchIndex
from .routing import evaluate_candidates, evaluate_diagnostic_candidates


import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from nabt import foundation


def _frames_json(path):
    """Do not lose duplicate fields or nonfinite values before frame checking."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_FRAME_FIELD: " + key)
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError("NONFINITE_FRAME_NUMBER: " + value)

    # The installed inventory has 24 frames, each with a 64 KiB runtime limit.
    maximum = 24 * 65_536
    with path.open("rb") as handle:
        raw = handle.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError("FRAME_FILE_RESOURCE_LIMIT")
    return json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=unique,
                      parse_constant=nonfinite)


def main():
    foundation.require_foundation('tools.grammar_catalog.__main__.main')
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
    for name, help_text in (
            ("route", "Require live Lean control checks with complete inventory fallback (v2)"),
            ("route-diagnostic", "Python replay only, without native authority (legacy v1)")):
        route = sub.add_parser(name, help=help_text)
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
                frames = _frames_json(args.frames)
                evaluate = evaluate_candidates if args.command == "route" else evaluate_diagnostic_candidates
                result = evaluate(index, [r["id"] for r in found["candidates"]], frames,
                                  budget=args.budget)
                result["retrieval"] = found
        text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        if args.command == "route":
            if result["status"] == "VERIFICATION_UNAVAILABLE":
                return 2
            # Zero attests only completion of the bounded conditional control
            # scan, never full linguistic acceptance or premise acquisition.
            return 0 if result["conditional_evaluation_complete"] else 3
        return 0
    except (CatalogError, RetrievalError, OSError, ValueError) as exc:
        print(json.dumps({"status": "INPUT_OR_SOURCE_ERROR", "message": str(exc),
                          "grants_language_license": False}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
