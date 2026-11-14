"""Transfer, evidence withdrawal, invalid inputs, and independent public replay."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.grammar_catalog import gateway
from tools.lexical_training import ntl_curriculum as ntl, teaching

ROOT = Path(__file__).resolve().parents[1]
REQUEST = json.loads((ROOT / "examples/io_gateway/ntl_count_change.json").read_text())
SOURCE = REQUEST["payload"]["lesson"]
NATIVE = all((ROOT / "formal/.lake/build/bin" / n).is_file()
             for n in ("temporalContextProbe", "scopedCompositionProbe", "epistemicMeasurement"))

def lesson():
    return deepcopy(SOURCE)

class Framework(unittest.TestCase):
    def test_alignment(self):
        current=json.loads((ROOT/"evidence/cognitive_curriculum_v1/learning_framework.json").read_text())
        aligned=ntl.framework()
        self.assertEqual(aligned["stages"],[s["id"] for s in current["stages"]])
        self.assertEqual(set(aligned["profiles"]),set(ntl.DOMAINS))
        objectives={o["id"] for o in current["objectives"]}
        for p in aligned["profiles"].values():
            self.assertTrue(set(p["objectives"]) <= objectives)
            self.assertEqual(len(p["progression"]),4)
        for bridge in aligned["bridges"]:
            self.assertIn(bridge["from"],ntl.DOMAINS)
            self.assertIn(bridge["to"],ntl.DOMAINS)

    def test_validation(self):
        for update in ({"implementation":"other"}, {"world_truth_established":True},
                       {"answers":{"formal":True}}, {"examples":[{}]}, {"record":False}):
            item=lesson();item.update(update)
            self.assertEqual(teaching.run_lesson(item)["status"],"INVALID_INPUT")
        item=lesson();item["exercise"]["before"]=True
        self.assertEqual(teaching.run_lesson(item)["status"],"INVALID_INPUT")

    def test_learning_from_examples_and_withdrawal(self):
        ex=SOURCE["exercise"];examples=SOURCE["examples"]
        learned=ntl.learn(examples,ex)
        self.assertEqual(learned["candidate_counts"],[10,4,2,1])
        self.assertEqual(learned["prediction"],[True])
        self.assertEqual(ntl.learn(examples,dict(ex,before=8,after=3))["prediction"],[False])
        incomplete=ntl.learn(examples[:1],ex)
        self.assertEqual(incomplete["candidate_counts"],[10,4])
        self.assertTrue(all(n>0 for n in incomplete["next_query"]["split"]))
        self.assertEqual(ntl.learn([],ex)["prediction"],[False,True])

@unittest.skipUnless(NATIVE,"Build io-gateway owners")
class CountChange(unittest.TestCase):
    def test_positive_and_tampering(self):
        req=deepcopy(REQUEST)
        receipt=gateway.run(req)
        self.assertTrue(gateway.accept_output(receipt,expected_request=req)["valid"])
        r=receipt["execution"]["owner_result"]
        self.assertEqual(r["transfer_to_record"],"APPLIES_TO_RECORD")
        self.assertEqual([r["cards"][s]["answer"] for s in ntl.DOMAINS],[5,"ALIGNED",3,True])
        self.assertTrue(all(x["feedback"]=="CORRECT" for x in r["cards"].values()))
        self.assertEqual(r["bridges"]["linguistic_to_physical"]["claims"][0]["status"], "SUPPORTED")
        self.assertEqual(len(r["bridges"]["physical_to_formal"]["observation_ids"]), 2)
        raw=SOURCE["record"].encode()
        claim=r["cards"]["linguistic"]["witness_ids"][0]
        w=next(row["witness"] for row in r["owners"]["record"]["records"] if row["id"]==claim)
        self.assertEqual(raw[slice(*w["utf8_span"])].decode(),w["text"])
        r["cards"]["programming"]["output"]=99
        self.assertFalse(gateway.accept_output(receipt,expected_request=req)["valid"])

    def test_remove_report_or_observation(self):
        for index,want in ((3,("OPEN","ALIGNED","APPLIES_TO_RECORD")),
                           (2,("ATTRIBUTED","OPEN","OPEN"))):
            q=lesson(); lines=q["record"].splitlines();lines.pop(index);q["record"]="\n".join(lines)
            r=teaching.run_lesson(q);c=r["cards"]
            self.assertEqual((c["linguistic"]["status"],c["physical"]["status"],r["transfer_to_record"]),want)
            self.assertEqual((c["formal"]["answer"],c["programming"]["output"]),(3,3))

    def test_units_conflict_and_report_alternatives(self):
        original=SOURCE["record"]; last=original.splitlines()[-1]
        for text,language,physics in [
            (original.replace("٢ [قطعة]", "٢ [جزء]"),"ATTRIBUTED","OPEN"),
            (original+"\nرصد «هند» اليوم ٢: العدد = ٦ [قطعة].","ATTRIBUTED","CONFLICT"),
            (original+"\n"+last.replace("٥","٦"),"MULTIPLE","ALIGNED"),
            (original.replace("رصد «سالم» اليوم ١: العدد = ٢","رصد «سالم» اليوم ١: العدد = ٣"),"ATTRIBUTED","MISMATCH")]:
            q=lesson();q["record"]=text
            r=teaching.run_lesson(q);c=r["cards"]
            self.assertEqual((c["linguistic"]["status"],c["physical"]["status"]),(language,physics))
            self.assertEqual(c["formal"]["answer"],3)
            if language=="MULTIPLE":
                self.assertEqual(c["linguistic"]["readings"],[5,6])
                self.assertEqual(c["linguistic"]["feedback"],"UNGRADABLE")
            if physics!="ALIGNED":self.assertEqual(r["transfer_to_record"],"OPEN")

    def test_incorrect_attribution_is_graded_without_vetoing_independent_bridge(self):
        q=lesson()
        lines=q["record"].splitlines()
        lines[-1]=lines[-1].replace("٥","٦")
        q["record"]="\n".join(lines)
        r=teaching.run_lesson(q)
        self.assertEqual(r["cards"]["linguistic"]["answer"],6)
        self.assertEqual(r["cards"]["linguistic"]["feedback"],"REVISE")
        self.assertEqual(r["bridges"]["linguistic_to_physical"]["claims"][0]["status"],"REFUTED")
        self.assertEqual(r["bridges"]["programming_to_physical"]["status"],"APPLIES_TO_RECORD")

    def test_decreasing_case_is_counterexample_and_zero(self):
        for before,after,impl,wanted in [(5,2,"magnitude",False),(5,2,"signed_delta",True),(0,0,"magnitude",True)]:
            q=lesson()
            q["record"]=q["record"].replace("٢ [قطعة]",f"{before} [قطعة]").replace("٥ [قطعة]",f"{after} [قطعة]")
            q["exercise"].update(before=before,after=after);q["implementation"]=impl
            r=teaching.run_lesson(q);c=r["cards"]
            self.assertIs(c["programming"]["answer"],wanted)
            self.assertEqual(c["formal"]["answer"],after-before)
            self.assertEqual(r["transfer_to_record"],"APPLIES_TO_RECORD" if wanted else "COUNTEREXAMPLE")
            self.assertFalse(r["limits"]["program_proved_for_all_inputs"])

    def test_unsupported_text_and_unavailable_comparison(self):
        q=lesson();q["record"]="قول لم يدخله هذا النحو"
        r=teaching.run_lesson(q)
        self.assertEqual(r["cards"]["linguistic"]["status"],"OUTSIDE_GRAMMAR")
        self.assertEqual(r["cards"]["formal"]["answer"],3)
        with patch.object(ntl.scoped_composition,"evaluate",return_value={
                "chain_complete":False,"status":"DEFER","native_check":None}):
            r=teaching.run_lesson(lesson())
        self.assertIsNone(r["cards"]["programming"]["answer"])
        self.assertEqual(r["transfer_to_record"],"OPEN")

if __name__=="__main__":
    unittest.main()
