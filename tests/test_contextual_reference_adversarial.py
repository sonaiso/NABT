"""Independent attacks on initial occurrence licences, not reference gold.

The nonce predicate and declared entities here are authored protocol controls.
No success is evidence of parsing a full sentence or its external truth.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def explicit_context():
    return {"entities": [
                {"id": "speaker_a", "name": "رَاءٌ", "gender": "masculine", "number": "singular", "kind": "person"},
                {"id": "speaker_b", "name": "جِيمٌ", "gender": "masculine", "number": "singular", "kind": "person"}],
            "speaker": "speaker_a", "addressee": "speaker_b", "closed_reference_scope": True,
            "deixis": [{"form": "هَذَا", "entity_ids": ["speaker_a", "speaker_b"]}]}


def specimen(text="أَنَا زَظَغٌ."):
    return {"text": text, "context": explicit_context()}


class ContextualCollectorAttacks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools import contextual_reference
        cls.adapter = contextual_reference
        if not cls.adapter.NATIVE.is_file():
            raise unittest.SkipTest("Build contextualReference for native occurrence licences")
        if not cls.adapter.loader.DEFAULT_SOURCE.is_file():
            raise unittest.SkipTest("Fetch the pinned QAC source before native occurrence tests")

    def assert_scope_preserved(self, result):
        scope = result["scope"]
        for key in ("sentence_syntax_promoted", "sentence_readings_promoted", "context_truth_established",
                    "world_truth_established", "hidden_motive_established", "whole_arabic_complete"):
            self.assertIs(scope[key], False, key)
        self.assertEqual(scope["tawatur_status"], "UNKNOWN")

    def assert_not_resolved(self, result):
        self.assert_scope_preserved(result)
        reference = result.get("reference")
        if reference is not None:
            self.assertIsNone(reference.get("bound_entity_id"))
            self.assertNotEqual(reference.get("status"), "RESOLVED")

    def test_nonce_predicate_allows_only_the_independent_occurrence_claim(self):
        result = self.adapter.execute_request(specimen())
        self.assertIs(result["native_checked"], True)
        self.assertIs(result["certificate_checked"], True)
        reference = result["reference"]
        self.assertEqual(reference["surface"], "أَنَا")
        self.assertEqual(reference["status"], "RESOLVED")
        self.assertEqual(reference["bound_entity_id"], "speaker_a")
        self.assert_scope_preserved(result)
        for key in ("syntax", "readings", "asserted_claims"):
            self.assertFalse(result.get(key))

    def test_same_text_new_speaker_changes_binding_and_context_identity(self):
        one = self.adapter.execute_request(specimen())
        changed = specimen()
        changed["context"]["speaker"] = "speaker_b"
        two = self.adapter.execute_request(changed)
        self.assertEqual(one["reference"]["bound_entity_id"], "speaker_a")
        self.assertEqual(two["reference"]["bound_entity_id"], "speaker_b")
        self.assertNotEqual(one["context_sha256"], two["context_sha256"])
        self.assertNotEqual(one["input_sha256"], two["input_sha256"])
        self.assertNotEqual(one["reference"]["reference_id"], two["reference"]["reference_id"])
        self.assert_scope_preserved(two)

    def test_ambiguous_deixis_never_chooses_first_context_entity(self):
        request = specimen("هَذَا زَظَغٌ.")
        result = self.adapter.execute_request(request)
        self.assertIs(result["native_checked"], True)
        self.assertEqual(result["reference"]["status"], "AMBIGUOUS")
        self.assertIsNone(result["reference"]["bound_entity_id"])
        self.assertEqual(set(result["reference"]["candidate_entity_ids"]), {"speaker_a", "speaker_b"})
        request["context"]["entities"].reverse()
        request["context"]["deixis"][0]["entity_ids"].reverse()
        reverse = self.adapter.execute_request(request)
        self.assertEqual(reverse["reference"]["status"], "AMBIGUOUS")
        self.assertEqual(set(reverse["reference"]["candidate_entity_ids"]), {"speaker_a", "speaker_b"})
        self.assert_scope_preserved(reverse)

    def test_unknown_competitor_is_not_dropped_to_fabricate_a_unique_referent(self):
        request = specimen("هَذَا زَظَغٌ.")
        request["context"]["entities"][1]["gender"] = "unknown"
        result = self.adapter.execute_request(request)
        self.assert_not_resolved(result)
        self.assertIn("speaker_b", result["reference"]["candidate_entity_ids"])

    def test_missing_participant_does_not_fall_back_to_the_only_entity(self):
        request = specimen()
        request["context"].pop("speaker")
        result = self.adapter.execute_request(request)
        self.assert_not_resolved(result)
        if result.get("reference"):
            self.assertEqual(result["reference"]["candidate_entity_ids"], [])

    def test_quotes_and_noninitial_occurrences_cannot_borrow_outer_speaker(self):
        for text in ("«أَنَا زَظَغٌ».", "قَالَ رَاءٌ: «أَنَا زَظَغٌ».",
                     "لَمْ يَقُلْ رَاءٌ: «أَنَا زَظَغٌ».", "زَظَغٌ أَنَا."):
            with self.subTest(text=text):
                self.assert_not_resolved(self.adapter.execute_request(specimen(text)))

    def test_whitespace_prefix_is_allowed_but_glued_or_altered_forms_are_not(self):
        good = self.adapter.execute_request(specimen(" \t\nأَنَا زَظَغٌ."))
        self.assertEqual(good["reference"]["bound_entity_id"], "speaker_a")
        self.assertIs(good["native_checked"], True)
        for text in ("أَنَازَظَغٌ.", "أَنَّا زَظَغٌ.", "أَنَا\u200d زَظَغٌ.", "ﺃَنَا زَظَغٌ."):
            with self.subTest(text=text):
                self.assert_not_resolved(self.adapter.execute_request(specimen(text)))

    def test_arbitrary_author_and_claimed_root_total_do_not_grant_a_licence(self):
        for field, value in (("LexicalCertificate", {"author": "سيبويه", "all_roots": True}),
                             ("author", "ابن منظور"), ("root_count", 5000),
                             ("reference_id", "C01–C05"), ("native_checked", True)):
            request = specimen()
            request[field] = value
            with self.subTest(field=field):
                result = self.adapter.execute_request(request)
                self.assertIs(result["native_checked"], False)
                self.assert_not_resolved(result)

    def test_duplicate_context_ids_and_non_boolean_scope_are_invalid(self):
        request = specimen()
        request["context"]["entities"].append(deepcopy(request["context"]["entities"][0]))
        result = self.adapter.execute_request(request)
        self.assertIs(result["native_checked"], False)
        self.assert_not_resolved(result)
        for value in (0, 1, "true", None):
            request = specimen()
            request["context"]["closed_reference_scope"] = value
            with self.subTest(value=value):
                result = self.adapter.execute_request(request)
                self.assertIs(result["native_checked"], False)
                self.assert_not_resolved(result)

    def test_missing_native_never_upgrades_python_acquisition_to_proof(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(self.adapter, "NATIVE", Path(temp) / "missing"):
            result = self.adapter.execute_request(specimen())
        self.assertIs(result["native_checked"], False)
        self.assertIs(result["certificate_checked"], False)
        self.assert_not_resolved(result)

    def test_changed_or_missing_original_corpus_does_not_accept_a_claimed_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "qac.txt"
            path.write_text("author=سيبويه; root_count=5000; verified=true", encoding="utf-8")
            with patch.object(self.adapter.loader, "DEFAULT_SOURCE", path):
                result = self.adapter.execute_request(specimen())
            self.assertIs(result["native_checked"], False)
            self.assert_not_resolved(result)
            path.unlink()
            with patch.object(self.adapter.loader, "DEFAULT_SOURCE", path):
                missing = self.adapter.execute_request(specimen())
            self.assertIs(missing["native_checked"], False)
            self.assert_not_resolved(missing)


class ContextualNativeAdversaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools import contextual_reference
        cls.adapter = contextual_reference
        if not cls.adapter.NATIVE.is_file() or not cls.adapter.loader.DEFAULT_SOURCE.is_file():
            raise unittest.SkipTest("Native checker and installed QAC are required")
        cls.personal, _ = cls.adapter.build_request(specimen())
        cls.ambiguous, _ = cls.adapter.build_request(specimen("هَذَا زَظَغٌ."))

    def native(self, payload):
        raw = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        proc = subprocess.run([str(self.adapter.NATIVE)], input=raw + "\n", text=True,
                              capture_output=True, timeout=20, check=True)
        result = json.loads(proc.stdout)
        for field in self.adapter.FALSE_FLAGS:
            self.assertIs(result[field], False, field)
        return result

    def test_complete_candidate_receipt_rejects_omission_duplicate_and_forced_resolution(self):
        payload = deepcopy(self.ambiguous)
        baseline = self.native(payload)
        self.assertEqual(baseline["status"], "AMBIGUOUS")
        proper = {key: deepcopy(baseline[key]) for key in self.adapter.RECEIPT_FIELDS}
        payload["proposed"] = proper
        self.assertIs(self.native(payload)["certificate_checked"], True)
        variants = []
        for candidates in (["speaker_a"], ["speaker_a", "speaker_b", "speaker_a"], ["speaker_b", "speaker_a"]):
            altered = deepcopy(proper)
            altered["candidate_entity_ids"] = candidates
            variants.append(altered)
        altered = deepcopy(proper)
        altered["status"], altered["bound_entity_id"] = "RESOLVED", "speaker_a"
        variants.append(altered)
        for key in ("reading_ids", "reading_results"):
            altered = deepcopy(proper)
            altered[key] = []
            variants.append(altered)
        for proposed in variants:
            with self.subTest(proposed=proposed):
                payload["proposed"] = proposed
                result = self.native(payload)
                self.assertEqual(result["status"], "INVALID_CERTIFICATE")
                self.assertIs(result["certificate_checked"], False)

    def test_swapped_context_does_not_accept_old_speaker_certificate(self):
        payload = deepcopy(self.personal)
        baseline = self.native(payload)
        payload["proposed"] = {key: deepcopy(baseline[key]) for key in self.adapter.RECEIPT_FIELDS}
        payload["context"]["speaker"] = "speaker_b"
        result = self.native(payload)
        self.assertEqual(result["status"], "INVALID_CERTIFICATE")
        self.assertIs(result["certificate_checked"], False)

    def test_donor_person_tag_and_decoded_source_form_are_not_free_labels(self):
        for mutate in (lambda p: p["alternatives"][0].update(profile_code="2MS"),
                       lambda p: p["alternatives"][0].update(source_form="هَذَا"),
                       lambda p: p["alternatives"][0].update(pos="DEM")):
            payload = deepcopy(self.personal)
            mutate(payload)
            with self.subTest(alternative=payload["alternatives"][0]):
                result = self.native(payload)
                self.assertNotEqual(result["status"], "RESOLVED")
                self.assertIsNone(result.get("bound_entity_id"))

    def test_retained_real_donor_cannot_license_an_arbitrary_target_word(self):
        payload = deepcopy(self.personal)
        payload["source"]["text"] = "زَظَغٌ."
        payload["source"]["revision"] = sha256(payload["source"]["text"].encode("utf-8")).hexdigest()
        payload["occurrence"] = {"start_byte": 0, "end_byte": len("زَظَغٌ".encode("utf-8")), "surface": "زَظَغٌ"}
        for row in payload["alternatives"]:
            row["target_surface"] = "زَظَغٌ"
        result = self.native(payload)
        self.assertNotEqual(result["status"], "RESOLVED")
        self.assertIsNone(result.get("bound_entity_id"))
        for row in payload["alternatives"]:
            row["source_form"] = "زَظَغٌ"
        result = self.native(payload)
        self.assertNotEqual(result["status"], "RESOLVED")
        self.assertIsNone(result.get("bound_entity_id"))

    def test_native_prefix_boundary_blocks_noninitial_rebinding(self):
        payload = deepcopy(self.personal)
        prefix = "قَالَ رَاءٌ: «"
        shift = len(prefix.encode("utf-8"))
        payload["source"]["text"] = prefix + payload["source"]["text"] + "»"
        payload["source"]["revision"] = sha256(payload["source"]["text"].encode("utf-8")).hexdigest()
        payload["occurrence"]["start_byte"] += shift
        payload["occurrence"]["end_byte"] += shift
        result = self.native(payload)
        self.assertEqual(result["status"], "OUT_OF_SCOPE")
        self.assertIsNone(result["bound_entity_id"])

    def test_native_integer_fields_and_context_ids_are_strict(self):
        for field, values in (("start_byte", [False, 0.0, 0.5]), ("end_byte", [True, 1.0, 1.5])):
            for value in values:
                payload = deepcopy(self.personal)
                payload["occurrence"][field] = value
                with self.subTest(field=field, value=value):
                    self.assertEqual(self.native(payload)["status"], "INVALID_INPUT")
        for value in (True, 256.0, -1):
            payload = deepcopy(self.personal)
            payload["budget"] = value
            self.assertEqual(self.native(payload)["status"], "INVALID_INPUT")
        payload = deepcopy(self.personal)
        payload["context"]["entities"].append(deepcopy(payload["context"]["entities"][0]))
        self.assertEqual(self.native(payload)["status"], "INVALID_INPUT")

    def test_duplicate_raw_keys_and_fabricated_author_fields_are_rejected(self):
        raw = json.dumps(self.personal).replace('"budget": 256', '"budget": 256, "bu\\u0064get": 256')
        self.assertEqual(self.native(raw)["status"], "INVALID_INPUT")
        payload = deepcopy(self.personal)
        payload["LexicalCertificate"] = {"author": "سيبويه", "root_count": 5000}
        self.assertEqual(self.native(payload)["status"], "INVALID_INPUT")

    def test_unknown_required_traits_preserve_candidate_without_resolution(self):
        payload = deepcopy(self.personal)
        payload["context"]["entities"][0]["number"] = "unknown"
        result = self.native(payload)
        self.assertEqual(result["status"], "UNRESOLVED_FEATURES")
        self.assertEqual(result["candidate_entity_ids"], ["speaker_a"])
        self.assertIsNone(result["bound_entity_id"])


class UntrustedNativeDeclarations(unittest.TestCase):
    def test_true_like_numbers_and_scope_promotions_are_not_native_verification(self):
        from tools import contextual_reference as adapter
        proposal = {"status": "NO_LEXICAL_READING", "reading_ids": [],
                    "candidate_entity_ids": [], "bound_entity_id": None, "reading_results": []}
        good = {**deepcopy(proposal), "law_id": adapter.LAW_ID,
                "observed_status": "NO_LEXICAL_READING", "certificate_checked": True,
                **{key: False for key in adapter.FALSE_FLAGS}}
        self.assertTrue(adapter._native_agrees(good, proposal))
        for key, value in [("certificate_checked", 1), ("certificate_checked", False),
                           ("candidate_entity_ids", ["forged"]), ("bound_entity_id", "forged"),
                           *[(field, True) for field in adapter.FALSE_FLAGS]]:
            forged = {**deepcopy(good), key: value}
            with self.subTest(field=key, value=value):
                self.assertFalse(adapter._native_agrees(forged, proposal))
        forged = deepcopy(good)
        forged["author"] = "سيبويه"
        self.assertFalse(adapter._native_agrees(forged, proposal))


class FrozenSemanticReferenceIdentity(unittest.TestCase):
    def test_old_twenty_five_cases_remain_the_same_exact_bytes(self):
        # This test checks the existing publication identity, not its answers.
        path = ROOT / "evidence/semantic_axes_v1/revision_2/reference.json"
        self.assertEqual(sha256(path.read_bytes()).hexdigest(),
                         "9787e4496118a80a4f352ef19193e1e37976eb282eaf96caaad511ce77ffa431")


if __name__ == "__main__":
    unittest.main()
