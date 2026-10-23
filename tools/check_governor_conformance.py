#!/usr/bin/env python3
"""Compare installed governor data and Python with a fresh Lean export.

The 197 probes exhaust the roles relevant to each of the 13 finite equations,
including missing observations. They do not prove lexical parsing or source
truth, and they do not enumerate every arbitrary unused role assignment.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from itertools import product
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nabt import governors

FIELDS = {"schema_version", "law_id", "mark_codes", "roles", "classes", "entries",
          "role_mark_number_domain", "role_mark_codes"}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def check_table(export: dict) -> dict:
    if type(export) is not dict or set(export) != FIELDS | {"assignment_probes"}:
        raise ValueError("Unexpected Lean governor export fields")
    raw = (ROOT / "src/nabt/data/governors.json").read_bytes()
    installed = json.loads(raw)
    if set(installed) != FIELDS | {"source"}:
        raise ValueError("Unexpected installed governor fields")
    if canonical({key: installed[key] for key in FIELDS}) != canonical({key: export[key] for key in FIELDS}):
        raise ValueError("Installed governor algebra differs from fresh Lean export")
    if governors.LAW_ID != export["law_id"] or governors.ROLE_MARK_DOMAIN != export["role_mark_number_domain"]:
        raise ValueError("Runtime law or numeric domain differs from Lean")
    governors.installed_table()  # Independent installed-byte pin at runtime.
    if len(installed["entries"]) != 100 or len({e["label"] for e in installed["entries"]}) != 96:
        raise ValueError("Unexpected finite table scope")
    seen_numbers = set()
    for pair in export["role_mark_codes"]:
        if type(pair) is not dict or set(pair) != {"role", "mark", "number", "allowed"}:
            raise ValueError("Malformed numeric role/case export")
        if (type(pair["number"]) is not int or type(pair["allowed"]) is not bool
                or governors.role_mark_number(pair["role"], pair["mark"]) != pair["number"]
                or governors.decode_role_mark(pair["number"]) != (pair["role"], pair["mark"])
                or governors.category_allows(pair["role"], pair["mark"]) != pair["allowed"]
                or pair["number"] in seen_numbers):
            raise ValueError("Numeric role/case codec differs from Lean")
        seen_numbers.add(pair["number"])
    if len(seen_numbers) != 36:
        raise ValueError("Missing numeric role/case pairs")
    seen_probes = set()
    for probe in export["assignment_probes"]:
        if type(probe) is not dict or set(probe) != {"class_code", "assignments", "complete", "viable"}:
            raise ValueError("Malformed assignment probe")
        assignment = {v["role"]: v["mark"] for v in probe["assignments"]}
        if len(assignment) != len(probe["assignments"]):
            raise ValueError("Duplicate assignment role")
        result = governors.check_assignment(probe["class_code"], assignment)
        if any(canonical(result[key]) != canonical(probe[key]) for key in ("complete", "viable")):
            raise ValueError("Python assignment result differs from Lean")
        key = (probe["class_code"], tuple(sorted(assignment.items())))
        if key in seen_probes:
            raise ValueError("Repeated assignment probe")
        seen_probes.add(key)
    if len(seen_probes) != 197:
        raise ValueError("Unexpected finite assignment probe coverage")
    expected_probes = set()
    for cls in export["classes"]:
        roles = {role for alt in cls["alternatives"] for role, _ in alt}
        roles.update(role for pair in cls["links"] for role in pair)
        ordered = sorted(roles)
        for marks in product((None, 0, 1, 2, 3), repeat=len(ordered)):
            expected_probes.add((cls["code"], tuple(zip(ordered, marks))))
    if seen_probes != expected_probes:
        raise ValueError("Probe inventory does not exhaust exactly each class's relevant roles")
    return {"ok": True, "law_id": governors.LAW_ID, "table_sha256": sha256(raw).hexdigest(),
            "entries": 100, "distinct_labels": 96, "classes": 13,
            "numeric_role_mark_pairs": 36, "category_allowed_pairs": 27,
            "exhaustive_relevant_role_probes": len(seen_probes),
            "scope": "finite class algebra/codec conformance; no Python parser refinement or all-Arabic claim"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        run = subprocess.run([args.lake, "env", "lean", "--run", "ExportGovernors.lean"],
                             cwd=ROOT / "formal", check=True, capture_output=True, text=True)
        report = check_table(json.loads(run.stdout))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        if isinstance(exc, subprocess.CalledProcessError):
            print(exc.stdout or "")
            print(exc.stderr or "")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
