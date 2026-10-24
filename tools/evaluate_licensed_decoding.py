#!/usr/bin/env python3
"""Paired current-proposer measurement and a separately labelled retry experiment."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import licensed_decoding as decoding
from tools import explainable_pilot as pilot
from tools import evaluate_explainable_pilot as previous
from tools.source_codec import verify_source
from nabt.errors import NabtError

PROTOCOL = ROOT / "evidence/licensed_decoding/protocol.json"


def metric(passed, total):
    return {"passed": passed, "total": total, "rate": passed / total if total else None}


def prefix_success(attempts, expected, k):
    return any(row.get("accepted") is True and row.get("answer_status") == expected
               for row in attempts[:k])


def timing(samples):
    ordered = sorted(samples)
    return {"samples_seconds": samples, "n": len(samples),
            "p95_seconds": ordered[math.ceil(.95 * len(ordered)) - 1] if ordered else None,
            "estimator": "nearest rank of local samples; no population confidence claim"}


def evaluate(*, checker=None):
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    cases = json.loads(previous.CASES.read_text(encoding="utf-8"))["cases"]
    if (protocol["case_file"] != str(previous.CASES.relative_to(ROOT))
            or type(protocol["comparison_k"]) is not int or protocol["comparison_k"] != 1
            or protocol["candidate_law"] != pilot.ground.LAW_ID
            or type(protocol["repeats_per_case"]) is not int or not 1 <= protocol["repeats_per_case"] <= 20
            or len({case["id"] for case in cases}) != len(cases)):
        raise pilot.PilotError("INVALID_INPUT", "Experiment protocol or case identity is inconsistent")
    binary, setup_error = None, None
    try:
        binary = pilot.checker_path(checker)
    except pilot.PilotError as exc:
        setup_error = exc
    rows, baseline_samples, candidate_samples = [], [], []
    for case_index, case in enumerate(cases):
        row = {"id": case["id"], "expected": case["expected"],
               "paired_status": False, "source_roundtrip": False, "native_replay": False,
               "pass_at_1": False, "fault_first_rejected": False,
               "fault_pass_at_1": False, "fault_pass_within_2": False,
               "baseline_seconds": [], "candidate_seconds": [],
               "fault_attempts": [{"index": i, "accepted": False, "executed": False,
                                   "answer_status": None, "error": "SETUP_NOT_COMPLETED"} for i in range(2)]}
        rows.append(row)
        try:
            raw, query = previous.inputs(case)
            row["source_sha256"], row["query_sha256"] = pilot.sha(raw), pilot.sha(query)
            if setup_error is not None:
                raise setup_error
            paired = True
            for repeat in range(protocol["repeats_per_case"]):
                values = {}
                order = ("baseline", "candidate") if (case_index + repeat) % 2 == 0 else ("candidate", "baseline")
                for arm in order:
                    start = time.perf_counter()
                    if arm == "baseline":
                        values[arm] = pilot.answer(raw, query, checker=binary)
                    else:
                        candidate = pilot.wire(pilot.propose_certificate(raw, query)).encode("utf-8")
                        values[arm] = decoding.run_candidates(raw, query, [candidate], k=1,
                            seconds=protocol["verification_seconds"], checker=binary)
                    row[arm + "_seconds"].append(time.perf_counter() - start)
                answer, report = values["baseline"], values["candidate"]
                paired &= (answer["answer"]["status"] == case["expected"]
                           and report["answer"] is not None
                           and report["answer"]["answer"]["status"] == case["expected"])
            row["paired_status"] = paired
            row["pass_at_1"] = prefix_success(report["attempts"], case["expected"], 1)
            row["source_roundtrip"] = (verify_source(raw, report["source"])
                                       and verify_source(query, report["query"]))
            row["native_replay"] = decoding.verify_selected(raw, query, [candidate], report, checker=binary)["verified"]
            altered = deepcopy(pilot.strict_json(candidate))
            # Actual binding attack; same proposal structure and all original traces.
            altered["query_text"] = "هل مختلف هو مختلف؟\n"
            fault_candidates = [pilot.wire(altered).encode("utf-8"), candidate]
            fault = decoding.run_candidates(raw, query, fault_candidates, k=2, checker=binary,
                                           seconds=protocol["verification_seconds"])
            row["fault_first_rejected"] = (fault["attempts"][0].get("error") == "CERTIFICATE_REJECTED"
                                            and fault["attempts"][0]["accepted"] is False)
            row["fault_pass_at_1"] = prefix_success(fault["attempts"], case["expected"], 1)
            row["fault_pass_within_2"] = prefix_success(fault["attempts"], case["expected"], 2)
            row["fault_attempts"] = fault["attempts"]
        except (pilot.PilotError, NabtError) as exc:
            row["error"] = exc.code
            for attempt in row["fault_attempts"]:
                if attempt.get("error") == "SETUP_NOT_COMPLETED":
                    attempt["error"] = exc.code
        baseline_samples.extend(row["baseline_seconds"])
        candidate_samples.extend(row["candidate_seconds"])
    total = len(rows)
    names = ("paired_status", "source_roundtrip", "native_replay", "pass_at_1", "fault_first_rejected",
             "fault_pass_at_1", "fault_pass_within_2")
    metrics = {name: metric(sum(row[name] for row in rows), total) for name in names}
    gates = ("paired_status", "source_roundtrip", "native_replay", "pass_at_1",
             "fault_first_rejected", "fault_pass_within_2")
    files = [PROTOCOL, previous.CASES, ROOT / "tools/evaluate_licensed_decoding.py",
             ROOT / "tools/licensed_decoding.py", ROOT / "tools/explainable_pilot.py",
             ROOT / "tools/verified_reading.py", ROOT / "tools/source_codec.py",
             ROOT / "src/nabt/alphabet.py", ROOT / "src/nabt/codec.py"]
    return {"schema": "nabt.decoding-measurement.v1", "created_utc": datetime.now(timezone.utc).isoformat(),
            "protocol": protocol, "hidden": False, "cases": rows, "metrics": metrics,
            "provenance": {str(p.relative_to(ROOT)): pilot.file_sha(p) for p in files},
            "git_parent_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "environment": {"python": sys.version, "platform": platform.platform(),
                            "checker_sha256": pilot.file_sha(binary) if binary is not None else None},
            "timing": {"baseline": timing(baseline_samples), "candidate": timing(candidate_samples)},
            "unmeasured": {k: None for k in ("hidden_accuracy", "neural_quality_gain", "llm_token_cost",
                "gpu_memory", "human_explanation_fidelity", "model_internal_causality", "grammar_masking_gain")},
            "passed": total == protocol["expected_cases"] and all(metrics[g]["passed"] == total for g in gates)
                      and metrics["fault_pass_at_1"]["passed"] == 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--checker", type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(checker=args.checker)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        print(pilot.wire({"report": str(args.output), "passed": result["passed"], "metrics": result["metrics"]}))
        return 0 if result["passed"] else 1
    except (pilot.PilotError, NabtError, OSError) as exc:
        print(pilot.wire({"schema": "nabt.pilot-error.v1", "error": getattr(exc, "code", "IO_ERROR"),
                          "message": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
