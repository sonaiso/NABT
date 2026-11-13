import json
from copy import deepcopy
from pathlib import Path
from unittest import TestCase, skipUnless

from tools.grammar_catalog import gateway, valency

ROOT=Path(__file__).resolve().parents[1]
CASES=json.loads((ROOT/"evidence/valency_v1/contrast.json").read_text())
BASE=json.loads((ROOT/"examples/io_gateway/valency_context.json").read_text())


class WrittenFrames(TestCase):
    def test_separate_arity_from_dependents_and_preserve_ranges(self):
        for ident,text,arity,force,expected in CASES:
            with self.subTest(case=ident):
                result=valency.analyze(text)
                if force is None:
                    self.assertIsNone(result)
                    continue
                row=result["reading"]
                self.assertEqual((row["active_object_arity"],row["force"]),(arity,force))
                self.assertEqual([r["role"] for r in row["roles"]],expected)
                for r in row["roles"]:
                    w=r["witness"]
                    self.assertEqual(text.encode()[slice(*w["utf8_span"])].decode(),w["surface"])
                self.assertFalse(row["world_occurrence_established"])

    def test_nested_proposition_is_believed_or_reported(self):
        for ident,scope in (("belief","CONTENT_OF_BELIEF"),("inform","CONTENT_OF_REPORT")):
            text=next(c[1] for c in CASES if c[0]==ident)
            sub=valency.analyze(text)["reading"]["embedded_predication"]
            self.assertEqual(sub["scope"],scope)
            self.assertFalse(sub["independent_property_assertion"])
        text=next(c[1] for c in CASES if c[0]=="transfer")
        self.assertIsNone(valency.analyze(text)["reading"]["embedded_predication"])

    def test_nominalization_and_attachment_revision(self):
        for label,outer in (("outer_object","desired_content"),("outer_subject","pleasing_content"),("goal","purpose")):
            text=next(c[1] for c in CASES if c[0]==label)
            r=valency.analyze(text)["reading"]
            inner=r["nominal_clause"]
            self.assertIn(outer,[x["role"] for x in r["roles"]])
            self.assertEqual((inner["inner_role"],inner["bearer"]["surface"]),("نائب فاعل","الْبَابُ"))
            self.assertIsNone(inner["time_from_masdar"])
            self.assertFalse(inner["world_occurrence"])
        no_goal=valency.analyze("جَلَسَ الْحَارِسُ.")["reading"]
        self.assertEqual(no_goal["active_object_arity"],0)
        self.assertIsNone(no_goal["nominal_clause"])

    def test_waw_and_lexical_sense(self):
        for surface,options in (("والطالب",["المعية","العطف على الفاعل"]),("وَالطَّالِبَ",["المعية"]),
                                ("وَالطَّالِبُ",["العطف على الفاعل"])):
            self.assertEqual(valency.analyze("سَارَ الْحَارِسُ "+surface)["reading"]["waw_alternatives"],options)
        for label,arity in (("see",1),("think",2)):
            text=next(c[1] for c in CASES if c[0]==label)
            self.assertEqual(valency.analyze(text)["reading"]["active_object_arity"],arity)

    def test_negative_or_nonlocal_does_not_leak(self):
        for text in ("لم يرد الحارس أن يفتح الباب","قيل: جَلَسَ الطَّالِبُ صَبَاحًا.",
                     "لِكَيْ يُفْتَحَ الْبَابَ","أَعْطَى الْحَارِسَ الطَّالِبُ الْكِتَابَ",
                     "ظَنَّ الْحَارِسُ الْبَابَ مَفْتُوحٌ","هل الْبَابُ مَفْتُوحٌ؟"):
            self.assertIsNone(valency.analyze(text))
        unmarked=valency.analyze("لم يُفتَح الباب")["reading"]
        self.assertTrue(unmarked["conditional_cue"])


@skipUnless((ROOT/"formal/.lake/build/bin/verifiedReading").is_file(),"build verifiedReading")
class LedgerBinding(TestCase):
    def setUp(self):
        self.text=BASE["payload"]["text"]
        self.ledger=BASE["payload"]["valency_context"]["ledger"]
        self.reading=valency.analyze(self.text)

    def bind(self,ledger,*,sid="input",text=None):
        t=self.text if text is None else text
        return valency.context_evidence(t,sid,valency.analyze(t,sid),{"ledger":ledger})

    def test_baseline_and_withdrawals(self):
        base=self.bind(self.ledger)
        self.assertTrue(all(base["profiles"].values()))
        for marker,gone,kept in ((" وقوع ","occurrence_in_ledger","capability_witnessed"),
                 (" زمان ","located","reported_instrument"),(" آلة ","reported_instrument","occurrence_in_ledger"),
                 (" سبب_مصرح ","reported_causal_link","occurrence_in_ledger"),(" عضوية ","capability_witnessed","located")):
            cut="".join(line for line in self.ledger.splitlines(keepends=True) if marker not in line)
            now=self.bind(cut)
            self.assertFalse(now["profiles"][gone])
            self.assertTrue(now["profiles"][kept])
        self.assertFalse(base["empirical_causality_established"])
        self.assertEqual(base,self.bind(self.ledger))

    def test_conflict_binding_identity_and_against_forged_precomputed_acceptance(self):
        when=next(l for l in self.ledger.splitlines(keepends=True) if " زمان " in l)
        conflict=self.bind(self.ledger+"ليس "+when)
        self.assertEqual(conflict["bound"]["time"]["candidates"][0]["status"],"CONFLICT")
        self.assertFalse(conflict["profiles"]["located"])
        self.assertTrue(conflict["profiles"]["capability_witnessed"])
        for r in (self.bind(self.ledger,sid="foreign"),self.bind(self.ledger,text=self.text.replace("الْحَارِسُ","الطَّالِبُ"))):
            self.assertFalse(any(r["profiles"].values()))
        bad=deepcopy(BASE);bad["payload"]["valency_context"]["licensed"]=True
        with self.assertRaises(ValueError):gateway.validate_request(bad)

    def test_normal_gateway_and_tampering(self):
        res=gateway.run(BASE)
        self.assertEqual(res["status"],"EXECUTED")
        self.assertTrue(gateway.accept_output(res,expected_request=BASE)["valid"])
        res["execution"]["owner_result"]["valency"]["reading"]["active_object_arity"]=3
        self.assertFalse(gateway.accept_output(res,expected_request=BASE)["valid"])
