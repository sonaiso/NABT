#!/usr/bin/env python3
"""Fresh native Lean export and independent source-relative reading comparison."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.classical_reference_readings import EXPORT, conformance, benchmark_reference_constructions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    subprocess.run([args.lake, "build", "exportClassicalReferenceReadings"], cwd=ROOT / "formal", check=True)
    raw = subprocess.check_output([str(ROOT / "formal/.lake/build/bin/exportClassicalReferenceReadings")])
    fresh = json.loads(raw)
    if fresh != json.loads(EXPORT.read_bytes()):
        raise ValueError("Installed conditional reading table differs from fresh Lean export")
    correspondence = conformance(fresh)
    benchmark = benchmark_reference_constructions()
    valid = (correspondence["valid"] and benchmark["source_replay_valid"] and
             benchmark["exact_set_matches"] == benchmark["case_count"] == benchmark["order_matches"] and
             benchmark["matched_reading_count"] == benchmark["expected_reading_count"] == benchmark["returned_reading_count"])
    report = {"valid": valid, "conformance": correspondence, "benchmark": benchmark,
              "free_text_parser_evaluated": False, "acquisition_of_premises_proved": False}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"valid": valid, "finite_inputs": correspondence["input_count"],
                      "reference_constructions": benchmark["case_count"],
                      "reference_readings": benchmark["matched_reading_count"],
                      "free_text_parser_evaluated": False}))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
