#!/usr/bin/env python3
"""Compare the actual Lean exporter with the optional Python guard adapter.

This finite conformance check is separate from general Lean soundness and from
Arabic interpretation, source truth, or held-out language acquisition.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from tools.mantuq_inference import guard_verdict, opposition_shape


def check(*, executable=None):
    path = Path(executable or os.environ.get("NABT_QUALIFIED_INFERENCE_EXPORT", ROOT / "formal/.lake/build/bin/exportQualifiedInference"))
    run = subprocess.run([str(path)], capture_output=True, timeout=60, check=True)
    rows = [json.loads(line) for line in run.stdout.splitlines()]
    counts = {"guard": 0, "opposition_shape": 0}
    mismatches = []
    for index, row in enumerate(rows):
        if row.get("law_id") != "nabt.qualified-inference.v1":
            raise ValueError("native exporter law ID differs")
        if row.get("row_kind") == "guard":
            observed = guard_verdict(row["kind"], row["requirements"], row["known"])
            expected = row["verdict"]
            counts["guard"] += 1
        elif row.get("row_kind") == "opposition_shape":
            observed = opposition_shape(row["antecedent"], row["consequent"], row["absent"], row["conclusion"])
            expected = row["accepted"]
            counts["opposition_shape"] += 1
        else:
            raise ValueError("unknown native exporter row kind")
        if type(observed) is not type(expected) or observed != expected:
            mismatches.append({"index": index, "expected": expected, "observed": observed})
    if counts != {"guard": 2906, "opposition_shape": 128}:
        raise ValueError("native exporter case inventory changed")
    return {"schema": "nabt.qualified-inference-conformance.v1", "checks": counts,
            "total": len(rows), "mismatches": mismatches, "pass": not mismatches,
            "export_sha256": hashlib.sha256(run.stdout).hexdigest(),
            "python_refinement_theorem": False, "all_arabic_complete": False,
            "world_truth_established": False, "evidence_kind": "finite_native_python_conformance"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", help="Build the pinned native exporter before checking")
    parser.add_argument("--executable", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.lake:
        subprocess.run([args.lake, "build", "exportQualifiedInference"],
                       cwd=ROOT / "formal", check=True)
    result = check(executable=args.executable)
    raw = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw)
    print(raw, end="")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
