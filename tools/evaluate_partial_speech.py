"""Replay a frozen paired speech experiment on either checkout through the public gateway."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
import json
from pathlib import Path

from tools.grammar_catalog import gateway
from tools.grammar_catalog.operations import ROOT, digest


def replay(row):
    req = {"schema":gateway.REQUEST_SCHEMA,"route":row.get("route","relations.analyze"),
           "payload":{"text":row["text"],"licensed_speech":{}}}
    receipt = gateway.run(req)
    verified = gateway.accept_output(receipt,expected_request=req)
    if not verified["valid"]:
        raise RuntimeError((row["id"],receipt["status"],verified,receipt["execution"].get("error")))
    owner = receipt["execution"]["owner_result"]
    graph = owner["licensed_speech"]
    readings = graph.get("decoded",[])
    actual = list(dict.fromkeys(r["force"] for r in readings))
    expected = [] if row["expected"]=="OPEN" else row["expected"].split("+")
    for reading in readings:
        for role in reading["roles"]:
            if row["text"].encode()[slice(*role["utf8_span"])].decode()!=role["surface"]:
                raise ValueError(("detached role",row["id"]))
    return {**row,"expected_sequence":expected,"actual":actual,"match":actual==expected,
            "neural_top":graph.get("neural",{}).get("top"),"request":req,"replay":verified["status"],
            "snapshot":receipt["snapshot_sha256"],"graph_sha256":digest(graph),"readings":readings,
            "obligations":graph.get("partial_speech",{}),"world":graph.get("world_truth_established",False)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases",type=Path,default=ROOT/"evidence/partial_speech_v1/paired.tsv")
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--workers",type=int,choices=range(1,5),default=2)
    args=parser.parse_args()
    with args.cases.open(encoding="utf-8") as f:
        cases=list(csv.DictReader(f,delimiter="\t"))
    with ProcessPoolExecutor(args.workers) as pool:
        rows=list(pool.map(replay,cases))
    if len({r["snapshot"] for r in rows})!=1 or any(r["world"] for r in rows):
        raise RuntimeError("Unstable snapshot or world promotion")
    groups={}
    for key in dict.fromkeys(r["split"] for r in rows):
        part=[r for r in rows if r["split"]==key]
        single=[r for r in part if len(r["expected_sequence"])==1]
        groups[key]={"n":len(part),"matches":sum(r["match"] for r in part),
                     "open":sum(not r["actual"] for r in part),"wrong_license":sum(bool(r["actual"]) and not r["match"] for r in part),
                     "neural_exact":sum(r["neural_top"]==r["expected"] for r in single),"neural_n":len(single)}
    with args.output.open("x",encoding="utf-8") as dest:
        json.dump({"groups":groups,"rows":rows},dest,ensure_ascii=False,indent=2)
    print(groups)


if __name__=="__main__":
    main()
