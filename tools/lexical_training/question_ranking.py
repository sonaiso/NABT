"""Local learned question proposals; the source-reading gate checks each operation separately."""
from collections import Counter
from functools import lru_cache
from hashlib import sha256
import json
import re
from pathlib import Path

MODEL = Path(__file__).with_name("data") / "question_prior_ranker.json"


def features(question):
    words = re.findall(r"[ء-ي]+", re.sub("[\u064b-\u065f]", "", question))
    counts = Counter()
    for word in words:
        padded = "_" + word + "_"
        counts.update([word] + [padded[i:i+3] for i in range(len(padded)-2)])
    return counts


@lru_cache(maxsize=1)
def decode(raw):
    return json.loads(raw)


def propose(question):
    try:
        raw = MODEL.read_bytes()
        model = decode(raw)
        if sha256(raw).hexdigest() != MODEL_SHA:
            raise ValueError("MODEL_IDENTITY_CHANGED")
        scores = dict.fromkeys(model["labels"], 0)
        for feature, count in features(question).items():
            for label, weight in model["weights"].get(feature, {}).items():
                scores[label] += weight * count
        return {"status": "PROPOSED", "ranking": sorted(scores, key=lambda k: (-scores[k], k)),
                "scores": scores, "model_sha256": MODEL_SHA, "authority": "PROPOSAL_ONLY"}
    except (ValueError, OSError) as error:
        return {"status": "MODEL_UNAVAILABLE", "reason": type(error).__name__, "authority": "NONE"}


MODEL_SHA = "33859dc03a53828507a7b002dbf5e29d2e9d71028f5815a2a0a8e42466af4c67"
