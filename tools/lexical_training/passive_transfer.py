"""Local neural proposals for a bounded passive clause. Only the owner may license a reading."""
from hashlib import sha256
from itertools import permutations
import math
import unicodedata

from tools.grammar_catalog.operations import exact_terms
from tools.lexical_testimony import _strict_json
from . import shared_encoder

DIRECTORY = shared_encoder.ROOT / "evidence/passive_relation_transfer_v1"
MODEL = DIRECTORY / "model.json"
MODEL_SHA256 = "46d2f0ef443ab93b62ffa9204e8adefba04bd34f5e76910c9bccb22f94e59898"
SCHEMA = "nabt.passive-relation-transfer.v1"
ASSERT, DENY, OUTSIDE = "ASSERT_PASSIVE", "DENY_PASSIVE", "OUTSIDE"
MAX_TERMS, MAX_BYTES, HIDDEN = 6, 2048, 8


def observed(surface):
    """Features from written scalars only. Never assign a missing vowel or a lexeme."""
    letters = [c for c in surface if not unicodedata.category(c).startswith("M")]
    marks = "".join(c for c in surface if unicodedata.category(c).startswith("M"))
    vowels = "".join(c for c in marks if c in "َُِ")
    clusters = []
    for char in surface:
        if unicodedata.category(char).startswith("M"):
            if clusters:
                clusters[-1] += char
        else:
            clusters.append("")
    return "".join(letters), (
        "n=" + str(min(len(letters), 7)), "marks=" + marks,
        "vowels=" + vowels, "first-vowel=" + vowels[:1], "inner-vowels=" + vowels[:2],
        "last=" + (surface[-1] if surface[-1] in "ًٌٍَُِْ" else "_"),
        "onset=" + "".join(letters[:1]), "prefix=" + "".join(letters[:2]),
        *(f"cluster-{i}={m}" for i,m in enumerate(clusters[:6])),
    )


def assignments(n):
    """Rank every assignment to distinct source occurrences; never prune by score."""
    for v, p in permutations(range(n), 2):
        yield ASSERT, v, p, None
    for c, v, p in permutations(range(n), 3):
        yield DENY, v, p, c


def candidates(text):
    tokens = exact_terms(text)
    if len(tokens) > MAX_TERMS:
        return None
    words = [observed(t["surface"]) for t in tokens]
    gaps = [text[:tokens[0]["codepoint_span"][0]]] if tokens else [text]
    for i, token in enumerate(tokens):
        end = tokens[i+1]["codepoint_span"][0] if i+1 < len(tokens) else len(text)
        gaps.append(text[token["codepoint_span"][1]:end])
    punctuation = sorted({c for gap in gaps for c in gap if not c.isspace()})
    spans = [t["utf8_span"] for t in tokens]
    output = []
    for kind, verb, patient, cue in assignments(len(tokens)):
        # The positional, surface and separator channels are observable. The
        # hypothetical role names describe a candidate, not a verified answer.
        context = [kind, f"v-at={verb}", f"p-v={patient-verb}", f"n={len(tokens)}"]
        context.extend("punct=" + c for c in punctuation)
        if any("\n" in g for g in gaps):
            context.append("line-break")
        shape = ["v/" + f for f in words[verb][1]] + ["p/" + f for f in words[patient][1]]
        for i, (skeleton, signs) in enumerate(words):
            if i != verb and i != patient:
                role = "cue/" if i == cue else "other/"
                context.extend([role + f"v-offset={i-verb}", role + "form=" + skeleton])
                context.extend(role + s for s in signs if s.startswith("cluster-"))
        candidate = {"relation": kind, "verb_span": spans[verb], "patient_span": spans[patient],
                     "cue_span": spans[cue] if cue is not None else None}
        output.append((candidate, context, shape))
    return output


def load_model():
    if MODEL.stat().st_size > 256_000:
        raise ValueError("Passive model budget exceeded")
    raw = MODEL.read_bytes()
    if sha256(raw).hexdigest() != MODEL_SHA256:
        raise ValueError("Installed passive model identity changed")
    return _strict_json(raw)


def hidden_state(indices, model):
    bias = model["bias"]
    embedding = model["embedding"]
    return [math.tanh(bias[h] + sum(embedding[i][h] for i in indices)) for h in range(HIDDEN)]


def rank(rows, model, channel="full"):
    vocabulary = {word:i for i, word in enumerate(model["features"])}
    ranked = [{"relation": OUTSIDE, "verb_span": None, "patient_span": None, "cue_span": None, "score": 0.0}]
    for candidate, context, shape in rows:
        names = context + shape if channel == "full" else context if channel == "context" else shape
        indices = [vocabulary[name] for name in names if name in vocabulary]
        h = hidden_state(indices, model)
        score = sum(a*b for a,b in zip(h, model["readout"], strict=True)) + model["offset"]
        ranked.append({**candidate, "score": round(score, 8)})
    return sorted(ranked, key=lambda c: -c["score"])


def propose(text):
    if type(text) is not str:
        raise ValueError("Expected exact source text")
    raw = text.encode("utf-8")
    result = {"schema": SCHEMA, "authority": "NONE", "source_sha256": sha256(raw).hexdigest(),
              "model_sha256": None, "relation": None, "verb_span": None, "patient_span": None,
              "cue_span": None, "candidates": [], "world_truth_established": False}
    rows = candidates(text) if len(raw) <= MAX_BYTES else None
    if rows is None:
        return {**result, "status": "RESOURCE_LIMIT", "reason": "PASSIVE_PROPOSAL_SOURCE_BUDGET"}
    try:
        model = load_model()
    except (OSError, ValueError) as error:
        return {**result, "status": "MODEL_UNAVAILABLE", "reason": type(error).__name__}
    ranked = rank(rows, model)
    best = ranked[0]
    return {**result, **{k: best[k] for k in ("relation", "verb_span", "patient_span", "cue_span")},
            "status": "OUTSIDE" if best["relation"] == OUTSIDE else "PROPOSED",
            "model_sha256": MODEL_SHA256, "candidates": ranked}
