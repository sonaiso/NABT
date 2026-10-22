import random
import unittest

from nabt.alphabet import CARRIERS, HARAKAT, cell_id, parse_word, render_word
from nabt.codec import (
    OccurrenceIdentity, append_numbers, decode_number, encode_cells, pack_cells,
    replace_cell, split_number, unpack_cells,
)
from nabt.errors import NabtError

from tests.oracle import CANONICAL, polynomial_number


class CodecTests(unittest.TestCase):
    def test_all_cells_have_unambiguous_carrier_state_identity(self):
        self.assertEqual(tuple(CARRIERS), CANONICAL)
        self.assertEqual(tuple(HARAKAT), tuple("َُِْ"))
        observed = set()
        for carrier_index, carrier in enumerate(CARRIERS):
            for state in range(4):
                value = cell_id(carrier, state)
                self.assertEqual(value, 4 * carrier_index + state)
                self.assertEqual(parse_word(carrier + HARAKAT[state]), (value,))
                self.assertEqual(render_word((value,)), carrier + HARAKAT[state])
                observed.add(value)
        self.assertEqual(observed, set(range(116)))

    def test_arithmetic_against_positional_sum_and_every_split(self):
        rng = random.Random(20261022)
        words = [(), (0,), (115,), (0, 0), (115, 115), (84, 8, 4), (85, 10, 4)]
        words += [tuple(rng.randrange(116) for _ in range(length)) for length in range(1, 25)]
        for cells in words:
            n = encode_cells(cells)
            self.assertEqual(n, polynomial_number(cells))
            self.assertEqual(decode_number(n), cells)
            for cut in range(len(cells) + 1):
                left, right = split_number(n, cut)
                self.assertEqual(left, polynomial_number(cells[:cut]))
                self.assertEqual(right, polynomial_number(cells[cut:]))
                self.assertEqual(append_numbers(left, right), n)
            for i in range(len(cells)):
                replacement = 115 - cells[i]
                expected = cells[:i] + (replacement,) + cells[i + 1:]
                changed = replace_cell(n, i, replacement)
                self.assertEqual(changed, polynomial_number(expected))
                self.assertEqual(changed - n, (replacement - cells[i]) * 116 ** (len(cells) - i - 1))

    def test_known_numbers_and_order_multiplicity(self):
        self.assertEqual(encode_cells((84, 8, 4)), 1_144_809)
        self.assertEqual(encode_cells((85, 10, 4)), 1_158_497)
        values = [encode_cells(x) for x in [(4,), (4, 4), (4, 8), (8, 4)]]
        self.assertEqual(len(set(values)), len(values))
        self.assertEqual(encode_cells(()), 0)
        self.assertEqual(decode_number(0), ())

    def test_all_seven_bit_codes_and_canonical_padding(self):
        header = b"NABT\x01" + (1).to_bytes(4, "big")
        for code in range(128):
            packet = header + bytes([code << 1])
            if code < 116:
                self.assertEqual(unpack_cells(packet), (code,))
                self.assertEqual(pack_cells((code,)), packet)
            else:
                with self.assertRaises(NabtError):
                    unpack_cells(packet)
        for code in range(116):
            with self.assertRaises(NabtError):
                unpack_cells(header + bytes([(code << 1) | 1]))
        for cells in [(), (0, 115, 0), tuple(range(116)), (84, 8, 4)]:
            self.assertEqual(unpack_cells(pack_cells(cells)), cells)

    def test_transport_rejects_truncation_extra_bytes_and_forged_count(self):
        packet = pack_cells((84, 8, 4))
        for truncated in [packet[:i] for i in range(len(packet))]:
            with self.assertRaises(NabtError):
                unpack_cells(truncated)
        for broken in [packet + b"\0", b"WRONG" + packet[5:], b"NABT\x01" + (2**32 - 1).to_bytes(4, "big")]:
            with self.assertRaises(NabtError):
                unpack_cells(broken)

    def test_numeric_arguments_reject_boolean_negative_and_wrong_types(self):
        for bad in [True, False, -1, 1.5, "1", None]:
            with self.subTest(argument=bad):
                with self.assertRaises(NabtError):
                    encode_cells((bad,))
                with self.assertRaises(NabtError):
                    decode_number(bad)
        for bad in [116, 127, 256]:
            with self.assertRaises(NabtError):
                encode_cells((bad,))
        for bad in [True, -1, 3]:
            with self.assertRaises(NabtError):
                split_number(encode_cells((4, 8)), bad)
        with self.assertRaises(NabtError):
            replace_cell(encode_cells((4,)), 1, 8)

    def test_occurrence_identity_is_scoped_not_only_a_local_number(self):
        a = OccurrenceIdentity("source-a", "analysis-v1", 2, 8)
        b = OccurrenceIdentity("source-b", "analysis-v1", 2, 8)
        c = OccurrenceIdentity("source-a", "analysis-v2", 2, 8)
        self.assertEqual(a.local_number, 240)
        self.assertEqual(a.local_number, b.local_number)
        self.assertNotEqual(a, b)
        self.assertNotEqual(a, c)
        for args in [("", "v1", 0, 8), ("s", "", 0, 8), ("s", "v1", -1, 8), ("s", "v1", True, 8), ("s", "v1", 0, 116)]:
            with self.assertRaises(NabtError):
                OccurrenceIdentity(*args)


class ParserTests(unittest.TestCase):
    def test_exact_fully_marked_word_roundtrips(self):
        for text in ["كَتَبَ", "كُتِبَ", "كَاْ", "دَحْرَجَ", "بَبَ", "ءَ", "اْ"]:
            self.assertEqual(render_word(parse_word(text)), text)

    def test_missing_mark_is_deferred_without_guessing(self):
        for text in ["كتب", "كَتبَ", "كَتَب", "ا"]:
            with self.assertRaises(NabtError) as caught:
                parse_word(text)
            self.assertEqual(caught.exception.status, "DEFER")

    def test_conflicting_or_duplicate_marks_have_no_precedence(self):
        for text in ["كَُ", "كَُ", "كَْ", "كَْ", "كََ", "َكَ"]:
            with self.assertRaises(NabtError):
                parse_word(text)

    def test_unsupported_features_are_not_silently_erased(self):
        for text in ["كَـتَبَ", "كَّ", "كً", "أَ", "ك\u200dَ", "كَ بَ", "كَ\nبَ", "", "\ud800"]:
            with self.assertRaises(NabtError):
                parse_word(text)


if __name__ == "__main__":
    unittest.main()
