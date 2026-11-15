"""Fit the four shared heads and measure frozen lexical, construction and voice transfers."""
import argparse
from base64 import b64encode
from collections import Counter,defaultdict
import csv
from hashlib import sha256
import json
from pathlib import Path
from zlib import compress

from tools.grammar_catalog import awamil_occurrence as law
from tools.grammar_catalog.operations import exact_terms, ROOT
from . import awamil_occurrence_model as net

DIR=ROOT/"evidence/awamil_occurrence_v1"
SEED=2718


def token_index(terms,span):
    if span is None:
        return 0
    return next(i for i,t in enumerate(terms,1) if t["utf8_span"][0]<=span[0]<t["utf8_span"][1])


def sample(p,regex,text):
    b=law.bound_fields(text,regex.fullmatch(text))
    terms=exact_terms(text)
    g=b.get("cue") if p.sense and p.polarity=="deny" else b.get("g")
    return {"text":text,"factor":p.factor,"relation":p.relation,
            "governor":token_index(terms,g["utf8_span"] if g else None),
            "dependent":token_index(terms,law.primary_span(p,b))}


def rows(split):
    bank,patterns=law.curriculum()
    result={}
    for p,regex in patterns:
        if p.sense and ((p.sense=="break") != (split=="event")):
            continue
        if not p.sense and split=="event":
            continue
        for j in range(12 if split=="train" else 4):
            def field(m):
                role,val=m.groups()
                if not val.startswith("$"):
                    return val
                options=bank["slots"][val[1:]]
                if p.sense and val[1:].startswith(p.sense+"_"):
                    choices=options if split=="event" else options[:2] if split=="train" else options[2:]
                else:
                    choices=options[:4] if split=="train" else options[4:]
                offset=j if role in ("actor","subject","patient","predicate") else j//2
                if role=="predicate" and "subject=" in p.template:
                    offset=j//3
                return choices[offset%len(choices)]
            text=law.FIELDS.sub(field,p.template)
            row=sample(p,regex,text)
            if text in result and row!=result[text]:
                raise ValueError("Ambiguous training gold: "+text)
            result[text]=row
    return list(result.values())


def blank(text):
    return {"text":text,"factor":0,"relation":"OUTSIDE","governor":0,"dependent":0}


def pack(a):
    import numpy as np
    scale=float(np.max(np.abs(a)))/127 or 1.
    q=np.rint(a/scale).clip(-127,127).astype("int8")
    return {"shape":list(a.shape),"scale":scale,"q":b64encode(compress(q.tobytes(),9)).decode()}


def fit(train):
    import numpy as np
    rng=np.random.default_rng(SEED)
    classes={k:sorted({r[k] for r in train}) for k in ("factor","relation","dependent","governor")}
    y={k:np.array([opts.index(r[k]) for r in train]) for k,opts in classes.items()}
    x=np.zeros((len(train),net.WIDTH))
    for i,r in enumerate(train):
        for col,n in net.observed(r["text"])[1].items():
            x[i,col]=n
    dim=48
    w={"projection":rng.normal(0,.12,(net.WIDTH,dim)),"bias":np.zeros((1,dim))}
    for key,opts in classes.items():
        w[key]=rng.normal(0,.1,(dim,len(opts)))
        w[key+"_bias"]=np.zeros((1,len(opts)))
    mom={k:np.zeros_like(v) for k,v in w.items()}
    vel={k:np.zeros_like(v) for k,v in w.items()}
    for t in range(1,201):
        h=np.tanh(x@w["projection"]+w["bias"])
        dh=np.zeros_like(h)
        grad={}
        for k in classes:
            logits=h@w[k]+w[k+"_bias"]
            prob=np.exp(logits-logits.max(axis=1,keepdims=True))
            prob/=prob.sum(axis=1,keepdims=True)
            prob[np.arange(len(x)),y[k]]-=1
            delta=prob/(len(x)*len(classes))
            grad[k]=h.T@delta
            grad[k+"_bias"]=delta.sum(axis=0,keepdims=True)
            dh+=delta@w[k].T
        dz=dh*(1-h*h)
        grad["projection"]=x.T@dz
        grad["bias"]=dz.sum(axis=0,keepdims=True)
        for k,d in grad.items():
            mom[k]=.9*mom[k]+.1*d
            vel[k]=.999*vel[k]+.001*d*d
            w[k]-=.025*(mom[k]/(1-.9**t))/(np.sqrt(vel[k]/(1-.999**t))+1e-8)
    return {"schema":"nabt.awamil-occurrence.model.v1","classes":classes,"weights":{k:pack(v) for k,v in w.items()},
            "training_examples":len(train),"seed":SEED,"epochs":200,"training_sha256":fingerprint(train),
            "curriculum_sha256":dict(law.SOURCES),"authority":"PROPOSAL_ONLY"}


def fingerprint(rows):
    return sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def dump(path,value):
    with path.open("x",encoding="utf-8") as f:
        f.write(json.dumps(value,ensure_ascii=False,separators=(",",":"))+"\n")


def evaluate(fitted,train,tests):
    first_token=defaultdict(Counter)
    for r in train:
        first_token[exact_terms(r["text"])[0]["surface"]][r["factor"]]+=1
    results=[]
    for row in tests:
        predicted=net.predict(row["text"],fitted)
        baseline=first_token[exact_terms(row["text"])[0]["surface"]].most_common(1)
        keys=[k for k in ("factor","relation","dependent","governor") if k in row]
        correct={k:row[k]==predicted[k] for k in keys}
        results.append({"text":row["text"],"gold":{k:row[k] for k in keys},"prediction":{k:predicted[k] for k in keys},
                        "correct":correct,"joint":all(correct.values()),"baseline_factor":bool(baseline and baseline[0][0]==row["factor"])})
    counts={k:sum(r["correct"].get(k,False) for r in results) for k in results[0]["correct"]}
    per_factor={str(i):{"total":sum(r["gold"]["factor"]==i for r in results),
                         "joint":sum(r["joint"] and r["gold"]["factor"]==i for r in results)}
                for i in sorted({r["gold"]["factor"] for r in results})}
    return {"n":len(results),"correct":counts,"joint":sum(r["joint"] for r in results),
            "baseline_factor":sum(r["baseline_factor"] for r in results),"per_factor":per_factor,
            "heldout_sha256":fingerprint(tests),"cases":results}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    train=rows("train")
    positives=len(train)
    train.extend(blank("«"+r["text"]+"»") for r in train[:positives:3])
    lexical=rows("heldout")
    controls=[blank(s) for s in json.loads((DIR/"contrast.json").read_bytes())["controls"]]
    novel=[{"text":r["text"],"factor":int(r["id"])} for r in csv.DictReader((DIR/"novel.tsv").read_text().splitlines(),delimiter="\t")]
    probes={"lexical":lexical,"reserved_event":rows("event"),"novel_wording":novel,"controls":controls}
    seen={r["text"] for r in train}
    if any(seen.intersection(r["text"] for r in split) for split in probes.values()):
        raise ValueError("Train and evaluation overlap")
    raw_model=fit(train)
    checkpoint=args.output/"weights.json"
    dump(checkpoint,raw_model)
    raw=checkpoint.read_bytes()
    fitted=net.decode(raw)
    report={k:evaluate(fitted,train,v) for k,v in probes.items()}
    dump(args.output/"evaluation.json",{"model_sha256":sha256(raw).hexdigest(),"train_n":len(train),
         "positive_train_n":positives,"factor_ids_seen":sorted({r["factor"] for r in train if r["factor"]}),"sets":report})
    print(sha256(raw).hexdigest(),len(train),{k:(v["n"],v["correct"],v["joint"]) for k,v in report.items()})


if __name__=="__main__":
    main()
