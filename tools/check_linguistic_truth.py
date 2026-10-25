#!/usr/bin/env python3
"""Compare the production Python calculus against actual compiled Lean fixtures.

Finite native/Python conformance is neither a refinement theorem, a source
interpretation proof, nor completeness of Arabic. The source ledger is an
explicit premise of both implementations.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from tools.linguistic_truth.calculus import LAW_ID, canonical_json, evaluate_request


def check(*, executable=None):
    path = Path(executable or os.environ.get("NABT_LINGUISTIC_TRUTH_CHECKER",
                                           ROOT / "formal/.lake/build/bin/linguisticTruth"))
    run = subprocess.run([str(path), "--export"], capture_output=True, timeout=60, check=True)
    rows = [json.loads(line) for line in run.stdout.splitlines()]
    if len(rows) != 786:
        raise ValueError("native exporter fixture count changed; expected 786")
    mismatches = []
    statuses, verdicts = Counter(), Counter()
    for index, row in enumerate(rows):
        if (set(row) != {"law_id", "row_kind", "request", "response"}
                or row["law_id"] != LAW_ID or row["row_kind"] != "request"):
            raise ValueError("native exporter fixture envelope differs")
        observed = evaluate_request(row["request"])
        expected = row["response"]
        statuses[expected["status"]] += 1
        verdicts.update(r["verdict"] for r in expected["rows"])
        # Canonical JSON comparison keeps false distinct from 0, even in a
        # malicious or malformed response from an unexpected executable.
        if canonical_json(observed) != canonical_json(expected):
            mismatches.append({"index": index, "expected": expected, "observed": observed})
    return {"schema": "nabt.linguistic-truth-conformance.v1", "law_id": LAW_ID,
            "evidence_kind": "finite_native_python_conformance",
            "checks": {"request_response": len(rows)}, "total": len(rows),
            "statuses": dict(sorted(statuses.items())), "guard_verdicts": dict(sorted(verdicts.items())),
            "mismatches": mismatches, "pass": not mismatches,
            "export_sha256": hashlib.sha256(run.stdout).hexdigest(),
            "adapter_sha256": hashlib.sha256((ROOT / "tools/linguistic_truth/calculus.py").read_bytes()).hexdigest(),
            "qualified_guard_module_sha256": hashlib.sha256((ROOT / "tools/mantuq_inference/evaluator.py").read_bytes()).hexdigest(),
            "python_refinement_theorem": False, "native_json_parser_refinement_theorem": False,
            "all_arabic_complete": False, "source_interpretation_proved": False,
            "world_truth_established": False,
            "bounds": {"designations": 128, "relations": 128, "known_atoms": 1024,
                       "proposed_candidates": 256, "ledger_scan_budget": 4096,
                       "input_line_bytes": 1048576, "text_field_utf8_bytes": 16384}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", help="Build the pinned native checker before comparing")
    parser.add_argument("--executable", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.lake:
        subprocess.run([args.lake, "build", "linguisticTruth"], cwd=ROOT / "formal", check=True)
    result = check(executable=args.executable)
    raw = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw)
    print(raw, end="")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
