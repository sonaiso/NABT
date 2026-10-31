"""Tiny-budget observation of pretty-print allocation before routing rejection."""
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
    payload = "x" * 32
    for _ in range(8):
        payload = [payload]
    real_dumps = json.dumps
    compact = real_dumps(payload, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    pretty = real_dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)
    calls = []

    def observed_dumps(value, *positional, **keywords):
        materialized = real_dumps(value, *positional, **keywords)
        calls.append({"indent": keywords.get("indent"),
                      "serialized_utf8_bytes": len(materialized.encode("utf-8"))})
        return materialized

    with patch.object(routing, "MAX_ROUTING_DOCUMENT_BYTES", 128), \
            patch.object(routing.json, "dumps", side_effect=observed_dumps):
        try:
            value = routing.routing_document_text(payload)
            outcome = {"type": "ACCEPTED", "returned_bytes": len(value.encode("utf-8"))}
        except Exception as error:
            outcome = {"type": type(error).__name__, "message": str(error)}
            if hasattr(error, "as_dict"):
                outcome["structured"] = error.as_dict()

    over = any(call["indent"] == 2 and call["serialized_utf8_bytes"] > 128 for call in calls)
    limited = outcome.get("structured", {}).get("code") == "RESOURCE_LIMIT"
    after = {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
    report = {
        "schema": "nabt.operator-context.pretty-budget-observation.v1",
        "repository_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "scope": "Tiny-budget Python output probe; no large allocation, native run, or semantic evaluation.",
        "code_and_spec_sha256_before": before,
        "code_and_spec_sha256_after": after,
        "sources_unchanged": before == after,
        "temporary_document_byte_budget": 128,
        "literal_input": payload,
        "canonical_bytes": len(compact),
        "pretty_bytes_before_final_newline": len(pretty.encode("utf-8")),
        "pretty_bytes_with_final_newline": len((pretty + "\n").encode("utf-8")),
        "expected_preflight_behavior": "RESOURCE_LIMIT without materializing the complete oversized pretty document",
        "observed_json_dumps_calls": calls,
        "oversized_pretty_json_fully_materialized": over,
        "observed_outcome": outcome,
        "interpretation": (
            "The canonical form fits the limit, but oversized pretty JSON is fully materialized before RESOURCE_LIMIT rejection."
            if over and limited else
            "Oversized pretty JSON was fully materialized; inspect the recorded outcome."
            if over else
            "The oversized pretty output was rejected with RESOURCE_LIMIT without whole-document json.dumps materialization."
            if limited else
            "No oversized whole-document json.dumps materialization was observed; inspect the recorded outcome."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "canonical_bytes": len(compact),
                      "pretty_bytes": len((pretty + "\n").encode("utf-8")),
                      "oversized_pretty_json_fully_materialized": over,
                      "outcome": outcome, "sources_unchanged": before == after}, ensure_ascii=False))


if __name__ == "__main__":
    main()
