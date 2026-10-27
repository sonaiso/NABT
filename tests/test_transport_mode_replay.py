"""Fresh seven-mode replay binds each existing domain, without universal proof."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import unittest

from nabt.transport_contract import ENVELOPE_SCHEMA, validate_transport_envelope
from tools import proof_lab as lab
from tools import licensed_workflow as workflow
from tests._transport_native import native_test


def _envelope(report):
    child = deepcopy(report)
    binding = child.pop("transport_contract")
    return {"schema": ENVELOPE_SCHEMA, "response": child, "transport_contract": binding}


class ActualTransportModeReplay(unittest.TestCase):
    @native_test("licensedInference", "lexicalDenotation", "epistemicMeasurement", "contextualReference")
    def test_all_seven_lab_modes_replay_fresh_and_keep_domain_authority(self):
        workflow_request = {"schema": workflow.REQUEST_SCHEMA, "op": "source_inference",
            "input": {"source": "سار زيد أمامك خلف الدار", "query": "هل سار زيد أمامك خلف الدار؟"}}
        examples = [
            (json.loads(lab.SMOKE_PAYLOAD), "SUPPORTED", "result"),
            ({"mode": "benchmark"}, "BENCHMARK_COMPLETE", "benchmark"),
            ({"mode": "testimony", "entry": "بيت", "target": ["المأوى"]}, "CONDITIONAL_INTERPRETATIONS", "testimony"),
            ({"mode": "semantic_axes"}, "SEMANTIC_AXES_COMPLETE", "semantic_axes"),
            ({"mode": "epistemic_measurement"}, "EPISTEMIC_MEASUREMENT_COMPLETE", "epistemic_measurement"),
            ({"mode": "contextual_reference"}, "CONTEXTUAL_REFERENCE_COMPLETE", "contextual_reference"),
            ({"mode": "licensed_workflow", "workflow": workflow_request}, "LICENSED_WORKFLOW_COMPLETE", "gateway_result"),
        ]
        for request, status, child_key in examples:
            with self.subTest(mode=request["mode"]):
                raw = json.dumps({"schema": lab.REQUEST_SCHEMA, **request}, ensure_ascii=False)
                report = lab.run_payload(lab.SMOKE_ID, raw)
                if output := os.environ.get("NABT_TRANSPORT_REPLAY_OUTPUT"):
                    directory = Path(output)
                    directory.mkdir(parents=True, exist_ok=True)
                    (directory / (request["mode"] + ".request.json")).write_text(raw, encoding="utf-8")
                    (directory / (request["mode"] + ".json")).write_text(
                        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
                self.assertEqual(report["status"], status, report.get("error"))
                self.assertIn(child_key, report)
                envelope = _envelope(report)
                checked = validate_transport_envelope(envelope)
                self.assertTrue(checked["integrity_valid"], checked)
                self.assertFalse(checked["proof_authority_established"])
                contract = report["transport_contract"]
                self.assertEqual(contract["request"], {"request_id": lab.SMOKE_ID,
                    "payload_sha256": sha256(raw.encode()).hexdigest()})
                self.assertEqual(contract["input_binding"], "EXACT_PAYLOAD_DIGEST")
                self.assertFalse(contract["transport_binding_kernel_proved"])
                if request["mode"] == "licensed_workflow":
                    self.assertTrue(contract["named_claims"])
                    self.assertTrue(all(c["child_path"].startswith("gateway_result.claims[") for c in contract["named_claims"]))
                    self.assertTrue(report["gateway_result"]["native_checked"])
                else:
                    self.assertEqual(contract["named_claims"], [])
                # Changing a reported result without a new fresh binding fails.
                envelope["response"]["status"] = "UNIVERSAL_COMPLETENESS"
                self.assertFalse(validate_transport_envelope(envelope)["integrity_valid"])

    def test_matrix_has_exact_gateway_operations_and_seven_proof_lab_modes(self):
        path = Path(__file__).parents[1] / "src/nabt/data/transport_command_contracts.json"
        rows = json.loads(path.read_text())["rows"]
        actual = {r["command"] for r in rows if r["entrypoint"] == "tools.licensed_workflow.run_request"}
        self.assertEqual(actual, set(workflow._OPERATIONS))
        for row in rows:
            if row["entrypoint"] == "tools.licensed_workflow.run_request":
                self.assertEqual(set(row["required_input_fields"]), workflow._OPERATIONS[row["command"]]["required"])
                self.assertEqual(set(row["optional_input_fields"]), workflow._OPERATIONS[row["command"]]["optional"])
        modes = {r["command"] for r in rows if r["entrypoint"] == "tools.proof_lab.run_payload"}
        self.assertEqual(modes, {"inference", "benchmark", "testimony", "semantic_axes",
                               "epistemic_measurement", "contextual_reference", "licensed_workflow"})
