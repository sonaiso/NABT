"""Replay independently retained questions and verify their public receipts."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import json
from pathlib import Path

from tools.grammar_catalog import gateway
from tools.grammar_catalog.operations import ROOT

FIXTURE=ROOT/"evidence/interpretation_chains_v1/challenge.json"


def replay(item):
    route,case=item
    req={"schema":gateway.REQUEST_SCHEMA,"route":route,"payload":{"text":case["text"]}}
    receipt=gateway.run(req)
    verified=gateway.accept_output(receipt,expected_request=req)["valid"]
    row={"id":case["id"],"route":route,"text":case["text"],"verified":verified,"status":receipt["status"],"match":False}
    if not verified or receipt["status"]!="EXECUTED":return row
    result=receipt["execution"]["owner_result"].get("interpretation_chain")
    if not result:return row
    row["chain_status"]=result["status"]
    if "treatment" in case:
        found=result.get("method") or {}
        row["match"]=(found.get("treatment")==case["treatment"] and found.get("application_established") is False)
    else:
        changes=[x["status"] for x in result.get("changes",[])]
        reports=[x["observation_check"] for x in result.get("reports",[])]
        heard=[bool(x["receipt_evidence"]) for x in result.get("reports",[])]
        conflict_days=[v["day"] for v in result.get("conflicts",[])]
        arithmetic=[c.get("arithmetic_check",{}).get("receipt") or {} for c in result.get("changes",[])
                    if c["axis"]=="العدد" and c["status"] in {"INCREASED","DECREASED","SAME_ENDPOINTS"}]
        row.update(changes=changes,reports=reports,receipt_evidence=heard,conflict_days=conflict_days,
                   arithmetic_verified=[r.get("native_checked",False) for r in arithmetic])
        row["match"]=(result["status"]==case.get("status","SOURCE_RELATIVE_CHAIN")
                      and changes==case.get("changes",[]) and reports==case.get("reports",[])
                      and heard==case.get("receipt",[]) and all(row["arithmetic_verified"])
                      and conflict_days==case.get("conflict_days",[]) and all(r["native_checked"] for r in result.get("reports",[]))
                      and not result["limits"]["external_event_established"] and not result["limits"]["cause_established"])
    return row


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--workers",type=int,choices=range(1,7),default=3)
    args=p.parse_args()
    raw=FIXTURE.read_bytes();cases=json.loads(raw)
    conflict=next(r for r in cases if r["id"]=="conflicting")
    conflict["conflict_days"]=[2]
    lines=conflict["text"].splitlines()
    cases.append({"id":"conflict_without_other_day","text":"\n".join([lines[0],lines[2],lines[3]]),
                  "changes":[],"reports":[],"receipt":[],"conflict_days":[2]})
    methods=[{"id":k,"text":f"ما منهج «{term}»؟","treatment":"METHOD"}
             for k,term in [("reproduction","يتكاثر"),("presupposition","الاقتضاء"),("validity","الفاسد")]]
    requests=[("text.read",r) for r in cases+methods]+[("relations.analyze",cases[0]),("text.read",cases[0])]
    with ProcessPoolExecutor(args.workers) as ex:
        results=list(ex.map(replay,requests))
    restored=results[0]["match"] and results[0]==results[-1]
    report={"schema":"nabt.interpretation-chains.public-test.v1","n":len(results),"correct":sum(r["match"] for r in results),
            "restored":restored,"fixture_sha256":sha256(raw).hexdigest(),"cases":results}
    with args.output.open("x",encoding="utf8") as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write("\n")
    print(report["correct"],"/",report["n"],"restored",restored)
    if not all(r["match"] for r in results) or not restored:raise SystemExit(1)


if __name__=="__main__": main()
