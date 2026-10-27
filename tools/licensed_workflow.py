"""One raw-request admission path with claim-specific, native authority.

This gateway never accepts a checker, imported result, receipt, or proof flag.
It invokes fixed repository-owned adapters and forwards only their named,
scoped claims.  A native deferral is not language acceptance.  The migration
inventory describes every registered surface; registration is not proof.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from importlib.resources import files
import json

from nabt import foundation
from nabt.errors import NabtError

REQUEST_SCHEMA = "nabt.licensed-workflow-request.v1"
RESPONSE_SCHEMA = "nabt.licensed-workflow-response.v1"
MAX_REQUEST_BYTES = 131_072
_BUDGET_LIMITS = {"max_input_bytes": 65536, "max_occurrences": 256,
                  "max_readings": 2048, "max_native_scan": 4096}


class _AdapterContractError(ValueError):
    pass

_OPERATIONS = {
    "lexical_surface": {
        "surface": "tools.linguistic_truth.surface.certify_surface",
        "required": {"text"},
        "optional": {"start_byte", "end_byte", "source_id", "context", "referent", "time"},
        "schema": "nabt.witnessed-surface-receipt.v2",
        "authority": "EXACT_DOCUMENTARY_FORM_AND_SOURCE_FIELDS"},
    "lexical_candidates": {
        "surface": "tools.linguistic_truth.certified.acquire_certified",
        "required": {"text"},
        "optional": {"profile_id", "budget", "source_id", "subject", "time", "context"},
        "schema": "nabt.certified-linguistic-acquisition.v1",
        "authority": "A116_CONDITIONAL_CANDIDATE_CONTRACT"},
    "classical_control": {
        "surface": "nabt.classical_certified.evaluate_certified",
        "required": {"rule_id", "frame"}, "optional": set(),
        "schema": "nabt.classical-certified-control.v1",
        "authority": "SUPPLIED_FRAME_NATIVE_CONTROL_EQUATION"},
    "scope_acquisition": {
        "surface": "tools.linguistic_truth.scopes.acquire_scope",
        "required": {"text"}, "optional": {"source_id", "context", "profile_id"},
        "schema": "nabt.scope-acquisition-receipt.v1",
        "authority": "EXACT_BOUNDED_SCOPE_ENVELOPE"},
    "lexical_transmission": {
        "surface": "tools.lexical_transmission.assess_transmission",
        "required": {"entry"}, "optional": {"context"},
        "schema": "nabt.lexical-transmission-receipt.v1",
        "authority": "DOCUMENTARY_SOURCE_DEPENDENCY_CLASSIFICATION"},
}

_CLAIM_LAWS = {
    "lexical_surface": {"EXACT_WITNESSED_FORM_WITH_DECLARED_ANNOTATION":
                        {"nabt.lexical-surface-binding.v1"}},
    "lexical_candidates": {
        "A116_EXACT_INSTALLED_CANDIDATE_SET": {"nabt.certified-lexical.v1"},
        "A116_CONDITIONAL_SUPPORTED_USE": {"nabt.certified-lexical.v1"}},
    "classical_control": {"CLASSICAL_FINITE_CONTROL_EQUATION": {
        "nabt.classical-weak.v1", "nabt.classical-hamza.v1", "nabt.classical-gemination.v1",
        "nabt.classical-boundary-affixes.v1"}},
    "scope_acquisition": {"EXACT_SCOPE_ENVELOPE": {"nabt.scope-acquisition.v1"}},
    "lexical_transmission": {"SOURCE_BOUND_REPORT_INVENTORY_AND_DEPENDENCY_CLASSIFICATION":
                             {"nabt.lexical-transmission.v1"}},
}


def _wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(value):
    return sha256(_wire(value)).hexdigest()


def _registry():
    raw = files("nabt").joinpath("data/framework_foundation.json").read_bytes()
    registry = json.loads(raw)
    if (registry.get("schema") != "nabt.framework-foundation.v1"
            or registry.get("foundation_law_id") != foundation.LAW_ID
            or type(registry.get("surfaces")) is not list):
        raise ValueError("INSTALLED_INTERFACE_REGISTRY_INVALID")
    ids = [row["id"] for row in registry["surfaces"]]
    if len(ids) != len(set(ids)):
        raise ValueError("INSTALLED_INTERFACE_REGISTRY_DUPLICATES")
    return registry, sha256(raw).hexdigest()


def migration_inventory():
    """List all installed interfaces and their remaining handover obligations.

    A known native adapter is migrated only for its explicitly stated claim.
    The remainder retain their existing diagnostic/conditional contracts.
    No function's name or ``kind=checked`` grants language-proof authority.
    """
    foundation.require_foundation("tools.licensed_workflow.migration_inventory")
    registry, digest = _registry()
    native = {row["surface"]: (op, row) for op, row in _OPERATIONS.items()}
    rows = []
    for surface in registry["surfaces"]:
        identity, kind = surface["id"], surface["kind"]
        operation = native.get(identity)
        if operation:
            state, authority = "SCOPED_GATEWAY_INSTALLED", operation[1]["authority"]
            pending = ["CLAIM_SPECIFIC_PREMISES_REMAIN_EXPLICIT",
                       "NO_GENERAL_LANGUAGE_ACCEPTANCE"]
        elif (kind == "encoding" or surface["layer"] in {"core", "shape_certificate"}
              or surface["guard_kind"] == "checked_snapshot_primitive"):
            state, authority = "RETAIN_TYPED_PRIMITIVE", "REPRESENTATION_OR_FIXED_MACHINE_DOMAIN"
            pending = ["LAYER_HANDOVER_REQUIRES_NEW_EVIDENCE"]
        elif kind in {"proposal", "retrieval", "diagnostic", "measurement"}:
            state, authority = "RETAIN_NON_AUTHORITATIVE", kind.upper() + "_ONLY"
            pending = ["OUTPUT_CANNOT_LICENSE_A_LINGUISTIC_CLAIM"]
        elif kind == "transport":
            state, authority = "CHILD_CONTRACT_REVIEW_REQUIRED", "TRANSPORT_ONLY"
            pending = ["EXACT_CHILD_REQUEST_AND_RESPONSE_BINDING",
                       "DISPLAY_ONLY_CHECKED_NAMED_CLAIMS"]
        else:
            state, authority = "ACQUISITION_AND_REFINEMENT_REVIEW_REQUIRED", "EXISTING_BOUNDED_DOMAIN_CONTRACT"
            pending = ["RAW_SOURCE_TO_PREMISE_ACQUISITION",
                       "NATIVE_REQUEST_RESPONSE_REFINEMENT",
                       "EXACT_CLAIM_AND_UNRESOLVED_PREMISES",
                       "INDEPENDENT_POSITIVE_AND_COUNTEREXAMPLE_CONTROLS"]
        rows.append({"surface_id": identity, "path": surface["path"],
            "entrypoint": surface["entrypoint"], "kind": kind,
            "guard_kind": surface["guard_kind"], "identifier_domain": surface["identifier_domain"],
            "migration_state": state, "authority_limit": authority,
            "gateway_operation": operation[0] if operation else None,
            "runtime_availability": "NOT_MEASURED_BY_INVENTORY",
            "pending_obligations": pending, "whole_language_claim": False})
    counts = {state: sum(row["migration_state"] == state for row in rows)
              for state in sorted({row["migration_state"] for row in rows})}
    return {"schema": "nabt.interface-migration-inventory.v1", "registry_sha256": digest,
        "foundation_law_id": foundation.LAW_ID, "surface_count": len(rows), "states": counts,
        "surfaces": rows, "all_interfaces_migrated": False,
        "whole_arabic_complete": False,
        "scope": "Installed admission inventory and explicit migration obligations, not a proof of every result or language coverage."}


def _execute(operation, arguments):
    # Imports and call targets are fixed in code, never selected by the caller.
    if operation == "lexical_surface":
        from tools.linguistic_truth.surface import certify_surface
        return certify_surface(**arguments)
    if operation == "lexical_candidates":
        from tools.linguistic_truth.certified import acquire_certified
        if arguments.get("budget") is not None:
            from tools.linguistic_truth.runtime import AcquisitionBudget
            arguments = {**arguments, "budget": AcquisitionBudget(**arguments["budget"])}
        return acquire_certified(**arguments)
    if operation == "classical_control":
        from nabt.classical_certified import evaluate_certified
        return evaluate_certified(**arguments)
    if operation == "scope_acquisition":
        from tools.linguistic_truth.scopes import acquire_scope
        return acquire_scope(**arguments)
    if operation == "lexical_transmission":
        from tools.lexical_transmission import assess_transmission
        return assess_transmission(**arguments)
    raise ValueError("UNKNOWN_WORKFLOW_OPERATION")


def _valid_proof(claim):
    if type(claim) is not dict or type(claim.get("kind")) is not str:
        return False
    proof = claim.get("proof")
    return (type(proof) is dict and type(proof.get("law_id")) is str
        and bool(proof["law_id"]) and type(proof.get("theorems")) is list
        and bool(proof["theorems"])
        and all(type(name) is str and name.startswith("Nabt.") for name in proof["theorems"])
        and type(claim.get("scope")) is str and bool(claim["scope"]))


def _claims(operation, result):
    """Defensive shape validation after trusted execution, not receipt import.

    The adapter has already compared its full native postcondition. These
    checks prevent transport promotion and retain an independently successful
    source-extraction claim if the later exact-form check is unavailable.
    """
    claims = result.get("claims", [])
    if type(claims) is not list or any(not _valid_proof(claim) for claim in claims):
        raise _AdapterContractError("INVALID_SCOPED_CLAIM_CONTRACT")
    for claim in claims:
        allowed_laws = _CLAIM_LAWS[operation].get(claim["kind"], set())
        if claim["proof"]["law_id"] not in allowed_laws:
            raise _AdapterContractError("UNREGISTERED_CLAIM_OR_LAW_FOR_OPERATION")
    if claims and result.get("native_checked") is not True:
        raise _AdapterContractError("CLAIM_WITHOUT_NATIVE_EXECUTION")
    output = [{**deepcopy(claim), "origin_path": f"claims[{index}]"}
              for index, claim in enumerate(claims)]
    acquisition = result.get("source_acquisition") if operation == "lexical_surface" else None
    if acquisition is not None:
        if (type(acquisition) is not dict
                or result.get("source_row_extraction_kernel_proved") is not True
                or result.get("annotation_field_extraction_kernel_proved") is not True):
            raise _AdapterContractError("INVALID_SOURCE_ACQUISITION_CONTRACT")
        claim = {"kind": "EXACT_SOURCE_ROW_AND_ANNOTATION_FIELD_EXTRACTION",
                 **deepcopy(acquisition), "origin_path": "source_acquisition",
                 "unresolved_premises": ["SOURCE_AUTHENTICITY_NOT_PROVED",
                                          "ANNOTATION_INTERPRETATION_NOT_PROVED"]}
        if not _valid_proof(claim):
            raise _AdapterContractError("INVALID_SOURCE_ACQUISITION_PROOF")
        if claim["proof"]["law_id"] != "nabt.lexical-source-acquisition.v1":
            raise _AdapterContractError("UNREGISTERED_SOURCE_ACQUISITION_LAW")
        output.insert(0, claim)
    return output


def run_request(request):
    """Execute only installed raw-request adapters; never import authority.

    Unknown/legacy operations are deferred with a migration obligation. A
    caller cannot pass a receipt, callback, manifest, proof status, or checker.
    The entire underlying result remains available with its original status;
    only the separate ``claims`` list is eligible for a proof label.
    """
    foundation.require_foundation("tools.licensed_workflow.run_request")
    response = {"schema": RESPONSE_SCHEMA, "status": "INVALID_INPUT",
        "workflow_status": "NO_SCOPED_CLAIMS", "operation": None, "claims": [],
        "native_checked": False, "strict_language_accepted": False,
        "whole_arabic_complete": False, "tawatur_established": False,
        "world_truth_established": False,
        "display_contract": {"proof_source": "claims[*].proof",
            "native_checked_is_not_blanket_proof": True}}
    execution_started = False
    try:
        if type(request) is not dict or set(request) != {"schema", "op", "input"}:
            raise ValueError("EXACT_WORKFLOW_REQUEST_FIELDS_REQUIRED")
        if request["schema"] != REQUEST_SCHEMA or type(request["op"]) is not str:
            raise ValueError("INVALID_WORKFLOW_REQUEST_IDENTITY")
        if len(_wire(request)) > MAX_REQUEST_BYTES:
            response.update(status="RESOURCE_EXHAUSTED", reason="WORKFLOW_REQUEST_LIMIT")
            return response
        response["request_sha256"] = _digest(request)
        operation, arguments = request["op"], request["input"]
        response["operation"] = operation
        if operation not in _OPERATIONS:
            response.update(status="DEFER", reason="UNMIGRATED_OR_UNKNOWN_OPERATION",
                residuals=["USE_AN_INSTALLED_SCOPED_ADAPTER_OR_COMPLETE_ITS_MIGRATION"])
            return response
        definition = _OPERATIONS[operation]
        if (type(arguments) is not dict
                or not definition["required"] <= set(arguments)
                or set(arguments) - definition["required"] - definition["optional"]):
            raise ValueError("UNDECLARED_OR_MISSING_ADAPTER_ARGUMENT")
        for key, value in arguments.items():
            if key in {"start_byte", "end_byte"}:
                if value is not None and (type(value) is not int or value < 0):
                    raise ValueError("EXACT_NONNEGATIVE_INTEGER_REQUIRED")
            elif key == "budget":
                if value is not None and (type(value) is not dict or set(value) - set(_BUDGET_LIMITS)
                        or any(type(limit) is not int or not 0 <= limit <= _BUDGET_LIMITS[field]
                               for field, limit in value.items())):
                    raise ValueError("BOUNDED_ACQUISITION_BUDGET_OBJECT_REQUIRED")
            elif key == "frame":
                if type(value) is not dict:
                    raise ValueError("EXACT_FRAME_OBJECT_REQUIRED")
            elif value is None and key == "profile_id":
                continue
            elif type(value) is not str:
                raise ValueError("EXACT_TEXT_ARGUMENT_REQUIRED")
        registry, registry_digest = _registry()
        if definition["surface"] not in {row["id"] for row in registry["surfaces"]}:
            response.update(status="VERIFICATION_UNAVAILABLE", reason="ADAPTER_NOT_REGISTERED")
            return response
        execution_started = True
        if operation == "lexical_candidates":
            response["effective_budget"] = {**_BUDGET_LIMITS, **(arguments.get("budget") or {})}
        result = _execute(operation, deepcopy(arguments))
        if (type(result) is not dict or result.get("schema") != definition["schema"]
                or type(result.get("status")) is not str
                or type(result.get("native_checked")) is not bool
                or result.get("strict_language_accepted") is not False):
            raise _AdapterContractError("ADAPTER_RESULT_CONTRACT_MISMATCH")
        for field in ("all_arabic_complete", "whole_arabic_complete", "tawatur_established",
                      "world_truth_established", "intended_sense_established"):
            if field in result and result[field] is not False:
                raise _AdapterContractError("UNLICENSED_ADAPTER_AUTHORITY_PROMOTION")
        claims = _claims(operation, result)
        response.update(status=result["status"], native_checked=result["native_checked"],
            workflow_status="SCOPED_CLAIMS_AVAILABLE" if claims else "NO_SCOPED_CLAIMS",
            surface_id=definition["surface"], authority_limit=definition["authority"],
            registry_sha256=registry_digest, result_sha256=_digest(result),
            claims=claims, result=result)
    except _AdapterContractError as exc:
        response.update(status="VERIFICATION_UNAVAILABLE", reason=str(exc))
    except NabtError as exc:
        response.update(status="RESOURCE_EXHAUSTED" if exc.code == "RESOURCE_LIMIT" else
                        "VERIFICATION_UNAVAILABLE" if exc.status == "DEFER" else "INVALID_INPUT",
                        reason=exc.code)
    except (OSError, ImportError) as exc:
        response.update(status="VERIFICATION_UNAVAILABLE", reason="INSTALLED_ADAPTER_UNAVAILABLE",
                        error_type=type(exc).__name__)
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError) as exc:
        response.update(status="VERIFICATION_UNAVAILABLE" if execution_started else "INVALID_INPUT",
                        reason=str(exc) if isinstance(exc, ValueError)
                        else "MALFORMED_WORKFLOW_OR_ADAPTER_RESULT")
    return response
