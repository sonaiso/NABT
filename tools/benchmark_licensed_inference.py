"""Independent bounded diagnostic; failures remain visible in a fixed denominator."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
from tools.licensed_inference_benchmark_adapter import build_request,execute_request,CapabilityUnavailable

GOLD_PATH=ROOT/'evidence/licensed_inference_v1/independent_gold.json'
GOLD_SHA256='4aae6aa0054d42820626f72fa5194d16902544e86629d1a57f69b52a971707af'
STATES={'SUPPORTED':(True,False),'REFUTED':(False,True),'CONFLICT':(True,True),'UNKNOWN':(False,False)}


def digest(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()


def load_gold()->dict[str,Any]:
    if digest(GOLD_PATH)!=GOLD_SHA256:raise ValueError('independent gold hash mismatch')
    return json.loads(GOLD_PATH.read_text())


def check(name,actual,expected,measured=True):
    exact=type(actual) is type(expected) and actual==expected
    return {'name':name,'actual':actual,'expected':expected,'outcome':('PASS' if exact else 'FAIL') if measured else 'UNMEASURED'}


def result_kind(checks):
    outcomes={c['outcome'] for c in checks}
    return 'FAIL' if 'FAIL' in outcomes else 'UNMEASURED' if 'UNMEASURED' in outcomes else 'PASS'


def observe(raw:dict[str,Any],request:dict[str,Any])->dict[str,Any]:
    out={k:raw[k] for k in ('status','world_truth_established','all_arabic_complete') if k in raw}
    if request['mode']=='aggregate_fixture':
        result=raw.get('aggregation_calculation',{});rows=raw.get('direct_fixture_rows',[])
        aggregate=result.get('aggregate',{});status=result.get('status')
        diversity=len({(r['positive'],r['negative']) for r in rows})
        out['native_aggregate_status']=status
        out['per_reading_status_diversity']=diversity
        # Gold's DISAGREEMENT means differing reading statuses, including an
        # unknown reading. Runtime reserves that word for opposite signs.
        # DEFER alone is insufficient: equal unclean readings stay DEFER.
        out['aggregate']='DISAGREEMENT' if status=='DEFER' and diversity>1 else status
        if 'within_reading_conflict' in aggregate:out['within_reading_conflict']=aggregate['within_reading_conflict']
        if 'skeptical_clean_positive' in aggregate and 'credulous_negative' in aggregate:
            out['unanimous_consistent_support']=aggregate['skeptical_clean_positive'] and not aggregate['credulous_negative']
        if all(k in aggregate for k in ('skeptical_positive','skeptical_negative','skeptical_clean_positive','skeptical_clean_negative')):
            out['empty_readings_not_consensus']=not rows and status=='UNKNOWN' and not any(aggregate[k] for k in ('skeptical_positive','skeptical_negative','skeptical_clean_positive','skeptical_clean_negative'))
        out['all_readings_retained']=len(rows)==len(request['readings']) and raw.get('submitted_reading_ids')==[r['id'] for r in request['readings']]
        return out
    status=raw.get('status')
    if status in set(STATES)|{'DEFER','DISAGREEMENT'}:out['target']=status
    if 'parse_status' in raw:
        out['full_licensed_reading']=raw['parse_status']=='CHECKED_COMPLETE_READING'
    elif (raw.get('verified') is False and raw.get('native_checked') is False
          and raw.get('all_readings_complete') is False and raw.get('readings')==[]):
        # A pre-parse resource stop explicitly reports that it produced no
        # checked reading. This is not a linguistic rejection of the text.
        out['full_licensed_reading']=False
    if raw.get('parse_reason')=='UNRESOLVED_REFERENCE':out['reference_resolved']=False
    elif raw.get('parse_status')=='CHECKED_COMPLETE_READING':out['reference_resolved']=True
    if 'parse_reason' in raw:out['outside_declared_surface_domain']=raw['parse_reason']=='OUTSIDE_FRAGMENT'
    if 'closures_checked' in raw and 'all_readings_complete' in raw:
        out['complete_closure']=raw['closures_checked'] and raw['all_readings_complete']
    if isinstance(raw.get('binding'),dict):
        binding=raw['binding'];out['identity_exact']=all(binding.get(k)==request[k] for k in ('source_id','revision','scope','time') if k in request)
        if 'native_scope' in binding:out['identity']=binding['native_scope']
    if isinstance(raw.get('source'),dict) and isinstance(raw.get('query'),dict):
        checks=[]
        for name,key in (('source','source_text'),('query','query_text')):
            text=request[key];entry=raw[name]
            if not isinstance(text,str):checks.append(False);continue
            data=text.encode('utf-8');checks.append(entry.get('raw_text')==text and entry.get('bytes')==len(data) and entry.get('sha256')==hashlib.sha256(data).hexdigest())
        out['exact_source_roundtrip']=all(checks)
    if 'readings' in raw:
        locations=set()
        def visit(value):
            if isinstance(value,dict):
                if value.get('predicate')=='سار':
                    for part in value.get('arguments',[]):
                        if part in ('أمامك','أمامك_خلف_الدار'):locations.add('أمامك')
                        if part in ('خلف_الدار','أمامك_خلف_الدار'):locations.add('خلف الدار')
                for nested in value.values():visit(nested)
            elif isinstance(value,list):
                for nested in value:visit(nested)
        for reading in raw['readings']:visit(reading.get('clauses',[]))
        out['preserve_locations']=sorted(locations)
    return out


def evaluate_case(case,observed,previous):
    checks=[]
    for key,wanted in case['expected'].items():
        if key in ('same_target_as','same_aggregate_as'):
            field='target' if key=='same_target_as' else 'aggregate'
            reference=previous.get(wanted,{})
            checks.append(check(key,observed.get(field),reference.get(field),field in observed and field in reference))
        elif key=='different_identity_from':
            reference=previous.get(wanted,{})
            checks.append(check(key,observed.get('identity')!=reference.get('identity'),True,'identity' in observed and 'identity' in reference))
        elif key=='desired_target':
            checks.append(check('desired_target',observed.get('target'),wanted,'target' in observed))
        else:checks.append(check(key,observed.get(key),wanted,key in observed))
    return checks


def summary(rows):
    total=Counter(r['outcome'] for r in rows);families=defaultdict(Counter)
    assertions=[];false_literals=missing_literals=0
    for row in rows:
        families[row['family']][row['outcome']]+=1
        for c in row['checks']:
            if c['name'] in ('target','desired_target') and c['outcome']!='UNMEASURED':
                assertions.append(c)
                actual=STATES.get(c['actual']);expected=STATES.get(c['expected'])
                if actual is not None and expected is not None:
                    false_literals+=sum(a and not e for a,e in zip(actual,expected))
                    missing_literals+=sum(e and not a for a,e in zip(actual,expected))
    auth=[c for row in rows for c in row['checks'] if c['name'] in ('world_truth_established','all_arabic_complete')]
    return {'cases':len(rows),'pass':total['PASS'],'fail':total['FAIL'],'unmeasured':total['UNMEASURED'],'executed':sum(r['executed'] for r in rows),'families':{k:dict(v) for k,v in families.items()},'target_observations':{'measured':len(assertions),'exact_matches':sum(c['outcome']=='PASS' for c in assertions),'false_supported_literals':false_literals,'missing_supported_literals':missing_literals},'authority':{'obligations':len(auth),'measured':sum(c['outcome']!='UNMEASURED' for c in auth),'overclaims':sum(c['outcome']=='FAIL' for c in auth),'unmeasured':sum(c['outcome']=='UNMEASURED' for c in auth)}}


def snapshot()->dict[str,Any]:
    modules={}
    for module in tuple(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if not name:continue
        p=Path(name)
        if not p.is_absolute():
            # Virtual modules can advertise e.g. "_ops.py". The working
            # directory is not provenance; only an absolute origin may bind it.
            origin=getattr(getattr(module,'__spec__',None),'origin',None)
            if not origin or not Path(origin).is_absolute():continue
            p=Path(origin)
        p=p.resolve()
        if p.suffix=='.py' and p.is_relative_to(ROOT):modules[str(p.relative_to(ROOT))]=digest(p)
    binary=(ROOT/'formal/.lake/build/bin/licensedInference').resolve()
    toolchain=ROOT/'formal/lean-toolchain'
    source_manifest=ROOT/'evidence/licensed_inference_v1/source_links.json'
    linked=json.loads(source_manifest.read_text())
    source_paths=[source_manifest]+[ROOT/s['local_path'] for s in linked['sources']]+[ROOT/s['path'] for s in linked['source_registries']]
    return {'repository_python':dict(sorted(modules.items())),'gold':{'path':str(GOLD_PATH.relative_to(ROOT)),'sha256':digest(GOLD_PATH)},'source_inputs':{str(p.relative_to(ROOT)):digest(p) for p in source_paths},'native':{'path':str(binary),'sha256':digest(binary) if binary.is_file() else None},'toolchain':{'sha256':digest(toolchain),'contents':toolchain.read_text().strip()},'python':{'path':sys.executable,'sha256':digest(Path(sys.executable).resolve()),'version':sys.version}}


def integrity(before,after):
    changed=[k for k in sorted(set(before)|set(after)) if before.get(k)!=after.get(k)]
    native=bool(before.get('native',{}).get('sha256') and after.get('native',{}).get('sha256'))
    return {'valid':not changed and native,'stable':not changed,'native_present':native,'changed_sections':changed}


def contracts(rows,counts,evidence):
    primary=[r for r in rows if r['mode']=='evaluate']
    auth=[c for r in primary for c in r['checks'] if c['name'] in ('world_truth_established','all_arabic_complete')]
    native_missing=[r['id'] for r in primary
                    if r.get('observed',{}).get('full_licensed_reading') is True
                    and r.get('raw_result',{}).get('status')!='RESOURCE_EXHAUSTED'
                    and not all(r.get('raw_result',{}).get(k) is True for k in ('native_checked','closures_checked','all_readings_complete'))]
    checks={'execution_identity_stable':evidence['valid'],'all_38_cases_handled':len(rows)==38 and all(r['executed'] for r in rows),'primary_authority_observed':len(auth)==64 and all(c['outcome']!='UNMEASURED' for c in auth),'no_authority_overclaim':counts['authority']['overclaims']==0,'no_false_supported_literals':counts['target_observations']['false_supported_literals']==0,'native_checker_for_complete_readings':not native_missing}
    return {'passed':all(checks.values()),'checks':checks,'scope':'Integrity and authority contracts only; 38-case diagnostic denominator and every unsupported or unmeasured capability remain visible.'}


def run(execute=execute_request):
    for name in ('tools.licensed_inference','tools.licensed_inference.parser','tools.licensed_inference.sources'):
        importlib.import_module(name)
    gold=load_gold();before=snapshot();rows=[];observations={}
    for case in gold['cases']:
        request=build_request(case);unchanged=deepcopy(request)
        try:
            raw=execute(request)
            if not isinstance(raw,dict):raise TypeError('runtime result must be an object')
            observed=observe(raw,request);checks=evaluate_case(case,observed,observations)
            row={'id':case['id'],'family':case['family'],'mode':request['mode'],'executed':True,'outcome':result_kind(checks),'checks':checks,'raw_result':raw,'observed':observed,'input_unchanged':request==unchanged}
            observations[case['id']]=observed
        except Exception as exc:
            row={'id':case['id'],'family':case['family'],'mode':request['mode'],'executed':False,'outcome':'UNMEASURED','checks':[check(k,None,v,False) for k,v in case['expected'].items()],'error':{'type':type(exc).__name__,'message':str(exc)},'input_unchanged':request==unchanged}
        rows.append(row)
    after=snapshot();stable=integrity(before,after);counts=summary(rows)
    return {'schema':'nabt.licensed-inference.independent-result.v1','measured_at_utc':datetime.now(timezone.utc).isoformat(),'gold_sha256':GOLD_SHA256,'summary':counts,'scope':'Finite independent-agent diagnostic, not external human evaluation or all-Arabic completeness.','execution_evidence':{'before':before,'after':after,'integrity':stable},'contract_gate':contracts(rows,counts,stable),'environment':{'platform':platform.platform()},'rows':rows}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--require-contracts',action='store_true');args=p.parse_args();report=run();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');code=0 if not args.require_contracts or report['contract_gate']['passed'] else 2
    print(json.dumps({'summary':report['summary'],'contract_gate':report['contract_gate'],'exit_status':code,'exit_zero_means':'Diagnostic executed; with --require-contracts, the listed execution/authority contracts also passed. Does not mean all 38 diagnostic cases passed.'},ensure_ascii=False,indent=2));return code

if __name__=='__main__':raise SystemExit(main())
