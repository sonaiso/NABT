#!/usr/bin/env python3
"""Independent finite surface/forward-inference conformance against native Lean.

The expected answers below follow a one-rule truth table, not the production
parser or closure recurrence. This checks a named finite matrix, not Arabic
population accuracy or general Python refinement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


def fixtures():
    names = ("زيد", "عمرو")
    frames = ("", " أمامك", " خلف الدار", " أمامك خلف الدار")
    for person in names:
        for positive in (True, False):
            for frame in frames:
                text = ("سار " if positive else "لم يسر ") + person + frame
                yield "motion_fact", text, "هل سار " + person + frame + "؟", (
                    "SUPPORTED" if positive else "REFUTED")
            text = ("عرف " if positive else "لم يعرف ") + person + " الحق"
            yield "knowledge_fact", text, "هل عرف " + person + " الحق؟", (
                "SUPPORTED" if positive else "REFUTED")
    for knower in names:
        for antecedent_positive in (True, False):
            body = ("عرف " if antecedent_positive else "لم يعرف ") + knower + " الحق"
            opposite = ("لم يعرف " if antecedent_positive else "عرف ") + knower + " الحق"
            for walker in names:
                for head_positive in (True, False):
                    for frame in frames:
                        head = ("سار " if head_positive else "لم يسر ") + walker + frame
                        query = "هل سار " + walker + frame + "؟"
                        for order in ("front", "post"):
                            rule = "إن " + body + " " + head if order == "front" else head + " إن " + body
                            for premise_kind, seed in (("absent", ""), ("matching", body), ("opposite", opposite)):
                                text = rule + "." + (" " + seed + "." if seed else "")
                                expected = ("SUPPORTED" if head_positive else "REFUTED") if premise_kind == "matching" else "UNKNOWN"
                                yield "conditional_" + order + "_" + premise_kind, text, query, expected
    # Separate written-case witnesses, signed query inversion and two independent
    # contradictory reports. Neither passive nor causative is normalized to active.
    yield "vocalized", "سَارَ زَيْدٌ أَمَامَكَ خَلْفَ الدَّارِ.", "هَلْ سَارَ زَيْدٌ أَمَامَكَ خَلْفَ الدَّارِ؟", "SUPPORTED"
    yield "vocalized", "إِنْ عَرَفَ زَيْدٌ الْحَقَّ سَارَ زَيْدٌ. عَرَفَ زَيْدٌ الْحَقَّ.", "هَلْ سَارَ زَيْدٌ؟", "SUPPORTED"
    yield "negative_query", "لم يسر عمرو خلف الدار.", "هل لم يسر عمرو خلف الدار؟", "SUPPORTED"
    yield "negative_query", "سار عمرو خلف الدار.", "هل لم يسر عمرو خلف الدار؟", "REFUTED"
    yield "conflict", "سار زيد. لم يسر زيد.", "هل سار زيد؟", "CONFLICT"
    yield "unrelated_conflict", "عرف زيد الحق. لم يعرف زيد الحق.", "هل سار عمرو؟", "UNKNOWN"


def snapshot(executable: Path):
    files = {executable.resolve()}
    for folder in (ROOT / "formal", ROOT / "tools/licensed_inference"):
        files.update(p for p in folder.rglob("*")
                     if p.is_file() and ".lake" not in p.parts and "__pycache__" not in p.parts)
    files.update((ROOT / "tools/verified_reading.py", Path(__file__).resolve(),
                  ROOT / "evidence/licensed_inference_v1/source_links.json"))
    return {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else "native_external":
            hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def check(executable: Path):
    from tools.licensed_inference import evaluate, aggregate_evidence
    installed = ROOT / "formal/.lake/build/bin/licensedInference"
    if executable.resolve() != installed.resolve():
        raise ValueError("conformance must measure the runtime's fixed installed native executable")
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise ValueError("native licensedInference executable is required")
    before = snapshot(executable)
    failures, counts = [], {}
    rows = list(fixtures())
    if len(rows) != 410:
        raise ValueError("independent finite matrix changed without a revised denominator")
    for index, (family, text, query, expected) in enumerate(rows):
        result = evaluate(text, query, source_id="conformance:" + str(index),
                          revision="v1", scope="finite-active-fragment", time="abstract-episode")
        counts[family] = counts.get(family, 0) + 1
        good = (result.get("status") == expected and result.get("native_checked") is True
                and result.get("all_readings_complete") is True
                and result.get("world_truth_established") is False
                and result.get("all_arabic_complete") is False)
        if not good:
            failures.append({"index": index, "family": family, "source_text": text,
                             "query_text": query, "expected": expected, "observed": result})
    # All 4-bit records and ordered pairs, including deliberately incoherent
    # records, exercise arithmetic aggregation only; these are not certificates.
    def bits(n):
        return dict(zip(("positive", "negative", "clean_positive", "clean_negative"),
                        (bool(n & (1 << i)) for i in range(4))))
    expected_inputs = [[]] + [[bits(i)] for i in range(16)] + [
        [bits(i), bits(j)] for i in range(16) for j in range(16)]
    exported = subprocess.run([str(executable), "--export"], check=True,
                              capture_output=True, text=True, timeout=60)
    aggregate_rows = [json.loads(line) for line in exported.stdout.splitlines()]
    if len(aggregate_rows) != len(expected_inputs):
        raise ValueError("native aggregation export is incomplete")
    for index, (inputs, native) in enumerate(zip(expected_inputs, aggregate_rows)):
        calculated = aggregate_evidence(inputs)
        expected = {"law_id": "nabt.licensed-inference.v1", "row_kind": "aggregate_fixture",
                    "authority": "DIAGNOSTIC_AGGREGATION_ONLY", "verified": False,
                    "evidence": inputs, **calculated}
        if proof_wire(native) != proof_wire(expected):
            failures.append({"aggregation_index": index, "expected": expected, "observed": native})
    after = snapshot(executable)
    return {"schema": "nabt.licensed-inference-conformance.v1",
            "total": len(rows) + len(aggregate_rows), "source_query_cases": len(rows),
            "diagnostic_aggregation_cases": len(aggregate_rows),
            "families": counts, "mismatches": failures, "inputs": before,
            "inputs_unchanged": before == after, "pass": not failures and before == after,
            "evidence_kind": "finite_independent_forward_truth_table_and_surface_checks",
            "native_json_parser_refinement_proved": False, "python_refinement_proved": False,
            "source_translation_fidelity_proved": False, "all_arabic_complete": False,
            "world_truth_established": False}


def proof_wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, default=ROOT / "formal/.lake/build/bin/licensedInference")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = check(args.executable)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("total", "families", "inputs_unchanged", "pass")}, ensure_ascii=False))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
