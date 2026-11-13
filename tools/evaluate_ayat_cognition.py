"""Paired source/context interventions and out-of-training question-family ranking via verified receipts."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path

from tools.grammar_catalog import gateway
from tools.grammar_catalog.ayat_al_dayn import source
from tools.lexical_training import ayat_questions as q


def cases():
    probes=q.rows(q.DATA/"probes.tsv")
    if {r["question"] for r in probes}&{r["question"] for r in q.rows(q.DATA/"train.tsv")}:
        raise ValueError("Overlapping questions")
    changes=[{},{"withdraw_context":["quran_attribution"]},{"withdraw_context":["human_disposition"]},
             {"withdraw":[1]},{"withdraw":[5]},{"withdraw":[11]},{"withdraw":[9]},
             {"withdraw":[54]},{"withdraw":[62]},{"withdraw":[97]},{"withdraw":[109]},{}]
    for i,(query,change) in enumerate(zip(probes,changes,strict=True)):
        yield i,query,{"schema":gateway.REQUEST_SCHEMA,"route":"ayat.read",
                       "payload":{"text":source(),"question":query["question"],**change}}


def check(job):
    i,query,request=job
    r=gateway.run(request)
    if not gateway.accept_output(r,expected_request=request)["valid"]:
        raise ValueError((i,r["status"],r.get("execution",{}).get("error")))
    result=r["execution"]["owner_result"]
    cog=result["cognition"]
    ranking=cog["question_ranking"]["ranking"]
    place=next(n for n,row in enumerate(ranking,1) if row["family"]==query["family"])
    cm=[[0,0],[0,0]]
    for c in cog["claims"]:
        truth=int(c["state"]=="WITHDRAWN")
        cm[truth][int(c["loss_score"]>=.5)]+=1
    if result["legal_ruling_established"] or cog["derived_legal_rulings"]:
        raise ValueError("Authority promotion")
    return {"case":i,"request":request,"gold_family":query["family"],"ranking":ranking,"rank":place,"cm":cm,
            "lost":[c["id"] for c in cog["claims"] if c["state"]=="WITHDRAWN"],"graph_states":{
                c["id"]:c["state"] for c in cog["claims"]},"snapshot":r["snapshot_sha256"],"verified":True}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--workers",type=int,default=2,choices=(1,2,3,4))
    args=p.parse_args()
    with ProcessPoolExecutor(args.workers) as pool:
        rows=list(pool.map(check,cases()))
    if rows[0]["graph_states"]!=rows[-1]["graph_states"] or len({r["snapshot"] for r in rows})!=1:
        raise ValueError("Snapshot or restoration mismatch")
    cm=[[sum(r["cm"][a][b] for r in rows) for b in (0,1)] for a in (0,1)]
    summary={"verified_requests":len(rows),"claims_per_request":len(rows[0]["graph_states"]),
             "query_top1":sum(r["rank"]==1 for r in rows),"query_top3":sum(r["rank"]<=3 for r in rows),
             "query_mrr":sum(1/r["rank"] for r in rows)/len(rows),"claim_confusion_rows_kept_lost":cm,
             "exact_graphs":sum(r["cm"][0][1]+r["cm"][1][0]==0 for r in rows)}
    with args.output.open("x",encoding="utf-8") as f:
        json.dump({"summary":summary,"rows":rows},f,ensure_ascii=False,indent=2)
    print(summary)
