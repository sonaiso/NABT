"""Developer boundary checks, separate from the frozen independent reference."""
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from tools import occurrence_sense as adapter


def request(text="قلم", target=None, *, index=0, budget=100000):
    return {"text": text, "context": {}, "token_index": index,
            "target": ["الذي يكتب به"] if target is None else target, "budget": budget}


class OccurrenceInputTests(unittest.TestCase):
    def test_authority_and_answer_fields_are_not_public_inputs(self):
        for name in ("root", "sense_id", "lexical_source", "registry", "expected", "native_checked"):
            value = request()
            value[name] = True
            result = adapter.assess(value)
            self.assertEqual(result["status"], "INVALID_INPUT")
            self.assertIs(result["native_checked"], False)

    def test_strict_natural_types_and_component_arrays(self):
        for field in ("token_index", "budget"):
            for value in (True, 1.0, -1, "0"):
                bad = request()
                bad[field] = value
                self.assertEqual(adapter.assess(bad)["status"], "INVALID_INPUT")
        for value in ((), ("a",), "a", [], ["a", "a"], [True]):
            self.assertEqual(adapter.assess(request(target=value))["status"], "INVALID_INPUT")
        self.assertEqual(adapter.validate_input(request())["budget"], 100000)
        self.assertEqual(adapter.assess(request(budget=1000001))["status"], "RESOURCE_LIMIT")

    def test_quote_contents_do_not_count_as_outer_tokens(self):
        text = "«عين حجر»\u2003هذا، قلم"
        first, second = adapter._occurrence(text, 0), adapter._occurrence(text, 1)
        self.assertEqual(first["surface"], "هذا")
        self.assertEqual(second["surface"], "قلم")
        self.assertEqual(text.encode()[second["start_byte"]:second["end_byte"]], "قلم".encode())
        with self.assertRaises(adapter.InputError):
            adapter._occurrence(text, 2)
        self.assertEqual(adapter.assess(request("«عين حجر»"))["status"], "INVALID_INPUT")

    def test_cli_rejects_duplicate_keys_before_source_access(self):
        process = subprocess.run([sys.executable, str(adapter.ROOT / "tools/occurrence_sense.py"), "--request", "-"],
            input='{"text":"x","text":"y"}', text=True, capture_output=True, check=False)
        self.assertEqual(process.returncode, 2)
        self.assertEqual(adapter.strict_loads(process.stdout)["status"], "INVALID_INPUT")

    def test_reference_context_cannot_be_substituted(self):
        value = request("أنا قلم", index=1)
        expected = {"text": value["text"], "context": value["context"]}
        receipt = {"input": expected, "input_sha256": adapter.digest(expected),
            "context_sha256": adapter.digest(value["context"]),
            "execution": {"input": {"source": {"text": value["text"]},
                "context": {"entities": [], "deixis": [], "speaker": None, "addressee": None,
                            "closed_reference_scope": False}}}}
        self.assertTrue(adapter._reference_bound(receipt, value))
        receipt["execution"]["input"]["context"]["closed_reference_scope"] = True
        self.assertFalse(adapter._reference_bound(receipt, value))


@unittest.skipUnless(adapter.loader.DEFAULT_SOURCE.is_file() and (adapter.ROOT / "artifacts/local/lisan.txt").is_file(),
                     "full pinned QAC/dictionary sources are not installed")
class OccurrenceSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loaded, cls.matrix, cls.catalogue, _ = adapter._installed()

    def payload(self, text="قلم", target=None, *, index=0, budget=100000):
        return adapter._build(adapter.validate_input(request(text, target, index=index, budget=budget)), self.loaded)

    def proposed(self, value):
        return adapter.propose(value, matrix=self.matrix, catalogue=self.catalogue)

    def test_all_dictionary_senses_survive_a_favorable_query(self):
        receipt = self.proposed(self.payload())
        self.assertEqual(receipt["status"], "CANDIDATES_ONLY")
        senses = receipt["readings"][0]["senses"]
        self.assertEqual([row["id"] for row in senses],
                         ["lisan:qalam-writing", "lisan:qalam-lot", "lisan:qalam-gambling"])
        self.assertEqual([row["mutabaqa"] for row in senses], [True, False, False])
        # Query substitution changes conditional indications, never acquisition.
        other = self.proposed(self.payload(target=["الزلم"]))
        self.assertEqual([row["id"] for row in other["readings"][0]["senses"]], [row["id"] for row in senses])
        self.assertEqual(other["readings"][0]["donor_ids"], receipt["readings"][0]["donor_ids"])

    def test_unmatched_morphology_is_retained_beside_dictionary_candidates(self):
        receipt = self.proposed(self.payload("شجر", ["النبات القائم على ساق"]))
        self.assertEqual(receipt["status"], "PARTIAL_CANDIDATES")
        verbs = [row for row in receipt["readings"] if row["pos"] == "V"]
        self.assertTrue(verbs)
        self.assertTrue(all(row["senses"] == [] and row["status"] == "UNMATCHED_READING" for row in verbs))
        self.assertTrue(any(row["senses"] for row in receipt["readings"]))

    def test_root_origin_passages_do_not_license_arbitrary_root_forms(self):
        receipt = self.proposed(self.payload("كتب", ["جمع شيء إلى شيء"]))
        self.assertEqual(receipt["status"], "NO_DICTIONARY_CANDIDATE")
        self.assertTrue(receipt["readings"])
        self.assertTrue(all(row["senses"] == [] for row in receipt["readings"]))

    def test_explicit_vowels_and_shadda_are_not_repaired(self):
        stone = self.proposed(self.payload("حَجَر", ["الصخرة"]))
        enclosure = self.proposed(self.payload("حِجْر", ["الصخرة"]))
        self.assertEqual({row["lemma_bw"] for row in stone["readings"]}, {"Hajar"})
        self.assertEqual({row["lemma_bw"] for row in enclosure["readings"]}, {"Hijor"})
        for surface in ("قُلَم", "قَلَّم"):
            self.assertEqual(self.proposed(self.payload(surface))["status"], "NO_MORPHOLOGY_READING")

    def test_budget_is_bound_and_exhaustion_is_not_a_negative_reading(self):
        zero = self.proposed(self.payload(budget=0))
        self.assertEqual(zero["status"], "RESOURCE_LIMIT")
        self.assertEqual(zero["readings"], [])
        self.assertEqual(zero["budget"], 0)
        self.assertEqual(self.proposed(self.payload(budget=100000))["budget"], 100000)

    def test_raw_source_donors_replay_at_their_exact_offsets(self):
        value = self.payload()
        for donor in value["donors"]:
            self.assertEqual(self.loaded.model.raw[donor["start_byte"]:donor["end_byte"]], donor["record"].encode())
        value["occurrence"]["start_byte"] = True
        with self.assertRaises(adapter.InputError):
            self.proposed(value)

    def test_missing_native_is_never_counted_as_success(self):
        with patch.object(adapter, "NATIVE", Path("/nonexistent/nabt-occurrence-native")):
            result = adapter.assess(request())
        self.assertEqual(result["status"], "UNMEASURED")
        self.assertFalse(result["native_checked"])
        self.assertEqual(result["readings"], [])
        self.assertEqual(result["execution"]["error"], "NATIVE_UNAVAILABLE")

    @unittest.skipUnless(adapter.NATIVE.is_file(), "native checker is not built")
    def test_native_rechecks_complete_senses_and_original_budget(self):
        value = self.payload()
        value["proposed"] = self.proposed(value)
        result = adapter._native(value)
        self.assertTrue(adapter._native_agrees(result, value["proposed"]))
        corrupt = deepcopy(value)
        corrupt["proposed"]["readings"][0]["senses"].pop()
        self.assertFalse(adapter._native(corrupt)["certificate_checked"])
        corrupt = deepcopy(value)
        corrupt["proposed"]["budget"] = 99
        self.assertFalse(adapter._native(corrupt)["certificate_checked"])

    @unittest.skipUnless(adapter.NATIVE.is_file(), "native checker is not built")
    def test_native_transport_rejects_duplicate_keys_and_changed_pos(self):
        value = self.payload()
        value["proposed"] = self.proposed(value)
        malformed = deepcopy(value)
        malformed["donors"][0]["record"] = malformed["donors"][0]["record"].replace("STEM|POS:N", "STEM|POS:V")
        for raw in (adapter.wire(malformed), adapter.wire(value)[:-1] + ',"budget":100000}'):
            process = subprocess.run([str(adapter.NATIVE)], input=raw + "\n", text=True, capture_output=True, check=False)
            self.assertEqual(adapter.strict_loads(process.stdout)["status"], "INVALID_INPUT")

    @unittest.skipUnless(adapter.NATIVE.is_file(), "native checker is not built")
    def test_native_outer_token_skips_quoted_contents(self):
        value = self.payload("«عين» قلم")
        value["proposed"] = self.proposed(value)
        self.assertTrue(adapter._native_agrees(adapter._native(value), value["proposed"]))
        self.assertEqual(value["occurrence"]["surface"], "قلم")

    @unittest.skipUnless(adapter.NATIVE.is_file() and adapter.contextual_reference.NATIVE.is_file(), "native checkers are not built")
    def test_initial_reference_is_bound_to_its_own_occurrence(self):
        value = request("هذا قلم", index=1)
        value["context"] = {"entities": [{"id": "object_a", "name": "قلم", "gender": "masculine",
            "number": "singular", "kind": "thing"}], "closed_reference_scope": True,
            "deixis": [{"form": "هذا", "entity_ids": ["object_a"]}]}
        result = adapter.assess(value)
        self.assertTrue(result["native_checked"], result["execution"]["error"])
        self.assertEqual(result["occurrence"]["surface"], "قلم")
        reference = result["initial_reference"]
        self.assertEqual(reference["execution"]["input"]["occurrence"]["surface"], "هذا")
        self.assertEqual(reference["context_sha256"], result["context_sha256"])
        self.assertFalse(result["reference_transferred"])
        self.assertFalse(result["contextual_sense_selected"])
        self.assertTrue(all(row["conditional_only"] and not row["sense_licensed_for_new_occurrence"]
                            for row in result["candidate_senses"]))

    @unittest.skipUnless(adapter.NATIVE.is_file(), "native checker is not built")
    def test_identity_change_during_native_check_invalidates_result(self):
        with patch.object(adapter, "identity", return_value={"changed": True}):
            result = adapter.assess(request())
        self.assertEqual(result["status"], "UNMEASURED")
        self.assertFalse(result["native_checked"])
        self.assertIn("identity changed", result["execution"]["error"])


if __name__ == "__main__":
    unittest.main()
