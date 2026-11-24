"""Sequential, source-held-out measurement for the historical NABT PR range."""

import argparse
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path

import numpy as np
from .cumulative_history import DATA, canonical, digest, snapshot
from . import cumulative_features as feat
from . import corpus_verbs


def metadata():
    protocol = json.loads((DATA / "protocol.json").read_bytes())
    pack = json.loads(gzip.decompress((DATA / "examples.json.gz").read_bytes()))
    return protocol, pack


def score(gold, pred):
    total, hits = Counter(gold), Counter(y for y, p in zip(gold, pred, strict=True) if y == p)
    return {
        "n": len(gold),
        "correct": sum(hits.values()),
        "classes": len(total),
        "balanced": (
            round(sum(hits[k] / n for k, n in total.items()) / len(total), 6) if total else None
        ),
    }


def projected(task, text, label):
    if task == "root_recipe":
        return (
            corpus_verbs.apply_script(json.loads(label), corpus_verbs.carriers(text))
            if label is not None
            else None
        )
    return label


def experiment(protocol, pack, dest, *, resume=None, save_stage=None, stage_dir=None):
    rows = pack["rows"]
    if {r["text"] for r in rows if r["split"] == "train"} & {
        r["text"] for r in rows if r["split"] == "test"
    }:
        raise ValueError("Held-out input leaked")
    groups = defaultdict(list)
    for r in rows:
        groups[r["task"]].append(r)
    # Tasks with little support remain in the denominator, never removed from the PR audit.
    tasks = sorted(
        t for t, g in groups.items() if len({r["gold"] for r in g if r["split"] == "train"}) >= 2
    )
    texts = sorted({r["text"] for t in tasks for r in groups[t]})
    ids = {s: i for i, s in enumerate(texts)}
    models = feat.parents()
    X = np.array([feat.features(x, models) for x in texts], dtype=np.float64)
    rng = np.random.default_rng(protocol["seed"])
    width = protocol["hidden"]
    W = rng.normal(0.0, 1 / feat.DIM**0.5, (feat.DIM, width))
    initial_W = W.copy()
    heads, initial_heads, indices, encoded, labelnames = {}, {}, {}, {}, {}
    for task in tasks:
        names = sorted({r["gold"] for r in groups[task] if r["split"] == "train"})
        labelnames[task] = names
        heads[task] = rng.normal(0.0, 0.04, (width + 1, len(names)))
        initial_heads[task] = heads[task].copy()
        indices[task] = np.array([ids[r["text"]] for r in groups[task]])
        encoded[task] = np.array(
            [names.index(r["gold"]) if r["gold"] in names else -1 for r in groups[task]]
        )
    labels_at = {}
    training = {}

    def predictions(task, features, head, active):
        logits = features @ head[:-1] + head[-1]
        logits[:, ~active] = -np.inf
        return [labelnames[task][k] for k in logits.argmax(1)]

    timeline, first, final_predictions = {}, {}, {}
    prediction_log = []
    start = 0
    signature = {
        k: digest((DATA / k).read_bytes())
        for k in ("pulls.json", "history.json.gz", "examples.json.gz", "protocol.json")
    }
    if resume:
        info = json.loads(gzip.decompress((resume / "state.json.gz").read_bytes()))
        raw = (resume / "weights.npz").read_bytes()
        if (
            info["inputs"] != signature
            or info["tasks"] != tasks
            or info["weights_sha256"] != digest(raw)
        ):
            raise ValueError("Incompatible stage checkpoint or changed inputs")
        start = info["stage"]
        if type(start) is not int or not 1 <= start < 143:
            raise ValueError("Continuation requires an intermediate PR stage")
        with np.load(resume / "weights.npz", allow_pickle=False) as saved:
            W = saved["shared"].copy()
            heads = {t: saved["h" + str(i)].copy() for i, t in enumerate(tasks)}
        first = {(t, j): v for t, j, v in info["first"]}
        timeline = info["timeline"]
        for t in tasks:
            training[t] = tuple(
                {r["text"] for r in groups[t] if r["split"] == "train" and r["pr"] <= start}
            )
    for pr in range(start + 1, 144):
        has_updates = False
        for task in tasks:
            # The same training input may be credited to two PRs but is fitted once.
            unique = {}
            for j, r in enumerate(groups[task]):
                if r["split"] == "train" and r["pr"] <= pr:
                    unique.setdefault(r["text"], j)
            idx = np.array(list(unique.values()), dtype=int)
            if len(idx) != len(training.get(task, ())):
                has_updates = True
            training[task] = idx
            active = np.zeros(len(labelnames[task]), dtype=bool)
            active[encoded[task][idx]] = True
            labels_at[task] = active
        if has_updates:
            active_tasks = [t for t in tasks if labels_at[t].sum() >= 2]
            for _ in range(protocol["updates_per_stage"]):
                H = np.tanh(X @ W)
                dh = np.zeros_like(H)
                for t in active_tasks:
                    idx = training[t]
                    xidx = indices[t][idx]
                    h = H[xidx]
                    head = heads[t]
                    z = h @ head[:-1] + head[-1]
                    z[:, ~labels_at[t]] = -np.inf
                    prob = np.exp(z - z.max(1, keepdims=True))
                    prob /= prob.sum(1, keepdims=True)
                    prob[np.arange(len(idx)), encoded[t][idx]] -= 1
                    delta = prob / len(idx)
                    np.add.at(dh, xidx, delta @ head[:-1].T)
                    head[:-1] -= protocol["learning_rate"] * (h.T @ delta)
                    head[-1] -= protocol["learning_rate"] * delta.sum(0)
                W -= (
                    protocol["learning_rate"]
                    * (X.T @ (dh * (1 - H * H)))
                    / max(1, len(active_tasks))
                )
        state = np.tanh(X @ W)
        stage = {}
        for t in tasks:
            if labels_at[t].sum() < 2:
                continue
            probe = [j for j, r in enumerate(groups[t]) if r["split"] == "test" and r["pr"] <= pr]
            if not probe:
                continue
            predictions_now = predictions(t, state[indices[t][probe]], heads[t], labels_at[t])
            # First and final scores below are compared on identical rows.
            for j, v in zip(probe, predictions_now, strict=True):
                first.setdefault((t, j), v)
            g = [groups[t][j]["gold"] for j in probe]
            stage[t] = score(g, predictions_now)
            if pr == 143:
                final_predictions[t] = dict(zip(probe, predictions_now, strict=True))
        timeline[str(pr)] = stage
        if pr == save_stage:
            stage_dir.mkdir(parents=True, exist_ok=False)
            np.savez_compressed(
                stage_dir / "weights.npz",
                shared=W,
                **{"h" + str(i): heads[t] for i, t in enumerate(tasks)},
            )
            (stage_dir / "state.json.gz").write_bytes(
                gzip.compress(
                    canonical(
                        {
                            "stage": pr,
                            "inputs": signature,
                            "tasks": tasks,
                            "weights_sha256": digest((stage_dir / "weights.npz").read_bytes()),
                            "timeline": timeline,
                            "first": [[t, j, v] for (t, j), v in first.items()],
                        }
                    ).encode(),
                    mtime=0,
                )
            )
    initstate = np.tanh(X @ initial_W)
    by_pr = defaultdict(lambda: defaultdict(list))
    results = {}
    for t in tasks:
        f = final_predictions.get(t, {})
        if not f:
            continue
        idx = list(f)
        init = predictions(t, initstate[indices[t][idx]], initial_heads[t], labels_at[t])
        majority = Counter(groups[t][j]["gold"] for j in training[t]).most_common(1)[0][0]
        samples = []
        for j, init_y in zip(idx, init, strict=True):
            r = groups[t][j]
            labels = [r["gold"], f[j], init_y, majority, first[t, j]]
            outcome = [projected(t, r["text"], y) for y in labels]
            samples.append((r["text"], *outcome))
            by_pr[r["pr"]][t].append(outcome)
            prediction_log.append(
                {
                    "pr": r["pr"],
                    "task": t,
                    "source": r["source"],
                    "lane": r["lane"],
                    "text_sha256": digest(r["text"].encode()),
                    "gold": outcome[0],
                    "prediction": outcome[1],
                    "initial": outcome[2],
                    "majority": outcome[3],
                    "first": outcome[4],
                }
            )
        unique = {p[0]: p[1:] for p in samples}
        results[t] = comparison(list(unique.values()), trained_classes=len(labelnames[t]))
    pr_rows = []
    hist = snapshot()
    for entry in hist["pull_requests"]:
        pr = entry["pr"]
        measures = {
            t: comparison(v, trained_classes=len(labelnames[t])) for t, v in by_pr[pr].items()
        }
        candidates = [r for r in rows if r["pr"] == pr]
        pr_rows.append(
            {
                "pr": pr,
                "files": entry["files"],
                "changed_tests": len(entry["touched_tests"]),
                "prepared_examples": len(candidates),
                "assessment_examples": sum(r["split"] == "test" for r in candidates),
                "measured": measures,
                "passed_task_slices": [t for t, v in measures.items() if v["passed"]],
                "changed_tests_without_passing_probe": len(
                    set(entry["touched_tests"])
                    - {
                        r["source"].split(":", 1)[1]
                        for r in candidates
                        if r["split"] == "test"
                        and r["task"] in measures
                        and measures[r["task"]]["passed"]
                        and "::" in r["source"]
                    }
                ),
                "scope": "BOUNDED_SLICES_ONLY" if measures else "NO_MEASURED_SLICE",
            }
        )
    # This is a necessary coverage condition. Even an exercised test method can
    # contain additional untouched assertions that the bounded probe never asked.
    for item in pr_rows:
        item["necessary_coverage_gate"] = bool(
            item["measured"]
            and item["assessment_examples"]
            and item["changed_tests"]
            and item["changed_tests_without_passing_probe"] == 0
            and all(
                v["passed"] and v["final"]["correct"] == v["final"]["n"]
                for v in item["measured"].values()
            )
        )
    dest.mkdir(parents=True, exist_ok=False)
    model = {"shared_columns": W.T.tolist(), "heads": {t: heads[t].T.tolist() for t in tasks}}
    (dest / "weights.json.gz").write_bytes(gzip.compress(canonical(model).encode(), mtime=0))
    manifest = {
        "schema": "nabt.cumulative-weights.v1",
        "tasks": tasks,
        "labels": labelnames,
        "v13_parent": feat.v13.PARENT_SHA,
        "v13_readout": feat.v13.MODEL_SHA,
        "ntp_parent": feat.recursive.MODEL_SHA256,
        "inputs": {
            p: digest((DATA / p).read_bytes())
            for p in ("pulls.json", "history.json.gz", "examples.json.gz", "protocol.json")
        },
        "weights_sha256": digest((dest / "weights.json.gz").read_bytes()),
        "final_stage": 143,
    }
    totals = {
        "range": len(pr_rows),
        "prs_with_examples": sum(bool(r["prepared_examples"]) for r in pr_rows),
        "prs_with_measurement": sum(bool(r["measured"]) for r in pr_rows),
        "prs_with_passing_slice": sum(bool(r["passed_task_slices"]) for r in pr_rows),
        "prs_meeting_necessary_coverage": sum(r["necessary_coverage_gate"] for r in pr_rows),
        "total_examples": len(rows),
        "measured_tasks": len(results),
        "passing_tasks": sum(v["passed"] for v in results.values()),
        "excluded": pack["excluded"],
    }
    (dest / "manifest.json").write_text(canonical(manifest) + "\n")
    (dest / "evaluation.json").write_text(
        json.dumps(
            {"summary": totals, "tasks": results, "pulls": pr_rows}, ensure_ascii=False, indent=1
        )
        + "\n"
    )
    (dest / "stages.json.gz").write_bytes(gzip.compress(canonical(timeline).encode(), mtime=0))
    (dest / "predictions.json.gz").write_bytes(
        gzip.compress(canonical(prediction_log).encode(), mtime=0)
    )
    print(canonical(totals))


def comparison(rows, trained_classes):
    gold, pred, init, majority, first = zip(*rows, strict=True)
    out = {
        key: score(gold, v)
        for key, v in (("final", pred), ("initial", init), ("majority", majority), ("first", first))
    }
    out["lost_after_learning"] = sum(
        a == y and b != y for y, a, b in zip(gold, first, pred, strict=True)
    )
    out["gained_after_learning"] = sum(
        a != y and b == y for y, a, b in zip(gold, first, pred, strict=True)
    )
    # For root recovery class diversity must refer to scripts for the task and to
    # dictionary radicals for the separately identified exact-root measure.
    out["passed"] = bool(
        trained_classes >= 2
        and out["final"]["classes"] >= 2
        and all(
            out["final"][k] > max(out[c][k] for c in ("initial", "majority"))
            for k in ("correct", "balanced")
        )
    )
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--save-stage", type=int, choices=range(1, 143), metavar="1..142")
    parser.add_argument("--stage-dir", type=Path)
    args = parser.parse_args()
    if (args.save_stage is None) != (args.stage_dir is None):
        parser.error("--save-stage and --stage-dir must be supplied together")
    experiment(
        *metadata(),
        args.output,
        resume=args.resume,
        save_stage=args.save_stage,
        stage_dir=args.stage_dir,
    )
