import csv
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.grammar_catalog import definition_network as graph
from tools.lexical_training import definition_messages as neural

DATA=graph.ROOT/"evidence/definition_inheritance_v1"


def claims(r):
    return {v["node"]:v for v in r["claims"]}


@unittest.skipUnless(graph.CHECKER.is_file(),"Build verifiedReading for proof-carrying edges")
class DefinitionNetwork(unittest.TestCase):
    def test_fixed_oracle_positive_negative_and_source_positions(self):
        rows=list(csv.DictReader((DATA/"challenge.tsv").read_text().splitlines(),delimiter="\t"))
        for row in rows:
            with self.subTest(text=row["text"]):
                graph_result=graph.read(row["text"])
                readings=graph_result["readings"]
                if not readings:
                    self.assertEqual(row["text"],"ما شبكة «ززز»؟")
                    continue
                for r in readings:
                    licensed=claims(r)
                    for k in row["required"].split(","):
                        if k!="-":self.assertIn(k,licensed)
                    for k in row["forbidden"].split(","):
                        if k!="-":self.assertNotIn(k,licensed)
                    mask=r["vector"]
                    self.assertEqual(set(licensed),{k for k,b in zip(mask["basis"],mask["mask"],strict=True) if b})
                    self.assertEqual(set(r["licensed_spaces"]),{graph.axis(k) for k in licensed})
                    self.assertTrue(r["ground_check"]["receipt"]["verified"])
                    for c in licensed.values():
                        for proof in c["proofs"]:
                            edges=[r["edges"][key] for key in proof]
                            self.assertEqual((edges[0]["child"],edges[-1]["parent"]),(r["focus"],c["node"]))
                            self.assertTrue(all(a["parent"]==b["child"] for a,b in zip(edges,edges[1:])))
                            for edge in edges:
                                witness=r["witnesses"][edge["witness"]]
                                self.assertEqual(witness["status"],"REPLAYED")
                                raw=graph.dictionary.SOURCE.read_bytes()[slice(*witness["span"])]
                                self.assertEqual(raw.decode(),witness["quote"])

    def test_separate_axes_and_senses(self):
        r=graph.read("ما شبكة «الصلب»؟")
        self.assertEqual({v["focus"] for v in r["readings"]},{"G:صلب","A:صلب"})
        for v in r["readings"]:
            if v["focus"]=="A:صلب":
                self.assertNotIn("G:عظم",claims(v))
            else:self.assertNotIn("A:شديد",claims(v))
        for word,focus in (("الرَّامِح","A:رامح"),("الرَّمَّاح","A:رماح")):
            self.assertEqual([s["focus"] for s in graph.read(f"ما شبكة «{word}»؟")["readings"]],[focus])

    def test_withdrawal_masks_messages_and_licensed_dependencies_only(self):
        question="ما شبكة «القانئ»؟"
        a=graph.read(question)["readings"][0]
        b=graph.read("ما شبكة «القانئ» بعد سحب شاهد «اللون هيئة كالسواد والحمرة»؟")["readings"][0]
        self.assertEqual(set(claims(a))-set(claims(b)),{"P:هيئة"})
        for k in claims(b):self.assertEqual(claims(a)[k],claims(b)[k])
        self.assertEqual(a["vector"]["basis"],b["vector"]["basis"])
        va,vb=(g["neural"]["vectors"] for g in (a,b))
        self.assertEqual(set(va)-set(vb),{"denotes_property/P:هيئة"})
        self.assertEqual({k:va[k] for k in vb},vb)
        self.assertEqual(graph.read(question)["readings"][0],a)
        unbound=graph.read("ما شبكة «القانئ» بعد سحب شاهد «المقلمة بالكسر وعاء الأقلام»؟")
        self.assertEqual(unbound["status"],"WITHDRAWAL_NOT_BOUND_TO_READING")

    def test_alternate_witness_paths_and_blocked_cycles(self):
        nodes,by,refs=graph.inventory()
        refs=graph.witness_rows(refs,graph.dictionary.SOURCE.read_bytes(),None)
        # Synthetic second support for the proof-replay operation, never installed as a lexical fact.
        by=deepcopy(by)
        extra={**by["G:برنية"][0],"parent":"G:وعاء","witness":"case"}
        by["G:برنية"].append(extra)
        r=graph.one_reading("G:برنية",by,refs,"test","test")
        self.assertEqual(len(claims(r)["G:وعاء"]["proofs"]),2)
        refs["vessel"]["status"]="WITHDRAWN_IN_SCENARIO"
        r=graph.one_reading("G:برنية",by,refs,"test","test")
        self.assertEqual(len(claims(r)["G:وعاء"]["proofs"]),1)
        bank=json.loads(graph.RESOURCE.read_bytes())
        bank["edges"].append({"child":"G:وعاء","relation":"is_a","parent":"G:مقلمة","witness":"case"})
        with self.assertRaisesRegex(ValueError,"Cyclic"):graph.compile_review(json.dumps(bank).encode())

    def test_failure_and_neural_scores_never_license_edges(self):
        t="ما شبكة «النمرقة»؟"
        orig=graph.read(t)["readings"][0]
        with patch.object(neural,"MODEL_SHA","wrong"):
            no_model=graph.read(t)["readings"][0]
            self.assertEqual(no_model["claims"],orig["claims"])
            self.assertEqual(no_model["neural"]["status"],"WEIGHTS_UNAVAILABLE")
        with patch.object(graph.pilot,"native",side_effect=ValueError("CHECKER_REJECTED")):
            self.assertEqual(graph.read(t)["readings"],[])
        source=graph.dictionary.SOURCE.read_bytes()
        a,b=orig["witnesses"]["rest"]["span"]
        with patch.object(graph.dictionary,"SOURCE",wraps=graph.dictionary.SOURCE) as f:
            f.read_bytes.return_value=source[:a]+b"x"*(b-a)+source[b:]
            r=graph.read(t)
            self.assertEqual(r["status"],"PARTIAL_SOURCE")
            self.assertEqual(set(claims(r["readings"][0])),{"A:صغير","G:وسادة"})

    def test_dict_occurrence_binding(self):
        t="ما معنى «النمرقة»؟"
        d=graph.dictionary.analyze(t)
        r=graph.read(t,d)
        self.assertEqual(r["readings"][0]["dictionary_sense_id"],"mukhtar:pillow")
        self.assertEqual(r["occurrence_span"],d["query"]["citation_span"])
        self.assertEqual(graph.read(t+" ",d)["status"],"VERIFICATION_UNAVAILABLE")
