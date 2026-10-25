#!/usr/bin/env python3
"""Compare the complete Lean shape export and replay the installed source law."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--lean-export", type=Path)
    args = parser.parse_args()
    if args.lean_export:
        exported = json.loads(args.lean_export.read_bytes())
    else:
        subprocess.run([args.lake, "build", "exportProductiveForms"], cwd=ROOT / "formal", check=True)
        exported = json.loads(subprocess.check_output([str(ROOT / "formal/.lake/build/bin/exportProductiveForms")]))
    from nabt.productive_forms import installed_shapes, replay_policy
    if exported != installed_shapes():
        raise ValueError("Installed table differs from complete fresh Lean export")
    # Independently transcribed three-row ibtida contract; no runtime helper decides the oracle.
    expected = [("َ", "ِ", "ْ"), ("ِ", "ِ", "ْ"), ("ُ", "ُ", "ْ")]
    if [(r["medial"], r["initial"], r["final"]) for r in exported["imperative"]] != expected:
        raise ValueError("Lean export differs from independently stated vowel contract")
    print(json.dumps({"valid": True, "vowel_rows": 3, "source_passages": len(replay_policy()["passages"]),
                      "scope": "Conditional shape correspondence; not Arabic-language completeness"}))


if __name__ == "__main__":
    main()
