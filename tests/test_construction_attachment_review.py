"""Post-review authored checks of modifier/claim correlation, frozen before repair."""

from hashlib import sha256
import json
from pathlib import Path
import unittest

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import ask_discourse, read_discourse


FOLDER = Path(__file__).resolve().parents[1] / "evidence/constructions/attachment_review"
MATERIAL_SHA256 = "9382cb7a2a4dadf22f9f1614baacf2fee5645656e12c534bb4418aeb30902905"


class ConstructionAttachmentReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = (FOLDER / "material_v1.json").read_bytes()
        if sha256(raw).hexdigest() != MATERIAL_SHA256:
            raise AssertionError("Frozen attachment material changed")
        material = json.loads(raw)
        cls.cases = {case["id"]: case for case in material["cases"]}
        cls.model = learn_qac_lexicon((FOLDER / material["source"]).read_bytes())
        cls.context = json.loads((FOLDER / material["context"]).read_bytes())

    def check_case(self, case_id):
        case = self.cases[case_id]
        expected = case["expected"]
        text = case["text"]
        report = read_discourse(text, lexical_model=self.model, context=self.context)
        self.assertEqual(report["status"], expected["document_status"])
        self.assertEqual(len(report["claims"]), expected["claim_count"])
        claim = report["claims"][0]
        self.assertEqual({key: claim[key] for key in expected["claim"]}, expected["claim"])
        analyses = [analysis for clause in report["clauses"] for analysis in clause["analyses"]
                    if analysis["licensed_syntax"] and analysis["references_complete"]
                    and not analysis["rejected_candidate"]]
        self.assertTrue(analyses)
        for analysis in analyses:
            with self.subTest(case=case_id, analysis=analysis["analysis_id"]):
                self.assertEqual(analysis["claims"], [expected["claim"]])
                assignments = [a for a in analysis["assignments"]
                               if a.get("actual_role") == expected["attachment_role"]]
                relations = [r for r in analysis["relations"]
                             if r.get("kind") == expected["attachment_role"]]
                self.assertTrue(assignments)
                self.assertTrue(relations)
                for assignment in assignments:
                    self.assertEqual(assignment["surface"], expected["dependent_surface"])
                    self.assertEqual(assignment["inflected_case"], expected["required_case"])
                    self.check_span(text, assignment["span"], expected["dependent_span"], expected["dependent_surface"])
                    self.check_span(text, assignment["head_span"], expected["head_span"], expected["head_surface"])
                for relation in relations:
                    self.check_span(text, relation["dependent_span"], expected["dependent_span"], expected["dependent_surface"])
                    self.check_span(text, relation["head_span"], expected["head_span"], expected["head_surface"])
        answer = ask_discourse(text, case["question"], lexical_model=self.model, context=self.context)
        self.assertEqual(answer["status"], expected["answer_status"])

    def check_span(self, text, span, expected_bounds, expected_surface):
        self.assertIsInstance(span, dict)
        raw = text.encode("utf-8")
        self.assertEqual(span["source_id"], "input")
        self.assertEqual(span["source_sha256"], sha256(raw).hexdigest())
        self.assertEqual([span["start"], span["end"]], expected_bounds)
        selected = raw[span["start"]:span["end"]]
        self.assertEqual(selected.decode("utf-8"), expected_surface)
        self.assertEqual(span["span_sha256"], sha256(selected).hexdigest())

    def test_simple_nominal_place(self):
        self.check_case("ATT-P01")

    def test_relative_verb_cannot_own_matrix_place(self):
        self.check_case("ATT-B01")

    def test_simple_nominal_time(self):
        self.check_case("ATT-P02")

    def test_relative_verb_cannot_own_matrix_time(self):
        self.check_case("ATT-B02")

    def test_vso_event_keeps_verbal_head(self):
        self.check_case("ATT-P03")

    def test_svo_event_keeps_verbal_head(self):
        self.check_case("ATT-P04")


if __name__ == "__main__":
    unittest.main()
