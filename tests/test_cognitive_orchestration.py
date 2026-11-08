from copy import deepcopy
from pathlib import Path
import json
import os
import subprocess
import unittest
from unittest.mock import patch
from tools.grammar_catalog import orchestration as o
from tools.grammar_catalog import gateway

ROOT=Path(__file__).resolve().parents[1]
NATIVE=ROOT/"formal/.lake/build/bin/exportCognitiveDispatch"
READY=all((ROOT/"formal/.lake/build/bin"/x).is_file() for x in
          ("alignedAcquisition","progressiveUnitProbe","lexicalDenotation"))
if os.environ.get("NABT_REQUIRE_ORCHESTRATION_NATIVE")=="1" and (not READY or not NATIVE.is_file()):
    raise RuntimeError("Native orchestration gates are required")

class DispatchTests(unittest.TestCase):
    def test_exhaustive_policy_against_independent_set_oracle(self):
        table=o.table()
        required=({0,1,2,3},{0,1,2,3,4,5},{0,1,2,3,6},{0,1,2,3,7})
        count=0
        for cursor in range(6):
            for target in range(6):
                for profile,needs in enumerate(required):
                    for mask in range(256):
                        supplied={n for n in range(8) if mask & (1 << n)}
                        expected=cursor==target and needs<=supplied
                        self.assertEqual(o.dispatch(cursor,target,profile,mask,policy=table)=="DISPATCH",expected)
                        count+=1
        self.assertEqual(count,36864)

    @unittest.skipUnless(NATIVE.is_file(),"native exporter unavailable")
    def test_frozen_table_equals_fresh_lean_export(self):
        self.assertEqual(json.loads(subprocess.check_output([str(NATIVE)])),o.table())

    def test_mutation_codes(self):
        for args,code in [((0,1,0,15),"LAYER_SKIPPED"),((0,0,0,14),"DISPATCH_WITHOUT_CONDITION"),
                          ((0,0,0,13),"DISPATCH_WITHOUT_ROW"),((0,0,0,11),"NONLOCAL_WITNESS"),
                          ((0,0,0,7),"CEILING_PROMOTION"),((4,4,1,15),"MAJAZ_BEFORE_TAADTHUR_OR_QARINA"),
                          ((5,5,2,15),"ANALOGY_SCOPE_WITNESS_MISSING"),((5,5,3,15),"DIVISION_TYPED_WITNESS_MISSING")]:
            self.assertEqual(o.dispatch(*args),code)
        for invalid in (True,1.0,-1,6):
            with self.assertRaises(ValueError):o.dispatch(invalid,0,0,15)

    def test_no_caller_authority_or_concept_copy(self):
        for key in ("condition_mask","licensed","model_path","concept_ids","dispatch_table"):
            with self.assertRaises(ValueError):o.validate({"text":"كتب",key:True})
        for mutation in ({"stage_gate":[[True]]},{"condition_gate":[[True]]}):
            with patch.object(o.TABLE.__class__,"read_bytes",return_value=json.dumps(mutation).encode()):
                with self.assertRaisesRegex(ValueError,"STALE_DISPATCH_TABLE"):o.table()

@unittest.skipUnless(READY,"native source owners unavailable")
class OrchestrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((ROOT/"examples/awamil_agent/nominal.json").read_text())
        cls.p["text"]="زَيْدٌ حَكِيمٌ.";cls.p["source_id"]="orchestration_test"
        cls.result=o.run(cls.p)

    def test_source_to_concept_has_contiguous_trace_and_one_identity(self):
        r=self.result
        self.assertEqual([x["name"] for x in r["dispatch_ledger"]],o.table()["layers"])
        self.assertEqual(r["stopped_at"],"concept");self.assertFalse(r["world_truth_established"])
        self.assertEqual(len(r["view_bindings"]),18)
        self.assertEqual(len(r["canonical_concept_ids"]),18)
        self.assertTrue(all(n["concept_ids_ref"]=="/canonical_concept_ids" and not n["new_concept_ids"] for n in r["networks"]))
        for prev,nxt in zip(r["dispatch_ledger"],r["dispatch_ledger"][1:]):
            self.assertTrue(prev["closed"]);self.assertEqual(nxt["previous"],prev["record_id"])
        self.assertTrue(all(x["retrieved_rows"] for x in r["dispatch_ledger"]))
        self.assertFalse(r["owner_reports"]["mantuq"]["assertion_is_external_truth"])
        self.assertFalse(r["owner_reports"]["mantuq"]["request_is_event_occurrence"])
        self.assertEqual(r["awamil"]["partition"],[91,7,2])

    def test_missing_vowels_stops_before_morphology_and_neural_execution(self):
        with patch.object(o,"_lexical",side_effect=AssertionError("unlicensed upper stage")):
            r=o.run({"text":"كتب"})
        self.assertEqual(r["stopped_at"],"orthography")
        self.assertEqual(r["canonical_concept_ids"],[])

    def test_withdraw_lexical_evidence_stops_before_syntax(self):
        with patch.object(o,"_syntax",side_effect=AssertionError("unlicensed syntax")):
            r=o.run({"text":self.p["text"],"source_id":self.p["source_id"]})
        self.assertEqual(r["stopped_at"],"morphology")

    def test_fresh_replay_rejects_source_and_ledger_mutations(self):
        self.assertTrue(o.verify(self.result,expected_request=self.p)["valid"])
        changed=deepcopy(self.result);changed["dispatch_ledger"][0]["closed"]=False
        self.assertFalse(o.verify(changed,expected_request=self.p)["valid"])
        with self.assertRaisesRegex(ValueError,"NONLOCAL_WITNESS"):
            o._local({"source_id":"foreign","source_sha256":self.result["source"]["sha256"]},self.result["source"])

    def test_domain_copy_is_rejected_without_granting_a_new_identity(self):
        changed=deepcopy(self.result);changed["networks"][1]["new_concept_ids"]=["usuli:human"]
        self.assertEqual(o.verify(changed,expected_request=self.p)["code"],"CONCEPT_COPIED_BY_DOMAIN")

    def test_external_gateway_retains_request_and_replay(self):
        request={"schema":"nabt.io.request.v1","route":"cognitive.orchestrate","payload":{"text":"كتب"}}
        report=gateway.run(request)
        result=gateway.accept_output(report,expected_request=request)
        self.assertTrue(result["valid"],result)
