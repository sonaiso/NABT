"""Independent finite exact-byte citation controls; not a source authenticator."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GOLD_SHA256='6fd157b2ddc110f5f89289d3413a5a4debc083270d3e12682b86746c7a2e07a9'


def inspect_claim(claim,source_bytes,reported_kind):
    start,end=claim.get('start'),claim.get('end')
    valid=isinstance(start,int) and not isinstance(start,bool) and isinstance(end,int) and not isinstance(end,bool) and 0<=start<=end<=len(source_bytes)
    exact=valid and isinstance(claim.get('quote'),str) and source_bytes[start:end]==claim['quote'].encode('utf-8')
    return {'exact_quote_match':bool(exact),'kind_matches_source_report':bool(exact and claim.get('claimed_kind')==reported_kind),'external_authenticity_established':False}


def run():
    path=ROOT/'evidence/linguistic_truth_v1/benchmark_verse_gold.json'
    if hashlib.sha256(path.read_bytes()).hexdigest()!=GOLD_SHA256:raise ValueError('frozen citation gold changed')
    gold=json.loads(path.read_text());source=gold['source'];raw=(ROOT/source['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=source['sha256']:raise ValueError('citation source bytes changed')
    rows=[]
    for case in gold['cases']:
        observed=inspect_claim(case['input'],raw,source['source_reported_kind'])
        rows.append({'id':case['id'],'observed':observed,'expected':case['expected'],'outcome':'PASS' if observed==case['expected'] else 'FAIL'})
    return {'schema':'nabt.linguistic-truth.citation-audit.v1','gold_sha256':GOLD_SHA256,'source_sha256':source['sha256'],'scope':gold['scope'],'cases':len(rows),'pass':sum(r['outcome']=='PASS' for r in rows),'fail':sum(r['outcome']=='FAIL' for r in rows),'rows':rows,'is_acquisition_benchmark':False,'is_external_source_authentication':False}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();r=run();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('cases','pass','fail','scope')},ensure_ascii=False))

if __name__=='__main__':main()
