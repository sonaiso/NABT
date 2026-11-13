"""Train an averaged multiclass perceptron on questions only, with deterministic shuffling."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import random

from .question_ranking import features

TRAIN = Path(__file__).resolve().parents[2] / "evidence/question_cognition_v1/train.tsv"


def fit(raw):
    rows = [line.split("\t") for line in raw.decode().splitlines()]
    labels = sorted({label for label, _ in rows})
    weights, totals, last = Counter(), Counter(), Counter()
    rng, step = random.Random(107), 0
    for _ in range(24):
        rng.shuffle(rows)
        for label, question in rows:
            step += 1
            x = features(question)
            guess = max(labels, key=lambda k: sum(weights[k, f] * count for f, count in x.items()))
            if guess == label:
                continue
            for f, count in x.items():
                for key, delta in [((label, f), count), ((guess, f), -count)]:
                    totals[key] += (step - last[key]) * weights[key]
                    last[key] = step
                    weights[key] += delta
    by_feature = defaultdict(dict)
    for (label, f), weight in weights.items():
        total = totals[label, f] + (step + 1 - last[label, f]) * weight
        if total:
            by_feature[f][label] = total
    return {"schema": "nabt.question-ranker.v1", "labels": labels, "weights": by_feature,
            "train_sha256": sha256(raw).hexdigest(), "seed": 107, "epochs": 24,
            "score_scale": step, "examples": len(rows)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(fit(TRAIN.read_bytes()), ensure_ascii=False,
                                      sort_keys=True, separators=(",", ":")) + "\n", encoding="utf8")
