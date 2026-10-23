#!/usr/bin/env python3
"""Replay the frozen single claim-edge counterexample on an isolated runtime."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys


BASE = Path(__file__).resolve().parent
MATERIAL_FREEZE_SHA256 = "c5519dee8842f982b22a1126c8c2c2a48bdf4089c4feed94756fecac69f95298"
RUNTIME_PINS = {
    "23d04d307c3e560c8198ee0700923673af001a8835d8e00d6c11d79534e6d611": "constructions_v3",
    "42476d67e30e7e86506c3e878552966ce9dc784ae1e5d98bec3af50e6f0a1aa5": "constructions_v4",
}


def digest(raw):
    return sha256(raw).hexdigest()


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--runtime-freeze", type=Path, required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    args = parser.parse_args()
    runtime = args.runtime_root.resolve()
    pin_bytes = args.runtime_freeze.read_bytes()
    runtime_pin = digest(pin_bytes)
    assert runtime_pin in RUNTIME_PINS
    freeze = json.loads(pin_bytes)
    material_pin = (BASE / "material_freeze_v1.json").read_bytes()
    assert digest(material_pin) == MATERIAL_FREEZE_SHA256
    for row in json.loads(material_pin)["files"]:
        raw = (BASE / row["path"]).read_bytes()
        assert len(raw) == row["bytes"] and digest(raw) == row["sha256"]

    def source_check():
        actual = {"pyproject.toml"} | {
            str(p.relative_to(runtime)) for p in (runtime / "src/nabt").rglob("*")
            if p.is_file() and p.suffix in {".py", ".json", ".txt"}}
        assert actual == {r["path"] for r in freeze["files"]}
        for row in freeze["files"]:
            raw = (runtime / row["path"]).read_bytes()
            assert len(raw) == row["bytes"] and digest(raw) == row["sha256"]

    source_check()
    assert not any(n == "nabt" or n.startswith("nabt.") for n in sys.modules)
    sys.path.insert(0, str(runtime / "src"))
    from nabt.corpus_evidence import learn_qac_lexicon
    from nabt.discourse import read_discourse, ask_discourse, verify_discourse_answer

    material = json.loads((BASE / "material_v1.json").read_bytes())
    source_raw = (BASE / material["source"]).read_bytes()
    model = learn_qac_lexicon(source_raw)
    context = json.loads((BASE / material["context"]).read_bytes())
    text, question, expected = material["text"], material["question"], material["expected"]
    document = read_discourse(text, lexical_model=model, context=context)
    inquiry = read_discourse(question, lexical_model=model, context=context, source_id="question")
    answer = ask_discourse(text, question, lexical_model=model, context=context)
    replay = verify_discourse_answer(answer, text=text, question=question, lexical_model=model, context=context)
    withdrawal = verify_discourse_answer(answer, text=text, question=question, context=context)
    checks = {
        "document_status": document["status"] == expected["document_status"],
        "inquiry_status": inquiry["status"] == expected["inquiry_status"],
        "answer_status": answer["status"] == expected["answer_status"],
        "no_borrowed_bindings": answer["bindings"] == expected["bindings"],
        "no_borrowed_proofs": answer["proofs"] == expected["proofs"],
        "no_borrowed_counterproofs": answer["counterproofs"] == expected["counterproofs"],
        "question_not_asserted": not inquiry["claims"] and all(
            not a["assertion_allowed"] for c in inquiry["clauses"] for a in c["analyses"]),
        "source_identity": document["lexical_model"]["source"]["sha256"] == digest(source_raw)
            and inquiry["lexical_model"] == document["lexical_model"]
            and document["source_sha256"] == digest(text.encode())
            and inquiry["source_sha256"] == digest(question.encode()),
        "same_source_replay": replay["valid"] is True,
        "source_withdrawal": withdrawal["valid"] is False,
    }
    origins = {n: str(Path(m.__file__).resolve()) for n, m in sys.modules.items()
               if (n == "nabt" or n.startswith("nabt.")) and getattr(m, "__file__", None)}
    assert origins and all(Path(p).is_relative_to(runtime / "src/nabt") for p in origins.values())
    source_check()
    raw_bytes = wire({"document": document, "inquiry": inquiry, "answer": answer,
                      "replay": replay, "withdrawal": withdrawal}) + b"\n"
    raw_path = Path(str(args.output_prefix) + ".raw.jsonl.gz")
    with raw_path.open("xb") as sink:
        with gzip.GzipFile(fileobj=sink, mode="wb", filename="", mtime=0) as stream:
            stream.write(raw_bytes)
    assert gzip.decompress(raw_path.read_bytes()) == raw_bytes
    row = {"id": "WHR_EDGE01", "passed": all(checks.values()), "checks": checks,
           "document_status": document["status"], "inquiry_status": inquiry["status"],
           "answer_status": answer["status"], "bindings": answer["bindings"],
           "proof_count": len(answer["proofs"]), "counterproof_count": len(answer["counterproofs"])}
    result = {"schema": "nabt.constructions.query-claim-edge-review-result.v1",
        "utc": datetime.now(timezone.utc).isoformat(), "runtime_selection": RUNTIME_PINS[runtime_pin],
        "runtime_manifest_sha256": runtime_pin, "runtime_snapshot_sha256": freeze["snapshot_sha256"],
        "runtime_files_checked_before_after": len(freeze["files"]), "runtime_root": str(runtime),
        "module_origins": origins, "material_freeze_sha256": MATERIAL_FREEZE_SHA256,
        "adapter_sha256": digest(Path(__file__).read_bytes()), "argv": sys.argv,
        "python": sys.version, "platform": platform.platform(),
        "passed": int(row["passed"]), "total": 1, "cases": [row],
        "raw_log": {"path": raw_path.name, "bytes": raw_path.stat().st_size,
            "sha256": digest(raw_path.read_bytes()), "records": 1,
            "uncompressed_sha256": digest(raw_bytes)}, "scope": material["scope"]}
    result_path = Path(str(args.output_prefix) + ".json")
    with result_path.open("x", encoding="utf-8") as output:
        output.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "total": result["total"],
        "report": str(result_path), "report_sha256": digest(result_path.read_bytes()),
        "failed": [] if row["passed"] else [row["id"]]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
