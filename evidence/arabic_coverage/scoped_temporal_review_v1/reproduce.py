#!/usr/bin/env python3
"""Replay the post-first-run scoped-time repair against retained freeze v1.

These are authored review cases, not an unseen evaluation or new gold. The
program never changes a runtime, source, freeze or held-out input. Each output
is written only if absent. The archived runtime is checked byte for byte before
it is imported in a separate process.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[3]
FREEZE = ROOT / "evidence/arabic_coverage/code_freeze_v1.json"
FREEZE_SHA256 = "a7194b9b52ab8a6db0c92d65c7dae76dc23c1f1c8777b4e10b2fb71efa01c89f"


def digest(raw):
    return sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def write_new(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)
    return {"path": path.name, "bytes": len(raw), "sha256": digest(raw)}


def inventory(root, records):
    result = []
    for record in records:
        raw = (root / record["path"]).read_bytes()
        result.append({"path": record["path"], "bytes": len(raw), "sha256": digest(raw)})
    return result


def complete(report):
    return [a for c in report["clauses"] for a in c["analyses"]
            if a["licensed_syntax"] and a["references_complete"] and not a["rejected_candidate"]]


def worker():
    from nabt.corpus_evidence import learn_qac_lexicon
    from nabt.discourse import ask_discourse, read_discourse, verify_discourse
    payload = json.load(sys.stdin)
    models = {key: learn_qac_lexicon(text.encode()) for key, text in payload["sources"].items()}
    results = []
    for case in payload["cases"]:
        model = models[case["model"]]
        report = read_discourse(case["text"], lexical_model=model, context=payload["context"])
        answers = [{"question": q["text"], "answer": ask_discourse(case["text"], q["text"],
                    lexical_model=model, context=payload["context"])} for q in case.get("questions", [])]
        results.append({"case_id": case["id"], "text": case["text"], "report": report,
                        "answers": answers,
                        "replay": verify_discourse(report, lexical_model=model, context=payload["context"])})
    sys.stdout.write(json.dumps(results, ensure_ascii=False, sort_keys=True))


def run_worker(root, payload):
    env = dict(os.environ, PYTHONPATH=str(root / "src"), PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--worker"],
        input=encode(payload), stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
        cwd=root, check=True)
    return json.loads(proc.stdout), proc.stderr.decode()


def summarize(results):
    return [{"case_id": r["case_id"], "status": r["report"]["status"],
             "accepted_claims": len(r["report"]["claims"]),
             "complete_analyses": len(complete(r["report"])),
             "answer_statuses": [a["answer"]["status"] for a in r["answers"]],
             "replay_valid": r["replay"]["valid"]} for r in results]


def assert_after(cases, results):
    for case, actual in zip(cases, results, strict=True):
        assert case["id"] == actual["case_id"]
        report = actual["report"]
        assert actual["replay"]["valid"], case["id"]
        if case["expected"] == "LICENSED_DISCOURSE":
            assert report["status"] == "LICENSED_DISCOURSE" and report["claims"], case["id"]
        else:
            assert not report["claims"] and not complete(report), case["id"]
        for expected, answer in zip(case.get("questions", []), actual["answers"], strict=True):
            assert answer["answer"]["status"] == expected["expected"], case["id"]
            if expected["expected"] == "UNKNOWN":
                assert not answer["answer"]["proofs"], case["id"]
        if case.get("scoped"):
            for claim in report["claims"]:
                assert claim["predicate_kind"] == "scoped" and claim["time"] == [], case["id"]
                scope = next(r for r in claim["restriction"] if r["kind"] == "operator_scope")
                assert not scope["embedded_fact_projection"] and scope["embedded"][0]["time"], case["id"]
            for analysis in complete(report):
                edge = next(r for r in analysis["relations"] if r["kind"] == "time_adverb")
                assert edge["scope"] == "embedded_event" and not edge["exhaustive_attachment_claimed"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        worker()
        return
    if args.output is None:
        parser.error("--output must name a new evidence directory")
    args.output.mkdir(parents=True, exist_ok=True)
    freeze_raw = FREEZE.read_bytes()
    assert digest(freeze_raw) == FREEZE_SHA256
    freeze = json.loads(freeze_raw)
    archive_path = FREEZE.with_name(freeze["archive_filename"])
    archive_raw = archive_path.read_bytes()
    assert digest(archive_raw) == freeze["archive_sha256"]
    source = (ROOT / "examples/construction_training.tsv").read_text()
    noun_source = source.replace("\t>amosi\tT\tSTEM|POS:T|LEM:>amos|ROOT:'ms|M",
                                "\t>amosi\tN\tSTEM|POS:N|LEM:>amos|ROOT:'ms|MS")
    assert noun_source != source
    cases = [
        {"id": "SCOPED-T01", "text": "كاد سالمٌ يكتبُ أمسِ.", "model": "teaching_T",
         "expected": "LICENSED_DISCOURSE", "scoped": True, "questions": [
             {"text": "هل كاد سالمٌ يكتبُ أمسِ؟", "expected": "SUPPORTED"},
             {"text": "هل كاد سالمٌ يكتبُ؟", "expected": "UNKNOWN"},
             {"text": "هل يكتبُ سالمٌ أمسِ؟", "expected": "UNKNOWN"}]},
        {"id": "SCOPED-T02", "text": "كاد سالمٌ أن يكتبَ أمسِ.", "model": "teaching_T",
         "expected": "LICENSED_DISCOURSE", "scoped": True},
        {"id": "SCOPED-T03", "text": "شرع سالمٌ يكتبُ أمسِ.", "model": "teaching_T",
         "expected": "LICENSED_DISCOURSE", "scoped": True},
        {"id": "SCOPED-T04", "text": "كاد سالمٌ يكتبَ أمسِ.", "model": "teaching_T",
         "expected": "NO_ACCEPTED_CLAIM"},
        {"id": "SCOPED-T05", "text": "شرع سالمٌ أن يكتبَ أمسِ.", "model": "teaching_T",
         "expected": "NO_ACCEPTED_CLAIM"},
        {"id": "SCOPED-T06", "text": "كان زيدٌ حكيمًا أمسِ.", "model": "teaching_N",
         "expected": "NO_ACCEPTED_CLAIM"},
        {"id": "SCOPED-T07", "text": "كتب زيدٌ أمسِ.", "model": "teaching_N",
         "expected": "LICENSED_DISCOURSE"},
    ]
    payload = {"sources": {"teaching_T": source, "teaching_N": noun_source},
               "context": json.loads((ROOT / "examples/construction_context.json").read_text()), "cases": cases}
    current_before = inventory(ROOT, freeze["files"])
    with tempfile.TemporaryDirectory(prefix="nabt-scoped-time-freeze-v1-") as tmp:
        frozen = Path(tmp)
        with tarfile.open(archive_path, "r:gz") as archive:
            expected = {r["path"]: r for r in freeze["files"]}
            assert set(archive.getnames()) == set(expected)
            for member in archive.getmembers():
                path = PurePosixPath(member.name)
                assert member.isfile() and not path.is_absolute() and ".." not in path.parts
                raw = archive.extractfile(member).read()
                record = expected[member.name]
                assert len(raw) == record["bytes"] and digest(raw) == record["sha256"]
                target = frozen / member.name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
        before, before_stderr = run_worker(frozen, payload)
    after, after_stderr = run_worker(ROOT, payload)
    current_after = inventory(ROOT, freeze["files"])
    assert current_after == current_before, "runtime changed during review"
    assert_after(cases, after)
    files = [write_new(args.output / "inputs.json", encode(payload)),
             write_new(args.output / "before_v1.raw.json.gz", gzip.compress(encode(before), mtime=0)),
             write_new(args.output / "after_v2.raw.json.gz", gzip.compress(encode(after), mtime=0))]
    review = {"schema": "nabt.scoped-temporal-review.v1", "utc": datetime.now(timezone.utc).isoformat(),
        "authorship": "Post-first-run authored review cases. Same implementation team and shared workspace; not blind evaluation, authenticated natural utterance, or proof of Arabic completeness.",
        "fix_scope": "A licensed final temporal adjunct is retained inside the imperfect clause of the bounded approximation/inception profile. Outer time stays empty. The unconsumed lexical variant remains available. Event-only N temporal source examples do not automatically license nominal predicates.",
        "attachment_boundary": "Embedded attachment is licensed in this declared frame. Exhaustive matrix-versus-embedded Arabic attachment enumeration is not claimed.",
        "evidence_boundary": "Pinned digital grammar passage plus authored lexical premises and executable detector results; no external event or general language truth is certified.",
        "before_freeze": {"path": str(FREEZE.relative_to(ROOT)), "sha256": FREEZE_SHA256,
                          "archive_sha256": digest(archive_raw)},
        "current_runtime_before": current_before, "current_runtime_after": current_after,
        "runtime_unchanged_during_review": True, "before": summarize(before), "after": summarize(after),
        "assertions_passed": True, "files": files,
        "reproducer": {"path": str(Path(__file__).resolve().relative_to(ROOT)),
                       "sha256": digest(Path(__file__).read_bytes())},
        "environment": {"python": sys.version, "executable": sys.executable, "platform": platform.platform()},
        "stderr": {"before": before_stderr, "after": after_stderr}}
    write_new(args.output / "review.json", encode(review))
    print(json.dumps({"status": "PASS", "review": str(args.output / "review.json"),
                      "before": review["before"], "after": review["after"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
