"""Check complete source/query bytes under the finite explicit-subject law."""
import argparse
import json
from pathlib import Path

from .runtime import InferenceBudget, evaluate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("query", type=Path)
    parser.add_argument("--source-id", default="user_text")
    parser.add_argument("--revision", default="1")
    parser.add_argument("--scope", default="default")
    parser.add_argument("--time", default="unspecified")
    parser.add_argument("--max-clauses", type=int, default=256)
    parser.add_argument("--max-readings", type=int, default=64)
    parser.add_argument("--max-atoms", type=int, default=512)
    parser.add_argument("--max-closure-steps", type=int, default=512)
    args = parser.parse_args()
    try:
        with args.source.open("rb") as stream:
            source = stream.read(65537)
        with args.query.open("rb") as stream:
            query = stream.read(8193)
        result = evaluate(source, query, source_id=args.source_id, revision=args.revision,
            scope=args.scope, time=args.time, budget=InferenceBudget(max_clauses=args.max_clauses,
                max_readings=args.max_readings, max_atoms=args.max_atoms,
                max_closure_steps=args.max_closure_steps))
    except (OSError, ValueError) as exc:
        result = {"status": "INVALID_INPUT", "reason": str(exc), "verified": False,
                  "all_arabic_complete": False, "world_truth_established": False}
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 2 if result["status"] in {"INVALID_INPUT", "SOURCE_UNAVAILABLE", "VERIFICATION_UNAVAILABLE"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
