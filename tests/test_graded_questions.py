import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.grammar_catalog import gateway, graded_questions as graded, question_frames
from tools.grammar_catalog.operations import digest
from tests.test_relational_bridge import TARGET, request as causal_request

FIXTURE = Path(__file__).resolve().parents[1] / "evidence/graded_question_chains_v1/challenge.json"
CASES = json.loads(FIXTURE.read_bytes())
NATIVE = all((FIXTURE.parents[2]/"formal/.lake/build/bin"/n).is_file()
             for n in ("verifiedReading","temporalContextProbe","scopedCompositionProbe","linguisticTruth"))


def node_map(report):
    return {n["id"]: n for n in report["nodes"]}


def schema(test, report):
    nodes = node_map(report)
    test.assertEqual(len(nodes), len(report["nodes"]))
    test.assertEqual([i for level in report["levels"] for i in level], list(nodes))
    for n in nodes.values():
        citation = report["owners"]
        for key in n["evidence_path"]:
            citation = citation[key]
        test.assertEqual(digest(citation), n["evidence_sha256"])
        for route in n["prerequisite_paths"]:
            for p in route:
                test.assertLess(nodes[p]["grade"], n["grade"])
        if n["status"] == "LICENSED":
            test.assertTrue(n["satisfied_paths"])
    test.assertFalse(report["world_truth_established"])
    test.assertFalse(report["community_practice_established"])


class Admission(unittest.TestCase):
    def test_request_guards(self):
        for route, fields in (("text.read", {"question_chain": False}), ("text.read", {"question_chain": True, "question_cycle": True}),
                              ("relations.analyze", {"question_chain": 1}), ("relations.analyze", {"question_chain": True, "question":"لماذا؟"})):
            with self.assertRaises(ValueError):
                gateway.validate_request({"schema":gateway.REQUEST_SCHEMA, "route":route,"payload":{"text":"النمرقة",**fields}})

    def test_no_cross_scope_or_premature_join(self):
        graph = graded.Chain("نص", "input")
        graph.add("a", graded.PHYS, "cause", "لماذا؟","OPEN",None,["input"])
        with self.assertRaises(ValueError):
            graph.add("b",graded.PHYS,"effect","ما الأثر؟","LICENSED","أثر",["input"],parents=["a"])
        with self.assertRaises(ValueError):
            graph.add("z",graded.PHYS,"cycle","ما الأصل؟","OPEN",None,["input"],parents=["z"])
        for word, agent, patient, instrument, arrived in question_frames.FRAMES:
            source = " ".join((word,agent,patient,"دون استعمال",instrument)) + "."
            g = graded.run(source)
            node = node_map(g)["joint"]
            self.assertEqual((node["status"], node["satisfied_paths"]), ("REFUTED",[["instrument"]]))
            schema(self,g)


@unittest.skipUnless(NATIVE, "build native gateway owners")
class NativeChains(unittest.TestCase):
    def test_frozen_inputs_and_domain_ceilings(self):
        for name,text,expected in CASES:
            with self.subTest(case=name):
                r = graded.run(text)
                schema(self,r)
                self.assertTrue(set(expected.items()) <= {(n["role"],n["status"]) for n in r["nodes"]})
                if name == "outside":
                    self.assertEqual((r["status"],r["nodes"]),("OUTSIDE_SOURCE",[]))
                if name == "count":
                    delta = next(n for n in r["nodes"] if n["role"] == "count_difference")
                    change = next(n for n in r["nodes"] if n["role"] == "change")
                    self.assertEqual((delta["value"],delta["domain"],change["domain"]), (3,graded.MATH,graded.PHYS))
                    self.assertEqual(change["satisfied_paths"], [[delta["id"]]])
                if name == "withdraw":
                    self.assertFalse(any(n["role"] in ("is_a","has_attribute","has_property") for n in r["nodes"]))

    def test_readings_and_inheritance_do_not_mix(self):
        g = graded.run("ما شبكة «صلب»؟")
        identities = [n for n in g["nodes"] if n["role"] == "lexical_sense"]
        self.assertEqual({n["value"] for n in identities},{"G:صلب","A:صلب"})
        by_id = node_map(g)
        for n in g["nodes"]:
            if n["role"] == "is_a":
                edge = by_id[n["satisfied_paths"][0][0]]
                self.assertTrue(n["id"].startswith(edge["prerequisite_paths"][0][0] + "/"))
        retained = graded.run("ما شبكة «القانئ» بعد سحب شاهد «اللون هيئة كالسواد والحمرة»؟")
        self.assertIn("P:لون",[n["value"] for n in retained["nodes"]])
        self.assertNotIn("P:هيئة",[n["value"] for n in retained["nodes"]])
        self.assertIn("denotes_property",[n["role"] for n in retained["nodes"]])

    def test_causal_and_temporal_withdrawal(self):
        p = causal_request()
        first = graded.run(TARGET,bridge=p)
        for suffix, expected in (
                ("جفاف1 دليل_سببي حدث1.", ["LICENSED","LICENSED","DEFER","DEFER"]),
                ("حدث1 وقوع شجرة1.", ["LICENSED","DEFER","DEFER","DEFER"]),
                ("حدث1 زمان يوم1.", ["DEFER"]*4)):
            reduced = {**p,"source_text":p["source_text"].replace(suffix+"\n","")}
            answer = graded.run(TARGET,bridge=reduced)
            schema(self,answer)
            nodes = node_map(answer)
            self.assertEqual([nodes["bridge/"+k]["status"] for k in ("disposition","occurrence","causality","effect")], expected)
        self.assertEqual(node_map(first)["bridge/effect"]["value"],"حدث1")
        self.assertEqual(graded.run(TARGET,bridge=p),first)

    def test_owner_failure_preserved(self):
        with patch("tools.grammar_catalog.scoped_composition.NATIVE", FIXTURE.parent / "no_binary"):
            r=graded.run("2+3")
            self.assertIn(r["status"], ("VERIFICATION_UNAVAILABLE","VERIFICATION_FAILED"))
            self.assertEqual(r["nodes"],[])

    def test_gateway_rejects_edited_chain(self):
        q={"schema":gateway.REQUEST_SCHEMA,"route":"text.read","payload":{"text":"1+2","question_chain":True}}
        r=gateway.run(q)
        self.assertEqual(r["status"], "EXECUTED")
        graph=r["execution"]["owner_result"]["graded_questions"]
        self.assertEqual(graph["profile"], "formal_expression")
        node_map(graph)["formal_result"]["grade"]=0
        self.assertFalse(gateway.accept_output(r, expected_request=q)["valid"])
