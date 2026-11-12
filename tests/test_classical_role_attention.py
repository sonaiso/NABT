"""Authentic source witnesses, pointer semantics and invariant/variant role edges."""
from copy import deepcopy
from hashlib import sha256
import json
import unittest
from unittest.mock import patch

from tools import evaluate_classical_attention as trial
from tools.grammar_catalog import classical_roles as law, gateway, text_reading
from tools.lexical_training import classical_attention as model
from tools.lexical_training import train_classical_attention as training

HELP = "ساعَدَ المُعَلِّمَيْنِ الطَّالِبانِ"
READY = all((law.ROOT / "formal/.lake/build/bin" / x).is_file()
            for x in ("alignedAcquisition","connectedAcquisitionV3","progressiveUnitProbe","lexicalDenotation","linguisticTruth"))


class ClassicalRoles(unittest.TestCase):
    def test_roles_are_bound_to_real_bytes_and_book_witnesses(self):
        graph = law.analyze(HELP)
        nodes = {v["id"] for v in graph["nodes"]}
        self.assertEqual({v["space"] for v in graph["nodes"]}, set("SCMGA"))
        for e in graph["edges"]:
            self.assertIn(e["from"], nodes)
            self.assertIn(e["to"], nodes)
            for ref in e.get("evidence", []):
                w = graph["witnesses"][ref]
                a,b = w["utf8_span"]
                raw = (law.ROOT / w["path"]).read_bytes()[a:b]
                self.assertEqual(sha256(raw).hexdigest(), w["sha256"])
            if e["type"] in ("subject","object"):
                a,b = e["sign_span"]
                self.assertEqual(HELP.encode()[a:b].decode(), "ا" if e["type"] == "subject" else "ي")
        self.assertEqual([r["case_name"] for r in graph["reading"]["object"]["case_rows"]], ["nasb","jarr"])
        self.assertEqual(graph["reading"]["subject"]["term"]["surface"], "الطَّالِبانِ")
        self.assertFalse(graph["world_truth_established"])
        self.assertFalse(graph["customary_use_established"])

    def test_attention_orders_both_candidates_and_cannot_promote_wrong_roles(self):
        proposed = model.propose(HELP)
        self.assertEqual(proposed["status"], "PROPOSED")
        original = law.analyze(HELP, proposed)["reading"]
        a,b = (original[k]["term"]["utf8_span"] for k in ("subject","object"))
        wrong = deepcopy(proposed)
        wrong["heads"]["subject"]["span"], wrong["heads"]["object"]["span"] = b, a
        changed = law.analyze(HELP, wrong)["reading"]
        self.assertEqual(changed["checked_orders"], [[b,a],[a,b]])
        self.assertEqual(original["checked_orders"], [[a,b],[b,a]])
        for role in ("subject","object","sense","force"):
            self.assertEqual(original[role], changed[role])
        for h in proposed["heads"].values():
            self.assertAlmostEqual(sum(x["weight"] for x in h["attention"]),1,places=7)
        wrong["source_sha256"] = "0"*64
        self.assertEqual(law.analyze(HELP, wrong)["reading"], law.analyze(HELP)["reading"])

    def test_withdrawal_and_convention_boundary(self):
        source = {"id":"input","sha256":sha256(HELP.encode()).hexdigest()}
        owner = {"status":"UNKNOWN", "source":source, "native_checked":True,"acquisition_scan_complete":True,"occurrences":[]}
        unavailable = {"status":"MODEL_UNAVAILABLE","authority":"NONE","source_sha256":source["sha256"]}
        with patch.object(model, "propose", return_value=unavailable):
            cards,r = text_reading.classical_reading(HELP, source, [], owner)
            self.assertEqual(len(cards), 1)
            self.assertFalse(r["attention_matches"])
            self.assertEqual(r["usage_handoff"]["status"],"NO_MATCHING_USAGE_OCCURRENCE")
        with patch.object(law, "pinned_excerpts", side_effect=ValueError("source excerpt changed")):
            cards,r = text_reading.classical_reading(HELP,source,[],owner)
            self.assertIsNone(r["graph"])
            self.assertEqual(cards[0]["scope"],"technical")
        graph = law.analyze(HELP)
        owner["occurrences"] = [{"occurrence_id":"x","span":{"start_byte":0,"end_byte":len("ساعَدَ".encode())},
                                 "available_senses":[]}]
        handoff = law.usage_handoff(graph, owner)
        self.assertEqual(handoff["status"],"SENSE_ALIGNMENT_REQUIRED")
        self.assertFalse(handoff["customary_use_established"])
        owner["source"] = {"sha256":"0"*64}
        self.assertEqual(law.usage_handoff(graph,owner)["status"],"UNBOUND_USAGE_SOURCE")

    def test_controls_and_disjoint_first_evaluation(self):
        j = json.loads(trial.CHALLENGE.read_bytes())
        self.assertEqual(sha256(trial.CHALLENGE.read_bytes()).hexdigest(),trial.CHALLENGE_SHA)
        self.assertFalse(set(j["reserved_nouns"]) & {
            law.lookup_key(stem)[2:] for stem in training.PROTOCOL["training_stems"]})
        bank = law.inventory()
        self.assertFalse(set(j["reserved_verbs"]) & {
            law.lookup_key(bank["verbs"][sense][0]) for sense in training.PROTOCOL["training_senses"]})
        for c in j["cases"]:
            with self.subTest(c["id"]):
                self.assertEqual(trial.checked_result(law.analyze(c["text"])),trial.expected(c))
        for c in ("شَكَرَ الضيفٌ الطبيبَ", "ساعَدَ المُعَلِّمَانِ الطّالِبَانِ", "ساعَدَ الطالبَ والمعلمُ"):
            self.assertIsNone(law.analyze(c))
        first=json.loads((model.ROOT/"evidence/grounded_attention_v1/FIRST_TEST.json").read_bytes())
        self.assertEqual(trial.evaluate(),first)

    @unittest.skipUnless(READY, "Build native gateway owners")
    def test_public_bound_question_and_independent_replay(self):
        text = "هل " + HELP + "؟"
        req = {"schema":gateway.REQUEST_SCHEMA,"route":"text.read","payload":{"text":text}}
        receipt = gateway.run(req)
        self.assertEqual(receipt["status"],"EXECUTED",receipt["execution"].get("code"))
        self.assertTrue(gateway.accept_output(receipt,expected_request=req)["valid"])
        view=receipt["execution"]["owner_result"]
        row, = [c for c in view["cards"] if c["scope"] == "classical_role_binding"]
        self.assertEqual(row["evidence"]["force"],"ask")
        self.assertIn("الطَّالِبانِ",row["understood"])
        result=view["classical_role_attention"]
        self.assertTrue(any(e["type"]=="asks_about" for e in result["graph"]["edges"]))
        self.assertFalse(result["usage_handoff"]["customary_use_established"])
        result["graph"]["edges"][-1]["type"]="asserts"
        self.assertFalse(gateway.accept_output(receipt,expected_request=req)["valid"])
