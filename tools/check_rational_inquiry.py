#!/usr/bin/env python3
"""Compare every bounded inquiry-gate input with a fresh Lean executable.

The table covers nine Boolean inputs and both ranks in 0..3. It verifies the
decision gate only. It does not prove that the Python source adapter derived
those inputs correctly, authenticate declared provenance, establish real-world
truth, or certify any human thinking rank.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import itertools
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LAW_ID = "nabt.rational-inquiry.v1"
FLAGS = (
    "formed", "reviewed", "provenance", "scopeCovered", "supported",
    "counterevidence", "requiresWorldBridge", "worldBridge", "exhausted",
)
ROW_KEYS = frozenset({
    "law_id", "mask", "requested_rank", "evidence_rank", "verdict",
    "authorized_rank",
})
EXPECTED_KEYS = frozenset(itertools.product(range(512), range(4), range(4)))


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


def check_export(raw: str):
    """Validate the complete fresh export; never accept a caller-supplied score."""
    sys.path.insert(0, str(ROOT / "src"))
    from nabt.rational_inquiry import decide_gate

    lines = raw.splitlines()
    if len(lines) != len(EXPECTED_KEYS):
        raise ValueError(f"Expected 8192 rows; received {len(lines)}")
    seen = set()
    verdict_counts = {}
    for index, line in enumerate(lines, 1):
        row = parse_row(line)
        if type(row) is not dict or frozenset(row) != ROW_KEYS:
            raise ValueError(f"Unexpected row schema at line {index}")
        if row["law_id"] != LAW_ID:
            raise ValueError(f"Wrong installed law identity at line {index}")
        for field in ("mask", "requested_rank", "evidence_rank", "authorized_rank"):
            if type(row[field]) is not int:
                raise ValueError(f"Non-integer {field} at line {index}")
        key = row["mask"], row["requested_rank"], row["evidence_rank"]
        if key not in EXPECTED_KEYS or key in seen:
            raise ValueError(f"Out-of-domain or duplicate input tuple at line {index}")
        seen.add(key)
        checks = {flag: bool(row["mask"] & (1 << bit))
                  for bit, flag in enumerate(FLAGS)}
        checks.update(requestedRank=row["requested_rank"],
                      evidenceRank=row["evidence_rank"])
        expected = {"verdict": row["verdict"],
                    "authorized_rank": row["authorized_rank"]}
        actual = decide_gate(checks)
        if canonical(actual) != canonical(expected):
            raise ValueError(f"Python/Lean decision mismatch for input {key}: "
                             f"Python={canonical(actual)}, Lean={canonical(expected)}")
        verdict_counts[row["verdict"]] = verdict_counts.get(row["verdict"], 0) + 1
    if seen != EXPECTED_KEYS:
        raise ValueError("Incomplete input domain")
    return {
        "ok": True,
        "law_id": LAW_ID,
        "rows_compared": len(seen),
        "input_domain": {"boolean_flags": list(FLAGS), "mask_count": 512,
                         "requested_ranks": [0, 1, 2, 3],
                         "evidence_ranks": [0, 1, 2, 3]},
        "verdict_counts": verdict_counts,
        "duplicate_or_missing_rows": 0,
        "type_sensitive_comparison": True,
        "fresh_export_sha256": sha256(raw.encode("utf-8")).hexdigest(),
        "source_adapter_formally_verified": False,
        "external_truth_certified": False,
        "scope": ("Exhaustive finite Python/Lean decision-gate correspondence. "
                  "Input extraction, declared provenance authenticity, real-world "
                  "truth and human thinking ranks are not established."),
    }


def file_record(path):
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
            "sha256": sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        build_command = [args.lake, "build", "exportRationalInquiry"]
        export_command = [args.lake, "env", "lean", "--run", "ExportRationalInquiry.lean"]
        subprocess.run(build_command, cwd=ROOT / "formal", check=True,
                       capture_output=True, text=True, timeout=300)
        result = subprocess.run(export_command, cwd=ROOT / "formal", check=True,
                                capture_output=True, text=True, timeout=90)
        report = check_export(result.stdout)
        report["provenance"] = {
            "toolchain": (ROOT / "formal/lean-toolchain").read_text().strip(),
            "build_command": build_command,
            "export_command": export_command,
            "files": [file_record(ROOT / name) for name in (
                "formal/lean-toolchain", "formal/Nabt/RationalInquiry.lean",
                "formal/ExportRationalInquiry.lean", "src/nabt/rational_inquiry.py",
                "tools/check_rational_inquiry.py",
            )],
        }
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
