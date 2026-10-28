#!/usr/bin/env python3
"""Replay the independently authored lifecycle oracle against frozen code.

Only input episodes reach the producer. Expected steps and verification pairs
remain evaluator-owned data. These are exposed conditional controls, not
physical observations, source authentication, or general Arabic accuracy.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import importlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_PATH = "tools/evaluate_aligned_acquisition.py"
BOOTSTRAP_SHA256 = "50b8e45b821818180854f6990324ea255206913ade849ee97c4fd5b5a0d056cb"
SOURCE_COMMIT = "4b1812127acf452ed72e57686ec02486bebc472c"
MATRIX_COMMIT = "1295da3349b50190dc6f68606f918054e7bbfdf2"
GOLD_PATH = "evidence/evidence_lifecycle_v1/cases.json"
GOLD_SHA256 = "04609a848ddd4336d600253997b0d79523b28f6475be47f064845769083486be"
SOURCE_PATH = "evidence/evidence_lifecycle_v1/source_scope.json"
CONVENTION_PATH = "evidence/convention_preparation_v1/source_packet.json"
SOURCE_PINS = {
    "docs/EVIDENCE_LIFECYCLE_V1_SPEC.md": "6864b6e1098491f67ba2c0fbc260605dcf6c36ea48d543874d43316717aabf5d",
    "docs/PRODUCTIVE_LIFECYCLE_V1_SPEC.md": "81deb8f66aa3e275a4253a31f31768b6989b8d0cbd34006f2e0c4dbc060255b5",
    "docs/ENTROPY_FRAMEWORK_V2_SPEC.md": "f78df7c9e17c6ed71403b5d6bced02dd600856715e877b2427dfa9fd63b96e84",
    "docs/CONVENTION_PREPARATION_V1_AR.md": "c8e29329de9dbe3ba4d50e21b87b3942a674aef074db59d2c0ea1396067b7803",
    "evidence/evidence_lifecycle_v1/acceptance_protocol.json": "a7586ec40111e318caf23082b427743c57f50ec87cfdc8b5dc4bdb3993c24e32",
    SOURCE_PATH: "61eae397c316f29726acf64330039086802f18f6b2c1a3e149d910b27814b660",
    CONVENTION_PATH: "c0906dc355fab3e37bd6645f8757b675da6e400f932238b013284b33fb78c9ab",
}
MATRIX_PINS = {GOLD_PATH: GOLD_SHA256,
    "evidence/evidence_lifecycle_v1/GOLD_METHOD.md": "c07ccda54b81f7314790f8ddcedd6edafa4e8c36b3471ef9e41c0956b8e81be3"}
PINS = {**SOURCE_PINS, **MATRIX_PINS}
LAW_ID = "nabt.evidence-lifecycle.v1"
EVALUATOR_ID = "nabt.evidence-lifecycle-evaluator.v1"
SCHEMA = "nabt.evidence-lifecycle-code-freeze.v1"
RESULT_SCHEMA = "nabt.evidence-lifecycle-evaluation.v1"
REPORT_SCHEMA = "nabt.evidence-lifecycle.result.v1"
FLAGS = {name: False for name in ("world_truth_established", "source_authenticity_established",
                                "referents_established", "all_arabic_complete")}
FAMILIES = dict.fromkeys(("withdrawal", "lineage", "conflict", "qualified_key", "revision_and_absence"), 8)
POPULATION = {"scenarios": 40, "families": FAMILIES, "valid_episodes": 34,
    "invalid_input_scenarios": 5, "outer_resource_scenarios": 1, "episode_steps": 79,
    "complete_decision_steps": 76, "ledger_resource_steps": 3, "verification_pairs": 73,
    "separate_historical_prefix_steps": 7}
NATIVE = "formal/.lake/build/bin/evidenceLifecycleV1"
NATIVE_PATHS = frozenset("formal/.lake/build/bin/" + name for name in
    ("alignedAcquisition", "licensedInference", "connectedAcquisitionV3", "productiveClauseV1", "evidenceLifecycleV1"))
REFERENCES = frozenset("evidence/evidence_lifecycle_v1/integration/" + name + ".json" for name in
    ("proof_catalog", "grammar_link_summary", "mantuq_proof_links", "linguistic_proof_links",
     "licensed_proof_links", "article_proof_links", "sourced_proof_links"))
EXTRA_PATHS = frozenset(PINS) | REFERENCES | frozenset({
    "evidence/aligned_acquisition_v1/gold.json", "formal/theorems.json", "Makefile",
    "tools/aligned_acquisition.mk", "tools/article_acquisition.mk", "tools/sourced_acquisition_v3.mk",
    "tools/productive_clause_v1.mk", "tools/evidence_lifecycle_v1.mk", "integrations/current_proof_references.mk",
    "tools/entropy_framework/registry.json", "evidence/operator_traceability_v1/registry.json",
    "docs/EVIDENCE_LIFECYCLE_V1_IMPLEMENTATION_NOTES.md",
    "integrations/grammar_catalog.mk", "integrations/mantuq_inference.mk",
    "integrations/linguistic_truth.mk", "integrations/licensed_inference.mk",
    ".github/workflows/aligned-acquisition.yml"})


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def same(left, right):
    try:
        return wire(left) == wire(right)
    except (TypeError, ValueError, RecursionError):
        return False


def digest(raw):
    return sha256(raw).hexdigest()


def load_bootstrap():
    path = ROOT / BOOTSTRAP_PATH
    raw = path.read_bytes()
    if path.resolve() != path or digest(raw) != BOOTSTRAP_SHA256:
        raise ValueError("trusted source-only bootstrap differs")
    module = ModuleType("_nabt_lifecycle_bootstrap")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    return module


def packets_at(guard, commit):
    names = (SOURCE_PATH, CONVENTION_PATH, "evidence/productive_clause_v1/source_scope.json",
             "evidence/sourced_acquisition_v3/source_evidence.json")
    return [guard.parse_json(guard.git("show", commit + ":" + name, binary=True)) for name in names]


def required_paths(guard, inventory, inference_sources, packets):
    result = guard.required_freeze_paths(inventory, inference_sources) | set(EXTRA_PATHS)
    scope, convention, productive, acquisition = packets
    for group in ("normative_documents", "existing_contract_references", "installed_packet_pins"):
        result.update(row["path"] for row in scope[group])
    result.update(row.get("local_path", row.get("path")) for row in convention["source_records"])
    result.update(row["path"] for row in convention["packet_pins"])
    for packet in (productive, acquisition):
        for row in packet.get("passages", []):
            if "local_path" in row:
                result.add(row["local_path"])
        for row in packet.get("sources", []):
            result.add(row.get("repository_path", row.get("path")))
        result.update(row["path"] for row in packet.get("upstream_dependencies", []))
    for name in result:
        guard.local_path(name)
    return result


def verify_freeze(path, phase):
    if phase not in {"first", "exposed"}:
        raise ValueError("unknown evaluation phase")
    guard = load_bootstrap()
    envelope, fingerprint = guard.load_json(path)
    if (envelope.get("schema") != SCHEMA or envelope.get("evaluator_id") != EVALUATOR_ID or
            envelope.get("content_pins") != PINS or envelope.get("source_commit") != SOURCE_COMMIT or
            envelope.get("matrix_commit") != MATRIX_COMMIT or envelope.get("bootstrap") !=
            {"path": BOOTSTRAP_PATH, "sha256": BOOTSTRAP_SHA256}):
        raise ValueError("freeze schema, chronology or code-owned pins differ")
    inner = envelope.get("baseline")
    if type(inner) is not dict or type(inner.get("native")) is not dict or set(inner["native"]) != NATIVE_PATHS:
        raise ValueError("freeze requires exactly the five declared executables")
    with tempfile.TemporaryDirectory(prefix="nabt-lifecycle-freeze-") as directory:
        baseline = Path(directory) / "baseline.json"
        baseline.write_text(wire(inner), encoding="utf-8")
        _, evidence = guard.verify_freeze(baseline, "exposed", guard.GOLD_PATH)
    commit = inner["commit"]
    inventory = set(guard.git("ls-files", "-z").split("\0")) | set(
        guard.git("ls-tree", "-r", "--name-only", "-z", commit).split("\0"))
    inference = guard.parse_json(guard.git("show", commit + ":" + guard.INFERENCE_SOURCE_PATH, binary=True))
    required = required_paths(guard, inventory, inference, packets_at(guard, commit))
    if not required <= set(inner["files"]):
        raise ValueError("missing required frozen inputs: " + ", ".join(sorted(required - set(inner["files"]))))
    for name, expected in {**PINS, BOOTSTRAP_PATH: BOOTSTRAP_SHA256}.items():
        if inner["files"].get(name) != expected:
            raise ValueError("frozen content pin differs: " + name)
    for name, expected in inner["native"].items():
        native = guard.local_path(name)
        if not native.is_file() or not os.access(native, os.X_OK) or digest(native.read_bytes()) != expected:
            raise ValueError("required native executable unavailable or changed: " + name)
    if phase == "first":
        if guard.git("rev-parse", "HEAD") != commit or commit in {SOURCE_COMMIT, MATRIX_COMMIT}:
            raise ValueError("first execution requires a later committed implementation HEAD")
        guard.git("merge-base", "--is-ancestor", SOURCE_COMMIT, MATRIX_COMMIT)
        guard.git("merge-base", "--is-ancestor", MATRIX_COMMIT, commit)
        for phase_commit, pins in ((SOURCE_COMMIT, SOURCE_PINS), (MATRIX_COMMIT, PINS)):
            for name, expected in pins.items():
                if digest(guard.git("show", phase_commit + ":" + name, binary=True)) != expected:
                    raise ValueError("phase content differs: " + name)
    return envelope, {"manifest_sha256": fingerprint, "commit": commit,
        "evaluator_id": EVALUATOR_ID, "evaluator_sha256": inner["files"]["tools/evaluate_evidence_lifecycle_v1.py"],
        "source_commit": SOURCE_COMMIT, "matrix_commit": MATRIX_COMMIT,
        "local_source_matrix_implementation_chronology_verified": phase == "first",
        "requested_first_execution": phase == "first", "blind": False,
        "actual_world_observations": False, "baseline": evidence}


def initial_snapshot(guard, inner, phase):
    before = guard.snapshot(inner, ROOT / GOLD_PATH)
    bad = [name for hashes in (inner["files"], inner["native"]) for name, expected in hashes.items()
           if before["files"].get(name) != expected]
    if before["gold_sha256"] != GOLD_SHA256:
        bad.append("independent matrix")
    if phase == "first" and before["head"] != inner["commit"]:
        bad.append("first execution HEAD")
    if bad:
        raise ValueError("initial snapshot differs from validated freeze: " + ", ".join(sorted(bad)))
    return before


def load_gold(guard):
    gold, actual = guard.load_json(ROOT / GOLD_PATH)
    if (actual != GOLD_SHA256 or gold.get("schema") != "nabt.evidence-lifecycle.cases.v1" or
            not same(gold.get("counts"), POPULATION)):
        raise ValueError("independent matrix identity or declared population differs")
    cases = gold.get("cases")
    if type(cases) is not list or len(cases) != 40 or len({c["id"] for c in cases}) != 40:
        raise ValueError("independent scenario population differs")
    if dict(Counter(c["family"] for c in cases)) != FAMILIES:
        raise ValueError("independent family population differs")
    if (sum(len(c["expected"]["steps"] or []) for c in cases) != 79 or
            sum(len(c["verification_pairs"]) for c in cases) != 73 or
            sum(len(h["expected"]["steps"]) for c in cases for h in c.get("historical_prefix_expectations", [])) != 7):
        raise ValueError("independent step or verification denominator differs")
    return gold


def flags_safe(value):
    return type(value) is dict and all(value.get(key) is False for key in FLAGS)


def error_native_matches(value, status):
    if (type(value) is not dict or set(value) != {"law_id", "status", "reason", *FLAGS} or
            value.get("law_id") != LAW_ID or value.get("status") != status or not flags_safe(value)):
        return False
    reason = value.get("reason")
    if type(reason) is not str or not reason.strip():
        return False
    try:
        reason.encode("utf-8", "strict")
    except UnicodeError:
        return False
    return True


def native_matches(episode, expected, observed):
    if expected["outcome"] != "VALID_EPISODE":
        return error_native_matches(observed, expected["status"])
    return same(observed, {"law_id": LAW_ID, "binding": episode, "steps": expected["steps"], **FLAGS})


def execution_matches(episode, expected, execution, identity):
    """Check execution claims against independent data and validated freeze hashes."""
    names = {"input", "proposal", "native_result", "input_sha256", "proposal_sha256",
             "native_result_sha256", "run_identity", "error"}
    if type(execution) is not dict or set(execution) != names:
        return False
    if expected["outcome"] != "VALID_EPISODE":
        # These six authored errors all arise while validating the complete
        # episode. No invalid input or accepted partial history may be retained.
        return (all(execution[name] is None for name in names - {"error"}) and
                type(execution["error"]) is str and bool(execution["error"].strip()))
    envelope = {"law_id": LAW_ID, "binding": episode, "steps": expected["steps"], **FLAGS}
    values = {"input": episode, "proposal": envelope, "native_result": envelope}
    return (execution["error"] is None and same(execution["run_identity"], identity) and
            all(same(execution[name], value) and execution[name + "_sha256"] == digest(wire(value).encode("utf-8"))
                for name, value in values.items()))


def audit_report(episode, expected, report, identity=None):
    if type(report) is not dict:
        return {"match": False, "false_authorization": False, "steps_match": []}
    report_fields = {"schema", "law_id", "status", "native_checked", "decision_complete",
                     "evidence_class", "observed", "execution", *FLAGS}
    shape = (set(report) == report_fields and report.get("schema") == REPORT_SCHEMA and report.get("law_id") == LAW_ID and
             report.get("evidence_class") == "AUTHORED_SCENARIO" and flags_safe(report) and
             type(report.get("native_checked")) is bool and type(report.get("decision_complete")) is bool and
             type(report.get("execution")) is dict)
    metadata = (report.get("status") == expected["status"] and
                report.get("decision_complete") is expected["decision_complete"] and
                (identity is None or execution_matches(episode, expected, report.get("execution"), identity)))
    observed = report.get("observed")
    if expected["outcome"] == "VALID_EPISODE":
        match = bool(shape and metadata and report.get("native_checked") is True and
                     native_matches(episode, expected, observed))
        actual_steps = observed.get("steps", []) if type(observed) is dict else []
        actual_steps = actual_steps if type(actual_steps) is list else []
        steps = [same(step, actual_steps[i]) if i < len(actual_steps) else False
                 for i, step in enumerate(expected["steps"])]
    else:
        match = bool(shape and metadata and report.get("native_checked") is False and observed is None)
        steps = []
    claims = (report.get("decision_complete") is True or report.get("native_checked") is True or
              observed is not None or "binding" in report or "steps" in report)
    return {"match": match, "false_authorization": bool((claims and not match) or not flags_safe(report)),
            "steps_match": steps}


def prefix_input(case, length):
    value = deepcopy(case["input"])
    value["updates"] = value["updates"][:length]
    return value


def prefix_expected(case, length):
    expected = case["expected"]
    if expected["outcome"] == "VALID_EPISODE":
        steps = deepcopy(expected["steps"][:length + 1])
        return {"outcome": "VALID_EPISODE", "status": steps[-1]["receipt"]["status"],
                "decision_complete": expected["decision_complete"], "steps": steps}
    for row in case.get("historical_prefix_expectations", []):
        if row["updates_count"] == length:
            return deepcopy(row["expected"])
    raise ValueError("no independently authored historical prefix")


def direct_native(episode, guard):
    completed = subprocess.run([str(ROOT / NATIVE)], input=(wire(episode) + "\n").encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=True)
    if len(completed.stdout) > 8 * 1024 * 1024:
        raise ValueError("native response exceeded frozen report bound")
    return guard.parse_json(completed.stdout)


def evaluate_case(case, reader, guard, identity=None):
    episode, expected = deepcopy(case["input"]), case["expected"]
    report = reader.evaluate_episode(deepcopy(episode))
    audit = audit_report(episode, expected, report, identity)
    native = direct_native(episode, guard)
    native_ok = native_matches(episode, expected, native)
    prefixes = {len(episode["updates"]): report}
    pairs = []
    for pair in case["verification_pairs"]:
        length = pair["receipt_prefix_updates"]
        historical = prefix_input(case, length)
        current = prefix_input(case, pair["expected_prefix_updates"])
        if length not in prefixes:
            prefixes[length] = reader.evaluate_episode(deepcopy(historical))
        receipt = prefixes[length]
        historical_audit = audit_report(historical, prefix_expected(case, length), receipt, identity)
        history_check = reader.verify_episode(deepcopy(receipt), expected_episode=deepcopy(historical))
        current_check = reader.verify_episode(deepcopy(receipt), expected_episode=deepcopy(current))
        history_ok = type(history_check) is dict and all(
            history_check.get(key) is pair["expected_historical_" + key] for key in ("replay_matches", "valid"))
        current_ok = type(current_check) is dict and all(
            current_check.get(key) is pair["expected_current_" + key] for key in ("replay_matches", "valid"))
        false = historical_audit["false_authorization"] or any(
            type(check) is dict and check.get("valid") is True and pair[wanted] is False
            for check, wanted in ((history_check, "expected_historical_valid"), (current_check, "expected_current_valid")))
        pairs.append({"id": pair["id"], "match": historical_audit["match"] and history_ok and current_ok,
            "historical_audit": historical_audit, "historical_verification": history_check,
            "current_verification": current_check, "false_authorization": bool(false)})
    native_false = not native_ok and type(native) is dict and (
        "binding" in native or "steps" in native or not flags_safe(native) or
        native.get("status") in {"SUPPORTED", "REFUTED", "CONFLICT"})
    false = audit["false_authorization"] or native_false or any(p["false_authorization"] for p in pairs)
    return {"id": case["id"], "family": case["family"], "expected_outcome": expected["outcome"],
        "contract_match": audit["match"] and native_ok and all(p["match"] for p in pairs) and not false,
        "false_authorization": bool(false), "audit": audit, "direct_native_match": native_ok,
        "report": report, "direct_native": native, "prefix_reports": {str(k): v for k, v in prefixes.items()},
        "verification_pairs": pairs}


def counts(rows):
    pairs = [pair for row in rows for pair in row["verification_pairs"]]
    steps = [step for row in rows for step in row["audit"]["steps_match"]]
    auxiliary_steps = [step for row in rows if row["expected_outcome"] != "VALID_EPISODE"
                       for pair in row["verification_pairs"] for step in pair["historical_audit"]["steps_match"]]
    return {"scenarios": len(rows), "scenario_contracts": sum(r["contract_match"] for r in rows),
        "by_family": {f: {"scenarios": sum(r["family"] == f for r in rows),
            "contracts": sum(r["family"] == f and r["contract_match"] for r in rows)} for f in FAMILIES},
        "main_episode_steps": len(steps), "matched_main_episode_steps": sum(steps),
        "verification_pairs": len(pairs), "matched_verification_pairs": sum(p["match"] for p in pairs),
        "auxiliary_historical_steps": len(auxiliary_steps), "matched_auxiliary_historical_steps": sum(auxiliary_steps),
        "native_error_contracts": sum(r["expected_outcome"] != "VALID_EPISODE" for r in rows),
        "matched_native_error_contracts": sum(r["expected_outcome"] != "VALID_EPISODE" and r["direct_native_match"] for r in rows),
        "observed_false_authorizations": sum(r["false_authorization"] for r in rows), "required_skips": 0}


def acceptance(summary, integrity):
    checks = {"forty_scenario_contracts": summary["scenarios"] == summary["scenario_contracts"] == 40,
        "five_families": all(v == {"scenarios": 8, "contracts": 8} for v in summary["by_family"].values()) and len(summary["by_family"]) == 5,
        "all_main_steps": summary["main_episode_steps"] == summary["matched_main_episode_steps"] == 79,
        "all_verification_pairs": summary["verification_pairs"] == summary["matched_verification_pairs"] == 73,
        "all_auxiliary_historical_steps": summary["auxiliary_historical_steps"] == summary["matched_auxiliary_historical_steps"] == 7,
        "native_error_contracts": summary["native_error_contracts"] == summary["matched_native_error_contracts"] == 6,
        "no_observed_false_authorizations": summary["observed_false_authorizations"] == 0,
        "no_required_skips": summary["required_skips"] == 0, "execution_integrity": bool(integrity)}
    return {"passed": all(checks.values()), "checks": checks,
            "authority": "AUTHORED_CONDITIONAL_MATRIX_ONLY", **FLAGS}


class ScenarioExecutionError(RuntimeError):
    """Retain completed observations if a later execution cannot produce a row."""
    def __init__(self, case_id, rows, cause):
        super().__init__(str(cause))
        self.case_id, self.rows, self.cause_type = case_id, rows, type(cause).__name__


def run(envelope, evidence, phase):
    guard = load_bootstrap(); inner = envelope["baseline"]
    before = initial_snapshot(guard, inner, phase)
    gold = load_gold(guard)
    with guard.frozen_runtime(inner) as imports:
        reader = importlib.import_module("tools.evidence_lifecycle_v1")
        identity = {"code": {name: inner["files"][name] for name in
                    ("tools/evidence_lifecycle_v1.py", "tools/epistemic_measurement.py")},
                    "native": {NATIVE: inner["native"][NATIVE]}}
        rows = []
        for case in gold["cases"]:
            try:
                rows.append(evaluate_case(case, reader, guard, identity))
            except Exception as exc:
                raise ScenarioExecutionError(case["id"], rows, exc) from exc
        after = guard.snapshot(inner, ROOT / GOLD_PATH)
        imports.audit_origins()
        wrong = sorted(name for name, actual in imports.executed.items() if inner["files"].get(name) != actual)
        loaded = {}
        for module in tuple(sys.modules.values()):
            filename = getattr(module, "__file__", None)
            if filename:
                path = Path(filename).resolve()
                if path.suffix == ".py" and path.is_relative_to(ROOT):
                    loaded[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
    uncovered = sorted(set(loaded) - set(inner["files"]))
    loaded_wrong = sorted(name for name, actual in loaded.items() if inner["files"].get(name) != actual)
    integrity = before == after and not wrong and not uncovered and not loaded_wrong
    summary = counts(rows)
    return {"schema": RESULT_SCHEMA, "evaluator_id": EVALUATOR_ID, "phase": phase,
        "measured_at_utc": datetime.now(timezone.utc).isoformat(), "population": POPULATION,
        "scope": "Forty authored, exposed conditional episodes; no actual world observation or general gate admission.",
        "summary": summary, "acceptance_gate": acceptance(summary, bool(integrity)),
        "execution_evidence": {**evidence, "before": before, "after": after,
            "initial_snapshot_matches_freeze": True, "integrity_valid": bool(integrity),
            "runtime_import_policy": "fresh-frozen-source-only.v1", "executed_repository_python": imports.executed,
            "executed_hash_mismatches": wrong, "loaded_repository_python": loaded,
            "uncovered_modules": uncovered, "loaded_hash_mismatches": loaded_wrong,
            "python": sys.version, "platform": platform.platform(), "command": list(sys.argv),
            "toolchain": (ROOT / "formal/lean-toolchain").read_text().strip()}, "rows": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-freeze", type=Path, required=True)
    parser.add_argument("--phase", choices=("first", "exposed"), required=True)
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        report = {"schema": RESULT_SCHEMA, "evaluator_id": EVALUATOR_ID, "phase": args.phase,
            "status": "ATTEMPT_STARTED", "started_at_utc": datetime.now(timezone.utc).isoformat(), "gold_sha256": GOLD_SHA256}
        stream.write(wire(report) + "\n"); stream.flush(); os.fsync(stream.fileno())
        stage = "preflight"
        try:
            freeze, evidence = verify_freeze(args.code_freeze, args.phase)
            stage = "execution"; report = run(freeze, evidence, args.phase)
        except Exception as exc:
            report = {**report, "status": "EVALUATOR_FAILURE", "failure_stage": stage,
                      "error": {"type": type(exc).__name__, "message": str(exc)}}
            if isinstance(exc, ScenarioExecutionError):
                report.update(failed_case_id=exc.case_id, cause_type=exc.cause_type,
                              completed_rows=exc.rows, acceptance_gate={"passed": False})
        stream.seek(0); json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n"); stream.truncate(); stream.flush(); os.fsync(stream.fileno())
    print(wire({k: v for k, v in report.items() if k in {"summary", "acceptance_gate", "status", "failure_stage", "error"}}))
    return 0 if report.get("acceptance_gate", {}).get("passed") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
