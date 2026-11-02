"""Retain a cheap before/after observation of publication helper guards.

Historical helpers run only as copied modules inside temporary directories.
The five tests use real small filesystem/Git fixtures and intercept expensive
archive/child-test execution.  No retained release output is executed or edited.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BEFORE = "2d6ec3b10f7b80a690060cebe9ddb502dfc36911"
TEST = "tests/test_derivation_surface_evidence_harness.py"
HELPERS = (
    "evidence/derivation_surface_v1/validation/clean_checkout/run_clean_checkout.py",
    "evidence/derivation_surface_v1/validation/clean_checkout_final/run_clean_checkout.py",
    "evidence/derivation_surface_v1/validation/collect_release_evidence.py",
)


def identity(raw):
    return {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("before", "after"))
    phase = parser.parse_args().phase
    output = HERE / phase
    output.mkdir(exist_ok=False)
    test_bytes = (ROOT / TEST).read_bytes()
    (output / "test_source.py.txt").write_bytes(test_bytes)
    selected = {}
    sources = {}
    for index, name in enumerate(HELPERS):
        raw = (subprocess.check_output(["git", "show", BEFORE + ":" + name], cwd=ROOT)
               if phase == "before" else (ROOT / name).read_bytes())
        selected[name] = raw
        snapshot = output / (str(index + 1) + "_helper.py.txt")
        snapshot.write_bytes(raw)
        sources[name] = {**identity(raw), "saved_source": str(snapshot.relative_to(ROOT))}
    spec = importlib.util.spec_from_file_location("test_derivation_surface_evidence_harness", ROOT / TEST)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix="nabt-publication-helper-inputs-") as temp:
        chosen = Path(temp)
        for name, raw in selected.items():
            path = chosen / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        module.SOURCE_ROOT = chosen
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        declared_methods = suite.countTestCases()
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    log = stream.getvalue().encode("utf-8")
    (output / "unittest.log").write_bytes(log)
    unsuccessful = [
        {"id": test.id(), "outcome": outcome}
        for outcome, rows in (("failure", result.failures), ("error", result.errors))
        for test, _ in rows
    ]
    unchanged = (ROOT / TEST).read_bytes() == test_bytes
    if phase == "after":
        unchanged = unchanged and all((ROOT / name).read_bytes() == raw for name, raw in selected.items())
    report = {
        "schema": "nabt.derivation-surface.publication-helper-review.v1",
        "phase": phase, "observed_utc": datetime.now(timezone.utc).isoformat(),
        "before_commit": BEFORE,
        "workspace_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "command": "PYTHONDONTWRITEBYTECODE=1 python evidence/derivation_surface_v1/review/publication_harness/run_review.py " + phase,
        "scope": "Five focused helper regressions using synthetic isolated evidence; no full suite, real release archive, or historical output rewrite",
        "test_source": {"path": TEST, **identity(test_bytes)},
        "runner_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "helper_sources": sources,
        "test_methods": declared_methods, "tests_run": result.testsRun,
        "skips": len(result.skipped), "failure_outcomes": len(result.failures),
        "error_outcomes": len(result.errors), "successful": result.wasSuccessful(),
        "unsuccessful_outcomes": unsuccessful,
        "distinct_methods_with_unsuccessful_outcomes": len({row["id"].split(" (", 1)[0] for row in unsuccessful}),
        "retained_inputs_unchanged_during_observation": unchanged,
        "log": {"path": str((output / "unittest.log").relative_to(ROOT)), **identity(log)},
        "process_exit_code": 0 if result.wasSuccessful() and unchanged else 1,
    }
    with (output / "summary.json").open("x", encoding="utf-8") as target:
        json.dump(report, target, ensure_ascii=False, indent=2)
        target.write("\n")
    print(json.dumps({key: report[key] for key in (
        "phase", "tests_run", "skips", "failure_outcomes", "error_outcomes", "successful",
        "distinct_methods_with_unsuccessful_outcomes", "retained_inputs_unchanged_during_observation",
        "process_exit_code", "log")}, ensure_ascii=False))
    return report["process_exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
