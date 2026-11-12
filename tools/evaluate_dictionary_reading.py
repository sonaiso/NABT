"""Replay the independently retained lexical questions through NABT's public text reader."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from tools.grammar_catalog import gateway
from tools.lexical_training.train_dictionary_indication import DIR, read_tsv, write


def evaluate_gold(result, gold):
    if not result or result["verification_debts"] or result["world_truth_established"] or result["intended_sense_established"]:
        return False
    status=gold["required_status"]
    if status in ("unknown","unbound"):
        expected="NO_SCOPED_LEXICAL_ENTRY" if status=="unknown" else "CONTEXT_OCCURRENCE_UNRESOLVED"
        return result["status"]==expected and not result["readings"]
    rows=[r for r in result["readings"] if r["root"]==gold["root"]]
    meanings=gold["gloss"].split("|")
    if not all(any(r["gloss"]==g for r in rows) for g in meanings):return False
    if result["status"]!="SOURCE_BOUND_READINGS":return False
    if status=="context":
        x=result["context_occurrence"]
        if gold["text"].encode()[slice(*x["utf8_span"])].decode()!=x["surface"]:return False
        ranking=result["proposals"]["context"]
        return any(r["sense_id"]==ranking.get("top") and r["gloss"]==gold["gloss"] for r in rows)
    if gold["target_kind"]=="-":return len(rows)>1 if status=="ambiguous" else bool(rows)
    kind=gold["target_kind"]
    return any(r["gloss"]==gold["gloss"] and r.get("native_checked") and
               r["indications"]==([] if kind=="none" else [kind]) for r in rows)


def replay(gold):
    request={"schema":gateway.REQUEST_SCHEMA,"route":"text.read","payload":{"text":gold["text"]}}
    receipt=gateway.run(request)
    checked=gateway.accept_output(receipt,expected_request=request)
    out={"text":gold["text"],"execution":receipt["status"],"verified":checked["valid"],"gold_match":False}
    if receipt["status"]!="EXECUTED" or not checked["valid"]:return out
    view=receipt["execution"]["owner_result"]
    r=view["dictionary_reading"]
    out.update(status=r["status"],gold_match=evaluate_gold(r,gold),
               senses=[{"id":v["sense_id"],"gloss":v["gloss"],"root":v["root"],"indications":v["indications"]} for v in r["readings"]],
               context_top=(r.get("proposals",{}).get("context") or {}).get("top"))
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--workers",type=int,choices=range(1,9),default=4)
    args=p.parse_args()
    with ProcessPoolExecutor(args.workers) as ex:
        cases=list(ex.map(replay,read_tsv(DIR/"challenge.tsv")))
    score=sum(c["gold_match"] for c in cases)
    write(args.output,{"schema":"nabt.public-dictionary-evaluation.v1","route":"text.read",
                       "n":len(cases),"correct":score,"cases":cases})
    print(f"{score}/{len(cases)}")
    if score!=len(cases):raise SystemExit(1)


if __name__=="__main__":main()
