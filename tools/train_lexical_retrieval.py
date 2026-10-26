#!/usr/bin/env python3
"""Train or replay CPU dictionary evidence retrieval; no semantic authority."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.lexical_training.data import ROOT,paired_data,save_json,digest,LISAN_SHA,MAQAYIS_SHA

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nabt import foundation

def ranks(scores,gold):
    import numpy as np
    # Stable ties use gallery order, not labels.
    order=np.argsort(-scores,axis=1,kind='stable')
    return (order==np.asarray(gold)[:,None]).argmax(axis=1)+1

def metrics(r):
    import numpy as np
    return {'n':len(r),'top1':float(np.mean(r==1)),'recall5':float(np.mean(r<=5)),
            'recall10':float(np.mean(r<=10)),'mrr':float(np.mean(1/r))}

def main(a):
    foundation.require_foundation('tools.train_lexical_retrieval.main')
    import numpy as np
    import torch
    from tools.lexical_training.model import Retriever,encode,embed
    p=json.loads(a.protocol.read_text());torch.set_num_threads(p['threads'])
    torch.manual_seed(p['seed']);np.random.seed(p['seed']);torch.use_deterministic_algorithms(True)
    pairs=paired_data(a.lisan);n=len(pairs);out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    manifest=[{k:x[k] for k in ['key','split']}|{'lisan_span':[x['lisan']['start_byte'],x['lisan']['end_byte']],
                'maqayis_span':[x['maqayis']['start_byte'],x['maqayis']['end_byte']],
                'query_sha256':digest(x['query'].encode()),'document_sha256':digest(x['document'].encode())} for x in pairs]
    manifest_hash=digest(json.dumps(manifest,ensure_ascii=False,sort_keys=True).encode())
    train=np.array([i for i,x in enumerate(pairs) if x['split']=='train']);dev=np.array([i for i,x in enumerate(pairs) if x['split']=='dev']);test=np.array([i for i,x in enumerate(pairs) if x['split']=='test'])
    model=Retriever(p['buckets'],p['embedding_dim'])
    if a.mode=='train':
        if (out/'FIRST_TEST.json').exists():raise ValueError('first test is immutable; use a new run directory')
        save_json(out/'protocol.json',p);save_json(out/'split_manifest.json',manifest)
        x,indices,weights,idf=encode(pairs,p)
        np.save(out/'idf.npy',idf,allow_pickle=False)
        baseline=x[:n][dev]@x[n:].T
        optimizer=torch.optim.AdamW(model.parameters(),lr=p['learning_rate'],weight_decay=0.01)
        initial=model.embedding.weight.detach().clone();best=(-1,None,None);history=[];updates=0;started=time.monotonic()
        for epoch in range(1,p['epochs']+1):
            model.train();losses=[]
            order=np.random.permutation(train)
            for start in range(0,len(order),p['batch_size']):
                batch=order[start:start+p['batch_size']]
                if len(batch)<2:continue
                q=model(indices[batch],weights[batch]);d=model(indices[batch+n],weights[batch+n])
                logits=q@d.T/p['temperature'];labels=torch.arange(len(batch))
                loss=(torch.nn.functional.cross_entropy(logits,labels)+torch.nn.functional.cross_entropy(logits.T,labels))/2
                optimizer.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5);optimizer.step();losses.append(loss.item());updates+=1
            emb=embed(model,indices,weights);neural=emb[:n][dev]@emb[n:].T
            trials=[]
            for alpha in p['alphas']:
                m=metrics(ranks((1-alpha)*baseline+alpha*neural,dev));trials.append({'alpha':alpha,**m})
                if m['mrr']>best[0]+1e-12:
                    best=(m['mrr'],epoch,alpha);torch.save(model.state_dict(),out/'weights.pt')
            history.append({'epoch':epoch,'loss':float(np.mean(losses)),'dev':trials})
            print(json.dumps({'epoch':epoch,'loss':history[-1]['loss'],'best':best}),flush=True)
        delta=float(torch.linalg.vector_norm(model.embedding.weight.detach()-initial))
        save_json(out/'training.json',{'protocol_sha256':digest(a.protocol.read_bytes()),'manifest_sha256':manifest_hash,
          'source_sha256':{'lisan':LISAN_SHA,'maqayis':MAQAYIS_SHA},'pairs':n,'splits':{'train':len(train),'dev':len(dev),'test':len(test)},
          'parameters':sum(v.numel() for v in model.parameters()),'updates':updates,'selected_epoch':best[1],'alpha':best[2],
          'seconds':time.monotonic()-started,'embedding_delta_l2_final':delta,'history':history,
          'environment':{'python':sys.version,'torch':torch.__version__,'numpy':np.__version__,'cuda':torch.cuda.is_available(),'threads':torch.get_num_threads()},
          'authority':'NONE'})
    else:
        manifest_old=json.loads((out/'split_manifest.json').read_text())
        if manifest!=manifest_old:raise ValueError('source split/view drift')
        frozen=json.loads((out/'protocol.json').read_text())
        if p!=frozen:raise ValueError('protocol drift')
        x,indices,weights,idf=encode(pairs,p,np.load(out/'idf.npy',allow_pickle=False))
    training=json.loads((out/'training.json').read_text())
    if training['manifest_sha256']!=manifest_hash:raise ValueError('manifest mismatch')
    model.load_state_dict(torch.load(out/'weights.pt',map_location='cpu',weights_only=True));emb=embed(model,indices,weights)
    bs=x[:n][test]@x[n:].T;ns=emb[:n][test]@emb[n:].T;alpha=training['alpha'];scores=(1-alpha)*bs+alpha*ns
    br,nr,fr=ranks(bs,test),ranks(ns,test),ranks(scores,test)
    rng=np.random.default_rng(826025);diff=(fr==1).astype(float)-(br==1).astype(float)
    boots=np.mean(diff[rng.integers(0,len(diff),size=(2000,len(diff)))],axis=1)
    order=np.argsort(-scores,axis=1,kind='stable')
    predictions=[{'root':pairs[i]['key'],'baseline_rank':int(br[j]),'neural_rank':int(nr[j]),'selected_rank':int(fr[j]),
      'top10_roots':[pairs[k]['key'] for k in order[j,:10]],'authority':'NONE'} for j,i in enumerate(test)]
    report={'task':p['task'],'protocol_sha256':training['protocol_sha256'],'manifest_sha256':manifest_hash,
      'weights_sha256':digest((out/'weights.pt').read_bytes()),'gallery_size':n,'baseline':metrics(br),'neural_only':metrics(nr),'selected':metrics(fr),
      'selected_alpha':alpha,'paired_top1_difference_95ci':[float(v) for v in np.quantile(boots,[.025,.975])],
      'improved_top1':int(np.sum((fr==1)&(br!=1))),'regressed_top1':int(np.sum((fr!=1)&(br==1))),
      'source_truth':'UNMEASURED','sense_equivalence':'UNMEASURED','all_arabic_readings':'UNMEASURED','authority':'NONE'}
    if a.mode=='train':
        save_json(out/'FIRST_TEST.json',report);save_json(out/'predictions.json',predictions)
    else:
        if report!=json.loads((out/'FIRST_TEST.json').read_text()):raise ValueError('metric replay mismatch')
        if predictions!=json.loads((out/'predictions.json').read_text()):raise ValueError('prediction replay mismatch')
    print(json.dumps({'replay':a.mode=='replay',**report},ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['train','replay'])
    parser.add_argument('--lisan',type=Path,required=True);parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--protocol',type=Path,default=ROOT/'evidence/lexical_denotation/protocol_v1.json')
    main(parser.parse_args())
