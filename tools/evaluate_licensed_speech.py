"""Measure held-out force, open readings, lexical joins and source revisions through the public gateway."""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import csv
import json
from pathlib import Path

from tools.grammar_catalog import gateway
from tools.grammar_catalog.operations import ROOT, digest
from tools.lexical_training.speech_force import LABELS, TRAIN

DATA = ROOT/"evidence/licensed_speech_v1"


def requests():
    with (DATA/"challenge.tsv").open(encoding="utf-8") as f:
        challenge = list(csv.DictReader(f,delimiter="\t"))
    with TRAIN.open(encoding="utf-8") as f:
        train = {r["text"] for r in csv.DictReader(f,delimiter="\t")}
    if train.intersection(r["text"] for r in challenge):
        raise ValueError("Training and challenge overlap")
    def req(payload,route="relations.analyze"):
        return {"schema":gateway.REQUEST_SCHEMA,"route":route,"payload":{"licensed_speech":{},**payload}}
    for r in challenge:
        yield r["case"], req({"text":r["text"]}), r["force"]
    for i,(text,entry,target,mode) in enumerate([("فَرَس","فرس","واحد الخيل","mutabaqa"),("إِنْسَان","إنسان","حيوان","tadammun"),
        ("عَمَى","عمي","البصر","iltizam"),("قَلَم","قلم","الذي يكتب به","mutabaqa"),("فَرَس","عمي","البصر",None)]):
        yield "lexical/"+str(i), req({"text":text,"licensed_speech":{"lexical":{"entry":entry,"target":[target]}}}), mode
    ctx=json.loads((ROOT/"examples/io_gateway/valency_context.json").read_text())["payload"]
    for tag in ("full","no_place","restore"):
        p=json.loads(json.dumps(ctx))
        if tag=="no_place":
            p["valency_context"]["ledger"]="".join(l for l in p["valency_context"]["ledger"].splitlines(keepends=True) if " مكان " not in l)
        yield "ledger/"+tag,req(p),None
    yield "display",json.loads((ROOT/"examples/io_gateway/licensed_speech.json").read_text()),"ask"
    for case,text,force in (("order","اِفْتَحِ الصُّنْدُوقَ بِالْمِفْتَاحِ","request"),
                            ("prohibition","لَا تَفْتَحِ الصُّنْدُوقَ بِالْمِفْتَاحِ","prohibit")):
        yield "directive/"+case,req({"text":text}),force
    yield "genus",req({"text":"ما شبكة «النمرقة»؟"}),None


def replay(case):
    tag,req,gold=case
    receipt=gateway.run(req)
    check=gateway.accept_output(receipt,expected_request=req)
    if not check["valid"]:
        raise ValueError((tag,receipt["status"],receipt["execution"].get("error"),check))
    g=receipt["execution"]["owner_result"]["licensed_speech"]
    forces=sorted({r["force"] for r in g["decoded"]})
    nodes={n["id"]:n for n in g["nodes"]}
    if tag.startswith("lexical/"):
        actual=sorted({n["value"] for n in g["nodes"] if n["role"]=="conditional_indication"})
        ok=actual==([gold] if gold else [])
        if tag=="lexical/3":
            ok &= sum(n["role"]=="candidate_sense" for n in g["nodes"])==3
    elif tag.startswith("ledger/"):
        actual={k:nodes["ledger/"+k]["status"] for k in ("capability","located","recorded_event","cause_to_effect")}
        ok=actual=={k:"OPEN" if tag=="ledger/no_place" and k!="capability" else "LICENSED" for k in actual}
    elif tag=="genus":
        actual=sorted(
            {n["value"] for n in g["nodes"] if n["transition"]["scope"]=="conditional_definition"})
        ok={"G:وسادة","A:صغير","P:إسناد_الخد"}<=set(actual)
    else:
        actual=forces
        ok=actual==([] if gold=="open" else [gold])
        if tag=="display":
            ok &= "valency/force" in g["revision"]["lost"] and "valency/content" in g["revision"]["surviving"]
    if not ok or g["world_truth_established"] or g["empirical_causality_established"]:
        raise ValueError((tag,actual,gold))
    return {"case":tag,"request":req,"verified":check["status"],"snapshot":receipt["snapshot_sha256"],
            "graph_sha256":digest(g),"gold":gold,"decoded":actual,"neural_top":g["neural"].get("top"),
            "roles":[r["roles"] for r in g["decoded"]],"node_count":len(nodes),"match":bool(ok)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers",type=int,choices=(1,2,3,4),default=2)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    with ProcessPoolExecutor(args.workers) as pool:
        rows=list(pool.map(replay,requests()))
    by_case={r["case"]:r for r in rows}
    if by_case["ledger/full"]["graph_sha256"]!=by_case["ledger/restore"]["graph_sha256"]:
        raise ValueError("Ledger restoration did not restore the graph")
    focus=[r for r in rows if r["gold"] in LABELS and r["case"]!="display" and not r["case"].startswith("directive/")]
    counts=Counter(r["gold"] for r in focus)
    with TRAIN.open(encoding="utf-8") as f:
        baseline=Counter(r["force"] for r in csv.DictReader(f,delimiter="\t")).most_common(1)[0][0]
    out={"n_gateway_replays":len(rows),"neural_n":len(focus),"neural_correct":sum(r["gold"]==r["neural_top"] for r in focus),
         "train_majority":baseline,"baseline_correct":counts[baseline],"per_class":{k:{"n":v,
          "correct":sum(r["gold"]==r["neural_top"]==k for r in focus)} for k,v in counts.items()},
         "neural_errors":[r["case"] for r in focus if r["gold"]!=r["neural_top"]],"rows":rows}
    with args.output.open("x",encoding="utf-8") as f:
        json.dump(out,f,ensure_ascii=False,indent=2)
        f.write("\n")
    print({k:v for k,v in out.items() if k!="rows"})


if __name__=="__main__":
    main()
