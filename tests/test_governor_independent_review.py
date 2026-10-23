"""Review the new evaluator with independent source/role/proof counterexamples."""
from __future__ import annotations

import copy
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import governor_evaluation as evaluation

DATA=ROOT/'evidence'/'governors'/'independent'
PACKAGE=ROOT/'src'/'nabt'


def span(raw,source_id,start,end):
    return {'source_id':source_id,'source_sha256':sha256(raw).hexdigest(),
            'start':start,'end':end,'span_sha256':sha256(raw[start:end]).hexdigest()}


def fixture(case_number=32):
    episodes,_,manual,annotations=evaluation.load_material(DATA)
    event=episodes[case_number]['events'][0]
    raw=event['text'].encode();sid='fixture';expected=event['gold']['governor_witness']
    parts=expected['roles']
    op=parts[0]
    source_policy={'policy_id':'nabt.arabic-governors.source-policy.v1',
                   'policy_sha256':evaluation.POLICY_SHA256,'source_id':'qatr',
                   'source_sha256':evaluation.QATR_SHA256,'authority':'CURATED_SOURCE_BOUND_POLICY',
                   'passages':[{'rule':rule,'source_id':'qatr','source_sha256':evaluation.QATR_SHA256,
                                **dict(zip(('start','end','span_sha256','line_start','line_end'),values))}
                               for rule,values in evaluation.POLICY_PASSAGES.items()]}
    roles=[]
    for index,part in enumerate(parts[1:]):
        evidence={'kind':'visible_tanwin','span':span(raw,sid,part['start'],part['end']),'policy_rule':'noun_marks'}
        roles.append({'role_code':index,'role':'inna_subject' if index==0 else 'inna_predicate',
                      'span':span(raw,sid,part['start'],part['end']),'surface':part['raw'],
                      'lexeme':event['gold']['facts'][1]['args'][0] if index==0 else event['gold']['facts'][1]['predicate'],'category':'noun','category_evidence':[evidence],
                      'observed_mark':index,'surface_mark':index,'surface_ending':'fixture_ending',
                      'role_mark_number':{'domain':'nabt.governors.role-mark.v1','value':5*index,
                                          'authority':'TYPED_ENCODING_ONLY'},'obligations':[]})
    prior=annotations[sha256(raw).hexdigest()]['statements'][0]['components'][0]
    gov={'law_id':'nabt.governors.v1','table_sha256':evaluation.TABLE_SHA256,'row_ids':[1],'class_code':2,
         'operator':{'span':span(raw,sid,op['start'],op['end']),'surface':op['raw'],'label':'إنّ'},
         'source_policy':source_policy,'roles':roles,
         'case_check':{'law_id':'nabt.governors.v1','class_code':2,'complete':[[[0,0],[1,1]]],
                       'viable':[[[0,0],[1,1]]],'deficits':[],'authority':'CASE_ASSIGNMENT_ONLY'},
         'syntactic_evidence_complete':True,
         'referent_identity':{'name':event['gold']['facts'][0]['args'][0],
                              'span':span(raw,sid,prior['start'],prior['end']),
                              'scope':'PREVIOUSLY_READ_IN_THIS_SOURCE'},
         'semantic_projection':'SOURCE_RELATIVE_ASSERTION','world_truth':'NOT_ESTABLISHED'}
    return {'steps':[{'governor':gov}]},expected,raw,sid,annotations


def validate(report,expected,raw,sid,annotations):
    return evaluation.check_governor_cue_report(report,expected,raw,sid,annotations,PACKAGE,
                                               require_reference=True)


class IndependentGovernorReviewTests(unittest.TestCase):
    @staticmethod
    def synthetic_material():
        text='فرد زيد.'
        goal={'predicate':'حاضر','args':['زيد'],'positive':True}
        case={'id':'independent_failure_probe','group':'declared_scope','events':[
            {'op':'add','source_id':'probe','text':text,
             'gold':{'facts':[],'rules':[],'accepted_required':True}},
            {'op':'query','query_id':'query_probe','text':'هل زيد هو حاضر؟',
             'gold':{'goal':goal,'status':'OUT_OF_SCOPE'}},
        ]}
        checksum=sha256(text.encode()).hexdigest()
        return [case],[],{checksum:{'facts':[],'rules':[]}},{checksum:{'facts':[],'rules':[],'statements':[]}}

    def test_pinned_cases_and_original_intervals(self):
        episodes,excerpts,manual,annotations=evaluation.load_material(DATA)
        self.assertEqual((len(episodes),len(excerpts),len(manual),len(annotations)),(38,6,22,22))
        self.assertTrue(all('فرد ' not in e.get('text','') for case in episodes for e in case['events']))
        for excerpt in excerpts:
            self.assertTrue(evaluation.check_original_excerpt(excerpt,PACKAGE))

    def test_interface_errata_precede_opening_and_do_not_rewrite_gold(self):
        episodes,_,_,_=evaluation.load_material(DATA)
        replacement=next(c for c in episodes if c['id']=='g09')['events'][2]
        self.assertEqual(replacement['op'],'replace')
        original=json.loads((DATA/'episodes.json').read_text())['episodes']
        self.assertEqual(next(c for c in original if c['id']=='g09')['events'][2]['op'],'add')
        errata=json.loads((DATA/'preopen_errata.json').read_text())
        self.assertFalse(errata['implementation_opened'])
        self.assertFalse(errata['runtime_results_seen'])

    def test_changed_gold_cannot_authorize_itself_with_an_updated_local_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'material';shutil.copytree(DATA,target)
            cases=json.loads((target/'episodes.json').read_text());cases['episodes'][0]['events'][0]['gold']['facts']=[]
            (target/'episodes.json').write_text(json.dumps(cases))
            with self.assertRaises(evaluation.oracle.ReplayValidationError):evaluation.load_material(target)
            freeze=json.loads((target/'material_freeze.json').read_text())
            for item in freeze['files']:
                if item['path']=='episodes.json':
                    raw=(target/'episodes.json').read_bytes();item.update(bytes=len(raw),sha256=sha256(raw).hexdigest())
            (target/'material_freeze.json').write_text(json.dumps(freeze))
            with self.assertRaises(evaluation.oracle.ReplayValidationError):evaluation.load_material(target)

    def test_valid_independently_authored_governor_witness(self):
        args=fixture()
        self.assertTrue(validate(*args)['case_equation'])

    def test_case_solution_and_integer_encoding_cannot_substitute_for_nominality(self):
        for mutate in (
            lambda g:g['roles'][0].__setitem__('category_evidence',[]),
            lambda g:g['roles'][0].__setitem__('category',None),
            lambda g:g['roles'][0].__setitem__('observed_mark',False),
            lambda g:g['roles'][1]['role_mark_number'].__setitem__('value',1),
            lambda g:g['case_check'].__setitem__('complete',[[[0,1],[1,0]]]),
        ):
            args=list(fixture());mutate(args[0]['steps'][0]['governor'])
            with self.assertRaises(evaluation.oracle.ReplayValidationError):validate(*args)

    def test_role_swap_and_tanwin_from_another_word_fail(self):
        for mode in ('swap','foreign_tanwin'):
            args=list(fixture());g=args[0]['steps'][0]['governor']
            if mode=='swap':g['roles'][0]['span'],g['roles'][1]['span']=g['roles'][1]['span'],g['roles'][0]['span']
            else:g['roles'][0]['category_evidence'][0]['span']=g['roles'][1]['span']
            with self.assertRaises(evaluation.oracle.ReplayValidationError):validate(*args)

    def test_source_policy_cannot_be_removed_truncated_or_rebound(self):
        for mode in ('missing','truncated','wrong_rule','wrong_source','wrong_pin'):
            args=list(fixture());p=args[0]['steps'][0]['governor']['source_policy']
            if mode=='missing':p['passages'].pop()
            elif mode=='truncated':
                p['passages'][1]['end']-=2
                original=(PACKAGE/'data/source_evidence/qatr.txt').read_bytes()
                w=p['passages'][1];w['span_sha256']=sha256(original[w['start']:w['end']]).hexdigest()
            elif mode=='wrong_rule':p['passages'][1]['rule']='noun_marks'
            elif mode=='wrong_source':p['passages'][1]['source_id']='alfiyya'
            else:p['policy_sha256']='1'*64
            with self.subTest(mode=mode),self.assertRaises(evaluation.oracle.ReplayValidationError):validate(*args)

    def test_referent_identity_must_be_a_previously_read_subject(self):
        for mode in ('self','predicate','name','missing'):
            args=list(fixture());g=args[0]['steps'][0]['governor'];raw=args[2];sid=args[3]
            if mode=='self':g['referent_identity']['span']=g['roles'][0]['span']
            elif mode=='predicate':
                c=args[4][sha256(raw).hexdigest()]['statements'][0]['components'][2]
                g['referent_identity']['span']=span(raw,sid,c['start'],c['end'])
            elif mode=='name':g['referent_identity']['name']='another_name'
            else:g['referent_identity']=None
            with self.subTest(mode=mode),self.assertRaises(evaluation.oracle.ReplayValidationError):validate(*args)

    def test_a_malformed_returned_certificate_is_an_error_not_safe_defer(self):
        episodes,_,manual,annotations=evaluation.load_material(DATA)
        event=episodes[0]['events'][0];active={'source':event['text']}
        target=episodes[0]['events'][1]['gold']['goal'];scope='contract_check'
        answer={'status':'SUPPORTED','reason':'CLEAN_DERIVATION','scope':scope,'query':target,
                'positive_support':True,'negative_support':False,'proofs':{'query':[]},
                'missing_premises':[],'missing_complete':True,'contested_premises':[],
                'missing_policy':'bounded_grounded_backward_plans_active_and_query_constants.v1',
                'world_truth':'NOT_ESTABLISHED','interpretation_status':'READ',
                'semantic_version':'nabt.signed-horn.v1',
                'program_sha256':evaluation.oracle.program_identity(active,scope,evaluation.PROFILE),
                'atom_number':0,'stats':{}}
        with self.assertRaises(evaluation.oracle.ReplayValidationError):
            evaluation.check_answer(answer,active,scope,manual,annotations,target,evaluation.PROFILE)

    def test_numeric_failure_cannot_leave_an_episode_complete(self):
        material=self.synthetic_material()
        with patch.object(evaluation,'load_material',return_value=material):
            reference=evaluation.run(DATA)
        self.assertTrue(reference['episodes'][0]['complete_episode'])
        with patch.object(evaluation,'load_material',return_value=material), \
                patch.object(evaluation,'run_program_case',side_effect=RuntimeError('execution probe')):
            failed=evaluation.run(DATA)['episodes'][0]
        self.assertFalse(failed['complete_episode'])
        self.assertFalse(failed['numeric_program']['numeric_roundtrip'])

    def test_source_restoration_failure_cannot_leave_an_episode_complete(self):
        with patch.object(evaluation,'load_material',return_value=self.synthetic_material()), \
                patch.object(evaluation.oracle,'restore_segments',return_value=False):
            failed=evaluation.run(DATA)['episodes'][0]
        self.assertFalse(failed['complete_episode'])
        self.assertFalse(failed['source_restoration'])
        self.assertFalse(failed['events'][0]['source_restored'])

    def test_required_source_denominator_survives_a_reading_error(self):
        with patch.object(evaluation,'load_material',return_value=self.synthetic_material()), \
                patch('nabt.governor_reader.read_arabic',side_effect=RuntimeError('reading probe')):
            failed=evaluation.run(DATA)['episodes'][0]
        self.assertEqual(failed['required_sources'],1)
        self.assertEqual(failed['complete_source_readings'],0)
        self.assertFalse(failed['complete_episode'])

    def test_checker_runtime_error_is_not_a_killed_mutation(self):
        minimal={'proofs':{'query':{'steps':[{}]}}}
        with patch.object(evaluation,'check_answer',side_effect=RuntimeError('checker bug')):
            with self.assertRaises(evaluation.EvaluatorError):
                evaluation.mutation_checks(minimal,{},'scope',{}, {},{},evaluation.PROFILE)

    def test_cli_returns_nonzero_for_an_evaluator_error(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(evaluation,'run',side_effect=evaluation.EvaluatorError('checker bug')), \
                redirect_stderr(io.StringIO()),redirect_stdout(io.StringIO()):
            output=Path(directory)/'new'
            code=evaluation.main(['--profile','baseline','--output-dir',str(output)])
            failure=json.loads((output/'failure.json').read_text())
        self.assertEqual(code,1)
        self.assertEqual(failure['error']['type'],'EvaluatorError')
        self.assertFalse(failure['coverage_goal_met'])

    def test_a_same_name_package_elsewhere_is_not_the_frozen_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            wrong=Path(directory)/'nabt';wrong.mkdir()
            filename=wrong/'__init__.py';filename.write_text('')
            module=SimpleNamespace(__file__=str(filename),__spec__=SimpleNamespace(origin=str(filename)))
            with self.assertRaises(evaluation.oracle.ReplayValidationError):
                evaluation.verify_loaded_package(ROOT,{'nabt':module})

    def test_sound_negative_answer_can_coexist_with_incomplete_intended_conflict(self):
        episodes,excerpts,manual,annotations=evaluation.load_material(DATA)
        selected=[case for case in episodes if case['id']=='g10']
        with patch.object(evaluation,'load_material',return_value=(selected,[],manual,annotations)):
            episode=evaluation.run(DATA)['episodes'][0]
        self.assertTrue(episode['admitted_claims_licensed'])
        self.assertTrue(episode['independent_certificates_pass'])
        self.assertFalse(episode['complete_episode'])
        self.assertEqual(episode['complete_source_readings'],1)
        self.assertTrue(any(e.get('answer',{}).get('status')=='REFUTED'
                            and e.get('query_status_matches') is False for e in episode['events']))

    def test_published_regression_gate_cannot_turn_abstention_into_coverage(self):
        result=json.loads((ROOT/'evidence/governors/evaluator_correction_run/results.json').read_text())
        gate=evaluation.regression_gate(result)
        self.assertEqual(gate['original_scope'],{'complete':0,'total':12,'baseline_complete':11})
        self.assertEqual(gate['constrained_scope'],{'complete':4,'total':5})
        self.assertEqual(gate['original_excerpts'],{'semantic_read':0,'total':6})
        self.assertFalse(gate['coverage_goal_met'])
        all_defer=copy.deepcopy(result)
        for episode in all_defer['episodes']:episode['complete_episode']=False
        with self.assertRaises(evaluation.oracle.ReplayValidationError):evaluation.regression_gate(all_defer)

    def test_regression_gate_rejects_bad_proof_origin_or_numeric_receipt(self):
        result=json.loads((ROOT/'evidence/governors/evaluator_correction_run/results.json').read_text())
        for mutate in (
            lambda r:r['episodes'][0].__setitem__('admitted_claims_licensed',False),
            lambda r:r['episodes'][0].__setitem__('source_restoration',False),
            lambda r:r['episodes'][0]['numeric_program'].__setitem__('numeric_roundtrip',False),
            lambda r:r['episodes'][0]['numeric_program']['production_receipt_replay'].__setitem__('valid',False),
            lambda r:next(e for e in r['episodes'] if e['mutations'])['mutations'][0]['error'].__setitem__('type','RuntimeError'),
        ):
            changed=copy.deepcopy(result);mutate(changed)
            with self.assertRaises(evaluation.oracle.ReplayValidationError):evaluation.regression_gate(changed)


if __name__=='__main__':unittest.main()
