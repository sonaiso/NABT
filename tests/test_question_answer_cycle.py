from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.grammar_catalog import gateway, question_answer_cycle as cycle, scoped_composition

FIXTURE = Path(__file__).resolve().parents[1] / "evidence/question_answer_cycle_v1/challenge.json"


class SourceCycle(unittest.TestCase):
    def test_source_only_generation_and_independent_expected_surface_questions(self):
        text = "سيفتح الحارس الباب إذا وصل المفتاح."
        result = cycle.run(text)
        items = {r["operation"]: r for r in result["items"]}
        self.assertEqual(set(items), {"instrument", "condition", "joint", "occurrence"})
        self.assertEqual(items["condition"]["question"], "في العبارة «سيفتح الحارس الباب»، هل يثبت النص اشتراط وصول «المفتاح» للفعل؟")
        for item in items.values():
            self.assertTrue(item["generated_grade"]["complete"])
            self.assertNotEqual(item["contrast"]["grade"]["claim"], "CORRECT")
            self.assertEqual(cycle.run(text, question=item["question"])["items"][0], item)
            self.assertEqual(item["question_parts"]["event"]["event"]["text"], "سيفتح الحارس الباب")
        self.assertEqual(items["occurrence"]["question_parts"]["scope"], "WORLD")
        self.assertEqual(items["instrument"]["question_parts"]["scope"], "SOURCE")

    def test_truth_table_of_independent_cues_and_silence(self):
        source = "سيكتب الطالب الدرس"
        for tool, arrival in product((None, False, True), repeat=2):
            text = source + {True:" بالقلم",False:" دون استعمال القلم",None:""}[tool]
            text += {True:" إذا وصل القلم",False:" دون اشتراط وصول القلم",None:""}[arrival]
            items = {i["operation"]:i for i in cycle.run(text)["items"]}
            rule = lambda x: {True:"SUPPORTED",False:"REFUTED",None:"OPEN"}[x]
            joint = False if False in (tool,arrival) else (True if tool and arrival else None)
            self.assertEqual([items[k]["status"] for k in ("instrument","condition","joint","occurrence")],
                             [rule(tool),rule(arrival),rule(joint),"OPEN"])
            self.assertTrue(all(v["generated_grade"]["complete"] for v in items.values()))

    def test_return_answers_against_frozen_oracle(self):
        for source, op, status, answer, claim, reason in json.loads(FIXTURE.read_bytes()):
            if op == "arithmetic":
                continue
            with self.subTest(source=source, op=op, answer=answer):
                item = next(i for i in cycle.run(source)["items"] if i["operation"] == op)
                assessed, = cycle.run(source, question=item["question"], answer=answer)["items"]
                self.assertEqual((assessed["status"],assessed["submitted_grade"]["claim"],
                                  assessed["submitted_grade"]["reason"]), (status,claim,reason))

    def test_no_question_substitution_or_custom_authority(self):
        source = "سيفتح الحارس الباب بالمفتاح."
        q = cycle.run(source)["items"][0]["question"]
        for changed in (q.replace("الحارس","الرسام"), q.replace("المفتاح","القلم"), q+" أمس"):
            self.assertEqual(cycle.run(source, question=changed, answer="نعم")["status"], "QUESTION_NOT_BOUND_TO_SOURCE")
        for fields in ({"question_cycle":False},{"answer":"نعم"},{"question_cycle":True,"question":q},
                       {"question":q,"answer":True},{"question_cycle":True,"correct":True}):
            with self.assertRaises(ValueError):
                gateway.validate_request({"schema":gateway.REQUEST_SCHEMA,"route":"text.read","payload":{"text":source,**fields}})
        self.assertEqual(cycle.run("ربما سيفتح الحارس الباب")["status"], "OUTSIDE_SOURCE")

    def test_reason_is_graded_against_the_submitted_polarity(self):
        items = cycle.run("سيكتب الطالب الدرس دون استعمال القلم.")["items"]
        decision = next(i for i in items if i["operation"] == "instrument")["owner"]["decision"]
        for text, claim, reason in (
                ("نعم؛ الشاهد «دون استعمال القلم».","CONTRADICTED","OPPOSES_CLAIM"),
                ("لا؛ لأني أظن ذلك.","CORRECT","UNPARSED_REASON")):
            grade = cycle.grade_event(text, decision)
            self.assertEqual((grade["claim"], grade["reason"], grade["complete"]), (claim, reason, False))
        open_decision = next(i for i in items if i["operation"] == "occurrence")["owner"]["decision"]
        grade = cycle.grade_event("نعم؛ الاحتمالان موافقان للنص.", open_decision)
        self.assertEqual((grade["claim"],grade["reason"]), ("UNSUPPORTED","SHOWS_UNDERDETERMINATION"))

    def test_withdrawal_revises_justification_and_preserves_other_question(self):
        full = "سيفتح الحارس الباب بالمفتاح إذا وصل المفتاح."
        short = full.replace(" بالمفتاح","")
        before, after = ({i["operation"]:i for i in cycle.run(t)["items"]} for t in (full,short))
        self.assertEqual(before["instrument"]["status"], "SUPPORTED")
        self.assertEqual(after["instrument"]["status"], "OPEN")
        self.assertEqual(before["condition"]["answer"], after["condition"]["answer"])
        self.assertEqual(after["condition"]["rubric"]["minimal_supports"][0]["evidence_ids"], [0])
        self.assertEqual(after["instrument"]["rubric"]["countermodels"][0]["arrival_condition"], True)
        self.assertEqual(len(after["instrument"]["rubric"]["countermodels"]), 2)

    @unittest.skipUnless(scoped_composition.NATIVE.is_file(), "build scopedCompositionProbe")
    def test_arithmetic_and_exact_types(self):
        for src, op, status, answer, claim, reason in json.loads(FIXTURE.read_bytes()):
            if op != "arithmetic":
                continue
            item, = cycle.run(src)["items"]
            row, = cycle.run(src, question=item["question"], answer=answer)["items"]
            self.assertEqual((row["status"],row["submitted_grade"]["claim"],row["submitted_grade"]["reason"]),
                             (status,claim,reason))
        for text, answer in (("2=2","1"),("2","صحيحة")):
            item, = cycle.run(text)["items"]
            self.assertEqual(cycle.run(text, question=item["question"], answer=answer)["items"][0]
                             ["submitted_grade"]["claim"], "WRONG_TYPE")
        with patch.object(scoped_composition, "NATIVE", scoped_composition.NATIVE.with_name("missing-cycle-native")):
            bad = cycle.run("2+3")
            self.assertEqual((bad["status"],bad["items"]),("VERIFICATION_UNAVAILABLE",[]))

    def test_public_replay_rejects_self_graded_mutation(self):
        source = "سيرسم الرسام الخط بالقلم."
        req = {"schema":gateway.REQUEST_SCHEMA,"route":"text.read","payload":{"text":source,"question_cycle":True}}
        r = gateway.run(req)
        self.assertEqual(r["status"],"EXECUTED")
        report = r["execution"]["owner_result"]["question_answer_cycle"]
        self.assertEqual(report["source_sha256"], sha256(source.encode()).hexdigest())
        report["items"][0]["answer"] = "لا"
        report["items"][0]["generated_grade"]["claim"] = "CORRECT"
        self.assertFalse(gateway.accept_output(r, expected_request=req)["valid"])
