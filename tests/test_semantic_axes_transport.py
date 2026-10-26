"""The live benchmark is a fixed, separately labelled Python measurement."""
import json
import unittest
from unittest.mock import patch

from tools import proof_lab


class SemanticAxesTransport(unittest.TestCase):
    REQUEST = json.dumps({"schema": proof_lab.REQUEST_SCHEMA, "mode": "semantic_axes"})
    ID = "f2702111-d080-4c99-8c4c-ef43f10a3def"
    IDENTITY = {"code_sha": "a" * 40, "native_sha256": None,
                "runtime_sha256": "b" * 64, "reference_sha256": "c" * 64}

    def test_fixed_reference_only(self):
        self.assertEqual(proof_lab.validate_payload(self.REQUEST)["mode"], "semantic_axes")
        for field in ("reference", "gold", "expected", "code", "budget", "cases"):
            with self.subTest(field=field), self.assertRaises(proof_lab.RequestError):
                proof_lab.validate_payload(json.dumps({**json.loads(self.REQUEST), field: {}}))

    def test_prepare_does_not_claim_or_require_lean_execution(self):
        with patch.object(proof_lab, "_semantic_axes_identity", return_value=self.IDENTITY):
            result = proof_lab.run_payload(self.ID, self.REQUEST, prepare=True)
        self.assertEqual(result["status"], "PREPARED")
        self.assertIsNone(result["native_sha256"])
        self.assertEqual(result["scope"]["verification_kind"], "PYTHON_REPLAY")
        self.assertNotIn("semantic_axes", result)

    def test_live_route_executes_fixed_suite_without_unused_native_gate(self):
        suite = {"schema": "nabt.semantic-axes-benchmark.v1", "lean_native_checked": False}
        with patch.object(proof_lab, "_semantic_axes_identity", return_value=self.IDENTITY), \
                patch("tools.benchmark_semantic_axes.run", return_value=suite) as run:
            result = proof_lab.run_payload(self.ID, self.REQUEST)
        run.assert_called_once_with()
        self.assertEqual(result["status"], "SEMANTIC_AXES_COMPLETE")
        self.assertEqual(result["semantic_axes"], suite)
        self.assertIs(result["all_arabic_complete"], False)
        self.assertIsNone(result["native_sha256"])

    def test_execution_identity_drift_clears_prior_success(self):
        with patch.object(proof_lab, "_semantic_axes_identity", side_effect=[self.IDENTITY, {**self.IDENTITY, "reference_sha256": "d" * 64}]), \
                patch("tools.benchmark_semantic_axes.run", return_value={"marker": "STALE"}):
            result = proof_lab.run_payload(self.ID, self.REQUEST)
        self.assertEqual(result["status"], "EXECUTION_FAILED")
        self.assertNotIn("semantic_axes", result)

    def test_failure_is_a_bound_receipt_without_success_payload_or_private_error(self):
        with patch.object(proof_lab, "_semantic_axes_identity", return_value=self.IDENTITY), \
                patch("tools.benchmark_semantic_axes.run", side_effect=ValueError("private-input")):
            result = proof_lab.run_payload(self.ID, self.REQUEST)
        self.assertEqual(result["status"], "EXECUTION_FAILED")
        self.assertEqual(result["request_id"], self.ID)
        self.assertNotIn("semantic_axes", result)
        self.assertNotIn("private-input", json.dumps(result))

    def test_resource_failure_removes_large_result(self):
        with patch.object(proof_lab, "_semantic_axes_identity", return_value=self.IDENTITY), \
                patch("tools.benchmark_semantic_axes.run", return_value={"large": "x" * proof_lab.MAX_RESULT_BYTES}):
            result = proof_lab.run_payload(self.ID, self.REQUEST)
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
        self.assertNotIn("semantic_axes", result)


if __name__ == "__main__":
    unittest.main()
