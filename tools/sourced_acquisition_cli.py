"""Run one explicit v3 acquisition goal on unchanged source text."""
from __future__ import annotations

import argparse
import json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=("pronunciation", "person", "nominal_syntax", "natural"), required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--source-id", default="input")
    parser.add_argument("--revision", default="1")
    parser.add_argument("--scope", default="default")
    parser.add_argument("--ending", choices=("wasl", "waqf"), default="wasl")
    parser.add_argument("--onset", choices=("word_initial", "connected"), default="word_initial")
    parser.add_argument("--summary", action="store_true", help="Display stable result fields; retain the same computation")
    args = parser.parse_args(argv)
    binding = dict(source_id=args.source_id, revision=args.revision, scope=args.scope,
                   ending=args.ending, onset=args.onset)
    if args.task == "pronunciation":
        from tools.connected_acquisition_v3 import read_acquired
        result = read_acquired(args.text, **binding)
    elif args.task == "natural":
        from tools.natural_acquisition_v3 import evaluate
        result = evaluate(args.text, **binding)
    else:
        from tools.acquired_person_nominal_v3 import evaluate
        result = evaluate(args.text, task=args.task, **binding)
    if args.summary:
        keys = {"schema", "law_id", "status", "verified", "shape_verified", "chain_complete",
                "task", "person", "nominal", "diagnostic_person_hypotheses", "selected_sense_ids",
                "candidate_sense_ids", "semantic_scope_complete", "assertion_polarity", "blocked_by",
                "world_truth_established", "author_intention_established", "referents_established"}
        result = {key: value for key, value in result.items() if key in keys}
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 2 if result.get("status") in {"INVALID_INPUT", "RESOURCE_EXHAUSTED", "VERIFICATION_FAILED",
        "VERIFICATION_UNAVAILABLE", "SOURCE_UNAVAILABLE", "SOURCE_EVIDENCE_UNAVAILABLE"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
