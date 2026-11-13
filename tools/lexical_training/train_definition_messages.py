"""Fit transition parameters on reviewed paths. Hold out whole focal definitions."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from tools.grammar_catalog import definition_network as law
from . import definition_messages as net

HELD={"G:ركوة","P:بياض","A:يقق","A:رماح","G:صلب","A:صلب","G:نمرقة"}


def examples(by_child):
    for focus in sorted(by_child):
        for n,mode,path in law.routes(focus,by_child):
            state=law.axis(focus) if len(path)==1 else (
                law.axis(path[-2]["parent"]) if all(e["relation"]=="is_a" for e in path[:-1])
                else next(e["relation"] for e in reversed(path[:-1]) if e["relation"]!="is_a"))
            if mode=="is_a":label=law.axis(n)
            else:label=net.state_label(mode)
            yield focus,n,mode,net.transition_input(state,path[-1]["relation"]),label


def main():
    import numpy as np
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    nodes,by_child,_=law.inventory()
    rows=list(examples(by_child))
    train=[r for r in rows if r[0] not in HELD]
    x=np.array([r[3] for r in train])
    y=[net.LABELS.index(r[4]) for r in train]
    rng=np.random.default_rng(239)
    h=rng.normal(0,.2,(12,x.shape[1]))
    w=rng.normal(0,.2,(len(net.LABELS),13))
    for _ in range(2000):
        a=np.tanh(x@h.T)
        z=np.column_stack((np.ones(len(x)),a))
        v=z@w.T
        prob=np.exp(v-v.max(axis=1,keepdims=True))
        prob/=prob.sum(axis=1,keepdims=True)
        prob[np.arange(len(x)),y]-=1
        delta=prob/len(x)
        dh=((delta@w[:,1:])*(1-a*a)).T@x
        w-=.6*(delta.T@z+.0001*w)
        h-=.6*(dh+.0001*h)
    weights={"schema":"nabt.definition-messages.v1","hidden":h.tolist(),"out":w.tolist(),
             "review_sha256":law.RESOURCE_SHA,"train_focus":sorted({r[0] for r in train}),
             "train_paths":len(train),"seed":239,"epochs":2000}
    args.output.mkdir(parents=True,exist_ok=True)
    def save(name,obj):
        with (args.output/name).open("x",encoding="utf-8") as f:
            f.write(json.dumps(obj,ensure_ascii=False,separators=(",",":"))+"\n")
    save("weights.json",weights)
    digest=sha256((args.output/"weights.json").read_bytes()).hexdigest()
    results=[]
    for focus in sorted(HELD):
        paths=list(law.routes(focus,by_child))
        proofs={}
        edges={}
        for n,mode,path in paths:
            proofs.setdefault((n,mode),[]).append([law.edge_key(e) for e in path])
            edges.update({law.edge_key(e):e for e in path})
        claims=[{"node":n,"relation":m,"proofs":p} for (n,m),p in proofs.items()]
        pred=net.predict_paths(focus,edges,claims,weights)["vectors"]
        for (n,m) in proofs:
            target=law.axis(n) if m=="is_a" else net.state_label(m)
            prediction=pred[m+"/"+n]["proposal"]
            results.append({"focus":focus,"target":n,"relation":m,"expected":target,"prediction":prediction,
                            "correct":target==prediction,"axis_only":law.axis(n)==target})
    report={"scope":"CLASSIFY_WITNESSED_PATHS_ONLY","training_paths":len(train),"heldout_focus":sorted(HELD),
            "n":len(results),"correct":sum(r["correct"] for r in results),
            "axis_only_correct":sum(r["axis_only"] for r in results),"model_sha256":digest,"cases":results}
    save("evaluation.json",report)
    print(digest,{k:report[k] for k in ("training_paths","n","correct","axis_only_correct")})


if __name__=="__main__":main()
