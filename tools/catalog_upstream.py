#!/usr/bin/env python3
"""Inventory theorem declarations at pinned local snapshots; never import trust.

The input is an explicit JSON list of {repository, commit, path}. Paths are
read only. Declaration extraction is a source inventory, not a Lean build or
an assertion that upstream assumptions hold. No upstream checkout is required
to install or run NABT; this optional tool only refreshes research provenance.
"""

import argparse
import json
import re
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

from check_integrity import lean_code_without_comments_or_strings


def catalog(snapshots):
    repositories = []
    total = 0
    pattern = re.compile(
        r"^[ \t]*(?:@\[[^\]\n]*\][ \t]*)*(?:(?:private|protected|noncomputable)\s+)*(?:theorem|lemma)\s+([^\s:({\[]+)",
        re.MULTILINE,
    )
    for item in snapshots:
        root = Path(item["path"])
        head = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip()
        if head != item["commit"]:
            raise ValueError(f"Snapshot differs from pin: {item['repository']}")
        files = subprocess.run(
            ["rg", "--files", "-g", "*.lean"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if files.returncode not in (0, 1):
            raise ValueError("Cannot enumerate snapshot")
        entries = []
        for relative in sorted(files.stdout.splitlines()):
            if any(
                part in {".lake", "vendor", "node_modules"}
                for part in Path(relative).parts
            ):
                continue
            raw = (root / relative).read_bytes()
            code = lean_code_without_comments_or_strings(raw.decode("utf-8", "strict"))
            declarations = [
                {
                    "name_as_written": m.group(1),
                    "line": code.count("\n", 0, m.start(1)) + 1,
                }
                for m in pattern.finditer(code)
            ]
            if declarations:
                entries.append(
                    {
                        "path": relative,
                        "file_sha256": sha256(raw).hexdigest(),
                        "declarations": declarations,
                        "source_url": f"https://github.com/{item['repository']}/blob/{head}/{relative}",
                    }
                )
        count = sum(len(x["declarations"]) for x in entries)
        total += count
        repositories.append(
            {
                "repository": item["repository"],
                "commit": head,
                "declaration_count": count,
                "files": entries,
                "status": "SOURCE_INVENTORY_NOT_KERNEL_VERIFICATION",
            }
        )
    return {
        "schema": "nabt.upstream-theorem-inventory.v1",
        "declaration_count": total,
        "repository_count": len(repositories),
        "repositories": repositories,
        "runtime_authority": False,
        "scope": "Named theorem/lemma declarations after stripping comments and strings; not full Lean syntax coverage or compilation",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot_map", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = catalog(json.loads(args.snapshot_map.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                k: report[k]
                for k in ("repository_count", "declaration_count", "runtime_authority")
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
