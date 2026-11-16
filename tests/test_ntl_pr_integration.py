"""Combined PR routes preserve independent owners, source identity and public replay."""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest

from tools.grammar_catalog import gateway, gateway_routes

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "formal/.lake/build/bin/verifiedReading"
REQUIRE_NATIVE = any(os.environ.get(flag) == "1" for flag in
                     ("NABT_REQUIRE_IO_GATEWAY_NATIVE", "NABT_REQUIRE_OPENCYC_NATIVE"))
if REQUIRE_NATIVE and not NATIVE.is_file():
    raise RuntimeError("Combined OpenCyc/report replay requires original verifiedReading in the native gate")


def combined_request():
    request = json.loads((ROOT / "examples/io_gateway/report_rank.json").read_bytes())
    ontology = json.loads((ROOT / "examples/relations/opencyc_slice.json").read_bytes())
    request["payload"]["opencyc_slice"] = ontology["payload"]["opencyc_slice"]
    # The ontology is an independent authored ledger. This opening report makes
    # no lexical-alignment claim to the example's Dog occurrence.
    request["payload"]["opencyc_slice"]["bindings"] = []
    return request


class IntegratedRouteContracts(unittest.TestCase):
    def test_both_relational_owners_validate_and_keep_independent_inputs(self):
        request = combined_request()
        checked = gateway.validate_request(request)
        self.assertEqual(checked, request)
        checked["payload"]["opencyc_slice"]["withdrawn"].append("g1")
        checked["payload"]["report_model"]["witnesses"].clear()
        self.assertEqual(request, combined_request())
        for field in ("report_model", "opencyc_slice"):
            broken = combined_request()
            broken["payload"][field] = {}
            with self.subTest(owner=field), self.assertRaises(ValueError):
                gateway.validate_request(broken)
        forbidden = combined_request()
        forbidden["payload"]["native_checked"] = True
        with self.assertRaises(ValueError):
            gateway.validate_request(forbidden)

    def test_combined_public_replay_keeps_both_results_and_rejects_each_tamper(self):
        request = combined_request()
        receipt = gateway.run(request)
        self.assertEqual(receipt["status"], "EXECUTED")
        accepted = gateway.accept_output(receipt, expected_request=request)
        self.assertTrue(accepted["valid"], accepted)
        owner = receipt["execution"]["owner_result"]
        report = owner["report_assessment"]
        ontology = owner["opencyc_slice"]
        self.assertEqual(report["report"]["fraction"], [1, 1])
        self.assertEqual(report["external_truth"], "UNASSESSED")
        self.assertEqual(ontology["outer_source_id"], request["payload"]["source_id"])
        self.assertEqual(ontology["outer_text_sha256"], request["payload"]["report_model"]["source_sha256"])
        self.assertEqual(ontology["compiled"]["request"], request["payload"]["opencyc_slice"])
        self.assertFalse(ontology["limits"]["world_truth_established"])
        self.assertFalse(ontology["limits"]["arabic_lexical_alignment_established"])
        if NATIVE.is_file():
            self.assertIs(ontology["native_checked"], True)
            self.assertEqual(ontology["status"], "SUPPORTED")
        else:
            self.assertIs(ontology["native_checked"], False)
            self.assertEqual(ontology["status"], "DEFER")
            self.assertIsNone(ontology["native_receipt"])
        for owner_key, field, value in (("report_assessment", "external_truth", "CERTAIN"),
                                        ("opencyc_slice", "status", "FORGED")):
            forged = deepcopy(receipt)
            forged["execution"]["owner_result"][owner_key][field] = value
            with self.subTest(owner=owner_key):
                self.assertFalse(gateway.accept_output(forged, expected_request=request)["valid"])
        changed = deepcopy(request)
        changed["payload"]["opencyc_slice"]["withdrawn"] = ["g1"]
        self.assertFalse(gateway.accept_output(receipt, expected_request=changed)["valid"])

    def test_text_reader_preserves_rule_learning_links_in_verified_output(self):
        self.assertIn("rule-learning", gateway_routes.ROUTES["text.read"][0])
        request = {"schema": gateway.REQUEST_SCHEMA, "route": "text.read", "payload": {"text": "بَابٌ"}}
        receipt = gateway.run(request)
        self.assertEqual(receipt["status"], "EXECUTED")
        accepted = gateway.accept_output(receipt, expected_request=request)
        self.assertTrue(accepted["valid"], accepted)
        links = receipt["proof_test_links"]
        self.assertIn("rule-learning", {row["family"] for row in links["family_test_links"]})
        self.assertFalse(links["test_execution_performed"])
        self.assertFalse(links["formal_application_established"])
        forged = deepcopy(receipt)
        forged["proof_test_links"]["family_test_links"] = [
            row for row in links["family_test_links"] if row["family"] != "rule-learning"]
        self.assertFalse(gateway.accept_output(forged, expected_request=request)["valid"])


@unittest.skipUnless(NATIVE.is_file(), "original native OpenCyc owner required for selective withdrawal")
class NativeCombinedWithdrawal(unittest.TestCase):
    def test_ontology_withdrawal_does_not_change_report_evidence(self):
        request = combined_request()
        before = gateway.run(request)
        cut = deepcopy(request)
        cut["payload"]["opencyc_slice"]["withdrawn"] = ["g1"]
        after = gateway.run(cut)
        self.assertTrue(gateway.accept_output(before, expected_request=request)["valid"])
        self.assertTrue(gateway.accept_output(after, expected_request=cut)["valid"])
        first = before["execution"]["owner_result"]
        second = after["execution"]["owner_result"]
        self.assertEqual(first["report_assessment"], second["report_assessment"])
        self.assertEqual(first["opencyc_slice"]["status"], "SUPPORTED")
        self.assertEqual(second["opencyc_slice"]["status"], "UNKNOWN")
        self.assertTrue(second["opencyc_slice"]["native_checked"])
        self.assertFalse(second["opencyc_slice"]["limits"]["world_truth_established"])


if __name__ == "__main__":
    unittest.main()
