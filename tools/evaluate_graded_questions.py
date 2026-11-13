"""Check the frozen question-chain cases and withdrawals via public receipt replay."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import json
from pathlib import Path

from tools.grammar_catalog import gateway
from tools.grammar_catalog.operations import ROOT, digest

FIXTURES = ROOT / "evidence/graded_question_chains_v1"


def cases():
    for name, text, expected in json.loads((FIXTURES/"challenge.json").read_bytes()):
        yield name, "text.read", {"text":text}, expected
    bridge = json.loads((FIXTURES/"ledger.json").read_bytes())
    for name, removed, expected in (
            ("ledger", "", ["LICENSED"]*4),
            ("remove_causal", "جفاف1 دليل_سببي حدث1.\n", ["LICENSED","LICENSED","DEFER","DEFER"]),
            ("remove_occurrence", "حدث1 وقوع شجرة1.\n", ["LICENSED","DEFER","DEFER","DEFER"]),
            ("remove_time", "حدث1 زمان يوم1.\n", ["DEFER"]*4),
            ("restore_ledger", "", ["LICENSED"]*4)):
        source = bridge["source_text"]
        if removed:
            assert source.count(removed) == 1
            source = source.replace(removed, "")
        payload = {"text":"اصفرّ الشجر","bridge":{**bridge,"source_text":source}}
        yield name,"relations.analyze",payload,dict(zip(("disposition","occurrence","cause","effect"),expected,strict=True))


def check(case):
    name, route, payload, expected = case
    req = {"schema":gateway.REQUEST_SCHEMA,"route":route,"payload":{**payload,"question_chain":True}}
    receipt = gateway.run(req)
    verify = gateway.accept_output(receipt, expected_request=req)
    owner = receipt.get("execution",{}).get("owner_result") or {}
    graph = owner.get("graded_questions",{})
    nodes = graph.get("nodes",[])
    found = {(n["role"],n["status"]) for n in nodes}
    match = (verify["valid"] and graph.get("world_truth_established") is False and set(expected.items()) <= found
             and (bool(nodes) if expected else graph.get("status") == "OUTSIDE_SOURCE"))
    return {"case":name,"route":route,"verified":verify["valid"],"pass":match,"status":graph.get("status"),
            "nodes":len(nodes),"grades":len(graph.get("levels",[])),"expected":expected,
            "source_scope_digest":digest(graph) if graph else None}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--workers", type=int, choices=range(1,7), default=3)
    args=p.parse_args()
    with ProcessPoolExecutor(args.workers) as pool:
        results=list(pool.map(check,cases()))
    by_id={r["case"]:r for r in results}
    restored=by_id["ledger"]["verified"] and by_id["ledger"]["source_scope_digest"] == by_id["restore_ledger"]["source_scope_digest"]
    out={"law":"nabt.graded-question-chains.measurement.v1","n":len(results),"passed":sum(r["pass"] for r in results),
         "restored":restored, "fixture_sha256":{p:sha256((FIXTURES/p).read_bytes()).hexdigest()
                                                for p in ("challenge.json","ledger.json")},"cases":results}
    with args.output.open("x", encoding="utf8") as f:
        json.dump(out,f,ensure_ascii=False,indent=2)
        f.write("\n")
    print({k:v for k,v in out.items() if k not in ("cases","fixture_sha256")})
    if not restored or out["passed"] != out["n"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
