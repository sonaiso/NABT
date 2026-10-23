#!/usr/bin/env python3
"""Compare the installed morphology law with a freshly executed Lean export."""

from __future__ import annotations

import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nabt import morphology as algebra


def check_table(export):
    installed = algebra.installed_table()
    canonical = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if canonical(export) != canonical(installed) or installed["law_id"] != algebra.LAW_ID:
        raise ValueError("Installed morphology table differs from fresh Lean export")
    if [row["mask"] for row in installed["cause_rows"]] != list(range(2048)):
        raise ValueError("Cause masks must be complete, canonical and unique")
    if [row["label"] for row in installed["cause_traits"]] != list(algebra.CAUSE_TRAITS):
        raise ValueError("Qualified cause schema differs")
    if [row["number"] for row in installed["verb_rows"]] != list(range(12)):
        raise ValueError("Verb inputs must be complete, canonical and unique")
    identity = {"source": "conformance", "occurrence": "finite", "reading": "r1",
                "context": "conditional_law", "policy": "fresh_lean_export"}
    for row in export["cause_rows"]:
        mask = row["mask"]
        states = tuple(1 if mask & (1 << i) else 2 for i in range(11))
        if algebra.cause_candidates(states) != (row["diptote"],):
            raise ValueError("Full cause evidence differs from Lean")
        residual = algebra.named_residual(algebra.CAUSE_TRAITS, states, identity=identity, formula_kind="cause")
        if (residual["status"] == "LICENSED") != row["diptote"]:
            raise ValueError("Named cause formula differs from Lean's full truth table")
    for row in export["genitive_rows"]:
        states = (row["al"], row["idhafa"])
        if algebra.evidence_number(states) != row["number"] or algebra.decode_evidence(row["number"], 2) != states:
            raise ValueError("Context evidence number differs from Lean")
        residual = algebra.named_residual(("al", "idhafa"), states, identity=identity, formula_kind="genitive")
        expected_status = ("PENDING", "REJECTED", "LICENSED", "CONFLICT")[row["result"]]
        if residual["status"] != expected_status:
            raise ValueError("Context projection differs from Lean")
        if residual["status"] != "CONFLICT":
            plans = sorted(sum(1 << (0 if name == "al" else 1) for name in plan) for plan in residual["minimal_plans"])
            if plans != sorted(row["plans"]):
                raise ValueError("Named contextual residual differs from Lean")
        candidates = sorted({2 if al or idhafa else 1 for al, idhafa in
                             product(*(algebra.possible_bools(s) for s in states))})
        if candidates != row["candidates"]:
            raise ValueError("Conditional endings differ from Lean")
    # The partial tables check the reader's relevant truth-table projections.
    from nabt.morphology_reader import read_morphology
    tense_clause = ("فعله ماض", "فعله مضارع", "فعله أمر")
    nun_clause = ("لا تتصل به نون إناث ولا نون توكيد", "تتصل به نون التوكيد مباشرة",
                  "تفصل بينه وبين نون التوكيد فاصل", "تتصل به نون الإناث")
    for row in export["verb_partial"]:
        clauses = ["يدل على حدث مقترن بزمن بهيئته"]
        if row["tense"] is not None:
            clauses.append(tense_clause[row["tense"]])
        if row["nun"] is not None:
            clauses.append(nun_clause[row["nun"]])
        text = "قراءة «r1» للفظ «فَعَلَ»:\n" + "\n".join(clauses)
        axis = read_morphology(text)["readings"][0]["axes"]["construction"]
        if axis["candidates"] != sorted(algebra.CONSTRUCTIONS[i] for i in row["constructions"]):
            raise ValueError("Source-reader verb candidates differ from Lean")
    def clauses_for(state, positive, negative):
        return ([positive] if state & 1 else []) + ([negative] if state & 2 else [])

    def axes_for(clauses):
        text = "قراءة «r1» للفظ «مِثَالٌ»:\n" + "\n".join(["يدل على معنى مستقل غير مقترن بزمن", *clauses])
        return read_morphology(text)["readings"][0]["axes"]

    for row in export["noun_partial"]:
        axis = axes_for(clauses_for(row["particle_resemblance"], "يشبه الحرف", "يسلم من شبه الحرف"))["construction"]
        if axis["candidates"] != sorted(algebra.CONSTRUCTIONS[i] for i in row["constructions"]):
            raise ValueError("Source-reader noun candidates differ from Lean")
    for row in export["nominal_partial"]:
        clauses = clauses_for(row["universal"], "لا يمنع تصوره الشركة", "يمنع تصوره الشركة")
        clauses += clauses_for(row["quality_bearer"], "يدل على ذات باعتبار صفة", "يدل على ذات دون اعتبار صفة")
        axis = axes_for(clauses)["nominal_semantics"]
        if axis["candidates"] != sorted(("outside_universal_noun", "jins_jamid", "mushtaq")[i] for i in row["denotations"]):
            raise ValueError("Source-reader nominal denotations differ from Lean")
    for row in export["genitive_rows"]:
        clauses = ["يسلم من شبه الحرف", "آخره ألف التأنيث"]
        clauses += clauses_for(row["al"], "دخلت عليه أل", "لم تدخل عليه أل")
        clauses += clauses_for(row["idhafa"], "هو مضاف", "ليس مضافا")
        axis = axes_for(clauses)["diptote"]["genitive"]
        if axis["candidates"] != sorted({1: "fatha", 2: "kasra"}[i] for i in row["candidates"]):
            raise ValueError("Source-reader conditional genitive signs differ from Lean")
    raw = (ROOT / "src/nabt/data/morphology.json").read_bytes()
    return {"ok": True, "law_id": algebra.LAW_ID, "table_sha256": sha256(raw).hexdigest(),
            "verb_rows": 12, "verb_partial": 20, "noun_rows": 2, "noun_partial": 4,
            "nominal_rows": 4, "nominal_partial": 16, "cause_rows": 2048, "genitive_contexts": 16,
            "public_reader_partial_projections": 56,
            "scope": "Finite conditional algebra and reader projections; not unrestricted Arabic understanding"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = subprocess.run([args.lake, "env", "lean", "--run", "ExportMorphology.lean"],
                                cwd=ROOT / "formal", capture_output=True, text=True, check=True)
        report = check_table(json.loads(result.stdout))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        if isinstance(error, subprocess.CalledProcessError):
            print(error.stdout or ""); print(error.stderr or "")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
