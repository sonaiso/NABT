"""Independent evaluation adapter. Only public NABT APIs are used.

The manual oracle and source bytes were frozen before new-code exposure. This
runner does not synthesize semantic labels from runtime output. Its source-span
and certificate checks are independent from NABT's production verifier.
"""
from __future__ import annotations
import argparse,hashlib,json,platform,time,sys
from pathlib import Path
from collections import Counter
from oracle_helpers import atom_key,rule_key,restore_segments,independent_certificate

EXPECTED_HASHES={
'episodes.json':'5b6c2a56b511065eb0cf1683cf9af63425501def33026b50cfc77b72997e5682',
'scope_episodes.json':'a7ae71feba70c84cb86e1bea71c9b6ec473fc5504fd660d1fdf1a53f01adcfb9',
'real_excerpts.json':'15cf499465cc37fca126319243e6d9d113aaccb6f633a23b41fa8b500879981f',
'manual_oracle.json':'5d08da7884a7100ef11de1daa61806f071ec9549de3fb8fd39df5d0566cbde3f',
'gold_review.json':'1a1bb535058a3e67df35fb6d5dbc4ff0890943edcdc5508ef10935163498ccab',
'independent_gold_review.json':'8eb2c502f2abc290fff420f431ea51b73164edf78dd537e0f6c99ee06e0f5dee',
}

def exception_record(error):
    if hasattr(error,'as_dict'): return error.as_dict()
    return {'type':type(error).__name__,'message':str(error)}

def compare_projection(doc,gold,allowed=None):
    facts=[x['atom'] for x in doc['facts']]
    rules=[{'body':x['body'],'head':x['head']} for x in doc['rules']]
    facts_gold=gold.get('facts',[]); rules_gold=gold.get('rules',[])
    f_ok=sorted(map(atom_key,facts))==sorted(map(atom_key,facts_gold))
    r_ok=sorted(map(rule_key,rules))==sorted(map(rule_key,rules_gold))
    q_ok=True
    if gold.get('gold_query') is not None:
        q_ok=[atom_key(x['atom']) for x in doc['queries']]==[atom_key(gold['gold_query'])]
    admissible_facts=list(facts_gold); admissible_rules=list(rules_gold)
    if allowed:
        admissible_facts+=allowed.get('safety_allowed_facts',[])
        admissible_rules+=allowed.get('safety_allowed_rules',[])
    # Accepted premises must be included in the independent manual meaning.
    safe=all(atom_key(x) in set(map(atom_key,admissible_facts)) for x in facts)
    safe=safe and all(rule_key(x) in set(map(rule_key,admissible_rules)) for x in rules)
    exact=f_ok and r_ok and q_ok
    semantically_nonempty=bool(facts_gold or rules_gold or gold.get('gold_query'))
    # Recognizing a speech-act marker or suspending an ambiguity is reported
    # separately; it is never counted as complete compositional interpretation.
    uncertain=gold.get('gold_mode') in {'ambiguous','scope_required','unresolved'}
    return {'exact_manual_projection':exact,'admitted_claims_licensed':not doc['accepted'] or safe,
            'semantic_read':doc['accepted'] and exact and semantically_nonempty and not uncertain,
            'fact_count':len(facts),'rule_count':len(rules),'query_count':len(doc['queries'])}

def run(data_root,profile):
    from nabt.semantics import SemanticKernel
    if profile=='arabic':
        from nabt.arabic_reader import read_arabic,LANGUAGE_ID
        def reader(raw,source_id,scope):
            r=read_arabic(raw,source_id=source_id,scope=scope)
            return r.document.as_dict(),r.as_dict()
        def kernel(): return SemanticKernel(language_id=LANGUAGE_ID)
    else:
        from nabt.text_reader import parse_document
        LANGUAGE_ID='nabt.controlled-arabic.v1'
        def reader(raw,source_id,scope):
            d=parse_document(raw,source_id=source_id,scope=scope).as_dict()
            return d,{'document':d,'steps':[],'language_id':LANGUAGE_ID,'accepted':d['accepted']}
        def kernel(): return SemanticKernel()
    for name,digest in EXPECTED_HASHES.items():
        assert hashlib.sha256((data_root/name).read_bytes()).hexdigest()==digest,name
    manual={r['source_text_sha256']:r['expected'] for r in json.loads((data_root/'manual_oracle.json').read_text())['records']}
    overrides={x['case_id']:x for x in json.loads((data_root/'gold_review.json').read_text())['overrides']}
    results=[]; all_start=time.perf_counter()
    for partition,file in [('standalone','episodes.json'),('declared_scope','scope_episodes.json')]:
      for case in json.loads((data_root/file).read_text())['cases']:
        start=time.perf_counter(); cid=case['id']; scope='eval_'+cid; k=kernel()
        events=[]; active={}; complete=True; claims_safe=True; proofs_ok=True; all_restore=True
        source_read_flags=[]; query_flags=[]; covered_query_flags=[]
        for idx,event in enumerate(case['events']):
          op=event['op']; row={'index':idx,'op':op}
          try:
            if op in ('add','replace'):
              raw=event['text'].encode(); sid=event['source_id']; gold=manual[hashlib.sha256(raw).hexdigest()]
              d,report=reader(raw,sid,scope)
              restored=restore_segments(d,raw,sid); all_restore &= restored
              comparison=compare_projection(d,gold,overrides.get(cid))
              row.update({'reading':report,'comparison':comparison,'source_restored':restored})
              admission=(k.add_source(event['text'],source_id=sid,scope=scope) if op=='add' else k.replace_source(event['text'],source_id=sid,scope=scope)).as_dict()
              row['admission']=admission
              # The replaying kernel must not accept a rejected reader document.
              assert not admission['accepted'] or d['accepted']
              accepted=admission['accepted']
              if accepted: active[sid]=event['text']
              complete &= accepted and comparison['exact_manual_projection']
              claims_safe &= (not accepted or comparison['admitted_claims_licensed'])
              source_read_flags.append(comparison['semantic_read'])
            elif op=='remove':
              out=k.remove_source(event['source_id']).as_dict(); row['revision']=out
              if out['accepted']: active.pop(event['source_id'],None)
              complete &= out['accepted']
            elif op=='query':
              out=k.query(event['text'],scope=scope).as_dict(); row['result']=out
              actual_query=out.get('query')
              target_ok=isinstance(actual_query,dict) and atom_key(actual_query)==atom_key(event['gold_atom'])
              correct=target_ok and out['status'] in event['gold_status']
              row['query_target_matches_gold']=target_ok
              row['status_matches_gold']=correct
              # p04 is explicitly a symbolic identity/gender-boundary probe.
              # Named grammar deferral is safe but is not successful answer coverage.
              row['diagnostic_nonstandard_query']=cid=='p04'
              row['covered_by_admitted_sources']=complete
              query_flags.append(correct); covered_query_flags.append(correct and complete)
              if out.get('world_truth')!='NOT_ESTABLISHED': claims_safe=False
              cert_checks=[]
              for name,cert in out.get('proofs',{}).items():
                if cert is None: continue
                independent_certificate(cert,active,scope,manual)
                cert_checks.append({'side':name,'independent_replay':True})
              row['independent_certificates']=cert_checks
              if out['status'] in ('SUPPORTED','REFUTED') and not correct: claims_safe=False
            else: raise AssertionError(f'Unknown frozen operation {op}')
          except Exception as error:
            row['error']=exception_record(error)
            row['error_type']=type(error).__name__
            complete=False
            if op in ('add','replace') and 'source_restored' not in row:
                all_restore=False
            if op=='query':
                if 'status_matches_gold' in row:
                    covered_query_flags[-1]=False
                else:
                    query_flags.append(False); covered_query_flags.append(False)
            # A normal language or missing-source exception is an uncovered case.
            # An assertion in the independent checker is a failed safety check.
            if isinstance(error,AssertionError): claims_safe=False; proofs_ok=False
          events.append(row)
        seconds=time.perf_counter()-start
        full=complete and all(query_flags) and bool(source_read_flags) and all(source_read_flags)
        results.append({'id':cid,'partition':partition,'stratum':case['stratum'],'complete_episode':full,
                        'source_admission_and_projection_complete':complete,'source_semantic_read_flags':source_read_flags,
                        'queries':len(query_flags),'query_matches':sum(query_flags),'covered_query_matches':sum(covered_query_flags),
                        'source_restoration':all_restore,'admitted_claims_licensed':claims_safe,'independent_certificates_pass':proofs_ok,
                        'within_budget':seconds<=5,'seconds':seconds,'events':events})
    real_results=[]
    for example in json.loads((data_root/'real_excerpts.json').read_text())['examples']:
        raw=example['raw_text'].encode(); sid=example['id']; gold=dict(example['gold'])
        if 'query' in gold: gold['gold_query']=gold.pop('query')
        try:
            d,r=reader(raw,sid,'authentic')
            restoration=restore_segments(d,raw,sid)
            c=compare_projection(d,gold)
            real_results.append({'id':sid,'source_restored':restoration,'comparison':c,'reading':r})
        except Exception as error:
            real_results.append({'id':sid,'error':exception_record(error),'source_restored':False})
    def summary(part):
      rows=[r for r in results if r['partition']==part]
      return {'episodes':len(rows),'complete_episodes':sum(r['complete_episode'] for r in rows),
              'queries':sum(r['queries'] for r in rows),'raw_query_matches':sum(r['query_matches'] for r in rows),
              'covered_query_matches':sum(r['covered_query_matches'] for r in rows),
              'source_restoration_episodes':sum(r['source_restoration'] for r in rows),
              'licensed_claim_episodes':sum(r['admitted_claims_licensed'] for r in rows),
              'source_admission_and_projection_complete':sum(r['source_admission_and_projection_complete'] for r in rows),
              'budget_pass':sum(r['within_budget'] for r in rows)}
    return {'schema':'nabt.arabic-syntax.evaluation-results.v1','profile':LANGUAGE_ID,
            'runtime':{'python':sys.version,'platform':platform.platform()},'data_hashes':EXPECTED_HASHES,
            'method':'Manual frozen semantic oracle; complete understanding, safe suspension, literal source restoration and source-relative proof replay are distinct metrics.',
            'seconds':time.perf_counter()-all_start,'summary':{'standalone':summary('standalone'),'declared_scope':summary('declared_scope'),
            'real_excerpts':{'total':len(real_results),'semantic_read':sum(r.get('comparison',{}).get('semantic_read',False) for r in real_results),
                             'source_restored':sum(r.get('source_restored',False) for r in real_results),
                             'licensed_claims':sum(r.get('comparison',{}).get('admitted_claims_licensed',False) for r in real_results)}},
            'episodes':results,'real_excerpts':real_results}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--profile',choices=['arabic','controlled'],required=True)
    p.add_argument('--data-root',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--output',type=Path,required=True); args=p.parse_args()
    out=run(args.data_root,args.profile);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(out['summary'],ensure_ascii=False,indent=2))
