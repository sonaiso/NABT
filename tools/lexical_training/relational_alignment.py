"""Optional sense ranking on the existing GRU; Lean owns every schema edge.

No neural output supplies an occurrence binding, lexical license or evidence.
The public caller cannot choose a checkpoint or prune competing meanings.
"""
from hashlib import sha256
import json
import subprocess

from tools import lexical_testimony, explainable_pilot
from tools.evidence_lifecycle_v1 import ResourceLimit
from tools.grammar_catalog.relational_bridge import schema_catalogue
from . import shared_encoder as shared
from .contextual_alignment import occurrence_vectors, validate_request

MODEL = shared.ROOT / "evidence/ontological_continuity_v1/training/model.json"
SCHEMA = "nabt.relational-neural-ranking.v1"
NULL = "__UNALIGNED__"
DIM = 4 * shared.HIDDEN


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def definitions(catalogue):
    meanings = {}
    for row in catalogue["schemas"]:
        sense, schema = row["schema"]["sense"], row["schema"]
        if sense in meanings and meanings[sense] != schema:
            raise ValueError("Same sense has incompatible installed schemas")
        meanings[sense] = schema
    return meanings


def load_model(base_sha, meanings):
    if MODEL.stat().st_size > 2_000_000:
        raise ValueError("Ranking model size exceeded")
    raw = MODEL.read_bytes(); model = lexical_testimony._strict_json(raw)
    fields = {"schema", "authority", "shared_model_sha256", "schema_sha256", "labels", "mean", "scale",
              "weight", "bias", "protocol", "training_sha256"}
    labels = list(meanings) + [NULL]
    if (type(model) is not dict or set(model) != fields or model["schema"] != SCHEMA
            or model["authority"] != "NONE" or model["shared_model_sha256"] != base_sha
            or model["schema_sha256"] != digest(meanings) or model["labels"] != labels
            or not shared._shape(model["mean"], (DIM,)) or not shared._shape(model["scale"], (DIM,))
            or min(model["scale"]) <= 0 or not shared._shape(model["weight"], (len(labels), DIM))
            or not shared._shape(model["bias"], (len(labels),))):
        raise ValueError("Ranking model or canonical schema identity changed")
    training = MODEL.with_name("train.json")
    if training.stat().st_size > 2_000_000 or digest(lexical_testimony._strict_json(training.read_bytes())) != model["training_sha256"]:
        raise ValueError("Ranking training provenance changed")
    return model, sha256(raw).hexdigest()


def logits(model, vector):
    x = [(v-m)/s for v,m,s in zip(vector, model["mean"], model["scale"], strict=True)]
    return shared._linear(model["weight"], model["bias"], x)


def rank(request):
    out = {"schema":SCHEMA, "status":"DEFER", "authority":"NONE", "occurrences":[],
           "all_installed_meanings_retained":False, "bindings_generated":False,
           "world_truth_established":False, "grammar_certified":False,
           "hidden_coordinates_are_semantically_interpretable":False,
           "deployment_status":"EXPERIMENTAL_NOT_PROMOTED_BACKGROUND_ERRORS"}
    try:
        p = validate_request(request)
        base, base_sha = shared.load_model()
        meanings = definitions(schema_catalogue())
        model, identity = load_model(base_sha, meanings)
        vectors, _ = occurrence_vectors(base, p["text"])
        for row in vectors:
            scores = logits(model, row["vector"])
            top = max(range(len(scores)), key=lambda i: (scores[i], -i))
            out["occurrences"].append({**{k:v for k,v in row.items() if k != "vector"},
                "top_label":model["labels"][top], "unaligned_score":scores[-1],
                "candidates":sorted([{"sense":sense, "score":scores[i],
                                      "ontological_signature":meanings[sense]}
                                     for i,sense in enumerate(meanings)], key=lambda r:(-r["score"], r["sense"]))})
        out.update(status="PROPOSED", all_installed_meanings_retained=True, model_sha256=identity,
                   source_sha256=sha256(p["text"].encode()).hexdigest(), schema_sha256=model["schema_sha256"],
                   shared_model_sha256=base_sha, training_sha256=model["training_sha256"],
                   feature_kind="EXISTING_SHARED_GRU_FORWARD_REVERSE_BOUNDARIES_96")
    except (OSError, ValueError, KeyError, ResourceLimit, subprocess.SubprocessError, explainable_pilot.PilotError) as error:
        out.update(reason=type(error).__name__, occurrences=[])
    return out
