"""Replay the discovered padding counterexample against both model versions."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def audit():
    import torch
    from tools.arabic_training.proposal import load_bundle
    torch.set_num_threads(1)
    records=[]
    for run in ('run_01','run_02'):
        model,vocab,receipt=load_bundle(ROOT/'evidence/source_morphology_training'/run)
        wi={w:i for i,w in enumerate(vocab['words'])};ci={c:i for i,c in enumerate(vocab['chars'])}
        for word in ('آبَاءِ','آتَاكَ','آتَاهُ'):
            chars=[ci[c] for c in word]
            short=torch.tensor([[chars+[0]*(max(3,len(chars))-len(chars))]])
            long=torch.tensor([[chars+[0]*8]])
            ids=torch.tensor([[wi[word]]]);lengths=torch.tensor([1])
            with torch.no_grad():
                a=model(ids,short,lengths);b=model(ids,long,lengths)
            delta=max(float((a[k]-b[k]).abs().max()) for k in a)
            if run=='run_02' and delta>1e-6:
                raise ValueError('corrected model still depends on character padding')
            records.append(dict(run=run,word=word,maximum_logit_difference=delta,model_sha256=receipt['files']['weights.npz']))
    return dict(schema='nabt.character-padding-counterexample.v1',status='FIXED_IN_RUN_02',
                scope='Implementation invariance, not linguistic accuracy or a new independent test',records=records)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(audit(),stream,ensure_ascii=False,indent=2);stream.write('\n')
