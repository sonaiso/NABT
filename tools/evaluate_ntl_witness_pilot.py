"""Score proposals without the teacher binding, then test scoped decoding and intervention separately."""
import argparse
from collections import Counter
import json
import re
from pathlib import Path

from tools.grammar_catalog import gateway
from tools.grammar_catalog.operations import exact_terms
from tools.lexical_training import ntl_witness_pilot as pilot


def request(row, cuts):
    return {"schema": gateway.REQUEST_SCHEMA, "route": "cognitive.lesson",
            "payload": {"lesson": {"schema": pilot.SCHEMA, "source_id": row["id"],
                                  "text": row["text"], "withdraw": cuts}}}


def evaluate():
    rows = pilot.ranker.origins()
    majority = Counter(r["relation"] for r in rows if r["split"] == "train").most_common(1)[0][0]
    obs = []
    for row in rows:
        lesson = request(row, [])["payload"]["lesson"]
        original = pilot.run(lesson)
        events = {}
        for key in ("cue", "binding", "context.surface", *(("proof.surface",) if row["proof"] else ())):
            result = pilot.run(request(row, [key])["payload"]["lesson"])
            events[key] = {"lost": result["lost"], "predicted": result["predicted_lost"]}
            required = {"context"} if key == "context.surface" else set() if key == "proof.surface" else {"reading"}
            digits = [int(n) for n in re.findall(r"[0-9]+", row["proof"])]
            valid_proof = bool(digits and digits[0] == digits[1] * digits[2] + sum(digits[3:]))
            if valid_proof and key != "context.surface":
                required.add("demonstrated")
            if set(result["lost"]) != required:
                raise AssertionError((row["id"], key, required, result["lost"]))
        restored = pilot.run(lesson)
        if restored != original:
            raise AssertionError(("restoration", row["id"]))
        proposals = original["neural"]["clauses"]
        focus = next(p for p in proposals if p["surface"] == row["clause"])
        other = next(p for p in proposals if p["surface"] == row["context"])
        # A predicted context label is the only input to this clause-selection diagnostic.
        unique_focus = [p for p in proposals if p["relation"] != "context"]
        first_term = exact_terms(row["clause"])[0]["surface"]
        obs.append({"id": row["id"], "family": row["id"][:-2], "split": row["split"],
                    "restored": True,
                    "joint_correct": len(unique_focus) == 1 and unique_focus[0] == focus and
                                    focus["relation"] == row["relation"] and focus["cue"] == row["cue"],
                    "gold_relation": row["relation"], "relation": focus["relation"],
                    "cue": focus["cue"], "expected_cue": row["cue"], "relation_correct": focus["relation"] == row["relation"],
                    "context_correct": other["relation"] == "context", "cue_correct": focus["cue"] == row["cue"],
                    "primary_clause_correct": len(unique_focus) == 1 and unique_focus[0] == focus,
                    "baseline_primary": proposals[0] == focus, "baseline_relation": row["relation"] == majority,
                    "baseline_cue": first_term == row["cue"], "interventions": events})
    summary = {}
    metrics = ("joint_correct", "restored", "relation_correct", "context_correct", "cue_correct", "primary_clause_correct",
               "baseline_primary", "baseline_relation", "baseline_cue")
    for group in ("train", "dev", "test", "test-door", "test-seed", "test-num", "test-doc"):
        parts = group.split("-")
        selected = [r for r in obs if r["split"] == parts[0] and (len(parts) == 1 or r["family"] == parts[1])]
        interventions = [e for r in selected for e in r["interventions"].values()]
        summary[group] = {"origins": len(selected), **{m: sum(r[m] for r in selected) for m in metrics},
                          "interventions": len(interventions),
                          "exact_loss_proposals": sum(e["predicted"] is not None and set(e["predicted"]) == set(e["lost"])
                                                      for e in interventions)}
    return {"training_majority": majority, "neural_head_sha256": pilot.ranker.HEAD_SHA,
            "summary": summary, "rows": obs}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    value = evaluate()
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps(value["summary"], ensure_ascii=False))
