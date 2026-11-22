"""NTP lesson adapter for versioned, explicitly selected simulated evidence."""
from datetime import datetime
import re

from tools import evidence_lifecycle_v1 as wire
from . import knowledge_assessment as checks
from .knowledge_records import Operation, Record, Ref, Store, fold, unfold

SCHEMA = "ntl.knowledge-assessment.v1"
RESULT = "ntl.knowledge-assessment-result.v1"
SCOPE = ("domain", *checks.SCOPE_FIELDS)
CHANNELS = ("simulated_interval", "reported_interval")


def identifier(value):
    if type(value) is not str or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,47}", value):
        raise ValueError("Expected a local record identifier")
    return value


def instant(value):
    wire._text(value, "timestamp", 48)
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() is None:
        raise ValueError("Supply an ISO timestamp with UTC offset")
    return parsed


def scope(row):
    for field in SCOPE:
        wire._text(row[field], field, 96)
    return {field: row[field] for field in checks.SCOPE_FIELDS}


def number(value):
    if type(value) is not int or abs(value) > 10**12:
        raise ValueError("Expected a bounded integer measurement")
    return value


def emit(store, ref, kind, domain, content, mode, operation, *, sources=(), dependencies=()):
    op_id = f"{ref.record_id}@{ref.version}/{operation}"
    record = Record.make(ref.record_id, ref.version, kind, domain, content, mode,
                         sources=sources, dependencies=dependencies, trace=(op_id,))
    store.log(Operation(op_id, operation, domain, tuple(sources) + tuple(dependencies),
                        (ref,), "LICENSED", "local structured episode"))
    return store.add(record)


def receive(store, lesson):
    origins = {}
    for row in lesson["occurrences"]:
        wire._fields(row, ("id", *SCOPE, "source", "channel", "received_at", "lower", "upper"), "occurrence")
        key = identifier(row["id"])
        if key in origins or row["channel"] not in CHANNELS:
            raise ValueError("Duplicate occurrence or unsupported channel")
        scope(row)
        wire._text(row["source"], "source", 128)
        instant(row["received_at"])
        number(row["lower"])
        number(row["upper"])
        origins[key] = emit(store, Ref("occurrence/" + key, 1), "occurrence", row["domain"],
                            row, row["channel"], "receive")

    for row in lesson["information"]:
        wire._fields(row, ("id", "occurrence"), "information")
        original = origins.get(identifier(row["occurrence"]))
        ref = Ref("info/" + identifier(row["id"]), 1)
        if original is None or ref in store.records:
            raise ValueError("Unknown origin or duplicate information identity")
        info = emit(store, ref, "information", original.domain, original.content,
                    "received_" + original.provenance_mode, "retain", sources=(original.ref,))
        # The interpretation has its own identity and the precise scope of the
        # received bounds. A reported interval can be understood before it qualifies.
        emit(store, Ref("interpret/" + ref.record_id, 1), "conception", info.domain,
             {**info.content, "interpretation": "closed_integer_bounds"},
             "derived_interval_reading", "read_interval", dependencies=(ref,))
    return origins


def claim_ref(data):
    raw = Ref.read(data)
    return Ref("claim/" + identifier(raw.record_id), raw.version)


def declare_claims(store, lesson):
    claims = {}
    for row in lesson["claims"]:
        wire._fields(row, ("ref", "symbol", "threshold", *SCOPE), "claim")
        ref = claim_ref(row["ref"])
        symbol = row["symbol"]
        if type(symbol) is not str or not re.fullmatch(r"[A-Z]", symbol):
            raise ValueError("Expected a propositional atom A through Z")
        previous = (Ref(ref.record_id, ref.version - 1),) if ref.version > 1 else ()
        if ref in claims or any(p not in claims for p in previous):
            raise ValueError("Claim versions must be unique and consecutive")
        claims[ref] = emit(store, ref, "claim", row["domain"],
                           {**scope(row), "predicate": "greater_than", "threshold": number(row["threshold"]),
                            "formula": symbol}, "authored_claim", "identify_claim", dependencies=previous)
    return claims


def require_claim(claims, value):
    ref = claim_ref(value)
    if ref not in claims:
        raise ValueError("Unknown exact claim version")
    return claims[ref]


def run(lesson):
    wire._encoded(lesson, wire.MAX_REQUEST_BYTES)
    wire._fields(lesson, ("schema", "occurrences", "information", "claims", "steps"), "knowledge lesson")
    if lesson["schema"] != SCHEMA:
        raise ValueError("Unknown knowledge lesson")
    for field, maximum in (("occurrences", 16), ("information", 24), ("claims", 8), ("steps", 16)):
        wire._array(lesson[field], field, maximum)
    store = Store()
    origins = receive(store, lesson)
    claims = declare_claims(store, lesson)
    policies = {}
    for domain in sorted({c.domain for c in claims.values()}):
        accepted = tuple(o.ref for o in origins.values()
                         if o.domain == domain and o.provenance_mode == "simulated_interval")
        policies[domain] = emit(store, Ref("policy/" + domain, 1), "prior", domain,
                                {"rule": "trusted_bounded_interval/v1",
                                 "accepted_occurrences": [r.data() for r in accepted]},
                                "declared_evaluation_policy", "install_interval_policy", sources=accepted)

    history, current = [], {}
    previous_time = None
    for index, step in enumerate(lesson["steps"]):
        if type(step) is not dict or step.get("op") not in ("assess", "audit"):
            raise ValueError("Unknown knowledge operation")
        fields = ("claim", "evidence") if step["op"] == "assess" else ("if", "then", "premise", "conclusion")
        wire._fields(step, ("op", "at", *fields), "knowledge step")
        at = instant(step["at"])
        if previous_time is not None and at < previous_time:
            raise ValueError("Assessment history must be chronological")
        previous_time = at
        if step["op"] == "assess":
            claim = require_claim(claims, step["claim"])
            wire._array(step["evidence"], "selected information", 24)
            selected = [Ref("info/" + identifier(key), 1) for key in step["evidence"]]
            if any(ref in store.records and instant(store.records[ref].content["received_at"]) > at
                   for ref in selected):
                raise ValueError("Selected information had not arrived at assessment time")
            previous = current.get(claim.ref)
            outcome = checks.assess_threshold(
                store, claim.ref, selected, policies[claim.domain].ref,
                f"assessment/{claim.ref.record_id}@{claim.ref.version}",
                version=previous.version + 1 if previous else 1, previous=previous, at=step["at"])
            if outcome.status == "LICENSED":
                current[claim.ref] = outcome.value.ref
        else:
            left, right, premise, target = (require_claim(claims, step[k]) for k in fields)
            if left.domain != right.domain:
                raise ValueError("This model stipulates implications within one domain")
            rule = emit(store, Ref("rule/" + str(index), 1), "prior", left.domain,
                        {"formula": ["implies", left.content["formula"], right.content["formula"]],
                         "rule_kind": "stipulated_axiom"}, "declared_model_rule", "stipulate_local_implication",
                        dependencies=(left.ref, right.ref))
            reviews = tuple(dict.fromkeys(current[r] for r in (premise.ref, target.ref) if r in current))
            outcome = checks.audit_link(store, (rule.ref, premise.ref), target.ref, reviews,
                                        "audit/" + str(index), at=step["at"])
        if outcome.status != "LICENSED":
            raise ValueError("Knowledge record could not be issued: " + ", ".join(outcome.reasons))
        history.append(outcome.value.ref.data())

    packed = fold(store, tuple(store.records))
    if packed.status != "LICENSED":
        raise wire.ResourceLimit("Knowledge snapshot exceeded its bounded contract")
    restored = unfold(packed.value)
    if (restored.status != "LICENSED" or restored.value.records != store.records
            or restored.value.operations != store.operations):
        raise ValueError("Knowledge snapshot replay mismatch")
    return {"schema": RESULT, "status": "ASSESSED_EPISODE", "execution_measured": True,
            "scope": "AUTHORED_INTERVALS_AND_STIPULATED_IMPLICATION", "request": lesson,
            "history": history, "records": [r.data() for r in store.records.values()],
            "operations": [op.data() for op in store.operations.values()],
            "snapshot": {"manifest": packed.value.manifest, "compressed_hex": packed.value.compressed.hex()},
            "source_authenticity_established": False, "world_truth_established": False,
            "neural_training_performed": False}
