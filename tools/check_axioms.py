#!/usr/bin/env python3
"""Run Lean's enforcing axiom audit and check its machine-readable manifest."""

import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"propext", "Classical.choice", "Quot.sound"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        execution = subprocess.run([args.lake, "env", "lean", "Audit.lean"],
                                   cwd=ROOT / "formal", check=True, capture_output=True, text=True)
        log = execution.stdout
        entries = re.findall(r"NABT_THEOREM (Nabt\.[\w.']+) AXIOMS \[([^\]]*)\]", log)
        actual_names = [name for name, _ in entries]
        manifest = json.loads((ROOT / "formal" / "theorems.json").read_text(encoding="utf-8"))["theorems"]
        if actual_names != manifest or len(set(manifest)) != len(manifest):
            raise ValueError("Compiled theorem audit differs from the unique declaration manifest")
        if not manifest or f"NABT_THEOREM_COUNT {len(manifest)}" not in log or "NABT_AUDIT_OK" not in log:
            raise ValueError("Lean audit did not report full success")
        theorem_axioms = {name: sorted(a.strip() for a in raw.split(",") if a.strip()) for name, raw in entries}
        observed = set().union(*(set(values) for values in theorem_axioms.values()))
        if not observed <= ALLOWED:
            raise ValueError(f"Unapproved axioms: {sorted(observed - ALLOWED)}")
        report = {"ok": True, "theorem_count": len(manifest), "observed_axioms": sorted(observed),
                  "project_axioms_allowed": False, "all_nabt_declarations_scanned": True,
                  "theorem_axioms": theorem_axioms}
        content = json.dumps(report, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding="utf-8")
            args.output.with_suffix(".log").write_text(log, encoding="utf-8")
        print(json.dumps({key: value for key, value in report.items() if key != "theorem_axioms"}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        if isinstance(exc, subprocess.CalledProcessError):
            print(exc.stdout or "")
            print(exc.stderr or "")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
