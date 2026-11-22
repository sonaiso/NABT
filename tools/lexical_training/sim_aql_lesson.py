"""Run SIM-AQL within cognitive.lesson, retaining the exact upstream NTL result."""
from dataclasses import MISSING, asdict, fields, is_dataclass
from functools import lru_cache
import json
from types import UnionType
from typing import get_args, get_origin, get_type_hints

from tools import evidence_lifecycle_v1 as wire
from . import inspection_discourse, knowledge_lesson
from .sim_aql import engine
from .sim_aql.guardian import Claim, Evidence, PolicyProfile, canonical, digest, utc_time

SCHEMA = "ntl.sim-aql.v0.2"
RESULT = "ntl.sim-aql-result.v0.2"


@lru_cache(maxsize=None)
def _types(cls):
    return get_type_hints(cls)


def _decode(kind, value, path):
    """Decode only the installed dataclasses. JSON strings never stand in for arrays."""
    origin, args = get_origin(kind), get_args(kind)
    if origin is UnionType and type(None) in args:
        return None if value is None else _decode(args[0], value, path)
    if origin is tuple:
        wire._array(value, path, 64)
        if args[-1] is Ellipsis:
            return tuple(_decode(args[0], item, path) for item in value)
        if len(args) != len(value):
            raise ValueError("Wrong tuple arity at " + path)
        return tuple(_decode(t, item, path) for t, item in zip(args, value))
    if is_dataclass(kind):
        if type(value) is not dict:
            raise ValueError("Expected a record at " + path)
        types = _types(kind)
        required = {f.name for f in fields(kind) if f.default is MISSING and f.default_factory is MISSING}
        if set(value) - types.keys() or required - value.keys():
            raise ValueError("Unexpected or missing field at " + path)
        return kind(**{k: _decode(types[k], v, path + "." + k) for k, v in value.items()})
    if kind not in (str, int) or type(value) is not kind:
        raise ValueError("Invalid type at " + path)
    return value


def _owner_context(claim, at, state, source_ref, payload, witness, version):
    """A reviewed NABT simulation result addresses exactly this positive claim."""
    if state in ("SUPPORTED", "REFUTED", "DENIED", "CONFLICT", "CONFLICTED"):
        blocking = ("OWNER_REFUTED_POSITIVE_CLAIM",) if state in ("REFUTED", "DENIED") else ()
        review = "UNREVIEWED" if state in ("CONFLICT", "CONFLICTED") else "ACCEPTED"
        evidence = Evidence("owner-review", version, claim.id, claim.domain, claim.target_id,
                            "REPLAYED_LOCAL_SIMULATION", source_ref, digest(witness), review,
                            (source_ref,), canonical(witness), blocking_residuals=blocking)
        rows = (engine.EvidenceRecord(evidence, role="NABT_OWNER_REPLAY"),)
    else:
        rows = ()
    return engine.EvaluationContext(
        question=engine.Question("owner-question", claim.id, claim.domain, claim.target_id, "DESCRIBE_REALITY", "PROPERTY"),
        reception=engine.Reception("owner-input", payload, "REPLAYED_LOCAL_EPISODE", source_ref, at),
        claims=(claim,), scopes=(engine.ClaimScope(claim.id, "DESCRIBE_REALITY", "PROPERTY"),),
        evidence=rows, steps=(engine.Step("admit", "ADMIT_REGISTERED_EVIDENCE", claim.id,
            "apply the scoped upstream judgment", tuple(r.evidence.id for r in rows)),),
        final_step_id="admit", as_of=at)


def _from_knowledge(source):
    wire._fields(source, ("kind", "lesson", "claim", "as_of"), "knowledge source")
    at = utc_time(source["as_of"])
    ref = knowledge_lesson.claim_ref(source["claim"]).data()
    upstream = knowledge_lesson.run(source["lesson"])
    if (any(utc_time(step["at"]) > at for step in source["lesson"]["steps"])
            or any(utc_time(row["received_at"]) > at for row in source["lesson"]["occurrences"])):
        raise ValueError("The knowledge history extends beyond the requested time")
    records = upstream["records"]
    record = next((r for r in records if r["kind"] == "claim" and r["ref"] == ref), None)
    if record is None:
        raise ValueError("Unknown exact knowledge claim version")
    reviews = [r for r in records if r["kind"] == "assessment" and r["content"]["claim"] == ref]
    latest = max(reviews, key=lambda r: r["ref"]["version"], default=None)
    state = latest["content"]["status"] if latest else "UNASSESSED"
    claim = Claim(canonical(ref), record["domain"], record["content"]["subject"], canonical(record["content"]))
    witness = {"claim": ref, "assessment": latest, "state": state,
               "snapshot_sha256": upstream["snapshot"]["manifest"]["sha256"]}
    context = _owner_context(claim, source["as_of"], state, "ntl.knowledge-assessment.v1",
                             canonical(record), witness, latest["ref"]["version"] if latest else 1)
    return context, upstream, witness


def _from_inspection(source):
    wire._fields(source, ("kind", "lesson", "as_of"), "inspection source")
    utc_time(source["as_of"])
    lesson = source["lesson"]
    upstream = inspection_discourse.run(lesson)
    support = upstream["answers"]["inspection"]
    condition = (upstream["answers"]["requested"] or {}).get("condition")
    # This claim describes the inspection register in this scene, even when the
    # bearer cannot be resolved. The separately reported utterance is retained.
    claim = Claim("registered-opening", inspection_discourse.LAW, lesson["scene_id"],
                  canonical({"scene": lesson["scene_id"], "condition": condition,
                             "object": support.get("object_id")}))
    ids = set(support["witness_ids"]) if "witness_ids" in support else set()
    witness = {"state": support["status"], "register": support,
               "observations": [step for step in lesson["steps"] if step.get("id") in ids and step["op"] == "observe"]}
    context = _owner_context(claim, source["as_of"], support["status"], inspection_discourse.LAW,
                             lesson["text"], witness, 1)
    return context, upstream, witness


def run(lesson):
    wire._encoded(lesson, 131072)
    wire._fields(lesson, ("schema", "source", "motive"), "SIM-AQL lesson")
    if lesson["schema"] != SCHEMA or type(lesson["source"]) is not dict:
        raise ValueError("Unknown SIM-AQL request")
    source = lesson["source"]
    kind = source.get("kind")
    upstream = binding = None
    if kind == "authored_context":
        wire._fields(source, ("kind", "context"), "authored context")
        context = _decode(engine.EvaluationContext, source["context"], "context")
        if any(row.role == "NABT_OWNER_REPLAY" for row in context.evidence):
            raise ValueError("An authored review cannot attest an upstream NABT run")
        if context.policy != PolicyProfile():
            raise ValueError("This lesson uses the installed reference policy")
    elif kind in ("knowledge_assessment", "inspection"):
        if type(source.get("as_of")) is not str or type(source.get("lesson")) is not dict:
            raise ValueError("An episode and its reference timestamp are required")
        owner = knowledge_lesson if kind == "knowledge_assessment" else inspection_discourse
        if source["lesson"].get("schema") != owner.SCHEMA:
            raise ValueError("Upstream lesson schema mismatch")
        context, upstream, binding = (_from_knowledge(source) if kind == "knowledge_assessment"
                                      else _from_inspection(source))
    else:
        raise ValueError("Unknown SIM-AQL source")
    motive = _decode(engine.Motive, lesson["motive"], "motive")
    run_record = engine.Simulator().run(context, motive)
    # Convert tuple-valued records to the public gateway's strict JSON wire.
    record = json.loads(canonical(asdict(run_record)))
    return {"schema": RESULT, "status": "SIMULATED", "request": lesson, "execution_measured": True,
            "source_kind": kind, "upstream_owner": upstream, "binding": binding,
            "run": record, "epistemic_sha256": engine.epistemic_digest(run_record),
            "scope": "LOCAL_SIMULATION_WITH_ATTRIBUTED_INPUTS", "action_authority": "NONE",
            "world_truth_established": False, "source_authenticated": False,
            "neural_training_performed": False}
