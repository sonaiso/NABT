"""Freeze source-acquisition registration without rewriting earlier evidence.

This command only records bytes. It does not execute language cases, produce
new expected answers, or waive any historical failure. Run once after the
implementation and discovery registration are final.
"""
from datetime import datetime, timezone
from hashlib import sha256
import difflib
import gzip
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PREVIOUS = ROOT / "evidence/progressive_rule_audit_v1"
PREVIOUS_MANIFEST_SHA = "b184a00c3c19b3204b889f14567b042c987046e7698f657bf9586ff307f01cf5"
PREVIOUS_ARCHIVE_SHA = "8646f73fef57bd97428cc3686843a0f3c9e12f2cf850342c6462e507c232c8e9"
PREVIOUS_POLICY_SHA = "4f1660cbba2b513f134f0677e5b48a04d57139b32b9a475b280bd4417a35664f"
ALLOWED_CHANGED = {"src/nabt/data/framework_foundation.json"}
ALLOWED_ADDED = set()
sys.path.insert(0, str(ROOT))
from tools.text_evaluation.integrity import authoritative_paths


def digest(raw):
    return sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def write_new(path, data):
    with path.open("xb") as stream:
        stream.write(data)


def main():
    names = ["code_freeze_v1.json", "code_freeze_v1.tar.gz", "regression_policy_v1.json",
             "runtime_migration.json", "runtime_migration.patch"]
    if any((HERE / name).exists() for name in names):
        raise ValueError("Never overwrite an observed freeze; create a new explicit revision")
    old_bytes = (PREVIOUS / names[0]).read_bytes()
    old_archive = (PREVIOUS / names[1]).read_bytes()
    old_policy_bytes = (PREVIOUS / names[2]).read_bytes()
    if tuple(map(digest, (old_bytes, old_archive, old_policy_bytes))) != (
            PREVIOUS_MANIFEST_SHA, PREVIOUS_ARCHIVE_SHA, PREVIOUS_POLICY_SHA):
        raise ValueError("Historical manifest/archive/policy bytes changed")
    old = json.loads(old_bytes)
    previous_rows = {row["path"]: row for row in old["files"]}
    paths = sorted(authoritative_paths(ROOT))
    rows = [{"path": name, "sha256": digest((ROOT / name).read_bytes()),
             "bytes": (ROOT / name).stat().st_size} for name in paths]
    changed = [row["path"] for row in rows if row["path"] in previous_rows
               and row != previous_rows[row["path"]]]
    added = set(paths) - set(previous_rows)
    removed = set(previous_rows) - set(paths)
    if removed or added != ALLOWED_ADDED or set(changed) != ALLOWED_CHANGED:
        raise ValueError("Only the source-acquisition discovery registration may change")
    archive_buffer = io.BytesIO()
    with tarfile.open(fileobj=archive_buffer, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for row in rows:
            path = ROOT / row["path"]
            if not path.resolve().is_relative_to(ROOT):
                raise ValueError("Runtime path escapes the repository")
            raw = path.read_bytes()
            if len(raw) != row["bytes"] or digest(raw) != row["sha256"]:
                raise ValueError("Runtime changed during archival: " + row["path"])
            info = tarfile.TarInfo(row["path"])
            info.size, info.mode, info.mtime = len(raw), 0o644, 0
            archive.addfile(info, io.BytesIO(raw))
    archive_bytes = gzip.compress(archive_buffer.getvalue(), mtime=0)
    manifest = {key: value for key, value in old.items()
                if key not in {"files", "snapshot_sha256", "archive_sha256"}}
    scope = ("Register the native source-row acquisition, qualified cue licensing and authority routing surfaces. "
             "Every packaged implementation/data file is unchanged except the discovery registry. "
             "No historical case, question, scorer, gold, denominator, threshold or residual signature changes. "
             "Acquisition tools, Lean and routing have separate execution identities; "
             "registration does not establish semantic completeness or transmission certainty.")
    manifest.update(
        utc=datetime.now(timezone.utc).isoformat(),
        repository_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        repository_status=subprocess.check_output(
            ["git", "status", "--short", "--", *sorted(set(changed) | added)],
            cwd=ROOT, text=True).strip(),
        previous_runtime_manifest_sha256=PREVIOUS_MANIFEST_SHA, change_scope=scope,
        changed_runtime_paths=sorted(changed), added_runtime_paths=sorted(added),
        removed_runtime_paths=[], files=rows,
        snapshot_sha256=digest(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()),
        archive_filename=names[1], archive_sha256=digest(archive_bytes))
    manifest_bytes = encode(manifest)
    policy = json.loads(old_policy_bytes)
    policy.update(previous_policy_sha256=PREVIOUS_POLICY_SHA,
                  runtime_freeze_sha256=digest(manifest_bytes),
                  runtime_snapshot_sha256=manifest["snapshot_sha256"],
                  runtime_file_count=len(rows), scope=scope)
    policy_bytes = encode(policy)
    patches = []
    with tarfile.open(fileobj=io.BytesIO(old_archive), mode="r:gz") as archive:
        for name in sorted(set(changed) | added):
            before = archive.extractfile(name).read().decode() if name in previous_rows else ""
            patches.extend(difflib.unified_diff(before.splitlines(keepends=True),
                (ROOT / name).read_text().splitlines(keepends=True),
                fromfile="previous/" + name, tofile="current/" + name, n=0))
    patch = "".join(patches).encode()
    migration = {"schema": "nabt.source-acquisition.runtime-migration.v1",
        "previous_manifest": str((PREVIOUS / names[0]).relative_to(ROOT)),
        "previous_manifest_sha256": PREVIOUS_MANIFEST_SHA,
        "previous_archive_sha256": PREVIOUS_ARCHIVE_SHA,
        "previous_policy_sha256": PREVIOUS_POLICY_SHA,
        "current_manifest": str((HERE / names[0]).relative_to(ROOT)),
        "current_manifest_sha256": digest(manifest_bytes),
        "current_archive_sha256": digest(archive_bytes),
        "current_policy_sha256": digest(policy_bytes),
        "runtime_file_count": len(rows), "changed_runtime_paths": sorted(changed),
        "added_runtime_paths": sorted(added), "removed_runtime_paths": [],
        "historical_material_changed": False, "historical_thresholds_changed": False,
        "runtime_calls_performed_by_migration": False,
        "patch_path": str((HERE / names[4]).relative_to(ROOT)), "patch_sha256": digest(patch),
        "scope": scope}
    for name, raw in zip(names, (manifest_bytes, archive_bytes, policy_bytes, encode(migration), patch)):
        write_new(HERE / name, raw)
    print(json.dumps(migration, ensure_ascii=False))


if __name__ == "__main__":
    main()
