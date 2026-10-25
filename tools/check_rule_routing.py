#!/usr/bin/env python3
"""Compare the proposal scheduler with Lean on a finite independent test domain."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from tools.grammar_catalog.routing import schedule  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        subprocess.run([args.lake, "build", "exportRuleRouting"], cwd=ROOT / "formal",
                       check=True, capture_output=True, text=True)
        execution = subprocess.run([str(ROOT / "formal/.lake/build/bin/exportRuleRouting")],
                                   check=True, capture_output=True, text=True)
        data = json.loads(execution.stdout)
        rows = data["rows"]
        if data["law_id"] != "nabt.rule-routing.v1" or len(rows) != 341:
            raise ValueError("unexpected Lean conformance domain")
        seen = set()
        for row in rows:
            ranked = tuple(row["ranked"])
            if ranked in seen:
                raise ValueError("repeated conformance input")
            seen.add(ranked)
            actual = schedule(row["inventory"], row["ranked"])
            if actual != row["schedule"]:
                raise ValueError("Python schedule differs from Lean")
            if set(actual) != set(row["inventory"]) or len(actual) != len(row["inventory"]):
                raise ValueError("installed membership or uniqueness lost")
            for budget, complete in enumerate(row["budget_complete"]):
                if complete != (budget >= len(actual)):
                    raise ValueError("budget completion differs from Lean")
            for mask, accepted in enumerate(row["accepted"]):
                # Independent finite subset oracle in inventory order. Compare
                # membership rather than requiring the ranker's presentation order.
                expected = {name for bit, name in enumerate(row["inventory"])
                            if mask & (1 << bit)}
                if set(accepted) != expected:
                    raise ValueError("checker acceptance changed with ranking")
        report = {"ok": True, "law_id": data["law_id"], "schedules": len(rows),
                  "budget_cases": len(rows) * 5, "checker_cases": len(rows) * 8,
                  "scope": "three installed IDs, one unknown ID, rankings of length 0 through 4",
                  "python_lean_refinement_theorem": False, "arabic_completeness_claim": False}
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report))
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        if isinstance(exc, subprocess.CalledProcessError):
            print(exc.stdout or "")
            print(exc.stderr or "")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
