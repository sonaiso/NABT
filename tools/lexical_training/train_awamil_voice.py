"""Train factorized heads using the original training partition. Test new roots after fitting."""
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

from . import awamil_voice as net
from .train_awamil_occurrence import DIR, dump, fingerprint, rows
from tools.grammar_catalog.operations import exact_terms


def train():
    import numpy as np
    obs=[r for r in rows("train") if r["relation"].startswith("event_")]
    feats=[net.evidence(r["text"]) for r in obs]
    voices=np.array([f[0] for f in feats])
    scopes=np.array([f[1] for f in feats])
    target_v=np.array(["passive" in r["relation"] for r in obs],dtype=float)
    target_s=np.array([r["relation"].endswith("deny") for r in obs],dtype=float)
    def binary(x,y):
        w=np.zeros(x.shape[1])
        for _ in range(1200):
            prob=1/(1+np.exp(-x@w))
            w-=.5*x.T@(prob-y)/len(x)
        return w
    v=binary(voices,target_v)
    s=binary(scopes,target_s)
    q=np.stack((np.ones(len(obs)),1/(1+np.exp(-voices@v))),axis=1)
    keys=np.zeros((len(obs),2,4))
    valid=np.zeros((len(obs),2),dtype=bool)
    ys=[]
    for i,(r,(_,_,k,terms)) in enumerate(zip(obs,feats,strict=True)):
        keys[i,:len(k)]=k
        valid[i,:len(k)]=True
        target=exact_terms(r["text"])[r["dependent"]-1]["utf8_span"]
        ys.append(next(j for j,t in enumerate(terms) if t["utf8_span"]==target))
    w=np.zeros((2,4))
    for _ in range(800):
        scores=np.einsum("bi,ij,bkj->bk",q,w,keys)
        scores[~valid]=-1e6
        prob=np.exp(scores-scores.max(axis=1,keepdims=True))
        prob/=prob.sum(axis=1,keepdims=True)
        prob[np.arange(len(obs)),ys]-=1
        w-=.5*np.einsum("bi,bk,bkj->ij",q,prob,keys)/len(obs)
    return {"schema":"nabt.awamil-voice.v1","voice":v.tolist(),"scope":s.tolist(),"patient":w.tolist(),
            "source_senses":["open","close"],"training_n":len(obs),"training_sha256":fingerprint(obs)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    output=p.parse_args().output
    output.mkdir(parents=True,exist_ok=True)
    w=train()
    dump(output/"voice_weights.json",w)
    with (DIR/"voice_transfer.tsv").open() as f:
        reserved=list(csv.DictReader(f,delimiter="\t"))
    four=json.loads((DIR/"contrast.json").read_bytes())["heldout"]
    report={}
    for key,items in (("break",four),("draw_reserved",reserved)):
        outcome=[]
        for r in items:
            pred=net.infer(r["text"],w)
            ok=(pred.get("voice"),pred.get("polarity"),pred.get("patient_surface"))==(r["voice"],r["polarity"],r["patient"])
            outcome.append({"input":r,"prediction":pred,"match":ok})
        report[key]={"n":len(items),"correct":sum(o["match"] for o in outcome),"cases":outcome}
    dump(output/"voice_evaluation.json",{"model_sha256":sha256((output/"voice_weights.json").read_bytes()).hexdigest(),
         "limits":"Finite marked event frame; second root tests proposals only. No source truth or usage promotion.",
         "sets":report})
    print({key:g["correct"] for key,g in report.items()})


if __name__=="__main__":
    main()
