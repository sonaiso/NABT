"""Offline, reproducible transfer and continuation from the retained V13 probe."""
import argparse
from collections import defaultdict
from hashlib import sha256
from io import BytesIO
from itertools import combinations
import json
import math
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import numpy as np
from nabt.alphabet import parse_word
from . import v13_occurrence as owner

ARCHIVE = "NABT_V13_Learning_Probe_01.zip"
PREFIX = "NABT_V13_Learning_Probe_01/"
CHECKPOINT = "nabt.v13-change-readout.v1"


def json_bytes(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def original(protocol):
    raw = (owner.DIRECTORY / ARCHIVE).read_bytes()
    if sha256(raw).hexdigest() != protocol["source_archive_sha256"]:
        raise ValueError("Changed source archive")
    with ZipFile(BytesIO(raw)) as z:
        manifest = json.loads(z.read(PREFIX + "MANIFEST.json"))
        files = {}
        for path, spec in manifest.items():
            contents = z.read(PREFIX + path)
            if sha256(contents).hexdigest() != spec["sha256"] or len(contents) != spec["bytes"]:
                raise ValueError(f"Changed original probe member {path}")
            files[path] = contents
    basis = json.loads(files["oracle/v12/inherited/atomic_ancestry_catalog_v10.json"])
    ids = [parse_word(r["surface"]) == (i,) and r["type_id"] == i for i, r in enumerate(basis["source116_rows"])]
    if len(ids) != 116 or not all(ids):
        raise ValueError("V13 and installed A116 identities differ")
    return files


def inputs(row):
    f = row["input"]
    return {"source116_id": row["source116_input_id"], "shadda": bool(f["shadda"]),
            "tanwin": bool(f["tanwin"]), "boundary": owner.BOUNDS[f["boundary"]]}


def replay(files, rows, parent, parent_path):
    # Reference architecture layouts and column ordering from the original experiment.
    names = ("carrier_index_local", "vowel", "shadda", "tanwin", "boundary")
    x = np.concatenate([np.eye(size)[[r["input"][k] for r in rows]]
                        for k, size in zip(names, (28, 3, 2, 2, 3), strict=True)], axis=1)
    layouts = {"flat": [(x, (2, 5, 2))], "invariant": [(x[:, 28:], (2, 5, 2))],
               "modular": [(x[:, 31:33], (2,)), (x[:, [28, 29, 30, 33, 34, 35, 36, 37]], (5, 2))]}
    scores = {}
    target = np.asarray([r["target"] for r in rows])
    for reference in json.loads(files["results/predictions.json"]):
        name, seed = reference["model"], reference["seed"]
        path = f"results/{name}_{seed}.npz"
        heads = []
        with np.load(BytesIO(files[path]), allow_pickle=False) as w:
            for i, (features, widths) in enumerate(layouts[name]):
                weights = {k: w[f"net{i}_{k}"] for k in ("W1", "b1", "W2", "b2")}
                if path == parent_path:
                    for key, value in weights.items():
                        np.testing.assert_array_equal(value, parent["nets"][i][key])
                hidden = np.tanh(features @ weights["W1"] + weights["b1"])
                logits = hidden @ weights["W2"] + weights["b2"]
                heads.extend(part.argmax(axis=1) for part in np.split(logits, np.cumsum(widths)[:-1], axis=1))
        pred = np.stack(heads, axis=1)
        np.testing.assert_array_equal(pred, reference["predictions"])
        np.testing.assert_array_equal(pred, target)
        scores[f"{name}_{seed}"] = len(pred)
    if set(scores) != {f"{m}_{s}" for m in layouts for s in (17, 29, 43)}:
        raise ValueError("Incomplete checkpoint replay")
    if parent["parent_npz_sha256"] != sha256(files[parent_path]).hexdigest():
        raise ValueError("Wrong parent")
    return scores


def fixed_random_encoder():
    # Reproduce experiment.MLP initialization, including the offset for net 1.
    nets = []
    for d, h, o, seed in ((2, 8, 2, 17), (8, 24, 7, 117)):
        rng = np.random.default_rng(seed)
        nets.append({"W1": rng.normal(0, (2/(d+h))**.5, (d, h)).tolist(), "b1": [0.]*h,
                     "W2": rng.normal(0, (2/(h+o))**.5, (h, o)).tolist(), "b2": [0.]*o})
    return nets


def contrasts(rows, nets):
    groups = defaultdict(list)
    random = fixed_random_encoder()
    for row in rows:
        item = inputs(row)
        old, h = owner.observe(nets, item)
        if old["units"] != row["expected_units"]:
            raise ValueError(f"Deployed parent failed ancestry replay on {row['id']}")
        _, r = owner.observe(random, item)
        groups[row["input"]["carrier"]].append((row, item, h, r, old))
    pairs = []
    for group in groups.values():
        for (a, left, h, r, old), (b, right, k, s, other) in combinations(group, 2):
            differences = [f for f in owner.INPUTS if left[f] != right[f]]
            if len(differences) != 1:
                continue
            field = "vowel" if differences[0] == "source116_id" else differences[0]
            def signature(row):
                f = row["input"]
                return tuple(f[key] for key in ("vowel", "shadda", "tanwin", "boundary"))
            signatures = tuple(sorted((signature(a), signature(b))))
            composition = any(v[1] and v[2] for v in signatures)
            split = a["carrier_partition"] + ("_composition" if composition else "_familiar")
            label = a["expected_units"] != b["expected_units"]
            pairs.append((split, field, signatures, label, owner.difference(h, k),
                          owner.difference(r, s), old["units"] != other["units"]))
    return pairs


def train_head(x, y, weights, bias, steps, rate):
    for _ in range(steps):
        z = x @ weights + bias
        error = 1/(1+np.exp(-np.clip(z, -700, 700))) - y
        weights = weights - rate * (x.T @ error / len(y))
        bias -= rate * float(error.mean())
    return weights, bias


def score(pairs, predictions):
    result = {}
    for split in sorted({p[0] for p in pairs}):
        ids = [i for i, p in enumerate(pairs) if p[0] == split]
        result[split] = {"pairs": len(ids), "distinct_functional_pairs": len({pairs[i][2] for i in ids}),
                         "changed": sum(pairs[i][3] for i in ids)}
        for name, pred in predictions.items():
            result[split][name] = sum(bool(pred[i]) == pairs[i][3] for i in ids)
        by_field = {}
        for field in sorted({pairs[i][1] for i in ids}):
            selected = [i for i in ids if pairs[i][1] == field]
            by_field[field] = {"n": len(selected), **{key: sum(bool(v[i]) == pairs[i][3] for i in selected)
                                                      for key, v in predictions.items()}}
        result[split]["by_field"] = by_field
    return result


def resume(raw):
    c = json.loads(raw)
    if (c["schema"] != CHECKPOINT or c["parent_sha256"] != owner.PARENT_SHA
            or c["protocol_sha256"] != owner.PROTOCOL_SHA or type(c["steps"]) is not int or c["steps"] < 0
            or type(c["weights"]) is not list or len(c["weights"]) != 32
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in [*c["weights"], c["bias"]])):
        raise ValueError("Incompatible readout checkpoint")
    return np.array(c["weights"], dtype=float), float(c["bias"]), c["steps"]


def experiment(previous=None, steps=None):
    protocol = owner.checked_json("protocol.json", owner.PROTOCOL_SHA)
    parent = owner.checked_json("parent.json", owner.PARENT_SHA)
    files = original(protocol)
    rows = json.loads(files["results/dataset.json"])
    old_scores = replay(files, rows, parent, protocol["parent"])
    pairs = contrasts(rows, parent["nets"])
    train = np.array([p[0] == "train_familiar" for p in pairs])
    y = np.array([p[3] for p in pairs], dtype=float)
    x = np.array([p[4] for p in pairs])
    random_x = np.array([p[5] for p in pairs])
    optimizer = protocol["optimizer"]
    steps = optimizer["steps"] if steps is None else steps
    if type(steps) is not int or steps < 1:
        raise ValueError("Positive training steps required")
    if previous is None:
        w, b, start = np.zeros(32), 0., 0
        source = owner.PARENT_SHA
    else:
        w, b, start = resume(previous)
        source = sha256(previous).hexdigest()
    rate = optimizer["learning_rate"]
    w, b = train_head(x[train], y[train], w, b, steps, rate)
    random_w, random_b = train_head(random_x[train], y[train], np.zeros(32), 0., start+steps, rate)
    checkpoint = {"schema": CHECKPOINT, "parent_sha256": owner.PARENT_SHA, "protocol_sha256": owner.PROTOCOL_SHA,
                  "started_from_sha256": source, "steps": start+steps, "weights": w.tolist(), "bias": b}
    predictions = {"transfer": [owner.changed(checkpoint, p[4]) for p in pairs],
                   "fixed_random": random_x @ random_w + random_b >= 0,
                   "majority": np.full(len(pairs), y[train].mean() >= .5), "old_units": [p[6] for p in pairs]}
    return checkpoint, {"schema": "nabt.v13-transfer-evaluation.v1", "previous_steps": start,
                        "steps": start+steps, "checkpoint_sha256": sha256(json_bytes(checkpoint)).hexdigest(),
                        "old_checkpoint_exact": old_scores, "deployed_parent_ancestry_exact": len(rows),
                        "splits": score(pairs, predictions)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("reproduce", "continue"))
    parser.add_argument("--output", type=Path, required=True, help="new directory")
    parser.add_argument("--from-checkpoint", type=Path, help="defaults to the installed trained readout for continue")
    parser.add_argument("--steps", type=int, help="additional full-batch steps")
    args = parser.parse_args()
    if args.output.exists() or (args.action == "reproduce" and args.from_checkpoint):
        parser.error("Choose a new output directory; reproduce always starts from the original trained parent")
    previous = None
    if args.action == "continue":
        if args.from_checkpoint:
            previous = args.from_checkpoint.read_bytes()
        else:
            previous = (owner.DIRECTORY / "checkpoint.json").read_bytes()
            if sha256(previous).hexdigest() != owner.MODEL_SHA:
                parser.error("Installed readout digest mismatch")
    checkpoint, evaluation = experiment(previous, args.steps)
    with TemporaryDirectory(dir=args.output.parent) as tmp:
        stage = Path(tmp) / "run"
        stage.mkdir()
        (stage / "checkpoint.json").write_bytes(json_bytes(checkpoint))
        (stage / "evaluation.json").write_bytes(json_bytes(evaluation))
        os.rename(stage, args.output)
    print(json.dumps({"steps": checkpoint["steps"], "checkpoint_sha256": evaluation["checkpoint_sha256"]}))


if __name__ == "__main__":
    main()
