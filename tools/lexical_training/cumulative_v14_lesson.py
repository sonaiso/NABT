"""NTP observations from the installed continuation of the cumulative PR learner.

The caller selects a historical report or supplies a task and source text.  It
cannot select weights, a parent, a calibration split, or a licensing authority.
Both the inherited and continued predictions remain review-only observations.
"""

from copy import deepcopy
import gzip
from hashlib import sha256
import json
from pathlib import Path

from . import cumulative_lesson

SCHEMA = "nabt.ntl.cumulative-v14.v1"
RESULT = "nabt.ntl.cumulative-v14-result.v1"
DIRECTORY = Path(__file__).resolve().parents[2] / "evidence/cumulative_v14"
ARTIFACT_NAMES = (
    "manifest.json", "weights.json.gz", "protocol.json", "skill_layout.json", "evaluation.json"
)
# Installed byte identities after training and replay. No hash is inferred
# from a request or from an artifact's own claim about its identity.
PINS = {
    "manifest.json": "16735e577f5a7e753ccf0eb691827b3ca117902ece047db01dbaefdca3ea0f9c",
    "weights.json.gz": "f1570cbf5ed419784d1401f10aa9ffdceed22f8177c0335f3d889c1523f5da04",
    "protocol.json": "8576e89bbbf4612becb2ecca633fe530e28f2e5321e04645fc369fb2ea6edfe1",
    "skill_layout.json": "356c14cd8022cb14b14a6e69a46304a0d4d561dbfa8b280f4d86a718f263dd3e",
    "evaluation.json": "0c319d53d182790b34c8efd7013197b78afc5724c4cea44ea2d513c9e4b92702",
}


def artifact(name):
    if set(PINS) != set(ARTIFACT_NAMES) or any(
        type(value) is not str
        or len(value) != 64
        or any(c not in "0123456789abcdef" for c in value)
        for value in PINS.values()
    ):
        raise ValueError("V14 artifact pins are not installed")
    if name not in ARTIFACT_NAMES:
        raise ValueError("Unknown V14 artifact")
    path = DIRECTORY / name
    if path.is_symlink() or not path.resolve().is_relative_to(DIRECTORY.resolve()):
        raise ValueError("V14 artifact escapes installed directory")
    data = path.read_bytes()
    if sha256(data).hexdigest() != PINS[name]:
        raise ValueError("Changed V14 artifact")
    if name.endswith(".gz"):
        data = gzip.decompress(data)
    return json.loads(data)


def _checked_bundle():
    artifacts = {name: artifact(name) for name in ARTIFACT_NAMES}
    from . import cumulative_v14_model as model

    bundle = model.load(DIRECTORY)
    # A fresh owner replay must not mix an old manifest with replacement
    # weights, even when this internal owner is invoked without the gateway.
    for name in ARTIFACT_NAMES:
        artifact(name)
    if bundle["manifest"] != artifacts["manifest.json"]:
        raise ValueError("V14 manifest changed during loading")
    return bundle, artifacts["evaluation.json"]


def _identity(bundle):
    return {
        "weights_sha256": PINS["weights.json.gz"],
        "parent_weights_sha256": bundle["parent_manifest"]["weights_sha256"],
        "protocol_sha256": PINS["protocol.json"],
        "skill_layout_sha256": PINS["skill_layout.json"],
    }


def run(lesson):
    base = {
        "schema": RESULT,
        "authority": "NONE",
        "review_only": True,
        "execution_measured": False,
    }
    if type(lesson) is not dict or lesson.get("schema") != SCHEMA:
        raise ValueError("Unknown V14 cumulative lesson")
    if set(lesson) == {"schema", "pr"}:
        n = lesson["pr"]
        if type(n) is not int or not 1 <= n <= 143:
            raise ValueError("Expected PR 1..143")
        try:
            bundle, evaluation = _checked_bundle()
            report = evaluation["pulls"][n - 1]
            pull = cumulative_lesson.artifact("pulls.json")[n - 1]
            if pull["number"] != n or report["pr"] != n:
                raise ValueError("Mismatched historical PR report")
            measures = deepcopy(report["measured"])
            return dict(
                base,
                status="MEASURED" if measures else "UNMEASURED",
                execution_measured=True,
                pr=n,
                head=pull["head"],
                pull_state=pull["state"],
                title=pull["title"],
                necessary_coverage_gate=report["necessary_coverage_gate"],
                legacy_necessary_coverage_gate=report["legacy_necessary_coverage_gate"],
                all_assessment_rows_measured=report["all_assessment_rows_measured"],
                strict_cumulative_gate=report["strict_cumulative_gate"],
                prepared_examples=report["prepared_examples"],
                assessment_examples=report["assessment_examples"],
                unmeasured_assessment_examples=report["unmeasured_assessment_examples"],
                changed_tests=report["changed_tests"],
                changed_tests_without_passing_probe=report["changed_tests_without_passing_probe"],
                outcome_status=report["outcome_status"],
                scope=report["scope"],
                outcome_slices=measures,
                **_identity(bundle),
            )
        except (OSError, ValueError, KeyError, IndexError, TypeError):
            return dict(base, status="ARTIFACT_UNAVAILABLE")
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
        bundle, _ = _checked_bundle()
        task = lesson["task"]
        if task not in bundle["manifest"]["labels"]:
            return dict(base, status="DEFER_NO_TRAINED_HEAD")
        from . import cumulative_v14_model as model

        proposed = model.propose(bundle, task, text)
        if proposed["authority"] != "NONE" or proposed["review_only"] is not True:
            raise ValueError("Model output cannot grant authority")
        if type(proposed["changed"]) is not bool:
            raise ValueError("Invalid parent comparison")
        return dict(
            base,
            status="PROPOSED",
            execution_measured=True,
            task=task,
            label=proposed["label"],
            value=proposed["value"],
            parent_label=proposed["parent_label"],
            parent_value=proposed["parent_value"],
            changed=proposed["changed"],
            **_identity(bundle),
        )
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        return dict(base, status="ARTIFACT_UNAVAILABLE")
