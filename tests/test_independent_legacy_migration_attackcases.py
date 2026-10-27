"""Independent integrity/authority attacks; imported receipts never certify truth."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import unittest

from nabt import transport_contract as transport


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "evidence/legacy_migration_v2/independent_review"
FROZEN_SHA = "94d2ca2169e9a7b9c009f57a88b915f620a4b09d4136a455433b4b02fa02fde5"


class IndependentLegacyMigrationAttacks(unittest.TestCase):
    def test_reference_frozen_before_execution_and_not_claimed_blind(self):
        raw = (REFERENCE / "cases.v1.json").read_bytes()
        frozen = json.loads((REFERENCE / "freeze.json").read_bytes())
        self.assertEqual(sha256(raw).hexdigest(), FROZEN_SHA)
        self.assertEqual(frozen["sha256"], FROZEN_SHA)
        self.assertFalse(frozen["new_implementation_executed"])
        self.assertFalse(frozen["blind"])
        cases = json.loads(raw)["cases"]
        self.assertEqual(len(cases), 32)
        self.assertEqual(len({case["id"] for case in cases}), 32)
        self.assertEqual(sum(case["expected"]["boundary_acquired"] for case in cases), 16)

    def make_forgery(self):
        # Valid byte binding is deliberately manufactured, not a native run.
        result = {"native_checked": True, "status": "SUPPORTED", "claims": [{
            "kind": "IMPORTED_ASSERTION", "scope": "arbitrary imported scope",
            "proof": {"law_id": "invented.law", "theorems": ["Imaginary.complete"]}}]}
        return transport._envelope(entrypoint="invented.caller", command="invented.command",
            resolved_request={"text": "هذا ادعاء مستورد"}, result=result,
            policy_id="invented.policy", authority="invented.authority", claim_paths=("claims[0]",))

    def test_self_consistent_native_flag_does_not_grant_imported_authority(self):
        report = transport.validate_transport_envelope(self.make_forgery())
        self.assertTrue(report["integrity_valid"], report)
        self.assertFalse(report["proof_authority_established"])
        self.assertTrue(report["fresh_execution_required"])
        self.assertFalse(report["grants_language_license"])
        self.assertFalse(report["all_arabic_complete"])

    def test_inherited_response_mutation_breaks_binding(self):
        forged = self.make_forgery()
        forged["response"]["claims"][0]["scope"] = "different inherited proof"
        report = transport.validate_transport_envelope(forged)
        self.assertFalse(report["integrity_valid"])
        self.assertFalse(report["proof_authority_established"])

    def test_request_text_and_context_are_not_interchangeable(self):
        forged = self.make_forgery()
        forged["transport_contract"]["request"]["text"] += " "
        report = transport.validate_transport_envelope(forged)
        self.assertFalse(report["integrity_valid"])
        self.assertFalse(report["proof_authority_established"])

    def test_noncanonical_claim_path_rejected(self):
        for path in ("claims[-1]", "claims[00]", "claims[0].__class__", "claims[0] "):
            with self.subTest(path=path):
                forged = self.make_forgery()
                forged["transport_contract"]["named_claims"][0]["child_path"] = path
                report = transport.validate_transport_envelope(forged)
                self.assertFalse(report["integrity_valid"])
                self.assertFalse(report["proof_authority_established"])

    def test_extra_authority_flag_cannot_be_ignored(self):
        for location in ("envelope", "binding"):
            forged = deepcopy(self.make_forgery())
            if location == "envelope":
                forged["proof_authority_established"] = True
            else:
                forged["transport_contract"]["proof_authority_established"] = True
            report = transport.validate_transport_envelope(forged)
            self.assertFalse(report["integrity_valid"])
            self.assertFalse(report["proof_authority_established"])


if __name__ == "__main__":
    unittest.main()
