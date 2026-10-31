"""Bounded observation of aggregate routing JSON before serialization.

Uses only a 128-byte temporary limit and a 202-byte canonical payload.
Does not edit production, test files, or frozen acceptance data.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from tools.grammar_catalog import routing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = ("tools/grammar_catalog/routing.py", "tools/grammar_catalog/retrieval.py",
             "tools/grammar_catalog/__main__.py", "docs/OPERATOR_CONTEXT_V1_SPEC.md")
    before = {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
    shared = "x" * 64
    payload = [shared, shared, shared]
    real_dumps = json.dumps
    expected_raw = real_dumps(payload, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":"), allow_nan=False).encode("utf-8")
    calls = []

    def observed_dumps(value, *positional, **keywords):
        calls.append({"value_count": len(value),
                      "unique_string_objects": len({id(item) for item in value}),
                      "string_bytes": [len(item.encode("utf-8")) for item in value]})
        return real_dumps(value, *positional, **keywords)

    with patch.object(routing, "MAX_ROUTING_DOCUMENT_BYTES", 128), \
            patch.object(routing.json, "dumps", side_effect=observed_dumps):
        try:
            routing._snapshot_document(payload, "aggregate budget probe")
            outcome = {"type": "ACCEPTED"}
        except Exception as error:
            outcome = {"type": type(error).__name__, "message": str(error)}
            if hasattr(error, "as_dict"):
                outcome["structured"] = error.as_dict()

    after = {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
    report = {
        "schema": "nabt.operator-context.aggregate-budget-observation.v1",
        "repository_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "scope": "Tiny-budget Python API probe; no large allocation, native run, or semantic evaluation.",
        "code_and_spec_sha256_before": before,
        "code_and_spec_sha256_after": after,
        "sources_unchanged": before == after,
        "temporary_document_byte_budget": 128,
        "literal_input": payload,
        "input_unique_string_objects": len({id(item) for item in payload}),
        "expected_canonical_bytes": len(expected_raw),
        "expected_canonical_sha256": sha256(expected_raw).hexdigest(),
        "expected_preflight_behavior": "RESOURCE_LIMIT before aggregate serialization",
        "observed_serializer_calls": calls,
        "oversized_aggregate_reached_serializer": bool(calls),
        "observed_outcome": outcome,
        "interpretation": (
            "Pre-fix behavior enters JSON serialization with an aggregate already over the declared byte limit; the final error is correct but occurs after allocation/work that may amplify shared strings."
            if calls and outcome.get("structured", {}).get("code") == "RESOURCE_LIMIT" else
            "Oversized aggregate reached JSON serialization; inspect the recorded outcome."
            if calls else
            "Oversized aggregate was rejected with RESOURCE_LIMIT before whole-document JSON serialization."
            if outcome.get("structured", {}).get("code") == "RESOURCE_LIMIT" else
            "No whole-document JSON serialization was observed; inspect the recorded outcome."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output),
                      "canonical_bytes": len(expected_raw),
                      "serializer_calls": len(calls), "outcome": outcome,
                      "sources_unchanged": before == after}, ensure_ascii=False))


if __name__ == "__main__":
    main()
