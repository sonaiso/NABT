"""Supervised token roles in mixed Arabic paragraphs. Scores have no action authority."""
import csv
import json
from collections import Counter, defaultdict
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from random import Random
from unicodedata import category

from tools.grammar_catalog.operations import ROOT, exact_terms

DATA = ROOT / "evidence/inspection_discourse_v1"
MODEL = Path(__file__).with_name("data") / "inspection_roles_v1.json"
MODEL_SHA = "184424cc0b1c1a9accf3e64b6d8d7e3c61bc52a69e938c4f4dd145e308f6800c"
LABELS = ("report", "content", "condition", "request", "prohibit")


def bare(word):
    return "".join(c for c in word if not category(c).startswith("M"))


def examples(path):
    with path.open(encoding="utf-8") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            parts, labels = [], []
            for slot in ("report", "content", "condition", "request", "tail"):
                if row[slot]:
                    parts.append(row[slot])
                    role = row["tail_role"] if slot == "tail" else slot
                    labels.extend([role] * len(exact_terms(row[slot])))
            yield " ".join(parts), labels


def features(text):
    terms = exact_terms(text)
    words = [bare(t["surface"]) for t in terms]
    for i, word in enumerate(words):
        cues = [f"short={len(words) <= 2}", "bias", "prefix=" + word[:2], "suffix=" + word[-2:]]
        for offset in (-2, -1, 0, 1, 2):
            j = i + offset
            token = words[j] if 0 <= j < len(words) else "#"
            cues.append(f"{offset}={token}")
            cues.append(f"{offset}:prefix={token[:2]}")
        yield cues


def predict(weights, cues):
    return max(LABELS, key=lambda label: sum(weights.get(cue, {}).get(label, 0) for cue in cues))


def fit():
    train = list(examples(DATA / "train.tsv"))
    weights = defaultdict(Counter)
    rng = Random(116)
    for _ in range(16):
        rng.shuffle(train)
        for text, targets in train:
            for cues, gold in zip(features(text), targets, strict=True):
                guess = predict(weights, cues)
                if guess != gold:
                    for cue in cues:
                        weights[cue][gold] += 1
                        weights[cue][guess] -= 1
    return {"schema": "ntl.inspection-roles.v1", "labels": list(LABELS), "epochs": 16,
            "training_sha256": sha256((DATA / "train.tsv").read_bytes()).hexdigest(),
            "weights": {f: {k: v for k, v in scores.items() if v} for f, scores in weights.items()}}


@lru_cache(maxsize=1)
def _decode(raw):
    if sha256(raw).hexdigest() != MODEL_SHA:
        raise ValueError("Unexpected inspection role weights")
    return json.loads(raw)["weights"]


def propose(text):
    raw = MODEL.read_bytes()
    labels = [predict(_decode(raw), cues) for cues in features(text)]
    return {"authority": "PROPOSAL_ONLY", "model_sha256": sha256(raw).hexdigest(), "roles": labels}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    path = parser.parse_args().output
    with path.open("x", encoding="utf-8") as stream:
        json.dump(fit(), stream, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
