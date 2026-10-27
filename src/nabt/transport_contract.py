"""Versioned transport bindings; metadata is never linguistic proof authority.

Only fresh fixed producer paths select claim paths. Rechecking an imported
envelope establishes internal byte integrity, not provenance, native execution,
or permission to display an imported claim as a newly checked proof.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

from nabt import foundation

BINDING_SCHEMA = "nabt.transport-binding.v1"
ENVELOPE_SCHEMA = "nabt.transport-envelope.v1"
_MAX_BYTES = 64 * 1024 * 1024
_CLASSICAL_LAWS = {"nabt.classical-weak.v1", "nabt.classical-hamza.v1",
                   "nabt.classical-gemination.v1", "nabt.classical-boundary-affixes.v1"}
_CLAIM_POLICIES = {
    "classical": {"CLASSICAL_FINITE_CONTROL_EQUATION": _CLASSICAL_LAWS},
    "lexical": {"A116_EXACT_INSTALLED_CANDIDATE_SET": {"nabt.certified-lexical.v1"},
                "A116_CONDITIONAL_SUPPORTED_USE": {"nabt.certified-lexical.v1"}},
    "inference": {"SOURCE_BOUND_FINITE_INFERENCE": {"nabt.licensed-inference.v1"}},
}


def _claim_paths(result, policy, prefix=""):
    """Select named claims only immediately after a fixed fresh adapter call.

    This is not a receipt validator and is deliberately not a public API.
    The adapter must already have matched its full native postcondition.
    """
    claims = result.get("claims", [])
    if not claims:
        return []
    if result.get("native_checked") is not True or type(claims) is not list:
        raise ValueError("UNCHECKED_TRANSPORT_CLAIMS")
    allowed = _CLAIM_POLICIES[policy]
    for claim in claims:
        proof = claim.get("proof", {})
        if (proof.get("law_id") not in allowed.get(claim.get("kind"), set())
                or type(proof.get("theorems")) is not list or not proof["theorems"]
                or any(type(t) is not str or not t for t in proof["theorems"])):
            raise ValueError("UNLICENSED_TRANSPORT_CLAIM_KIND_OR_LAW")
    return [prefix + f"claims[{i}]" for i in range(len(claims))]


def _canonical(value):
    text = json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)
    raw = text.encode("utf-8", "strict")
    if len(raw) > _MAX_BYTES:
        raise ValueError("TRANSPORT_BINDING_RESOURCE_LIMIT")
    return text, raw


def _json_value(value):
    if type(value) is bytes:
        return {"encoding": "exact-bytes-hex", "hex": value.hex(),
                "bytes": len(value), "sha256": sha256(value).hexdigest()}
    if isinstance(value, Path):
        return {"path_argument": str(value), "file_bytes_bound": False}
    if type(value) in (str, int, bool, float) or value is None:
        return value
    if type(value) in (list, tuple):
        return [_json_value(item) for item in value]
    if type(value) is dict and all(type(key) is str for key in value):
        return {key: _json_value(item) for key, item in value.items()}
    raise ValueError("TRANSPORT_REQUEST_REQUIRES_EXPLICIT_JSON_OR_BYTES")


def _resolve(value, path):
    if type(path) is not str or not re.fullmatch(
            r"[A-Za-z_][A-Za-z_0-9]*(?:\[(?:0|[1-9][0-9]*)\]|\.[A-Za-z_][A-Za-z_0-9]*)*", path):
        raise ValueError("NONCANONICAL_TRANSPORT_CLAIM_PATH")
    for token in re.findall(r"[A-Za-z_][A-Za-z_0-9]*|\[(?:0|[1-9][0-9]*)\]", path):
        if token.startswith("["):
            if type(value) is not list:
                raise ValueError("TRANSPORT_CLAIM_PATH_REQUIRES_ARRAY")
            value = value[int(token[1:-1])]
        else:
            if type(value) is not dict:
                raise ValueError("TRANSPORT_CLAIM_PATH_REQUIRES_OBJECT")
            value = value[token]
    return value


def _bind_metadata(*, entrypoint, command, resolved_request, result, policy_id,
                   authority, input_binding="RESOLVED_CHILD_INPUT", claim_paths=(),
                   unresolved_premises=()):
    """Internal producer helper; no receipt-import or execution authority.

    The caller must have just run its fixed child and selected paths using its
    own scoped contract. This helper binds bytes and checks path integrity only.
    """
    request = _json_value(resolved_request)
    request_canonical, request_raw = _canonical(request)
    response_canonical, response_raw = _canonical(result)
    if len(claim_paths) != len(set(claim_paths)):
        raise ValueError("DUPLICATE_TRANSPORT_CLAIM_PATH")
    claims = []
    for path in claim_paths:
        claim = _resolve(result, path)
        if (type(claim) is not dict or type(claim.get("kind")) is not str
                or not claim["kind"] or type(claim.get("scope")) is not str or not claim["scope"]
                or type(claim.get("proof")) is not dict
                or type(claim["proof"].get("law_id")) is not str
                or not claim["proof"]["law_id"]
                or type(claim["proof"].get("theorems")) is not list
                or not claim["proof"]["theorems"]):
            raise ValueError("TRANSPORT_PATH_IS_NOT_A_NAMED_SCOPED_CLAIM")
        claim_canonical, raw = _canonical(claim)
        claims.append({"child_path": path, "claim_sha256": sha256(raw).hexdigest(),
                       "claim_canonical": claim_canonical,
                       "kind": claim["kind"], "law_id": claim["proof"]["law_id"]})
    return {"schema": BINDING_SCHEMA, "entrypoint": entrypoint, "command": command,
        "policy_id": policy_id, "authority": authority, "input_binding": input_binding,
        "request": request, "request_canonical": request_canonical,
        "request_sha256": sha256(request_raw).hexdigest(),
        "child_response_canonical": response_canonical,
        "child_response_sha256": sha256(response_raw).hexdigest(),
        "child_response_bytes": len(response_raw), "named_claims": claims,
        "unresolved_premises": list(unresolved_premises),
        "transport_binding_kernel_proved": False, "grants_language_license": False,
        "all_arabic_complete": False}


def _envelope(**kwargs):
    result = kwargs["result"]
    return {"schema": ENVELOPE_SCHEMA,
            "transport_contract": _bind_metadata(**kwargs), "response": deepcopy(result)}


def validate_transport_envelope(envelope):
    """Check imported byte integrity only; never grant imported proof authority."""
    foundation.require_foundation("nabt.transport_contract.validate_transport_envelope")
    report = {"schema": "nabt.transport-envelope-integrity.v1", "integrity_valid": False,
              "proof_authority_established": False, "fresh_execution_required": True,
              "grants_language_license": False, "all_arabic_complete": False}
    try:
        if type(envelope) is not dict or set(envelope) != {"schema", "transport_contract", "response"}:
            raise ValueError("EXACT_TRANSPORT_ENVELOPE_FIELDS_REQUIRED")
        if envelope["schema"] != ENVELOPE_SCHEMA:
            raise ValueError("UNSUPPORTED_TRANSPORT_ENVELOPE_SCHEMA")
        binding = envelope["transport_contract"]
        if type(binding) is not dict or binding.get("schema") != BINDING_SCHEMA:
            raise ValueError("UNSUPPORTED_TRANSPORT_BINDING")
        expected = _bind_metadata(entrypoint=binding["entrypoint"], command=binding["command"],
            resolved_request=binding["request"], result=envelope["response"],
            policy_id=binding["policy_id"], authority=binding["authority"],
            input_binding=binding["input_binding"],
            claim_paths=[row["child_path"] for row in binding["named_claims"]],
            unresolved_premises=binding["unresolved_premises"])
        if _canonical(expected) != _canonical(binding):
            raise ValueError("TRANSPORT_BINDING_MISMATCH")
        report["integrity_valid"] = True
    except (ValueError, TypeError, KeyError, IndexError, RecursionError, UnicodeError) as error:
        report["reason"] = str(error)
    return report
