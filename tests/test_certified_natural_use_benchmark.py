"""Independent failure controls for the new occurrence-bound diagnostic scorer."""
import hashlib
import unittest

from tools import benchmark_certified_natural_use as benchmark


def report_for(case, *, sense="spring", selected=True):
    text = case["input"]["text"]
    raw = text.encode()
    span = case["target"]
    arguments = benchmark._arguments(case)
    names = {"spring": "عين الماء", "eye": "العين الباصرة", "gold": "الذهب"}
    candidates = [{"sense_id": key, "gloss": value} for key, value in names.items()]
    occurrence = {"occurrence_id": "exact-target", "expression": "عين",
                  "span": {"start_byte": span["start_byte"], "end_byte": span["end_byte"],
                           "raw_text": span["surface"], "sha256": span["sha256"]},
                  "frame": {"occurrence": {"raw": text, "revision": hashlib.sha256(raw).hexdigest(),
                                             "start_byte": span["start_byte"], "end_byte": span["end_byte"],
                                             "source": arguments["source_id"], "referent": arguments["subject"],
                                             "context": arguments["context"]}},
                  "candidates": candidates, "selected_sense_ids": [sense] if selected else [],
                  "excluded_sense_ids": []}
    return {"strict_language_accepted": False, "native_checked": True, "status": "DEFER",
            "foundation_source": {"status": "PARTIAL"}, "claims": [],
            "diagnostic": {"status": "COMPLETE", "world_truth_established": False,
                           "all_arabic_complete": False,
                           "source": {"source_id": arguments["source_id"], "raw_text": text,
                                      "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()},
                           "occurrences": [occurrence]}}


def consistent_claim_fixture(case):
    """Synthetic consistency fixture; never a real Lean execution receipt."""
    raw = report_for(case)
    occurrence = raw["diagnostic"]["occurrences"][0]
    occurrence["native_request"] = {"frame": occurrence["frame"], "proposed": [{"fixture": "candidate"}]}
    source = {"id": case["input"]["context"]["utterance_id"],
              "revision": raw["diagnostic"]["source"]["sha256"], "text": case["input"]["text"]}
    raw["foundation_source"] = {"source": source, "cells": [1], "status": "COMPLETE"}
    request = {"op": "certify_a116", "source": source, "cells": [1], "request": occurrence["native_request"]}
    receipt = {"source": source, "cells": [1], "projection_status": "COMPLETE",
               "source_bound": True, "cells_exact": True, "candidate_set_checked": True}
    request_sha = benchmark.sha(benchmark.canonical(request).encode())
    response_sha = benchmark.sha(benchmark.canonical(receipt).encode())
    raw["occurrences"] = [{"occurrence_id": occurrence["occurrence_id"], "native_checked": True,
                            "native_receipt": receipt, "request_sha256": request_sha,
                            "response_sha256": response_sha}]
    raw["claims"] = [{"kind": "A116_EXACT_INSTALLED_CANDIDATE_SET", "candidate_count": 1,
                       "authority": "KERNEL_CHECKED_CONDITIONAL",
                       "proof": {"kind": "NATIVE_LEAN_RECEIPT", "law_id": "nabt.certified-lexical.v1"},
                       "binding": {"frame": occurrence["frame"], "source": source,
                                   "request_sha256": request_sha, "response_sha256": response_sha}}]
    return raw


class IndependentCertifiedBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases, cls.controls = benchmark.load_cases()
        cls.by_id = {case["id"]: case for case in cls.cases}

    def test_frozen_domains_and_denominators_are_separate(self):
        self.assertEqual(len(self.cases), 30)
        self.assertEqual(len(self.controls), 3)
        self.assertEqual(len({case["family"] for case in self.cases}), 6)
        for case in self.cases:
            target = case["target"]
            self.assertEqual(case["input"]["text"].encode()[target["start_byte"]:target["end_byte"]],
                             target["surface"].encode())

    def test_case_inflection_does_not_erase_exact_target(self):
        case = self.by_id["A01"]
        raw = report_for(case, selected=False)
        result = benchmark.evaluate(case, raw)
        self.assertEqual(result["semantic_diagnostic"], "PASS")
        self.assertIn("gold", result["observation"]["candidates"])

    def test_other_occurrence_cannot_supply_target_selection(self):
        case = self.by_id["D03"]
        raw = report_for(case, sense="spring")
        distractor = report_for(self.by_id["D04"], sense="eye")["diagnostic"]["occurrences"][0]
        raw["diagnostic"]["occurrences"].append(distractor)
        result = benchmark.evaluate(case, raw)
        self.assertEqual(result["observation"]["selected"], ["spring"])
        self.assertEqual(result["semantic_diagnostic"], "PASS")
        raw["diagnostic"]["occurrences"].pop(0)
        self.assertEqual(benchmark.evaluate(case, raw)["semantic_diagnostic"], "FAIL")

    def test_context_replay_is_not_accepted_on_identical_text(self):
        first, second = self.by_id["D01"], self.by_id["D02"]
        self.assertEqual(first["input"]["text"], second["input"]["text"])
        result = benchmark.evaluate(second, report_for(first))
        self.assertEqual(result["integrity"]["outcome"], "FAIL")
        checks = {check["name"]: check for check in result["checks"]}
        self.assertEqual(checks["target_context_identity"]["outcome"], "FAIL")

    def test_span_boolean_cannot_match_integer(self):
        case = self.by_id["E01"]
        raw = report_for(case)
        raw["diagnostic"]["occurrences"][0]["span"]["start_byte"] = True
        self.assertEqual(benchmark.evaluate(case, raw)["semantic_diagnostic"], "FAIL")

    def test_native_flag_does_not_count_as_positive_language(self):
        case = self.by_id["E01"]
        raw = report_for(case, selected=False)
        result = benchmark.evaluate(case, raw)
        summary = benchmark.summarize([result])
        self.assertEqual(summary["declared_native_checked_cases"]["numerator"], 1)
        self.assertEqual(summary["native_receipt_cases"]["numerator"], 0)
        self.assertEqual(summary["positive_selection"]["numerator"], 0)
        self.assertEqual(summary["strict_language_acceptances"], 0)
        self.assertEqual(result["semantic_diagnostic"], "FAIL")

    def test_unimplemented_scope_is_unmeasured_even_when_sense_matches(self):
        case = self.by_id["S04"]
        result = benchmark.evaluate(case, report_for(case))
        self.assertEqual(result["semantic_diagnostic"], "UNMEASURED")
        scopes = [check for check in result["checks"] if check["name"] == "acquired_scope"]
        self.assertEqual(scopes[0]["outcome"], "UNMEASURED")

    def test_boolean_false_cannot_be_integer_zero_authority(self):
        case = self.by_id["E01"]
        raw = report_for(case)
        raw["strict_language_accepted"] = 0
        self.assertEqual(benchmark.evaluate(case, raw)["authority"]["outcome"], "FAIL")

    def test_claim_label_without_bound_native_receipt_fails(self):
        case = self.by_id["E01"]
        raw = report_for(case)
        raw["claims"] = [{"kind": "A116_EXACT_INSTALLED_CANDIDATE_SET",
                          "authority": "KERNEL_CHECKED_CONDITIONAL", "binding": {},
                          "proof": {"kind": "NATIVE_LEAN_RECEIPT"}}]
        result = benchmark.evaluate(case, raw)
        self.assertEqual(result["authority"]["outcome"], "FAIL")
        self.assertEqual(result["observation"]["consistent_named_claim_count"], 0)

    def test_consistent_import_is_still_not_a_local_proof_execution(self):
        case = self.by_id["E01"]
        result = benchmark.evaluate(case, consistent_claim_fixture(case))
        self.assertEqual(result["authority"]["outcome"], "PASS")
        summary = benchmark.summarize([result])
        self.assertEqual(summary["consistent_named_claims"], 1)
        self.assertEqual(summary["locally_executed_named_claims"], 0)
        self.assertEqual(summary["native_receipt_cases"]["numerator"], 0)

    def test_boolean_cell_does_not_match_numeric_cell_even_with_rehashed_receipt(self):
        case = self.by_id["E01"]
        raw = consistent_claim_fixture(case)
        raw["occurrences"][0]["native_receipt"]["cells"] = [True]
        changed = benchmark.sha(benchmark.canonical(raw["occurrences"][0]["native_receipt"]).encode())
        raw["occurrences"][0]["response_sha256"] = changed
        raw["claims"][0]["binding"]["response_sha256"] = changed
        self.assertEqual(benchmark.evaluate(case, raw)["authority"]["outcome"], "FAIL")

    def test_boolean_candidate_count_is_rejected(self):
        case = self.by_id["E01"]
        raw = consistent_claim_fixture(case)
        raw["claims"][0]["candidate_count"] = True
        self.assertEqual(benchmark.evaluate(case, raw)["authority"]["outcome"], "FAIL")

    def test_duplicate_occurrences_or_claims_do_not_inflate_proof_counts(self):
        case = self.by_id["E01"]
        for key in ("occurrences", "claims"):
            raw = consistent_claim_fixture(case)
            raw[key].append(raw[key][0])
            self.assertEqual(benchmark.evaluate(case, raw)["authority"]["outcome"], "FAIL")
        raw = consistent_claim_fixture(case)
        raw["diagnostic"]["occurrences"].append(raw["diagnostic"]["occurrences"][0])
        self.assertEqual(benchmark.evaluate(case, raw)["authority"]["outcome"], "FAIL")

    def test_missing_native_with_zero_claims_cannot_pass_execution_gate(self):
        case = self.by_id["E01"]
        raw = report_for(case, selected=False)
        raw["native_checked"] = False
        raw["claims"] = []
        result = benchmark.evaluate(case, raw)
        self.assertEqual(result["authority"]["outcome"], "PASS")
        self.assertEqual(result["execution"]["outcome"], "FAIL")

    def test_outer_authority_cannot_contradict_inner_false_or_assert_motive(self):
        case = self.by_id["E01"]
        for key in ("all_arabic_complete", "world_truth_established", "motive_established"):
            raw = report_for(case)
            raw[key] = True
            self.assertEqual(benchmark.evaluate(case, raw)["authority"]["outcome"], "FAIL")
        raw = report_for(case)
        raw["lexical_surface_licensed"] = True
        self.assertEqual(benchmark.evaluate(case, raw)["authority"]["outcome"], "FAIL")

    def test_rejects_fabricated_completeness_and_world_truth(self):
        case = self.by_id["E01"]
        raw = report_for(case)
        raw["diagnostic"]["all_arabic_complete"] = True
        raw["diagnostic"]["world_truth_established"] = True
        raw["strict_language_accepted"] = True
        self.assertEqual(benchmark.evaluate(case, raw)["authority"]["outcome"], "FAIL")


if __name__ == "__main__":
    unittest.main()
