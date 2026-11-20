"""Consume the compiled local A116 exporter. Refit and measure pinned lesson heads."""
import argparse
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path

from . import pattern_learning as net, pattern_lesson as lesson


def encode(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


# Ordered, disjoint roots for each structural contrast. Licensing is conditional on
# the supplied radicals; these are not attestations that all generated words are used.
ROOT_PAIRS = {
    "sound": (("كتب", "حفظ"), ("جلس", "ضرب")),
    "hamza": (("بدء", "ءمر"), ("قرء", "سءل")),
    "hollow": (("قوم", "بيع"), ("زور", "سير")),
    "defective": (("دعو", "رمي"), ("غزو", "سقي")),
    "initial_weak": (("وعد", "يسر"), ("وزن", "يمن")),
    "doubled": (("مدد", "شدد"), ("ردد", "مسس")),
    "double_weak": (("وقي", "طوي"), ("وعي", "روي")),
    "quad": (("دحرج", "زلزل"), ("بعثر", "وسوس")),
}


def cell_heads(data, encoder):
    """Fit lesson readouts on filled, explicit A116 cells. Measure held roots by stratum."""
    recipes = {(domain, key):recipe for domain, key, recipe in data["paradigms"]}
    keys = list(dict.fromkeys(key for _, key in recipes))
    heads, results = {}, {name:Counter() for name in ROOT_PAIRS}
    for key in keys:
        train, test = [], []
        for name, (seen, held) in ROOT_PAIRS.items():
            for roots, samples in ((seen, train), (held, test)):
                for root in roots:
                    if len(root) == 4:
                        domain = "****" if ("****", key) in recipes else "ل***" if root[0] == "ل" else "!***"
                    else:
                        domain = "".join(c if c in "ويلء" else "*" for c in root)
                        domain += "=" if root[1] == root[2] else "!"
                    recipe = recipes.get((domain, key))
                    if recipe:
                        word = "".join(root[int(c)-1] if c in "1234" else c for c in recipe)
                        if not net.features(word):
                            raise ValueError("Cell rendering exceeds encoder contract")
                        samples.append((name, word))
        if not train or not test:
            raise ValueError(f"No disjoint examples for {key}")
        positives = sorted({w for _, w in train})
        fitted = lesson.fit_readout(encoder, positives, lesson.counterexamples(train), positives[0])
        head = {k:fitted[k] for k in ("weights", "bias")}
        heads[key] = head
        for name, word in test:
            for probe in [word, *lesson.counterexamples([(name, word)])]:
                v = net.hidden_state(encoder, net.features(probe))
                score = head["bias"] + sum(x*y for x,y in zip(head["weights"],v,strict=True))
                kind = "positive" if word == probe else "negative"
                results[name][kind] += 1
                results[name][kind+"_accepted"] += score > 0
    return {"heads":heads, "root_splits":ROOT_PAIRS, "evaluation_by_root_class":results}


def build(data):
    entries = [p for p in net.inventory() if p["source_contract"].startswith("Ishtiqaq.")]
    if len(entries) != len(data["sources"]):
        raise ValueError("Local A116 and NABT have different verb inventories")
    heads, measured = {}, Counter()
    held = ["جلس", "ضرب", "سمع", "دخل", "خرج", "رسم", "سجد", "طلب"]
    encoder = net.model()["patterns"]
    for spec, text in zip(entries, data["sources"], strict=True):
        tokens = [int(c)-1 if c in "123" else c for c in text]
        def fill(root):
            return "".join(root[t] if type(t) is int else t for t in tokens)
        pairs = [[r, fill(r)] for r in ("كتب", "حفظ")]
        if tokens != spec["tokens"] or net.induce(pairs) != [tokens]:
            raise ValueError(f"Root transport failed for {spec['id']}")
        negatives = lesson.counterexamples(pairs)
        fitted = lesson.fit_readout(encoder, [s for _, s in pairs], negatives, pairs[0][1])
        head = {k: fitted[k] for k in ("weights", "bias")}
        heads[spec["id"]] = head
        for root in held:
            correct = fill(root)
            for word in [correct, *lesson.counterexamples([(root, correct)])]:
                score = head["bias"] + sum(v*w for v, w in zip(
                    net.hidden_state(encoder, net.features(word)), head["weights"], strict=True))
                kind = "positive" if word == correct else "negative"
                measured[kind] += 1
                measured[kind + "_accepted"] += score > 0
                measured[kind + "_ties"] += score == 0
    return {"encoder":net.MODEL_SHA, "cell_readouts":cell_heads(data,encoder), "heads":heads, "training_roots":["كتب","حفظ"],
            "test_roots":held, "evaluation":measured}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lean_json", type=Path)
    parser.add_argument("--studies", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = json.loads(args.lean_json.read_bytes())
    artifacts = {"a116_verb_rules.json.gz":gzip.compress(encode(data), compresslevel=9, mtime=0),
                 "verb_contrast_heads.json":encode(build(data))}
    # Fix the OS header byte across Python/zlib versions.
    raw = artifacts["a116_verb_rules.json.gz"]
    artifacts["a116_verb_rules.json.gz"] = raw[:9] + b"\xff" + raw[10:]
    studies = gzip.compress(encode(json.loads(args.studies.read_bytes())), compresslevel=9, mtime=0)
    artifacts["masdar_studies.json.gz"] = studies[:9] + b"\xff" + studies[10:]
    for name, raw in artifacts.items():
        path = net.DIRECTORY / name
        if args.check:
            if path.read_bytes() != raw:
                raise ValueError(f"Regeneration differed for {name}")
        else:
            path.write_bytes(raw)
        print(name, sha256(raw).hexdigest())


if __name__ == "__main__":
    main()
