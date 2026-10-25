"""Inspect the ledger or acquire explicit intended use from raw Arabic text."""
import argparse
import json
from pathlib import Path

from .runtime import AcquisitionBudget, acquire


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    sub.add_parser("catalogue")
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)
    for operation in ("acquire", "pipeline"):
        intake = sub.add_parser(operation)
        source = intake.add_mutually_exclusive_group(required=True)
        source.add_argument("--text")
        source.add_argument("--file", type=Path)
        intake.add_argument("--profile", help="explicit convention assumption; omission retains pending profiles")
        intake.add_argument("--source-id", default="user_text")
        intake.add_argument("--subject", default="unspecified")
        intake.add_argument("--time", default="unspecified")
        intake.add_argument("--context", default="unspecified")
        intake.add_argument("--max-occurrences", type=int, default=256)
        intake.add_argument("--max-readings", type=int, default=2048)
        intake.add_argument("--max-native-scan", type=int, default=4096)
        if operation == "pipeline":
            intake.add_argument("--limit", type=int, default=10)
            intake.add_argument("--reverse-candidates", action="store_true")
    args = parser.parse_args()
    try:
        if args.operation == "catalogue":
            from .inventory import build_inventory
            result = build_inventory()
        elif args.operation == "search":
            from .retrieval import LinguisticTruthSearchIndex
            result = LinguisticTruthSearchIndex().search(args.query, limit=args.limit)
        else:
            if args.file:
                with args.file.open("rb") as stream:
                    text = stream.read(65537)
            else:
                text = args.text
            options = {"profile_id": args.profile, "source_id": args.source_id,
                       "subject": args.subject, "time": args.time, "context": args.context,
                       "budget": AcquisitionBudget(max_occurrences=args.max_occurrences,
                           max_readings=args.max_readings, max_native_scan=args.max_native_scan)}
            if args.operation == "pipeline":
                from .pipeline import run
                result = run(text, display_limit=args.limit,
                             reverse_candidates=args.reverse_candidates, **options)
            else:
                result = acquire(text, **options)
    except (OSError, ValueError) as exc:
        result = {"status": "INVALID_INPUT", "reason": str(exc), "world_truth_established": False,
                  "all_arabic_complete": False}
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    status = result.get("status", result.get("acquisition", {}).get("status"))
    return 2 if status in {"INVALID_INPUT", "SOURCE_UNAVAILABLE", "VERIFICATION_UNAVAILABLE"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
