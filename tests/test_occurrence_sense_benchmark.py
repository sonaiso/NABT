"""Independent scorer tests using fabricated receipts, never runtime outputs."""
from copy import deepcopy
import unittest

from tools import benchmark_occurrence_sense as scorer


def seal(receipt):
    receipt["receipt_sha256"] = scorer.digest({k: v for k, v in receipt.items() if k != "receipt_sha256"})
    return receipt


def fixture_case():
    return {"id": "FIXTURE", "input": {"text": "شَجَرٌ", "context": {}, "token_index": 0,
                                       "target": ["تعريف"], "budget": 12},
            "expect": {"logical_class": "synthetic_test", "candidate_sense_ids_exact": ["sense:a", "sense:b"],
                       "conditional_matching_sense_ids_exact": ["sense:a"],
                       "conditional_inclusion_sense_ids_exact": [], "conditional_entailment_sense_ids_exact": []}}


def fixture_receipt(case):
    request = deepcopy(case["input"])
    return seal({"schema": scorer.SCHEMA, "status": "CANDIDATES_ONLY", "input": request,
                 "input_sha256": scorer.digest(request), "context_sha256": scorer.digest(request["context"]),
                 "occurrence": scorer.outer_occurrences(request["text"])[request["token_index"]],
                 "readings": [{"source_form": "synthetic", "lemma_bw": "test", "root_bw": "test",
                               "pos": "N", "donor_ids": ["synthetic_donor"], "status": "CANDIDATES_ONLY",
                               "senses": [{"id": "sense:a", "mutabaqa": True, "tadammun": False, "iltizam": False},
                                          {"id": "sense:b", "mutabaqa": False, "tadammun": False, "iltizam": False}]}],
                 "candidate_senses": [{"id": sid, "conditional_only": True,
                                       "sense_licensed_for_new_occurrence": False,
                                       "interpretation_status": "AUTHORED_NOT_INDEPENDENTLY_ADJUDICATED"}
                                      for sid in ("sense:a", "sense:b")],
                 "native_checked": True, "certificate_checked": True, "initial_reference": None,
                 "contextual_sense_selected": False, "world_truth_established": False,
                 "whole_clause_checked": False, "reference_transferred": False, "all_arabic_complete": False})


class OccurrenceBenchmarkTests(unittest.TestCase):
    def test_frozen_bytes_and_explicit_input_boundary(self):
        ref = scorer.load_reference()
        self.assertEqual(len(ref["cases"]), 20)
        self.assertEqual(len(ref["metamorphic_obligations"]), 5)
        self.assertEqual(scorer.digest(ref), scorer.DERIVED_REFERENCE_SHA256)

    def test_erratum_cannot_change_senses_inputs_or_other_fields(self):
        case = fixture_case()
        before = ["sense:a", "QATR-REFERENCE"]
        case["expect"]["candidate_sense_ids_exact"] = before
        amendment = {"case_id": "FIXTURE", "field": "candidate_sense_ids_exact", "before": before,
                     "after": ["sense:a"], "reason": "synthetic provenance pollution"}
        reference = {"cases": [case]}
        kwargs = {"catalogue_ids": {"sense:a", "sense:b"}, "passage_ids": scorer.PASSAGE_ID_ERRATA}
        changed = deepcopy(amendment)
        changed["after"] = []
        with self.assertRaises(ValueError):
            scorer.apply_erratum(reference, [changed], **kwargs)
        for field in ("input", "conditional_matching_sense_ids_exact", "world_truth_asserted"):
            changed = {**amendment, "field": field}
            with self.assertRaises(ValueError):
                scorer.apply_erratum(reference, [changed], **kwargs)
        self.assertEqual(reference["cases"][0]["expect"]["candidate_sense_ids_exact"], before)

    def test_shared_generator_list_does_not_mutate_original_or_provenance(self):
        case = fixture_case()
        shared = ["sense:a", "QATR-REFERENCE"]
        case["expect"]["candidate_sense_ids_exact"] = shared
        case["source_basis"] = shared
        original_input = deepcopy(case["input"])
        correction = {"case_id": "FIXTURE", "field": "candidate_sense_ids_exact", "before": shared,
                      "after": ["sense:a"], "reason": "synthetic shared-list regression"}
        derived = scorer.apply_erratum({"cases": [case]}, [correction],
                                       catalogue_ids={"sense:a", "sense:b"}, passage_ids=scorer.PASSAGE_ID_ERRATA)
        self.assertEqual(derived["cases"][0]["expect"]["candidate_sense_ids_exact"], ["sense:a"])
        self.assertEqual(derived["cases"][0]["source_basis"], shared)
        self.assertEqual(case["expect"]["candidate_sense_ids_exact"], shared)
        self.assertEqual(derived["cases"][0]["input"], original_input)

    def test_reference_validation_rejects_unknown_and_duplicate_labels(self):
        case = fixture_case()
        case["expect"]["candidate_sense_ids_exact"] = ["sense:a", "sense:a"]
        with self.assertRaises(ValueError):
            scorer.validate_reference_labels({"cases": [case]}, {"sense:a", "sense:b"})
        case["expect"]["candidate_sense_ids_exact"] = ["QATR-REFERENCE"]
        with self.assertRaises(ValueError):
            scorer.validate_reference_labels({"cases": [case]}, {"sense:a", "sense:b"})

    def test_independent_span_oracle_excludes_quote_and_counts_utf8(self):
        tokens = scorer.outer_occurrences('«أَنَا» رَجُلٌ.')
        self.assertEqual(tokens, [{"surface": "رَجُلٌ", "start_byte": len('«أَنَا» '.encode()),
                                   "end_byte": len('«أَنَا» رَجُلٌ'.encode())}])

    def test_positive_inventory_and_indication_are_separate(self):
        case = fixture_case()
        receipt = fixture_receipt(case)
        result = scorer.compare_case(case, receipt)["comparison"]
        self.assertEqual(result["candidate_acquisition"]["status"], "PASS")
        self.assertEqual(result["conditional_indication"]["status"], "PASS")
        receipt["readings"][0]["senses"][0]["mutabaqa"] = False
        result = scorer.compare_case(case, seal(receipt))["comparison"]
        self.assertEqual(result["candidate_acquisition"]["status"], "PASS")
        self.assertEqual(result["conditional_indication"]["status"], "FAIL")

    def test_dropping_an_alternative_is_not_correct_ambiguity(self):
        case = fixture_case()
        receipt = fixture_receipt(case)
        receipt["readings"][0]["senses"].pop()
        receipt["candidate_senses"].pop()
        result = scorer.compare_case(case, seal(receipt))["comparison"]
        self.assertEqual(result["ambiguity"]["status"], "FAIL")
        self.assertEqual(result["candidate_acquisition"]["status"], "FAIL")

    def test_safe_abstention_does_not_satisfy_positive_coverage(self):
        case = fixture_case()
        case["expect"]["linguistic_candidate_obligation"] = ["sense:a"]
        receipt = fixture_receipt(case)
        receipt.update(status="NO_MORPHOLOGY_READING", readings=[], candidate_senses=[])
        result = scorer.compare_case(case, seal(receipt))["comparison"]
        self.assertEqual(result["safety"]["status"], "PASS")
        self.assertEqual(result["candidate_acquisition"]["status"], "FAIL")
        self.assertEqual(result["linguistic_coverage"]["status"], "FAIL")
        self.assertEqual(result["native"]["status"], "PASS")

    def test_native_success_never_substitutes_for_expected_meaning(self):
        case = fixture_case()
        receipt = fixture_receipt(case)
        receipt["readings"][0]["senses"][1]["iltizam"] = True
        result = scorer.compare_case(case, seal(receipt))["comparison"]
        self.assertEqual(result["native"]["status"], "PASS")
        self.assertEqual(result["conditional_indication"]["status"], "FAIL")
        self.assertEqual(result["safety"]["status"], "FAIL")

    def test_missing_flags_unknown_status_and_boolean_alias_fail_closed(self):
        case = fixture_case()
        receipt = fixture_receipt(case)
        del receipt["world_truth_established"]
        self.assertEqual(scorer.compare_case(case, seal(receipt))["comparison"]["safety"]["status"], "FAIL")
        receipt = fixture_receipt(case)
        receipt["status"] = "EVERYTHING_PROVED"
        self.assertTrue(scorer.normalize(seal(receipt))["errors"])
        receipt = fixture_receipt(case)
        receipt["readings"][0]["senses"][0]["mutabaqa"] = 1
        self.assertIn("MALFORMED_INDICATION", scorer.normalize(seal(receipt))["errors"])

    def test_context_or_occurrence_substitution_fails_even_with_new_hash(self):
        case = fixture_case()
        receipt = fixture_receipt(case)
        receipt["input"]["context"] = {"speaker": "somebody"}
        receipt["input_sha256"] = scorer.digest(receipt["input"])
        self.assertEqual(scorer.compare_case(case, seal(receipt))["comparison"]["safety"]["status"], "FAIL")
        receipt = fixture_receipt(case)
        receipt["occurrence"]["start_byte"] += 1
        self.assertEqual(scorer.compare_case(case, seal(receipt))["comparison"]["safety"]["reason"], "WRONG_SELECTED_OCCURRENCE")

    def test_missing_inventory_cannot_be_an_empty_success(self):
        case = fixture_case()
        case["expect"]["candidate_sense_ids_exact"] = []
        receipt = fixture_receipt(case)
        del receipt["readings"]
        receipt["candidate_senses"] = []
        result = scorer.compare_case(case, seal(receipt))["comparison"]
        self.assertEqual(result["candidate_acquisition"]["status"], "FAIL")

    def test_resource_stop_never_certifies_partial_success(self):
        case = fixture_case()
        receipt = fixture_receipt(case)
        receipt["status"] = "RESOURCE_LIMIT"
        normalized = scorer.normalize(seal(receipt))
        self.assertIn("STOP_RESULT_CONTAINS_SUCCESS_CANDIDATES", normalized["errors"])

    def test_missing_reference_or_output_does_not_crash_pair_scorer(self):
        case = fixture_case()
        rows = [scorer.compare_case(case, None)]
        pairs = scorer.compare_pairs([{"cases": ["FIXTURE"], "same": ["initial_reference.bound_entity_id"]}], rows)
        self.assertEqual(pairs[0]["status"], "FAIL")

    def test_initial_reference_must_bind_its_own_occurrence(self):
        case = fixture_case()
        case["input"]["text"] = "أَنَا شَجَرٌ"
        case["input"]["token_index"] = 1
        case["expect"]["initial_reference"] = {
            "candidate_entity_ids_exact": ["person_a"], "bound_entity_id": "person_a",
            "occurrence_token_index": 0}
        receipt = fixture_receipt(case)
        initial_input = {key: deepcopy(case["input"][key]) for key in ("text", "context")}
        receipt["initial_reference"] = {
            "input": initial_input, "input_sha256": scorer.digest(initial_input),
            "native_checked": True, "certificate_checked": True,
            "execution": {"input": {"occurrence": scorer.outer_occurrences(initial_input["text"])[0]}},
            "reference": {"candidate_entity_ids": ["person_a"], "bound_entity_id": "person_a",
                          "status": "RESOLVED", "scope": "outer", "occurrence": 0}}
        self.assertEqual(scorer.compare_case(case, seal(receipt))["comparison"]["initial_reference"]["status"], "PASS")
        receipt["initial_reference"]["execution"]["input"]["occurrence"] = receipt["occurrence"]
        self.assertEqual(scorer.compare_case(case, seal(receipt))["comparison"]["initial_reference"]["status"], "FAIL")

    def test_execution_receives_no_case_labels_and_errors_are_unmeasured(self):
        calls = []
        def unavailable(request):
            self.assertEqual(set(request), {"text", "context", "token_index", "target", "budget"})
            calls.append(deepcopy(request))
            raise OSError("synthetic unavailable source")
        report = scorer.run(execute=unavailable, require_native=True, require_safety=True)
        self.assertEqual(len(calls), 20)
        self.assertEqual(report["summary"]["safety"]["unmeasured"], 20)
        self.assertFalse(report["requirements_met"])


if __name__ == "__main__":
    unittest.main()
