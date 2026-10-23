"""Adversarial contracts for new source properties, separate from frozen gold."""

from copy import deepcopy
from itertools import product
import unittest
from unittest.mock import patch

from nabt.errors import NabtError
from nabt import morphology as algebra
from nabt.morphology_reader import (read_morphology, verify_morphology,
                                    morphology_number, decode_morphology)


def dossier(lexeme="مِثَالٌ", *clauses):
    return f"قراءة «r1» للفظ «{lexeme}»:\n" + "\n".join(c + "." for c in clauses)


NOUN = "يدل على معنى مستقل غير مقترن بزمن"
VERB = "يدل على حدث مقترن بزمن بهيئته"


class MorphologyContracts(unittest.TestCase):
    def test_evidence_codec_rejects_aliases_and_roundtrips(self):
        for states in product(range(4), repeat=4):
            self.assertEqual(algebra.decode_evidence(algebra.evidence_number(states), 4), states)
        for operation in (lambda: algebra.evidence_number((True,)),
                          lambda: algebra.evidence_number([1]),
                          lambda: algebra.decode_evidence(True, 1),
                          lambda: algebra.decode_evidence(4, 1),
                          lambda: algebra.decode_evidence(0, True)):
            with self.assertRaises(NabtError):
                operation()

    def test_new_names_do_not_change_the_property_inference(self):
        outputs = []
        for word in ("زَيْدٌ", "نَوْفَلٌ", "عَلَمٌ", "جَدِيدٌ"):
            report = read_morphology(dossier(word, VERB, "فعله مضارع", "تتصل به نون الإناث"))
            outputs.append(report["readings"][0]["axes"]["construction"]["candidates"])
        self.assertEqual(outputs, [["built"]] * 4)
        # Source descriptions, including intentionally nonstandard examples,
        # are conditional premises. This is not external lexical attestation.

    def test_event_time_does_not_prove_form_time(self):
        report = read_morphology(dossier("ضَرْبُ", "يدل على حدث مقترن بزمن", "فعله مضارع"))
        self.assertEqual(report["readings"][0]["axes"]["kind"]["candidates"], ["noun", "verb"])
        self.assertEqual(report["readings"][0]["axes"]["kind"]["status"], "DEFER")

    def test_malformed_next_header_cannot_poison_prior_scope(self):
        text = dossier("رَجُلٌ", NOUN) + "\nقراءة «bad-id» للفظ «مَنْ»:\nيشبه الحرف."
        with self.assertRaises(NabtError) as caught:
            read_morphology(text)
        self.assertEqual(caught.exception.code, "MALFORMED_READING_HEADER")

    def test_unknown_clause_suspends_scope_and_blocks_partial_licence(self):
        text = dossier("نَهْرٌ", NOUN, "يسلم من شبه الحرف", "افترض أن ما سبق اقتباس", "يشبه الحرف")
        report = read_morphology(text)
        self.assertEqual(report["status"], "DEFER")
        reading = report["readings"][0]
        self.assertTrue(report["unscoped_clauses"])
        self.assertEqual(reading["axes"]["construction"]["status"], "DEFER")
        self.assertEqual(reading["axes"]["construction"]["candidates"], ["inflected"])
        self.assertFalse(any(e["property"] == "particle_resemblance" and e["value"] is True for e in reading["evidence"]))

    def test_qualified_adjective_pair_and_no_spelling_shortcut(self):
        positive = read_morphology(dossier("أَكْبَرُ", NOUN,
                                  "صفة أصلية على أفعل لا تلحق مؤنثها تاء التأنيث"))
        self.assertEqual(positive["readings"][0]["axes"]["diptote"]["candidates"], ["diptote"])
        missing = read_morphology(dossier("أَكْبَرُ", NOUN))
        self.assertEqual(missing["readings"][0]["axes"]["diptote"]["candidates"], ["diptote", "ordinary"])

    def test_ordinary_requires_explicit_negatives_and_named_residuals(self):
        absent = read_morphology(dossier("نَهْرٌ", NOUN))["readings"][0]["axes"]["diptote"]
        self.assertEqual(absent["status"], "DEFER")
        self.assertIn(["tanithAlif"], absent["residual"]["minimal_plans"])
        explicit = read_morphology(dossier("نَهْرٌ", NOUN, "ليس علما", "ليس وصفا",
                                          "ليس آخره ألف التأنيث", "ليس على صيغة منتهى الجموع"))
        self.assertEqual(explicit["readings"][0]["axes"]["diptote"]["candidates"], ["ordinary"])
        self.assertEqual(explicit["readings"][0]["axes"]["diptote"]["residual"]["minimal_plans"], [])

    def test_diptote_context_keeps_cause_and_never_invents_genitive_case(self):
        base = dossier("صَحْرَاءُ", NOUN, "يسلم من شبه الحرف", "آخره ألف التأنيث", "ليس مضافا")
        for clause, mark in (("لم تدخل عليه أل", "fatha"), ("دخلت عليه أل", "kasra")):
            report = read_morphology(base + "\n" + clause + ".")
            diptote = report["readings"][0]["axes"]["diptote"]
            self.assertEqual(diptote["candidates"], ["diptote"])
            self.assertEqual(diptote["genitive"]["candidates"], [mark])
            self.assertFalse(diptote["genitive"]["applied_to_occurrence"])
            self.assertIn("INDEPENDENT_GENITIVE_CASE_WITNESS", diptote["genitive"]["prerequisites"])
            self.assertEqual(report["facts"], [])

    def test_conflict_is_not_replaced_by_last_clause(self):
        for first, last in (("دخلت عليه أل", "لم تدخل عليه أل"), ("لم تدخل عليه أل", "دخلت عليه أل")):
            report = read_morphology(dossier("صَحْرَاءُ", NOUN, "آخره ألف التأنيث", first, last))
            self.assertEqual(report["status"], "CONFLICT")
            axis = report["readings"][0]["axes"]["diptote"]["genitive"]
            self.assertEqual(axis["status"], "CONFLICT")
            self.assertEqual(axis["candidates"], [])

    def test_cause_property_is_not_nominal_derivation(self):
        report = read_morphology(dossier("أَحْمَدُ", NOUN, "علم على وزن يختص بالفعل أو يغلب فيه"))
        axes = report["readings"][0]["axes"]
        self.assertEqual(axes["diptote"]["candidates"], ["diptote"])
        self.assertEqual(axes["nominal_semantics"]["status"], "DEFER")
        self.assertIn("ETYMOLOGICAL_ROOT_DERIVATION", report["readings"][0]["unimplemented_axes"])

    def test_built_noun_cannot_borrow_diptote_class_from_conditional_cause(self):
        report = read_morphology(dossier("سَلْمَى", NOUN, "يشبه الحرف", "آخره ألف التأنيث"))
        axis = report["readings"][0]["axes"]["diptote"]
        self.assertEqual(axis["cause_prediction"]["candidates"], ["diptote"])
        self.assertEqual(axis["status"], "OUT_OF_DOMAIN")
        self.assertIn("LICENSED_INFLECTED_NOUN", axis["prerequisites"])

    def test_unknown_scope_blocks_nested_genitive_class_approval(self):
        text = dossier("صَحْرَاءُ", NOUN, "يسلم من شبه الحرف", "آخره ألف التأنيث",
                       "دخلت عليه أل", "سياق لا تفسره النسخة")
        axis = read_morphology(text)["readings"][0]["axes"]["diptote"]["genitive"]
        self.assertEqual(axis["candidates"], ["kasra"])
        self.assertEqual(axis["status"], "DEFER")
        self.assertIn("COMPLETE_SOURCE_INTERPRETATION", axis["prerequisites"])

    def test_missing_installed_table_defers_replay(self):
        text = dossier("كَتَبَ", VERB, "فعله ماض")
        report = read_morphology(text)
        with patch("nabt.morphology.files") as mock_files:
            mock_files.return_value.joinpath.return_value.read_bytes.side_effect = FileNotFoundError()
            replay = verify_morphology(report)
            self.assertEqual(replay["status"], "DEFER")
            self.assertEqual(replay["code"], "INSTALLED_CONTRACT_FAILED")

    def test_replay_binds_complete_report_source_scope_and_reading(self):
        text = dossier("كَتَبَ", VERB, "فعله ماض")
        report = read_morphology(text, source_id="book", scope="s1")
        self.assertTrue(verify_morphology(report, text=text, source_id="book", scope="s1")["valid"])
        for changed in (None, [], {}, {**report, "raw_text": text + " "},
                        {**report, "readings": []}, {**report, "scope": "s2"},
                        {**report, "source_id": "other"}):
            self.assertFalse(verify_morphology(changed, text=text, source_id="book", scope="s1")["valid"])
        tampered = deepcopy(report)
        tampered["readings"][0]["evidence"][0]["reading_id"] = "r2"
        self.assertFalse(verify_morphology(tampered)["valid"])

    def test_reversible_number_replays_and_rejects_boolean(self):
        report = read_morphology(dossier("كَتَبَ", VERB, "فعله ماض"))
        self.assertEqual(decode_morphology(morphology_number(report)), report)
        with self.assertRaises(NabtError):
            decode_morphology(True)
        with patch("nabt.morphology_reader.EXPECTED_POLICY_SHA256", "0" * 64):
            replay = verify_morphology(report)
            self.assertFalse(replay["valid"])
            self.assertEqual(replay["status"], "DEFER")


if __name__ == "__main__":
    unittest.main()
