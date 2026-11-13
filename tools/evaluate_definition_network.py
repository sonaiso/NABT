"""Independently replay the frozen definition questions and focused revision controls."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
import json
from pathlib import Path

from tools.grammar_catalog import gateway, definition_network as net

DATA=net.ROOT/"evidence/definition_inheritance_v1"


def cases():
    with (DATA/"challenge.tsv").open() as f:
        rows=[{**r,"route":"text.read"} for r in csv.DictReader(f,delimiter="\t")]
    rows.extend([
        {"text":"ما شبكة «القانئ» بعد سحب شاهد «اللون هيئة كالسواد والحمرة»؟","route":"text.read",
         "required":"A:أحمر,P:حمرة,P:شدة_الحمرة,P:لون","forbidden":"P:هيئة"},
        {"text":"ما شبكة «النمرقة» بعد سحب شاهد «المخدة بالكسر الوسادة يوضع عليها الخد»؟","route":"text.read",
         "required":"G:وسادة,A:صغير","forbidden":"P:إسناد_الخد"},
        {"text":"ما معنى «النمرقة»؟","route":"text.read","required":"G:وسادة,P:إسناد_الخد","forbidden":"-"},
        {"text":"ما شبكة «القانئ»؟","route":"relations.analyze","required":"A:أحمر,P:حمرة,P:هيئة","forbidden":"A:أبيض"},
        {"text":"ما شبكة «القانئ»؟","route":"text.read","required":"A:أحمر,P:حمرة,P:هيئة","forbidden":"A:أبيض"}])
    return rows


def replay(case):
    text=case["text"]
    req={"schema":gateway.REQUEST_SCHEMA,"route":case["route"],"payload":{"text":text}}
    rec=gateway.run(req)
    valid=gateway.accept_output(rec,expected_request=req)["valid"]
    result={"text":text,"route":case["route"],"status":rec["status"],"verified":valid,"match":False}
    if rec["status"]!="EXECUTED" or not valid:return result
    view=rec["execution"]["owner_result"]
    g=view.get("definition_network")
    if not g:return result
    reads={r["focus"]:r for r in g["readings"]}
    known="ززز" not in text
    ok=g["status"]==("VERIFIED_CONDITIONAL_NETWORK" if known else "NO_REVIEWED_NETWORK")
    if known:
        ok &= bool(reads) and all(r["ground_check"]["receipt"]["verified"] for r in reads.values())
    required=set(case["required"].split(","))-{"-"}
    forbidden=set(case["forbidden"].split(","))-{"-"}
    out={}
    for focus,r in reads.items():
        coords={v["node"] for v in r["claims"]}
        ok &= required<=coords and not coords&forbidden
        ok &= {k for k,v in zip(r["vector"]["basis"],r["vector"]["mask"],strict=True) if v}==coords
        out[focus]={"nodes":sorted(coords),"paths":{c["relation"]+"/"+c["node"]:c["proofs"] for c in r["claims"]}}
    if "الصلب" in text:
        ok = (ok and set(reads)=={"A:صلب","G:صلب"}
              and set(out["A:صلب"]["nodes"])=={"A:شديد"}
              and set(out["G:صلب"]["nodes"])=={"G:عظم","P:ذو_فقار"})
    if text.startswith("ما معنى"):
        ok &= any(c["evidence"].get("definition_network_ref")=="/definition_network/readings/0"
                  for c in view["cards"] if c["scope"]=="dictionary_sense")
    return {**result,"match":bool(ok and not g["world_truth_established"]),"readings":out,"graph_status":g["status"]}


def restored(rows):
    if not rows:
        return False
    final=rows[-1]
    baseline=next((r for r in rows[:-1] if (r["text"],r["route"])==(final["text"],final["route"])),None)
    return bool(baseline and baseline.get("match") and final.get("match")
                and baseline.get("readings") and baseline["readings"]==final.get("readings"))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--workers",type=int,choices=range(1,7),default=3)
    args=parser.parse_args()
    with ProcessPoolExecutor(args.workers) as pool:rows=list(pool.map(replay,cases()))
    restore=restored(rows)
    out={"schema":"nabt.definition-inheritance.evaluation.v1","n":len(rows),
         "correct":sum(r["match"] for r in rows),"restored":restore,"cases":rows}
    with args.output.open("x",encoding="utf-8") as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write("\n")
    print(out["correct"],"/",out["n"],"restored",restore)
    if not restore or out["correct"]!=len(rows):raise SystemExit(1)


if __name__=="__main__":main()
