"""Finite native oracle and source/scope/withdrawal counterexamples."""
from copy import deepcopy
from itertools import product
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from tools.grammar_catalog import temporal as t
from tools.lexical_training import teaching
from tools.evidence_lifecycle_v1 import ResourceLimit

ROOT=Path(__file__).resolve().parents[1]
READY=(ROOT/'formal/.lake/build/bin/temporalContextProbe').is_file()
if os.environ.get('NABT_REQUIRE_CONTEXT_NATIVE')=='1' and not READY:
    raise RuntimeError('Temporal integration requires its native checker')


def example(name='yesterday'):
    return json.loads((ROOT/'examples/context_application'/f'{name}.json').read_text())


class TemporalInputTests(unittest.TestCase):
    def test_legacy_context_does_not_invent_time(self):
        self.assertEqual(t.context_envelope(None),(None,None,True))
        result=t.evaluate({'text':'كتب','temporal':None})
        self.assertEqual(result['status'],'UNKNOWN')
        self.assertFalse(result['implicit_speech_time_added'])
        self.assertFalse(result['world_truth_established'])
        with self.assertRaises(ValueError):
            t.context_envelope({'schema':'nabt.discourse-context.v2','reference':[],'temporal':None})

    def test_malformed_fields_spans_and_dates_fail_before_native(self):
        mutations=[
            lambda q:q.update(answer=True),
            lambda q:q['temporal']['scopes'][0].update(parent=[]),
            lambda q:q['temporal']['scopes'][0].update(span=[1,2]),
            lambda q:q['temporal']['nodes'][0].update(scope_id=[]),
            lambda q:q['temporal']['relations'][0].update(days=True),
            lambda q:q['temporal']['evidence'][1].update(text='غدًا'),
            lambda q:q['temporal']['evidence'][1].update(active=1),
            lambda q:q['temporal']['nodes'][0]['anchors'][0]['interval'].update(first='20240229'),
            lambda q:q['temporal']['nodes'][0]['anchors'][0]['interval'].update(first='2024-03-01'),
            lambda q:q['temporal']['nodes'][0]['anchors'][0].update(evidence_ids=['invented']),
            lambda q:q['temporal']['nodes'].append(deepcopy(q['temporal']['nodes'][0])),
        ]
        for mutation in mutations:
            q=example();mutation(q)
            with self.subTest(mutation=mutation),patch.object(t,'native') as run:
                with self.assertRaises(ValueError):t.evaluate(q)
                run.assert_not_called()

    def test_no_implicit_cross_scope_or_cyclic_self_support(self):
        q=example('quotation');q['temporal']['relations'][1]['right']='outer-speech'
        with self.assertRaisesRegex(ValueError,'cross-scope'):t.evaluate(q)
        q=example();q['temporal']['relations'][0].update(left='speech',right='event')
        with self.assertRaisesRegex(ValueError,'justify itself'):t.evaluate(q)
        q=example('quotation');q['temporal']['scopes'][0]['parent']='quoted'
        with self.assertRaises(ValueError):t.evaluate(q)

    def test_limits_remain_resource_limits(self):
        q=example();q['temporal']['relations'][0]['days']=36601
        with self.assertRaises(ResourceLimit):t.evaluate(q)
        q=example();q['temporal']['nodes']=[{'id':str(i)} for i in range(33)]
        with self.assertRaises(ResourceLimit):t.evaluate(q)
        q=example('tomorrow');q['temporal']['nodes'][0]['anchors'][0]['interval']={'first':'9999-12-31','last':'9999-12-31'}
        with self.assertRaises(ResourceLimit):t.evaluate(q)

    def test_absent_executable_is_defer_without_forged_native_success(self):
        with patch.object(t,'ROOT',ROOT/'does-not-exist'):
            r=t.evaluate(example())
        self.assertEqual(r['status'],'DEFER')
        self.assertFalse(r['native_checked'])
        self.assertFalse(r['world_truth_established'])


@unittest.skipUnless(READY,'build temporalContextProbe')
class NativeTemporalTests(unittest.TestCase):
    def test_native_signed_transport_rejects_noncanonical_and_boolean_inputs(self):
        requests=[{'op':'shift','interval':{'first':'10','last':'10'},'days':v}
                  for v in (-1,True,'-0','+1','01','1.0','1e2','9'*257)]
        result=subprocess.run([str(ROOT/'formal/.lake/build/bin/temporalContextProbe')],
            input=''.join(json.dumps(r)+'\n' for r in requests),capture_output=True,text=True,check=True)
        replies=[json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(replies),len(requests))
        self.assertTrue(all(r['status']=='ERROR' for r in replies))
        self.assertEqual(replies[-1]['code'],'RESOURCE_LIMIT')

    def test_finite_set_oracle_for_all_six_relations_and_invalid_intervals(self):
        # Enumerated point sets provide an independent finite oracle, including
        # singleton equality, touching endpoints and reversed intervals.
        intervals=[{'first':a,'last':b} for a,b in product(range(-2,3),repeat=2)]+[None]
        requests=[];expected=[]
        for relation,a,b in product(t.RELATIONS,intervals,intervals):
            requests.append({'op':'check','relation':relation,'left':a,'right':b})
            if a is None or b is None:expected.append('UNKNOWN');continue
            left=set(range(a['first'],a['last']+1));right=set(range(b['first'],b['last']+1))
            good=bool(left and right)
            if good:
                good={'before':all(x<y for x in left for y in right),
                      'after':all(x>y for x in left for y in right),
                      'equals':left==right,'intersects':bool(left & right),
                      'contains':left>=right,'within':left<=right}[relation]
            expected.append('CONFIRMED' if good else 'CONFLICT')
        actual=[]
        for start in range(0,len(requests),512):
            receipt=t.native(requests[start:start+512])
            actual.extend(x['response']['verdict'] for x in receipt['calls'])
        self.assertEqual(actual,expected)
        self.assertEqual(len(actual),4056)

    def test_leap_day_and_year_transition_keep_sre_separate(self):
        for name,want in [('yesterday','2024-02-28'),('tomorrow','2041-01-01')]:
            r=t.evaluate(example(name));nodes={n['id']:n for n in r['nodes']}
            self.assertEqual(r['status'],'CHECKED')
            self.assertEqual(nodes['event']['candidates'][0]['dates']['first'],want)
            self.assertEqual({n['role'] for n in r['nodes']},{'S','R','E'})
            self.assertTrue(r['relations'][1]['native_call_indices'])
            self.assertFalse(r['arabic_time_interpretation_acquired'])

    def test_quotation_has_its_own_speech_time(self):
        q=example('quotation');r=t.evaluate(q)
        event=next(n for n in r['nodes'] if n['id']=='event')
        self.assertEqual(event['candidates'][0]['dates']['first'],'2000-02-29')
        q['temporal']['nodes'][-1]['anchors'][0]['interval']={'first':'2080-12-31','last':'2080-12-31'}
        other=t.evaluate(q)
        self.assertEqual(event,next(n for n in other['nodes'] if n['id']=='event'))
        q['temporal']['nodes'][0]['anchors']=[]
        unknown=t.evaluate(q)
        self.assertEqual(next(n for n in unknown['nodes'] if n['id']=='event')['candidates'],[])
        self.assertEqual(unknown['status'],'PARTIAL')

    def test_withdrawal_drops_only_dependent_derivations(self):
        q=example('withdrawn');r=t.evaluate(q)
        self.assertTrue(all(not n['candidates'] for n in r['nodes']))
        self.assertEqual(r['status'],'PARTIAL')
        q['temporal']['evidence'].append({'id':'independent','kind':'context','active':True,'value':{'day':'2024-02-29'}})
        q['temporal']['nodes'][0]['anchors'].append({'interval':{'first':'2024-02-29','last':'2024-02-29'},'evidence_ids':['independent']})
        r=t.evaluate(q);event=next(n for n in r['nodes'] if n['id']=='event')
        self.assertEqual(event['candidates'][0]['dates']['first'],'2024-02-28')
        self.assertNotIn('dated-speech',event['candidates'][0]['evidence_ids'])
        self.assertFalse(r['world_truth_established'])

    def test_alternatives_and_conflicts_are_not_resolved_by_first_hit(self):
        q=example();q['temporal']['relations'][-1]['relation']='after'
        self.assertEqual(t.evaluate(q)['status'],'CONFLICT')
        q=example();q['temporal']['nodes'][0]['anchors'].append({'interval':{'first':'2024-03-02','last':'2024-03-02'},'evidence_ids':['dated-speech']})
        r=t.evaluate(q)
        self.assertEqual(len(next(n for n in r['nodes'] if n['id']=='event')['candidates']),2)
        self.assertEqual(r['status'],'PARTIAL')
        self.assertIn('AMBIGUOUS',{x['status'] for x in r['relations']})

    def test_negative_conditional_command_and_quote_never_establish_occurrence(self):
        for force in ('assertion','conditional','quotation','question','command','possible'):
            q=example();q['temporal']['scopes'][0]['force']=force
            r=t.evaluate(q)
            self.assertEqual(r['scopes'][0]['force'],force)
            self.assertEqual(r['scopes'][0]['polarity'],'negative')
            self.assertFalse(r['world_truth_established'])
            self.assertFalse(r['empirical_causality_established'])
            self.assertTrue(all(not n['event_occurrence_established'] for n in r['nodes']))

    def test_unanchored_order_does_not_become_consistency_or_actuality_proof(self):
        q=example();q['temporal']['relations']=[q['temporal']['relations'][-1]]
        for n in q['temporal']['nodes']:n['anchors']=[]
        r=t.evaluate(q)
        self.assertEqual(r['relations'][0]['status'],'UNKNOWN')
        self.assertFalse(r['unanchored_constraint_network_complete'])

    def test_replay_detects_witness_scope_and_result_tampering(self):
        q=example();r=t.evaluate(q)
        self.assertTrue(t.verify(r,expected_request=q)['valid'])
        other=deepcopy(q);other['temporal']['evidence'][0]['active']=False
        self.assertFalse(t.verify(r,expected_request=other)['valid'])
        altered=deepcopy(r);altered['world_truth_established']=True
        self.assertFalse(t.verify(altered,expected_request=q)['valid'])
        other=deepcopy(q);other['temporal']['scopes'][0]['polarity']='positive'
        self.assertFalse(t.verify(r,expected_request=other)['valid'])

    def test_existing_teacher_routes_the_next_missing_obligation(self):
        for name,status,action in [('yesterday','CHECKED','ASSESS_CONTRAST_AND_WITHDRAWAL'),
                                   ('withdrawn','PARTIAL','ACQUIRE_TEMPORAL_ANCHOR_OR_DISAMBIGUATION')]:
            lesson=example(name+'_lesson');r=teaching.run_lesson(lesson)
            self.assertTrue(r['execution_measured'],r)
            self.assertEqual(r['status'],status)
            self.assertEqual(r['next_step']['action'],action)
            self.assertFalse(r['limits']['neural_training_performed'])
            self.assertTrue(teaching.verify_lesson(r,expected_lesson=lesson)['valid'])
