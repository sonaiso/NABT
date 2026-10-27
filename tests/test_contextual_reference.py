"""Bounded initial-occurrence licences; no benchmark answers enter runtime."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import contextual_reference as adapter


def context():
    return {"entities": [
        {"id": "first", "name": "رَاءٌ", "gender": "masculine", "number": "singular", "kind": "person"},
        {"id": "second", "name": "جِيمٌ", "gender": "masculine", "number": "singular", "kind": "person"}],
        "speaker": "first", "addressee": "second", "deixis": [], "closed_reference_scope": True}


def payload():
    # Authored protocol control with a declared QAC-format donor, never a
    # claim that this test fixture was acquired from the installed corpus.
    record = "(1:1:1:1)\t>anaA\tPRON\tSTEM|POS:PRON|1S\r\n"
    text = "أَنَا زَظَغٌ."
    return {"source": {"id": "authored_control", "revision": "1", "text": text},
            "occurrence": {"start_byte": 0, "end_byte": len("أَنَا".encode()), "surface": "أَنَا"},
            "context": context(),
            "donors": [{"id": "d", "source_id": "authored_control", "source_revision": "1",
                        "start_byte": 0, "end_byte": len(record.encode()), "record": record}],
            "alternatives": [{"id": "r", "pos": "PRON", "profile_code": "1S", "target_surface": "أَنَا",
                              "source_form": "أَنَا", "donor_ids": ["d"]}], "budget": 256, "proposed": None}


def native_result(proposal):
    return {**deepcopy(proposal), "law_id": adapter.LAW_ID, "observed_status": proposal["status"],
            "certificate_checked": True, **{key: False for key in adapter.FALSE_FLAGS}}


class ContextualInputAndReceiptTests(unittest.TestCase):
    def test_public_contract_rejects_claim_authority_and_expected_answers(self):
        for name in ("expected", "query", "native_checked", "author", "case_id", "source_profile"):
            request = {"text": "أَنَا", "context": context(), name: True}
            result = adapter.execute_request(request)
            self.assertEqual(result["status"], "INVALID_INPUT")
            self.assertIs(result["native_checked"], False)
            self.assertIsNone(result["reference"])

    def test_duplicate_keys_and_lossy_numbers_rejected_before_inference(self):
        for raw in ('{"text":"a","text":"b"}', '{"budget":1.0}', '{"budget":1e1}'):
            with self.assertRaises((adapter.InputError, ValueError)):
                adapter.strict_loads(raw)
        for number in (True, 1.0, -1, "1"):
            value = payload()
            value["budget"] = number
            with self.assertRaises((adapter.InputError, adapter.ResourceLimit)):
                adapter.propose(value)

    def test_initial_source_span_is_exact_and_not_a_subword(self):
        value = payload()
        value["occurrence"]["end_byte"] -= 1
        with self.assertRaises(adapter.InputError):
            adapter.propose(value)
        value = payload()
        value["source"]["text"] = "أَنَازَظَغٌ"
        self.assertEqual(adapter.propose(value)["status"], "OUT_OF_SCOPE")

    def test_quote_scope_is_not_outer_speaker_scope(self):
        value = payload()
        value["source"]["text"] = "«" + value["source"]["text"] + "»"
        value["occurrence"]["start_byte"] += 2
        value["occurrence"]["end_byte"] += 2
        result = adapter.propose(value)
        self.assertEqual(result["status"], "OUT_OF_SCOPE")
        self.assertEqual(result["reading_ids"], [])

    def test_closed_speaker_selector_and_input_only_context_change(self):
        value = payload()
        self.assertEqual(adapter.propose(value)["bound_entity_id"], "first")
        value["context"]["speaker"] = "second"
        self.assertEqual(adapter.propose(value)["bound_entity_id"], "second")
        value["context"]["speaker"] = None
        self.assertEqual(adapter.propose(value)["status"], "NO_CANDIDATE")

    def test_open_context_never_resolves_a_singleton(self):
        value = payload()
        value["context"]["closed_reference_scope"] = False
        result = adapter.propose(value)
        self.assertEqual(result["status"], "OPEN_SCOPE")
        self.assertEqual(result["candidate_entity_ids"], ["first"])
        self.assertIsNone(result["bound_entity_id"])

    def test_unknown_required_number_does_not_disappear_or_resolve(self):
        value = payload()
        value["context"]["entities"][0]["number"] = "unknown"
        result = adapter.propose(value)
        self.assertEqual(result["status"], "UNRESOLVED_FEATURES")
        self.assertEqual(result["candidate_entity_ids"], ["first"])
        self.assertIsNone(result["bound_entity_id"])
        value["context"]["entities"][0]["number"] = "singular"
        value["context"]["entities"][0]["gender"] = "unknown"
        self.assertEqual(adapter.propose(value)["status"], "RESOLVED")  # 1S has no gender constraint.

    def test_all_source_alternatives_preserved_even_when_one_is_unsupported(self):
        value = payload()
        value["alternatives"].append({**value["alternatives"][0], "id": "unknown", "pos": "OTHER", "profile_code": None})
        result = adapter.propose(value)
        self.assertEqual(result["status"], "UNSUPPORTED_READING")
        self.assertEqual(result["reading_ids"], ["r", "unknown"])
        self.assertEqual(result["candidate_entity_ids"], ["first"])

    def test_bad_donor_profile_does_not_grant_lexical_person(self):
        value = payload()
        value["alternatives"][0]["profile_code"] = "2MS"
        self.assertEqual(adapter.propose(value)["status"], "UNSUPPORTED_READING")
        value = payload()
        value["donors"][0]["source_id"] = "An alleged famous author"
        value["alternatives"][0]["pos"] = "DEM"
        value["alternatives"][0]["profile_code"] = "3MS"
        self.assertEqual(adapter.propose(value)["status"], "UNSUPPORTED_READING")

    def test_authentic_donor_cannot_be_assigned_to_an_arbitrary_surface(self):
        value = payload()
        value["source"]["text"] = "زَظَغٌ"
        value["occurrence"] = {"start_byte": 0, "end_byte": len("زَظَغٌ".encode()), "surface": "زَظَغٌ"}
        value["alternatives"][0]["target_surface"] = "زَظَغٌ"
        self.assertEqual(adapter.propose(value)["status"], "UNSUPPORTED_READING")
        value["alternatives"][0]["source_form"] = "زَظَغٌ"
        self.assertEqual(adapter.propose(value)["status"], "UNSUPPORTED_READING")

    def test_more_than_one_retained_candidate_remains_ambiguous(self):
        value = payload()
        form, source_form = "هَذَا", "هَٰذَا"
        record = "(1:1:1:1)\th`a*A\tDEM\tSTEM|POS:DEM|MS\r\n"
        # Use the exact retained spelling: h`a*A is dagger alif + fatha.
        source_form = adapter.buckwalter_to_arabic("h`a*A")
        value["source"]["text"] = form
        value["occurrence"] = {"start_byte": 0, "end_byte": len(form.encode()), "surface": form}
        value["donors"][0].update(record=record, end_byte=len(record.encode()))
        value["alternatives"][0].update(pos="DEM", profile_code="3MS", source_form=source_form, target_surface=form)
        value["context"]["deixis"] = [{"form": form, "entity_ids": ["second", "first"]}]
        value["context"]["entities"][1]["gender"] = "unknown"
        result = adapter.propose(value)
        self.assertEqual(result["status"], "AMBIGUOUS")
        self.assertEqual(result["candidate_entity_ids"], ["first", "second"])

    def test_insufficient_budget_has_a_real_failure_receipt(self):
        value = payload()
        value["budget"] = 0
        result = adapter.propose(value)
        self.assertEqual(result["status"], "RESOURCE_LIMIT")
        self.assertEqual(result["candidate_entity_ids"], [])
        self.assertTrue(adapter._native_agrees(native_result(result), result))

    def test_strict_native_result_never_trusts_imported_boolean_or_subset(self):
        proposal = adapter.propose(payload())
        result = native_result(proposal)
        self.assertTrue(adapter._native_agrees(result, proposal))
        for key, value in (("certificate_checked", 1), ("whole_clause_checked", True),
                           ("reading_ids", []), ("candidate_entity_ids", []), ("bound_entity_id", "second")):
            with self.subTest(key=key):
                changed = {**result, key: value}
                self.assertFalse(adapter._native_agrees(changed, proposal))

    def test_failures_are_digest_bound_without_native_authority(self):
        result = adapter.execute_request({"text": "أَنَا", "context": context(), "verified": True})
        body = {key: value for key, value in result.items() if key != "receipt_sha256"}
        self.assertEqual(result["receipt_sha256"], adapter.digest(body))
        self.assertFalse(result["native_checked"])


class ContextualInstalledSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not adapter.loader.DEFAULT_SOURCE.is_file():
            raise unittest.SkipTest("Fetch installed pinned QAC source")
        cls.request = {"text": "أَنَا زَظَغٌ.", "context": context()}
        cls.payload, cls.bindings = adapter.build_request(cls.request)

    def test_source_records_are_exact_whole_source_offsets(self):
        loaded = adapter.loader.load_attested_lexicon()
        for donor, binding in zip(self.payload["donors"], self.bindings, strict=True):
            original = loaded.model.raw[donor["start_byte"]:donor["end_byte"]]
            self.assertEqual(original.decode(), donor["record"])
            self.assertEqual(sha256(original).hexdigest(), binding["content_sha256"])
            self.assertEqual(binding["source_sha256"], adapter.loader.SOURCE_SHA256)

    def test_identity_never_loads_source_or_requires_native(self):
        with patch.object(adapter.loader, "load_attested_lexicon", side_effect=AssertionError("No source load")):
            with tempfile.TemporaryDirectory() as directory, patch.object(adapter, "NATIVE", Path(directory) / "absent"):
                self.assertIsNone(adapter.identity()["native_sha256"])

    def test_missing_native_retains_unchecked_proposal_not_reference(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(adapter, "NATIVE", Path(directory) / "absent"):
            result = adapter.execute_request(self.request)
        self.assertEqual(result["status"], "UNMEASURED")
        self.assertEqual(result["execution"]["proposal"]["status"], "RESOLVED")
        self.assertIsNone(result["reference"])
        self.assertFalse(result["native_checked"])

    def test_live_native_receipt_binds_source_context_and_every_alternative(self):
        if not adapter.NATIVE.is_file():
            self.skipTest("Build native contextualReference")
        result = adapter.execute_request(self.request)
        self.assertTrue(result["native_checked"], result["execution"]["error"])
        self.assertEqual(result["reference"]["bound_entity_id"], "first")
        self.assertEqual(result["reference"]["span"], {"start": 0, "end": len("أَنَا")})
        self.assertEqual(result["execution"]["input"]["context"], context())
        self.assertEqual(result["execution"]["proposal"]["reading_ids"], [x["id"] for x in result["execution"]["input"]["alternatives"]])
        self.assertFalse(result["scope"]["sentence_syntax_promoted"])
        self.assertFalse(result["scope"]["whole_arabic_complete"])


if __name__ == "__main__":
    unittest.main()
