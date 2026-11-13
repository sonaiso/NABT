"""Independent graph interventions, withholding, permutation and gateway controls."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from tools.grammar_catalog import gateway,licensed_speech
from tools.lexical_training import graph_interventions as graph


def node(key,grade,paths,view="joint",role="content"):
    return {"id":key,"status":"LICENSED","grade":grade,"role":role,
            "satisfied_paths":paths,"transition":{"view":view,"position":{"utf8_span":[0,4]}}}


def diamond():
    return [node("a",0,[[]],"sign","sign"),node("b",0,[[]],"sign","sign"),
            node("c",1,[["a"]]),node("d",1,[["b"]]),node("e",2,[["c"],["d"]])]


class GraphLearning(TestCase):
    def test_fork_and_alternate_support(self):
        rows=diamond()
        self.assertEqual(licensed_speech.surviving_nodes(rows,{"a"}),{"b","d","e"})
        self.assertEqual(licensed_speech.surviving_nodes(rows,{"a","b"}),set())
        w=graph.load(graph.MODEL.read_bytes())
        g=graph.encode(rows)
        z=graph.representations(g,w)
        for cuts,gold in [([],[]),([0],[0,2]),([1],[1,3]),([0,1],[0,1,2,3,4])]:
            scores=graph.effects(g,z,w,set(cuts))
            self.assertEqual([i for i,p in enumerate(scores) if p>=.5],gold)

    def test_node_vectors_invariant_to_opaque_ids_and_edge_head_blind_to_parent_labels(self):
        before=diamond()
        alias={n["id"]:str(81-i) for i,n in enumerate(before)}
        after=deepcopy(before)
        for n in after:
            n["id"]=alias[n["id"]]
            n["satisfied_paths"]=[[alias[p] for p in r] for r in n["satisfied_paths"]]
        a=graph.propose(before,["b"]);b=graph.propose(after,[alias["b"]])
        self.assertEqual(a["status"],"PROPOSED")
        self.assertEqual([n["vector"] for n in a["rows"]],[n["vector"] for n in b["rows"]])
        self.assertEqual([n["loss_score"] for n in a["rows"]],[n["loss_score"] for n in b["rows"]])
        swapped=deepcopy(before)
        swapped[2]["satisfied_paths"]=[["b"]]
        c=graph.propose(swapped,["b"])
        self.assertEqual([n["candidate_edges"] for n in a["rows"]],[n["candidate_edges"] for n in c["rows"]])
        self.assertNotEqual(a["rows"][2]["proposed_lost"],c["rows"][2]["proposed_lost"])

    def test_limits_and_model_failure_are_source_relative(self):
        r=diamond()
        self.assertEqual(graph.propose(r,["absent"])["status"],"UNBOUND_WITHDRAWAL")
        with TemporaryDirectory() as d,patch.object(graph,"MODEL",Path(d)/"missing"):
            self.assertEqual(graph.propose(r,[])["status"],"MODEL_UNAVAILABLE")
        for value in (False,"true",1,{"weights":[]},None):
            with self.assertRaises(ValueError):
                licensed_speech.validate({"graph_learning":value})
        self.assertEqual(graph.propose([],[])["status"],"NO_LICENSED_NODES")

    def test_same_authoritative_answer_and_tampered_prediction_rejected(self):
        req={"schema":gateway.REQUEST_SCHEMA,"route":"relations.analyze","payload":{"text":"هَلِ الصُّنْدُوقُ مَفْتُوحٌ؟",
            "licensed_speech":{"withdraw":["sign/0"],"graph_learning":True}}}
        report=gateway.run(req)
        self.assertTrue(gateway.accept_output(report,expected_request=req)["valid"])
        owner=report["execution"]["owner_result"]["licensed_speech"]
        head=owner["graph_learning"]
        self.assertEqual(head["authority"],"NONE")
        self.assertEqual(head["admitted_edges_added"],0)
        self.assertIn("valency/force",owner["revision"]["lost"])
        self.assertIn("valency/content",owner["revision"]["surviving"])
        local=deepcopy(req)
        del local["payload"]["licensed_speech"]["graph_learning"]
        other=gateway.run(local)
        self.assertTrue(gateway.accept_output(other,expected_request=local)["valid"])
        expected=dict(owner)
        del expected["graph_learning"]
        self.assertEqual(expected,other["execution"]["owner_result"]["licensed_speech"])
        head["rows"][0]["loss_score"]=-1.
        self.assertFalse(gateway.accept_output(report,expected_request=req)["valid"])
