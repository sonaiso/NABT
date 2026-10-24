#!/usr/bin/env python3
"""Replay the independently authored N/T rival and source-withdrawal controls."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from nabt.corpus_evidence import learn_qac_lexicon
from nabt.discourse import ask_discourse, read_discourse, verify_discourse


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
    before_path = Path(__file__).with_name("before.raw.json")
    before_raw = before_path.read_bytes()
    assert sha256(before_raw).hexdigest() == "6402307c6799a38cb77386c3ee0446f76a11de583d013d005724eb89d44e21e7"
    before = json.loads(before_raw)
    source, context = before["source_text"], before["context"]
    paths = [r["path"] for r in json.loads((ROOT / "evidence/arabic_coverage/code_freeze_v1.json").read_bytes())["files"]]
    def inventory():
        return [{"path": p, "sha256": sha256((ROOT / p).read_bytes()).hexdigest(),
                 "bytes": (ROOT / p).stat().st_size} for p in paths]
    runtime_before = inventory()
    outputs = []
    for case in before["cases"]:
        model = learn_qac_lexicon(source.encode(), source_id=before["source_id"])
        report = read_discourse(case["input"], lexical_model=model, context=context)
        verify = verify_discourse(report, lexical_model=model, context=context)
        assert report["status"] == "DEFER" and not report["claims"] and verify["valid"]
        outputs.append({"input": case["input"], "report": report, "verification": verify})
    target = outputs[1]
    assert before["cases"][1]["report"]["status"] == "LICENSED_DISCOURSE"
    pending = [a for c in target["report"]["clauses"] for a in c["analyses"]
               if "KADA_COMPLEMENT_ARGUMENT_FRAME_REQUIRED" in a["obligations"]]
    assert pending and any(not a["rejected_candidate"] for a in pending)
    assert all(not a["assertion_allowed"] and not a["claims"] for a in pending)
    controls = []
    for label, omit in (("no_nominal_source", ("(92:2:", "(92:3:")),
                        ("no_imperfect_object_host_witness", ("(93:1:",))):
        raw = "\n".join(line for line in source.splitlines() if not line.startswith(omit)) + "\n"
        model = learn_qac_lexicon(raw.encode(), source_id=before["source_id"])
        report = read_discourse(target["input"], lexical_model=model, context=context)
        assert report["status"] == "LICENSED_DISCOURSE" and report["claims"]
        assert not any("KADA_COMPLEMENT_ARGUMENT_FRAME_REQUIRED" in a["obligations"]
                       for c in report["clauses"] for a in c["analyses"])
        controls.append({"control": label, "source_text": raw, "report": report})
    runtime_after = inventory()
    assert runtime_before == runtime_after
    artifact = save(args.output / "after.raw.json", {"schema": "nabt.operator-argument-review.raw.v1",
        "source_text": source, "source_id": before["source_id"], "context": context,
        "cases": outputs, "controls": controls})
    result = {"schema": "nabt.operator-argument-review.v1", "phase": "POST_FIRST_FROZEN_RUN_ADVERSARIAL_REVIEW",
        "authorship": "Counterexample authored by a different collaborating agent in a shared workspace after the temporal repair. It is not a blind corpus sample.",
        "defect": "Keeping the original token sequence alone did not preserve a nominal object rival: the one-verb operator clause production ignored the longer tail while accepting its temporal-T interpretation.",
        "repair": "A nominal reading plus independently acquired host/object-pronoun valency witness now produces a separate pending operator-argument candidate. Its argument roles remain inactive, it carries no claims, and it blocks a unique source judgment. No nominal rival is manufactured from a T tag or a context name alone.",
        "remaining_obligation": "KADA_COMPLEMENT_ARGUMENT_FRAME_REQUIRED",
        "complete_arabic_attachment_claimed": False, "world_event_established": False,
        "runtime_before": runtime_before, "runtime_after": runtime_after, "runtime_stable": True,
        "before_target_status": before["cases"][1]["report"]["status"],
        "after_target_status": target["report"]["status"], "pending_candidates": len(pending),
        "control_statuses": {r["control"]: r["report"]["status"] for r in controls},
        "before_raw_sha256": sha256(before_raw).hexdigest(), "artifact": artifact,
        "reproducer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "passed": True}
    save(args.output / "review.json", result)
    print(json.dumps({"passed": True, "pending_candidates": len(pending), "artifact": artifact}))


if __name__ == "__main__":
    main()
