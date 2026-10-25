#!/usr/bin/env python3
"""Frozen, bounded inference-contract diagnostic; not Arabic/world truth accuracy."""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import sys
from time import perf_counter
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
GOLD_PATH = Path("evidence/mantuq_inference_v1/benchmark_gold.json")
GOLD_SHA256 = "a33105c62684171b4daedafa75a4fea5fe159fe4769cbdf04642d45d8eaf374a"
OUTCOMES = {"SUPPORTED", "UNKNOWN", "CONFLICT", "INVALID", "RESOURCE_EXHAUSTED"}


def execution_inputs(root: Path = ROOT) -> dict:
    """Record actual implementation/source/binary identities, not proof authority."""
    from tools.mantuq_inference import build_inventory
    from tools.mantuq_inference.retrieval import inventory_sha256
    from tools import source_semantics
    paths = [
        "tools/benchmark_mantuq_inference.py", "tools/mantuq_inference_benchmark_adapter.py",
        "tools/mantuq_inference/evaluator.py", "tools/mantuq_inference/pipeline.py",
        "tools/mantuq_inference/retrieval.py", "tools/mantuq_sources.py",
        "tools/mantuq_inference/inventory.py", "tools/mantuq_inference/__init__.py",
        "tools/grammar_catalog/routing.py", "tools/grammar_catalog/retrieval.py",
        "tools/mantuq_mafhum.py", "tools/verified_reading.py", "tools/source_semantics.py",
        "formal/Nabt/MantuqMafhum.lean", "formal/Nabt/VerifiedReading.lean",
        "formal/Nabt/QualifiedInference.lean", "formal/lean-toolchain",
    ]
    files = [{"path": path, "sha256": sha256((root / path).read_bytes()).hexdigest()}
             for path in paths]
    inventory = build_inventory(root)
    binaries = []
    try:
        probe = source_semantics.executable()
    except RuntimeError:
        probe = root / "formal/.lake/build/bin/classicalSemanticProbe"
    for name, path in [
        ("classicalSemanticProbe", Path(probe)),
        ("verifiedReading", Path(os.environ.get("NABT_VERIFIED_READING", root / "formal/.lake/build/bin/verifiedReading"))),
    ]:
        path = path.resolve()
        label = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        record = {"name": name, "path": label, "available": path.is_file()}
        if path.is_file():
            digest = sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            record.update(sha256=digest.hexdigest(), bytes=path.stat().st_size)
        binaries.append(record)
    return {"files": files, "inventory_sha256": inventory_sha256(inventory),
            "inventory_counts": {"sources": len(inventory["sources"]), "passages": len(inventory["passages"]),
                                 "policies": len(inventory["rules"])},
            "sources": [{"source_id": source["source_id"], "path": source["local_path"],
                         "sha256": source["sha256"], "bytes": source["bytes"]} for source in inventory["sources"]],
            "native_binaries": binaries,
            "declared_lean_toolchain": (root / "formal/lean-toolchain").read_text().strip(),
            "hashes_grant_semantic_authority": False}


def load_gold(root: Path = ROOT, path: Path | None = None) -> dict:
    raw = (path if path is not None else root / GOLD_PATH).read_bytes()
    if sha256(raw).hexdigest() != GOLD_SHA256:
        raise ValueError("Frozen inference gold changed; use a new benchmark version")
    gold = json.loads(raw)
    for source in gold["contract_inputs"]:
        if sha256((root / source["path"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("Frozen contract input changed: " + source["path"])
    cases = gold["cases"]
    if len({case["id"] for case in cases}) != len(cases):
        raise ValueError("Duplicate benchmark case identity")
    if dict(Counter(case["family"] for case in cases)) != gold["expected_counts"]:
        raise ValueError("Frozen case counts differ")
    for case in cases:
        expected = case["expected"]
        if expected["outcome"] not in OUTCOMES:
            raise ValueError("Unknown gold outcome")
        if expected["conditional_support"] is not (expected["outcome"] == "SUPPORTED"):
            raise ValueError("Gold support and outcome disagree")
        if expected["world_truth_established"] is not False or expected["whole_arabic_complete"] is not False:
            raise ValueError("Contract benchmark cannot establish world truth/whole Arabic")
    return gold


def score_observation(case: dict, observation: dict) -> dict:
    """Score target entailment; preserve raw application status separately.

    Opposite evidence for an obligation can refute that *application*. It does
    not prove the opposite target. The adapter records this distinction rather
    than incorrectly promoting an application-level REFUTED result to ¬target.
    """
    if type(observation) is not dict:
        raise ValueError("An observation must be a dictionary")
    required = {"outcome", "conditional_support", "world_truth_established", "whole_arabic_complete"}
    if not required <= set(observation):
        raise ValueError("Missing observation fields")
    outcome = observation["outcome"]
    if type(outcome) is not str or outcome not in OUTCOMES | {"UNMEASURED"}:
        raise ValueError("Invalid observation outcome")
    for field in required - {"outcome"}:
        if type(observation[field]) is not bool:
            raise ValueError("Observation flags must be actual booleans")
    if observation["conditional_support"] is not (outcome == "SUPPORTED"):
        raise ValueError("Outcome and conditional support disagree")
    checks = observation.get("contract_checks", {})
    if type(checks) is not dict or any(type(k) is not str or type(v) is not bool for k, v in checks.items()):
        raise ValueError("Contract checks must be named actual booleans")
    expected = case["expected"]
    measured = outcome != "UNMEASURED"
    matched = measured and all(observation[k] == v for k, v in expected.items()) and all(checks.values())
    return {
        "id": case["id"], "family": case["family"], "expected": expected,
        "observed": observation, "measured": measured, "matched": matched,
        "false_support": observation["conditional_support"] and not expected["conditional_support"],
        "lost_support": measured and expected["conditional_support"] and not observation["conditional_support"],
        "authority_overclaim": observation["world_truth_established"] or observation["whole_arabic_complete"],
        "failed_contract_checks": [name for name, passed in checks.items() if not passed],
    }


def run_benchmark(gold: dict, observer: Callable[[dict], dict]) -> dict:
    started = perf_counter()
    rows = [score_observation(case, observer(case)) for case in gold["cases"]]

    def counts(group):
        measured = sum(row["measured"] for row in group)
        matched = sum(row["matched"] for row in group)
        return {"cases": len(group), "measured": measured, "unmeasured": len(group) - measured,
                "matched": matched, "mismatched": measured - matched,
                "false_support": sum(row["false_support"] for row in group),
                "lost_support": sum(row["lost_support"] for row in group),
                "authority_overclaims": sum(row["authority_overclaim"] for row in group)}

    return {
        "schema": "nabt.qualified-inference-benchmark.v1",
        "authority": "BOUNDED_CONTRACT_OBSERVATIONS_ONLY",
        "gold_sha256": GOLD_SHA256, "gold_verified_by_cli": False,
        "independence": gold["independence"], "scope": gold["scope"],
        "aggregate": counts(rows),
        "by_family": {family: counts([row for row in rows if row["family"] == family])
                      for family in sorted({row["family"] for row in rows})},
        "complete_on_declared_diagnostic": all(row["matched"] for row in rows),
        "whole_arabic_complete": False, "world_truth_established": False,
        "free_arabic_acquisition_measured": False,
        "usuli_occurrence_classification_measured": False,
        "empirical_experiment_performed": False,
        "statistical_population_accuracy_estimated": False,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "elapsed_seconds": perf_counter() - started, "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "src"))
    from tools.mantuq_inference_benchmark_adapter import observe
    gold = load_gold()
    before = execution_inputs()
    report = run_benchmark(gold, observe)
    after = execution_inputs()
    report["gold_verified_by_cli"] = True
    report["execution_inputs"] = before
    report["execution_inputs_unchanged_during_run"] = before == after
    report["complete_on_declared_diagnostic"] &= before == after
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(json.dumps({"aggregate": report["aggregate"],
                      "complete_on_declared_diagnostic": report["complete_on_declared_diagnostic"],
                      "whole_arabic_complete": False}, ensure_ascii=False))
    return 0 if report["complete_on_declared_diagnostic"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
