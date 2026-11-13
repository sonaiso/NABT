"""Evaluate the frozen questions through the public gateway and replay every receipt."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import json
from pathlib import Path

from tools.grammar_catalog import gateway
from tools.grammar_catalog.operations import ROOT

FIXTURE = ROOT / "evidence/question_cognition_v1/challenge.json"


def measure(item):
    index, route, case = item
    text, question, expected, value = case
    request = {"schema": gateway.REQUEST_SCHEMA, "route": route, "payload": {"text": text, "question": question}}
    receipt = gateway.run(request)
    verified = gateway.accept_output(receipt, expected_request=request)["valid"]
    report = (receipt.get("execution", {}).get("owner_result") or {}).get("question_cognition") or {}
    decision = report.get("decision", {})
    op = report.get("operation")
    prediction = report.get("proposal", {}).get("ranking", [None])[0]
    row = {"case": index, "route": route, "question": question, "operation": op, "expected": expected,
           "actual": decision.get("status"), "verified": verified, "proposal": prediction,
           "decision_sha256": gateway.digest(decision)}
    row["pass"] = bool(verified and report.get("world_truth_established") is False
                       and row["actual"] == expected and (value is None or decision.get("value") is value))
    return row


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--workers", type=int, choices=range(1,7), default=3)
    args = p.parse_args()
    raw = FIXTURE.read_bytes()
    cases = json.loads(raw)
    jobs = [(i, "text.read", case) for i, case in enumerate(cases)]
    # Compare normal entry points and restore the original query.
    jobs += [(0, "relations.analyze", cases[0]), (0, "text.read", cases[0])]
    with ProcessPoolExecutor(args.workers) as pool:
        rows = list(pool.map(measure, jobs))
    restored = rows[0] == rows[-1]
    routes_agree = rows[0]["decision_sha256"] == rows[-2]["decision_sha256"]
    questions = {r["question"]: r for r in rows if r["operation"]}
    out = {"schema": "nabt.question-cognition.measurement.v1", "challenge_sha256": sha256(raw).hexdigest(),
           "requests": len(rows), "passed": sum(r["pass"] for r in rows), "distinct_licensed_questions": len(questions),
           "proposal_top1_correct": sum(r["proposal"] == r["operation"] for r in questions.values()),
           "restored": restored, "routes_agree": routes_agree, "rows": rows}
    with args.output.open("x", encoding="utf8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print({k: v for k, v in out.items() if k != "rows"})
    if not all(r["pass"] for r in rows) or not restored or not routes_agree:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
