"""Evaluator boundaries using synthetic data, never the independent gold."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import evaluate_sourced_acquisition_v3 as evaluator


class FrozenEvaluatorBoundaries(unittest.TestCase):
    def test_projections_preserve_json_scalar_types(self):
        report = {"count": True, "flag": 1, "a/b": [{"~x": "value"}]}
        self.assertEqual(evaluator.matches(report, {"/count": 1, "/flag": True}),
                         {"/count": False, "/flag": False})
        self.assertEqual(evaluator.pointer(report, "/a~1b/0/~0x"), "value")
        for path in ("/a~1b/-1", "/a~1b/00", "/a~1b/١", "/absent", "/count/item"):
            self.assertFalse(evaluator.matches(report, {path: None})[path])

    def test_initial_source_and_native_hashes_are_bound_to_validated_freeze(self):
        freeze = {"files": {"tools/example.py": "source-pin"},
                  "native": {"formal/.lake/build/bin/example": "native-pin"}, "commit": "head"}
        good = {"files": {**freeze["files"], **freeze["native"]},
                "gold_sha256": evaluator.GOLD_SHA256, "head": "head"}
        for target in ("tools/example.py", "formal/.lake/build/bin/example"):
            changed = {**good, "files": {**good["files"], target: "stable-but-not-frozen"}}
            guard = SimpleNamespace(snapshot=lambda *_: changed)
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, "initial snapshot"):
                evaluator.initial_snapshot(guard, freeze, "exposed")
        guard = SimpleNamespace(snapshot=lambda *_: good)
        self.assertEqual(evaluator.initial_snapshot(guard, freeze, "first"), good)

    def test_matrix_and_first_head_are_checked_before_execution(self):
        freeze = {"files": {"a": "pin"}, "native": {}, "commit": "expected"}
        for mutation in ({"gold_sha256": "other"}, {"head": "other"}):
            snapshot = {"files": {"a": "pin"}, "gold_sha256": evaluator.GOLD_SHA256,
                        "head": "expected", **mutation}
            with self.assertRaises(ValueError):
                evaluator.initial_snapshot(SimpleNamespace(snapshot=lambda *_: snapshot), freeze, "first")

    def test_required_inventory_includes_new_source_dependencies_and_current_links(self):
        seen = []
        guard = SimpleNamespace(required_freeze_paths=lambda *_: {"tools/base.py"},
                                local_path=lambda path: seen.append(path))
        packets = [{"sources": [{"repository_path": "evidence/retained/source.txt"}],
                    "upstream_dependencies": [{"path": "evidence/upstream.json"}]},
                   {"sources": [{"path": "evidence/lexicon/source.txt"}]}]
        paths = evaluator.required_paths(guard, {"evidence/linguistic_truth_v1/inventory.json"}, {}, packets)
        for name in ("evidence/retained/source.txt", "evidence/lexicon/source.txt",
                     "evidence/upstream.json", "evidence/operator_traceability_v1/registry.json",
                     "evidence/linguistic_truth_v1/inventory.json",
                     "integrations/current_proof_references.mk"):
            self.assertIn(name, paths)
        self.assertTrue(evaluator.REFERENCES <= paths)
        self.assertFalse(evaluator.NATIVE_PATHS & paths)
        self.assertEqual(len(seen), 3)

    def test_failed_first_preflight_is_preserved_and_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "first.json"
            argv = ["--phase", "first", "--code-freeze", str(Path(directory) / "absent.json"),
                    "--output", str(target)]
            with patch.object(evaluator, "verify_freeze", side_effect=ValueError("synthetic rejected freeze")), \
                    patch.object(evaluator, "run") as run, redirect_stdout(StringIO()):
                self.assertEqual(evaluator.main(argv), 2)
                run.assert_not_called()
                document = json.loads(target.read_text())
                self.assertEqual(document["status"], "EVALUATOR_FAILURE")
                self.assertEqual(document["failure_stage"], "preflight")
                self.assertEqual(document["phase"], "first")
                original = target.read_bytes()
                with self.assertRaises(FileExistsError):
                    evaluator.main(argv)
                self.assertEqual(target.read_bytes(), original)


class GoalAccounting(unittest.TestCase):
    """Separate structural safety, correctness, and narrower legitimate goals."""

    def evaluate(self, entry, report, expected, success):
        case = {"id": "synthetic-accounting", "family": "synthetic", "entry_point": entry,
                "text": "source", "ending": "wasl", "onset": "word_initial",
                "expected": expected, "goal": {"kind": "synthetic", "positive": True,
                                                "success": success}}
        # Native/structural checks can pass while an independent literal or
        # semantic expectation fails. This test targets the accounting boundary.
        checks = SimpleNamespace(audit_report=lambda *args, **kwargs: {
            "source_safe": True, "chain_safe": True, "claim_safe": True,
            "source_checks": [], "realization_checks": [], "binding_checks": {}})
        with patch.object(evaluator, "dispatch", return_value=report):
            return evaluator.evaluate_case(case, {"checks": checks})

    def test_false_authorized_cells_do_not_earn_status_only_positive_goal(self):
        report = {"status": "ACQUIRED", "verified": True, "shape_verified": True,
                  "acquisition": {"words": [{"cells": [4, 9]}]}}
        row = self.evaluate("connected", report,
            {"/status": "ACQUIRED", "/acquisition/words/0/cells": [4, 8]},
            {"/status": "ACQUIRED"})
        self.assertTrue(all(row[key] for key in ("source_safe", "chain_safe", "claim_safe")))
        self.assertTrue(row["goal_projection_matches"])
        self.assertTrue(row["false_authorization"])
        self.assertFalse(row["goal_acquired"])
        summary = evaluator.counts([row])
        self.assertEqual(summary["required_positive"], 1)
        self.assertEqual(summary["positive_acquired"], 0)
        self.assertEqual(summary["positive_misses"], ["synthetic-accounting"])
        self.assertEqual(summary["false_authorizations"], 1)

    def test_false_authorized_chain_is_claimed_but_not_credited(self):
        report = {"status": "LICENSED_PERSON", "verified": True, "chain_complete": True,
                  "person": {"person": 2}, "nominal": None}
        rejected = self.evaluate("person_nominal", report,
            {"/chain_complete": True, "/person/person": 1}, {"/chain_complete": True})
        self.assertTrue(rejected["goal_projection_matches"])
        self.assertTrue(rejected["false_authorization"])
        self.assertTrue(rejected["chain_claimed"])
        self.assertFalse(rejected["goal_acquired"])
        self.assertFalse(rejected["chain_complete"])
        accepted = self.evaluate("person_nominal", report,
            {"/chain_complete": True, "/person/person": 2}, {"/chain_complete": True})
        self.assertFalse(accepted["false_authorization"])
        self.assertTrue(accepted["goal_acquired"])
        self.assertTrue(accepted["chain_complete"])
        summary = evaluator.counts([rejected, accepted])
        self.assertEqual(summary["positive_acquired"], 1)
        self.assertEqual(summary["complete_chains"], 1)

    def test_correct_natural_lower_stage_keeps_its_separate_goal_credit(self):
        report = {"status": "COMPLETE", "selected_sense_ids": ["synthetic_sense"],
                  "semantic_scope_complete": True, "chain_complete": False,
                  "assertion_polarity": "positive", "author_intention_established": False,
                  "world_truth_established": False}
        expected = {"/status": "COMPLETE", "/selected_sense_ids": ["synthetic_sense"],
                    "/semantic_scope_complete": True, "/chain_complete": True,
                    "/assertion_polarity": "positive", "/author_intention_established": False,
                    "/world_truth_established": False}
        lower = self.evaluate("natural", report, expected,
            {"/selected_sense_ids": ["synthetic_sense"], "/semantic_scope_complete": True})
        self.assertFalse(lower["contract_match"])
        self.assertFalse(lower["false_authorization"])
        self.assertTrue(lower["goal_acquired"])
        self.assertFalse(lower["chain_complete"])
        whole = self.evaluate("natural", report, expected, {"/chain_complete": True})
        self.assertFalse(whole["false_authorization"])
        self.assertFalse(whole["goal_acquired"])
        self.assertFalse(whole["chain_complete"])
        summary = evaluator.counts([lower, whole])
        self.assertEqual(summary["required_positive"], 2)
        self.assertEqual(summary["positive_acquired"], 1)
        self.assertEqual(summary["complete_chains"], 0)

    def test_correct_complete_unknown_inference_chain_keeps_credit(self):
        row = self.evaluate("conditional_pr34", {
            "status": "UNKNOWN", "verified": True, "chain_complete": True,
            "answer": {"status": "UNKNOWN"}},
            {"/status": "UNKNOWN", "/chain_complete": True}, {"/chain_complete": True})
        self.assertFalse(row["false_authorization"])
        self.assertTrue(row["goal_acquired"])
        self.assertTrue(row["chain_complete"])


if __name__ == "__main__":
    unittest.main()
