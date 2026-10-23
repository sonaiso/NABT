"""External schema, exact bytes, duplicate readings and replay boundaries.

Fixtures are authored here; no original corpus or independent evaluation set is
bundled. Python's CSV writer/reader provide a separate dialect oracle where used.
"""

from copy import deepcopy
import csv
from hashlib import sha256
import io
import random
import unittest
from unittest.mock import patch

from nabt.corpus_sources import read_corpus, verify_corpus
from nabt.errors import NabtError


QAC = b"LOCATION\tFORM\tTAG\tFEATURES\r\n"
AR = ("ID,Sura_No,Verse_No,Column5,Word_No,Word,Without_Diacritics,"
      "Segmented_Word,Morph_tag,Morph_type,Punctuation_Mark,Invariable_Declinable,"
      "Syntactic_Role,Possessive_Construct,Case_Mood,Case_Mood_Marker,Phrase,"
      "Phrasal_Function,Notes").split(",")
EN = ("ID,Sura_No,Verse_No,Word_No,Segment_No,Word,Without_Diacritics,"
      "Segmented_Word,Morph_Tag,Morph_Type,Punctuation_Mark,Invariable_Declinable,"
      "Syntactic_Role,Possessive_Construct,Case_Mood,Case_Mood_Marker,Phrase,"
      "Phrasal_Function,Gloss").split(",")


def csv_bytes(header, rows, *, bom=False, ending="\r\n", quoting=csv.QUOTE_MINIMAL):
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator=ending, quoting=quoting)
    writer.writerow(header)
    writer.writerows(rows)
    return ("\ufeff" if bom else "").encode() + output.getvalue().encode()


def nominal_row():
    return ["7", "2", "5", "11", "3", "لفظٌ", "لفظ", "لفظٌ", "N", "Stem",
            "", "معرب", "فاعل", "", "مرفوع", "الضمة", "", "", "ملاحظة"]


class CorpusSources(unittest.TestCase):
    def assert_coverage(self, report, raw):
        parts = [report["header"], *report["records"], *report["nonrecord_fragments"]]
        parts.sort(key=lambda p: p["byte_start"])
        cursor = 0
        restored = bytearray()
        for part in parts:
            self.assertEqual(part["byte_start"], cursor)
            self.assertGreater(part["byte_end"], cursor)
            fragment = part["raw_record"].encode("utf-8")
            self.assertEqual(fragment, raw[cursor:part["byte_end"]])
            restored.extend(fragment)
            cursor = part["byte_end"]
        self.assertEqual(cursor, len(raw))
        self.assertEqual(bytes(restored), raw)
        self.assertTrue(report["summary"]["source_coverage_complete"])

    def test_qac_keeps_preamble_features_and_missing_number(self):
        raw = (b"\xef\xbb\xbf# attribution\r\n\r\n" + QAC
               + b"(1:1:1:1)\tbi\tP\tPREFIX|bi+\r\n"
               + b"# source note\n"
               + b"(1:1:1:2)\tname\tN\tSTEM|POS:N|M|ROOT:xyz|GEN||M\n"
               + b"\r\n# end")
        report = read_corpus(raw, format="qac", source_id="qac_test")
        self.assertEqual(report["source"], {"id": "qac_test", "sha256": sha256(raw).hexdigest(),
                                            "byte_length": len(raw)})
        self.assertEqual(report["header"]["fieldnames"], ["LOCATION", "FORM", "TAG", "FEATURES"])
        self.assertEqual(report["summary"]["record_count"], 2)
        noun = report["records"][1]
        self.assertEqual(noun["feature_tokens"], ["STEM", "POS:N", "M", "ROOT:xyz", "GEN", "", "M"])
        self.assertNotIn("S", noun["feature_tokens"])
        self.assertEqual(noun["locator"], [1, 1, 1, 2])
        self.assertEqual(report["authority"], "ANNOTATION_REPLAY_ONLY")
        self.assertNotIn("grammatical_class", noun)
        self.assert_coverage(report, raw)
        self.assertTrue(verify_corpus(report, raw=raw, format="qac", source_id="qac_test")["valid"])

    def test_duplicate_locators_are_separate_occurrences_not_merged_readings(self):
        raw = (QAC + b"(2:3:4:1)\ta\tN\tSTEM|NOM\n"
               + b"(2:3:4:1)\ta\tV\tSTEM|MOOD:JUS\n"
               + b"(2:3:4:1)\ta\tN\tSTEM|NOM\n")
        report = read_corpus(raw, format="qac")
        self.assertEqual(report["summary"]["record_count"], 3)
        self.assertEqual(report["summary"]["duplicate_locator_groups"], 1)
        self.assertEqual(report["summary"]["duplicate_locator_excess_records"], 2)
        self.assertEqual(len({r["identity"] for r in report["records"]}), 3)
        self.assertEqual([r["ordinal"] for r in report["records"]], [1, 2, 3])
        self.assertEqual([r["fields"]["TAG"] for r in report["records"]], ["N", "V", "N"])
        self.assertTrue(all(r["valid"] for r in report["records"]))
        other = read_corpus(raw, format="qac", source_id="other")
        self.assertNotEqual(other["records"][0]["identity"], report["records"][0]["identity"])

    def test_qac_malformed_rows_are_kept_and_counted(self):
        raw = QAC + b"broken\ta\tN\tSTEM\n(1:1:1:1)\ta\tN\n(1:1:1:1)\ta\tN\tSTEM\textra\n"
        report = read_corpus(raw, format="qac")
        self.assertEqual(report["status"], "READ_WITH_ERRORS")
        self.assertEqual(report["summary"]["invalid_count"], 3)
        self.assertEqual(report["summary"]["diagnostic_counts"], {"COLUMN_COUNT": 2, "INVALID_LOCATOR": 1})
        self.assertEqual(report["records"][0]["fields"]["LOCATION"], "broken")
        self.assertEqual(report["records"][1]["fields"], {})
        self.assertEqual(report["records"][2]["diagnostics"][0]["actual"], 5)
        self.assert_coverage(report, raw)
        # Replay can verify an accurately reported invalid row without licensing it.
        self.assertTrue(verify_corpus(report, raw=raw, format="qac")["valid"])

    def test_both_masaq_schemas_keep_their_exact_names_and_coordinates(self):
        for fmt, header in (("masaq-ar", AR), ("masaq-en", EN)):
            with self.subTest(format=fmt):
                values = nominal_row()
                raw = csv_bytes(header, [values], bom=True, quoting=csv.QUOTE_ALL)
                report = read_corpus(raw, format=fmt)
                row = report["records"][0]
                self.assertTrue(row["valid"])
                self.assertEqual(row["locator"], [2, 5, 11, 3])
                self.assertEqual(row["fields"], dict(zip(header, values)))
                self.assertEqual(report["header"]["fieldnames"], header)
                self.assertTrue(report["header"]["raw_record"].startswith("\ufeff"))
                self.assert_coverage(report, raw)
                with self.assertRaises(NabtError) as failure:
                    read_corpus(raw, format="masaq-en" if fmt == "masaq-ar" else "masaq-ar")
                self.assertEqual(failure.exception.code, "INVALID_CORPUS_HEADER")

    def test_csv_quoted_newlines_quotes_and_unicode_have_physical_byte_spans(self):
        first, second = nominal_row(), nominal_row()
        first[-1] = 'سطر، أول\r\nثم "اقتباس", و\nسطر آخر\rنهاية'
        second[0], second[-1] = "8", "آخر بلا إنهاء سطر"
        raw = csv_bytes(EN, [first, second])[:-2]
        report = read_corpus(raw, format="masaq-en")
        records = report["records"]
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["fields"]["Gloss"], first[-1])
        self.assertEqual(records[1]["fields"]["Gloss"], second[-1])
        self.assertGreater(records[0]["raw_record"].count("\n"), 1)
        self.assertEqual(records[1]["byte_start"], records[0]["byte_end"])
        self.assertGreater(records[0]["byte_end"] - records[0]["byte_start"], len(records[0]["raw_record"]))
        self.assertEqual(records[1]["byte_end"], len(raw))
        self.assert_coverage(report, raw)

    def test_csv_matches_independent_stdlib_oracle_over_quoted_fields(self):
        rng = random.Random(274019)
        atoms = ["", "أ", "x", ",", '"', "\r", "\n", "\r\n", " ", "\t", "😀", "\u2028"]
        rows = []
        for index in range(36):
            values = nominal_row()
            values[0] = str(index + 1)
            for field in range(5, 19):
                values[field] = "".join(rng.choice(atoms) for _ in range(rng.randrange(12)))
            rows.append(values)
        for ending in ("\r\n", "\n", "\r"):
            raw = csv_bytes(EN, rows, ending=ending, quoting=csv.QUOTE_ALL)
            reference = list(csv.reader(io.StringIO(raw.decode(), newline=""), strict=True))
            actual = read_corpus(raw, format="masaq-en")
            self.assertEqual([list(r["fields"].values()) for r in actual["records"]], reference[1:])
            self.assert_coverage(actual, raw)

    def test_invalid_ids_and_coordinates_survive_without_repair(self):
        rows = []
        for invalid in ("عت", "0", "01", "-1", "١", str(2**63), "9" * 300):
            values = nominal_row()
            values[0] = invalid
            rows.append(values)
        bad_coord = nominal_row()
        bad_coord[2] = "0"
        rows.append(bad_coord)
        raw = csv_bytes(AR, rows)
        report = read_corpus(raw, format="masaq-ar")
        self.assertEqual(report["summary"]["invalid_count"], len(rows))
        for expected, record in zip(rows[:-1], report["records"][:-1]):
            self.assertEqual(record["fields"]["ID"], expected[0])
            self.assertEqual(record["locator"], [2, 5, 11, 3])
            self.assertEqual(record["diagnostics"], [{"code": "INVALID_ID", "field": "ID"}])
        self.assertIsNone(report["records"][-1]["locator"])
        self.assert_coverage(report, raw)

    def test_wrong_width_blank_and_very_wide_csv_rows_are_retained(self):
        raw = csv_bytes(EN, [nominal_row()]) + b"\r\nwrong,width\n" + b"," * 10_000
        report = read_corpus(raw, format="masaq-en")
        self.assertEqual(report["summary"]["record_count"], 4)
        self.assertEqual(report["summary"]["invalid_count"], 3)
        self.assertEqual([r["diagnostics"][0]["actual"] for r in report["records"][1:]], [1, 2, 10_001])
        self.assertTrue(all(r["fields"] == {} for r in report["records"][1:]))
        self.assert_coverage(report, raw)

    def test_unrecoverable_csv_syntax_rejects_the_whole_parse(self):
        header = csv_bytes(EN, [])
        for tail in (b'"unterminated\n', b'ab"cd,ef\n', b'"closed" trailing,field\n',
                     b'"closed" trailing', b'"a""'):
            with self.subTest(tail=tail), self.assertRaises(NabtError) as failure:
                read_corpus(header + tail, format="masaq-en")
            self.assertEqual(failure.exception.code, "INVALID_CORPUS_CSV")

    def test_encoding_and_headers_are_global_rejections(self):
        for raw, fmt, code in ((QAC + b"\xff", "qac", "INVALID_UTF8"),
                               (b"# only comments\n", "qac", "INVALID_CORPUS_HEADER"),
                               (b"location\tFORM\tTAG\tFEATURES\n", "qac", "INVALID_CORPUS_HEADER"),
                               (csv_bytes(EN + ["extra"], []), "masaq-en", "INVALID_CORPUS_HEADER"),
                               (csv_bytes(EN[::-1], []), "masaq-en", "INVALID_CORPUS_HEADER")):
            with self.subTest(code=code), self.assertRaises(NabtError) as failure:
                read_corpus(raw, format=fmt)
            self.assertEqual(failure.exception.code, code)
        empty_table = read_corpus(QAC, format="qac")
        self.assertEqual(empty_table["summary"]["record_count"], 0)
        self.assert_coverage(empty_table, QAC)

    def test_source_identity_format_and_bytes_have_strict_types(self):
        class StringSubclass(str):
            pass

        for source_id in (None, True, 3, "", "Upper", "a b", "a\n", "é", "a" * 129, StringSubclass("a")):
            with self.subTest(source_id=repr(source_id)), self.assertRaises(NabtError):
                read_corpus(QAC, format="qac", source_id=source_id)
        for raw in ("LOCATION\tFORM\tTAG\tFEATURES", bytearray(QAC), None, True, b""):
            with self.subTest(raw_type=type(raw)), self.assertRaises(NabtError):
                read_corpus(raw, format="qac")
        for fmt in (True, "MASAQ", "csv", StringSubclass("qac")):
            with self.subTest(format=fmt), self.assertRaises(NabtError):
                read_corpus(QAC, format=fmt)
        self.assertEqual(read_corpus(QAC, format="qac", source_id="a" * 128)["source"]["id"], "a" * 128)

    def test_declared_budgets_defer_and_count_invalid_records_too(self):
        raw = QAC + b"bad\n" * 3
        with patch("nabt.corpus_sources.MAX_RECORDS", 2):
            with self.assertRaises(NabtError) as failure:
                read_corpus(raw, format="qac")
            self.assertEqual((failure.exception.code, failure.exception.status), ("RESOURCE_LIMIT", "DEFER"))
        with patch("nabt.corpus_sources.MAX_SOURCE_BYTES", len(QAC)):
            self.assertEqual(read_corpus(QAC, format="qac")["summary"]["record_count"], 0)
            with self.assertRaises(NabtError) as failure:
                read_corpus(QAC + b"\n", format="qac")
            self.assertEqual(failure.exception.status, "DEFER")

    def test_large_quoted_field_does_not_change_global_csv_limit(self):
        before = csv.field_size_limit()
        values = nominal_row()
        values[-1] = "أ" * 140_000 + '\n"حرف",آخر'
        raw = csv_bytes(EN, [values])
        report = read_corpus(raw, format="masaq-en")
        self.assertEqual(report["records"][0]["fields"]["Gloss"], values[-1])
        self.assertEqual(csv.field_size_limit(), before)
        self.assert_coverage(report, raw)

    def test_replay_rejects_mutation_type_confusion_and_external_rebinding(self):
        raw = QAC + b"(1:1:1:1)\tx\tN\tSTEM|M\n"
        report = read_corpus(raw, format="qac")
        mutations = [
            lambda r: r["source"].update(id="other"),
            lambda r: r["records"][0].update(identity="0" * 64),
            lambda r: r["records"][0].update(byte_end=len(raw) - 1),
            lambda r: r["records"][0].update(raw_record="changed"),
            lambda r: r["records"][0].update(ordinal=True),
            lambda r: r["records"][0].update(ordinal=1.0),
            lambda r: r["records"][0].update(locator=(1, 1, 1, 1)),
            lambda r: r["records"][0]["fields"].update(TAG="V"),
            lambda r: r["records"][0]["feature_tokens"].append("S"),
            lambda r: r["summary"].update(valid_count=False),
            lambda r: r.update(authority="LINGUISTIC_TRUTH"),
            lambda r: r.update(extra="trusted"),
        ]
        for mutate in mutations:
            forged = deepcopy(report)
            mutate(forged)
            self.assertFalse(verify_corpus(forged, raw=raw, format="qac")["valid"])
        for kwargs in ({"raw": raw + b"\n", "format": "qac"},
                       {"raw": raw, "format": "qac", "source_id": "other"},
                       {"raw": raw, "format": "masaq-ar"}):
            self.assertFalse(verify_corpus(report, **kwargs)["valid"])
        reordered = dict(reversed(list(report.items())))
        self.assertTrue(verify_corpus(reordered, raw=raw, format="qac")["valid"])

    def test_replay_cyclic_forgery_fails_and_resource_failure_is_defer(self):
        report = read_corpus(QAC, format="qac")
        forged = deepcopy(report)
        forged["summary"] = forged
        self.assertFalse(verify_corpus(forged, raw=QAC, format="qac")["valid"])
        self.assertFalse(verify_corpus(None, raw=QAC, format="qac")["valid"])
        with patch("nabt.corpus_sources.MAX_SOURCE_BYTES", len(QAC) - 1):
            result = verify_corpus(report, raw=QAC, format="qac")
        self.assertEqual((result["valid"], result["status"], result["code"]),
                         (False, "DEFER", "RESOURCE_LIMIT"))


if __name__ == "__main__":
    unittest.main()
