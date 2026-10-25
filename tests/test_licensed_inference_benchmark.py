from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys
import unittest
from tools.licensed_inference_benchmark_adapter import build_request,execute_request
from tools.benchmark_licensed_inference import load_gold,evaluate_case,result_kind,summary,integrity,observe,check,contracts

class IndependentBenchmarkTests(unittest.TestCase):
    def test_frozen_gold_has_38_distinct_cases(self):
        gold=load_gold();self.assertEqual(len(gold['cases']),38);self.assertEqual(len({c['id'] for c in gold['cases']}),38)
        self.assertFalse(gold['independence']['new_runtime_read']);self.assertFalse(gold['independence']['external_human_review'])

    def test_expected_mutation_cannot_change_transport(self):
        a=load_gold()['cases'][0];b=deepcopy(a);b['expected']={'target':'OPPOSITE'}
        self.assertEqual(build_request(a),build_request(b))

    def test_original_implicit_subject_is_not_rewritten(self):
        a=load_gold()['cases'][0];r=build_request(a)
        self.assertIn('إن عرف الحق',r['source_text']);self.assertNotIn('إن عرف زيد الحق',r['source_text'])

    def test_natural_positive_abstention_is_a_miss(self):
        case=next(c for c in load_gold()['cases'] if c['id']=='L26')
        checks=evaluate_case(case,{'target':'UNKNOWN','world_truth_established':False,'all_arabic_complete':False},{})
        self.assertEqual(result_kind(checks),'FAIL')

    def test_unmeasured_aggregate_not_counted_as_pass(self):
        case=next(c for c in load_gold()['cases'] if c['id']=='A01')
        checks=evaluate_case(case,{},{});self.assertEqual(result_kind(checks),'UNMEASURED')

    def test_signed_false_and_missing_support_count_separately(self):
        row={'outcome':'FAIL','family':'fixture','executed':True,'checks':[{'name':'target','actual':'REFUTED','expected':'SUPPORTED','outcome':'FAIL'}]}
        s=summary([row]);self.assertEqual(s['target_observations']['false_supported_literals'],1);self.assertEqual(s['target_observations']['missing_supported_literals'],1)

    def test_typed_budget_rejection_precedes_evaluation(self):
        def budget(**kw):raise ValueError('boolean is not natural')
        def evaluate(*args,**kw):self.fail('should not run')
        raw=execute_request({'mode':'evaluate','source_text':'x','query_text':'y','resource_limit':{'kind':'closure_steps','value':True}},evaluate_fn=evaluate,budget_type=budget)
        self.assertEqual(raw['status'],'INVALID_INPUT');self.assertEqual(raw['boundary_rejection']['component'],'runtime.InferenceBudget')

    def test_aggregation_fixture_transport_does_not_drop_conflict(self):
        seen=[]
        def aggregate(rows):seen.extend(rows);return {'status':'CONFLICT'}
        r={'mode':'aggregate_fixture','readings':[{'id':'r1','positive':True,'negative':True}],'display_limit':1}
        result=execute_request(r,aggregate_fn=aggregate)
        self.assertEqual(seen,[{'positive':True,'negative':True,'clean_positive':False,'clean_negative':False}]);self.assertEqual(result['submitted_reading_ids'],['r1'])

    def test_native_hash_drift_invalidates_measurement(self):
        self.assertFalse(integrity({'native':{'sha256':'x'}},{'native':{'sha256':'y'}})['valid'])

    def test_direct_cli_help_with_make_environment(self):
        root=Path(__file__).resolve().parents[1]
        r=subprocess.run([sys.executable,str(root/'tools/benchmark_licensed_inference.py'),'--help'],cwd=root,env={**os.environ,'PYTHONPATH':'src'},capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr);self.assertIn('--require-contracts',r.stdout)

    def test_defer_with_equal_unclean_readings_is_not_disagreement(self):
        row={'positive':True,'negative':False,'clean_positive':False,'clean_negative':False}
        raw={'aggregation_calculation':{'status':'DEFER','aggregate':{}},'direct_fixture_rows':[row,row]}
        request={'mode':'aggregate_fixture','readings':[{'id':'r1'},{'id':'r2'}]}
        self.assertEqual(observe(raw,request)['aggregate'],'DEFER')

    def test_broad_disagreement_mapping_requires_actual_row_diversity(self):
        rows=[{'positive':True,'negative':False,'clean_positive':True,'clean_negative':False},{'positive':False,'negative':False,'clean_positive':False,'clean_negative':False}]
        raw={'aggregation_calculation':{'status':'DEFER','aggregate':{}},'direct_fixture_rows':rows}
        request={'mode':'aggregate_fixture','readings':[{'id':'r1'},{'id':'r2'}]}
        observed=observe(raw,request)
        self.assertEqual(observed['aggregate'],'DISAGREEMENT');self.assertEqual(observed['native_aggregate_status'],'DEFER')

    def test_numeric_zero_cannot_impersonate_false_authority_flag(self):
        self.assertEqual(check('world_truth_established',0,False)['outcome'],'FAIL')

    def test_changed_native_scope_does_not_reuse_prior_identity(self):
        case=next(c for c in load_gold()['cases'] if c['id']=='L28')
        checks=evaluate_case(case,{'identity':'same_scope_digest'},{'L27':{'identity':'same_scope_digest'}})
        self.assertEqual(next(c for c in checks if c['name']=='different_identity_from')['outcome'],'FAIL')

    def test_complete_parse_without_checked_clean_closure_fails_gate(self):
        rows=[]
        for i in range(38):
            rows.append({'id':str(i),'family':'fixture','mode':'evaluate' if i<32 else 'aggregate_fixture','executed':True,'outcome':'PASS','checks':[check('world_truth_established',False,False),check('all_arabic_complete',False,False)]})
        rows[0].update(observed={'full_licensed_reading':True},raw_result={'status':'SUPPORTED','native_checked':True,'closures_checked':False,'all_readings_complete':True})
        gate=contracts(rows,summary(rows),{'valid':True})
        self.assertFalse(gate['passed']);self.assertFalse(gate['checks']['native_checker_for_complete_readings'])

    def test_preparse_resource_stop_is_not_an_unobserved_or_rejected_reading(self):
        request={'mode':'evaluate','source_text':'x','query_text':'y'}
        raw={'status':'RESOURCE_EXHAUSTED','verified':False,'native_checked':False,'all_readings_complete':False,'readings':[]}
        observed=observe(raw,request)
        self.assertFalse(observed['full_licensed_reading']);self.assertEqual(observed['status'],'RESOURCE_EXHAUSTED')
        self.assertNotIn('full_licensed_reading',observe({'status':'UNKNOWN'},request))

if __name__=='__main__':unittest.main()
