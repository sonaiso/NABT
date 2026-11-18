"""Frozen primitive fit and complete finite update evaluation; no test-based selection."""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256
from itertools import product
import json
import math
import random

from . import update_memory_model as model

# Independently declared primitive truth tables; episode outcomes never enter fit.
TABLE = {"and": [0, 0, 0, 1], "or": [0, 1, 1, 1]}


def primitive_rows():
    return [{"operator": op, "input": list(pair), "target": label}
            for op, labels in TABLE.items()
            for pair, label in zip(product((0, 1), repeat=2), labels, strict=True)]


def loss_gradient(parameters, rows):
    gradient = {op: [0.0] * 3 for op in TABLE}
    loss = 0.0
    for row in rows:
        op, (a, b), y = row["operator"], row["input"], row["target"]
        z = sum(w * x for w, x in zip(parameters[op], [1.0, a, b], strict=True))
        loss += max(z, 0.0) - z * y + math.log1p(math.exp(-abs(z)))
        residual = model.sigmoid(z) - y
        for j, x in enumerate((1.0, a, b)):
            gradient[op][j] += residual * x / len(rows)
    return loss / len(rows), gradient


def fit(protocol):
    raw = (model.DIRECTORY / "protocol.json").read_bytes()
    if (sha256(raw).hexdigest() != model.PROTOCOL_SHA256 or
            json.dumps(protocol, sort_keys=True, allow_nan=False) !=
            json.dumps(json.loads(raw), sort_keys=True, allow_nan=False)):
        raise ValueError("Fit requires the exact frozen protocol")
    rng = random.Random(protocol["seed"])
    initial = {op: [rng.uniform(-0.2, 0.2) for _ in range(3)] for op in TABLE}
    parameters = deepcopy(initial)
    history = []
    rows = primitive_rows()
    for epoch in range(protocol["epochs"] + 1):
        loss, gradient = loss_gradient(parameters, rows)
        if epoch % 100 == 0 or epoch == protocol["epochs"]:
            history.append({"epoch": epoch, "loss": loss})
        if epoch != protocol["epochs"]:
            for op in TABLE:
                for j in range(3):
                    parameters[op][j] -= protocol["learning_rate"] * gradient[op][j]
    return initial, parameters, history


def gradient_check(parameters):
    _, analytic = loss_gradient(parameters, primitive_rows())
    rows = []
    for op in TABLE:
        for j in range(3):
            plus, minus = deepcopy(parameters), deepcopy(parameters)
            plus[op][j] += 1e-5
            minus[op][j] -= 1e-5
            numeric = (loss_gradient(plus, primitive_rows())[0] - loss_gradient(minus, primitive_rows())[0]) / 2e-5
            rows.append({"operator": op, "parameter": j, "analytic": analytic[op][j],
                         "numeric": numeric, "error": abs(numeric - analytic[op][j])})
    return rows


def reference(state):
    h, l, e, n, s = state
    return [int(h == 1 and l == 1), e, n, s]


def contexts():
    return [None] + [[i, value] for i in range(5) for value in (0, 1)]


def apply(state, action):
    result = list(state)
    if action is not None:
        result[action[0]] = action[1]
    return result


def evaluate(initial, trained):
    states = list(product((0, 1), repeat=5))
    actions = contexts()
    sources = [{"id": f"s{i}", "role": role} for i, role in enumerate(model.ROLES)]
    rows, signatures = [], set()
    answer_only = defaultdict(Counter)
    for state in states:
        signatures.add(tuple(tuple(reference(apply(state, action))) for action in actions))
        for a_index, first in enumerate(actions):
            once = apply(state, first)
            answer_only[(tuple(reference(state)), a_index)][tuple(reference(once))] += 1
            for b_index, second in enumerate(actions):
                after = apply(once, second)
                active = {f"s{i}" for i, value in enumerate(after) if value}
                predictions = {name: model.predict(parameters, sources, active)
                               for name, parameters in (("untrained", initial), ("trained", trained))}
                rows.append({"initial_memory": list(state), "actions": [first, second],
                             "final_memory": after, "reference": reference(after),
                             "untrained": predictions["untrained"]["prediction"],
                             "trained": predictions["trained"]["prediction"],
                             "trained_scores": predictions["trained"]["scores"],
                             "single_step": b_index == 0})
    metrics = {}
    for length, selected in (("single_step", [r for r in rows if r["single_step"]]), ("two_step", rows)):
        metrics[length] = {"count": len(selected), **{
            name + "_correct": sum(r[name] == r["reference"] for r in selected)
            for name in ("untrained", "trained")}}
    metrics.update(current_classes=len({tuple(reference(s)) for s in states}), update_classes=len(signatures),
        answer_only_best_single_step_correct=sum(max(counts.values()) for counts in answer_only.values()),
        answer_only_single_step_count=len(states) * len(actions))
    # Repeated OR composition has fresh witness IDs and depths absent from the
    # primitive fit. Exactly one source per slot was used in the finite model.
    alternate = []
    for width in (2, 4, 8, 12):
        # Within the public maximum 12 total sources, reserve two law witnesses.
        sources = ([{"id": f"new_p{i}", "role": "property"} for i in range(width - 2)] +
                   [{"id": "new_l0", "role": "law"}, {"id": "new_l1", "role": "law"}])
        for mask in range(1 << len(sources)):
            active = {s["id"] for i, s in enumerate(sources) if mask & (1 << i)}
            expected = [int(any(s["role"] == "property" and s["id"] in active for s in sources)
                            and any(s["role"] == "law" and s["id"] in active for s in sources)), 0, 0, 0]
            prediction = model.predict(trained, sources, active)
            alternate.append({"source_count": width, "active": sorted(active), "reference": expected,
                              "prediction": prediction["prediction"], "scores": prediction["scores"]})
    metrics["alternative_support"] = {"count": len(alternate),
        "correct": sum(r["reference"] == r["prediction"] for r in alternate)}
    return {"metrics": metrics, "rows": rows, "alternative_support": alternate}


def train():
    raw = (model.DIRECTORY / "protocol.json").read_bytes()
    protocol = json.loads(raw)
    if sha256(raw).hexdigest() != model.PROTOCOL_SHA256:
        raise ValueError("Frozen fitting contract changed")
    initial, trained, history = fit(protocol)
    result = {"schema": "nabt.update-memory-model.v1", "parameters": trained,
              "protocol_sha256": sha256(raw).hexdigest(), "authority": "NONE", "release_policy": "REVIEW_ONLY"}
    gradient = gradient_check(initial)
    evaluation = evaluate(initial, trained)
    training = {"schema": "nabt.update-memory-training.v1", "protocol_sha256": sha256(raw).hexdigest(),
                "protocol_commit": "3af6a878c983b07a7b5dbeb87d5f1c6986553b81",
                "primitive_rows": primitive_rows(), "initial_parameters": initial, "parameters": trained,
                "history": history, "gradient_check": gradient,
                "max_gradient_error": max(r["error"] for r in gradient),
                "parameter_changes": {op: [b-a for a,b in zip(initial[op], trained[op], strict=True)] for op in TABLE},
                "scope": "All primitive cases fitted; held-out composition, not held-out primitive truth tables",
                "evaluation": evaluation["metrics"]}
    return result, training, evaluation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    artifacts = dict(zip(("model.json", "training.json", "evaluation.json"), train(), strict=True))
    for name, content in artifacts.items():
        path = model.DIRECTORY / name
        raw = (json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
        if args.check:
            # Float tolerance is for cross-platform libm only; every prediction,
            # input, reference and structural field must remain exact.
            def same(a, b):
                if type(a) is float and type(b) is float:
                    return math.isclose(a, b, rel_tol=0, abs_tol=2e-9)
                if type(a) is not type(b): return False
                if type(a) is dict: return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
                if type(a) is list: return len(a) == len(b) and all(same(x,y) for x,y in zip(a,b))
                return a == b
            if not same(json.loads(path.read_bytes()), content):
                raise ValueError("Retained fitting result changed: " + name)
        else:
            if path.exists():
                raise ValueError("Refusing to overwrite retained result: " + name)
            path.write_bytes(raw)
    print(json.dumps({"reproduced": args.check, "model_sha256": sha256((model.DIRECTORY / "model.json").read_bytes()).hexdigest(),
                      "metrics": artifacts["evaluation.json"]["metrics"],
                      "max_gradient_error": artifacts["training.json"]["max_gradient_error"]}, indent=2))


if __name__ == "__main__":
    main()
