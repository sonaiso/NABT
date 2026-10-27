"""Independent construction controls and actual native receipt replay.

These cases exercise a declared fragment. Passing them is not evidence of
whole-language coverage, historical source truth, or acquired speaker intent.
Transport attacks are maintained independently in test_six_noun_adversarial.
"""
from hashlib import sha256
import json
import subprocess
import unittest
from unittest.mock import patch

from tools.linguistic_truth import six_noun
from tests._transport_native import require_native
from nabt import codec


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

    def test_documentary_link_failure_cannot_issue_a_claim(self):
        # A synthetic transport fixture isolates the post-replay documentary
        # membership check. This does not count as execution of native Lean.
        text = "جَاءَ أَبُو زَيْدٍ"
        request = {"source": {"id": "test:links", "revision": sha256(text.encode()).hexdigest(),
                              "text": text}, "context": "documentary guard fixture"}
        for passages in ([], "qatr_subject", ["missing_passage"], [True],
                         ["qatr_subject", "missing_passage"]):
            with self.subTest(passages=passages):
                fixture = six_noun._expected(request)
                fixture["node_trace"][0]["passage_ids"] = passages
                with patch.object(six_noun, "_native", return_value=(fixture, "0" * 64)):
                    result = six_noun.acquire_six_noun(text, source_id="test:links",
                                                     context=request["context"])
                self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
                self.assertEqual(result["reason"], "SIX_NOUN_DOCUMENTARY_LINK_NOT_IN_REVIEW")
                self.assertEqual(result["claims"], [])
                self.assertEqual(result["node_trace"], [])
                self.assertFalse(result["native_checked"])
                self.assertFalse(result["grammar_certified"])


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
                self.assertEqual(result["node_trace"], [])
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

    def test_each_native_node_binds_number_source_and_documentary_rule(self):
        result = six_noun.acquire_six_noun("مَرَرْتُ بِحَمِي عَمْرٍو",
                                         source_id="test:nodes", context="لا إثبات لواقعة")
        self.assertEqual(result["status"], "CHECKED_SIX_NOUN", result)
        self.assertEqual(result["node_trace"], result["native_receipt"]["node_trace"])
        self.assertEqual(result["node_trace"], result["claims"][0]["node_trace"])
        self.assertEqual([n["node_id"] for n in result["node_trace"]],
                         ["prefix", "noun", "complement", "idafa", "sentence"])
        known_passages = {p["id"] for p in six_noun._review()["passages"]}
        for node in result["node_trace"]:
            with self.subTest(node=node["node_id"]):
                self.assertEqual(node["source"], result["source"])
                self.assertEqual(node["context"], result["context"])
                self.assertEqual(node["scope"], "INSTALLED_EXACT_SPELLING_COMMON_LETTER_PROFILE")
                self.assertEqual(node["rule_source_review_sha256"], six_noun._REVIEW_SHA)
                self.assertTrue(node["passage_ids"])
                self.assertTrue(set(node["passage_ids"]).issubset(known_passages))
                self.assertEqual(list(codec.decode_number(int(node["output_number"]))), node["output_cells"])
                self.assertEqual(result["source"]["text"].encode()[node["start_byte"]:node["end_byte"]],
                                 node["raw"].encode())
        self.assertEqual(result["node_trace"][-1]["output_cells"], result["orthographic_bridge"]["cells"])
        self.assertEqual(result["node_trace"][-1]["output_number"], result["orthographic_bridge"]["number"])
        self.assertIn("Nabt.SixNounAcquisition.certificate_trace_nodes_licensed",
                      result["claims"][0]["proof"]["theorems"])

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
