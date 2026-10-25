#!/usr/bin/env python3
"""Follow-up diagonal metric learning after the failed dense bottleneck run.

The 395-root test has already been observed. This is a declared secondary
evaluation, not a new independent holdout or a general semantic benchmark.
"""
import argparse
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.lexical_training.data import ROOT,paired_data,digest,save_json
from tools.train_lexical_retrieval import ranks,metrics

def main(a):
    import numpy as np
    import torch
    from tools.lexical_training.model import encode
    original=ROOT/'evidence/lexical_denotation/run_01'
    p=json.loads((original/'protocol.json').read_text())
    protocol=json.loads(a.protocol.read_text())
    torch.set_num_threads(protocol['threads']);torch.manual_seed(protocol['seed'])
    torch.use_deterministic_algorithms(True);rng=np.random.default_rng(protocol['seed'])
    pairs=paired_data(a.lisan);n=len(pairs)
    x,_,_,_=encode(pairs,p,np.load(original/'idf.npy',allow_pickle=False))
    x=torch.from_numpy(x)
    indices={s:np.array([i for i,r in enumerate(pairs) if r['split']==s]) for s in ['train','dev','test']}
    out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    log_weights=torch.nn.Parameter(torch.zeros(p['buckets']))
    def encoding():return torch.nn.functional.normalize(x*torch.exp(log_weights.clamp(-2,2)/2),dim=1)
    def score(ids):
        with torch.no_grad():
            e=encoding();return (e[ids]@e[n:].T).numpy()
    if a.mode=='train':
        if (out/'FIRST_TEST.json').exists():raise ValueError('immutable first report; use new run')
        save_json(out/'protocol.json',protocol)
        baseline_dev=metrics(ranks(score(indices['dev']),indices['dev']))
        best=baseline_dev['mrr'];selected=0;history=[]
        np.save(out/'log_weights.npy',log_weights.detach().numpy(),allow_pickle=False)
        opt=torch.optim.Adam([log_weights],lr=protocol['learning_rate']);started=time.monotonic();updates=0
        for epoch in range(1,protocol['epochs']+1):
            losses=[];order=rng.permutation(indices['train'])
            for start in range(0,len(order),protocol['batch_size']):
                ix=order[start:start+protocol['batch_size']]
                if len(ix)<2:continue
                w=torch.exp(log_weights.clamp(-2,2)/2)
                q=torch.nn.functional.normalize(x[ix]*w,dim=1)
                d=torch.nn.functional.normalize(x[ix+n]*w,dim=1)
                logits=q@d.T/protocol['temperature'];labels=torch.arange(len(ix))
                loss=(torch.nn.functional.cross_entropy(logits,labels)+torch.nn.functional.cross_entropy(logits.T,labels))/2
                loss=loss+protocol['regularization']*log_weights.square().mean()
                opt.zero_grad();loss.backward();opt.step();losses.append(loss.item());updates+=1
            dev=metrics(ranks(score(indices['dev']),indices['dev']))
            if dev['mrr']>best+1e-12:
                best=dev['mrr'];selected=epoch;np.save(out/'log_weights.npy',log_weights.detach().numpy(),allow_pickle=False)
            history.append({'epoch':epoch,'loss':float(np.mean(losses)),'dev':dev})
            print(json.dumps({'epoch':epoch,'dev':dev,'selected':selected}),flush=True)
        np.save(out/'final_log_weights.npy',log_weights.detach().numpy(),allow_pickle=False)
        save_json(out/'training.json',{'protocol_sha256':digest(a.protocol.read_bytes()),'parameters':len(log_weights),
          'updates':updates,'seconds':time.monotonic()-started,'selected_epoch':selected,'baseline_dev':baseline_dev,
          'selected_dev_mrr':best,'final_weight_delta_l2':float(log_weights.detach().norm()),'history':history,
          'environment':{'torch':torch.__version__,'numpy':np.__version__,'threads':torch.get_num_threads()},
          'test_status':'SECONDARY_REUSED_AFTER_RUN_01','authority':'NONE'})
    else:
        if protocol!=json.loads((out/'protocol.json').read_text()):raise ValueError('protocol drift')
    selected=np.load(out/'log_weights.npy',allow_pickle=False)
    with torch.no_grad():log_weights.copy_(torch.from_numpy(selected))
    test=indices['test'];scores=score(test)
    # Baseline computed with the same numeric backend and tie policy.
    baseline=(x[test]@x[n:].T).numpy();br,rr=ranks(baseline,test),ranks(scores,test)
    predictions=[{'root':pairs[i]['key'],'baseline_rank':int(br[j]),'selected_rank':int(rr[j]),
      'top10_roots':[pairs[k]['key'] for k in np.argsort(-scores[j],kind='stable')[:10]],'authority':'NONE'} for j,i in enumerate(test)]
    delta=(rr==1).astype(float)-(br==1).astype(float);boot=np.random.default_rng(826025)
    ci=np.quantile(delta[boot.integers(0,len(delta),size=(2000,len(delta)))].mean(1),[.025,.975])
    report={'task':p['task'],'test_status':'SECONDARY_REUSED_AFTER_RUN_01','weights_sha256':digest((out/'log_weights.npy').read_bytes()),
      'baseline':metrics(br),'selected':metrics(rr),'paired_top1_difference_95ci_descriptive_only':[float(v) for v in ci],
      'improved_top1':int(np.sum((rr==1)&(br!=1))),'regressed_top1':int(np.sum((rr!=1)&(br==1))),
      'source_truth':'UNMEASURED','sense_equivalence':'UNMEASURED','all_arabic_readings':'UNMEASURED','authority':'NONE'}
    if a.mode=='train':save_json(out/'FIRST_TEST.json',report);save_json(out/'predictions.json',predictions)
    else:
        if report!=json.loads((out/'FIRST_TEST.json').read_text()):raise ValueError('metric replay mismatch')
        if predictions!=json.loads((out/'predictions.json').read_text()):raise ValueError('prediction replay mismatch')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['train','replay'])
    p.add_argument('--lisan',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--protocol',type=Path,default=ROOT/'evidence/lexical_denotation/protocol_v2.json')
    main(p.parse_args())
