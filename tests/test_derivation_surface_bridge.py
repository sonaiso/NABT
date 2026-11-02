"""Exposed independent preimplementation acceptance for the delegated bridge.

Literal gold is frozen separately. These tests exercise transformations, source
identity, attacks and the existing recursive consumer, not a copied rewrite.
"""
from copy import deepcopy
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from nabt.errors import NabtError

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / 'evidence/derivation_surface_v1/independent/gold.json'


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def gold():
    return json.loads(GOLD.read_text())['cases']


def request(text='قَالَ', **changes):
    value = {'schema': 'nabt.derivation-surface-request.v1',
             'profile': 'medial-alif-unmarked.v1',
             'span': {'start': 0, 'end': len(text.encode('utf-8'))},
             'root': 'قول', 'pattern_id': 'past.I.a', 'ending': 'َ',
             'hypotheses': {'context': 'ordinary', 'origin': 'original'}}
    value.update(changes)
    return value


class DerivationSurfaceIndependentAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = import_module('tools.derivation_surface_bridge')

    def evaluate(self, text='قَالَ', req=None, **kwargs):
        return self.bridge.evaluate_derivation_surface(text, request() if req is None else req, **kwargs)

    def verify(self, report, text='قَالَ', req=None, **kwargs):
        return self.bridge.verify_derivation_surface(report, text=text,
            request=request() if req is None else req, **kwargs)

    def assert_error(self, call, *, status, code=None):
        with self.assertRaises(NabtError) as caught:
            call()
        self.assertEqual(caught.exception.status, status)
        if code:
            self.assertEqual(caught.exception.code, code)

    def test_literal_gold_positive_mismatch_blocker_and_scope(self):
        for case in gold():
            with self.subTest(case=case['id']):
                text, req, expected = case['text'], case['request'], case['expect']
                report = self.evaluate(text, req)
                self.assertEqual(report['status'], expected['status'])
                self.assertEqual(report['reason'], expected['reason'])
                self.assertEqual(report['missing_hypotheses'], expected['missing_hypotheses'])
                self.assertEqual(wire(report['original_request']), wire(req))
                self.assertEqual(report['schema'], 'nabt.derivation-surface-report.v1')
                self.assertEqual(report['authority'], 'SOURCE_BOUND_CONDITIONAL_SURFACE_APPLICATION')
                for flag in ('attested_root', 'application_established', 'grammar_certified', 'grants_language_license'):
                    self.assertIs(report[flag], False, flag)
                self.assertEqual(report['world_truth'], 'NOT_ESTABLISHED')
                self.assertTrue(report['unresolved'])
                if expected['generation_surface'] is None:
                    self.assertIsNone(report['generation'])
                    self.assertIsNone(report['input_cells'])
                else:
                    self.assertEqual(report['generation']['surface'], expected['generation_surface'])
                    self.assertIs(report['generation']['attested_root'], False)
                alternatives = report['surface_alternatives']
                if expected['realized_surface'] is None:
                    self.assertEqual(alternatives, [])
                else:
                    self.assertEqual(len(alternatives), 1)
                    self.assertEqual(alternatives[0]['action'], 'to_alif')
                    self.assertEqual(alternatives[0]['realized_surface'], expected['realized_surface'])
                    self.assertIs(alternatives[0]['exact_source_match'], expected['status'] == 'CONDITIONAL_MATCH')
                if expected['status'] == 'DEFER':
                    self.assertIsNone(report['classical_receipt'])
                else:
                    self.assertIs(report['classical_receipt']['result']['application_established'], False)
                replay = self.verify(report, text, req)
                self.assertTrue(replay['valid'])
                self.assertEqual(replay['authority'], 'DERIVATION_SURFACE_REPLAY_ONLY')

    def test_existing_owner_receipts_are_complete_and_unchanged(self):
        from nabt import derivation, classical_laws
        report = self.evaluate()
        self.assertEqual(wire(report['generation']), wire(derivation.generate_derivation('قول', 'past.I.a', ending='َ')))
        frame = {'cells': [['ق', 'a'], ['و', 'a'], ['ل', 'a']], 'index': 1,
                 'position': 'ayn', 'context': 'ordinary', 'origin': 'original', 'lexeme': ''}
        self.assertEqual(wire(report['classical_receipt']),
                         wire(classical_laws.evaluate('WEAK-MOVE-TO-ALIF', frame)))
        self.assertTrue(classical_laws.verify(report['classical_receipt'])['valid'])
        self.assertEqual(report['input_cells']['alphabet_id'], 'nabt.a116.v1')
        self.assertEqual(report['input_cells']['morphophonemic'], frame['cells'])
        # Literal A116 positions: qaf=20, waw=26, lam=22, fatha=0.
        self.assertEqual(report['input_cells']['ids'], [80, 104, 88])

    def test_omission_and_three_coordinate_domains(self):
        text = '  قَالَ، '
        req = request(span={'start': 2, 'end': 12})
        report = self.evaluate(text, req)
        alt = report['surface_alternatives'][0]
        self.assertEqual(alt['canonical_marked_surface'], 'قَاْلَ')
        self.assertEqual(alt['realized_surface'], 'قَالَ')
        self.assertEqual(alt['omitted_mark'], {'mark': 'ْ', 'cell_index': 1,
            'coordinate_domain': 'canonical_marked_surface', 'scalar_start': 3,
            'scalar_end': 4, 'byte_start': 6, 'byte_end': 8})
        self.assertEqual(alt['canonical_marked_surface'][:3] + alt['canonical_marked_surface'][4:], alt['realized_surface'])
        self.assertEqual(len(alt['cell_alignment']), 3)
        expected = [((0,2,0,4),(0,2,0,4)), ((2,4,4,8),(2,3,4,6)), ((4,6,8,12),(3,5,6,10))]
        keys = ('scalar_start','scalar_end','byte_start','byte_end')
        for i, row in enumerate(alt['cell_alignment']):
            self.assertEqual((row['cell_index'],row['root_index']), (i,i))
            self.assertEqual(tuple(row['generated'][k] for k in keys), expected[i][0])
            self.assertEqual(tuple(row['canonical'][k] for k in keys), expected[i][0])
            self.assertEqual(tuple(row['realized'][k] for k in keys), expected[i][1])
            ss = row['source_span']
            self.assertEqual((ss['start'], ss['end']), (2 + expected[i][1][2], 2 + expected[i][1][3]))
            part = text.encode()[ss['start']:ss['end']]
            self.assertEqual(ss['span_sha256'], sha256(part).hexdigest())
        mismatch = self.evaluate('قَالُ', request('قَالُ'))
        self.assertTrue(all(r['source_span'] is None for r in mismatch['surface_alternatives'][0]['cell_alignment']))

    def test_independent_request_source_and_occurrence_rebinding(self):
        report = self.evaluate(source_id='s', scope='a')
        replacements = [dict(text='قَامَ'), dict(req=request(pattern_id='past.I.u')),
                        dict(source_id='other'), dict(scope='other'),
                        dict(req=request(hypotheses={'context':'ordinary','origin':'transferred'}))]
        for change in replacements:
            options = dict(text='قَالَ', req=request(), source_id='s', scope='a'); options.update(change)
            with self.subTest(change=change):
                got = self.verify(report, **options)
                self.assertFalse(got['valid'])
                self.assertEqual(got['status'], 'REJECT')
        text = 'قَالَ قَالَ'
        first = request(span={'start':0,'end':10})
        second = request(span={'start':11,'end':21})
        report = self.evaluate(text, first)
        self.assertFalse(self.verify(report, text, second)['valid'])
        self.assertTrue(self.verify(self.evaluate(text, second), text, second)['valid'])

    def test_complete_receipt_tampering_and_typed_values_fail_replay(self):
        report = self.evaluate()
        attacks = []
        def attack(change):
            r = deepcopy(report); change(r); attacks.append(r)
        attack(lambda r: r.update(status='SURFACE_MISMATCH'))
        attack(lambda r: r.update(attested_root=True))
        attack(lambda r: r.update(application_established=0))
        attack(lambda r: r.update(unresolved=[]))
        attack(lambda r: r['generation'].update(surface='بَيَعَ'))
        attack(lambda r: r['input_cells']['ids'].__setitem__(1,0))
        attack(lambda r: r['original_request']['span'].update(start=False))
        attack(lambda r: r['classical_receipt']['result'].update(application_established=True))
        attack(lambda r: r['classical_receipt']['result']['alternatives'][0]['cells'][1].__setitem__(0,'ي'))
        attack(lambda r: r['surface_alternatives'][0].update(realized_surface='قَامَ'))
        attack(lambda r: r['surface_alternatives'][0]['omitted_mark'].update(byte_start=4))
        attack(lambda r: r['surface_alternatives'][0]['cell_alignment'][1].update(root_index=0))
        attack(lambda r: r['source'].update(raw_text='قَامَ'))
        attack(lambda r: r.update(injected_authority='APPROVED'))
        for i, changed in enumerate(attacks):
            with self.subTest(attack=i):
                got = self.verify(changed)
                self.assertFalse(got['valid'])
                self.assertEqual(got['code'],'DERIVATION_SURFACE_REPLAY_MISMATCH')

    def test_malformed_and_nonoccurrence_requests_reject(self):
        bad = []
        for change in ({'cells':[]}, {'schema':'wrong'}, {'root':True},
                       {'span':{'start':False,'end':10}}, {'span':{'start':1,'end':10}},
                       {'span':{'start':0,'end':8}}, {'span':{'start':0,'end':12}},
                       {'hypotheses':{'context':1,'origin':'original'}}):
            q=request();q.update(change);bad.append(q)
        q=request();del q['root'];bad.append(q)
        for q in bad:
            with self.subTest(request=q):
                self.assert_error(lambda:self.evaluate(req=q),status='REJECT')
        self.assert_error(lambda:self.evaluate('«قَالَ»',request(span={'start':2,'end':12})),status='REJECT')

    def test_source_owner_failure_cannot_be_bypassed(self):
        from nabt import derivation, classical_laws
        failure = NabtError('INSTALLED_CONTRACT_FAILED','injected unavailable pinned source',status='DEFER')
        for owner, method in ((derivation,'installed_registry'),(classical_laws,'replay_inventory')):
            with self.subTest(owner=owner.__name__), patch.object(owner,method,side_effect=failure):
                self.assert_error(lambda:self.evaluate(),status='DEFER',code='INSTALLED_CONTRACT_FAILED')
        report=self.evaluate()
        with patch.object(classical_laws,'replay_inventory',side_effect=failure):
            replay=self.verify(report)
            self.assertFalse(replay['valid']);self.assertEqual(replay['status'],'DEFER')
            self.assertEqual(replay['code'],'INSTALLED_CONTRACT_FAILED')

    def test_fixed_limits_are_distinct_from_scope_rejection(self):
        text=' '*(8192-10)+'قَالَ';q=request(span={'start':8192-10,'end':8192})
        self.assertEqual(self.evaluate(text,q)['status'],'CONDITIONAL_MATCH')
        self.assert_error(lambda:self.evaluate(text+' ',q),status='DEFER',code='RESOURCE_LIMIT')
        self.assert_error(lambda:self.evaluate(req=request(root='ك'*3000)),status='DEFER',code='RESOURCE_LIMIT')
        q=request(root='');q['root']='x'*(4096-len(wire(q)))
        self.assertEqual(len(wire(q)),4096)
        self.assertEqual(self.evaluate(req=q)['reason'],'OUTSIDE_PROFILE')
        self.assert_error(lambda:self.evaluate(req={**q,'root':q['root']+'x'}),status='DEFER',code='RESOURCE_LIMIT')
        for field in ('source_id','scope'):
            self.assertEqual(self.evaluate(**{field:'x'*96})['status'],'CONDITIONAL_MATCH')
            self.assert_error(lambda:self.evaluate(**{field:'x'*97}),status='DEFER',code='RESOURCE_LIMIT')
        report=self.evaluate();report['oversized']='x'*262144
        replay=self.verify(report)
        self.assertFalse(replay['valid']);self.assertEqual(replay['code'],'RESOURCE_LIMIT')

    def test_input_aliases_and_bytes_do_not_change_exact_evidence(self):
        req=request();report=self.evaluate(req=req)
        req['hypotheses']['context']='afal_quality'
        self.assertEqual(report['original_request']['hypotheses']['context'],'ordinary')
        self.assertEqual(wire(self.evaluate(b'\xd9\x82\xd9\x8e\xd8\xa7\xd9\x84\xd9\x8e')),wire(self.evaluate()))


class RecursiveApplicationIndependentAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.consumer=import_module('tools.recursive_bridge')
        for name in ('read_recursive_applications','verify_recursive_applications'):
            if not callable(getattr(cls.consumer,name,None)):
                raise AssertionError('preimplementation capability absent: '+name)

    def read(self,requests=None,text='قَالَ',**kwargs):
        return self.consumer.read_recursive_applications(text,[request()] if requests is None else requests,**kwargs)

    def verify(self,report,requests=None,text='قَالَ',**kwargs):
        return self.consumer.verify_recursive_applications(report,text=text,
            requests=[request()] if requests is None else requests,**kwargs)

    def test_actual_consumer_preserves_old_transport_and_all_applications(self):
        requests=[request(),request(pattern_id='past.I.u'),request()]
        report=self.read(requests)
        self.assertEqual(report['schema'],'nabt.recursive-source-transport.v2')
        self.assertEqual(report['report_version'],2)
        self.assertEqual(wire(report['transport']),wire(self.consumer.read_recursive_source('قَالَ')))
        self.assertEqual(report['source'],report['transport']['source'])
        self.assertEqual(report['original_requests'],requests)
        self.assertEqual(report['limits'],{'max_requests':16,'max_aggregate_bytes':16777216})
        for flag in ('grammar_certified','sense_equivalence_established','grants_language_license'):
            self.assertIs(report[flag],False)
        self.assertEqual(len(report['applications']),3)
        bridge=import_module('tools.derivation_surface_bridge')
        for i,row in enumerate(report['applications']):
            self.assertEqual(row['request_index'],i);self.assertEqual(row['request'],requests[i])
            self.assertEqual(wire(row['report']),wire(bridge.evaluate_derivation_surface('قَالَ',requests[i])))
            self.assertEqual(row['occurrence_binding']['byte_span'],row['report']['occurrence']['span'])
            self.assertEqual(row['occurrence_binding']['atom_span'],self.consumer._atom_span(report['source'],row['report']['occurrence']['span']))
        payload={k:v for k,v in report.items() if k!='report_id'}
        self.assertEqual(report['report_id'],sha256(wire(payload)).hexdigest())
        self.assertTrue(self.verify(report,requests)['valid'])

    def test_consumer_replays_requests_order_source_and_nested_receipts(self):
        requests=[request(),request(pattern_id='past.I.u')];report=self.read(requests)
        for expected in (list(reversed(requests)),[request(),request()],requests[:1]):
            self.assertFalse(self.verify(report,expected)['valid'])
        self.assertFalse(self.verify(report,requests,source_id='other')['valid'])
        self.assertFalse(self.verify(report,requests,scope='other')['valid'])
        self.assertFalse(self.verify(report,requests,text='قَامَ')['valid'])
        changed=deepcopy(report);changed['applications'][0]['report']['application_established']=True
        changed['report_id']=sha256(wire({k:v for k,v in changed.items() if k!='report_id'})).hexdigest()
        replay=self.verify(changed,requests)
        self.assertFalse(replay['valid']);self.assertEqual(replay['code'],'RECURSIVE_APPLICATION_REPLAY_MISMATCH')
        changed=deepcopy(report);changed['transport']['grammar_certified']=True
        self.assertFalse(self.verify(changed,requests)['valid'])
        changed=deepcopy(report);changed['applications'][0]['occurrence_binding']['atom_span']['start']=1
        self.assertFalse(self.verify(changed,requests)['valid'])

    def test_all_requests_and_occurrences_preflight_before_transform(self):
        from nabt import classical_laws
        for bad in (request(span={'start':1,'end':10}),{**request(),'cells':[]}):
            with self.subTest(bad=bad),patch.object(classical_laws,'replay_inventory',side_effect=AssertionError('owner called before preflight')):
                with self.assertRaises(NabtError) as caught:self.read([request(),bad])
                self.assertEqual(caught.exception.status,'REJECT')
        with patch.object(self.consumer,'read_recursive_source',side_effect=AssertionError('source owner called before count bound')):
            with self.assertRaises(NabtError) as caught:self.read([request()]*17,text='')
            self.assertEqual(caught.exception.code,'RESOURCE_LIMIT')
        self.assertEqual(len(self.read([request()]*16)['applications']),16)

    def test_mismatch_and_defer_still_bind_original_occurrences(self):
        requests=[request(),request(hypotheses={'context':None,'origin':'original'}),request(root='كتب')]
        report=self.read(requests,text='قَالُ')
        self.assertEqual([r['report']['status'] for r in report['applications']],['SURFACE_MISMATCH','DEFER','DEFER'])
        for row in report['applications']:
            self.assertEqual(row['occurrence_binding']['byte_span']['start'],0)
            self.assertEqual(row['occurrence_binding']['atom_span']['stop'],5)
        self.assertTrue(self.verify(report,requests,text='قَالُ')['valid'])

    def test_cli_existing_path_and_resource_order(self):
        with tempfile.TemporaryDirectory() as directory:
            directory=Path(directory);source=directory/'source.txt';applications=directory/'requests.json';saved=directory/'report.json'
            source.write_text('قَالَ');applications.write_text(json.dumps([request()],ensure_ascii=False))
            prefix=[sys.executable,'-m','tools.recursive_bridge']
            read=subprocess.run(prefix+['read-applications',str(source),'--applications',str(applications)],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(read.returncode,0,read.stderr+read.stdout)
            report=json.loads(read.stdout);saved.write_text(json.dumps(report,ensure_ascii=False))
            replay=subprocess.run(prefix+['verify-applications',str(source),'--applications',str(applications),'--report',str(saved)],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(replay.returncode,0,replay.stderr+replay.stdout)
            self.assertTrue(json.loads(replay.stdout)['valid'])
            rejected=subprocess.run(prefix+['read-applications',str(source),'--applications',str(applications),'--discourse'],cwd=ROOT,capture_output=True,text=True)
            self.assertNotEqual(rejected.returncode,0)
            applications.write_text(json.dumps([request()]*17,ensure_ascii=False))
            exceeded=subprocess.run(prefix+['read-applications',str(directory/'missing.txt'),'--applications',str(applications)],cwd=ROOT,capture_output=True,text=True)
            self.assertNotEqual(exceeded.returncode,0)
            self.assertEqual(json.loads(exceeded.stdout)['code'],'RESOURCE_LIMIT')


if __name__=='__main__':
    unittest.main()
