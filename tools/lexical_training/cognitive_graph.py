"""Two linked graph views over one shared encoder and the existing owners.

The sign view contains exact occurrences, never lexical identities copied into
another registry. The concept view uses native definition IDs. Candidate edges
cannot license a reading, world claim, causal role, or evidence application.
"""
from hashlib import sha256
from copy import deepcopy

from nabt.alphabet import parse_word, render_word, ALPHABET_ID
from nabt.errors import NabtError
from nabt.machine import Machine
from tools.evidence_lifecycle_v1 import wire
from tools.grammar_catalog.operations import exact_terms
from tools.grammar_catalog import relational
from . import contextual_alignment as alignment, shared_encoder as shared
from .rag_views import VIEWS

DIRECTORY = shared.ROOT / "evidence/cognitive_graph_v1"
MODEL = DIRECTORY / "model.json"
TRAIN = DIRECTORY / "train.json"

# Crosswalk to existing RAG views only; not proof ownership or new rule laws.
# Missing numbers in the supplied ledger are retained, never guessed.
DECOMPOSITIONS = {
    1: ("الدال والترخيص المتدرج", ("trace", "sound", "orthography", "cells", "graded"), "WORD_SHAPE_AND_SOURCE_TRACE"),
    2: ("أقسام المدلول", ("genera", "lexicon"), "CLASSIFICATION_ACQUISITION_OPEN"),
    4: ("اللفظ والدلالات", ("indications", "understanding"), "SENSE_PROPOSALS_NATIVE_DEFINITIONS"),
    5: ("التركيب", ("syntax",), "EXISTING_OWNER_RESULTS"),
    6: ("العوامل", ("syntax",), "EXISTING_OWNER_RESULTS"),
    7: ("النسب", ("restriction", "indications"), "GENERAL_RELATION_ACQUISITION_OPEN"),
    8: ("الأدوار والسببية", ("inference", "world"), "EXISTING_OWNER_RESULTS_NO_CAUSAL_PROMOTION"),
    9: ("العلامات الإعرابية", ("syntax", "morphology"), "EXISTING_OWNER_RESULTS"),
    10: ("المقام", ("usage", "speech_act"), "GENERAL_CONTEXT_ACQUISITION_OPEN"),
    11: ("الزمان والمكان", ("quantity",), "EXISTING_OWNER_RESULTS"),
    12: ("الأجناس والخواص والقابليات", ("genera", "world"), "SCOPED_ONTOLOGY_BRIDGE_REQUIRED"),
    13: ("الإفادة", ("understanding", "speech_act"), "GENERAL_IFADAH_ACQUISITION_OPEN"),
}


def coverage():
    views = {name: {"id": name, "title_ar": title, "owner_families": list(families)}
             for name, title, families in VIEWS}
    return [{"number": i, "name_ar": DECOMPOSITIONS[i][0],
             "views": [views[k] for k in DECOMPOSITIONS[i][1]],
             "connection": DECOMPOSITIONS[i][2], "whole_decomposition_learned": False}
            if i in DECOMPOSITIONS else {"number": i, "status": "NOT_SPECIFIED_IN_SUPPLIED_LEDGER"}
            for i in range(1, 15)]


def sign_nodes(text, source_id):
    raw = text.encode(); digest = sha256(raw).hexdigest()
    machines = {mode: Machine(mode) for mode in ("wasl", "waqf")}
    nodes = []
    try:
        cell_model, cell_sha = shared.load_cell_model()
        cell_error = None
    except (OSError, ValueError) as error:
        cell_model, cell_sha, cell_error = None, None, type(error).__name__
    for term in exact_terms(text):
        identity = sha256(wire([source_id, digest, term["utf8_span"]]).encode()).hexdigest()
        row = {"id": identity, "kind": "WRITTEN_OCCURRENCE", **term,
               "source_sha256": digest, "a116": {"status": "DEFER", "alphabet_id": ALPHABET_ID}}
        try:
            cells = parse_word(term["surface"])
            if render_word(cells) != term["surface"]:
                raise ValueError("Strict reader did not restore original surface")
            row["a116"].update(status="REPRESENTED", cells=list(cells),
                                 reading_modes={mode: machine.analyse(cells).as_dict() for mode, machine in machines.items()},
                                 lexical_attestation_established=False, intended_sense_established=False)
            row['cell_neural'] = {'status':'DEFER', 'model_sha256':cell_sha,
                'authority':'NONE', 'model_error':cell_error}
            if cell_model is not None and len(cells)<=64:
                scores=shared.cell_logits(cell_model,cells)
                row['cell_neural'].update(status='PROPOSED',input_ids=shared.cell_ids(cells),
                    kernel_cells_ref='/a116/cells',alphabet_id=ALPHABET_ID,
                    heads={h:[{'label':label,'score':score} for label,score in
                        zip(cell_model['labels'][h],scores[h])] for h in scores})
        except NabtError as error:
            row["a116"].update(error.as_dict())
        nodes.append(row)
    return nodes


def validate_request(request):
    if type(request) is not dict or set(request) - {"text", "source_id", "lexical_text", "context", "usage_context"}:
        raise ValueError("Expected source and existing linguistic owner inputs")
    source = alignment.validate_request({k: v for k, v in request.items() if k in {"text", "source_id"}})
    p = {**deepcopy(request), **source}
    if "lexical_text" in p and (type(p["lexical_text"]) is not str or len(p["lexical_text"].encode()) > 131072):
        raise ValueError("Expected bounded lexical evidence text")
    if "context" in p:
        from nabt.discourse_context import read_context
        read_context(p["context"])
    if "usage_context" in p:
        from tools.grammar_catalog.usage_witness import validate_context
        validate_context(p["usage_context"])
    relational.validate({k: v for k, v in p.items() if k != "usage_context"})
    return p


def analyze(request):
    request = validate_request(request)
    text, source_id = request["text"], request["source_id"]
    nodes = sign_nodes(text, source_id)
    proposal = alignment.align({"text": text, "source_id": source_id}, model_path=MODEL, training_path=TRAIN)
    # Preserve the original syntactic/temporal/relational owner's report in full.
    relations = relational.analyze({k: v for k, v in request.items() if k != "usage_context"})
    definitions = proposal["definitions"]
    concepts = [{"id": key, "kind": "NATIVE_CONCEPT_DEFINITION", **definition,
                 "admission": "DEFINITION_CANDIDATE_NOT_GROUNDED_APPLICATION",
                 "external_instance_established": False} for key, definition in definitions.items()]
    occurrence_ids = {r["id"] for r in nodes}
    edges = []
    for index, occurrence in enumerate(proposal["occurrences"]):
        if occurrence["occurrence_id"] not in occurrence_ids:
            raise ValueError("Neural occurrence detached from sign graph")
        for candidate in occurrence["candidates"]:
            if candidate["concept_id"] not in definitions:
                raise ValueError("Candidate refers to a foreign definition")
            edges.append({"source": occurrence["occurrence_id"], "target": candidate["concept_id"],
                          "relation": "CANDIDATE_DENOTATION", "score": candidate["score"],
                          "proposed": candidate["concept_id"] == occurrence["proposed_id"],
                          "accepted": False, "evidence_pointer": "/neural_observation/occurrences/" +
                          str(index),
                          "missing": ["OCCURRENCE_INTERPRETATION_WITNESS"]})
    source = {"id": source_id, "text": text, "sha256": sha256(text.encode()).hexdigest(),
              "utf8_hex": text.encode().hex(), "unicode_scalars": [ord(c) for c in text]}
    if relations["source_sha256"] != source["sha256"]:
        raise ValueError("Relational owner changed the source binding")
    result = {"schema": "nabt.cognitive-graph.v1", "status": "PARTIAL" if proposal["status"] == "DEFER" else "PROPOSALS_WITH_OWNER_RESULTS",
            "deployment": "EXPERIMENTAL_NOT_DEFAULT_ALIGNMENT_REPLACEMENT",
            "source": source, "sign_graph": {"nodes": nodes},
            "concept_graph": {"nodes": concepts, "admitted_concept_applications": [],
                              "grounded_world_claims": []},
            "alignment_edges": edges, "neural_observation": proposal,
            "relational_owner": relations, "decompositions": coverage(),
            "shared_encoder_heads": list(shared.HEADS) + ["occurrence_alignment"],
            "acceptance": {"status": "DEFER", "reasons": [
                "NEURAL_ALIGNMENT_IS_A_PROPOSAL", "SOURCE_INTERPRETATION_AND_WORLD_GROUNDING_REQUIRE_OWNERS"],
                "unknown_is_meaningless": False, "absence_of_evidence_is_negation": False,
                "all_fourteen_learned": False, "world_truth_established": False,
                "audio_learning_established": False, "authority": "NONE"}}
    if "usage_context" in request:
        from tools.grammar_catalog.usage_witness import run
        usage = run({"text": text, "source_id": source_id, "usage_context": request["usage_context"]})
        result["usage_witness"] = usage
        existing = {c["id"] for c in concepts}
        concepts.extend(c for c in usage["concepts"] if c["id"] not in existing)
        result["concept_graph"]["source_use_applications"] = deepcopy(usage["applications"])
        result["acceptance"]["source_use_application_count"] = len(usage["applications"])
        result["acceptance"]["source_use_is_world_grounding"] = False
    return result


def observe_lesson(adapter, payload):
    return alignment.observe_lesson(adapter, payload, analyzer=analyze)
