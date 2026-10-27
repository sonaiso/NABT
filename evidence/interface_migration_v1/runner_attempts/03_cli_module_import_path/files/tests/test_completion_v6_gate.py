"""New runtime pin must keep all existing completeness/safety gate obligations."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

from tools import arabic_completion_v5_gate as old
from tools import arabic_completion_v6_gate as current

ROOT = Path(__file__).resolve().parents[1]

# Include the independent continuation's semantic tamper controls in the
# standard suite as well as its standalone, pre-execution test run.
_REVIEW_TEST = ROOT / 'evidence/interface_migration_v1/independent_oracle/test_continuation_v3.py'
_REVIEW_SPEC = importlib.util.spec_from_file_location('completion_v6_review2_tests', _REVIEW_TEST)
_REVIEW_MODULE = importlib.util.module_from_spec(_REVIEW_SPEC)
_REVIEW_SPEC.loader.exec_module(_REVIEW_MODULE)
ContinuationReview2Tests = _REVIEW_MODULE.ContinuationReview2Tests


def fixture(suite):
    return json.loads((ROOT / old.load_policy()["suites"][suite]["strict_measurement"]).read_bytes())


class ClassicalExtensionGateTests(unittest.TestCase):
    def test_new_pin_does_not_authorize_old_runtime_or_fabricated_denominator(self):
        # A real prior fixture remains tied to its prior runtime.
        for suite in ("construction", "discourse"):
            result = fixture(suite)
            self.assertFalse(current.gate_decision(suite, result, True)["gate_pass"])

    def test_only_runtime_identity_changes_in_preserved_residual_policy(self):
        before, after = old.load_policy(), current.load_policy()
        self.assertEqual(before["suites"], after["suites"])
        self.assertEqual(after["runtime_file_count"], 99)
        self.assertNotEqual(before["runtime_freeze_sha256"], after["runtime_freeze_sha256"])

    def test_runtime_pin_cannot_waive_false_acceptance_or_missing_cases(self):
        policy = current.load_policy()
        for suite in ("construction", "discourse"):
            result = fixture(suite)
            # Synthetic gate fixture only; production callers separately verify runtime bytes.
            result["snapshot"].update({k: policy[k] for k in (
                "runtime_freeze_sha256", "runtime_snapshot_sha256", "runtime_file_count")})
            self.assertTrue(current.gate_decision(suite, result, True)["gate_pass"])
            for kind in ("false_accept", "missing_case", "false_total"):
                changed = deepcopy(result)
                if kind == "false_accept":
                    changed["cases"][0]["false_accepts"] = ["invented authority"]
                elif kind == "missing_case":
                    changed["cases"].pop()
                else:
                    changed["passed"] += 1
                self.assertFalse(current.gate_decision(suite, changed, True)["gate_pass"])


if __name__ == "__main__":
    unittest.main()
