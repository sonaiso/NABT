"""Independent benchmark integrity and counterexamples, without runtime calls."""
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys
import unittest
from tools.linguistic_truth_benchmark_adapter import build_request,execute_request
from tools.benchmark_linguistic_truth import case_outcome,evaluate,load_gold,observation,summarize,ranking_observation,integrity_check,contract_gate

class BenchmarkIntegrityTests(unittest.TestCase):
    def test_direct_script_help_with_make_pythonpath(self):
        root=Path(__file__).resolve().parents[1]
        completed=subprocess.run([sys.executable,str(root/'tools/benchmark_linguistic_truth.py'),'--help'],cwd=root,env={**os.environ,'PYTHONPATH':'src'},capture_output=True,text=True,timeout=10)
        self.assertEqual(completed.returncode,0,completed.stderr)
        self.assertIn('--require-contracts',completed.stdout)

    def test_gold_is_frozen_and_denominator_fixed(self):
        gold=load_gold()
        self.assertEqual(len(gold['cases']),44)
        self.assertEqual(len({c['id'] for c in gold['cases']}),44)
        self.assertFalse(gold['independence']['external_human_review'])

    def test_expected_label_mutation_cannot_change_transport(self):
        original=load_gold()['cases'][0]
        changed=deepcopy(original)
        changed['expected']={'everything':'opposite'}
        self.assertEqual(build_request(original),build_request(changed))
        request=build_request(original)
        request['text']='changed'
        self.assertNotEqual(request['text'],original['input']['text'])

    def test_request_transport_does_not_manufacture_cues(self):
        case={'input':{'text':'القرء.','profile_id':'linguistic'},'expected':{'selected':'الطهر'}}
        seen=[]
        def acquire(text,**kw):seen.append((text,kw));return {'status':'UNKNOWN'}
        result=execute_request(build_request(case),acquire=acquire,budget_type=dict)
        self.assertEqual(seen,[('القرء.',{'profile_id':'linguistic'})])
        self.assertEqual(result['status'],'UNKNOWN')

    def test_safe_abstention_is_not_positive_acquisition(self):
        case=load_gold()['cases'][0]
        obs=observation({'status':'UNKNOWN','occurrences':[],'world_truth_established':False,'all_arabic_complete':False})
        checks=evaluate(case,obs)
        self.assertEqual(case_outcome(checks),'FAIL')
        self.assertTrue(any(c['name']=='selected_senses' and c['outcome']=='FAIL' for c in checks))

    def test_missing_dimension_stays_unmeasured(self):
        case=next(c for c in load_gold()['cases'] if c['id']=='S447')
        obs=observation({'status':'UNKNOWN','occurrences':[],'world_truth_established':False,'all_arabic_complete':False})
        checks=evaluate(case,obs)
        self.assertEqual(case_outcome(checks),'UNMEASURED')
        self.assertTrue(any(c['name'].startswith('source_understanding.') and c['outcome']=='UNMEASURED' for c in checks))

    def test_world_claim_fails_even_if_linguistic_result_is_missing(self):
        case=load_gold()['cases'][0]
        obs=observation({'status':'COMPLETE','world_truth_established':True,'all_arabic_complete':False})
        self.assertEqual(case_outcome(evaluate(case,obs)),'FAIL')

    def test_resource_exhaustion_is_not_linguistic_rejection(self):
        case=next(c for c in load_gold()['cases'] if c['id']=='B01')
        obs=observation({'status':'UNKNOWN','occurrences':[],'world_truth_established':False,'all_arabic_complete':False})
        self.assertEqual(case_outcome(evaluate(case,obs)),'FAIL')

    def test_summary_keeps_unmeasured_denominator(self):
        rows=[{'family':'x','outcome':'PASS','executed':True,'checks':[]}, {'family':'x','outcome':'FAIL','executed':True,'checks':[]}, {'family':'x','outcome':'UNMEASURED','executed':False,'checks':[]}]
        s=summarize(rows)
        self.assertEqual((s['total_cases'],s['pass'],s['fail'],s['unmeasured'],s['executed']),(3,1,1,1,2))

    def test_excluded_sense_is_not_selected(self):
        raw={'status':'UNKNOWN','world_truth_established':False,'all_arabic_complete':False,'occurrences':[{'surface':'الأسد','candidates':[{'sense_id':'a','gloss':'الحيوان المفترس','use_kind':'literal'},{'sense_id':'b','gloss':'الرجل الشجاع','use_kind':'figurative'}],'selected_sense_ids':[],'excluded_sense_ids':['b']}]}
        o=observation(raw)
        self.assertEqual(o['occurrences'][0]['selected'],[])
        self.assertEqual(o['occurrences'][0]['excluded'],['brave_man'])

    def test_public_budget_rejection_prevents_acquisition(self):
        def rejected_budget(**kw):raise ValueError('boolean budget is invalid')
        def forbidden_acquire(*args,**kw):self.fail('acquisition ran after invalid budget')
        observed=execute_request({'text':'القرء.','budget':{'max_readings':True}},acquire=forbidden_acquire,budget_type=rejected_budget)
        self.assertEqual(observed['status'],'INVALID_INPUT')
        self.assertEqual(observed['boundary_rejection']['component'],'runtime.AcquisitionBudget')

    def test_raw_source_roundtrip_requires_matching_bytes_and_hash(self):
        case=next(c for c in load_gold()['cases'] if c['id']=='M09')
        obs={'authority':{},'source':{'raw_text':case['input']['text'],'bytes':1,'sha256':'0'*64}}
        c=next(x for x in evaluate(case,obs) if x['name']=='semantics.source_roundtrip')
        self.assertEqual(c['outcome'],'FAIL')

    def test_candidate_completeness_flag_cannot_hide_missing_native_row(self):
        ids=('qur_hayd','qur_tuhr')
        occurrence={'expression':'القرء','frame':{'convention':'linguistic'},'candidates':[{'designation_id':s,'sense_id':s} for s in ids],'native_checked':True,'native_result':{'complete_proposal':True,'rows':[{'candidate':{'designation':{'id':s},'intended_sense':s}} for s in ids]}}
        acquisition={'occurrences':[occurrence]}
        pair={'baseline':{'acquisition':deepcopy(acquisition),'retrieval':{'candidates':[{'id':'first'},{'id':'last'}],'limit':1000}},'perturbed':{'acquisition':deepcopy(acquisition),'retrieval':{'candidates':[{'id':'last'}],'limit':1,'reversed_for_diagnostic':True}}}
        observed,_=ranking_observation(pair)
        self.assertTrue(observed['all_installed_candidates_examined'])
        pair['perturbed']['acquisition']['occurrences'][0]['native_result']['rows'].pop()
        observed,_=ranking_observation(pair)
        self.assertFalse(observed['all_installed_candidates_examined'])
        self.assertFalse(observed['same_semantic_result'])

    def test_evidence_drift_is_not_a_valid_measurement(self):
        before={'native_checker':{'sha256':'a'},'python_repository_modules':{'runtime.py':'x'}}
        after={'native_checker':{'sha256':'b'},'python_repository_modules':{'runtime.py':'x'}}
        result=integrity_check(before,after)
        self.assertFalse(result['valid'])
        self.assertEqual(result['changed_sections'],['native_checker'])

    def test_contract_gate_cannot_hide_missing_native_checker(self):
        rows=[{'id':str(i),'executed':True,'raw_result':{}} for i in range(44)]
        rows[0]['raw_result']={'status':'COMPLETE','occurrences':[{'occurrence_id':'o','candidates':[{}],'native_checked':False}]}
        summary={'authority':{'obligations':88,'unmeasured':0,'excess_claims':0},'intended_selection':{'false_selected_senses':0}}
        gate=contract_gate(rows,summary,{'valid':True})
        self.assertFalse(gate['passed'])
        self.assertEqual(gate['missing_native_checks'],['0:o'])

    def test_exhaustion_preserves_checked_prefix_without_completeness_claim(self):
        rows=[{'id':str(i),'executed':True,'raw_result':{}} for i in range(44)]
        rows[0]['raw_result']={'status':'RESOURCE_EXHAUSTED','acquisition_scan_complete':False,'all_installed_readings_retained':False,'occurrences':[{'candidates':[{}],'native_checked':True,'certified_sense_ids':['verified_prefix']}]}
        summary={'authority':{'obligations':88,'unmeasured':0,'excess_claims':0},'intended_selection':{'false_selected_senses':0}}
        self.assertTrue(contract_gate(rows,summary,{'valid':True})['passed'])
        rows[0]['raw_result']['occurrences'][0]['native_checked']=False
        self.assertFalse(contract_gate(rows,summary,{'valid':True})['passed'])

if __name__=='__main__':unittest.main()
