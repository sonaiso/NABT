"""Independent source identity and original-byte admission boundary tests."""
from copy import deepcopy
import gzip
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import attested_lexical_loader as loader
from nabt.corpus_evidence import lexical_index, template_matches
from nabt.errors import NabtError


class SourceAdmissionBoundaries(unittest.TestCase):
    def test_missing_source_defers_without_a_teaching_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(NabtError) as raised:
                loader.load_attested_lexicon(Path(directory) / "not-present.gz")
        self.assertEqual(raised.exception.code, "ATTESTED_SOURCE_UNAVAILABLE")
        self.assertEqual(raised.exception.status, "DEFER")

    def test_untrusted_small_source_is_not_an_attestation(self):
        for raw in (b"LOCATION\tFORM\tTAG\tFEATURES\n", b"native_checked=true", b"{}"):
            with self.subTest(raw=raw), self.assertRaises(NabtError) as raised:
                loader._decode_source(raw)
            self.assertEqual(raised.exception.code, "ATTESTED_SOURCE_IDENTITY_MISMATCH")

    def test_empty_and_nonbytes_inputs_are_rejected(self):
        for value in (b"", "source", True, 12):
            with self.subTest(value=value), self.assertRaises(NabtError):
                loader._decode_source(value)

    def test_compressed_payload_cannot_expand_beyond_pinned_size(self):
        bomb = gzip.compress(b"A" * (loader.SOURCE_BYTES + 1), mtime=0)
        with self.assertRaises(NabtError) as raised:
            loader._decode_source(bomb)
        self.assertEqual(raised.exception.code, "RESOURCE_LIMIT")
        self.assertEqual(raised.exception.status, "DEFER")

    def test_oversized_uncompressed_payload_is_a_resource_boundary(self):
        with self.assertRaises(NabtError) as raised:
            loader._decode_source(b"A" * (loader.SOURCE_BYTES + 1))
        self.assertEqual(raised.exception.code, "RESOURCE_LIMIT")

    def test_bad_compression_is_not_silently_read_as_raw(self):
        for value in (b"\x1f\x8b", gzip.compress(b"not the source", mtime=0)[:-3]):
            with self.subTest(value=value), self.assertRaises(NabtError) as raised:
                loader._decode_source(value)
            self.assertEqual(raised.exception.code, "INVALID_ATTESTED_SOURCE")

    def test_installed_manifest_hash_is_checked_before_json_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matrix.json"
            path.write_text('{"schema":"nabt.lexical-loading-matrix.v1","verified":true}')
            with patch.object(loader, "MATRIX_PATH", path), self.assertRaises(NabtError) as raised:
                loader._installed_matrix()
        self.assertEqual(raised.exception.code, "LEXICAL_MATRIX_IDENTITY_MISMATCH")

    def test_registry_is_fixed_and_not_query_selected(self):
        value, digest = loader._installed_matrix()
        self.assertEqual(digest, loader.MATRIX_SHA256)
        self.assertEqual(len(value["entries"]), 42)
        self.assertEqual(len({entry["id"] for entry in value["entries"]}), 42)
        self.assertTrue(all(entry["sense_licensed_for_new_occurrence"] is False
                            for entry in value["entries"]))


class FullPinnedSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not loader.DEFAULT_SOURCE.is_file():
            raise unittest.SkipTest("Explicitly acquire the pinned external QAC source for source replay")
        cls.loaded = loader.load_attested_lexicon()
        cls.original = cls.loaded.model.raw
        cls.matrix, cls.digest = loader._installed_matrix()

    def test_full_raw_identity_and_training_scope_are_preserved(self):
        report = self.loaded.report
        self.assertEqual(sha256(self.original).hexdigest(), loader.SOURCE_SHA256)
        self.assertEqual(len(self.original), loader.SOURCE_BYTES)
        self.assertEqual(self.loaded.model.source_id, loader.PROFILE_ID)
        self.assertEqual(report["source"]["record_count"], 128219)
        self.assertFalse(report["teaching_corpus_included"])
        self.assertFalse(report["matrix_filters_runtime"])
        self.assertFalse(report["lean_native_checked"])
        self.assertFalse(report["world_truth_asserted"])
        self.assertFalse(report["transmission_evaluated"])
        self.assertFalse(report["all_arabic_complete"])

    def test_raw_and_compressed_storage_have_the_same_lexical_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.txt"
            path.write_bytes(self.original)
            second = loader.load_attested_lexicon(path)
        self.assertEqual(second.model.raw, self.original)
        self.assertEqual(second.report["model_summary"]["inventory_sha256"],
                         self.loaded.report["model_summary"]["inventory_sha256"])

    def test_one_byte_source_edit_cannot_use_an_old_matrix(self):
        changed = self.original[:-1] + (b"X" if self.original[-1:] != b"X" else b"Y")
        with self.assertRaises(NabtError) as raised:
            loader._decode_source(changed)
        self.assertEqual(raised.exception.code, "ATTESTED_SOURCE_IDENTITY_MISMATCH")

    def test_gzip_storage_without_compression_keeps_the_same_original(self):
        framed = gzip.compress(self.original, compresslevel=0, mtime=0)
        self.assertGreater(len(framed), loader.SOURCE_BYTES)
        self.assertEqual(loader._decode_source(framed), self.original)

    def test_witness_counts_are_distinct_from_dictionary_and_reader_counts(self):
        matrix = self.loaded.report["matrix"]
        self.assertEqual(matrix["entry_count"], 42)
        self.assertEqual(matrix["aligned_entry_count"], 27)
        self.assertEqual(matrix["unmatched_entry_count"], 15)
        self.assertEqual(matrix["witness_count"], 1302)
        self.assertEqual(matrix["cross_source_senses_licensed"], 0)
        self.assertGreater(matrix["witness_link_count"], matrix["witness_count"])
        self.assertGreater(self.loaded.report["model_summary"]["lexical_readings"], matrix["entry_count"])

    def test_mutating_a_report_does_not_change_a_later_receipt(self):
        first = loader.load_attested_lexicon()
        first.report["matrix"]["cross_source_senses_licensed"] = 42
        first.report["world_truth_asserted"] = True
        second = loader.load_attested_lexicon()
        self.assertEqual(second.report["matrix"]["cross_source_senses_licensed"], 0)
        self.assertFalse(second.report["world_truth_asserted"])

    def test_replayed_bytes_and_coordinates_do_not_accept_lossy_integers(self):
        for change in ("bool_start", "float_end", "wrong_hash", "wrong_locator", "wrong_features"):
            altered = deepcopy(self.matrix)
            witness = next(e["morphology_candidates"][0]["witnesses"][0]
                           for e in altered["entries"] if e["morphology_candidates"])
            if change == "bool_start":
                witness["source_record"]["byte_start"] = True
            elif change == "float_end":
                witness["source_record"]["byte_end"] = float(witness["source_record"]["byte_end"])
            elif change == "wrong_hash":
                witness["source_record"]["sha256"] = "0" * 64
            elif change == "wrong_locator":
                witness["word_locator"][0] = True
            else:
                witness["features"] += "|ASSUMED:REAL"
            with self.subTest(change=change), self.assertRaises(NabtError):
                loader._matrix_report(altered, self.original, self.digest)

    def test_sense_promotion_and_duplicate_witnesses_are_rejected(self):
        for change in ("world", "sense", "duplicate", "count"):
            altered = deepcopy(self.matrix)
            entry = next(e for e in altered["entries"] if e["morphology_candidates"])
            candidate = entry["morphology_candidates"][0]
            if change == "world":
                entry["world_truth_asserted"] = True
            elif change == "sense":
                candidate["contextual_sense_identified"] = True
            elif change == "duplicate":
                candidate["witnesses"].append(deepcopy(candidate["witnesses"][0]))
                candidate["occurrence_count"] += 1
            else:
                altered["counts"]["catalogue_senses"] = 42.0
            with self.subTest(change=change), self.assertRaises(NabtError):
                loader._matrix_report(altered, self.original, self.digest)

    def test_candidate_group_or_occurrence_cannot_be_silently_omitted(self):
        for change in ("group", "occurrence"):
            altered = deepcopy(self.matrix)
            entry = next(e for e in altered["entries"] if e["morphology_candidates"])
            if change == "group":
                entry["morphology_candidates"].pop()
            else:
                candidate = entry["morphology_candidates"][0]
                candidate["witnesses"].pop()
                candidate["occurrence_count"] -= 1
            with self.subTest(change=change), self.assertRaises(NabtError):
                loader._matrix_report(altered, self.original, self.digest)

    def test_headword_projection_keeps_shadda_hamza_and_dagger_alif(self):
        self.assertEqual(loader._candidate_key("عِلْمٌ"), "علم")
        self.assertNotEqual(loader._candidate_key("عَلَّمَ"), loader._candidate_key("عَلِمَ"))
        self.assertNotEqual(loader._candidate_key("أرض"), loader._candidate_key("ارض"))
        self.assertNotEqual(loader._candidate_key("قَلَٰم"), loader._candidate_key("قَلَم"))

    def test_shadda_remains_a_reading_constraint_and_oov_stays_unknown(self):
        index, _ = lexical_index(self.loaded.model)
        for ordinary, doubled in (("أَرْضٌ", "أَرَّضٌ"), ("شَمْسٌ", "شَمَّسٌ")):
            from nabt.corpus_evidence import lookup_key
            rows = [json.loads(row) for row in index[lookup_key(ordinary)]]
            self.assertTrue(any(template_matches(ordinary, row["template"]) for row in rows))
            self.assertFalse(any(template_matches(doubled, row["template"]) for row in rows))
        self.assertNotIn("زظغ", index)


if __name__ == "__main__":
    unittest.main()
