"""Fit advisory readouts on the existing frozen GRU; NumPy is training-only.

The authored family split and fixed choices live in evidence before the first
fit. Test labels never enter fit or development calibration. --write refuses
to replace artifacts; --check replays the fit without writing any file.
"""
import argparse
from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path

from tools.evidence_lifecycle_v1 import strict_loads
from . import apprentice_readout as readout, shared_encoder as shared, witness_recall

EVIDENCE = shared.ROOT / "evidence/ntl_school_apprentice_v1"
TRAINING = EVIDENCE / "training.json"
PROTOCOL = EVIDENCE / "protocol.json"
EVALUATION = EVIDENCE / "evaluation.json"
TOLERANCE = 2e-9


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                       separators=(",", ":")) + "\n").encode("utf-8")


def identity(value):
    return sha256(encoded(value)).hexdigest()


def validate_data(data, protocol):
    """Check split isolation before presenting any row to an optimizer."""
    if (type(data) is not dict or data.get("schema") != "nabt.ntl-apprentice-training.v1"
            or type(data.get("rows")) is not list or type(data.get("outside_scope")) is not list):
        raise ValueError("Invalid training corpus")
    if (protocol.get("schema") != "nabt.ntl-apprentice-protocol.v1"
            or protocol.get("feature_owner") != "tools.lexical_training.witness_recall.vector"
            or protocol.get("encoder_sha256") != readout.ENCODER_SHA256
            or protocol.get("feature_dimension") != readout.DIM
            or protocol.get("fit") != "MASKED_CLASS_BALANCED_RIDGE"
            or protocol.get("feature_standardization") != "TRAIN_ONLY_MEAN_AND_STD_FLOOR_0.05"
            or protocol.get("alpha") != .25 or protocol.get("rounding_decimals") != 10
            or protocol.get("encoder_updated") is not False
            or protocol.get("test_used_for_selection") is not False):
        raise ValueError("Fixed fit contract changed")
    families, ids, texts = {}, set(), set()
    splits = {name: [] for name in ("train", "development", "test")}
    for row in data["rows"]:
        if (type(row) is not dict or set(row) != {"id", "family", "split", "language", "text",
                "action", "obligations", "provenance"}
                or row["split"] not in splits or row["language"] not in ("ar", "en")
                or row["action"] not in readout.ACTIONS
                or type(row["obligations"]) is not dict
                or set(row["obligations"]) != set(readout.OBLIGATIONS)
                or any(type(v) is not bool and v is not None for v in row["obligations"].values())
                or row["provenance"] != "ORIGINAL_AUTHORED_SYNTHETIC_V1"):
            raise ValueError("Invalid annotated row")
        if any(type(row[k]) is not str or not row[k] for k in ("id", "family", "text")):
            raise ValueError("Invalid source identity")
        if row["id"] in ids or row["text"] in texts:
            raise ValueError("Duplicate source or identifier")
        if row["family"] in families and families[row["family"]] != row["split"]:
            raise ValueError("Scenario family crosses a split")
        if len(row["text"].encode("utf-8", "strict")) > readout.MAX_TEXT_BYTES:
            raise ValueError("Training text exceeds runtime budget")
        shared.source_windows(row["text"])
        ids.add(row["id"])
        texts.add(row["text"])
        families[row["family"]] = row["split"]
        splits[row["split"]].append(row)
    for split, rows in splits.items():
        if (len(rows) != protocol["split_counts"][split]
                or len({r["family"] for r in rows}) != protocol["family_counts"][split]
                or set(r["action"] for r in rows) != set(readout.ACTIONS)):
            raise ValueError("Frozen split composition changed")
        for family in {r["family"] for r in rows}:
            paired = [r for r in rows if r["family"] == family]
            if (len(paired) != 2 or {r["language"] for r in paired} != {"ar", "en"}
                    or paired[0]["action"] != paired[1]["action"]
                    or paired[0]["obligations"] != paired[1]["obligations"]):
                raise ValueError("Bilingual scenario must stay paired")
    if len(data["outside_scope"]) != protocol["outside_scope_count"]:
        raise ValueError("Frozen outside-domain probes changed")
    for row in data["outside_scope"]:
        if (type(row) is not dict or set(row) != {"id", "language", "text", "expected"}
                or row["expected"] != "DEFER_OUTSIDE_DECLARED_DOMAIN"
                or row["language"] not in ("ar", "en")
                or row["id"] in ids or row["text"] in texts):
            raise ValueError("Invalid outside-domain row")
        shared.source_windows(row["text"])
        ids.add(row["id"])
        texts.add(row["text"])
    return splits


def inputs():
    data_bytes, protocol_bytes = TRAINING.read_bytes(), PROTOCOL.read_bytes()
    data = strict_loads(data_bytes, maximum_bytes=2_000_000, report=True)
    protocol = strict_loads(protocol_bytes, maximum_bytes=50_000, report=True)
    if sha256(data_bytes).hexdigest() != protocol["data_sha256"]:
        raise ValueError("Frozen corpus identity changed")
    return data, protocol, validate_data(data, protocol), sha256(protocol_bytes).hexdigest()


def fit_head(vectors, labels, classes, alpha=.25):
    """Class-balanced ridge on known targets only, including a penalized bias.

    A None target contributes no design row, response row or class count. This
    is also the small independently testable masked-label boundary.
    """
    import numpy as np
    if len(vectors) != len(labels) or not vectors or len(set(classes)) != len(classes):
        raise ValueError("Invalid fit arrays")
    known = [(v, label) for v, label in zip(vectors, labels, strict=True) if label is not None]
    if any(label not in classes for _, label in known):
        raise ValueError("Unknown training target")
    counts = Counter(label for _, label in known)
    if set(counts) != set(classes):
        raise ValueError("Each target class requires training observations")
    x = np.asarray([list(v) + [1.] for v, _ in known], dtype=np.float64)
    y = np.asarray([[float(label == c) for c in classes] for _, label in known], dtype=np.float64)
    weights = np.asarray([1. / counts[label] for _, label in known], dtype=np.float64)
    if not np.isfinite(x).all() or not math.isfinite(alpha) or alpha <= 0:
        raise ValueError("Nonfinite or unregularized fit")
    fitted = np.linalg.solve((x.T * weights) @ x + alpha * np.eye(x.shape[1]),
                             (x.T * weights) @ y).T
    if not np.isfinite(fitted).all():
        raise ValueError("Nonfinite trained weights")
    return fitted.round(10).tolist(), {
        "observed": len(known), "masked": len(labels) - len(known),
        "class_counts": {str(c).lower(): counts[c] for c in classes}}


def fit_readouts(training_rows, training_vectors, protocol, protocol_sha):
    """No development/test rows or labels are accepted at this fitting boundary."""
    import numpy as np
    if (len(training_rows) != len(training_vectors) or not training_rows
            or any(row.get("split") != "train" for row in training_rows)):
        raise ValueError("Only training rows may fit weights or normalization")
    matrix = np.asarray(training_vectors, dtype=np.float64)
    if matrix.shape != (len(training_rows), readout.DIM) or not np.isfinite(matrix).all():
        raise ValueError("Invalid frozen feature matrix")
    mean = matrix.mean(axis=0).round(10)
    scale = np.maximum(matrix.std(axis=0), .05).round(10)
    x = ((matrix - mean) / scale).tolist()
    action, action_counts = fit_head(x, [r["action"] for r in training_rows], readout.ACTIONS,
                                     protocol["alpha"])
    weights, counts = {}, {}
    for name in readout.OBLIGATIONS:
        weights[name], counts[name] = fit_head(x, [r["obligations"][name] for r in training_rows],
                                              (False, True), protocol["alpha"])
    return {"schema": readout.MODEL_SCHEMA, "authority": "NONE",
            "encoder_sha256": readout.ENCODER_SHA256, "features": readout.FEATURES,
            "dimension": readout.DIM, "actions": list(readout.ACTIONS),
            "obligations": list(readout.OBLIGATIONS), "feature_mean": mean.tolist(),
            "feature_scale": scale.tolist(), "action_weights": action,
            "obligation_weights": weights, "training_sha256": identity(training_rows),
            "development_sha256": "0" * 64, "protocol_sha256": protocol_sha,
            "fit": {"method": "MASKED_CLASS_BALANCED_RIDGE", "alpha": protocol["alpha"],
                    "encoder_updated": False, "target_true_false_order": [False, True],
                    "normalization_rows": len(training_rows), "normalization_split": "train",
                    "action_targets": action_counts, "obligation_targets": counts,
                    "none_targets_are_negative": False, "seed_used": False,
                    "initialization": "CLOSED_FORM_NO_RANDOM_INITIALIZATION"},
            "calibration": {"min_action_score": 0., "min_action_margin": 0.,
                            "obligation_thresholds": dict.fromkeys(readout.OBLIGATIONS, .5),
                            "selection": "DEVELOPMENT_ONLY_FIXED_GRID",
                            "calibrated_probabilities": False}}


def binary_counts(gold, predicted):
    values = [(g, p) for g, p in zip(gold, predicted, strict=True) if g is not None]
    tp = sum(g is True and p is True for g, p in values)
    fp = sum(g is False and p is True for g, p in values)
    fn = sum(g is True and p is False for g, p in values)
    tn = sum(g is False and p is False for g, p in values)
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.
    recalls = [a / (a + b) for a, b in ((tp, fn), (tn, fp)) if a + b]
    return {"labelled": len(values), "masked": len(gold) - len(values),
            "tp": tp, "fp": fp, "fn": fn, "tn": tn, "f1": f1,
            "balanced_accuracy": sum(recalls) / len(recalls) if recalls else None}


def calibrate(model, development_rows, development_vectors, protocol):
    if (not development_rows or len(development_rows) != len(development_vectors)
            or any(row.get("split") != "development" for row in development_rows)):
        raise ValueError("Threshold selection accepts development rows only")
    scores = [readout.vector_scores(model, vector) for vector in development_vectors]
    action_candidates = []
    for score_floor in protocol["action_score_grid"]:
        for margin_floor in protocol["action_margin_grid"]:
            correct, wrong, deferred = 0, 0, 0
            for row, (action_scores, _) in zip(development_rows, scores, strict=True):
                ranking = sorted(zip(readout.ACTIONS, action_scores, strict=True), key=lambda p: (-p[1], p[0]))
                margin = ranking[0][1] - ranking[1][1]
                if ranking[0][1] < score_floor or margin < margin_floor or margin <= 1e-12:
                    deferred += 1
                elif ranking[0][0] == row["action"]:
                    correct += 1
                else:
                    wrong += 1
            action_candidates.append({"score": score_floor, "margin": margin_floor,
                                      "correct": correct, "wrong": wrong, "deferred": deferred,
                                      "utility": round(correct - wrong - .1 * deferred, 10)})
    best = max(action_candidates, key=lambda v: (v["utility"], v["correct"] + v["wrong"],
                                                -v["score"], -v["margin"]))
    chosen, threshold_trials = {}, {}
    for name in readout.OBLIGATIONS:
        gold = [r["obligations"][name] for r in development_rows]
        trials = [{"threshold": threshold, **binary_counts(gold, [o[name] >= threshold for _, o in scores])}
                  for threshold in protocol["obligation_threshold_grid"]]
        chosen[name] = max(trials, key=lambda v: (v["f1"], v["balanced_accuracy"],
                                                -abs(v["threshold"] - .5), -v["threshold"]))["threshold"]
        threshold_trials[name] = trials
    model["development_sha256"] = identity(development_rows)
    model["calibration"].update(min_action_score=best["score"], min_action_margin=best["margin"],
                                 obligation_thresholds=chosen)
    return {"source_split": "development", "rows": len(development_rows),
            "test_labels_consumed": 0, "selected_action_trial": best,
            "action_trials": action_candidates, "obligation_trials": threshold_trials}


def action_metrics(rows, predictions):
    count = len(rows)
    issued = [p for p in predictions if p["status"] == "PROPOSED"]
    correct = sum(p["action"] == r["action"] for r, p in zip(rows, predictions, strict=True))
    forced = sum(p["forced_action"] == r["action"] for r, p in zip(rows, predictions, strict=True))
    confusion = {label: dict.fromkeys(readout.ACTIONS, 0) for label in readout.ACTIONS}
    by_language, by_class = {}, {}
    for row, proposal in zip(rows, predictions, strict=True):
        confusion[row["action"]][proposal["forced_action"]] += 1
    for key, destination in (("language", by_language), ("action", by_class)):
        for value in sorted({r[key] for r in rows}):
            selected = [(r, p) for r, p in zip(rows, predictions, strict=True) if r[key] == value]
            destination[value] = {"rows": len(selected),
                                  "forced_correct": sum(r["action"] == p["forced_action"] for r, p in selected),
                                  "issued": sum(p["status"] == "PROPOSED" for _, p in selected),
                                  "issued_correct": sum(r["action"] == p["action"] for r, p in selected)}
    return {"rows": count, "forced_correct": forced, "forced_accuracy": forced / count,
            "issued": len(issued), "deferred": count - len(issued), "coverage": len(issued) / count,
            "issued_correct": correct, "selective_accuracy": correct / len(issued) if issued else None,
            "by_language": by_language, "by_class": by_class, "forced_confusion": confusion}


def obligation_metrics(rows, predictions):
    by_label = {name: binary_counts([r["obligations"][name] for r in rows],
                                   [p["obligations"][name] for p in predictions])
                for name in readout.OBLIGATIONS}
    tp, fp, fn = [sum(v[k] for v in by_label.values()) for k in ("tp", "fp", "fn")]
    exact = sum(all(g is None or g == p["obligations"][name] for name, g in r["obligations"].items())
                for r, p in zip(rows, predictions, strict=True))
    return {"by_label": by_label, "macro_f1": sum(v["f1"] for v in by_label.values()) / len(by_label),
            "micro_f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.,
            "labelled_targets": sum(v["labelled"] for v in by_label.values()),
            "masked_targets": sum(v["masked"] for v in by_label.values()),
            "exact_annotated_set_rows": exact, "exact_annotated_set_accuracy": exact / len(rows)}


def baselines(training_rows, training_vectors, rows, vectors):
    counts = Counter(r["action"] for r in training_rows)
    majority = sorted(counts, key=lambda label: (-counts[label], label))[0]
    binary = {name: sum(r["obligations"][name] is True for r in training_rows) >
                    sum(r["obligations"][name] is False for r in training_rows)
              for name in readout.OBLIGATIONS}
    majority_predictions = [{"status": "PROPOSED", "action": majority, "forced_action": majority,
                             "obligations": binary} for _ in rows]
    def cosine(a, b):
        norm = math.sqrt(sum(v * v for v in a) * sum(v * v for v in b))
        return sum(x * y for x, y in zip(a, b, strict=True)) / norm if norm else 0.
    nearest = []
    for vector in vectors:
        index = max(range(len(training_rows)), key=lambda i: (cosine(vector, training_vectors[i]), -i))
        label = training_rows[index]["action"]
        nearest.append({"status": "PROPOSED", "action": label, "forced_action": label})
    return {"train_majority_action": majority, "majority_action": action_metrics(rows, majority_predictions),
            "majority_obligations": obligation_metrics(rows, majority_predictions),
            "nearest_frozen_vector_action": action_metrics(rows, nearest),
            "nearest_note": "Cosine on original frozen vectors; nearest training label; no development/test fit."}


def numpy_parity(model, vectors):
    """Independent matrix implementation checks the portable readout arithmetic."""
    import numpy as np
    x = (np.asarray(vectors) - np.asarray(model["feature_mean"])) / np.asarray(model["feature_scale"])
    x = np.column_stack((x, np.ones(len(x))))
    def softmax(weights):
        logits = x @ np.asarray(weights).T
        values = np.exp(logits - logits.max(axis=1, keepdims=True))
        return values / values.sum(axis=1, keepdims=True)
    action = softmax(model["action_weights"])
    binary = {name: softmax(model["obligation_weights"][name])[:, 1] for name in readout.OBLIGATIONS}
    maximum = 0.
    for index, vector in enumerate(vectors):
        a, b = readout.vector_scores(model, vector)
        maximum = max(maximum, *(abs(float(n) - p) for n, p in zip(action[index], a, strict=True)),
                      *(abs(float(binary[name][index]) - b[name]) for name in readout.OBLIGATIONS))
    if maximum > 1e-12:
        raise ValueError("Portable/NumPy readout mismatch")
    return {"rows": len(vectors), "maximum_absolute_score_error": maximum, "tolerance": 1e-12,
            "passed": True, "claim": "Arithmetic parity only; no semantic refinement theorem."}


def release_decision(report):
    """Deployment annotation made after evaluation; it never alters the fit."""
    test = report["splits"]["test"]
    return {"policy": "REVIEW_ONLY", "automatic_action_selection": False,
            "decision_timing": "AFTER_FIRST_FROZEN_EVALUATION_NO_RETRAINING",
            "model_or_thresholds_changed_after_test": False,
            "reasons": ["Held-out action and obligation quality is insufficient for automatic selection.",
                        "Development-selected abstention did not improve held-out accuracy.",
                        "Outside-domain false proposals show that confidence is not a domain contract."],
            "observed": {"train_action_accuracy": report["splits"]["train"]["actions"]["forced_accuracy"],
                         "development_action_accuracy": report["splits"]["development"]["actions"]["forced_accuracy"],
                         "test_action_accuracy": test["actions"]["forced_accuracy"],
                         "test_selective_accuracy": test["actions"]["selective_accuracy"],
                         "test_obligation_exact_set_accuracy": test["obligations"]["exact_annotated_set_accuracy"],
                         "outside_scope_unsupported_proposals": report["outside_scope"]["unsupported_proposals"]},
            "diagnosis": "Training versus held-out performance shows overfit in this corpus/representation/readout setup; it does not isolate the encoder as the causal failure.",
            "enforcement": "The independent school owner selects the fixed eligible teaching action; this flag alone grants no authority."}


def evaluate(model, data, splits, vectors, calibration_audit, protocol):
    report = {"schema": "nabt.ntl-apprentice-evaluation.v1", "authority": "NONE",
              "source_commit": protocol["source_commit"], "model_sha256": sha256(encoded(model)).hexdigest(),
              "encoder_sha256": model["encoder_sha256"], "training_corpus_sha256": protocol["data_sha256"],
              "training_rows_sha256": model["training_sha256"],
              "development_rows_sha256": model["development_sha256"],
              "test_rows_sha256": identity(splits["test"]), "protocol_sha256": model["protocol_sha256"],
              "calibration": calibration_audit, "splits": {},
              "fit_boundary": {"weight_rows": "train", "normalization_rows": "train",
                               "threshold_rows": "development", "test_labels_used_for_selection": 0,
                               "outside_domain_labels_used_for_selection": 0,
                               "masked_none_targets_in_fit": sum(v["masked"] for v in model["fit"]["obligation_targets"].values()),
                               "none_replaced_with_false": False},
              "interpretation": [
                  "One fixed fit and development threshold selection; held-out test/OOD mistakes were retained.",
                  "All rows are original synthetic examples authored by the implementer, not an independently adjudicated school sample.",
                  "Scenario families and their language variants are isolated; topical vocabulary may still recur across families.",
                  "Frozen features precede this task; target-labelled ridge readouts are newly fitted, with no encoder update.",
                  "Small held-out accuracy cannot establish population reliability, concept discovery, explanation quality or human learning.",
                  "The classifier has no authoritative domain detector. OOD false proposals require the separate input/domain/action gates.",
                  "False obligation targets mean not assigned in that teaching annotation; null targets are unadjudicated, never negative evidence.",
                  "Runtime scores grant no admission, permission, truth, curriculum coverage, IB grade or learner mastery."]}
    for split, rows in splits.items():
        predictions = [readout.decide(model, vectors[r["id"]]) for r in rows]
        report["splits"][split] = {
            "actions": action_metrics(rows, predictions), "obligations": obligation_metrics(rows, predictions),
            "baselines": baselines(splits["train"], [vectors[r["id"]] for r in splits["train"]],
                                   rows, [vectors[r["id"]] for r in rows]),
            "predictions": [{"id": r["id"], "family": r["family"], "language": r["language"],
                             "gold_action": r["action"], "gold_obligations": r["obligations"],
                             **p} for r, p in zip(rows, predictions, strict=True)]}
    outside = [{"id": row["id"], "language": row["language"], "expected": row["expected"],
                **readout.decide(model, vectors[row["id"]])} for row in data["outside_scope"]]
    report["outside_scope"] = {"rows": len(outside),
                               "deferred": sum(r["status"] == "DEFER" for r in outside),
                               "unsupported_proposals": sum(r["status"] == "PROPOSED" for r in outside),
                               "predictions": outside}
    report["portable_parity"] = numpy_parity(model, list(vectors.values()))
    report["weights_differ_from_zero"] = any(abs(v) > 0 for row in model["action_weights"] for v in row)
    report["release_decision"] = release_decision(report)
    return report


def build():
    """Return a fixed fitted/calibrated model before any test vector is scored."""
    data, protocol, splits, protocol_sha = inputs()
    encoder, fingerprint = shared.load_model()
    if fingerprint != readout.ENCODER_SHA256:
        raise ValueError("Installed encoder identity differs from frozen protocol")
    vectors = {}
    def features(rows):
        for row in rows:
            vectors[row["id"]] = witness_recall.vector(encoder, row["text"])
        return [vectors[r["id"]] for r in rows]
    print("Encoding training sources with the unchanged portable GRU...", flush=True)
    training_vectors = features(splits["train"])
    model = fit_readouts(splits["train"], training_vectors, protocol, protocol_sha)
    print("Selecting fixed-grid thresholds on development families only...", flush=True)
    audit = calibrate(model, splits["development"], features(splits["development"]), protocol)
    readout.validate_model(model)
    if sha256(shared.MODEL.read_bytes()).hexdigest() != fingerprint:
        raise ValueError("Encoder was modified during training")
    return model, data, protocol, splits, vectors, audit, encoder


def _difference(left, right):
    """Exact structure and identities, bounded tolerance for float-only drift."""
    if type(left) is not type(right):
        raise ValueError("Replay type differs")
    if type(left) is dict:
        if left.keys() != right.keys():
            raise ValueError("Replay fields differ")
        return max((_difference(left[k], right[k]) for k in left), default=0.)
    if type(left) is list:
        if len(left) != len(right):
            raise ValueError("Replay length differs")
        return max((_difference(a, b) for a, b in zip(left, right, strict=True)), default=0.)
    if type(left) is float:
        if not math.isfinite(left) or not math.isfinite(right):
            raise ValueError("Nonfinite replay number")
        return abs(left - right)
    if left != right:
        raise ValueError("Replay nonnumerical identity differs")
    return 0.


def run(write=False):
    if write and (readout.MODEL.exists() or EVALUATION.exists()):
        raise FileExistsError("First-fit artifacts already exist; --check never rewrites them")
    model, data, protocol, splits, vectors, audit, encoder = build()
    raw = encoded(model)
    if write:
        # Freeze the artifact before feature extraction or scoring of held-out test/OOD.
        with readout.MODEL.open("xb") as file:
            file.write(raw)
        comparison = {"mode": "FIRST_FIXED_FIT", "byte_identical": True, "maximum_weight_error": 0.}
    else:
        installed_bytes = readout.MODEL.read_bytes()
        if sha256(installed_bytes).hexdigest() != readout.MODEL_SHA256:
            raise ValueError("Installed model SHA does not match runtime identity")
        installed = readout.validate_model(strict_loads(installed_bytes, maximum_bytes=readout.MAX_MODEL_BYTES, report=True))
        difference = _difference(model, installed)
        if difference > TOLERANCE:
            raise ValueError("Fit replay exceeded numerical tolerance")
        comparison = {"mode": "REPLAY", "byte_identical": raw == installed_bytes,
                      "maximum_weight_error": difference, "tolerance": TOLERANCE}
        # Evaluate the installed bytes so the record remains tied to the admitted identity.
        model = installed
    print("Model frozen; evaluating held-out families and outside-domain probes...", flush=True)
    for row in splits["test"] + data["outside_scope"]:
        vectors[row["id"]] = witness_recall.vector(encoder, row["text"])
    evaluation = evaluate(model, data, splits, vectors, audit, protocol)
    if write:
        with EVALUATION.open("xb") as file:
            file.write(encoded(evaluation))
    else:
        recorded = strict_loads(EVALUATION.read_bytes(), maximum_bytes=2_000_000, report=True)
        difference = _difference(evaluation, recorded)
        if difference > TOLERANCE:
            raise ValueError("Frozen evaluation replay exceeded numerical tolerance")
        comparison["maximum_evaluation_error"] = difference
    print(json.dumps({"model_sha256": sha256(encoded(model)).hexdigest(), "replay": comparison,
                      "test_actions": evaluation["splits"]["test"]["actions"],
                      "test_obligations": {k: v for k, v in evaluation["splits"]["test"]["obligations"].items()
                                           if k != "by_label"},
                      "outside_scope": {k: v for k, v in evaluation["outside_scope"].items() if k != "predictions"},
                      "portable_parity": evaluation["portable_parity"]}, ensure_ascii=False, sort_keys=True))
    return evaluation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="First fit only; refuse existing model/evaluation")
    mode.add_argument("--check", action="store_true", help="Replay exact identity or bounded LAPACK float drift, no writes")
    args = parser.parse_args()
    run(write=args.write)


if __name__ == "__main__":
    main()
