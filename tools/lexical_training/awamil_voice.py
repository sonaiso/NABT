"""Factorized voice, scope and patient pointers for a short definite-noun frame."""
from hashlib import sha256
import json
import math

from nabt.corpus_evidence import lookup_clusters, lookup_key
from tools.grammar_catalog.operations import ROOT, exact_terms

PATH="evidence/awamil_occurrence_v1/voice_weights.json"
MODEL_SHA="c19312d9c43783d60932a225fdc5930f16e4e1154ecefe05ec0bbdaedac4e706"


def evidence(text):
    terms=exact_terms(text)
    if not 2<=len(terms)<=4 or text != " ".join(t["surface"] for t in terms):
        return None
    initial=terms[0]["surface"]
    cue=lookup_key(initial)=="لم"
    if len(terms)-int(cue) not in (2,3):
        return None
    verb=terms[int(cue)]["surface"]
    cs=lookup_clusters(verb)
    nouns=terms[int(cue)+1:]
    if not cs or len(cs)<3 or not cs[0][1] or not cs[-2][1]:
        return None
    noun_marks=[]
    for n in nouns:
        c=lookup_clusters(n["surface"])
        if not c or not lookup_key(n["surface"]).startswith("ال") or not c[-1][1]:
            return None
        m=c[-1][1]
        noun_marks.append([1.,float("ُ" in m),float("َ" in m),float("ِ" in m)])
    # Voice sees written verb marks only. Scope sees the initial operator
    # profile; neither sees the number/order or lexical identity of the nouns.
    voice=[1.,*map(float,("ُ" in cs[0][1],"َ" in cs[0][1],"ِ" in cs[-2][1],
                         "َ" in cs[-2][1],"ُ" in cs[-2][1],cs[0][0]=="ي"))]
    scope=[1.,float(cue),float(initial=="لَمْ")]
    return voice,scope,noun_marks,nouns


def dot(a,b):
    return sum(x*y for x,y in zip(a,b,strict=True))


def sigmoid(v):
    return 1/(1+math.exp(-v))


def infer(text,w):
    features=evidence(text)
    if features is None:
        return {"status":"OUTSIDE_WRITTEN_FRAME","authority":"NONE"}
    v,s,keys,terms=features
    voice=sigmoid(dot(w["voice"],v))
    neg=sigmoid(dot(w["scope"],s))
    query=[1.,voice]
    scores=[dot(query,[dot(weights,k) for weights in w["patient"]]) for k in keys]
    top=max(scores)
    weights=[math.exp(x-top) for x in scores]
    total=sum(weights)
    winners=[i for i,s in enumerate(scores) if s==top]
    if len(winners)!=1 or voice==.5 or neg==.5:
        return {"status":"DEFER","authority":"NONE"}
    return {"status":"PROPOSED","authority":"NONE","source_sha256":sha256(text.encode()).hexdigest(),
            "voice":"passive" if voice>.5 else "active","polarity":"deny" if neg>.5 else "assert",
            "patient_span":terms[winners[0]]["utf8_span"],"patient_surface":terms[winners[0]]["surface"],
            "attention":[{"span":t["utf8_span"],"weight":round(n/total,8)} for t,n in zip(terms,weights,strict=True)]}


def propose(text):
    if len(text.encode())>1024 or evidence(text) is None:
        return {"status":"OUTSIDE_WRITTEN_FRAME","authority":"NONE"}
    try:
        raw=(ROOT/PATH).read_bytes()
        if sha256(raw).hexdigest()!=MODEL_SHA:
            raise ValueError("Voice checkpoint identity differs")
        return {**infer(text,json.loads(raw)),"model_sha256":MODEL_SHA}
    except (ValueError,OSError) as e:
        return {"status":"MODEL_UNAVAILABLE","authority":"NONE","reason":str(e)}
