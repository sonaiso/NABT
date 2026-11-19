"""Fit a lesson-local neural readout and independently reconstruct an unseen stem."""
from math import gcd

from nabt import derivation
from tools import evidence_lifecycle_v1 as wire
from . import pattern_learning as net

SCHEMA = "ntl.pattern-induction.v1"
RESULT = "ntl.pattern-induction-result.v1"


def counterexamples(pairs):
    """Change one visible short vowel per example. The learned templates fix that literal."""
    positives = {stem for _, stem in pairs}
    changes = {"َ": "ُ", "ُ": "ِ", "ِ": "َ", "ْ": "َ"}
    contrasts = {stem[:i] + changes[v] + stem[i + 1:] for _, stem in pairs
                 for i, v in enumerate(stem) if v in changes}
    return sorted(contrasts - positives)


def fit_readout(head, positives, negatives, probe):
    # Nearest class mean in the trained ReLU space is a linear neural readout.
    # Clear denominators to fit and replay every coefficient with exact integers.
    def encode(word):
        return net.hidden_state(head, net.features(word))
    p = [len(negatives) * sum(values) for values in zip(*(encode(w) for w in positives))]
    n = [len(positives) * sum(values) for values in zip(*(encode(w) for w in negatives))]
    factor = 2 * len(positives) * len(negatives)
    weights = [factor * (a - b) for a, b in zip(p, n)]
    bias = sum(b*b - a*a for a, b in zip(p, n))
    divisor = gcd(bias, *weights) or 1
    weights = [w // divisor for w in weights]
    bias //= divisor
    score = bias + sum(w * x for w, x in zip(weights, encode(probe), strict=True))
    return {"status": "FITTED", "encoder_sha256": net.MODEL_SHA, "weights": weights, "bias": bias,
            "score": score, "prediction": score > 0 if score else None,
            "positive_stems": positives, "changed_vowel_stems": negatives, "authority": "NONE"}


def run(lesson):
    wire._fields(lesson, {"schema", "pairs", "probe"}, "pattern lesson")
    if lesson["schema"] != SCHEMA:
        raise ValueError("Unknown pattern lesson")
    pairs, probe = lesson["pairs"], lesson["probe"]
    wire._array(pairs, "aligned demonstrations", 8)
    wire._text(probe, "probe stem", 128)
    if not net.features(probe):
        raise ValueError("Expected a single Arabic probe within the encoder window")
    for pair in pairs:
        if type(pair) is not list or len(pair) != 2:
            raise ValueError("Expected a [root, stem] pair")
        wire._text(pair[0], "root", 24)
        wire._text(pair[1], "stem", 128)
        if not net.features(pair[1]):
            raise ValueError("Malformed or overlong demonstration")
    result = {"schema": RESULT, "execution_measured": True, "request": lesson,
              "authority": "CONDITIONAL_ON_SUPPLIED_ROOT_STEM_ALIGNMENT", "action_authority": "NONE",
              "global_model_updated": False, "alternatives": [], "readout": {"status": "INSUFFICIENT_EXAMPLES"}}
    if not pairs:
        return dict(result, status="DEFER_NO_DEMONSTRATIONS")
    templates = net.induce(pairs)
    if len(templates) > 256:
        raise wire.ResourceLimit("Too many surviving alignments for a replayable lesson")
    arity = len(pairs[0][0])
    for tokens in templates:
        root = derivation._recover({"arity": arity, "tokens": tokens, "root_domain": "radicals28_shape_only"}, probe)
        result["alternatives"].append({"tokens": tokens, "probe_root": root})
    if not templates:
        return dict(result, status="NO_CONSISTENT_TEMPLATE")
    if len(templates) > 1:
        return dict(result, status="AMBIGUOUS_TEMPLATES")
    positives = sorted({s for _, s in pairs})
    negatives = counterexamples(pairs)
    hits = result["alternatives"][0]["probe_root"] is not None
    if len({r for r, _ in pairs}) >= 2 and negatives:
        trained = net.model()
        if trained:
            result["readout"] = fit_readout(trained["patterns"], positives, negatives, probe)
            result["readout"]["agrees_with_refill"] = result["readout"]["prediction"] is hits
        else:
            result["readout"] = {"status": "ENCODER_UNAVAILABLE"}
    return dict(result, status="MATCHED_CONDITIONAL_SHAPE" if hits else "NO_EXACT_REFILL")
