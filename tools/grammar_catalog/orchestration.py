"""Source-local, deterministic dispatch over installed owners, not a truth oracle.

The finite Lean policy orders *admission* stages. Each stage retains the full
owner report and alternatives. No request-supplied check or confidence is used.
S/C/M/G/A are views, not five independent identities or newly trained networks.
"""
from copy import deepcopy
from hashlib import sha256
import json
import re

from tools.evidence_lifecycle_v1 import _encoded, wire, MAX_INTEGER
from .operations import ROOT, digest
from tools.lexical_training.rag_views import inventory, VIEWS

TABLE = ROOT / "evidence/cognitive_orchestration_v1/dispatch.json"
TABLE_SHA256 = "f52fb14785169c50c4b802923847c91646667125d8a14bf8f727a85f259a2d90"
SCHEMA = "nabt.cognitive-orchestration.v1"


def table():
    raw = TABLE.read_bytes()
    if sha256(raw).hexdigest() != TABLE_SHA256:
        raise ValueError("STALE_DISPATCH_TABLE")
    value = json.loads(raw)
    if [r["id"] for r in value["views"]] != [r[0] for r in VIEWS]:
        raise ValueError("DISPATCH_VIEW_IDENTITY_DRIFT")
    return value


def dispatch(cursor, layer, profile, mask, *, policy=None):
    """Internal finite policy. Public callers cannot supply mask or policy."""
    if any(type(n) is not int for n in (cursor, layer, profile, mask)):
        raise ValueError("Dispatch coordinates must be canonical integers")
    if not (0 <= cursor < 6 and 0 <= layer < 6 and 0 <= profile < 4 and 0 <= mask < 256):
        raise ValueError("Dispatch coordinates outside frozen domain")
    p = table() if policy is None else policy
    if not p["stage_gate"][cursor][layer]:
        return "LAYER_SKIPPED"
    if not mask & 1:
        return "DISPATCH_WITHOUT_CONDITION"
    if not mask & 2:
        return "DISPATCH_WITHOUT_ROW"
    if not mask & 4:
        return "NONLOCAL_WITNESS"
    if not mask & 8:
        return "CEILING_PROMOTION"
    if not p["condition_gate"][profile][mask]:
        return ("DISPATCH_WITHOUT_CONDITION", "MAJAZ_BEFORE_TAADTHUR_OR_QARINA",
                "ANALOGY_SCOPE_WITNESS_MISSING", "DIVISION_TYPED_WITNESS_MISSING")[profile]
    return "DISPATCH"


def validate(request):
    if type(request) is not dict or "text" not in request or set(request) - {
            "text", "source_id", "lexical_text", "context", "mode", "usage_context"}:
        raise ValueError("Expected source and installed owner inputs; caller licenses are forbidden")
    _encoded(request, 262144)
    from tools.lexical_training.contextual_alignment import validate_request
    validate_request({"text": request["text"]})
    sid = request.get("source_id", "input")
    if type(sid) is not str or len(sid.encode()) > 128 or re.fullmatch(r"[a-z][a-z0-9_]*", sid) is None:
        raise ValueError("Expected bounded source identity")
    if request.get("mode", "wasl") not in ("wasl", "waqf"):
        raise ValueError("Unknown reading mode")
    if "lexical_text" in request and (type(request["lexical_text"]) is not str or len(request["lexical_text"].encode()) > 131072):
        raise ValueError("Expected bounded lexical evidence text")
    if "context" in request and type(request["context"]) is not dict:
        raise ValueError("Expected existing discourse context")
    if "usage_context" in request:
        from .usage_witness import validate_context
        validate_context(request["usage_context"])
    return deepcopy(request)


def _local(report, source):
    if report.get("source_id") != source["id"] or report.get("source_sha256") != source["sha256"]:
        raise ValueError("NONLOCAL_WITNESS")


def _shape(p, source):
    from tools.arabic_training.unit_composition import execute
    result = execute({"op": "source", "text": p["text"], "source_id": source["id"],
                      "mode": p.get("mode", "wasl")})
    body = result["result"]; _local(body, source)
    runs = body["written_runs"]
    words = [w for r in runs for w in r["owner_result"].get("words", [])]
    closed = bool(runs) and all(r["owner_result"].get("words") for r in runs) and all(
        w.get("native_receipt", {}).get("sound_shape_accepted") is True and
        w.get("acquisition_owner", {}).get("verified") is True for w in words)
    closed = closed and body.get("source_restored") is True and body.get("word_boundaries_preserved") is True
    closed = closed and all(s["kind"] in ("written_run", "spacing", "punctuation") for s in body["segments"])
    # Long, valid words have exact unit numbers beyond JSON's portable integer
    # range. Preserve the *complete* original owner wire without changing its
    # integer values or weakening the external gateway's numeric contract.
    def large(value):
        if type(value) is int:return abs(value)>MAX_INTEGER
        if type(value) is dict:return any(large(v) for v in value.values())
        if type(value) is list:return any(large(v) for v in value)
        return False
    if large(result):
        from tools.arabic_training.unit_composition import wire as exact_wire
        raw=exact_wire(result)
        result={'schema':'nabt.exact-unit-owner-transport.v1','source_id':source['id'],
                'source_sha256':source['sha256'],'owner_json':raw,
                'owner_json_sha256':sha256(raw.encode()).hexdigest(),
                'transport_reason':'EXACT_UNIT_INTEGER_EXCEEDS_PORTABLE_JSON_RANGE'}
    return result, closed


def _lexical(p, source):
    from nabt.corpus_evidence import learn_qac_lexicon
    from nabt.inflection_reader import read_inflection
    text = p.get("lexical_text")
    model = learn_qac_lexicon(text.encode(), source_id="orchestration_lexical_evidence") if text else None
    report = read_inflection(p["text"], source_id=source["id"], lexical_model=model)
    _local(report, source)
    def licensed(r):
        # Particle rows have their own installed source-rule support.
        return (not r.get("annotation_only", False) and not r.get("obligations", []) and
                (bool(r.get("support_records")) or (r.get("operator_qualified") is True and bool(r.get("operator_rule")))) and
                r.get("segmentation", {}).get("licensed") is True)
    occurrences = report["occurrences"]
    closed = bool(occurrences) and all(any(licensed(r) for r in o["readings"]) for o in occurrences)
    return report, closed, model


def _syntax(p, source, model):
    from nabt.discourse_reader import read_discourse
    report = read_discourse(p["text"], source_id=source["id"], lexical_model=model, context=p.get("context"))
    _local(report, source)
    closed = bool(report["clauses"]) and all(c["status"] == "LICENSED" and any(
        a["licensed_syntax"] and not a["rejected_candidate"] for a in c["analyses"]) for c in report["clauses"])
    return report, closed


def run(request, *, _recover=True):
    p = validate(request); policy = table()
    source = {"id": p.get("source_id", "input"), "text": p["text"],
              "sha256": sha256(p["text"].encode()).hexdigest()}
    views = {v["id"]: v for v in inventory()["views"]}
    reports = {}; ledger = []; cursor = 0; model = None; graph = None
    for layer, name in enumerate(policy["layers"]):
        # word_kind is an existing projection of morphology, not a nineteenth RAG.
        selected = [v for v in policy["views"] if v["layer"] == layer]
        if layer == 2:
            selected = [v for v in policy["views"] if v["id"] == "morphology"]
        rows = [views[v["id"]] for v in selected]
        previous = ledger[-1]["record_id"] if ledger else digest(source)
        mask = int(layer == 0 or ledger[-1]["closed"]) | (2 if rows else 0) | 4 | 8
        decision = dispatch(cursor, layer, 0, mask, policy=policy)
        if decision != "DISPATCH":
            raise ValueError(decision)
        if layer == 0:
            result, closed = _shape(p, source)
            ceiling = "NATIVE_REPLAYED_SOURCE_REPRESENTATION_AND_WORD_SHAPE"
        elif layer == 1:
            result, closed, model = _lexical(p, source)
            ceiling = "CONDITIONAL_SOURCE_LEXICAL_ALTERNATIVES"
        elif layer == 2:
            result = {"source_id": source["id"], "source_sha256": source["sha256"],
                      "owner_report_ref": "/owner_reports/morphology",
                      "occurrences": [{"id": o["occurrence_id"], "kinds": sorted({r["kind"] for r in o["readings"]})}
                                      for o in reports["morphology"]["occurrences"]]}
            closed = bool(result["occurrences"]) and all(o["kinds"] and set(o["kinds"]) <= {"noun", "verb", "particle"} for o in result["occurrences"])
            ceiling = "CONDITIONAL_SOURCE_WORD_KINDS"
        elif layer == 3:
            result, closed = _syntax(p, source, model)
            ceiling = "SOURCE_RELATIVE_SYNTAX_WITH_ALTERNATIVES"
        elif layer == 4:
            owner = reports["syntax"]
            result = {"source_id": source["id"], "source_sha256": source["sha256"],
                      "owner_report_ref": "/owner_reports/syntax", "claims": deepcopy(owner["claims"]),
                      "speech_acts": [{"clause_id": c["clause_id"], "force": c["force"], "span": c["span"]} for c in owner["clauses"]],
                      "assertion_is_external_truth": False, "request_is_event_occurrence": False}
            closed = all(c["force"] != "AMBIGUOUS" and any(a["references_complete"] and a["licensed_syntax"]
                         and not a["rejected_candidate"] for a in c["analyses"]) for c in owner["clauses"])
            ceiling = "SOURCE_RELATIVE_MANTUQ_PROJECTION_NOT_WORLD_TRUTH"
        else:
            from tools.lexical_training.cognitive_graph import analyze
            graph = analyze({"text": p["text"], "source_id": source["id"],
                             **{k: p[k] for k in ("lexical_text", "context", "usage_context") if k in p}})
            result = graph; closed = False
            ceiling = "NEURAL_DEFINITION_PROPOSALS_NOT_GROUNDED_APPLICATIONS"
        reports[name] = result
        record = {"layer": layer, "name": name, "dispatch": decision, "source_sha256": source["sha256"],
                  "source_id": source["id"], "previous": previous, "condition_mask": mask,
                  "condition_witness": previous, "retrieved_rows": rows,
                  "retrieved_rows_sha256": digest(rows), "consumed_gate": name,
                  "owner_result_ref": "/owner_reports/"+name, "owner_result_sha256": digest(result),
                  "ceiling": ceiling, "ceiling_merged": False, "closed": bool(closed),
                  "result": "CLOSED_WITHIN_OWNER_SCOPE" if closed else "DEFER"}
        record["record_id"] = digest(record); ledger.append(record)
        if not closed:
            break
        cursor += 1
    ids = [n["id"] for n in graph["concept_graph"]["nodes"]] if graph else []
    networks = [{"id": network, "view_ids": [v["id"] for v in policy["views"] if network in v["networks"]],
                 "concept_ids_ref": "/canonical_concept_ids", "new_concept_ids": [],
                 "learned_separate_network": False} for network in ("S", "C", "M", "G", "A")]
    special = [{"profile": profile, "dispatch": "NOT_DISPATCHED",
                "reason": "OWNER_TO_CONDITION_BUNDLE_BRIDGE_OPEN"} for profile in policy["profiles"][1:]]
    if graph is not None and "usage_witness" in graph:
        from .usage_witness import dispatch_majaz
        special[0] = dispatch_majaz(graph["usage_witness"], source=source, cursor=5,
                                   predecessor=ledger[-2], policy=policy)
    result = {"schema": SCHEMA, "status": "DEFER", "source": source,
            "orchestrator": {"id": "truth-interpretation-dispatch", "kind": "CONTROL_OPERATOR",
                             "concept_id": None, "trainable_parameters": 0, "law_id": policy["law_id"],
                             "table_sha256": TABLE_SHA256},
            "canonical_concept_ids": ids, "networks": networks,
            "view_bindings": policy["views"], "dispatch_ledger": ledger, "owner_reports": reports,
            "stopped_at": ledger[-1]["name"], "unexecuted_layers": policy["layers"][len(ledger):],
            "special_gates": special,
            "awamil": {"count": policy["awamil_count"], "partition": policy["awamil_partition"],
                       "speech_partition_82_18_established": False, "pruned_by_speech_type": False},
            "learning_records": {"refs": [r["record_id"] for r in ledger],
                "unreviewed_records_are_labels": False, "automatic_weight_update": False},
            "world_truth_established": False, "all_eighteen_mastered": False,
            "open_obligations": ["OCCURRENCE_INTERPRETATION_AND_GROUNDED_CONCEPT_APPLICATION",
                "GENERAL_ARABIC_USE_ACQUISITION_AND_WORLD_GROUNDING",
                "ANALOGY_DIVISION_OWNER_BUNDLE_BRIDGES", "INDEPENDENT_REVIEW_BEFORE_TRAINING"]}
    if _recover:
        from tools.arabic_training.source_reading import analyze as read_source
        recovery = read_source(p['text'],source_id=source['id'],lexical_text=p.get('lexical_text'),
                               mode=p.get('mode','wasl'))
        result['source_reading'] = recovery
        result['conditional_readings'] = []
        if result['stopped_at']=='orthography':
            for candidate in recovery['derived_sources']:
                derived_id='reading_'+digest([source['id'],source['sha256'],candidate['sha256']])[:32]
                # The original ledger remains DEFER. Each derived source must
                # start again at orthography; this cannot open an upper gate for
                # the unmarked parent or copy occurrence-local usage witnesses.
                # Discourse context declares entities/participants, without
                # source offsets. Replay those premises on the new text.
                # Usage witnesses, in contrast, bind exact source occurrences.
                branch={k:v for k,v in p.items() if k not in {'text','source_id','usage_context'}}
                branch.update(text=candidate['text'],source_id=derived_id)
                result['conditional_readings'].append({'reading':candidate,'source_id':derived_id,
                    'parent_claim_promoted':False,'withheld_parent_context':['usage_context'],
                    'result':run(branch,_recover=False)})
    return result


def verify(report, *, expected_request):
    if type(report) is not dict or any(
            n.get("concept_ids_ref") != "/canonical_concept_ids" or n.get("new_concept_ids") != []
            for n in report.get("networks", [])):
        return {"valid": False, "code": "CONCEPT_COPIED_BY_DOMAIN", "semantic_rank_promoted": False}
    return {"valid": wire(report) == wire(run(expected_request)),
            "method": "FRESH_OWNER_REPLAY_FROM_INDEPENDENT_REQUEST", "semantic_rank_promoted": False}
