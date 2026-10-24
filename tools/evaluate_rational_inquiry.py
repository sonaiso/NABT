#!/usr/bin/env python3
"""Reproduce the authored inquiry-contract tests and six bounded demonstrations.

This evaluates an exactly frozen runtime. It is not a natural-language holdout,
an authenticated acquisition experiment, or an observation of a physical box.
Existing evidence files are never overwritten.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEST_PATTERN = "test_rational_inquiry*.py"
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from tools.text_evaluation.integrity import verify_code_freeze


def record(path):
    path = path.resolve()
    raw = path.read_bytes()
    name = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
    return {"path": name, "bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.methods = []
        self.subtests = []

    def startTest(self, test):
        super().startTest(test)
        self.methods.append({"test_id": test.id(), "outcome": "RUNNING"})

    def _outcome(self, test, outcome):
        for entry in reversed(self.methods):
            if entry["test_id"] == test.id():
                entry["outcome"] = outcome
                return

    def addSuccess(self, test):
        super().addSuccess(test)
        self._outcome(test, "PASS")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._outcome(test, "FAIL")

    def addError(self, test, err):
        super().addError(test, err)
        self._outcome(test, "ERROR")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._outcome(test, "SKIP")

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        self.subtests.append({"test_id": test.id(), "parameters": str(subtest.params),
                              "outcome": "PASS" if err is None else "FAIL"})
        if err is not None:
            self._outcome(test, "FAIL")


def run_tests():
    # The CLI probes launch a new Python process, which needs the same local src.
    os.environ["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + str(ROOT)
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"),
                                                pattern=TEST_PATTERN)
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2,
                                    resultclass=RecordedResult).run(suite)
    if result.testsRun == 0:
        raise ValueError("No inquiry contract tests were discovered")
    return {
        "strict_pass": result.wasSuccessful() and not result.skipped,
        "test_methods_run": result.testsRun,
        "subtests_run": len(result.subtests),
        "failure_count": len(result.failures),
        "error_count": len(result.errors),
        "skipped_count": len(result.skipped),
        "test_discovery_pattern": TEST_PATTERN,
        "methods": result.methods,
        "subtests": result.subtests,
        "log": log.getvalue(),
        "denominator": ("Authored unittest methods with explicitly listed subcases. "
                        "Methods and subcases are not added together or presented as "
                        "independent observations of natural language or the world."),
    }


def demonstrations():
    from nabt.rational_inquiry import audit_inquiry, verify_inquiry

    plan = json.loads((ROOT / "examples/rational_inquiry/plan.json").read_text())
    sources = json.loads((ROOT / "examples/rational_inquiry/sources.json").read_text())
    references = [source for source in sources if source["role"] == "REFERENCE"]
    if len(references) != 1:
        raise ValueError("The published demonstration requires one base reference")
    reference_id = references[0]["source_id"]
    rows = []

    def run(case_id, case_plan, case_sources, expected, budget=128):
        actual = audit_inquiry(case_plan, case_sources, max_checks=budget)
        verified = verify_inquiry(actual, case_plan, case_sources, max_checks=budget)
        selected = {key: actual.get(key) for key in expected}
        passed = (canonical(selected) == canonical(expected) and verified["valid"] is True
                  and actual["world_truth"] == "NOT_ESTABLISHED"
                  and actual["external_truth_certified"] is False)
        rows.append({"case_id": case_id, "expected": expected, "passed": passed,
                     "inputs": {"plan": case_plan, "sources": case_sources, "max_checks": budget},
                     "actual_report": actual, "exact_replay": verified})
        return actual

    base = run("bounded_record_match", deepcopy(plan), deepcopy(sources),
               {"status": "LICENSED", "authorized_rank": 2, "box_opened": True,
                "coverage_complete": True})

    different = deepcopy(sources)
    next(s for s in different if s["source_id"] == reference_id)["content"] = "لون الصندوق أخضر."
    run("bounded_record_refutation", deepcopy(plan), different,
        {"status": "REFUTED", "authorized_rank": 0, "box_opened": True,
         "coverage_complete": True})

    conflict = deepcopy(sources)
    other = deepcopy(references[0])
    other.update(source_id="opposing-reference", origin="authored-opposing-route",
                 content="لون الصندوق أخضر.")
    conflict.append(other)
    run("incompatible_declared_records", deepcopy(plan), conflict,
        {"status": "CONFLICT", "authorized_rank": 0, "box_opened": True,
         "coverage_complete": True})

    world_plan = deepcopy(plan)
    world_plan["claim"]["kind"] = "WORLD_CORRESPONDENCE"
    run("world_observer_not_installed", world_plan, deepcopy(sources),
        {"status": "DEFER", "authorized_rank": 0, "box_opened": False,
         "coverage_complete": True})

    run("partial_check_budget", deepcopy(plan), deepcopy(sources),
        {"status": "RESOURCE_LIMIT", "authorized_rank": 0, "box_opened": True,
         "coverage_complete": False}, budget=1)

    changed = deepcopy(sources)
    next(s for s in changed if s["source_id"] == reference_id)["content"] += "!"
    rejection = verify_inquiry(base, plan, changed)
    expected = {"valid": False, "status": "REJECT", "reason": "STALE_OR_FORGED_INQUIRY"}
    rows.append({
        "case_id": "stale_source_bytes_rejected", "expected": expected,
        "passed": canonical({key: rejection.get(key) for key in expected}) == canonical(expected),
        "inputs": {"report_from_case": "bounded_record_match", "expected_plan": plan,
                   "expected_sources": changed, "max_checks": 128},
        "actual_verification": rejection,
    })
    return {
        "strict_pass": all(row["passed"] for row in rows),
        "cases_run": len(rows), "cases_passed": sum(row["passed"] for row in rows),
        "cases": rows,
        "denominator": ("Six authored contract demonstrations, including one replay rejection. "
                        "These are neither six linguistic holdouts nor six world observations."),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", required=True, type=Path,
                        help="Exact runtime freeze for this evaluation")
    parser.add_argument("--evidence-version", required=True,
                        help="Output revision such as v2; separate from the installed law version")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        if re.fullmatch(r"v[1-9][0-9]*", args.evidence_version) is None:
            raise ValueError("Evidence version requires v followed by a positive integer")
        freeze = verify_code_freeze(args.freeze, ROOT)
        output = args.output_dir.resolve()
        paths = [output / f"independent_tests_{args.evidence_version}.json",
                 output / f"demonstration_{args.evidence_version}.json"]
        if args.output_dir.is_symlink() or any(path.exists() or path.is_symlink() for path in paths):
            raise ValueError("Choose fresh report paths; existing evidence is never overwritten")
        if any(path == args.freeze.resolve() for path in paths):
            raise ValueError("Output cannot overwrite the code freeze")
        from nabt import __version__
        provenance = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "runtime_version": __version__,
            "python": sys.version,
            "platform": platform.platform(),
            "base_git_commit": subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                capture_output=True, text=True).stdout.strip(),
            "runtime_freeze": record(args.freeze),
            "runtime_snapshot_sha256": freeze["snapshot_sha256"],
            "runtime_files_verified": len(freeze["files"]),
            "evaluation_files": [record(path) for path in sorted((ROOT / "tests").glob(TEST_PATTERN))] +
                [record(ROOT / name) for name in (
                "tools/evaluate_rational_inquiry.py",
                "tools/check_rational_inquiry.py", "tools/text_evaluation/integrity.py",
                "examples/rational_inquiry/plan.json", "examples/rational_inquiry/sources.json",
            )],
            "reproduction": {
                "argv": ["python", "tools/evaluate_rational_inquiry.py", "--freeze",
                         record(args.freeze)["path"], "--evidence-version", args.evidence_version,
                         "--output-dir", "<new-output-directory>"],
                "environment": {"PYTHONPATH": "src"}, "working_directory": "repository root",
            },
        }
        authorship = {
            "author": "Separate evaluation and review agents in a shared development workspace",
            "independence": ("Counterexample matrix proposed before reading the implementation; "
                             "test code written and reviewed while implementation was available. "
                             "The implementation and tests were revised during shared review. "
                             "This is not blinded or held-out evaluation and not external human review."),
            "oracle": ("Declared authority boundaries and concrete counterexamples; not a copied "
                       "production recurrence. The separate finite conformance file compares the gate."),
            "provenance_boundary": ("Source origins, ancestry and active states are declarations. "
                                    "No acquisition identity, historical preregistration, unseen reference "
                                    "or physical observation was authenticated."),
            "review_history": ("Review hardened world-bridge and provenance/scope guards, propagated "
                               "resource exhaustion, separated context checks from claim checks, and "
                               "kept contested-premise derivations out of clean refutation. Provisional "
                               "DEFER/UNREVIEWED oracle labels were aligned with the final explicit law. "
                               "Subsequent independent review found a real CLI report-size round-trip "
                               "defect; v1 evidence is retained as pre-fix history. Discovery includes "
                               "the separately authored report-budget regressions and freeze tests."),
        }
        tests = run_tests()
        demo = demonstrations()
        # Detect source changes during the evaluation as well as before it.
        verify_code_freeze(args.freeze, ROOT)
        expected_tests = {entry["path"] for entry in provenance["evaluation_files"]
                          if entry["path"].startswith("tests/")}
        actual_tests = {path.relative_to(ROOT).as_posix()
                        for path in (ROOT / "tests").glob(TEST_PATTERN)}
        if actual_tests != expected_tests:
            raise ValueError("Inquiry test inventory changed during execution")
        for entry in provenance["evaluation_files"]:
            if record(ROOT / entry["path"]) != entry:
                raise ValueError("Evaluation input changed during execution: " + entry["path"])
        output.mkdir(parents=True, exist_ok=True)
        for path, result in zip(paths, (tests, demo)):
            report = {"law_id": "nabt.rational-inquiry.v1", "evidence_version": args.evidence_version,
                      "provenance": provenance,
                      "authorship": authorship, "external_truth_certified": False, **result}
            with path.open("x", encoding="utf-8") as handle:
                json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
                handle.write("\n")
        print(json.dumps({"strict_pass": tests["strict_pass"] and demo["strict_pass"],
                          "evidence_version": args.evidence_version,
                          "test_methods_run": tests["test_methods_run"],
                          "subtests_run": tests["subtests_run"],
                          "demonstrations_passed": demo["cases_passed"],
                          "demonstrations_run": demo["cases_run"],
                          "runtime_snapshot_sha256": freeze["snapshot_sha256"],
                          "output_files": [str(path) for path in paths]}, indent=2))
        return 0 if tests["strict_pass"] and demo["strict_pass"] else 1
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(json.dumps({"strict_pass": False, "error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
