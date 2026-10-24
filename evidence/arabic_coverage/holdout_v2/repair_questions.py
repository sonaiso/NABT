"""Pre-prediction source correction; no NABT import or prediction probing."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OLD = ROOT / "evidence/arabic_coverage/holdout_v1"
NEW = Path(__file__).resolve().parent
ERRATUM = ROOT / "evidence/arabic_coverage/holdout_review_v1/question_force_erratum.json"


def write(name, data):
    with (NEW / name).open("xb") as handle:
        handle.write(data)


if __name__ == "__main__":
    assert sha256((OLD / "freeze.json").read_bytes()).hexdigest() == "1e53a8c970288f77c2703f3d57db9982ea35263b30b2830b79eeee47fde617e5"
    for row in json.loads((OLD / "freeze.json").read_text())["files"]:
        assert sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    source = json.loads((OLD / "cases.json").read_text(encoding="utf-8"))
    corrected = deepcopy(source)
    erratum = json.loads(ERRATUM.read_text(encoding="utf-8"))
    changes = []
    for delta in erratum["affected_questions"]:
        cid, qi = delta["case_id"], delta["question_index_zero_based"]
        case = next(c for c in corrected["cases"] if c["id"] == cid)
        question = case["questions"][qi]
        assert question["text"] == delta["original_question"]
        assert question["expected_status"] == delta["unchanged_semantic_expectation"]
        question["text"] = delta["proposed_source_licensed_input"]
        changes.append({"case_id": cid, "question_index_zero_based": qi,
                        "old": delta["original_question"], "new": question["text"],
                        "expected_status_unchanged": question["expected_status"]})
    # This schema is unchanged. The material version and amendment are explicit.
    corrected["material_revision"] = 2
    corrected["preexecution_correction"] = {
        "original_material_freeze_sha256": erratum["frozen_v1_sha256"],
        "erratum_path": str(ERRATUM.relative_to(ROOT)),
        "erratum_sha256": sha256(ERRATUM.read_bytes()).hexdigest(),
        "reason": "Interrogative hamza replaces هل before explicit negation, following the cited Ibn Hisham passage; no expected answer was changed.",
        "predictions_executed_before_correction": False,
        "changes": changes}
    write("cases.json", (json.dumps(corrected, ensure_ascii=False, indent=2) + "\n").encode())
    for filename in ("contexts.json", "lexical_premises.tsv", "source_premises.json"):
        write(filename, (OLD / filename).read_bytes())
    write("question_source_addendum.json", (json.dumps({
        "schema": "nabt.holdout-question-source-addendum.v1",
        "material_revision": 2,
        "primary_source": erratum["primary_source"],
        "changes": changes,
        "authority": "Ibn Hisham's stated restriction on interrogative هل, not a claim that all modern or dialectal usage follows this restriction.",
        "scope": "The corrected questions use the published NABT detached-hamza token convention. Neither this correction nor the unchanged case expectations tests every joined interrogative orthography."},
        ensure_ascii=False, indent=2) + "\n").encode())
    print(json.dumps({"cases": len(corrected["cases"]),
                      "questions": sum(len(c["questions"]) for c in corrected["cases"]),
                      "question_inputs_corrected": len(changes), "expected_statuses_changed": 0}))
