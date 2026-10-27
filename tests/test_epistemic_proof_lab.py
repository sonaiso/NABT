"""Transport boundaries for the fixed, independently referenced evidence suite."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from tools import proof_lab as lab

PAYLOAD = json.dumps({"schema": lab.REQUEST_SCHEMA, "mode": "epistemic_measurement"})
IDENTITY = {"code_sha": "a" * 40, "native_sha256": "b" * 64,
            "runtime_sha256": "c" * 64, "runner_sha256": "d" * 64,
            "reference_sha256": "e" * 64, "source_registry_sha256": "f" * 64}


def suite():
    return {"schema": "nabt.epistemic-measurement-benchmark.v1",
            "law_id": "nabt.epistemic-measurement.v1",
            "native_sha256": IDENTITY["native_sha256"],
            "runtime_sha256": IDENTITY["runtime_sha256"],
            "reference_sha256": IDENTITY["reference_sha256"],
            "source_registry_sha256": IDENTITY["source_registry_sha256"],
            "hidden_motive_measured": False, "free_arabic_acquisition_measured": False,
            "whole_arabic_complete": False, "world_truth_established": False}


class EpistemicTransport(unittest.TestCase):
    def test_fixed_mode_cannot_inject_gold_sources_or_native_code(self):
        self.assertEqual(lab.validate_payload(PAYLOAD)["mode"], "epistemic_measurement")
        for key in ("gold", "query", "source", "registry", "url", "path", "executable",
                    "native_checked", "certificate", "lexical_profile", "budget"):
            with self.subTest(key=key), self.assertRaises(lab.RequestError):
                lab.validate_payload(json.dumps({**json.loads(PAYLOAD), key: "injected"}))

    def test_prepare_does_not_execute_and_declares_its_limits(self):
        with patch.object(lab, "_epistemic_identity", return_value=IDENTITY), \
             patch("tools.benchmark_epistemic_measurement.run", side_effect=AssertionError("executed")):
            response = lab.run_payload(lab.SMOKE_ID, PAYLOAD, prepare=True)
        self.assertEqual(response["status"], "PREPARED")
        self.assertEqual(response["scope"]["hidden_motive"], "UNMEASURED")
        self.assertEqual(response["scope"]["external_world"], "NOT_VERIFIED")
        self.assertNotIn("epistemic_measurement", response)

    def test_missing_native_does_not_promote_python(self):
        with patch.object(lab, "_epistemic_identity", return_value=IDENTITY | {"native_sha256": None}), \
             patch("tools.benchmark_epistemic_measurement.run", side_effect=AssertionError("executed")):
            response = lab.run_payload(lab.SMOKE_ID, PAYLOAD)
        self.assertEqual(response["status"], "VERIFICATION_UNAVAILABLE")
        self.assertNotIn("epistemic_measurement", response)

    def test_suite_binds_adapter_checker_and_qualified_scope(self):
        with patch.object(lab, "_epistemic_identity", return_value=IDENTITY), \
             patch("tools.benchmark_epistemic_measurement.run", return_value=suite()) as run:
            response = lab.run_payload(lab.SMOKE_ID, PAYLOAD)
        run.assert_called_once_with(require_native=True)
        self.assertEqual(response["status"], "EPISTEMIC_MEASUREMENT_COMPLETE")
        self.assertIs(response["all_arabic_complete"], False)
        self.assertIs(response["world_truth_established"], False)

    def test_authority_or_executable_substitution_rejects_entire_receipt(self):
        for key in ("hidden_motive_measured", "free_arabic_acquisition_measured",
                    "whole_arabic_complete", "world_truth_established", "native_sha256", "runtime_sha256",
                    "reference_sha256", "source_registry_sha256"):
            bad = suite()
            bad[key] = True if type(bad[key]) is bool else "0" * 64
            with self.subTest(key=key), patch.object(lab, "_epistemic_identity", return_value=IDENTITY), \
                 patch("tools.benchmark_epistemic_measurement.run", return_value=bad):
                response = lab.run_payload(lab.SMOKE_ID, PAYLOAD)
            self.assertEqual(response["status"], "EXECUTION_FAILED")
            self.assertNotIn("epistemic_measurement", response)

    def test_changed_execution_identity_rejects_collected_rows(self):
        with patch.object(lab, "_epistemic_identity", side_effect=[IDENTITY, IDENTITY | {"native_sha256": "e" * 64}]), \
             patch("tools.benchmark_epistemic_measurement.run", return_value=suite()):
            response = lab.run_payload(lab.SMOKE_ID, PAYLOAD)
        self.assertEqual(response["status"], "EXECUTION_FAILED")
        self.assertNotIn("epistemic_measurement", response)

    def test_oversized_suite_has_bounded_failure_receipt(self):
        large = deepcopy(suite())
        large["cases"] = ["x" * lab.MAX_RESULT_BYTES]
        with patch.object(lab, "_epistemic_identity", return_value=IDENTITY), \
             patch("tools.benchmark_epistemic_measurement.run", return_value=large):
            response = lab.run_payload(lab.SMOKE_ID, PAYLOAD)
        self.assertEqual(response["status"], "RESOURCE_EXHAUSTED")
        self.assertNotIn("epistemic_measurement", response)


if __name__ == "__main__":
    unittest.main()
