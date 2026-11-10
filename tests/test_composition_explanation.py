"""Independent counterexamples for controlled reformulation and evidence views."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from tests.test_scoped_composition import NATIVE, ROOT, fixture, quantified
from tools.grammar_catalog import scoped_composition as app, composition_explanation as view, gateway


class ExplanationBoundary(unittest.TestCase):
    def test_client_cannot_supply_a_reading_or_explanation(self):
        for key in ("reading_view", "evidence_view", "canonical_text"):
            request = quantified("ليس كل طالب مجتهدًا")
            request[key] = "accepted"
            with self.subTest(field=key), self.assertRaises(ValueError):
                app.validate(request)

    def test_no_native_no_checked_reformulation_or_evidence(self):
        with patch.object(app, "NATIVE", ROOT / "missing-reader"):
            result = app.evaluate(quantified("ليس كل طالب مجتهدًا"))
        self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
        self.assertIsNone(result["reading_view"])
        self.assertIsNone(result["evidence_view"])


@unittest.skipUnless(NATIVE, "build the scoped composition and source native owners")
class ExplanationNative(unittest.TestCase):
    def evaluate(self, request):
        result = app.evaluate(request)
        self.assertTrue(result["chain_complete"], (result["status"], result.get("error")))
        self.assertTrue(result["reading_view"]["native_check"]["native_checked"])
        return result

    def test_reformulation_preserves_force_scope_and_raw_source(self):
        cases = [("ليس كل طالب مجتهدًا", "ليس كل طالب هو مجتهد.", "assertion_target"),
                 ("هل كل طالب غير مجتهد؟", "هل كل طالب ليس هو مجتهد؟", "question"),
                 ("هل كل طالب هو مجتهد؟", "هل كل طالب هو مجتهد؟", "question")]
        for text, expected, force in cases:
            with self.subTest(text=text):
                result = self.evaluate(quantified(text))
                self.assertEqual(result["reading_view"]["canonical_text"], expected)
                self.assertEqual(result["source"]["text"], text)
                meaning = result["reading_view"]["semantic_projection"]
                self.assertEqual(meaning["frame"]["force"], force)
                self.assertFalse(result["reading_view"]["reformulation_added_as_evidence"])
                self.assertNotIn(expected, [s["text"] for s in result["owner_result"]["request"]["sources"]])
                self.assertEqual(result["native_check"]["response"]["request"]["text"], text)
                self.assertEqual(result["reading_view"]["native_check"]["response"]["request"]["text"], expected)

    def test_equal_answers_do_not_make_different_scopes_equivalent(self):
        facts = "سالم هو طالب. نادر هو طالب. ليس سالم هو مجتهد. ليس نادر هو مجتهد."
        a = self.evaluate(quantified("ليس كل طالب مجتهدًا", facts))
        b = self.evaluate(quantified("كل طالب غير مجتهد", facts))
        self.assertEqual((a["status"], b["status"]), ("SUPPORTED", "SUPPORTED"))
        self.assertNotEqual(a["reading_view"]["semantic_projection"], b["reading_view"]["semantic_projection"])

    def test_forged_scope_force_genus_or_property_blocks_the_chain(self):
        for changed in ("كل طالب ليس هو مجتهد.", "هل ليس كل طالب هو مجتهد؟",
                        "ليس كل مهندس هو مجتهد.", "ليس كل طالب هو حاضر."):
            with self.subTest(text=changed), patch.object(view, "canonical_text", return_value=changed):
                result = app.evaluate(quantified("ليس كل طالب مجتهدًا"))
            self.assertEqual(result["status"], "VERIFICATION_FAILED")
            self.assertFalse(result["chain_complete"])
            self.assertIsNone(result["reading_view"])
            self.assertIsNone(result["evidence_view"])

    def test_witness_indices_restore_exact_source_and_policy_bindings(self):
        request = quantified("ليس كل طالب مجتهدًا")
        result = self.evaluate(request)
        evidence = result["evidence_view"]
        sources = {s["id"]: s["text"] for s in request["sources"]}
        for row in evidence["source_ledger"]:
            raw = sources[row["source_id"]].encode()
            self.assertEqual(raw[row["span"]["start"]:row["span"]["end"]].decode(), row["text"])
        branch = evidence["history"][0]["branches"][2]
        self.assertEqual(branch["conclusion_polarity"], "support")
        self.assertEqual([r["atom"] for r in branch["premises"]], [
            {"predicate": "طالب", "arguments": ["نادر"], "positive": True},
            {"predicate": "مجتهد", "arguments": ["نادر"], "positive": False}])
        self.assertTrue(branch["rule_present_in_native_program"])
        self.assertEqual({r["clause"]["source_id"] for r in branch["rule_source_bindings"]}, {"scope_policy"})
        self.assertTrue(all(r["source_witnesses"] for r in branch["premises"]))
        self.assertFalse(evidence["decision_recomputed"])

    def test_missing_genus_membership_does_not_become_a_negative_fact(self):
        result = self.evaluate(quantified("ليس كل طالب مجتهدًا",
            "سالم هو طالب. سالم هو مجتهد. ليس نادر هو مجتهد."))
        step = result["evidence_view"]["history"][0]
        self.assertEqual(step["status"], "UNKNOWN")
        branch = step["branches"][2]
        self.assertEqual(branch["missing_premise_indices"], [0])
        self.assertEqual(branch["opposed_premise_indices"], [])
        self.assertEqual(branch["premises"][0]["opposing_source_witnesses"], [])
        self.assertTrue(branch["premises"][1]["source_witnesses"])

    def test_evidence_withdrawal_and_irrelevant_change_keep_original_history(self):
        result = self.evaluate(fixture("quantifier")["payload"])
        history = result["evidence_view"]["history"]
        self.assertEqual([h["status"] for h in history], ["SUPPORTED", "SUPPORTED", "UNKNOWN", "SUPPORTED"])
        self.assertNotIn("color", history[1]["ready_sources"])
        self.assertEqual(history[2]["branches"][2]["missing_premise_indices"], [1])
        self.assertEqual(history[3]["branches"][2]["missing_premise_indices"], [])
        self.assertEqual([h["support_ids"] for h in history],
                         [h["support_ids"] for h in result["owner_result"]["history"]])

    def test_active_dependent_source_is_not_a_ready_witness(self):
        request = fixture("quantifier")["payload"]
        request["sources"][2]["parents"] = ["color"]
        result = self.evaluate(request)
        step = result["evidence_view"]["history"][1]
        self.assertIn("counterexample", step["active_sources"])
        self.assertNotIn("counterexample", step["ready_sources"])
        self.assertEqual(step["branches"][2]["premises"][1]["source_witnesses"], [])
        self.assertIn("counterexample", {s["source_id"] for s in result["evidence_view"]["source_ledger"]})

    def test_independent_alternative_survives_withdrawal(self):
        request = fixture("quantifier")["payload"]
        request["sources"].append({"id": "alternative", "text": "ليس نادر هو مجتهد.", "parents": []})
        request["initial_active"].append("alternative")
        request["events"] = [{"id": "withdraw_original", "kind": "withdraw", "target": "counterexample"}]
        result = self.evaluate(request)
        evidence = result["evidence_view"]
        self.assertEqual([h["status"] for h in evidence["history"]], ["SUPPORTED", "SUPPORTED"])
        witnesses = evidence["history"][1]["branches"][2]["premises"][1]["source_witnesses"]
        self.assertEqual({evidence["source_ledger"][i]["source_id"] for i in witnesses}, {"alternative"})

    def test_opposing_witness_and_foreign_individual_are_preserved(self):
        request = quantified("ليس كل طالب مجتهدًا")
        request["sources"][0]["text"] += " نادر هو مجتهد. ليس مازن هو مجتهد."
        result = self.evaluate(request)
        evidence = result["evidence_view"]
        self.assertEqual(evidence["status"], "CONFLICT")
        branch = evidence["history"][0]["branches"][2]
        row = branch["premises"][1]
        self.assertTrue(row["source_witnesses"])
        self.assertTrue(row["opposing_source_witnesses"])
        self.assertIn(1, branch["opposed_premise_indices"])
        self.assertTrue(any(s["atom"]["arguments"] == ["مازن"] for s in evidence["source_ledger"]))
        self.assertFalse(any(p["atom"]["arguments"] == ["مازن"] for b in evidence["history"][0]["branches"] for p in b["premises"]))

    def test_complete_facts_do_not_restore_a_withdrawn_policy(self):
        request = quantified("كل طالب هو مجتهد.",
            "سالم هو طالب. نادر هو طالب. سالم هو مجتهد. نادر هو مجتهد.")
        request["events"] = [{"id": "withdraw_policy", "kind": "withdraw", "target": "scope_policy"}]
        result = self.evaluate(request)
        before, after = result["evidence_view"]["history"]
        self.assertEqual((before["status"], after["status"]), ("SUPPORTED", "UNKNOWN"))
        self.assertFalse(after["policy_ready"])
        branch = after["branches"][0]
        self.assertEqual(branch["missing_premise_indices"], [])
        self.assertEqual(branch["nonclean_premise_indices"], [])
        self.assertFalse(branch["rule_present_in_native_program"])
        self.assertEqual(branch["rule_source_bindings"], [])

    def test_incomplete_owner_never_issues_completed_evidence_view(self):
        original = app.connection.evaluate
        def incomplete(request):
            result = original(request)
            result.update(chain_complete=False, status="VERIFICATION_UNAVAILABLE")
            return result
        with patch.object(app.connection, "evaluate", incomplete):
            result = app.evaluate(quantified("ليس كل طالب مجتهدًا"))
        self.assertFalse(result["chain_complete"])
        self.assertIsNotNone(result["reading_view"])
        self.assertIsNone(result["evidence_view"])


@unittest.skipUnless(NATIVE, "build the scoped composition and source native owners")
class ExplanationGateway(unittest.TestCase):
    def test_public_replay_rejects_reading_and_witness_mutations(self):
        request = fixture("quantifier")
        receipt = gateway.run(request)
        self.assertEqual(receipt["status"], "EXECUTED")
        self.assertTrue(gateway.accept_output(receipt, expected_request=request)["valid"])
        for field in ("reading_view", "evidence_view"):
            changed = deepcopy(receipt)
            owner = changed["execution"]["owner_result"]
            if field == "reading_view":
                owner[field]["canonical_text"] = "كل طالب ليس هو مجتهد."
            else:
                owner[field]["history"][0]["branches"][2]["premises"][1]["source_witnesses"] = []
            with self.subTest(field=field):
                self.assertFalse(gateway.accept_output(changed, expected_request=request)["valid"])
