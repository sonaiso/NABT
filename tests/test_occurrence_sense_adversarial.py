"""Independent receipt/transport counterexamples; no frozen reference imports.

These tests mutate premises or serialized certificates rather than duplicating
the acquisition recurrence. Native donor authenticity remains a collector
premise, so that boundary is attacked through the public source loader.
"""
from copy import deepcopy
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import occurrence_sense as adapter


def request(text="قلم", *, index=0, context=None, target=None):
    return {"text": text, "context": {} if context is None else context,
            "token_index": index, "target": ["الذي يكتب به"] if target is None else target,
            "budget": 100000}


@unittest.skipUnless(adapter.NATIVE.is_file() and adapter.loader.DEFAULT_SOURCE.is_file()
                     and (adapter.ROOT / "artifacts/local/lisan.txt").is_file(),
                     "native checker and pinned full sources are required")
class OccurrenceAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loaded, cls.matrix, cls.catalogue, _ = adapter._installed()

    def payload(self, value):
        payload = adapter._build(adapter.validate_input(value), self.loaded)
        payload["proposed"] = adapter.propose(payload, matrix=self.matrix, catalogue=self.catalogue)
        return payload

    def raw_native(self, raw):
        completed = subprocess.run([str(adapter.NATIVE)], input=raw, capture_output=True,
                                   timeout=30, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr[:512])
        return [adapter.strict_loads(line) for line in completed.stdout.splitlines()]

    def test_stale_query_receipt_is_rejected_even_with_same_candidate_inventory(self):
        old = self.payload(request())
        changed = self.payload(request(target=["الزلم"]))
        changed["proposed"] = old["proposed"]
        result = adapter._native(changed)
        self.assertEqual(result["status"], "INVALID_CERTIFICATE")
        self.assertIs(result["certificate_checked"], False)

    def test_identical_surface_at_a_different_occurrence_cannot_reuse_receipt(self):
        old = self.payload(request("قلم قلم", index=0))
        changed = self.payload(request("قلم قلم", index=1))
        self.assertEqual(old["occurrence"]["surface"], changed["occurrence"]["surface"])
        self.assertNotEqual(old["occurrence"]["start_byte"], changed["occurrence"]["start_byte"])
        changed["proposed"] = old["proposed"]
        self.assertIs(adapter._native(changed)["certificate_checked"], False)

    def test_shifted_source_bytes_invalidate_old_occurrence_receipt(self):
        old = self.payload(request())
        changed = self.payload(request("\u2003قلم"))
        self.assertEqual(changed["occurrence"]["start_byte"], 3)
        changed["proposed"] = old["proposed"]
        self.assertIs(adapter._native(changed)["certificate_checked"], False)

    def test_native_context_binding_cannot_reuse_old_receipt(self):
        old = self.payload(request())
        changed = self.payload(request(context={"closed_reference_scope": True}))
        changed["proposed"] = old["proposed"]
        self.assertIs(adapter._native(changed)["certificate_checked"], False)

    def test_raw_native_rejects_noncanonical_naturals(self):
        raw = adapter.wire(self.payload(request()))
        self.assertIn('"budget":100000,', raw)
        for number in ("true", "1.0", "1e0", "-0", "00"):
            with self.subTest(number=number):
                malformed = raw.replace('"budget":100000,', '"budget":' + number + ',', 1)
                result = self.raw_native((malformed + "\n").encode())[0]
                self.assertEqual(result["status"], "INVALID_INPUT")
                self.assertIs(result["certificate_checked"], False)

    def test_escaped_duplicate_key_is_not_hidden_by_json_decoding(self):
        raw = adapter.wire(self.payload(request()))
        raw = raw.replace('"budget":100000,', '"budget":100000,"budge\\u0074":100000,', 1)
        result = self.raw_native((raw + "\n").encode())[0]
        self.assertEqual(result["status"], "INVALID_INPUT")
        self.assertIs(result["certificate_checked"], False)

    def test_oversized_native_line_does_not_consume_the_next_request(self):
        valid = adapter.wire(self.payload(request())).encode()
        results = self.raw_native(b" " * (adapter.MAX_NATIVE_BYTES + 1) + b"\n" + valid + b"\n")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["status"], "RESOURCE_LIMIT")
        self.assertIs(results[0]["certificate_checked"], False)
        self.assertEqual(results[1]["status"], "CANDIDATES_ONLY")
        self.assertIs(results[1]["certificate_checked"], True)

    def test_public_acquisition_rejects_corrupt_raw_source(self):
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / "qac.txt"
            raw = bytearray(self.loaded.model.raw)
            raw[0] ^= 1
            changed.write_bytes(raw)
            with patch.object(adapter.loader, "DEFAULT_SOURCE", changed):
                result = adapter.assess(request())
        self.assertEqual(result["status"], "UNMEASURED")
        self.assertIs(result["native_checked"], False)
        self.assertEqual(result["readings"], [])
        self.assertIn("source", result["execution"]["error"].lower())

    def test_pinned_dictionary_byte_mutation_stops_before_native_semantic_success(self):
        baseline = adapter.assess(request())
        self.assertIs(baseline["native_checked"], True)
        citation = next(row["citation"] for row in self.catalogue["senses"]
                        if row["id"] == "lisan:qalam-writing")
        original_path = adapter.ROOT / adapter.SOURCE_PATHS[citation["work"]]
        # Keep the catalogue, its expected digest, and the preceding receipt.
        # Change an actual dictionary quotation byte in a temporary full file.
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / "lisan.txt"
            raw = bytearray(original_path.read_bytes())
            raw[citation["start_byte"]] ^= 1
            changed.write_bytes(raw)
            paths = {**adapter.SOURCE_PATHS, citation["work"]: str(changed)}
            with patch.object(adapter, "SOURCE_PATHS", paths), \
                    patch.object(adapter, "_native", wraps=adapter._native) as native:
                result = adapter.assess(request())
                native.assert_not_called()
        self.assertEqual(result["status"], "UNMEASURED")
        self.assertIs(result["native_checked"], False)
        self.assertIs(result["certificate_checked"], False)
        self.assertEqual(result["readings"], [])
        self.assertEqual(result["candidate_senses"], [])
        self.assertIn("dictionary citation", result["execution"]["error"])

    def test_positive_insufficient_budget_does_not_return_a_partial_inventory(self):
        value = request("عين", target=["حاسة البصر والرؤية"])
        baseline = adapter.assess(value)
        self.assertIs(baseline["native_checked"], True)
        self.assertGreater(len(baseline["readings"]), 1)
        limited = deepcopy(value)
        limited["budget"] = 1
        result = adapter.assess(limited)
        self.assertEqual(result["status"], "RESOURCE_LIMIT")
        self.assertIs(result["native_checked"], True)
        self.assertIs(result["certificate_checked"], True)
        self.assertEqual(result["readings"], [])
        self.assertEqual(result["candidate_senses"], [])
        self.assertIs(result["contextual_sense_selected"], False)
        self.assertIs(result["all_arabic_complete"], False)

    def test_deleting_an_entire_reading_invalidates_the_native_receipt(self):
        payload = self.payload(request("عين", target=["حاسة البصر والرؤية"]))
        self.assertGreater(len(payload["proposed"]["readings"]), 1)
        original_hash = adapter.digest(payload["proposed"])
        payload["proposed"]["readings"].pop()
        # A caller can recompute a digest, but native replay does not consult it.
        self.assertNotEqual(adapter.digest(payload["proposed"]), original_hash)
        result = adapter._native(payload)
        self.assertEqual(result["status"], "INVALID_CERTIFICATE")
        self.assertIs(result["certificate_checked"], False)

    def test_native_truth_flag_is_not_authority_for_world_truth(self):
        native = adapter._native

        def false_authority(payload=None):
            result = native(payload)
            if payload is not None:
                result["world_truth_established"] = True
            return result

        with patch.object(adapter, "_native", side_effect=false_authority):
            result = adapter.assess(request())
        self.assertEqual(result["status"], "UNMEASURED")
        self.assertIs(result["native_checked"], False)
        self.assertIs(result["world_truth_established"], False)
        self.assertEqual(result["readings"], [])

    def test_public_context_swap_rejects_stale_reference_subreceipt(self):
        context = {"entities": [
            {"id": "first", "name": "زيد", "gender": "masculine", "number": "singular", "kind": "person"},
            {"id": "second", "name": "عمر", "gender": "masculine", "number": "singular", "kind": "person"}],
            "speaker": "first", "closed_reference_scope": True}
        value = request("أنا قلم", index=1, context=context)
        stale = adapter.contextual_reference.execute_request({"text": value["text"], "context": context})
        self.assertIs(stale["native_checked"], True)
        changed = deepcopy(value)
        changed["context"]["speaker"] = "second"
        with patch.object(adapter.contextual_reference, "execute_request", return_value=stale):
            result = adapter.assess(changed)
        self.assertEqual(result["status"], "UNMEASURED")
        self.assertIs(result["native_checked"], False)
        self.assertEqual(result["readings"], [])
        self.assertIn("input context", result["execution"]["error"])


if __name__ == "__main__":
    unittest.main()
