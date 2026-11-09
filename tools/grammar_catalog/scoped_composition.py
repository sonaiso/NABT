"""Source composition followed by the installed evidence/inference owners.

The arithmetic and finite quantifier front ends fill explicitly missing reading
obligations. They do not replace the source kernel, lifecycle or proof registry.
"""
from copy import deepcopy
from hashlib import sha256
import subprocess
import tempfile

from tools import source_learning_connection as connection
from tools import evidence_lifecycle_v1 as life
from tools import verified_reading as ground
from . import composition_arithmetic as arithmetic, composition_quantifier as quantifier
from .operations import ROOT, digest

LAW_ID = "nabt.scoped-composition.v1"
SCHEMA = "nabt.scoped-composition.request.v1"
NATIVE = ROOT / "formal/.lake/build/bin/scopedCompositionProbe"
LIMITS = {
    "law_id": LAW_ID, "world_truth_established": False,
    "source_authenticity_established": False, "action_authority": "NONE",
    "free_arabic_complete": False, "general_python_lean_refinement_proved": False,
    "native_parser_soundness_theorem": False, "neural_training_performed": False,
    "domain_completeness_in_world_established": False,
    "evidence_strength": "SOURCE_RELATIVE_CONDITIONAL_OR_EXACT_FORMAL_COMPUTATION",
    "recursive_tree_is_grammar_license": False,
}


def validate(request):
    life._encoded(request, life.MAX_REQUEST_BYTES)
    if type(request) is not dict or request.get("schema") != SCHEMA:
        raise life.InputError("Unknown composition request")
    profile = request.get("profile")
    fields = {"arithmetic": ("text",), "quantifier": ("text", "domain", "sources", "initial_active", "events"),
              "conditional": ("connection",)}
    if type(profile) is not str or profile not in fields:
        raise life.InputError("Unknown composition profile")
    life._fields(request, ("schema", "profile", *fields[profile]), "composition request")
    if profile == "conditional":
        if type(request["connection"]) is not dict:
            raise life.InputError("Expected existing source connection request")
    else:
        life._text(request["text"], "composition text", 2048, content=True)
    if profile == "quantifier":
        life._array(request["domain"], "domain", 4)
        if not request["domain"] or any(type(n) is not str or len(n) > 64 or
                not ground.valid_name(n) or n in quantifier.RESERVED for n in request["domain"]):
            raise life.InputError("Nonempty scope of canonical names required")
        if len(set(request["domain"])) != len(request["domain"]):
            raise life.InputError("Scope names must be distinct")
        life._array(request["sources"], "sources", 7)
        for row in request["sources"]:
            life._fields(row, ("id", "text", "parents"), "source")
            if row["id"] == quantifier.POLICY_SOURCE:
                raise life.InputError("Cannot replace the installed scope policy")
        life._names(request["initial_active"], "initial_active")
        life._array(request["events"], "events", 16)
    return deepcopy(request)


def native(request, projection):
    """Reparse raw source, compare the complete projection, retain binary identity."""
    if NATIVE.is_symlink() or not NATIVE.resolve().is_relative_to(ROOT.resolve()):
        raise connection.ConnectionMismatch("Composition checker path escapes repository")
    before = sha256(NATIVE.read_bytes()).hexdigest()
    with tempfile.TemporaryFile() as output:
        try:
            proc = subprocess.run([str(NATIVE)], input=(life.wire(request) + "\n").encode(),
                                  stdout=output, stderr=subprocess.DEVNULL, timeout=20, check=False)
        except subprocess.TimeoutExpired as error:
            raise life.ResourceLimit("Composition checker time bound") from error
        output.seek(0)
        raw = output.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise life.ResourceLimit("Composition checker output bound")
    if proc.returncode or before != sha256(NATIVE.read_bytes()).hexdigest():
        raise connection.ConnectionMismatch("Composition checker execution or identity failed")
    try:
        reply = life.strict_loads(raw)
    except ValueError as error:
        raise connection.ConnectionMismatch("Invalid native composition response") from error
    expected = {"law_id": LAW_ID, "status": "OK", "request": request, "projection": projection}
    if life.wire(reply) != life.wire(expected):
        raise connection.ConnectionMismatch("Native composition differs from the complete source projection")
    return {"native_checked": True, "binary_sha256": before, "response": reply}


def _quantified_request(request, projection):
    compiled = {"schema": connection.REQUEST_SCHEMA,
        "sources": [{"id": quantifier.POLICY_SOURCE, "text": projection["policy_text"], "parents": []},
                    *deepcopy(request["sources"])],
        "query": projection["query_text"], "scope": LAW_ID + ":" + digest(projection),
        "initial_active": deepcopy(request["initial_active"]), "events": deepcopy(request["events"])}
    kernel, _, _, _ = connection._request(compiled)
    for doc in kernel._program().documents:
        if doc.source.source_id == quantifier.POLICY_SOURCE:
            continue
        if doc.rules or not doc.facts:
            raise life.InputError("Quantifier evidence must be facts, not caller policies")
        if any(f.atom.predicate == quantifier.GOAL["predicate"] for f in doc.facts):
            raise life.InputError("Caller cannot assert the compiled scope conclusion")
    return compiled


def _history(owner):
    rows, previous = [], None
    for step in owner.get("history", []):
        row = {k: deepcopy(step[k]) for k in ("step", "event_id", "status", "active_sources", "ready_sources",
                                             "support_ids", "refutation_ids", "signed_support_status")}
        row["change"] = ("INITIAL" if previous is None else
                         "PRESERVED" if previous == row["status"] else "REVISED")
        row["evidence_strength"] = "SOURCE_RELATIVE_CONDITIONAL"
        row["evidence_change_is_world_change"] = False
        rows.append(row)
        previous = row["status"]
    return rows


def evaluate(request):
    result = {"schema": "nabt.scoped-composition.result.v1", "law_id": LAW_ID,
              "status": "INVALID_INPUT", "chain_complete": False, "request": deepcopy(request),
              "native_check": None, "projection": None, "owner_result": None,
              "history": [], "limits": deepcopy(LIMITS)}
    try:
        request = validate(request)
        profile = request["profile"]
        if profile == "conditional":
            compiled = request["connection"]
            result["interpretation"] = {"owner": "nabt.controlled-arabic.v1",
                "conditional_is_evidence_of_antecedent": False,
                "implication_is_converse_or_physical_cause": False}
        else:
            text = request["text"]
            result["source"] = {"text": text, "sha256": sha256(text.encode()).hexdigest(),
                                "bytes": len(text.encode()), "text_is_world_evidence": False}
            projection = (arithmetic.project(text) if profile == "arithmetic" else
                          quantifier.project(text, request["domain"]))
            result["projection"] = projection
            native_request = {"law_id": LAW_ID, "profile": profile, "text": text}
            if profile == "quantifier": native_request["domain"] = request["domain"]
            result["native_check"] = native(native_request, projection)
            if profile == "arithmetic":
                result["status"] = projection["result"]["status"]
                result["chain_complete"] = result["status"] in ("COMPUTED", "BLOCKED")
                result["paraphrase_ar"] = arithmetic.paraphrase(projection["tree"])
                result["operator_registry"] = deepcopy(arithmetic.REGISTRY)
                return result
            compiled = _quantified_request(request, projection)
        owner = connection.evaluate(compiled)
        result.update(owner_result=owner, status=owner["status"], chain_complete=owner["chain_complete"])
        # The full owner retains source spans, signed premises, proofs, clashes,
        # alternatives, dependencies and independent native lifecycle receipts.
        result["history"] = _history(owner)
        life._encoded(result, life.MAX_REPORT_BYTES, floats=True)
    except arithmetic.CompositionError as error:
        result.update(status=error.code, error=str(error))
    except connection.SourceReadError as error:
        codes = {r.get("code") for r in error.report["residuals"]}
        result.update(status="RESOURCE_LIMIT" if "RESOURCE_LIMIT" in codes else
                      "DEFER" if error.report["status"] == "DEFER" else "INVALID_INPUT",
                      source_failure=error.report, error=str(error))
    except life.ResourceLimit as error:
        return {"schema": result["schema"], "law_id": LAW_ID, "status": "RESOURCE_LIMIT",
                "chain_complete": False, "history": [], "error": str(error), "limits": deepcopy(LIMITS)}
    except connection.ConnectionMismatch as error:
        result.update(status="VERIFICATION_FAILED", chain_complete=False, error=str(error))
    except connection.NabtError as error:
        result.update(status="RESOURCE_LIMIT" if error.code == "RESOURCE_LIMIT" else "INVALID_INPUT",
                      chain_complete=False, error=error.code)
    except OSError as error:
        result.update(status="VERIFICATION_UNAVAILABLE", chain_complete=False, error=str(error))
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError) as error:
        result.update(status="INVALID_INPUT", chain_complete=False, error=str(error))
    return result
