#!/usr/bin/env python3
"""Versioned continuation of the identical 24-case directed oracle.

No original-86 case, scorer debt policy, or holdout-v2 exception is consulted.
This is a transparent directed test after material freeze, not a random blind
sample. Every actual public API call is written to a canonical raw journal.
"""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime,timezone
from hashlib import sha256
import gzip
import importlib.util
import json
from pathlib import Path
import sys
import traceback

EXEC_DIR=Path(__file__).resolve().parent
HERE=EXEC_DIR.parent
ROOT=HERE.parents[2]
MATERIAL_SHA='78589ad292f747a27b76cf08c56848377f93fe370b6fa9f0229951fa8f443a3f'
RUNTIME_SHA='eda208c3e092a8185a3223ba8f0848ff6d0232aca3b8c3e94645482233d7dcb9'
spec=importlib.util.spec_from_file_location('completion_oracle_checks',HERE/'oracle_checks_v2.py')
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
E=S.E
VERSION='nabt.completion-directed-oracle-execution.v4'


def dump(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def file_row(path):
    raw=path.read_bytes()
    return {'path':str(path.relative_to(ROOT)),'bytes':len(raw),'sha256':sha256(raw).hexdigest()}


def load_material():
    payload=(HERE/'freeze.json').read_bytes();E.require(sha256(payload).hexdigest()==MATERIAL_SHA,'Oracle freeze changed')
    manifest=json.loads(payload)
    for item in manifest['files']:
        path=HERE/item['path'];raw=path.read_bytes()
        E.require(not Path(item['path']).is_absolute() and '..' not in Path(item['path']).parts,'Unsafe material path')
        E.require(len(raw)==item['bytes'] and sha256(raw).hexdigest()==item['sha256'],'Oracle material changed: '+item['path'])
    cases=json.loads((HERE/'cases.json').read_text());contexts=json.loads((HERE/'contexts.json').read_text())
    profiles=json.loads((HERE/'lexical_profiles.json').read_text())['profiles']
    E.require(len(cases['cases'])==24 and len({c['id'] for c in cases['cases']})==24,'Case inventory changed')
    E.require(sum(c['expected']['document_status'] is not None for c in cases['cases'])==22
              and sum(len(c['expected']['questions']) for c in cases['cases'])==29,'Declared denominators changed')
    for profile in profiles.values():
        E.require(sha256((HERE/profile['file']).read_bytes()).hexdigest()==profile['sha256'],'Raw teaching profile changed')
    return manifest,cases,contexts,profiles


def check_runner_freeze(path):
    raw=path.read_bytes();freeze=json.loads(raw)
    E.require(freeze['schema']=='nabt.completion-directed-runner-freeze.v4'
              and freeze['material_freeze_sha256']==MATERIAL_SHA and freeze['runtime_freeze_sha256']==RUNTIME_SHA,
              'Unapproved runner/material/runtime combination')
    for item in freeze['files']:
        E.require(not Path(item['path']).is_absolute() and '..' not in Path(item['path']).parts,'Unsafe runner path')
        E.require(file_row(ROOT/item['path'])==item,'Runner/dependency changed: '+item['path'])
    E.require(str(Path(__file__).relative_to(ROOT)) in {i['path'] for i in freeze['files']},'Runner not frozen')
    return {'path':str(path.relative_to(ROOT)),'sha256':sha256(raw).hexdigest(),'files':freeze['files']}


def capture(snapshot,output,material,runner):
    by_path={row['path']:row for row in snapshot['files']}
    for item in runner['files']:
        by_path.setdefault(item['path'],item)
    for path in (EXEC_DIR/'runner_freeze_v4_review3.json', ROOT/snapshot['runtime_freeze']):
        row=file_row(path);by_path.setdefault(row['path'],row)
    for name in ['freeze.json',*[item['path'] for item in material['files']]]:
        row=file_row(HERE/name);by_path.setdefault(row['path'],row)
    extended={**snapshot,'files':list(by_path.values())}
    extended['measured_snapshot_sha256']=E.digest(extended['files'])
    return extended,E.capture_code(extended,output)


def finish_journal(path,inventory):
    decoded=gzip.decompress(path.read_bytes());lines=decoded.splitlines(keepends=True)
    E.require(decoded.endswith(b'\n') and len(lines)==len(inventory),'Raw journal truncated')
    for index,(line,item) in enumerate(zip(lines,inventory)):
        value=json.loads(line)
        E.require(line==dump(value)+b'\n' and item['index']==index and item['bytes']==len(line)
                  and item['sha256']==sha256(line).hexdigest(),'Noncanonical or changed raw journal record')
    return {'path':str(path.relative_to(ROOT)),'sha256':sha256(path.read_bytes()).hexdigest(),
            'uncompressed_sha256':sha256(decoded).hexdigest(),'record_count':len(lines),
            'inventory':inventory,'inventory_sha256':E.digest(inventory)}


def execute(output_dir,runtime_freeze,runner_freeze):
    E.require(not any(n=='nabt' or n.startswith('nabt.') for n in sys.modules),'Use a fresh process before importing runtime')
    E.require(not output_dir.exists(),'Refusing to replace an execution directory')
    E.require(output_dir.is_relative_to(ROOT),'Output directory must be inside the repository for canonical inventory paths')
    E.require(sha256(runtime_freeze.read_bytes()).hexdigest()==RUNTIME_SHA,'Candidate runtime is not the approved freeze')
    material,cases,contexts,profiles=load_material();runner=check_runner_freeze(runner_freeze)
    snapshot=E.runtime_snapshot(runtime_freeze,ROOT)
    output_dir.mkdir(parents=True);output=output_dir/'result.json'
    measured,archive=capture(snapshot,output,material,runner)
    result={'schema':VERSION,'scorer':S.VERSION,'started_utc':datetime.now(timezone.utc).isoformat(),
        'material_freeze_sha256':MATERIAL_SHA,'runner':runner,'snapshot':measured,'code_archive':archive,
        'runtime_freeze_sha256':RUNTIME_SHA,'statistical_blind_sample_claimed':False,
        'scope':'24 directed authored cases: 22 fixed coverage/boundary obligations, 2 conditional provenance probes, 29 questions; old denominators/gold unchanged.',
        'cases':[],'execution_errors':[],'scoring_errors':[],'cross_case_checks':[],
        'strict_only':True,'regression_waiver_used':False}
    journal_path=output_dir/'raw.jsonl.gz';inventory=[];records={};models={};audits={};call_id=0
    sys.path.insert(0,str(ROOT/'src'))
    from nabt.corpus_evidence import learn_qac_lexicon
    from nabt.discourse import read_discourse,ask_discourse,verify_discourse,verify_discourse_answer
    E.verify_import_origins(ROOT)
    with gzip.open(journal_path,'wb') as journal:
        def log(value):
            line=dump(value)+b'\n';inventory.append({'index':len(inventory),'bytes':len(line),'sha256':sha256(line).hexdigest(),
                'kind':value['kind'],'case_id':value.get('case_id'),'call_id':value.get('call_id')})
            journal.write(line);journal.flush()
        def call(name,fn,*,cid=None,qi=None,public_inputs=None):
            nonlocal call_id
            call_id+=1;value={'kind':'public_api_call','call_id':call_id,'name':name,'case_id':cid,'question_index':qi,'inputs':public_inputs}
            try:
                returned=fn();value['returned']=returned
            except Exception as error:
                returned=None;value['error']={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
                result['execution_errors'].append({k:value[k] for k in ('call_id','name','case_id','question_index','error')})
            log(value);return returned
        # The model object is intentionally not serialized as an authority.
        # Its raw input and public summary are logged; all receipts replay raw.
        for key,profile in profiles.items():
            raw=(HERE/profile['file']).read_bytes();source_id='independent_oracle_lexical_'+key
            def acquire():
                models[key]=learn_qac_lexicon(raw,source_id=source_id)
                return models[key].summary()
            call('learn_qac_lexicon',acquire,public_inputs={'source_id':source_id,'raw_sha256':sha256(raw).hexdigest(),
                 'raw_hex':raw.hex(),'excluded_verses':[]})
            audits[key]=E.SourceAudit(raw,source_id=source_id)
        for case in cases['cases']:
            public=case['input'];cid=case['id'];context=contexts[public['context_id']];profile=public['lexical_profile']
            inputs={k:public[k] for k in ('text','source_id','scope')};inputs['context']=deepcopy(context)
            if profile not in models:
                record={'case_id':cid,'inputs':inputs,'profile':profile,'questions':[{} for _ in case['expected']['questions']],
                        'report':None,'errors':['MODEL_ACQUISITION_FAILED']}
                score=S.score_case(case,record,audits[profile]);records[cid]=record;result['cases'].append(score)
                log({'kind':'case_observation','case_id':cid,'record':record,'score':score});continue
            kwargs={'lexical_model':models[profile],'context':context,'source_id':inputs['source_id'],'scope':inputs['scope']}
            public_call={**inputs,'lexical_profile':profile,'model_summary':models[profile].summary()}
            record={'case_id':cid,'inputs':inputs,'profile':profile,'questions':[]}
            report=call('read_discourse',lambda:read_discourse(inputs['text'],**kwargs),cid=cid,public_inputs=public_call)
            record['report']=report
            if report is not None:
                record['verification']=call('verify_discourse',lambda:verify_discourse(report,text=inputs['text'],**kwargs),
                    cid=cid,public_inputs={**public_call,'certificate_report_id':report.get('report_id')})
            for qi,wanted in enumerate(case['expected']['questions']):
                question=wanted['text'];entry={}
                entry['answer']=call('ask_discourse',lambda:ask_discourse(inputs['text'],question,**kwargs),cid=cid,qi=qi,
                    public_inputs={**public_call,'question':question})
                entry['inquiry']=call('read_discourse',lambda:read_discourse(question,**{**kwargs,'source_id':'question'}),cid=cid,qi=qi,
                    public_inputs={**public_call,'text':question,'source_id':'question'})
                if entry['inquiry'] is not None:
                    entry['inquiry_verification']=call('verify_discourse',lambda:verify_discourse(entry['inquiry'],text=question,
                        **{**kwargs,'source_id':'question'}),cid=cid,qi=qi,public_inputs={'certificate_report_id':entry['inquiry']['report_id'],
                        **public_call,'text':question,'source_id':'question'})
                if entry['answer'] is not None:
                    entry['verification']=call('verify_discourse_answer',lambda:verify_discourse_answer(entry['answer'],text=inputs['text'],
                        question=question,**kwargs),cid=cid,qi=qi,public_inputs={**public_call,'question':question,
                        'certificate_answer_id':entry['answer']['answer_id']})
                record['questions'].append(entry)
            try:
                score=S.score_case(case,record,audits[profile])
            except Exception as error:
                finding={'case_id':cid,'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
                result['scoring_errors'].append(finding)
                score={'id':cid,'family':case['family'],'category':case['category'],
                    'fixed_status_case':case['expected']['document_status'] is not None,'passed':False,'unsafe':[],
                    'checks':[{'check':'scorer_completed','kind':'integrity','passed':False,'detail':finding}],
                    'questions':[],'provenance_outcome':'unresolved_independent_review' if case['category']=='provenance_probe' else None}
            records[cid]=record;result['cases'].append(score)
            log({'kind':'case_observation','case_id':cid,'record':record,'score':score})
            print(json.dumps({'id':cid,'passed':score['passed'],'status':report.get('status') if report else None,
                              'failed':[x['check'] for x in score['checks'] if not x['passed']]},ensure_ascii=False),flush=True)
        for source_id,other_id in [('P04','P05'),('P05','P04')]:
            record=records[source_id];other=records[other_id];inputs=record['inputs']
            if record['profile'] not in models:
                record['changed_speaker_replay']={'report':None,'answer':None};continue
            kwargs={'lexical_model':models[record['profile']],'context':other['inputs']['context'],
                    'source_id':inputs['source_id'],'scope':inputs['scope']}
            verify=None;answer_verify=None
            if record['report'] is not None:
                verify=call('verify_discourse_changed_speaker',lambda:verify_discourse(record['report'],text=inputs['text'],**kwargs),
                    cid=source_id,public_inputs={**inputs,'context':other['inputs']['context'],'certificate_report_id':record['report']['report_id']})
            answer=record['questions'][0].get('answer')
            question=next(c for c in cases['cases'] if c['id']==source_id)['expected']['questions'][0]['text']
            if answer is not None:
                answer_verify=call('verify_answer_changed_speaker',lambda:verify_discourse_answer(answer,text=inputs['text'],question=question,**kwargs),
                    cid=source_id,public_inputs={**inputs,'context':other['inputs']['context'],'question':question,'certificate_answer_id':answer['answer_id']})
            record['changed_speaker_replay']={'report':verify,'answer':answer_verify}
        byid={row['id']:row for row in result['cases']}
        checks=[('X01',all(byid[x]['passed'] for x in ('G01','G05','G06'))),
                ('X02',byid['N01']['passed'] and byid['N03']['provenance_outcome'] in ('correct_abstention','checked_derivation'))]
        same=records['P04']['inputs']['text']==records['P05']['inputs']['text']
        actor=True
        for cid,wanted in [('P04','malik'),('P05','hind')]:
            report=records[cid]['report'];replay=records[cid]['changed_speaker_replay']
            actor=actor and report is not None and any(c['predicate_kind']=='event' and c['predicate']=='أَكْرَمَ'
                and c['args']==[wanted,'khalid'] for c in report['claims'])
            actor=actor and replay['report'] is not None and replay['report'].get('valid') is False
            actor=actor and replay['answer'] is not None and replay['answer'].get('valid') is False
        checks.append(('X03',same and actor))
        result['cross_case_checks']=[{'id':key,'passed':bool(value)} for key,value in checks]
        log({'kind':'cross_case_observations','case_id':None,'checks':result['cross_case_checks'],
             'changed_speaker':{key:records[key]['changed_speaker_replay'] for key in ('P04','P05')}})
        # Mutations use observed certificates when available. An unexercised
        # precondition remains explicit and cannot become a language pass.
        from_path=HERE/'oracle_mutations_v2.py'
        mspec=importlib.util.spec_from_file_location('completion_oracle_mutations',from_path)
        M=importlib.util.module_from_spec(mspec);mspec.loader.exec_module(M)
        # Use the exact canonical case records, before the separate context-change
        # observations were attached in memory. This is the same input to the
        # preserved v2 postreview mutations; no public payload is removed.
        mutation_records={cid:{k:v for k,v in record.items() if k!='changed_speaker_replay'}
                          for cid,record in records.items()}
        result['mutation_checks']=M.run(mutation_records,audits,log)
    result['raw_journal']=finish_journal(journal_path,inventory)
    result['public_api_calls']=call_id
    after=E.runtime_snapshot(runtime_freeze,ROOT);runner_after=check_runner_freeze(runner_freeze)
    result['runtime_unchanged']=after==snapshot
    result['runner_and_helpers_unchanged']=runner_after==runner
    result['snapshot_after']=after
    load_material()
    fixed=[c for c in result['cases'] if c['fixed_status_case']];probes=[c for c in result['cases'] if not c['fixed_status_case']]
    result['fixed_cases']={'total':22,'passed':sum(c['passed'] for c in fixed),'failed':sum(not c['passed'] for c in fixed)}
    result['conditional_provenance']={'total':2,'outcomes':{c['id']:c['provenance_outcome'] for c in probes},
        'not_counted_as_language_coverage':True}
    questions=[q for c in result['cases'] for q in c.get('questions',[])]
    result['questions']={'total':29,'observed':len(questions),'status_matches':sum(q['status_match'] for q in questions),
                        'independently_validated':sum(q['independently_validated'] for q in questions)}
    result['categories']={category:{'total':sum(c['category']==category for c in result['cases']),
        'passed':sum(c['category']==category and c['passed'] for c in result['cases'])}
        for category in sorted({c['category'] for c in result['cases']})}
    result['unsafe_check_failures']=[{'id':c['id'],'check':name} for c in result['cases'] for name in c['unsafe']]
    result['independent_integrity_failures']=[{'id':c['id'],'check':x['check'],'detail':x.get('detail')}
        for c in result['cases'] for x in c['checks'] if x['kind'] in ('integrity','execution') and not x['passed']]
    result['measurement_valid']=not(result['execution_errors'] or result['scoring_errors'] or result['independent_integrity_failures']
        or any(m['outcome']=='ERROR' for m in result['mutation_checks']))
    result['strict_pass']=bool(result['measurement_valid'] and result['runtime_unchanged'] and result['runner_and_helpers_unchanged']
        and all(c['passed'] for c in result['cases']) and all(x['passed'] for x in result['cross_case_checks'])
        and all(x['outcome']=='PASS' for x in result['mutation_checks']))
    result['finished_utc']=datetime.now(timezone.utc).isoformat()
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'output':str(output),'fixed_cases':result['fixed_cases'],'questions':result['questions'],
        'measurement_valid':result['measurement_valid'],'strict_pass':result['strict_pass']},ensure_ascii=False),flush=True)
    return 0 if result['strict_pass'] else 1


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--runtime-freeze',type=Path,default=ROOT/'evidence/arabic_completion_v4/code_freeze_v2.json')
    p.add_argument('--runner-freeze',type=Path,default=EXEC_DIR/'runner_freeze_v4_review3.json')
    args=p.parse_args();raise SystemExit(execute(args.output_dir.resolve(),args.runtime_freeze.resolve(),args.runner_freeze.resolve()))
