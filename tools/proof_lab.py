"""Bounded transport from a private proof lab to the installed Lean checker.

The request contains text and budgets, never code, paths, rules or authority.
The result is an execution receipt; it does not strengthen the kernel's scope.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from tools.licensed_inference import InferenceBudget, evaluate

REQUEST_SCHEMA = "nabt.proof-lab-request.v1"
RESULT_SCHEMA = "nabt.proof-lab-result.v1"
ENVELOPE_SCHEMA = "nabt.proof-lab-envelope.v1"
MAX_PAYLOAD_BYTES = 32768
MAX_SOURCE_BYTES = 16384
MAX_QUERY_BYTES = 4096
MAX_RESULT_BYTES = 2 * 1024 * 1024
MAX_EVENT_BYTES = 2 * 1024 * 1024
BUDGET_LIMITS = {
    "max_clauses": 64, "max_readings": 64,
    "max_atoms": 256, "max_closure_steps": 256,
}
SMOKE_ID = "00000000-0000-4000-8000-000000000001"
SMOKE_PAYLOAD = json.dumps({
    "schema": REQUEST_SCHEMA, "mode": "inference",
    "source_text": "إِنْ عَرَفَ زَيْدٌ الْحَقَّ سَارَ زَيْدٌ. عَرَفَ زَيْدٌ الْحَقَّ.",
    "query_text": "هَلْ سَارَ زَيْدٌ؟",
}, ensure_ascii=False, separators=(",", ":"))
SCOPE = {
    "law_id": "nabt.licensed-inference.v1",
    "accepted_language": "nabt.explicit-subject-active.v1",
    "claim": "Source-relative inference in the installed bounded grammar",
    "whole_arabic": "NOT_PROVED",
    "external_world": "NOT_VERIFIED",
    "benchmark_denominator": "38 frozen diagnostic cases, not all Arabic",
}
RESULT_STATES = {
    "SUPPORTED", "REFUTED", "CONFLICT", "UNKNOWN", "DEFER", "DISAGREEMENT",
    "INVALID_INPUT", "SOURCE_UNAVAILABLE", "VERIFICATION_UNAVAILABLE", "RESOURCE_EXHAUSTED",
}
CHECKED_STATES = {"SUPPORTED", "REFUTED", "CONFLICT", "UNKNOWN", "DEFER", "DISAGREEMENT"}
BOOLEAN_FLAGS = {
    "verified", "native_checked", "all_readings_complete", "closures_checked",
    "all_arabic_complete", "world_truth_established", "premise_world_truth_established",
    "source_interpretation_historically_proved",
}


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nabt import foundation

class RequestError(ValueError):
    """A stable error code; it never includes caller-supplied text."""


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RequestError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _constant(_):
    raise RequestError("NONFINITE_JSON_NUMBER")


def strict_json(raw: str | bytes, maximum: int):
    if type(raw) not in (str, bytes):
        raise RequestError("JSON_TEXT_REQUIRED")
    try:
        encoded = raw.encode("utf-8", "strict") if type(raw) is str else raw
        if len(encoded) > maximum:
            raise RequestError("INPUT_BYTE_LIMIT")
        return json.loads(encoded.decode("utf-8", "strict"),
                          object_pairs_hook=_unique, parse_constant=_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise RequestError("INVALID_UTF8_OR_JSON") from exc


def validate_id(value):
    if type(value) is not str:
        raise RequestError("INVALID_REQUEST_ID")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise RequestError("INVALID_REQUEST_ID") from exc
    if str(parsed) != value or parsed.version != 4:
        raise RequestError("INVALID_REQUEST_ID")
    return value


def transport_key(value):
    if type(value) is not str or re.fullmatch(r"[0-9a-fA-F]{64}", value) is None:
        raise RequestError("TRANSPORT_KEY_UNAVAILABLE")
    return bytes.fromhex(value)


def _base64(value, maximum):
    if type(value) is not str or len(value) > 4 * ((maximum + 2) // 3):
        raise RequestError("INVALID_ENCRYPTED_ENVELOPE")
    try:
        result = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise RequestError("INVALID_ENCRYPTED_ENVELOPE") from exc
    if len(result) > maximum or base64.b64encode(result).decode("ascii") != value:
        raise RequestError("INVALID_ENCRYPTED_ENVELOPE")
    return result


def decrypt_envelope(request_id, serialized, key, maximum=MAX_PAYLOAD_BYTES):
    """AES-256-GCM authenticates the request ID and never accepts bare JSON."""
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    validate_id(request_id)
    if type(key) is not bytes or len(key) != 32:
        raise RequestError("TRANSPORT_KEY_UNAVAILABLE")
    envelope = strict_json(serialized, 512 + 4 * ((maximum + 18) // 3))
    if (type(envelope) is not dict or set(envelope) != {"schema", "nonce", "ciphertext"}
            or envelope["schema"] != ENVELOPE_SCHEMA):
        raise RequestError("INVALID_ENCRYPTED_ENVELOPE")
    nonce = _base64(envelope["nonce"], 12)
    ciphertext = _base64(envelope["ciphertext"], maximum + 16)
    if len(nonce) != 12 or len(ciphertext) < 16:
        raise RequestError("INVALID_ENCRYPTED_ENVELOPE")
    try:
        return AESGCM(key).decrypt(nonce, ciphertext, request_id.encode("utf-8"))
    except InvalidTag as exc:
        raise RequestError("ENCRYPTED_REQUEST_AUTHENTICATION_FAILED") from exc


def encrypt_envelope(request_id, plaintext, key, maximum=MAX_RESULT_BYTES):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    validate_id(request_id)
    if type(key) is not bytes or len(key) != 32:
        raise RequestError("TRANSPORT_KEY_UNAVAILABLE")
    if type(plaintext) is not bytes or len(plaintext) > maximum:
        raise RequestError("ENCRYPTED_PLAINTEXT_BYTE_LIMIT")
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, request_id.encode("utf-8"))
    return {"schema": ENVELOPE_SCHEMA,
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii")}


def _text(value, maximum, field):
    if type(value) is not str or not value.strip():
        raise RequestError(field + "_TEXT_REQUIRED")
    try:
        raw = value.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise RequestError("INVALID_UNICODE") from exc
    if len(raw) > maximum:
        raise RequestError(field + "_BYTE_LIMIT")
    return value


def validate_payload(payload):
    request = strict_json(payload, MAX_PAYLOAD_BYTES)
    if type(request) is not dict or request.get("schema") != REQUEST_SCHEMA:
        raise RequestError("INVALID_REQUEST_SCHEMA")
    mode = request.get("mode")
    if mode == "licensed_workflow":
        if set(request) != {"schema", "mode", "workflow"}:
            raise RequestError("UNEXPECTED_REQUEST_FIELD")
        workflow = request["workflow"]
        if (type(workflow) is not dict or set(workflow) != {"schema", "op", "input"}
                or workflow["schema"] != "nabt.licensed-workflow-request.v1"
                or type(workflow["op"]) is not str
                or workflow["op"] not in {"lexical_surface", "lexical_candidates", "classical_control",
                                          "scope_acquisition", "lexical_transmission", "discourse_boundary", "source_inference",
                                          "six_noun_acquisition"}
                or type(workflow["input"]) is not dict):
            raise RequestError("INVALID_WORKFLOW_REQUEST")
        from tools.licensed_workflow import _OPERATIONS
        definition = _OPERATIONS[workflow["op"]]
        if (not definition["required"] <= set(workflow["input"])
                or set(workflow["input"]) - definition["required"] - definition["optional"]):
            raise RequestError("UNDECLARED_WORKFLOW_ARGUMENT")
        def portable(value):
            if type(value) is int and not -(2**53-1) <= value <= 2**53-1:
                raise RequestError("UNSAFE_WORKFLOW_INTEGER")
            if type(value) is float:
                raise RequestError("WORKFLOW_INTEGER_REQUIRED")
            if type(value) is str:
                value.encode("utf-8", "strict")
            if type(value) is dict:
                for key, child in value.items():
                    portable(key)
                    portable(child)
            if type(value) is list:
                for child in value:
                    portable(child)
        portable(workflow)
        return request
    if mode == "testimony":
        if set(request) != {"schema", "mode", "entry", "target"}:
            raise RequestError("UNEXPECTED_REQUEST_FIELD")
        _text(request["entry"], 128, "ENTRY")
        if type(request["target"]) is not list or len(request["target"]) > 64:
            raise RequestError("INVALID_TARGET")
        for component in request["target"]:
            _text(component, 4096, "TARGET")
        return request
    if mode == "semantic_axes":
        if set(request) not in ({"schema", "mode"}, {"schema", "mode", "lexical_profile"}):
            raise RequestError("UNEXPECTED_REQUEST_FIELD")
        profile = request.get("lexical_profile", "teaching_v1")
        if type(profile) is not str or profile not in {"teaching_v1", "attested_qac_v1"}:
            raise RequestError("INVALID_LEXICAL_PROFILE")
        return request
    if mode in ("benchmark", "epistemic_measurement", "contextual_reference"):
        if set(request) != {"schema", "mode"}:
            raise RequestError("UNEXPECTED_REQUEST_FIELD")
        return request
    if mode != "inference":
        raise RequestError("UNSUPPORTED_MODE")
    required = {"schema", "mode", "source_text", "query_text"}
    if not required <= set(request) or not set(request) <= required | {"budget"}:
        raise RequestError("UNEXPECTED_REQUEST_FIELD")
    _text(request["source_text"], MAX_SOURCE_BYTES, "SOURCE")
    _text(request["query_text"], MAX_QUERY_BYTES, "QUERY")
    supplied = request.get("budget", {})
    if type(supplied) is not dict or not set(supplied) <= set(BUDGET_LIMITS):
        raise RequestError("INVALID_BUDGET_FIELDS")
    for key, value in supplied.items():
        if type(value) is not int or not 0 <= value <= BUDGET_LIMITS[key]:
            raise RequestError("INVALID_BUDGET_VALUE")
    return request


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _code_sha():
    value = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                           capture_output=True, text=True, check=True,
                           timeout=5).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise RuntimeError("CODE_IDENTITY_UNAVAILABLE")
    expected = os.environ.get("GITHUB_SHA")
    if expected and value != expected:
        raise RuntimeError("CODE_IDENTITY_MISMATCH")
    return value


def _identity():
    binary = ROOT / "formal/.lake/build/bin/licensedInference"
    return {
        "code_sha": _code_sha(),
        "native_sha256": _sha(binary.read_bytes()) if binary.is_file() else None,
        "runner_sha256": _sha(Path(__file__).read_bytes()),
        "runtime_sha256": _sha((ROOT / "tools/licensed_inference/runtime.py").read_bytes()),
        "toolchain": (ROOT / "formal/lean-toolchain").read_text().strip(),
    }


def _workflow_wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _workflow_identity():
    binaries = ("lexicalSourceRows", "lexicalSurface", "linguisticTruth", "exportClassicalHamza",
                "exportClassicalWeak", "exportClassicalGemination", "exportClassicalBoundaryAffixes", "qualifiedCueLicensing",
                "scopeAcquisition", "sixNounAcquisition", "lexicalTransmission", "discourseBoundaryCue", "licensedInference")
    native = {name: _sha(path.read_bytes()) if (path := ROOT / "formal/.lake/build/bin" / name).is_file()
              else None for name in binaries}
    return {"code_sha": _code_sha(), "native_sha256": None, "native_binaries_sha256": native,
        "runner_sha256": _sha(Path(__file__).read_bytes()),
        "runtime_sha256": _sha((ROOT / "tools/licensed_workflow.py").read_bytes()),
        "registry_sha256": _sha((ROOT / "src/nabt/data/framework_foundation.json").read_bytes()),
        "toolchain": (ROOT / "formal/lean-toolchain").read_text().strip()}


def _testimony_identity():
    from tools.lexical_testimony import CATALOG
    binary = ROOT / "formal/.lake/build/bin/lexicalDenotation"
    return {"code_sha": _code_sha(),
            "native_sha256": _sha(binary.read_bytes()) if binary.is_file() else None,
            "runner_sha256": _sha(Path(__file__).read_bytes()),
            "runtime_sha256": _sha((ROOT / "tools/lexical_testimony.py").read_bytes()),
            "catalogue_sha256": _sha((ROOT / CATALOG).read_bytes()),
            "toolchain": (ROOT / "formal/lean-toolchain").read_text().strip()}


def _semantic_axes_identity(lexical_profile="teaching_v1"):
    # This route replays the Python discourse reader. A Lean binary installed
    # beside it is not evidence that Lean checked these benchmark claims.
    from tools.benchmark_semantic_axes import REFERENCE
    measured_sources = sorted((ROOT / "src/nabt").rglob("*.py")) + [
        ROOT / "tools/semantic_axes.py", ROOT / "tools/benchmark_semantic_axes.py",
        ROOT / "examples/discourse_training.tsv", REFERENCE.parent / "freeze.json"]
    source_manifest = {str(path.relative_to(ROOT)): _sha(path.read_bytes()) for path in measured_sources}
    if lexical_profile == "attested_qac_v1":
        from tools.attested_lexical_loader import DEFAULT_SOURCE, MATRIX_PATH
        for path in (DEFAULT_SOURCE, MATRIX_PATH, ROOT / "tools/attested_lexical_loader.py",
                     ROOT / "evidence/lexical_completion_v1/catalog.json"):
            source_manifest[str(path.relative_to(ROOT))] = _sha(path.read_bytes()) if path.is_file() else None
    return {"code_sha": _code_sha(), "native_sha256": None,
            "runner_sha256": _sha(Path(__file__).read_bytes()),
            "runtime_sha256": _sha((ROOT / "tools/semantic_axes.py").read_bytes()),
            "reference_sha256": _sha(REFERENCE.read_bytes()),
            "measurement_source_sha256": _sha(json.dumps(source_manifest, sort_keys=True).encode()),
            "toolchain": (ROOT / "formal/lean-toolchain").read_text().strip()}


def _epistemic_identity():
    """Bind the installed finite suite, acquisition records, and native checker.

    The manifest identifies bytes; it does not authenticate the outside agency
    or turn a supplied source interpretation into a fact about the world.
    """
    from tools.benchmark_epistemic_measurement import identity
    installed = identity()
    measured_sources = [ROOT / "tools/epistemic_measurement.py",
        ROOT / "tools/benchmark_epistemic_measurement.py",
        ROOT / "formal/Nabt/EpistemicMeasurement.lean",
        ROOT / "formal/EpistemicMeasurementMain.lean"]
    measured_sources += sorted((ROOT / "evidence/epistemic_measurement_v1").rglob("*.json"))
    manifest = {str(path.relative_to(ROOT)): _sha(path.read_bytes()) for path in measured_sources}
    return {**installed, "code_sha": _code_sha(),
            "runner_sha256": _sha(Path(__file__).read_bytes()),
            "runtime_sha256": _sha((ROOT / "tools/epistemic_measurement.py").read_bytes()),
            "measurement_source_sha256": _sha(json.dumps(manifest, sort_keys=True).encode()),
            "toolchain": (ROOT / "formal/lean-toolchain").read_text().strip()}


def _contextual_identity():
    from tools.benchmark_contextual_reference import identity
    installed = identity()
    measured_sources = [ROOT / "tools/contextual_reference.py",
        ROOT / "tools/benchmark_contextual_reference.py",
        ROOT / "formal/Nabt/ContextualReference.lean",
        ROOT / "formal/ContextualReferenceMain.lean"]
    measured_sources += sorted((ROOT / "evidence/contextual_semantics_v1").rglob("*.json"))
    manifest = {str(path.relative_to(ROOT)): _sha(path.read_bytes()) for path in measured_sources}
    return {**{key: value for key, value in installed.items() if key != "law_id"},
            "code_sha": _code_sha(), "runner_sha256": _sha(Path(__file__).read_bytes()),
            "measurement_source_sha256": _sha(json.dumps(manifest, sort_keys=True).encode()),
            "toolchain": (ROOT / "formal/lean-toolchain").read_text().strip()}


def _authority_guard(result):
    if (type(result) is not dict or any(type(result.get(key)) is not bool for key in BOOLEAN_FLAGS)
            or result.get("schema") != "nabt.licensed-inference-result.v1"
            or result.get("law_id") != SCOPE["law_id"]
            or result.get("accepted_language") != SCOPE["accepted_language"]
            or result.get("all_arabic_complete") is not False
            or result.get("world_truth_established") is not False
            or result.get("premise_world_truth_established") is not False
            or result.get("source_interpretation_historically_proved") is not False
            or type(result.get("status")) is not str or result["status"] not in RESULT_STATES):
        raise RuntimeError("AUTHORITY_CONTRACT_FAILURE")
    if result.get("verified") is True and not (
        result.get("native_checked") is True
        and result.get("closures_checked") is True
        and result.get("all_readings_complete") is True
        and result.get("authority") == "SOURCE_RELATIVE_CONSEQUENCE"
        and result["status"] in CHECKED_STATES
    ):
        raise RuntimeError("AUTHORITY_CONTRACT_FAILURE")
    if result["verified"] is False and (
        result["native_checked"] or result["closures_checked"] or result["all_readings_complete"]
        or result.get("authority") != "UNVERIFIED_PROPOSAL"
        or result["status"] in {"SUPPORTED", "REFUTED", "CONFLICT", "DEFER", "DISAGREEMENT"}
    ):
        raise RuntimeError("AUTHORITY_CONTRACT_FAILURE")


def _benchmark():
    from tools.benchmark_licensed_inference import run
    report = run()
    # Rows retain failed and unmeasured obligations. Raw results and large
    # environment snapshots are omitted only from this bounded transport.
    rows = [{key: row[key] for key in ("id", "family", "mode", "executed",
             "outcome", "checks", "observed") if key in row}
            for row in report["rows"]]
    return {
        "schema": report["schema"],
        "measured_at_utc": report["measured_at_utc"],
        "gold_sha256": report["gold_sha256"],
        "summary": report["summary"],
        "contract_gate": report["contract_gate"],
        "execution_integrity": report["execution_evidence"]["integrity"],
        "scope": report["scope"], "rows": rows,
    }


def _bind_transport(response):
    # This only binds a fresh fixed producer's output. It never imports proof
    # authority from caller-provided receipts or native flags.
    from nabt.transport_contract import _bind_metadata
    response.pop("transport_contract", None)
    paths = []
    if response.get("mode") == "licensed_workflow" and "gateway_result" in response:
        paths = [f"gateway_result.claims[{i}]"
                 for i in range(len(response["gateway_result"]["claims"]))]
    response["transport_contract"] = _bind_metadata(
        entrypoint="tools.proof_lab.run_payload", command=response.get("mode"),
        resolved_request={"request_id": response.get("request_id"),
                          "payload_sha256": response.get("payload_sha256")},
        result=response, policy_id="nabt.proof-lab." + (response.get("mode") or "invalid") + ".v1",
        authority="CHILD_DOMAIN_CONTRACT_RETAINED", input_binding="EXACT_PAYLOAD_DIGEST",
        claim_paths=paths,
        unresolved_premises=["TRANSPORT_BINDING_IS_NOT_KERNEL_PROOF",
                             "EACH_CHILD_RETAINS_ITS_DECLARED_AUTHORITY"])
    return response


def run_payload(request_id, payload, *, prepare=False):
    foundation.require_foundation('tools.proof_lab.run_payload')
    started = time.monotonic()
    response = {
        "schema": RESULT_SCHEMA, "request_id": None,
        "payload_sha256": None, "code_sha": None, "native_sha256": None,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "duration_ms": 0, "mode": None, "status": "INVALID_INPUT",
        "all_arabic_complete": False, "world_truth_established": False,
        "scope": dict(SCOPE),
    }
    try:
        response["request_id"] = validate_id(request_id)
        # Preserve the exact dispatch string in the digest; do not normalize.
        if type(payload) in (str, bytes):
            raw = payload.encode("utf-8", "strict") if type(payload) is str else payload
            response["payload_sha256"] = _sha(raw)
        request = validate_payload(payload)
        if request["mode"] == "inference":
            try:
                foundation.validate_source(request["source_text"])
                foundation.validate_source(request["query_text"])
            except ValueError as error:
                raise RequestError("MALFORMED_SOURCE_REPRESENTATION") from error
        response["mode"] = request["mode"]
        identity = {"licensed_workflow": _workflow_identity, "testimony": _testimony_identity,
                    "epistemic_measurement": _epistemic_identity,
                    "contextual_reference": _contextual_identity,
                    "semantic_axes": _semantic_axes_identity}.get(request["mode"], _identity)
        profile = request.get("lexical_profile", "teaching_v1")
        if request["mode"] == "semantic_axes" and profile != "teaching_v1":
            identity = lambda: _semantic_axes_identity(profile)
        before = identity()
        response.update(before)
        if request["mode"] == "testimony":
            response["scope"] = {"law_id": "nabt.lexical-denotation.v1",
                "claim": "Source-attributed conditional interpretation in the installed lexical catalogue",
                "whole_arabic": "NOT_PROVED", "external_world": "NOT_VERIFIED"}
        elif request["mode"] == "semantic_axes":
            response["scope"] = {"law_id": "nabt.semantic-axes.v1",
                "claim": "Reference comparison of the bounded discourse reader, separately by semantic axis",
                "verification_kind": "PYTHON_REPLAY",
                "whole_arabic": "NOT_PROVED", "external_world": "NOT_VERIFIED"}
            response["lexical_profile"] = profile
        elif request["mode"] == "epistemic_measurement":
            response["scope"] = {"law_id": "nabt.epistemic-measurement.v1",
                "claim": "Complete enumeration of licensed evidence in the supplied finite ledger",
                "verification_kind": "NATIVE_RECEIPT_CHECK",
                "whole_arabic": "NOT_PROVED", "external_world": "NOT_VERIFIED",
                "hidden_motive": "UNMEASURED", "free_arabic_acquisition": "UNMEASURED"}
        elif request["mode"] == "contextual_reference":
            response["scope"] = {"law_id": "nabt.initial-contextual-reference.v1",
                "claim": "Source-bound initial-occurrence reference relative to declared context",
                "verification_kind": "NATIVE_REFERENCE_RECEIPT_AND_PYTHON_GOLD_COMPARISON",
                "whole_clause": "NOT_PROVED", "whole_arabic": "NOT_PROVED",
                "external_world": "NOT_VERIFIED", "tawatur": "NOT_EVALUATED"}
        if request["mode"] == "licensed_workflow":
            response["scope"] = {"law_id": "nabt.licensed-workflow.v1",
                "claim": "Only exact named claims returned by registered native adapters",
                "whole_arabic": "NOT_PROVED", "external_world": "NOT_VERIFIED",
                "all_interfaces_migrated": False, "tawatur": "NOT_ESTABLISHED"}
        if prepare:
            response["status"] = "PREPARED"
        elif request["mode"] == "semantic_axes":
            from tools.benchmark_semantic_axes import run
            suite = run() if profile == "teaching_v1" else run(lexical_profile=profile)
            response.update(status="SEMANTIC_AXES_COMPLETE", semantic_axes=suite)
        elif request["mode"] == "licensed_workflow":
            from tools.licensed_workflow import run_request, migration_inventory
            gateway = run_request(request["workflow"])
            inventory = migration_inventory()
            response.update(status="LICENSED_WORKFLOW_COMPLETE", workflow_request=request["workflow"],
                workflow_request_sha256=_sha(_workflow_wire(request["workflow"]).encode("utf-8")),
                gateway_result=gateway, gateway_result_json=_workflow_wire(gateway),
                gateway_result_sha256=_sha(_workflow_wire(gateway).encode("utf-8")),
                adapter_result_json=_workflow_wire(gateway["result"]) if "result" in gateway else None,
                migration_inventory=inventory)
        elif response["native_sha256"] is None:
            response.update(status="VERIFICATION_UNAVAILABLE", error="NATIVE_CHECKER_MISSING")
        elif request["mode"] == "epistemic_measurement":
            from tools.benchmark_epistemic_measurement import run
            suite = run(require_native=True)
            if (any(suite.get(key) != response[key] for key in (
                        "native_sha256", "runtime_sha256", "reference_sha256", "source_registry_sha256"))
                    or suite.get("schema") != "nabt.epistemic-measurement-benchmark.v1"
                    or suite.get("law_id") != response["scope"]["law_id"]
                    or any(suite.get(key) is not False for key in (
                        "hidden_motive_measured", "free_arabic_acquisition_measured",
                        "whole_arabic_complete", "world_truth_established"))):
                raise RuntimeError("AUTHORITY_CONTRACT_FAILURE")
            response.update(status="EPISTEMIC_MEASUREMENT_COMPLETE", epistemic_measurement=suite)
        elif request["mode"] == "contextual_reference":
            from tools.benchmark_contextual_reference import run
            suite = run(require_native=True)
            if (any(suite.get(key) != response[key] for key in (
                        "native_sha256", "runtime_sha256", "original_reference_sha256",
                        "independent_reference_sha256", "source_registry_sha256", "scorer_sha256",
                        "baseline_source_sha256"))
                    or suite.get("schema") != "nabt.contextual-reference-benchmark.v1"
                    or suite.get("law_id") != response["scope"]["law_id"]
                    or suite.get("all_cases_native_checked") is not True
                    or any(suite.get(key) is not False for key in (
                        "whole_arabic_complete", "tawatur_evaluated",
                        "world_truth_established", "motive_measured"))):
                raise RuntimeError("AUTHORITY_CONTRACT_FAILURE")
            response.update(status="CONTEXTUAL_REFERENCE_COMPLETE", contextual_reference=suite)
        elif request["mode"] == "testimony":
            from tools.lexical_testimony import assess
            testimony = assess(request["entry"], request["target"])
            response.update(status=testimony["status"], testimony=testimony)
        elif request["mode"] == "inference":
            budget = InferenceBudget(max_source_bytes=MAX_SOURCE_BYTES,
                max_query_bytes=MAX_QUERY_BYTES, **(BUDGET_LIMITS | request.get("budget", {})))
            result = evaluate(request["source_text"], request["query_text"],
                source_id="proof-lab:" + request_id, revision=response["code_sha"],
                scope="proof-lab-single-discourse", time="unspecified", budget=budget)
            _authority_guard(result)
            response.update(status=result["status"], result=result)
        else:
            report = _benchmark()
            response.update(status="BENCHMARK_COMPLETE" if report["contract_gate"]["passed"]
                            else "BENCHMARK_CONTRACT_FAILURE", benchmark=report)
        if not prepare and identity() != before:
            raise RuntimeError("EXECUTION_IDENTITY_CHANGED")
    except (RequestError, UnicodeError) as exc:
        response.update(status="INVALID_INPUT", error=str(exc) if isinstance(exc, RequestError)
                        else "INVALID_UNICODE")
    except Exception:
        # Never copy exception strings: a library exception can contain text
        # from a private source, a path, or runtime credentials.
        response.update(status="EXECUTION_FAILED", error="INTERNAL_EXECUTION_FAILURE")
        response.pop("result", None)
        response.pop("benchmark", None)
        response.pop("testimony", None)
        response.pop("semantic_axes", None)
        response.pop("epistemic_measurement", None)
        response.pop("contextual_reference", None)
        for field in ("gateway_result", "gateway_result_json", "gateway_result_sha256", "adapter_result_json", "workflow_request", "workflow_request_sha256", "migration_inventory"):
            response.pop(field, None)
    response["duration_ms"] = round((time.monotonic() - started) * 1000)
    # Validate and bound the producer before copying canonical bytes. Private
    # malformed diagnostic values must fail closed, without echoing the child.
    try:
        for phase in range(2):
            encoded = json.dumps(response, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
            if len(encoded) >= MAX_RESULT_BYTES:
                for field in ("result", "benchmark", "testimony", "semantic_axes", "epistemic_measurement",
                              "contextual_reference", "gateway_result", "gateway_result_json", "gateway_result_sha256",
                              "adapter_result_json", "workflow_request", "workflow_request_sha256", "migration_inventory",
                              "transport_contract"):
                    response.pop(field, None)
                response.update(status="RESOURCE_EXHAUSTED", error="RESULT_BYTE_LIMIT")
            if phase == 0 or response.get("transport_contract") is None:
                _bind_transport(response)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        for field in ("result", "benchmark", "testimony", "semantic_axes", "epistemic_measurement",
                      "contextual_reference", "gateway_result", "gateway_result_json", "gateway_result_sha256",
                      "adapter_result_json", "workflow_request", "workflow_request_sha256", "migration_inventory",
                      "transport_contract"):
            response.pop(field, None)
        response.update(status="EXECUTION_FAILED", error="INTERNAL_EXECUTION_FAILURE")
        _bind_transport(response)
    return response


def _event_request(path, event_name):
    with path.open("rb") as stream:
        event = strict_json(stream.read(MAX_EVENT_BYTES + 1), MAX_EVENT_BYTES)
    if type(event) is not dict:
        raise RequestError("INVALID_EVENT")
    if event_name == "workflow_dispatch":
        inputs = event.get("inputs")
        if type(inputs) is not dict or set(inputs) != {"request_id", "payload"}:
            raise RequestError("INVALID_EVENT_INPUTS")
        request_id = validate_id(inputs["request_id"])
        key = transport_key(os.environ.get("NABT_LAB_TRANSPORT_KEY"))
        return request_id, decrypt_envelope(request_id, inputs["payload"], key), False
    if event_name in {"push", "pull_request"}:
        return SMOKE_ID, SMOKE_PAYLOAD, True
    raise RequestError("UNSUPPORTED_EVENT")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-file", type=Path)
    parser.add_argument("--request-file", type=Path)
    parser.add_argument("--request-id")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args(argv)
    smoke = False
    encrypted = args.event_file is not None and os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
    try:
        if args.event_file is not None and args.request_file is None and args.request_id is None:
            request_id, payload, smoke = _event_request(args.event_file, os.environ.get("GITHUB_EVENT_NAME"))
        elif args.request_file is not None and args.event_file is None and args.request_id is not None:
            with args.request_file.open("rb") as stream:
                payload = stream.read(MAX_PAYLOAD_BYTES + 1)
            request_id = args.request_id
        else:
            raise RequestError("ONE_INPUT_MODE_REQUIRED")
        result = run_payload(request_id, payload, prepare=args.prepare)
    except (OSError, RequestError, ImportError):
        if encrypted:
            # A failed envelope has no trusted private result to publish. No
            # plaintext fallback is written into a public repository artifact.
            print(json.dumps({"status": "ENCRYPTED_TRANSPORT_REJECTED"}))
            return 2
        result = run_payload(None, None, prepare=args.prepare)
        result["error"] = "INPUT_TRANSPORT_FAILURE"
        _bind_transport(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    if encrypted:
        key = transport_key(os.environ.get("NABT_LAB_TRANSPORT_KEY"))
        envelope = encrypt_envelope(request_id, serialized.encode("utf-8"), key)
        args.output.write_text(json.dumps(envelope, separators=(",", ":")) + "\n")
    else:
        args.output.write_text(serialized + "\n")
    if args.github_output is not None:
        valid = result["status"] == "PREPARED"
        artifact = "nabt-lab-smoke" if smoke else (
            "nabt-lab-" + result["request_id"] if result["request_id"] else "nabt-lab-rejected")
        # Both values are derived from validated UUIDs or fixed literals.
        with args.github_output.open("a") as stream:
            stream.write("valid=" + ("true" if valid else "false") + "\n")
            stream.write("artifact_name=" + artifact + "\n")
            stream.write("attested_source=" + ("true" if valid and (
                result.get("lexical_profile") == "attested_qac_v1" or
                result.get("mode") in {"contextual_reference", "licensed_workflow"}) else "false") + "\n")
    print(json.dumps({"request_id": result["request_id"],
        "status": ("ENCRYPTED_RESULT_WRITTEN" if encrypted else result["status"])}, ensure_ascii=False))
    if smoke and not args.prepare and not (result.get("result", {}).get("verified") is True
                                          and result["status"] == "SUPPORTED"):
        return 2
    return 2 if result["status"] in {"EXECUTION_FAILED", "VERIFICATION_UNAVAILABLE",
                                    "BENCHMARK_CONTRACT_FAILURE"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
