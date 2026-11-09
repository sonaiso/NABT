"""Independent boundary cases for retained abstraction and event evidence."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from tools.grammar_catalog import relational_bridge as bridge
from tests.test_relational_bridge import LEDGER, TARGET, NATIVE, request


@unittest.skipUnless(NATIVE.is_file(), "Build verifiedReading for continuity")
class OntologicalContinuity(unittest.TestCase):
    def row(self, result, index=0, candidate=0):
        self.assertEqual(result["status"], "SCHEMAS_RETAINED", result)
        return result["occurrences"][index]["candidates"][candidate]

    def test_source_and_derivative_retain_same_ontological_relations(self):
        result = bridge.continuity("اصفرار اصفرّ مُصْفَرّ")
        rows = [self.row(result, i) for i in range(3)]
        self.assertEqual(rows[0]["ontological_signature"], rows[1]["ontological_signature"])
        self.assertEqual(rows[1]["ontological_signature"], rows[2]["ontological_signature"])
        self.assertEqual(rows[0]["match_kind"], "schema_label_reference")
        self.assertEqual(rows[2]["reading_id"], "yellowing_participle")
        for row in rows:
            self.assertEqual([b["slot"] for b in row["general_bindings"]],
                             ["event", "bearer", "genus", "property", "time", "place"])
            self.assertTrue(all(b["state"] == "unbound_variable" and b["value"] == ""
                                for b in row["general_bindings"]))
            self.assertIsNone(row["occurrence_bindings"])
            self.assertFalse(row["occurrence_license"])
        edges = rows[0]["ontological_signature"]["relations"]
        self.assertIn({"left":"event", "relation":"property_in_event", "right":"property"}, edges)
        self.assertFalse(result["world_truth_established"])

    def test_deleted_duplicated_or_reordered_dimensions_are_rejected(self):
        row = self.row(bridge.continuity("اصفرّ"))
        bindings = row["general_bindings"]
        for bad in [bindings[:-1], bindings[1:], bindings[:-1] + [bindings[0]], list(reversed(bindings))]:
            with self.subTest(bindings=bad):
                self.assertFalse(bridge.check_bindings("yellowing_past", bad)["structurally_valid"])

    def test_unknown_is_not_zero_and_no_physical_not_applicable_escape(self):
        bindings = self.row(bridge.continuity("اصفرّ"))["general_bindings"]
        bindings[-1]["state"] = "unknown_in_occurrence"
        self.assertTrue(bridge.check_bindings("yellowing_past", bindings)["structurally_valid"])
        for state, value in [("unbound_variable", "صفر"), ("unknown_in_occurrence", "حديقة1"),
                             ("bound_value", ""), ("inapplicable_with_domain_certificate", "")]:
            bad = deepcopy(bindings); bad[-1].update(state=state, value=value)
            with self.assertRaises(ValueError): bridge.check_bindings("yellowing_past", bad)

    def test_structural_value_is_not_an_evidence_certificate(self):
        bindings = self.row(bridge.continuity("اصفرّ"))["general_bindings"]
        bindings[-1].update(state="bound_value", value="حديقة_مخترعة")
        receipt = bridge.check_bindings("yellowing_past", bindings)
        self.assertTrue(receipt["structurally_valid"])
        self.assertFalse(receipt["binding_evidence_checked"])

    def test_withdraw_state_exposes_old_gap_without_erasing_schema(self):
        p = request(); p["source_text"] = LEDGER.replace("حدث1 حالة لون_اصفر.\n", "")
        result = bridge.evaluate(TARGET, p)
        self.assertTrue(result["native_receipt"]["legacy_v1_licensed"])
        self.assertFalse(result["licensed"])
        row = self.row(bridge.continuity(TARGET, result))
        values = {b["slot"]:b for b in row["occurrence_bindings"]}
        self.assertEqual(values["property"]["state"], "unknown_in_occurrence")
        self.assertEqual(values["time"]["value"], "يوم1")
        self.assertEqual(values["place"]["value"], "حديقة1")
        self.assertEqual(len(row["ontological_signature"]["relations"]), 7)

    def test_other_event_cannot_supply_property_state(self):
        p = request(); p["source_text"] = LEDGER.replace("حدث1 حالة لون_اصفر.", "حدث2 حالة لون_اصفر.")
        self.assertFalse(bridge.evaluate(TARGET, p)["licensed"])

    def test_conflicted_or_tainted_state_cannot_bind_property(self):
        for suffix in ["ليس حدث1 حالة لون_اصفر.\n",
                       "سند1 هو صالح.\nليس سند1 هو صالح.\nإذا سند1 هو صالح فإن حدث1 حالة لون_اصفر.\n"]:
            p = request()
            p["source_text"] = (LEDGER if suffix.startswith("ليس") else
                                LEDGER.replace("حدث1 حالة لون_اصفر.\n", "")) + suffix
            result = bridge.evaluate(TARGET, p)
            self.assertFalse(result["licensed"])
            row = self.row(bridge.continuity(TARGET, result))
            self.assertEqual(next(b for b in row["occurrence_bindings"] if b["slot"] == "property")["state"],
                             "unknown_in_occurrence")

    def test_withdraw_time_place_or_membership_keeps_typed_unknown(self):
        for line, slot in [("حدث1 زمان يوم1.\n", "time"), ("حدث1 مكان حديقة1.\n", "place"),
                           ("شجرة1 عضوية نبات.\n", "genus")]:
            with self.subTest(slot=slot):
                p = request(); p["source_text"] = LEDGER.replace(line, "")
                result = bridge.evaluate(TARGET, p)
                self.assertFalse(result["licensed"])
                row = self.row(bridge.continuity(TARGET, result))
                value = next(b for b in row["occurrence_bindings"] if b["slot"] == slot)
                self.assertEqual(value, {"slot":slot, "state":"unknown_in_occurrence", "value":""})

    def test_full_ledger_binds_source_relative_instance_only(self):
        result = bridge.evaluate(TARGET, request())
        row = self.row(bridge.continuity(TARGET, result))
        self.assertTrue(row["occurrence_license"])
        self.assertEqual([b["value"] for b in row["occurrence_bindings"]],
                         ["حدث1", "شجرة1", "نبات", "لون_اصفر", "يوم1", "حديقة1"])
        self.assertFalse(result["world_truth_established"])

    def test_ambiguous_vowels_and_repeated_occurrences_preserved(self):
        result = bridge.continuity("كبر كَبِرَ كَبُرَ كبر")
        self.assertEqual([[r["reading_id"] for r in t["candidates"]] for t in result["occurrences"]],
                         [["growth_age", "growth_magnitude"], ["growth_age"],
                          ["growth_magnitude"], ["growth_age", "growth_magnitude"]])
        self.assertEqual(len({tuple(t["codepoint_span"]) for t in result["occurrences"]}), 4)

    def test_unreviewed_words_and_partial_tokens_get_no_invented_schema(self):
        result = bridge.continuity("واصفرّ اصفرّون يكتب")
        self.assertEqual(result["status"], "NO_INSTALLED_EXACT_SCHEMA")
        self.assertEqual(result["occurrences"], [])

    def test_native_unavailable_fails_closed(self):
        with patch.object(bridge.pilot, "file_sha", side_effect=FileNotFoundError):
            result = bridge.continuity("اصفرار")
        self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
        self.assertEqual(result["occurrences"], [])

    def test_gateway_replays_and_rejects_erasure_or_fabricated_binding(self):
        from tools.grammar_catalog import gateway
        req = {"schema":gateway.REQUEST_SCHEMA, "route":"relations.analyze", "payload":{"text":"اصفرار"}}
        result = gateway.run(req)
        self.assertEqual(result["status"], "EXECUTED", result)
        self.assertTrue(gateway.accept_output(result, expected_request=req)["valid"])
        for mutation in ("relations", "binding"):
            bad = deepcopy(result)
            row = bad["execution"]["owner_result"]["semantic_continuity"]["occurrences"][0]["candidates"][0]
            if mutation == "relations": row["ontological_signature"]["relations"].pop()
            else: row["general_bindings"][-1].update(state="bound_value", value="مكان_مخترع")
            self.assertFalse(gateway.accept_output(bad, expected_request=req)["valid"])


if __name__ == "__main__":
    unittest.main()
