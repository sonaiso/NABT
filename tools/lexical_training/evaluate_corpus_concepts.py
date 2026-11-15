"""Check the fixed, authored transfer exercises through the public NABT gateway."""
import argparse
import json
from pathlib import Path

from tools.grammar_catalog import gateway
from . import corpus_concepts as cc


def evaluate(items):
    rows = []
    for item in items:
        lesson = {"schema": cc.SCHEMA, "text": item["text"], "target_index": item["target_index"]}
        req = {"schema": gateway.REQUEST_SCHEMA, "route": "cognitive.lesson", "payload": {"lesson": lesson}}
        receipt = gateway.run(req)
        verified = gateway.accept_output(receipt, expected_request=req)
        if not verified["valid"]:
            raise ValueError("Failed public gateway replay: " + str(verified))
        owner = receipt["execution"]["owner_result"]
        if not owner.get("execution_measured"):
            raise ValueError("Unmeasured corpus concept lesson")
        decision = (owner["frame"] or {}).get("id")
        rows.append({**item, "predicted": decision, "reason": owner["reason"],
                     "model_id": owner["model_id"], "reading": owner.get("reading"),
                     "gateway_verified": True})
    return {"schema": "ntl.corpus-concepts.probe-evaluation.v1", "total": len(rows),
            "proposed": sum(r["predicted"] is not None for r in rows),
            "correct": sum(r["predicted"] == r["frame"] for r in rows), "rows": rows}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--probes", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = evaluate(json.loads(args.probes.read_text()))
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print({k: result[k] for k in ("total", "proposed", "correct")})


if __name__ == "__main__":
    main()
