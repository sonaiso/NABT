"""Independent byte, alphabet and numeric oracles for the source boundary."""
from copy import deepcopy
import json
import unittest

from nabt.errors import NabtError
from tools.source_codec import encode_source, restore_source, verify_source, word_view
from nabt.codec import decode_number, unpack_cells


class SourceCodecTests(unittest.TestCase):
    def test_exact_bytes_including_marks_bom_controls_and_line_endings(self):
        samples = [b"", b"\xef\xbb\xbfA\r\nB\n", b"a\0b", "كَتَبَ\tكُتِبَ".encode(),
                   "أَ ا\u0654َ كَـتَبَ ك\u200dَ 👋".encode()]
        for raw in samples:
            envelope = encode_source(raw, identity="source", revision="r2", scope="scope")
            self.assertEqual(restore_source(envelope), raw)
            self.assertEqual(bytes.fromhex(envelope["raw_hex"]), raw)
            self.assertTrue(verify_source(raw, envelope, identity="source", revision="r2", scope="scope"))
        self.assertNotEqual(encode_source("أَ".encode())["sha256"],
                            encode_source("ا\u0654َ".encode())["sha256"])

    def test_a_self_consistent_substitution_is_not_source_authority(self):
        forged = encode_source(b"different", identity="other")
        self.assertEqual(restore_source(forged), b"different")
        with self.assertRaises(NabtError) as caught:
            verify_source(b"original", forged)
        self.assertEqual(caught.exception.code, "SOURCE_BINDING_MISMATCH")

    def test_types_hashes_extra_fields_and_binding_cannot_be_forged(self):
        base = encode_source(b"a")
        changes = [("byte_length", True), ("byte_length", 1.0), ("byte_length", 2),
                   ("sha256", "0" * 64), ("normalization", "NFC"), ("extra", "claim"),
                   ("raw_hex", "61 "), ("raw_hex", "F0"), ("raw_hex", "6")]
        for field, value in changes:
            changed = deepcopy(base)
            changed[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(NabtError):
                restore_source(changed)
        for field in ("source_id", "revision", "scope"):
            changed = deepcopy(base)
            changed["binding"][field] = "other"
            with self.assertRaises(NabtError):
                verify_source(b"a", changed)

    def test_invalid_utf8_and_resource_errors_are_distinct(self):
        for value, code in ((b"\xff", "INVALID_UTF8"), ("text", "INVALID_BYTES"),
                            (b"a" * 65537, "RESOURCE_LIMIT")):
            with self.assertRaises(NabtError) as caught:
                encode_source(value)
            self.assertEqual(caught.exception.code, code)
        self.assertEqual(len(restore_source(encode_source(b"a" * 65536))), 65536)

    def test_each_of_116_identities_against_literal_registry(self):
        carriers = "ابتثجحخدذرزسشصضطظعغفقكلمنهويء"
        marks = "َُِْ"  # Pinned existing order, not changed to another convention.
        for i, letter in enumerate(carriers):
            for j, mark in enumerate(marks):
                view = word_view((letter + mark).encode())
                value = i * 4 + j
                self.assertEqual(view["cells"], [value])
                self.assertEqual(int(view["number_hex"], 16), value + 1)
                self.assertEqual(unpack_cells(bytes.fromhex(view["packed_hex"])), (value,))
                self.assertFalse(view["linguistic_admissibility_established"])

    def test_known_word_and_long_number_transport_without_decimal_conversion(self):
        view = word_view("كَتَبَ".encode())
        self.assertEqual(view["cells"], [84, 8, 4])
        self.assertEqual(int(view["number_hex"], 16), 1_144_809)
        self.assertEqual(decode_number(int(view["number_hex"], 16)), (84, 8, 4))
        long_view = word_view(("بَ" * 4096).encode())
        self.assertEqual(len(long_view["cells"]), 4096)
        self.assertEqual(len(decode_number(int(long_view["number_hex"], 16))), 4096)
        json.dumps(long_view, allow_nan=False)

    def test_no_missing_marks_or_orthography_are_invented(self):
        for text, outcome, code in (("كتب", "DEFER", "MISSING_VOCALIZATION"),
                ("أَ", "DEFER", "UNSUPPORTED_ORTHOGRAPHY"),
                ("كَّ", "DEFER", "UNSUPPORTED_ORTHOGRAPHY"),
                ("كَُ", "REJECT", "CONFLICTING_MARKS"),
                ("كَ بَ", "REJECT", "WORD_BOUNDARY_NOT_ALLOWED")):
            result = word_view(text.encode())
            self.assertEqual((result["outcome"], result["error"]), (outcome, code))
            self.assertNotIn("cells", result)
            self.assertEqual(restore_source(result["source"]), text.encode())


if __name__ == "__main__":
    unittest.main()
