"""Advisory pedagogical readouts on NABT's unchanged frozen byte GRU.

This internal owner consumes text only. Installed input/domain/authority owners,
not these scores, decide which operation may run and what evidence supports it.
Runtime inference uses the existing portable encoder and Python's standard library.
"""
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
import math
from pathlib import Path

from tools.evidence_lifecycle_v1 import ResourceLimit, strict_loads
from . import shared_encoder as shared, witness_recall

SCHEMA = "nabt.ntl-apprentice-proposal.v1"
MODEL_SCHEMA = "nabt.ntl-apprentice-readouts.v1"
RELEASE_POLICY = "REVIEW_ONLY"
MODEL = Path(__file__).with_name("data") / "ntl_apprentice_model_v1.json"
MODEL_SHA256 = "53a07b32d0c990ab50761dd08f4192731387b1e2fff42de83dc97533c9b9e307"
ENCODER_SHA256 = "d472287d1a04296001e5fa3d64c0686e4ddef940ce121218ee486e0448b5b12c"
FEATURES = "witness_recall.vector/SHARED_FORWARD_REVERSE_BYTE_BOUNDARIES_V1/train_standardized"
DIM = witness_recall.DIM
MAX_TEXT_BYTES, MAX_MODEL_BYTES = 2048, 250_000
ACTIONS = ("request_evidence", "compare_measurements", "inspect_causal_design",
           "inspect_source", "compare_perspectives", "seek_counterexample", "independent_transfer")
OBLIGATIONS = ("identity", "complete_observation", "time_and_unit", "precision", "causal_design",
               "source_support", "counterevidence", "scope", "perspectives", "transfer")


def _unit(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1


def validate_model(model):
    fields = {"schema", "authority", "encoder_sha256", "features", "dimension", "actions",
              "obligations", "feature_mean", "feature_scale", "action_weights", "obligation_weights",
              "calibration", "training_sha256", "development_sha256", "protocol_sha256", "fit"}
    if (type(model) is not dict or set(model) != fields or model["schema"] != MODEL_SCHEMA
            or model["authority"] != "NONE" or model["encoder_sha256"] != ENCODER_SHA256
            or model["features"] != FEATURES or type(model["dimension"]) is not int
            or model["dimension"] != DIM or model["actions"] != list(ACTIONS)
            or model["obligations"] != list(OBLIGATIONS)):
        raise ValueError("Apprentice model contract differs")
    for name in ("training_sha256", "development_sha256", "protocol_sha256"):
        value = model[name]
        if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("Invalid training identity")
    if (not shared._shape(model["feature_mean"], (DIM,))
            or not shared._shape(model["feature_scale"], (DIM,))
            or any(v <= 0 for v in model["feature_scale"])
            or not shared._shape(model["action_weights"], (len(ACTIONS), DIM + 1))
            or type(model["obligation_weights"]) is not dict
            or set(model["obligation_weights"]) != set(OBLIGATIONS)
            or any(not shared._shape(w, (2, DIM + 1)) for w in model["obligation_weights"].values())):
        raise ValueError("Invalid finite readout tensors")
    calibration = model["calibration"]
    if (type(calibration) is not dict or set(calibration) != {"min_action_score", "min_action_margin",
            "obligation_thresholds", "selection", "calibrated_probabilities"}
            or not _unit(calibration["min_action_score"]) or not _unit(calibration["min_action_margin"])
            or calibration["selection"] != "DEVELOPMENT_ONLY_FIXED_GRID"
            or calibration["calibrated_probabilities"] is not False
            or type(calibration["obligation_thresholds"]) is not dict
            or set(calibration["obligation_thresholds"]) != set(OBLIGATIONS)
            or any(not _unit(x) for x in calibration["obligation_thresholds"].values())):
        raise ValueError("Invalid development thresholds")
    if (type(model["fit"]) is not dict or model["fit"].get("encoder_updated") is not False
            or model["fit"].get("method") != "MASKED_CLASS_BALANCED_RIDGE"
            or model["fit"].get("target_true_false_order") != [False, True]):
        raise ValueError("Invalid fit contract")
    return model


@lru_cache(maxsize=2)
def _decode(model_bytes, encoder_bytes):
    if sha256(model_bytes).hexdigest() != MODEL_SHA256:
        raise ValueError("APPRENTICE_MODEL_IDENTITY_CHANGED")
    if sha256(encoder_bytes).hexdigest() != ENCODER_SHA256:
        raise ValueError("ENCODER_IDENTITY_CHANGED")
    model = validate_model(strict_loads(model_bytes, maximum_bytes=MAX_MODEL_BYTES, report=True))
    encoder = shared.validate_model(strict_loads(encoder_bytes, maximum_bytes=2_000_000, report=True))
    return model, encoder


def load():
    if MODEL.stat().st_size > MAX_MODEL_BYTES or shared.MODEL.stat().st_size > 2_000_000:
        raise ValueError("Installed model exceeds budget")
    return _decode(MODEL.read_bytes(), shared.MODEL.read_bytes())


def vector_scores(model, vector):
    """Portable readout shared by runtime and the independent NumPy parity check."""
    if len(vector) != DIM or any(type(x) not in (int, float) or not math.isfinite(x) for x in vector):
        raise ValueError("Invalid encoder vector")
    x = [(v - mean) / scale for v, mean, scale in
         zip(vector, model["feature_mean"], model["feature_scale"], strict=True)]
    action = witness_recall.distribution(model["action_weights"], x)
    obligations = {name: witness_recall.distribution(model["obligation_weights"][name], x)[1]
                   for name in OBLIGATIONS}
    return action, obligations


def decide(model, vector):
    action_scores, obligation_scores = vector_scores(model, vector)
    ranked = sorted(zip(ACTIONS, action_scores, strict=True), key=lambda pair: (-pair[1], pair[0]))
    top, second = ranked[:2]
    calibration = model["calibration"]
    margin = top[1] - second[1]
    reason = ("TIED_ACTION_SCORES" if abs(margin) <= 1e-12 else
              "BELOW_DEVELOPMENT_THRESHOLD" if top[1] < calibration["min_action_score"]
              or margin < calibration["min_action_margin"] else None)
    return {"status": "DEFER" if reason else "PROPOSED", "action": None if reason else top[0],
            "forced_action": top[0],
            "action_ranking": [{"label": label, "score": score} for label, score in ranked],
            "action_margin": margin, "abstention_reason": reason,
            "obligations": {name: score >= calibration["obligation_thresholds"][name]
                            for name, score in obligation_scores.items()},
            "obligation_scores": obligation_scores}


def propose(text):
    """Propose from text; never accept a model path, answer key, role or permission."""
    result = {"schema": SCHEMA, "status": "INPUT_DEFER", "authority": "NONE",
              "release_policy": RELEASE_POLICY, "automatic_selection_permitted": False,
              "action": None, "forced_action": None, "action_ranking": [],
              "obligations": dict.fromkeys(OBLIGATIONS), "obligation_scores": {},
              "permissions_granted": [], "means_executed": [], "owner_evidence_modified": False,
              "encoder_updated": False, "semantic_authority": "NONE", "world_truth_established": False,
              "human_mastery_established": False, "score_is_probability_of_correctness": False,
              "out_of_domain_detection_established": False,
              "limits": ["First frozen evaluation failed release for automatic selection; proposals are for review only.",
                         "Learned action and obligation suggestions only; independent domain/input gates are required.",
                         "Obligation False predicts this teaching label, not the truth or absence of a world fact.",
                         "The unchanged encoder uses whole-token windows; cross-window meaning is not established.",
                         "Style, explanation wording, source admission and school authorization are not learned here."]}
    try:
        if type(text) is not str or not text.strip():
            raise ValueError("Expected nonempty source text")
        raw = text.encode("utf-8", "strict")
        if len(raw) > MAX_TEXT_BYTES:
            raise ValueError("Apprentice source byte budget")
        result.update(source_sha256=sha256(raw).hexdigest(), source_byte_length=len(raw))
        shared.source_windows(text)
    except (UnicodeError, ValueError, TypeError, ResourceLimit) as error:
        return {**result, "reason": type(error).__name__}
    try:
        model, encoder = load()
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
        return {**result, "status": "MODEL_UNAVAILABLE", "reason": type(error).__name__}
    try:
        vector = witness_recall.vector(encoder, text)
        prediction = decide(model, vector)
    except (ValueError, TypeError, KeyError, OverflowError, ResourceLimit) as error:
        return {**result, "reason": type(error).__name__}
    return {**result, **prediction, "model_sha256": MODEL_SHA256, "encoder_sha256": ENCODER_SHA256,
            "feature_contract": FEATURES, "calibration": deepcopy(model["calibration"]),
            "required_independent_checks": ["DOMAIN_CONTRACT", "INPUT_OBLIGATIONS", "ACTION_CAPABILITY", "ORIGINAL_OWNER"]}
