"""Replay the exposed PR 34/acquisition integration fixture without relabeling."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from tools.acquired_inference import evaluate, verify  # noqa: E402

PIN = "985e0be8faa597ca0d1675e3ae7ee5eb7c6f1b086d95c589fadab635275030da"


def run():
    path = ROOT / "evidence/aligned_acquisition_v1/integration/cases.json"
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError("integration fixture changed")
    binding = dict(source_id="integration", revision="1", scope="source", time="episode1",
                   source_ending="wasl", query_ending="wasl")
    rows = []
    for case in json.loads(raw)["cases"]:
        result = evaluate(case["source"], case["query"], **binding)
        replay = verify(result, source=case["source"], query=case["query"], **binding)
        licensed = result.get("licensed_inference") or {}
        matches = (licensed.get("status") == case["inference_status"] and
                   result["chain_complete"] is case["chain_complete"] and
                   replay.get("replay_matches") is True and replay["valid"] is case["chain_complete"])
        rows.append({"id": case["id"], "matches": matches,
                     "expected_chain_complete": case["chain_complete"],
                     "expected_inference_status": case["inference_status"],
                     "receipt": result, "replay": replay})
    return {"schema": "nabt.acquired-inference-regression-result.v1", "fixture_sha256": PIN,
            "scope": "exposed integration regression; not a new held-out linguistic matrix",
            "passed": all(r["matches"] for r in rows), "cases": len(rows),
            "matching_contracts": sum(r["matches"] for r in rows),
            "complete_chains": sum(r["receipt"]["chain_complete"] for r in rows),
            "positive_inference_cases": sum(r["expected_inference_status"] == "SUPPORTED" for r in rows),
            "positive_complete_chains": sum(r["receipt"]["chain_complete"] and
                r["expected_inference_status"] == "SUPPORTED" for r in rows),
            "all_arabic_complete": False, "world_truth_established": False, "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
