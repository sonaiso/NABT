from copy import deepcopy
import json
from hashlib import sha256
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.lexical_training import concepts, shared_encoder as n, teaching as t
from tools.lexical_training import rag_views
from tools.grammar_catalog import gateway, lexical_ontolex

ROOT = Path(__file__).resolve().parents[1]
READY = concepts.NATIVE.is_file()
if os.environ.get("NABT_REQUIRE_SHARED_NATIVE") == "1" and not READY:
    raise RuntimeError("Shared cognition requires the installed native definition owner")
if os.environ.get("NABT_REQUIRE_SHARED_NATIVE") == "1" and not all(
        (ROOT/"formal/.lake/build/bin"/name).is_file() for name in
        ("evidenceLifecycleV1", "verifiedReading", "classicalSemanticProbe")):
    raise RuntimeError("Shared cognition requires source learning and inference owners")


class RepresentationTests(unittest.TestCase):
    def test_order_marks_and_raw_utf8_roundtrip(self):
        texts = ["كَتَبَ", "كُتِبَ", "قُمْتُ", "قُمْتَ", "قُمْتِ", "بت", "تب"]
        encoded = [n.byte_ids(text) for text in texts]
        self.assertEqual(len({tuple(row) for row in encoded}), len(texts))
        for row,text in zip(encoded,texts):
            self.assertEqual(bytes(i-1 for i in row).decode(), text)

    def test_model_contract_rejects_injection_nonfinite_and_shape(self):
        with self.assertRaises(ValueError):
            n.validate_request({"text":"كتب", "model":"/tmp/model"})
        for text in (True, "", "ا"*129):
            with self.assertRaises(ValueError):
                n.byte_ids(text)
        m,_ = n.load_model()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"model.json"
            for key,value in (("gru.bias_hh_l0", [0]), ("gru.bias_hh_l0", [float('nan')]*72)):
                changed = deepcopy(m);changed["parameters"][key] = value
                path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    n.load_model(path)

    def test_first_test_retains_failures_and_baselines(self):
        base = ROOT/"evidence/shared_cognition_v1"
        report = json.loads((base/"FIRST_TEST.json").read_text())
        self.assertEqual(report["weights_sha256"],sha256((base/"model.json").read_bytes()).hexdigest())
        predictions = json.loads((base/"predictions.json").read_text())
        self.assertEqual(report["optimizer_steps"], 100)
        self.assertGreater(report["parameter_delta_l2"], 0)
        self.assertLess(report["portable_max_abs_error"], 1e-4)
        for method,heads in report["metrics"].items():
            for head,metric in heads.items():
                rows = [r["heads"][head] for r in predictions if head in r["heads"]]
                self.assertEqual(metric["n"], len(rows))
                self.assertEqual(metric["top1_correct"], sum(r["predictions"][method] in r["gold"] for r in rows))
        self.assertFalse(report["learned_predictions_grant_authority"])

    def test_eighteen_overlapping_views_reference_existing_owners(self):
        result = rag_views.inventory()
        self.assertEqual(len(result["views"]),18)
        self.assertFalse(result["new_concept_registry"])
        self.assertTrue(all(row["owners"] for row in result["views"]))
        self.assertFalse(result["runtime_execution_performed"])


@unittest.skipUnless(READY, "build lexicalDenotation")
class NativeContinuityTests(unittest.TestCase):
    def test_ten_same_definition_across_views_and_domains(self):
        refs=[]
        for view,domain in (("cognitive_concept","mathematics"),("mafhum","usul"),("mantuq","communication")):
            out=concepts.evaluate({"kind":"cardinal","value":10,"view":view,"domain":domain})
            self.assertTrue(out["native_checked"])
            refs.append(out["concepts"][0]["reference"])
            self.assertFalse(out["world_truth_established"])
        self.assertTrue(all(r==refs[0] for r in refs))
        other=concepts.evaluate({"kind":"cardinal","value":11,"view":"mafhum","domain":"usul"})
        self.assertNotEqual(other["concepts"][0]["reference"],refs[0])
        with self.assertRaises(ValueError):
            concepts.validate({"kind":"cardinal","value":True,"view":"mafhum","domain":"usul"})

    def test_polysemy_preserved_and_ontolex_uses_same_definitions(self):
        out=concepts.evaluate({"kind":"lexical","value":"قلم","view":"mafhum","domain":"usul"})
        refs={r["reference"]["id"]:r["reference"] for r in out["concepts"]}
        self.assertEqual(len(refs),3)
        graph=lexical_ontolex.export({"entry":"قلم","target":[]})["graph"]["@graph"]
        nodes=[node for node in graph if node["@type"]=="ontolex:LexicalConcept"]
        self.assertEqual({node["nabt:sourceSenseID"]:node["nabt:sharedDefinition"]["@value"] for node in nodes}, refs)

    def test_unknown_is_not_meaninglessness_and_missing_native_never_passes(self):
        out=concepts.evaluate({"kind":"lexical","value":"غيرمقيس","view":"madlul","domain":"usul"})
        self.assertEqual(out["status"],"UNMEASURED_ROOT")
        with patch.object(concepts,"NATIVE",ROOT/"missing-checker"):
            out=concepts.evaluate({"kind":"cardinal","value":10,"view":"mafhum","domain":"usul"})
            self.assertFalse(out["native_checked"])
            self.assertEqual(out["status"],"DEFER")

    def test_neural_heads_share_actual_catalogue_without_granting_authority(self):
        out=n.propose({"text":"كَتَبَ"})
        self.assertEqual(out["status"],"PROPOSED",out)
        self.assertEqual(set(out["heads"]),set(n.HEADS))
        refs={r["identity"]["id"]:r["reference"] for r in concepts.catalogue()["concepts"]}
        self.assertEqual({r["label"]:r["concept_reference"] for r in out["heads"]["concept"]},refs)
        self.assertFalse(out["grammar_certified"])
        self.assertFalse(out["intended_sense_established"])
        self.assertFalse(out["world_truth_established"])

    def test_changed_definition_invalidates_trained_model(self):
        model,_=n.load_model();model["concept_references"][next(iter(model["concept_references"]))]["id"]="forged"
        with patch.object(n,"load_model",return_value=(model,"unused")):
            self.assertEqual(n.propose({"text":"كَتَبَ"})["status"],"DEFER")

    def test_gateway_replays_and_rejects_changed_concept_and_neural_score(self):
        for route,payload in (("concept.view",{"kind":"cardinal","value":10,"view":"mafhum","domain":"usul"}),
                              ("neural.propose",{"text":"قُمْتُ"})):
            request={"schema":"nabt.io.request.v1", "route":route,"payload":payload}
            receipt=gateway.run(request)
            self.assertTrue(gateway.accept_output(receipt,expected_request=request)["valid"],receipt)
            changed=deepcopy(receipt)
            # Rehashing cannot replace an independent replay with caller truth.
            changed["execution"]["owner_result"]["world_truth_established"]=True
            self.assertFalse(gateway.accept_output(changed,expected_request=request)["valid"])

    @unittest.skipUnless((ROOT/"formal/.lake/build/bin/evidenceLifecycleV1").is_file(), "build evidenceLifecycleV1")
    def test_gateway_lesson_connects_neural_observation_to_evidence_revision(self):
        request=json.loads((ROOT/"examples/io_gateway/shared_lesson.json").read_text())
        report=gateway.run(request)
        self.assertEqual(report["status"],"EXECUTED",report)
        operation=report["execution"]["owner_result"]["execution"]
        self.assertTrue(operation["owner_verification"]["valid"],operation)
        owner=operation["owner_result"]
        self.assertTrue(owner["execution_measured"])
        self.assertEqual([r["status"] for r in owner["measurements"]["steps"]],
                         ["SUPPORTED","SUPPORTED","SUPPORTED","UNKNOWN","SUPPORTED"])
        self.assertEqual(owner["episode"]["neural_observation"]["status"],"OBSERVED")
        self.assertTrue(gateway.accept_output(report,expected_request=request)["valid"])


class SharedLessonTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/"formal/.lake/build/bin/evidenceLifecycleV1").is_file(), "build evidenceLifecycleV1")
    def test_native_learning_in_mafhum_view_keeps_withdrawal_history(self):
        request=json.loads((ROOT/"examples/cognitive_teaching/learning.json").read_text())
        request["schema"]=t.SCHEMA_V2
        first=t.run_lesson(request)
        request["matrix_id"]="mafhum"
        second=t.run_lesson(request)
        self.assertTrue(second["execution_measured"],second)
        self.assertEqual(first["owner_result"],second["owner_result"])
        self.assertEqual(first["episode"]["operation_sha256"],second["episode"]["operation_sha256"])
        self.assertEqual([row["status"] for row in second["measurements"]["steps"]],
                         ["SUPPORTED","SUPPORTED","SUPPORTED","UNKNOWN","SUPPORTED"])
        self.assertTrue(t.verify_lesson(second,expected_lesson=request)["valid"])
        observations=second["episode"]["neural_observation"]["observations"]
        self.assertEqual(len(observations),len(request["payload"]["sources"]))
        for row,source in zip(observations,request["payload"]["sources"]):
            self.assertEqual(row["source_text"],source["text"])
            self.assertEqual(row["source_sha256"],sha256(source["text"].encode()).hexdigest())
            self.assertFalse(row["proposal"]["world_truth_established"])

    def test_v2_routes_by_actual_operation_without_relabelling_policy(self):
        request=json.loads((ROOT/"examples/cognitive_teaching/qualified.json").read_text())
        request["schema"]=t.SCHEMA_V2
        reference=None
        for view in ("cognitive_concept","mafhum","restricted"):
            request["matrix_id"]=view
            # Check actual dispatch without requiring every old native binary.
            stub={"status":"UNKNOWN","source_answer":{},"conditional_result":None,"conditional_consequence":False}
            with patch.object(t.source_bound,"evaluate_source",return_value=stub) as run:
                result=t.run_lesson(request)
                self.assertEqual(result["status"],"UNKNOWN",result)
                self.assertEqual(run.call_args.args[2]["policy_id"],"guarded_cause")
                episode=result["episode"]["operation_sha256"]
                if reference is None: reference=episode
                self.assertEqual(reference,episode)
        request["payload"]["plan"]["policy_id"]="invented"
        with patch.object(t.source_bound,"evaluate_source") as run:
            self.assertEqual(t.run_lesson(request)["status"],"INVALID_INPUT")
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
