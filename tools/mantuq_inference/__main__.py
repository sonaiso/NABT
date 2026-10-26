"""Command-line research adapter; text search never supplies logical premises."""
import argparse
import json
from pathlib import Path

from . import EvaluationBudget, build_inventory, evaluate


import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from nabt import foundation

def _unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON object key: " + key)
        out[key] = value
    return out


def _load(path):
    raw = path.read_bytes()
    if len(raw) > 1048576:
        raise ValueError("request exceeds one MiB")
    return json.loads(raw, object_pairs_hook=_unique,
                      parse_constant=lambda s: (_ for _ in ()).throw(ValueError("nonfinite JSON number")))


def main():
    foundation.require_foundation('tools.mantuq_inference.__main__.main')
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    sub.add_parser("catalogue")
    run = sub.add_parser("evaluate")
    run.add_argument("request", type=Path)
    run.add_argument("--max-readings", type=int, default=64)
    find = sub.add_parser("search")
    find.add_argument("query")
    find.add_argument("--limit", type=int, default=10)
    pipeline = sub.add_parser("pipeline")
    pipeline.add_argument("query")
    pipeline.add_argument("requests", type=Path, help="object mapping installed policy IDs to explicit requests")
    pipeline.add_argument("--limit", type=int, default=10, help="displayed retrieval candidates only")
    pipeline.add_argument("--max-policies", type=int)
    args = parser.parse_args()
    if args.operation == "catalogue":
        out = build_inventory()
    elif args.operation == "search":
        from .retrieval import search
        out = search(args.query, limit=args.limit)
    else:
        try:
            if args.operation == "pipeline":
                from .pipeline import run
                out = run(args.query, _load(args.requests), display_limit=args.limit, max_policies=args.max_policies)
            else:
                out = evaluate(_load(args.request), budget=EvaluationBudget(max_readings=args.max_readings))
        except (ValueError, OSError) as exc:
            out = {"status": "INVALID", "reason": str(exc), "conditional_consequence": False,
                   "all_arabic_complete": False, "world_truth_established": False}
    print(json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if out.get("status") not in {"INVALID", "SOURCE_ERROR", "VERIFICATION_UNAVAILABLE"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
