"""Checker counterexamples: input-only planning, typed scoring and consistency."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nabt_progressive_unit_checker", ROOT / "tools/check_progressive_units.py")
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


def envelope(operation, **fields):
    return {"law_id": checker.LAW, "scope": checker.SCOPE, "conditional": True,
            "acquisition_measured": False, "status": "OK", "op": operation, **fields}


class ProgressiveUnitCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.material = checker.load_material()

    def case(self, case_id):
        return deepcopy(next(c for c in self.material["cases"] if c["id"] == case_id))

    def planned(self, case_id):
        case = self.case(case_id)
        return checker.build_requests(case["operation"], case["input"])

    def test_plan_is_invariant_under_complete_gold_and_rationale_mutation(self):
        altered = deepcopy(self.material)
        for case in altered["cases"]:
            case["expected"] = {"admitted": "poison", "surface": ["gold-only-atom"],
                                "rank": True, "all_exact_positive": True}
            case["rationale"] = "gold-only-rule"
        self.assertEqual(checker.build_plan(altered), checker.build_plan(self.material))
        self.assertNotIn("gold-only", checker.canonical(checker.build_plan(altered)))

    def test_asserted_rank_contract_is_not_silently_replaced_by_computed_height(self):
        for case_id in ("D13", "D14"):
            plan = self.planned(case_id)
            self.assertEqual(plan["requests"], [])
            self.assertIn("derivation height", plan["unmeasured_reason"])

    def test_status_labels_and_completeness_flags_do_not_create_necessity_witnesses(self):
        for case_id in ("D17", "D18"):
            plan = self.planned(case_id)
            self.assertEqual(plan["requests"], [])
            self.assertIn("CompleteWithin", plan["unmeasured_reason"])

    def test_false_removed_atom_is_preserved_in_local_substitution_request(self):
        request = self.planned("D12")["requests"][0]["request"]
        edits = [t for t in checker.nodes(request["tree"]) if t["op"] == "substitute"]
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0]["child"]["value"], "C")
        self.assertEqual(edits[0]["child"]["source"]["atoms"][1], "V")
        self.assertFalse(checker.tree_view(request["tree"], request["inventory"])["structural"])

    def test_atomic_out_of_range_assertion_is_sent_without_repair(self):
        request = self.planned("D02")["requests"][0]["request"]
        atom = request["tree"]
        self.assertEqual(atom["before"], ["C", "V", "C", "V"])
        self.assertEqual(atom["value"], "V")
        self.assertEqual(atom["after"], [])
        self.assertFalse(checker.tree_view(atom, request["inventory"])["structural"])

    def test_explicit_positive_fixture_targets_every_composite_exactly(self):
        request = self.planned("D03")["requests"][0]["request"]
        self.assertEqual([r["target"] for r in request["offered"]], checker.nodes(request["tree"]))
        self.assertEqual(request["offered"], request["interpreted"])
        self.assertTrue(all(r["supports"] and r["positive"] is True for r in request["offered"]))

    def test_no_evidence_fixture_does_not_get_automatic_support(self):
        request = self.planned("D06")["requests"][0]["request"]
        self.assertEqual(request["offered"], [])
        self.assertEqual(request["interpreted"], [])

    def test_wrap_only_receipt_is_not_rewritten_into_join_evidence(self):
        request = self.planned("D07")["requests"][0]["request"]
        self.assertEqual(request["tree"]["op"], "join")
        self.assertEqual(request["offered"][0]["target"]["op"], "wrap")
        self.assertFalse(checker.valid_receipt(request, request["tree"], request["offered"][0]))

    def test_source_revision_alternative_remains_distinct_and_registered(self):
        request = self.planned("D05")["requests"][0]["request"]
        revisions = {source["revision"] for source in request["inventory"]}
        self.assertEqual(revisions, {1, 2})
        self.assertFalse(checker.tree_view(request["tree"], request["inventory"])["structural"])

    def test_withdrawal_retains_parent_tree_and_opaque_lift_contract(self):
        rows = self.planned("D16")["requests"]
        before, after = rows[0]["request"], rows[1]["request"]
        self.assertEqual(before["tree"], after["tree"])
        self.assertEqual(before["inventory"], after["inventory"])
        self.assertEqual(before["tree"]["tag"]["class_id"], 73)
        self.assertEqual(before["tree"]["child"]["tag"]["class_id"], 74)
        self.assertTrue(checker.tree_view(before["tree"], before["inventory"])["structural"])
        self.assertLess(len(after["offered"]), len(before["offered"]))
        self.assertTrue(any(r["target"] == before["tree"] for r in after["offered"]))

    def test_missing_probe_field_is_unmeasured_not_an_expected_success(self):
        case = self.case("D01")
        material = {"cases": [case]}
        plan = checker.build_plan(material)
        response = envelope("derive")
        result = checker.score(material, plan, {plan["requests"][0]["request_id"]: response})
        self.assertEqual(result["summary"]["measured_pass"], 0)
        self.assertEqual(result["summary"]["unmeasured"], len(case["expected"]))
        self.assertFalse(result["summary"]["measured_contract_gate"])

    def test_empty_quota_occurrence_claim_stays_unmeasured(self):
        case = self.case("P09")
        material = {"cases": [case]}
        plan = checker.build_plan(material)
        response = envelope("quota", enumeration="COMPLETE", shapes=[""], count=1,
                            consonants=0, vowels=0, search_complete=True, shape_numbers=[0])
        result = checker.score(material, plan, {plan["requests"][0]["request_id"]: response})
        assertions = {row["field"]: row for row in result["cases"][0]["assertions"]}
        self.assertEqual(assertions["empty_occurrence_licensed"]["status"], "UNMEASURED")
        self.assertEqual(result["summary"]["measured_pass"], 3)

    def test_boolean_cannot_pass_as_integer_even_nested(self):
        self.assertFalse(checker.field_agrees("count", True, 1))
        self.assertFalse(checker.field_agrees("extent", [True, 2], [1, 2]))
        request = {"op": "quota", "consonants": 0, "vowels": 0, "max_atoms": 0}
        response = envelope("quota", enumeration="COMPLETE", shapes=[""], count=True)
        with self.assertRaises(ValueError):
            checker.validate_response(request, response)

    def test_unsupported_child_cannot_be_reported_licensed(self):
        request = self.planned("D06")["requests"][0]["request"]
        with self.assertRaisesRegex(ValueError, "inconsistent field verdict"):
            checker.validate_response(request, envelope("derive", verdict="LICENSED", licensed=True))

    def test_conflict_cannot_be_hidden_by_top_level_license(self):
        request = self.planned("D08")["requests"][0]["request"]
        with self.assertRaises(ValueError):
            checker.validate_response(request, envelope("derive", verdict="LICENSED", licensed=True, conflict=False))

    def test_known_negative_remains_checked_when_omitted_from_offered(self):
        request = self.planned("D08")["requests"][0]["request"]
        request["offered"] = [r for r in request["offered"] if r["positive"]]
        checker.validate_response(request, envelope("derive", verdict="REJECTED", licensed=False, conflict=True))
        with self.assertRaises(ValueError):
            checker.validate_response(request, envelope("derive", verdict="LICENSED", licensed=True))

    def test_admitted_ids_cannot_contradict_the_exact_receipt_target(self):
        request = self.planned("D07")["requests"][0]["request"]
        steps = [{"target": node, "offered_admitted_ids": []} for node in checker.nodes(request["tree"])]
        steps[0]["offered_admitted_ids"] = [1]
        with self.assertRaisesRegex(ValueError, "offered_admitted_ids"):
            checker.validate_response(request, envelope("derive", verdict="UNKNOWN", licensed=False,
                                                       premise_steps=steps))

    def test_displaced_output_cannot_be_fabricated_by_the_checker_or_probe(self):
        request = self.planned("D10")["requests"][0]["request"]
        steps = [{"target": node} for node in checker.nodes(request["tree"])]
        for step in steps:
            if step["target"]["op"] == "substitute":
                step["displaced_output"] = ["gold-only-atom"]
        with self.assertRaisesRegex(ValueError, "displaced_output"):
            checker.validate_response(request, envelope("derive", premise_steps=steps))

    def test_proposal_comparison_cannot_be_reported_as_a_licensed_comparison(self):
        request = self.planned("D19")["requests"][0]["request"]
        with self.assertRaisesRegex(ValueError, "comparison_scope"):
            checker.validate_response(request, envelope("compare", comparison_scope="licensed"))
        self.assertEqual(checker.observation("occurrence_identity", {},
                         {"comparison": envelope("compare", same_occurrence=False)}), {})

    def test_false_withdrawal_control_does_not_get_credit_for_nonacceptance(self):
        with self.assertRaisesRegex(ValueError, "did not begin licensed"):
            checker.observation("withdraw_premise", {}, {"before": {"licensed": False},
                                "after": {"licensed": False, "verdict": "UNKNOWN"}})

    def test_output_artifact_is_exclusive_and_never_overwrites_a_prior_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "measurement.json"
            checker.write_json(path, {"first": True})
            original = path.read_bytes()
            with self.assertRaises(FileExistsError):
                checker.write_json(path, {"second": True})
            self.assertEqual(path.read_bytes(), original)

    def test_duplicate_json_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            checker.parse('{"licensed":false,"licensed":true}')

    def test_compound_output_number_domain_is_distinct_from_its_atomic_input(self):
        request = {"op": "cell_effect", "cells": [68, 55, 39], "mode": "waqf", "entry": 0}
        valid = envelope("cell_effect", alphabet_id="nabt.a116-sequence.v1",
                         sub_law_id="nabt.unit-carrier.v1", sound_law_id="nabt-sound-shape-v1",
                         cells=[68, 55, 39], mode="waqf", entry=0, unit_n=935000,
                         exit=35, weight=3, sound_shape_accepted=True, lexical_attestation_inferred=False)
        checker.validate_response(request, valid)
        wrong = {**valid, "alphabet_id": "nabt.a116.v1"}
        with self.assertRaisesRegex(ValueError, "alphabet_id"):
            checker.validate_response(request, wrong)


if __name__ == "__main__":
    unittest.main()
