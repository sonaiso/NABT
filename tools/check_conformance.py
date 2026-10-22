#!/usr/bin/env python3
"""Build the Lean kernel, export its law, and compare the whole runtime table."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from check_integrity import ROOT, check


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        # Explicit targets prevent an executable-only default from omitting proofs.
        subprocess.run([args.lake, "build", "Nabt", "exportTable"], cwd=ROOT / "formal", check=True)
        result = subprocess.run([args.lake, "exe", "exportTable"], cwd=ROOT / "formal",
                                check=True, capture_output=True)
        with tempfile.TemporaryDirectory(prefix="nabt-conformance-") as tmp:
            path = Path(tmp) / "law.json"
            path.write_bytes(result.stdout)
            report = check(path)
        report["kernel_build_checked"] = True
        report["scope"] = "Lean kernel build and complete table conformance; not a full Python refinement proof"
        content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding="utf-8")
        print(content, end="")
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
