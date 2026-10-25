"""Run frozen hand-authored controls; report coverage separately from correctness."""
import argparse
from collections import Counter
import json
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.lexical_completion import CompletionEngine, assess, sha

CASES = ROOT / "evidence/lexical_completion_v1/benchmark_cases.json"
CASES_SHA = "9f0b18ae2b38cf0a3b8d64e57d3b64a2623ef83998942c64b1473f4698408387"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    raw = CASES.read_bytes()
    if sha(raw) != CASES_SHA:
        raise ValueError("FROZEN_CONTROLS_CHANGED")
    fixture = json.loads(raw)
    start = time.perf_counter()
    engine = CompletionEngine()
    setup = time.perf_counter() - start
    results = []
    for case in fixture["cases"]:
        started = time.perf_counter()
        actual = assess(case["request"], engine=engine)
        native = actual.get("native_result", {})
        licensed = (None if native.get("all_targets_licensed") is None else
                    sum(c["targets_licensed"] for c in native["combinations"]))
        matched = (actual["native_checked"] and actual["status"] == case["expected_status"]
                   and native["combination_count"] == case["expected_combinations"]
                   and licensed == case["expected_licensed_combinations"])
        results.append({"id": case["id"], "matched_control": matched, "status": actual["status"],
                        "combination_count": native.get("combination_count"),
                        "licensed_combinations": licensed, "seconds": time.perf_counter() - started})
    if sha(CASES.read_bytes()) != CASES_SHA:
        raise ValueError("CONTROLS_CHANGED_DURING_RUN")
    report = {"schema": "nabt.lexical-completion.benchmark.v1", "fixture_sha256": CASES_SHA,
              "protocol": fixture["review_status"], "scope": fixture["scope"],
              "matched_controls": sum(r["matched_control"] for r in results), "controls": len(results),
              "outcomes": dict(Counter(r["status"] for r in results)),
              "linguistic_accuracy_not_measured": True, "whole_arabic_complete": False,
              "inventory": engine.inventory(), "setup_seconds": setup,
              "elapsed_seconds": time.perf_counter() - start,
              "environment": {"python": platform.python_version(), "system": platform.system(),
                              "machine": platform.machine(), "lean": "leanprover/lean4:v4.34.1"},
              "results": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("matched_controls", "controls", "outcomes", "whole_arabic_complete")}))
    return 0 if all(r["matched_control"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
