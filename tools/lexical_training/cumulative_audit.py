"""Replay all held-out predictions and keep the full PR acceptance denominator."""

import argparse
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path

from . import cumulative_features as feat, cumulative_lesson as owner
from .cumulative_history import canonical, digest


def replay(directory, *, ablate=False):
    def read(name):
        raw = (directory / name).read_bytes()
        return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)

    manifest = read("manifest.json")
    for name, sha in {**manifest["inputs"], "weights.json.gz": manifest["weights_sha256"]}.items():
        if digest((directory / name).read_bytes()) != sha:
            raise ValueError("Changed cumulative input: " + name)
    if (manifest["v13_parent"], manifest["v13_readout"], manifest["ntp_parent"]) != (
        feat.v13.PARENT_SHA,
        feat.v13.MODEL_SHA,
        feat.recursive.MODEL_SHA256,
    ):
        raise ValueError("Cumulative parent identities changed")
    pulls, history = read("pulls.json"), read("history.json.gz")
    reports = read("evaluation.json")["pulls"]
    if any(
        [p[k] for p in items] != list(range(1, 144))
        for items, k in ((pulls, "number"), (history["pull_requests"], "pr"), (reports, "pr"))
    ):
        raise ValueError("Missing or reordered PR outcomes")
    rows = read("examples.json.gz")["rows"]
    training = {r["text"] for r in rows if r["split"] == "train"}
    withheld = [r for r in rows if r["split"] == "test"]
    if any(r["text"] in training for r in withheld):
        raise ValueError("Assessment input present in training")
    labels = manifest["labels"]
    model = read("weights.json.gz")
    parents = feat.parents()
    predictions = read("predictions.json.gz")

    def key(pr, task, source, sha):
        return pr, task, source, sha

    recorded = {key(p["pr"], p["task"], p["source"], p["text_sha256"]): p for p in predictions}
    if len(recorded) != len(predictions):
        raise ValueError("Duplicate saved prediction")
    ablations = defaultdict(lambda: defaultdict(Counter))
    vectors = {}
    outcomes = defaultdict(list)
    for r in withheld:
        if r["task"] not in labels:
            continue
        text = r["text"]
        if text not in vectors:
            vectors[text] = feat.features(text, parents)
        t = r["task"]
        prediction = owner.observe(model, labels, t, vectors[text])
        answer = r["gold"]
        if t == "root_recipe":
            letters = owner.corpus_verbs.carriers(text)
            prediction = owner.corpus_verbs.apply_script(json.loads(prediction), letters)
            answer = owner.corpus_verbs.apply_script(json.loads(answer), letters)
        row = recorded.pop(key(r["pr"], t, r["source"], digest(text.encode())))
        if (prediction, answer) != (row["prediction"], row["gold"]):
            raise ValueError(f"Historical prediction or gold changed for {r['source']}")
        outcomes[r["pr"], t].append(row)
        if ablate:
            values = vectors[text]
            for channel, indices in (
                ("v13", [*range(feat.HASH_DIM, feat.HASH_DIM + 32), feat.DIM - 3, feat.DIM - 1]),
                ("ntp_recursive", [*range(feat.HASH_DIM + 32, feat.DIM - 3), feat.DIM - 2]),
                ("v13_change_readout_only", [feat.DIM - 1]),
            ):
                masked = values.copy()
                for i in indices:
                    masked[i] = 0.0
                new = owner.observe(model, labels, t, masked)
                if t == "root_recipe":
                    new = owner.corpus_verbs.apply_script(json.loads(new), letters)
                for name in ("all_rows", r["lane"]):
                    counts = ablations[channel][name]
                    counts["tested"] += 1
                    counts["nonzero_channel"] += any(values[i] != 0 for i in indices)
                    counts["prediction_changed"] += new != prediction
                    counts["correct_full"] += prediction == answer
                    counts["correct_masked"] += new == answer
                    counts["lost"] += prediction == answer and new != answer
                    counts["gained"] += prediction != answer and new == answer
    if recorded:
        raise ValueError("Unexpected extra predictions")

    def scores(items, field):
        counts, correct = Counter(), Counter()
        for r in items:
            counts[r["gold"]] += 1
            correct[r["gold"]] += r["gold"] == r[field]
        return (
            len(items),
            sum(correct.values()),
            round(sum(correct[k] / v for k, v in counts.items()) / len(counts), 6),
        )

    gaps = []
    for pull, entry in zip(pulls, reports, strict=True):
        pr = pull["number"]
        ts = {t for (n, t) in outcomes if n == pr}
        if ts != set(entry["measured"]):
            raise ValueError("Incomplete PR measurement table")
        for t in ts:
            items = outcomes[pr, t]
            m = entry["measured"][t]
            for field, ref in (
                ("prediction", "final"),
                ("initial", "initial"),
                ("majority", "majority"),
                ("first", "first"),
            ):
                summary = m[ref]
                if scores(items, field) != (summary["n"], summary["correct"], summary["balanced"]):
                    raise ValueError("Changed score " + t)
            passed = m["final"]["classes"] >= 2 and all(
                m["final"][k] > max(m[c][k] for c in ("majority", "initial"))
                for k in ("correct", "balanced")
            )
            if m["passed"] != passed:
                raise ValueError("Changed attainment flag")
        changed = history["pull_requests"][pr - 1]["touched_tests"]
        matched = {
            r["source"].split(":", 1)[1]
            for r in withheld
            if r["pr"] == pr
            and r["task"] in ts
            and entry["measured"][r["task"]]["passed"]
            and "::" in r["source"]
        }
        pending = len(set(changed) - matched)
        necessary = bool(
            ts
            and changed
            and not pending
            and all(
                m["passed"] and m["final"]["correct"] == m["final"]["n"]
                for m in entry["measured"].values()
            )
        )
        if (
            entry["necessary_coverage_gate"] != necessary
            or entry["changed_tests_without_passing_probe"] != pending
        ):
            raise ValueError("Changed PR coverage decision")
        if not necessary:
            gaps.append(pr)
    return {
        "replayed_heldout_predictions": sum(len(x) for x in outcomes.values()),
        "all_heldout": len(withheld),
        "no_trained_head": len(withheld) - len(predictions),
        "covered_pr_range": [1, 143],
        "unmet_necessary_coverage": gaps,
        "necessary_gate_passed": not gaps,
        **({"fixed_weight_inference_ablation": ablations} if ablate else {}),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-every-pr", action="store_true")
    parser.add_argument("--ablate-parents", action="store_true")
    args = parser.parse_args()
    report = replay(owner.DIRECTORY, ablate=args.ablate_parents)
    print(canonical(report))
    return 2 if args.require_every_pr and not report["necessary_gate_passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
