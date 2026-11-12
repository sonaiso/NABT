"""Read actual written bytes; a full-pattern witness and a neural score have distinct authority."""
import json
import unittest
from unittest.mock import patch

from tools.grammar_catalog import awamil_occurrence as law, passive_relation, text_reading
from tools.lexical_training import awamil_occurrence_model as net, awamil_voice as voice
from tools.lexical_training.train_awamil_occurrence import DIR, rows


class OccurrenceCurriculum(unittest.TestCase):
    def test_all_factors_have_heldout_source_bound_roles(self):
        seen=set()
        training={r["text"] for r in rows("train")}
        for gold in rows("heldout"):
            text=gold["text"]
            self.assertNotIn(text,training)
            if gold["relation"].startswith("event_"):
                continue
            parsed,status=law.read(text)
            self.assertEqual(status,"MATCHED_AUTHORED_READING")
            self.assertEqual(len(parsed),1)
            row=parsed[0]
            self.assertEqual((row["factor"],row["relation"]),(gold["factor"],gold["relation"]))
            seen.add(row["factor"])
            for r in row["bindings"].values():
                self.assertEqual(text.encode()[slice(*r["utf8_span"])].decode(),r["surface"])
            for sign in row["signs"]:
                self.assertEqual(text.encode()[slice(*sign["utf8_span"])].decode(),sign["observed"])
            self.assertTrue(row["witnesses"])
            self.assertFalse(row["customary_use_established"])
        self.assertEqual(seen,set(range(1,101)))

    def test_controls_and_last_two_implicit_governors(self):
        for text in json.loads((DIR/"contrast.json").read_bytes())["controls"]:
            self.assertFalse(law.read(text)[0],text)
        for row in rows("heldout"):
            if row["factor"] in (99,100):
                parsed,_=law.read(row["text"])
                self.assertIsNone(parsed[0]["factors"][0]["occurrence"])
        fused=law.read("كَتَبْتُ بِحِبْرٍ")[0][0]["bindings"]
        self.assertEqual(fused["g"]["utf8_span"][1],fused["instrument"]["utf8_span"][0])

    def test_patient_survives_voice_and_negation(self):
        for item in json.loads((DIR/"contrast.json").read_bytes())["heldout"]:
            t=item["text"]
            r=law.read(t,passive_relation.analyze(t))[0][0]
            e=r["event"]
            self.assertEqual((e["voice"],e["polarity"],e["patient"]["surface"]),
                             (item["voice"],item["polarity"],item["patient"]))
            self.assertEqual(e["patient_key"],"القلم")
            self.assertEqual([f["id"] for f in r["factors"]],["jurjani:038","jurjani:092"] if item["polarity"]=="deny" else ["jurjani:092"])
            pred=voice.propose(t)
            self.assertEqual((pred["voice"],pred["polarity"],pred["patient_span"]),(e["voice"],e["polarity"],e["patient"]["utf8_span"]))
        self.assertEqual(law.read("كُسِرَ الْقَلَمُ")[1],"OWNER_OBLIGATION_OPEN")

    def test_swapped_neural_ids_and_source_withdrawal(self):
        text="لَنْ أَدْرُسَ غَدًا"
        src={"id":"input","sha256":law.sha256(text.encode()).hexdigest()}
        with patch.object(net,"propose",return_value={"status":"PROPOSED","factor":3,"authority":"NONE"}):
            cards,report=text_reading.awamil_reading(text,src,[],[])
            self.assertEqual(report["readings"][0]["factor"],34)
            self.assertEqual(len(cards),1)
        with patch.object(law,"pinned_excerpts",side_effect=ValueError("witness withdrawn")):
            cards,report=text_reading.awamil_reading(text,src,[],[])
            self.assertEqual(report["readings"],[])
            self.assertEqual(report["status"],"SOURCE_EVIDENCE_UNAVAILABLE")
            self.assertEqual(cards[0]["scope"],"technical")
        with patch.object(net,"MODEL_SHA","invalid"):
            self.assertEqual(net.propose(text)["status"],"MODEL_UNAVAILABLE")
            self.assertEqual(law.read(text)[0][0]["factor"],34)
