"""Continue the complete cumulative parent; select nothing on assessment gold.

NumPy is needed for fitting only. The deployed owner uses the standard library.
Both variants keep the identical frozen parent output skip and replay every
eligible inherited task. Checkpoints contain the optimizer, not just weights.
"""

import argparse
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path

import numpy as np

from . import cumulative_v14_model as model, cumulative_features as features
from . import cumulative_lesson as previous

PROTOCOL = model.DIRECTORY / "protocol.json"


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (model.canonical(value) + "\n").encode()
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def _softmax(z):
    p = np.exp(z - z.max(axis=1, keepdims=True))
    return p / p.sum(axis=1, keepdims=True)


def prepare(protocol, pack=None):
    """Build fitting/calibration data from TRAIN rows, never assessment answers."""
    pm, pmodel = model.parent()
    pack = model.read(previous.DIRECTORY / "examples.json.gz") if pack is None else pack
    rows = pack["rows"]
    training = [r for r in rows if r["split"] == "train"]
    train_texts = {r["text"] for r in training}
    if train_texts & {r["text"] for r in rows if r["split"] == "test"}:
        raise ValueError("Held-out input leaked into V14 training")
    tasks, labels = pm["tasks"], pm["labels"]
    grouped = {t: {} for t in tasks}
    for r in training:
        if r["task"] not in labels:
            continue
        t, text, gold = r["task"], r["text"], r["gold"]
        if gold not in labels[t]:
            raise ValueError("Training class differs from inherited output identity")
        if text in grouped[t] and grouped[t][text] != gold:
            raise ValueError("Conflicting training answers")
        grouped[t][text] = gold
    for t in tasks:
        if set(grouped[t].values()) != set(labels[t]):
            raise ValueError("An inherited task or training class was dropped")
    texts = sorted({s for g in grouped.values() for s in g})
    ids = {s: i for i, s in enumerate(texts)}
    development = {s for s in texts if int(model.digest(("v14-development:" + s).encode()), 16) % 5 == 0}
    moved = []
    # Moving a text is global, so a duplicate cannot cross fit/calibration tasks.
    for task in tasks:
        for label in labels[task]:
            candidates = sorted(s for s, y in grouped[task].items() if y == label)
            if all(s in development for s in candidates):
                text = candidates[0]
                development.remove(text)
                moved.append({"text_sha256": model.digest(text.encode()), "task": task, "label": label})
    lower = features.parents()
    X = np.array([features.features(s, lower) for s in texts], dtype=np.float64)
    W0 = np.array(pmodel["shared_columns"], dtype=np.float64).T
    H0 = np.tanh(X @ W0)
    skill_blocks, bases, teachers, groups = [], {}, {}, {}
    for t in tasks:
        head = np.array(pmodel["heads"][t], dtype=np.float64).T
        z = H0 @ head[:-1] + head[-1]
        prob = _softmax(z)
        skill_blocks.append(prob - 1 / len(labels[t]))
        for split in ("fit", "development"):
            pairs = sorted((s, y) for s, y in grouped[t].items() if (s in development) == (split == "development"))
            idx = np.array([ids[s] for s, _ in pairs], dtype=np.int64)
            y = np.array([labels[t].index(y) for _, y in pairs], dtype=np.int64)
            groups[t, split] = {"indices": idx, "targets": y, "texts": [s for s, _ in pairs]}
        bases[t], teachers[t] = z, prob
    Z = np.concatenate([X, H0, *skill_blocks], axis=1)
    layout = model.make_layout(pm, pmodel)
    if Z.shape[1] != layout["dimension"]:
        raise ValueError("Inherited feature layout mismatch")
    partition = {
        "fit_text_sha256": [model.digest(s.encode()) for s in texts if s not in development],
        "development_text_sha256": [model.digest(s.encode()) for s in texts if s in development],
        "moved_to_preserve_training_classes": moved,
    }
    training_records = [[t, s, grouped[t][s]] for t in tasks for s in sorted(grouped[t])]
    signature = {
        "protocol_sha256": model.digest(model.canonical(protocol).encode()),
        "parent_weights_sha256": previous.PINS["weights.json.gz"],
        "parent_manifest_sha256": previous.PINS["manifest.json"],
        "training_records_sha256": model.digest(model.canonical(training_records).encode()),
        "partition_sha256": model.digest(model.canonical(partition).encode()),
        "layout_sha256": model.digest(model.canonical(layout).encode()),
    }
    return dict(protocol=protocol, parent_manifest=pm, parent_model=pmodel, tasks=tasks, labels=labels,
                texts=texts, features=Z, bases=bases, teachers=teachers, groups=groups,
                layout=layout, partition=partition, signature=signature,
                training_pairs=len(training_records), source_training_rows=len(training),
                all_source_tasks=len({r["task"] for r in rows}))


def initial_state(data, protocol):
    rng = np.random.default_rng(protocol["seed"])
    width, dim = protocol["adapter_hidden"], data["layout"]["dimension"]
    parameters = {
        "adapter": rng.normal(0, 1 / dim ** .5, (dim, width)),
        "bias": np.zeros(width, dtype=np.float64),
    }
    parameters.update({"head:" + t: np.zeros((width + 1, len(data["labels"][t])), dtype=np.float64) for t in data["tasks"]})
    return {"step": 0, "parameters": parameters,
            "first_moments": {k: np.zeros_like(v) for k, v in parameters.items()},
            "second_moments": {k: np.zeros_like(v) for k, v in parameters.items()},
            "history": []}


def feature_view(data, variant):
    if variant not in ("full", "without_task_memory"):
        raise ValueError("Unknown V14 training variant")
    Z = data["features"].copy()
    if variant == "without_task_memory":
        Z[:, data["layout"]["parent_hidden"][0]:] = 0.0
    return Z


def fit_step(state, data, protocol, Z):
    """One deterministic task-balanced Adam update, with frozen-parent distillation."""
    params = state["parameters"]
    H = np.tanh(Z @ params["adapter"] + params["bias"])
    dH = np.zeros_like(H)
    gradients = {}
    loss, ce_loss, distillation = 0.0, 0.0, 0.0
    count = len(data["tasks"])
    alpha = protocol["distillation_weight"]
    for t in data["tasks"]:
        group = data["groups"][t, "fit"]
        idx, y = group["indices"], group["targets"]
        head = params["head:" + t]
        logits = data["bases"][t][idx] + H[idx] @ head[:-1] + head[-1]
        probabilities = _softmax(logits)
        teacher = data["teachers"][t][idx]
        logs = np.log(np.maximum(probabilities, 1e-300))
        ce = -logs[np.arange(len(y)), y].mean()
        kl = np.sum(teacher * (np.log(np.maximum(teacher, 1e-300)) - logs), axis=1).mean()
        ce_loss += float(ce) / count
        distillation += float(kl) / count
        delta = (1 + alpha) * probabilities - alpha * teacher
        delta[np.arange(len(y)), y] -= 1.0
        delta /= len(y) * count
        gradients["head:" + t] = np.vstack([H[idx].T @ delta, delta.sum(axis=0)])
        np.add.at(dH, idx, delta @ head[:-1].T)
    dz = dH * (1 - H * H)
    gradients["adapter"] = Z.T @ dz
    gradients["bias"] = dz.sum(axis=0)
    decay = protocol["weight_decay"]
    penalty = decay * .5 * sum(float(np.sum(v * v)) for v in params.values())
    loss = ce_loss + alpha * distillation + penalty
    if not np.isfinite(loss):
        raise ValueError("Non-finite training loss")
    state["step"] += 1
    step = state["step"]
    for name, value in params.items():
        grad = gradients[name] + decay * value
        m, v = state["first_moments"][name], state["second_moments"][name]
        m *= .9
        m += .1 * grad
        v *= .999
        v += .001 * grad * grad
        value -= protocol["learning_rate"] * (m / (1 - .9 ** step)) / (np.sqrt(v / (1 - .999 ** step)) + 1e-8)
    # Every update is preserved so a checkpoint does not alter the timeline.
    state["history"].append({"step": step, "loss": loss, "cross_entropy": ce_loss,
                             "parent_distillation": distillation, "weight_penalty": penalty})


def _scores(task, texts, labels, gold, indices):
    expected = [model.project(task, s, labels[int(y)]) for s, y in zip(texts, gold, strict=True)]
    predicted = [model.project(task, s, labels[int(y)]) for s, y in zip(texts, indices, strict=True)]
    counts, hits = Counter(expected), Counter(y for y, p in zip(expected, predicted, strict=True) if y == p)
    return {"n": len(gold), "correct": sum(hits.values()), "classes": len(counts),
            "balanced": sum(hits[y] / n for y, n in counts.items()) / len(counts) if counts else None}


def calibrate(state, data, Z):
    params = state["parameters"]
    H = np.tanh(Z @ params["adapter"] + params["bias"])
    gates, details = {}, {}
    for t in data["tasks"]:
        group = data["groups"][t, "development"]
        idx, y = group["indices"], group["targets"]
        names = data["labels"][t]
        if len(idx) < 4 or len(set(y.tolist())) < 2:
            gates[t] = 0.0
            details[t] = {"gate": 0.0, "status": "PARENT_RETAINED_INSUFFICIENT_CALIBRATION",
                          "n": len(idx), "classes": len(set(y.tolist())), "candidates": []}
            continue
        base = data["bases"][t][idx]
        parent_score = _scores(t, group["texts"], names, y, base.argmax(1))
        head = params["head:" + t]
        delta = H[idx] @ head[:-1] + head[-1]
        best, best_loss, candidates = 0.0, float("inf"), []
        for gate in (0.0, .25, .5, 1.0):
            logits = base + gate * delta
            prob = _softmax(logits)
            loss = float(-np.log(np.maximum(prob[np.arange(len(y)), y], 1e-300)).mean())
            result = _scores(t, group["texts"], names, y, logits.argmax(1))
            eligible = result["correct"] >= parent_score["correct"] and result["balanced"] >= parent_score["balanced"]
            candidates.append(dict(result, gate=gate, negative_log_likelihood=loss, eligible=eligible))
            if eligible and loss < best_loss:
                best, best_loss = gate, loss
        gates[t] = best
        details[t] = {"gate": best, "status": "CALIBRATED_ON_TRAINING_DERIVED_INPUTS",
                      "n": len(idx), "classes": len(set(y.tolist())), "candidates": candidates}
    return gates, details


def save_checkpoint(directory, state, data, variant):
    value = {"schema": "nabt.cumulative-v14-checkpoint.v1", "variant": variant,
             "signature": data["signature"], "partition": data["partition"], "tasks": data["tasks"],
             "step": state["step"], "history": state["history"]}
    for field in ("parameters", "first_moments", "second_moments"):
        value[field] = {k: v.tolist() for k, v in state[field].items()}
    write_json(Path(directory) / "checkpoint.json.gz", value)


def restore_checkpoint(directory, data, protocol, variant):
    value = model.read(Path(directory) / "checkpoint.json.gz")
    if (value.get("schema") != "nabt.cumulative-v14-checkpoint.v1"
            or value.get("variant") != variant
            or model.canonical(value.get("signature")) != model.canonical(data["signature"])
            or model.canonical(value.get("partition")) != model.canonical(data["partition"])
            or value.get("tasks") != data["tasks"]):
        raise ValueError("Checkpoint does not belong to this parent/training partition")
    step = value.get("step")
    if type(step) is not int or not 0 <= step <= protocol["updates"]:
        raise ValueError("Invalid optimizer step")
    fresh = initial_state(data, protocol)
    fresh["step"], fresh["history"] = step, value["history"]
    if (type(fresh["history"]) is not list or len(fresh["history"]) != step
            or any(type(row) is not dict or type(row.get("step")) is not int
                   or set(row) != {"step", "loss", "cross_entropy", "parent_distillation", "weight_penalty"}
                   or any(type(row[k]) not in (int, float) or not np.isfinite(row[k])
                          for k in ("loss", "cross_entropy", "parent_distillation", "weight_penalty"))
                   for row in fresh["history"])
            or [x["step"] for x in fresh["history"]] != list(range(1, step + 1))):
        raise ValueError("Incomplete training timeline")
    for field in ("parameters", "first_moments", "second_moments"):
        if set(value[field]) != set(fresh[field]):
            raise ValueError("Checkpoint dropped task parameters")
        for k, expected in fresh[field].items():
            raw = value[field][k]
            # Explicitly reject bools rather than silently coercing them to floats.
            def numeric(x):
                return all(numeric(v) for v in x) if type(x) is list else type(x) in (int, float)
            if not numeric(raw):
                raise ValueError("Non-numeric optimizer state")
            loaded = np.array(raw, dtype=np.float64)
            if loaded.shape != expected.shape or not np.isfinite(loaded).all():
                raise ValueError("Invalid optimizer parameter shape/value")
            if field == "second_moments" and (loaded < 0).any():
                raise ValueError("Invalid negative second moment")
            fresh[field][k] = loaded
    return fresh


def write_model(directory, state, data, protocol, variant, Z):
    directory = Path(directory)
    gates, calibration = calibrate(state, data, Z)
    params = state["parameters"]
    weights = {"adapter_columns": params["adapter"].T.tolist(), "adapter_bias": params["bias"].tolist(),
               "residual_heads": {t: params["head:" + t].T.tolist() for t in data["tasks"]}, "gates": gates}
    model.validate_weights(weights, data["layout"], data["labels"], protocol["adapter_hidden"])
    training = {
        "schema": "nabt.cumulative-v14-training.v1", "variant": variant, "step": state["step"],
        "complete_budget": state["step"] == protocol["updates"], "signature": data["signature"],
        "partition": data["partition"], "history": state["history"], "calibration": calibration,
        "source_training_rows": data["source_training_rows"], "unique_eligible_training_pairs": data["training_pairs"],
        "all_source_tasks": data["all_source_tasks"], "retained_trained_tasks": len(data["tasks"]),
        "calibrated_tasks": sum(d["status"].startswith("CALIBRATED") for d in calibration.values()),
        "active_residual_tasks": sum(g > 0 for g in gates.values()),
        "fit_pairs": sum(len(data["groups"][t, "fit"]["indices"]) for t in data["tasks"]),
        "development_pairs": sum(len(data["groups"][t, "development"]["indices"]) for t in data["tasks"]),
        "fit_heldout_overlap": 0,
        "development_prior_exposure": "The retained parent already trained on these original training inputs; calibration is not independent validation.",
        "assessment_labels_used_for_gradients_or_selection": False,
        "authority": "NONE", "review_only": True,
    }
    for name, value in (("protocol.json", protocol), ("skill_layout.json", data["layout"]),
                        ("training.json", training), ("weights.json.gz", weights)):
        write_json(directory / name, value)
    manifest = {
        "schema": model.SCHEMA, "variant": variant,
        "parent": {"commit": model.PARENT_COMMIT, "weights_sha256": previous.PINS["weights.json.gz"],
                   "manifest_sha256": previous.PINS["manifest.json"], "final_stage": 143},
        "tasks": data["tasks"], "labels": data["labels"],
        "weights_sha256": model.digest((directory / "weights.json.gz").read_bytes()),
        "inputs": {name: model.digest((directory / name).read_bytes()) for name in ("protocol.json", "skill_layout.json", "training.json")},
        "source_tasks": data["all_source_tasks"], "authority": "NONE", "review_only": True,
    }
    write_json(directory / "manifest.json", manifest)
    return manifest, training


def experiment(output, *, variant="full", resume=None, stop_after=None,
               save_step=None, checkpoint_dir=None, protocol_path=None):
    protocol = model.read(Path(protocol_path) if protocol_path else PROTOCOL)
    data = prepare(protocol)
    Z = feature_view(data, variant)
    state = restore_checkpoint(resume, data, protocol, variant) if resume else initial_state(data, protocol)
    limit = protocol["updates"] if stop_after is None else stop_after
    if type(limit) is not int or not state["step"] <= limit <= protocol["updates"]:
        raise ValueError("Invalid stopping step")
    if save_step is not None and (checkpoint_dir is None or type(save_step) is not int or not state["step"] < save_step <= limit):
        raise ValueError("Expected a future checkpoint step and directory")
    while state["step"] < limit:
        fit_step(state, data, protocol, Z)
        if state["step"] % 32 == 0:
            print(model.canonical({"variant": variant, **state["history"][-1]}), flush=True)
        if state["step"] == save_step:
            save_checkpoint(checkpoint_dir, state, data, variant)
    if limit < protocol["updates"]:
        save_checkpoint(checkpoint_dir or output, state, data, variant)
        return {"status": "CHECKPOINT", "step": state["step"], "variant": variant}
    manifest, training = write_model(output, state, data, protocol, variant, Z)
    return {"status": "TRAINED", "variant": variant, "step": state["step"],
            "weights_sha256": manifest["weights_sha256"], "retained_tasks": len(data["tasks"]),
            "active_residual_tasks": training["active_residual_tasks"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=model.DIRECTORY)
    parser.add_argument("--variant", choices=("full", "without_task_memory"), default="full")
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--stop-after", type=int)
    parser.add_argument("--save-step", type=int)
    parser.add_argument("--checkpoint-dir", type=Path)
    parser.add_argument("--protocol", type=Path)
    args = parser.parse_args()
    print(model.canonical(experiment(args.output, variant=args.variant, resume=args.resume,
                                    stop_after=args.stop_after, save_step=args.save_step,
                                    checkpoint_dir=args.checkpoint_dir, protocol_path=args.protocol)))


if __name__ == "__main__":
    main()
