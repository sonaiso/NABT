"""Exploratory candidate recall requested after first results were opened.

This does not change the predeclared score or confer admission authority. It
matches exact signed atoms already present in Alternative.atoms; it never
reconstructs omitted operators from the gold or reads implementation code.
"""
from pathlib import Path
import json,hashlib,collections
from oracle_helpers import atom_key
P=Path(__file__).resolve().parent

def analyze(results,manual):
    records=[]; seen=set()
    for case in results['episodes']:
      for event in case['events']:
        report=event.get('reading');
        if not report: continue
        doc=report['document']; sid=doc['source_sha256']
        if doc['accepted'] or sid in seen: continue
        seen.add(sid); gold=manual[sid]
        labels=[('fact',a) for a in gold['facts']]
        if gold.get('gold_query'): labels.append(('question_payload',gold['gold_query']))
        candidates=[a for step in report.get('steps',[]) for alt in step.get('alternatives',[]) for a in alt.get('atoms',[])]
        keys={atom_key(a) for a in candidates}
        counted=[{'role':role,'atom':a,'found_exact_signed_atom':atom_key(a) in keys} for role,a in labels]
        records.append({'source_sha256':sid,'first_case':case['id'],'partition':case['partition'],
                        'gold_atomic_items':counted,'stored_candidate_atoms':candidates,
                        'gold_rule_count':len(gold['rules']),
                        'obligations':sorted({x for step in report.get('steps',[]) for x in step.get('obligations',[])})})
    def summarize(rows):
      atoms=[a for r in rows for a in r['gold_atomic_items']]
      return {'unadmitted_unique_sources':len(rows),'sources_with_atomic_gold':sum(bool(r['gold_atomic_items']) for r in rows),
              'gold_atomic_items':len(atoms),'exact_signed_atoms_present':sum(a['found_exact_signed_atom'] for a in atoms),
              'gold_rules_in_unadmitted_sources':sum(r['gold_rule_count'] for r in rows),
              'note':'An atom may occur among incompatible alternatives. This is not a coherent full reading, licensed assertion, derivation, or answer.'}
    real=[]
    for ex in results['real_excerpts']:
      report=ex.get('reading');
      if not report or report['document']['accepted']: continue
      gold=next(x for x in json.loads((P/'real_excerpts.json').read_text())['examples'] if x['id']==ex['id'])['gold']
      labels=[('fact',a) for a in gold.get('facts',[])]
      if gold.get('query'): labels.append(('question_payload',gold['query']))
      keys={atom_key(a) for st in report.get('steps',[]) for alt in st.get('alternatives',[]) for a in alt.get('atoms',[])}
      real.extend({'source':ex['id'],'role':role,'atom':a,'found_exact_signed_atom':atom_key(a) in keys} for role,a in labels)
    counts=collections.Counter(x for r in records for x in r['obligations'])
    return {'schema':'nabt.arabic-syntax.exploratory-candidate-recall.v1','stage':'Post-opening exploratory analysis, requested after the first evaluation. Not predeclared and not a release success gate.',
            'meaning':'Exact signed atomic gold present somewhere in saved Alternative.atoms. No union of alternatives is admitted. Full rules and operator scopes cannot be established by atom presence alone.',
            'summary':{'standalone':summarize([r for r in records if r['partition']=='standalone']),
                       'declared_scope':summarize([r for r in records if r['partition']=='declared_scope']),
                       'real_excerpts':{'atomic_gold_items':len(real),'exact_signed_atoms_present':sum(x['found_exact_signed_atom'] for x in real)}},
            'obligation_source_counts':dict(counts),'sources':records,'real_items':real}
if __name__=='__main__':
    results=json.loads((P/'first_results.json').read_text())
    manual={r['source_text_sha256']:r['expected'] for r in json.loads((P/'manual_oracle.json').read_text())['records']}
    out=analyze(results,manual);(P/'candidate_recall.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(out['summary'],ensure_ascii=False,indent=2));print(json.dumps(out['obligation_source_counts']))
