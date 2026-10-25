#!/usr/bin/env python3
"""Package completed local verification outputs, then verify every ZIP member.

Run from a checkout after validation has finished. This does not certify Arabic
completeness and does not replace the Lean/runtime checks whose receipts it saves.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
ARCHIVE = BASE / "validation_bundle.zip"
MANIFEST = BASE / "validation_bundle_manifest.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert digest(ARCHIVE.read_bytes()) == manifest["archive_sha256"]
    expected = {row["path"]: row for row in manifest["files"]}
    assert len(expected) == len(manifest["files"])
    with zipfile.ZipFile(ARCHIVE) as archive:
        assert len(archive.namelist()) == len(set(archive.namelist()))
        assert set(archive.namelist()) == set(expected)
        for name, row in expected.items():
            assert not Path(name).is_absolute() and ".." not in Path(name).parts
            data = archive.read(name)
            assert len(data) == row["bytes"]
            assert digest(data) == row["sha256"]
    return {"valid": True, "files": len(expected),
            "archive_bytes": ARCHIVE.stat().st_size,
            "archive_sha256": manifest["archive_sha256"]}


def build() -> dict:
    receipt = json.loads((BASE / "validation/make-check.receipt.json").read_text())
    assert receipt["exit"] == 0, "Do not package an unfinished or failed gate"
    summary = json.loads((BASE / "validation/summary.json").read_text())
    assert summary["status"] == "local_full_gate_passed"
    paths = sorted(path for path in (BASE / "validation").rglob("*") if path.is_file())
    paths += [Path(__file__).resolve(), ROOT / "docs/ARABIC_COMPLETENESS_V6.md"]
    rows = []
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for path in paths:
            assert not path.is_symlink()
            data = path.read_bytes()
            name = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 25, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED,
                             compresslevel=9)
            rows.append({"path": name, "bytes": len(data), "sha256": digest(data)})
    manifest = {
        "schema": "nabt.classical-completion-validation-bundle.v1",
        "implementation_commit": summary["implementation_commit"],
        "runtime_freeze_sha256": summary["runtime_freeze_sha256"],
        "archive_sha256": digest(ARCHIVE.read_bytes()),
        "archive_bytes": ARCHIVE.stat().st_size,
        "file_count": len(rows),
        "scope": "Raw local validation outputs and Arabic report. Checkout of the pinned repository is required to rerun all gates; this is not a complete repository archive or a proof of all Arabic.",
        "remote_ci": summary["remote_ci"],
        "files": rows,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return verify()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify() if args.verify_only else build(), ensure_ascii=False))
