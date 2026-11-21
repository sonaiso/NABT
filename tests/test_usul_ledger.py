import json
from pathlib import Path
import unittest

from tools.grammar_catalog import named_matrix


def sample():
    return json.loads((Path(__file__).resolve().parents[1] / "examples/relations/usul_ledger.json").read_text())["payload"]


def evaluate(payload):
    p = payload["named_matrix"]
    return named_matrix.analyze(payload["text"], payload["source_id"], p)


class UsulLedgerTest(unittest.TestCase):
    def test_restricting_one_does_not_restrict_the_other(self):
        result = evaluate(sample())
        self.assertEqual([r["status"] for r in result["answers"]],
                         ["SUPPORTED","REFUTED","REFUTED","SUPPORTED"])
        self.assertTrue(result["answers"][0]["positive"]["observation_ids"])

    def test_open_roster_positive_witness_and_unknown_negative(self):
        p = sample()
        p["named_matrix"]["ledger"] = p["named_matrix"]["ledger"].replace("نطاق_الخزانة حصر عدد_2.\n","")
        rows = evaluate(p)["answers"]
        self.assertEqual([x["status"] for x in rows[:2]], ["SUPPORTED","UNKNOWN"])

    def test_withdrawal_is_not_a_negative_witness(self):
        p = sample()
        p["named_matrix"]["ledger"] = p["named_matrix"]["ledger"].replace("ليس عين_ألف خاصية صفة_نحاسي.\n","")
        rows = evaluate(p)["answers"]
        self.assertEqual([x["status"] for x in rows[:3]],["SUPPORTED","UNKNOWN","UNKNOWN"])

    def test_two_modes_need_two_readings(self):
        p = sample()
        p["named_matrix"]["ledger"] += "قول_واحد صيغة كم_استغراق.\n"
        with self.assertRaises(ValueError):
            evaluate(p)

    def test_fulfillment_cannot_be_supplied_as_a_fact(self):
        p = sample()
        p["named_matrix"]["ledger"] += "قول_مقيد وفاء_بالطلب عمل_تسليم.\n"
        with self.assertRaises(ValueError):
            evaluate(p)

    def test_text_alignment_and_world_evidence_remain_separate(self):
        result = evaluate(sample())
        self.assertFalse(result["surface_alignment_established"])
        self.assertFalse(result["world_truth_established"])

    def test_qualified_capability_is_independent_of_event_occurrence(self):
        p = sample()
        m = p["named_matrix"]
        m["ledger"] = m["ledger"].replace("قيد_صفة صفة_نحاسي", "قيد_قابلية عمل_فتح")
        m["ledger"] += "نوع_مفتاح قابلية_النوع عمل_فتح.\n"
        m["queries"] += [["وقع","حدث_أ","عمل_فتح"]]
        ans = evaluate(p)["answers"]
        self.assertEqual([ans[1]["status"],ans[-1]["status"]],["SUPPORTED","UNKNOWN"])
