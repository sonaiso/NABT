"""Replay V14 against its retained PR 1..143 parent without dropping gaps.

The historical holdout is a retrospective comparison, not a new blind exam.
Scoring never selects weights. A proposal is not an owner's accepted result.
This module and its deployed learner need only the Python standard library.
"""

import argparse
from collections import Counter, defaultdict
import csv
import gzip
from hashlib import sha256
import io
import json
from pathlib import Path

from . import cumulative_lesson as parent_owner, corpus_verbs

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "evidence/cumulative_outcomes_v1"
DIRECTORY = ROOT / "evidence/cumulative_v14"
PARENT_PREDICTIONS_SHA256 = "7977efd12902580247a513f2e3abe636107fd92a166d782ae68272b0f9b8b1f1"
ABLATIONS = (
    "v13", "ntp_recursive", "v13_change_readout_only", "task_memory", "parent_heads_only"
)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return sha256(value).hexdigest()


def _read(directory, name):
    raw = (Path(directory) / name).read_bytes()
    if name.endswith(".gz"):
        raw = gzip.decompress(raw)
    return json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))


def _learner():
    from . import cumulative_v14_model
    return cumulative_v14_model


def _source_snapshot():
    # The four original artifacts remain pinned by their original owner.
    manifest = parent_owner.artifact("manifest.json")
    evaluation = parent_owner.artifact("evaluation.json")
    pulls = parent_owner.artifact("pulls.json")
    parent_owner.artifact("weights.json.gz")
    for name, expected in manifest["inputs"].items():
        if digest((SOURCE / name).read_bytes()) != expected:
            raise ValueError("Changed inherited input: " + name)
    if digest((SOURCE / "predictions.json.gz").read_bytes()) != PARENT_PREDICTIONS_SHA256:
        raise ValueError("Changed inherited prediction baselines")
    return {
        "manifest": manifest,
        "evaluation": evaluation,
        "pulls": pulls,
        "history": _read(SOURCE, "history.json.gz"),
        "pack": _read(SOURCE, "examples.json.gz"),
        "predictions": _read(SOURCE, "predictions.json.gz"),
    }


def _equal(a, b):
    return canonical(a) == canonical(b)


def score(gold, predictions):
    if len(gold) != len(predictions):
        raise ValueError("Misaligned scoring rows")
    counts, hits = Counter(map(canonical, gold)), Counter()
    for answer, prediction in zip(gold, predictions, strict=True):
        if _equal(answer, prediction):
            hits[canonical(answer)] += 1
    return {
        "n": len(gold), "correct": sum(hits.values()), "classes": len(counts),
        "balanced": round(sum(hits[k] / n for k, n in counts.items()) / len(counts), 6) if counts else None,
    }


def projected(task, text, label):
    if task == "root_recipe" and label is not None:
        return corpus_verbs.apply_script(json.loads(label), corpus_verbs.carriers(text))
    return label


def _key(row):
    return row["pr"], row["task"], row["source"], row["text_sha256"]


def _unique(rows):
    unique = {}
    for row in rows:
        key = row["task"], row["text_sha256"]
        if key in unique:
            old = unique[key]
            for field in ("gold", "prediction", "parent", "initial", "majority"):
                if not _equal(old[field], row[field]):
                    raise ValueError("Inconsistent repeated task/input outcome: " + field)
        # A repeated public input can have different first-measured stages in
        # different PRs. Keep the original audit's last attribution for that
        # historical field; parent-to-V14 retention is independent of it.
        unique[key] = row
    return list(unique.values())


def comparison(rows, trained_classes):
    gold = [r["gold"] for r in rows]
    out = {
        name: score(gold, [r[field] for r in rows])
        for name, field in (
            ("final", "prediction"), ("parent", "parent"), ("initial", "initial"),
            ("majority", "majority"), ("first", "first")
        )
    }
    out.update(
        lost_from_parent=sum(_equal(r["parent"], r["gold"]) and not _equal(r["prediction"], r["gold"]) for r in rows),
        gained_from_parent=sum(not _equal(r["parent"], r["gold"]) and _equal(r["prediction"], r["gold"]) for r in rows),
        retained_parent_correct=sum(_equal(r["parent"], r["gold"]) and _equal(r["prediction"], r["gold"]) for r in rows),
        prediction_changes=sum(not _equal(r["prediction"], r["parent"]) for r in rows),
        lost_after_learning=sum(_equal(r["first"], r["gold"]) and not _equal(r["prediction"], r["gold"]) for r in rows),
        gained_after_learning=sum(not _equal(r["first"], r["gold"]) and _equal(r["prediction"], r["gold"]) for r in rows),
    )
    out["passed"] = bool(
        trained_classes >= 2 and out["final"]["classes"] >= 2
        and all(out["final"][k] > max(out[b][k] for b in ("initial", "majority")) for k in ("correct", "balanced"))
    )
    out["improved_over_parent"] = bool(rows and all(out["final"][k] > out["parent"][k] for k in ("correct", "balanced")))
    out["regressed_from_parent"] = bool(rows and any(out["final"][k] < out["parent"][k] for k in ("correct", "balanced")))
    out["no_parent_correct_lost"] = out["lost_from_parent"] == 0
    return out


def build_report(directory=None, *, ablate=False):
    learner = _learner()
    bundle = learner.load(Path(directory) if directory is not None else DIRECTORY)
    source = _source_snapshot()
    parent_manifest = source["manifest"]
    if bundle["parent_manifest"] != parent_manifest:
        raise ValueError("V14 is not bound to the retained cumulative parent")
    pulls, history, pack = source["pulls"], source["history"], source["pack"]
    wanted = list(range(1, 144))
    if (
        [r["number"] for r in pulls] != wanted
        or [r["pr"] for r in history["pull_requests"]] != wanted
        or [r["pr"] for r in source["evaluation"]["pulls"]] != wanted
    ):
        raise ValueError("Missing or reordered inherited PR")
    rows = pack["rows"]
    train_texts = {r["text"] for r in rows if r["split"] == "train"}
    withheld = [r for r in rows if r["split"] == "test"]
    if train_texts & {r["text"] for r in withheld}:
        raise ValueError("Inherited holdout input occurs in training")
    labels = parent_manifest["labels"]
    old = {_key(r): r for r in source["predictions"]}
    if len(old) != len(source["predictions"]):
        raise ValueError("Duplicate inherited prediction")
    proposals, predictions = {}, []
    ablations = defaultdict(lambda: defaultdict(Counter))
    for row in withheld:
        t, text = row["task"], row["text"]
        record = {k: row[k] for k in ("pr", "task", "source", "lane")}
        record["text_sha256"] = digest(text.encode())
        record["gold"] = projected(t, text, row["gold"])
        record.update(authority="NONE", review_only=True)
        if t not in labels:
            record.update(status="DEFER_NO_TRAINED_HEAD", prediction=None, parent=None,
                          initial=None, majority=None, first=None, label=None, parent_label=None)
            predictions.append(record)
            continue
        legacy = old.pop(_key(record), None)
        if legacy is None:
            raise ValueError("Missing inherited row prediction")
        if not _equal(legacy["gold"], record["gold"]):
            raise ValueError("Inherited source answer changed")
        cache_key = t, text
        if cache_key not in proposals:
            proposals[cache_key] = learner.propose(bundle, t, text)
        p = proposals[cache_key]
        if p.get("authority") != "NONE" or p.get("review_only") is not True:
            raise ValueError("Learned proposal acquired acceptance authority")
        if p.get("label") not in labels[t] or p.get("parent_label") not in labels[t]:
            raise ValueError("Prediction outside inherited output alphabet")
        if not _equal(p["value"], projected(t, text, p["label"])):
            raise ValueError("Proposal label and projected value disagree")
        if not _equal(p["parent_value"], projected(t, text, p["parent_label"])):
            raise ValueError("Parent label and projected value disagree")
        if not _equal(p["parent_value"], legacy["prediction"]):
            raise ValueError("Retained parent prediction changed")
        record.update(
            status="PROPOSED", prediction=p["value"], parent=p["parent_value"],
            label=p["label"], parent_label=p["parent_label"],
            initial=legacy["initial"], majority=legacy["majority"], first=legacy["first"],
            changed=not _equal(p["value"], p["parent_value"]),
        )
        predictions.append(record)
        if ablate:
            for channel in ABLATIONS:
                q = learner.propose(bundle, t, text, ablate=channel)
                if q.get("authority") != "NONE" or q.get("review_only") is not True:
                    raise ValueError("Ablation proposal acquired acceptance authority")
                if q.get("label") not in labels[t] or q.get("parent_label") not in labels[t]:
                    raise ValueError("Ablation prediction outside inherited output alphabet")
                if not _equal(q["value"], projected(t, text, q["label"])):
                    raise ValueError("Ablation label and projected value disagree")
                if not _equal(q["parent_value"], projected(t, text, q["parent_label"])):
                    raise ValueError("Ablation parent label and projected value disagree")
                if not _equal(q["parent_value"], legacy["prediction"]):
                    raise ValueError("Ablation changed the tracking identity of the original parent")
                for lane in ("all_rows", row["lane"]):
                    counts = ablations[channel][lane]
                    counts["tested"] += 1
                    counts["prediction_changed"] += not _equal(q["value"], p["value"])
                    counts["correct_full"] += _equal(p["value"], record["gold"])
                    counts["correct_masked"] += _equal(q["value"], record["gold"])
                    counts["lost"] += _equal(p["value"], record["gold"]) and not _equal(q["value"], record["gold"])
                    counts["gained"] += not _equal(p["value"], record["gold"]) and _equal(q["value"], record["gold"])
    if old:
        raise ValueError("Unexpected inherited predictions")
    measured = [r for r in predictions if r["status"] == "PROPOSED"]
    unique = _unique(measured)
    grouped, by_pr, by_lane = defaultdict(list), defaultdict(lambda: defaultdict(list)), defaultdict(list)
    for r in unique:
        grouped[r["task"]].append(r)
    for r in measured:
        by_pr[r["pr"]][r["task"]].append(r)
        by_lane[r["lane"]].append(r)
    tasks = {t: comparison(g, len(labels[t])) for t, g in sorted(grouped.items())}
    pull_reports = []
    for pull, entry in zip(pulls, history["pull_requests"], strict=True):
        n = pull["number"]
        candidates = [r for r in rows if r["pr"] == n]
        tests = [r for r in candidates if r["split"] == "test"]
        measures = {t: comparison(g, len(labels[t])) for t, g in sorted(by_pr[n].items())}
        passing = [t for t, m in measures.items() if m["passed"]]
        matched = {
            r["source"].split(":", 1)[1] for r in tests
            if r["task"] in passing and "::" in r["source"]
        }
        changed = entry["touched_tests"]
        pending = len(set(changed) - matched)
        necessary = bool(measures and tests and changed and pending == 0 and all(
            m["passed"] and m["final"]["correct"] == m["final"]["n"] for m in measures.values()
        ))
        all_measured = bool(tests) and all(r["task"] in labels for r in tests)
        strict = necessary and all_measured
        outcome = ("EMPTY_HISTORICAL_DIFF" if not entry["files"] else
                   "NO_VALID_EXAMPLE" if not candidates else
                   "NO_HOLDOUT" if not tests else
                   "NO_ELIGIBLE_TRAINED_HEAD" if not measures else
                   "BOUNDED_SLICE_GAIN" if passing else "MEASURED_WITHOUT_BASELINE_GAIN")
        pull_reports.append({
            "pr": n, "title": pull["title"], "pull_state": pull["state"], "head": pull["head"],
            "files": entry["files"], "changed_tests": len(changed),
            "prepared_examples": len(candidates), "assessment_examples": len(tests),
            "unmeasured_assessment_examples": sum(r["task"] not in labels for r in tests),
            "measured": measures, "passed_task_slices": passing,
            "changed_tests_without_passing_probe": pending,
            # Keep V1's meaning intact. The stricter V14 gate also requires
            # every assessment row to have an eligible head.
            "necessary_coverage_gate": necessary,
            "legacy_necessary_coverage_gate": necessary,
            "all_assessment_rows_measured": all_measured,
            "strict_cumulative_gate": strict,
            "scope": "BOUNDED_SLICES_ONLY" if measures else "NO_MEASURED_SLICE",
            "outcome_status": outcome,
        })
    lanes = {}
    for lane in sorted({r["lane"] for r in withheld}):
        all_lane = [r for r in predictions if r["lane"] == lane]
        g = _unique(by_lane[lane])
        lane_tasks = defaultdict(list)
        for r in g:
            lane_tasks[r["task"]].append(r)
        lane_measures = {t: comparison(v, len(labels[t])) for t, v in sorted(lane_tasks.items())}
        lanes[lane] = {
            "all_heldout_rows": len(all_lane), "measured_rows": len(by_lane[lane]),
            "no_trained_head": sum(r["status"] != "PROPOSED" for r in all_lane),
            "unique_task_inputs": len(g),
            "parent_correct": sum(_equal(r["parent"], r["gold"]) for r in g),
            "final_correct": sum(_equal(r["prediction"], r["gold"]) for r in g),
            "tasks": lane_measures,
            "interpretation": "PUBLISHED_CODE_CONTRACT_PREDICTION_NOT_ARABIC_UNDERSTANDING" if lane == "masked_public_contract" else "SOURCE_LANE_SPECIFIC_RETROSPECTIVE_MEASUREMENT",
        }
    summary = {
        "range": 143, "total_examples": len(rows),
        "all_task_ids": len({r["task"] for r in rows}), "retained_trained_heads": len(labels),
        "all_heldout": len(withheld), "measured_rows": len(measured),
        "no_trained_head": len(withheld)-len(measured),
        "parent_correct_rows": sum(_equal(r["parent"], r["gold"]) for r in measured),
        "final_correct_rows": sum(_equal(r["prediction"], r["gold"]) for r in measured),
        "unique_task_inputs": len(unique),
        "parent_correct_unique": sum(_equal(r["parent"], r["gold"]) for r in unique),
        "final_correct_unique": sum(_equal(r["prediction"], r["gold"]) for r in unique),
        "lost_from_parent_unique": sum(t["lost_from_parent"] for t in tasks.values()),
        "gained_from_parent_unique": sum(t["gained_from_parent"] for t in tasks.values()),
        "measured_tasks": len(tasks),
        "passing_tasks": sum(t["passed"] for t in tasks.values()),
        "improved_tasks_over_parent": sum(t["improved_over_parent"] for t in tasks.values()),
        "regressed_tasks_from_parent": sum(t["regressed_from_parent"] for t in tasks.values()),
        "no_parent_correct_lost": all(t["no_parent_correct_lost"] for t in tasks.values()),
        "prs_with_examples": sum(bool(r["prepared_examples"]) for r in pull_reports),
        "prs_with_measurement": sum(bool(r["measured"]) for r in pull_reports),
        "prs_with_passing_slice": sum(bool(r["passed_task_slices"]) for r in pull_reports),
        "prs_meeting_necessary_coverage": sum(r["necessary_coverage_gate"] for r in pull_reports),
        "unmet_necessary_coverage": [r["pr"] for r in pull_reports if not r["necessary_coverage_gate"]],
        "necessary_gate_passed": all(r["necessary_coverage_gate"] for r in pull_reports),
        "legacy_necessary_gate_passed": all(r["necessary_coverage_gate"] for r in pull_reports),
        "prs_meeting_strict_cumulative_coverage": sum(r["strict_cumulative_gate"] for r in pull_reports),
        "unmet_strict_cumulative_coverage": [r["pr"] for r in pull_reports if not r["strict_cumulative_gate"]],
        "strict_cumulative_gate_passed": all(r["strict_cumulative_gate"] for r in pull_reports),
        "outcome_counts": dict(sorted(Counter(r["outcome_status"] for r in pull_reports).items())),
        "excluded": pack.get("excluded", {}),
    }
    report = {
        "schema": "nabt.cumulative-v14-evaluation.v1", "authority": "NONE",
        "assessment": "RETROSPECTIVE_FIXED_HISTORICAL_HOLDOUT_NOT_NEW_BLIND_VALIDATION",
        "selection": "REPORT_ONLY_NO_WEIGHT_OR_MODEL_SELECTION",
        "coverage_scope": "NECESSARY_CONDITION_ONLY; FULL_PR_OUTCOME_SEMANTICS_REMAIN_REQUIRED",
        "model_variant": bundle["manifest"]["variant"],
        "model_weights_sha256": bundle["manifest"]["weights_sha256"],
        "model_input_sha256": bundle["manifest"]["inputs"],
        "parent_weights_sha256": parent_manifest["weights_sha256"],
        "summary": summary, "tasks": tasks, "pulls": pull_reports,
        "predictions": predictions, "lanes": lanes,
    }
    if ablate:
        report["fixed_weight_inference_ablation"] = {
            channel: {lane: dict(counts) for lane, counts in groups.items()}
            for channel, groups in ablations.items()
        }
    return report


def coverage_csv(report):
    """Render every PR from the same report that the replay checker rebuilds."""
    output = io.StringIO(newline="")
    fields = (
        "pr", "title", "state", "head", "changed_files", "changed_tests",
        "train_examples", "heldout_examples", "scored", "unmeasured_heldout",
        "parent_correct", "final_correct", "lost_from_parent", "gained_from_parent",
        "measured_task_slices", "passing_task_slices", "changed_tests_without_passing_probe",
        "legacy_necessary_coverage_gate", "all_assessment_rows_measured",
        "strict_cumulative_gate", "scope", "outcome_status",
    )
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for pull in report["pulls"]:
        measures = list(pull["measured"].values())
        writer.writerow({
            "pr": pull["pr"], "title": pull["title"], "state": pull["pull_state"],
            "head": pull["head"], "changed_files": pull["files"],
            "changed_tests": pull["changed_tests"],
            "train_examples": pull["prepared_examples"] - pull["assessment_examples"],
            "heldout_examples": pull["assessment_examples"],
            "scored": sum(m["final"]["n"] for m in measures),
            "unmeasured_heldout": pull["unmeasured_assessment_examples"],
            "parent_correct": sum(m["parent"]["correct"] for m in measures),
            "final_correct": sum(m["final"]["correct"] for m in measures),
            "lost_from_parent": sum(m["lost_from_parent"] for m in measures),
            "gained_from_parent": sum(m["gained_from_parent"] for m in measures),
            "measured_task_slices": len(measures),
            "passing_task_slices": len(pull["passed_task_slices"]),
            "changed_tests_without_passing_probe": pull["changed_tests_without_passing_probe"],
            "legacy_necessary_coverage_gate": str(pull["legacy_necessary_coverage_gate"]).lower(),
            "all_assessment_rows_measured": str(pull["all_assessment_rows_measured"]).lower(),
            "strict_cumulative_gate": str(pull["strict_cumulative_gate"]).lower(),
            "scope": pull["scope"], "outcome_status": pull["outcome_status"],
        })
    return output.getvalue()


def save_report(directory=None, report=None):
    directory = Path(directory) if directory is not None else DIRECTORY
    full = build_report(directory) if report is None else report
    if "fixed_weight_inference_ablation" in full:
        raise ValueError("Save ablation diagnostics separately from the replay baseline")
    evaluation = {k: v for k, v in full.items() if k != "predictions"}
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "evaluation.json").write_text(canonical(evaluation) + "\n", encoding="utf-8")
    (directory / "predictions.json.gz").write_bytes(
        gzip.compress(canonical(full["predictions"]).encode(), mtime=0)
    )
    (directory / "coverage.csv").write_bytes(coverage_csv(full).encode())
    return full


def replay(directory=None, *, ablate=False):
    directory = Path(directory) if directory is not None else DIRECTORY
    fresh = build_report(directory, ablate=False)
    predictions = fresh.pop("predictions")
    if canonical(_read(directory, "evaluation.json")) != canonical(fresh):
        raise ValueError("Changed V14 evaluation, scores, baselines, or coverage")
    if canonical(_read(directory, "predictions.json.gz")) != canonical(predictions):
        raise ValueError("Changed V14 prediction rows, order, or pending outcomes")
    if (directory / "coverage.csv").read_bytes() != coverage_csv(fresh).encode():
        raise ValueError("Changed V14 CSV coverage, denominators, or gates")
    result = dict(fresh["summary"], replayed_heldout_predictions=fresh["summary"]["measured_rows"],
                  checked_all_heldout_rows=len(predictions), replay="PASS")
    if ablate:
        result["fixed_weight_inference_ablation"] = build_report(directory, ablate=True)["fixed_weight_inference_ablation"]
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DIRECTORY)
    parser.add_argument("--require-every-pr", action="store_true")
    parser.add_argument("--ablate-parents", action="store_true")
    args = parser.parse_args(argv)
    report = replay(args.directory, ablate=args.ablate_parents)
    print(canonical(report))
    return 2 if args.require_every_pr and not report["strict_cumulative_gate_passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
