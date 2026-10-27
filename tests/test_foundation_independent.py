"""Independent A116 boundary checks; these are regressions, not a blind corpus.

Expected cells are an explicit spelling table, never the production registry.
Expected numbers use a positional sum, never the production recurrence. Native
tests skip only when no executable was requested and the default is absent.
NABT_FOUNDATION_EXECUTABLE makes a missing executable a hard failure.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock, patch

from nabt import foundation
from nabt.alphabet import parse_word, render_word
from nabt.codec import decode_number, encode_cells, unpack_cells
from nabt.errors import NabtError
from nabt.machine import Machine


ROOT = Path(__file__).resolve().parents[1]
ALPHABET = "nabt.a116.v1"
LAW = "nabt.foundation.v1"
NUMBER_DOMAIN = "nabt.foundation.projected-cells.bijective116.v1"

# Fixed independently of Cell.encode, Python's registry and generated exports.
CELL_TABLE = (
    "اَ", "اُ", "اِ", "اْ", "بَ", "بُ", "بِ", "بْ",
    "تَ", "تُ", "تِ", "تْ", "ثَ", "ثُ", "ثِ", "ثْ",
    "جَ", "جُ", "جِ", "جْ", "حَ", "حُ", "حِ", "حْ",
    "خَ", "خُ", "خِ", "خْ", "دَ", "دُ", "دِ", "دْ",
    "ذَ", "ذُ", "ذِ", "ذْ", "رَ", "رُ", "رِ", "رْ",
    "زَ", "زُ", "زِ", "زْ", "سَ", "سُ", "سِ", "سْ",
    "شَ", "شُ", "شِ", "شْ", "صَ", "صُ", "صِ", "صْ",
    "ضَ", "ضُ", "ضِ", "ضْ", "طَ", "طُ", "طِ", "طْ",
    "ظَ", "ظُ", "ظِ", "ظْ", "عَ", "عُ", "عِ", "عْ",
    "غَ", "غُ", "غِ", "غْ", "فَ", "فُ", "فِ", "فْ",
    "قَ", "قُ", "قِ", "قْ", "كَ", "كُ", "كِ", "كْ",
    "لَ", "لُ", "لِ", "لْ", "مَ", "مُ", "مِ", "مْ",
    "نَ", "نُ", "نِ", "نْ", "هَ", "هُ", "هِ", "هْ",
    "وَ", "وُ", "وِ", "وْ", "يَ", "يُ", "يِ", "يْ",
    "ءَ", "ءُ", "ءِ", "ءْ",
)


def polynomial(cells):
    return sum((cell + 1) * 116 ** (len(cells) - i - 1)
               for i, cell in enumerate(cells))


def decimal_chunks(decimal):
    """Read large decimal values without changing Python's process-wide limit."""
    return sum(int(decimal[start:start + 9]) * 10 ** (len(decimal) - min(start + 9, len(decimal)))
               for start in range(0, len(decimal), 9))


def source(text, identity="independent", revision="1"):
    return {"id": identity, "revision": revision, "text": text}


def project(text, identity="independent", revision="1"):
    return foundation.inspect_source(text, source_id=identity, revision=revision)


class FoundationIndependentTests(unittest.TestCase):
    def assert_projection(self, receipt, text, *, status, cells):
        raw = text.encode("utf-8")
        self.assertEqual(receipt["alphabet_id"], ALPHABET)
        self.assertEqual(receipt["law_id"], LAW)
        self.assertEqual(receipt["number_domain"], NUMBER_DOMAIN)
        self.assertEqual(receipt["source"]["text"], text)
        self.assertEqual(receipt["raw_utf8"], list(raw))
        self.assertEqual(receipt["status"], status)
        self.assertEqual(receipt["cells"], list(cells))
        self.assertEqual(receipt["number"], str(polynomial(cells)))
        cursor, recovered, projected = 0, [], []
        for piece in receipt["pieces"]:
            self.assertEqual(piece["start_byte"], cursor)
            self.assertGreater(piece["end_byte"], cursor)
            part = raw[cursor:piece["end_byte"]]
            self.assertEqual(part.decode("utf-8"), piece["text"])
            recovered.append(part)
            cursor = piece["end_byte"]
            if piece["kind"] == "cell":
                self.assertIs(type(piece["cell"]), int)
                self.assertIn(piece["cell"], range(116))
                self.assertEqual(piece["text"], CELL_TABLE[piece["cell"]])
                projected.append(piece["cell"])
            else:
                self.assertIn(piece["kind"], {"separator", "residual"})
                self.assertIsNone(piece["cell"])
        self.assertEqual(cursor, len(raw))
        self.assertEqual(b"".join(recovered), raw)
        self.assertEqual(projected, list(cells))
        for issue in receipt["issues"]:
            self.assertGreaterEqual(issue["start_byte"], 0)
            self.assertLessEqual(issue["end_byte"], len(raw))
            self.assertLessEqual(issue["start_byte"], issue["end_byte"])
        # Checking the representation must never become a semantic assertion.
        for flag in ("meaning_established", "world_truth_established",
                     "sound_licensed", "linguistic_licensed", "all_arabic_complete"):
            self.assertIsNot(receipt.get(flag), True, flag)

    def test_fixed_table_has_116_unique_observed_spellings(self):
        self.assertEqual(len(CELL_TABLE), 116)
        self.assertEqual(len(set(CELL_TABLE)), 116)
        for cell, spelling in enumerate(CELL_TABLE):
            with self.subTest(cell=cell):
                self.assertEqual(parse_word(spelling), (cell,))
                self.assertEqual(render_word((cell,)), spelling)
                self.assert_projection(project(spelling), spelling,
                                       status="COMPLETE", cells=[cell])

    def test_foundation_guard_reports_representation_identity_only(self):
        identity = foundation.require_foundation("independent.test")
        self.assertEqual(identity["foundation_id"], LAW)
        self.assertEqual(identity["alphabet_id"], ALPHABET)
        self.assertEqual(identity["shape_law_id"], "nabt-sound-shape-v1")
        self.assertEqual(identity["alphabet_size"], 116)
        self.assertEqual(identity["authority"], "REPRESENTATION_FOUNDATION_ONLY")
        self.assertRegex(identity["law_table_sha256"], r"^[0-9a-f]{64}$")
        self.assertNotIn("native_checked", identity)
        for bad in ("", True, 1, None, "../foreign", "x" * 257):
            with self.subTest(value=bad):
                with self.assertRaises(NabtError):
                    foundation.require_foundation(bad)

    def test_warm_cache_does_not_hide_changed_installed_law(self):
        foundation.require_foundation("independent.warm")
        raw = (ROOT / "src/nabt/data/law.json").read_bytes()
        altered = bytearray(raw)
        altered[len(altered) // 2] ^= 1
        fake_package = Mock()
        fake_package.joinpath.return_value.read_bytes.return_value = bytes(altered)
        with patch.object(foundation, "files", return_value=fake_package):
            for operation in (lambda: foundation.require_foundation("independent.changed"),
                              lambda: project("كَتَبَ")):
                with self.assertRaises(NabtError) as caught:
                    operation()
                self.assertEqual(caught.exception.code, "FOUNDATION_INTEGRITY")
        # The test replaces only the reader; installed bytes were not modified.
        self.assertEqual((ROOT / "src/nabt/data/law.json").read_bytes(), raw)

    def test_missing_installed_law_is_unavailable_not_linguistically_false(self):
        fake_package = Mock()
        fake_package.joinpath.return_value.read_bytes.side_effect = FileNotFoundError("missing")
        with patch.object(foundation, "files", return_value=fake_package):
            with self.assertRaises(NabtError) as caught:
                project("كَتَبَ")
        self.assertEqual(caught.exception.code, "FOUNDATION_UNAVAILABLE")
        self.assertEqual(caught.exception.status, "DEFER")

    def test_numeric_projection_uses_closed_positional_sum(self):
        samples = [(), (0,), (115,), (0, 0), (115, 0), (0, 115),
                   (84, 8, 4), (81, 95, 9), tuple(range(116)),
                   tuple(reversed(range(116)))]
        # Deterministic mixed sequences, not examples generated by the encoder.
        samples += [tuple((37 * i + 11 * n) % 116 for i in range(n))
                    for n in (2, 7, 31, 127)]
        for cells in samples:
            with self.subTest(length=len(cells), prefix=cells[:3]):
                number = polynomial(cells)
                self.assertEqual(encode_cells(cells), number)
                self.assertEqual(decode_number(number), cells)
                if cells:
                    text = "".join(CELL_TABLE[c] for c in cells)
                    self.assert_projection(project(text), text,
                                           status="COMPLETE", cells=cells)

    def test_numeric_cell_domain_never_accepts_model_ids_or_booleans(self):
        for bad in (True, False, -1, 116, 127, 15366, "84", 84.0, None):
            with self.subTest(value=bad):
                with self.assertRaises(NabtError):
                    encode_cells((bad,))

    def test_all_unused_seven_bit_values_are_rejected(self):
        header = b"NABT\x01" + (1).to_bytes(4, "big")
        for cell in range(116, 128):
            with self.subTest(cell=cell):
                with self.assertRaises(NabtError):
                    unpack_cells(header + bytes([cell << 1]))

    def test_partial_vocalization_keeps_residuals_without_fake_cells(self):
        for text, expected in (("كتب", []), ("كَتبَ", [84, 4]),
                               ("كَتَب", [84, 8]), ("ك", [])):
            with self.subTest(text=text):
                receipt = project(text)
                self.assert_projection(receipt, text, status="PARTIAL", cells=expected)
                self.assertTrue(receipt["issues"])
                self.assertTrue(any(p["kind"] == "residual" for p in receipt["pieces"]))
                foundation.validate_source(text)

    def test_unsupported_clusters_are_preserved_as_whole_residuals(self):
        # Shadda/tanwin/hamza carriers have no silently erased bridge here.
        for text in ("بَّ", "بَّ", "بً", "أَ", "إِ", "ؤُ", "ئِ", "آ", "ٱ", "ى", "ة", "بَٰ"):
            with self.subTest(text=text):
                receipt = project(text)
                self.assert_projection(receipt, text, status="PARTIAL", cells=[])
                self.assertTrue(receipt["issues"])
                foundation.validate_source(text)

    def test_foreign_and_unmarked_source_survives_without_forced_alphabet(self):
        for text in ("Latin", "123", "😀", "ب\u200d", "كَـتَبَ"):
            with self.subTest(text=text):
                receipt = project(text)
                self.assertEqual(receipt["status"], "PARTIAL")
                self.assertEqual(receipt["raw_utf8"], list(text.encode()))
                self.assertEqual("".join(p["text"] for p in receipt["pieces"]), text)
                foundation.validate_source(text)

    def test_duplicate_and_conflicting_marks_never_yield_cluster_prefix_cell(self):
        for text in ("كَُ", "كَُ", "كَْ", "كَْ", "كََ", "كُُ", "كًَ", "كّّ", "َكَ"):
            with self.subTest(text=text):
                receipt = project(text)
                self.assertEqual(receipt["status"], "INVALID")
                self.assertTrue(receipt["issues"])
                self.assertEqual("".join(p["text"] for p in receipt["pieces"]), text)
                if not text.startswith("َ"):
                    self.assertEqual(receipt["cells"], [])
                    self.assertTrue(all(p["kind"] != "cell" for p in receipt["pieces"]))
                with self.assertRaises(NabtError):
                    foundation.validate_source(text)

    def test_corrupt_cluster_preserves_valid_neighbors_without_complete_claim(self):
        text = "بَكَُتِ"
        receipt = project(text)
        self.assert_projection(receipt, text, status="INVALID", cells=[4, 10])
        self.assertTrue(receipt["issues"])
        self.assertNotIn(84, receipt["cells"])

    def test_spaces_and_line_endings_are_source_pieces_not_cells(self):
        text = " \tقُمْتُ\r\nكَتَبَ "
        receipt = project(text)
        self.assert_projection(receipt, text, status="COMPLETE", cells=[81, 95, 9, 84, 8, 4])
        self.assertTrue(any(p["kind"] == "separator" for p in receipt["pieces"]))

    def test_no_unicode_normalization_or_diacritic_reordering(self):
        first, second = "بَّ", "بَّ"
        a, b = project(first), project(second)
        self.assertNotEqual(a["raw_utf8"], b["raw_utf8"])
        self.assertEqual(a["source"]["text"], first)
        self.assertEqual(b["source"]["text"], second)
        self.assertEqual(a["status"], "PARTIAL")
        self.assertEqual(b["status"], "PARTIAL")

    def test_empty_source_has_no_invented_word(self):
        receipt = project("")
        self.assert_projection(receipt, "", status="INVALID", cells=[])
        self.assertTrue(receipt["issues"])
        with self.assertRaises(NabtError):
            foundation.validate_source("")

    def test_invalid_unicode_and_nontext_are_not_silently_coerced(self):
        for text in ("\ud800", b"\xff", True, 17, None, ["كَ"]):
            with self.subTest(value=repr(text)):
                with self.assertRaises((NabtError, UnicodeError, ValueError, TypeError)):
                    project(text)

    def test_byte_source_and_string_source_have_identical_projection(self):
        text = "قُمْتُ، كَتَبَ"
        self.assertEqual(project(text.encode()), project(text))

    def test_packet_completeness_does_not_grant_sound_or_meaning(self):
        text = "اْ"
        receipt = project(text)
        self.assert_projection(receipt, text, status="COMPLETE", cells=[3])
        self.assertFalse(Machine("wasl").analyse((3,)).licensed)
        self.assertFalse(Machine("waqf").analyse((3,)).licensed)
        self.assertTrue(foundation.verify_source_receipt(receipt))
        self.assertNotIn("meaning", receipt)

    def test_same_projected_number_cannot_replace_source_identity_or_status(self):
        complete, partial, spaced = (project(text) for text in ("كَ", "كَب", "كَ "))
        self.assertEqual({r["number"] for r in (complete, partial, spaced)}, {"85"})
        self.assertEqual(complete["status"], "COMPLETE")
        self.assertEqual(partial["status"], "PARTIAL")
        self.assertNotEqual(complete["raw_utf8"], partial["raw_utf8"])
        self.assertNotEqual(complete["raw_utf8"], spaced["raw_utf8"])
        self.assertTrue(foundation.verify_source_receipt(partial))
        self.assertFalse(foundation.verify_source_receipt(partial, text="كَ"))

    def test_receipt_replay_rejects_every_changed_cell_and_number(self):
        receipt = project("كَتَبَ")
        self.assertTrue(foundation.verify_source_receipt(receipt))
        for key, value in (("cells", [84, 8, 5]), ("number", "0"),
                           ("number", receipt["number"].rjust(12, "0")),
                           ("raw_utf8", receipt["raw_utf8"][:-1]),
                           ("status", "PARTIAL"), ("issues", [{"code": "invented", "start_byte": 0, "end_byte": 0}])):
            broken = deepcopy(receipt)
            broken[key] = value
            with self.subTest(field=key, value=value):
                self.assertFalse(foundation.verify_source_receipt(broken))

    def test_receipt_replay_rejects_self_asserted_authority_and_wrong_domains(self):
        receipt = project("كَتَبَ")
        for key, value in (("native_checked", True), ("verified", True),
                           ("world_truth_established", True), ("alphabet_id", "mashru.a116.v1"),
                           ("law_id", "nabt-sound-shape-v1"), ("number_domain", "word-vocabulary")):
            broken = deepcopy(receipt)
            broken[key] = value
            with self.subTest(field=key):
                self.assertFalse(foundation.verify_source_receipt(broken))

    def test_receipt_replay_rejects_corrupt_span_and_kind(self):
        receipt = project("كَتَبَ")
        for field, value in (("start_byte", 1), ("end_byte", 3),
                             ("text", "كُ"), ("kind", "residual"), ("cell", True), ("cell", 116)):
            broken = deepcopy(receipt)
            broken["pieces"][0][field] = value
            with self.subTest(field=field, value=value):
                self.assertFalse(foundation.verify_source_receipt(broken))

    def test_boolean_is_not_cell_one_or_byte_offset_zero(self):
        receipt = project("اُ")
        self.assertEqual(receipt["cells"], [1])
        variants = []
        changed = deepcopy(receipt)
        changed["cells"] = [True]
        variants.append(changed)
        changed = deepcopy(receipt)
        changed["pieces"][0]["cell"] = True
        variants.append(changed)
        changed = deepcopy(receipt)
        changed["pieces"][0]["start_byte"] = False
        variants.append(changed)
        for changed in variants:
            self.assertFalse(foundation.verify_source_receipt(changed))

    def test_source_scope_is_retained_and_external_text_must_match(self):
        a = project("كَتَبَ", "a", "1")
        b = project("كَتَبَ", "b", "1")
        c = project("كَتَبَ", "a", "2")
        self.assertEqual(a["number"], b["number"])
        self.assertEqual(a["number"], c["number"])
        self.assertNotEqual(a["source"], b["source"])
        self.assertNotEqual(a["source"], c["source"])
        self.assertTrue(foundation.verify_source_receipt(a, text="كَتَبَ"))
        self.assertFalse(foundation.verify_source_receipt(a, text="كُتِبَ"))
        self.assertTrue(foundation.verify_source_receipt(a, source_id="a", revision="1"))
        self.assertFalse(foundation.verify_source_receipt(a, source_id="b", revision="1"))
        self.assertFalse(foundation.verify_source_receipt(a, source_id="a", revision="2"))
        # A receipt checks coherence, not a self-asserted source's authenticity.
        changed = deepcopy(a)
        changed["source"]["id"] = "b"
        self.assertFalse(foundation.verify_source_receipt(changed, source_id="a"))
        self.assertTrue(foundation.verify_source_receipt(changed, source_id="b"))
        for invalid in ("", True, 1, None):
            with self.subTest(identity=invalid):
                with self.assertRaises((NabtError, ValueError, TypeError)):
                    project("كَ", invalid)
                with self.assertRaises((NabtError, ValueError, TypeError)):
                    project("كَ", "a", invalid)

    def test_source_identity_limits_and_controls_are_not_silently_trimmed(self):
        valid = "i" * 256
        self.assertEqual(project("كَ", valid, valid)["source"], source("كَ", valid, valid))
        for invalid in ("i" * 257, "a\n", "a\x00", "a\t"):
            with self.subTest(identity=repr(invalid)):
                with self.assertRaises(NabtError):
                    project("كَ", invalid)
                with self.assertRaises(NabtError):
                    project("كَ", "a", invalid)

    def test_byte_budget_counts_utf8_bytes_and_defers_exhaustion(self):
        # One long residual cluster exercises the byte limit without hitting
        # the separately declared receipt-size limit first.
        text = "x" + "ّ" * 32767 + "y"
        receipt = project(text)
        self.assertEqual(len(receipt["raw_utf8"]), 65536)
        self.assertEqual(receipt["status"], "INVALID")
        self.assertEqual(receipt["cells"], [])
        self.assertEqual("".join(p["text"] for p in receipt["pieces"]), text)
        for text in ("x" * 65537, "ك" * 32769, text + "z"):
            with self.subTest(bytes=len(text.encode())):
                with self.assertRaises(NabtError) as caught:
                    project(text)
                self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")
                self.assertEqual(caught.exception.status, "DEFER")

    def test_receipt_budget_suspends_many_residuals_without_invalid_verdict(self):
        for text in ("x" * 65536, "ك" * 32768):
            with self.subTest(bytes=len(text.encode())):
                with self.assertRaises(NabtError) as caught:
                    project(text)
                self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")
                self.assertEqual(caught.exception.status, "DEFER")

    def test_cell_budget_accepts_boundary_and_defers_one_more(self):
        text = "بَ" * 4096
        receipt = project(text)
        self.assertEqual(receipt["status"], "COMPLETE")
        self.assertEqual(receipt["cells"], [4] * 4096)
        # Avoid Python's unrelated int-to-decimal string limit in this oracle.
        # The projected integer must have the independent base-116 value.
        self.assertEqual(decimal_chunks(receipt["number"]), polynomial([4] * 4096))
        with self.assertRaises(NabtError) as caught:
            project(text + "بَ")
        self.assertEqual(caught.exception.code, "RESOURCE_LIMIT")
        self.assertEqual(caught.exception.status, "DEFER")


class FoundationNativeIndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        declared = os.environ.get("NABT_FOUNDATION_EXECUTABLE")
        cls.executable = Path(declared) if declared else ROOT / "formal/.lake/build/bin/foundationProbe"
        if not cls.executable.is_file():
            if declared:
                raise RuntimeError("Declared Lean foundation executable is missing: " + str(cls.executable))
            raise unittest.SkipTest("Build foundationProbe or set NABT_FOUNDATION_EXECUTABLE for native checks")

    def queries(self, *requests):
        raw = "".join(json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n" for r in requests).encode()
        answers = self.raw_queries(raw)
        self.assertEqual(len(answers), len(requests))
        return answers

    def raw_queries(self, raw):
        run = subprocess.run([str(self.executable)], input=raw, capture_output=True,
                             timeout=30, check=True)
        self.assertEqual(run.stderr, b"")
        answers = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertTrue(answers)
        return answers

    def test_all_116_native_cells_match_the_independent_table(self):
        answers = self.queries(*({"op": "project", "source": source(text)} for text in CELL_TABLE))
        for cell, (text, answer) in enumerate(zip(CELL_TABLE, answers, strict=True)):
            with self.subTest(cell=cell):
                self.assertEqual(answer["law_id"], LAW)
                self.assertEqual(answer["status"], "COMPLETE")
                self.assertEqual(answer["cells"], [cell])
                self.assertEqual(answer["number"], str(cell + 1))
                self.assertEqual(answer["raw_utf8"], list(text.encode()))

    def test_native_projection_preserves_partial_and_invalid_cases(self):
        cases = [("كتب", "PARTIAL", []), ("كَتبَ", "PARTIAL", [84, 4]),
                 ("بَّ", "PARTIAL", []), ("كَُ", "INVALID", []),
                 ("بَكَُتِ", "INVALID", [4, 10]), ("", "INVALID", [])]
        answers = self.queries(*({"op": "project", "source": source(text)} for text, _, _ in cases))
        for (text, status, cells), answer in zip(cases, answers, strict=True):
            with self.subTest(text=text):
                self.assertEqual(answer["status"], status)
                self.assertEqual(answer["cells"], cells)
                self.assertEqual(answer["number"], str(polynomial(cells)))
                self.assertEqual(answer["raw_utf8"], list(text.encode()))
                self.assertEqual("".join(p["text"] for p in answer["pieces"]), text)

    def test_native_check_binds_receipt_to_external_source_and_scope(self):
        expected_source = source("كَتَبَ")
        receipt, = self.queries({"op": "project", "source": expected_source})
        requests = [{"op": "check", "source": expected_source, "receipt": receipt}]
        for field, value in (("id", "another"), ("revision", "2"), ("text", "كُتِبَ")):
            changed = {**expected_source, field: value}
            requests.append({"op": "check", "source": changed, "receipt": receipt})
        answers = self.queries(*requests)
        self.assertIs(answers[0]["certificate_checked"], True)
        for answer in answers[1:]:
            self.assertIs(answer["certificate_checked"], False)

    def test_native_check_rejects_tampering_with_valid_receipt(self):
        expected_source = source("كَتَبَ")
        receipt, = self.queries({"op": "project", "source": expected_source})
        requests = []
        for key, value in (("cells", [84, 8, 116]), ("number", "0"),
                           ("alphabet_id", "model-vocabulary"), ("law_id", "nabt-sound-shape-v1"),
                           ("number_domain", "semantic-identity"), ("native_checked", True)):
            changed = deepcopy(receipt)
            changed[key] = value
            requests.append({"op": "check", "source": expected_source, "receipt": changed})
        for answer in self.queries(*requests):
            self.assertIsNot(answer.get("certificate_checked"), True)

    def test_native_transport_rejects_duplicate_keys_and_invalid_unicode(self):
        requests = (
            b'{"op":"project","source":{"id":"a","revision":"1","text":"\\ud800"}}\n',
            b'{"op":"project","source":{"id":"a","revision":"1","text":"a","text":"b"}}\n',
            b'{"op":"project","op":"identity","source":{"id":"a","revision":"1","text":"a"}}\n',
            b'{"op":"project","source":{"id":true,"revision":"1","text":"a"}}\n',
            b'{"op":"project","source":{"id":"a","revision":1,"text":"a"}}\n',
            b'{"op":"project","source":{"id":"a","revision":"1","text":"\xff"}}\n',
        )
        for raw in requests:
            with self.subTest(payload=raw):
                for answer in self.raw_queries(raw):
                    self.assertIsNot(answer.get("certificate_checked"), True)
                    self.assertNotIn(answer.get("status"), {"COMPLETE", "PARTIAL"})

    def test_native_boolean_never_impersonates_cell_one_or_offset_zero(self):
        expected_source = source("اُ")
        receipt, = self.queries({"op": "project", "source": expected_source})
        changed = [deepcopy(receipt) for _ in range(3)]
        changed[0]["cells"] = [True]
        changed[1]["pieces"][0]["cell"] = True
        changed[2]["pieces"][0]["start_byte"] = False
        for answer in self.queries(*({"op": "check", "source": expected_source, "receipt": r} for r in changed)):
            self.assertIsNot(answer.get("certificate_checked"), True)

    def test_native_resource_boundaries_remain_distinct_from_invalid_source(self):
        text = "بَ" * 4096
        expected_source = source(text)
        receipt, = self.queries({"op": "project", "source": expected_source})
        self.assertEqual(receipt["status"], "COMPLETE")
        self.assertEqual(receipt["cells"], [4] * 4096)
        self.assertEqual(decimal_chunks(receipt["number"]), polynomial([4] * 4096))
        checked, = self.queries({"op": "check", "source": expected_source, "receipt": receipt})
        self.assertIs(checked["certificate_checked"], True)
        # The byte boundary is exercised separately from the output-size cap.
        boundary = "x" + "ّ" * 32767 + "y"
        bounded, = self.queries({"op": "project", "source": source(boundary)})
        self.assertEqual(bounded["status"], "INVALID")
        self.assertEqual(bounded["raw_utf8"], list(boundary.encode()))
        over_limits = ("x" * 65537, text + "بَ", "x" * 65536, "ك" * 32768)
        for answer in self.queries(*({"op": "project", "source": source(value)} for value in over_limits)):
            self.assertEqual(answer["status"], "RESOURCE_LIMIT")
            self.assertIsNot(answer.get("certificate_checked"), True)


if __name__ == "__main__":
    unittest.main()
