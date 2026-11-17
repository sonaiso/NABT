"""Update-preserving NTL lessons over the existing source-replayed semantic kernel.

The explicit family profile supplies controlled source-role bindings. It is not
a new free-text reader, a material model, or evidence of external occurrence.
"""
from copy import deepcopy
from hashlib import sha256
import re

from nabt import arabic_reader
from nabt.errors import NabtError
from nabt.semantics import SemanticKernel
from tools import evidence_lifecycle_v1 as wire
from . import update_memory_model as neural

SCHEMA = "ntl.update-memory.v1"
RESULT = "ntl.update-memory-result.v1"
FAMILIES = {
    "breaking": ("هش", "قابل للكسر", "وقوع الكسر", "مكسور"),
    "opening": ("قابل للحركة", "قابل للفتح", "وقوع الفتح", "مفتوح"),
}
MAX_SOURCES = 12
MAX_UPDATES = 16


def quoted(value):
    wire._text(value, "local identity", 96)
    if any(c in value for c in "«»") or value.startswith("?"):
        raise ValueError("Invalid local identity")
    return "«" + value + "»"


def profile(family, entity, event):
    if type(family) is not str or family not in FAMILIES:
        raise ValueError("Unknown installed conditional family")
    prop, capacity, occurrence, state = map(quoted, FAMILIES[family])
    entity, event = quoted(entity), quoted(event)
    if entity == event:
        raise ValueError("Entity and event identities must differ")
    sources = {
        "property": f"{entity} هو {prop}.",
        "law": f"كل {prop} هو {capacity}.",
        "event_positive": f"{event} هو {occurrence}.",
        "event_negative": f"ليس {event} هو {occurrence}.",
        "state": f"{entity} هو {state}.",
    }
    declarations = " ".join(f"مفهوم {p}." for p in (prop, capacity, occurrence, state))
    queries = {"capacity": f"هل {entity} هو {capacity}؟",
               "event": f"هل {event} هو {occurrence}؟", "state": f"هل {entity} هو {state}؟"}
    return sources, declarations, queries


def validate(lesson):
    wire._encoded(lesson, wire.MAX_REQUEST_BYTES)
    wire._fields(lesson, ("schema", "family", "entity", "event", "scope", "sources", "active", "updates"), "update lesson")
    if lesson["schema"] != SCHEMA:
        raise ValueError("Unknown update-memory schema")
    templates, declarations, queries = profile(lesson["family"], lesson["entity"], lesson["event"])
    wire._text(lesson["scope"], "scope", 96)
    wire._array(lesson["sources"], "sources", MAX_SOURCES)
    wire._array(lesson["updates"], "updates", MAX_UPDATES)
    wire._names(lesson["active"], "active")
    sources, ids = [], set()
    for row in lesson["sources"]:
        wire._fields(row, ("id", "text"), "source")
        if type(row["id"]) is not str or re.fullmatch(r"[a-z][a-z0-9_]{0,63}", row["id"]) is None or row["id"] == "declarations":
            raise ValueError("Invalid source identity")
        if row["id"] in ids:
            raise ValueError("Duplicate source identity")
        ids.add(row["id"])
        wire._text(row["text"], "source text", 2048, content=True)
        role = next((role for role, text in templates.items() if text == row["text"]), None)
        sources.append({**row, "role": role, "sha256": sha256(row["text"].encode()).hexdigest()})
    if not set(lesson["active"]) <= ids:
        raise ValueError("Unregistered active source")
    for update in lesson["updates"]:
        wire._fields(update, ("op", "source_id"), "update")
        if update["op"] not in ("activate", "withdraw") or type(update["source_id"]) is not str or update["source_id"] not in ids:
            raise ValueError("Unknown update or unregistered source")
    return sources, declarations, queries


def _memory(lesson, sources, active):
    # Exact reversible data, including inactive registered sources. A digest is
    # an integrity identifier, never a substitute for the payload.
    value = {"schema": "ntl.update-memory.fold.v1", "family": lesson["family"],
             "entity": lesson["entity"], "event": lesson["event"], "scope": lesson["scope"],
             "sources": [{"id": s["id"], "text": s["text"]} for s in sources], "active": sorted(active)}
    return {"payload": value, "sha256": sha256(wire.wire(value).encode()).hexdigest()}


def unfold(memory, updates):
    wire._fields(memory, ("payload", "sha256"), "folded memory")
    value = memory["payload"]
    wire._fields(value, ("schema", "family", "entity", "event", "scope", "sources", "active"), "fold payload")
    if (value["schema"] != "ntl.update-memory.fold.v1" or
            memory["sha256"] != sha256(wire.wire(value).encode()).hexdigest()):
        raise ValueError("Invalid memory transport")
    lesson = {**deepcopy(value), "schema": SCHEMA, "updates": deepcopy(updates)}
    validate(lesson)
    return lesson


def run(lesson):
    sources, declarations, queries = validate(lesson)
    result = {"schema": RESULT, "request": deepcopy(lesson), "execution_measured": True,
              "family_scope": "AUTHORED_CONDITIONAL_THEORY", "world_truth_established": False,
              "source_authenticity_established": False, "sources": sources, "history": [],
              "residuals": ["SOURCE_TRUTH_AND_MATERIAL_LAW_NOT_ESTABLISHED"]}
    unbound = [s["id"] for s in sources if s["role"] is None]
    if unbound:
        return {**result, "status": "DEFER_READING", "unbound_sources": unbound}
    kernel = SemanticKernel(language_id=arabic_reader.LANGUAGE_ID)
    scope = lesson["scope"]
    base = kernel.add_source(declarations, source_id="declarations", scope=scope)
    if not base.accepted:
        return {**result, "status": "OWNER_UNAVAILABLE", "owner_admission": base.as_dict()}
    result["declarations"] = {"text": declarations, "receipt": base.as_dict(), "asserts_facts": False}
    # Validate registered source interpretation even if initially inactive.
    for source in sources:
        checker = SemanticKernel(language_id=arabic_reader.LANGUAGE_ID)
        admission = checker.add_source(source["text"], source_id=source["id"], scope=scope)
        source["admission"] = admission.as_dict()
        if not admission.accepted:
            return {**result, "status": "DEFER_READING", "unbound_sources": [source["id"]]}
    active = set(lesson["active"])
    records = {s["id"]: s for s in sources}
    for source in sources:
        if source["id"] in active:
            admission = kernel.add_source(source["text"], source_id=source["id"], scope=scope)
            if not admission.accepted:
                return {**result, "status": "DEFER_READING", "owner_admission": admission.as_dict()}

    def snapshot(update, transition):
        answers = {}
        for name, query in queries.items():
            claim = kernel.query_text(query, scope=scope)
            checks = {side: kernel.verify_certificate(proof) for side, proof in claim.proofs.items()}
            answers[name] = {"question": query, "owner_result": claim.as_dict(), "certificate_checks": checks}
            if any(check.get("accepted") is not True for check in checks.values()):
                raise ValueError("Owner certificate replay failed")
        values = [int(answers["capacity"]["owner_result"]["positive_support"]),
                  int(answers["event"]["owner_result"]["positive_support"]),
                  int(answers["event"]["owner_result"]["negative_support"]),
                  int(answers["state"]["owner_result"]["positive_support"])]
        observation = neural.propose(sources, active)
        if "prediction" in observation:
            observation["matches_owner"] = observation["prediction"] == values
        result["history"].append({"step": len(result["history"]), "update": update,
            "transition_receipt": transition, "active": sorted(active), "questions": answers,
            "answer_projection": values, "neural_observation": observation,
            "memory": _memory(lesson, sources, active)})

    try:
        snapshot(None, None)
        for update in lesson["updates"]:
            identity = update["source_id"]
            transition = None
            if update["op"] == "activate" and identity not in active:
                receipt = kernel.add_source(records[identity]["text"], source_id=identity, scope=scope)
                if not receipt.accepted:
                    raise ValueError("Source activation was not admitted")
                transition = receipt.as_dict()
                active.add(identity)
            elif update["op"] == "withdraw" and identity in active:
                receipt = kernel.remove_source(identity)
                if not receipt.accepted:
                    raise ValueError("Source withdrawal was not admitted")
                transition = receipt.as_dict()
                active.remove(identity)
            snapshot(deepcopy(update), transition)
    except NabtError as error:
        if error.code == "RESOURCE_LIMIT":
            return {**result, "status": "RESOURCE_LIMIT", "execution_measured": False,
                    "error": error.as_dict(), "history_complete": False}
        raise ValueError(str(error)) from error
    return {**result, "status": "SOURCE_BOUND", "history_complete": True}
