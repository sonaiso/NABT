"""Train three likelihoods on retained sources; measure extraction, usage ranking, indication separately."""
import argparse
from collections import defaultdict
import csv
from hashlib import sha256
import json
from pathlib import Path

from tools import lexical_testimony
from tools.grammar_catalog import dictionary_reading as law
from . import dictionary_indication as net

DIR=law.ROOT/"evidence/lexical_indication_learning_v1"


def read_tsv(path):
    return list(csv.DictReader(path.read_text().splitlines(),delimiter="\t"))


def write(path,obj):
    with path.open("x",encoding="utf8") as f:
        f.write(json.dumps(obj,ensure_ascii=False,separators=(",",":"),allow_nan=False)+"\n")


def fingerprint(obj):
    return sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def span_trial(raw,rows,held):
    import numpy as np
    groups=defaultdict(list)
    for r in rows:groups[(r["root"],r["lemma"])].append(r)
    training=[]
    for (root,lemma),rs in groups.items():
        if root in held:continue
        candidates=net.span_candidates(raw,rs[0]["entry_span"],lemma)
        gold={tuple(r["gloss_span"]) for r in rs}
        x=np.array([v[2] for v in candidates])
        y=np.array([tuple(v[0]) in gold for v in candidates],dtype=float)
        if not y.any():raise ValueError("Training gloss unreachable: "+lemma)
        training.append((x,y/y.sum()))
    w=np.zeros(training[0][0].shape[1])
    for step in range(550):
        grad=np.zeros_like(w)
        for x,y in training:
            v=x@w
            p=np.exp(v-v.max());p/=p.sum()
            grad+=(p-y)@x
        w-=.32*(grad/len(training)+.0005*w)
    cases=[]
    for (root,lemma),rs in groups.items():
        if root not in held:continue
        r=net.extract(raw,rs,w)[0]
        predicted=[tuple(a["span"]) for a in r["top_spans"]]
        for s in rs:
            gold=tuple(s["gloss_span"])
            first=net.span_candidates(raw,s["entry_span"],lemma)
            baseline=next((a[0] for a in first if len(a[1].split())==1),None)
            cases.append({"id":s["id"],"root":root,"lemma":lemma,"gold":list(gold),"gloss":s["gloss"],
                          "top":r["top_spans"],"top1":bool(predicted and predicted[0]==gold),
                          "top3":gold in predicted,"first_token_baseline":baseline==list(gold),
                          "reachable":any(a[0]==list(gold) for a in first)})
    return w.tolist(),{"training_lemmas":len(training),"heldout_senses":len(cases),"cases":cases,
                        **{k:sum(c[k] for c in cases) for k in ("top1","top3","first_token_baseline","reachable")}}


def usage_trial(rows):
    import numpy as np
    train,test=(read_tsv(DIR/name) for name in ("usage_train.tsv","usage_test.tsv"))
    if {r["text"] for r in train}&{r["text"] for r in test}:raise ValueError("Context overlap")
    by_id={r["id"]:r for r in rows}
    labels=sorted({r["sense"] for r in train})
    by_lemma=defaultdict(list)
    for i,sid in enumerate(labels):by_lemma[by_id[sid]["lemma"]].append(i)
    w=np.zeros((len(labels),net.BINS))
    xs=np.array([net.context_vector(r["text"]) for r in train])
    for _ in range(450):
        grad=np.zeros_like(w)
        for x,r in zip(xs,train):
            ids=by_lemma[by_id[r["sense"]]["lemma"]]
            v=w[ids]@x
            p=np.exp(v-v.max());p/=p.sum()
            p[ids.index(labels.index(r["sense"]))]-=1
            grad[ids]+=p[:,None]*x
        w-=1.8*(grad/len(train)+.001*w)
    weights={sid:w[i].tolist() for i,sid in enumerate(labels)}
    result=[]
    for r in test:
        group=[s for s in rows if s["lemma"]==by_id[r["sense"]]["lemma"]]
        pred=net.rank(r["text"],group,weights)
        result.append({**r,"prediction":pred.get("top"),"first_sense_baseline":group[0]["id"]==r["sense"],
                       "correct":pred.get("top")=="mukhtar:"+r["sense"]})
    return weights,{"train":len(train),"n":len(result),"correct":sum(r["correct"] for r in result),
                    "baseline":sum(r["first_sense_baseline"] for r in result),"cases":result}


def relation_trial(rows,held):
    import numpy as np
    raw=(law.ROOT/lexical_testimony.CATALOG).read_bytes()
    if sha256(raw).hexdigest()!=lexical_testimony.CATALOG_SHA:
        raise ValueError("Denotation catalogue identity differs")
    cat=json.loads(raw)
    for row in cat["senses"]+cat["necessities"]:
        lexical_testimony._citation(row["citation"],law.ROOT)
    mental={r["sense_id"]:[r["target"]] for r in cat["necessities"]}
    bank=[dict(id="mukhtar:"+r["id"],root=r["root"],components=r["components"]) for r in rows]+cat["senses"]
    pool=set(c for s in bank if s["root"] not in held for c in s["components"])
    train,test=[],[]
    for s in bank:
        parts=s["components"]
        links=mental.get(s["id"],[])
        distractor=next(c for c in sorted(pool) if c not in parts and c not in links)
        examples=[(parts,"mutabaqa",links),([distractor],"none",links),([],"none",links)]
        if len(parts)>1:examples.extend(([c],"tadammun",links) for c in parts)
        for k in links:
            examples.extend([([k],"iltizam",links),([k],"none",[])])
        if not links:examples.append((["ضروري في الواقع"],"none",[]))
        for target,kind,ledger in examples:
            dest=test if s["root"] in held else train
            dest.append((s["id"],parts,target,ledger,kind))
    x=np.array([net.relation_features(c,t,n) for _,c,t,n,_ in train])
    y=np.array([net.CLASSES.index(r[-1]) for r in train])
    w=np.zeros((len(net.CLASSES),x.shape[1]))
    for _ in range(1450):
        v=x@w.T
        p=np.exp(v-v.max(axis=1,keepdims=True));p/=p.sum(axis=1,keepdims=True)
        p[np.arange(len(y)),y]-=1
        # Macro-class weighting keeps the sole training necessity visible.
        p*= (len(y)/(len(net.CLASSES)*np.bincount(y)[y]))[:,None]
        w-=.45*(p.T@x/len(y)+.0002*w)
    out=[]
    for sid,c,t,ledger,kind in test:
        v=w@net.relation_features(c,t,ledger)
        got=net.CLASSES[int(np.argmax(v))]
        out.append({"id":sid,"target":t,"mental_witness":ledger,"expected":kind,"predicted":got,"correct":kind==got})
    return w.tolist(),{"train":len(train),"n":len(out),"correct":sum(r["correct"] for r in out),
                       "by_kind":{k:{"n":sum(r["expected"]==k for r in out),"correct":sum(r["expected"]==k and r["correct"] for r in out)}
                                  for k in net.CLASSES},"cases":out}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    dest=p.parse_args().output
    dest.mkdir(parents=True,exist_ok=True)
    protocol=json.loads((DIR/"protocol.json").read_bytes())
    raw,rows=law.resources()
    span,s=span_trial(raw,rows,set(protocol["span_heldout_roots"]))
    context,c=usage_trial(rows)
    relation,r=relation_trial(rows,set(protocol["relation_heldout_roots"]))
    model={"schema":"nabt.dictionary-learning.v1","span":span,"context":context,"relation":relation,
           "source_sha256":law.SOURCE_SHA,"alignment_sha256":law.MEMBERS_SHA,"protocol_sha256":fingerprint(protocol),
           "denotation_catalog_sha256":lexical_testimony.CATALOG_SHA,
           "context_training_sha256":sha256((DIR/"usage_train.tsv").read_bytes()).hexdigest()}
    write(dest/"weights.json",model)
    digest=sha256((dest/"weights.json").read_bytes()).hexdigest()
    write(dest/"evaluation.json",{"schema":"nabt.dictionary-learning.evaluation.v1","model_sha256":digest,
           "span":s,"context":c,"relation":r})
    print(digest)
    for result in (s,c,r):print({k:v for k,v in result.items() if k!="cases"})


if __name__=="__main__":main()
