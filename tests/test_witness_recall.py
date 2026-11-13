"""Independent source, support and recall-boundary tests."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.grammar_catalog import gateway, question_cognition
from tools.lexical_training import witness_recall as recall

ROOT=Path(__file__).resolve().parents[1]
Q=question_cognition.QUESTIONS


class WitnessRecall(unittest.TestCase):
    def test_joint_and_source_binding(self):
        text="سيفتح الحارس الباب بالمفتاح إذا وصل المفتاح."
        r=recall.recall(text,Q["joint"][0])
        d=r["decoding"]
        self.assertTrue(d["grade"]["complete"])
        self.assertEqual(d["all_minimal_supports"],[[0,1]])
        self.assertEqual(d["selected_indices"],[0,1])
        self.assertEqual(r["proposal"]["status"],"PROPOSED")
        self.assertEqual(len(d["selected_occurrences"]),2)
        for w in r["memory"]:
            self.assertEqual(text.encode()[slice(*w["utf8_span"])].decode(),w["text"])
        other=recall.recall(text,Q["joint"][0],"other")
        self.assertTrue(set(d["selected_occurrences"]).isdisjoint(other["decoding"]["selected_occurrences"]))

    def test_withdrawal_conflict_and_duplicates(self):
        prefix="سيرسم الرسام الخط"
        refer=recall.recall(prefix+" بالقلم.",Q["instrument"][0])
        no=recall.recall(prefix+" إذا وصل القلم.",Q["instrument"][0])
        self.assertEqual((refer["status"],no["status"]),("SUPPORTED","OPEN"))
        self.assertEqual(len(no["decoding"]["countermodels"]),2)
        opposed=recall.recall(prefix+" بالقلم دون استعمال القلم.",Q["instrument"][0])
        self.assertEqual(opposed["status"],"CONFLICT")
        self.assertEqual(len(opposed["decoding"]["selected_indices"]),2)
        copies=recall.recall(prefix+" بالقلم بالقلم.",Q["instrument"][0])
        self.assertEqual(copies["decoding"]["all_minimal_supports"],[[0],[1]])
        self.assertNotEqual(copies["memory"][0]["occurrence"],copies["memory"][1]["occurrence"])

    def test_neural_failure_and_wrong_order_cannot_alter_conclusion(self):
        text="سيكتب الطالب الدرس إذا وصل القلم بالقلم."
        with patch.object(recall,"load",side_effect=OSError("missing")):
            r=recall.recall(text,Q["instrument"][0])
        self.assertEqual(r["proposal"]["status"],"MODEL_UNAVAILABLE")
        self.assertEqual(r["decoding"]["selected_indices"],[1])
        with patch.object(recall,"propose",return_value={"status":"PROPOSED","rows":[{"index":0},{"index":1}]}):
            second=recall.recall(text,Q["instrument"][0])
        self.assertEqual(r["decoding"],second["decoding"])
        self.assertEqual(recall.recall("غول قديم",Q["instrument"][0])["decoding"],None)

    def test_public_schema(self):
        req=json.loads((ROOT/"examples/io_gateway/witness_recall.json").read_text())
        for change in ({"score":1},{"question_cycle":True},{"witness_recall":1},{"answer":"نعم"}):
            with self.assertRaises(ValueError):
                gateway.validate_request({**req,"payload":{**req["payload"],**change}})
        with self.assertRaises(ValueError):
            gateway.validate_request({**req,"payload":{"text":"أ","witness_recall":True}})

    @unittest.skipUnless((ROOT/"formal/.lake/build/bin/verifiedReading").is_file(),"build gateway owners")
    def test_public_replay_rejects_tampering(self):
        req=json.loads((ROOT/"examples/io_gateway/witness_recall.json").read_text())
        r=gateway.run(req)
        self.assertEqual(r["status"],"EXECUTED")
        self.assertTrue(gateway.accept_output(r,expected_request=req)["valid"])
        memory=r["execution"]["owner_result"]["witness_recall"]["memory"]
        memory[0]["positive"]=not memory[0]["positive"]
        self.assertFalse(gateway.accept_output(r,expected_request=req)["valid"])
