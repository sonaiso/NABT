"""Regenerate the public Q/A report from the original TSV through verified gateway I/O."""
import argparse
import json
from pathlib import Path

from tools.evaluate_ntl_witness_pilot import request
from tools.grammar_catalog import gateway
from tools.lexical_training import witness_origins


def public_questions(origin):
    withdrawn = "proof.surface" if origin["proof"] else "binding"
    req = request(origin, [withdrawn])
    receipt = gateway.run(req)
    verification = gateway.accept_output(receipt, expected_request=req)
    if not verification["valid"]:
        raise RuntimeError((origin["id"], verification))
    result = receipt["execution"]["owner_result"]
    if result["status"] != "SOURCE_BOUND" or not result["questions"]:
        raise RuntimeError((origin["id"], result["status"]))
    questions = [{"question": q["question"], "before": q["before"]["answer"], "after": q["after"]["answer"],
                  "sufficient_support": q["sufficient_support"]} for q in result["questions"]]
    return {"origin": origin["id"], "snapshot_sha256": receipt["snapshot_sha256"], "request": req,
            "replay": verification["status"], "binding": result["binding"], "questions": questions,
            "cue": result["evidence"]["cue"], "lost": result["lost"], "kept": result["kept"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    destination = parser.parse_args().output
    records = [public_questions(r) for r in witness_origins.origins()]
    with destination.open("x", encoding="utf-8") as output:
        json.dump(records, output, ensure_ascii=False, indent=2)
        output.write("\n")
