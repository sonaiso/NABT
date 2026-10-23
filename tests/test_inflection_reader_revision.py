"""Source-coordinate and authority boundaries for the second reader revision.

The miniature records below are authored fixtures, not evaluation material or
quotations from QAC. Expected spans are taken from the new Arabic input bytes.
"""

from copy import deepcopy
from hashlib import sha256
import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.inflection_reader import read_inflection, verify_inflection


TRAINING = (
    "LOCATION\tFORM\tTAG\tFEATURES\n"
    "(1:1:1:1)\tyasokunu\tV\tSTEM|POS:V|IMPF|LEM:sakana|ROOT:skn|3MP\n"
    "(1:1:1:2)\twna\tPRON\tSUFFIX|PRON:3MP\n"
    "(1:2:1:1)\tyakotubo\tV\tSTEM|POS:V|IMPF|LEM:kataba|ROOT:ktb|3FP\n"
    "(1:2:1:2)\tna\tPRON\tSUFFIX|PRON:3FP\n"
    "(1:2:1:3)\thu\tPRON\tSUFFIX|PRON:3MS\n"
    "(1:3:1:1)\tyasokuna\tV\tSTEM|POS:V|IMPF|LEM:sakana|ROOT:skn|3MS\n"
    "(1:3:1:2)\tn~a\tEMPH\tSUFFIX|EMPH\n"
    "(1:4:1:1)\tyakotuba\tV\tSTEM|POS:V|IMPF|LEM:kataba|ROOT:ktb|3MS\n"
    "(1:4:1:2)\tA\tEMPH\tSUFFIX|EMPH\n"
    "(1:5:1:1)\t{kotubo\tV\tSTEM|POS:V|IMPV|LEM:kataba|ROOT:ktb|2MS\n"
    "(1:5:1:2)\thu\tPRON\tSUFFIX|PRON:3MS\n"
).encode("utf-8")


def content_readings(report):
    return [r for o in report["occurrences"] for r in o["readings"] if r["kind"] != "particle"]


class InflectionReaderRevisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = learn_qac_lexicon(TRAINING)

    def read(self, text):
        return read_inflection(text, lexical_model=self.model, source_id="new_text", scope="line")

    def assert_source_span(self, report, span, surface):
        raw = report["raw_text"].encode("utf-8")
        self.assertEqual(raw[span["start"]:span["end"]].decode("utf-8"), surface)
        self.assertEqual(span["source_id"], "new_text")
        self.assertEqual(span["source_sha256"], sha256(raw).hexdigest())
        self.assertEqual(span["span_sha256"], sha256(surface.encode("utf-8")).hexdigest())

    def test_radical_and_inflection_nuns_have_distinct_positions_in_one_reading(self):
        report = self.read("  يَسْكُنُونَ  ")
        reading, = content_readings(report)
        nuns = reading["nun_readings"]
        self.assertEqual([(n["kind"], n["cluster_index"], n["surface"]) for n in nuns],
                         [("radical", 3, "نُ"), ("five_verb_raf", 5, "نَ")])
        for nun in nuns:
            self.assertEqual(nun["realization"], "present")
            self.assert_source_span(report, nun["span"], nun["surface"])
            self.assertEqual(nun["support_ids"], [r["record_id"] for r in reading["support_records"]])
        self.assertLess(nuns[0]["span"]["end"], nuns[1]["span"]["start"])
        self.assertEqual(report["assignments"], [])

    def test_deleted_nun_has_no_fabricated_span_beside_a_visible_radical_nun(self):
        report = self.read("لَمْ يَسْكُنُوا")
        reading, = content_readings(report)
        radical, inflection = reading["nun_readings"]
        self.assert_source_span(report, radical["span"], "نُ")
        self.assertEqual(inflection["realization"], "deleted")
        self.assertIsNone(inflection["cluster_index"])
        self.assertIsNone(inflection["span"])
        self.assertIsNone(inflection["surface"])
        self.assertEqual(reading["actual_case"], "jazm")
        self.assertEqual({s["sign_name"] for s in reading["sign_candidates"]}, {"nun_deleted"})

    def test_source_suffix_partition_preserves_bytes_without_attachment_authority(self):
        report = self.read("لَمْ يَكْتُبْنَهُ")
        reading, = content_readings(report)
        self.assertTrue(reading["annotation_only"])
        self.assertEqual(reading["suffix_boundary"], "ATTACHED_SUFFIX_ACTIVATION_UNIMPLEMENTED")
        self.assertIn(reading["suffix_boundary"], reading["obligations"])
        self.assertTrue(reading["segmentation"]["coverage_valid"])
        self.assertFalse(reading["segmentation"]["licensed"])
        parts = reading["segmentation"]["parts"]
        self.assertEqual([(p["kind"], p["surface"]) for p in parts],
                         [("verbal_stem", "يَكْتُبْ"), ("feminine_subject", "نَ"),
                          ("annotated_pronominal_suffix", "هُ")])
        self.assertEqual("".join(p["surface"] for p in parts), reading["stem_surface"])
        for part in parts:
            self.assert_source_span(report, part["span"], part["surface"])
        self.assertTrue(all(a["span"]["end"] == b["span"]["start"] for a, b in zip(parts, parts[1:])))
        self.assertEqual(reading["nun_readings"][0]["span"], parts[1]["span"])
        self.assertEqual(reading["class_candidates"], [])
        self.assertEqual(reading["sign_candidates"], [])
        self.assertTrue(all(reading[k] is None for k in ("construction", "actual_role", "actual_case", "local_case")))
        self.assertEqual(report["relations"], [])
        self.assertEqual(report["assignments"], [])

    def test_annotation_only_final_mark_is_not_mutable(self):
        self.assertTrue(content_readings(self.read("يَكْتُبْنَهُ")))
        self.assertFalse(content_readings(self.read("يَكْتُبْنَهِ")))
        self.assertFalse(content_readings(self.read("يَكْتُبْنَهَّ")))

    def test_emphasis_neither_resolves_connection_nor_invents_a_nun_on_alif(self):
        report = self.read("لَمْ يَسْكُنَنَّ")
        reading, = content_readings(report)
        radical, emphasis = reading["nun_readings"]
        self.assertEqual(radical["kind"], "radical")
        self.assertEqual(emphasis["kind"], "emphasis")
        self.assertEqual(emphasis["directness"], "unknown")
        self.assert_source_span(report, emphasis["span"], "نَّ")
        self.assertLessEqual(radical["span"]["end"], emphasis["span"]["start"])
        self.assertEqual(report["relations"], [])
        unresolved, = content_readings(self.read("لَمْ يَكْتُبَا"))
        nun, = unresolved["nun_readings"]
        self.assertEqual(nun["realization"], "unresolved")
        self.assertEqual(nun["directness"], "unknown")
        self.assertIsNone(nun["cluster_index"])
        self.assertIsNone(nun["span"])
        self.assertIsNone(nun["surface"])
        self.assertIsNone(unresolved["actual_role"])

    def test_lookup_wasl_projection_does_not_rewrite_partition_text(self):
        for text in ("ٱكْتُبْهُ", "اكْتُبْهُ"):
            with self.subTest(text=text):
                report = self.read(text)
                reading, = content_readings(report)
                parts = reading["segmentation"]["parts"]
                self.assertEqual("".join(p["surface"] for p in parts), text)
                self.assertEqual(parts[0]["surface"][0], text[0])
                for part in parts:
                    self.assert_source_span(report, part["span"], part["surface"])

    def test_replay_rejects_nun_position_substitution_and_source_withdrawal(self):
        report = self.read("يَسْكُنُونَ")
        self.assertTrue(verify_inflection(report, lexical_model=self.model)["valid"])
        self.assertFalse(verify_inflection(report)["valid"])
        excluded = learn_qac_lexicon(TRAINING, excluded_verses=("1:1",))
        self.assertFalse(verify_inflection(report, lexical_model=excluded)["valid"])
        changed = deepcopy(report)
        reading, = content_readings(changed)
        reading["nun_readings"][1]["span"] = reading["nun_readings"][0]["span"]
        self.assertFalse(verify_inflection(changed, lexical_model=self.model)["valid"])
        self.assertEqual(report["reader_version"], "nabt.inflection-reader.v2")


if __name__ == "__main__":
    unittest.main()
