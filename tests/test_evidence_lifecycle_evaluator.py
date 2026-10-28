"""Independent synthetic attacks on the evaluator; never execute the gold matrix."""
from copy import deepcopy
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import evaluate_evidence_lifecycle_v1 as evaluator
from tools import freeze_evidence_lifecycle_v1 as freezer


def fixture():
    source = {"identity": "test:A", "revision": "1", "content": "authored A"}
    query_source = {"identity": "test:Q", "revision": "1", "content": "authored Q"}
    key = dict(axis="recorded_observation", entity="probe", predicate="p", value="v",
               unit="u", context="ctx", time="0", place="site")
    episode = {"schema": "nabt.evidence-lifecycle.episode.v1", "episode_id": "synthetic",
        "query": {"key": key, "positive": True, "origin": "q"},
        "active_sources": [query_source, source], "origins": [{"id": "q", "parents": []}, {"id": "a", "parents": []}],
        "interpretations": [{"id": "e", "source": source, "key": key, "positive": True,
            "kind": "observation", "origin": "a", "ancestry": ["a"]}],
        "bindings": [{"origin_id": "q", "source": query_source, "rank": 0},
                     {"origin_id": "a", "source": source, "rank": 0}], "budget": 1, "updates": []}
    steps = [{"step": 0, "event_id": None, "active_sources": deepcopy(episode["active_sources"]),
        "receipt": {"status": "SUPPORTED", "support_ids": ["e"], "refutation_ids": [], "selected_ids": ["e"]},
        "dependency_ready_ids": ["e"], "dependency_blocked_ids": [], "affected_ids": []}]
    expected = {"outcome": "VALID_EPISODE", "status": "SUPPORTED", "decision_complete": True, "steps": steps}
    report = {"schema": evaluator.REPORT_SCHEMA, "law_id": evaluator.LAW_ID, "status": "SUPPORTED",
        "native_checked": True, "decision_complete": True, "evidence_class": "AUTHORED_SCENARIO",
        "observed": {"law_id": evaluator.LAW_ID, "binding": deepcopy(episode), "steps": deepcopy(steps), **evaluator.FLAGS},
        "execution": {}, **evaluator.FLAGS}
    return episode, expected, report


class ProjectionTests(unittest.TestCase):
    def test_execution_claims_are_bound_to_external_freeze(self):
        episode, expected, report = fixture()
        identity = {"code": {"reader.py": "frozen-code"}, "native": {"native": "frozen-native"}}
        execution = {"run_identity": deepcopy(identity), "error": None}
        for name, value in (("input", episode), ("proposal", report["observed"]), ("native_result", report["observed"])):
            execution[name] = deepcopy(value)
            execution[name + "_sha256"] = evaluator.digest(evaluator.wire(value).encode("utf-8"))
        report["execution"] = execution
        self.assertTrue(evaluator.audit_report(episode, expected, report, identity)["match"])
        mutations = [lambda r: r["execution"]["run_identity"]["code"].update({"reader.py": "invented-code"}),
            lambda r: r["execution"].update(input_sha256="invented"),
            lambda r: r["execution"]["proposal"]["binding"].update(episode_id="borrowed"),
            lambda r: r["execution"].update(error="hidden verification error")]
        for mutation in mutations:
            changed = deepcopy(report); mutation(changed)
            self.assertFalse(evaluator.audit_report(episode, expected, changed, identity)["match"])

    def test_typed_full_episode_and_source_binding(self):
        episode, expected, report = fixture()
        self.assertTrue(evaluator.audit_report(episode, expected, report)["match"])
        mutations = [
            lambda r: r["observed"]["binding"]["active_sources"][1].update(content="different"),
            lambda r: r["observed"]["binding"]["bindings"][1].update(rank=False),
            lambda r: r["observed"]["steps"][0].update(step=False),
            lambda r: r["observed"]["steps"][0].update(step=0.0),
            lambda r: r["observed"]["steps"][0].update(dependency_blocked_ids=None),
            lambda r: r["observed"]["steps"][0]["receipt"].update(selected_ids=[]),
            lambda r: r["observed"].update(world_truth_established=True),
            lambda r: r.update(referents_established=True),
            lambda r: r.update(native_checked=1),
            lambda r: r.update(decision_complete=1),
        ]
        for mutation in mutations:
            changed = deepcopy(report); mutation(changed)
            with self.subTest(mutation=mutation):
                audit = evaluator.audit_report(episode, expected, changed)
                self.assertFalse(audit["match"])
                self.assertTrue(audit["false_authorization"])

    def test_equal_final_state_does_not_replace_complete_history(self):
        episode, expected, report = fixture()
        changed = deepcopy(report)
        changed["observed"]["binding"]["updates"] = [{"event_id": "withdraw", "kind": "withdraw"}]
        self.assertFalse(evaluator.audit_report(episode, expected, changed)["match"])

    def test_no_native_is_a_miss_without_false_authorization(self):
        episode, expected, report = fixture()
        report.update(status="UNMEASURED", native_checked=False, decision_complete=False, observed=None)
        audit = evaluator.audit_report(episode, expected, report)
        self.assertFalse(audit["match"])
        self.assertFalse(audit["false_authorization"])
        self.assertEqual(audit["steps_match"], [False])

    def test_resource_null_diagnostics_are_not_empty_counts(self):
        episode, expected, report = fixture()
        expected.update(status="RESOURCE_LIMIT", decision_complete=False)
        step = expected["steps"][0]
        step["receipt"] = dict(status="RESOURCE_LIMIT", support_ids=[], refutation_ids=[], selected_ids=[])
        step.update(dependency_ready_ids=None, dependency_blocked_ids=None, affected_ids=None)
        report.update(status="RESOURCE_LIMIT", decision_complete=False)
        report["observed"]["steps"] = deepcopy(expected["steps"])
        self.assertTrue(evaluator.audit_report(episode, expected, report)["match"])
        report["observed"]["steps"][0]["dependency_ready_ids"] = []
        self.assertFalse(evaluator.audit_report(episode, expected, report)["match"])

    def test_error_envelope_cannot_hide_an_accepted_prefix(self):
        error = {"law_id": evaluator.LAW_ID, "status": "INVALID_INPUT", "reason": "bad graph", **evaluator.FLAGS}
        self.assertTrue(evaluator.error_native_matches(error, "INVALID_INPUT"))
        for addition in ({"steps": []}, {"binding": {}}, {"world_truth_established": True},
                         {"reason": ""}, {"reason": "\ud800"}, {"status": "UNKNOWN"}):
            self.assertFalse(evaluator.error_native_matches({**error, **addition}, "INVALID_INPUT"))

    def test_invalid_episode_cannot_claim_native_check_or_world_authority(self):
        episode, _, report = fixture()
        expected = {"outcome": "INVALID_INPUT", "status": "INVALID_INPUT", "decision_complete": False, "steps": None}
        report.update(status="INVALID_INPUT", decision_complete=False, native_checked=False, observed=None)
        self.assertTrue(evaluator.audit_report(episode, expected, report)["match"])
        report["native_checked"] = True
        self.assertTrue(evaluator.audit_report(episode, expected, report)["false_authorization"])
        report["native_checked"] = False
        for key in ("binding", "steps"):
            changed = {**report, key: []}
            audit = evaluator.audit_report(episode, expected, changed)
            self.assertFalse(audit["match"])
            self.assertTrue(audit["false_authorization"])
        case = {"id": "bad", "family": "lineage", "input": episode, "expected": expected, "verification_pairs": []}
        native = {"law_id": evaluator.LAW_ID, "status": "INVALID_INPUT", "reason": "bad", **evaluator.FLAGS}
        native["world_truth_established"] = True
        reader = SimpleNamespace(evaluate_episode=lambda _: report)
        with patch.object(evaluator, "direct_native", return_value=native):
            measured = evaluator.evaluate_case(case, reader, object())
        self.assertFalse(measured["contract_match"])
        self.assertTrue(measured["false_authorization"])

    def test_prefix_oracle_is_explicit_for_invalid_episode(self):
        episode, expected, _ = fixture()
        case = {"input": episode, "expected": {"outcome": "INVALID_INPUT"},
                "historical_prefix_expectations": [{"updates_count": 0, "expected": expected}]}
        self.assertEqual(evaluator.prefix_expected(case, 0), expected)
        with self.assertRaisesRegex(ValueError, "no independently"):
            evaluator.prefix_expected(case, 1)
        prefix = evaluator.prefix_input(case, 0)
        prefix["active_sources"][0]["content"] = "changed"
        self.assertEqual(case["input"]["active_sources"][0]["content"], "authored Q")

    def test_producer_receives_only_input_and_verifier_uses_external_episode(self):
        episode, expected, report = fixture()
        case = {"id": "synthetic", "family": "withdrawal", "input": episode, "expected": expected,
            "verification_pairs": [{"id": "self", "receipt_prefix_updates": 0, "expected_prefix_updates": 0,
                "expected_historical_replay_matches": True, "expected_historical_valid": True,
                "expected_current_replay_matches": True, "expected_current_valid": True}]}
        calls = []
        def evaluate(value):
            self.assertEqual(value, episode)
            self.assertNotIn("expected", value)
            return deepcopy(report)
        def verify(receipt, *, expected_episode):
            self.assertEqual(expected_episode, episode)
            self.assertIsNot(expected_episode, receipt["observed"]["binding"])
            calls.append(expected_episode)
            return {"replay_matches": True, "valid": True}
        reader = SimpleNamespace(evaluate_episode=evaluate, verify_episode=verify)
        with patch.object(evaluator, "direct_native", return_value=report["observed"]):
            result = evaluator.evaluate_case(case, reader, object())
        self.assertTrue(result["contract_match"])
        self.assertEqual(len(calls), 2)


class FreezeBoundaryTests(unittest.TestCase):
    def test_initial_snapshot_checks_source_native_gold_and_first_head(self):
        inner = {"files": {"source": "a"}, "native": {"native": "b"}, "commit": "head"}
        good = {"files": {"source": "a", "native": "b"}, "head": "head", "gold_sha256": evaluator.GOLD_SHA256}
        guard = SimpleNamespace(snapshot=lambda *args: deepcopy(good))
        self.assertEqual(evaluator.initial_snapshot(guard, inner, "first"), good)
        for mutate in (lambda s: s["files"].update(source="x"), lambda s: s["files"].update(native="x"),
                       lambda s: s.update(gold_sha256="x"), lambda s: s.update(head="x")):
            bad = deepcopy(good); mutate(bad)
            guard.snapshot = lambda *args: bad
            with self.assertRaisesRegex(ValueError, "initial snapshot"):
                evaluator.initial_snapshot(guard, inner, "first")

    def test_preflight_fails_before_runtime_and_preserves_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            with patch.object(evaluator, "verify_freeze", side_effect=ValueError("changed source")), \
                    patch.object(evaluator, "run") as run, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(evaluator.main(["--output", str(output), "--code-freeze", "unused", "--phase", "first"]), 2)
            run.assert_not_called()
            first = output.read_bytes()
            self.assertEqual(json.loads(first)["failure_stage"], "preflight")
            with self.assertRaises(FileExistsError):
                evaluator.main(["--output", str(output), "--code-freeze", "unused", "--phase", "exposed"])
            self.assertEqual(output.read_bytes(), first)

    def test_freeze_output_is_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "freeze.json"
            output.write_text("retained")
            with patch.object(freezer, "build_freeze", return_value={}):
                with self.assertRaises(FileExistsError):
                    freezer.main(["--output", str(output)])
            self.assertEqual(output.read_text(), "retained")

    def test_mid_execution_failure_retains_completed_rows_and_case_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "failed.json"
            error = evaluator.ScenarioExecutionError("second", [{"id": "first", "contract_match": True}], ValueError("native stopped"))
            with patch.object(evaluator, "verify_freeze", return_value=({}, {})), \
                    patch.object(evaluator, "run", side_effect=error), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(evaluator.main(["--output", str(output), "--code-freeze", "unused", "--phase", "first"]), 2)
            report = json.loads(output.read_text())
            self.assertEqual(report["failed_case_id"], "second")
            self.assertEqual(report["completed_rows"], [{"id": "first", "contract_match": True}])
            self.assertFalse(report["acceptance_gate"]["passed"])

    def test_bootstrap_still_pinned_and_strict(self):
        guard = evaluator.load_bootstrap()
        with self.assertRaises(ValueError):
            guard.parse_json(b'{"a":1,"a":2}')

    def test_frozen_source_inventory_includes_both_retained_path_schemas(self):
        guard = evaluator.load_bootstrap()
        commit = evaluator.MATRIX_COMMIT
        inference = guard.parse_json(guard.git("show", commit + ":" + guard.INFERENCE_SOURCE_PATH, binary=True))
        inventory = set(guard.git("ls-files", "-z").split("\0"))
        paths = evaluator.required_paths(guard, inventory, inference, evaluator.packets_at(guard, commit))
        self.assertIn("evidence/linguistic_truth_v1/sources/thinking_cognition.txt", paths)
        self.assertIn("evidence/classical_language/sources/maqayis.txt", paths)
        self.assertIn("docs/EVIDENCE_LIFECYCLE_V1_IMPLEMENTATION_NOTES.md", paths)
        self.assertFalse(set(paths) & evaluator.NATIVE_PATHS)

    def test_empty_population_never_passes(self):
        self.assertFalse(evaluator.acceptance(evaluator.counts([]), True)["passed"])


if __name__ == "__main__":
    unittest.main()
