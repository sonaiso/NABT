"""Offline generator. Run in the clean pinned #143 worktree; outputs oracle rows only."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

PR143 = "fdb1f7e3"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.checkout.resolve()
    pins = json.loads((Path(__file__).resolve().parents[2] / "evidence/cumulative_outcomes_v1/pulls.json").read_bytes())
    pin = pins[142]["head"]
    if (not pin.startswith(PR143) or subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"]).decode().strip()!=pin
            or subprocess.check_output(["git","-C",str(root),"status","--porcelain","--untracked-files=all"]).strip()):
        raise ValueError("Expected the clean pinned historical dictionary checkout")
    sys.path[:0] = [str(root),str(root/"src")]
    from tools.lexical_training import dictionary_deposit
    from tools.grammar_catalog import gateway
    path = "examples/io_gateway/ntl_dictionary_deposit.json"
    request = json.loads((root/path).read_bytes())
    lesson = request["payload"]["input"]["lesson"]
    out = []
    for removed in ([],["mukhtar"],["maqayis"],["mukhtar","maqayis"]):
        lesson["withdraw_sources"] = removed
        receipt = gateway.run(request)
        if not gateway.accept_output(receipt,expected_request=request)["valid"]:
            raise ValueError("Historical gateway did not replay")
        result = receipt["execution"]["owner_result"]["owner_result"]
        if result["schema"] != dictionary_deposit.RESULT:
            raise ValueError("Wrong historical owner")
        for row in result["rows"]:
            term, work = row["term"], row["source"]
            text = f"المعجم {work}، اللفظ {term}، المصادر المسحوبة "+(",".join(removed) or "لا شيء")
            out.append({"pr":143,"task":"dictionary_source_status","text":text,"gold":row["status"],
                        "split":"test" if int(sha256(term.encode()).hexdigest(),16)%5==0 else "train",
                        "source":pin+":"+path+"#/queries/"+str(row["position"]),"lane":"verified_branch_teacher"})
    args.output.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=1)+"\n")


if __name__ == "__main__":
    main()
