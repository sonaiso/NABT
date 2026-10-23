"""Authored regressions from the source review, separate from frozen evaluation.

These miniature QAC-shaped fixtures are not original corpus rows. They check
preservation and authority boundaries, not corpus accuracy or Arabic coverage.
"""

import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.inflection_reader import read_inflection


def read_authored(text, rows):
    raw = ("LOCATION\tFORM\tTAG\tFEATURES\n"
           + "".join("\t".join(row) + "\n" for row in rows)).encode("utf-8")
    model = learn_qac_lexicon(raw, source_id="source_review_authored")
    report = read_inflection(text, lexical_model=model)
    return report, [reading for occurrence in report["occurrences"]
                    for reading in occurrence["readings"]]


class InflectionSourceRevision(unittest.TestCase):
    def assert_unactivated_partition(self, text, report, reading):
        self.assertTrue(reading["annotation_only"])
        self.assertIsNone(reading["construction"])
        self.assertEqual(reading["class_candidates"], [])
        self.assertEqual(reading["sign_candidates"], [])
        self.assertFalse(reading["segmentation"]["licensed"])
        self.assertIsNone(reading["actual_case"])
        self.assertIsNone(reading["actual_role"])
        self.assertEqual(report["assignments"], [])
        raw = text.encode("utf-8")
        cursor = 0
        for part in reading["segmentation"]["parts"]:
            start, end = part["span"]["start"], part["span"]["end"]
            self.assertEqual(start, cursor)
            self.assertEqual(raw[start:end].decode("utf-8"), part["surface"])
            cursor = end
        self.assertEqual(cursor, len(raw))

    def test_deleted_subject_without_retained_base_stays_attested(self):
        text = "يَكْتُبُوا"
        report, readings = read_authored(text, [
            ("(1:1:1:1)", "yakotubu", "V", "STEM|POS:V|IMPF|LEM:kataba|ROOT:ktb|3MP"),
            ("(1:1:1:2)", "wA", "PRON", "SUFFIX|PRON:3MP"),
        ])
        self.assertEqual(len(readings), 1)
        reading = readings[0]
        self.assert_unactivated_partition(text, report, reading)
        self.assertEqual(reading["segmentation"]["parts"][-1]["kind"], "annotated_subject_suffix")
        self.assertEqual(reading["nun_readings"], [])
        self.assertEqual(len(reading["support_records"]), 2)

    def test_pron_annotation_does_not_assign_object_role(self):
        text = "كَتَبْتُ"
        report, readings = read_authored(text, [
            ("(1:1:1:1)", "katabo", "V", "STEM|POS:V|PERF|LEM:kataba|ROOT:ktb|1S"),
            ("(1:1:1:2)", "tu", "PRON", "SUFFIX|PRON:1S"),
        ])
        self.assertEqual(len(readings), 1)
        reading = readings[0]
        self.assert_unactivated_partition(text, report, reading)
        self.assertEqual(reading["segmentation"]["parts"][-1]["kind"], "annotated_pronominal_suffix")
        self.assertEqual(reading["nun_readings"], [])

    def test_unresolved_plural_does_not_assign_final_nun_to_root(self):
        report, readings = read_authored("مُؤْمِنِينَ", [
            ("(1:1:1:1)", "mu&ominiyna", "N", "STEM|POS:N|LEM:mu&ominuwna|ROOT:Amn|MP"),
        ])
        self.assertTrue(readings)
        self.assertEqual(report["assignments"], [])
        for reading in readings:
            self.assertIsNone(reading["construction"])
            self.assertNotIn(3, reading["class_candidates"])
            self.assertEqual(reading["nun_readings"], [])
            self.assertIsNone(reading["lexical_features"]["nominal_form"])
            self.assertEqual(reading["lexical_features"]["singular_witnesses"], [])

        # The same wrong-position risk also occurs when a verbal STEM already
        # includes the retained plural ending and an object pronoun follows it.
        text = "يُؤْمِنُونَهُ"
        report, readings = read_authored(text, [
            ("(1:1:1:1)", "yu&ominuwna", "V", "STEM|POS:V|IMPF|LEM:'aAmana|ROOT:Amn|3MP"),
            ("(1:1:1:2)", "hu", "PRON", "SUFFIX|PRON:3MS"),
        ])
        self.assertEqual(len(readings), 1)
        reading = readings[0]
        self.assert_unactivated_partition(text, report, reading)
        radical = [nun for nun in reading["nun_readings"] if nun["kind"] == "radical"]
        self.assertEqual(len(radical), 1)
        self.assertEqual(radical[0]["cluster_index"], 3)
        span = radical[0]["span"]
        self.assertEqual(text.encode("utf-8")[span["start"]:span["end"]].decode("utf-8"), "نُ")

    def test_paired_plural_keeps_distinct_nuns_without_inventing_singular(self):
        text = "مُؤْمِنِينَ"
        _, readings = read_authored(text, [
            ("(1:1:1:1)", "mu&ominuwna", "N", "STEM|POS:N|LEM:mu&ominuwna|ROOT:Amn|MP"),
            ("(1:1:2:1)", "mu&ominiyna", "N", "STEM|POS:N|LEM:mu&ominuwna|ROOT:Amn|MP"),
        ])
        self.assertTrue(readings)
        raw = text.encode("utf-8")
        for reading in readings:
            self.assertEqual(reading["class_candidates"], [3])
            self.assertEqual(reading["construction_basis"], "paired_annotated_plural_letter_realizations")
            self.assertEqual(reading["lexical_features"]["nominal_form"], "masculine_plural_letter_paradigm")
            self.assertEqual(reading["lexical_features"]["singular_witnesses"], [])
            self.assertEqual(len({s["record_id"] for s in reading["construction_supports"]}), 2)
            nuns = {nun["kind"]: nun for nun in reading["nun_readings"]}
            self.assertEqual(set(nuns), {"radical", "nominal_dual_plural"})
            self.assertEqual(nuns["radical"]["cluster_index"], 3)
            self.assertEqual(nuns["nominal_dual_plural"]["cluster_index"], 5)
            self.assertNotEqual(nuns["radical"]["span"], nuns["nominal_dual_plural"]["span"])
            for nun in nuns.values():
                self.assertEqual(nun["realization"], "present")
                span = nun["span"]
                self.assertEqual(raw[span["start"]:span["end"]].decode("utf-8"), nun["surface"])


if __name__ == "__main__":
    unittest.main()
