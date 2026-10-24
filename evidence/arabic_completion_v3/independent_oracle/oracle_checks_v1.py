"""Pre-execution scorer for the frozen 24 directed cases.

This module imports independent validators, never a production parser. Its
extra checks compare accepted claim proof graphs, raw annotated features,
source partitions and explicit oracle constraints. Missing public evidence is
reported as a failure or an unresolved provenance check, never synthesized.
"""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('completion_independent_evaluator', ROOT/'tools/construction_evaluation.py')
E = importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
V = E.source_validation
VERSION = 'nabt.completion-directed-oracle-scorer.v1'


def claim_matches(pattern, claim):
    return all(claim.get(key) == value for key, value in pattern.items())


def analyses(report):
    return [a for c in report['clauses'] for a in c['analyses']]


def accepted_graphs(report):
    index={(c['clause_id'],a['analysis_id']):a for c in report['clauses'] for a in c['analyses']}
    return [(claim,index[(p['clause_id'],p['analysis_id'])]) for claim in report['claims']
            for p in claim.get('proofs',[]) if (p['clause_id'],p['analysis_id']) in index]


def piece(inputs,span):
    return inputs['text'].encode()[span['start']:span['end']].decode()


def same_claim_qualifier(report, inputs, wanted):
    """An endpoint elsewhere in the document does not satisfy this predicate."""
    rows,_=E.reading_rows(report)
    owner=wanted['owner']
    for claim,a in accepted_graphs(report):
        if owner not in claim['args'] or not a.get('assertion_allowed'):
            continue
        for rel in a.get('relations',[]):
            if rel.get('kind')!=wanted['kind']:
                continue
            dep=rows.get(rel.get('dependent_reading_id'))
            dspan=rel.get('dependent_span');hspan=rel.get('head_span')
            if dep is None or dspan is None or hspan is None or rel['dependent_reading_id'] not in a['reading_ids']:
                continue
            if piece(inputs,dspan)!=wanted['dependent']:
                continue
            assignments=[x for x in a['assignments'] if x['span']==dspan and x['reading_id']==dep['reading_id']
                         and x['role']==wanted['kind'] and x.get('activated') and x.get('head_span')==hspan]
            if not assignments:
                continue
            qualifiers=[q for q in claim['restriction'] if type(q) is dict and q.get('kind')==wanted['kind']
                        and q.get('predicate')==dep.get('lexical_features',{}).get('lemma')]
            if wanted['kind']=='naat':
                if piece(inputs,hspan)!=wanted['head'] or not any(q.get('target')==owner for q in qualifiers):
                    continue
                heads=[x for x in a['assignments'] if x['span']==hspan and x.get('activated')
                       and x['reading_id']==rel.get('head_reading_id')]
                refs=[r for r in a['references'] if r['span']==hspan and r.get('bound_entity_id')==owner]
                if heads and refs and rel.get('agreement')=='confirmed':
                    return True
                continue
            if piece(inputs,hspan)!=wanted['governor'] or not qualifiers:
                continue
            governors=[rows[r] for r in a['reading_ids'] if rows[r].get('stem_span')==hspan
                       and rows[r].get('kind')=='verb' and rows[r].get('lexical_features',{}).get('lemma')==claim['predicate']]
            targets=[x for x in a['assignments'] if x.get('activated') and x.get('head_span')==hspan
                     and x['role'] in ('active_subject','passive_subject','direct_object')
                     and piece(inputs,x['span'])==wanted['target']]
            for target in targets:
                refs=[r for r in a['references'] if r['span']==target['span'] and r.get('bound_entity_id')==owner]
                if not refs or not governors:
                    continue
                explicit=rel.get('owner_span',rel.get('target_span'))
                if explicit is not None and explicit!=target['span']:
                    continue
                if any(q.get('owner',owner)!=owner for q in qualifiers):
                    continue
                # Legacy unary nisba has no owner slot. The only same-governor
                # participant can discharge this adapter, with its bound role.
                # A transitive clause must expose an explicit object endpoint.
                participants=[x for x in a['assignments'] if x.get('activated') and x.get('head_span')==hspan
                              and x['role'] in ('active_subject','passive_subject','direct_object')]
                if explicit is None and not (len(claim['args'])==1 and len(participants)==1
                        and target['role'] in ('active_subject','passive_subject')):
                    continue
                if target['role']=='direct_object' and explicit!=target['span']:
                    continue
                if target['role']=='direct_object' and claim['args'][-1]!=owner:
                    continue
                return True
    return False


def nominal_traits(report,audit):
    """Inspect actual raw annotations; an omitted S is not an annotation of S."""
    rows,_=E.reading_rows(report);observations=[];errors=[];unresolved=[]
    for row in rows.values():
        features=row.get('lexical_features',{})
        if row.get('kind')!='noun' or row.get('variant')!='attested' or features.get('pos') not in ('N','PN','ADJ'):
            continue
        raw=[]
        for proof in row.get('support_records',[]):
            if type(proof) is not dict or 'record_id' not in proof:
                continue
            record=audit.receipt(proof)
            if record['tag'] in ('N','PN','ADJ') and record['tokens'][0]=='STEM':
                profile,derivation=V.raw_features(record)
                if profile['pos']==features['pos'] and profile['lemma']==features.get('lemma'):
                    raw.append((proof,profile))
        if not raw:
            unresolved.append({'reading_id':row['reading_id'],'reason':'NO_SAME_POS_LEMMA_RAW_NOMINAL_PROFILE'})
            continue
        values={axis:sorted({p[axis] for _,p in raw},key=lambda x:str(x)) for axis in ('gender','number')}
        observations.append({'reading_id':row['reading_id'],'pos':features['pos'],'lemma':features.get('lemma'),
            'observed':{axis:features.get(axis) for axis in values},'raw_values':values,
            'record_ids':[p['record_id'] for p,_ in raw]})
        for axis in values:
            value=features.get(axis)
            if value not in (None,'unknown') and value not in values[axis]:
                derivations={k:v for k,v in row.items() if 'derivation' in k or 'inferred' in k}
                finding={'reading_id':row['reading_id'],'axis':axis,'value':value,'raw_values':values[axis]}
                if derivations:
                    unresolved.append({**finding,'reason':'NEW_DERIVATION_REQUIRES_INDEPENDENT_REVIEW','evidence':derivations})
                else:
                    errors.append({**finding,'reason':'UNSUPPORTED_NOMINAL_FEATURE_INFERENCE'})
    return {'observations':observations,'errors':errors,'unresolved':unresolved}


def activated_surface_errors(report,inputs):
    rows,_=E.reading_rows(report);errors=[]
    allowed={'raf':set('ٌُ'),'nasb':set('ًَ'),'jarr':set('ٍِ')}
    for a in analyses(report):
        for role in a['assignments']:
            if not role.get('activated'):
                continue
            row=rows[role['reading_id']]
            if row.get('kind')!='noun':
                continue
            surface=piece(inputs,role['span'])
            if role['role']=='tamyiz' and (row.get('al_evidence')==1 or V.letters(surface).startswith('ال')):
                errors.append({'reading_id':row['reading_id'],'reason':'DEFINITE_ORDINARY_NISBA_TAMYIZ'})
            if row.get('class_candidates')==[0] and role.get('inflected_case') in allowed:
                parts=V.clusters(surface)
                observed=parts[-1][1]&V.VOWELS
                if row.get('nominal_case_carrier') and parts[-1][0]=='ا' and len(parts)>1:
                    observed=parts[-2][1]&V.VOWELS
                if observed and not observed <= allowed[role['inflected_case']]:
                    errors.append({'reading_id':row['reading_id'],'reason':'VISIBLE_CASE_CONFLICT',
                                   'surface':surface,'case':role['inflected_case']})
    return errors


def attached_host_evidence(report,inputs,audit):
    rows,_=E.reading_rows(report);result={'examined':0,'licensed':0,'errors':[]}
    for row in rows.values():
        pe=row.get('person_evidence',{})
        if row.get('kind')!='verb' or not pe.get('attached_pronouns'):
            continue
        result['examined']+=1
        try:
            occurrence=row['identity']['span'];parts=row['segmentation']['parts'];cursor=occurrence['start']
            for part in parts:
                E.check_span(part['span'],inputs,part['surface'])
                E.require(part['span']['start']==cursor,'Connected token has a partition gap/overlap')
                cursor=part['span']['end']
            E.require(cursor==occurrence['end'] and ''.join(p['surface'] for p in parts)==piece(inputs,occurrence),
                      'Connected token omits source suffix bytes')
            proofs={p['record_id']:p for p in pe.get('supports',[]) if type(p) is dict and 'record_id' in p}
            raw={rid:audit.receipt(p) for rid,p in proofs.items()}
            code=pe.get('source_person_code')
            host=[r for r in raw.values() if r['tag']=='V' and r['tokens'][0]=='STEM'
                  and [t for t in r['tokens'] if re.fullmatch(r'[123][MF]?[SDP]',t)]==[code]
                  and V._decode(V._field(r['tokens'],'LEM:'))==pe.get('lemma')
                  and V._decode(V._field(r['tokens'],'ROOT:'),V.ROOT_BW)==pe.get('root')]
            licensed=[p for p in pe['attached_pronouns'] if p.get('licensed') is True]
            if licensed:
                result['licensed']+=1
                E.require(host,'Licensed host lacks its own raw lexical person profile')
                E.require(type(code) is str and re.fullmatch(r'[123][MF]?[SDP]',code),'Host raw person profile missing')
                E.require(pe.get('person_profile')=={'person':int(code[0]),
                    'gender':0 if 'M' in code else 1 if 'F' in code else 2,
                    'number':{'S':0,'D':1,'P':2}[code[-1]]},'Object suffix replaced host person/gender/number')
                for suffix in licensed:
                    suffix_code=suffix.get('source_person_code')
                    supports=[raw[rid] for rid in suffix.get('support_ids',[]) if rid in raw]
                    E.require(any(r['tag']=='PRON' and r['tokens'][0]=='SUFFIX'
                                  and [t for t in r['tokens'] if re.fullmatch(r'[123][MF]?[SDP]',t)]==[suffix_code]
                                  for r in supports),'Licensed suffix lacks its own raw profile')
                    E.require(suffix.get('person_profile')=={'person':int(suffix_code[0]),
                        'gender':0 if 'M' in suffix_code else 1 if 'F' in suffix_code else 2,
                        'number':{'S':0,'D':1,'P':2}[suffix_code[-1]]}, 'Host profile replaced object person/gender/number')
                    E.require(type(suffix['start_cluster']) is int and type(suffix['end_cluster']) is int
                              and 0<=pe['host_end_cluster']<=suffix['start_cluster']<suffix['end_cluster'],
                              'Host and attached object overlap')
        except (ValueError,KeyError,TypeError,IndexError) as error:
            result['errors'].append({'reading_id':row['reading_id'],'message':str(error)})
    return result


def score_case(case,record,audit):
    report=record.get('report');inputs=record['inputs'];expected=case['expected'];checks=[];unsafe=[]
    def check(name,passed,detail=None,*,kind='coverage',danger=False):
        passed=passed is True
        checks.append({'check':name,'passed':passed,'kind':kind,'detail':detail})
        if danger and not passed:unsafe.append(name)
    if report is None:
        check('document_returned',False,record.get('errors'),kind='execution')
        return {'id':case['id'],'category':case['category'],'fixed_status_case':expected['document_status'] is not None,
                'passed':False,'checks':checks,'unsafe':unsafe,'provenance_outcome':None,'status':None}
    check('document_replay',(record.get('verification') or {}).get('valid') is True,kind='integrity')
    try:
        E.validate_report(report,inputs,audit);integrity=True
    except Exception as error:
        integrity=False;check('independent_report_validation',False,{'type':type(error).__name__,'message':str(error)},kind='integrity',danger=True)
    else:check('independent_report_validation',True,kind='integrity')
    if expected['document_status'] is not None:
        check('document_status',report['status']==expected['document_status'],{'expected':expected['document_status'],'actual':report['status']})
    for index,pattern in enumerate(expected['required_claims']):
        check('required_claim:'+str(index),any(claim_matches(pattern,c) for c in report['claims']),pattern)
    for index,pattern in enumerate(expected['forbidden_claims']):
        check('forbidden_claim:'+str(index),not any(claim_matches(pattern,c) for c in report['claims']),pattern,danger=True)
    for name,operation in (('claims_min',lambda a,b:a>=b),('claims_max',lambda a,b:a<=b)):
        if name in expected:check(name,operation(len(report['claims']),expected[name]),{'expected':expected[name],'actual':len(report['claims'])},danger=name=='claims_max')
    for index,relation in enumerate(expected['relations']):
        check('same_claim_relation:'+str(index),same_claim_qualifier(report,inputs,relation),relation)
    viable=[a for a in analyses(report) if not a['rejected_candidate']]
    for index,wanted in enumerate(expected['references']):
        refs=[r for a in viable for r in a['references'] if r.get('surface')==wanted['surface']]
        if 'within' in wanted:
            raw=inputs['text'].encode();word=wanted['within'].encode();occurrences=[];start=0
            while (start:=raw.find(word,start))>=0:
                occurrences.append((start,start+len(word)));start+=len(word)
            refs=[r for r in refs if any(a<=r['span']['start']<r['span']['end']<=b for a,b in occurrences)]
        check('reference_exposed:'+str(index),bool(refs),wanted)
        if 'required_candidates' in wanted:
            check('reference_candidates:'+str(index),bool(refs) and all(set(r['candidate_entity_ids'])==set(wanted['required_candidates']) for r in refs),wanted)
        if 'bound' in wanted:
            check('reference_binding:'+str(index),bool(refs) and all(r.get('bound_entity_id')==wanted['bound'] for r in refs),wanted,
                  danger=bool(refs) and any(r.get('bound_entity_id') not in (None,wanted['bound']) for r in refs))
        if 'forbidden_bound' in wanted:
            check('reference_forbidden:'+str(index),all(r.get('bound_entity_id') not in wanted['forbidden_bound'] for r in refs),wanted,danger=True)
    if expected['clause_forces']:
        check('clause_forces',[c['force'] for c in report['clauses']]==expected['clause_forces'],
              {'expected':expected['clause_forces'],'actual':[c['force'] for c in report['clauses']]})
    if case['id']=='P03':
        refs=[r for a in viable for r in a['references'] if r.get('origin')=='antecedent']
        check('no_catalogue_as_prior_antecedent',all(not r.get('candidate_entity_ids') and r.get('bound_entity_id') is None for r in refs),kind='integrity',danger=True)
    traits=nominal_traits(report,audit);surface_errors=activated_surface_errors(report,inputs)
    attached=attached_host_evidence(report,inputs,audit)
    check('raw_nominal_traits',not traits['errors'],traits['errors'],kind='integrity',danger=True)
    check('activated_surface_constraints',not surface_errors,surface_errors,kind='integrity',danger=True)
    check('connected_partition_and_profiles',not attached['errors'],attached,kind='integrity',danger=True)
    if case['id']=='G02':
        check('inna_subject_and_predicate_cases',any(
            any(x.get('activated') and x['role']=='inna_subject' and x.get('inflected_case')=='nasb' for x in a['assignments'])
            and any(x.get('activated') and x['role']=='inna_predicate' and x.get('inflected_case')=='raf' for x in a['assignments'])
            for c,a in accepted_graphs(report)))
    if 'AGREEMENT_SAME_READING_AND_SUBJECT' in expected['obligations']:
        entities={e['id']:e for e in inputs['context']['entities']}
        for index,pattern in enumerate(expected['required_claims']):
            if pattern['predicate_kind']=='property':
                eid=pattern['args'][0];profile={k:entities[eid][k] for k in ('gender','number')}
                check('same_claim_adjective_agreement:'+str(index),any(claim_matches(pattern,c) and
                    E.question_validation.source_agreement_witnesses(c,profile,eid,report) for c in report['claims']))
    if 'SAME_READING_GEMINATION' in expected['obligations']:
        check('source_gemination_witness_exposed',any(r.get('name_correspondence') for a in viable for r in a['references']))
    if 'CONNECTED_HOST_SOURCE_CONSERVATION' in expected['obligations'] and expected['document_status']=='LICENSED_DISCOURSE':
        check('complete_attached_host_evidence_exposed',attached['licensed']>0)
    provenance=None
    if case['category']=='provenance_probe':
        lemma='مَاهِرَة' if case['id']=='N03' else 'كَرِيم'
        observations=[o for o in traits['observations'] if o['lemma']==lemma]
        relevant={o['reading_id'] for o in observations}
        errors=[e for e in traits['errors'] if e['reading_id'] in relevant]
        unresolved=[e for e in traits['unresolved'] if e['reading_id'] in relevant]
        if case['id']=='N06':
            check('preserve_N_and_ADJ',{o['pos'] for o in observations}>={'N','ADJ'},kind='provenance')
        unsupported=bool(errors)
        provenance=('unsupported_inference' if unsupported else 'unresolved_independent_review' if unresolved or not observations
                    else 'correct_abstention' if report['status']=='DEFER' else 'checked_derivation')
        # A complete report with absent source number requires a derivation;
        # none is supplied merely by agreeing with the expected surface.
        absent=[o for o in observations if o['raw_values']['number']==[None]]
        if report['status']=='LICENSED_DISCOURSE' and absent and not unsupported:
            provenance='unresolved_independent_review'
        check('conditional_provenance',provenance in ('correct_abstention','checked_derivation'),
              {'outcome':provenance,'observations':observations,'unresolved':unresolved,'errors':errors},kind='provenance',danger=unsupported)
    question_results=[]
    for qi,wanted in enumerate(expected['questions']):
        item=record['questions'][qi];answer=item.get('answer');inquiry=item.get('inquiry')
        check('question_status:'+str(qi),answer is not None and answer.get('status')==wanted['expected_status'],
              {'expected':wanted['expected_status'],'actual':None if answer is None else answer.get('status')},
              danger=answer is not None and answer.get('status') in ('SUPPORTED','REFUTED','CONFLICT') and wanted['expected_status'] in ('UNKNOWN','DEFER'))
        valid=False;error=None
        try:
            E.require(answer is not None and inquiry is not None,'Question or answer was not returned')
            E.validate_report(inquiry,{**inputs,'text':wanted['text'],'source_id':'question'},audit)
            E.validate_answer(answer,report,inquiry,inputs,wanted['text']);valid=True
        except Exception as err:error={'type':type(err).__name__,'message':str(err)}
        check('question_independent_validation:'+str(qi),valid,error,kind='integrity',danger=answer is not None)
        check('question_replays:'+str(qi),(item.get('inquiry_verification') or {}).get('valid') is True
              and (item.get('verification') or {}).get('valid') is True,kind='integrity')
        question_results.append({'index':qi,'expected_status':wanted['expected_status'],
            'actual_status':answer.get('status') if answer else None,'status_match':answer is not None and answer.get('status')==wanted['expected_status'],
            'independently_validated':valid})
    return {'id':case['id'],'family':case['family'],'category':case['category'],
            'fixed_status_case':expected['document_status'] is not None,'status':report['status'],
            'passed':all(c['passed'] for c in checks),'checks':checks,'unsafe':unsafe,
            'provenance_outcome':provenance,'questions':question_results,
            'declared_obligations':expected['obligations'],'raw_trait_observations':traits,
            'unvalidated_raw_trait_rows':traits['unresolved'],
            'interpretation_limit':'Compiler candidate enumeration is checked by separate exact runtime replay; this scorer does not prove all Arabic readings were enumerated.'}
