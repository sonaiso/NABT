"""Failure/resource transport receipts carry integrity, never blanket proof.

Limits are scaled down in allocation tests: the ordering of the independent
request, response and canonical-binding ceilings is the production ordering.
No reference corpus or expected linguistic answer is changed by these tests.
"""
from copy import deepcopy
from hashlib import sha256
import json
import unittest
from unittest.mock import patch

from nabt import transport_contract as transport
from tools import licensed_workflow as workflow
from tools import proof_lab as lab
from tests._transport_native import native_test


def _identity(native=True):
    return {"code_sha": "a" * 40, "native_sha256": "b" * 64 if native else None,
            "runner_sha256": "c" * 64, "runtime_sha256": "d" * 64,
            "toolchain": "bounded-transport-test"}


def _unverified(**extra):
    return {**{key: False for key in lab.BOOLEAN_FLAGS},
            "status": "UNKNOWN", "authority": "UNVERIFIED_PROPOSAL",
            "schema": "nabt.licensed-inference-result.v1", "law_id": lab.SCOPE["law_id"],
            "accepted_language": lab.SCOPE["accepted_language"], **extra}


def _detached(report):
    response = deepcopy(report)
    binding = response.pop("transport_contract")
    return {"schema": transport.ENVELOPE_SCHEMA, "transport_contract": binding,
            "response": response}


class BindingAssertions:
    def assert_unprivileged_binding(self, result):
        binding = result["transport_contract"]
        self.assertEqual(binding["named_claims"], [])
        self.assertFalse(binding["transport_binding_kernel_proved"])
        self.assertFalse(binding["grants_language_license"])
        checked = transport.validate_transport_envelope(_detached(result))
        self.assertTrue(checked["integrity_valid"], checked)
        self.assertFalse(checked["proof_authority_established"])


class LiveFailureBindings(BindingAssertions, unittest.TestCase):
    def test_missing_native_receipts_need_no_benchmark_payload(self):
        examples = [
            (json.loads(lab.SMOKE_PAYLOAD), "_identity"),
            ({"mode": "benchmark"}, "_identity"),
            ({"mode": "testimony", "entry": "بيت", "target": ["المأوى"]}, "_testimony_identity"),
            ({"mode": "epistemic_measurement"}, "_epistemic_identity"),
            ({"mode": "contextual_reference"}, "_contextual_identity"),
        ]
        for request, identity in examples:
            with self.subTest(mode=request["mode"]):
                raw = json.dumps({"schema": lab.REQUEST_SCHEMA, **request}, ensure_ascii=False)
                with patch.object(lab, identity, return_value=_identity(False)), \
                     patch.object(lab, "_benchmark") as benchmark, \
                     patch.object(lab, "evaluate") as evaluate:
                    result = lab.run_payload(lab.SMOKE_ID, raw)
                self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
                self.assertEqual(result["error"], "NATIVE_CHECKER_MISSING")
                self.assertNotIn("benchmark", result)
                self.assertNotIn("result", result)
                benchmark.assert_not_called()
                evaluate.assert_not_called()
                self.assertEqual(result["payload_sha256"], sha256(raw.encode()).hexdigest())
                self.assert_unprivileged_binding(result)

    def test_python_benchmark_failure_retains_failure_without_fake_suite(self):
        raw = json.dumps({"schema": lab.REQUEST_SCHEMA, "mode": "semantic_axes"})
        with patch.object(lab, "_semantic_axes_identity", return_value=_identity(False)), \
             patch("tools.benchmark_semantic_axes.run", side_effect=RuntimeError("PRIVATE_FAILURE_DETAIL")):
            result = lab.run_payload(lab.SMOKE_ID, raw)
        self.assertEqual(result["status"], "EXECUTION_FAILED")
        self.assertNotIn("semantic_axes", result)
        self.assertNotIn("PRIVATE_FAILURE_DETAIL", json.dumps(result))
        self.assert_unprivileged_binding(result)

    def test_gateway_child_failure_binds_failure_without_benchmark(self):
        request = {"schema": workflow.REQUEST_SCHEMA, "op": "source_inference",
                   "input": {"source": "سار زيد", "query": "هل سار زيد؟"}}
        child = {"schema": workflow.RESPONSE_SCHEMA, "operation": "source_inference",
                 "status": "RESOURCE_EXHAUSTED", "native_checked": False, "claims": []}
        raw = json.dumps({"schema": lab.REQUEST_SCHEMA, "mode": "licensed_workflow", "workflow": request})
        with patch.object(lab, "_workflow_identity", return_value=_identity(False)), \
             patch.object(workflow, "run_request", return_value=child), \
             patch.object(workflow, "migration_inventory", return_value={"surface_count": 0}):
            result = lab.run_payload(lab.SMOKE_ID, raw)
        self.assertEqual(result["status"], "LICENSED_WORKFLOW_COMPLETE")
        self.assertEqual(result["gateway_result"]["status"], "RESOURCE_EXHAUSTED")
        self.assertNotIn("benchmark", result)
        self.assertIsNone(result["adapter_result_json"])
        self.assert_unprivileged_binding(result)

    def test_malformed_wire_failure_still_binds_exact_received_bytes(self):
        for raw in (b"\xff", b'{"schema":', b"[]", b"  null\n"):
            with self.subTest(raw=raw):
                result = lab.run_payload(lab.SMOKE_ID, raw)
                self.assertEqual(result["status"], "INVALID_INPUT")
                self.assertEqual(result["payload_sha256"], sha256(raw).hexdigest())
                self.assert_unprivileged_binding(result)

    def test_unrepresentable_workflow_request_has_no_exact_input_claim(self):
        request = {"schema": workflow.REQUEST_SCHEMA, "op": "classical_control", "input": {}}
        request["input"]["frame"] = request
        result = workflow.run_request(request)
        self.assertEqual(result["status"], "INVALID_INPUT")
        self.assertEqual(result["claims"], [])
        self.assertEqual(result["transport_contract"]["input_binding"], "UNBOUND_INVALID_INPUT")
        self.assert_unprivileged_binding(result)


class LiveResourceBindings(BindingAssertions, unittest.TestCase):
    @native_test("discourseBoundaryCue", "linguisticTruth", "qualifiedCueLicensing")
    def test_small_bounded_discourse_survives_actual_live_transport_copy_budget(self):
        # This is an actual installed native execution: a short user request
        # must not be rejected solely by repeated transport serialization.
        request = {"schema": workflow.REQUEST_SCHEMA, "op": "discourse_boundary",
                   "input": {"text": "لم أشاهد البحر؛ وأقصد بالأسد الحيوان المفترس.",
                             "profile_id": None}}
        raw = json.dumps({"schema": lab.REQUEST_SCHEMA, "mode": "licensed_workflow",
                          "workflow": request}, ensure_ascii=False)
        result = lab.run_payload(lab.SMOKE_ID, raw)
        self.assertEqual(result["status"], "LICENSED_WORKFLOW_COMPLETE", result.get("error"))
        gateway = result["gateway_result"]
        self.assertEqual(gateway["status"], "CHECKED_DISCOURSE_BOUNDARY")
        self.assertTrue(gateway["native_checked"])
        self.assertEqual({claim["kind"] for claim in gateway["claims"]},
                         {"EXACT_DISCOURSE_BOUNDARY_AND_CUE_SLICE"})
        self.assertFalse(gateway["strict_language_accepted"])
        self.assertLess(len(json.dumps(result, ensure_ascii=False).encode()), lab.MAX_RESULT_BYTES)
        checked = transport.validate_transport_envelope(_detached(result))
        self.assertTrue(checked["integrity_valid"], checked)
        self.assertFalse(checked["proof_authority_established"])

    def test_workflow_oversize_binds_digest_without_recursively_copying_request(self):
        request = {"schema": workflow.REQUEST_SCHEMA, "op": "lexical_surface",
                   "input": {"text": "x" * 16384}}
        raw = workflow._wire(request)
        with patch.object(workflow, "MAX_REQUEST_BYTES", 8192), \
             patch.object(transport, "_MAX_BYTES", 12288), \
             patch.object(workflow, "_execute") as execute:
            result = workflow.run_request(request)
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
        self.assertEqual(result["claims"], [])
        execute.assert_not_called()
        binding = result["transport_contract"]
        self.assertEqual(binding["input_binding"], "EXACT_WORKFLOW_REQUEST_DIGEST")
        self.assertEqual(binding["request"], {"sha256": sha256(raw).hexdigest(), "bytes": len(raw)})
        self.assertEqual(result["request_sha256"], sha256(raw).hexdigest())
        self.assertNotIn(request["input"]["text"], json.dumps(result))
        self.assert_unprivileged_binding(result)

    def test_child_exceeding_canonical_budget_is_a_small_resource_receipt(self):
        with patch.object(lab, "MAX_RESULT_BYTES", 8192), \
             patch.object(transport, "_MAX_BYTES", 12288), \
             patch.object(lab, "_identity", return_value=_identity()), \
             patch.object(lab, "evaluate", return_value=_unverified(padding="x" * 16384)):
            result = lab.run_payload(lab.SMOKE_ID, lab.SMOKE_PAYLOAD)
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
        self.assertEqual(result["error"], "RESULT_BYTE_LIMIT")
        self.assertNotIn("result", result)
        self.assertLess(len(json.dumps(result).encode()), 8192)
        self.assert_unprivileged_binding(result)

    def test_binding_expansion_cannot_escape_response_budget(self):
        # The base child fits 8 KiB; the canonical copy carried by the binding
        # does not. Both stages must be measured before transport encryption.
        with patch.object(lab, "MAX_RESULT_BYTES", 8192), \
             patch.object(lab, "_identity", return_value=_identity()), \
             patch.object(lab, "evaluate", return_value=_unverified(padding="x" * 4800)):
            result = lab.run_payload(lab.SMOKE_ID, lab.SMOKE_PAYLOAD)
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
        self.assertNotIn("result", result)
        self.assertLess(len(json.dumps(result).encode()), 8192)
        self.assert_unprivileged_binding(result)

    def test_noncanonical_child_output_fails_closed_without_echoing_private_data(self):
        for value in (float("nan"), float("inf"), "\ud800"):
            with self.subTest(value=repr(value)), \
                 patch.object(lab, "_identity", return_value=_identity()), \
                 patch.object(lab, "evaluate", return_value=_unverified(
                     diagnostic_value=value, private="PRIVATE_CHILD_DETAIL")):
                result = lab.run_payload(lab.SMOKE_ID, lab.SMOKE_PAYLOAD)
                self.assertEqual(result["status"], "EXECUTION_FAILED")
                self.assertNotIn("result", result)
                self.assertNotIn("PRIVATE_CHILD_DETAIL", json.dumps(result))
                self.assert_unprivileged_binding(result)


if __name__ == "__main__":
    unittest.main()
