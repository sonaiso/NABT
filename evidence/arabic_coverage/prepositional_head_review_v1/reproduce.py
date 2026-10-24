#!/usr/bin/env python3
"""Post-failure replay of the exact prefixed-NP head boundary, without scoring gold."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import ask_discourse, read_discourse, verify_discourse, verify_discourse_answer


def wire(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def save(path, value):
    raw = wire(value)
    with path.open("xb") as stream:
        stream.write(raw)
    return {"path": path.name, "bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    folder = ROOT / "evidence/constructions"
    freeze_raw = (folder / "independent_freeze_v1.json").read_bytes()
    assert sha256(freeze_raw).hexdigest() == "5e4e9856b00ee648888e58c84e62c0a334cd3875d14cea326273d7c0f732254e"
    for record in json.loads(freeze_raw)["files"]:
        raw = (ROOT / record["path"]).read_bytes()
        assert len(raw) == record["bytes"] and sha256(raw).hexdigest() == record["sha256"]
    material = json.loads((folder / "independent_cases_v1.json").read_bytes())
    case = next(c for c in material["cases"] if c["id"] == "CON-W02")
    source = (folder / material["source_file"]).read_bytes()
    model = learn_qac_lexicon(source, source_id="construction_authored_lexicon")
    inputs = case["input"]
    kwargs = {"lexical_model": model, "context": inputs["context"],
              "source_id": inputs["source_id"], "scope": inputs["scope"]}
    paths = [r["path"] for r in json.loads((ROOT / "evidence/arabic_coverage/code_freeze_v1.json").read_bytes())["files"]]
    def inventory():
        return [{"path": p, "sha256": sha256((ROOT / p).read_bytes()).hexdigest(),
                 "bytes": (ROOT / p).stat().st_size} for p in paths]
    before = inventory()
    report = read_discourse(inputs["text"], **kwargs)
    verification = verify_discourse(report, text=inputs["text"], **kwargs)
    questions = []
    for wanted in case["expected"].get("questions", []):
        text = wanted["text"]
        answer = ask_discourse(inputs["text"], text, **kwargs)
        questions.append({"answer": answer,
            "inquiry": read_discourse(text, **{**kwargs, "source_id": "question"}),
            "verification": verify_discourse_answer(answer, text=inputs["text"], question=text, **kwargs)})
    after = inventory()
    assert before == after, "Runtime changed during the scoped replay"
    assert report["status"] == "LICENSED_DISCOURSE" and verification["valid"]
    assert all(q["answer"]["status"] == "SUPPORTED" and q["verification"]["valid"] for q in questions)
    spans = []
    text_bytes = inputs["text"].encode()
    for clause in report["clauses"]:
        for analysis in clause["analyses"]:
            if not analysis["licensed_syntax"] or not analysis["references_complete"] or analysis["rejected_candidate"]:
                continue
            for dependent in analysis["assignments"]:
                if dependent["role"] != "tawkeed":
                    continue
                heads = [a for a in analysis["assignments"] if a["span"] == dependent["head_span"]]
                assert {a["required_case"] for a in heads} == {"jarr"}
                assert any(a["role"] == "preposition_object" for a in heads)
                nominal = next(a for a in heads if a["role"] == "preposition_object")
                edge = next(r for r in analysis["relations"] if r["kind"] == "preposition_object"
                            and r["dependent_span"] == nominal["span"])
                reference = next(r for r in analysis["references"] if r["reference_id"] == edge["object_reference"])
                assert reference["span"] == nominal["span"] and reference["bound_entity_id"] == "samir"
                prefix, stem, written = edge["head_span"], edge["dependent_span"], edge["written_token_span"]
                assert written["start"] == prefix["start"] and prefix["end"] == stem["start"] and stem["end"] == written["end"]
                assert text_bytes[prefix["start"]:prefix["end"]] + text_bytes[stem["start"]:stem["end"]] == text_bytes[written["start"]:written["end"]]
                spans.append({"prefix": prefix, "nominal": stem, "written": written,
                              "inherited_case": dependent["required_case"]})
    assert spans
    # PP owner remains a qualification. It is not an added event argument.
    assert all(c["args"] == ["basim"] for c in report["claims"])
    artifact = save(args.output / "after.raw.json", {"id": case["id"], "report": report,
        "questions": questions, "verification": verification, "replay": None})
    result = {"schema": "nabt.prepositional-head-review.v1", "case_id": case["id"],
        "phase": "POST_FIRST_FROZEN_RUN_REVIEW_NOT_BLIND_GOLD", "gold_modified": False,
        "fix": "Normalize the governed NP root to the independently segmented nominal substring, including all naat/tawkeed/idafa heads. Retain the prefix span, complete written-token span, original lexical reading and source bytes.",
        "checker_boundary": "This replay checks source/reference/assignment conservation. Qualification scoring is separately reviewed and is not changed by this program.",
        "gold_freeze_sha256": sha256(freeze_raw).hexdigest(), "lexical_source_sha256": sha256(source).hexdigest(),
        "runtime_before": before, "runtime_after": after, "runtime_stable": True,
        "source_status": report["status"], "question_statuses": [q["answer"]["status"] for q in questions],
        "head_spans": spans, "artifact": artifact, "passed": True,
        "reproducer_sha256": sha256(Path(__file__).read_bytes()).hexdigest()}
    save(args.output / "review.json", result)
    print(json.dumps({"passed": True, "artifact": artifact, "analyses_checked": len(spans)}))


if __name__ == "__main__":
    main()
