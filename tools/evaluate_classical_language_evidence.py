#!/usr/bin/env python3
"""Replay authored classical-source contract tests and ten bounded examples.

The initial semantic counterexample matrix predates the adapter. The executable
tests and demonstrations were developed with implementation and source access.
This is not a blinded language holdout, a historical-authenticity examination,
or a new observation of the events described in classical books.
"""

from __future__ import annotations

import argparse
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
TEST_PATTERN = "test_classical_language_evidence.py"
MATRIX_PATH = "evidence/classical_language/independent_case_matrix_v1.json"
MATRIX_SHA256 = "3516e8359ed4fcd05f3355b6a52fa9708b9011c4ca4e54aeaa1686e2c685c66a"
sys.path[:0] = [str(ROOT), str(ROOT / "src")]


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def record(path):
    path = path.resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Evaluation input is outside the repository")
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
            "sha256": sha256(raw).hexdigest()}


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

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self._outcome(test, "EXPECTED_FAILURE")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self._outcome(test, "UNEXPECTED_SUCCESS")

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        self.subtests.append({"test_id": test.id(), "parameters": str(subtest.params),
                              "outcome": "PASS" if err is None else "FAIL"})
        if err is not None:
            self._outcome(test, "FAIL")


def run_tests():
    os.environ["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + str(ROOT)
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern=TEST_PATTERN)
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2,
                                    resultclass=RecordedResult).run(suite)
    if result.testsRun == 0:
        raise ValueError("No classical language evidence tests were discovered")
    groups = {}
    for method in result.methods:
        group = method["test_id"].split(".")[-2]
        groups[group] = groups.get(group, 0) + 1
    return {
        "strict_pass": result.wasSuccessful() and not result.skipped and not result.expectedFailures,
        "test_methods_run": result.testsRun, "subtests_run": len(result.subtests),
        "failure_count": len(result.failures), "error_count": len(result.errors),
        "skipped_count": len(result.skipped), "expected_failure_count": len(result.expectedFailures),
        "unexpected_success_count": len(result.unexpectedSuccesses),
        "test_discovery_pattern": TEST_PATTERN,
        "methods_by_class": groups, "methods": result.methods, "subtests": result.subtests,
        "log": log.getvalue(),
        "denominator": ("Authored unittest methods with separately enumerated subcases. "
                        "Methods and subcases are not added together as independent observations. "
                        "Checker mutation cases test the conformance checker, not natural grammar."),
    }


# These expectations are stated independently of assess() output and of the
# request's claimed expected result. Changing a request does not rewrite them.
EXAMPLE_EXPECTATIONS = {
    "awamil_partition.json": {
        "status": "CONDITIONALLY_CHECKED",
        "actual": {"samai": 91, "qiyasi": 7, "manawi": 2, "total": 100},
        "source_evidence_kind": "MANUALLY_REVIEWED_TRANSCRIPTION",
        "premises_authority": "CALLER_INTERPRETED",
    },
    "external_event.json": {"status": "DEFER", "actual": None},
    "maqayis_ilm.json": {
        "status": "LEXICALLY_ATTESTED", "actual": {"root": "علم", "gloss": "العلم: نقيض الجهل"},
        "source_evidence_kind": "LEXICAL_ENTRY",
    },
    "maqayis_ktb.json": {
        "status": "LEXICALLY_ATTESTED",
        "actual": {"root": "كتب", "gloss": "أصل صحيح واحد يدل على جمع شيء إلى شيء."},
        "source_evidence_kind": "LEXICAL_ENTRY",
    },
    "maqayis_universal.json": {"status": "DEFER", "actual": None},
    "qatr_inna.json": {
        "status": "CONDITIONALLY_CHECKED", "actual": {"options": ["governed"]},
        "ambiguity_retained": False, "premises_authority": "CALLER_INTERPRETED",
    },
    "qatr_layta_ma.json": {
        "status": "CONDITIONALLY_CHECKED", "actual": {"options": ["governed", "blocked"]},
        "ambiguity_retained": True, "premises_authority": "CALLER_INTERPRETED",
    },
    "qatr_unknown_ma.json": {
        "status": "DEFER", "actual": {"options": []}, "ambiguity_retained": False,
        "premises_authority": "CALLER_INTERPRETED",
    },
    "sibawayhi_reported_usage.json": {
        "status": "ATTESTED", "source_evidence_kind": "REPORTED_USAGE_WITH_TRANSMISSION_AND_SCOPE_LIMIT",
    },
    "sibawayhi_surface.json": {
        "status": "CONDITIONALLY_CHECKED", "actual": {"courses": ["nasb", "fath"]},
        "ambiguity_retained": True, "premises_authority": "CALLER_INTERPRETED",
    },
}


def demonstrations():
    from tools.classical_language_evidence import assess, verify

    rows, status_counts = [], {}
    for filename, expected in EXAMPLE_EXPECTATIONS.items():
        path = ROOT / "examples/classical_language" / filename
        request = json.loads(path.read_bytes())
        actual = assess(request)
        verification = verify(actual, request)
        selected = {key: actual.get(key) for key in expected}
        expected_replay = {"valid": True, "status": "VERIFIED", "claim_status": expected["status"]}
        selected_replay = {key: verification.get(key) for key in expected_replay}
        boundaries = {"source_attested": True, "target_parsed": False,
                      "application_established": False, "external_event_established": False,
                      "universal_language_certified": False}
        observed_boundaries = {key: actual.get(key) for key in boundaries}
        passed = (canonical(selected) == canonical(expected)
                  and canonical(selected_replay) == canonical(expected_replay)
                  and canonical(observed_boundaries) == canonical(boundaries))
        rows.append({"case_id": path.stem, "request_file": record(path),
                     "expected": {**expected, **boundaries}, "expected_replay": expected_replay,
                     "passed": passed, "actual_report": actual, "exact_replay": verification})
        status_counts[actual["status"]] = status_counts.get(actual["status"], 0) + 1
    return {
        "strict_pass": all(row["passed"] for row in rows),
        "cases_run": len(rows), "cases_passed": sum(row["passed"] for row in rows),
        "claim_status_counts": status_counts, "cases": rows,
        "denominator": ("Ten authored examples with independently stated contract expectations. "
                        "A correctly retained DEFER counts as a passing contract example, not a "
                        "positive linguistic claim. VERIFIED means report replay, not claim truth."),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-version", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        if re.fullmatch(r"v[1-9][0-9]*", args.evidence_version) is None:
            raise ValueError("Evidence version requires v followed by a positive integer")
        output = args.output_dir.resolve()
        paths = [output / f"independent_tests_{args.evidence_version}.json",
                 output / f"demonstration_{args.evidence_version}.json"]
        if args.output_dir.is_symlink() or any(path.exists() or path.is_symlink() for path in paths):
            raise ValueError("Choose fresh evidence paths; earlier observations are never overwritten")
        from tools.classical_language_evidence import CATALOG_PATH, CATALOG_SHA256, VERSION, audit_catalog

        matrix = record(ROOT / MATRIX_PATH)
        if matrix["sha256"] != MATRIX_SHA256:
            raise ValueError("The initial counterexample matrix changed")
        catalog_path = ROOT / CATALOG_PATH
        if record(catalog_path)["sha256"] != CATALOG_SHA256:
            raise ValueError("Installed catalog does not match the code pin")
        catalog = json.loads(catalog_path.read_bytes())
        example_paths = sorted((ROOT / "examples/classical_language").glob("*.json"))
        if {path.name for path in example_paths} != set(EXAMPLE_EXPECTATIONS):
            raise ValueError("Published example inventory differs from the ten declared cases")
        input_paths = [ROOT / name for name in (
            "tools/classical_language_evidence.py", "tools/check_classical_language_evidence.py",
            "tools/evaluate_classical_language_evidence.py", "tests/test_classical_language_evidence.py",
            "formal/lean-toolchain", "formal/Nabt/ClassicalLanguageEvidence.lean",
            "formal/ExportClassicalLanguageEvidence.lean", MATRIX_PATH, CATALOG_PATH,
            "evidence/classical_language/report_budget_review_v1/reproduce.py",
            "evidence/classical_language/report_budget_review_v1/classical_language_evidence_before.py",
            "evidence/classical_language/report_budget_review_v1/observed_before.json",
            "evidence/classical_language/report_budget_review_v1/observed_after.json",
        )] + example_paths + [ROOT / source["local_path"] for source in catalog["sources"]]
        files_before = [record(path) for path in input_paths]
        provenance = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "python": sys.version, "platform": platform.platform(),
            "base_git_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                check=True, capture_output=True, text=True).stdout.strip(),
            "catalog_path": CATALOG_PATH, "catalog_sha256": CATALOG_SHA256,
            "input_files": files_before,
            "reproduction": {
                "argv": ["python", "tools/evaluate_classical_language_evidence.py",
                         "--evidence-version", args.evidence_version, "--output-dir", "<new-output-directory>"],
                "working_directory": "repository root",
            },
        }
        authorship = {
            "author": "Separate evaluation agent in the shared implementation workspace",
            "initial_matrix": {**matrix, "semantic_scenarios": 29, "selected_source_windows": 7,
                               "execution_status": "Design artifact, not 29 executed measurements"},
            "independence": ("The initial matrix was recorded before the adapter implementation. "
                             "The later executable tests and ten examples were authored with source "
                             "and implementation access; defects were shared and repaired during review. "
                             "This is not blind, held out, or external expert review."),
            "oracle": ("Selected raw byte windows, explicit source statements and declared authority "
                       "boundaries. Checker mutation cases exercise format and tamper detection; "
                       "fresh finite Lean correspondence is reported separately."),
            "gold_boundary": ("Existing construction/discourse gold is not a source for these examples "
                              "and its scores are not changed by this evaluation."),
            "source_boundary": ("Pins authenticate the deposited digital edition or reviewed transcript. "
                                "Passage selection and interpretation are authored. No historical "
                                "speaker, manuscript chain, or external event is authenticated here."),
            "review_history": ("The immutable initial matrix and catalog v1 predate a correction of "
                               "the han example's kind to reported usage by unnamed speakers in catalog v2. "
                               "A real valid-request/report-budget replay defect was preserved with "
                               "pre-fix code and observations, then tested again after a separate report budget. "
                               "These corrections are not hidden as blind successes."),
        }
        source_audit = audit_catalog()
        if source_audit["status"] != "VERIFIED":
            raise ValueError("The installed source catalog did not reopen completely")
        tests = run_tests()
        demo = demonstrations()
        files_after = [record(path) for path in input_paths]
        if files_after != files_before:
            raise ValueError("A pinned evaluation input changed during execution")
        if sorted((ROOT / "examples/classical_language").glob("*.json")) != example_paths:
            raise ValueError("The example inventory changed during execution")
        provenance["input_files_unchanged_during_execution"] = True
        provenance["source_audit"] = {
            "status": source_audit["status"], "sources_reopened": len(source_audit["sources"]),
            "passages_reopened": len(source_audit["records"]),
            "raw_source_authentication_only": True,
        }
        output.mkdir(parents=True, exist_ok=True)
        for path, result in zip(paths, (tests, demo)):
            report = {"version": VERSION, "evidence_version": args.evidence_version,
                      "provenance": provenance, "authorship": authorship,
                      "application_established": False, "external_event_established": False,
                      "universal_language_certified": False, **result}
            with path.open("x", encoding="utf-8") as handle:
                json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
                handle.write("\n")
        print(json.dumps({"strict_pass": tests["strict_pass"] and demo["strict_pass"],
                          "evidence_version": args.evidence_version,
                          "test_methods_run": tests["test_methods_run"], "subtests_run": tests["subtests_run"],
                          "demonstrations_run": demo["cases_run"], "demonstrations_passed": demo["cases_passed"],
                          "demonstration_status_counts": demo["claim_status_counts"],
                          "output_files": [str(path) for path in paths]}, indent=2))
        return 0 if tests["strict_pass"] and demo["strict_pass"] else 1
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(json.dumps({"strict_pass": False, "error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
