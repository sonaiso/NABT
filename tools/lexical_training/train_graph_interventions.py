"""Generate withdrawal labels and hidden-edge labels from executable NABT proof graphs and fit both heads."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from tools.grammar_catalog import gateway
from tools.grammar_catalog.licensed_speech import surviving_nodes
from tools.grammar_catalog.operations import ROOT,digest
from . import graph_interventions as net

DATA=ROOT/"evidence/graph_interventions_v1/split.json"


@dataclass
class Sample:
    family: str
    graph: net.Graph
    cuts: list
    targets: list
    edge_i: list
    edge_j: list
    edge_y: list
    edge_features: list
    owner_sha: str
    request_sha: str


def examples(spec):
    if "request_file" in spec:
        req=json.loads((ROOT/spec["request_file"]).read_bytes())
    else:
        req={"schema":gateway.REQUEST_SCHEMA,"route":"relations.analyze","payload":{"text":spec["text"]}}
    option={"lexical":spec["lexical"]} if "lexical" in spec else {}
    req["payload"]["licensed_speech"]=option
    receipt=gateway.run(req)
    check=gateway.accept_output(receipt,expected_request=req)
    if not check["valid"]:
        raise ValueError((spec["family"],check,receipt["execution"].get("error")))
    owner=receipt["execution"]["owner_result"]["licensed_speech"]
    if owner.get("owners",{}).get("dictionary",{}).get("native_checked") is False:
        raise ValueError("Native lexical owner unavailable")
    nodes=owner["nodes"]
    if "lexical" in spec and not any(n["role"]=="candidate_sense" for n in nodes):
        raise ValueError("Missing lexical joins")
    if spec["family"]=="ledger" and not any(n["id"]=="ledger/cause_to_effect" and n["status"]=="LICENSED" for n in nodes):
        raise ValueError("Missing ledger joins")
    if spec["family"]=="definition_inheritance" and not any(n["transition"]["scope"]=="conditional_definition" for n in nodes):
        raise ValueError("Missing definition paths")
    g=net.encode(nodes)
    if surviving_nodes(nodes,set())!=set(g.ids):
        raise ValueError("Initial owner state differs from the training population")
    ranks=sorted(range(len(g.ids)),key=lambda i:digest([spec["family"],g.ids[i]]))
    cuts=[[]]+[[i] for i in range(len(g.ids))]+[ranks[i:i+2] for i in range(0,len(ranks)-1,2)]
    ys=[]
    for cut in cuts:
        live=surviving_nodes(nodes,{g.ids[i] for i in cut})
        ys.append([key not in live for key in g.ids])
    left=[];right=[];labels=[];features=[]
    for j,paths in enumerate(g.paths):
        parents={i for path in paths for i in path}
        for i in range(j):
            if g.grades[i]<g.grades[j]:
                left.append(i);right.append(j);labels.append(i in parents)
                features.append(net.geometry(g,i,j))
    return Sample(spec["family"],g,cuts,ys,left,right,labels,features,digest(owner),digest(req))


def array_parameters(rng):
    import numpy as np
    return {"projection":rng.normal(0,.16,(net.HIDDEN,net.WIDTH)),"bias":np.zeros(net.HIDDEN),
            "relation":rng.normal(0,.12,(net.HIDDEN,net.HIDDEN)),"geometry":np.zeros(net.EDGE_WIDTH),
            "effect":rng.normal(0,.12,3+net.HIDDEN)}


def balanced(y):
    import numpy as np
    return np.where(y, .5/max(1,y.sum()), .5/max(1,y.size-y.sum()))


def compile_batch(samples):
    import numpy as np
    xs=[]; local_nodes=[]; effects=[]; eweights=[]; ei=[]; ej=[]; ey=[]; ef=[]
    for s in samples:
        offset=len(xs)
        xs.extend(s.graph.features)
        for cut, targets in zip(s.cuts,s.targets,strict=True):
            # Teacher forcing uses the owner's previous-layer states during fitting.
            # Deployment/evaluation always use the model's own recursive predictions.
            for i, routes in enumerate(s.graph.paths):
                local_nodes.append(offset+i)
                message=net.message(routes,targets)
                effects.append([1.,float(i in cut),float(message)])
                eweights.append(targets[i])
        ei.extend(offset+i for i in s.edge_i);ej.extend(offset+i for i in s.edge_j)
        ey.extend(s.edge_y);ef.extend(s.edge_features)
    return tuple(np.array(a) for a in (xs,local_nodes,effects,eweights,ei,ej,ey,ef))


def train(samples, protocol):
    import numpy as np
    if protocol["hidden"]!=net.HIDDEN:
        raise ValueError("Incompatible graph projection width")
    p=array_parameters(np.random.default_rng(protocol["seed"]))
    initial={k:v.copy() for k,v in p.items()}
    x,ind,base,y,ei,ej,edge_y,edge_features=compile_batch(samples)
    wy,we=balanced(y),balanced(edge_y)
    first={k:np.zeros_like(v) for k,v in p.items()}
    second={k:np.zeros_like(v) for k,v in p.items()}
    losses=[]
    for epoch in range(1,protocol["epochs"]+1):
        z=np.tanh(x@p["projection"].T+p["bias"])
        feats=np.column_stack((base,z[ind]))
        logits=feats@p["effect"]
        link=(z[ei]*(z[ej]@p["relation"].T)).sum(axis=1)+edge_features@p["geometry"]
        def derivative(raw,label,weight):
            return (1./(1.+np.exp(-np.clip(raw,-50,50)))-label)*weight
        d=derivative(logits,y,wy)
        a=derivative(link,edge_y,we)
        dz=np.zeros_like(z)
        np.add.at(dz,ind,d[:,None]*p["effect"][None,3:])
        np.add.at(dz,ei,a[:,None]*(z[ej]@p["relation"].T))
        np.add.at(dz,ej,a[:,None]*(z[ei]@p["relation"]))
        dh=dz*(1.-z*z)
        grad={"effect":d@feats,"geometry":a@edge_features,"relation":(z[ei]*a[:,None]).T@z[ej],
              "projection":dh.T@x,"bias":dh.sum(axis=0)}
        if epoch in (1,protocol["epochs"]):
            losses.append(float(wy@(np.logaddexp(0,logits)-y*logits)+we@(np.logaddexp(0,link)-edge_y*link)))
        for key,g in grad.items():
            first[key]=.9*first[key]+.1*g
            second[key]=.999*second[key]+.001*g*g
            p[key]-=protocol["learning_rate"]*(first[key]/(1-.9**epoch))/(np.sqrt(second[key]/(1-.999**epoch))+1e-8)
    def pack(weights):
        return {k:v.round(10).tolist() for k,v in weights.items()}
    return pack(p),pack(initial),losses


def score(s,w,no_edges=False):
    g=s.graph
    z=net.representations(g,w)
    cm=[[0,0],[0,0]]
    exact=0
    for cut,target in zip(s.cuts,s.targets,strict=True):
        probs=net.effects(g,z,w,set(cut),use_edges=not no_edges)
        predicted=[p>=.5 for p in probs]
        exact+=predicted==target
        for i,(truth,guess) in enumerate(zip(target,predicted,strict=True)):
            if i not in cut:
                cm[int(truth)][int(guess)]+=1
    rankings=net.links(g,z,w)
    ap=[];uniform=[]
    for j,ranked in enumerate(rankings):
        positives={i for route in g.paths[j] for i in route}
        if not positives or len(positives)==len(ranked):
            continue
        found=0;precision=0.
        for rank,(i,_) in enumerate(ranked,1):
            if i in positives:
                found+=1
                precision+=found/rank
        ap.append(precision/len(positives))
        uniform.append(len(positives)/len(ranked))
    return {"family":s.family,"nodes":len(g.ids),"scenarios":len(s.cuts),"exact":exact,"cm":cm,
            "ranked_targets":len(ap),"AP_sum":sum(ap),"edge_density_sum":sum(uniform),
            "edge_labels":len(s.edge_y),"positive_edges":sum(s.edge_y),"owner_sha256":s.owner_sha,"request_sha256":s.request_sha}


def summarize(rows):
    cm=[[sum(r["cm"][a][b] for r in rows) for b in (0,1)] for a in (0,1)]
    recalls=[cm[k][k]/sum(cm[k]) for k in (0,1)]
    n=sum(r["ranked_targets"] for r in rows)
    return {"confusion_true_rows_survive_lost":cm,"balanced_accuracy":sum(recalls)/2,
            "recall_lost":recalls[1],"exact_graphs":sum(r["exact"] for r in rows),"scenarios":sum(r["scenarios"] for r in rows),
            "masked_edge_map":sum(r["AP_sum"] for r in rows)/n,"ranked_edge_targets":n,
            "positive_candidate_fraction":sum(r["edge_density_sum"] for r in rows)/n,"details":rows}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--workers",type=int,choices=(1,2,3,4),default=2)
    args=parser.parse_args()
    protocol=json.loads(DATA.read_bytes())
    def families(split):
        return {s["family"] for s in protocol[split]}
    if families("train") & families("test"):
        raise ValueError("Overlapping graph families")
    with ProcessPoolExecutor(args.workers) as pool:
        training=list(pool.map(examples,protocol["train"]))
        w,initial,losses=train(training,protocol)
        # No validation or test objects participate in fitting or model selection.
        test=list(pool.map(examples,protocol["test"]))
    obj={"schema":"nabt.graph-intervention-weights.v1","parameters":w,"spaces":list(net.SPACES),"roles":list(net.ROLES),
         "split_sha256":sha256(DATA.read_bytes()).hexdigest(),"seed":protocol["seed"],"hidden":net.HIDDEN}
    report={"schema":"nabt.graph-intervention-evaluation.v1","test":summarize([score(s,w) for s in test]),
            "no_messages":summarize([score(s,w,True) for s in test]),"untrained":summarize([score(s,initial) for s in test]),
            "always_unchanged_indirect_balanced_accuracy":.5,"train":summarize([score(s,w) for s in training]),
            "training_loss_first_last":losses,"train_families":sorted(families("train")),"test_families":sorted(families("test")),
            "world_truth_established":False,"neural_authority":"NONE"}
    args.output.mkdir(parents=True,exist_ok=False)
    for name,value in (("model.json",obj),("evaluation.json",report)):
        (args.output/name).write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:report["test"][k] for k in ("balanced_accuracy","recall_lost","masked_edge_map","exact_graphs","scenarios")}))


if __name__=="__main__":
    main()
