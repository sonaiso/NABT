#!/usr/bin/env python3
"""Fresh finite Lean/Python correspondence for bounded classical grammar fragments.

The 49 rows cover eight supplied grammatical courses, four ambiguous surface
markers, 36 supplied inna-family contexts, and one source-declared partition.
This checks their conditional algebra, not a parser of a book or a new sentence
and not universal grammar.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import itertools
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
COURSES = ("nasb", "jarr", "raf", "jazm", "fath", "damm", "kasr", "waqf")
SURFACES = ("fatha", "kasra", "damma", "sukun")
OPERATORS = ("inna", "anna", "kaanna", "lakinna", "layta", "laalla")
FORMS = ("full", "light")
MA_STATES = ("absent", "kaffa", "unknown")
EXPECTED_KEYS = (frozenset(("course", course) for course in COURSES)
                 | frozenset(("surface", surface) for surface in SURFACES)
                 | frozenset(("inna", op, form, ma)
                             for op, form, ma in itertools.product(OPERATORS, FORMS, MA_STATES))
                 | frozenset({("awamil_partition",)}))


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def parse_row(raw):
    def reject_constant(value):
        raise ValueError("Non-JSON constant: " + value)

    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=reject_constant)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def choice(value, choices, name):
    if type(value) is not str or value not in choices:
        raise ValueError("Invalid " + name)


def choice_list(value, choices, name):
    if type(value) is not list:
        raise ValueError(name + " must be an array")
    for item in value:
        choice(item, choices, name)
    if len(set(value)) != len(value):
        raise ValueError("Duplicate " + name)


def row_key(row):
    if type(row) is not dict:
        raise ValueError("Every row must be an object")
    kind = row.get("kind")
    choice(kind, ("course", "surface", "inna", "awamil_partition"), "row kind")
    schemas = {
        "course": {"law_id", "kind", "course", "surface", "regime"},
        "surface": {"law_id", "kind", "surface", "courses"},
        "inna": {"law_id", "kind", "operator", "form", "ma", "options"},
        "awamil_partition": {"law_id", "kind", "samai", "qiyasi", "manawi", "total"},
    }
    if set(row) != schemas[kind]:
        raise ValueError("Unexpected row schema")
    expected_law = {"inna": "qatr-inna-v1",
                    "awamil_partition": "jurjani-awamil-partition-v1"}.get(
                        kind, "sibawayhi-functions-v1")
    if row["law_id"] != expected_law:
        raise ValueError("Wrong grammar law identity")
    if kind == "awamil_partition":
        for name in ("samai", "qiyasi", "manawi", "total"):
            if type(row[name]) is not int or not 0 <= row[name] <= 100:
                raise ValueError("Invalid partition integer: " + name)
        return (kind,)
    if kind == "course":
        choice(row["course"], COURSES, "course")
        choice(row["surface"], SURFACES, "surface")
        choice(row["regime"], ("irab", "bina"), "regime")
        return kind, row["course"]
    if kind == "surface":
        choice(row["surface"], SURFACES, "surface")
        choice_list(row["courses"], COURSES, "courses")
        return kind, row["surface"]
    choice(row["operator"], OPERATORS, "operator")
    choice(row["form"], FORMS, "form")
    choice(row["ma"], MA_STATES, "ma state")
    choice_list(row["options"], ("governed", "blocked"), "options")
    return kind, row["operator"], row["form"], row["ma"]


def index_rows(rows, origin):
    if type(rows) is not list or len(rows) != 49:
        raise ValueError(origin + " must contain exactly 49 rows")
    index = {}
    for row in rows:
        key = row_key(row)
        if key not in EXPECTED_KEYS or key in index:
            raise ValueError(origin + " contains an out-of-domain or duplicate input tuple")
        index[key] = row
    if set(index) != EXPECTED_KEYS:
        raise ValueError(origin + " omits part of the finite input domain")
    return index


def check_export(raw):
    lines = raw.splitlines()
    if len(lines) != 49:
        raise ValueError(f"Expected 49 fresh Lean rows; received {len(lines)}")
    exported = [parse_row(line) for line in lines]
    lean = index_rows(exported, "Lean export")
    sys.path.insert(0, str(ROOT))
    from tools.classical_language_evidence import formal_rows

    actual = formal_rows()
    python = index_rows(actual, "Python mirror")
    for key in sorted(EXPECTED_KEYS):
        if canonical(lean[key]) != canonical(python[key]):
            raise ValueError("Python/Lean mismatch for " + repr(key))
    return {
        "ok": True,
        "law_ids": ["sibawayhi-functions-v1", "qatr-inna-v1", "jurjani-awamil-partition-v1"],
        "rows_compared": 49,
        "domains": {"courses": list(COURSES), "surfaces": list(SURFACES),
                    "operators": list(OPERATORS), "forms": list(FORMS), "ma": list(MA_STATES)},
        "rows_by_kind": {"course": 8, "surface": 4, "inna": 36, "awamil_partition": 1},
        "duplicate_or_missing_rows": 0,
        "type_sensitive_comparison": True,
        "fresh_export_sha256": sha256(raw.encode("utf-8")).hexdigest(),
        "runtime_rows_sha256": sha256(canonical(actual).encode("utf-8")).hexdigest(),
        "source_catalog_verified_by_this_check": False,
        "source_reader_formally_verified": False,
        "target_text_parsed": False,
        "external_event_established": False,
        "universal_language_certified": False,
        "scope": ("Exhaustive finite correspondence of conditional grammar laws on supplied "
                  "interpretations. Source attestation and the applicability of those interpretations "
                  "to a target sentence are separate obligations."),
    }


def file_record(path):
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
            "sha256": sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--raw-output", type=Path,
                        help="Save the fresh Lean JSONL export without overwriting an existing file")
    args = parser.parse_args()
    try:
        for destination in (args.output, args.raw_output):
            if destination is not None and destination.exists():
                raise ValueError("Evidence output already exists: " + str(destination))
        filenames = (
            "formal/lean-toolchain", "formal/Nabt/ClassicalLanguageEvidence.lean",
            "formal/ExportClassicalLanguageEvidence.lean",
            "tools/classical_language_evidence.py", "tools/check_classical_language_evidence.py",
        )
        files_before = [file_record(ROOT / name) for name in filenames]
        build_command = [args.lake, "build", "exportClassicalLanguageEvidence"]
        export_command = [args.lake, "env", "lean", "--run", "ExportClassicalLanguageEvidence.lean"]
        subprocess.run(build_command, cwd=ROOT / "formal", check=True,
                       capture_output=True, text=True, timeout=300)
        result = subprocess.run(export_command, cwd=ROOT / "formal", check=True,
                                capture_output=True, text=True, timeout=90)
        report = check_export(result.stdout)
        files_after = [file_record(ROOT / name) for name in filenames]
        if files_after != files_before:
            raise ValueError("A checked implementation file changed during conformance execution")
        report["provenance"] = {
            "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
            "toolchain": (ROOT / "formal/lean-toolchain").read_text().strip(),
            "build_command": build_command, "export_command": export_command,
            "files_unchanged_during_execution": True,
            "files": files_after,
        }
        if args.raw_output:
            args.raw_output.parent.mkdir(parents=True, exist_ok=True)
            with args.raw_output.open("x", encoding="utf-8") as handle:
                handle.write(result.stdout)
            report["provenance"]["raw_export_path"] = str(args.raw_output)
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(rendered)
        print(rendered, end="")
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        if isinstance(error, subprocess.CalledProcessError):
            print(error.stdout or "")
            print(error.stderr or "")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
