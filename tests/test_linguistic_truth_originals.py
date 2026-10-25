"""Original replay boundaries; no private books or office installation required."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.linguistic_truth import verify_originals as replay


class OriginalReplayTests(unittest.TestCase):
    def setUp(self):
        # Each Arabic scalar occupies two UTF-8 bytes; each LF occupies one.
        self.original = b"\xd8\xa3\n\xd8\xa8\n"
        self.retained = b"\xd8\xa8\n"
        self.source = {"source_id": "fixture"}
        self.passage = {"source_id": "fixture", "start": 0, "end": 3,
                        "sha256": hashlib.sha256(self.retained).hexdigest(),
                        "original_start": 3, "original_end": 6, "paragraph": 2}

    def check(self, passage):
        return replay._check_passages(self.source, [passage], self.retained, self.original)

    def test_default_reports_retained_only(self):
        result = replay.verify()
        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "RETAINED_ONLY")
        self.assertFalse(result["originals_rechecked"])
        self.assertEqual(result["original_book_count"], 0)
        self.assertTrue(result["sources"])
        self.assertTrue(all(not s["original_ranges_rechecked"] for s in result["sources"]))
        self.assertFalse(result["world_truth_established"])

    def test_changed_original_rejected_before_conversion(self):
        with tempfile.TemporaryDirectory() as temporary:
            changed = Path(temporary) / "changed.docx"
            changed.write_bytes(b"not the registered original")
            with self.assertRaisesRegex(ValueError, "ORIGINAL_CHANGED"):
                replay.verify(part1=changed, part3=changed, thinking=changed)

    def test_partial_original_arguments_do_not_claim_a_recheck(self):
        with self.assertRaisesRegex(ValueError, "ALL_THREE_ORIGINALS_REQUIRED"):
            replay.verify(part1=Path("not-opened.docx"))

    def test_exact_original_range(self):
        self.assertEqual(self.check(self.passage), 1)

    def test_equal_length_wrong_original_range(self):
        changed = dict(self.passage, original_start=0, original_end=3)
        with self.assertRaisesRegex(ValueError, "ORIGINAL_PASSAGE_CHANGED"):
            self.check(changed)

    def test_right_bytes_wrong_paragraph(self):
        changed = dict(self.passage, paragraph=1)
        with self.assertRaisesRegex(ValueError, "ORIGINAL_UNIT_RANGE_CHANGED"):
            self.check(changed)

    def test_boolean_offsets_rejected(self):
        for field in ("start", "end", "original_start", "original_end", "paragraph"):
            with self.subTest(field=field):
                changed = dict(self.passage, **{field: True})
                with self.assertRaisesRegex(ValueError, "INVALID_NATURAL"):
                    self.check(changed)

    def test_utf8_mid_scalar_range_rejected(self):
        with self.assertRaises(UnicodeDecodeError):
            replay._range(self.original, 1, 3, "ORIGINAL")

    def test_uncovered_retained_suffix_rejected(self):
        with self.assertRaisesRegex(ValueError, "RETAINED_PASSAGE_COVERAGE_INCOMPLETE"):
            replay._check_passages(self.source, [self.passage], self.retained + b"!", self.original)

    def test_wrong_work_binding_rejected(self):
        changed = dict(self.passage, source_id="another-source")
        with self.assertRaisesRegex(ValueError, "PASSAGE_SOURCE_MISMATCH"):
            self.check(changed)

    def test_canonical_docx_retains_empty_and_table_paragraphs(self):
        xml = b'''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:body><w:p><w:r><w:t>A</w:t></w:r><w:r><w:t> B</w:t></w:r></w:p>
          <w:p/><w:tbl><w:tr><w:tc><w:p><w:r><w:t>C</w:t></w:r></w:p>
          </w:tc></w:tr></w:tbl></w:body></w:document>'''
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", xml)
            self.assertEqual(replay._docx_text(path), (b"A B\n\nC\n", 3))


if __name__ == "__main__":
    unittest.main()
