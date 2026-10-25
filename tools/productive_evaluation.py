#!/usr/bin/env python3
"""Identical authored diagnostics on a selected runtime; no gold passed to NABT."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
MATERIAL_SHA256 = 'df414b7ba82fe39f9864139d9207e79472815d0b4532ed60d2e871d461aae3a1'
SOURCE_SHA256 = 'ed24c28da3c603f2e52825d0af4679aa3799228ef7538bc90992178cc69f9455'


def run(runtime_root, output):
    if output.exists():
        raise ValueError("Refusing to replace an observed measurement")
    sys.path.insert(0, str(runtime_root / "src"))
    sys.path.insert(1, str(ROOT))
    from nabt.corpus_evidence import learn_qac_lexicon
    from nabt.person_evidence import person_candidates
    from nabt.discourse import read_discourse, verify_discourse
    from tools.discourse_evaluation import SourceAudit
    from tools.productive_form_validation import validate_imperative, validate_nominal
    folder = ROOT / "evidence/arabic_completion_v4"
    material = folder / "productive_cases.json"
    source = (folder / "productive_source.tsv").read_bytes()
    if sha256(material.read_bytes()).hexdigest() != MATERIAL_SHA256 or sha256(source).hexdigest() != SOURCE_SHA256:
        raise ValueError("Diagnostic material differs from its declared freeze")
    reference = json.loads(material.read_bytes())
    records, journal = [], []
    start = time.perf_counter()
    for c in reference["cases"]:
        model = learn_qac_lexicon(source, excluded_verses=tuple(c["excluded_verses"]), source_id="productive_diagnostic")
        audit = SourceAudit(source, c["excluded_verses"], "productive_diagnostic")
        began = time.perf_counter()
        if c["family"] == "imperative":
            report = person_candidates(c["text"], lexical_model=model)
            rows = [r for r in report if r.get("aspect") == "IMPV" and r.get("construction") == "built"]
            for row in rows:
                if row.get("productive_derivation"):
                    validate_imperative(row, audit)
        else:
            report = read_discourse(c["text"], lexical_model=model, source_id="productive_target")
            if not verify_discourse(report, lexical_model=model)["valid"]:
                raise ValueError("Report replay failed")
            rows = [r for o in report["occurrences"] for r in o["readings"]
                    if r.get("kind") == "noun" and r.get("construction") == "inflected" and
                    r.get("possible_cases") == [0]]
            for row in rows:
                if row.get("nominal_case_carrier", {}).get("generated_form"):
                    validate_nominal(row, {"text": c["text"], "source_id": "productive_target"}, audit)
        accepted = bool(rows)
        records.append({"id": c["id"], "family": c["family"], "expected": c["expected"],
                        "accepted": accepted, "passed": accepted == c["expected"], "readings": len(rows),
                        "seconds": time.perf_counter() - began})
        journal.append({"id": c["id"], "report": report})
    positives = [c for c in records if c["expected"]]
    negatives = [c for c in records if not c["expected"]]
    runtime = [{"path": str(p.relative_to(runtime_root)), "sha256": sha256(p.read_bytes()).hexdigest()}
               for p in sorted((runtime_root / "src").rglob("*")) if p.is_file() and "__pycache__" not in p.parts]
    result = {"schema": "nabt.productive-evaluation.v1", "scope": reference["scope"],
              "material_sha256": sha256(material.read_bytes()).hexdigest(), "source_sha256": sha256(source).hexdigest(),
              "runtime": runtime, "cases": records, "total": len(records), "passed": sum(c["passed"] for c in records),
              "positive_coverage": {"numerator": sum(c["accepted"] for c in positives), "denominator": len(positives)},
              "false_accepts": {"numerator": sum(c["accepted"] for c in negatives), "denominator": len(negatives)},
              "seconds": time.perf_counter() - start, "universal_arabic_completeness": "NOT_INFERRED"}
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for r in journal).encode()
    raw_path = output.with_suffix(".raw.jsonl")
    if raw_path.exists():
        raise ValueError("Raw measurement already exists")
    raw_path.write_bytes(raw)
    result["raw_sha256"] = sha256(raw).hexdigest()
    result["checker_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
    result["independent_source_validator_sha256"] = sha256((ROOT / "tools/productive_form_validation.py").read_bytes()).hexdigest()
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("total", "passed", "positive_coverage", "false_accepts", "seconds")}))
    return 0 if result["passed"] == result["total"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.exit(run(args.runtime_root.resolve(), args.output.resolve()))
