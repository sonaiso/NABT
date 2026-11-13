from itertools import product
from pathlib import Path
import json
import os
import unittest
from unittest.mock import patch

from tools.grammar_catalog import gateway, question_cognition as cognition, question_frames as frames
from tools.lexical_training import question_ranking as ranker, train_question_ranking as training

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "evidence/question_cognition_v1/challenge.json").read_bytes())
READY = all((ROOT / "formal/.lake/build/bin" / name).is_file() for name in
            ("verifiedReading", "epistemicMeasurement", "linguisticTruth", "scopedCompositionProbe", "temporalContextProbe"))
if os.environ.get("NABT_REQUIRE_IO_GATEWAY_NATIVE") == "1" and not READY:
    raise RuntimeError("Question cognition requires its installed native owners")


class QuestionLaws(unittest.TestCase):
    def test_minimal_support_and_independent_alternatives(self):
        head = "سيكتب الطالب الدرس"
        instrument, condition = " بالقلم", " إذا وصل القلم"
        for a, b in product((False, True), repeat=2):
            text = head + instrument * a + condition * b
            result = frames.interpret(text, "joint")
            self.assertEqual(result["status"], "SUPPORTED" if a and b else "OPEN")
            if a and b:
                proof, = result["minimal_supports"]
                self.assertEqual(proof["evidence_ids"], [0, 1])
                self.assertTrue(all(d["status"] == "OPEN" and len(d["alternatives"]) == 2
                                    for d in proof["single_deletions"]))
            else:
                worlds = result["alternatives"]
                self.assertEqual({w["instrument"] and w["arrival_condition"] for w in worlds}, {True, False})
                self.assertTrue(all((not a or w["instrument"]) and (not b or w["arrival_condition"]) for w in worlds))
        only_condition = frames.interpret(head + condition, "instrument")
        self.assertTrue(all(w["arrival_condition"] for w in only_condition["alternatives"]))
        independent = frames.interpret(head + instrument + " دون استعمال القلم" + condition, "occurrence")
        self.assertTrue(all(w["arrival_condition"] and w["instrument"] is None for w in independent["alternatives"]))
        repeated = frames.interpret(head + instrument * 2, "instrument")
        self.assertEqual([s["evidence_ids"] for s in repeated["minimal_supports"]], [[0], [1]])
        self.assertNotEqual(repeated["evidence"][0]["witness"], repeated["evidence"][1]["witness"])

    def test_holds_source_fixed_and_changes_only_relevant_axis(self):
        text = "سيقيس الفني الطول بالمسطرة دون استعمال المسطرة إذا وصلت المسطرة."
        for op, status in (("instrument", "CONFLICT"), ("condition", "SUPPORTED"), ("occurrence", "OPEN")):
            d = frames.interpret(text, op)
            self.assertEqual(d["status"], status)
            self.assertEqual(d["conflicting_axes"], ["instrument"])
            for row in d["evidence"]:
                w = row["witness"]
                self.assertEqual(text.encode()[slice(*w["utf8_span"])].decode(), w["text"])
        text = text.replace(" إذا وصلت المسطرة", "")
        self.assertEqual(frames.interpret(text, "condition")["status"], "OPEN")
        self.assertEqual(frames.interpret(text, "instrument")["status"], "CONFLICT")

    def test_reproducible_ranker_and_score_cannot_assert_or_erase_a_reading(self):
        self.assertEqual(training.fit(training.TRAIN.read_bytes()), json.loads(ranker.MODEL.read_bytes()))
        training_questions = {s.split("\t")[1] for s in training.TRAIN.read_text().splitlines()}
        self.assertTrue(training_questions.isdisjoint(q for _, q, _, _ in CASES))
        text, question = CASES[0][:2]
        with patch.object(ranker, "MODEL_SHA", "wrong"):
            report = cognition.analyze(text, question)
            self.assertEqual(report["proposal"]["status"], "MODEL_UNAVAILABLE")
            self.assertEqual(report["decision"]["status"], "OPEN")
        self.assertEqual(cognition.analyze(text, question+" ولماذا؟")["decision"]["status"], "OUTSIDE_QUESTION")

    def test_domain_boundary_does_not_trust_injected_fields(self):
        for route in ("text.read", "relations.analyze"):
            for question in (None, True, "", "س"*300):
                with self.assertRaises(ValueError):
                    gateway.validate_request({"schema": gateway.REQUEST_SCHEMA, "route": route,
                                              "payload": {"text": "كتب", "question": question}})


@unittest.skipUnless(READY, "build native gateway owners")
class NativeQuestionCognition(unittest.TestCase):
    def test_retained_oracles(self):
        for text, question, status, value in CASES:
            with self.subTest(question=question, text=text):
                r = cognition.analyze(text, question)
                self.assertEqual(r["decision"]["status"], status)
                if value is not None or r["operation"] in frames.REQUIRED:
                    self.assertEqual(r["decision"].get("value"), value)
                self.assertFalse(r["world_truth_established"])
                cognition.cards(r)

    def test_genus_comparison_does_not_infer_exclusion_and_retains_all_senses(self):
        r = cognition.compare_definitions("«برنية» أو «ركوة»", "scope")
        comp, = r["value"]
        self.assertEqual({x["node"] for x in comp["shared"]}, {"G:إناء","G:وعاء"})
        self.assertEqual([x["node"] for x in comp["left_attested_only"]], ["P:من_خزف"])
        self.assertEqual([x["node"] for x in comp["right_attested_only"]], ["P:للماء"])
        self.assertFalse(r["absence_from_definition_proves_exclusion"])
        self.assertEqual(len(cognition.compare_definitions("«صلب» أو «ركوة»", "scope")["value"]), 2)

    def test_gateway_rejects_a_changed_decision(self):
        text, question = CASES[0][:2]
        request = {"schema": gateway.REQUEST_SCHEMA, "route": "text.read", "payload": {"text": text, "question": question}}
        receipt = gateway.run(request)
        self.assertEqual(receipt["status"], "EXECUTED")
        result = receipt["execution"]["owner_result"]["question_cognition"]
        self.assertEqual(result["decision"]["status"], "OPEN")
        result["decision"].update(status="SUPPORTED", value=True)
        self.assertFalse(gateway.accept_output(receipt, expected_request=request)["valid"])
