"""Independent byte reconstruction and adversarial whole-book claim controls."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("book_rule_coverage", ROOT / "tools/book_rule_coverage.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BookCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = MODULE.build_index()

    def reject(self, mutation):
        candidate = deepcopy(self.document)
        mutation(candidate)
        with self.assertRaises(ValueError):
            MODULE.validate_index(candidate)

    def test_partition_reconstructs_original_bytes_without_normalization(self):
        for book in self.document["books"]:
            original = (MODULE.SOURCE_DIRECTORY / book["file"]).read_bytes()
            cursor = 0
            reconstructed = bytearray()
            identities = set()
            for span in book["segments"]:
                self.assertEqual(cursor, span["start"])
                self.assertGreater(span["end"], span["start"])
                piece = original[span["start"]:span["end"]]
                self.assertEqual(sha256(piece).hexdigest(), span["sha256"])
                piece.decode("utf-8")
                reconstructed.extend(piece)
                cursor = span["end"]
                identities.add(span["segment_id"])
            self.assertEqual(bytes(reconstructed), original)
            self.assertEqual(cursor, len(original))
            self.assertEqual(len(identities), len(book["segments"]))

    def test_independently_known_source_endings_and_supplement_attribution(self):
        books = {b["source_id"]: b for b in self.document["books"]}
        self.assertEqual(books["qatr"]["size_bytes"], 40168)
        self.assertEqual(books["qatr"]["line_count"], 453)
        self.assertEqual(books["sabban"]["page_markers"][-1]["marker"], "PageV03P462")
        self.assertEqual(books["sibawayhi"]["page_markers"][-1]["marker"], "PageV04P485")
        supplement = [s for s in books["ibn_aqil"]["segments"] if s["layer"] == "named_editor_supplement"]
        self.assertEqual(supplement[0]["line_start"], 9658)
        self.assertEqual(supplement[-1]["line_end"], 10665)
        self.assertTrue(all(not s["selected_law_ids"] for s in supplement))

    def test_selected_rule_overlap_cannot_count_as_section_completion(self):
        result = MODULE.validate_index(self.document)
        self.assertEqual(result["selected_rule_count"], 38)
        self.assertGreater(result["body_segments_with_selected_law_overlap"], 0)
        self.assertGreater(result["body_segment_obligations"], result["body_segments_with_selected_law_overlap"])
        self.assertEqual(result["fully_adjudicated_body_segments"], 0)
        self.assertFalse(result["whole_book_strict_pass"])
        self.assertIsNone(result["whole_book_rule_denominator"])

    def test_cannot_remove_a_difficult_book(self):
        self.reject(lambda d: d["books"].pop(3))

    def test_cannot_omit_an_uncited_segment(self):
        self.reject(lambda d: d["books"][0]["segments"].pop(2))

    def test_cannot_duplicate_segment_to_inflate_evidence(self):
        self.reject(lambda d: d["books"][0]["segments"].append(deepcopy(d["books"][0]["segments"][1])))

    def test_overlap_cannot_hide_gap(self):
        self.reject(lambda d: d["books"][0]["segments"][1].update(start=d["books"][0]["segments"][0]["start"]))

    def test_cannot_replace_hash_with_newly_computed_authority(self):
        self.reject(lambda d: d["books"][0]["segments"][1].update(sha256="0" * 64))

    def test_boolean_coordinate_is_not_integer(self):
        self.reject(lambda d: d["books"][0]["segments"][0].update(line_start=True))

    def test_float_page_coordinate_is_not_integer(self):
        self.reject(lambda d: d["books"][0]["page_markers"][0].update(start=float(d["books"][0]["page_markers"][0]["start"])))

    def test_header_is_not_rule_authority(self):
        self.reject(lambda d: d["books"][0]["heading_candidates"][0].update(rule_adjudication="complete"))

    def test_marking_every_segment_reviewed_cannot_close_book(self):
        def forged(document):
            for book in document["books"]:
                for segment in book["segments"]:
                    segment["adjudication"] = "complete"
        self.reject(forged)

    def test_cannot_assert_global_completeness(self):
        self.reject(lambda d: d.update(whole_book_complete=True, whole_arabic_complete=True))

    def test_cannot_supply_a_known_denominator_without_adjudication(self):
        self.reject(lambda d: d.update(whole_book_rule_denominator=38, whole_arabic_coverage=1.0))

    def test_cannot_remove_extent_blocker(self):
        self.reject(lambda d: d["books"][3].update(extent_status="complete", extent_notes=[]))

    def test_cannot_attribute_editor_supplement_to_ibn_aqil(self):
        def forged(document):
            book = next(b for b in document["books"] if b["source_id"] == "ibn_aqil")
            next(s for s in book["segments"] if s["layer"] == "named_editor_supplement")["layer"] = "main_text_attribution_unadjudicated"
        self.reject(forged)

    def test_cannot_assign_selected_rule_to_unrelated_book(self):
        self.reject(lambda d: d["selected_rule_links"][0]["source_spans"][0].update(source_id="mughni"))

    def test_qatr_docket_covers_every_postmetadata_line(self):
        docket = self.document["qatr_semantic_docket"]
        raw = (MODULE.SOURCE_DIRECTORY / "qatr.txt").read_bytes()
        lines = raw.splitlines(keepends=True)
        self.assertEqual(docket["section_count"], 55)
        self.assertEqual(docket["extraction_obligation_count"], 187)
        cursor = 38
        reconstruction = bytearray()
        for section in docket["sections"]:
            self.assertEqual(section["line_start"], cursor)
            self.assertGreater(len(section["extraction_obligations"]), 0)
            reconstruction.extend(raw[section["start"]:section["end"]])
            cursor = section["line_end"] + 1
        self.assertEqual(cursor, 454)
        self.assertEqual(bytes(reconstruction), b"".join(lines[37:]))
        self.assertEqual(docket["sections_with_existing_narrow_bridge"], 30)
        self.assertEqual(docket["complete_section_count"], 0)

    def test_missing_qatr_semantic_section_cannot_hide_behind_byte_partition(self):
        self.reject(lambda d: d["qatr_semantic_docket"]["sections"].pop(26))

    def test_narrow_theorem_is_not_whole_section_proof(self):
        def forged(document):
            row = document["qatr_semantic_docket"]["sections"][1]
            row["section_complete"] = True
            row["existing_formal_references"][0]["source_translation_fidelity_proved"] = True
        self.reject(forged)

    def test_cannot_remove_a_semantic_exception_obligation(self):
        self.reject(lambda d: d["qatr_semantic_docket"]["sections"][38]["extraction_obligations"].pop())

    def test_uninstalled_receipt_ids_cannot_close_any_obligation(self):
        candidate = deepcopy(self.document)
        candidate["closure_receipts"] = {key: ["forged-kernel-success"] for key in MODULE.GATE_OBLIGATIONS}
        result = MODULE.closure_status(candidate)
        self.assertFalse(result["whole_book_strict_pass"])
        self.assertFalse(any(result["obligation_results"].values()))
        with self.assertRaises(ValueError):
            MODULE.validate_index(candidate)

    def test_same_length_source_mutation_is_detected_before_indexing(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "classical_rule_inventory_v1.json").write_bytes(
                (MODULE.SOURCE_DIRECTORY / "classical_rule_inventory_v1.json").read_bytes())
            source = bytearray((MODULE.SOURCE_DIRECTORY / "qatr.txt").read_bytes())
            source[0] = ord("!")
            (directory / "qatr.txt").write_bytes(source)
            with self.assertRaisesRegex(ValueError, "source identity changed: qatr"):
                MODULE.build_index(directory)

    def test_strict_cli_returns_failure_for_real_unclosed_scope(self):
        result = subprocess.run([sys.executable, str(ROOT / "tools/book_rule_coverage.py"),
                                 "--require-whole-book"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        summary = json.loads(result.stdout)
        self.assertTrue(summary["valid"])
        self.assertFalse(summary["whole_book_strict_pass"])


if __name__ == "__main__":
    unittest.main()
