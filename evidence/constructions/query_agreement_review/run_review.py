#!/usr/bin/env python3
"""Measure frozen authored query/agreement checks against one archived runtime."""
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
MATERIAL_FREEZE_SHA256 = "395f365e0773a0b2530fae9c1bba7f4e1c109b6827c1f175d592700507f287f0"
RUNTIME_PINS = {
    "23d04d307c3e560c8198ee0700923673af001a8835d8e00d6c11d79534e6d611": "constructions_v3",
}


def digest(raw):
    return sha256(raw).hexdigest()


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def proof_correlated(answer, document, inquiry):
    claims = {c["claim_id"]: c for c in document["claims"]}
    analyses = {(c["clause_id"], a["analysis_id"]): a
                for c in document["clauses"] for a in c["analyses"]}
    for proof in answer["proofs"] + answer["counterproofs"]:
        claim = claims.get(proof["claim_id"])
        if (claim is None or proof["document_report_id"] != document["report_id"]
                or proof["question_report_id"] != inquiry["report_id"]
                or claim["args"] != [proof["bindings"].get("?person")]
                or not proof["source_proofs"]):
            return False
        for source in proof["source_proofs"]:
            analysis = analyses.get((source["clause_id"], source["analysis_id"]))
            if (source not in claim["proofs"] or analysis is None or analysis["rejected_candidate"]
                    or not analysis["licensed_syntax"] or not analysis["references_complete"]
                    or not analysis["assertion_allowed"]):
                return False
            shape = {k: claim[k] for k in analysis["claims"][0]} if analysis["claims"] else None
            if shape is None or shape not in analysis["claims"]:
                return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--runtime-freeze", type=Path, required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    args = parser.parse_args()
    runtime = args.runtime_root.resolve()
    pin_raw = args.runtime_freeze.read_bytes()
    runtime_pin = digest(pin_raw)
    assert runtime_pin in RUNTIME_PINS
    freeze = json.loads(pin_raw)
    material_pin = (BASE / "material_freeze_v1.json").read_bytes()
    assert digest(material_pin) == MATERIAL_FREEZE_SHA256
    for row in json.loads(material_pin)["files"]:
        raw = (BASE / row["path"]).read_bytes()
        assert len(raw) == row["bytes"] and digest(raw) == row["sha256"]

    def source_check():
        wanted = {r["path"] for r in freeze["files"]}
        actual = {"pyproject.toml"} | {
            str(p.relative_to(runtime)) for p in (runtime / "src/nabt").rglob("*")
            if p.is_file() and p.suffix in {".py", ".json", ".txt"}}
        assert actual == wanted
        for row in freeze["files"]:
            raw = (runtime / row["path"]).read_bytes()
            assert len(raw) == row["bytes"] and digest(raw) == row["sha256"]

    source_check()
    assert not any(n == "nabt" or n.startswith("nabt.") for n in sys.modules)
    sys.path.insert(0, str(runtime / "src"))
    from nabt.corpus_evidence import learn_qac_lexicon
    from nabt.discourse import read_discourse, ask_discourse, verify_discourse_answer

    material = json.loads((BASE / "material_v1.json").read_bytes())
    models, rows, raw_records = {}, [], []
    for case in material["cases"]:
        source_raw = (BASE / case["source"]).read_bytes()
        model = models.setdefault(case["source"], learn_qac_lexicon(source_raw))
        context = json.loads((BASE / case["context"]).read_bytes())
        text, question, expected = case["text"], case["question"], case["expected"]
        document = read_discourse(text, lexical_model=model, context=context)
        inquiry = read_discourse(question, lexical_model=model, context=context, source_id="question")
        answer = ask_discourse(text, question, lexical_model=model, context=context)
        same = verify_discourse_answer(answer, text=text, question=question, lexical_model=model, context=context)
        no_source = verify_discourse_answer(answer, text=text, question=question, context=context)
        no_context = verify_discourse_answer(answer, text=text, question=question, lexical_model=model)
        changed = verify_discourse_answer(answer, text=text + "\n", question=question,
                                          lexical_model=model, context=context)
        all_readings = inquiry["derived_readings"] + [r for o in inquiry["occurrences"] for r in o["readings"]]
        intg = [r for r in all_readings if r["lexical_features"].get("pos") == "INTG"]
        bound = sorted(b["values"]["?person"] for b in answer["bindings"])
        checks = {
            "document_status": document["status"] == expected["document_status"],
            "inquiry_status": inquiry["status"] == expected["inquiry_status"],
            "answer_status": answer["status"] in expected["answer_statuses"],
            "bound_person_ids": bound == expected["bound_person_ids"],
            "proof_presence": bool(answer["proofs"]) == bool(expected["bound_person_ids"]),
            "no_counterproofs": not answer["counterproofs"],
            "question_not_asserted": len(inquiry["claims"]) == expected["question_asserted_claims"]
                and all(not a["assertion_allowed"] for c in inquiry["clauses"] for a in c["analyses"]),
            "intg_profile_preserved": bool(intg) and all(
                r["lexical_features"].get("gender") is None and r["lexical_features"].get("number") is None
                and r.get("profile", {}).get("gender") is None and r.get("profile", {}).get("number") is None
                for r in intg),
            "document_claims_remain_concrete": all(type(a) is str and not a.startswith("?")
                for claim in document["claims"] for a in claim["args"]),
            "source_identity": document["lexical_model"]["source"]["sha256"] == digest(source_raw)
                and inquiry["lexical_model"] == document["lexical_model"]
                and document["source_sha256"] == case["source_sha256"]
                and inquiry["source_sha256"] == case["question_sha256"],
            "proof_correlated": proof_correlated(answer, document, inquiry),
            "same_source_replay": same["valid"] is expected["same_source_replay_valid"],
            "source_withdrawal": no_source["valid"] is expected["source_withdrawal_valid"],
            "context_withdrawal": no_context["valid"] is expected["context_withdrawal_valid"],
            "changed_source_bytes": changed["valid"] is expected["changed_source_bytes_valid"],
        }
        rows.append({"id": case["id"], "passed": all(checks.values()), "checks": checks,
            "document_status": document["status"], "inquiry_status": inquiry["status"],
            "answer_status": answer["status"], "bound_person_ids": bound,
            "proof_count": len(answer["proofs"]), "counterproof_count": len(answer["counterproofs"]),
            "question_claim_count": len(inquiry["claims"]), "intg_readings": len(intg),
            "replay": {"same": same, "no_source": no_source, "no_context": no_context, "changed_source": changed}})
        raw_records.append({"id": case["id"], "document": document, "inquiry": inquiry,
                            "answer": answer, "replay": rows[-1]["replay"]})
    origins = {n: str(Path(m.__file__).resolve()) for n, m in sys.modules.items()
               if (n == "nabt" or n.startswith("nabt.")) and getattr(m, "__file__", None)}
    assert origins and all(Path(p).is_relative_to(runtime / "src/nabt") for p in origins.values())
    source_check()
    raw_bytes = b"".join(wire(r) + b"\n" for r in raw_records)
    raw_path = Path(str(args.output_prefix) + ".raw.jsonl.gz")
    with raw_path.open("xb") as sink:
        with gzip.GzipFile(fileobj=sink, mode="wb", filename="", mtime=0) as stream:
            stream.write(raw_bytes)
    assert gzip.decompress(raw_path.read_bytes()) == raw_bytes
    result = {"schema": "nabt.constructions.query-agreement-review-result.v1",
        "utc": datetime.now(timezone.utc).isoformat(), "runtime_selection": RUNTIME_PINS[runtime_pin],
        "runtime_manifest_sha256": runtime_pin, "runtime_snapshot_sha256": freeze["snapshot_sha256"],
        "runtime_files_checked_before_after": len(freeze["files"]), "runtime_root": str(runtime),
        "module_origins": origins, "material_freeze_sha256": MATERIAL_FREEZE_SHA256,
        "adapter_sha256": digest(Path(__file__).read_bytes()), "argv": sys.argv,
        "python": sys.version, "platform": platform.platform(),
        "passed": sum(r["passed"] for r in rows), "total": len(rows), "cases": rows,
        "raw_log": {"path": raw_path.name, "bytes": raw_path.stat().st_size,
            "sha256": digest(raw_path.read_bytes()), "records": len(raw_records),
            "uncompressed_sha256": digest(raw_bytes)},
        "scope": material["scope"]}
    result_path = Path(str(args.output_prefix) + ".json")
    with result_path.open("x", encoding="utf-8") as output:
        output.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "total": result["total"],
        "report": str(result_path), "report_sha256": digest(result_path.read_bytes()),
        "failed": [r["id"] for r in rows if not r["passed"]]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
