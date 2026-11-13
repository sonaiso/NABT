"""Generate questions from source alone, then submit frozen answers in separate verified requests."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import json
from pathlib import Path

from tools.grammar_catalog import gateway
from tools.grammar_catalog.operations import ROOT

FIXTURE = ROOT / "evidence/question_answer_cycle_v1/challenge.json"


def replay(payload):
    request = {"schema": gateway.REQUEST_SCHEMA, "route": "text.read", "payload": payload}
    result = gateway.run(request)
    checked = gateway.accept_output(result, expected_request=request)
    if not checked["valid"]:
        raise RuntimeError(f"public replay failed: {result['status']} {checked['status']}")
    return result["execution"]["owner_result"]["question_answer_cycle"]


def exercise(source):
    report = replay({"text": source, "question_cycle": True})
    return {"source": source, "questions": {i["operation"]: i["question"] for i in report["items"]},
            "generated_and_complete": all(i["generated_grade"]["complete"] for i in report["items"]),
            "status": report["status"]}


def submit(case_and_question):
    case, question = case_and_question
    source, operation, status, answer, claim, reason = case
    report = replay({"text": source, "question": question, "answer": answer})
    item, = report["items"]
    grade = item["submitted_grade"]
    return {"source": source, "question": question, "answer": answer, "operation": item["operation"],
            "source_status": item["status"], "claim": grade["claim"], "reason": grade["reason"],
            "complete": grade["complete"], "passed":
            (item["operation"], item["status"], grade["claim"], grade["reason"]) == (operation, status, claim, reason)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, choices=range(1, 7), default=3)
    args = parser.parse_args()
    raw = FIXTURE.read_bytes()
    cases = json.loads(raw)
    with ProcessPoolExecutor(args.workers) as pool:
        generated = list(pool.map(exercise, dict.fromkeys(case[0] for case in cases)))
        by_source = {row["source"]: row["questions"] for row in generated}
        grades = list(pool.map(submit, [(c, by_source[c[0]][c[1]]) for c in cases]))
    passed = all(r["generated_and_complete"] and r["status"] == "ASSESSED" for r in generated)
    out = {"schema": "nabt.question-answer-cycle.measurement.v1", "fixture_sha256": sha256(raw).hexdigest(),
           "source_count": len(generated), "generated_questions": sum(len(r["questions"]) for r in generated),
           "generated_roundtrips": passed, "submitted": len(grades), "matched": sum(g["passed"] for g in grades),
           "public_requests_replayed": len(generated) + len(grades), "generations": generated, "grades": grades}
    with args.output.open("x", encoding="utf8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print({k: v for k, v in out.items() if k not in ("generations", "grades")})
    if not passed or not all(g["passed"] for g in grades):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
