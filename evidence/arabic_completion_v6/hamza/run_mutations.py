#!/usr/bin/env python3
"""Six local semantic mutants against fixed source gold and Lean control output.

This is development mutation evidence, not independent linguistic adjudication.
The production module and historical evidence are never modified.
"""
from __future__ import annotations
import json
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "src/nabt/classical_hamza.py"

MUTATIONS = [
    ("drop_interrogative_tashil", 'emit("interrogative_tashil", ["ء", "HAMZA_TASHIL", "ل", *tail])', 'pass'),
    ("ignore_added_alif", 'elif origin != "added":', 'elif False:'),
    ("ignore_verb_illal", 'elif state != "changed_to_alif":', 'elif False:'),
    ("ignore_singular_origin", 'elif origin != "added_long" or core[2] not in LONGS.values():', 'elif core[2] not in LONGS.values():'),
    ("admit_mafail_long", 'elif template != "mafail":', 'elif template == "other":'),
    ("drop_attested_oukul", 'emit("full_dialect_command", ["ء", "و", "ك", "ل"])', 'pass'),
]


def main():
    original = SOURCE.read_text()
    cases = json.loads((HERE / "diagnostics.json").read_text())["cases"]
    controls = json.loads((HERE / "lean_controls.json").read_text())["rows"]
    rows = []
    for name, old, new in MUTATIONS:
        assert old in original, name
        module = types.ModuleType("nabt._hamza_mutant")
        module.__package__ = "nabt"
        exec(compile(original.replace(old, new), str(SOURCE), "exec"), module.__dict__)
        failed_gold, failed_controls = [], []
        for case in cases:
            actual = module.evaluate(case["rule_id"], case["frame"])
            if (actual["status"] != case["expected_status"] or
                    [a["operation"] for a in actual["alternatives"]] != case["expected_operations"] or
                    [a["morphophonemes"] for a in actual["alternatives"]] != case["expected_outputs"]):
                failed_gold.append(case["case_id"])
        for index, row in enumerate(controls):
            actual = module.evaluate(row["rule_id"], row["frame"])
            if ([a["operation"] for a in actual["alternatives"]] != row["operations"] or
                    [a["morphophonemes"] for a in actual["alternatives"]] != row["outputs"]):
                failed_controls.append(index)
        rows.append({"mutation": name, "killed": bool(failed_gold or failed_controls),
                     "failing_source_cases": failed_gold, "failing_lean_control_indexes": failed_controls})
    result = {"schema": "nabt.classical-hamza-mutation.v1", "mutations": rows,
              "killed": sum(r["killed"] for r in rows), "total": len(rows)}
    (HERE / "mutations.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))
    if result["killed"] != result["total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
