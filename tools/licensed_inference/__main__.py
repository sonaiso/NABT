"""Check complete source/query bytes under the finite explicit-subject law."""
import argparse
import json
from pathlib import Path

from .runtime import InferenceBudget, evaluate


import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from nabt import foundation

def main():
    foundation.require_foundation('tools.licensed_inference.__main__.main')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--response-contract", choices=("legacy", "scoped-v1"), default="legacy")
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
    request = {"source_path": args.source, "query_path": args.query}
    resolved = False
    try:
        with args.source.open("rb") as stream:
            source = stream.read(65537)
        with args.query.open("rb") as stream:
            query = stream.read(8193)
        from dataclasses import asdict
        budget = InferenceBudget(max_clauses=args.max_clauses, max_readings=args.max_readings,
            max_atoms=args.max_atoms, max_closure_steps=args.max_closure_steps)
        options = dict(source_id=args.source_id, revision=args.revision, scope=args.scope, time=args.time)
        request = dict(source=source, query=query, **options, budget=asdict(budget))
        resolved = True
        if args.response_contract == "scoped-v1":
            from tools.transport_adapters import certify_inference
            result = certify_inference(source, query, **options, budget=asdict(budget))
        else:
            result = evaluate(source, query, **options, budget=budget)
    except (OSError, ValueError) as exc:
        result = {"status": "INVALID_INPUT", "reason": str(exc), "verified": False,
                  "all_arabic_complete": False, "world_truth_established": False}
    code = 2 if result["status"] in {"INVALID_INPUT", "SOURCE_UNAVAILABLE", "VERIFICATION_UNAVAILABLE"} else 0
    if args.response_contract == "scoped-v1":
        from nabt.transport_contract import _envelope, _claim_paths
        result = _envelope(entrypoint="tools.licensed_inference.__main__.main", command="evaluate",
            resolved_request=request, result=result, policy_id="licensed-inference.evaluate.scoped-v1",
            authority="SOURCE_RELATIVE_FINITE_INFERENCE", claim_paths=_claim_paths(result, "inference"),
            input_binding="RESOLVED_CHILD_INPUT" if resolved else "CLI_ARGUMENTS_ONLY",
            unresolved_premises=["FIXED_ACTIVE_VOICE_GRAMMAR", "SOURCE_ASSERTIONS_ARE_PREMISES_NOT_OBSERVATIONS",
                                 "INTENDED_SENSE_AND_HISTORICAL_TESTIMONY_NOT_ESTABLISHED"])
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
