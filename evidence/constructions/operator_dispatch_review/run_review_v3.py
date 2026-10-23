#!/usr/bin/env python3
"""Measure the immutable authored operator-dispatch review, in isolation."""
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
MATERIAL_FREEZE_SHA256 = "c54ff94d45dfabc3a598bd0e576dcac49f889a4651e164116e19ecd17d689c8a"
RUNTIME_PINS = {
    "23d04d307c3e560c8198ee0700923673af001a8835d8e00d6c11d79534e6d611": "constructions_v3",
    "5d4bf3ec6331dab12ebc735f57203cf6bdbc86a563eae0311a66316eb8b820b1":
        "constructions_v2",
}


def digest(data):
    return sha256(data).hexdigest()


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
        assert digest(raw) == row["sha256"] and len(raw) == row["bytes"]

    def source_check():
        wanted = {r["path"] for r in freeze["files"]}
        actual = {"pyproject.toml"} | {
            str(p.relative_to(runtime)) for p in (runtime / "src/nabt").rglob("*")
            if p.is_file() and p.suffix in {".py", ".json", ".txt"}
        }
        assert actual == wanted
        for row in freeze["files"]:
            raw = (runtime / row["path"]).read_bytes()
            assert digest(raw) == row["sha256"] and len(raw) == row["bytes"]

    source_check()
    assert not any(name == "nabt" or name.startswith("nabt.") for name in sys.modules)
    sys.path.insert(0, str(runtime / "src"))
    from nabt.corpus_evidence import learn_qac_lexicon
    from nabt.discourse import read_discourse, ask_discourse

    material = json.loads((BASE / "material_v1.json").read_bytes())
    context = json.loads((BASE / "context.json").read_bytes())
    model = learn_qac_lexicon((BASE / "training.tsv").read_bytes())
    rows, raw_records = [], []
    for case in material["cases"]:
        report = read_discourse(case["text"], lexical_model=model, context=context)
        answer = ask_discourse(case["text"], case["question"], lexical_model=model, context=context)
        analyses = [a for c in report["clauses"] for a in c["analyses"]]
        activated = sum(a["activated"] for row in analyses for a in row["assignments"])
        expected = case["expected"]
        checks = {
            "document_status": report["status"] == expected["document_status"],
            "claim_count": len(report["claims"]) == expected["claim_count"],
            "answer_status": answer["status"] == expected["answer_status"],
            "actual_role_boundary": expected["activated_roles_allowed"] or activated == 0,
        }
        row = {"id": case["id"], "text": case["text"], "question": case["question"],
               "passed": all(checks.values()), "checks": checks,
               "document_status": report["status"], "claim_count": len(report["claims"]),
               "answer_status": answer["status"], "proof_count": len(answer["proofs"]),
               "activated_assignments": activated,
               "frames": sorted({a["frame"] for a in analyses}),
               "obligations": sorted({o for a in analyses for o in a["obligations"]}),
               "construction_gates": sum(r["kind"] == "construction_gate" for a in analyses for r in a["relations"])}
        rows.append(row)
        raw_records.append({"id": case["id"], "report": report, "answer": answer})
    origins = {name: str(Path(module.__file__).resolve()) for name, module in sys.modules.items()
               if (name == "nabt" or name.startswith("nabt.")) and getattr(module, "__file__", None)}
    assert origins and all(Path(path).is_relative_to(runtime / "src/nabt") for path in origins.values())
    source_check()
    raw_path = Path(str(args.output_prefix) + ".raw.jsonl.gz")
    raw_bytes = b"".join(wire(record) + b"\n" for record in raw_records)
    with raw_path.open("xb") as sink:
        with gzip.GzipFile(fileobj=sink, mode="wb", filename="", mtime=0) as stream:
            stream.write(raw_bytes)
    assert gzip.decompress(raw_path.read_bytes()) == raw_bytes
    result = {"schema": "nabt.constructions.operator-dispatch-review-result.v1",
              "utc": datetime.now(timezone.utc).isoformat(),
              "runtime_selection": RUNTIME_PINS[runtime_pin], "runtime_manifest_sha256": runtime_pin,
              "runtime_snapshot_sha256": freeze["snapshot_sha256"],
              "runtime_files_checked_before_after": len(freeze["files"]),
              "runtime_root": str(runtime), "module_origins": origins,
              "material_freeze_sha256": MATERIAL_FREEZE_SHA256,
              "adapter_sha256": digest(Path(__file__).read_bytes()),
              "argv": sys.argv, "python": sys.version, "platform": platform.platform(),
              "passed": sum(r["passed"] for r in rows), "total": len(rows), "cases": rows,
              "raw_log": {"path": raw_path.name, "bytes": raw_path.stat().st_size,
                          "sha256": digest(raw_path.read_bytes()), "records": len(raw_records),
                          "uncompressed_sha256": digest(raw_bytes)},
              "scope": "Nine authored explicit-mark dispatch regressions only; no new held-out language score."}
    report_path = Path(str(args.output_prefix) + ".json")
    with report_path.open("x", encoding="utf-8") as output:
        output.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "total": result["total"],
                      "report": str(report_path), "report_sha256": digest(report_path.read_bytes()),
                      "failed": [r["id"] for r in rows if not r["passed"]]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
