#!/usr/bin/env python3
"""Check a fresh Lean cue export and both public finite Python projections.

This gate proves no parser refinement or external linguistic activation. It
checks complete finite correspondence for the installed algebra, then checks
short evidence lists against an independent set-intersection interpretation.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from itertools import combinations, product
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nabt import text_evidence as algebra

KINDS = ("noun", "verb", "particle")
ACTIVATION_BITS = ("identity_match", "rule_match", "active", "blocked",
                   "support_present", "support_valid")


def canonical(value) -> str:
    """JSON text equality distinguishes true/1 and null/false, unlike ==."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Repeated export key: {key}")
        result[key] = value
    return result


def logical_candidates(cues: tuple[int, ...]) -> tuple[str, ...]:
    """A relation intersection; independent of bit numbering and table lookup."""
    permitted = set(KINDS)
    relations = ({"noun"}, {"verb"}, {"particle"})
    for cue in cues:
        permitted.intersection_update(relations[cue])
    return tuple(kind for kind in KINDS if kind in permitted)


def logical_activation(flags: tuple[bool, ...]) -> bool:
    """Named prerequisite inclusion, with a separate blocking condition."""
    present = {name for name, flag in zip(ACTIVATION_BITS, flags) if flag}
    required = {"identity_match", "rule_match", "active", "support_present", "support_valid"}
    return required.issubset(present) and "blocked" not in present


def check_table(export: dict) -> dict:
    installed = algebra.installed_table()
    if canonical(export) != canonical(installed):
        raise ValueError("Installed text-evidence table differs from fresh Lean export")
    if export["law_id"] != algebra.LAW_ID:
        raise ValueError("Text-evidence law identifier differs")
    if canonical(export["number_domains"]) != canonical({
        "kind_mask": "nabt.text-evidence.kind-cue-mask.v1",
        "activation_mask": "nabt.text-evidence.activation-mask.v1",
    }):
        raise ValueError("Text-evidence mask domains differ")
    if canonical(export["kinds"]) != canonical([
        {"code": code, "label": name} for code, name in enumerate(KINDS)
    ]) or type(algebra.KINDS) is not tuple or algebra.KINDS != KINDS:
        raise ValueError("Kind interpretation differs from the declared relation")
    if canonical(export["cues"]) != canonical([
        {"bit": 0, "kind": 0, "label": "noun_sign"},
        {"bit": 1, "kind": 1, "label": "independent_verb_witness"},
        {"bit": 2, "kind": 2, "label": "particle_witness"},
    ]):
        raise ValueError("Cue interpretation differs")
    if canonical(export["activation_bits"]) != canonical(ACTIVATION_BITS):
        raise ValueError("Receipt flag interpretation differs")
    for key, count in (("kind_rows", 8), ("receipt_rows", 64)):
        if canonical([row["mask"] for row in export[key]]) != canonical(list(range(count))):
            raise ValueError(f"{key} must be complete, unique and in canonical mask order")

    mask_checks = 0
    for width in range(4):
        for cues in combinations(range(3), width):
            expected = logical_candidates(cues)
            mask = sum(2 ** cue for cue in cues)
            row = export["kind_rows"][mask]
            encoded = [KINDS.index(kind) for kind in expected]
            selected = encoded[0] if len(encoded) == 1 else None
            if canonical(row["candidates"]) != canonical(encoded) or canonical(row["selected"]) != canonical(selected):
                raise ValueError(f"Lean mask {mask} differs from independent cue intersection")
            actual = algebra.kind_candidates(cues)
            if type(actual) is not tuple or actual != expected:
                raise ValueError(f"Python mask {mask} differs from the checked relation")
            mask_checks += 1

    receipt_checks = 0
    for flags in product((False, True), repeat=6):
        mask = sum(2 ** position for position, flag in enumerate(flags) if flag)
        expected = logical_activation(flags)
        observed = export["receipt_rows"][mask]["activated"]
        actual = algebra.receipt_activated(flags)
        if type(observed) is not bool or observed is not expected or type(actual) is not bool or actual is not expected:
            raise ValueError(f"Receipt mask {mask} differs from named prerequisite semantics")
        receipt_checks += 1

    list_checks = deletion_checks = duplication_checks = 0
    for width in range(5):
        for cues in product(range(3), repeat=width):
            expected = logical_candidates(cues)
            actual = algebra.kind_candidates(cues)
            if type(actual) is not tuple or actual != expected:
                raise ValueError(f"Public cue list differs from independent relation: {cues}")
            list_checks += 1
            for index, cue in enumerate(cues):
                without = cues[:index] + cues[index + 1:]
                wider = algebra.kind_candidates(without)
                if wider != logical_candidates(without) or not set(actual).issubset(wider):
                    raise ValueError("Deleting one receipt narrowed the candidate relation")
                deletion_checks += 1
                duplicated = cues[:index] + (cue,) + cues[index:]
                if algebra.kind_candidates(duplicated) != actual:
                    raise ValueError("Duplicating one receipt changed its authority")
                duplication_checks += 1

    raw = (ROOT / "src/nabt/data/text_evidence.json").read_bytes()
    return {"ok": True, "law_id": algebra.LAW_ID,
            "table_sha256": sha256(raw).hexdigest(),
            "kind_masks": mask_checks, "receipt_masks": receipt_checks,
            "independent_cue_lists": list_checks,
            "max_source_list_length": 4,
            "single_deletion_checks": deletion_checks,
            "duplicate_receipt_checks": duplication_checks,
            "scope": "Complete finite conditional algebra correspondence and bounded list properties; "
                     "not source-reader refinement, linguistic cue activation or Arabic completeness"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        subprocess.run([args.lake, "build"], cwd=ROOT / "formal",
                       check=True, capture_output=True, text=True)
        process = subprocess.run([args.lake, "env", "lean", "--run", "ExportTextEvidence.lean"],
                                 cwd=ROOT / "formal", check=True, capture_output=True, text=True)
        export = json.loads(process.stdout, object_pairs_hook=unique_object,
                            parse_constant=lambda value: (_ for _ in ()).throw(
                                ValueError(f"Non-JSON export constant: {value}")))
        report = check_table(export)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        if isinstance(error, subprocess.CalledProcessError):
            print(error.stdout or "")
            print(error.stderr or "")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
