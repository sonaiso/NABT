"""One bounded case application, composed from existing NABT owners.

No new reader, closure, learning law or source lifecycle is implemented here.
The installed policy supplies the target obligations, never their evidence.
Caller records are facts only; the original reader and native source owners
retain the entire interpretation, source spans, alternatives and history.
"""
from copy import deepcopy
from hashlib import sha256

from tools import source_learning_connection as connection
from tools import verified_reading as ground
from tools.evidence_lifecycle_v1 import InputError, ResourceLimit, _encoded, wire, strict_loads
from tools.mantuq_inference import source_bound
from .operations import ROOT, digest

LAW_ID = "nabt.case-application.v1"
SCHEMA = "nabt.case-application.request.v1"
POLICY_ID = "warehouse-transfer.v1"
POLICY_PATH = "tools/grammar_catalog/data/warehouse_transfer_v1.json"
CASE_FIELDS = ("event", "item", "actor", "origin", "destination", "time")
POLICY_SOURCE = "installed_policy"
DECISIONS = {
    "SUPPORTED": ("SUPPORTED", "استوفى الطلب السياسة بحسب الشواهد الحالية."),
    "REFUTED": ("NOT_APPLICABLE", "عارض شاهد شرطًا لازمًا؛ لم يثبت نفي النتيجة عمومًا."),
    "CONFLICT": ("CONFLICT", "تعارضت الشواهد المؤثرة؛ حُجب قبول التطبيق."),
    "UNKNOWN": ("UNKNOWN", "لم تكتمل شواهد التطبيق أو سُحب مستند السياسة."),
}
LIMITS = {
    "domain": POLICY_ID, "language": "nabt.controlled-arabic.v1",
    "evidence_strength": "SOURCE_RELATIVE_CONDITIONAL",
    "source_authenticity_established": False, "world_truth_established": False,
    "sensor_grounding_established": False, "free_arabic_complete": False,
    "general_python_lean_refinement_proved": False, "neural_training_performed": False,
    "action_authority": "NONE", "time_and_place": "EXACT_SYMBOLIC_RELATIONS_ONLY",
    "update_semantics": "EVIDENCE_REVISION_NOT_AN_ASSERTION_OF_PHYSICAL_EVENT_ORDER",
    "support_granularity": "WHOLE_SOURCE", "max_caller_sources": 7, "max_events": 16,
    "source_annotations_are_authentication": False,
}


def validate(request):
    """Close the application boundary; original owners validate their inputs."""
    _encoded(request, connection.life.MAX_REQUEST_BYTES)
    connection.life._fields(request, ("schema", "policy_id", "case", "sources",
                                      "initial_active", "events"), "case request")
    if request["schema"] != SCHEMA or request["policy_id"] != POLICY_ID:
        raise InputError("Unknown installed case application or policy")
    connection.life._fields(request["case"], CASE_FIELDS, "case binding")
    for value in request["case"].values():
        if type(value) is not str or len(value) > 64 or not ground.valid_name(value):
            raise InputError("Case roles require bounded canonical ground names")
    values = list(request["case"].values())
    if len(set(values)) != len(values) or set(values) & {"صندوق", "سياسة_النقل"}:
        raise InputError("Distinct case roles and installed constants must not alias")
    connection.life._array(request["sources"], "case sources", 7)
    connection.life._names(request["initial_active"], "initial_active")
    connection.life._array(request["events"], "case events", 16)
    for row in request["sources"]:
        connection.life._fields(row, ("id", "text", "parents"), "source")
        connection.life._text(row["id"], "source.id", 64)
        connection.life._text(row["text"], "source.text", 8192, content=True)
        connection.life._names(row["parents"], "source.parents")
        if row["id"] == POLICY_SOURCE:
            raise InputError("Caller cannot replace the installed policy")
    for event in request["events"]:
        connection.life._fields(event, ("id", "kind", "target"), "event")
        for key in ("id", "kind", "target"):
            connection.life._text(event[key], "event." + key, 128)
    # Reading and source semantics belong to the owner, inside the worker.
    # An unsupported sentence must retain its DEFER and original residuals.
    return deepcopy(request)


def installed_policy():
    path = ROOT / POLICY_PATH
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
        raise InputError("Installed policy escapes repository")
    raw = path.read_bytes()
    policy = strict_loads(raw)
    if policy["id"] != POLICY_ID or policy["source_id"] != POLICY_SOURCE:
        raise InputError("Installed policy identity differs")
    return policy, sha256(raw).hexdigest()


def compile_request(request):
    """Instantiate a reviewed rule. No case metadata is inserted as a fact."""
    policy, policy_sha = installed_policy()

    def bind(atom):
        return {"predicate": atom["predicate"], "positive": atom["positive"],
                "arguments": [request["case"][s[1:]] if s.startswith("@") else s
                              for s in atom["arguments"]]}

    requirements = [{"slot": row["slot"], "label_ar": row["label_ar"], "atom": bind(row)}
                    for row in policy["requirements"]]
    conclusion = bind(policy["conclusion"])
    clause = {"kind": "rule", "body": [r["atom"] for r in requirements], "head": conclusion}
    text = ground.render_clause(clause)
    for row in request["sources"]:
        if type(row) is not dict or row.get("id") == POLICY_SOURCE:
            raise InputError("Caller cannot replace the installed policy")
    compiled = {"schema": connection.REQUEST_SCHEMA,
        "sources": [{"id": POLICY_SOURCE, "text": text, "parents": []}, *deepcopy(request["sources"])],
        "query": "هل " + ground.render_atom(conclusion) + "؟\n",
        "scope": LAW_ID + ":" + digest(request["case"]),
        "initial_active": deepcopy(request["initial_active"]), "events": deepcopy(request["events"])}
    binding = {"policy": policy, "path": POLICY_PATH, "sha256": policy_sha,
        "case": deepcopy(request["case"]), "case_binding_is_evidence": False,
        "instantiated_source": text, "requirements": requirements, "conclusion": conclusion}
    return compiled, binding


def _source_records(compiled):
    """Reuse the installed reader; reject rules or conclusions in fact records."""
    kernel, _, _, _ = connection._request(compiled)
    for document in kernel._program().documents:
        if document.source.source_id == POLICY_SOURCE:
            continue
        if document.rules or not document.facts:
            raise InputError("Case evidence must contain facts, not rules or empty records")
        if any(f.atom.predicate == "يستوفي" for f in document.facts):
            raise InputError("Caller evidence cannot assert the application conclusion")


def _ledger(owner):
    result = []
    for document in owner["acquisition"]:
        for fact in document["facts"]:
            span = fact["span"]
            text = document["raw_text"].encode()[span["start"]:span["end"]].decode()
            atom = fact["atom"]
            result.append({"source_id": document["source_id"], "source_sha256": document["source_sha256"],
                "span": deepcopy(span), "text": text, "component_spans": deepcopy(fact["component_spans"]),
                "atom": {"predicate": atom["predicate"], "arguments": atom["args"], "positive": atom["positive"]}})
    return result


def _requirements(binding, ledger, ready, certificate):
    """Display source witnesses and the native closure, never derive a verdict."""
    known = {ground.key(a) for a in certificate["known"]}
    clean = {ground.key(a) for a in certificate["clean_known"]}
    rows = []
    for requirement in binding["requirements"]:
        key = ground.key(requirement["atom"])
        opposite = ground.opposite(key)
        rows.append({**deepcopy(requirement),
            "present_in_native_closure": key in known, "present_in_clean_closure": key in clean,
            "opposite_in_native_closure": opposite in known,
            "source_witnesses": [i for i, row in enumerate(ledger)
                if row["source_id"] in ready and ground.key(row["atom"]) == key],
            "opposing_source_witnesses": [i for i, row in enumerate(ledger)
                if row["source_id"] in ready and ground.key(row["atom"]) == opposite]})
    return rows


def _step(history, compiled, binding, ledger):
    native = history["ground_inference"]
    if not native["native_checked"]:
        return {"step": history["step"], "event_id": history["event_id"],
                "status": "DEFER", "conditional_consequence": False,
                "reason": "GROUND_READING_NOT_CHECKED", "application_complete": False}
    certificate = native["answer"]["analysis_certificate"]["kernel_certificate"]
    rule = {"kind": "rule", "body": [r["atom"] for r in binding["requirements"]],
            "head": binding["conclusion"]}
    matches = [i for i, c in enumerate(certificate["clauses"]) if c == rule]
    if len(matches) > 1:
        raise InputError("Installed policy has multiple unexpected ground occurrences")
    plan = {"schema": source_bound.PLAN_SCHEMA, "policy_id": "matching",
        "requirements": [{"slot": r["slot"], "atom": r["atom"]} for r in binding["requirements"]],
        "bridge_clause": "c" + str(matches[0]) if matches else None}
    checked = source_bound.evaluate_source(certificate["source"]["text"].encode(),
        certificate["query_text"].encode(), plan, source_id=certificate["source"]["identity"],
        revision=certificate["source"]["revision"], scope=compiled["scope"],
        context=wire(binding["case"]), time=binding["case"]["time"])
    accepted = checked["conditional_consequence"]
    if accepted != (history["status"] == "SUPPORTED") and checked["status"] in DECISIONS:
        raise connection.ConnectionMismatch("Case owners disagree on positive application")
    status, text = DECISIONS.get(checked["status"],
        (checked["status"], "لم يكتمل فحص التطبيق؛ راجع نتيجة المالك الأصلية."))
    obligations = _requirements(binding, ledger, set(history["ready_sources"]), certificate)
    return {"step": history["step"], "event_id": history["event_id"],
        "status": status, "explanation_ar": text, "reason": checked["reason"],
        "conditional_consequence": accepted, "application_complete": checked["status"] in DECISIONS,
        "source_consequence_status": history["status"], "qualified_status": checked["status"],
        "active_sources": history["active_sources"], "ready_sources": history["ready_sources"],
        "policy_active": POLICY_SOURCE in history["ready_sources"],
        "requirements": obligations,
        "residuals": [{"slot": r["slot"],
            "missing": not r["present_in_native_closure"],
            "opposed": r["opposite_in_native_closure"]} for r in obligations
            if not r["present_in_clean_closure"] or r["opposite_in_native_closure"]],
        "evidence_strength": "SOURCE_RELATIVE_CONDITIONAL" if accepted else "NO_ACCEPTED_APPLICATION",
        "qualified_replay": checked}


def _changes(previous, current):
    if previous is None:
        return {"kind": "INITIAL", "changed_requirements": [], "judgment_changed": False}
    fields = ("present_in_native_closure", "present_in_clean_closure", "opposite_in_native_closure")
    changed = [new["slot"] for old, new in zip(previous.get("requirements", []), current.get("requirements", []))
               if any(old[k] != new[k] for k in fields)]
    judgment_changed = ((previous["status"], previous["conditional_consequence"]) !=
                        (current["status"], current["conditional_consequence"]))
    return {"kind": "REVISED" if judgment_changed else "PRESERVED",
            "changed_requirements": changed, "judgment_changed": judgment_changed,
            "policy_availability_changed": previous.get("policy_active") != current.get("policy_active"),
            "evidence_change_is_world_change": False}


def evaluate(request):
    result = {"schema": "nabt.case-application.result.v1", "law_id": LAW_ID,
              "status": "INVALID_INPUT", "chain_complete": False, "request": deepcopy(request),
              "policy_binding": None, "source_ledger": [], "history": [], "owner_result": None,
              "limits": deepcopy(LIMITS)}
    try:
        validated = validate(request)
        compiled, binding = compile_request(validated)
        _source_records(compiled)
        result["policy_binding"] = binding
        owner = connection.evaluate(compiled)
        result["owner_result"] = owner
        if not owner["chain_complete"]:
            result["status"] = owner["status"]
            return result
        ledger = _ledger(owner)
        result["source_ledger"] = ledger
        previous = None
        for row in owner["history"]:
            current = _step(row, compiled, binding, ledger)
            current["change"] = _changes(previous, current)
            result["history"].append(current)
            previous = current
        if installed_policy()[1] != binding["sha256"]:
            raise connection.ConnectionMismatch("Installed policy changed during replay")
        result.update(status=previous["status"], chain_complete=all(
            row["application_complete"] for row in result["history"]))
        if not result["chain_complete"]:
            result["status"] = "DEFER"
            result["error"] = "INCOMPLETE_APPLICATION_HISTORY"
            return result
        result["current_decision"] = {"status": previous["status"],
            "conditional_consequence": previous["conditional_consequence"],
            "explanation_ar": previous["explanation_ar"],
            "evidence_strength": previous["evidence_strength"],
            "world_truth_established": False, "action_authority": "NONE"}
        _encoded(result, connection.life.MAX_REPORT_BYTES, floats=True)
    except connection.SourceReadError as error:
        codes = {r.get("code") for r in error.report["residuals"]}
        result.update(status="RESOURCE_LIMIT" if "RESOURCE_LIMIT" in codes else
                      "DEFER" if error.report["status"] == "DEFER" else "INVALID_INPUT",
                      source_failure=error.report, error=str(error))
    except ResourceLimit as error:
        # Do not return a partial historical positive result as a complete run.
        result = {"schema": result["schema"], "law_id": LAW_ID, "status": "RESOURCE_LIMIT",
                  "chain_complete": False, "history": [], "error": str(error), "limits": deepcopy(LIMITS)}
    except connection.ConnectionMismatch as error:
        result.update(status="VERIFICATION_FAILED", chain_complete=False, error=str(error))
    except connection.NabtError as error:
        result.update(status="RESOURCE_LIMIT" if error.code == "RESOURCE_LIMIT" else "INVALID_INPUT",
                      chain_complete=False, error=error.code)
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError) as error:
        result.update(status="INVALID_INPUT", chain_complete=False, error=str(error))
    except OSError as error:
        result.update(status="VERIFICATION_UNAVAILABLE", chain_complete=False, error=str(error))
    return result
