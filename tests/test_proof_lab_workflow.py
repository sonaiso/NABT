"""Live adapter transport, independent of Lean authority testing itself."""
import hashlib
import json
import unittest
from unittest.mock import patch
from tools import proof_lab as lab

ID = "11111111-1111-4111-8111-111111111111"
WORKFLOW = {"schema": "nabt.licensed-workflow-request.v1", "op": "lexical_surface", "input": {"text": "عَيْنَ", "context": "مقام جديد"}}

def request(workflow=None):
    return json.dumps({"schema": lab.REQUEST_SCHEMA, "mode": "licensed_workflow", "workflow": WORKFLOW if workflow is None else workflow}, ensure_ascii=False)

def identity():
    return {"code_sha": "a" * 40, "native_sha256": None, "runner_sha256": "b" * 64,
            "runtime_sha256": "c" * 64, "registry_sha256": "d" * 64,
            "native_binaries_sha256": {"lexicalSurface": None}, "toolchain": "test-fixture"}

class WorkflowTransportTests(unittest.TestCase):
    def test_raw_request_preserved(self):
        self.assertEqual(lab.validate_payload(request())["workflow"], WORKFLOW)

    def test_six_noun_admission_preserves_raw_text_and_declared_context(self):
        value = {"schema": WORKFLOW["schema"], "op": "six_noun_acquisition",
                 "input": {"text": "جَاءَ أَبُو زَيْدٍ", "source_id": "independent-case", "context": "مقام جديد"}}
        self.assertEqual(lab.validate_payload(request(value))["workflow"], value)
        for field in ("grammar_certified", "native_checked", "proof", "reading", "profile_id", "rule_id"):
            with self.subTest(field=field), self.assertRaises(lab.RequestError):
                lab.validate_payload(request(value | {"input": value["input"] | {field: True}}))
        with self.assertRaises(lab.RequestError):
            lab.validate_payload(request(value | {"input": {"context": "مقام جديد"}}))

    def test_admission_rejects_authority_and_arbitrary_operations(self):
        for field in ("proof", "checker", "verified", "native_checked", "manifest"):
            with self.subTest(field=field), self.assertRaises(lab.RequestError):
                lab.validate_payload(request(WORKFLOW | {"input": WORKFLOW["input"] | {field: True}}))
        for op in ([], "exec", "evaluate_diagnostic_candidates"):
            with self.subTest(op=op), self.assertRaises(lab.RequestError):
                lab.validate_payload(request(WORKFLOW | {"op": op}))

    def test_portable_integers_and_unicode_are_not_lossily_coerced(self):
        for n in (1.1, 2**53, -(2**53)):
            with self.subTest(n=n), self.assertRaises(lab.RequestError):
                lab.validate_payload(request(WORKFLOW | {"input": WORKFLOW["input"] | {"start_byte": n}}))
        with self.assertRaises((lab.RequestError, UnicodeError)):
            lab.validate_payload(json.dumps({"schema": lab.REQUEST_SCHEMA, "mode": "licensed_workflow", "workflow": WORKFLOW | {"input": {"text": "\ud800"}}}))

    def test_missing_native_can_return_an_explicit_gateway_failure_without_claims(self):
        gateway={"schema":"nabt.licensed-workflow-response.v1", "status":"VERIFICATION_UNAVAILABLE", "operation":"lexical_surface", "native_checked":False, "claims":[]}
        with patch.object(lab, "_workflow_identity", side_effect=identity), patch("tools.licensed_workflow.run_request", return_value=gateway) as run, patch("tools.licensed_workflow.migration_inventory", return_value={"surface_count":0}):
            result=lab.run_payload(ID,request())
        run.assert_called_once_with(WORKFLOW)
        self.assertEqual(result["status"],"LICENSED_WORKFLOW_COMPLETE")
        self.assertFalse(result["gateway_result"]["native_checked"])
        self.assertEqual(result["gateway_result"]["claims"],[])
        self.assertEqual(result["gateway_result_sha256"],hashlib.sha256(result["gateway_result_json"].encode()).hexdigest())

    def test_changed_identity_removes_entire_gateway_payload(self):
        with patch.object(lab, "_workflow_identity", side_effect=[identity(),identity() | {"runtime_sha256":"e"*64}]), patch("tools.licensed_workflow.run_request", return_value={}), patch("tools.licensed_workflow.migration_inventory", return_value={}):
            result=lab.run_payload(ID,request())
        self.assertEqual(result["status"],"EXECUTION_FAILED")
        for field in ("gateway_result","gateway_result_json","adapter_result_json","migration_inventory","workflow_request"):
            self.assertNotIn(field,result)
