#!/usr/bin/env python3
"""Replay the frozen, authored transport matrix without deriving its answers.

The oracle is the preimplementation 73-case matrix. Direct native responses,
public receipts, productive source handoff and authority flags are separate
observations. This evaluator measures finite contracts, never open Arabic,
source authenticity, world truth, or agreement between human interpreters.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import importlib
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from types import ModuleType
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_PATH = "tools/evaluate_aligned_acquisition.py"
BOOTSTRAP_SHA256 = "50b8e45b821818180854f6990324ea255206913ade849ee97c4fd5b5a0d056cb"
SOURCE_COMMIT = "168eec4ec205509ef74825c207b0dcef35a23b4a"
MATRIX_COMMIT = "02f48d67f2804295ad8c2cc668d95629709b1d61"
PREFIX = "evidence/meaning_preservation_v1/"
SOURCE_PATH = PREFIX + "source_scope.json"
INVENTORY_PATH = PREFIX + "research_inventory.json"
GOLD_PATH = PREFIX + "cases.json"
GOLD_SHA256 = "50f71123f992e764ea2b837a4221a627a2b17fe346e52c0ddd9908327f312aaa"
SOURCE_PINS = {
    "docs/MEANING_PRESERVATION_V1_SPEC.md": "6c49dc2a1012007bd488e6929eea32e1064baa85d3ee75437dd642de1a4e1b9a",
    "docs/MEANING_PRESERVATION_V1_FORMAL_SPEC.md": "6a27cfaffac9b4735117ea35f6370693d4e29bd11010bcc1e8e9fd5d029abc08",
    SOURCE_PATH: "5364e2bb2603a18950ded79d8b7d8787c3aba2d90c5617d6746c7a3b56ff18fe",
    INVENTORY_PATH: "d1cbf80bb015f47325561584712e21bacff14d18ae6c9f2b26256632289865c0",
    PREFIX + "source_protocol.json": "f887e29e4320bf7540289472b263db45b8f8692662389067985f9e71015c1df4",
    PREFIX + "research/morphology_inventory.json": "8c6dfee3ec18b79575b4a5d9a6d1123fc8d2c6fe0bf2a8fb499e1009635201fd",
    PREFIX + "research/composition_inventory.json": "c5d3051bde59c4584f8f5ba8916e3e42c618f15569e1abe628882521bd71683c",
    PREFIX + "research/interpretation_contracts.json": "9952651acb57b9416dca7fba095c6f14dd95bade40320201c804a196a2ddda0a",
}
MATRIX_PINS = {GOLD_PATH: GOLD_SHA256,
    PREFIX + "FOUR_FAMILY_PROTOCOL.md": "840d2feb4f49f883b21cca61b5aa8468ca0e0089150e00153ea395deb8411873"}
PINS = {**SOURCE_PINS, **MATRIX_PINS}
LAW_ID = "nabt.meaning-preservation.v1"
QUERY_ID = "joint-readings.v1"
CODEC_ID = "strict-json-packet.v1"
EVALUATOR_ID = "nabt.meaning-preservation-evaluator.v1"
SCHEMA = "nabt.meaning-preservation-code-freeze.v1"
RESULT_SCHEMA = "nabt.meaning-preservation-evaluation.v1"
REPORT_SCHEMA = "nabt.meaning-preservation.result.v1"
NATIVE_SCHEMA = "nabt.meaning-preservation.native-response.v1"
FLAGS = {name: False for name in ("world_truth_established", "source_authenticity_established",
    "referents_established", "all_arabic_complete", "human_interpretation_agreement_established")}
FAMILIES = {"preservation_positive": 15, "counterexamples": 20,
            "input_integrity": 26, "scope_resource_and_authority": 12}
LAYERS = {"public_contract": 65, "wrapper": 2, "productive_adapter": 6}
POPULATION = {"by_family": FAMILIES, "by_layer": LAYERS, "total_authored_cases": 73,
              "new_linguistic_coverage_cases": 0, "human_trials": 0}
NATIVE = "formal/.lake/build/bin/meaningPreservationV1"
NATIVE_PATHS = frozenset("formal/.lake/build/bin/" + name for name in
    ("alignedAcquisition", "licensedInference", "connectedAcquisitionV3", "productiveClauseV1", "meaningPreservationV1"))
REFERENCES = frozenset(PREFIX + "integration/" + name + ".json" for name in
    ("proof_catalog", "grammar_link_summary", "mantuq_proof_links", "linguistic_proof_links",
     "licensed_proof_links", "article_proof_links", "sourced_proof_links"))
EXTRA_PATHS = frozenset(PINS) | REFERENCES | frozenset({
    "evidence/aligned_acquisition_v1/gold.json", "formal/theorems.json", "Makefile",
    "tools/aligned_acquisition.mk", "tools/article_acquisition.mk", "tools/sourced_acquisition_v3.mk",
    "tools/productive_clause_v1.mk", "tools/meaning_preservation_v1.mk",
    "integrations/current_proof_references.mk", "evidence/operator_traceability_v1/registry.json",
    "docs/MEANING_PRESERVATION_RESEARCH_AR.md", "integrations/grammar_catalog.mk",
    "integrations/mantuq_inference.mk", "integrations/linguistic_truth.mk", "integrations/licensed_inference.mk",
    ".github/workflows/aligned-acquisition.yml", ".github/workflows/meaning-preservation.yml"})
CODE_IDENTITY_PATHS = ("tools/meaning_preservation_v1.py", "tools/meaning_preservation_cli.py")
SEMANTIC_STATUSES = {"FINITE_CONTRACT_VERIFIED", "CONTRACT_VIOLATION"}
CLAIM_FIELDS = ("verified", "chain_complete", "finite_contract_verified")
MAX_REPORT_BYTES = 8 * 1024 * 1024
# Authored from the installed source specification and frozen fixture texts.
# This table checks the adapter's role projection, not a new Arabic parser.
PRODUCTIVE_ROLES = {"MP-A01": ("ZAYD", "AMR"), "MP-A02": ("ZAYD", "AMR"),
                    "MP-A03": ("ZAYD", "ZAYD"), "MP-A06": ("ZAYD", "AMR")}
PRODUCTIVE_GATES = {"source_evidence_checked", "source_acquired", "acquisition_native_checked",
    "source_shapes", "syntax_native_checked", "finite_grammar_reading", "same_source_binding",
    "source_alignment", "scope_modes"}


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
    module = ModuleType("_nabt_meaning_preservation_bootstrap")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    return module


def packets_at(guard, commit):
    return [guard.parse_json(guard.git("show", commit + ":" + name, binary=True)) for name in
            (SOURCE_PATH, INVENTORY_PATH, "evidence/productive_clause_v1/source_scope.json",
             "evidence/sourced_acquisition_v3/source_evidence.json")]


def required_paths(guard, inventory, inference_sources, packets):
    result = guard.required_freeze_paths(inventory, inference_sources) | set(EXTRA_PATHS)
    scope, research, productive, acquisition = packets
    result.update(row["path"] for row in scope["imports"])
    result.add(scope["crosswalk"]["path"])
    result.update(row["path"] for row in research["existing_record_anchors"])
    for packet in (productive, acquisition):
        result.update(row["local_path"] for row in packet.get("passages", []) if "local_path" in row)
        result.update(row.get("repository_path", row.get("path")) for row in packet.get("sources", []))
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
            not same(envelope.get("content_pins"), PINS) or envelope.get("source_commit") != SOURCE_COMMIT or
            envelope.get("matrix_commit") != MATRIX_COMMIT or envelope.get("bootstrap") !=
            {"path": BOOTSTRAP_PATH, "sha256": BOOTSTRAP_SHA256}):
        raise ValueError("freeze schema, chronology or code-owned pins differ")
    inner = envelope.get("baseline")
    if type(inner) is not dict or type(inner.get("native")) is not dict or set(inner["native"]) != NATIVE_PATHS:
        raise ValueError("freeze requires exactly the five declared executables")
    with tempfile.TemporaryDirectory(prefix="nabt-meaning-freeze-") as directory:
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
        "evaluator_id": EVALUATOR_ID, "evaluator_sha256": inner["files"]["tools/evaluate_meaning_preservation_v1.py"],
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
    if (actual != GOLD_SHA256 or gold.get("schema") != "nabt.meaning-preservation-independent-matrix.v1" or
            not same(gold.get("counts"), POPULATION) or
            gold.get("authoring", {}).get("source_spec_commit") != SOURCE_COMMIT):
        raise ValueError("independent matrix identity or population differs")
    cases = gold.get("cases")
    if type(cases) is not list or len(cases) != 73 or len({c["id"] for c in cases}) != 73:
        raise ValueError("independent case population differs")
    if (dict(Counter(c["family"] for c in cases)) != FAMILIES or
            dict(Counter(c["layer"] for c in cases)) != LAYERS):
        raise ValueError("independent family or execution-layer population differs")
    return gold


def flags_safe(value):
    return type(value) is dict and all(value.get(key) is False for key in FLAGS)


def fixture_bytes(fixture):
    """Expand only the frozen fixture language; no producer or expected outputs."""
    kind = fixture["kind"]
    if kind in {"object_request", "native_control"}:
        return wire(deepcopy(fixture["request"])).encode("utf-8")
    if kind == "raw_json":
        return fixture["text"].encode("utf-8", "strict")
    if kind == "raw_bytes_hex":
        return bytes.fromhex(fixture["hex"])
    if kind == "expanded_source_text":
        request = deepcopy(fixture["request"])
        content = fixture["ascii_character"] * fixture["repeat"]
        for row in request["cases"]:
            row["original"]["binding"]["source_text"] = content
            packet = json.loads(row["transported_payload"])
            packet["binding"]["source_text"] = content
            row["transported_payload"] = wire(packet)
        return wire(request).encode("utf-8")
    if kind == "padded_json_with_trailing_spaces":
        raw = wire(fixture["request"]).encode("utf-8")
        padding = fixture["total_bytes"] - len(raw)
        if padding < 0:
            raise ValueError("frozen padding target is smaller than its request")
        return raw + b" " * padding
    raise ValueError("unknown frozen raw fixture kind: " + kind)


def call_cli(cli, guard, raw):
    with tempfile.TemporaryDirectory(prefix="nabt-meaning-case-") as directory:
        path = Path(directory) / "request.json"
        path.write_bytes(raw)
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = cli.main(["authored", "--request", str(path)])
        encoded = output.getvalue().encode("utf-8", "strict")
        if len(encoded) > MAX_REPORT_BYTES:
            raise ValueError("public report exceeds the declared byte limit")
        return guard.parse_json(encoded), exit_code


def direct_native(raw, guard):
    with tempfile.TemporaryDirectory(prefix="nabt-meaning-direct-") as directory:
        output = Path(directory) / "native.json"
        with output.open("wb") as stream:
            run = subprocess.run([str(ROOT / NATIVE)], input=raw + b"\n", stdout=stream,
                                 stderr=subprocess.PIPE, timeout=30, check=False)
        if output.stat().st_size > MAX_REPORT_BYTES:
            raise ValueError("direct native response exceeded frozen report bound")
        observed = output.read_bytes()
    return {"response": guard.parse_json(observed), "returncode": run.returncode,
            "stderr": run.stderr.decode("utf-8", "replace")[:4096],
            "request_sha256": digest(raw), "request_bytes": len(raw), "response_sha256": digest(observed)}


def expected_native(expected, request):
    """Project the authored expected status to the fixed native wire contract."""
    status = expected["status"]
    reason = expected["reason"]
    count, first, other = 0, None, None
    if status in SEMANTIC_STATUSES:
        count = len(request["cases"])
        if status == "CONTRACT_VIOLATION":
            first = request["cases"][0]["case_id"]
            if reason == "FIBER_COLLISION":
                other = request["cases"][1]["case_id"]
    elif status in {"INVALID_INPUT", "RESOURCE_EXHAUSTED"}:
        reason = "INVALID_REQUEST" if status == "INVALID_INPUT" else "RESOURCE_LIMIT"
    else:
        raise ValueError("this expectation does not require a direct native response")
    return {"schema": NATIVE_SCHEMA, "law_id": LAW_ID, "query_id": QUERY_ID,
            "codec_id": CODEC_ID, "status": status, "reason": reason, "case_id": first,
            "other_case_id": other, "case_count": count, "world_truth_established": False,
            "whole_arabic_completeness_established": False}


def native_matches(expected, request, direct):
    code = 0 if expected["status"] in SEMANTIC_STATUSES else 2
    return type(direct) is dict and direct.get("returncode") == code and same(
        direct.get("response"), expected_native(expected, request))


def source_observation_vectors(packet):
    """Independent trace audit using the declared tuple fields, not a decision oracle."""
    context, binding = packet["source_context"], packet["binding"]
    def term(value):
        if value is None:
            return None
        return (value["kind"], value["value"] if value["kind"] == "entity" else context[value["kind"]])
    return {wire((r["predicate"], term(r["subject"]), term(r["object"]), r["positive"],
                  r["tense"], r["voice"], r["force"], binding["scope"], binding["convention"],
                  context["time"], context["place"])) for r in packet["alternatives"]}


def trace_matches(request, observations, guard):
    try:
        if type(observations) is not list or len(observations) != len(request["cases"]):
            return False
        fields = {"predicate", "subject", "object", "positive", "tense", "voice", "force",
                  "scope", "convention", "time", "place"}
        for case, observed in zip(request["cases"], observations):
            payload = case["transported_payload"].encode("utf-8")
            if (set(observed) != {"case_id", "original", "decoded", "payload_bytes", "payload_sha256"} or
                    observed["case_id"] != case["case_id"] or type(observed["payload_bytes"]) is not int or
                    observed["payload_bytes"] != len(payload) or observed["payload_sha256"] != digest(payload)):
                return False
            for key, packet in (("original", case["original"]), ("decoded", guard.parse_json(payload))):
                values = observed[key]
                if type(values) is not list or any(type(v) is not dict or set(v) != fields for v in values):
                    return False
                def term(v):
                    if v is None:
                        return None
                    if type(v) is not dict or set(v) != {"kind", "value"}:
                        raise ValueError("malformed observed Term")
                    return (v["kind"], v["value"])
                vectors = [wire((v["predicate"], term(v["subject"]), term(v["object"]), v["positive"],
                    v["tense"], v["voice"], v["force"], v["scope"], v["convention"], v["time"], v["place"])) for v in values]
                if len(set(vectors)) != len(vectors) or set(vectors) != source_observation_vectors(packet):
                    return False
        return True
    except (KeyError, TypeError, ValueError, UnicodeError):
        return False


def identity_matches(value, inner):
    expected = {"code": {name: inner["files"][name] for name in CODE_IDENTITY_PATHS},
                "native_path": NATIVE, "native_sha256": inner["native"][NATIVE]}
    return same(value, expected)


def audit_report(case, report, request, guard, inner=None, direct=None, cli_exit=None):
    expected = case["expected"]
    if type(report) is not dict:
        return {"match": False, "false_authorization": False}
    status_ok = report.get("status") == expected["status"]
    reason_ok = expected["reason"] is None or report.get("reason") == expected["reason"]
    shape_ok = flags_safe(report)
    schema_present = "schema" in report
    if schema_present:
        shape_ok = shape_ok and report.get("schema") == REPORT_SCHEMA and all(
            report.get(key) == value for key, value in (("law_id", LAW_ID), ("query_id", QUERY_ID), ("codec_id", CODEC_ID)))
        shape_ok = shape_ok and all(type(report.get(key)) is bool for key in (*CLAIM_FIELDS, "native_checked", "producer_chain_complete"))
    else:
        shape_ok = shape_ok and set(report) == {"status", "reason", *FLAGS} and expected["status"] in {"INVALID_INPUT", "RESOURCE_EXHAUSTED"}
    positive = expected["status"] == "FINITE_CONTRACT_VERIFIED"
    claims_ok = all(report.get(key) is positive for key in CLAIM_FIELDS) if schema_present else not positive
    if schema_present:
        authority = ("PRODUCTIVE_CLAUSE_SOURCE_BOUND_FINITE_CONTRACT" if case["layer"] == "productive_adapter"
                     else "AUTHORED_PREMISES_FINITE_CONTRACT") if positive else "NO_FINITE_CONTRACT_AUTHORITY"
        claims_ok = claims_ok and report.get("authority") == authority
    semantic = expected["status"] in SEMANTIC_STATUSES
    binding_ok = True
    if semantic:
        binding_ok = (schema_present and report.get("native_checked") is True and
            same(report.get("contract_request"), request) and
            report.get("contract_request_sha256") == digest(wire(request).encode("utf-8")) and
            same(report.get("proposal"), expected_native(expected, request)) and
            same(report.get("native_result"), expected_native(expected, request)) and
            trace_matches(request, report.get("observations"), guard) and
            (inner is None or identity_matches(report.get("execution"), inner)))
    elif schema_present:
        binding_ok = report.get("native_checked") is False and report.get("native_result") is None
    input_ok = True
    if semantic or case["layer"] == "productive_adapter":
        input_ok = same(report.get("input_request"), case.get("executed_input", request))
    producer_ok = True
    if "producer_chain_complete" in expected:
        producer_ok = report.get("producer_chain_complete") is expected["producer_chain_complete"]
        producer = report.get("producer")
        producer_ok = producer_ok and type(producer) is dict and producer.get("chain_complete") is expected["producer_chain_complete"]
        if expected["producer_chain_complete"] and type(producer) is dict:
            producer_ok = (producer_ok and producer.get("verified") is True and
                type(producer.get("gates")) is dict and set(producer["gates"]) == PRODUCTIVE_GATES and
                all(value is True for value in producer["gates"].values()) and producer.get("blocked_by") == [] and
                all(producer.get(key) is False for key in ("world_truth_established", "referents_established",
                                                          "entails_exclusivity", "all_arabic_complete")))
        elif not expected["producer_chain_complete"]:
            producer_ok = producer_ok and report.get("contract_request") is None
    native_ok = direct is None or native_matches(expected, request, direct)
    code_ok = True
    if cli_exit is not None:
        wanted = 0 if positive else 3 if expected["status"] in {"CONTRACT_VIOLATION", "DEFER", "REJECTED_IN_SCOPE"} else 5 if expected["status"] == "RESOURCE_EXHAUSTED" else 2 if expected["status"] == "INVALID_INPUT" else 4
        code_ok = type(cli_exit) is int and cli_exit == wanted
    match = bool(shape_ok and status_ok and reason_ok and claims_ok and binding_ok and input_ok and producer_ok and native_ok and code_ok)
    claims = report.get("status") == "FINITE_CONTRACT_VERIFIED" or any(
        report.get(key) is not False and report.get(key) is not None for key in CLAIM_FIELDS)
    false_native = direct is not None and type(direct.get("response")) is dict and (
        (direct["response"].get("status") == "FINITE_CONTRACT_VERIFIED" and not native_ok) or
        any(direct["response"].get(key) is not False for key in
            ("world_truth_established", "whole_arabic_completeness_established")))
    producer = report.get("producer")
    false_producer = type(producer) is dict and any(producer.get(key) is not False for key in
        ("world_truth_established", "referents_established", "entails_exclusivity", "all_arabic_complete"))
    return {"match": match, "false_authorization": bool((claims and not match) or not flags_safe(report) or false_native or false_producer),
        "status_match": status_ok, "shape_match": bool(shape_ok), "binding_match": bool(binding_ok),
        "input_match": input_ok, "producer_match": producer_ok, "direct_native_match": native_ok,
        "cli_exit_match": code_ok}


def productive_projection_matches(case_id, original_request, contract):
    """Literal source-role oracle for the four complete declared fixtures."""
    try:
        subject, obj = PRODUCTIVE_ROLES[case_id]
        if (type(contract) is not dict or set(contract) !=
                {"law_id", "query_id", "codec_id", "cases", "recipient_context"} or
                contract["law_id"] != LAW_ID or contract["query_id"] != QUERY_ID or
                contract["codec_id"] != CODEC_ID or type(contract["cases"]) is not list or
                len(contract["cases"]) != 1):
            return False
        case = contract["cases"][0]
        if (set(case) != {"case_id", "original", "transported_payload"} or
                type(case["case_id"]) is not str or not case["case_id"]):
            return False
        packet = case["original"]
        expected = {"binding": {"source_id": original_request["source_id"], "revision": original_request["revision"],
                    "scope": original_request["scope"], "source_text": original_request["text"],
                    "convention": "nabt.productive-clause.v1"},
            "source_context": original_request["source_context"],
            "alternatives": [{"predicate": "DARABA", "subject": {"kind": "entity", "value": subject},
                "object": {"kind": "entity", "value": obj}, "positive": True,
                "tense": "past", "voice": "active", "force": "asserted"}]}
        payload = original_request["transported_payload"]
        expected_payload = wire(expected) if payload is None else payload
        return (same(packet, expected) and case["transported_payload"] == expected_payload and
                same(contract["recipient_context"], original_request["recipient_context"]))
    except (KeyError, IndexError, TypeError):
        return False


def evaluate_case(case, reader, cli, guard, inner=None):
    fixture, expected = case["fixture"], case["expected"]
    observed_case = deepcopy(case)
    preliminary, direct, verification, cli_exit = None, None, None, None
    intervention = None
    if fixture["kind"] == "productive_request":
        executed = deepcopy(fixture["request"])
        if fixture.get("transport_edit"):
            if fixture["transport_edit"] != "swap_subject_object_after_fresh_projection":
                raise ValueError("unknown frozen productive channel mutation")
            preliminary = reader.evaluate_productive_request(deepcopy(executed))
            if preliminary.get("verified") is True and preliminary.get("producer_chain_complete") is True:
                packet = deepcopy(preliminary["contract_request"]["cases"][0]["original"])
                for reading in packet["alternatives"]:
                    reading["subject"], reading["object"] = reading["object"], reading["subject"]
                executed["transported_payload"] = wire(packet)
                report = reader.evaluate_productive_request(deepcopy(executed))
            else:
                report = preliminary
        else:
            report = reader.evaluate_productive_request(deepcopy(executed))
        request = report.get("contract_request")
        observed_case["executed_input"] = deepcopy(executed)
        if type(request) is dict:
            direct = direct_native(wire(request).encode("utf-8"), guard)
        projection_ok = (not expected["producer_chain_complete"] or
                         productive_projection_matches(case["id"], executed, request))
    else:
        raw = fixture_bytes(fixture)
        try:
            request = guard.parse_json(raw)
        except (ValueError, UnicodeError):
            request = None
        if fixture["kind"] == "native_control":
            if fixture["control"] == "missing_binary":
                missing = ROOT / "formal/.lake/build/bin/__meaning_missing_control__"
                if missing.exists():
                    raise ValueError("missing-native control path unexpectedly exists")
                with patch.object(reader, "NATIVE", missing):
                    report, cli_exit = call_cli(cli, guard, raw)
                intervention = "DECLARED_MISSING_NATIVE_PATH_CONTROL"
            elif fixture["control"] == "nonzero_exit":
                real_run = subprocess.run
                def failed_process(command, **kwargs):
                    if command != [str(ROOT / NATIVE)]:
                        raise ValueError("unexpected subprocess in native failure control")
                    return real_run([sys.executable, "-c", "raise SystemExit(23)"], **kwargs)
                with patch.object(reader.subprocess, "run", side_effect=failed_process):
                    report, cli_exit = call_cli(cli, guard, raw)
                intervention = "DECLARED_REAL_NONZERO_PROCESS_SUBSTITUTION_CONTROL"
            else:
                raise ValueError("unknown frozen native control")
        else:
            report, cli_exit = call_cli(cli, guard, raw)
            direct = direct_native(raw, guard)
        projection_ok = True
    audit = audit_report(observed_case, report, request, guard, inner, direct, cli_exit)
    audit["productive_projection_match"] = projection_ok
    replay_required = expected["status"] in SEMANTIC_STATUSES or case["layer"] == "productive_adapter"
    if replay_required:
        mode = "productive" if case["layer"] == "productive_adapter" else "authored"
        supplied = observed_case.get("executed_input", request)
        verification = reader.verify(deepcopy(report), expected_request=deepcopy(supplied), mode=mode)
        replay_ok = (type(verification) is dict and verification.get("replay_matches") is True and
                     verification.get("valid") is (expected["status"] == "FINITE_CONTRACT_VERIFIED") and flags_safe(verification))
    else:
        replay_ok = True
    direct_required = case["layer"] == "public_contract" or (case["layer"] == "productive_adapter" and expected.get("producer_chain_complete") is True)
    direct_ok = bool(direct is not None and native_matches(expected, request, direct)) if direct_required else direct is None
    match = audit["match"] and projection_ok and replay_ok and direct_ok
    false = audit["false_authorization"] or (type(verification) is dict and (
        (verification.get("valid") is True and not match) or not flags_safe(verification)))
    if not projection_ok and report.get("verified") is True:
        false = True
    match = match and not false
    return {"id": case["id"], "family": case["family"], "layer": case["layer"],
        "expected_status": expected["status"], "contract_match": bool(match), "false_authorization": bool(false),
        "direct_native_required": direct_required, "direct_native_match": direct_ok,
        "verification_required": replay_required, "verification_match": replay_ok,
        "producer_complete_required": expected.get("producer_chain_complete"),
        "productive_projection_match": projection_ok, "audit": audit, "public_report": report,
        "direct_native": direct, "verification": verification, "preliminary_producer_report": preliminary,
        "controlled_intervention": intervention, "cli_exit": cli_exit}


def counts(rows):
    return {"cases": len(rows), "contracts": sum(r["contract_match"] for r in rows),
        "by_family": {name: {"cases": sum(r["family"] == name for r in rows),
            "contracts": sum(r["family"] == name and r["contract_match"] for r in rows)} for name in FAMILIES},
        "by_layer": {name: {"cases": sum(r["layer"] == name for r in rows),
            "contracts": sum(r["layer"] == name and r["contract_match"] for r in rows)} for name in LAYERS},
        "positive_goals": sum(r["expected_status"] == "FINITE_CONTRACT_VERIFIED" for r in rows),
        "positive_goals_met": sum(r["expected_status"] == "FINITE_CONTRACT_VERIFIED" and r["contract_match"] for r in rows),
        "direct_native_required": sum(r["direct_native_required"] for r in rows),
        "direct_native_matched": sum(r["direct_native_required"] and r["direct_native_match"] for r in rows),
        "direct_native_errors_required": sum(r["direct_native_required"] and r["expected_status"] in {"INVALID_INPUT", "RESOURCE_EXHAUSTED"} for r in rows),
        "direct_native_errors_matched": sum(r["direct_native_required"] and r["direct_native_match"] and r["expected_status"] in {"INVALID_INPUT", "RESOURCE_EXHAUSTED"} for r in rows),
        "receipt_replays_required": sum(r["verification_required"] for r in rows),
        "receipt_replays_matched": sum(r["verification_required"] and r["verification_match"] for r in rows),
        "productive_complete_required": sum(r["producer_complete_required"] is True for r in rows),
        "productive_complete_matched": sum(r["producer_complete_required"] is True and r["contract_match"] for r in rows),
        "observed_false_authorizations": sum(r["false_authorization"] for r in rows), "required_skips": 0}


def acceptance(summary, integrity):
    checks = {"all_authored_contracts": summary["cases"] == summary["contracts"] == 73,
        "family_denominators": all(summary["by_family"][name] == {"cases": n, "contracts": n} for name, n in FAMILIES.items()),
        "layer_denominators": all(summary["by_layer"][name] == {"cases": n, "contracts": n} for name, n in LAYERS.items()),
        "all_positive_goals": summary["positive_goals"] == summary["positive_goals_met"] == 15,
        "all_direct_native": summary["direct_native_required"] == summary["direct_native_matched"] == 69,
        "direct_native_errors": summary["direct_native_errors_required"] == summary["direct_native_errors_matched"] == 34,
        "receipt_replays": summary["receipt_replays_required"] == summary["receipt_replays_matched"] == 37,
        "productive_complete": summary["productive_complete_required"] == summary["productive_complete_matched"] == 4,
        "no_observed_false_authorizations": summary["observed_false_authorizations"] == 0,
        "no_required_skips": summary["required_skips"] == 0, "execution_integrity": bool(integrity)}
    return {"passed": all(checks.values()), "checks": checks, "authority": "AUTHORED_FINITE_CONTRACT_MATRIX_ONLY", **FLAGS}


class ScenarioExecutionError(RuntimeError):
    def __init__(self, case_id, rows, cause):
        super().__init__(str(cause))
        self.case_id, self.rows, self.cause_type = case_id, deepcopy(rows), type(cause).__name__
        self.cause_message = str(cause)
        self.execution_evidence = {"integrity_valid": False}


def run(envelope, evidence, phase, *, checkpoint=None):
    guard = load_bootstrap(); inner = envelope["baseline"]
    before = initial_snapshot(guard, inner, phase)
    gold = load_gold(guard)
    rows = []
    run_stage = "__runtime_setup__"
    partial_evidence = {"before": before, "initial_snapshot_matches_freeze": True,
                        "integrity_valid": False}
    try:
        # This try also covers context-manager exit and final report assembly.
        # Neither a postflight error nor an origin-audit error discards rows.
        with guard.frozen_runtime(inner) as imports:
            reader = importlib.import_module("tools.meaning_preservation_v1")
            cli = importlib.import_module("tools.meaning_preservation_cli")
            for case in gold["cases"]:
                try:
                    rows.append(evaluate_case(case, reader, cli, guard, inner))
                except Exception as exc:
                    raise ScenarioExecutionError(case["id"], rows, exc) from exc
                if checkpoint is not None:
                    try:
                        checkpoint(rows[-1])
                    except Exception as exc:
                        raise ScenarioExecutionError("__checkpoint__:" + case["id"], rows, exc) from exc
            run_stage = "__postflight__"
            after = guard.snapshot(inner, ROOT / GOLD_PATH)
            partial_evidence["after"] = after
            partial_evidence["executed_repository_python"] = dict(imports.executed)
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
            "scope": "73 authored exposed finite transport controls; no new Arabic accuracy or human/world observations.",
            "summary": summary, "acceptance_gate": acceptance(summary, bool(integrity)),
            "execution_evidence": {**evidence, "before": before, "after": after,
                "initial_snapshot_matches_freeze": True, "integrity_valid": bool(integrity),
                "runtime_import_policy": "fresh-frozen-source-only.v1", "executed_repository_python": imports.executed,
                "executed_hash_mismatches": wrong, "loaded_repository_python": loaded,
                "uncovered_modules": uncovered, "loaded_hash_mismatches": loaded_wrong,
                "python": sys.version, "platform": platform.platform(),
                "command": evidence.get("command", list(sys.argv)),
                "toolchain": (ROOT / "formal/lean-toolchain").read_text().strip()}, "rows": rows}
    except ScenarioExecutionError as exc:
        exc.execution_evidence.update(partial_evidence)
        raise
    except Exception as exc:
        failure = ScenarioExecutionError(run_stage, rows, exc)
        failure.execution_evidence.update(partial_evidence)
        raise failure from exc


def persist_report(stream, report):
    stream.seek(0)
    json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
    stream.write("\n"); stream.truncate(); stream.flush(); os.fsync(stream.fileno())


def append_checkpoint(stream, event):
    """Retain completed observations; this is not atomic execution isolation."""
    stream.write(wire(event) + "\n"); stream.flush(); os.fsync(stream.fileno())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-freeze", type=Path, required=True)
    parser.add_argument("--phase", choices=("first", "exposed"), required=True)
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    command = list(sys.argv) if argv is None else [str(Path(__file__)), *argv]
    progress_path = args.output.with_name(args.output.name + ".progress.jsonl")
    attempt = {"command": command, "code_freeze_path": str(args.code_freeze.resolve()),
               "output_path": str(args.output.resolve())}
    progress_info = {"path": str(progress_path.resolve()),
        "scope": "Completed-row checkpoints; not a success receipt or atomic execution isolation."}
    with args.output.open("x", encoding="utf-8") as stream:
        report = {"schema": RESULT_SCHEMA, "evaluator_id": EVALUATOR_ID, "phase": args.phase,
            "status": "ATTEMPT_STARTED", "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "gold_sha256": GOLD_SHA256, "attempt": attempt, "progress_log": progress_info}
        persist_report(stream, report)
        with ExitStack() as resources:
            stage = "checkpoint_initialization"
            try:
                progress = resources.enter_context(progress_path.open("x", encoding="utf-8"))
                append_checkpoint(progress, {"event": "attempt_started", "attempt": attempt,
                    "phase": args.phase, "gold_sha256": GOLD_SHA256})
                stage = "preflight"
                freeze, evidence = verify_freeze(args.code_freeze, args.phase)
                evidence = {**evidence, "code_freeze_path": attempt["code_freeze_path"], "command": command}
                report.update(status="PREFLIGHT_VALIDATED", execution_evidence=evidence)
                # The validated manifest hash, path and command survive even if
                # run fails before returning or the process is interrupted.
                persist_report(stream, report)
                append_checkpoint(progress, {"event": "preflight_validated", "execution_evidence": evidence})
                stage = "execution"
                measured = run(freeze, evidence, args.phase,
                    checkpoint=lambda row: append_checkpoint(progress, {"event": "case_completed", "row": row}))
                report = {**measured, "attempt": attempt, "progress_log": progress_info}
            except Exception as exc:
                report = {**report, "status": "EVALUATOR_FAILURE", "failure_stage": stage,
                          "error": {"type": type(exc).__name__, "message": str(exc)},
                          "acceptance_gate": {"passed": False},
                          "execution_evidence": {**report.get("execution_evidence", {}), "integrity_valid": False}}
                if isinstance(exc, ScenarioExecutionError):
                    report.update(failed_case_id=exc.case_id, cause_type=exc.cause_type,
                                  cause_message=exc.cause_message, completed_rows=exc.rows)
                    report["execution_evidence"].update(exc.execution_evidence)
            persist_report(stream, report)
    print(wire({k: v for k, v in report.items() if k in {"summary", "acceptance_gate", "status", "failure_stage", "error"}}))
    return 0 if report.get("acceptance_gate", {}).get("passed") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
