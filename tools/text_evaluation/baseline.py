"""Declared fact-retrieval baseline: same raw input, no rule application."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from .controlled import EXPECTED_SHA,DATASET,ROOT,question_oracle,expected_literal
from .integrity import require_output, verify_code_freeze, verify_published_inputs, write_report


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',required=True,type=Path)
    ap.add_argument('--code-freeze',required=True,type=Path)
    args=ap.parse_args()
    require_output(args.output, data=DATASET.parent, freeze=args.code_freeze)
    verify_published_inputs(DATASET.parent)
    assert hashlib.sha256(DATASET.read_bytes()).hexdigest()==EXPECTED_SHA
    freeze=verify_code_freeze(args.code_freeze)
    from nabt.text_reader import parse_document
    data=json.loads(DATASET.read_text())
    results=[]
    for ep in data['episodes']:
        active={}
        def install(src):
            doc=parse_document(src['text'].encode(),source_id=src['source_id'],scope=src['scope'])
            assert doc.accepted
            active[src['source_id']]={'scope':src['scope'],'facts':[expected_literal(f['atom']) for f in doc.as_dict()['facts']]}
        for src in ep['sources']:
            install(src)
        checkpoints=[]
        for index,step in enumerate(ep['steps']):
            op=step['operation']
            if op=='remove_source':
                del active[step['source_id']]
            elif op in {'add_source','replace_source'}:
                install(step['source'])
            elif op=='query':
                target=question_oracle(step['text'])
                opposite=(target[0],target[1],not target[2])
                facts={a for src in active.values() if src['scope']==step['scope'] for a in src['facts']}
                pos,neg=target in facts,opposite in facts
                status='CONFLICT' if pos and neg else 'SUPPORTED' if pos else 'REFUTED' if neg else 'UNKNOWN'
                checkpoints.append({'index':index,'expected_status':step['expected']['status'],'baseline_status':status,'passed':status==step['expected']['status']})
        results.append({'id':ep['id'],'partition':ep['partition'],'family':ep['family'],'status_episode_passed':all(c['passed'] for c in checkpoints),'checkpoints':checkpoints})
    summary={}
    for partition in ('first40','reserve20','all'):
        rows=[r for r in results if partition=='all' or r['partition']==partition]
        cps=[c for r in rows for c in r['checkpoints']]
        answered=[c for c in cps if c['baseline_status'] in {'SUPPORTED','REFUTED'}]
        sufficient=[c for c in cps if c['expected_status'] in {'SUPPORTED','REFUTED'}]
        correct_answers=[c for c in answered if c['passed']]
        summary[partition]={'episodes':len(rows),'status_episode_passed':sum(r['status_episode_passed'] for r in rows),
                            'checkpoints':len(cps),'status_checkpoints_passed':sum(c['passed'] for c in cps),
                            'answers':len(answered),'correct_answers':len(correct_answers),'sufficient_evidence_queries':len(sufficient),
                            'answer_precision':len(correct_answers)/len(answered) if answered else None,
                            'justified_coverage':len(correct_answers)/len(sufficient) if sufficient else None,
                            'baseline_status_counts':dict(Counter(c['baseline_status'] for c in cps))}
    report={'schema':'nabt-fact-retrieval-only-baseline-v1','dataset_sha256':EXPECTED_SHA,'code_freeze':freeze,
            'method':'Uses the same reader on the same source bytes and scope/update sequence. It retrieves only explicitly asserted signed facts, never applies definition, universal, or conditional rules. Both signs conflict; a single sign supports/refutes; no matching direct assertion stays UNKNOWN. It has no learned parameters and does not stand for a language-model baseline.',
            'metric_scope':'Status-only comparisons are shown for both the baseline and kernel; the main kernel benchmark additionally checks proof replay, named missing premises, conditional-world-truth labels, and result schema.',
            'summary':summary,'results':results}
    write_report(args.output, report, data=DATASET.parent, freeze=args.code_freeze)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
