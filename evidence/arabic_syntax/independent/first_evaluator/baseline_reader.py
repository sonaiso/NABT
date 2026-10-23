from pathlib import Path
import json,hashlib,time
from nabt.text_reader import parse_document
P=Path('/tmp/nabt-syntax-independent')
def norm_atom(a):
    return (a['predicate'],tuple('?x' if x.startswith('?') else x for x in a['args']),a['positive'])
def norm_rule(r):
    return (tuple(sorted(norm_atom(a) for a in r['body'])),norm_atom(r['head']))
def restore(d,raw):
    off=0; restored=b''; digest=hashlib.sha256(raw).hexdigest()
    for s in d['segments']:
      x=s['span']; assert x['start']==off and x['end']>off
      b=raw[x['start']:x['end']]; assert hashlib.sha256(b).hexdigest()==x['span_sha256']
      assert x['source_sha256']==digest
      restored+=b; off=x['end']
    return restored==raw
out=[]
for i,r in enumerate(json.loads((P/'manual_oracle.json').read_text())['records']):
    raw=r['raw_text'].encode(); t=time.perf_counter()
    d=parse_document(raw,source_id=f'baseline_{i}').as_dict(); gold=r['expected']
    facts=[x['atom'] for x in d['facts']]; rules=[{'body':x['body'],'head':x['head']} for x in d['rules']]
    matches=sorted(norm_atom(x) for x in facts)==sorted(norm_atom(x) for x in gold['facts']) and sorted(norm_rule(x) for x in rules)==sorted(norm_rule(x) for x in gold['rules'])
    if 'gold_query' in gold: matches=matches and [norm_atom(x['atom']) for x in d['queries']]==[norm_atom(gold['gold_query'])]
    # Speech-act classification is outside v1, so empty accepted content is not
    # credited as understanding a command or an ambiguity.
    ambiguous=gold.get('gold_mode') in {'ambiguous','scope_required','unresolved'}
    semantic_coverage=d['accepted'] and matches and not ambiguous
    out.append({'source_text_sha256':r['source_text_sha256'],'accepted':d['accepted'],'restored':restore(d,raw),'manual_interpretation_match':matches,'semantic_coverage':semantic_coverage,'accepted_wrong_interpretation':d['accepted'] and not matches,'seconds':time.perf_counter()-t,'reader':d})
result={'baseline_commit':'fd5ebc582b63445cc3f9c60973e98c493e47c56b','baseline_language':'nabt.controlled-arabic.v1','interpretation':'These texts are not declared v1 inputs. Differences from natural-language gold measure lack of applicability, not a contradiction of the v1 formal contract.','counts':{'unique_source_documents':len(out),'accepted':sum(x['accepted'] for x in out),'source_restoration':sum(x['restored'] for x in out),'semantic_coverage':sum(x['semantic_coverage'] for x in out),'accepted_natural_gold_mismatch':sum(x['accepted_wrong_interpretation'] for x in out)},'results':out}
(P/'baseline_reader_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result['counts']))
