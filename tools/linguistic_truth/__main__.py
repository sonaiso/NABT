"""Inspect lexical evidence or request source-bound A116/Lean claim checks.

`certify` is the strict proof entry. `acquire` and `pipeline` expose diagnostic
acquisition with conditional premises; their success is not end-to-end proof.
"""
import argparse
import json
from pathlib import Path

from .runtime import AcquisitionBudget, acquire


import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from nabt import foundation

def main():
    foundation.require_foundation('tools.linguistic_truth.__main__.main')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--response-contract", choices=("legacy", "scoped-v1"), default="legacy")
    sub = parser.add_subparsers(dest="operation", required=True)
    sub.add_parser("catalogue")
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)
    for operation in ("certify", "acquire", "pipeline"):
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
    request = {key: value for key, value in vars(args).items() if key != "response_contract"}
    resolved = args.operation in {"catalogue", "search"}
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
            from dataclasses import asdict
            request = {"text": text, **options, "budget": asdict(options["budget"])}
            if args.operation == "pipeline":
                request.update(display_limit=args.limit, reverse_candidates=args.reverse_candidates)
            resolved = True
            if args.operation == "certify":
                from .certified import acquire_certified
                result = acquire_certified(text, **options)
            elif args.operation == "pipeline":
                from .pipeline import run
                result = run(text, display_limit=args.limit,
                             reverse_candidates=args.reverse_candidates, **options)
            else:
                result = acquire(text, **options)
    except (OSError, ValueError) as exc:
        result = {"status": "INVALID_INPUT", "reason": str(exc), "world_truth_established": False,
                  "all_arabic_complete": False}
    status = result.get("status", result.get("acquisition", {}).get("status"))
    code = 2 if status in {"INVALID_INPUT", "SOURCE_UNAVAILABLE", "VERIFICATION_UNAVAILABLE"} else 0
    if args.operation == "certify":
        # Exit zero is reserved for actual complete language acceptance. A
        # checked partial claim or honest deferral cannot masquerade as it.
        if code != 2:
            code = 0 if result.get("strict_language_accepted") is True else 3
    if args.response_contract == "scoped-v1":
        from nabt.transport_contract import _envelope, _claim_paths
        result = _envelope(entrypoint="tools.linguistic_truth.__main__.main", command=args.operation,
            resolved_request=request, result=result, policy_id="linguistic-truth." + args.operation + ".scoped-v1",
            authority="A116_CONDITIONAL_CANDIDATE_CONTRACT" if args.operation == "certify" else "DIAGNOSTIC_ONLY",
            input_binding="RESOLVED_CHILD_INPUT" if resolved else "CLI_ARGUMENTS_ONLY",
            claim_paths=_claim_paths(result, "lexical") if args.operation == "certify" else [],
            unresolved_premises=["PYTHON_ACQUISITION_NOT_KERNEL_PROVED", "INTENDED_SENSE_NOT_ESTABLISHED"])
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
