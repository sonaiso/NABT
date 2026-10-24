#!/usr/bin/env python3
"""Replay raw duplicate-key cases against the current recursive probe.

The pre-fix responses in before.json remain immutable. The script prints the
current results without overwriting either historical record.
"""

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BINARY = ROOT / "formal/.lake/build/bin/recursiveBridgeProbe"


def run():
    before = json.loads((HERE / "before.json").read_text())
    results = []
    for old in before["results"]:
        payload = (old["request_json"] + "\n").encode("utf-8")
        completed = subprocess.run([str(BINARY)], input=payload, capture_output=True,
                                   timeout=30, check=True)
        assert completed.stderr == b""
        response = json.loads(completed.stdout)
        assert response["status"] == "ERROR"
        assert response["error"] == "INVALID_INPUT"
        assert response["message"] == "duplicate JSON object key"
        results.append({"case": old["case"], "request_sha256": sha256(payload).hexdigest(),
                        "response": response, "returncode": completed.returncode})

    # A canonical encoding of the formerly overwritten object remains valid;
    # invalid input does not poison the following independent JSONL request.
    control = json.dumps(json.loads(before["results"][1]["request_json"]),
                         ensure_ascii=False, separators=(",", ":"))
    bad = before["results"][0]["request_json"]
    completed = subprocess.run([str(BINARY)], input=(bad + "\n" + control + "\n").encode(),
                               capture_output=True, timeout=30, check=True)
    rejected, accepted = [json.loads(row) for row in completed.stdout.splitlines()]
    assert rejected["error"] == "INVALID_INPUT"
    assert accepted["status"] == "OK" and accepted["verdict"] == "SOURCE_ONLY"
    assert accepted["source_bound"] is True

    # Many distinct unknown keys exercise per-object balanced-set bookkeeping.
    # The request fits the byte budget and is rejected for undeclared fields.
    large = {"op": "core_number", "registry_id": "development.protocol",
             "tree": {"op": "leaf", "seed": {"kind": "lexical", "entry": 0}}}
    large.update({f"unknown_{index}": 0 for index in range(40000)})
    payload = json.dumps(large, separators=(",", ":")).encode() + b"\n"
    assert len(payload) <= 1048576
    started = time.monotonic()
    completed = subprocess.run([str(BINARY)], input=payload, capture_output=True,
                               timeout=30, check=True)
    elapsed = time.monotonic() - started
    rejection = json.loads(completed.stdout)
    assert rejection["error"] == "INVALID_INPUT"
    assert rejection["message"] == "an object contains an undeclared field"

    return {
        "schema": "nabt.recursive-duplicate-key-review.v1", "phase": "after_fix",
        "probe_sha256": sha256(BINARY.read_bytes()).hexdigest(),
        "results": results,
        "following_line_control": {"invalid_rejected": True, "valid_source_bound": True,
                                   "valid_verdict": accepted["verdict"]},
        "many_distinct_keys_control": {"unknown_keys": 40000, "input_bytes": len(payload),
                                       "elapsed_seconds": round(elapsed, 6), "response": rejection},
        "changed_files": ["formal/RecursiveBridgeProbe.lean", "tests/test_recursive_bridge_probe.py"],
        "semantic_proofs_changed": False,
        "shared_ProbeJson_changed": False,
    }


if __name__ == "__main__":
    sys.stdout.write(json.dumps(run(), ensure_ascii=False, indent=2) + "\n")
