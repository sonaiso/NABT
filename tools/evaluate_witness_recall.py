"""Authored held-frame challenge. Gold comes from cue construction, independently of the readout."""
import argparse
from collections import Counter
from itertools import product
from pathlib import Path
import json
from tools.grammar_catalog import question_cognition as cognition, gateway
from tools.lexical_training import witness_recall as recall, question_ranking


FRAMES=(("سيرسم الرسام الخط","القلم","وصل"),("سيقيس الفني الطول","المسطرة","وصلت"))
CONFIGS=(("i",),("c",),("i","c"),("c","i"),("ni","c"),("c","nc"),("i","ni"),("i","nc"))
OPS=("instrument","condition","joint","occurrence")


def reference(op,cues):
    axes={"instrument":("i",),"condition":("c",),"joint":("i","c"),"occurrence":("o",)}[op]
    polarity={k:{not c.startswith("n") for c in cues if c.lstrip("n")==k} for k in axes}
    if any(len(v)>1 for v in polarity.values()):
        return "CONFLICT"
    if any(v=={False} for v in polarity.values()):
        return "REFUTED"
    return "SUPPORTED" if all(v=={True} for v in polarity.values()) else "OPEN"


def evaluate():
    counts=Counter()
    by_question={}
    cases=[]
    for (head,inst,arrival),cues,op in product(FRAMES,CONFIGS,OPS):
        phrases={"i":"ب"+inst,"ni":"دون استعمال "+inst,"c":"إذا "+arrival+" "+inst,"nc":"دون اشتراط وصول "+inst}
        surface=[phrases[c] for c in cues]
        text=head+" "+" ".join(surface)+"."
        relevant={"instrument":"i","condition":"c","joint":"ic","occurrence":"o"}[op]
        eligible=[i for i,c in enumerate(cues) if c.lstrip("n") in relevant]
        truth=reference(op,cues)
        for q in cognition.QUESTIONS[op]:
            r=recall.recall(text,q)
            p=r["proposal"]
            if p["status"]!="PROPOSED":
                raise ValueError("Unmeasured readout")
            picked=p["rows"][0]["index"]
            q_dist=p["question_distribution"]
            by_question[q]={"reference":op,"neural":max(q_dist,key=q_dist.get),
                            "existing_ranker":question_ranking.propose(q)["ranking"][0]}
            selected=r["decoding"]["selected_indices"]
            subset=[cues[i] for i in selected]
            minimal=reference(op,subset)==truth and all(reference(op,subset[:j]+subset[j+1:])!=truth for j in range(len(subset)))
            valid=(r["status"]==truth and r["decoding"]["grade"]["complete"] and minimal
                   and (truth!="OPEN" or len(r["decoding"]["countermodels"])==2))
            counts["complete"]+=int(valid)
            if eligible:
                counts["eligible"]+=1
                counts["top1"]+=int(picked in eligible)
                counts["position"]+=int(0 in eligible)
                overlap=[len(set(q.split()) & set(s.split())) for s in surface]
                counts["overlap"]+=int(max(range(len(surface)),key=overlap.__getitem__) in eligible)
                counts["one_complete"]+=int(truth!="OPEN" and reference(op,[cues[picked]])==truth)
            cases.append({"text":text,"question":q,"operation":op,"reference":truth,"eligible":eligible,
                          "neural_top1":picked,"selected_indices":selected,"checked_status":r["status"],
                          "complete":valid})
    return {"schema":"nabt.witness-recall-evaluation.v1","requests":len(cases),"counts":dict(counts),
            "unique_questions":by_question,"rows":cases}


def public():
    q=cognition.QUESTIONS
    base="سيفتح الحارس الباب"
    cases=[(base+" بالمفتاح إذا وصل المفتاح.",q["joint"][0],"SUPPORTED"),
           (base+" إذا وصل المفتاح.",q["instrument"][0],"OPEN"),
           (base+" بالمفتاح دون استعمال المفتاح.",q["instrument"][0],"CONFLICT"),
           (base+" دون استعمال المفتاح.",q["instrument"][1],"REFUTED"),
           (base+" بالمفتاح.",q["occurrence"][0],"OPEN"),
           (base+" بالمفتاح إذا وصل المفتاح.",q["joint"][0],"SUPPORTED")]
    results=[]
    for text,question,expected in cases:
        req={"schema":gateway.REQUEST_SCHEMA,"route":"text.read","payload":{"text":text,"question":question,"witness_recall":True}}
        receipt=gateway.run(req)
        checked=gateway.accept_output(receipt,expected_request=req)
        if receipt["status"]!="EXECUTED" or not checked["valid"]:
            raise ValueError("Unverified public request")
        r=receipt["execution"]["owner_result"]["witness_recall"]
        if r["status"]!=expected:
            raise ValueError("Unexpected semantic status")
        results.append({"request":req,"verified":checked["status"],"result":r})
    if results[0]!=results[-1]:
        raise ValueError("Restoration changed the original decision or witnesses")
    return results


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output",type=Path,required=True)
    cli.add_argument("--public",action="store_true")
    args=cli.parse_args()
    result=public() if args.public else evaluate()
    with args.output.open("x",encoding="utf-8") as f:
        json.dump(result,f,indent=2,ensure_ascii=False);f.write("\n")
    print("Verified public requests:",len(result)) if args.public else print(result["counts"])
