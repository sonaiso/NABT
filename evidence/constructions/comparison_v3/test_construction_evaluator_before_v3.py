"""Independent adapter obligations, without running the frozen construction cases."""
from copy import deepcopy
from hashlib import sha256
import gzip
import importlib.util
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

PATH=Path(__file__).resolve().parents[1]/'tools/construction_evaluation.py'
spec=importlib.util.spec_from_file_location('construction_review_evaluator',PATH)
evaluation=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=evaluation
spec.loader.exec_module(evaluation)

def example():
    text = 'حازم حكيم'
    source_id = 'test_source'
    inputs = {'text': text, 'source_id': source_id, 'scope': 'test',
              'context': {'entities': [{'id': 'h', 'name': 'حازم'}], 'closed_reference_scope': True}}
    checksum = sha256(text.encode()).hexdigest()
    def span(a, b):
        return {'source_id': source_id, 'source_sha256': checksum, 'start': a, 'end': b}
    first, gap, second, whole = span(0, 8), span(8, 9), span(9, 17), span(0, 17)
    context = {'entities': [{'id': 'h', 'name': 'حازم', 'gender': 'unknown', 'number': 'unknown', 'kind': 'unknown'}],
               'deixis': [], 'closed_reference_scope': True}
    context_sha = evaluation.digest(context)
    reference = {'origin': 'named', 'surface': 'حازم', 'span': first, 'scope': 'test',
                 'context_sha256': context_sha, 'candidate_entity_ids': ['h'], 'bound_entity_id': 'h'}
    reference['reference_id'] = evaluation.digest(reference)
    rows = []
    for rid, surface, location, pos in [('subject', 'حازم', first, 'PN'), ('predicate', 'حكيم', second, 'N')]:
        rows.append({'reading_id': rid, 'kind': 'noun', 'construction': None, 'class_candidates': [],
                     'stem_span': location, 'stem_surface': surface, 'nun_readings': [],
                     'lexical_features': {'lemma': surface, 'pos': pos},
                     'segmentation': {'parts': [{'span': location, 'surface': surface}]}})
    assignments = []
    for rid, surface, location, role, head in [('subject', 'حازم', first, 'nominal_subject', None),
                                              ('predicate', 'حكيم', second, 'nominal_predicate', first)]:
        assignments.append({'reading_id': rid, 'span': location, 'surface': surface, 'role': role,
            'required_case': 'raf', 'head_span': head, 'activated': True, 'actual_role': role,
            'inflected_case': None, 'local_case': None, 'case_domain': None, 'sign_candidates': []})
    claim = {'predicate': 'حكيم', 'predicate_kind': 'property', 'voice': None, 'args': ['h'],
             'positive': True, 'tense': 'unspecified', 'time': [], 'place': [], 'restriction': []}
    analysis = {'span': whole, 'reading_ids': ['subject', 'predicate'], 'references': [reference],
                'assignments': assignments, 'relations': [], 'force': 'ASSERT', 'licensed_syntax': True,
                'references_complete': True, 'rejected_candidate': False, 'assertion_allowed': True,
                'claims': [deepcopy(claim)]}
    analysis['analysis_id'] = evaluation.digest(analysis)
    clause = {'span': whole, 'status': 'LICENSED', 'force': 'ASSERT', 'analyses': [analysis]}
    clause['clause_id'] = evaluation.digest(clause)
    claim['claim_id'] = 'claim'
    claim['proofs'] = [{'analysis_id': analysis['analysis_id'], 'clause_id': clause['clause_id'], 'span': whole}]
    report = {'source_text': text, 'source_id': source_id, 'scope': 'test', 'source_sha256': checksum,
              'world_truth': 'NOT_ESTABLISHED', 'context': {'value': context, 'sha256': context_sha},
              'partition': [{'kind': 'written_run', 'surface': 'حازم', 'span': first},
                            {'kind': 'spacing', 'surface': ' ', 'span': gap},
                            {'kind': 'written_run', 'surface': 'حكيم', 'span': second}],
              'occurrences': [{'surface': row['stem_surface'], 'span': row['stem_span'], 'readings': [row]} for row in rows],
              'derived_readings': [], 'clauses': [clause], 'claims': [claim], 'status': 'LICENSED_DISCOURSE'}
    report['report_id'] = evaluation.digest(report)
    return inputs, report

def rehash(report):
    for clause in report['clauses']:
        for analysis in clause['analyses']:
            analysis['analysis_id'] = evaluation.digest({k: v for k, v in analysis.items() if k != 'analysis_id'})
        clause['clause_id'] = evaluation.digest({k: v for k, v in clause.items() if k != 'clause_id'})
    for claim in report['claims']:
        for proof in claim['proofs']:
            proof['analysis_id'] = report['clauses'][0]['analyses'][0]['analysis_id']
            proof['clause_id'] = report['clauses'][0]['clause_id']
    report['report_id'] = evaluation.digest({k: v for k, v in report.items() if k != 'report_id'})

def update_context(inputs, report):
    value = {'entities': [{'gender': 'unknown', 'number': 'unknown', 'kind': 'unknown', **e}
                          for e in inputs['context']['entities']],
             'deixis': inputs['context'].get('deixis', []),
             'closed_reference_scope': inputs['context'].get('closed_reference_scope', False)}
    for name in ('speaker', 'addressee'):
        if name in inputs['context']:
            value[name] = inputs['context'][name]
    report['context'] = {'value': value, 'sha256': evaluation.digest(value)}
    for clause in report['clauses']:
        for analysis in clause['analyses']:
            for reference in analysis['references']:
                reference['context_sha256'] = report['context']['sha256']
                reference['reference_id'] = evaluation.digest({k: v for k, v in reference.items() if k != 'reference_id'})
    rehash(report)

def answer_example(variable=False):
    inputs, document = example()
    inputs['context']['entities'][0]['kind'] = 'person'
    update_context(inputs, document)
    inquiry = deepcopy(document)
    inquiry['claims'] = []
    analysis = inquiry['clauses'][0]['analyses'][0]
    analysis['force'], analysis['assertion_allowed'] = 'QUESTION', False
    analysis['question_kind'] = 'person' if variable else 'polar'
    inquiry['clauses'][0]['force'] = 'QUESTION'
    if variable:
        analysis['claims'][0]['args'] = ['?person']
    rehash(inquiry)
    bindings = {'?person': 'h'} if variable else {}
    proof = {'claim_id': document['claims'][0]['claim_id'], 'document_report_id': document['report_id'],
             'question_report_id': inquiry['report_id'], 'bindings': bindings,
             'source_proofs': deepcopy(document['claims'][0]['proofs'])}
    answer = {'source_text': inputs['text'], 'question_text': inputs['text'], 'scope': inputs['scope'],
              'source_id': inputs['source_id'], 'source_sha256': document['source_sha256'],
              'question_sha256': inquiry['source_sha256'], 'document_report_id': document['report_id'],
              'question_report_id': inquiry['report_id'], 'context_sha256': document['context']['sha256'],
              'world_truth': 'NOT_ESTABLISHED', 'kind': 'person' if variable else 'polar', 'status': 'SUPPORTED',
              'query': deepcopy(analysis['claims'][0]), 'proofs': [proof], 'counterproofs': [],
              'bindings': [{'values': bindings, 'status': 'SUPPORTED', 'proofs': [deepcopy(proof)],
                            'counterproofs': []}] if variable else []}
    answer['answer_id'] = evaluation.digest(answer)
    return inputs, document, inquiry, answer


def scoped_example():
    child={'predicate':'حَكِيم','predicate_kind':'property','voice':None,'args':['x'],
           'positive':True,'tense':'relative_to_operator','time':[],'place':[],'restriction':[]}
    claim={'predicate':'@operator:ظن','predicate_kind':'scoped','voice':None,'args':['h'],
           'positive':True,'tense':'past','time':[],'place':[],
           'restriction':[{'kind':'operator_scope','family':'zanna','lemma':'ظن','sense':'epistemic',
             'aspect':'PERF','embedded':[child],'embedded_fact_projection':False}]}
    expected={'family':'epistemic','operator_lemma':'ظَنَّ','operator_aspect':'perfect','matrix_args':['h'],
              'positive':True,'embedded':{**deepcopy(child),'tense':'unspecified'}}
    return expected,claim

def partial_gate_example():
    _,material,_=evaluation.load_material()
    cases=[{'id':c['id'],'passed':True,'checks':[{'check':'report_replay','passed':True}],
            'failures':[],'false_accepts':[]} for c in material['cases']]
    result={'cases':cases,'total':86,'passed':86,'strict_pass':True,'measurement_valid':True,
            'false_accept_count':0,'execution_errors':[],'question_execution_errors':[],'finalization_errors':[],
            'gold_freeze_sha256':evaluation.GOLD_FREEZE_SHA256,
            'snapshot':{'runtime_freeze_sha256':evaluation.BOUNDARY_RUNTIME_SHA256},
            'raw_log':{'case_ids':[c['id'] for c in cases],'complete_gzip_verified':True,
                       'canonical_json_verified':True,'write_time_inventory_verified':True}}
    add_gate_failure(result,'CON-Z02','complete_construction')
    return result

def add_gate_failure(result,case_id,check,details=None):
    case=next(c for c in result['cases'] if c['id']==case_id)
    row={'check':check,'passed':False}
    if details is not None:row['details']=details
    case['checks'].append(row);case['failures'].append(row);case['passed']=False
    result['passed']=sum(c['passed'] for c in result['cases']);result['strict_pass']=False


class ConstructionEvaluatorTests(unittest.TestCase):
    def test_partial_gate_requires_opt_in_and_preserves_strict_failure(self):
        result=partial_gate_example()
        self.assertFalse(evaluation.gate_decision(result)['gate_pass'])
        gate=evaluation.gate_decision(result,True)
        self.assertTrue(gate['gate_pass']);self.assertFalse(result['strict_pass'])
        self.assertEqual(gate['documented_boundary_failures'],[{'id':'CON-Z02','check':'complete_construction'}])

    def test_partial_gate_is_bound_to_v2_and_exact_failure_signatures(self):
        result=partial_gate_example();result['snapshot']['runtime_freeze_sha256']='earlier_or_future_runtime'
        self.assertFalse(evaluation.gate_decision(result,True)['gate_pass'])
        result=partial_gate_example();add_gate_failure(result,'CON-Z02','role:99')
        self.assertFalse(evaluation.gate_decision(result,True)['gate_pass'])

    def test_partial_gate_never_waives_kana_repair_or_replay(self):
        for case_id,check in [('CON-K06','claim:0'),('CON-R01','replay_changed_answer'),('CON-Z02','report_replay')]:
            result=partial_gate_example();add_gate_failure(result,case_id,check)
            self.assertFalse(evaluation.gate_decision(result,True)['gate_pass'],(case_id,check))

    def test_allowed_question_coverage_failure_cannot_hide_bad_certificate(self):
        result=partial_gate_example();add_gate_failure(result,'CON-Z02','question:0',{'certificate':True})
        self.assertTrue(evaluation.gate_decision(result,True)['gate_pass'])
        result['cases'][next(i for i,c in enumerate(result['cases']) if c['id']=='CON-Z02')]['checks'][-1]['details']['certificate']=False
        self.assertFalse(evaluation.gate_decision(result,True)['gate_pass'])

    def test_partial_gate_never_waives_false_accepts_errors_or_incomplete_raw(self):
        for mutation in ('false_accept','execution','raw','missing_case'):
            result=partial_gate_example()
            if mutation=='false_accept':result['false_accept_count']=1
            elif mutation=='execution':result['execution_errors'].append({'type':'SyntheticFailure'})
            elif mutation=='raw':result['raw_log']['complete_gzip_verified']=False
            else:result['cases'].pop()
            self.assertFalse(evaluation.gate_decision(result,True)['gate_pass'],mutation)

    def test_raw_finalization_requires_complete_gzip_scores_and_question_inventory(self):
        material={'cases':[{'id':'UNIT-RAW','expected':{'questions':[{}]}}]}
        score={'id':'UNIT-RAW','failures':[],'passed':True,'seconds':0.01}
        result={'model_summary':{'words':1},'source_sha256':'source','cases':[score],
                'execution_errors':[],'question_execution_errors':[]}
        records=[{'model_summary':result['model_summary'],'source_sha256':'source'},
                 {'id':'UNIT-RAW','report':{},'verification':{},'replay':None,'score':score,
                  'questions':[{'answer':{},'inquiry':{},'verification':{}}]}]
        def payload(values):
            return gzip.compress(b''.join(evaluation.wire(value)+b'\n' for value in values))
        with TemporaryDirectory() as folder:
            path=Path(folder)/'raw.jsonl.gz';original=payload(records);path.write_bytes(original)
            checked=evaluation.finalize_raw_log(path,material,result)
            self.assertEqual((checked['record_count'],checked['case_count'],checked['question_count']),(2,1,1))
            self.assertTrue(checked['complete_gzip_verified'])
            evaluation.finalize_raw_log(path,material,result,checked['record_inventory'])
            path.write_bytes(original[:-8])
            with self.assertRaises((EOFError,ValueError,OSError)):
                evaluation.finalize_raw_log(path,material,result)
            for mutation in ('missing_case','missing_question','changed_score'):
                changed=deepcopy(records)
                if mutation=='missing_case':changed.pop()
                elif mutation=='missing_question':changed[1]['questions']=[]
                else:changed[1]['score']['passed']=False
                path.write_bytes(payload(changed))
                with self.assertRaises(ValueError,msg=mutation):
                    evaluation.finalize_raw_log(path,material,result)

    def test_frozen_material_inventory_and_declared_predicates(self):
        freeze,material,source=evaluation.load_material()
        self.assertEqual((freeze['case_count'],len(material['cases'])),(86,86))
        self.assertEqual((freeze['comprehension_case_count'],freeze['replay_case_count']),(80,6))
        self.assertEqual(freeze['comprehension_question_count'],100)
        self.assertNotIn(b'|NOM',source)
        self.assertNotIn(b'|ACC',source)
        self.assertNotIn(b'MOOD:',source)

    def test_valid_source_correlated_report(self):
        inputs,report=example()
        evaluation.validate_report(report,inputs)

    def test_positive_integer_cannot_replace_boolean(self):
        _,claim=scoped_example();claim['positive']=1
        with self.assertRaises(ValueError):evaluation.claim_view(claim)

    def test_relative_tense_cannot_escape_to_top_level(self):
        _,report=example();claim=report['claims'][0];claim['tense']='relative_to_operator'
        with self.assertRaisesRegex(ValueError,'escaped'):evaluation.claim_view(claim)

    def test_operator_scope_preserves_all_proposition_fields(self):
        expected,claim=scoped_example()
        self.assertTrue(evaluation.scope_matches(expected,claim))
        for target,value in [('args',['wrong']),('positive',False),('predicate','آخر'),('voice','passive'),('place',['p'])]:
            bad=deepcopy(claim);bad['restriction'][0]['embedded'][0][target]=value
            self.assertFalse(evaluation.scope_matches(expected,bad),target)
        for target,value in [('lemma','علم'),('sense','hope'),('aspect','IMPF')]:
            bad=deepcopy(claim);bad['restriction'][0][target]=value
            self.assertFalse(evaluation.scope_matches(expected,bad),target)

    def test_outer_matrix_tense_is_compared_even_with_relative_child(self):
        expected,claim=scoped_example();claim['tense']='nonpast'
        self.assertFalse(evaluation.scope_matches(expected,claim))

    def test_closed_scope_labels_have_explicit_semantic_correspondences(self):
        expected,claim=scoped_example();claim['restriction'][0]['sense']='belief'
        self.assertTrue(evaluation.scope_matches(expected,claim))
        claim['restriction'][0]['sense']='proximity'
        self.assertFalse(evaluation.scope_matches(expected,claim))

    def test_explicit_shadda_requires_declared_mark_in_published_name_profile(self):
        self.assertFalse(evaluation.context_form_compatible('مُدَرِّسٌ','مدرس'))
        self.assertTrue(evaluation.context_form_compatible('مدرس','مُدَرِّس'))
        self.assertTrue(evaluation.context_form_compatible('مُدَرِّسٍ','مُدَرِّس'))

    def test_unresolved_candidate_argument_is_retained_but_never_grounded(self):
        inputs,report=example();inputs['context']['entities'][0]['name']='خالد'
        update_context(inputs,report);analysis=report['clauses'][0]['analyses'][0]
        ref=analysis['references'][0];ref['candidate_entity_ids']=[];ref['bound_entity_id']=None
        ref['reference_id']=evaluation.digest({k:v for k,v in ref.items() if k!='reference_id'})
        analysis['references_complete']=False;analysis['assertion_allowed']=False;analysis['claims'][0]['args']=[None]
        report['claims']=[];report['clauses'][0]['status']='DEFER';report['status']='DEFER'
        rehash(report);evaluation.validate_report(report,inputs)
        report['clauses'][0]['status']='LICENSED';rehash(report)
        with self.assertRaisesRegex(ValueError,'incomplete viable'):evaluation.validate_report(report,inputs)

    def test_scoped_fact_cannot_equal_bare_embedded_fact(self):
        expected,claim=scoped_example()
        self.assertNotEqual(evaluation.semantic_key(expected['embedded']),evaluation.semantic_key(claim))
        claim['restriction'][0]['embedded_fact_projection']=True
        with self.assertRaisesRegex(ValueError,'projects'):evaluation.claim_view(claim)

    def test_qualified_time_does_not_erase_article_distinction(self):
        exact={'lemma':'يَوْم','form':'اليوم','source_article':True}
        other={'lemma':'يَوْم','form':'يوم','source_article':False}
        self.assertEqual(evaluation.gold_time(exact),'اليوم')
        self.assertNotEqual(evaluation.gold_time(other),'اليوم')

    def test_same_analysis_inherited_case(self):
        inputs,report=example();analysis=report['clauses'][0]['analyses'][0]
        dep={'role':'naat','head_span':analysis['assignments'][0]['span'],'required_case':'raf'}
        self.assertEqual(evaluation.assignment_case(dep,analysis),'raf')
        dep['head_span']=None
        with self.assertRaisesRegex(ValueError,'same-analysis'):evaluation.assignment_case(dep,analysis)

    def test_subject_predicate_argument_identity_is_not_context_membership(self):
        inputs,report=example();inputs['context']['entities'].append({'id':'other','name':'آخر'})
        update_context(inputs,report)
        for claim in [report['claims'][0],report['clauses'][0]['analyses'][0]['claims'][0]]:claim['args']=['other']
        rehash(report)
        with self.assertRaisesRegex(ValueError,'bound subject'):evaluation.validate_report(report,inputs)

    def test_predicate_cannot_borrow_subject_lemma(self):
        inputs,report=example()
        for claim in [report['claims'][0],report['clauses'][0]['analyses'][0]['claims'][0]]:claim['predicate']='حازم'
        rehash(report)
        with self.assertRaisesRegex(ValueError,'predicate-role'):evaluation.validate_report(report,inputs)

    def test_incomplete_source_partition_is_rejected_after_rehash(self):
        inputs,report=example();report['partition'].pop(1);rehash(report)
        with self.assertRaisesRegex(ValueError,'gap/overlap'):evaluation.validate_report(report,inputs)

    def test_named_reference_cannot_rebind_to_different_written_name(self):
        inputs,report=example();inputs['context']['entities'].append({'id':'other','name':'آخر'})
        update_context(inputs,report);ref=report['clauses'][0]['analyses'][0]['references'][0]
        ref['candidate_entity_ids']=['other'];ref['bound_entity_id']='other'
        ref['reference_id']=evaluation.digest({k:v for k,v in ref.items() if k!='reference_id'})
        for claim in [report['claims'][0],report['clauses'][0]['analyses'][0]['claims'][0]]:claim['args']=['other']
        rehash(report)
        with self.assertRaisesRegex(ValueError,'original context'):evaluation.validate_report(report,inputs)

    def test_answer_cannot_drop_question_restriction(self):
        inputs,doc,inquiry,answer=answer_example()
        inquiry['clauses'][0]['analyses'][0]['claims'][0]['restriction']=[{'kind':'test','owner':'h'}]
        rehash(inquiry);answer['question_report_id']=inquiry['report_id']
        answer['proofs'][0]['question_report_id']=inquiry['report_id']
        answer['answer_id']=evaluation.digest({k:v for k,v in answer.items() if k!='answer_id'})
        with self.assertRaisesRegex(ValueError,'original question'):evaluation.validate_answer(answer,doc,inquiry,inputs,inputs['text'])

    def test_answer_kind_and_binding_domains_remain_checked(self):
        inputs,doc,inquiry,answer=answer_example()
        answer['kind']='person';answer['answer_id']=evaluation.digest({k:v for k,v in answer.items() if k!='answer_id'})
        with self.assertRaisesRegex(ValueError,'kind differs'):evaluation.validate_answer(answer,doc,inquiry,inputs,inputs['text'])

    def test_partial_document_or_question_cannot_ground_an_answer_after_rehash(self):
        for target in ('document','inquiry'):
            inputs,doc,inquiry,answer=answer_example()
            changed=doc if target=='document' else inquiry
            changed['status']='DEFER';rehash(changed)
            field='document_report_id' if target=='document' else 'question_report_id'
            answer[field]=changed['report_id']
            for proof in answer['proofs']:proof[field]=changed['report_id']
            answer['answer_id']=evaluation.digest({k:v for k,v in answer.items() if k!='answer_id'})
            with self.assertRaisesRegex(ValueError,'complete document and question'):
                evaluation.validate_answer(answer,doc,inquiry,inputs,inputs['text'])

    def test_source_receipt_must_cover_original_full_record(self):
        raw=b'LOCATION\tFORM\tTAG\tFEATURES\n(1:1:1:1)\tkitaAbN\tN\tSTEM|POS:N|LEM:kitaAb|MS\n'
        audit=evaluation.SourceAudit(raw,source_id='authored')
        start,end=next(iter(audit.records));row=audit.records[(start,end)]
        receipt={'source_id':'authored','source_sha256':sha256(raw).hexdigest(),'byte_start':start,'byte_end':end,
                 'ordinal':1,'locator':[1,1,1,1],'record_id':evaluation.digest(['nabt.corpus-source.v1','qac','authored',sha256(raw).hexdigest(),start,end,1])}
        self.assertEqual(audit.receipt(receipt),row)
        receipt['byte_end']-=1
        with self.assertRaisesRegex(ValueError,'complete raw'):audit.receipt(receipt)

    def test_arbitrary_anchor_substring_is_not_a_licensed_stem(self):
        inputs,report=example();row=report['occurrences'][0]['readings'][0]
        expected={'surface':'حازم','span':[0,8],'span_basis':'occurrence_or_licensed_stem'}
        truncated={**row['stem_span'],'end':6}
        self.assertFalse(evaluation.anchor_matches(expected,truncated,row))

    def test_roles_cannot_be_pooled_across_alternative_analyses(self):
        inputs,report=example();clause=report['clauses'][0]
        for o in report['occurrences']:
            o['readings'][0]['construction']='inflected';o['readings'][0]['class_candidates']=[0]
        first=clause['analyses'][0];second=deepcopy(first)
        for analysis,index in [(first,0),(second,1)]:
            a=analysis['assignments'][index]
            a['inflected_case']='raf';a['case_domain']='inflected_case'
            a['sign_candidates']=[{'case':1,'sign':0,'sign_name':'damma'}]
            analysis['analysis_id']=evaluation.digest({k:v for k,v in analysis.items() if k!='analysis_id'})
        clause['analyses']=[first,second]
        clause['clause_id']=evaluation.digest({k:v for k,v in clause.items() if k!='clause_id'})
        report['claims'][0]['proofs']=[{'analysis_id':a['analysis_id'],'clause_id':clause['clause_id'],'span':clause['span']} for a in clause['analyses']]
        report['report_id']=evaluation.digest({k:v for k,v in report.items() if k!='report_id'})
        roles=[{'surface':a['surface'],'span':[a['span']['start'],a['span']['end']],
                'role':a['role'],'case':'raf','case_domain':'inflected','sign':'damma'} for a in first['assignments']]
        case={'id':'UNIT-CORRELATION','group':'unit','mode':'positive','input':inputs,
              'expected':{'complete_construction_required':True,'required_roles':roles,'questions':[]}}
        scored=evaluation.score_case(case,report,[],{'valid':True})
        checks={c['check']:c['passed'] for c in scored['checks']}
        self.assertTrue(checks['role:0'] and checks['role:1'])
        self.assertFalse(checks['roles_same_analysis'])
        self.assertFalse(checks['coherent_analysis'])

    def test_partial_replay_never_counts_as_comprehension(self):
        freeze,material,_=evaluation.load_material()
        replay=[c for c in material['cases'] if c['mode']=='replay']
        self.assertEqual(len(replay),6)
        self.assertTrue(all('required_claims' not in c['expected'] for c in replay))
        question=next(c for c in replay if c['expected']['replay']['change']=='question')
        self.assertFalse(question['expected']['replay']['changed_report_must_invalidate'])
        self.assertTrue(question['expected']['replay']['changed_answer_must_invalidate'])

    def test_selected_runtime_cannot_reuse_preloaded_nabt(self):
        with patch.dict(sys.modules,{'nabt':object()}):
            with self.assertRaisesRegex(ValueError,'fresh process'):
                evaluation.evaluate(Path('/tmp/not-used-construction.json'),Path('/tmp/not-used-manifest'),Path('/tmp/not-used-runtime'))

    def test_unsupported_manifest_is_rejected_before_runtime_import(self):
        with patch.object(Path,'read_bytes',return_value=b'{}'):
            with self.assertRaisesRegex(ValueError,'Unapproved runtime'):
                evaluation.runtime_snapshot(Path('/tmp/unapproved'),Path('/tmp/anything'))


if __name__=='__main__':unittest.main()
