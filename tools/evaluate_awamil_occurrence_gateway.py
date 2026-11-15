"""Read and independently replay one held-out occurrence per factor, plus contrast controls."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
import json
from pathlib import Path

from tools.grammar_catalog import gateway
from tools.awamil_occurrence_fixtures import SOURCE_SHA256, agrees, fixtures
from tools.lexical_training.train_awamil_occurrence import DIR, dump


def requests():
    result=[("factor",r) for r in fixtures()]
    challenge=json.loads((DIR/"contrast.json").read_bytes())
    result += [("event",r) for r in challenge["heldout"]]
    result += [("control",{"text":s}) for s in challenge["controls"]]
    with (DIR/"voice_transfer.tsv").open() as source:
        result += [("neural_only",r) for r in csv.DictReader(source,delimiter="\t")]
    return result


def replay(item):
    kind,r=item
    req={"schema":gateway.REQUEST_SCHEMA,"route":"text.read","payload":{"text":r["text"]}}
    receipt=gateway.run(req)
    checked=gateway.accept_output(receipt,expected_request=req)
    result={"kind":kind,"text":r["text"],"execution":receipt["status"],"verified":checked["valid"],"match":False}
    if not checked["valid"] or receipt["status"]!="EXECUTED":
        return result
    view=receipt["execution"]["owner_result"]
    report=view["awamil_occurrence"]
    readings=report["readings"]
    result.update(status=report["status"],ids=[[f["id"] for f in a["factors"]] for a in readings],
                  customary=report["customary_use_established"],world=report["world_truth_established"])
    if kind=="factor":
        if len(readings)==1:
            a=readings[0]
            result.update(relation=a["relation"], principal_span=a["principal_span"],
                          operator_span=(a["factors"][0]["occurrence"] or {}).get("utf8_span"),
                          expected_case=r["case"], expected_mark_span=r["mark_span"])
            result["match"]=(agrees(a,r) and a["source_sha256"]==view["source"]["sha256"]
                             and bool(a["witnesses"]) and bool(a["edges"]))
    elif kind=="event":
        if len(readings)==1 and readings[0]["event"]:
            e=readings[0]["event"]
            result.update(event={k:e[k] for k in ("voice","polarity","patient","patient_key","patient_syntax","sense")})
            result["match"]=(e["voice"]==r["voice"] and e["polarity"]==r["polarity"] and e["patient"]["surface"]==r["patient"]
                             and (e["actor"] is None)==(r["voice"]=="passive") and e["sense"]=="break")
    else:
        result["match"]=not readings and report["status"]=="OUTSIDE_AUTHORED_PATTERNS"
        if kind=="neural_only":
            proposal=report["event_proposal"]
            result["match"] &= (proposal.get("voice"),proposal.get("polarity"),proposal.get("patient_surface"))==(
                r["voice"],r["polarity"],r["patient"])
    result["match"] &= not result["customary"] and not result["world"]
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workers",type=int,choices=range(1,9),default=3)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        cases=list(ex.map(replay,requests()))
    summary={k:{"n":len(group),"correct":sum(r["match"] for r in group)} for k in sorted({r["kind"] for r in cases})
             if (group:=[r for r in cases if r["kind"]==k])}
    dump(args.output,{"schema":"nabt.awamil-occurrence.public-evaluation.v1","route":"text.read","fixture_sha256":SOURCE_SHA256,"summary":summary,"cases":cases})
    print(summary)
    if not all(r["match"] for r in cases):
        raise SystemExit(1)


if __name__=="__main__":
    main()
