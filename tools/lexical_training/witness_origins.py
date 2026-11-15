"""Two source-blind learned proposal heads on the existing frozen NABT byte GRU."""
import csv
from functools import lru_cache
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path

from . import shared_encoder as shared
from .contextual_alignment import occurrence_vectors
from .witness_recall import distribution

BANK = Path(__file__).with_name("data") / "ntl_witness_origins.tsv"
MODEL = BANK.with_name("ntl_witness_head.json")
LABELS = ("capacity", "state", "event", "negative", "purpose", "request", "even", "odd", "context")


@lru_cache(maxsize=1)
def _bank(raw):
    rows = list(csv.DictReader(StringIO(raw.decode()), delimiter="\t"))
    for row in rows:
        if row["relation"] not in LABELS[:-1] or row["clause"].count(row["cue"]) != 1:
            raise ValueError("Invalid retained witness")
        pieces = [row["clause"], row["context"]]
        if int(row["id"][-2:]) % 2 == 0:
            pieces.reverse()
        if row["proof"]:
            pieces.append(row["proof"])
        row["text"] = "؛ ".join(pieces) + "."
    if len({r["id"] for r in rows}) != len(rows) or len({r["text"] for r in rows}) != len(rows):
        raise ValueError("Non-unique retained source")
    return rows


def origins():
    return _bank(BANK.read_bytes())


def views(encoder, text):
    rows, _ = occurrence_vectors(encoder, text)
    if not rows:
        return None, []
    def mean(group):
        return [sum(col) / len(group) for col in zip(*(r["vector"] for r in group), strict=True)]
    clause = rows[0]["vector"] + mean(rows)
    spans = []
    for start in range(len(rows)):
        for size in range(1, min(3, len(rows) - start) + 1):
            group = rows[start:start + size]
            lo, hi = group[0]["utf8_span"][0], group[-1]["utf8_span"][1]
            spans.append((lo, hi, mean(group) + [size / 3, start / len(rows)]))
    return clause, spans


@lru_cache(maxsize=1)
def _model(raw, encoder_bytes):
    head = json.loads(raw)
    if sha256(raw).hexdigest() != HEAD_SHA or sha256(encoder_bytes).hexdigest() != head["encoder_sha256"]:
        raise ValueError("Changed witness model")
    return shared.validate_model(json.loads(encoder_bytes)), head


def propose(text):
    try:
        encoder, head = _model(MODEL.read_bytes(), shared.MODEL.read_bytes())
    except (OSError, ValueError, KeyError):
        return {"status": "MODEL_UNAVAILABLE", "authority": "NONE", "clauses": []}
    result = []
    offset = 0
    for fragment in text.split("؛"):
        part = fragment.strip().removesuffix(".").rstrip()
        if part and any("\u0621" <= c <= "\u064a" for c in part):
            start = offset + len(fragment[:fragment.index(part)].encode())
            features, candidates = views(encoder, part)
            if features:
                scores = distribution(head["relation"], features)
                a, b, vector = max(candidates, key=lambda c: distribution(head["cue"], c[2])[1])
                result.append({"surface": part, "utf8_span": [start, start + len(part.encode())],
                               "relation": LABELS[max(range(len(scores)), key=scores.__getitem__)],
                               "cue": part.encode()[a:b].decode(), "cue_utf8_span": [start + a, start + b]})
        offset += len(fragment.encode()) + len("؛".encode())
    return {"status": "PROPOSED", "authority": "NONE", "head_sha256": HEAD_SHA, "clauses": result}


HEAD_SHA = "810666213506f3cd31d9def0c8eb706bf4e2c3e3a59f775c62727692fe7c5c19"
