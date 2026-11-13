"""Real-verse routing, occurrence witnesses, field-scoped authority and two independent outputs."""
from copy import deepcopy
from hashlib import sha256
from unittest import TestCase
from unittest.mock import patch

from tools.grammar_catalog import ayat_al_dayn as ayat, gateway
from tools.grammar_catalog.ayat_import import DATA


class VerseRouting(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text=ayat.source()
        cls.report=ayat.analyze(cls.text)

    def test_full_source_reconstruction_and_original_byte_offsets(self):
        report=self.report
        self.assertEqual(sha256(self.text.encode()).hexdigest(),ayat.SOURCE_SHA)
        self.assertEqual((len(self.text.encode()),len(report["tokens"])),(2166,129))
        self.assertEqual([r["position"] for r in report["tokens"]],list(range(1,130)))
        for row in report["tokens"]:
            self.assertEqual(self.text.encode()[slice(*row["utf8_span"])].decode(),row["surface"])
        self.assertEqual(" ".join(x["surface"] for x in report["tokens"]),self.text)
        self.assertEqual(report["counts"]["gate_executed"],128)

    def test_no_roots_from_closed_or_missing_hosts(self):
        for r in self.report["tokens"]:
            if r["root_route"]!="OPEN":
                self.assertIsNone(r["root_input"])
                self.assertIsNone(r["reported_root_claim"])
            else:
                self.assertEqual(r["root_input"],r["source_segment"]["host_surface"])
            if r["reported_root_claim"]:
                self.assertEqual(r["layers"]["RADICAL"],"LICENSED")
        r=self.report["tokens"][120]
        self.assertEqual((r["surface"],r["root_route"]),("بِكُمْ","BLOCKED_NO_LEXICAL_HOST"))
        self.assertEqual((r["source_segment"]["proclitics"],r["source_segment"]["enclitics"]),(["بِ"],["كُمْ"]))

    def test_morphology_claim_scope_and_conflicts(self):
        rows=self.report["tokens"]
        t=rows[5]
        self.assertEqual(t["upstream_class"],"FI3L")
        self.assertEqual(t["upstream_root_state"],"DEFERRED")
        self.assertIn("PATTERN_CANDIDATE_SET",t["deferred_claims"])
        self.assertIn("WORD_CLASS_SLOT",t["licensed_claims"])
        self.assertTrue(t["upstream_weight_display"])
        self.assertIsNone(t["reported_root_claim"])
        for i,wordclass,tag in ((4,"FI3L","PERFECT_IV"),(25,"FI3L","JUSSIVE_IV_DICTATION"),
                 (29,"FI3L","JUSSIVE_VIII"),(31,"ISM","NOUN_ACC_POSSESSIVE"),
                 (78,"FI3L","PERFECT_PASSIVE_3MP"),(95,"HARF","SUBORDINATOR_PLUS_NEGATION"),
                 (107,"HARF","SUBORDINATOR_PLUS_NEGATION")):
            r=rows[i-1]
            self.assertEqual((r["review"]["class"],r["review"]["tag"]),(wordclass,tag))
        self.assertEqual(rows[77]["review"]["class_relation"],"CONFLICT")
        self.assertNotEqual(rows[94]["review"]["source"],rows[106]["review"]["source"])
        self.assertEqual(rows[3]["review"]["lemma"],"آمَنَ")
        self.assertEqual(rows[28]["review"]["root"],"وقي")
        self.assertEqual(rows[45]["root_review_status"],"CONFLICT")
        self.assertIsNone(rows[45]["reported_root_claim"])

    def test_dependency_scope_and_witness_withdrawal(self):
        cards=self.report["cards"]
        covered=[i for c in cards for i in range(c["scope"]["positions"][0],c["scope"]["positions"][1]+1)]
        self.assertEqual(covered,list(range(1,130)))
        self.assertEqual(self.report["counts"]["active"],16)
        cases={5:"debt",12:"scribe",41:"guardian",76:"summons",95:"reasons",97:"trade",107:"trade",110:"sale"}
        for i,name in cases.items():
            with self.subTest(position=i):
                g=ayat.analyze(self.text,[i])
                lost=[c for c in g["cards"] if c["status"]=="WITHDRAWN"]
                self.assertEqual([c["id"] for c in lost],["clause/"+name])
                self.assertIsNone(lost[0]["answer_ar"])
                self.assertIsNone(lost[0]["focus_witness"])
                self.assertEqual(lost[0]["withdrawn_supports"],[i])
        self.assertEqual(ayat.analyze(self.text),self.report)

    def test_scoped_language_and_neural_authority(self):
        g=self.report
        self.assertFalse(g["legal_ruling_established"])
        self.assertEqual(g["resources_used_in_decision"],[])
        self.assertEqual(g["neural"]["authority"],"NONE")
        self.assertGreater(sum(bool(c["focus_witness"]) for c in g["cards"]),0)
        g1={c["id"]:c for c in g["cards"]}
        self.assertEqual(g1["clause/scribe"]["roles"]["agent"]["positions"],[14,14])
        self.assertEqual(g1["clause/summons"]["roles"]["agent"]["surface"],"الشُّهَدَاءُ")
        self.assertIn("مؤجّلة",g1["clause/harm"]["debt"])
        with patch.object(ayat.graph_interventions,"propose",return_value={"status":"MODEL_UNAVAILABLE","authority":"NONE"}):
            no_model=ayat.analyze(self.text)
        self.assertEqual([c["explanation_ar"] for c in no_model["cards"]],[c["explanation_ar"] for c in g["cards"]])
        self.assertTrue(all(c["focus_witness"] is None for c in no_model["cards"]))

    def test_changed_source_missing_guard_and_corrupt_recording(self):
        for edit in (self.text.replace("أَلَّا","إِلَّا",1),self.text+" ",self.text.replace("رَبَّهُ","رَبُّهُ")):
            self.assertEqual(ayat.analyze(edit)["status"],"SOURCE_MISMATCH")
        with self.assertRaises(ValueError):
            ayat.observations((DATA/"hokom.json").read_bytes()+b" ")
        fixture=deepcopy(ayat.observations((DATA/"hokom.json").read_bytes()))
        fixture["rows"][11]["segment"]["host_surface"]="غَيْرُهُ"
        with patch.object(ayat,"observations",return_value=fixture):
            out=ayat.analyze(self.text)
        self.assertEqual([c["id"] for c in out["cards"] if c["status"]=="DEFERRED"],["clause/scribe"])

    def test_gateway_replay_rejects_changed_reading(self):
        req={"schema":gateway.REQUEST_SCHEMA,"route":"ayat.read","payload":{"text":self.text,"withdraw":[97]}}
        receipt=gateway.run(req)
        self.assertTrue(gateway.accept_output(receipt,expected_request=req)["valid"])
        owner=receipt["execution"]["owner_result"]
        self.assertEqual(owner["counts"]["active"],15)
        owner["legal_ruling_established"]=True
        self.assertFalse(gateway.accept_output(receipt,expected_request=req)["valid"])
        for cut in ([0],[130],[False],[1,1],["root"]):
            with self.assertRaises(ValueError):
                gateway.validate_request({**req,"payload":{"text":self.text,"withdraw":cut}})
