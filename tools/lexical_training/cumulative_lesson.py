"""NTP observation of historical PR measurements or predictions from the installed learner."""

import gzip
from hashlib import sha256
import json
import math
from pathlib import Path

from . import cumulative_features as features, corpus_verbs

SCHEMA = "nabt.ntl.cumulative-outcomes.v1"
RESULT = "nabt.ntl.cumulative-outcomes-result.v1"
DIRECTORY = Path(__file__).resolve().parents[2] / "evidence/cumulative_outcomes_v1"
PINS = {
    "pulls.json": "bba71eaacaf79cab1f40d1d6c8e04c229ae29720c0bca44a915530e7b6e22b80",
    "manifest.json": "27387baa87f72343e6818483fa3a4dc379ab7cb8cc62cd0e538187f0c6f9a4a9",
    "weights.json.gz": "4542016e2543aed5d7bbb9d2f87d50d96607b6d212264ed49098107f40148028",
    "evaluation.json": "42590444c9c5eeec2e5325aa738033a2e32516e4d2374b16944087547a057ebc",
}


def artifact(name):
    data = (DIRECTORY / name).read_bytes()
    if sha256(data).hexdigest() != PINS[name]:
        raise ValueError("Changed cumulative artifact")
    if name.endswith(".gz"):
        data = gzip.decompress(data)
    return json.loads(data)


def observe(model, labels, task, x):
    # The deployed calculation requires only the Python standard library.
    hidden = [
        math.tanh(sum(a * b for a, b in zip(x, c, strict=True))) for c in model["shared_columns"]
    ]
    weights = model["heads"][task]
    values = [v[-1] + sum(a * b for a, b in zip(hidden, v[:-1], strict=True)) for v in weights]
    return labels[task][max(range(len(values)), key=values.__getitem__)]


def run(lesson):
    base = {"schema": RESULT, "authority": "NONE", "execution_measured": False}
    if type(lesson) is not dict or lesson.get("schema") != SCHEMA:
        raise ValueError("Unknown cumulative lesson")
    if set(lesson) == {"schema", "pr"}:
        n = lesson["pr"]
        if type(n) is not int or not 1 <= n <= 143:
            raise ValueError("Expected PR 1..143")
        try:
            report = artifact("evaluation.json")["pulls"][n - 1]
            pull = artifact("pulls.json")[n - 1]
        except (OSError, ValueError):
            return dict(base, status="ARTIFACT_UNAVAILABLE")
        measures = {
            t: {
                "correct": m["final"]["correct"],
                "n": m["final"]["n"],
                "passed": m["passed"],
                "lost_after_learning": m["lost_after_learning"],
            }
            for t, m in report["measured"].items()
        }
        return dict(
            base,
            status="MEASURED" if measures else "UNMEASURED",
            execution_measured=True,
            pr=n,
            head=pull["head"],
            pull_state=pull["state"],
            title=pull["title"],
            necessary_coverage_gate=report["necessary_coverage_gate"],
            prepared_examples=report["prepared_examples"],
            changed_tests=report["changed_tests"],
            changed_tests_without_passing_probe=report["changed_tests_without_passing_probe"],
            outcome_slices=measures,
        )
    if (
        set(lesson) != {"schema", "task", "text"}
        or type(lesson["task"]) is not str
        or not 1 <= len(lesson["task"]) <= 256
    ):
        raise ValueError("Expected a PR number or a task and its text")
    text = lesson["text"]
    if type(text) is not str or not text.strip() or len(text.encode()) > 1024:
        raise ValueError("Expected 1..1024 source bytes")
    try:
        manifest = artifact("manifest.json")
        if lesson["task"] not in manifest["labels"]:
            return dict(base, status="DEFER_NO_TRAINED_HEAD")
        model = artifact("weights.json.gz")
        x = features.features(text, features.parents())
    except (OSError, ValueError):
        return dict(base, status="ARTIFACT_UNAVAILABLE")
    label = observe(model, manifest["labels"], lesson["task"], x)
    value = (
        corpus_verbs.apply_script(json.loads(label), corpus_verbs.carriers(text))
        if lesson["task"] == "root_recipe"
        else label
    )
    return dict(
        base,
        status="PROPOSED",
        execution_measured=True,
        task=lesson["task"],
        value=value,
        label=label,
        weights_sha256=manifest["weights_sha256"],
        review_only=True,
    )
