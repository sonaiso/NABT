"""Input boundaries plus actual source replay/native conditional checking.

Parser fixtures below test tokenization only and never furnish authority to
the public acquisition path. Public semantic tests use the installed ledger.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.linguistic_truth import AcquisitionBudget, acquire
from tools.linguistic_truth.runtime import ROOT, _parse_clause, _tokens, _verify_native


class RawCueSyntax(unittest.TestCase):
    forms = {"اللفظ": {"اللفظ"}}
    senses = {"اللفظ": {
        "one": {"sense_id": "one", "forms": {"المعنى الأول"}},
        "two": {"sense_id": "two", "forms": {"المعنى الآخر"}}}}

    def parse(self, text):
        offsets = [len(text[:i].encode()) for i in range(len(text) + 1)]
        return _parse_clause(_tokens(text, 0, len(text), offsets), self.forms, self.senses)

    def test_complete_cue_and_real_utf8_sense_span(self):
        raw = "أَعْنِي بِاللَّفْظِ المَعْنَى الأَوَّلَ"
        parsed = self.parse(raw)
        self.assertEqual(parsed["expression"], "اللفظ")
        row = parsed["readings"][0][0]
        self.assertEqual(row["sense_id"], "one")
        self.assertEqual(raw.encode()[row["start"]:row["end"]].decode(), "المَعْنَى الأَوَّلَ")

    def test_conjunction_and_signed_cues_preserve_both(self):
        both = self.parse("أريد باللفظ المعنى الأول والمعنى الآخر")
        self.assertEqual({c["sense_id"] for c in both["readings"][0]}, {"one", "two"})
        signed = self.parse("أعني باللفظ المعنى الأول لا المعنى الأول")
        self.assertEqual([c["positive"] for c in signed["readings"][0]], [True, False])
        negative = self.parse("لا أعني باللفظ المعنى الأول")
        self.assertFalse(negative["readings"][0][0]["positive"])

    def test_same_occurrence_negative_reference(self):
        parsed = self.parse("أعني باللفظ المعنى الأول ولا أعني به المعنى الأول")
        self.assertEqual([c["positive"] for c in parsed["readings"][0]], [True, False])

    def test_recognized_prefix_does_not_hide_unparsed_suffix(self):
        for raw in ("أعني باللفظ المعنى الأول ربما", "ربما أعني باللفظ المعنى الأول",
                    "أعني باللفظ", "أعني باللفظ المعنى الأول إلا المعنى الآخر"):
            self.assertIsNone(self.parse(raw))

    def test_long_repeated_conjunction_is_resource_not_stack_overflow(self):
        text = "أعني باللفظ المعنى الأول" + " والمعنى الأول" * 1200
        self.assertLess(len(text.encode()), 65536)
        with self.assertRaises(OverflowError):
            self.parse(text)


class PublicInputBoundaries(unittest.TestCase):
    def test_invalid_scalar_utf8_empty_and_boolean_budgets(self):
        for raw in (True, 8, {}, [], "", "  ", "\ud800", b"\xff"):
            self.assertEqual(acquire(raw)["status"], "INVALID_INPUT")
        for value in (True, -1, 1.5, 1000001):
            with self.assertRaises(ValueError):
                AcquisitionBudget(max_readings=value)
        self.assertEqual(acquire("الأسد", budget={})["status"], "INVALID_INPUT")
        self.assertEqual(acquire("الأسد", context="\ud800")["status"], "INVALID_INPUT")

    def test_resource_budget_is_not_semantic_rejection(self):
        result = acquire("الأسد", budget=AcquisitionBudget(max_input_bytes=0))
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
        self.assertFalse(result["acquisition_scan_complete"])
        self.assertFalse(result["world_truth_established"])

    def test_missing_sources_never_become_empty_success(self):
        with tempfile.TemporaryDirectory() as root:
            result = acquire("أعني بالأسد الحيوان المفترس", root=Path(root))
        self.assertEqual(result["status"], "SOURCE_UNAVAILABLE")
        self.assertFalse(result["acquisition_scan_complete"])


class ActualInstalledSources(unittest.TestCase):
    def acquire(self, text, **kwargs):
        return acquire(text, profile_id="linguistic", **kwargs)

    @classmethod
    def setUpClass(cls):
        from tools.linguistic_truth.inventory import build_inventory
        cls.inventory = build_inventory()
        cls.native = ROOT / "formal/.lake/build/bin/linguisticTruth"
        if not cls.native.exists():
            raise unittest.SkipTest("optional native linguisticTruth checker not built")

    def test_vocalized_cue_retains_source_and_replayed_spelling_premises(self):
        raw = "أَعْنِي بِالْأَسَدِ الْحَيَوَانَ الْمُفْتَرِسَ"
        result = self.acquire(raw, subject="المتكلم", time="وقت الاختبار", context="حديث عن اللفظ")
        # v4 replays a separate stem/inflection review. The old semantic ledger
        # alone still cannot license these marks; the new evidence is explicit
        # and remains an acquisition premise outside the native semantic proof.
        self.assertEqual(result["status"], "COMPLETE")
        self.assertTrue(result["intended_sense_acquired"])
        self.assertTrue(result["acquired_premises"])
        self.assertIs(result["orthography_evidence"][0]["native_acquisition_proof"], False)
        self.assertTrue(result["native_checked"])
        self.assertEqual(result["source"]["raw_text"], raw)
        self.assertEqual(result["source"]["sha256"], hashlib.sha256(raw.encode()).hexdigest())
        occurrence = result["occurrences"][0]
        self.assertEqual(occurrence["span"]["raw_text"], "بِالْأَسَدِ")
        self.assertEqual(occurrence["supported_use_kinds"], ["literal"])
        self.assertGreaterEqual(len(occurrence["candidates"]), 2)
        for key in ("world_truth_established", "truth_of_claim_established", "empirical_validation_established",
                    "all_arabic_complete"):
            self.assertFalse(result[key])

    def test_figurative_guard_needs_exclusion_without_losing_acquired_intent(self):
        plain = self.acquire("أعني بالأسد الرجل الشجاع")["occurrences"][0]
        explicit = self.acquire("أعني بالأسد الرجل الشجاع لا الحيوان المفترس")["occurrences"][0]
        self.assertTrue(plain["selected_sense_ids"])
        self.assertEqual(plain["classification_status"], "UNKNOWN")
        self.assertEqual(explicit["supported_use_kinds"], ["figurative"])
        self.assertEqual(plain["selected_sense_ids"], explicit["selected_sense_ids"])
        self.assertEqual(len(plain["candidates"]), len(explicit["candidates"]))

    def test_homonym_no_context_and_both_senses_are_retained(self):
        missing = self.acquire("القرء")
        self.assertEqual(missing["status"], "UNKNOWN")
        self.assertEqual(len(missing["occurrences"][0]["candidates"]), 2)
        both = self.acquire("أعني بالقرء الطهر والحيض")["occurrences"][0]
        self.assertEqual(len(both["selected_sense_ids"]), 2)
        self.assertEqual(len(both["certified_sense_ids"]), 2)
        self.assertFalse(both["signed_conflict"])

    def test_conflict_not_explosion_and_negative_not_default(self):
        result = self.acquire("أعني بالأسد الحيوان المفترس لا الحيوان المفترس")
        self.assertEqual(result["status"], "CONFLICT")
        self.assertTrue(result["occurrences"][0]["signed_conflict"])
        self.assertFalse(result["occurrences"][0]["certified_sense_ids"])
        no_cue = self.acquire("رأيت الأسد")
        self.assertEqual(no_cue["status"], "UNKNOWN")
        self.assertFalse(no_cue["acquired_premises"])

    def test_quotation_suffix_and_negation_outside_language_remain_unknown(self):
        for raw in ("«أعني بالأسد الحيوان المفترس»", "أعني بالأسد الحيوان المفترس ربما",
                    "ليس صحيحا أن أعني بالأسد الحيوان المفترس", "أعني بالأسد، الحيوان المفترس"):
            result = self.acquire(raw)
            self.assertEqual(result["status"], "UNKNOWN", raw)
            self.assertFalse(result["acquired_premises"])
            self.assertTrue(result["unclassified_spans"])

    def test_quotation_scope_cannot_leak_across_separators(self):
        marks = [("«", "»"), ("[", "]"), ("'", "'"), ("‘", "’"), ("`", "`"), ("```", "```"), ("{", "}")]
        for left, right in marks:
            raw = left + "\nأعني بالأسد الحيوان المفترس\n" + right
            result = self.acquire(raw)
            self.assertEqual(result["status"], "UNKNOWN")
            self.assertFalse(result["acquired_premises"])

    def test_omitted_convention_keeps_all_profiles_pending(self):
        result = acquire("أعني بالصلاة الدعاء")
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIsNone(result["context"]["profile_id"])
        self.assertEqual(result["context"]["authority"], "UNESTABLISHED_CONVENTION")
        occurrence = result["occurrences"][0]
        self.assertGreaterEqual(len(occurrence["candidates"]), 2)
        self.assertFalse(occurrence["certified_sense_ids"])
        self.assertTrue(occurrence["selected_sense_ids"])
        self.assertTrue(all(r["support_status"] == "UNKNOWN_PREMISE" for r in occurrence["candidates"]))

    def test_all_occurrences_are_local_and_resource_limits_visible(self):
        raw = "أعني بالأسد الحيوان المفترس. أعني بالأسد الرجل الشجاع لا الحيوان المفترس"
        result = self.acquire(raw)
        self.assertEqual(len(result["occurrences"]), 2)
        self.assertNotEqual(result["occurrences"][0]["selected_sense_ids"], result["occurrences"][1]["selected_sense_ids"])
        for budget in (AcquisitionBudget(max_occurrences=0), AcquisitionBudget(max_readings=0),
                       AcquisitionBudget(max_native_scan=0)):
            bounded = self.acquire(raw, budget=budget)
            self.assertEqual(bounded["status"], "RESOURCE_EXHAUSTED")

    def test_unparsed_clause_clitics_remain_visible_to_occurrence_budget(self):
        text = "ذُكر الأسد. وتحدثتُ بالدابة."
        result = self.acquire(text)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(len(result["occurrences"]), 2)
        self.assertFalse(result["acquired_premises"])
        self.assertEqual(result["occurrences"][1]["span"]["raw_text"], "بالدابة")
        self.assertEqual(result["occurrences"][1]["surface_segmentations"][0]["normalized_prefix"], "ب")
        result = self.acquire(text, budget=AcquisitionBudget(max_occurrences=1))
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
        self.assertFalse(result["acquisition_scan_complete"])

    def test_supplied_authority_flags_are_not_an_api_input(self):
        with self.assertRaises(TypeError):
            acquire("الأسد", is_empirical_reality=True)
        with self.assertRaises(TypeError):
            acquire("الأسد", classification="literal")

    def test_native_unavailability_is_reported_without_invented_support(self):
        with patch("tools.linguistic_truth.runtime._verify_native", side_effect=OSError("missing checker")):
            result = self.acquire("أعني بالأسد الحيوان المفترس")
        self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
        self.assertTrue(result["intended_sense_acquired"])
        self.assertFalse(result["native_checked"])
        self.assertTrue(all(r["support_status"] == "UNKNOWN_PREMISE"
                            for o in result["occurrences"] for r in o["candidates"]))

    def test_invalid_native_response_and_late_row_mismatch_are_atomic(self):
        text = "أعني بالأسد الحيوان المفترس"
        valid = self.acquire(text)["occurrences"][0]["native_result"]
        variants = []
        for key, value in (("status", "MADE_UP"), ("law_id", "forged-law"),
                           ("world_truth_asserted", True)):
            bad = deepcopy(valid)
            bad[key] = value
            variants.append(bad)
        bad = deepcopy(valid)
        bad["rows"][-1]["candidate"]["intended_sense"] = "swapped-after-supported-row"
        variants.append(bad)
        bad = deepcopy(valid)
        citation = bad["rows"][0]["candidate"]["designation"]["citation"]
        citation["start_byte"] = float(citation["start_byte"])
        variants.append(bad)
        for response in variants:
            with patch("tools.linguistic_truth.runtime._verify_native", return_value=response):
                result = self.acquire(text)
            self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
            self.assertFalse(result["native_checked"])
            self.assertTrue(all(r["support_status"] == "UNKNOWN_PREMISE"
                                for o in result["occurrences"] for r in o["candidates"]))

    def test_native_limits_and_timeout_are_exhaustion(self):
        with self.assertRaises(ValueError):
            AcquisitionBudget(max_native_scan=4097)
        result = self.acquire("أعني بالأسد الحيوان المفترس" + " " * 17000)
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
        with patch("tools.linguistic_truth.runtime._verify_native",
                   side_effect=subprocess.TimeoutExpired("linguisticTruth", 60)):
            result = self.acquire("أعني بالأسد الحيوان المفترس")
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")

    def test_secondary_inventory_replay_failure_is_structured(self):
        from tools.linguistic_truth.inventory import build_inventory
        with patch("tools.linguistic_truth.inventory.build_inventory",
                   side_effect=[build_inventory(), ValueError("withdrawn on second replay")]):
            result = acquire("أعني بالأسد الحيوان المفترس")
        self.assertEqual(result["status"], "SOURCE_UNAVAILABLE")
        self.assertFalse(result["native_checked"])


if __name__ == "__main__":
    unittest.main()
