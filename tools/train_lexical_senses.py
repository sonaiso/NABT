#!/usr/bin/env python3
"""Train a fixed diagnostic text-to-sense model; never train a proof-acceptance head."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.lexical_training.senses import catalogue, encode, forward, train, training_rows, SCHEMA
from tools.lexical_training.data import digest
from tools.lexical_testimony import CATALOG_SHA


def main(output):
    source = ROOT/'evidence/neural_senses_v1'
    protocol_raw = (source/'protocol.json').read_bytes()
    cases_raw = (source/'acceptance.json').read_bytes()
    protocol = json.loads(protocol_raw)
    cases = json.loads(cases_raw)['queries']
    cat = catalogue()
    ids = [s['id'] for s in cat['senses']]
    texts, y = training_rows(cat)
    if any(c['text'] in texts or any(i not in ids for i in c['expected_ids']) for c in cases):
        raise ValueError('diagnostic must have distinct query text and installed labels')
    output.mkdir(parents=True, exist_ok=False)
    x = encode(texts)
    weights, history = train(x, y, protocol)
    np.savez(output/'weights.npz', **weights)
    meta = {'schema': SCHEMA, 'catalogue_sha256': CATALOG_SHA, 'sense_ids': ids,
            'features': 'lexical-crc32-word-char34-v1',
            'weights_sha256': digest((output/'weights.npz').read_bytes()),
            'protocol_sha256': digest(protocol_raw), 'acceptance_sha256': digest(cases_raw),
            'authority': 'NONE'}
    (output/'model.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2)+'\n')
    (output/'training_rows.json').write_text(json.dumps([{'text': t, 'sense_ids': [ids[j] for j in np.flatnonzero(y[i])]} for i,t in enumerate(texts)],ensure_ascii=False,indent=2)+'\n')
    z = encode([c['text'] for c in cases]); neural = forward(weights, z)
    similarity = z @ x.T
    baseline = np.column_stack([similarity[:, y[:,j]>0].max(axis=1) for j in range(len(ids))])
    predictions = []
    for i,c in enumerate(cases):
        eligible = [j for j,s in enumerate(cat['senses']) if s['root']==c['root']]
        row = {**c, 'candidate_count':len(eligible)}
        for name,scores in [('neural',neural),('lexical_baseline',baseline)]:
            ranking=sorted(eligible,key=lambda j:(-float(scores[i,j]),ids[j]))
            row[name]={'ranked_ids':[ids[j] for j in ranking],
                       'correct':ids[ranking[0]] in c['expected_ids'],
                       'first_gold_rank': next(k+1 for k,j in enumerate(ranking) if ids[j] in c['expected_ids'])}
        predictions.append(row)
    report={'schema':'nabt.neural-senses-evaluation.v1','authority':'NONE',
            'parameters':sum(v.size for v in weights.values()),'training_rows':len(texts),
            'catalogue_senses':len(ids),'history':history,'numpy':np.__version__,
            'test_status':'AUTHORED_SEEN_SENSE_PARAPHRASES_NOT_BLIND',
            'protocol':protocol,'model':meta,'metrics':{},
            'native_checked':False,'default_ranker_changed':False,
            'limits':['No unseen-sense or unseen-root generalization measured.',
                      'Singleton root results do not measure sense disambiguation.',
                      'No source authenticity, intended meaning, free Arabic completeness or Python refinement proved.']}
    for group,rows in [('all',predictions),('ambiguous_roots',[r for r in predictions if r['candidate_count']>1])]:
        report['metrics'][group]={'n':len(rows),**{name:{'correct':sum(r[name]['correct'] for r in rows),'mrr':sum(1/r[name]['first_gold_rank'] for r in rows)/len(rows)} for name in ['neural','lexical_baseline']}}
    for name,data in [('FIRST_TEST.json',report),('predictions.json',predictions)]:
        (output/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report['metrics'],indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    main(parser.parse_args().output_dir)
