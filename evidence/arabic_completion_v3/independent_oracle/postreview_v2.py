#!/usr/bin/env python3
"""A pinned post-review rescore of the preserved first 24-case observation.

No runtime prediction or verification is invoked. The exact saved public calls
and their frozen checker/runtime inventories are checked before rescoring.
Only the documented occurrence adapter may change the six integrity results.
The resulting coverage failures remain failures; this is not a blind rerun.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
from hashlib import sha256
import gzip
import importlib.util
import json
from pathlib import Path
import sys
import tarfile

HERE=Path(__file__).resolve().parent

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

R=module('postreview_original_runner','run_oracle_v1.py');E=R.E
S=module('postreview_corrected_scorer','oracle_checks_v2.py')
M=module('postreview_corrected_mutations','oracle_mutations_v2.py')
FIRST_RESULT='3a8fe4d22da4ab2c0ab3e26060d5b1a9c3ba5c488b049363473f920f8a8a0159'
FIRST_RAW='d401000ab9334c094064d3845abd6df659cdd2db8268a249ea9b67e5699d5ac0'
RUNNER='2555b69d676aaf9fd9e374ca16e6b422799f1f16c366d0a3af9f9cc4450bc384'
AFFECTED={'P01','P02','P03','P04','P05','P06'}
ALLOWED_CHECK='connected_partition_and_profiles'
NEW_FILES=('oracle_checks_v2.py','oracle_mutations_v2.py','postreview_v2.py',
           'test_postreview_v2.py','postreview_erratum_v2.json','postreview_tests_v2.log',
           'run_regression_v2.py','REGRESSION_CONTRACT_v2.md')


def current_new_inventory():return [R.file_row(HERE/name) for name in NEW_FILES]


def snapshot_equal(current,saved):
    """Relocate exactly one absolute metadata path; preserve typed bytes/fields."""
    if (type(current) is not dict or type(saved) is not dict or
            type(current.get('runtime_root')) is not str or type(saved.get('runtime_root')) is not str or
            not Path(current['runtime_root']).is_absolute() or not Path(saved['runtime_root']).is_absolute()):
        return False
    return E.wire(current)==E.wire({**saved,'runtime_root':current['runtime_root']})


def checked_inputs(result_path,raw_path):
    baseline_result=HERE/'first_run_v1/result.json';baseline_raw=HERE/'first_run_v1/raw.jsonl.gz'
    E.require(sha256(baseline_result.read_bytes()).hexdigest()==FIRST_RESULT,'Preserved first result changed')
    E.require(sha256(baseline_raw.read_bytes()).hexdigest()==FIRST_RAW,'Preserved first raw observations changed')
    baseline=json.loads(baseline_result.read_text());original=json.loads(result_path.read_text());R.load_material()
    E.require(set(original)==set(baseline),'Fresh result added or omitted result fields')
    for key in ('schema','scorer','scope','strict_only','regression_waiver_used','strict_pass','measurement_valid',
                'fixed_cases','conditional_provenance','questions','cross_case_checks','unsafe_check_failures'):
        E.require(E.wire(original[key])==E.wire(baseline[key]),'Fresh original metadata/outcome differs: '+key)
    runner=R.check_runner_freeze(HERE/'runner_freeze_v1.json')
    E.require(runner['sha256']==RUNNER and original['runner']==runner,'First runner identity changed')
    E.require(original['material_freeze_sha256']==R.MATERIAL_SHA and original['runtime_freeze_sha256']==R.RUNTIME_SHA
              and original['runtime_unchanged'] is True and original['runner_and_helpers_unchanged'] is True,
              'Original runtime/material/helper pins are incomplete')
    E.require(not original['execution_errors'] and not original['scoring_errors'],'An execution/scoring exception cannot be erased')
    current=E.runtime_snapshot(R.ROOT/'evidence/arabic_completion_v3/code_freeze_v1.json',R.ROOT)
    # The absolute checkout location is metadata. All identities, files,
    # bytes, hashes and relative inventory paths still have to agree.
    E.require(snapshot_equal(current,original['snapshot_after']),
              'Current runtime/checkers differ from the measured inventory')
    inventory=R.finish_journal(raw_path,original['raw_journal']['inventory'])
    E.require(all(inventory[k]==original['raw_journal'][k] for k in inventory if k!='path'),'Raw journal identity changed')
    E.require(inventory['uncompressed_sha256']==baseline['raw_journal']['uncompressed_sha256']
              and inventory['inventory_sha256']==baseline['raw_journal']['inventory_sha256'],
              'Fresh raw public-call payloads or ordered observations differ from the preserved first measurement')
    archive=result_path.parent/original['code_archive']['filename']
    E.require(sha256(archive.read_bytes()).hexdigest()==original['code_archive']['sha256'],'Measured code archive changed')
    by_path={item['path']:item for item in original['snapshot']['files']}
    E.require(E.wire(original['snapshot']['files'])==E.wire(baseline['snapshot']['files']),'Measured code/material inventory differs')
    with tarfile.open(archive,'r:gz') as saved:
        members=saved.getmembers()
        E.require(len(members)==len(by_path) and {m.name for m in members}==set(by_path) and all(m.isfile() for m in members),
                  'Measured archive inventory differs')
        for member in members:
            data=saved.extractfile(member).read();item=by_path[member.name]
            E.require(len(data)==item['bytes'] and sha256(data).hexdigest()==item['sha256'],'Measured archive member changed')
    lines=[json.loads(line) for line in gzip.decompress(raw_path.read_bytes()).splitlines()]
    calls=[x for x in lines if x['kind']=='public_api_call']
    E.require([x['call_id'] for x in calls]==list(range(1,172)) and original['public_api_calls']==171,'Public call inventory incomplete')
    E.require(all('error' not in x for x in calls),'Retained call contains an execution failure')
    counts=Counter(x['name'] for x in calls)
    E.require(counts=={'learn_qac_lexicon':3,'read_discourse':53,'verify_discourse':53,'ask_discourse':29,
        'verify_discourse_answer':29,'verify_discourse_changed_speaker':2,'verify_answer_changed_speaker':2},'API inventory changed')
    for call in calls:
        if call['name'].startswith('verify_'):
            expected=False if 'changed_speaker' in call['name'] else True
            E.require(call['returned'].get('valid') is expected,'Saved replay does not have the required outcome')
    observed=[x for x in lines if x['kind']=='case_observation'];records={x['case_id']:x['record'] for x in observed}
    _,material,contexts,profiles=R.load_material()
    E.require([x['case_id'] for x in observed]==[c['id'] for c in material['cases']] and len(records)==24,
              'Case observations omitted, repeated or reordered')
    audits={key:E.SourceAudit((HERE/p['file']).read_bytes(),source_id='independent_oracle_lexical_'+key)
            for key,p in profiles.items()}
    for c,x in zip(material['cases'],observed):
        original_input=c['input'];record=x['record'];expected_input={k:original_input[k] for k in ('text','source_id','scope')}
        expected_input['context']=contexts[original_input['context_id']]
        E.require(E.wire(record['inputs'])==E.wire(expected_input) and record['profile']==original_input['lexical_profile'],
                  'Observation input changed the frozen material')
        old_score=R.S.score_case(c,record,audits[record['profile']])
        E.require(E.wire(old_score)==E.wire(x['score'])==E.wire(next(s for s in original['cases'] if s['id']==c['id'])),
                  'Original scorer does not reproduce its preserved score')
    errors=original['independent_integrity_failures']
    E.require(len(errors)==6 and {e['id'] for e in errors}==AFFECTED and all(e['check']==ALLOWED_CHECK and
        e['detail']['examined']==1 and e['detail']['licensed']==0 and len(e['detail']['errors'])==1 and
        e['detail']['errors'][0]['message']=="'identity'" for e in errors),'First failure inventory exceeds the documented adapter defect')
    return original,records,material,audits,current,runner,inventory


def review(result_path,raw_path,output_dir):
    E.require(not output_dir.exists(),'Refusing to replace a review')
    before=current_new_inventory();freeze=json.loads((HERE/'postreview_freeze_v2.json').read_text())
    E.require(E.wire(freeze['files'])==E.wire(before) and freeze['first_result_sha256']==FIRST_RESULT and freeze['runner_freeze_sha256']==RUNNER,
              'Post-review code inventory changed')
    original,records,material,audits,current,runner,inventory=checked_inputs(result_path,raw_path)
    scores=[];changes=[]
    for case in material['cases']:
        old=next(row for row in original['cases'] if row['id']==case['id'])
        new=S.score_case(case,records[case['id']],audits[records[case['id']]['profile']]);scores.append(new)
        old_checks={x['check']:x for x in old['checks']};new_checks={x['check']:x for x in new['checks']}
        E.require(set(old_checks)==set(new_checks),'Scorer added or removed an oracle check')
        changed=[key for key in old_checks if E.wire(old_checks[key])!=E.wire(new_checks[key])]
        E.require(changed==([ALLOWED_CHECK] if case['id'] in AFFECTED else []),'An unrelated check changed: '+case['id'])
        if changed:
            E.require(new_checks[ALLOWED_CHECK]['passed'] is True and new_checks[ALLOWED_CHECK]['detail']['licensed']==0
                and not new_checks[ALLOWED_CHECK]['detail']['errors'],'Corrected partition did not validate, or licensed profile was invented')
            changes.append({'id':case['id'],'check':ALLOWED_CHECK,'before':old_checks[ALLOWED_CHECK],
                            'after':new_checks[ALLOWED_CHECK],'case_pass_before':old['passed'],'case_pass_after':new['passed']})
        E.require(new['questions']==old['questions'] and new['raw_trait_observations']==old['raw_trait_observations']
                  and new['provenance_outcome']==old['provenance_outcome'],'Questions or provenance silently changed')
    E.require([row['id'] for row in scores if row['passed'] and not next(x for x in original['cases'] if x['id']==row['id'])['passed']]==['P03'],
              'A positive coverage miss was converted to success')
    output_dir.mkdir(parents=True);mutations=[]
    def log(value):mutations.append(value)
    outcomes=M.run(records,audits,log)
    journal=b''.join(R.dump(x)+b'\n' for x in mutations)
    (output_dir/'mutations.jsonl.gz').write_bytes(gzip.compress(journal,mtime=0))
    oldmut={x['id']:x['outcome'] for x in original['mutation_checks']};newmut={x['id']:x['outcome'] for x in outcomes}
    E.require([key for key in oldmut if oldmut[key]!=newmut[key]]==['V-P02'] and oldmut['V-P02']=='UNEXERCISED'
              and newmut['V-P02']=='PASS','A non-partition mutation outcome changed')
    fixed=[x for x in scores if x['fixed_status_case']]
    integrity=[{'id':c['id'],'check':x['check'],'detail':x.get('detail')} for c in scores for x in c['checks']
               if x['kind'] in ('integrity','execution') and not x['passed']]
    result={'schema':'nabt.completion-oracle-postreview.v2','reviewed_utc':datetime.now(timezone.utc).isoformat(),
        'basis':'POSTREVIEW_OF_IDENTICAL_SAVED_CALLS_NOT_A_NEW_BLIND_RUN','new_runtime_calls':0,
        'original_result':{'path':str(result_path.relative_to(R.ROOT)),'sha256':sha256(result_path.read_bytes()).hexdigest()},
        'preserved_first_result_sha256':FIRST_RESULT,'preserved_first_raw_sha256':FIRST_RAW,
        'identical_raw_public_call_payloads_and_ordered_observations':True,
        'original_raw':inventory,'material_freeze_sha256':R.MATERIAL_SHA,'runtime_freeze_sha256':R.RUNTIME_SHA,
        'runner_freeze_sha256':RUNNER,'review_files_before':before,'cases':scores,'check_changes':changes,
        'fixed_cases':{'total':22,'passed':sum(x['passed'] for x in fixed),'failed':sum(not x['passed'] for x in fixed)},
        'conditional_provenance':original['conditional_provenance'],'questions':original['questions'],
        'cross_case_checks':original['cross_case_checks'],'mutation_checks':outcomes,
        'mutation_journal_sha256':sha256(journal).hexdigest(),
        'unsafe_check_failures':[{'id':x['id'],'check':name} for x in scores for name in x['unsafe']],
        'independent_integrity_failures':integrity,'execution_errors':[],'scoring_errors':[],
        'measurement_valid':not integrity and not any(m['outcome']=='ERROR' for m in outcomes),
        'runtime_unchanged':E.runtime_snapshot(R.ROOT/'evidence/arabic_completion_v3/code_freeze_v1.json',R.ROOT)==current,
        'runner_and_helpers_unchanged':R.check_runner_freeze(HERE/'runner_freeze_v1.json')==runner,
        'review_files_after':current_new_inventory(),'review_valid':True,
        'strict_pass':False,'regression_waiver_used':False,
        'limits':['Corrects only six erroneous occurrence-schema alarms; preserves all other failures.',
                  'All attached candidates remain unlicensed; no positive host/suffix profile authority is inferred.',
                  'N06 remains unresolved independent review; neither tracing probe is counted as a language success.',
                  'Finite authored coverage and saved replay evidence are not universal Arabic understanding.']}
    E.require(result['review_files_after']==before and result['runtime_unchanged'] and result['runner_and_helpers_unchanged'],
              'Code or runtime changed during post-review')
    expected_failures={c['id']:sorted(x['check'] for x in c['checks'] if not x['passed']
        and not(c['id'] in AFFECTED and x['check']==ALLOWED_CHECK)) for c in original['cases']}
    actual_failures={c['id']:sorted(x['check'] for x in c['checks'] if not x['passed']) for c in scores}
    result['regression_gate']={
        'schema':'nabt.completion-same-frozen-trace-regression.v1',
        'gate_mode':'EXACT_SAME_TRACE_WITH_DOCUMENTED_OCCURRENCE_ADAPTER_CORRECTION',
        'strict_coverage_success':False,
        'gate_pass':bool(result['measurement_valid'] and not result['unsafe_check_failures']
            and actual_failures==expected_failures and result['fixed_cases']=={'total':22,'passed':14,'failed':8}
            and result['questions']=={'total':29,'observed':29,'status_matches':19,'independently_validated':29}
            and result['conditional_provenance']['outcomes']=={'N03':'correct_abstention','N06':'unresolved_independent_review'}
            and {key:value for key,value in newmut.items() if value!='PASS'}=={
                'V-T01':'UNEXERCISED','V-T05':'UNEXERCISED','V-P01':'UNEXERCISED',
                'V-P04':'UNEXERCISED','V-P05':'UNEXERCISED'}),
        'expected_failure_inventory':expected_failures,
        'actual_failure_inventory':actual_failures,
        'ordinary_arabic_completeness_established':False,
        'coverage_failures_remain_failures':True}
    (output_dir/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'output':str(output_dir/'review.json'),'fixed_cases':result['fixed_cases'],
        'questions':result['questions'],'measurement_valid':result['measurement_valid'],
        'review_valid':result['review_valid'],'strict_pass':False},ensure_ascii=False))
    # This exit status reports a completed valid review, not a coverage gate.
    return 0 if result['review_valid'] and result['measurement_valid'] else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--result',type=Path,default=HERE/'first_run_v1/result.json')
    parser.add_argument('--raw',type=Path,default=HERE/'first_run_v1/raw.jsonl.gz')
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();sys.exit(review(args.result.resolve(),args.raw.resolve(),args.output_dir.resolve()))
