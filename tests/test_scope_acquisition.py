"""Scope acquisition tests authored independently of the parser recurrence.

The contract measures exact envelope boundaries separately from the diagnostic
meaning of a quoted body. No native invocation is counted as semantic success.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools.linguistic_truth import scopes


BODY = "أَعْنِي بِالْعَيْنِ عَيْنَ الْمَاءِ"
QUOTE = "قَالَ زَيْدٌ: «" + BODY + "»."
NEGATED = "لَيْسَ صَحِيحًا أَنِّي " + BODY + "."
CONDITIONAL = "إِنْ قُلْتُ " + BODY + " فَلَا تَفْهَمِ الْعَيْنَ الْبَاصِرَةَ."


class ScopePortable(unittest.TestCase):
    def test_direct_api_requires_installed_foundation_before_any_native_work(self):
        with patch.object(scopes.foundation, "require_foundation", side_effect=RuntimeError("blocked")):
            with self.assertRaisesRegex(RuntimeError, "blocked"):
                scopes.acquire_scope(QUOTE)

    def test_invalid_input_is_not_a_scope_deferral_or_false_receipt(self):
        cases = [(None, {}), (True, {}), (b"\xff", {}), ("", {}), ("\ud800", {}),
                 (QUOTE, {"context": True}), (QUOTE, {"source_id": 1}),
                 (QUOTE, {"profile_id": " "})]
        for text, kwargs in cases:
            with self.subTest(text=repr(text), kwargs=kwargs):
                result = scopes.acquire_scope(text, **kwargs)
                self.assertEqual(result["status"], "INVALID_INPUT")
                self.assertFalse(result["native_checked"])
                self.assertEqual(result["claims"], [])

    def test_input_limit_is_resource_status_not_linguistic_rejection(self):
        result = scopes.acquire_scope("سَ" * 5000)
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
        self.assertEqual(result["claims"], [])

    def test_foundation_piece_limit_is_not_invalid_arabic(self):
        # This fits the outer byte budget but exceeds the independent
        # representation-piece budget. No native checker is needed to classify
        # the exhausted resource correctly.
        result = scopes.acquire_scope("قَالَ زَيْدٌ: «" + "ب" * 4000 + "»")
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
        self.assertEqual(result["reason"], "RESOURCE_LIMIT")
        self.assertFalse(result["native_checked"])
        self.assertEqual(result["claims"], [])

    def test_missing_native_checker_never_grants_scope_claim(self):
        with patch.object(scopes, "_EXECUTABLE", Path("/nonexistent/nabt/scopeAcquisition")):
            result = scopes.acquire_scope(QUOTE)
        self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
        self.assertFalse(result["native_checked"])
        self.assertEqual(result["claims"], [])

    def test_source_review_is_replayed_not_caller_attested(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.json"
            path.write_bytes(scopes._REVIEW.read_bytes() + b" ")
            with patch.object(scopes, "_REVIEW", path):
                result = scopes.acquire_scope(QUOTE)
        self.assertEqual(result["status"], "SOURCE_UNAVAILABLE")
        self.assertEqual(result["claims"], [])

    def test_caller_cannot_supply_scope_speaker_or_native_authority(self):
        for key in ("scope", "speaker_id", "quoted_speaker_id", "native_checked", "checker", "receipt"):
            with self.subTest(key=key):
                with self.assertRaises(TypeError):
                    scopes.acquire_scope(QUOTE, **{key: True})

    def test_strict_json_rejects_duplicate_or_nonfinite_claim_fields(self):
        for raw in ('{"native_checked":false,"native_checked":true}', '{"x":NaN}'):
            with self.assertRaises(ValueError):
                scopes._parse_json(raw)


class ScopeNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not scopes._EXECUTABLE.is_file():
            raise unittest.SkipTest("native scopeAcquisition not built")

    def test_quote_extracts_actual_original_byte_interval(self):
        result = scopes.acquire_scope(QUOTE, source_id="test:quote", context="narrator")
        self.assertEqual(result["status"], "CHECKED_SCOPE_ENVELOPE")
        self.assertTrue(result["native_checked"])
        envelope = result["envelope"]
        self.assertEqual(envelope["kind"], "quoted_speaker")
        self.assertEqual(envelope["speaker_label"], "زَيْدٌ")
        self.assertEqual((envelope["start_byte"], envelope["end_byte"]), (27, 94))
        self.assertEqual(QUOTE.encode()[27:94].decode(), BODY)
        self.assertEqual(envelope["prefix"] + envelope["body"] + envelope["suffix"], QUOTE)
        self.assertEqual(result["source"]["revision"], sha256(QUOTE.encode()).hexdigest())
        self.assertEqual(result["claims"][0]["id"], "EXACT_SCOPE_ENVELOPE")
        self.assertFalse(result["source_projection_complete"])
        self.assertFalse(result["strict_language_accepted"])

    def test_quoted_meaning_is_attributed_without_narrator_or_referent_promotion(self):
        result = scopes.acquire_scope(QUOTE, context="speaker:narrator")
        chosen = [row for row in result["selected_senses_scoped"] if row["sense_ids"]]
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0]["sense_ids"], ["ayn_spring"])
        self.assertEqual(chosen[0]["speaker_label"], "زَيْدٌ")
        self.assertEqual((chosen[0]["parent_start_byte"], chosen[0]["parent_end_byte"]), (42, 64))
        self.assertFalse(chosen[0]["projects_to_narrator"])
        self.assertFalse(result["intended_sense_kernel_proved"])
        self.assertFalse(result["speaker_reference_established"])
        self.assertFalse(result["world_truth_established"])
        self.assertNotIn("INTENDED_SENSE", {c["id"] for c in result["claims"]})

    def test_different_speakers_and_body_meanings_do_not_share_identity(self):
        texts = ["قَالَ عَمْرٌو: «أَعْنِي بِالْعَيْنِ الْعَيْنَ الْبَاصِرَةَ»",
                 "قَالَ خَالِدٌ: «لَا أَعْنِي بِالْعَيْنِ عَيْنَ الْمَاءِ»"]
        results = [scopes.acquire_scope(text) for text in texts]
        self.assertEqual([r["envelope"]["speaker_label"] for r in results], ["عَمْرٌو", "خَالِدٌ"])
        self.assertEqual([s for row in results[0]["selected_senses_scoped"] for s in row["sense_ids"]], ["ayn_eye"])
        self.assertEqual([s for row in results[1]["selected_senses_scoped"] for s in row["excluded_sense_ids"]], ["ayn_spring"])
        self.assertNotEqual(results[0]["claims"][0]["request_sha256"], results[1]["claims"][0]["request_sha256"])

    def test_negation_and_hypothesis_are_acquired_without_executing_positive_body_reader(self):
        with patch("tools.linguistic_truth.runtime.acquire", side_effect=AssertionError("must remain scoped")):
            for text, expected in ((NEGATED, "negated_embedding"), (CONDITIONAL, "hypothetical")):
                with self.subTest(expected=expected):
                    result = scopes.acquire_scope(text)
                    self.assertEqual(result["envelope"]["kind"], expected)
                    self.assertEqual(result["envelope"]["body"], BODY)
                    self.assertEqual(result["selected_senses_scoped"], [])
                    self.assertIsNone(result["quoted_reading"])
                    self.assertFalse(result["envelope"]["projects_to_narrator"])

    def test_opaque_unmarked_body_retains_partial_projection_without_syntax_claim(self):
        result = scopes.acquire_scope("قَالَ زيد: «أعني بالعين عين الماء»")
        self.assertEqual(result["status"], "CHECKED_SCOPE_ENVELOPE")
        self.assertFalse(result["source_projection_complete"])
        self.assertFalse(result["native_receipt"]["body_syntax_established"])
        self.assertFalse(result["strict_language_accepted"])

    def test_nonascii_space_in_opaque_label_is_preserved_not_normalized(self):
        # The installed envelope grammar separates labels with ASCII space.
        # A different scalar remains part of an opaque label, with partial
        # source representation and no reference/syntax authority.
        label = "زَيْدٌ\u00a0عَمْرٌو"
        result = scopes.acquire_scope("قَالَ " + label + ": «" + BODY + "»")
        self.assertEqual(result["status"], "CHECKED_SCOPE_ENVELOPE")
        self.assertEqual(result["envelope"]["speaker_label"], label)
        self.assertFalse(result["source_projection_complete"])
        self.assertFalse(result["speaker_reference_established"])

    def test_nested_quotes_and_second_sentences_cannot_escape_scope(self):
        cases = [QUOTE + " أَعْنِي بِالْعَيْنِ الْعَيْنَ الْبَاصِرَةَ",
                 "قَالَ زَيْدٌ: «قَالَ عَمْرٌو: «" + BODY + "»».",
                 "قَالَ زَيْدٌ: «" + BODY + ". أَعْنِي بِالْعَيْنِ الْعَيْنَ الْبَاصِرَةَ».",
                 "قَالَ زَيْدٌ عَمْرٌو: «" + BODY + "».",
                 QUOTE.replace("».. ", "»") + ".", QUOTE.replace("«", "“")]
        for text in cases:
            with self.subTest(text=text):
                result = scopes.acquire_scope(text)
                self.assertEqual(result["status"], "OUTSIDE_EXECUTED_SCOPE")
                self.assertEqual(result["claims"], [])
                self.assertEqual(result["selected_senses_scoped"], [])

    def test_missing_or_moved_boundaries_and_empty_body_never_license_envelope(self):
        for text in (QUOTE.replace("«", ""), QUOTE.replace(": «", ":«"),
                     "قَالَ زَيْدٌ: «»", "قَالَ زَيْدٌ: « " + BODY + "»",
                     "قَالَ زَيْدٌ: «" + BODY + " »", BODY,
                     "إن قلت " + BODY + " فلا تفهم العين الباصرة"):
            with self.subTest(text=text):
                result = scopes.acquire_scope(text)
                self.assertEqual(result["status"], "OUTSIDE_EXECUTED_SCOPE")
                self.assertEqual(result["claims"], [])

    def test_changed_observed_mark_is_not_normalized_to_the_wrapper(self):
        for text in (QUOTE.replace("قَالَ", "قَالِ"), NEGATED.replace("لَيْسَ", "لَيْسُ"),
                     CONDITIONAL.replace("إِنْ", "إِنَ")):
            result = scopes.acquire_scope(text)
            self.assertEqual(result["status"], "OUTSIDE_EXECUTED_SCOPE")

    def test_native_request_cannot_supply_candidate_structure(self):
        source = {"id": "s", "revision": "r", "text": QUOTE}
        for request in ({"source": source, "context": "c", "envelope": {}},
                        {"source": {**source, "native_checked": True}, "context": "c"},
                        {"source": source, "context": True}):
            done = subprocess.run([str(scopes._EXECUTABLE)], input=json.dumps(request) + "\n",
                                  text=True, capture_output=True, check=True)
            self.assertEqual(json.loads(done.stdout)["status"], "INVALID_INPUT")

    def test_native_receipt_all_fields_and_integer_types_are_bound(self):
        checked = scopes.acquire_scope(QUOTE)["native_receipt"]
        variants = []
        for path, value in ((["context"], "forged"), (["source", "text"], BODY),
                            (["envelope", "start_byte"], 27.0),
                            (["envelope", "body"], "عَيْن"),
                            (["strict_language_accepted"], 0),
                            (["envelope", "projects_to_narrator"], True),
                            (["envelope", "speaker_label"], "عَمْرٌو")):
            variant = deepcopy(checked)
            target = variant
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            variants.append(json.dumps(variant, ensure_ascii=False).encode() + b"\n")
        variants.append(b'{"status":"FAILED",' + json.dumps(checked, ensure_ascii=False).encode()[1:] + b"\n")
        for stdout in variants:
            with self.subTest(stdout=stdout[:90]):
                with patch.object(scopes.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=stdout)):
                    result = scopes.acquire_scope(QUOTE)
                self.assertEqual(result["status"], "VERIFICATION_UNAVAILABLE")
                self.assertEqual(result["claims"], [])

    def test_native_timeout_is_resource_status_and_has_no_claim(self):
        with patch.object(scopes.subprocess, "run", side_effect=subprocess.TimeoutExpired("scopeAcquisition", 30)):
            result = scopes.acquire_scope(QUOTE)
        self.assertEqual(result["status"], "RESOURCE_EXHAUSTED")
        self.assertEqual(result["claims"], [])


if __name__ == "__main__":
    unittest.main()
