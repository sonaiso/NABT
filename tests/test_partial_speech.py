import csv
import json
from unittest import TestCase
from unittest.mock import patch

from tools.grammar_catalog import gateway, licensed_speech as speech, valency
from tools.grammar_catalog.operations import ROOT
from tools.lexical_training import speech_force


def read(text, withdraw=()):
    return speech.project(text,"input",{"withdraw":list(withdraw)},{"valency":valency.analyze(text)})


class PartialReadings(TestCase):
    def test_frozen_cases_and_every_proposed_mark_is_conditional(self):
        with (ROOT/"evidence/partial_speech_v1/paired.tsv").open(encoding="utf-8") as f:
            for c in csv.DictReader(f,delimiter="\t"):
                with self.subTest(case=c["id"]):
                    g=read(c["text"])
                    acts=list(dict.fromkeys(v["force"] for v in g["decoded"]))
                    self.assertEqual(acts,[] if c["expected"]=="OPEN" else c["expected"].split("+"))
                    self.assertFalse(g["world_truth_established"])
                    for r in g["decoded"]:
                        owner=g["owners"][r["owner"]]
                        if owner.get("law")!="nabt.partial-opening-speech.v1":
                            continue
                        self.assertTrue(owner["witnesses"])
                        for term in owner["forms"]:
                            self.assertEqual(c["text"].encode()[slice(*term["utf8_span"])].decode(),term["observed"])
                            self.assertTrue(speech.classical_roles.compatible(term["observed"],term["compatible_form"]))
                        self.assertFalse(owner["world_truth_established"])

    def test_two_acts_have_separate_content_cues_and_participants(self):
        t="يا طلاب المدرسة، افتحوا صندوق المكتب."
        a,b=read(t)["decoded"]
        self.assertEqual([(r["role"],r["surface"]) for r in a["roles"]],
                         [("addressee","طلاب المدرسة"),("possessor","المدرسة")])
        self.assertIn(("opened_entity","صندوق المكتب"),[(r["role"],r["surface"]) for r in b["roles"]])
        cut=read(t,["sign/0"])["revision"]
        self.assertIn(a["force_node"],cut["lost"])
        self.assertIn(b["force_node"],cut["surviving"])
        self.assertIn("partial/0/content",cut["surviving"])

    def test_unmarked_negative_cue_keeps_the_competitor(self):
        t="لم يُفتح باب المدرسة أمس."
        g=read(t)
        owner=g["owners"]["partial/0"]
        self.assertEqual((owner["competing_operator"],owner["polarity"],owner["specific_actor"]),("لِمَ","denied",None))
        self.assertEqual([r["surface"] for r in g["decoded"][0]["roles"] if r["role"]=="passive_subject"],["باب المدرسة"])
        self.assertIsNone(read("لَمْ يُفتَح صندوق البيت أمس.")["owners"]["partial/0"]["competing_operator"])
        self.assertEqual(read("لم يفتح باب المدرسة أمس.")["decoded"],[])

    def test_text_integrity_unknown_attachment_and_order(self):
        for t in ("يا أهل القرية، افتح النافذة", "لعل النافذة مفتوحٌ","افتح النافذة بعد",
                  "افتحِ نافذة البيت","افتح النافذة؛ بعد الظهر","«افتح النافذة بعد الظهر»",
                  "لم يُفتحِ باب المدرسة أمس.","افتح النافذة بعد المدرسة", "لعل النافذةُ مفْتوحة"):
            with self.subTest(text=t):
                self.assertEqual(read(t)["decoded"],[])
        r=read("هل فتحَ البابَ الحارسُ؟")["decoded"][0]["roles"]
        self.assertIn(("opener","الحارسُ"),[(e["role"],e["surface"]) for e in r])
        self.assertIn(("opened_entity","البابَ"),[(e["role"],e["surface"]) for e in r])

    def test_neural_rank_cannot_change_covered_or_open_readings(self):
        bad={"status":"PROPOSED","authority":"NONE","top":"wish"}
        with patch.object(speech_force,"propose",return_value=bad):
            self.assertEqual(read("افتح بوابة القرية قبل العصر.")["decoded"][0]["force"],"request")
            self.assertEqual(read("لعل النافذة مفتوحةً.")["decoded"],[])

    def test_no_transformed_challenge_rows_in_training(self):
        rows,excluded=speech_force.training_examples()
        train={v for r in rows for v in speech_force.training_views(r["text"])}
        with (ROOT/"evidence/partial_speech_v1/paired.tsv").open(encoding="utf-8") as f:
            cases={v["text"] for v in csv.DictReader(f,delimiter="\t")}
        self.assertFalse(train & cases)
        model=json.loads(speech_force.MODEL.read_bytes())
        self.assertEqual((model["n"],model["n_views"]),(len(rows),len(train)))
        self.assertIn("هَلْ فَتَحَ الْحَارِسُ الْبَابَ؟",excluded)

    def test_reader_exposes_both_frames_after_public_replay(self):
        req={"schema":gateway.REQUEST_SCHEMA,"route":"text.read","payload":{
            "text":"يا أهل القرية، افتحوا الباب","licensed_speech":{"withdraw":["sign/0"]}}}
        report=gateway.run(req)
        self.assertEqual(report["status"],"EXECUTED")
        self.assertTrue(gateway.accept_output(report,expected_request=req)["valid"])
        owner=report["execution"]["owner_result"]
        cards=[r for r in owner["cards"] if r["scope"]=="licensed_speech"]
        self.assertEqual(len(cards),2)
        self.assertIn("نداء",cards[0]["understood"])
        self.assertIn("طلب فعل",cards[1]["understood"])
        default_req={"schema":gateway.REQUEST_SCHEMA,"route":"text.read","payload":{"text":"افتح النافذة بعد الظهر."}}
        default=gateway.run(default_req)
        self.assertTrue(gateway.accept_output(default,expected_request=default_req)["valid"])
        card=default["execution"]["owner_result"]["cards"][0]
        self.assertIn("طلب فعل",card["understood"])
        self.assertIn("بعد الظهر",card["understood"])
