"""Transport integrity and inference authority are independent contracts."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nabt.transport_contract import _envelope, _claim_paths, validate_transport_envelope
from tools.transport_adapters import certify_inference
from tools.licensed_inference import runtime
from tests._transport_native import require_native

SOURCE = "سار زيد أمامك خلف الدار"
QUERY = "هل سار زيد أمامك خلف الدار؟"


class TransportIntegrityTests(unittest.TestCase):
    def envelope(self, result=None):
        return _envelope(entrypoint="test", command="diagnose", resolved_request={"text": "عَيْنَ", "time": "t1"},
            result=result or {"value": 1.0, "integer": 9007199254740993}, policy_id="diagnostic",
            authority="DIAGNOSTIC_ONLY")

    def test_lossless_canonical_byte_binding_without_imported_authority(self):
        envelope = self.envelope()
        binding = envelope["transport_contract"]
        self.assertIn("9007199254740993", binding["child_response_canonical"])
        self.assertIn("1.0", binding["child_response_canonical"])
        self.assertEqual(sha256(binding["child_response_canonical"].encode()).hexdigest(), binding["child_response_sha256"])
        result = validate_transport_envelope(envelope)
        self.assertTrue(result["integrity_valid"])
        self.assertFalse(result["proof_authority_established"])
        self.assertTrue(result["fresh_execution_required"])

    def test_mutated_request_response_metadata_are_rejected(self):
        original = self.envelope()
        changes = [lambda e: e["response"].update(integer=9007199254740992),
                   lambda e: e["transport_contract"]["request"].update(time="t2"),
                   lambda e: e["transport_contract"].update(child_response_sha256="0" * 64),
                   lambda e: e["transport_contract"].update(grants_language_license=True)]
        for change in changes:
            item = deepcopy(original)
            change(item)
            self.assertFalse(validate_transport_envelope(item)["integrity_valid"])

    def test_rehashed_forged_claim_remains_untrusted_import(self):
        forged = {"native_checked": True, "claims": [{"kind": "UNFOUNDED", "scope": "all Arabic",
            "proof": {"law_id": "fake", "theorems": ["imaginary"]}}]}
        envelope = _envelope(entrypoint="fake", command="fake", resolved_request={}, result=forged,
            policy_id="fake", authority="fake", claim_paths=["claims[0]"])
        result = validate_transport_envelope(envelope)
        self.assertTrue(result["integrity_valid"])
        self.assertFalse(result["proof_authority_established"])
        with self.assertRaises(ValueError):
            _claim_paths(forged, "inference")

    def test_noncanonical_paths_nonfinite_values_and_duplicate_paths_rejected(self):
        claim = {"kind": "X", "scope": "scope", "proof": {"law_id": "law", "theorems": ["t"]}}
        for paths in (["claims[-1]"], ["claims[00]"], ["claims[0]", "claims[0]"]):
            with self.assertRaises(ValueError):
                _envelope(entrypoint="test", command="test", resolved_request={}, result={"claims": [claim]},
                    policy_id="test", authority="test", claim_paths=paths)
        with self.assertRaises(ValueError):
            self.envelope({"value": float("nan")})

    def test_exact_bytes_are_not_an_arabic_cell_cast(self):
        item = _envelope(entrypoint="test", command="test", resolved_request={"raw": "عَيْنَ".encode()},
            result={}, policy_id="test", authority="DIAGNOSTIC_ONLY")
        request = item["transport_contract"]["request"]["raw"]
        self.assertEqual(bytes.fromhex(request["hex"]), "عَيْنَ".encode())
        self.assertNotIn("cells", request)

    def test_missing_native_skips_portable_discovery_but_fails_mandatory_gate(self):
        with tempfile.TemporaryDirectory() as directory, patch("tests._transport_native.BIN", Path(directory)):
            with patch.dict(os.environ, {"NABT_REQUIRE_NATIVE_TRANSPORT": "0"}):
                with self.assertRaises(unittest.SkipTest):
                    require_native("missing-checker")
            with patch.dict(os.environ, {"NABT_REQUIRE_NATIVE_TRANSPORT": "1"}):
                with self.assertRaises(AssertionError):
                    require_native("missing-checker")


class InferenceTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_native("licensedInference")
        cls.baseline = runtime.evaluate(SOURCE, QUERY)
        if cls.baseline.get("native_checked") is not True:
            raise AssertionError("Mandatory installed licensedInference native check unavailable")

    def test_fresh_raw_input_executes_native_and_names_exact_claim(self):
        result = certify_inference(SOURCE, QUERY)
        self.assertEqual(result["status"], "SUPPORTED")
        self.assertTrue(result["native_checked"])
        self.assertEqual(result["claims"][0]["kind"], "SOURCE_BOUND_FINITE_INFERENCE")
        self.assertFalse(result["strict_language_accepted"])
        self.assertFalse(result["world_truth_established"])

    def test_source_query_scope_and_time_are_bound_independently(self):
        for changes in ({"source_id": "different"}, {"scope": "another"}, {"time": "t2"}, {"revision": "2"}):
            with self.subTest(changes=changes), patch.object(runtime, "evaluate", return_value=deepcopy(self.baseline)):
                result = certify_inference(SOURCE, QUERY, **changes)
                self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
                self.assertEqual(result["claims"], [])
        for source, query in ((SOURCE + " ", QUERY), (SOURCE, QUERY + " ")):
            with patch.object(runtime, "evaluate", return_value=deepcopy(self.baseline)):
                self.assertEqual(certify_inference(source, query)["claims"], [])

    def test_false_and_numeric_verification_or_changed_native_fields_cannot_gain_claim(self):
        changes = [lambda r: r.update(verified=1), lambda r: r.update(closures_checked=False),
                   lambda r: r.update(all_readings_complete=False),
                   lambda r: r["native_result"].update(source_text="another"),
                   lambda r: r["native_result"].update(reading_count=0),
                   lambda r: r["proposal"].update(readings=[]),
                   lambda r: r.update(aggregate={"skeptical_clean_positive": True})]
        for change in changes:
            item = deepcopy(self.baseline)
            change(item)
            with patch.object(runtime, "evaluate", return_value=item):
                result = certify_inference(SOURCE, QUERY)
                self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
                self.assertFalse(result["native_checked"])
                self.assertEqual(result["claims"], [])

    def test_missing_native_unknown_and_resource_are_separate_no_claims(self):
        with patch.object(runtime, "_native", side_effect=FileNotFoundError("missing native")):
            result = certify_inference(SOURCE, QUERY)
            self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
            self.assertEqual(result["claims"], [])
        self.assertEqual(certify_inference(SOURCE + " ربما", QUERY)["status"], "UNKNOWN")
        result = certify_inference(SOURCE, QUERY, budget={"max_source_bytes": 1})
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
        self.assertEqual(result["claims"], [])

class InferenceTransportPortableTests(unittest.TestCase):
    def test_no_caller_checker_proof_root_or_boolean_budget(self):
        for key in ("native_checked", "checker", "receipt", "root"):
            with self.assertRaises(TypeError):
                certify_inference(SOURCE, QUERY, **{key: True})
        for budget in ({"max_readings": True}, {"extra": 1}, 1):
            self.assertEqual(certify_inference(SOURCE, QUERY, budget=budget)["status"], "INVALID_INPUT")

    def test_foundation_guard_precedes_dependency_execution(self):
        with patch("nabt.foundation.require_foundation", side_effect=RuntimeError("blocked")), \
             patch.object(runtime, "evaluate") as evaluate:
            with self.assertRaises(RuntimeError):
                certify_inference(SOURCE, QUERY)
            evaluate.assert_not_called()
