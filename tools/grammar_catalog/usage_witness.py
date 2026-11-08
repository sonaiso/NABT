"""Occurrence-local use witnesses from the installed LinguisticTruth owner.

This is an adapter, not a reader or another inference calculus. A source-use
application never certifies the external referent or the six-stage grammar path.
"""
from copy import deepcopy
from hashlib import sha256
import subprocess

from tools.evidence_lifecycle_v1 import wire
from tools.linguistic_truth import runtime as owner
from tools.linguistic_truth.calculus import guard_requirements
from tools.linguistic_truth.inventory import build_inventory
from tools.lexical_training import concepts as identities
from .operations import digest

SCHEMA = "nabt.usage-witness-bridge.v1"
# An explicit, bounded editorial alignment, not equality inferred from spelling.
# Both installed catalogues and their original quotations are replayed below.
# Other usage IDs remain references to their existing owner, never domain copies.
ALIASES = {"asad_animal": "lisan:asad-animal"}


def validate_context(context):
    if type(context) is not dict or set(context) - {"profile_id", "subject", "time", "context"}:
        raise ValueError("Use explicit convention context, never licensing flags or witness paths")
    for key, value in context.items():
        if type(value) is not str or not value.strip() or len(value.encode()) > 512:
            raise ValueError("Expected bounded usage context: " + key)
    return deepcopy(context)


def _span(span, raw):
    if type(span) is not dict:
        raise ValueError("MISSING_LOCAL_SPAN")
    a, b = span.get("start_byte"), span.get("end_byte")
    if (type(a) is not int or type(b) is not int or not 0 <= a < b <= len(raw)
            or raw[a:b] != span.get("raw_text", "").encode()
            or sha256(raw[a:b]).hexdigest() != span.get("sha256")):
        raise ValueError("NONLOCAL_WITNESS")
    return a, b


def _clean(atom, known):
    opposite = {**atom, "positive": not atom["positive"]}
    return wire(atom) in known and wire(opposite) not in known


def _references(inventory):
    # No new definition is asserted: these are pointers to original owner rows.
    native = {r["identity"]["id"]: r for r in identities.catalogue()["concepts"]}
    definitions = {}
    for kind, rows, key in (("designations", inventory["designations"], "sense_id"),
                            ("relations", inventory["relations"], "target_sense_id")):
        for index, row in enumerate(rows):
            sid = row[key]
            definitions.setdefault(sid, []).append({"pointer": "/"+kind+"/"+str(index), "value": row})
    refs = {}
    for sid, rows in definitions.items():
        canonical = ALIASES.get(sid, sid)
        origin = {"law_id": "nabt.linguistic-truth.v1", "sense_id": sid,
                  "inventory_sha256": inventory["review_sha256"], "rows": rows}
        if sid in ALIASES:
            target = native[canonical]
            # This deliberately names one reviewed sense, not all الأسد readings.
            if (sid != "asad_animal" or target["sense"]["root"] != "أسد"
                    or target["sense"]["components"] != ["من السباع"]
                    or rows[0]["value"]["gloss"] != "الحيوان المفترس"):
                raise ValueError("USAGE_IDENTITY_ALIGNMENT_CHANGED")
            reference = target["reference"]
            alignment = {"status": "SCOPED_EDITORIAL_ALIGNMENT", "independent_review": False,
                         "native_definition": target, "usage_definition": origin,
                         "scope": "THE_SELECTED_LION_ANIMAL_SENSE_ONLY"}
        else:
            if canonical in native:
                raise ValueError("CONCEPT_ID_COLLISION_REQUIRES_EXPLICIT_ALIGNMENT")
            reference = {"id": canonical, "owner": origin, "definition_sha256": digest(origin)}
            alignment = {"status": "EXACT_EXISTING_OWNER_ID", "usage_definition": origin}
        refs[sid] = {"id": canonical, "kind": "EXISTING_OWNER_SENSE_REFERENCE",
                     "reference": reference, "identity_alignment": alignment,
                     "admission": "DEFINITION_NOT_WORLD_INSTANCE", "external_instance_established": False}
    return refs


def run(request):
    # The graph boundary supplies only the original source and explicit context.
    from tools.lexical_training.contextual_alignment import validate_request
    if type(request) is not dict or set(request) - {"text", "source_id", "usage_context"}:
        raise ValueError("Expected source and usage context")
    p = validate_request({k: v for k, v in request.items() if k != "usage_context"})
    context = validate_context(request.get("usage_context", {}))
    raw = p["text"].encode()
    source = {"id": p["source_id"], "text": p["text"], "sha256": sha256(raw).hexdigest()}
    report = owner.acquire(p["text"], source_id=p["source_id"], **context)
    owner_status = report.get("status", "DEFER")
    status = owner_status if owner_status in {"INVALID_INPUT", "SOURCE_UNAVAILABLE", "RESOURCE_EXHAUSTED",
                                              "VERIFICATION_UNAVAILABLE", "CONFLICT"} else "DEFER"
    result = {"schema": SCHEMA, "source": source, "owner_report": report,
              "owner_report_sha256": digest(report), "concepts": [], "applications": [],
              "majaz_candidates": [], "status": status, "world_truth_established": False,
              "grammar_path_certified": False, "automatic_training_label": False}
    if report.get("source") != {"source_id": source["id"], "raw_text": source["text"],
                                 "sha256": source["sha256"], "bytes": len(raw)}:
        result["reason"] = "OWNER_SOURCE_UNAVAILABLE_OR_INVALID"
        return result
    # Exhaustion/unavailability is atomic: no partial source is certified.
    if (report["native_checked"] is not True or report["acquisition_scan_complete"] is not True
            or report.get("context", {}).get("profile_id") is None):
        result["reason"] = report.get("reason", "OWNER_WITNESS_UNAVAILABLE")
        return result
    try:
        inventory = build_inventory()
        if report["inventory_sha256"] != inventory["review_sha256"]:
            raise ValueError("SOURCE_REVIEW_CHANGED")
        references = _references(inventory)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        result["status"] = "IDENTITY_UNAVAILABLE"
        result["reason"] = "CONCEPT_IDENTITY_UNAVAILABLE:"+type(error).__name__
        return result
    result["concepts"] = list({r["id"]: r for r in references.values()}.values())
    for oi, occurrence in enumerate(report["occurrences"]):
        a, b = _span(occurrence["span"], raw)
        frame = occurrence["frame"]
        expected = {"source": source["id"], "revision": source["sha256"], "raw": source["text"],
                    "start_byte": a, "end_byte": b, "referent": context.get("subject", "unspecified"),
                    "time": context.get("time", "unspecified"), "context": context.get("context", "unspecified")}
        if frame["occurrence"] != expected:
            raise ValueError("NONLOCAL_WITNESS")
        known = {wire(atom) for atom in occurrence["native_request"]["known"]}
        local = []
        for premise in report["acquired_premises"]:
            if premise["occurrence_id"] != occurrence["occurrence_id"]:
                continue
            start, stop = _span(premise["cue_span"], raw)
            sa, sb = _span(premise["sense_span"], raw)
            if not (start <= a < b <= stop and start <= sa < sb <= stop
                    and premise["cue_span"] == occurrence["clause_span"]):
                raise ValueError("NONLOCAL_WITNESS")
            local.append(premise)
        for ci, row in enumerate(occurrence["candidates"]):
            candidate = row["candidate"]
            requirements = guard_requirements(frame, candidate)
            clean = all(_clean(r["atom"], known) for r in requirements)
            base_clean = all(_clean(r["atom"], known) for r in requirements
                             if r["atom"]["value"]["kind"] != "excludes")
            cue = any(e["sense_id"] == row["sense_id"] and e["positive"] is True for e in local)
            exclusion = any(e["sense_id"] == candidate["designation"]["sense"] and e["positive"] is False for e in local)
            accepted = (occurrence["native_checked"] is True and not occurrence["signed_conflict"]
                        and row["support_status"] == "SUPPORTED_PREMISES" and clean and cue)
            if row["use_kind"] == "figurative":
                accepted = accepted and exclusion
            bundle = {"source_id": source["id"], "source_sha256": source["sha256"],
                      "occurrence_id": digest([source["id"], source["sha256"], [a, b]]),
                      "owner_occurrence_id": occurrence["occurrence_id"], "span": deepcopy(occurrence["span"]),
                      "frame": deepcopy(frame), "concept_id": references[row["sense_id"]]["id"],
                      "concept_reference": references[row["sense_id"]]["reference"],
                      "identity_alignment": references[row["sense_id"]]["identity_alignment"],
                      "use_kind": row["use_kind"], "owner_verdict": row["support_status"],
                      "accepted": bool(accepted), "requirements": requirements,
                      "local_premises": deepcopy(local), "literal_excluded": exclusion,
                      "contextual_cue": cue, "owner_clean_support": clean,
                      "dispatch_base_ready": bool(base_clean and occurrence["native_checked"] is True
                                                  and not occurrence["signed_conflict"]),
                      "owner_result_ref": "/owner_report/occurrences/"+str(oi)+"/candidates/"+str(ci),
                      "owner_report_sha256": result["owner_report_sha256"],
                      "ceiling": "CONDITIONAL_SOURCE_USE_NOT_WORLD_TRUTH",
                      "world_truth_established": False}
            bundle["witness_id"] = digest(bundle)
            if row["use_kind"] == "figurative":
                result["majaz_candidates"].append(bundle)
            if accepted:
                result["applications"].append(bundle)
    if result["applications"] and result["status"] == "DEFER":
        result["status"] = "SCOPED_SOURCE_USE_APPLICATIONS"
    return result


def dispatch_majaz(usage, *, source, cursor, predecessor, policy=None):
    """Internal consumption after mantuq, never an externally supplied mask."""
    from .orchestration import dispatch
    if usage["source"] != source or usage["owner_report_sha256"] != digest(usage["owner_report"]):
        raise ValueError("NONLOCAL_WITNESS")
    if (predecessor.get("source_id") != source["id"] or predecessor.get("source_sha256") != source["sha256"]
            or predecessor.get("record_id") != digest({k: v for k, v in predecessor.items() if k != "record_id"})):
        raise ValueError("NONLOCAL_PREDECESSOR")
    rows = []
    for bundle in usage["majaz_candidates"]:
        if (bundle["source_id"] != source["id"] or bundle["source_sha256"] != source["sha256"]
                or bundle["owner_report_sha256"] != usage["owner_report_sha256"]
                or bundle["witness_id"] != digest({k: v for k, v in bundle.items() if k != "witness_id"})):
            raise ValueError("NONLOCAL_WITNESS")
        ready = predecessor.get("name") == "mantuq" and predecessor.get("layer") == 4 and predecessor.get("closed") is True
        mask = (int(ready and bundle["dispatch_base_ready"]) | 2 | 4 | 8
                | (16 if bundle["literal_excluded"] else 0) | (32 if bundle["contextual_cue"] else 0))
        decision = dispatch(cursor, 5, 1, mask, policy=policy)
        if decision == "DISPATCH" and not bundle["accepted"]:
            # E.g. an opposing exclusion atom: a positive bit is insufficient.
            decision = "OWNER_PREMISES_NOT_SUPPORTED"
        row = {"source_id": source["id"], "source_sha256": source["sha256"], "previous": predecessor["record_id"],
               "occurrence_id": bundle["occurrence_id"], "concept_id": bundle["concept_id"],
               "condition_mask": mask, "condition_witness": bundle["witness_id"], "dispatch": decision,
               "consumed_gate": "Nabt.LinguisticTruth.assess", "retrieved_row": bundle["owner_result_ref"],
               "owner_report_sha256": usage["owner_report_sha256"], "ceiling": bundle["ceiling"], "ceiling_merged": False}
        row["record_id"] = digest(row)
        rows.append(row)
    return {"profile": "majaz", "dispatch": "PER_OCCURRENCE" if rows else "NOT_DISPATCHED",
            "records": rows, "reason": "SOURCE_LOCAL_OWNER_WITNESSES" if rows else "NO_QUALIFIED_OWNER_CANDIDATES"}
