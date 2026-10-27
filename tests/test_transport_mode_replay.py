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

    @native_test("sixNounAcquisition")
    def test_six_noun_gateway_and_lab_replay_checked_and_deferred_constructions(self):
        # Independent examples exercise the admitted family and two distinct
        # missing/contradicted premises; deferral is never rejection of Arabic.
        cases = [
            ("checked", "جَاءَ أَبُو زَيْدٍ", "CHECKED_SIX_NOUN", None),
            ("unknown_companionship", "جَاءَ ذُو زَيْدٍ", "DEFER", "DHU_COMPANIONSHIP_NOT_ACQUIRED"),
            ("case_mismatch", "جَاءَ أَبِي زَيْدٍ", "DEFER", "COMMON_LETTER_CASE_MISMATCH"),
        ]
        for label, text, status, reason in cases:
            with self.subTest(case=label):
                incoming = {"schema": workflow.REQUEST_SCHEMA, "op": "six_noun_acquisition",
                    "input": {"text": text, "source_id": "independent-transport-replay",
                              "context": "المقام محفوظ؛ المراد والواقع غير مثبتين"}}
                raw = json.dumps({"schema": lab.REQUEST_SCHEMA, "mode": "licensed_workflow",
                                  "workflow": incoming}, ensure_ascii=False)
                report = lab.run_payload(lab.SMOKE_ID, raw)
                if output := os.environ.get("NABT_TRANSPORT_REPLAY_OUTPUT"):
                    directory = Path(output)
                    directory.mkdir(parents=True, exist_ok=True)
                    (directory / ("six_noun_" + label + ".request.json")).write_text(raw, encoding="utf-8")
                    (directory / ("six_noun_" + label + ".json")).write_text(
                        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
                self.assertEqual(report["status"], "LICENSED_WORKFLOW_COMPLETE", report.get("error"))
                gateway = report["gateway_result"]
                self.assertEqual(gateway["status"], status, gateway)
                self.assertTrue(gateway["native_checked"])
                child = gateway["result"]
                self.assertEqual(child["source"]["text"], text)
                self.assertEqual(child["source"]["revision"], sha256(text.encode()).hexdigest())
                self.assertEqual(child["context"], incoming["input"]["context"])
                self.assertEqual(child["grammar_certified"], status == "CHECKED_SIX_NOUN")
                self.assertFalse(child["source_projection_complete"])
                self.assertFalse(child["foundation_complete"])
                self.assertTrue(child["orthographic_bridge"]["canonical_projection_complete"])
                for key in ("strict_language_accepted", "intended_sense_established", "world_truth_established",
                            "tawatur_established", "whole_arabic_complete", "linguistic_rejection"):
                    self.assertFalse(child[key], key)
                claims = gateway["claims"]
                self.assertEqual(len(claims), 1 if status == "CHECKED_SIX_NOUN" else 0)
                if claims:
                    self.assertEqual(claims[0]["kind"], "SOURCE_BOUND_SIX_NOUN_CONSTRUCTION")
                    self.assertEqual(claims[0]["proof"]["law_id"], "nabt.six-noun-acquisition.v1")
                    self.assertEqual(claims[0]["source"], child["source"])
                else:
                    self.assertEqual(child["reason"], reason)
                    self.assertIn(reason, child["residuals"])
                for value in (gateway, report):
                    checked = validate_transport_envelope(_envelope(value))
                    self.assertTrue(checked["integrity_valid"], checked)
                    self.assertFalse(checked["proof_authority_established"])
                    self.assertEqual(len(value["transport_contract"]["named_claims"]), len(claims))
                self.assertEqual(gateway["transport_contract"]["request"], incoming)
                changed = _envelope(report)
                changed["response"]["gateway_result"]["result"]["context"] = "مقام آخر"
                self.assertFalse(validate_transport_envelope(changed)["integrity_valid"])

    def test_matrix_has_exact_gateway_operations_and_seven_proof_lab_modes(self):
        path = Path(__file__).parents[1] / "src/nabt/data/transport_command_contracts.json"
        rows = json.loads(path.read_text())["rows"]
        actual = {r["command"] for r in rows if r["entrypoint"] == "tools.licensed_workflow.run_request"}
        self.assertEqual(actual, set(workflow._OPERATIONS))
        for row in rows:
            if row["entrypoint"] == "tools.licensed_workflow.run_request":
                self.assertEqual(set(row["required_input_fields"]), workflow._OPERATIONS[row["command"]]["required"])
                self.assertEqual(set(row["optional_input_fields"]), workflow._OPERATIONS[row["command"]]["optional"])
        six_noun = next(r for r in rows if r["entrypoint"] == "tools.licensed_workflow.run_request"
                        and r["command"] == "six_noun_acquisition")
        self.assertEqual(six_noun["named_claim_kinds"], ["SOURCE_BOUND_SIX_NOUN_CONSTRUCTION"])
        self.assertEqual(six_noun["authority"], workflow._OPERATIONS["six_noun_acquisition"]["authority"])
        lab_workflow = next(r for r in rows if r["entrypoint"] == "tools.proof_lab.run_payload"
                           and r["command"] == "licensed_workflow")
        self.assertIn("SOURCE_BOUND_SIX_NOUN_CONSTRUCTION", lab_workflow["named_claim_kinds"])
        modes = {r["command"] for r in rows if r["entrypoint"] == "tools.proof_lab.run_payload"}
        self.assertEqual(modes, {"inference", "benchmark", "testimony", "semantic_axes",
                               "epistemic_measurement", "contextual_reference", "licensed_workflow"})
