"""Small learned pointer-attention heads. Source occurrence IDs are the values."""
from hashlib import sha256
import json
import math

from nabt.corpus_evidence import lookup_clusters
from tools.grammar_catalog.operations import ROOT, exact_terms

MODEL_PATH = "evidence/grounded_attention_v1/model.json"
MODEL_SHA256 = "46ad451365a09c62aeec57189a817b8696a5c9c0333d6324c415913fee689400"
HEADS = ("subject", "object", "question_cue")
WIDTH = 6
MAX_BYTES = 1024
KEYS = ("bias", "null", "article", "lam", "hal", "ends_nun", "penult_alif", "penult_ya",
        "last_damma", "last_fatha", "last_kasra", "last_sukun", "penult_sukun",
        "before_penult_fatha", "first_damma", "inner_fatha", "inner_kasra", "other")
QUERIES = ("bias", "length_three", "length_four", "has_hal", "governor_inner_fatha",
           "governor_begins_damma", "question_mark", "other_punctuation", "internal_break",
           "definite_count", "alif_count", "ya_count", "damma_count", "fatha_count")


def token_key(surface):
    cs = lookup_clusters(surface)
    if not cs:
        return [int(k in ("bias", "other")) for k in KEYS]
    letters = "".join(c[0] for c in cs)
    marks = [c[1] for c in cs]
    prev = marks[-2] if len(cs) >= 2 else set()
    return list(map(float, (1, 0, letters.startswith("ال"), letters == "لم", letters == "هل",
        letters.endswith("ن"), letters.endswith("ان"), letters.endswith("ين"),
        "ُ" in marks[-1], "َ" in marks[-1], "ِ" in marks[-1], "ْ" in marks[-1],
        "ْ" in prev, len(cs) > 2 and "َ" in marks[-3], "ُ" in marks[0],
        "َ" in prev, "ِ" in prev, 0)))


def encode(text):
    terms = exact_terms(text)
    keys = [token_key(t["surface"]) for t in terms]
    hi = {k: i for i, k in enumerate(KEYS)}
    has_hal = bool(keys and keys[0][hi["hal"]])
    verb = keys[int(has_hal)] if len(keys) > int(has_hal) else [0] * len(KEYS)
    tail = text[terms[-1]["codepoint_span"][1]:].strip() if terms else text
    gaps = [text[:terms[0]["codepoint_span"][0]]] if terms else []
    gaps.extend(text[a["codepoint_span"][1]:b["codepoint_span"][0]] for a,b in zip(terms, terms[1:]))
    other_punct = tail not in ("", ".", "؟", "?") or any(g.strip() for g in gaps)
    counts = [sum(k[hi[f]] for k in keys if k[hi["article"]]) / 2
              for f in ("article", "penult_alif", "penult_ya", "last_damma", "last_fatha")]
    query = list(map(float, (1, len(keys) == 3, len(keys) == 4, has_hal, verb[hi["inner_fatha"]],
                  verb[hi["first_damma"]], tail in ("؟", "?"), other_punct, "\n" in text.strip(), *counts)))
    null = [float(k in ("bias", "null")) for k in KEYS]
    return terms, query, [null, *keys]


def project(x, matrix):
    return [sum(a*b for a,b in zip(x, column, strict=True)) for column in zip(*matrix, strict=True)]


def attend(text, model, *, masked_heads=(), hide_nominal_marks=False):
    terms, x, keys = encode(text)
    if hide_nominal_marks:
        # Keep the sentence, source offsets, governor and cue unchanged. Remove
        # inflection observations and their aggregates, without refitting.
        for key in keys:
            if key[KEYS.index("article")]:
                for name in ("ends_nun", "penult_alif", "penult_ya", "last_damma", "last_fatha",
                             "last_kasra", "last_sukun", "penult_sukun", "before_penult_fatha",
                             "inner_fatha", "inner_kasra"):
                    key[KEYS.index(name)] = 0.
        for name in ("alif_count", "ya_count", "damma_count", "fatha_count"):
            x[QUERIES.index(name)] = 0.
    spans = [None, *(t["utf8_span"] for t in terms)]
    heads = {}
    for name in HEADS:
        weights = model["heads"][name]
        q = project(x, weights["Wq"])
        logits = [sum(a*b for a,b in zip(q, project(key, weights["Wk"]), strict=True)) / math.sqrt(WIDTH)
                  for key in keys]
        if name in masked_heads:
            logits = [0.0] * len(keys)
        top = max(logits)
        exps = [math.exp(v - top) for v in logits]
        total = sum(exps)
        # Fixed one-hot V for each local occurrence (plus NULL) makes alpha @ V
        # a source pointer distribution. Equal maxima are left unresolved.
        winners = [i for i, v in enumerate(logits) if v == top]
        selected = spans[winners[0]] if len(winners) == 1 else None
        heads[name] = {"span": selected, "attention": [
            {"span": span, "weight": round(v/total, 9)} for span, v in zip(spans, exps, strict=True)]}
    subj, obj = (heads[k]["span"] for k in HEADS[:2])
    bound = bool(subj and obj and subj != obj)
    return {"heads": heads, "status": "PROPOSED" if bound else "DEFER",
            "force_proposal": ("ask" if heads["question_cue"]["span"] else "assert") if bound else None}


def propose(text):
    raw = text.encode()
    base = {"schema": "nabt.classical-role-attention.v1", "authority": "NONE",
            "source_sha256": sha256(raw).hexdigest()}
    if len(raw) > MAX_BYTES or len(exact_terms(text)) > 4:
        return {**base, "status": "OUTSIDE_BUDGET"}
    try:
        data = (ROOT / MODEL_PATH).read_bytes()
        if sha256(data).hexdigest() != MODEL_SHA256:
            raise ValueError("MODEL_IDENTITY_MISMATCH")
        model = json.loads(data)
    except (OSError, ValueError) as error:
        return {**base, "status": "MODEL_UNAVAILABLE", "reason": type(error).__name__}
    return {**base, **attend(text, model), "model_sha256": MODEL_SHA256}
