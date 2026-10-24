"""Authored regressions for a bounded negative-polar-question limitation.

The grammar source review distinguishes overt negative matrices from other
uses of ma. These cases do not revise frozen gold, establish all registers of
Arabic, or independently license hal with continuative ma-zala.
"""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import ask_discourse, read_discourse, verify_discourse, verify_discourse_answer


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "examples/construction_training.tsv").read_bytes()
CONTEXT = json.loads((ROOT / "examples/construction_context.json").read_text())
REASON = "NEGATIVE_POLAR_QUESTION_REQUIRES_LICENSE"
NEGATIVE_TEXT = "مَا ظَنَّ زيدٌ سالمًا حكيمًا."


def analyses(report):
    return [a for c in report["clauses"] for a in c["analyses"]]


class NegativePolarQuestionBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = learn_qac_lexicon(SOURCE, source_id="authored_negative_polar_guard")

    def read(self, text):
        return read_discourse(text, lexical_model=self.model, context=CONTEXT)

    def ask(self, text, question):
        return ask_discourse(text, question, lexical_model=self.model, context=CONTEXT)

    def test_hal_explicit_negative_matrix_remains_pending_not_rejected(self):
        question = "هل مَا ظَنَّ زيدٌ سالمًا حكيمًا؟"
        report = self.read(question)
        self.assertEqual(report["status"], "DEFER")
        self.assertEqual(report["claims"], [])
        rows = analyses(report)
        self.assertTrue(rows)
        self.assertTrue(all(REASON in a["obligations"] for a in rows))
        self.assertTrue(all(not a["licensed_syntax"] and not a["rejected_candidate"] for a in rows))
        self.assertTrue(any(r.get("kind") == "matrix_negation" and r.get("scope") == "epistemic_matrix"
                            for a in rows for r in a["relations"]))
        answer = self.ask(NEGATIVE_TEXT, question)
        self.assertEqual(answer["status"], "DEFER")
        self.assertEqual(answer["missing_premises"], ["ONE_COMPLETE_QUESTION_READING"])
        self.assertEqual(answer["question_interpretations"], [])
        self.assertEqual(answer["proofs"], [])
        self.assertEqual(answer["counterproofs"], [])
        self.assertTrue(verify_discourse(report, lexical_model=self.model, context=CONTEXT)["valid"])
        self.assertTrue(verify_discourse_answer(answer, lexical_model=self.model, context=CONTEXT)["valid"])

    def test_hamza_preserves_the_negative_matrix_question(self):
        for question in ("أَ مَا ظَنَّ زيدٌ سالمًا حكيمًا؟", "أَمَا ظَنَّ زيدٌ سالمًا حكيمًا؟"):
            with self.subTest(question=question):
                report = self.read(question)
                self.assertEqual(report["status"], "LICENSED_DISCOURSE")
                self.assertFalse(any(REASON in a["obligations"] for a in analyses(report)))
                answer = self.ask(NEGATIVE_TEXT, question)
                self.assertEqual(answer["status"], "SUPPORTED")
                self.assertTrue(answer["proofs"])
                self.assertFalse(answer["query"]["positive"])

    def test_positive_hal_and_existing_continuative_route_are_unchanged(self):
        # The ma-zala check is a non-regression of this bounded guard, not a
        # new independent grammatical license for all hal + ma-zala uses.
        for text, question in (
                ("ظَنَّ زيدٌ سالمًا حكيمًا.", "هل ظَنَّ زيدٌ سالمًا حكيمًا؟"),
                ("ما زال زيدٌ حكيمًا.", "هل ما زال زيدٌ حكيمًا؟")):
            with self.subTest(question=question):
                report = self.read(question)
                self.assertFalse(any(REASON in a["obligations"] for a in analyses(report)))
                self.assertEqual(self.ask(text, question)["status"], "SUPPORTED")

    def test_unparsed_ma_uses_are_not_classified_as_matrix_negation(self):
        for question in ("ما هذا؟", "هل ما عند زيد نافع؟", "هل مُا ظَنَّ زيدٌ سالمًا حكيمًا؟",
                         "هل مَا ظَنَّ زيدٌ سالمًا؟"):
            with self.subTest(question=question):
                report = self.read(question)
                self.assertEqual(report["status"], "DEFER")
                self.assertFalse(any(REASON in a["obligations"] for a in analyses(report)))

    def test_serialized_report_cannot_remove_the_question_limitation(self):
        report = self.read("هل مَا ظَنَّ زيدٌ سالمًا حكيمًا؟")
        forged = deepcopy(report)
        for row in analyses(forged):
            row["obligations"] = [o for o in row["obligations"] if o != REASON]
            row["licensed_syntax"] = True
        self.assertFalse(verify_discourse(forged, lexical_model=self.model, context=CONTEXT)["valid"])


if __name__ == "__main__":
    unittest.main()
