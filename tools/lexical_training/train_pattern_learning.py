"""Train and evaluate two small CPU networks on NABT's installed generators."""
import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import random

from nabt import derivation
from . import pattern_learning as net

SEED = 11671


def aligned_inventory():
    # These root contrasts distinguish literal and radical positions in the output.
    rows = []
    for p in net.inventory():
        roots = {3: ("كتب", "درس"), 4: ("دحرج", "بعثر"), 5: ("سفرجل", "قذعمل")}[p["arity"]]
        if "slot_vowels" in p:
            # Replay the printed vowel coordinates independently of expanded_template.
            marks = "".join({"a": "َ", "i": "ِ", "u": "ُ", "0": "ْ"}[v] for v in p["slot_vowels"])
            pairs = [(r, "".join(ch + v for ch, v in zip(r[:-1], marks, strict=True)) + r[-1]) for r in roots]
        else:
            pairs = [(r, derivation.generate_derivation(r, p["id"])["stem"]) for r in roots]
        templates = net.induce(pairs)
        if templates != [p["tokens"]]:
            raise ValueError(f"Contrast does not determine {p['id']}")
        rows.append({"id": p["id"], "pairs": pairs, "tokens": templates[0], "owner": p["source_contract"]})
    return rows


def split_roots():
    rng = random.Random(SEED)
    letters = "بتثجحخدذرزسشصضطظعغفقكلمنه"
    reserved = {"كتب", "درس", "دحرج", "بعثر", "فتح", "حفظ", "جعل", "خلق"}
    reserved.update("".join(ch for ch in p["example"] if ch not in net.MARKS)
                    for p in net.inventory() if "example" in p)
    reserved.update(("قذعمل", "سفرجل"))
    splits = []
    for size in (48, 16):
        part = {}
        for arity in (3, 4, 5):
            roots = []
            while len(roots) < size:
                root = "".join(rng.sample(letters, arity))
                if root not in reserved:
                    reserved.add(root)
                    roots.append(root)
            part[arity] = roots
        splits.append(part)
    return splits


def morphology_rows(roots, inventory):
    # The network sees only the surface. Colliding labels share one target.
    rows = defaultdict(set)
    for index, (p, induced) in enumerate(zip(net.inventory(), inventory, strict=True)):
        for j, root in enumerate(roots[p["arity"]]):
            stem = "".join(root[t] if type(t) is int else t for t in induced["tokens"])
            ending = p["endings"][j % len(p["endings"])]
            marked = stem + ending
            rows[stem].add(index)
            rows[marked].add(index)
            rows["".join(ch for ch in marked if ch not in net.MARKS)].add(index)
    return sorted(rows.items())


def guard_rows(split):
    from .report_draft import COUNT_GUARDS, PENDING_GUARDS
    forms = COUNT_GUARDS if split == "train" else PENDING_GUARDS
    rows = {}
    for operator, clauses in forms.items():
        for clause in clauses:
            verb = clause.split()[1]
            for word in {verb, "".join(c for c in verb if c not in net.MARKS)}:
                for limit in ((2, 5) if split == "train" else (3, 12)):
                    for n in (limit - 1, limit, limit + 1):
                        label = n > limit if operator == "GT" else n >= limit
                        rows[word, n, limit] = {int(label)}
    return sorted(rows.items())


def arrays(rows, encode, size, classes):
    import numpy as np
    x = np.zeros((len(rows), size + 1))
    y = np.zeros((len(rows), classes))
    for i, (source, labels) in enumerate(rows):
        x[i, encode(source)] = 1
        y[i, sorted(labels)] = 1 / len(labels)
    x[:, -1] = 1
    return x, y


def fit(train, hidden, epochs):
    import numpy as np
    x, y = train
    rng = np.random.default_rng(SEED)
    w = rng.normal(0, .09, (x.shape[1], hidden))
    v = rng.normal(0, .09, (hidden + 1, y.shape[1]))
    initial = (w.copy(), v.copy())
    # Minibatch cross-entropy, including distributional targets for homographs.
    m = [np.zeros_like(w), np.zeros_like(v)]
    s = [np.zeros_like(w), np.zeros_like(v)]
    step = 0
    for _ in range(epochs):
        perm = rng.permutation(len(x))
        for k in range(0, len(x), 128):
            inds = perm[k:k + 128]
            batch = x[inds]
            h = np.maximum(0, batch @ w)
            h1 = np.column_stack((h, np.ones(len(h))))
            z = h1 @ v
            p = np.exp(z - z.max(axis=1, keepdims=True))
            err = (p / p.sum(axis=1, keepdims=True) - y[inds]) / len(inds)
            gradients = (batch.T @ ((err @ v[:-1].T) * (h > 0)), h1.T @ err)
            step += 1
            for j, (param, grad) in enumerate(zip((w, v), gradients)):
                m[j] = .9 * m[j] + .1 * grad
                s[j] = .999 * s[j] + .001 * grad**2
                param -= .008 * (m[j] / (1 - .9**step)) / ((s[j] / (1 - .999**step))**.5 + 1e-8)
    return initial, (w, v)


def quantized(params):
    import numpy as np
    result = []
    for p in params:
        scaled = np.rint(p * 128)
        if np.max(np.abs(scaled)) > 32767:
            raise ValueError("Quantization overflow")
        result.append(scaled.astype("int64"))
    return result


def measure(params, data):
    import numpy as np
    a, b = quantized(params)
    x, y = data
    h = np.maximum(0, x @ a)
    z = h @ b[:-1] + 128 * b[-1]
    ok = y[np.arange(len(x)), np.argmax(z, axis=1)] > 0
    return {"correct_top1_compatible": int(ok.sum()), "surfaces": len(x)}


def train():
    inv = aligned_inventory()
    train_roots, test_roots = split_roots()
    labels = [p["id"] for p in net.inventory()]
    report = {"seed": SEED, "selection": "FIXED_FINAL_EPOCH", "train_roots": train_roots,
              "test_roots": test_roots, "induced": inv,
              "distinct_templates": len({tuple(row["tokens"]) for row in inv})}
    model = {"schema": "ntl.surface-weights.v1", "table": derivation.EXPECTED_TABLE_SHA256,
             "nominal_table": net.NOMINAL_SHA}
    for name, targets, hidden, epochs, size, encode, train_rows, test_rows in (
            ("patterns", labels, 48, 22, net.SHAPE_INPUTS, net.features,
             morphology_rows(train_roots, inv), morphology_rows(test_roots, inv)),
            ("guard", [False, True], 12, 240, net.GUARD_INPUTS, lambda row: net.guard_features(*row),
             guard_rows("train"), guard_rows("test"))):
        if {r[0] for r in train_rows} & {r[0] for r in test_rows}:
            raise ValueError("Surface leakage")
        if name == "guard" and {r[0][0] for r in train_rows} & {r[0][0] for r in test_rows}:
            raise ValueError("Verb-form leakage")
        train_set, test_set = [arrays(rows, encode, size, len(targets)) for rows in (train_rows, test_rows)]
        initial, result = fit(train_set, hidden, epochs)
        a, b = quantized(result)
        model[name] = {"labels": targets, "hidden": hidden,
                       "input": net.pack_matrix(a), "output": net.pack_matrix(b.T)}
        report[name] = {"epochs": epochs, "parameters": a.size + b.size, "train_rows": len(train_rows),
                        "initial_test": measure(initial, test_set), "final_test": measure(result, test_set),
                        "final_train": measure(result, train_set)}
        if name == "patterns":
            for profile, mask in (("no_marks", [not any(c in net.MARKS for c in row[0]) for row in test_rows]),
                                  ("marked", [any(c in net.MARKS for c in row[0]) for row in test_rows])):
                report[name][profile] = measure(result, tuple(v[mask] for v in test_set))
    # Repository examples are a separate, finite transfer probe, never fitting inputs.
    probes = [p for p in net.inventory() if "example" in p]
    if {p["example"] for p in probes} & {r[0] for r in morphology_rows(train_roots, inv)}:
        raise ValueError("Source example leakage")
    head = net.unpack(model)["patterns"]
    report["nominal_examples"] = []
    for p in probes:
        scores = net.logits(head, net.features(p["example"]))
        predicted = labels[max(range(len(labels)), key=scores.__getitem__)]
        allowed = [o["pattern"] for _, o in net.alternatives(p["example"])]
        report["nominal_examples"].append({"word": p["example"], "target": p["id"], "first_raw": predicted,
                                          "target_recovered": p["id"] in allowed,
                                          "raw_top1_exact_id": p["id"] == predicted})
    return model, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--induce", type=Path, help="JSON list of aligned [root, stem] examples")
    args = parser.parse_args()
    if args.induce:
        print(json.dumps(net.induce(json.loads(args.induce.read_text())), ensure_ascii=False))
        return
    if not args.check and not args.output:
        parser.error("choose --output DIRECTORY or --check")
    model, report = train()
    raw = (json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    report["model_sha256"] = sha256(raw).hexdigest()
    result = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    if args.check:
        if (net.DIRECTORY / "model.json").read_bytes() != raw or (net.DIRECTORY / "training.json").read_bytes() != result:
            raise SystemExit("Refit differs from installed model or evaluation")
    else:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "model.json").write_bytes(raw)
        (args.output / "training.json").write_bytes(result)
    print(json.dumps({k: v for k, v in report.items() if k in ("patterns", "guard", "distinct_templates","model_sha256")}, indent=2))


if __name__ == "__main__":
    main()
