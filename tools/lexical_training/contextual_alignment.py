"""Occurrence-level proposals from the existing byte GRU and native concepts.

Forward and reverse trajectories share every encoder weight. Source boundaries,
all alternatives, dictionary testimony and unknowns survive neural ranking.
"""
from difflib import SequenceMatcher
from hashlib import sha256
import math
from pathlib import Path
import subprocess

from tools.grammar_catalog.operations import exact_terms
from tools import lexical_testimony as owner
from tools.evidence_lifecycle_v1 import wire
from . import concepts, shared_encoder as shared

ROOT = shared.ROOT
DIRECTORY = ROOT / "evidence/contextual_alignment_v1"
MODEL = DIRECTORY / "model.json"
SCHEMA = "nabt.shared-contextual-alignment.v1"
NULL = "__UNALIGNED__"
MAX_TERMS = 32
FEATURES = "SHARED_FORWARD_REVERSE_BYTE_BOUNDARIES_V1"


def validate_request(request):
    if type(request) is not dict or not {"text"} <= set(request) <= {"text", "source_id"}:
        raise ValueError("Expected text and optional source locator, never labels or model paths")
    text = shared.validate_request({"text": request["text"]})
    source = request.get("source_id", "input")
    if type(source) is not str or not source.strip() or len(source.encode()) > 128:
        raise ValueError("Invalid source locator")
    if len(exact_terms(text)) > MAX_TERMS:
        raise ValueError("Occurrence budget exceeded; no silent truncation")
    return {"text": text, "source_id": source}


def load_model(path=MODEL):
    if path.stat().st_size > 2_000_000:
        raise ValueError("Alignment model byte limit")
    raw = path.read_bytes()
    m = owner._strict_json(raw)
    fields = {"schema", "features", "shared_model", "alignment_labels", "alignment_weight",
              "alignment_bias", "calibration", "protocol", "training_sha256", "authority"}
    if (type(m) is not dict or set(m) != fields or m["schema"] != SCHEMA
            or m["features"] != FEATURES or m["authority"] != "NONE"):
        raise ValueError("Alignment model contract changed")
    base = shared.validate_model(m["shared_model"])
    expected = base["labels"]["concept"] + [NULL]
    if (m["alignment_labels"] != expected
            or not shared._shape(m["alignment_weight"], (len(expected), 4 * shared.HIDDEN))
            or not shared._shape(m["alignment_bias"], (len(expected),))):
        raise ValueError("Alignment labels or tensors changed")
    c = m["calibration"]
    if (type(c) is not dict or set(c) != {"min_probability", "min_margin", "validation_sha256"}
            or any(type(c[k]) not in (int,float) or not math.isfinite(c[k]) or not 0 <= c[k] <= 1
                   for k in ("min_probability", "min_margin"))
            or type(c["validation_sha256"]) is not str or len(c["validation_sha256"]) != 64
            or type(m["training_sha256"]) is not str or len(m["training_sha256"]) != 64):
        raise ValueError("Invalid fixed validation calibration")
    return m, sha256(raw).hexdigest()


def occurrence_logits(model, text):
    tokens = shared.byte_ids(text)
    base = model["shared_model"]
    forward = shared.states_for_ids(base, tokens)
    reverse = shared.states_for_ids(base, list(reversed(tokens)))
    rows = []
    for term in exact_terms(text):
        start, end = term["utf8_span"]
        vector = forward[start] + forward[end] + reverse[len(tokens)-end] + reverse[len(tokens)-start]
        scores = shared._linear(model["alignment_weight"], model["alignment_bias"], vector)
        rows.append({**term, "logits": scores})
    return rows, shared.head_logits(base, forward[-1])


def distribution(scores):
    maximum = max(scores)
    values = [math.exp(x-maximum) for x in scores]
    total = sum(values)
    return [v/total for v in values]


def decide(model, scores):
    values = distribution(scores)
    order = sorted(range(len(values)), key=lambda i: (-values[i], model["alignment_labels"][i]))
    first, second = order[:2]
    margin = values[first] - values[second]
    label = model["alignment_labels"][first]
    if label == NULL:
        status, proposed = "UNALIGNED", None
    elif values[first] < model["calibration"]["min_probability"] or margin < model["calibration"]["min_margin"]:
        status, proposed = "AMBIGUOUS", None
    else:
        status, proposed = "PROPOSED", label
    return {"status": status, "proposed_id": proposed, "top_label": label,
            "margin": margin, "softmax": values}


def _training_rows(model):
    path = DIRECTORY / "train.json"
    if path.stat().st_size > 2_000_000:
        raise ValueError("Training provenance byte limit")
    raw = path.read_bytes()
    rows = owner._strict_json(raw)
    if sha256(wire(rows).encode()).hexdigest() != model["training_sha256"]:
        raise ValueError("Training provenance changed")
    return rows


def _training_neighbors(model, text, label, rows=None):
    rows = _training_rows(model) if rows is None else rows
    candidates = [r for r in rows if any(label in a["concept_ids"] for a in r["annotations"])]
    ranked = sorted(candidates, key=lambda r: (-SequenceMatcher(None,text,r["text"]).ratio(),r["id"]))[:3]
    return [{"training_id":r["id"], "text":r["text"], "annotations":r["annotations"],
             "provenance":r["provenance"], "authority":"TRAINING_EXAMPLE_NOT_CURRENT_USE_EVIDENCE"} for r in ranked]


def align(request):
    request = validate_request(request)
    text, source = request["text"], request["source_id"]
    raw = text.encode()
    digest = sha256(raw).hexdigest()
    out = {"schema":"nabt.contextual-alignment-result.v1", "status":"DEFER", "source_id":source,
           "source_text":text, "source_sha256":digest, "utf8_hex":raw.hex(),
           "occurrences":[], "definitions":{}, "shared_heads":{}, "authority":"NONE",
           "intended_sense_established":False, "world_truth_established":False,
           "grammar_certified":False, "scope_analysis":"NOT_PERFORMED",
           "score_is_calibrated_probability":False, "unknown_means_meaningless":False,
           "next_obligation":"CHECK_CONTEXTUAL_USE_WITH_INDEPENDENT_SOURCE_WITNESS"}
    try:
        model, identity = load_model()
        catalogue = concepts.catalogue()
        definitions = {r["identity"]["id"]:{"reference":r["reference"], "testimony":r["testimony"],
                       "interpretation_scope":"INSTALLED_DICTIONARY_READING_NOT_THIS_OCCURRENCE"}
                       for r in catalogue["concepts"]}
        refs = {k:v["reference"] for k,v in definitions.items()}
        if (model["shared_model"]["concept_references"] != refs
                or set(model["shared_model"]["labels"]["concept"]) != set(refs)):
            raise ValueError("Native definitions changed since training")
        training_rows = _training_rows(model)
        rows, heads = occurrence_logits(model, text)
        for row in rows:
            decision = decide(model, row["logits"])
            start,end = row["utf8_span"]
            if raw[start:end].decode() != row["surface"]:
                raise ValueError("Occurrence byte boundary mismatch")
            identity_input = [source, digest, row["utf8_span"]]
            candidates = sorted([{"concept_id":label,"score":score,"softmax":prob,
                            "definition_pointer":"/definitions/"+label}
                           for label,score,prob in zip(model["alignment_labels"],row["logits"],decision["softmax"])
                           if label != NULL], key=lambda r:(-r["score"],r["concept_id"]))
            out["occurrences"].append({"occurrence_id":sha256(wire(identity_input).encode()).hexdigest(),
                 "surface":row["surface"], "codepoint_span":row["codepoint_span"], "utf8_span":row["utf8_span"],
                 "source_sha256":digest,"status":decision["status"],"proposed_id":decision["proposed_id"],
                 "margin":decision["margin"], "unaligned_score":row["logits"][-1],
                 "candidates":candidates, "training_neighbors":_training_neighbors(model,text,decision["proposed_id"],training_rows)
                        if decision["proposed_id"] else [],
                 "alignment_evidence":"LEARNED_CONTEXT_PROPOSAL_WITH_EXACT_SOURCE_BINDING"})
        out.update(status="PROPOSED" if any(r["proposed_id"] for r in out["occurrences"]) else "UNALIGNED",
                   definitions=definitions, model_sha256=identity, training_sha256=model["training_sha256"],
                   calibration=model["calibration"], features=FEATURES,
                   all_installed_concepts_retained=True,
                   shared_heads={h: [{"label":label,"score":score} for label,score in
                                 zip(model["shared_model"]["labels"][h],values)] for h,values in heads.items()})
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        out.update(status="DEFER", reason=type(error).__name__, occurrences=[], definitions={}, shared_heads={})
    return out


def observe_lesson(adapter, payload):
    if adapter == "source_learning":
        sources = [(r["id"],r["text"],f"/payload/sources/{i}/text") for i,r in enumerate(payload["sources"])]
    elif adapter == "qualified_inference":
        sources = [(payload["source_id"],payload["source_text"],"/payload/source_text")]
    else:
        return {"status":"UNMAPPED_INPUT_CONTRACT","observations":[],"owner_evidence_modified":False}
    rows=[]
    for index,(source,text,pointer) in enumerate(sources):
        row={"source_id":source,"source_text":text,"input_pointer":pointer,
             "source_sha256":sha256(text.encode()).hexdigest(),"proposal":None}
        if index >= 8 or len(text.encode()) > shared.MAX_BYTES or len(exact_terms(text)) > MAX_TERMS:
            row["status"]="NEURAL_BUDGET_DEFER"
        else:
            row["proposal"]=align({"text":text,"source_id":source})
            row["status"]=row["proposal"]["status"]
        rows.append(row)
    return {"status":"OBSERVED" if all(r["status"] in ("PROPOSED","UNALIGNED") for r in rows) else "PARTIAL",
            "observations":rows,"owner_evidence_modified":False,
            "concept_alignment":"LEARNED_OCCURRENCE_PROPOSALS_WITH_CANONICAL_DEFINITIONS",
            "revision_owner":"EXISTING_OWNER_HISTORY_AND_ACTIVE_SOURCES"}
