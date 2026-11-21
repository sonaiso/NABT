"""Independent examples for the source-only length question profile."""
from copy import deepcopy
import unittest

from nabt.alphabet import render_word
from tools.grammar_catalog import ntp
from tools.lexical_training import ntl_core as core


FIRST = "اليوم ١: طول القضيب ٣ ± ٠ سم. "
SECOND = "اليوم ٢: طول القضيب ٤٠ ± ١ مم. "
UP = "هَلْ زاد الطول؟"
DELTA = "كَمْ تغيرت القراءة الاسمية بالملليمتر؟"
CAUSE = "هل سببت الحرارة زيادة الطول؟"


def typed_query(source):
    return core.measurement_question({"source_ar": source})


class LengthReading(unittest.TestCase):
    def test_paraphrase_and_recover_exact_occurrences(self):
        for q in (UP, "هل ازداد الطول؟"):
            text = FIRST + SECOND + q
            report = typed_query(text)
            self.assertEqual(report["answer"]["decision"], "INCREASE")
            trace = report["trace"]
            self.assertEqual(trace["measurement"]["trace"]["intervals_mm"], [[30, 30], [39, 41]])
            source = trace["source_reading"]
            fields = [*source["observations"], {k: source["question"][k] for k in ("head", "body")}]
            for group in fields:
                for item in group.values():
                    a, b = item["utf8_span"]
                    self.assertEqual(text.encode()[a:b].decode(), item["text"])
            ids = source["question"]["head_cells"]
            if q == UP:
                self.assertEqual(render_word(ids), "هَلْ")
            else:
                self.assertIsNone(ids)

    def test_precision_and_cause_do_not_erase_the_observation(self):
        uncertain = SECOND.replace("٤٠ ± ١", "٣١ ± ١")
        self.assertEqual(typed_query(FIRST + uncertain + UP)["answer"]["decision"], "UNRESOLVED_PRECISION")
        missing = FIRST + SECOND.replace(" ± ١", "")
        self.assertEqual(typed_query(missing + UP)["trace"]["missing"], ["R2.error"])
        cause = typed_query(FIRST + SECOND + CAUSE)
        self.assertIsNone(cause["answer"])
        self.assertEqual(cause["trace"]["missing"], ["causal_design"])
        self.assertEqual(cause["trace"]["measurement"]["answer"]["decision"], "INCREASE")

    def test_signed_arithmetic_without_fabricated_precision(self):
        if not core.scoped_composition.NATIVE.is_file():
            self.skipTest("Requires the installed native arithmetic checker")
        text = FIRST + SECOND.replace("٤٠ ± ١", "٢٥")
        answer = typed_query(text + DELTA)
        self.assertEqual(answer["answer"]["decision"], "-5")
        self.assertEqual(answer["trace"]["unit"], "mm")
        self.assertTrue(answer["trace"]["arithmetic"]["trace"]["native_check"]["native_checked"])
        for left, right, key in (("الأولى", "الثانية", "-5"), ("الثانية", "الأولى", "5")):
            q = f"كَمْ ناتج طرح القراءة {left} من {right} بالملليمتر؟"
            report = typed_query(text + q)
            self.assertEqual(report["answer"]["decision"], key)
            role = report["trace"]["source_reading"]["question"]["operands"]["minuend"]
            a, b = role["utf8_span"]
            self.assertEqual((text + q).encode()[a:b].decode(), right)
        other = FIRST + SECOND.replace("القضيب", "السلك")
        explicit = "كم ناتج طرح القراءة الأولى من الثانية بالملليمتر؟"
        self.assertEqual(typed_query(other + explicit)["answer"]["decision"], "10")
        self.assertEqual(typed_query(other + DELTA)["answer"]["decision"], "UNALIGNED")
        self.assertEqual(typed_query(text.replace("مم.", ".") + DELTA)["trace"]["missing"], ["R2.unit"])

    def test_complete_consumption_identity_time_and_no_injected_roles(self):
        for text in (FIRST + SECOND + UP + " لا.", FIRST + SECOND + "هل لم يزد الطول؟",
                     FIRST + SECOND.replace("مم", "كغ") + UP, FIRST + SECOND + "كَمْ زاد الطول؟"):
            self.assertIsNone(typed_query(text)["answer"])
        for second in (SECOND.replace("القضيب", "السلك"), SECOND.replace("٢:", "١:")):
            for q in (UP, DELTA):
                self.assertEqual(typed_query(FIRST + second + q)["answer"]["decision"], "UNALIGNED")
        with self.assertRaises(ValueError):
            core.measurement_question({"source_ar": FIRST + SECOND + UP, "readings": []})

    def test_induction_skips_unread_training_and_keeps_deferred_probe(self):
        source = FIRST + SECOND + UP
        missing = {"source_ar": source.replace(" ± ١", "")}
        lesson = {"schema": core.SCHEMA, "action": "induce", "unit": "measurement",
                  "examples": [missing, {"source_ar": source}], "probes": [missing]}
        result = core.run(lesson)
        self.assertEqual(result["candidate_counts"][0], result["candidate_counts"][1])
        self.assertEqual(result["probes"][0]["missing"], ["R2.error"])
        locations, _ = ntp._lesson_sources(lesson, result)
        self.assertEqual([row["request_path"] for row in locations],
                         ["/payload/input/lesson/examples/0/source_ar", "/payload/input/lesson/examples/1/source_ar",
                          "/payload/input/lesson/probes/0/source_ar"])
        duplicate = deepcopy(lesson)
        duplicate["probes"] = [{"source_ar": source.replace(UP, "هل ازداد الطول؟")}]
        with self.assertRaisesRegex(ValueError, "distinct"):
            core.run(duplicate)
