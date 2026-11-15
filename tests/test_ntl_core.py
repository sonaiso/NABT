"""Independent keys, held-out inputs, crossed controls and public-boundary replay."""
from copy import deepcopy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.grammar_catalog import gateway
from tools.lexical_training import ntl_core as core, teaching

ROOT = Path(__file__).resolve().parents[1]
BINS = ("verifiedReading", "lexicalDenotation", "scopedCompositionProbe")
READY = all((ROOT/"formal/.lake/build/bin"/binary).is_file() for binary in BINS)
if os.environ.get("NABT_REQUIRE_IO_GATEWAY_NATIVE") == "1" and not READY:
    raise RuntimeError("Build the relation, lexical and scoped-composition owners for NTL")
P = ["design", "P1", "P2", "P3", "P4", "P5", "P6"]
R = ["R1", "R2"]
E = ["expression"]
G = ["domain"]
O = "عضوية قابلية خاصية حالة مانع معنى مكان زمان نص موضع قراءة حدث حامل يقبل يحول شروط".split()
KEY = {
    "sign": [("ASSERT", ["سالم هو حاضر"]), ("QUESTION", ["هل أنس هو مدقق"]),
             ("VOCATIVE", ["يا سالم"]), ("UNRESOLVED", [])],
    "passage": [("SUPPORTED", ["كلُّ باحثٍ مدققٌ","أنس هو باحث"]),
                ("SUPPORTED", ["كلُّ معدنٍ موصلٌ","كلُّ موصلٍ ناقلٌ","نحاسٌ هو معدنٌ"]),
                ("CONFLICT", ["كلُّ معدنٍ موصلٌ","نحاس هو معدن","ليس نحاس هو موصل"]), ("UNKNOWN", [])],
    "indication": [("mutabaqa", ["lisan:faras"]), ("tadammun", ["maqayis:bayt-origin"]),
                   ("iltizam", ["lisan:ama"]), ("MISSING_TARGET", [])],
    "ontology": [("SCOPED_SOURCE_LICENSE", O), ("SCOPED_SOURCE_LICENSE", O+["وقوع"]),
                 ("CONFLICT", ["مانع"]), ("UNKNOWN_PREMISE", ["وقوع"])],
    "measurement": [("INCREASE",R),("DECREASE",R),("UNRESOLVED_PRECISION",R),("MISSING_READING",["R1"])],
    "experiment": [("REJECT_SHARP_NULL",P), ("INSUFFICIENT_EVIDENCE",P),
                   ("DESIGN_INSUFFICIENT",["design"]), ("MISSING_OUTCOME",["P3"])],
    "formal": [("14",E),("TRUE",E),("DIVISION_BY_ZERO",E),("MISSING_EXPRESSION",[])],
    "program": [("ALL_IN_DOMAIN",G),("ALL_IN_DOMAIN",G),("COUNTEREXAMPLE",["1,0"]),("MISSING_UPPER_BOUND",G)],
    "integrated": [("APPLIES_TO_RECORDED_INTERVAL",R+E+["program","كلُّ متمددٍ متزايدٌ","قضيب هو متمدد"]),
                   ("APPLIES_TO_RECORDED_INTERVAL",R+E+["program","كلُّ متمددٍ متزايدٌ","لوح هو متمدد"]),
                   ("IMPLEMENTATION_DISAGREES",E+["program"]), ("INCREASE_NOT_ESTABLISHED",["R1"])],
}


def session(action, unit, **kw):
    return {"schema": core.SCHEMA, "action": action, "unit": unit, **kw}


def submissions():
    return {u: {stage: {"decision": decision, "witnesses": refs} for stage,(decision,refs) in
                zip(core.STAGES, rows, strict=True)} for u,rows in KEY.items()}


class Validation(unittest.TestCase):
    def test_worksheet_shows_no_decisions_or_receipts(self):
        for unit in KEY:
            r = teaching.run_lesson(session("worksheet", unit))
            self.assertEqual(set(r["cases"]), set(core.STAGES))
            for row in r["cases"].values():
                self.assertFalse(set(row) & {"answer","trace","grade"})

    def test_invalid_and_unanswered_are_distinct(self):
        for req in [session("assess","formal",submissions={"worked":{"decision":"14","witnesses":["x","x"]}}),
                    session("teach","measurement",task={"readings":[]}), session("teach","program",task={
                        "domain":[True,3],"implementation":"signed_delta"}),
                    dict(schema=core.SCHEMA,action="portfolio",submissions={},complete_on_declared_core=True)]:
            self.assertEqual(teaching.run_lesson(req)["status"], "INVALID_INPUT")
        r = teaching.run_lesson(dict(schema=core.SCHEMA,action="portfolio",submissions={}))
        self.assertEqual((r["earned"],r["required"],r["complete_on_declared_core"]), (0,27,False))

    def test_learn_from_changed_measurements_and_withdraw_training(self):
        lesson = json.loads((ROOT/"examples/io_gateway/ntl_minimum_induction.json").read_text())["payload"]["lesson"]
        result = teaching.run_lesson(lesson)
        self.assertEqual(result["candidate_counts"][-1], 1)
        self.assertEqual([p["possible"] for p in result["probes"]], [[True], [False], [False], []])
        self.assertFalse(result["probes"][1]["pattern_seen"])
        self.assertEqual(result["probes"][-1]["status"], "MISSING_READING")
        empty = teaching.run_lesson(dict(lesson, examples=[]))
        self.assertEqual(empty["probes"][1]["status"], "UNDECIDED")
        invalid = teaching.run_lesson(dict(lesson, probes=lesson["examples"][:1]))
        self.assertEqual(invalid["status"], "INVALID_INPUT")

    def test_exact_randomization_flips_ties_null_and_withdrawal(self):
        base = core.curriculum()["experiment"]["cases"]["worked"]
        def examine(rows):
            return core.paired_trial(dict(base,pairs=rows))
        for n in (1,5,6):
            r = examine(base["pairs"][:n])
            self.assertEqual((r["trace"]["extreme"],r["trace"]["assignments"]),(2,2**n))
            self.assertEqual(r["answer"]["decision"]=="REJECT_SHARP_NULL", n==6)
        for changed in ({"intervention":None},{"control":base["intervention"]},{"endpoint":None}):
            self.assertEqual(core.paired_trial(dict(base, **changed))["answer"]["decision"], "UNDEFINED_COMPARISON")
        a = deepcopy(base["pairs"])
        for row in a:
            row["treated"] = 1-row["treated"]
        self.assertEqual(examine(a)["trace"]["observed_mean_difference"],"-2")
        self.assertEqual(examine(a)["trace"]["exact_p"],"1/32")
        a[0]["values"] = [11,11]
        self.assertEqual(examine(a)["trace"]["exact_p"],"1/16")
        a[1]["ids"][0] = a[0]["ids"][1]
        with self.assertRaises(ValueError):
            examine(a)

    def test_independent_length_and_program_edges(self):
        row = dict(object="وتد",day=1,value=10,error=0,unit="cm")
        for change,expected in [({"object":"آخر"},"UNALIGNED"),({"day":1},"UNALIGNED"),
                                ({"value":100,"unit":"mm"},"SAME"),({"error":1},"UNRESOLVED_PRECISION")]:
            r = core.measurement({"readings":[row,dict(dict(row,day=3), **change)]})
            self.assertEqual(r["answer"]["decision"],expected)
        r=core.program({"domain":[-16,16],"implementation":"signed_delta"})
        self.assertEqual(r["trace"]["inputs_checked"],1089)
        self.assertEqual(core.program({"domain":[-1,1],"implementation":"reversed"})["answer"]["witnesses"],["-1,0"])


@unittest.skipUnless(READY,"Build the NTL native checkers")
class Core(unittest.TestCase):
    def test_entire_portfolio_and_loss_of_witness(self):
        answers = submissions()
        r = teaching.run_lesson(dict(schema=core.SCHEMA,action="portfolio",submissions=answers))
        self.assertEqual((r["earned"],r["required"],r["complete_on_declared_core"]), (27,27,True))
        self.assertTrue(all(set(u["grades"].values())=={"CORRECT"} for u in r["units"].values()))
        answers["experiment"]["withdrawal"]["witnesses"] = ["P4"]
        p = teaching.run_lesson(session("assess","experiment",submissions=answers["experiment"]))
        self.assertEqual(p["cases"]["withdrawal"]["grade"],"REVISE")
        p = teaching.run_lesson(session("assess","formal",submissions={}))
        self.assertEqual(p["cases"]["transfer"]["grade"],"UNANSWERED")

    def test_new_arabic_without_caller_roles_and_mixed_unsupported_text(self):
        premise="كلُّ متأملٍ صبورٌ."
        fact="نادر هو متأمل."
        q="هل نادر هو صبور؟"
        for txt, status in [(fact+" "+premise,"SUPPORTED"),(premise+" "+fact,"SUPPORTED"),
                            (premise,"UNKNOWN"),("ليس نادر هو صبور.","REFUTED"),
                            (fact+" "+premise+" ثم ربما تأخر نادر.","UNREAD")]:
            r=core.passage({"text":txt,"query":q})
            self.assertEqual(r["answer"]["decision"],status)
            if status=="SUPPORTED":
                self.assertTrue(all(r["trace"]["certificate_checks"].values()))
                self.assertEqual(set(r["answer"]["witnesses"]),{premise[:-1],fact[:-1]})

    def test_new_lexical_readings_preserve_ambiguity(self):
        r=core.indication({"root":"قلم","target":["الذي يكتب به"]})
        self.assertEqual(r["answer"]["decision"],"SENSE_DEPENDENT")
        self.assertEqual(len(r["trace"]["rows"]),3)
        self.assertEqual(core.indication({"root":"شمس","target":["النهار"]})["answer"]["decision"],"UNMEASURED")

    def test_wrong_subject_negative_news_lost_source_and_native_failure(self):
        task=core.curriculum()["integrated"]["cases"]["worked"]
        for subject, phrase in [("لوح","متزايد"),("قضيب","جامد")]:
            t=dict(task,text=subject+" هو "+phrase+".",query="هل "+subject+" هو "+phrase+"؟")
            self.assertEqual(core.integrated(t)["answer"]["decision"],"NO_MATCHING_CLAIM")
        r=core.integrated(dict(task,text="ليس قضيب هو متزايد.",query="هل ليس قضيب هو متزايد؟"))
        self.assertEqual(r["answer"]["decision"],"NO_MATCHING_CLAIM")
        with patch.object(core.scoped_composition,"evaluate",return_value={"chain_complete":False,"native_check":None}):
            r=teaching.run_lesson(session("assess","formal",task={"text":"2+1"},submissions={
                "new":{"decision":"3","witnesses":["expression"]}}))
        self.assertEqual(r["cases"]["new"]["grade"],"UNGRADABLE")

    def test_new_formal_arithmetic_and_reversible_sign(self):
        self.assertEqual(core.arithmetic({"text":"(7-2)/4"})["answer"]["decision"],"5/4")
        r=core.sign({"text":"هل مروان هو حاضر؟"})
        self.assertTrue(r["trace"]["restored_exactly"])
        self.assertEqual(r["trace"]["reading"]["document"]["raw_text"],"هل مروان هو حاضر؟")

    def test_public_unseen_input_replay_tamper_and_old_course(self):
        request=json.loads((ROOT/"examples/io_gateway/ntl_minimum_new_passage.json").read_text())
        receipt=gateway.run(request)
        self.assertTrue(gateway.accept_output(receipt,expected_request=request)["valid"])
        grade=receipt["execution"]["owner_result"]["cases"]["new"]
        self.assertEqual(grade["grade"],"CORRECT")
        grade["grade"]="REVISE"
        self.assertFalse(gateway.accept_output(receipt,expected_request=request)["valid"])
        older=json.loads((ROOT/"examples/io_gateway/ntl_course_worksheet.json").read_text())
        self.assertEqual(teaching.run_lesson(older["payload"]["lesson"])["status"],"COURSE_SESSION")
