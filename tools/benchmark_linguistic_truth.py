"""Evaluate frozen independent diagnostics without changing their denominator.

Unknown on a desired positive reading is an acquisition miss. Missing observation
capabilities are unmeasured. Source-understanding/audit claims require their own
observable fields and are never inferred from acquisition or file hashes.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from copy import deepcopy
from dataclasses import asdict,is_dataclass
from datetime import datetime,timezone
import hashlib
import importlib
import json
from pathlib import Path
import platform
import sys
import unicodedata
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))

from tools.linguistic_truth_benchmark_adapter import build_request,execute_request,run_ranking_scenario

GOLD_SHA256='8d980b7ae2611e9a8157db17a8218c7a9305d4ec6c59b06a85f84c9ede6bf86a'
GOLD_PATH=ROOT/'evidence/linguistic_truth_v1/benchmark_gold.json'


def evidence_snapshot()->dict[str,Any]:
    """Hash the imported runtime closure and exact execution inputs, not reports."""
    from tools.linguistic_truth.marked_forms import REVIEW_PATH, _load_review
    marked_review = _load_review(ROOT)
    modules={}
    for name,module in tuple(sys.modules.items()):
        filename=getattr(module,'__file__',None)
        if not filename:continue
        path=Path(filename)
        if not path.is_absolute():
            # Virtual modules' relative filenames are not rooted in the repo.
            # Keep a legitimate absolute import origin, without guessing cwd.
            origin=getattr(getattr(module,'__spec__',None),'origin',None)
            if not origin or not Path(origin).is_absolute():continue
            path=Path(origin)
        path=path.resolve()
        if path.suffix!='.py' or not path.is_relative_to(ROOT):continue
        modules[str(path.relative_to(ROOT))]=digest(path)
    inventory_path=ROOT/'evidence/linguistic_truth_v1/source_inventory.json'
    installed=json.loads(inventory_path.read_text())
    from tools.linguistic_truth.correction import CITATION
    inputs=[GOLD_PATH,inventory_path,ROOT/CITATION['path']]+[ROOT/s['local_path'] for s in installed['sources']]
    # The vocalization bridge is a source-replayed acquisition premise. Bind
    # its exact review and source bytes as well as the imported Python code;
    # a checked semantic receipt alone does not attest these spellings.
    inputs += [ROOT / REVIEW_PATH] + [ROOT / s['path'] for s in marked_review['sources']]
    native=ROOT/'formal/.lake/build/bin/linguisticTruth'
    toolchain=ROOT/'formal/lean-toolchain'
    return {
        'python_repository_modules':dict(sorted(modules.items())),
        'input_files':{str(p.relative_to(ROOT)):digest(p) for p in inputs},
        'native_checker':{'path':str(native.relative_to(ROOT)),'sha256':digest(native) if native.is_file() else None,'bytes':native.stat().st_size if native.is_file() else None},
        'formal_toolchain':{'path':str(toolchain.relative_to(ROOT)),'sha256':digest(toolchain),'contents':toolchain.read_text().strip()},
        'python_executable':{'path':sys.executable,'sha256':digest(Path(sys.executable).resolve()),'version':sys.version},
    }


def integrity_check(before:dict[str,Any],after:dict[str,Any])->dict[str,Any]:
    changed=[k for k in sorted(set(before)|set(after)) if before.get(k)!=after.get(k)]
    native_present=bool(before.get('native_checker',{}).get('sha256') and after.get('native_checker',{}).get('sha256'))
    return {'stable':not changed,'native_checker_present':native_present,'valid':not changed and native_present,'changed_sections':changed,'meaning':'Hashes of the imported repository Python module closure, executed native checker, pinned toolchain, gold, installed source inventory and its exact source files agree before and after all calls.'}


def contract_gate(rows:list[dict[str,Any]],summary:dict[str,Any],integrity:dict[str,Any])->dict[str,Any]:
    missing_native=[]
    for row in rows:
        raw=row.get('raw_result',{})
        for o in raw.get('occurrences',[]):
            if raw.get('status')=='RESOURCE_EXHAUSTED':
                # A verified prefix certificate remains valid conditionally;
                # exhaustion forbids claiming the remaining search completed.
                if o.get('certified_sense_ids') and o.get('native_checked') is not True:
                    missing_native.append(row['id']+':unchecked_certificate_after_exhaustion')
            elif o.get('candidates') and o.get('native_checked') is not True:
                missing_native.append(row['id']+':'+str(o.get('occurrence_id')))
    checks={
        'execution_evidence_stable':integrity['valid'],
        'all_44_cases_handled':len(rows)==44 and all(r.get('executed') for r in rows),
        'all_authority_observations_present':summary['authority']['obligations']==88 and summary['authority']['unmeasured']==0,
        'no_authority_overclaim':summary['authority']['excess_claims']==0,
        'no_false_selected_senses':summary['intended_selection']['false_selected_senses']==0,
        'native_checker_present_for_parsed_candidates':not missing_native,
    }
    return {'passed':all(checks.values()),'checks':checks,'missing_native_checks':missing_native,'scope':'Execution-integrity and safety contracts only; does not require or imply acquisition completeness, all diagnostic cases passing, or all source assertions measured.'}


def digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(text:Any)->str:
    if not isinstance(text,str):return ''
    return ''.join(c for c in unicodedata.normalize('NFD',text) if unicodedata.category(c)!='Mn' and c!='ـ').replace('أ','ا').replace('إ','ا').replace('آ','ا').strip()


# Transport vocabulary only; independently frozen gold retains semantic names.
ALIASES={
 'lion':('الحيوان المفترس','حيوان مفترس','السبع المعروف','الأسد الحيوان'),
 'brave_man':('الرجل الشجاع','رجل شجاع','الشجاع'),
 'menstruation':('الحيض',),'purity':('الطهر',),
 'supplication':('الدعاء',),'ritual_prayer':('العبادة المخصوصة','الأفعال المخصوصة','الأقوال والأفعال المخصوصة','الأفعال والأقوال المخصوصة'),
 'spring':('عين الماء الجارية','عين الماء','العين الجارية','الماء النابع'),
 'eye':('العين الباصرة','الباصرة','عضو الإبصار'),
}
ALIAS_BY_GLOSS={normalized(g):k for k,v in ALIASES.items() for g in v}


def alias(candidate:dict[str,Any])->str:
    gloss=normalized(candidate.get('gloss'))
    return ALIAS_BY_GLOSS.get(gloss,'UNMAPPED:'+str(candidate.get('sense_id',gloss)))


def plain(result:Any)->dict[str,Any]:
    if is_dataclass(result):return asdict(result)
    if hasattr(result,'to_dict'):return result.to_dict()
    if isinstance(result,dict):return deepcopy(result)
    raise TypeError('runtime result must be a mapping or dataclass')


def observation(raw:dict[str,Any])->dict[str,Any]:
    out={'status':raw.get('status'),'authority':{k:raw[k] for k in ('world_truth_established','all_arabic_complete') if k in raw},'occurrences':[],'source':raw.get('source')}
    if 'occurrences' not in raw:out.pop('occurrences')
    for o in raw.get('occurrences',[]):
        cs=o.get('candidates',[]); senses={str(c.get('sense_id')):alias(c) for c in cs}
        item={'surface':o.get('expression',o.get('surface',o.get('text',o.get('token',o.get('span',{}).get('raw_text',''))))),'candidates':[alias(c) for c in cs],'candidate_kinds':{alias(c):c.get('use_kind') for c in cs},'selected':[senses.get(str(x),'UNMAPPED:'+str(x)) for x in o.get('selected_sense_ids',[])],'excluded':[senses.get(str(x),'UNMAPPED:'+str(x)) for x in o.get('excluded_sense_ids',[])],'certified':[senses.get(str(x),'UNMAPPED:'+str(x)) for x in o.get('certified_sense_ids',[])],'signed_conflict':o.get('signed_conflict'),'raw':o}
        out['occurrences'].append(item)
    for k in ('attachment_audit','source_understanding','semantics','metamorphic'):
        if k in raw:out[k]=raw[k]
    return out


def check(name:str,actual:Any,expected:Any,measured:bool=True)->dict[str,Any]:
    return {'name':name,'outcome':('PASS' if actual==expected else 'FAIL') if measured else 'UNMEASURED','actual':actual,'expected':expected}


def evaluate(case:dict[str,Any],obs:dict[str,Any])->list[dict[str,Any]]:
    exp=case['expected'];checks=[]
    for k,v in exp['authority'].items():checks.append(check('authority.'+k,obs.get('authority',{}).get(k),v,k in obs.get('authority',{})))
    if 'status' in exp:checks.append(check('status',obs.get('status'),exp['status'],obs.get('status') is not None))
    if 'acquisition' in exp:
        a=exp['acquisition']; occ=obs.get('occurrences',[])
        # Current lexical queries contain at most one focus family. Retain all
        # matching occurrences; aggregate selection does not erase per-occurrence
        # scope checks, which are separately required below.
        target=normalized(a['focus']).removeprefix('ال')
        selected_occ=[o for o in occ if normalized(o['surface']).removeprefix('ال').removeprefix('ب') in (target,target+'ا') or normalized(o['surface'])==normalized(a['focus'])]
        # Some transports expose only IDs. Do not silently invent focus spans.
        candidates=set(x for o in selected_occ for x in o['candidates'])
        selected=set(x for o in selected_occ for x in o['selected'])
        measurable='occurrences' in obs
        for s in a.get('required_candidates',[]):checks.append(check('candidate_recall.'+s,s in candidates,True,measurable))
        if 'selected_senses' in a:checks.append(check('selected_senses',sorted(selected),sorted(a['selected_senses']),measurable))
        if 'use_kind' in a:
            kinds={o['candidate_kinds'].get(s) for o in selected_occ for s in o['selected']}
            checks.append(check('selected_use_kind',sorted(str(x) for x in kinds),[a['use_kind']],measurable))
    for dim in ('semantics','attachment_audit','source_understanding','metamorphic'):
        for k,v in exp.get(dim,{}).items():
            observed=obs.get(dim,{})
            if dim=='semantics' and k=='same_context_conflict' and 'occurrences' in obs:
                checks.append(check(dim+'.'+k,any(o.get('signed_conflict') is True for o in obs['occurrences']),v))
            elif dim=='semantics' and k=='source_roundtrip' and isinstance(obs.get('source'),dict):
                source=obs['source'];text=case['input']['text'];blob=text.encode('utf-8')
                exact=source.get('raw_text')==text and source.get('bytes')==len(blob) and source.get('sha256')==hashlib.sha256(blob).hexdigest()
                checks.append(check(dim+'.'+k,exact,v))
            elif dim=='semantics' and k in ('literal_positive_support','brave_man_negative_support','ambiguous','preserve_selected_senses','distinct_contexts','consistent_unique_literal_proof') and 'occurrences' in obs:
                occurrences=obs['occurrences'];all_selected={s for o in occurrences for s in o['selected']}
                all_excluded={s for o in occurrences for s in o['excluded']}
                values={
                    'literal_positive_support':any(o['candidate_kinds'].get(s)=='literal' for o in occurrences for s in o['selected']),
                    'brave_man_negative_support':'brave_man' in all_excluded,
                    'ambiguous':any(len(o['candidates'])>1 and not o['selected'] and not o['certified'] and not o.get('signed_conflict') for o in occurrences),
                    'preserve_selected_senses':sorted(all_selected),
                    'distinct_contexts':len({(o['raw'].get('frame',{}).get('occurrence',{}).get('context'),o['raw'].get('frame',{}).get('occurrence',{}).get('referent')) for o in occurrences}),
                    'consistent_unique_literal_proof':any(len(o['certified'])==1 and o['candidate_kinds'].get(o['certified'][0])=='literal' and not o.get('signed_conflict') for o in occurrences),
                }
                checks.append(check(dim+'.'+k,values[k],sorted(v) if isinstance(v,list) else v))
            else:checks.append(check(dim+'.'+k,observed.get(k),v,k in observed))
    return checks


def case_outcome(checks:list[dict[str,Any]])->str:
    statuses={c['outcome'] for c in checks}
    return 'FAIL' if 'FAIL' in statuses else 'UNMEASURED' if 'UNMEASURED' in statuses else 'PASS'


def ranking_observation(pair:dict[str,Any])->tuple[dict[str,Any],dict[str,Any]]:
    """Observe two actual executions and independently check installed IDs."""
    baseline,perturbed=pair['baseline'],pair['perturbed']
    a,b=baseline['acquisition'],perturbed['acquisition']
    left=baseline.get('retrieval',{});right=perturbed.get('retrieval',{})
    lrows,rrows=left.get('candidates',[]),right.get('candidates',[])
    reversed_order=bool(len(lrows)>1 and len(rrows)==1 and rrows[0].get('id')==lrows[-1].get('id') and right.get('reversed_for_diagnostic') is True)
    installed=json.loads((ROOT/'evidence/linguistic_truth_v1/source_inventory.json').read_text())
    examined=[]
    for result in (a,b):
        for o in result.get('occurrences',[]):
            frame=o.get('frame',{});expression=o.get('expression');convention=frame.get('convention')
            expected={(d['designation_id'],d['sense_id']) for d in installed['designations'] if d['expression']==expression and d['convention']==convention}
            base_ids={x[0] for x in expected}
            for relation in installed.get('relations',[]):
                if relation.get('designation_id') in base_ids:
                    expected.add((relation['designation_id'],relation['target_sense_id']))
            candidates={(c.get('designation_id'),c.get('sense_id')) for c in o.get('candidates',[])}
            native=o.get('native_result',{})
            native_ids={(row.get('candidate',{}).get('designation',{}).get('id'),row.get('candidate',{}).get('intended_sense')) for row in native.get('rows',[])}
            checked=bool(expected and candidates==expected and native_ids==expected and native.get('complete_proposal') is True and o.get('native_checked') is True)
            examined.append({'expression':expression,'convention':convention,'installed':sorted(expected),'candidates':sorted(candidates),'native_rows':sorted(native_ids),'all_examined':checked})
    observation={'reverse_candidates':reversed_order,'display_limit':right.get('limit'),'same_semantic_result':a==b,'all_installed_candidates_examined':bool(examined) and all(x['all_examined'] for x in examined)}
    evidence={'baseline_displayed_ids':[x.get('id') for x in lrows],'perturbed_displayed_ids':[x.get('id') for x in rrows],'baseline_matched_documents':left.get('matched_documents'),'perturbed_matched_documents':right.get('matched_documents'),'baseline_acquisition_sha256':hashlib.sha256(json.dumps(a,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'perturbed_acquisition_sha256':hashlib.sha256(json.dumps(b,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'examined':examined,'observation':observation}
    return observation,evidence


def load_gold(path:Path=GOLD_PATH)->dict[str,Any]:
    if digest(path)!=GOLD_SHA256:raise ValueError('frozen gold hash mismatch; preserve old gold and version changes')
    return json.loads(path.read_text())


def summarize(rows:list[dict[str,Any]])->dict[str,Any]:
    outcomes=Counter(r['outcome'] for r in rows)
    groups=defaultdict(Counter)
    checks=Counter()
    for r in rows:
        groups[r['family']][r['outcome']]+=1
        for c in r['checks']:checks[c['outcome']]+=1
    candidates=[c for r in rows for c in r['checks'] if c['name'].startswith('candidate_recall.')]
    selected=[c for r in rows for c in r['checks'] if c['name']=='selected_senses']
    false_selected=sum(len(set(c['actual'])-set(c['expected'])) for c in selected if c['outcome']!='UNMEASURED')
    missed_selected=sum(len(set(c['expected'])-set(c['actual'])) for c in selected if c['outcome']!='UNMEASURED')
    auth=[c for r in rows for c in r['checks'] if c['name'].startswith('authority.')]
    natural=[r for r in rows if r['family']=='natural_use_holdout']
    return {'total_cases':len(rows),'pass':outcomes['PASS'],'fail':outcomes['FAIL'],'unmeasured':outcomes['UNMEASURED'],'executed':sum(r.get('executed',False) for r in rows),'checks':dict(checks),'families':{k:dict(v) for k,v in groups.items()},'candidate_recall':{'required_sense_obligations':len(candidates),'found':sum(c['outcome']=='PASS' for c in candidates),'missing':sum(c['outcome']=='FAIL' for c in candidates),'unmeasured':sum(c['outcome']=='UNMEASURED' for c in candidates)},'intended_selection':{'cases':len(selected),'exact_matches':sum(c['outcome']=='PASS' for c in selected),'misses':sum(c['outcome']=='FAIL' for c in selected),'unmeasured':sum(c['outcome']=='UNMEASURED' for c in selected),'false_selected_senses':false_selected,'missed_selected_senses':missed_selected},'authority':{'obligations':len(auth),'excess_claims':sum(c['outcome']=='FAIL' for c in auth),'unmeasured':sum(c['outcome']=='UNMEASURED' for c in auth)},'natural_use_holdout':{'cases':len(natural),'pass':sum(r['outcome']=='PASS' for r in natural),'fail':sum(r['outcome']=='FAIL' for r in natural),'unmeasured':sum(r['outcome']=='UNMEASURED' for r in natural)}}


def run(*,execute=execute_request,scenario_execute=run_ranking_scenario)->dict[str,Any]:
    # Preload the actual entrypoint closure so lazy repository imports are also
    # covered by the before snapshot. Any later newly imported module is a
    # visible integrity difference rather than silently added after execution.
    for name in ('tools.linguistic_truth','tools.linguistic_truth.inventory','tools.linguistic_truth.sources','tools.linguistic_truth.pipeline','tools.linguistic_truth.correction'):
        importlib.import_module(name)
    gold=load_gold();before_evidence=evidence_snapshot();rows=[]
    for c in gold['cases']:
        request=build_request(c);before=deepcopy(request)
        try:
            scenario=None
            if c['id']=='B06':
                pair=scenario_execute(request);raw=plain(pair['baseline']['acquisition']);obs=observation(raw)
                obs['metamorphic'],scenario=ranking_observation(pair)
            else:
                raw=plain(execute(request));obs=observation(raw)
            checks=evaluate(c,obs)
            row={'id':c['id'],'family':c['family'],'executed':True,'outcome':case_outcome(checks),'checks':checks,'raw_result':raw,'observation':obs,'input_unchanged':request==before}
            if scenario is not None:row['scenario']=scenario
            rows.append(row)
        except Exception as exc:
            checks=[check('runtime_available',None,'result',False)]
            rows.append({'id':c['id'],'family':c['family'],'executed':False,'outcome':'UNMEASURED','checks':checks,'error':{'type':type(exc).__name__,'message':str(exc)},'input_unchanged':request==before})
    if digest(GOLD_PATH)!=GOLD_SHA256:raise ValueError('gold changed during evaluation')
    after_evidence=evidence_snapshot();integrity=integrity_check(before_evidence,after_evidence);summary=summarize(rows)
    return {'schema':'nabt.linguistic-truth.benchmark-result.v1','measured_at_utc':datetime.now(timezone.utc).isoformat(),'gold_sha256':GOLD_SHA256,'scope':'finite independently authored diagnostic, not external human review or Arabic population accuracy','summary':summary,'environment':{'python':sys.version,'platform':platform.platform()},'execution_evidence':{'before':before_evidence,'after':after_evidence,'integrity':integrity},'contract_gate':contract_gate(rows,summary,integrity),'rows':rows}


def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--require-contracts',action='store_true',help='Fail on execution-integrity/safety contract violations; not a claim that every diagnostic passed.');args=parser.parse_args()
    report=run();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    exit_status=0 if not args.require_contracts or report['contract_gate']['passed'] else 2
    print(json.dumps({'summary':report['summary'],'contract_gate':report['contract_gate'],'exit_status':exit_status,'exit_zero_meaning':'diagnostic execution completed'+(' and execution-integrity/safety contracts passed' if args.require_contracts else '; does not mean all diagnostic cases passed')},ensure_ascii=False,indent=2))
    return exit_status

if __name__=='__main__':raise SystemExit(main())
