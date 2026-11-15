"""Recheck scoped valency decisions, contextual withdrawals and restoration through the public gateway."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
from tools.grammar_catalog import gateway
from tools.grammar_catalog.operations import ROOT, digest


def inputs():
    rows=[]
    for ident,text,arity,force,roles in json.loads((ROOT/"evidence/valency_v1/contrast.json").read_text()):
        rows.append((ident,{"schema":gateway.REQUEST_SCHEMA,"route":"text.read","payload":{"text":text}},(arity,force,roles)))
    base=json.loads((ROOT/"examples/io_gateway/valency_context.json").read_text())
    for name,removed in (("baseline",None),("no_kind","عضوية"),("no_occurrence","وقوع"),("no_time","زمان"),
                         ("no_place","مكان"),("no_tool","آلة"),("no_cause","سبب_مصرح"),("restore",None)):
        p=deepcopy(base)
        field=p["payload"]["valency_context"]
        if removed:
            field["ledger"]="".join(l for l in field["ledger"].splitlines(keepends=True) if " "+removed+" " not in l)
        rows.append((name,p,None))
    return rows


def evaluate(case):
    name,request,reference=case
    receipt=gateway.run(request)
    check=gateway.accept_output(receipt,expected_request=request)
    if receipt["status"]!="EXECUTED" or not check["valid"]:
        raise ValueError((name,receipt["status"],check["status"]))
    owner=receipt["execution"]["owner_result"]
    record=owner.get("valency")
    row=record["reading"] if record else {}
    actual=(row.get("active_object_arity"),row.get("force"),[r["role"] for r in row.get("roles",[])])
    result={"case":name,"request":request,"verified":check["status"],"reading":actual,
            "roles":row.get("roles",[]),"scope":row.get("embedded_predication"),"nominal_clause":row.get("nominal_clause"),
            "owner_sha256":digest(owner)}
    if reference is not None:
        if actual!=reference:
            raise ValueError((name,actual,reference))
    else:
        audited=owner["valency_context"]
        expected={k:True for k in ("text_binding","capability_witnessed","located","occurrence_in_ledger",
                                   "reported_instrument","reported_actor","reported_causal_link")}
        gone={"no_kind":["capability_witnessed"],"no_occurrence":["occurrence_in_ledger","reported_causal_link"],
              "no_time":["located","occurrence_in_ledger","reported_causal_link"],
              "no_place":["located","occurrence_in_ledger","reported_causal_link"],
              "no_tool":["reported_instrument"],"no_cause":["reported_causal_link"]}
        expected.update({k:False for k in gone.get(name,[])})
        if audited["profiles"]!=expected or audited["empirical_causality_established"]:
            raise ValueError((name,audited["profiles"],expected))
        result.update(profiles=audited["profiles"],requirements=audited["requirements"],anchor=audited["anchor"])
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers",type=int,choices=(1,2,3,4),default=2)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    with ProcessPoolExecutor(args.workers) as pool:
        rows=list(pool.map(evaluate,inputs()))
    by_id={r["case"]:r for r in rows}
    if by_id["baseline"]["owner_sha256"]!=by_id["restore"]["owner_sha256"]:
        raise ValueError("Restoring the original request changed the owner report")
    with args.output.open("x",encoding="utf-8") as f:
        json.dump({"schema":"nabt.valency-public-acceptance.v1","n":len(rows),"rows":rows},f,ensure_ascii=False,indent=2)
        f.write("\n")
    print("Verified requests:",len(rows))
