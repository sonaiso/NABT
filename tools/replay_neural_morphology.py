"""Recompute the published test predictions and baselines without retraining."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def replay(source,directory):
    import torch
    from tools.arabic_training.data import read_source,sha
    from tools.arabic_training.experiment import vocabulary,encode,predict,evaluate,baseline_tables,baseline_predict,paired_intervals
    from tools.arabic_training.proposal import load_bundle
    from tools.evaluate_book_morphology import evaluate as book_evaluate
    torch.set_num_threads(2)
    results=json.loads((directory/'RESULTS.json').read_text())
    for name,digest in results['code_sha256'].items():
        snapshot=directory/'code_snapshot'/name
        implementation=snapshot if snapshot.exists() else ROOT/name
        if sha(implementation.read_bytes())!=digest:
            raise ValueError('training implementation changed: '+name)
    examples,intake,conflicts=read_source(source)
    if intake!=json.loads((directory/'intake.json').read_text()) or conflicts!=json.loads((directory/'annotation_conflicts.json').read_text()):
        raise ValueError('source intake mismatch')
    parts={s:[e for e in examples if e['split']==s] for s in ('train','test')}
    model,vocab,_=load_bundle(directory)
    if vocab!=vocabulary(parts['train']):
        raise ValueError('vocabulary is not training-only')
    predictions=predict(model,encode(parts['test'],vocab),vocab)
    saved=[json.loads(line) for line in (directory/'test_predictions.jsonl').read_text().splitlines()]
    words=[(e,i,w) for e in parts['test'] for i,w in enumerate(e['words'])]
    if len(saved)!=len(words):
        raise ValueError('saved test denominator mismatch')
    for row,(e,i,w) in zip(saved,words,strict=True):
        expected=dict(address=w['address'],csv_rows=w['csv_rows'],text_sha256=w['text_sha256'],
                      gold=w['labels'],affix_gold=w['affixes'],prediction=predictions[e['id']][i],
                      excluded_reasons=w['excluded_reasons'],status='UNVERIFIED_MORPHOLOGY_PROPOSAL')
        if row!=expected:
            raise ValueError('prediction replay mismatch at '+str(w['address']))
    metric=evaluate(parts['test'],predictions,set(vocab['words']))
    # Roundtrip normalizes integer JSON dictionary keys, not numerical values.
    normalize=lambda x:json.loads(json.dumps(x,sort_keys=True,allow_nan=False))
    if normalize(metric)!=results['test']['neural']:
        raise ValueError('neural metric mismatch')
    table=baseline_tables(parts['train'])
    for name,lexical in [('lexical_baseline',True),('majority_baseline',False)]:
        computed=evaluate(parts['test'],baseline_predict(parts['test'],table,lexical=lexical),set(vocab['words']))
        if normalize(computed)!=results['test'][name]:
            raise ValueError('baseline mismatch: '+name)
    lexical=evaluate(parts['test'],baseline_predict(parts['test'],table,lexical=True),set(vocab['words']))
    if paired_intervals(metric,lexical)!=results['paired_accuracy_intervals']:
        raise ValueError('paired interval mismatch')
    books=book_evaluate(directory,ROOT/'evidence/source_morphology_training/book_probe.json')
    if books!=json.loads((directory/'book_transfer_results.json').read_text()):
        raise ValueError('book transfer result mismatch')
    return dict(status='PASS',source_sha256=intake['source_sha256'],test_words_replayed=len(words),
                metrics_and_two_baselines_replayed=True,book_cases_replayed=books['total'],
                book_cases_passed=books['passed'],proof_authority_granted=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--model-dir',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    result=replay(args.source,args.model_dir)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
