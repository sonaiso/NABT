#!/usr/bin/env python3
"""Independent frozen projections, source safety, and separate positive goals.

Repository imports execute only after validation against committed source bytes.
The unchanged v1 bootstrap owns source-only import isolation; it grants no new
linguistic authority. The interpreter/stdlib/host remain trusted assumptions.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import importlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_PATH = "tools/evaluate_aligned_acquisition.py"
BOOTSTRAP_SHA256 = "50b8e45b821818180854f6990324ea255206913ade849ee97c4fd5b5a0d056cb"
SOURCE_COMMIT = "d597b8583f21a6b31d709f79ffc8c5008ebc5f80"
MATRIX_COMMIT = "286651fb860e808b2f51b604803f7e177ac9febd"
GOLD_PATH = "evidence/sourced_acquisition_v3/gold.json"
GOLD_SHA256 = "c61c971adc4e88e4626a890f3fb304dfdeafcc3ac6b312e46854e1f3a67ccbee"
PINS = {
    "docs/SOURCED_ACQUISITION_V3_SPEC.md": "f68e8e9f8cf77252afbd3d1ee63ada99b32dd0fecfabb01b2ec796898e99be49",
    "docs/SOURCED_ACQUISITION_V3_CONNECTED.md": "59e5965501abe71d95c7a94f3a73dc6e75da5212ca507aab3c3e2f8b72caf517",
    "docs/SOURCED_ACQUISITION_V3_PERSON_NOMINAL.md": "1108b617e3f62d865620471355f03a9fd09e9d9098a3189e3b12ccb8ae701572",
    "docs/SOURCED_ACQUISITION_V3_NATURAL.md": "ac041e9b1168f0bf9b90cd4d3c70390e445b5d858d2098b2cdf03a23c5c63490",
    "docs/SOURCED_ACQUISITION_V3_ARCHITECTURE.md": "67c1178deb383a1a9f7eaab24dd9daf513e57fb6d99d33ff19eca8bc28b23f1a",
    "evidence/sourced_acquisition_v3/source_evidence.json": "64d6d40943ed59a34d16a58de92e11f8672cbdc7ed47ec15f4e341d07594e423",
    "evidence/sourced_acquisition_v3/natural_sources.json": "f96689c943b06155f8e91a10fabf7b94ac9ae34200a8682ffa086aad604db7f6",
    GOLD_PATH: GOLD_SHA256,
    "evidence/sourced_acquisition_v3/GOLD_METHOD.md": "0e2913621fee3cab9e76d3fca729d332646769dff7e39d1294dab28f1bb5c8d2",
}
SCHEMA = "nabt.sourced-acquisition-code-freeze.v3"
RESULT_SCHEMA = "nabt.sourced-acquisition-evaluation.v3"
SCOPE = "independent-sourced-v3"
FAMILIES = {"orthography": 50, "person_category": 27,
            "nominal_predication": 34, "conditional_inference": 50}
ENTRYPOINTS = {"connected": 50, "person_nominal": 61, "natural": 40, "conditional_pr34": 10}
NATIVE_PATHS = frozenset("formal/.lake/build/bin/" + name for name in
    ("alignedAcquisition", "alignedAcquisitionV2", "connectedAcquisitionV3",
     "acquiredSyntaxV3", "linguisticTruth", "licensedInference"))
REFERENCES = frozenset("evidence/sourced_acquisition_v3/integration/" + name + ".json" for name in
    ("proof_catalog", "grammar_link_summary", "mantuq_proof_links", "linguistic_proof_links",
     "licensed_proof_links", "article_proof_links", "sourced_proof_links"))
EXTRA_PATHS = frozenset(PINS) | REFERENCES | frozenset({
    "evidence/aligned_acquisition_v1/gold.json", "evidence/article_acquisition_v2/source_evidence.json",
    "evidence/operator_traceability_v1/registry.json", "formal/theorems.json", "Makefile",
    "tools/aligned_acquisition.mk", "tools/article_acquisition.mk", "tools/sourced_acquisition_v3.mk",
    "integrations/current_proof_references.mk", "integrations/grammar_catalog.mk",
    "integrations/mantuq_inference.mk", "integrations/linguistic_truth.mk",
    "integrations/licensed_inference.mk", ".github/workflows/aligned-acquisition.yml"})
NEW_PRODUCTION = ("tools/connected_acquisition_v3.py", "tools/acquired_person_nominal_v3.py",
                  "tools/natural_acquisition_v3.py", "formal/Nabt/ConnectedAcquisitionV3.lean",
                  "formal/Nabt/AcquiredSyntaxV3.lean")


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(raw):
    return sha256(raw).hexdigest()


def load_bootstrap():
    path = ROOT / BOOTSTRAP_PATH
    raw = path.read_bytes()
    if path.resolve() != path or digest(raw) != BOOTSTRAP_SHA256:
        raise ValueError("trusted source-only bootstrap differs")
    module = ModuleType("_nabt_sourced_v3_bootstrap")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    return module


def required_paths(guard, inventory, inference_sources, source_packets):
    result = guard.required_freeze_paths(inventory, inference_sources) | set(EXTRA_PATHS)
    # Include the installed semantic ledger and retained evidence, not benchmark
    # predictions as authority. Extra snapshots here are integrity inputs only.
    result.update(name for name in inventory if
        name.startswith("evidence/linguistic_truth_v1/") and
        name.endswith((".json", ".txt")) and "/validation/" not in name)
    for packet in source_packets:
        for row in packet["sources"]:
            path = row.get("repository_path", row.get("path"))
            guard.local_path(path)
            result.add(path)
        for row in packet.get("upstream_dependencies", []):
            guard.local_path(row["path"])
            result.add(row["path"])
    return result


def packets_at(guard, commit):
    return [guard.parse_json(guard.git("show", commit + ":" + path, binary=True)) for path in
            ("evidence/sourced_acquisition_v3/source_evidence.json",
             "evidence/sourced_acquisition_v3/natural_sources.json")]


def verify_freeze(path, phase):
    guard = load_bootstrap()
    envelope, fingerprint = guard.load_json(path)
    if (phase not in {"first", "exposed"} or envelope.get("schema") != SCHEMA or
            envelope.get("content_pins") != PINS or
            envelope.get("source_commit") != SOURCE_COMMIT or
            envelope.get("matrix_commit") != MATRIX_COMMIT or
            envelope.get("bootstrap") != {"path": BOOTSTRAP_PATH, "sha256": BOOTSTRAP_SHA256}):
        raise ValueError("freeze schema, chronology or code-owned pins differ")
    inner = envelope.get("baseline")
    if type(inner) is not dict or set(inner.get("native", {})) != NATIVE_PATHS:
        raise ValueError("freeze requires exactly the six installed executables")
    with tempfile.TemporaryDirectory(prefix="nabt-sourced-freeze-") as directory:
        old = Path(directory) / "baseline.json"
        old.write_text(wire(inner), encoding="utf-8")
        _, evidence = guard.verify_freeze(old, "exposed", guard.GOLD_PATH)
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
    if phase == "first":
        if guard.git("rev-parse", "HEAD") != commit:
            raise ValueError("first execution requires HEAD at its implementation freeze")
        guard.git("merge-base", "--is-ancestor", SOURCE_COMMIT, MATRIX_COMMIT)
        guard.git("merge-base", "--is-ancestor", MATRIX_COMMIT, commit)
        for name, expected in PINS.items():
            if digest(guard.git("show", MATRIX_COMMIT + ":" + name, binary=True)) != expected:
                raise ValueError("matrix-time pin differs: " + name)
            if name.startswith("docs/") or name.endswith(("source_evidence.json", "natural_sources.json")):
                if digest(guard.git("show", SOURCE_COMMIT + ":" + name, binary=True)) != expected:
                    raise ValueError("source-time pin differs: " + name)
        matrix_files = set(guard.git("ls-tree", "-r", "--name-only", "-z", MATRIX_COMMIT).split("\0"))
        if matrix_files.intersection(NEW_PRODUCTION):
            raise ValueError("new production implementation already existed at matrix freeze")
    return envelope, {"manifest_sha256": fingerprint, "commit": commit,
        "source_commit": SOURCE_COMMIT, "matrix_commit": MATRIX_COMMIT,
        "chronology_verified": phase == "first", "requested_first_execution": phase == "first",
        "chronology_scope": "Git ancestry and content only; not secrecy or absence of undisclosed prior runs.",
        "baseline": evidence}


def pointer(value, path):
    if type(path) is not str or not path.startswith("/"):
        raise ValueError("projection paths must be JSON pointers")
    for part in path[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if type(value) is list:
            if not part.isascii() or not part.isdigit() or str(int(part)) != part:
                raise KeyError(path)
            value = value[int(part)]
        elif type(value) is dict:
            value = value[part]
        else:
            raise KeyError(path)
    return value


def matches(report, assertions):
    result = {}
    for path, expected in assertions.items():
        try:
            result[path] = wire(pointer(report, path)) == wire(expected)
        except (KeyError, IndexError, ValueError, TypeError, OverflowError):
            result[path] = False
    return result


def load_gold(guard):
    gold, actual = guard.load_json(ROOT / GOLD_PATH)
    if actual != GOLD_SHA256 or gold.get("schema") != "nabt.sourced-acquisition-gold.v3":
        raise ValueError("independent matrix pin or schema differs")
    cases = gold.get("cases")
    if type(cases) is not list or len(cases) != 161:
        raise ValueError("independent matrix denominator differs")
    ids, families, entries, positives = set(), Counter(), Counter(), 0
    for case in cases:
        if type(case) is not dict or any(type(case.get(k)) is not str for k in
                ("id", "family", "entry_point", "text", "ending", "onset")):
            raise ValueError("malformed case identity")
        if not case["id"] or case["id"] in ids:
            raise ValueError("duplicate or empty case identity")
        ids.add(case["id"]); families[case["family"]] += 1; entries[case["entry_point"]] += 1
        case["text"].encode("utf-8", "strict")
        if case["ending"] not in {"wasl", "waqf"} or case["onset"] not in {"word_initial", "connected"}:
            raise ValueError("invalid performance policy in matrix")
        goal = case.get("goal")
        if (type(goal) is not dict or type(goal.get("positive")) is not bool or
                type(goal.get("kind")) is not str):
            raise ValueError("malformed goal")
        positives += goal["positive"]
        for assertions in (case.get("expected"), goal.get("success")):
            if type(assertions) is not dict or not assertions or any(
                    type(path) is not str or not path.startswith("/") for path in assertions):
                raise ValueError("matrix requires nonempty pointer projections")
        if case["entry_point"] == "person_nominal" and case.get("task") not in {"person", "nominal_syntax"}:
            raise ValueError("unknown grammatical task")
        if case["entry_point"] == "conditional_pr34" and (type(case.get("query")) is not str or
                case.get("query_ending") not in {"wasl", "waqf"}):
            raise ValueError("conditional control lacks query binding")
    if dict(families) != FAMILIES or dict(entries) != ENTRYPOINTS or positives != 109:
        raise ValueError("matrix populations differ from independent freeze")
    return gold


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


def dispatch(case, modules):
    binding = {"source_id": "v3:" + case["id"], "revision": "1", "scope": SCOPE,
               "ending": case["ending"], "onset": case["onset"]}
    entry = case["entry_point"]
    if entry == "connected":
        return modules[entry].read_acquired(case["text"], **binding)
    if entry == "person_nominal":
        return modules[entry].evaluate(case["text"], task=case["task"], **binding)
    if entry == "natural":
        return modules[entry].evaluate(case["text"], **binding)
    ending = binding.pop("ending")
    return modules[entry].evaluate(case["text"], case["query"], source_ending=ending,
        query_ending=case["query_ending"], time="unspecified", **binding)


def evaluate_case(case, modules):
    report = dispatch(case, modules)
    expected = matches(report, case["expected"])
    goal = matches(report, case["goal"]["success"])
    entry = case["entry_point"]
    audit = modules["checks"].audit_report(entry, report, text=case["text"],
        source_id="v3:" + case["id"], revision="1", scope=SCOPE,
        ending=case["ending"], onset=case["onset"], task=case.get("task"),
        query=case.get("query"), query_ending=case.get("query_ending"), time="unspecified")
    source_safe, chain_safe, claim_safe = (audit[key] is True for key in
                                         ("source_safe", "chain_safe", "claim_safe"))
    chain = report.get("chain_complete") is True
    if entry == "connected":
        grants = report.get("status") == "ACQUIRED" or report.get("shape_verified") is True
    elif entry == "natural":
        grants = chain or bool(report.get("selected_sense_ids")) or report.get("semantic_scope_complete") is True
    elif entry == "person_nominal":
        grants = chain or report.get("verified") is True or report.get("person") is not None or report.get("nominal") is not None
    else:
        grants = chain or report.get("verified") is True or report.get("answer") is not None
    contract = all(expected.values())
    # A correct lower-stage reading with a missing higher-stage handoff is a
    # coverage miss, not a false lower-stage license. Scope each claimed result.
    claimed_paths = set(expected)
    if entry == "natural":
        claimed_paths = {path for path in expected if path in {
            "/selected_sense_ids", "/semantic_scope_complete", "/assertion_polarity",
            "/author_intention_established", "/world_truth_established"}}
        if chain:
            claimed_paths.add("/chain_complete")
    claim_matches = all(expected[path] for path in claimed_paths if path in expected)
    if entry == "conditional_pr34" and chain and case["expected"].get("/chain_complete") is False:
        grants = True
        claim_matches = False
    safe = source_safe and chain_safe and claim_safe
    required_candidates = case["expected"].get("/candidate_sense_ids")
    candidate_measurement = None
    if type(required_candidates) is list:
        actual_candidates = report.get("candidate_sense_ids", [])
        if type(actual_candidates) is not list or any(type(x) is not str for x in actual_candidates):
            actual_candidates = []
        candidate_measurement = {"required": len(set(required_candidates)),
            "retained": len(set(required_candidates) & set(actual_candidates)) if safe else 0,
            "observed_retained": len(set(required_candidates) & set(actual_candidates)),
            "unexpected": sorted(set(actual_candidates) - set(required_candidates))}
    return {"id": case["id"], "family": case["family"], "entry_point": entry,
        "goal_kind": case["goal"]["kind"], "positive": case["goal"]["positive"],
        "expected_checks": expected, "goal_checks": goal, "contract_match": contract,
        "goal_projection_matches": all(goal.values()), "goal_acquired": all(goal.values()) and safe,
        "source_checks": audit["source_checks"], "realization_checks": audit["realization_checks"],
        "binding_checks": audit["binding_checks"], "candidate_measurement": candidate_measurement,
        "source_safe": source_safe, "chain_safe": chain_safe, "claim_safe": claim_safe,
        "false_authorization": grants and not (claim_matches and safe),
        "chain_claimed": chain, "chain_complete": chain and safe, "raw_result": report}


def counts(rows):
    positives = [row for row in rows if row["positive"]]
    negatives = [row for row in rows if not row["positive"]]
    candidates = [row["candidate_measurement"] for row in rows if row.get("candidate_measurement") is not None]
    return {"cases": len(rows), "contract_matches": sum(row["contract_match"] for row in rows),
        "required_positive": len(positives), "positive_acquired": sum(row["goal_acquired"] for row in positives),
        "positive_misses": [row["id"] for row in positives if not row["goal_acquired"]],
        "negative_controls": len(negatives), "negative_contract_matches": sum(row["contract_match"] for row in negatives),
        "false_authorizations": sum(row["false_authorization"] for row in rows),
        "lexical_candidate_measurement": {"measured_cases": len(candidates),
            "required": sum(row["required"] for row in candidates),
            "retained": sum(row["retained"] for row in candidates),
            "unexpected": sum(len(row["unexpected"]) for row in candidates)},
        "complete_chains": sum(row["chain_complete"] for row in rows),
        "statuses": dict(Counter(row["raw_result"].get("status", "MISSING") for row in rows))}


def run(envelope, evidence, phase):
    guard = load_bootstrap(); inner = envelope["baseline"]
    before = initial_snapshot(guard, inner, phase)
    gold = load_gold(guard)
    with guard.frozen_runtime(inner) as imports:
        modules = {key: importlib.import_module(path) for key, path in {
            "connected": "tools.connected_acquisition_v3",
            "person_nominal": "tools.acquired_person_nominal_v3",
            "natural": "tools.natural_acquisition_v3",
            "conditional_pr34": "tools.acquired_inference_v2",
            "checks": "tools.sourced_acquisition_v3_checks"}.items()}
        rows = [evaluate_case(case, modules) for case in gold["cases"]]
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
    unsafe = [row["id"] for row in rows if not row["source_safe"] or not row["chain_safe"] or not row["claim_safe"] or row["false_authorization"]]
    return {"schema": RESULT_SCHEMA, "phase": phase, "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Finite four-family independent matrix. Positive coverage, restraint, lexical reading and complete chains have separate denominators; no overall Arabic completeness claim.",
        "summary": counts(rows),
        "families": {family: counts([r for r in rows if r["family"] == family]) for family in FAMILIES},
        "goals": {kind: counts([r for r in rows if r["goal_kind"] == kind]) for kind in sorted({r["goal_kind"] for r in rows})},
        "entry_points": {key: counts([r for r in rows if r["entry_point"] == key]) for key in ENTRYPOINTS},
        "execution_evidence": {**evidence, "before": before, "after": after,
            "initial_snapshot_matches_freeze": True, "integrity_valid": integrity,
            "runtime_import_policy": "fresh-frozen-source-only.v1", "executed_repository_python": imports.executed,
            "executed_hash_mismatches": wrong, "loaded_repository_python": loaded,
            "uncovered_modules": uncovered, "loaded_hash_mismatches": loaded_wrong,
            "python": sys.version, "platform": platform.platform()},
        "contract_gate": {"passed": integrity and not unsafe, "failures": unsafe},
        "projection_gate": {"passed": all(row["contract_match"] for row in rows),
                            "failures": [row["id"] for row in rows if not row["contract_match"]]},
        "rows": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-freeze", type=Path, required=True)
    parser.add_argument("--phase", choices=("first", "exposed"), required=True)
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        report = {"schema": RESULT_SCHEMA, "phase": args.phase, "status": "ATTEMPT_STARTED",
                  "started_at_utc": datetime.now(timezone.utc).isoformat(), "gold_sha256": GOLD_SHA256}
        stream.write(wire(report) + "\n"); stream.flush(); os.fsync(stream.fileno())
        stage = "preflight"
        try:
            freeze, evidence = verify_freeze(args.code_freeze, args.phase)
            stage = "execution"; report = run(freeze, evidence, args.phase)
        except Exception as exc:
            report = {**report, "status": "EVALUATOR_FAILURE", "failure_stage": stage,
                      "error": {"type": type(exc).__name__, "message": str(exc)}}
        stream.seek(0); json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n"); stream.truncate(); stream.flush(); os.fsync(stream.fileno())
    print(wire({key: value for key, value in report.items() if key in
                {"summary", "contract_gate", "projection_gate", "status", "failure_stage", "error"}}))
    return 0 if all(report.get(key, {}).get("passed") is True for key in ("contract_gate", "projection_gate")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
