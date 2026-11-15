"""Rebuild a finite grammar-to-concept proposal model and its out-of-sura evaluation."""
import argparse
from collections import Counter, defaultdict
import csv
from dataclasses import dataclass, replace
import gzip
import json
import math
from pathlib import Path

from nabt.corpus_evidence import buckwalter_to_arabic
from nabt.corpus_sources import read_corpus
from tools.arabic_training.data import DATA_SHA256, read_source, sha
from tools.fetch_qac_source import checked, DECODED_SHA256
from . import corpus_concepts as cc

ATLAS_SHA = "ebb765fad5866af3196ad5fcda614c1c3792fc9edd1e88e15febf995ac25cb3d"
ROLE = {
    "فاعل": "subject", "مفعول به": "object", "نائب فاعل": "deputy",
    "اسم مجرور": "prep", "مضاف إليه": "idafa", "نعت": "attribute",
    "مبتدأ": "topic", "مبتدأ مؤخر": "topic", "خبر": "predicate", "خبر مقدم": "predicate",
    "ظرف زمان": "time", "ظرف مكان": "place", "فعل أمر": "imperative",
    "فعل مضارع": "active", "فعل ماضٍ": "active",
    "فعل ماضٍ مبني للمجهول": "passive", "فعل مضارع مبني للمجهول": "passive",
}
MIN_TRAIN, MIN_DEV, PURITY, MAX_DEPTH = 20, 5, 85, 5


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def atlas_index(path):
    raw = path.read_bytes()
    if sha(raw) != ATLAS_SHA:
        raise ValueError("Atlas byte identity mismatch")
    required = {frame[2] for frame in cc.FRAMES.values()}
    rows = list(csv.DictReader(raw.decode().splitlines(), delimiter="\t"))
    index = {r["wahda"]: {"unit": r["wahda"], "layer": r["tabaqa"],
                          "in_mashru_engine": r["fi_muharrik"] == "نعم", "line": i}
             for i, r in enumerate(rows, 2) if r["wahda"] in required}
    if index.keys() != required:
        raise ValueError("Missing conceptual frame anchor in atlas")
    return index


def qac_words(path):
    compressed = path.read_bytes()
    checked(compressed)
    report = read_corpus(gzip.decompress(compressed), format="qac", source_id="qac_v04")
    if report["status"] != "READ" or report["summary"]["duplicate_locator_groups"]:
        raise ValueError("QAC coordinate integrity")
    groups = defaultdict(list)
    for row in report["records"]:
        groups[tuple(row["locator"][:3])].append((row["locator"][3], row["fields"], row["feature_tokens"]))
    words = {}
    for address, group in groups.items():
        group.sort(key=lambda r: r[0])
        stems = [r for r in group if "STEM" in r[2]]
        if len(stems) != 1:
            continue
        segment, fields, tokens = stems[0]
        pos = fields["TAG"]
        case = next((t for t in tokens if t in ("NOM", "ACC", "GEN")), "NA")
        aspect = next((t for t in tokens if t in ("PERF", "IMPF", "IMPV")), "NA")
        voice = ("PASS" if "PASS" in tokens else "ACT") if pos == "V" else "NA"
        prefixes = {f["TAG"] for _, f, ts in group if "PREFIX" in ts}
        suffix = any("SUFFIX" in ts for _, _, ts in group)
        shape = (pos, case, voice, aspect, str(int("P" in prefixes)),
                 str(int("DET" in prefixes)), str(int(suffix)))
        text = buckwalter_to_arabic("".join(f["FORM"] for _, f, _ in group))
        root = next((t[5:] for t in tokens if t.startswith("ROOT:")), None)
        words[address] = (cc.spelling(text), shape, root, segment)
    return words, len(groups)


@dataclass
class Sample:
    x: dict
    gold: str
    loc: tuple
    segment: int
    csv_line: int
    text: str
    prev: str
    root: str

    def witness(self):
        return {"qac": [*self.loc, self.segment], "masaq_csv_line": self.csv_line, "projected": self.gold}


def learn_patterns(type_sets, lex):
    # One vote per marked spelling and distinct analysis, across different
    # spellings in train and validation. Labels are QAC morphology only.
    groups = defaultdict(lambda: defaultdict(Counter))
    for fold in ("train", "dev"):
        for word, readings in type_sets[fold].items():
            if fold == "dev" and word in type_sets["train"]:
                continue
            template = cc.pattern(word)
            if template is not None:
                groups[template][fold].update(readings)
    rules = {}
    for template, sides in groups.items():
        training, dev = sides["train"], sides["dev"]
        if not training:
            continue
        choice, good = training.most_common(1)[0]
        if (good >= 6 and dev[choice] >= 3 and good * 100 >= 90 * training.total()
                and dev[choice] * 100 >= 90 * dev.total()):
            rules[template] = (choice, {"train_agree": good, "train_votes": training.total(),
                                       "dev_agree": dev[choice], "dev_votes": dev.total()})
    blocks = set()
    for word in type_sets["train"]:
        word_key = cc.key(word)
        rule = rules.get(cc.pattern(word))
        if rule and set(lex[word_key]) != {rule[0]}:
            blocks.add(word_key)
    return rules, sorted(blocks)


def prepare(qac, masaq):
    words, word_count = qac_words(qac)
    verses, manifest, _ = read_source(masaq)
    # The existing intake owns exact CSV-row provenance, conflict/duplicate
    # quarantine and the frozen sura split. Read the role by that admitted row.
    with masaq.open(encoding="utf-8-sig", newline="") as stream:
        roles = {n: r["Syntactic_Role"].strip() for n, r in enumerate(csv.DictReader(stream), 2)
                 if r["Morph_type"] == "Stem"}
    splits = defaultdict(list)
    off_target = defaultdict(list)
    lex = defaultdict(Counter)
    roots = set()
    type_sets = {"train": defaultdict(set), "dev": defaultdict(set)}
    audit = Counter()
    for verse in verses:
        split = verse["split"]
        last_shape, last_address, last_text = None, None, None
        for w in verse["words"]:
            address = tuple(w["address"])
            contiguous = last_address == address[2] - 1
            previous = last_shape if contiguous else None
            prev_text = last_text if contiguous else None
            last_shape, last_address, last_text = None, address[2], w["text"]
            record = words.get(address)
            audit["unquarantined_words"] += 1
            if record is None:
                audit["missing_qac_stem"] += 1
                continue
            form, shape, root, segment = record
            # QAC alone supplies morphology in the allowed training suras.
            # A divergent MASAQ spelling never receives that QAC analysis.
            if split in type_sets and cc.VOWELS.search(form):
                type_sets[split][form].add(shape)
            if split == "train":
                if root:
                    roots.add(root)
                if cc.VOWELS.search(form):
                    lex[cc.key(form)][shape] += 1
            if form != cc.spelling(w["text"]):
                audit["marked_spelling_disagrees"] += 1
                continue
            audit["matched_address_and_spelling"] += 1
            last_shape = shape
            target_pos = shape[0] in cc.NOMINAL | {"V"}
            if not target_pos:
                audit["outside_target_pos"] += 1
            if w["excluded_reasons"]:
                audit["masaq_intake_excluded"] += 1
                continue
            (line,) = [n for n in w["csv_rows"] if n in roles]
            if not roles[line]:
                audit["unlabelled"] += 1
                continue
            x = cc.features(shape, previous, initial=address[2] == 1)
            gold = ROLE.get(roles[line], cc.OTHER)
            if target_pos:
                splits[split].append(Sample(x, gold, address, segment, line, w["text"], prev_text, root))
            else:
                off_target[split].append(Sample(x, cc.OTHER, address, segment, line, w["text"], prev_text, root))
    unambiguous = {k: next(iter(v)) for k, v in lex.items() if len(v) == 1 and v.total() >= 2}
    rules, blocks = learn_patterns(type_sets, lex)
    analyses = sorted(set(unambiguous.values()) | {shape for shape, _ in rules.values()})
    indices = {v: i for i, v in enumerate(analyses)}
    info = {"qac_words": word_count, **audit, "cross_sura_duplicate_verses_excluded":
            len(manifest["duplicate_verses_quarantined"]),
            "ambiguous_training_spellings": sum(len(v) > 1 for v in lex.values()),
            "unique_singletons_omitted": sum(v.total() == 1 for v in lex.values()),
            "splits": {k: {"rows": len(splits[k]), "suras": v["suras"]}
                       for k, v in manifest["splits"].items()}}
    morphology = {"analyses": analyses, "lexicon": {k: indices[v] for k, v in unambiguous.items()},
                  "patterns": {k: {"analysis": indices[v], **stats} for k, (v, stats) in rules.items()},
                  "shape_blocks": blocks}
    return splits, off_target, morphology, roots, info


def entropy(rows):
    counts = Counter(r.gold for r in rows)
    return -sum(n / len(rows) * math.log2(n / len(rows)) for n in counts.values())


def fit(rows, dev, names, depth=0):
    counts = Counter(r.gold for r in rows)
    label = counts.most_common(1)[0][0]
    if (depth < MAX_DEPTH and len(rows) >= 2 * MIN_TRAIN and len(counts) > 1
            and counts[label] < 0.99 * len(rows)):
        best_gain, best_name, best_groups = 0.001, None, None
        base = entropy(rows)
        for name in names:
            groups = defaultdict(list)
            for row in rows:
                groups[row.x.get(name)].append(row)
            if sum(len(g) >= MIN_TRAIN for g in groups.values()) < 2:
                continue
            gain = base - sum(len(g) * entropy(g) for g in groups.values()) / len(rows)
            if gain > best_gain:
                best_gain, best_name, best_groups = gain, name, groups
        if best_name is not None:
            remaining = [n for n in names if n != best_name]
            children = {value: fit(g, [r for r in dev if r.x.get(best_name) == value],
                                   remaining, depth + 1)
                        for value, g in best_groups.items() if value is not None and len(g) >= MIN_TRAIN}
            return {"feature": best_name, "children": children}
    dev_good = sum(r.gold == label for r in dev)
    admitted = (label != cc.OTHER and len(dev) >= MIN_DEV and counts[label] * 100 >= PURITY * len(rows)
                and dev_good * 100 >= PURITY * len(dev))
    return {"candidate": label, "admitted": admitted, "train_counts": dict(counts),
            "dev_correct": dev_good, "dev_total": len(dev),
            "witness": next(r.witness() for r in rows if r.gold == label),
            "counterexample": next((r.witness() for r in rows if r.gold != label), None)}


def prediction(tree, features):
    if features is not None:
        node, _ = cc.leaf(tree, features)
        if node and node["admitted"]:
            return node["candidate"]


def score(rows, predict):
    counts = defaultdict(Counter)
    for row in rows:
        result = predict(row)
        counts[row.gold]["support"] += 1
        if result is not None:
            counts[result]["proposed"] += 1
            if result == row.gold:
                counts[result]["correct"] += 1
    roles = {k: {s: v[s] for s in ("support", "proposed", "correct")}
             for k, v in sorted(counts.items())}
    totals = {k: sum(v[k] for v in roles.values()) for k in ("support", "proposed", "correct")}
    return {**totals, "roles": roles}


def train(qac, masaq, atlas):
    anchors = atlas_index(atlas)
    splits, off_target, morphology_reader, roots, intake = prepare(qac, masaq)
    training, dev, test = (splits[k] for k in ("train", "dev", "test"))
    tree = fit(training, dev, cc.FEATURES)
    model = {"schema": "ntl.corpus-concepts.model.v1", "tree": tree, **morphology_reader,
              "atlas": anchors, "pins": {"atlas": ATLAS_SHA, "qac": DECODED_SHA256,
                                                              "masaq": DATA_SHA256}}
    def via_morphology(row, use_patterns=True):
        observed = cc.surface_observation(model, row.text, row.prev, row.loc[2] == 1, use_patterns=use_patterns)
        return prediction(tree, observed)

    def written_rows(rows, residual_only=False):
        converted = []
        for row in rows:
            if residual_only and via_morphology(row) is not None:
                continue
            observed = cc.written_features(row.text, row.prev, row.loc[2] == 1)
            if observed is not None:
                converted.append(replace(row, x=observed))
        return converted

    # Fit on all eligible POS, including negative examples. Validate each leaf
    # on exactly the dev population routed to this fallback at deployment.
    model["written_tree"] = fit(written_rows(training + off_target["train"]),
                                written_rows(dev + off_target["dev"], residual_only=True),
                                cc.SURFACE_FEATURES)
    model["model_id"] = sha(wire(model))
    morphology = fit(training, dev, cc.TOKEN_FEATURES)
    frequent = Counter(r.gold for r in training if r.gold != cc.OTHER).most_common(1)[0][0]
    contexts = {(cc.spelling(r.text), cc.spelling(r.prev or "")) for r in training}
    unseen = [r for r in test if (cc.spelling(r.text), cc.spelling(r.prev or "")) not in contexts]
    new_roots = [r for r in test if r.root and r.root not in roots]

    def structured(r):
        return prediction(tree, r.x)

    def surface(r):
        node, _, _ = cc.select(model, r.text, r.prev, r.loc[2] == 1)
        return node["candidate"] if node and node["admitted"] else None

    def exact(r):
        return via_morphology(r, False)

    metrics = {"surface_off_target_pos": score(off_target["test"], surface),
               "surface_morphology_channel": score(test, via_morphology),
               "surface_without_patterns": score(test, exact),
               "surface_without_patterns_unseen_root": score(new_roots, exact),
               "always_most_frequent_frame": score(test, lambda r: frequent),
               "annotated_no_previous_word": score(test, lambda r: prediction(morphology, r.x)),
               "annotated": score(test, structured), "surface": score(test, surface),
               "annotated_unseen_word_pair": score(unseen, structured),
               "surface_unseen_word_pair": score(unseen, surface),
               "annotated_unseen_root": score(new_roots, structured),
               "surface_unseen_root": score(new_roots, surface)}
    return model, {"schema": "ntl.corpus-concepts.evaluation.v1", "model_id": model["model_id"],
                   "minimum_train": MIN_TRAIN, "minimum_dev": MIN_DEV, "purity_pct": PURITY,
                   "max_depth": MAX_DEPTH, "intake": intake, "metrics": metrics,
                   "eligible_test_by_sura": dict(Counter(r.loc[0] for r in test))}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("qac", "masaq", "atlas", "model", "evaluation"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    model, evaluation = train(args.qac, args.masaq, args.atlas)
    args.model.write_bytes(wire(model) + b"\n")
    args.evaluation.write_text(json.dumps(evaluation, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: [v["correct"], v["proposed"], v["support"]]
                      for k, v in evaluation["metrics"].items()}, indent=2))


if __name__ == "__main__":
    main()
