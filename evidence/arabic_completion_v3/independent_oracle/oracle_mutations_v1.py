"""Predeclared counterexamples, using only retained observations and validators.

No parser prediction is requested here. Unavailable positive evidence is an
UNEXERCISED test, never a PASS. Before/after objects are stored in the journal.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('mutation_independent_checks',HERE/'oracle_checks_v1.py')
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
E=S.E


class Unavailable(Exception):pass


def rehash(report):
    changed={}
    for clause in report['clauses']:
        for analysis in clause['analyses']:
            old=analysis['analysis_id'];analysis['analysis_id']=E.digest({k:v for k,v in analysis.items() if k!='analysis_id'})
            changed[old]=analysis['analysis_id']
        old=clause['clause_id'];clause['clause_id']=E.digest({k:v for k,v in clause.items() if k!='clause_id'})
        changed[old]=clause['clause_id']
    for claim in report['claims']:
        for proof in claim['proofs']:
            for key in ('clause_id','analysis_id'):proof[key]=changed.get(proof[key],proof[key])
    report['report_id']=E.digest({k:v for k,v in report.items() if k!='report_id'})


def run(records,audits,log):
    recipes=json.loads((HERE/'adversarial_checks.json').read_text())['checks'];results=[]
    def record(cid):
        value=deepcopy(records[cid])
        if value.get('report') is None:raise Unavailable('No original report: '+cid)
        return value
    def audit(value):return audits[value['profile']]
    def names(value):
        for a in S.analyses(value['report']):
            for ref in a['references']:
                if ref.get('name_correspondence'):return a,ref
        raise Unavailable('No source-bound name witness was exposed')
    def name_valid(value):
        a,ref=names(value);rows,_=E.reading_rows(value['report'])
        E.validate_reference_origin(ref,value['inputs'],{e['id']:e for e in value['inputs']['context']['entities']},
            analysis=a,rows=rows,audit=audit(value),model_summary=value['report']['lexical_model'])
        return True
    def traits_valid(value):
        finding=S.nominal_traits(value['report'],audit(value))
        return not finding['errors'] and not finding['unresolved']
    def full_valid(value):
        E.validate_report(value['report'],value['inputs'],audit(value));return True
    def attempt(recipe,before,mutate,check):
        try:
            before=before()
            if not check(before):raise Unavailable('The retained original does not expose a valid positive control for this predicate')
            after=deepcopy(before);mutate(after)
            try:accepted=check(after);error=None
            except (ValueError,KeyError,TypeError,IndexError) as err:accepted=False;error={'type':type(err).__name__,'message':str(err)}
            result={'id':recipe['id'],'outcome':'FAIL' if accepted else 'PASS','independent_mutation_accepted':bool(accepted),
                    'error':error,'meaning':'Independent checker refusal; not an extra Arabic language case.'}
            log({'kind':'mutation_observation','case_id':before.get('case_id'),'recipe':recipe,'before':before,'after':after,'result':result})
        except (Unavailable,StopIteration) as err:
            result={'id':recipe['id'],'outcome':'UNEXERCISED','reason':str(err) or 'Required positive witness not exposed',
                    'meaning':'No successful refusal is claimed when the needed source certificate is unavailable.'}
            log({'kind':'mutation_observation','case_id':None,'recipe':recipe,'result':result})
        except Exception as err:
            result={'id':recipe['id'],'outcome':'ERROR','error':{'type':type(err).__name__,'message':str(err)},
                    'meaning':'Mutation adapter/control failure is not an accepted rejection.'}
            log({'kind':'mutation_observation','case_id':None,'recipe':recipe,'result':result})
        results.append(result)
    byid={r['id']:r for r in recipes}
    def g1(v):names(v)[1]['name_correspondence']['reading_id']='0'*64
    def g2(v):
        for e in v['inputs']['context']['entities']:
            if e['id']=='teacher':e['name']='الْمُدَرَّس'
    def g3(v):
        a,ref=names(v);w=ref['name_correspondence'];rows,_=E.reading_rows(v['report'])
        rows[w['reading_id']]['construction_supports']=[];w['construction_supports']=[]
    def g4(v):
        _,ref=names(v);ref['candidate_entity_ids']=ref['candidate_entity_ids'][:1];ref['bound_entity_id']=ref['candidate_entity_ids'][0]
    for key,cid,mutation in [('V-G01','G01',g1),('V-G02','G01',g2),('V-G03','G01',g3),('V-G04','G05',g4)]:
        attempt(byid[key],lambda cid=cid:record(cid),mutation,name_valid)
    def trait_mutation(value,pos,lemma):
        rows,_=E.reading_rows(value['report']);targets=[r for r in rows.values() if r.get('lexical_features',{}).get('pos')==pos
              and r.get('lexical_features',{}).get('lemma')==lemma and r['lexical_features'].get('number') is None]
        if not targets:raise Unavailable('No source-number-omitted reading retained')
        rid=targets[0]['reading_id']
        for occurrence in value['report']['occurrences']:
            for row in occurrence['readings']:
                if row['reading_id']==rid:row['lexical_features']['number']='singular'
        for row in value['report'].get('derived_readings',[]):
            if row['reading_id']==rid:row['lexical_features']['number']='singular'
    attempt(byid['V-N01'],lambda:record('N03'),lambda v:trait_mutation(v,'ADJ','مَاهِرَة'),traits_valid)
    attempt(byid['V-N02'],lambda:record('N06'),lambda v:trait_mutation(v,'N','كَرِيم'),traits_valid)
    def agreement_valid(v):
        return any(c['predicate_kind']=='property' and c['args']==['hind'] and
            E.question_validation.source_agreement_witnesses(c,{'gender':'feminine','number':'singular'},'hind',v['report'])
            for c in v['report']['claims'])
    def borrow_relative(v):
        for a in S.analyses(v['report']):
            edges=[r for r in a.get('relations',[]) if r.get('kind')=='predicate_agreement']
            for edge in edges:a['relations'].append({'kind':'relative_clause','inner_predicate_reading_id':edge['dependent_reading_id'],
                                                    'inner_predicate_span':deepcopy(edge['dependent_span'])})
    attempt(byid['V-N03'],lambda:record('N01'),borrow_relative,agreement_valid)
    def positive_answer():
        for value in records.values():
            for index,q in enumerate(value['questions']):
                if (q.get('answer') or {}).get('status')=='SUPPORTED' and q.get('inquiry'):
                    return {'case_id':value['case_id'],'inputs':deepcopy(value['inputs']),'report':deepcopy(value['report']),
                            'question':deepcopy(q),'profile':value['profile']}
        raise Unavailable('No complete supported answer certificate')
    def answer_valid(v):
        q=v['question'];E.question_validation.validate_interpretations(q['answer'],v['report'],q['inquiry'],v['inputs'],claim_view=E.claim_view)
        return True
    def incomplete(v):
        inquiry=v['question']['inquiry'];a=next(a for a in S.analyses(inquiry) if not a['rejected_candidate'])
        a['licensed_syntax']=False;a['references_complete']=False
    attempt(byid['V-N04'],positive_answer,incomplete,answer_valid)
    oracle=json.loads((HERE/'cases.json').read_text())['cases'];wanted={c['id']:c['expected'] for c in oracle}
    def relation_valid(v):return S.same_claim_qualifier(v['report'],v['inputs'],wanted[v['case_id']]['relations'][0])
    def owner_to_actor(v):
        for c in v['report']['claims']:
            for q in c['restriction']:
                if type(q) is dict and q.get('kind')=='tamyiz':q['owner']='khalid'
    attempt(byid['V-T01'],lambda:record('T03'),owner_to_actor,relation_valid)
    def cross_clause(v):
        clauses=v['report']['clauses']
        if len(clauses)<2:raise Unavailable('Second clause not exposed')
        other=clauses[1]['span']
        for a in clauses[0]['analyses']:
            for rel in a.get('relations',[]):
                if rel.get('kind')=='tamyiz':rel['head_span']=deepcopy(other)
    attempt(byid['V-T02'],lambda:record('T06'),cross_clause,relation_valid)
    def event_roles_valid(v):
        rows,ranges=E.reading_rows(v['report']);found=False
        for claim,a in S.accepted_graphs(v['report']):
            if claim['predicate_kind']=='event':E.validate_claim_roles(claim,a,rows,ranges);found=True
        return found
    def tamyiz_as_object(v):
        for claim in v['report']['claims']:
            if claim['predicate_kind']=='event':claim['args'].append('vessel');claim['restriction']=[]
    attempt(byid['V-T03'],lambda:record('T01'),tamyiz_as_object,event_roles_valid)
    def activate_wrong_case(v):
        assignments=[x for a in S.analyses(v['report']) for x in a['assignments'] if x['role']=='tamyiz']
        if not assignments:raise Unavailable('No pending nominative tamyiz assignment exposed')
        for x in assignments:x.update(activated=True,actual_role='tamyiz',inflected_case='nasb')
    attempt(byid['V-T04'],lambda:record('T05'),activate_wrong_case,
            lambda v:not S.activated_surface_errors(v['report'],v['inputs']))
    result={'id':'V-T05','outcome':'UNEXERCISED',
        'reason':'This predeclared temporal-vs-tamyiz control has no frozen temporal teaching input or positive certificate in the 24 cases; no uncounted fixed-status case is invented.',
        'meaning':'Separate future source/control obligation; not a PASS.'}
    results.append(result);log({'kind':'mutation_observation','case_id':None,'recipe':byid['V-T05'],'result':result})
    def attached_valid(v):
        result=S.attached_host_evidence(v['report'],v['inputs'],audit(v))
        if not result['examined']:raise Unavailable('No connected host candidate exposed')
        return not result['errors']
    def contaminate_host(v):
        rows,_=E.reading_rows(v['report'])
        row=next(r for r in rows.values() if r.get('person_evidence',{}).get('attached_pronouns')
                 and any(p.get('licensed') for p in r['person_evidence']['attached_pronouns']))
        row['person_evidence']['person_profile']=deepcopy(row['person_evidence']['attached_pronouns'][0]['person_profile'])
    attempt(byid['V-P01'],lambda:record('P04'),contaminate_host,attached_valid)
    def overlap_suffix(v):
        rows,_=E.reading_rows(v['report'])
        row=next(r for r in rows.values() if r.get('person_evidence',{}).get('attached_pronouns'))
        parts=row['segmentation']['parts']
        if len(parts)<2:raise Unavailable('No separate source suffix partition exposed')
        parts[-1]['span']['start']=parts[-2]['span']['start']
    attempt(byid['V-P02'],lambda:record('P01'),overlap_suffix,attached_valid)
    def change_speaker(v):v['inputs']['context']=deepcopy(records['P05']['inputs']['context'])
    attempt(byid['V-P03'],lambda:record('P04'),change_speaker,full_valid)
    def assert_command(v):
        candidates=[a for a in S.analyses(v['report']) if a['force']=='COMMAND']
        if not candidates:raise Unavailable('No command-force candidate exposed')
        for a in candidates:
            a['assertion_allowed']=True
            for c in a['claims']:c['tense']='past'
        rehash(v['report'])
    attempt(byid['V-P04'],lambda:record('P06'),assert_command,full_valid)
    def antecedent_valid(v):
        refs=[r for a in S.analyses(v['report']) if not a['rejected_candidate'] for r in a['references']
              if r.get('surface')=='هُ' and r.get('origin')=='antecedent']
        if not refs:raise Unavailable('No ambiguous object reference exposed')
        return all(set(r['candidate_entity_ids'])=={'khalid','malik'} and r.get('bound_entity_id') is None for r in refs)
    def nearest(v):
        for a in S.analyses(v['report']):
            for r in a['references']:
                if r.get('surface')=='هُ' and r.get('origin')=='antecedent':
                    r['candidate_entity_ids']=['malik'];r['bound_entity_id']='malik'
    attempt(byid['V-P05'],lambda:record('P02'),nearest,antecedent_valid)
    E.require({r['id'] for r in results}==set(byid) and len(results)==18,'Mutation recipe inventory changed')
    return results
