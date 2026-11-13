import csv
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.mock import patch

from tools.grammar_catalog import definition_network, gateway, licensed_speech as speech, valency
from tools.grammar_catalog.operations import ROOT, digest
from tools.lexical_training import speech_force as neural

DATA = ROOT / "evidence/licensed_speech_v1"


def corpus(name):
    with (DATA/name).open(encoding="utf-8") as source:
        return list(csv.DictReader(source, delimiter="\t"))


def run(text, options=None):
    return speech.project(text,"input",options or {},{"valency":valency.analyze(text)})


def nodes(g):
    return {n["id"]:n for n in g["nodes"]}


class ScopeTests(TestCase):
    def test_challenge_and_nonoverlap(self):
        train = {r["text"] for r in corpus("train.tsv")}
        held = corpus("challenge.tsv")
        self.assertFalse(train.intersection(r["text"] for r in held))
        for row in held:
            with self.subTest(case=row["case"]):
                g = run(row["text"])
                self.assertEqual({r["force"] for r in g["decoded"]},set() if row["force"]=="open" else {row["force"]})
                for s in g["decoded"]:
                    self.assertEqual(s["matrix_assertion"],s["force"]=="assert")
                    for r in s["roles"]:
                        self.assertEqual(row["text"].encode()[slice(*r["utf8_span"])].decode(),r["surface"])
                self.assertFalse(g["world_truth_established"])
                self.assertFalse(g["empirical_causality_established"])
                by_id = nodes(g)
                for n in by_id.values():
                    for path in n["prerequisite_paths"]:
                        self.assertTrue(all(by_id[p]["grade"]<n["grade"] for p in path))
                    self.assertTrue(all(n["transition"].get(k) for k in ("carrier","state","position")))
                    src = g["owners"]
                    for part in n["evidence_path"]:
                        src = src[part]
                    self.assertEqual(digest(src),n["evidence_sha256"])

    def test_force_operator_and_content_can_be_withdrawn_independently(self):
        t = "هَلِ الصُّنْدُوقُ مَفْتُوحٌ؟"
        edit = run(t,{"withdraw":["sign/0"]})
        self.assertEqual([w["surface"] for w in edit["decoded"][0]["decisive_written_witnesses"] if w["content_survives"]],["هَلِ"])
        self.assertIn("valency/force",edit["revision"]["lost"])
        self.assertIn("valency/content",edit["revision"]["surviving"])
        self.assertTrue(all(r["node"] in edit["revision"]["surviving"] for r in edit["decoded"][0]["roles"]))
        baseline = run(t)
        self.assertEqual(baseline,run(t,{"withdraw":[]}))
        # Deleting the written operator and punctuation warrants a different fresh matrix ruling.
        plain = run("الصُّنْدُوقُ مَفْتُوحٌ")
        self.assertEqual(plain["decoded"][0]["force"],"assert")
        self.assertEqual([(r["role"],r["surface"]) for r in baseline["decoded"][0]["roles"]],
                         [(r["role"],r["surface"]) for r in plain["decoded"][0]["roles"]])
        self.assertEqual(run(t,{"withdraw":["foreign"]})["revision"]["status"],"UNBOUND_WITHDRAWAL")

    def test_neural_weight_and_source_failure(self):
        with TemporaryDirectory() as temporary, patch.object(neural,"MODEL",Path(temporary)/"missing.json"):
            g=run("هَلْ فَتَحَ الْحَارِسُ الْبَابَ؟")
        self.assertEqual(g["neural"]["status"],"MODEL_UNAVAILABLE")
        self.assertEqual([r["force"] for r in g["decoded"]],["ask"])
        malformed=run("لَيْتَ الْمُهَنْدِسُ مُجْتَهِدٌ")
        self.assertEqual(malformed["force_status"],"OPEN")
        self.assertEqual(run("هَلْ لِكَيْ يُفْتَحَ الْبَابُ؟")["decoded"],[])

    def test_word_categories_source_roles_and_embedded_scope(self):
        g=run("هَلْ فَتَحَ الْمُهَنْدِسُ الصُّنْدُوقَ؟")
        licensed = [n for n in g["nodes"] if n["role"]=="word_kind" and n["status"]=="LICENSED"]
        self.assertIn(["particle"],[n["value"] for n in licensed])
        self.assertIn(["verb"],[n["value"] for n in licensed])
        self.assertIn(["noun"],[n["value"] for n in run("رَجُلٌ")["nodes"] if n["role"]=="word_kind" and n["status"]=="LICENSED"])
        g=run("ظَنَّ الْمُهَنْدِسُ الصُّنْدُوقَ مَفْتُوحًا.")
        self.assertEqual({r["scope"] for r in g["decoded"][0]["roles"] if r["relation"]=="embedding"},{"embedded"})
        g=run("جَلَسَ الْمُهَنْدِسُ صَبَاحًا أَمَامَ الْمَكْتَبِ.")
        self.assertEqual({r["role"] for r in g["decoded"][0]["roles"] if r["relation"]=="restriction"},{"time","place"})

    def test_same_event_under_three_different_operators(self):
        for text,expected in (("اِفْتَحِ الصُّنْدُوقَ بِالْمِفْتَاحِ","request"),
                              ("لَا تَفْتَحِ الصُّنْدُوقَ بِالْمِفْتَاحِ","prohibit"),
                              ("فَتَحَ الْمُهَنْدِسُ الصُّنْدُوقَ بِالْمِفْتَاحِ","assert")):
            g=run(text)
            self.assertEqual({r["force"] for r in g["decoded"]},{expected})
            roles=g["decoded"][0]["roles"]
            self.assertIn(("opened_entity","الصُّنْدُوقَ"),[(r["role"],r["surface"]) for r in roles])
            self.assertIn(("instrument","restriction"),[(r["role"],r["relation"]) for r in roles])
        bare = run("افتح الصندوق")
        self.assertEqual([r["force"] for r in bare["decoded"]],["request"])
        self.assertEqual(bare["owners"]["partial/0"]["scope"],"SOURCE_CONDITIONAL")
        for text in ("لَا تَفْتَحُ الصُّنْدُوقَ", "اِفْتَحِ الصُّنْدُوقُ",
                     "اِفْتَحِ الصُّنْدُوقَ غَرِيبٌ"):
            self.assertEqual(run(text)["decoded"],[])

    def test_rejects_caller_verdicts_and_unknown_models(self):
        for options in ({"force":"assert"},{"withdraw":[False]},{"lexical":{"entry":"بيت","target":[],"accepted":True}},
                        {"model":"/tmp/weights"}, {"withdraw":["a","a"]}):
            with self.assertRaises(ValueError):
                gateway.validate_request({"schema":gateway.REQUEST_SCHEMA,"route":"relations.analyze",
                                          "payload":{"text":"بيت","licensed_speech":options}})


@skipUnless((ROOT/"formal/.lake/build/bin/lexicalDenotation").is_file() and definition_network.CHECKER.is_file(),
            "Build native lexicalDenotation and verifiedReading")
class SemanticTests(TestCase):
    def test_three_lexical_indications_ambiguity_and_mismatch(self):
        for word,index,target,mode in [("فَرَس","فرس","واحد الخيل","mutabaqa"),("إِنْسَان","إنسان","حيوان","tadammun"),
                                       ("عَمَى","عمي","البصر","iltizam")]:
            g=run(word,{"lexical":{"entry":index,"target":[target]}})
            self.assertIn("form/0/"+mode,nodes(g))
            self.assertFalse(g["intended_sense_established"])
        g=run("فَرَس",{"lexical":{"entry":"عمي","target":["البصر"]}})
        self.assertIn("sense/0/iltizam",nodes(g))
        self.assertFalse(any(k.startswith("form/") for k in nodes(g)))
        g=run("عَمَى",{"lexical":{"entry":"عمي","target":["البصر"]},"withdraw":["sense/0/condition/0"]})
        self.assertIn("form/0/iltizam",g["revision"]["lost"])
        self.assertIn("form/0",g["revision"]["surviving"])
        g=run("قَلَم",{"lexical":{"entry":"قلم","target":["الذي يكتب به"]}})
        self.assertEqual({n["value"] for n in g["nodes"] if n["role"]=="candidate_sense"},
                         {"lisan:qalam-writing","lisan:qalam-lot","lisan:qalam-gambling"})

    def test_definition_proof_paths_survive_only_with_relevant_citation(self):
        text="ما شبكة «القانئ»؟"
        result=definition_network.read(text)
        owner=result["readings"][0]
        wid=next(k for k,w in owner["witnesses"].items() if w.get("quote")=="اللون هيئة كالسواد والحمرة")
        g=speech.project(text,"input",{"withdraw":["definition/0/witness/"+wid]},{"definition_network":result})
        lost=[nodes(g)[k]["value"] for k in g["revision"]["lost"]]
        self.assertIn("P:هيئة",lost)
        self.assertNotIn("P:لون",lost)

    def test_ledger_causality_keeps_independent_capability_and_actor(self):
        p=json.loads((ROOT/"examples/io_gateway/valency_context.json").read_text())["payload"]
        t,ctx = p["text"],p["valency_context"]
        frame=valency.analyze(t)
        def read(context,withdraw):
            ledger=valency.context_evidence(t,"input",frame,context)
            return speech.project(t,"input",{"withdraw":withdraw},{"valency":frame,"valency_context":ledger})
        org=read(ctx,["ledger/place"])
        self.assertTrue({"ledger/located","ledger/recorded_event","ledger/cause_to_effect"}<=set(org["revision"]["lost"]))
        self.assertTrue({"ledger/actor","ledger/capability","ledger/instrument"}<=set(org["revision"]["surviving"]))
        edited={"ledger":"".join(l for l in ctx["ledger"].splitlines(keepends=True) if " مكان " not in l)}
        adjusted=read(edited,[])
        for k in ("ledger/located","ledger/recorded_event","ledger/cause_to_effect"):
            self.assertEqual(nodes(adjusted)[k]["status"],"OPEN")
        self.assertFalse(adjusted["empirical_causality_established"])

    def test_gateway_rejects_forged_force(self):
        req={"schema":gateway.REQUEST_SCHEMA,"route":"relations.analyze","payload":{
             "text":"هَلِ الصُّنْدُوقُ مَفْتُوحٌ؟","licensed_speech":{}}}
        result=gateway.run(req)
        self.assertEqual(result["status"],"EXECUTED")
        self.assertTrue(gateway.accept_output(result,expected_request=req)["valid"])
        forged=deepcopy(result)
        forged["execution"]["owner_result"]["licensed_speech"]["decoded"][0]["force"]="assert"
        self.assertFalse(gateway.accept_output(forged,expected_request=req)["valid"])
