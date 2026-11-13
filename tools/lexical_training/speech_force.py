"""Order source-checked readings with a frozen byte GRU and a local linear readout."""
import csv
from collections import Counter
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import unicodedata

from . import shared_encoder as shared
from .contextual_alignment import occurrence_vectors
from .witness_recall import distribution

LABELS = ("assert", "ask", "request", "prohibit", "vocative", "wish", "hope", "praise", "blame")
MODEL = Path(__file__).with_name("data") / "speech_force_v2.json"
TRAIN = shared.ROOT / "evidence/licensed_speech_v1/train.tsv"
MODEL_SHA = "05f661d1a204cdc00c516ad9d4b54f5be1031fdcd8d19387185475daebd86b29"


def features(encoder, text):
    rows, _ = occurrence_vectors(encoder, text)
    if not rows:
        raise ValueError("No written terms")
    # First-token boundaries retain an initial operator; the mean retains the rest of the utterance.
    return rows[0]["vector"] + [sum(col) / len(rows) for col in zip(*(r["vector"] for r in rows), strict=True)]


def training_views(text):
    """Keep observed carriers in order. Drop combining marks only in the training view."""
    marks = 0
    alternating = []
    bare = []
    for c in text:
        if unicodedata.category(c).startswith("M"):
            marks += 1
            if marks % 2:
                alternating.append(c)
        else:
            alternating.append(c)
            bare.append(c)
    return list(dict.fromkeys([text, "".join(alternating), "".join(bare)]))


def training_examples():
    with TRAIN.open(encoding="utf-8") as f:
        source = list(csv.DictReader(f, delimiter="\t"))
    # Reserve complete orthographic families prior to augmentation, including the disclosed development probes.
    reserved = set()
    for relative in ("partial_speech_v1/paired.tsv", "licensed_speech_v1/challenge.tsv"):
        with (shared.ROOT/"evidence"/relative).open(encoding="utf-8") as f:
            reserved.update(training_views(r["text"])[-1] for r in csv.DictReader(f,delimiter="\t"))
    retained = [r for r in source if training_views(r["text"])[-1] not in reserved]
    return retained, [r["text"] for r in source if r not in retained]


def fit():
    import numpy as np
    encoder, model_sha = shared.load_model()
    rows, excluded = training_examples()
    counts = Counter(r["force"] for r in rows)
    if set(counts) != set(LABELS) or len({r["text"] for r in rows}) != len(rows):
        raise ValueError("Incomplete or duplicate speech training rows")
    examples = [(r["force"], view, 1. / (counts[r["force"]] * len(views)))
                for r in rows for views in [training_views(r["text"])] for view in views]
    x = np.array([features(encoder, view) + [1.] for _,view,_ in examples])
    y = np.array([[float(label == gold) for label in LABELS] for gold,_,_ in examples])
    w = np.array([w for _,_,w in examples])
    weights = np.linalg.solve((x.T * w) @ x + .1 * np.eye(x.shape[1]), (x.T * w) @ y)
    return {"schema": "nabt.speech-force-head.v1", "labels": list(LABELS), "encoder_sha256": model_sha,
            "training_sha256": sha256(TRAIN.read_bytes()).hexdigest(), "alpha": .1, "n": len(rows), "n_views": len(examples),
            "augmentation":"observed_original_alternating_and_bare_v1", "reserved_training_rows":excluded,
            "weights": weights.T.round(10).tolist()}


@lru_cache(maxsize=1)
def checked_model(encoder_bytes, head_bytes):
    if sha256(head_bytes).hexdigest() != MODEL_SHA:
        raise ValueError("Changed speech readout")
    head = json.loads(head_bytes)
    if (sha256(encoder_bytes).hexdigest() != head["encoder_sha256"] or head["labels"] != list(LABELS)
            or not shared._shape(head["weights"], (len(LABELS), 8 * shared.HIDDEN + 1))):
        raise ValueError("Unbound speech readout")
    return shared.validate_model(json.loads(encoder_bytes)), head


def propose(text):
    try:
        encoder, head = checked_model(shared.MODEL.read_bytes(), MODEL.read_bytes())
        scores = distribution(head["weights"], features(encoder, text))
        return {"status": "PROPOSED", "authority": "NONE", "model_sha256": MODEL_SHA,
                "encoder_sha256": head["encoder_sha256"], "top": LABELS[scores.index(max(scores))],
                "scores": dict(zip(LABELS, scores, strict=True))}
    except (OSError, ValueError, KeyError) as err:
        return {"status": "MODEL_UNAVAILABLE", "authority": "NONE", "reason": type(err).__name__}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    with parser.parse_args().output.open("x", encoding="utf-8") as dst:
        json.dump(fit(), dst, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        dst.write("\n")
