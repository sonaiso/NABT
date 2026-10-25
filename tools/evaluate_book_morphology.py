"""Report all frozen authored book-transfer cases, including failures."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def evaluate(model_dir,probe_path):
    import torch
    from tools.arabic_training.data import sha
    from tools.arabic_training.proposal import load_bundle,propose
    torch.set_num_threads(2)
    model,vocab,receipt=load_bundle(model_dir)
    probe=json.loads(probe_path.read_text())
    rows=[]
    for case in probe['cases']:
        source=(ROOT/case['source_path']).read_bytes()
        quote=source[case['start_byte']:case['end_byte']]
        if sha(source)!=case['source_sha256'] or quote.decode()!=case['quote'] or sha(quote)!=case['quote_sha256']:
            raise ValueError('book source replay failed')
        output=propose(case['editorial_surface'].encode(),model,vocab,receipt)
        predicted=output['tokens'][case['target_word']]['top']
        if case['task']=='verb_form':
            actual={'PV':'past','PV_PASS':'past','IV':'present','IV_PASS':'present','CV':'imperative'}.get(predicted['tag'],'other')
        elif case['task']=='word_class':
            actual='noun' if predicted['tag'].startswith(('NOUN','GERUND','ADJ')) else 'other'
        else:
            actual=predicted['case_mood']
        rows.append(dict(id=case['id'],book=case['book'],surface=case['editorial_surface'],
                         task=case['task'],expected=case['expected'],actual=actual,passed=actual==case['expected'],
                         full_prediction=predicted,unseen_surface=output['tokens'][case['target_word']]['unseen_surface']))
    by_book={b:dict(passed=sum(r['passed'] for r in rows if r['book']==b),total=sum(r['book']==b for r in rows)) for b in ('sibawayhi','qatr')}
    return dict(schema='nabt.authored-book-transfer-results.v1',probe_sha256=sha(probe_path.read_bytes()),
                model_sha256=receipt['files']['weights.npz'],status=probe['status'],
                passed=sum(r['passed'] for r in rows),total=len(rows),by_book=by_book,cases=rows,
                independent_human_review=False,general_arabic_improvement_established=False,
                used_for_fitting_or_selection=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model-dir',type=Path,required=True)
    p.add_argument('--probe',type=Path,default=ROOT/'evidence/source_morphology_training/book_probe.json')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(evaluate(args.model_dir,args.probe),stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')
