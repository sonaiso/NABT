#!/usr/bin/env python3
"""Preserve post-base-merge receipts separately from the first observed bundle."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
ARCHIVE = BASE / "post_base_merge_bundle.zip"
MANIFEST = BASE / "post_base_merge_bundle_manifest.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify():
    manifest = json.loads(MANIFEST.read_text())
    if sha(ARCHIVE.read_bytes()) != manifest["archive_sha256"]:
        raise ValueError("Archive hash mismatch")
    rows = manifest["files"]
    expected = {row["path"]: row for row in rows}
    with zipfile.ZipFile(ARCHIVE) as archive:
        names = archive.namelist()
        if len(expected) != len(rows) or len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError("Duplicate or changed member inventory")
        for name, row in expected.items():
            if Path(name).is_absolute() or ".." in Path(name).parts:
                raise ValueError("Unsafe member path")
            data = archive.read(name)
            if len(data) != row["bytes"] or sha(data) != row["sha256"]:
                raise ValueError("Member bytes changed: " + name)
    return {"valid": True, "files": len(rows), "archive_bytes": ARCHIVE.stat().st_size,
            "archive_sha256": manifest["archive_sha256"]}


def build():
    if ARCHIVE.exists() or MANIFEST.exists():
        raise ValueError("Never replace an observed validation bundle")
    summary = json.loads((BASE / "validation/post_base_merge_summary.json").read_text())
    update = summary["post_base_merge"]
    if update["unit_tests"]["exit"] != 0 or update["oracle"]["regression_gate_pass"] is not True:
        raise ValueError("Post-merge validation did not pass")
    paths = sorted(p for p in (BASE / "validation/post_base_merge").rglob("*") if p.is_file())
    paths += [BASE / "validation/post_base_merge_summary.json", ROOT / "docs/ARABIC_COMPLETENESS_V6.md",
              Path(__file__).resolve()]
    rows = []
    with zipfile.ZipFile(ARCHIVE, "w") as archive:
        for path in paths:
            if path.is_symlink():
                raise ValueError("Symlink in validation outputs")
            data = path.read_bytes()
            name = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 25, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            rows.append({"path": name, "bytes": len(data), "sha256": sha(data)})
    manifest = {"schema": "nabt.v6.post-base-merge-bundle.v1",
                "archive_sha256": sha(ARCHIVE.read_bytes()), "file_count": len(rows),
                "prior_bundle_sha256": sha((BASE / "validation_bundle.zip").read_bytes()),
                "scope": "Supplement to the preserved original bundle after upstream validator hardening. Same runtime and formal sources; separate evaluator continuation and new observations.",
                "files": rows}
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return verify()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify() if args.verify_only else build(), ensure_ascii=False))
