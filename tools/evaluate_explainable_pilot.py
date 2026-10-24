#!/usr/bin/env python3
"""Measure the current proposer, native-checker wrapper and display contract.

This is a public development regression suite, not a new hidden Arabic or LLM
benchmark. Preserve denominators on failure; every claim has its scope/count.
"""
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
from tools import explainable_pilot as pilot

CASES = ROOT / "evidence/explainable_pilot/cases.json"
ATTACK_BINDINGS = (("identity", "other"), ("revision", "2"), ("scope", "other"))


def inputs(case):
    return tuple((ROOT / case[k + "_path"]).read_bytes() if k + "_path" in case
                 else case[k].encode("utf-8") for k in ("source", "query"))


def metric(passed, total):
    return {"passed": passed, "total": total, "rate": passed / total if total else None}


def attack_changes():
    """Executable, named attacks, not arbitrary repetitions inflated to N=3000."""
    return [
        ("forged-answer", lambda b: b["answer"].update(status="REFUTED")),
        ("invented-explanation", lambda b: b["answer"].update(text_ar="ثبت صدق المصدر في العالم")),
        ("forged-world-truth", lambda b: b["limits"].update(world_truth_established=True)),
        ("omitted-derivation", lambda b: b["analysis_certificate"]["kernel_certificate"]["steps"].pop()),
        ("forged-premise", lambda b: b["analysis_certificate"]["kernel_certificate"]["known"][0].update(predicate="مخترع")),
        ("changed-span", lambda b: b["analysis_certificate"]["source_clauses"][0].update(byte_start=1)),
        ("boolean-integer", lambda b: b["analysis_certificate"]["source_clauses"][0].update(byte_start=False)),
        ("omitted-proof-edge", lambda b: b["analysis_certificate"]["traces"]["full"][-1].update(premises=[])),
        ("changed-root", lambda b: b["analysis_certificate"]["roots"]["clean"].update(query=None)),
        ("fake-checker", lambda b: b["verification"].update(checker_sha256="0" * 64)),
        ("extra-claim", lambda b: b.update(confidence=1.0)),
    ]


def attacks(bundle):
    for name, change in attack_changes():
        altered = deepcopy(bundle)
        change(altered)
        yield name, altered, {}
    for field, value in ATTACK_BINDINGS:
        yield "changed-" + field, deepcopy(bundle), {field: value}


def timing(samples):
    return {"samples_seconds": samples, "count": len(samples),
            "p95_nearest_rank_seconds": sorted(samples)[math.ceil(.95 * len(samples)) - 1] if samples else None}


def evaluate(*, checker=None, repeats=3):
    if type(repeats) is not int or not 1 <= repeats <= 20:
        raise ValueError("repeats must be an integer in [1,20]")
    binary = pilot.checker_path(checker)  # absent checker is a failed run, never a passing skip
    material = pilot.strict_json(CASES.read_bytes())
    rows, baseline_times, answer_times = [], [], []
    replay_pass = roundtrip_pass = answer_pass = decisive = correct_decisive = 0
    for case in material["cases"]:
        raw, query = inputs(case)
        row = {"id": case["id"], "expected": case["expected"], "passed": False,
               "source_sha256": pilot.sha(raw), "query_sha256": pilot.sha(query),
               "replay_pass": False, "roundtrip_pass": False}
        try:
            for _ in range(repeats):
                start = time.perf_counter()
                proposal = pilot.propose_certificate(raw, query)
                baseline, _fingerprint = pilot.native(raw, query, proposal, "text", "1", "default", binary, 20)
                baseline_times.append(time.perf_counter() - start)
                start = time.perf_counter()
                bundle = pilot.answer(raw, query, checker=binary)
                answer_times.append(time.perf_counter() - start)
            observed = bundle["answer"]["status"]
            row.update(observed=observed, passed=observed == case["expected"],
                       baseline_status=baseline["status"], baseline_agreement=observed == baseline["status"])
            row["replay_pass"] = pilot.verify(raw, query, bundle, checker=binary)["verified"]
            restored = "".join(c["text"] for c in bundle["analysis_certificate"]["source_clauses"]).encode()
            row["roundtrip_pass"] = restored == raw
            row["answer_sha256"] = pilot.sha(pilot.wire(bundle).encode())
            if observed in {"SUPPORTED", "REFUTED"}:
                decisive += 1
                correct_decisive += observed == case["expected"]
        except pilot.PilotError as exc:
            row["error"] = exc.code
        answer_pass += row["passed"]
        replay_pass += row["replay_pass"]
        roundtrip_pass += row["roundtrip_pass"]
        rows.append(row)
    raw, query = inputs(material["cases"][0])
    attack_rows = []
    try:
        bundle = pilot.answer(raw, query, checker=binary)
        for name, altered, options in attacks(bundle):
            row = {"id": name, "rejected": False}
            try:
                pilot.verify(raw, query, altered, checker=binary, **options)
            except pilot.PilotError as exc:
                row.update(rejected=exc.code in {"ANSWER_REJECTED", "CERTIFICATE_REJECTED"}, error=exc.code)
            attack_rows.append(row)
    except pilot.PilotError as exc:
        # Preserve every planned attack even when setup prevents execution.
        names = [name for name, _ in attack_changes()] + ["changed-" + field for field, _ in ATTACK_BINDINGS]
        attack_rows = [{"id": name, "rejected": False, "error": exc.code, "not_executed": True} for name in names]
    ablation_rows = []
    for case in material["ablations"]:
        row = {"id": case["id"], "expected": case["expected"], "passed": False}
        try:
            observed = pilot.answer(*inputs(case), checker=binary)["answer"]["status"]
            row.update(observed=observed, passed=observed == case["expected"])
        except pilot.PilotError as exc:
            row["error"] = exc.code
        ablation_rows.append(row)
    dependencies = sorted((ROOT / "src/nabt").rglob("*.py")) + sorted((ROOT / "formal").glob("*.lean"))
    dependencies += sorted((ROOT / "formal/Nabt").glob("*.lean"))
    dependencies += [ROOT / p for p in ("tools/explainable_pilot.py", "tools/evaluate_explainable_pilot.py",
                                      "tools/verified_reading.py", "formal/lean-toolchain")]
    dependencies += sorted(p for p in (ROOT / "src/nabt/data").rglob("*") if p.is_file())
    dependencies += [CASES, ROOT / "evidence/explainable_pilot/goals.json",
                     ROOT / "examples/verified_reading/source.txt", ROOT / "examples/verified_reading/query.txt"]
    hashes = {str(p.relative_to(ROOT)): pilot.file_sha(p) for p in dependencies}
    total = len(rows)
    metrics = {"status_exact": metric(answer_pass, total), "independent_native_replay": metric(replay_pass, total),
               "source_byte_roundtrip": metric(roundtrip_pass, total),
               "decisive_precision": metric(correct_decisive, decisive), "decisive_coverage": metric(decisive, total),
               "tampering_rejected": metric(sum(r["rejected"] for r in attack_rows), len(attack_rows)),
               "source_ablation": metric(sum(r["passed"] for r in ablation_rows), len(ablation_rows))}
    return {"schema": "nabt.explainable-pilot-metrics.v1", "created_utc": datetime.now(timezone.utc).isoformat(),
            "model": "existing deterministic verified_reading proposer; no neural model or training",
            "split": material["split"], "hidden": False, "provenance": material["provenance"],
            "git_parent_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "environment": {"python": sys.version, "platform": platform.platform(), "checker_sha256": pilot.file_sha(binary)},
            "input_hashes": hashes, "metrics": metrics, "cases": rows,
            "attacks": attack_rows, "ablations": ablation_rows,
            "timing": {"repeats_per_case": repeats, "baseline_propose_and_native": timing(baseline_times),
                       "answer_including_native_and_rendering": timing(answer_times),
                       "scope": "local sequential wall-clock observations; subprocess and hashing included; not a hardware-general SLA"},
            "unmeasured": {k: None for k in ("hidden_arabic_accuracy", "independent_human_explanation_fidelity",
                "neural_model_accuracy", "training_gain", "gpu_memory", "llm_token_cost", "model_internal_causality")},
            "passed": all(r["passed"] and r["replay_pass"] and r["roundtrip_pass"] and r.get("baseline_agreement") for r in rows)
                      and len(attack_rows) == 14 and all(r["rejected"] for r in attack_rows)
                      and all(r["passed"] for r in ablation_rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--checker", type=Path)
    parser.add_argument("--repeats", type=int, choices=range(1, 21), default=3)
    args = parser.parse_args()
    result = evaluate(checker=args.checker, repeats=args.repeats)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as out:
        out.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(pilot.wire({"report": str(args.output), "passed": result["passed"], "metrics": result["metrics"]}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
