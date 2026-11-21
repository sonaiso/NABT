"""Recheck frozen questions on the named owner or across the full external gateway."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys

from tools.grammar_catalog import named_matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def read(path):
    return json.loads(path.read_text())

def check(case, output, native_only):
    request = case["request"]
    if native_only:
        payload = request["payload"]
        result = named_matrix.analyze(payload["text"],payload["source_id"],payload["named_matrix"])
    else:
        folder = output / case["id"]
        folder.mkdir(parents=True,exist_ok=True)
        source,receipt,verification = (folder / name for name in ("request.json","receipt.json","verify.json"))
        source.write_text(json.dumps(request,ensure_ascii=False)+"\n")
        command = [sys.executable,"-m","tools.grammar_catalog","gateway"]
        for args in (["run","--request",source,"--output",receipt],
                     ["verify","--request",source,"--receipt",receipt,"--output",verification]):
            subprocess.run(command+args,cwd=ROOT,env={**os.environ,"PYTHONPATH":"src:."},check=True)
        if not read(verification)["valid"]:
            raise ValueError("Gateway replay failed for "+case["id"])
        result = read(receipt)["execution"]["owner_result"]["named_matrix"]
    got = [row["status"] for row in result["answers"]]
    if result["status"]!="VERIFIED_PROJECTION" or got!=case["statuses"]:
        raise ValueError((case["id"],result["status"],got,case["statuses"]))
    return len(got)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--suite",choices=("event","retained"),default="event")
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--native-only",action="store_true")
    p.add_argument("--jobs",type=int,choices=range(1,9),default=3)
    args=p.parse_args()
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    cases=[json.loads(line) for line in (HERE/(args.suite+".jsonl")).read_text().splitlines()]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        counts=list(pool.map(lambda c: check(c,output,args.native_only),cases))
    summary={"suite":args.suite,"route":"native" if args.native_only else "gateway",
             "scenes":len(counts),"answers":sum(counts)}
    (output/(args.suite+"-summary.json")).write_text(json.dumps(summary)+"\n")
    print(json.dumps(summary))

if __name__=="__main__":
    main()
