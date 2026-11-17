"""Shared learned support operators; exact sources and licensed answers stay outside weights."""
from hashlib import sha256
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / "evidence/ntl_update_memory_v1"
MODEL = DIRECTORY / "model.json"
MODEL_SHA256 = "94db3cad29577278eff0e8a650784ae8f3b478037c8e7355feb48b3eb3434de9"
PROTOCOL_SHA256 = "208dba93e5085464c1e0ce7402ef02bd373fdcf197ed86dea9f4a5b74788735e"
ROLES = ("property", "law", "event_positive", "event_negative", "state")


def sigmoid(z):
    return 1.0 / (1.0 + math.exp(-max(-50.0, min(50.0, z))))


def gate(parameters, op, left, right):
    bias, a, b = parameters[op]
    return sigmoid(bias + a * left + b * right)


def load():
    raw = MODEL.read_bytes()
    if len(raw) > 16384 or sha256(raw).hexdigest() != MODEL_SHA256:
        raise ValueError("Update-memory model identity changed")
    model = json.loads(raw)
    if (set(model) != {"schema", "parameters", "protocol_sha256", "authority", "release_policy"}
            or model["schema"] != "nabt.update-memory-model.v1"
            or model["authority"] != "NONE" or model["release_policy"] != "REVIEW_ONLY"
            or model["protocol_sha256"] != PROTOCOL_SHA256
            or sha256((DIRECTORY / "protocol.json").read_bytes()).hexdigest() != PROTOCOL_SHA256
            or set(model["parameters"]) != {"and", "or"}):
        raise ValueError("Update-memory model contract changed")
    for values in model["parameters"].values():
        if (type(values) is not list or len(values) != 3 or
                any(type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 1000 for v in values)):
            raise ValueError("Invalid operator parameters")
    return model


def predict(parameters, sources, active):
    """Read active source support only, never owner answers. IDs are not features."""
    support = {}
    for role in ROLES:
        values = [float(source["id"] in active) for source in sources if source["role"] == role]
        value = 0.0
        for next_value in values:
            value = gate(parameters, "or", value, next_value)
        support[role] = value
    values = [gate(parameters, "and", support["property"], support["law"]),
              support["event_positive"], support["event_negative"], support["state"]]
    return {"scores": values, "prediction": [int(v >= 0.5) for v in values],
            "role_scores": support, "authority": "NONE"}


def propose(sources, active):
    try:
        model = load()
        return {"status": "PROPOSED", "model_sha256": MODEL_SHA256,
                **predict(model["parameters"], sources, active)}
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {"status": "MODEL_UNAVAILABLE", "reason": type(error).__name__, "authority": "NONE"}
