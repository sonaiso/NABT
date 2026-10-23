#!/usr/bin/env python3
"""Check the complete finite word table against a fresh native Lean export."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nabt import words


def check_table(export: dict) -> dict:
    raw = (ROOT / "src/nabt/data/words.json").read_bytes()
    installed = json.loads(raw)
    canonical = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if canonical(export) != canonical(installed) or export["law_id"] != words.LAW_ID:
        raise ValueError("Installed word table differs from fresh Lean export")
    if export["class_case_number_domain"] != words.CLASS_CASE_DOMAIN:
        raise ValueError("Class/case number domain differs from Lean")
    if [(row["class"], row["case"]) for row in export["rows"]] != [(c, k) for c in range(15) for k in range(4)]:
        raise ValueError("Class/case outcomes must be complete, unique, and canonical")
    if [(row["class"], row["ending"]) for row in export["inverse"]] != [(c, e) for c in range(15) for e in range(11)]:
        raise ValueError("Inverse images must cover every declared class and ending")
    classes, rows = words.installed_table()
    if len(classes) != 15 or len(rows) != 60:
        raise ValueError("Wrong finite scope")
    for row in export["rows"]:
        pair = row["class"], row["case"]
        if (rows[pair] != row["ending"] or words.class_case_number(*pair) != row["number"]
                or words.decode_class_case(row["number"]) != pair):
            raise ValueError("Class/case numerical transport differs from Lean")
    for row in export["inverse"]:
        expected = tuple((row["class"], case) for case in row["cases"])
        if words.case_candidates((row["class"],), row["ending"]) != expected:
            raise ValueError("Python inverse differs from the checked finite relation")
    for kind in export["kinds"]:
        if kind["label"] != words.KINDS[kind["code"]]:
            raise ValueError("Kind codes differ")
        capacity = words.capacities(kind["code"])
        if [capacity["subject"], capacity["predicate"]] != kind["capacities"]:
            raise ValueError("Predication capacities differ from Lean")
    if sum(row["ending"] is not None for row in export["rows"]) != 45:
        raise ValueError("Unexpected licensed class/case pair count")
    return {"ok": True, "law_id": words.LAW_ID, "table_sha256": sha256(raw).hexdigest(),
            "kinds": 3, "declension_classes": 15, "ending_types": 11,
            "class_case_outcomes": 60, "licensed_pairs": 45, "inverse_images": 165,
            "scope": "finite conditional algebra and codecs; not parser refinement or Arabic completeness"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        proc = subprocess.run([args.lake, "env", "lean", "--run", "ExportWords.lean"],
                              cwd=ROOT / "formal", check=True, capture_output=True, text=True)
        report = check_table(json.loads(proc.stdout))
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
