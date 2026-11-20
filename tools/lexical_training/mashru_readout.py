"""Train a bounded force proposal on the original Lean reader's observations."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from . import shared_encoder, speech_force
from .mashru_lesson import native_traces

MODEL = Path(__file__).with_name("data") / "mashru_force_v1.json"
SCALE = 1_000_000
# Withhold whole predicate/argument pairs before forming operator contrasts.
TRAIN = (("خَرَجَ", "يَخْرُجْ", "الرَّجُلُ"), ("وَقَفَ", "يَقِفْ", "الطِّفْلُ"), ("جَلَسَ", "يَجْلِسْ", "الْوَلَدُ"),
         ("وَصَلَ", "يَصِلْ", "الضَّيْفُ"), ("دَخَلَ", "يَدْخُلْ", "الْحَارِسُ"), ("رَجَعَ", "يَرْجِعْ", "الْمُعَلِّمُ"))
TEST = (("حَضَرَ", "يَحْضُرْ", "الْكَاتِبُ"), ("سَكَتَ", "يَسْكُتْ", "الْخَطِيبُ"), ("نَزَلَ", "يَنْزِلْ", "الْمُسَافِرُ"))
OPERATORS = ("", "لَمْ", "إِنْ", "هَلْ", "مَنْ")


def examples(pairs):
    rows = []
    for past, jussive, subject in pairs:
        for op in OPERATORS:
            # Provide an imperfect governed verb after lam. The teacher assigns
            # force from its own frames/rows, including its explicit abstention.
            verb = jussive if op == "لَمْ" else past
            rows.append(" ".join(word for word in (op, verb, subject) if word))
    return rows


def vector(encoder, text):
    return speech_force.features(encoder, text) + [1.0]


def predict(model, encoder, text):
    x = vector(encoder, text)
    scores = [round(sum(w*v for w, v in zip(row, x, strict=True))) for row in model["weights"]]
    return model["labels"][scores.index(max(scores))]


def fit():
    import numpy as np
    encoder, digest = shared_encoder.load_model()
    train, test = examples(TRAIN), examples(TEST)
    traces = native_traces(train + test)
    labels = [trace["QUWWA"][0][0] for trace in traces]
    gold, held = labels[:len(train)], labels[len(train):]
    classes = sorted(set(gold))
    if len(classes) != 5 or set(held) != set(classes):
        raise ValueError("incomplete native contrasts")
    x = np.array([vector(encoder, text) for text in train])
    y = np.array([[float(label == other) for other in classes] for label in gold])
    weights = np.linalg.solve(x.T @ x + .01 * np.eye(x.shape[1]), x.T @ y)
    model = {"schema": "nabt.mashru-force-head.v1", "encoder_sha256": digest, "labels": classes,
             "weights": np.rint(weights.T * SCALE).astype(int).tolist(), "scale": SCALE,
             "teacher": "Nizam.Athar.quwwaJumla", "train_count": len(train),
             "teacher_rows_sha256": sha256(json.dumps(list(zip(train, gold)), ensure_ascii=False).encode()).hexdigest()}
    guesses = [predict(model, encoder, text) for text in test]
    majority = Counter(gold).most_common(1)[0][0]
    model["heldout"] = {"scope": "new predicate/argument pairs, shared initial operators",
                        "correct": sum(a == b for a, b in zip(guesses, held)), "total": len(held),
                        "majority_correct": held.count(majority),
                        "rows": [{"text": t, "native": a, "proposal": b} for t,a,b in zip(test, held, guesses)]}
    return model


def propose(text):
    try:
        data = MODEL.read_bytes()
        model = json.loads(data)
        encoder, digest = shared_encoder.load_model()
        if model["encoder_sha256"] != digest:
            raise ValueError("stale force encoder")
        return {"status": "PROPOSED", "label": predict(model, encoder, text),
                "model_sha256": sha256(data).hexdigest(), "authority": "NONE"}
    except (OSError, ValueError, KeyError) as exc:
        return {"status": "MODEL_UNAVAILABLE", "reason": type(exc).__name__, "authority": "NONE"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    model = fit()
    serialized = json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    if args.check:
        if MODEL.read_text() != serialized:
            raise SystemExit("readout does not reproduce")
    else:
        MODEL.write_text(serialized)
    print({k: v for k, v in model["heldout"].items() if k != "rows"})
