"""Typed, conditional reasoning over explicit assumptions, never free-text truth.

An installed source policy determines the required evidence roles. Callers must
also supply a bridge implication; satisfying a guard never creates that bridge.
Successful consequences are replayed by the existing native Lean checker over
an explicitly generated assumption transcript. The original Arabic occurrence
is retained, but this adapter does not prove its interpretation.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from tools import mantuq_mafhum, verified_reading
from .inventory import build_inventory
from nabt.errors import NabtError

ROOT = Path(__file__).resolve().parents[2]
REQUEST_SCHEMA = "nabt.mantuq-inference-request.v1"
RESULT_SCHEMA = "nabt.mantuq-inference-result.v1"
LAW_ID = "nabt.qualified-inference-adapter.v1"

SLOTS = {
    "matching": ("premise",),
    "inclusion": ("premise", "transferBridge"),
    "requirement": ("premise", "transferBridge"),
    "alert": ("premise", "transferBridge"),
    "allusion": ("premise", "transferBridge"),
    "agreement": ("premise", "transferBridge"),
    "opposition": ("premise", "necessaryBridge", "qualified", "countertextAbsence", "usualCaseAbsence"),
    "guarded_cause": ("cause", "condition", "blockerAbsence"),
    "analogy": ("originRuling", "sharedCause", "transferBridge", "condition", "blockerAbsence"),
}
ROLES = {
    "premise": "premise", "cause": "cause", "condition": "condition",
    "blockerAbsence": "blocker_absence", "necessaryBridge": "necessary_bridge",
    "originRuling": "origin_ruling", "sharedCause": "shared_cause",
    "transferBridge": "transfer_bridge", "qualified": "condition",
    "countertextAbsence": "blocker_absence", "usualCaseAbsence": "blocker_absence",
}
KINDS = {"guarded_cause": "causal", "opposition": "opposition", "analogy": "analogy"}


import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from nabt import foundation

class InvalidRequest(ValueError):
    pass


@dataclass(frozen=True)
class EvaluationBudget:
    max_readings: int = 64
    max_hypotheses: int = 128
    max_total_atoms: int = 2048

    def __post_init__(self):
        for key, value in vars(self).items():
            if type(value) is not int or not 0 <= value <= 100000:
                raise ValueError(f"{key} must be a bounded natural, not a boolean")


def _wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value):
    return hashlib.sha256(_wire(value).encode()).hexdigest()


def _object(value, fields, name, optional=()):
    if type(value) is not dict or set(value) - set(fields) - set(optional) or not set(fields) <= set(value):
        raise InvalidRequest(f"{name}: unexpected or missing fields")
    return value


def _text(value, name, maximum=512):
    if type(value) is not str or not value.strip() or len(value) > maximum:
        raise InvalidRequest(f"{name}: nonempty bounded text required")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise InvalidRequest(f"{name}: valid UTF-8 text required") from exc
    return value


def _atom(value):
    _object(value, ("predicate", "arguments", "positive"), "atom")
    _text(value["predicate"], "predicate", 128)
    if type(value["positive"]) is not bool:
        raise InvalidRequest("atom polarity must be boolean")
    if type(value["arguments"]) is not list or len(value["arguments"]) > 8:
        raise InvalidRequest("atom arguments must be a list of at most eight names")
    for arg in value["arguments"]:
        _text(arg, "argument", 128)
    return dict(value, arguments=list(value["arguments"]))


def _key(atom):
    return atom["predicate"], tuple(atom["arguments"]), atom["positive"]


def _opposite(atom):
    return dict(atom, positive=not atom["positive"])


def _guard_atom_valid(atom):
    """Admit only the runtime atom or the exporter's inert Nat/scoped atom."""
    if type(atom) is not dict:
        return False
    if set(atom) == {"value", "positive", "scope"}:
        if (type(atom["value"]) is not int or atom["value"] < 0
                or type(atom["positive"]) is not bool or type(atom["scope"]) is not str):
            return False
        try:
            atom["scope"].encode("utf-8")
        except UnicodeError:
            return False
        return True
    try:
        _atom(atom)
    except (ValueError, TypeError):
        return False
    return True


def guard_verdict(kind, requirements, known):
    """Finite adapter of QualifiedInference.assess; inputs are inert JSON values.

    Scope may be present on atoms for conformance. Atom identity includes every
    supplied field, so scope changes cannot count as the same obligation.
    """
    allowed = set(ROLES.values())
    if (type(kind) is not str or kind not in {"direct", "causal", "opposition", "analogy"}
            or type(requirements) is not list or not requirements or type(known) is not list
            or any(type(r) is not dict or set(r) - {"role", "atom", "slot"}
                   or not {"role", "atom"} <= set(r) or type(r["role"]) is not str
                   or not _guard_atom_valid(r["atom"]) for r in requirements)
            or any(not _guard_atom_valid(a) for a in known)):
        return "INVALID_PROFILE"
    roles = [r["role"] for r in requirements]
    if any(r not in allowed for r in roles):
        return "INVALID_PROFILE"
    required = {"direct": (), "causal": ("cause",), "opposition": ("necessary_bridge",),
                "analogy": ("origin_ruling", "shared_cause", "transfer_bridge")}[kind]
    if any(role not in roles for role in required):
        return "INVALID_PROFILE"
    if any(r["role"] == "blocker_absence" and r["atom"]["positive"] for r in requirements):
        return "INVALID_PROFILE"
    present = {_wire(a) for a in known}
    states = [(_wire(r["atom"]) in present, _wire(_opposite(r["atom"])) in present) for r in requirements]
    if any(yes and no for yes, no in states):
        return "CONFLICT"
    if any(no for _, no in states):
        return "REFUTED_PREMISE"
    if any(not yes for yes, _ in states):
        return "UNKNOWN_PREMISE"
    return "SUPPORTED_PREMISES"


def opposition_shape(antecedent, consequent, absent, conclusion):
    """Structural Q -> P, not P, therefore not Q; relation truth is assumed."""
    return (all(_guard_atom_valid(a) for a in (antecedent, consequent, absent, conclusion))
            and antecedent.get("positive") is True and consequent.get("positive") is True
            and antecedent.get("scope") == consequent.get("scope")
            and _wire(absent) == _wire(_opposite(consequent))
            and _wire(conclusion) == _wire(_opposite(antecedent)))


def _base():
    return {"schema": RESULT_SCHEMA, "law_id": LAW_ID,
            "authority": "CONDITIONAL_ASSUMPTIONS_ONLY",
            "all_arabic_complete": False, "world_truth_established": False,
            "source_to_requirements_proved": False, "occurrence_classification_proved": False,
            "semantic_bridge_proved": False, "reading_enumeration_proved": False,
            "empirical_validation_established": False, "readings": [],
            "conditional_consequence": False, "declared_request_scan_complete": False,
            "inventory_scope": "supplied readings for one selected policy",
            "conditional_evaluation_complete": False}


def _validate(payload, budget):
    _object(payload, ("schema", "policy_id", "binding", "conclusion", "readings"), "request", ("contrast_kind",))
    if payload["schema"] != REQUEST_SCHEMA or payload["policy_id"] not in SLOTS:
        raise InvalidRequest("unknown schema or installed policy")
    binding = _object(payload["binding"], ("source_id", "source_text", "scope", "context", "time"), "binding")
    for key, val in binding.items():
        _text(val, key, 65536 if key == "source_text" else 4096 if key == "context" else 512)
    conclusion = _atom(payload["conclusion"])
    policy = payload["policy_id"]
    if policy == "opposition":
        if payload.get("contrast_kind") not in {"attribute", "condition", "endpoint", "number", "name", "innama"}:
            raise InvalidRequest("opposition requires an explicit installed contrast_kind")
    elif "contrast_kind" in payload:
        raise InvalidRequest("contrast_kind belongs only to opposition")
    readings = payload["readings"]
    if type(readings) is not list or not readings:
        raise InvalidRequest("one or more explicit readings are required")
    if len(readings) > budget.max_readings:
        return None, "max_readings"
    seen, total, fresh = set(), 0, []
    for reading in readings:
        _object(reading, ("reading_id", "requirements", "hypotheses", "bridge"), "reading", ("necessary_relation",))
        rid = _text(reading["reading_id"], "reading_id")
        if rid in seen:
            raise InvalidRequest("duplicate reading identity")
        seen.add(rid)
        requirements = reading["requirements"]
        if type(requirements) is not list or not requirements or len(requirements) > 16:
            raise InvalidRequest("one to sixteen requirements are required")
        slots, atoms, clean = set(), set(), []
        for req in requirements:
            _object(req, ("slot", "atom"), "requirement")
            slot = _text(req["slot"], "slot", 128)
            role_key = slot.split(":", 1)[0]
            extra = ":" in slot and role_key in {"condition", "blockerAbsence"} and bool(slot.split(":", 1)[1])
            if slot not in SLOTS[policy] and not extra:
                raise InvalidRequest("requirement slot is not installed for this policy")
            if slot in slots:
                raise InvalidRequest("duplicate slot")
            slots.add(slot)
            atom = _atom(req["atom"])
            unsigned = _key(atom)[:2]
            if unsigned in atoms:
                raise InvalidRequest("distinct obligations cannot alias the same unsigned atom")
            atoms.add(unsigned)
            role = ROLES[role_key]
            if role == "blocker_absence" and atom["positive"]:
                raise InvalidRequest("blocker absence requires an explicitly negative atom")
            if slot == "qualified" and not atom["positive"]:
                raise InvalidRequest("qualified guard requires positive support")
            clean.append({"slot": slot, "role": role, "atom": atom})
        if not set(SLOTS[policy]) <= slots:
            raise InvalidRequest("missing declared policy slot; missing evidence belongs in hypotheses")
        hypotheses = reading["hypotheses"]
        if hypotheses is not None:
            if type(hypotheses) is not list:
                raise InvalidRequest("hypotheses must be a list or null for an incomplete reading")
            if len(hypotheses) > budget.max_hypotheses:
                return None, "max_hypotheses"
            hypotheses = [_atom(a) for a in hypotheses]
            if len({_key(a) for a in hypotheses}) != len(hypotheses):
                raise InvalidRequest("duplicate signed hypothesis")
        total += len(clean) + len(hypotheses or []) + 1
        if total > budget.max_total_atoms:
            return None, "max_total_atoms"
        bridge = reading["bridge"]
        if bridge is not None:
            _object(bridge, ("body", "head", "basis"), "bridge")
            if (bridge["basis"] != "caller_assumption" or type(bridge["body"]) is not list
                    or len(bridge["body"]) != len(clean)):
                raise InvalidRequest("bridge must explicitly declare caller_assumption")
            body = [_atom(a) for a in bridge["body"]]
            head = _atom(bridge["head"])
            if body != [r["atom"] for r in clean] or head != conclusion:
                raise InvalidRequest("bridge body/head differs from exact requirements/conclusion")
            bridge = {"body": body, "head": head, "basis": "caller_assumption"}
        relation = reading.get("necessary_relation")
        if policy != "opposition" and "necessary_relation" in reading:
            raise InvalidRequest("necessary_relation belongs only to opposition")
        if relation is not None:
            _object(relation, ("kind", "antecedent", "consequent", "basis"), "necessary_relation")
            antecedent, consequent = _atom(relation["antecedent"]), _atom(relation["consequent"])
            premise = next(r["atom"] for r in clean if r["slot"] == "premise")
            if (relation["kind"] != "necessary" or relation["basis"] != "caller_assumption"
                    or not opposition_shape(antecedent, consequent, premise, conclusion)):
                raise InvalidRequest("necessary relation must be Q -> P with explicit not P and target not Q")
            relation = {"kind": "necessary", "antecedent": antecedent, "consequent": consequent,
                        "basis": "caller_assumption"}
        fresh.append({"reading_id": rid, "requirements": clean, "hypotheses": hypotheses,
                      "bridge": bridge, "necessary_relation": relation})
    return {"policy_id": policy, "binding": dict(binding), "conclusion": conclusion,
            "readings": fresh, "contrast_kind": payload.get("contrast_kind")}, None


def _native_consequence(reading, binding, conclusion):
    # Whole unsigned atom identity is retained in the reversible lookup; hashes
    # only give bounded parser names, and collisions explicitly fail closed.
    labels = {}
    bound_id = _digest(binding)
    def lower(atom):
        identity = {"binding": binding, "predicate": atom["predicate"], "arguments": atom["arguments"]}
        key = "a_" + _digest(identity)
        if key in labels and labels[key] != identity:
            raise InvalidRequest("atom-name collision")
        labels[key] = identity
        return {"predicate": key, "arguments": ["case_" + bound_id], "positive": atom["positive"]}
    facts = [{"kind": "fact", "atom": lower(a)} for a in reading["hypotheses"]]
    rule = {"kind": "rule", "body": [lower(a) for a in reading["bridge"]["body"]],
            "head": lower(reading["bridge"]["head"])}
    query = lower(conclusion)
    raw = "".join(verified_reading.render_clause(c) for c in [*facts, rule]).encode()
    query_raw = ("هل " + verified_reading.render_atom(query) + "؟\n").encode()
    with tempfile.TemporaryDirectory(prefix="nabt-assumptions-") as temp:
        source_path, query_path = Path(temp) / "assumptions.txt", Path(temp) / "query.txt"
        source_path.write_bytes(raw)
        query_path.write_bytes(query_raw)
        checked = mantuq_mafhum.derive_controlled(source_path, query_path,
            identity="generated_assumptions_" + bound_id, scope="scope_" + bound_id)
    execution = checked["execution"]
    # Native verification checks full saturation/clean support, not just a
    # user-supplied success flag. The target must have its own signed proof.
    # Evidence booleans are relative to the *signed query*, even when the
    # requested atom itself is negative; see VerifiedReading.evidence.
    if (execution.get("verified") is not True or execution.get("status") != "SUPPORTED"
            or execution.get("positive") is not True or execution.get("negative") is not False
            or execution.get("clean_positive") is not True or execution.get("clean_negative") is not False
            or not any(row["atom"] == query for row in checked["signed_consequences"])):
        raise RuntimeError("native checker did not certify the requested signed conclusion")
    return {"kind": "generated_assumption_transcript", "source_text": raw.decode(),
            "sha256": hashlib.sha256(raw).hexdigest(), "atom_bindings": labels,
            "original_arabic_interpretation_checked": False, "lean": checked}


def evaluate(payload, *, budget=None, root=ROOT):
    """Evaluate every supplied reading; search ranking is never an argument.

    A SUPPORTED result is conditional on explicit premises and a caller-supplied
    bridge. It is not a license for the original Arabic text or a worldly fact.
    """
    foundation.require_foundation('tools.mantuq_inference.evaluator.evaluate')
    out = _base()
    if budget is None:
        budget = EvaluationBudget()
    if type(budget) is not EvaluationBudget:
        return dict(out, status="INVALID", reason="budget must use installed EvaluationBudget")
    try:
        request, exhausted = _validate(payload, budget)
    except (InvalidRequest, TypeError, KeyError, ValueError, RecursionError) as exc:
        return dict(out, status="INVALID", reason=str(exc))
    if exhausted:
        return dict(out, status="RESOURCE_EXHAUSTED", reason=exhausted)
    try:
        inventory = build_inventory(root=root)
    except (ValueError, OSError) as exc:
        return dict(out, status="SOURCE_ERROR", reason=str(exc))
    policies = {r["rule_id"]: r for r in inventory["rules"]}
    if request["policy_id"] not in policies:
        return dict(out, status="SOURCE_ERROR", reason="installed source policy is absent")
    out.update(policy_id=request["policy_id"], binding=request["binding"],
               binding_sha256=_digest(request["binding"]), conclusion=request["conclusion"],
               policy=policies[request["policy_id"]],
               supplied_readings=len(request["readings"]))
    for reading in request["readings"]:
        row = {"reading_id": reading["reading_id"], "conditional_consequence": False,
               "requirements": reading["requirements"], "bridge_basis": "caller_assumption" if reading["bridge"] else None,
               "necessary_relation": reading["necessary_relation"]}
        if reading["hypotheses"] is None:
            row.update(status="UNKNOWN", reason="INCOMPLETE_READING", guard_status="UNKNOWN_PREMISE")
        elif request["policy_id"] == "opposition" and request["contrast_kind"] in {"name", "innama"}:
            row.update(status="REFUTED", reason="SOURCE_POLICY_DOES_NOT_LICENSE_CONTRAST", guard_status="INVALID_PROFILE")
        else:
            guard = guard_verdict(KINDS.get(request["policy_id"], "direct"), reading["requirements"], reading["hypotheses"])
            row["guard_status"] = guard
            status = {"INVALID_PROFILE": "INVALID", "CONFLICT": "CONFLICT", "REFUTED_PREMISE": "REFUTED",
                      "UNKNOWN_PREMISE": "UNKNOWN", "SUPPORTED_PREMISES": "SUPPORTED"}[guard]
            row.update(status=status, reason=guard)
            known = {_key(a) for a in reading["hypotheses"]}
            if _key(request["conclusion"]) in known and _key(_opposite(request["conclusion"])) in known:
                row.update(status="CONFLICT", reason="CONCLUSION_CONFLICT")
            elif _key(_opposite(request["conclusion"])) in known:
                row["conclusion_counterevidence"] = True
                if (status == "SUPPORTED" and reading["bridge"] is not None
                        and (request["policy_id"] != "opposition" or reading["necessary_relation"] is not None)):
                    row.update(status="CONFLICT", reason="DERIVABLE_CONCLUSION_OPPOSED")
            if row["status"] == "SUPPORTED":
                if reading["bridge"] is None:
                    row.update(status="UNKNOWN", reason="BRIDGE_MISSING")
                elif request["policy_id"] == "opposition" and reading["necessary_relation"] is None:
                    row.update(status="UNKNOWN", reason="NECESSARY_RELATION_MISSING")
                else:
                    try:
                        row["proof"] = _native_consequence(reading, request["binding"], request["conclusion"])
                        row.update(conditional_consequence=True, reason="NATIVE_CONDITIONAL_CONSEQUENCE")
                    except subprocess.TimeoutExpired:
                        row.update(status="RESOURCE_EXHAUSTED", reason="NATIVE_CHECK_TIMEOUT")
                    except NabtError as exc:
                        row.update(status="RESOURCE_EXHAUSTED" if exc.code == "RESOURCE_LIMIT" else "VERIFICATION_UNAVAILABLE",
                                   reason=exc.code, error=exc.as_dict())
                    except (RuntimeError, OSError, ValueError) as exc:
                        limited = str(exc).startswith("RESOURCE_LIMIT:")
                        row.update(status="RESOURCE_EXHAUSTED" if limited else "VERIFICATION_UNAVAILABLE",
                                   reason="RESOURCE_LIMIT" if limited else str(exc),
                                   error={"code": "RESOURCE_LIMIT", "message": str(exc)} if limited else {"message": str(exc)})
        out["readings"].append(row)
    out["declared_request_scan_complete"] = True
    statuses = {r["status"] for r in out["readings"]}
    if statuses == {"SUPPORTED"}:
        out.update(status="SUPPORTED", reason="ALL_SUPPLIED_READINGS_CONDITIONALLY_SUPPORT",
                   conditional_consequence=True, conditional_evaluation_complete=True)
    elif "RESOURCE_EXHAUSTED" in statuses:
        out.update(status="RESOURCE_EXHAUSTED", reason="NATIVE_RESOURCE_LIMIT")
    elif "VERIFICATION_UNAVAILABLE" in statuses:
        out.update(status="VERIFICATION_UNAVAILABLE", reason="NATIVE_VERIFICATION_REQUIRED")
    elif "CONFLICT" in statuses:
        out.update(status="CONFLICT", reason="CONFLICT_IN_SUPPLIED_READING")
    elif statuses == {"REFUTED"}:
        out.update(status="REFUTED", reason="REQUIRED_PREMISE_OPPOSED_NOT_CONCLUSION_NEGATION")
    elif "INVALID" in statuses:
        out.update(status="INVALID", reason="INVALID_READING_PROFILE")
    elif "SUPPORTED" in statuses and "REFUTED" in statuses:
        out.update(status="INCONSISTENT_READINGS", reason="READINGS_DISAGREE")
    else:
        out.update(status="UNKNOWN", reason="NOT_ALL_SUPPLIED_READINGS_SUPPORT")
    return out
