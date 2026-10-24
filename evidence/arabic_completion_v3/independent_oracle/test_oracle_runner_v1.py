"""Static/input and adversarial scorer tests before the first 24-case run."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('tested_completion_runner',HERE/'run_oracle_v1.py')
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
S=R.S;E=S.E


def graph():
    text='فَجَّرَ خَالِدٌ الْأَرْضَ عُيُونًا.'
    inputs={'text':text};raw=text.encode()
    def span(surface):
        word=surface.encode();start=raw.index(word)
        return {'start':start,'end':start+len(word)}
    surfaces=['فَجَّرَ','خَالِدٌ','الْأَرْضَ','عُيُونًا'];spans=list(map(span,surfaces))
    ids=['verb','actor','object','unit'];rows=[{'reading_id':rid,'stem_span':sp,'kind':'verb' if i==0 else 'noun',
        'lexical_features':{'lemma':['فَجَّرَ','خَالِد','أَرْض','عَيْن'][i]}} for i,(rid,sp) in enumerate(zip(ids,spans))]
    claim={'predicate_kind':'event','predicate':'فَجَّرَ','args':['khalid','earth'],
        'restriction':[{'kind':'tamyiz','predicate':'عَيْن','owner':'earth'}],
        'proofs':[{'clause_id':'clause','analysis_id':'analysis'}]}
    a={'analysis_id':'analysis','assertion_allowed':True,'reading_ids':ids,
       'assignments':[{'span':spans[i],'reading_id':ids[i],'head_span':spans[0],'activated':True,
                       'role':['active_subject','direct_object','tamyiz'][i-1]} for i in (1,2,3)],
       'references':[{'span':spans[1],'bound_entity_id':'khalid'},{'span':spans[2],'bound_entity_id':'earth'}],
       'relations':[{'kind':'tamyiz','head_span':spans[0],'dependent_span':spans[3],
                     'dependent_reading_id':'unit','owner_span':spans[2]}]}
    report={'claims':[claim],'clauses':[{'clause_id':'clause','analyses':[a]}],
        'occurrences':[{'span':sp,'readings':[row]} for sp,row in zip(spans,rows)]}
    wanted={'kind':'tamyiz','governor':surfaces[0],'target':surfaces[2],'dependent':surfaces[3],'owner':'earth'}
    return report,inputs,wanted


class OracleRunnerTests(unittest.TestCase):
    def test_frozen_material_and_declared_denominators(self):
        _,cases,_,_=R.load_material()
        self.assertEqual(len(cases['cases']),24)
        self.assertEqual(sum(len(c['expected']['questions']) for c in cases['cases']),29)

    def test_object_owner_requires_its_exact_relation_and_reference(self):
        report,inputs,wanted=graph()
        self.assertTrue(S.same_claim_qualifier(report,inputs,wanted))
        for field in ('qualifier','endpoint','missing_endpoint','reference'):
            r=deepcopy(report);a=r['clauses'][0]['analyses'][0]
            if field=='qualifier':r['claims'][0]['restriction'][0]['owner']='khalid'
            if field=='endpoint':a['relations'][0]['owner_span']=a['references'][0]['span']
            if field=='missing_endpoint':del a['relations'][0]['owner_span']
            if field=='reference':a['references'][1]['bound_entity_id']='khalid'
            with self.subTest(field=field):self.assertFalse(S.same_claim_qualifier(r,inputs,wanted))

    def test_same_lemma_in_other_participant_or_clause_is_not_a_relation(self):
        report,inputs,wanted=graph()
        a=report['clauses'][0]['analyses'][0]
        a['relations'][0]['head_span']=a['references'][0]['span']
        self.assertFalse(S.same_claim_qualifier(report,inputs,wanted))

    def test_a_missing_positive_claim_stays_a_failure_without_an_unsafe_flag(self):
        f=json.loads((HERE/'validator_review_v1/name_v2.json').read_text())
        expected={'document_status':'LICENSED_DISCOURSE','questions':[],'required_claims':[],
            'forbidden_claims':[],'obligations':[],'relations':[],'references':[],'clause_forces':[]}
        case={'id':'UNIT','family':'unit','category':'positive','expected':expected}
        record={'inputs':f['inputs'],'report':f['report'],'verification':{'valid':True},'questions':[]}
        audit=E.SourceAudit(f['raw'].encode(),source_id=f['report']['lexical_model']['source']['id'])
        self.assertTrue(S.score_case(case,record,audit)['passed'])
        expected['required_claims']=[{'predicate':'NOT_IN_SOURCE'}]
        score=S.score_case(case,record,audit)
        self.assertFalse(score['passed']);self.assertFalse(score['unsafe'])

    def test_runtime_error_is_not_defer(self):
        case={'id':'UNIT','category':'positive','expected':{'document_status':'LICENSED_DISCOURSE'}}
        result=S.score_case(case,{'report':None,'inputs':{},'errors':['example']},None)
        self.assertFalse(result['passed']);self.assertIsNone(result['status'])
        self.assertEqual(result['checks'][0]['kind'],'execution')


if __name__=='__main__':unittest.main()
