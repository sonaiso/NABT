"""Fit on pinned QAC word/stem records; hold roots and all evaluation spellings out."""
import argparse
from collections import Counter, defaultdict
import gzip
from hashlib import sha256
from itertools import groupby, product
import json
from pathlib import Path
import re

from nabt.corpus_evidence import buckwalter_to_arabic
from nabt.errors import NabtError
from tools.fetch_qac_source import checked
from . import corpus_verbs as cv, pattern_learning as net
from .train_pattern_learning import arrays, fit, quantized


def root_script(letters, root):
    choices = []
    for ch in root:
        places = [i for i, c in enumerate(letters) if c == ch]
        if not places and ch not in "ويء":
            return None
        choices.append(places or [ch])
    def preference(ops):
        positions = [i for i in ops if type(i) is int]
        return (sum(i > j for i, j in zip(positions, positions[1:])),
                len(positions) - len(set(positions)), positions)
    return min(product(*choices), key=preference)


def split(key):
    return "test" if int.from_bytes(sha256(key.encode()).digest()[:4], "big") % 5 == 0 else "train"


def raw_records(path):
    raw = path.read_bytes()
    checked(raw)
    lines = (s.split("\t") for s in gzip.decompress(raw).decode("utf-8-sig").splitlines() if s.startswith("("))
    for address, segments in groupby(lines, lambda r: r[0].rsplit(":", 1)[0]):
        segments = list(segments)
        stems = [r for r in segments if r[3].startswith("STEM|")]
        if len(stems) != 1:
            continue
        _, segment, tag, fields = stems[0]
        f = fields.split("|")
        root = next((v[5:] for v in f if v.startswith("ROOT:")), None)
        if root is None:
            continue
        # Keep all verbs and a fixed address-based background sample of rooted nonverbs.
        if tag != "V" and int.from_bytes(sha256(address.encode()).digest()[:2], "big") % 3:
            continue
        try:
            root = buckwalter_to_arabic(root).translate(cv.ROOT_GRAPH)
            stem, word = (buckwalter_to_arabic(w) for w in (segment, "".join(r[1] for r in segments)))
        except NabtError:
            raise ValueError("Unmapped symbol in pinned QAC source")
        if tag == "V":
            aspect, = [x for x in f if x in ("PERF","IMPF","IMPV")]
            family = next((x[1:-1] for x in f if re.fullmatch(r"\([IVX]+\)", x)), "I")
            label = "/".join((aspect, "PASS" if "PASS" in f else "ACT", family))
        else:
            label = "OTHER"
        for unit, form in (("stem",stem), ("word",word)):
            yield split(root), unit, form, root, label


def encode(rows, label_ids):
    return sorted((w, {label_ids[k] for k in targets}) for w, targets in rows.items())


def train(path):
    records = list(raw_records(path))
    # Exclude collisions from fitting; the testing denominator stays untouched.
    held = {cv.project(form) for s, _, form, _, _ in records if s == "test"}
    analysis, scripts = defaultdict(set), defaultdict(set)
    fit_roots, held_roots = set(), {r for s, _, _, r, _ in records if s == "test"}
    excluded = Counter()
    for s, _, form, root, tag in records:
        if s != "train":
            continue
        projected = cv.project(form)
        if not projected or projected in held:
            excluded["unavailable_or_held_surface"] += 1
            continue
        fit_roots.add(root)
        analysis[projected].add(tag)
        if tag != "OTHER":
            script = root_script(cv.carriers(projected), root)
            if script is None:
                excluded["unexpressible_root"] += 1
            else:
                scripts[projected].add(json.dumps(script, ensure_ascii=False))
    if fit_roots & held_roots or (set(analysis) | set(scripts)) & held:
        raise ValueError("Partition leakage")
    model = {"schema": "ntl.qac-verb-observer.v1", "source": cv.QAC}
    report = {"source_sha256": cv.QAC, "fit_roots": len(fit_roots), "test_roots": len(held_roots),
              "excluded_training_occurrences": dict(excluded), "selection":"FIXED_FINAL_EPOCH"}
    for name, table in (("analysis",analysis), ("root",scripts)):
        labels = sorted(set().union(*table.values()))
        rows = encode(table, {v:i for i,v in enumerate(labels)})
        xy = arrays(rows, net.features, net.SHAPE_INPUTS, len(labels))
        _, params = fit(xy, 48, 24)
        a, b = quantized(params)
        model[name] = {"hidden":48, "labels":labels if name == "analysis" else [json.loads(v) for v in labels],
                       "input":net.pack_matrix(a), "output":net.pack_matrix(b.T)}
        report[name] = {"training_surfaces": len(rows), "classes": len(labels), "parameters": a.size + b.size}
    raw = (json.dumps(model, sort_keys=True, ensure_ascii=False, separators=(",",":"))+"\n").encode()
    heads = cv.unpack(raw)
    cache, shape_baseline = {}, {}
    pattern_params = net.model()["patterns"]
    pattern_inventory = net.inventory()
    counts = defaultdict(Counter)
    for s, unit, form, root, tag in records:
        if s != "test":
            continue
        if form not in cache:
            cache[form] = cv.analyze(heads, form)
            offered = net.alternatives(form)
            baseline = None
            if offered:
                values = net.logits(pattern_params, net.features(form))
                i, first = max(offered, key=lambda row: values[row[0]])
                p = pattern_inventory[i]
                aspect = {"past":"PERF", "imperfect":"IMPF", "imperative":"IMPV"}.get(p.get("form"))
                if aspect:
                    baseline = (first["root"], "/".join((aspect, "PASS" if p["voice"] == "passive" else "ACT", p["family"])))
            shape_baseline[form] = baseline
        obs = cache[form]
        group = counts[unit]
        group["occurrences"] += 1
        if tag == "OTHER":
            group["nonverbs"] += 1
            group["correct_nonverb_abstention"] += obs is None
            continue
        group["verbs"] += 1
        group["fixed_template_ranker_joint_correct"] += shape_baseline[form] == (root, tag)
        match = bool(obs and "/".join((obs["aspect"],obs["voice"],obs["family"])) == tag)
        recovered = bool(obs and obs["root"] == root)
        group["aspect_voice_family_correct"] += match
        group["root_correct"] += recovered
        group["joint_correct"] += match and recovered
    report["test"] = {k: dict(v) for k, v in counts.items()}
    report["model_sha256"] = sha256(raw).hexdigest()
    return raw, (json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2)+"\n").encode()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--check", action="store_true")
    a = p.parse_args()
    if not a.check and not a.output:
        p.error("Use --check or --output DIRECTORY")
    raw, report = train(a.source)
    for name, data in (("corpus_verbs.json",raw), ("corpus_training.json", report)):
        if a.check:
            if (net.DIRECTORY/name).read_bytes() != data:
                raise SystemExit("Refit differs: "+name)
        else:
            a.output.mkdir(parents=True, exist_ok=True)
            (a.output/name).write_bytes(data)
    print(report.decode())


if __name__ == "__main__":
    main()
