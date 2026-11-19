"""Score the installed NTL course on the pre-existing frozen Arabic transfer set."""
from hashlib import sha256
import json

from tools.evaluate_classical_attention import CHALLENGE, CHALLENGE_SHA
from tools.lexical_training import ntl_classical_books as books


def evaluate():
    challenge = CHALLENGE.read_bytes()
    if sha256(challenge).hexdigest() != CHALLENGE_SHA:
        raise ValueError("Frozen challenge has changed")
    demo_path = books.ROOT / "examples/ntl_classical_books/object_first.json"
    examples = json.loads(demo_path.read_bytes())["payload"]["input"]["lesson"]["examples"]
    groups = {}
    errors = []
    for case in json.loads(challenge)["cases"]:
        text = case["text"]
        if text in examples:
            raise ValueError("Probe repeated in course demonstrations")
        lesson = {"schema": books.SCHEMA, "text": text, "source_id": case["id"], "examples": examples}
        result = books.run(lesson)
        rows = {q["id"]: q for q in result["questions"]}
        has_gold = case["subject"] is not None
        group = "answerable" if has_gold else "outside_profile"
        scores = groups.setdefault(group, {"n": 0, "source_reading_correct": 0, "learner_pointer_correct": 0,
                                           "unjustified_world_answers": 0})
        scores["n"] += 1
        if has_gold:
            wanted = [case["subject"], case["object"], {"ask": "استفهام", "assert": "خبر"}[case["force"]]]
            correct = all(rows[key]["decision"] == "SUPPORTED" and rows[key]["answer"] == target
                          for key, target in zip(("subject", "object", "utterance"), wanted))
        else:
            correct = all(rows[key]["decision"] == "UNKNOWN" for key in ("subject", "object", "utterance"))
        span = result["learning"]["agreed_proposal"]
        surface = text.encode()[slice(*span)].decode() if span is not None else None
        pointer_correct = surface == case["subject"]
        scores["source_reading_correct"] += int(correct)
        scores["learner_pointer_correct"] += int(pointer_correct)
        scores["unjustified_world_answers"] += int(rows["world"]["decision"] != "UNKNOWN")
        if not correct or not pointer_correct:
            errors.append({"id": case["id"], "source_reading_correct": correct, "learner_pointer": surface,
                           "expected_subject": case["subject"]})
    return {"challenge_sha256": CHALLENGE_SHA, "demonstrations": examples, "groups": groups, "errors": errors}


if __name__ == "__main__":
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))
