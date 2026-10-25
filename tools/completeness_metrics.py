#!/usr/bin/env python3
"""ACB v1: score frozen, adjudicated reading sets; never infer Arabic completeness.

No model calls, gold generation, guessed labels, or certificate promotion.
Missing outputs remain in the denominator. Undefined ratios are JSON null.
This scorer measures agreement with a supplied reference, not its adequacy.
"""
from __future__ import annotations
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

KINDS = {"positive", "ambiguity", "negative", "needs_context"}
STATUSES = {"licensed", "licensed_multiple", "rejected", "defer",
            "resource_error", "invalid_input"}
ACCEPTED = {"licensed", "licensed_multiple"}
FINAL = ACCEPTED | {"rejected"}


def ratio(n, d):
    return {"numerator": n, "denominator": d, "value": n / d if d else None}


def unique_strings(items, name):
    if not isinstance(items, list) or any(not isinstance(x, str) or not x for x in items):
        raise ValueError(f"{name}: expected nonempty strings in a list")
    if len(set(items)) != len(items):
        raise ValueError(f"{name}: duplicate values")
    return set(items)


def validate_reference(reference):
    if reference.get("schema") != "acb.reference.v1":
        raise ValueError("Unknown reference schema")
    if not reference.get("version") or not reference.get("scope"):
        raise ValueError("Reference version and scope are mandatory")
    families = unique_strings(reference.get("required_families"), "required_families")
    if not families:
        raise ValueError("The declared family inventory must not be empty")
    cases = reference.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Empty or absent reference is not measurable")
    unique_strings([c.get("id") for c in cases], "case ids")
    for c in cases:
        if c.get("kind") not in KINDS or not c.get("family") or not c.get("source_ref"):
            raise ValueError(f"{c.get('id')}: kind/family/source_ref required")
        if c["family"] not in families:
            raise ValueError("Case family is outside the declared inventory")
        gold = unique_strings(c.get("gold_readings"), "gold_readings")
        if c["kind"] != "needs_context" and c.get("gold_complete") is not True:
            raise ValueError("Set precision/exactness require a closed, adjudicated gold set")
        if c["kind"] == "positive" and len(gold) != 1:
            raise ValueError("A positive case has one licensed reading")
        if c["kind"] == "ambiguity" and len(gold) < 2:
            raise ValueError("An ambiguity case has at least two licensed readings")
        if c["kind"] in {"negative", "needs_context"} and gold:
            raise ValueError("Negative/context-required cases have no final gold readings")
    return cases


def evaluate(reference, predictions):
    cases = validate_reference(reference)
    if not isinstance(predictions, list):
        raise ValueError("Predictions must be a list")
    unique_strings([p.get("id") for p in predictions], "prediction ids")
    known = {c["id"] for c in cases}
    by_id = {}
    for p in predictions:
        if p["id"] not in known:
            raise ValueError("Unexpected prediction id: " + p["id"])
        status = p.get("status")
        if status not in STATUSES:
            raise ValueError("Unknown prediction status")
        readings = unique_strings(p.get("readings"), "predicted readings")
        if status not in ACCEPTED and readings:
            raise ValueError("Unaccepted candidates must not be put in final readings")
        if status == "licensed" and len(readings) != 1:
            raise ValueError("licensed requires one final reading")
        if status == "licensed_multiple" and len(readings) < 2:
            raise ValueError("licensed_multiple requires multiple final readings")
        by_id[p["id"]] = p

    rows = []
    for c in cases:
        p = by_id.get(c["id"], {"status": "missing", "readings": []})
        actual, gold = set(p["readings"]), set(c["gold_readings"])
        kind, status = c["kind"], p["status"]
        if kind in {"positive", "ambiguity"}:
            correct = status in ACCEPTED and actual == gold
        elif kind == "negative":
            correct = status == "rejected"
        else:
            correct = status == "defer"
        closed = kind != "needs_context"
        rows.append({"id": c["id"], "family": c["family"], "kind": kind,
                     "status": status, "correct": correct,
                     "tp": len(actual & gold) if closed else None,
                     "fp": len(actual - gold) if closed else None,
                     "fn": len(gold - actual) if closed else None})

    def subset(kinds): return [r for r in rows if r["kind"] in kinds]
    positives = subset({"positive", "ambiguity"})
    negatives = subset({"negative"})
    contexts = subset({"needs_context"})
    sufficient = positives + negatives
    final = [r for r in rows if r["status"] in FINAL]
    abstained = [r for r in rows if r["status"] == "defer"]
    closed = sufficient
    tp, fp, fn = (sum(r[k] for r in closed) for k in ["tp", "fp", "fn"])
    p, r = ratio(tp, tp + fp), ratio(tp, tp + fn)
    # F1 has denominator 2 TP + FP + FN, so no_predictions with gold is zero.
    metrics = {
        "positive_exact_set_coverage": ratio(sum(x["correct"] for x in positives), len(positives)),
        "selective_decision_accuracy": ratio(sum(x["correct"] for x in final), len(final)),
        "decision_coverage_on_sufficient": ratio(sum(x["status"] in FINAL for x in sufficient), len(sufficient)),
        "correct_coverage_on_sufficient": ratio(sum(x["correct"] for x in sufficient), len(sufficient)),
        "licensed_reading_precision": p,
        "licensed_reading_recall": r,
        "licensed_reading_f1": ratio(2 * tp, 2 * tp + fp + fn),
        "ambiguity_exact_set_coverage": ratio(sum(x["correct"] for x in positives if x["kind"] == "ambiguity"), sum(x["kind"] == "ambiguity" for x in positives)),
        "false_accept_rate_on_negative": ratio(sum(x["status"] in ACCEPTED for x in negatives), len(negatives)),
        "negative_rejection_rate": ratio(sum(x["correct"] for x in negatives), len(negatives)),
        "correct_context_deferral_rate": ratio(sum(x["correct"] for x in contexts), len(contexts)),
        "premature_finalization_on_context": ratio(sum(x["status"] in FINAL for x in contexts), len(contexts)),
        "justified_deferral_precision": ratio(sum(x["kind"] == "needs_context" for x in abstained), len(abstained)),
        "execution_error_rate": ratio(sum(x["status"] in {"resource_error", "invalid_input", "missing"} for x in rows), len(rows)),
    }
    families = {}
    for family in sorted(reference["required_families"]):
        group = [x for x in positives if x["family"] == family]
        families[family] = ratio(sum(x["correct"] for x in group), len(group))
    measured = [x["value"] for x in families.values() if x["value"] is not None]
    return {"schema": "acb.scores.v1", "reference_version": reference["version"],
            "scope": reference["scope"], "counts": dict(Counter(x["kind"] for x in rows)),
            "metrics": metrics, "positive_family_scores": families,
            "macro_positive_exact_set": sum(measured) / len(measured) if measured else None,
            "worst_measured_family": min(measured) if measured else None,
            "unmeasured_positive_families": [k for k,v in families.items() if v["value"] is None],
            "cases": rows, "universal_arabic_completeness": "NOT_INFERRED",
            "reference_adequacy": "EXTERNAL_OBLIGATION",
            "certificate_verification": "NOT_PERFORMED_BY_THIS_SCORER",
            "confidence_intervals": "NOT_INFERRED_WITHOUT_A_SAMPLING_DESIGN"}


def paired_comparison(first, second):
    a, b = first["cases"], second["cases"]
    if [(r["id"],r["kind"]) for r in a] != [(r["id"],r["kind"]) for r in b]:
        raise ValueError("Paired comparison requires the identical reference cases")
    pairs = [(x,y) for x,y in zip(a,b) if x["kind"] in {"positive", "ambiguity"}]
    wins = [x["id"] for x,y in pairs if x["correct"] and not y["correct"]]
    losses = [x["id"] for x,y in pairs if y["correct"] and not x["correct"]]
    return {"direction": "first_minus_second", "paired_positive_cases": len(pairs),
            "wins": wins, "losses": losses,
            "delta_positive_exact_set": (len(wins)-len(losses))/len(pairs) if pairs else None,
            "statistical_superiority": "NOT_INFERRED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--reference-sha256", required=True)
    parser.add_argument("--compare-predictions", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.reference.read_bytes()
    if sha256(raw).hexdigest() != args.reference_sha256:
        raise ValueError("Reference bytes differ from the declared freeze")
    prediction_bytes = args.predictions.read_bytes()
    result = evaluate(json.loads(raw), json.loads(prediction_bytes))
    result.update(reference_sha256=sha256(raw).hexdigest(),
                  predictions_sha256=sha256(prediction_bytes).hexdigest(),
                  scorer_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
    if args.compare_predictions:
        other_bytes = args.compare_predictions.read_bytes()
        other = evaluate(json.loads(raw), json.loads(other_bytes))
        result["comparison"] = paired_comparison(result, other)
        result["comparison"]["second_predictions_sha256"] = sha256(other_bytes).hexdigest()
    # Exclusive creation preserves the first measurement.
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
