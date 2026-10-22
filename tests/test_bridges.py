"""Independent spelling, positional-sum and interval-decode bridge oracles."""

import json
import random
import unittest

from nabt.alphabet import ALPHABET_ID, MAX_CELLS
from nabt.bridges import (
    ALGHANEM_BRIDGE_ALPHABET_ID, ALGHANEM_CANONICAL_ALPHABET_ID,
    ALGHANEM_CANONICAL_NUMBER_CODEC, ALGHANEM_NUMBER_CODEC,
    ALPHABET_REGISTRY, CODEC_REGISTRY, MASHRU_ALPHABET_ID, MASHRU_NUMBER_CODEC,
    NABT_CELLS_CODEC, NABT_FRAME_CODEC, NABT_NUMBER_CODEC,
    SLGE_ALPHABET_ID, SLGE_NUMBER_CODEC,
    cell_parts, convert_bytes, convert_cell, convert_cells, convert_number,
    decode_bytes, decode_number, encode_bytes, encode_number,
    get_alphabet, get_codec, render_cells, transcode,
)
from nabt.errors import NabtError
from nabt.machine import Machine


# These declarations are intentionally independent of the installed registry.
ORDERS = {
    ALPHABET_ID: "ابتثجحخدذرزسشصضطظعغفقكلمنهويء",
    ALGHANEM_CANONICAL_ALPHABET_ID: "ابتثجحخدذرزسشصضطظعغفقكلمنهويء",
    ALGHANEM_BRIDGE_ALPHABET_ID: "ءبتثجحخدذرزسشصضطظعغفقكلمنهويا",
    MASHRU_ALPHABET_ID: "ءهاعحغخقكجشيضلنرطدتزسصظذثفبمو",
    SLGE_ALPHABET_ID: "ءهاعحغخقكجشيضلنرطدتزسصظذثفبمو",
}
MARKS = "َُِْ"
NUMBER_CODECS = {
    NABT_NUMBER_CODEC: (ALPHABET_ID, "big"),
    ALGHANEM_CANONICAL_NUMBER_CODEC: (ALGHANEM_CANONICAL_ALPHABET_ID, "big"),
    ALGHANEM_NUMBER_CODEC: (ALGHANEM_BRIDGE_ALPHABET_ID, "big"),
    MASHRU_NUMBER_CODEC: (MASHRU_ALPHABET_ID, "big"),
    SLGE_NUMBER_CODEC: (SLGE_ALPHABET_ID, "little"),
}


def spelling(cells, alphabet):
    table = tuple(carrier + mark for carrier in ORDERS[alphabet] for mark in MARKS)
    return "".join(table[cell] for cell in cells)


def spelling_cells(text, alphabet):
    table = tuple(carrier + mark for carrier in ORDERS[alphabet] for mark in MARKS)
    return tuple(table.index(text[i:i + 2]) for i in range(0, len(text), 2))


def polynomial(cells, direction="big"):
    count = len(cells)
    return sum((cell + 1) * 116 ** (i if direction == "little" else count - i - 1)
               for i, cell in enumerate(cells))


def interval_decode(number, direction="big"):
    # Locate the fixed-length block, remove its geometric offset, then read
    # ordinary positional digits. No subtract-one recurrence is reused.
    length = 0
    while number >= sum(116 ** i for i in range(length + 1)):
        length += 1
    digits = number - sum(116 ** i for i in range(length))
    cells = tuple((digits // 116 ** (length - i - 1)) % 116 for i in range(length))
    return cells[::-1] if direction == "little" else cells


class BridgeRegistryTests(unittest.TestCase):
    def test_registry_is_immutable_and_source_pins_are_exact(self):
        with self.assertRaises(TypeError):
            ALPHABET_REGISTRY["forged"] = get_alphabet(ALPHABET_ID)
        with self.assertRaises(TypeError):
            CODEC_REGISTRY["forged"] = get_codec(NABT_NUMBER_CODEC)
        with self.assertRaises(AttributeError):
            get_alphabet(ALPHABET_ID).carriers = tuple(reversed(ORDERS[ALPHABET_ID]))
        with self.assertRaises(AttributeError):
            get_codec(NABT_NUMBER_CODEC).encoding = "forged"
        with self.assertRaises(AttributeError):
            object.__setattr__(get_alphabet(ALPHABET_ID), "alphabet_id", "forged")
        with self.assertRaises(AttributeError):
            object.__setattr__(get_alphabet(ALPHABET_ID), "carriers", ())
        with self.assertRaises(AttributeError):
            object.__setattr__(get_codec(NABT_NUMBER_CODEC), "codec_id", "forged")
        with self.assertRaises(AttributeError):
            object.__setattr__(get_codec(NABT_NUMBER_CODEC), "encoding", "forged")
        pins = [pin for spec in ALPHABET_REGISTRY.values() for pin in spec.sources]
        pins += [pin for spec in CODEC_REGISTRY.values() for pin in spec.sources]
        expected = {
            "Saleh1967/Alghanem": "9d8fa03a51f894416e0abaf3b6821c5ae6441dcd",
            "Saleh1967/Mashru": "e4c801ffe9171dadedcc3aae23051ea0953ae361",
        }
        self.assertGreaterEqual(len({pin.path for pin in pins}), 10)
        for pin in pins:
            self.assertEqual(pin.commit, expected[pin.repository])
            self.assertRegex(pin.sha256, r"^[0-9a-f]{64}$")
            self.assertIn(f"/blob/{pin.commit}/", pin.url)
            self.assertTrue(pin.definitions)
            with self.assertRaises(AttributeError):
                pin.commit = "forged"
            with self.assertRaises(AttributeError):
                object.__setattr__(pin, "commit", "forged")

    def test_every_installed_alphabet_is_an_explicit_116_identity_table(self):
        self.assertEqual(set(ALPHABET_REGISTRY), set(ORDERS))
        for alphabet, order in ORDERS.items():
            self.assertEqual(get_alphabet(alphabet).carriers, tuple(order))
            self.assertEqual(get_alphabet(alphabet).marks, tuple(MARKS))
            self.assertEqual(get_alphabet(alphabet).size, 116)
            self.assertEqual(get_alphabet(alphabet).as_dict()["scope"], "ENCODING_ONLY")
        for spec in CODEC_REGISTRY.values():
            self.assertEqual(spec.as_dict()["domain"], "cell-sequence")
            self.assertIn(spec.alphabet_id, ORDERS)
        self.assertIn("NOT Ladder.wordEnc", get_codec(SLGE_NUMBER_CODEC).description)
        self.assertEqual(get_codec(ALGHANEM_CANONICAL_NUMBER_CODEC).origin, "NABT")

    def test_unknown_and_unspecified_registries_are_rejected(self):
        for bad in (None, "", "SLGE", "A116", "utf-8", "mashru.slge.wordEnc", True, 1, [], {}):
            with self.subTest(bad=bad):
                for reader in (get_alphabet, get_codec):
                    with self.assertRaises(NabtError):
                        reader(bad)
                with self.assertRaises(NabtError):
                    transcode(0, bad, NABT_NUMBER_CODEC)
                with self.assertRaises(NabtError):
                    transcode(0, NABT_NUMBER_CODEC, bad)


class CellBridgeTests(unittest.TestCase):
    def test_all_116_cells_in_every_pair_of_alphabets(self):
        for source in ORDERS:
            for target in ORDERS:
                mapped = convert_cells(range(116), source, target)
                self.assertEqual(set(mapped), set(range(116)))
                self.assertEqual(convert_cells(mapped, target, source), tuple(range(116)))
                for cell, result in enumerate(mapped):
                    text = spelling((cell,), source)
                    self.assertEqual(spelling((result,), target), text)
                    self.assertEqual(cell_parts(cell, source), tuple(text))
                    self.assertEqual(convert_cell(cell, source, target), result)
                    self.assertEqual(result % 4, cell % 4)

    def test_alghanem_eight_differences_are_exactly_hamza_and_alif(self):
        mapping = convert_cells(range(116), ALGHANEM_BRIDGE_ALPHABET_ID, ALPHABET_ID)
        different = [i for i in range(116) if mapping[i] != i]
        self.assertEqual(different, list(range(4)) + list(range(112, 116)))
        self.assertEqual(mapping[:4], (112, 113, 114, 115))
        self.assertEqual(mapping[-4:], (0, 1, 2, 3))

    def test_sequences_preserve_positions_repeats_and_append(self):
        words = [(), (0,), (115,), (0, 0), (115, 115), (0, 115, 0, 115),
                 tuple(range(116)), tuple(reversed(range(116)))]
        rng = random.Random(20261023)
        words += [tuple(rng.randrange(116) for _ in range(n)) for n in range(1, 25)]
        for source in ORDERS:
            for target in ORDERS:
                for cells in words:
                    expected = spelling(cells, source)
                    mapped = convert_cells(cells, source, target)
                    self.assertEqual(len(mapped), len(cells))
                    self.assertEqual(mapped, spelling_cells(expected, target))
                    self.assertEqual(render_cells(mapped, target), expected)
                    for cut in {0, 1, len(cells) // 2, len(cells)}:
                        self.assertEqual(mapped, convert_cells(cells[:cut], source, target)
                                         + convert_cells(cells[cut:], source, target))


class NumericBridgeTests(unittest.TestCase):
    def test_every_singleton_and_two_cell_code_against_independent_oracles(self):
        # Exhaust all length-0, length-1 and length-2 codes, including the
        # transition 0 -> 1, 116 -> 117 and every zero/maximum cell position.
        for codec, (_, direction) in NUMBER_CODECS.items():
            for number in range(1 + 116 + 116 ** 2):
                cells = interval_decode(number, direction)
                self.assertEqual(decode_number(number, codec), cells)
                self.assertEqual(encode_number(cells, codec), polynomial(cells, direction))
                self.assertEqual(polynomial(cells, direction), number)

    def test_numbers_across_alphabets_and_endianness(self):
        numbers = [0, 1, 2, 4, 112, 113, 115, 116, 117, 118, 13572, 13573]
        for length in range(1, 25):
            offset = sum(116 ** i for i in range(length))
            numbers.extend((offset - 1, offset, offset + 1, offset + 116 ** length - 1))
        rng = random.Random(90419)
        numbers += [rng.randrange(116 ** rng.randrange(1, 25)) for _ in range(80)]
        for source, (source_alpha, source_direction) in NUMBER_CODECS.items():
            for target, (target_alpha, target_direction) in NUMBER_CODECS.items():
                for number in numbers:
                    source_cells = interval_decode(number, source_direction)
                    text = spelling(source_cells, source_alpha)
                    expected_cells = spelling_cells(text, target_alpha)
                    result = convert_number(number, source, target)
                    self.assertEqual(result.source_cells, source_cells)
                    self.assertEqual(result.target_cells, expected_cells)
                    self.assertEqual(result.value, polynomial(expected_cells, target_direction))
                    self.assertEqual(result.rendered, text)
                    self.assertEqual(convert_number(result.value, target, source).value, number)
                    self.assertEqual(result.authority, "ENCODING_ONLY")

    def test_same_number_is_not_same_identity_and_mashru_kataba(self):
        self.assertEqual(convert_number(1, ALGHANEM_NUMBER_CODEC, NABT_NUMBER_CODEC).value, 113)
        self.assertEqual(convert_number(1, NABT_NUMBER_CODEC, ALGHANEM_NUMBER_CODEC).value, 113)
        self.assertEqual(convert_number(0, ALGHANEM_NUMBER_CODEC, NABT_NUMBER_CODEC).value, 0)
        result = convert_number(452621, MASHRU_NUMBER_CODEC, NABT_NUMBER_CODEC)
        self.assertEqual(result.rendered, "كَتَبَ")
        self.assertEqual(result.source_cells, (32, 72, 104))
        self.assertEqual(result.target_cells, (84, 8, 4))
        self.assertEqual(result.value, 1144809)
        slge = convert_number(452621, MASHRU_NUMBER_CODEC, SLGE_NUMBER_CODEC)
        self.assertEqual(slge.target_cells, (32, 72, 104))
        self.assertEqual(slge.value, 33 + 73 * 116 + 105 * 116 ** 2)
        self.assertNotEqual(slge.value, 452621)


class ByteBridgeTests(unittest.TestCase):
    def test_all_byte_codecs_against_independent_render_and_bit_oracle(self):
        words = [(), (0,), (115,), (0, 0), (0, 115, 0), (84, 8, 4), tuple(range(116))]
        for codec, spec in CODEC_REGISTRY.items():
            if spec.kind != "bytes":
                continue
            for cells in words + [(i,) for i in range(116)]:
                encoded = encode_bytes(cells, codec)
                if spec.encoding == "u8":
                    expected = bytes(cells)
                elif spec.encoding == "utf8-pairs":
                    expected = spelling(cells, spec.alphabet_id).encode("utf-8")
                else:
                    bits = "".join(f"{cell:07b}" for cell in cells)
                    bits += "0" * (-len(bits) % 8)
                    expected = b"NABT\x01" + len(cells).to_bytes(4, "big")
                    expected += bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
                self.assertEqual(encoded, expected)
                self.assertEqual(decode_bytes(expected, codec), cells)

    def test_all_codec_types_transcode_and_reverse_with_source_identity(self):
        text = "ءَاْكَتَبَءُاِ"
        for source, source_spec in CODEC_REGISTRY.items():
            cells = spelling_cells(text, source_spec.alphabet_id)
            if source_spec.kind == "number":
                value = encode_number(cells, source)
            elif source_spec.kind == "bytes":
                value = encode_bytes(cells, source)
            else:
                value = cells
            for target in CODEC_REGISTRY:
                result = transcode(value, source, target)
                self.assertEqual(result.rendered, text)
                self.assertEqual(transcode(result.value, target, source).value, value)
                self.assertEqual(result.authority, "ENCODING_ONLY")
                json.dumps(result.as_dict())

    def test_frame_rejects_all_reserved_cells_and_nonzero_padding(self):
        header = b"NABT\x01" + (1).to_bytes(4, "big")
        for cell in range(128):
            if cell >= 116:
                with self.assertRaises(NabtError):
                    decode_bytes(header + bytes((cell << 1,)), NABT_FRAME_CODEC)
            with self.assertRaises(NabtError) as caught:
                decode_bytes(header + bytes(((cell << 1) | 1,)), NABT_FRAME_CODEC)
            self.assertEqual(caught.exception.code, "NON_CANONICAL_PADDING")
        frame = encode_bytes((0, 115, 0), NABT_FRAME_CODEC)
        for bad in [frame[:i] for i in range(len(frame))] + [frame + b"\x00"]:
            with self.assertRaises(NabtError):
                decode_bytes(bad, NABT_FRAME_CODEC)

    def test_u8_rejects_all_reserved_bytes(self):
        for codec, spec in CODEC_REGISTRY.items():
            if spec.encoding != "u8":
                continue
            for cell in range(116, 256):
                with self.assertRaises(NabtError):
                    decode_bytes(bytes((cell,)), codec)

    def test_utf8_rejects_noncanonical_source_instead_of_normalizing(self):
        bad_sources = [b"\xff", b"\xc0\x80", b"\xed\xa0\x80", b"\xef\xbb\xbf"]
        bad_sources += [s.encode("utf-8") for s in
                        ["كَـتَبَ", "كَّ", "كً", "أَ", "ا", "كََ", "َكَ", "كَ بَ", "ك\u200dَ"]]
        for codec, spec in CODEC_REGISTRY.items():
            if spec.encoding == "utf8-pairs":
                for bad in bad_sources:
                    with self.assertRaises(NabtError):
                        decode_bytes(bad, codec)
                self.assertEqual(decode_bytes(b"", codec), ())


class BridgeBoundaryTests(unittest.TestCase):
    def test_strict_integer_and_kind_boundaries(self):
        bad_cells = (True, False, -1, 116, 1.0, "1", None)
        for bad in bad_cells:
            with self.assertRaises(NabtError):
                convert_cell(bad, ALPHABET_ID, SLGE_ALPHABET_ID)
            with self.assertRaises(NabtError):
                convert_cells((bad,), ALPHABET_ID, SLGE_ALPHABET_ID)
            with self.assertRaises(NabtError):
                encode_number((bad,), NABT_NUMBER_CODEC)
            with self.assertRaises(NabtError):
                encode_bytes((bad,), NABT_FRAME_CODEC)
        for bad in (True, False, -1, 1.0, "1", None):
            for codec in NUMBER_CODECS:
                with self.assertRaises(NabtError):
                    decode_number(bad, codec)
        for bad in (b"\0", bytearray((0,)), "0", None, True):
            with self.assertRaises(NabtError):
                transcode(bad, NABT_CELLS_CODEC, NABT_NUMBER_CODEC)
        for bad in (bytearray(), memoryview(b""), "", None, True):
            with self.assertRaises(NabtError):
                decode_bytes(bad, NABT_FRAME_CODEC)
        with self.assertRaises(NabtError):
            decode_number(0, NABT_FRAME_CODEC)
        with self.assertRaises(NabtError):
            encode_bytes((), NABT_NUMBER_CODEC)
        with self.assertRaises(NabtError):
            convert_number(0, NABT_NUMBER_CODEC, NABT_FRAME_CODEC)
        with self.assertRaises(NabtError):
            convert_bytes(b"", "nabt.u8.nabt.v1", NABT_NUMBER_CODEC)

    def test_maximum_cells_and_resource_exhaustion_are_distinct(self):
        cells = (115,) * MAX_CELLS
        for codec in NUMBER_CODECS:
            number = encode_number(cells, codec)
            self.assertEqual(decode_number(number, codec), cells)
            converted = convert_number(number, codec, NABT_NUMBER_CODEC)
            self.assertEqual(converted.as_dict()["value_encoding"], "hex")
            json.dumps(converted.as_dict())
        cases = [lambda: convert_cells(cells + (0,), ALPHABET_ID, SLGE_ALPHABET_ID),
                 lambda: decode_number(1 << (7 * MAX_CELLS + 2), NABT_NUMBER_CODEC),
                 lambda: decode_bytes(b"\0" * (MAX_CELLS + 1), "nabt.u8.nabt.v1"),
                 lambda: decode_bytes("بَ".encode("utf-8") * (MAX_CELLS + 1),
                                      "nabt.utf8-pairs.nabt.v1"),
                 lambda: decode_bytes(b"NABT\x01" + (MAX_CELLS + 1).to_bytes(4, "big"),
                                      NABT_FRAME_CODEC)]
        for call in cases:
            with self.assertRaises(NabtError) as caught:
                call()
            self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")
            self.assertEqual(caught.exception.status, "DEFER")

    def test_total_mapping_does_not_grant_shape_or_meaning_authority(self):
        # A leading sukun and a mismatching alif closure are numerically valid.
        for text in ("بْ", "كُاْ"):
            cells = spelling_cells(text, ALPHABET_ID)
            numeric = encode_number(cells, NABT_NUMBER_CODEC)
            result = convert_number(numeric, NABT_NUMBER_CODEC, MASHRU_NUMBER_CODEC)
            self.assertEqual(result.rendered, text)
            self.assertEqual(result.authority, "ENCODING_ONLY")
            self.assertEqual(result.as_dict()["scope"], "ENCODING_ONLY")
            self.assertNotIn("accepted", result.as_dict())
            self.assertNotIn("meaning", result.as_dict())
            self.assertFalse(Machine().analyse(cells).licensed)


if __name__ == "__main__":
    unittest.main()
