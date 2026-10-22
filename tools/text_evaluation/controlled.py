"""Public-API adapter for a separately frozen manual oracle.

The dataset, not this adapter, supplies every expected logical result.
Do not alter dataset bytes after freeze. Adapter corrections must be logged.
"""
import argparse
import collections
import hashlib
import json
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PRIVATE=ROOT/'evidence/text_inquiry'
DATASET=PRIVATE/'controlled_text_benchmark.json'
EXPECTED_SHA='1edb63bd0df4e6c35e466b989a9bc4e55d5204d66a4771f6b72f073895419127'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plain(report):
    return report.as_dict() if hasattr(report,'as_dict') else report


def expected_literal(raw):
    return (raw['predicate'],tuple(raw.get('args',raw.get('arguments',()))),raw.get('positive',True))


def question_oracle(text):
    """Read only the finite ground-question surface independently of NABT."""
    assert text.startswith('هل ') and text.endswith('؟')
    parts=re.findall(r'«[^»]*»|[^\s]+',text[3:-1])
    positive=not (parts and parts[0]=='ليس')
    if not positive:
        parts=parts[1:]
    assert len(parts)==3, parts
    def name(part):
        return part[1:-1] if part.startswith('«') and part.endswith('»') else part
    if parts[1]=='هو':
        return (name(parts[2]),(name(parts[0]),),positive)
    return (name(parts[1]),(name(parts[0]),name(parts[2])),positive)


def proof_errors(result,question,active_sources):
    """Check byte replay and elementary proof steps without calling verifier.

    This does not establish the truth of a source or interpret arbitrary Arabic;
    the manually authored status oracle is separate from this finite checker.
    """
    problems=[]
    target=question_oracle(question)
    if expected_literal(result.get('query',{}))!=target:
        problems.append('query_literal_differs_from_frozen_question')
    proofs=result.get('proofs',{})
    need={'SUPPORTED':('query',),'REFUTED':('opposite',),'CONFLICT':('query','opposite')}.get(result.get('status'),())
    for slot in need:
        if slot not in proofs:
            problems.append('missing_certificate_'+slot)
    for slot,cert in proofs.items():
        required=target if slot=='query' else (target[0],target[1],not target[2])
        if expected_literal(cert.get('query',{}))!=required:
            problems.append('certificate_query_mismatch_'+slot)
        if cert.get('scope')!=result.get('scope'):
            problems.append('certificate_scope_mismatch')
        if cert.get('program_sha256')!=result.get('program_sha256'):
            problems.append('certificate_program_hash_mismatch')
        if result.get('status') in {'SUPPORTED','REFUTED'} and slot in need and cert.get('proof_kind')!='clean':
            problems.append('answered_without_clean_certificate')
        steps=cert.get('steps',[])
        for index,step in enumerate(steps):
            clause=step['clause']
            src=active_sources.get(clause.get('source_id'))
            if src is None:
                problems.append('certificate_source_inactive')
                continue
            raw=src['text'].encode('utf-8')
            full_hash=hashlib.sha256(raw).hexdigest()
            if clause.get('source_sha256')!=full_hash or clause.get('scope')!=src['scope'] or src['scope']!=result.get('scope'):
                problems.append('certificate_source_or_scope_transferred')
            for span in [clause['span']]+clause.get('component_spans',[]):
                start,end=span.get('start'),span.get('end')
                if type(start) is not int or type(end) is not int or not 0<=start<end<=len(raw):
                    problems.append('certificate_span_bounds_invalid')
                    continue
                if span.get('source_id')!=src['source_id'] or span.get('source_sha256')!=full_hash or span.get('span_sha256')!=hashlib.sha256(raw[start:end]).hexdigest():
                    problems.append('certificate_span_replay_mismatch')
                try:
                    raw[start:end].decode('utf-8',errors='strict')
                except UnicodeError:
                    problems.append('certificate_span_splits_utf8')
            premise_indices=step.get('premises',[])
            if any(type(p) is not int or not 0<=p<index for p in premise_indices):
                problems.append('certificate_forward_or_invalid_premise')
                continue
            binding=step.get('binding',{})
            def instantiate(atom):
                pred,args,sign=expected_literal(atom)
                return (pred,tuple(binding.get(a,a) if a.startswith('?') else a for a in args),sign)
            actual=expected_literal(step['atom'])
            if clause['kind']=='fact':
                if premise_indices or binding or actual!=expected_literal(clause['atom']):
                    problems.append('certificate_fact_step_mismatch')
            elif clause['kind']=='rule':
                if actual!=instantiate(clause['head']):
                    problems.append('certificate_rule_head_mismatch')
                if [instantiate(a) for a in clause['body']]!=[expected_literal(steps[p]['atom']) for p in premise_indices]:
                    problems.append('certificate_rule_premise_mismatch')
            else:
                problems.append('certificate_unknown_clause_kind')
        end=cert.get('conclusion')
        if type(end) is not int or not 0<=end<len(steps) or expected_literal(steps[end]['atom'])!=required:
            problems.append('certificate_conclusion_mismatch')
    return problems


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--partition',choices=['first40','reserve20','all'],required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--code-freeze',type=Path,required=True)
    args=ap.parse_args()
    if digest(DATASET)!=EXPECTED_SHA:
        raise RuntimeError('Frozen benchmark checksum differs')
    code_freeze=json.loads(args.code_freeze.read_text())
    for entry in code_freeze['files']:
        if digest(ROOT/entry['path'])!=entry['sha256']:
            raise RuntimeError('Implementation differs from code freeze: '+entry['path'])
    from nabt.text_reader import parse_document, parse_query
    from nabt.semantics import SemanticKernel

    dataset=json.loads(DATASET.read_text())
    chosen=[ep for ep in dataset['episodes'] if args.partition=='all' or ep['partition']==args.partition]
    results=[]
    run_start=time.perf_counter()
    for ep in chosen:
        ep_start=time.perf_counter()
        kernel=SemanticKernel()
        admissions=[]
        steps=[]
        active_sources={}
        errors=[]
        for src in ep['sources']:
            try:
                doc=parse_document(src['text'].encode('utf-8'),source_id=src['source_id'],scope=src['scope'])
                admission=plain(kernel.add_document(doc))
                admissions.append({'source_id':src['source_id'],'report':admission})
                if admission.get('accepted'):
                    active_sources[src['source_id']]=src
                else:
                    errors.append({'kind':'admission_failure','source_id':src['source_id']})
            except Exception as exc:
                errors.append({'kind':'admission_exception','source_id':src['source_id'],'type':type(exc).__name__,'message':str(exc)})
        for idx,step in enumerate(ep['steps']):
            try:
                op=step['operation']
                if op=='query':
                    q=parse_query(step['text'].encode('utf-8'),source_id='query',scope=step['scope'])
                    result=plain(kernel.query(q,scope=step['scope']))
                    expected=step['expected']
                    mismatches=[]
                    for key in ('status','reason','world_truth'):
                        if key in expected and result.get(key)!=expected[key]:
                            mismatches.append({'field':key,'expected':expected[key],'actual':result.get(key)})
                    if 'missing_contains' in expected:
                        target={expected_literal(a) for a in expected['missing_contains']}
                        plans=result.get('missing_premises',[])
                        found=any(target=={expected_literal(a) for a in p.get('atoms',[])} for p in plans)
                        if not found:
                            mismatches.append({'field':'missing_premises','expected_literal_set':sorted(target),'actual':plans})
                    if result.get('interpretation_status')!='READ':
                        mismatches.append({'field':'interpretation_status','expected':'READ','actual':result.get('interpretation_status')})
                    if not re.fullmatch('[0-9a-f]{64}',result.get('program_sha256','')):
                        mismatches.append({'field':'program_sha256','expected':'64 lowercase hexadecimal characters','actual':result.get('program_sha256')})
                    provenance_failures=proof_errors(result,step['text'],active_sources)
                    if provenance_failures:
                        mismatches.append({'field':'independent_proof_replay','expected':[],'actual':provenance_failures})
                    steps.append({'index':idx,'operation':op,'expected':expected,'actual':result,'mismatches':mismatches,'passed':not mismatches})
                    errors.extend({'kind':'query_mismatch','step':idx,**item} for item in mismatches)
                elif op=='remove_source':
                    result=plain(kernel.remove_source(step['source_id']))
                    steps.append({'index':idx,'operation':op,'actual':result})
                    if not result.get('accepted'):
                        errors.append({'kind':'revision_rejection','step':idx,'report':result})
                    else:
                        active_sources.pop(step['source_id'],None)
                elif op in {'add_source','replace_source'}:
                    src=step['source']
                    if op=='add_source':
                        result=plain(kernel.add_document(parse_document(src['text'].encode('utf-8'),source_id=src['source_id'],scope=src['scope'])))
                    else:
                        result=plain(kernel.replace_source(src['text'].encode('utf-8'),source_id=src['source_id'],scope=src['scope']))
                    steps.append({'index':idx,'operation':op,'actual':result})
                    if not result.get('accepted'):
                        errors.append({'kind':'revision_rejection','step':idx,'report':result})
                    else:
                        active_sources[src['source_id']]=src
                else:
                    raise AssertionError('Unknown frozen operation: '+op)
            except Exception as exc:
                errors.append({'kind':'step_exception','step':idx,'operation':step['operation'],'type':type(exc).__name__,'message':str(exc)})
                steps.append({'index':idx,'operation':step['operation'],'passed':False,'exception':{'type':type(exc).__name__,'message':str(exc)}})
        elapsed=time.perf_counter()-ep_start
        if elapsed>dataset['episode_budget_seconds']:
            errors.append({'kind':'episode_budget_exceeded','elapsed_seconds':elapsed})
        results.append({'id':ep['id'],'family':ep['family'],'partition':ep['partition'],'passed':not errors,'elapsed_seconds':elapsed,'admissions':admissions,'steps':steps,'errors':errors})
        if time.perf_counter()-run_start>dataset['whole_run_budget_seconds']:
            raise RuntimeError('Whole-run budget exceeded; retain completed result log before any rerun')
    elapsed=time.perf_counter()-run_start
    summary={'episodes':len(chosen),'episodes_passed':sum(r['passed'] for r in results),'query_checkpoints':sum(s['operation']=='query' for e in chosen for s in e['steps']),
             'query_checkpoints_passed':sum(s.get('passed',False) for r in results for s in r['steps'] if s['operation']=='query'),
             'elapsed_seconds':elapsed,'by_family':{},'error_classes':dict(collections.Counter(e['kind'] for r in results for e in r['errors']))}
    for family in sorted({r['family'] for r in results}):
        rows=[r for r in results if r['family']==family]
        summary['by_family'][family]={'episodes':len(rows),'passed':sum(r['passed'] for r in rows)}
    output={'schema':'nabt-independent-controlled-text-results-v1','partition':args.partition,'dataset_sha256':EXPECTED_SHA,'code_freeze':code_freeze,
            'adapter_sha256':digest(Path(__file__)),'environment':{'python':sys.version,'platform':platform.platform()},'summary':summary,'results':results}
    args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    # Only aggregate counts are public until the sealed reserve has been run.
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
