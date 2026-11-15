"""One-attempt Arabic NTL transfer audit. Run as python -m tools.evaluate_context_transfer."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import platform
import random
import subprocess
from time import perf_counter

from tools.grammar_catalog import gateway

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/data/context_transfer/families.json"
ATTEMPTS = 1
SCHEMA = "ntl.context-transfer.v1"


def request(lesson):
    return {"schema":gateway.REQUEST_SCHEMA, "route":"cognitive.lesson", "payload":{"lesson":lesson}}


def execute(req):
    start = perf_counter()
    result = gateway.run(req)
    duration = perf_counter() - start
    verify = gateway.accept_output(result, expected_request=req)
    if not verify["valid"]:
        raise RuntimeError(f"Gateway returned {result['status']} / {verify['status']}")
    owner = result["execution"]["owner_result"]
    return owner, {"request_sha256":result["request_sha256"], "snapshot":result["snapshot_sha256"],
                   "receipt_sha256":gateway.digest(result), "seconds":round(duration,3),
                   "replay_seconds":round(perf_counter()-start-duration,3), "verified":verify["status"]}


def correct(text, expected, result):
    decision, *witnesses = expected
    if result["decision"] != decision:
        return False
    if not witnesses:
        return decision == "UNRESOLVED" and not result["matches"]
    address = result.get("address",{})
    if address.get("status") != "ACQUIRED":
        return False
    b = text.encode()
    found = set()
    for match in result["matches"]:
        start,end = match["utf8_span"]
        if b[start:end].decode() != match["surface"]:
            return False
        found.add(match["surface"])
    return found == set(witnesses)


def evaluate(args):
    family, method, seed = args
    rng = random.Random(str(seed)+family["term"])
    cases = list(enumerate(family["cases"]))
    rng.shuffle(cases)
    pairs = list(family["examples"])
    if method == "swapped":
        pairs = [(s,"literal" if l=="figurative" else "figurative") for s,l in pairs]
    if method == "zero":
        pairs = []
    rng.shuffle(pairs)
    lesson = {"schema":SCHEMA,"term":family["term"],"examples":[{"text":s,"label":l} for s,l in pairs],
              "probes":[case[0] for _,case in cases]}
    owner, receipt = execute(request(lesson))
    if owner["status"]!="COURSE_SESSION" or len(owner["predictions"])!=len(cases):
        raise ValueError(f"Unscorable session: {owner['status']}")
    rows=[]
    for (index, (text, *expected)), pred in zip(cases,owner["predictions"],strict=True):
        if pred["text_sha256"] != sha256(text.encode()).hexdigest():
            raise ValueError("Probe identity mismatch")
        rows.append({"case":index,"term":family["term"],"expected":expected, "text":text,
                     "correct":correct(text,expected,pred),"prediction":pred})
    return {"family":family["term"],"method":method,"receipt":receipt,"rows":rows}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases",type=Path,default=FIXTURES,help="Public diagnostic or independently held family bank")
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--seed",type=int,default=116)
    parser.add_argument("--workers",type=int,choices=(1,2,3,4),default=2)
    args=parser.parse_args()
    wall_start=perf_counter()
    raw=args.cases.read_bytes()
    families=json.loads(raw)
    work=[(f,m,args.seed) for f in families for m in ("zero","trained","swapped")]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        sessions=list(pool.map(evaluate,work))
    summary={}
    for method in ("zero","trained","swapped"):
        rows=[r for session in sessions if session["method"]==method for r in session["rows"]]
        decisive=[r for r in rows if r["expected"][0] in ("literal","figurative")]
        negative=[r for r in rows if r["expected"][0] not in ("literal","figurative")]
        summary[method]={"exact_with_witness":sum(r["correct"] for r in rows),"total":len(rows),
                         "decisive_correct":sum(r["correct"] for r in decisive),"decisive":len(decisive),
                         "boundary_correct":sum(r["correct"] for r in negative),"boundary":len(negative)}
    baselines={label:sum(r["expected"][0]==label for r in decisive) for label in ("literal","figurative")}
    out={"always_literal_decision_only":[baselines["literal"],len(decisive)],
         "always_abstain_decisive":[0,len(decisive)],"wall_seconds":round(perf_counter()-wall_start,3),
         "bank_sha256":sha256(raw).hexdigest(),"seed":args.seed,"attempts":ATTEMPTS,
         "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
         "platform":platform.platform(),"python":platform.python_version(),"workers":args.workers,
         "external_model_calls":0,"summary":summary,"sessions":sessions}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary))
if __name__=="__main__":
    main()
