"""Regression tests for the gap between freeze validation and execution.

Use actual files, git contents and hashes for provenance. Stub only the matrix
and language computation: these tests establish execution integrity, not Arabic
coverage or a new independent linguistic oracle.
"""
from contextlib import ExitStack
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tools import evaluate_aligned_acquisition as evaluator


class AlignedAcquisitionEvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory())).resolve()
        self.gold = self.root / "gold.json"
        self.source = "tools/aligned_acquisition.py"
        self.native = "formal/.lake/build/bin/alignedAcquisition"
        files = {
            self.source: b"# frozen acquisition fixture\n",
            "tools/evaluate_aligned_acquisition.py": b"# frozen evaluator fixture\n",
            evaluator.SPEC_PATH: b"frozen specification\n",
            evaluator.INFERENCE_SOURCE_PATH: b'{"sources": [], "source_registries": []}\n',
            "evidence/aligned_acquisition_v1/source_evidence.json": b"{}\n",
        }
        native = {self.native: b"frozen acquisition executable\n",
                  "formal/.lake/build/bin/licensedInference": b"frozen inference executable\n"}
        for name, raw in {**files, **native, "gold.json": b"{}\n"}.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        def git(*args):
            return subprocess.run(["git", "-C", str(self.root), *args], check=True,
                                  capture_output=True, text=True).stdout.strip()
        git("init", "-q")
        git("add", *files, "gold.json")
        git("-c", "user.name=Freeze test", "-c", "user.email=freeze@example.invalid",
            "-c", "commit.gpgsign=false", "commit", "-qm", "Freeze test inputs")
        commit = git("rev-parse", "HEAD")
        self.freeze = {"schema": "nabt.aligned-acquisition-code-freeze.v1", "commit": commit,
                       "spec_sha256": evaluator.digest(files[evaluator.SPEC_PATH]),
                       "gold": {"path": "gold.json", "sha256": evaluator.digest(b"{}\n")},
                       "files": {name: evaluator.digest(raw) for name, raw in files.items()},
                       "native": {name: evaluator.digest(raw) for name, raw in native.items()}}
        self.manifest = self.root / "freeze.json"
        self.manifest.write_text(json.dumps(self.freeze), encoding="utf-8")
        self.stack.enter_context(patch.multiple(evaluator, ROOT=self.root, MATRIX_COMMIT=commit,
            GOLD_SHA256=self.freeze["gold"]["sha256"], SPEC_SHA256=self.freeze["spec_sha256"]))
        # run() prepends its runtime paths. Restore the caller's path after each test.
        saved_path = sys.path[:]
        self.stack.callback(lambda: sys.path.__setitem__(slice(None), saved_path))
        self.stack.enter_context(patch.object(evaluator, "load_gold", return_value={"cases": [{}]}))
        self.import_runtime = Mock(return_value=SimpleNamespace(read_acquired=Mock(), evaluate=Mock()))
        self.stack.enter_context(patch.object(evaluator, "importlib",
                                              SimpleNamespace(import_module=self.import_runtime)))
        self.evaluate = self.stack.enter_context(patch.object(evaluator, "evaluate_case", return_value={
            "id": "integrity-fixture", "family": "boundary", "executed": True,
            "expected": {"acquisition_status": "ACQUIRED"},
            "observed": {"status": "ACQUIRED", "verified": True,
                         "source_checks": {"source_identity": True}},
            "verified_acquired": True, "false_license": False,
            "checks": {"status_match": True, "cells_expected": False, "cells_match": None,
                       "reason_expected": False, "reason_match": None, "representation_match": True},
            "goal": {"kind": "acquisition", "positive": True, "outcome": "SUCCESS",
                     "measurement_status": "MEASURED"},
        }))

    def validated(self, phase="first"):
        return evaluator.verify_freeze(self.manifest, phase, self.gold)

    def assert_initial_rejected(self, freeze, evidence, phase="first"):
        with self.assertRaisesRegex(ValueError, "initial snapshot differs from validated freeze"):
            evaluator.run(self.gold, freeze, evidence, phase)
        self.import_runtime.assert_not_called()
        self.evaluate.assert_not_called()

    def test_unchanged_validated_inputs_pass_in_both_phases(self):
        for phase in ("first", "exposed"):
            with self.subTest(phase=phase):
                freeze, evidence = self.validated(phase)
                report = evaluator.run(self.gold, freeze, evidence, phase)
                self.assertTrue(report["execution_evidence"]["integrity_valid"])
                self.assertTrue(report["contract_gate"]["passed"])
                self.assertTrue(report["representation_gate"]["passed"])

    def test_source_replaced_after_validation_is_rejected_before_import(self):
        freeze, evidence = self.validated()
        (self.root / self.source).write_bytes(b"# replacement after validation\n")
        self.assert_initial_rejected(freeze, evidence)

    def test_native_replaced_after_validation_is_rejected_before_import(self):
        freeze, evidence = self.validated()
        (self.root / self.native).write_bytes(b"replacement executable\n")
        self.assert_initial_rejected(freeze, evidence)

    def test_deleted_validated_input_is_rejected_before_import(self):
        freeze, evidence = self.validated()
        (self.root / self.source).unlink()
        self.assert_initial_rejected(freeze, evidence)

    def test_exposed_phase_cannot_license_a_different_native_build(self):
        (self.root / self.native).write_bytes(b"different exposed build\n")
        freeze, evidence = self.validated("exposed")
        self.assertFalse(evidence["native_matches_freeze"])
        self.assert_initial_rejected(freeze, evidence, "exposed")

    def test_gold_changed_after_validation_is_rejected_before_import(self):
        freeze, evidence = self.validated()
        self.gold.write_bytes(b'{"replacement": true}\n')
        self.assert_initial_rejected(freeze, evidence)

    def test_first_run_head_must_still_be_the_validated_commit(self):
        freeze, evidence = self.validated()
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Freeze test",
                        "-c", "user.email=freeze@example.invalid", "-c", "commit.gpgsign=false",
                        "commit", "--allow-empty", "-qm", "New HEAD after validation"],
                       check=True, capture_output=True)
        self.assert_initial_rejected(freeze, evidence)
        # Exposed replay intentionally permits newer commits with identical inputs.
        freeze, evidence = self.validated("exposed")
        self.assertTrue(evaluator.run(self.gold, freeze, evidence, "exposed")["contract_gate"]["passed"])

    def test_source_changed_during_execution_fails_final_gate(self):
        freeze, evidence = self.validated()
        row = self.evaluate.return_value
        def mutate(*args):
            (self.root / self.source).write_bytes(b"# changed during execution\n")
            return row
        self.evaluate.side_effect = mutate
        report = evaluator.run(self.gold, freeze, evidence, "first")
        self.assertEqual(report["execution_evidence"]["changed_files"], [self.source])
        self.assertFalse(report["contract_gate"]["passed"])
        self.assertFalse(report["representation_gate"]["passed"])

    def test_loaded_source_must_still_match_its_frozen_hash(self):
        freeze, evidence = self.validated()
        real_snapshot = evaluator.snapshot
        calls = 0
        def snapshot_then_mutate(*args):
            nonlocal calls
            result = real_snapshot(*args)
            calls += 1
            if calls == 2:
                (self.root / self.source).write_bytes(b"# changed before module hash audit\n")
            return result
        module = SimpleNamespace(__file__=str(self.root / self.source))
        with patch.dict(sys.modules, {"nabt_freeze_fixture": module}), \
                patch.object(evaluator, "snapshot", side_effect=snapshot_then_mutate):
            report = evaluator.run(self.gold, freeze, evidence, "first")
        self.assertEqual(report["execution_evidence"]["before"], report["execution_evidence"]["after"])
        self.assertFalse(report["contract_gate"]["passed"])
        self.assertFalse(report["representation_gate"]["passed"])

    def test_cli_retains_failure_and_never_overwrites_a_result(self):
        output = self.root / "result.json"
        original_verify = evaluator.verify_freeze
        def verify_then_mutate(*args):
            frozen = original_verify(*args)
            (self.root / self.native).write_bytes(b"swapped after verify\n")
            return frozen
        args = ["evaluate", "--output", str(output), "--gold", str(self.gold),
                "--phase", "first", "--code-freeze", str(self.manifest)]
        with patch.object(sys, "argv", args), patch.object(evaluator, "verify_freeze", side_effect=verify_then_mutate), \
                patch("builtins.print"):
            self.assertEqual(evaluator.main(), 2)
        result = json.loads(output.read_text())
        self.assertEqual(result["status"], "EVALUATOR_FAILURE")
        self.assertIn("initial snapshot differs from validated freeze", result["error"]["message"])
        original = output.read_bytes()
        (self.root / self.native).write_bytes(b"frozen acquisition executable\n")
        with patch.object(sys, "argv", args), self.assertRaises(FileExistsError):
            evaluator.main()
        self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
