"""Three learned proposals. No score may approve a sense or an indication."""
from hashlib import sha256
import json
import math
import re

from tools.grammar_catalog.operations import ROOT, exact_terms
from tools.grammar_catalog.dictionary_reading import letters
from .features import features

PATH="evidence/lexical_indication_learning_v1/weights.json"
MODEL_SHA="46273a2096a35c2a25409568b6739fba64791886cad894b6e7d8802e2de31bdb"
CLASSES=("mutabaqa","tadammun","iltizam","none")
BOUNDARY={"و","وقد","وهو","وهي","والجمع","والمصدر","وجمعها","وجمعه","وبابه","ومنه",
          "وقيل","قال","وهذا","فهو","وأنشد","ويقال","ويجمع","ويسمى","والأنثى","على"}
LINKERS={"أي","أيضا","هو","وهو","هي","وهي","بمعنى","بالكسر","بالضم","بالفتح"}
STARTERS={"ضد","لون","صاحب","حاسة","واحد","الذي","ذو","وعاء","طعم","عظم","وسادة"}
BINS=128


def stem(w):
    s=letters(w)
    if s.startswith("وال"): return s[3:]
    if s.startswith("ال"): return s[2:]
    return s


def span_candidates(raw, bounds, lemma):
    """Search spans inside the entry; only heading/lemma, never gold offsets, are inputs."""
    a,b=bounds
    # Tokenization is on a bounded prefix, at a UTF-8 boundary.
    stop=min(b,a+8192)
    if stop<b:
        # Avoid turning a truncated token into a proposed dictionary witness.
        while stop>a and raw[stop:stop+1] not in (b" ",b"\n",b"\t"):
            stop-=1
    data=raw[a:stop].decode()
    tokens=exact_terms(data)[:100]
    surfaces=[t["surface"] for t in tokens]
    heads=[i for i,w in enumerate(surfaces) if stem(w)==letters(lemma)]
    result=[]
    for start,t in enumerate(tokens):
        before=[i for i in heads if i<start and start-i<=12]
        if not before: continue
        gap=start-before[-1]
        left=surfaces[start-1]
        for end in range(start,min(len(tokens),start+7)):
            u=tokens[end]
            x,y=t["codepoint_span"][0],u["codepoint_span"][1]
            span=data[x:y]
            if not re.fullmatch(r"[ء-يَ-ْ]+(?: [ء-يَ-ْ]+)*",span):break
            following=surfaces[end+1] if end+1<len(tokens) else ""
            length=end-start+1
            selected=surfaces[start:end+1]
            vector=[1., gap==1,gap==2,gap<=4,1/gap,left in LINKERS,left in BOUNDARY,
                    surfaces[start] in STARTERS,stem(surfaces[start])==letters(lemma),
                    following in BOUNDARY,following.startswith("و"),not following,
                    sum(w in BOUNDARY for w in selected),sum(w.startswith("و") and len(w)>2 for w in selected[1:]),
                    following in LINKERS,length==1,length==2,length==3,length/7,
                    selected[-1] in LINKERS, selected[-1] in ("في","على","ذو","من","حين","ضد"),
                    surfaces[start] in ("و","أيضا","أي","بوزن","بالضم","بالكسر","بالفتح"),
                    following in ("في","إلى","به","له","ذو","كله"), selected[-1] in ("و","هي","هو")]
            result.append(([a+t["utf8_span"][0],a+u["utf8_span"][1]],span,vector))
    return result


def context_vector(text):
    # Preserve the written source in the receipt. The learner sees word/character
    # features of the surrounding context with common function words downweighted.
    s=" ".join(stem(t["surface"]) for t in exact_terms(text) if t["surface"] not in {"في","من","على","إلى","كان"})
    fs=features(s,BINS)
    norm=math.sqrt(sum(x*x for x in fs.values())) or 1.
    return [fs.get(i,0)/norm for i in range(BINS)]


def similarity(a,b):
    x,y=set(a.split()),set(b.split())
    return len(x&y)/max(1,len(x|y))


def relation_features(components,target,necessities):
    c,t=set(components),set(target)
    overlap=len(c&t)
    # Necessities are evidence read separately from the selected dictionary sense.
    # The learner receives the witness target strings, never a native verdict.
    expr=" ".join(target)
    return [1., len(t)/max(1,len(c)), overlap/max(1,len(c)), overlap/max(1,len(t)),
            max((similarity(expr,k) for k in c),default=0.),len(c)>1,len(t)>1,
            max((similarity(expr,k) for k in necessities),default=0.),bool(necessities),not t]


def dot(a,b): return sum(x*y for x,y in zip(a,b,strict=True))


def scores(readings,target,model):
    result=[]
    for r in readings:
        x=relation_features(r["components"],r["target"],[n["target"] for n in r.get("necessity_records",[])])
        logits=[dot(x,w) for w in model["relation"]]
        top=max(logits)
        winners=[label for label,v in zip(CLASSES,logits) if v==top]
        result.append({"sense_id":r["sense_id"],"kind":winners[0] if len(winners)==1 else None})
    return result


def extract(raw,rows,w):
    seen=set()
    out=[]
    for r in rows:
        key=(r["lemma"],*r["entry_span"])
        if key in seen:continue
        seen.add(key)
        candidates=span_candidates(raw,r["entry_span"],r["lemma"])
        ranked=sorted(candidates,key=lambda v:(-dot(v[2],w),v[0]))
        out.append({"lemma":r["lemma"],"root":r["root"],"window":r["entry_span"],"candidates_examined":len(candidates),
                    "top_spans":[{"span":s,"text":g} for s,g,_ in ranked[:3]]})
    return out


def rank(context,rows,weights):
    x=context_vector(context)
    rivals=[r for r in rows if r["id"] in weights]
    # Never silently ignore a competitor lacking fitted parameters.
    if len(rivals)!=len(rows) or len(rivals)<2:
        return {"status":"NO_TRAINED_COMPETITION","ordered":[]}
    ordered=sorted(((dot(x,weights[r["id"]]),r["id"]) for r in rivals),reverse=True)
    tied=ordered[0][0]==ordered[1][0]
    return {"status":"TIE" if tied else "PROPOSED","ordered":["mukhtar:"+sid for _,sid in ordered],
            "top":None if tied else "mukhtar:"+ordered[0][1]}


def propose(raw,rows,readings,context,target):
    try:
        data=(ROOT/PATH).read_bytes()
        if sha256(data).hexdigest()!=MODEL_SHA:raise ValueError("CHECKPOINT_CHANGED")
        model=json.loads(data)
        return {"status":"AVAILABLE","authority":"NONE","model_sha256":MODEL_SHA,
                "extractive":extract(raw,rows,model["span"]),
                "context":rank(context,rows,model["context"]) if context else {"status":"NO_CONTEXT"},
                "relations":scores(readings,target,model) if target else []}
    except (OSError,ValueError) as err:
        return {"status":"MODEL_UNAVAILABLE","authority":"NONE","reason":str(err)}
