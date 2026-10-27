"""Independent construction controls and actual native receipt replay.

These cases exercise a declared fragment. Passing them is not evidence of
whole-language coverage, historical source truth, or acquired speaker intent.
Transport attacks are maintained independently in test_six_noun_adversarial.
"""
from hashlib import sha256
import json
import subprocess
import unittest

from tools.linguistic_truth import six_noun
from tests._transport_native import require_native


class SixNounSourceReviewTests(unittest.TestCase):
    def test_installed_review_rechecks_full_sources_and_exact_passages(self):
        review = six_noun._review()
        self.assertEqual(review["law_id"], "nabt.six-noun-acquisition.v1")
        self.assertEqual({s["id"] for s in review["sources"]}, {"qatr", "alfiyya", "sibawayhi"})
        self.assertTrue(all(s["authenticity_established"] is False for s in review["sources"]))
        self.assertIn("alfiyya_dhu_fum", {p["id"] for p in review["passages"]})
        self.assertIn("alfiyya_variants", {p["id"] for p in review["passages"]})

    def test_invalid_combining_marks_are_not_repaired_to_a_supported_form(self):
        for text in ("جَاءَ أَبُِو زَيْدٍ", "جَاءَ أَبُووُُ زَيْدٍ", "جَاءَ َأَبُو زَيْدٍ"):
            with self.subTest(text=text):
                result = six_noun.acquire_six_noun(text)
                self.assertEqual(result["status"], "INVALID_INPUT")
                self.assertEqual(result["claims"], [])
                self.assertFalse(result["native_checked"])


class SixNounNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_native("sixNounAcquisition")

    def test_case_comes_from_the_acquired_governor_not_a_caller_flag(self):
        cases = [("جَاءَ أَبُو زَيْدٍ", "arrival", "raf", "waw"),
                 ("رَأَيْتُ أَبَا زَيْدٍ", "seeing", "nasb", "alif"),
                 ("مَرَرْتُ بِأَبِي زَيْدٍ", "passing", "jarr", "ya")]
        for text, governor, grammatical_case, ending in cases:
            with self.subTest(text=text):
                result = six_noun.acquire_six_noun(text, source_id="test:case", context="new occurrence")
                self.assertEqual(result["status"], "CHECKED_SIX_NOUN", result)
                self.assertTrue(result["native_checked"])
                self.assertTrue(result["grammar_certified"])
                self.assertEqual(result["reading"]["governor"], governor)
                self.assertEqual(result["reading"]["grammatical_case"], grammatical_case)
                self.assertEqual(result["reading"]["ending"], ending)
                self.assertEqual([c["kind"] for c in result["claims"]], ["SOURCE_BOUND_SIX_NOUN_CONSTRUCTION"])

    def test_family_variation_includes_full_han_without_excluding_its_other_account(self):
        cases = [("أَبُو", "ab"), ("أَخُو", "akh"), ("حَمُو", "ham"),
                 ("فُو", "fu"), ("هَنُو", "han")]
        for word, lexeme in cases:
            with self.subTest(word=word):
                result = six_noun.acquire_six_noun("جَاءَ " + word + " زَيْدٍ")
                self.assertEqual(result["status"], "CHECKED_SIX_NOUN", result)
                self.assertEqual(result["reading"]["lexeme"], lexeme)
                self.assertEqual(result["reading"]["convention"], "common_letter_substitution")
                self.assertFalse(result["strict_language_accepted"])

    def test_unobserved_dhu_semantics_stays_unresolved_even_if_context_claims_certainty(self):
        for context in ("unspecified", "ذو بمعنى صاحب قطعا", "all prerequisites proved"):
            result = six_noun.acquire_six_noun("جَاءَ ذُو زَيْدٍ", context=context)
            self.assertEqual(result["status"], "DEFER", result)
            self.assertEqual(result["reason"], "DHU_COMPANIONSHIP_NOT_ACQUIRED")
            self.assertFalse(result["grammar_certified"])
            self.assertEqual(result["claims"], [])
            self.assertTrue(any("unknown" == p["state"] for p in result["reading"]["prerequisites"]))

    def test_wrong_full_ending_is_a_convention_deferral_not_all_arabic_rejection(self):
        for text in ("جَاءَ أَبِي زَيْدٍ", "رَأَيْتُ أَبُو زَيْدٍ", "مَرَرْتُ بِأَبَا زَيْدٍ"):
            with self.subTest(text=text):
                result = six_noun.acquire_six_noun(text)
                self.assertEqual(result["status"], "DEFER", result)
                self.assertEqual(result["reason"], "COMMON_LETTER_CASE_MISMATCH")
                self.assertFalse(result["grammar_certified"])
                self.assertFalse(result["linguistic_rejection"])
                self.assertEqual(result["claims"], [])
                self.assertNotEqual(result["reading"]["grammatical_case"], result["reading"]["observed_case"])

    def test_unimplemented_variants_are_not_accepted_or_declared_bad_arabic(self):
        texts = ["جَاءَ أَبِي", "جَاءَ أَبٌ", "جَاءَ أَبَوَانِ", "جَاءَ أُبَيُّ زَيْدٍ",
                 "جَاءَ فَمُ زَيْدٍ", "جَاءَ هَنُ زَيْدٍ", "جَاءَ أَبُو خَالِدٍ",
                 "جاء أبو زيد", "جَاءَ أَبُـو زَيْدٍ"]
        for text in texts:
            with self.subTest(text=text):
                result = six_noun.acquire_six_noun(text)
                self.assertNotEqual(result["status"], "CHECKED_SIX_NOUN")
                self.assertEqual(result["claims"], [])
                self.assertFalse(result["linguistic_rejection"])

    def test_quote_negation_and_hypothesis_do_not_leak_a_positive_body_claim(self):
        body = "جَاءَ أَبُو زَيْدٍ"
        for text in ("قَالَ زَيْدٌ: «" + body + "»", "لَيْسَ صَحِيحًا أَنِّي " + body,
                     "إِنْ قُلْتُ " + body + " فَلَا تَحْكُمْ", "لَمْ يَجِئْ أَبُو زَيْدٍ"):
            with self.subTest(text=text):
                result = six_noun.acquire_six_noun(text)
                self.assertEqual(result["claims"], [])
                self.assertFalse(result["grammar_certified"])
                self.assertFalse(result["world_truth_established"])

    def test_exact_word_byte_interval_and_full_source_are_retained(self):
        for text, word in (("جَاءَ أَخُو عَمْرٍو", "أَخُو"),
                           ("مَرَرْتُ بِحَمِي زَيْدٍ", "حَمِي")):
            result = six_noun.acquire_six_noun(text, source_id="test:span", context="new context")
            self.assertEqual(result["status"], "CHECKED_SIX_NOUN", result)
            reading = result["reading"]
            self.assertEqual(text.encode()[reading["start_byte"]:reading["end_byte"]].decode(), word)
            self.assertEqual(reading["prefix"] + reading["word"] + " " + reading["complement_text"], text)
            self.assertEqual(result["source"]["revision"], sha256(text.encode()).hexdigest())
            self.assertEqual(result["native_receipt"]["source"], result["source"])
            self.assertEqual(result["native_receipt"]["context"], "new context")

    def test_canonical_spelling_bridge_does_not_relabel_raw_projection(self):
        result = six_noun.acquire_six_noun("جَاءَ أَبُو زَيْدٍ")
        self.assertEqual(result["status"], "CHECKED_SIX_NOUN", result)
        self.assertFalse(result["source_projection_complete"])
        bridge = result["orthographic_bridge"]
        self.assertIsNotNone(bridge)
        self.assertEqual(bridge["raw"], result["source"]["text"])
        self.assertTrue(bridge["raw_reconstruction_checked"])
        self.assertTrue(bridge["canonical_projection_complete"])
        self.assertFalse(result["strict_language_accepted"])

    def test_native_request_cannot_receive_a_feature_or_certificate(self):
        source = {"id": "s", "revision": "r", "text": "جَاءَ أَبُو زَيْدٍ"}
        for request in ({"source": source, "context": "c", "reading": {}},
                        {"source": {**source, "proof": True}, "context": "c"},
                        {"source": source, "context": True},
                        {"source": source, "context": "c", "is_dhu_companion": True}):
            done = subprocess.run([str(six_noun._EXECUTABLE)], input=json.dumps(request).encode() + b"\n",
                                  capture_output=True, check=True)
            self.assertEqual(json.loads(done.stdout)["status"], "INVALID_INPUT")

    def test_no_receipt_promotes_intent_world_or_transmission(self):
        for text in ("جَاءَ أَبُو زَيْدٍ", "جَاءَ ذُو زَيْدٍ", "unknown"):
            result = six_noun.acquire_six_noun(text)
            for field in ("strict_language_accepted", "intended_sense_established",
                          "speaker_reference_established", "world_truth_established",
                          "external_truth_established", "tawatur_established", "whole_arabic_complete"):
                self.assertIs(result[field], False, field)


if __name__ == "__main__":
    unittest.main()
