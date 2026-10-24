"""Boundaries of the corrected-runtime continuation; no new predictions."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "evidence/arabic_completion_v3"
SPEC = importlib.util.spec_from_file_location("completion_finalizer_v2", PHASE / "finalize_validation_v2.py")
F = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(F)


class CompletionContinuationFinalizerTests(unittest.TestCase):
    def test_unreviewed_pin_and_numeric_boolean_count_stop_continuation(self):
        F.require_ready()
        for name in ("RUNTIME_SHA256", "RUNTIME_SNAPSHOT_SHA256", "RUNTIME_ARCHIVE_SHA256",
                     "POLICY_SHA256", "COMPLETION_ORACLE_FREEZE_SHA256"):
            with self.subTest(pin=name), patch.object(F, name, "PENDING_REVIEW"):
                with self.assertRaises(ValueError):
                    F.require_ready()
        with patch.object(F, "RUNTIME_FILE_COUNT", True), self.assertRaises(ValueError):
            F.require_ready()

    def test_historical_evidence_is_preserved_and_cannot_be_relabelled(self):
        historical = F.preserved_history()
        self.assertEqual(historical["historical_file_count"], 206)
        self.assertTrue(historical["all_original_bytes_preserved"])
        (ROOT / "artifacts/local").mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / "artifacts/local") as temporary:
            directory = Path(temporary)
            manifest = F.load(PHASE / "continuation_preservation_v1.json")
            manifest["files"][0]["bytes"] += 1
            (directory / "continuation_preservation_v1.json").write_bytes(F.wire(manifest) + b"\n")
            with patch.object(F, "FOLDER", directory), self.assertRaisesRegex(ValueError, "manifest changed"):
                F.preserved_history()

    def test_corrected_policy_cannot_replace_gold_or_case_check_inventory(self):
        policy = F.load(PHASE / "regression_policy_v2.json")
        F.check_original_domain(policy)
        for mutate in (
            lambda p: p["suites"]["construction"].update(total=85),
            lambda p: p["suites"]["construction"].update(gold_freeze_sha256="other-gold"),
            lambda p: p["suites"]["discourse"].update(source_sha256="other-source"),
            lambda p: p["suites"]["discourse"]["cases"].reverse(),
            lambda p: p["suites"]["construction"]["cases"][0]["checks"].pop(),
        ):
            changed = deepcopy(policy)
            mutate(changed)
            with self.assertRaises(ValueError):
                F.check_original_domain(changed)

    def test_actual_new_strict_scores_are_recomputed_and_stay_partial(self):
        policy_path = PHASE / "regression_policy_v2.json"
        self.assertEqual(sha256(policy_path.read_bytes()).hexdigest(), F.POLICY_SHA256)
        policy = F.load(policy_path)
        for name, reference in policy["suites"].items():
            path = ROOT / reference["strict_measurement"]
            self.assertEqual(sha256(path.read_bytes()).hexdigest(), reference["strict_measurement_sha256"])
            result = F.load(path)
            checked = F.check_coverage(name, result, policy, gate=False)
            self.assertEqual(checked["passed"], reference["observed_passed"])
            self.assertEqual(checked["total"], 86)
            self.assertFalse(checked["strict_pass"])
            forged = deepcopy(result)
            forged["passed"], forged["strict_pass"] = 86, True
            with self.assertRaises(ValueError):
                F.check_coverage(name, forged, policy, gate=False)


if __name__ == "__main__":
    unittest.main()
