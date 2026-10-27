"""Create an immutable runtime-identity migration, without executing language cases.

The package remains the same 101-file domain. The tools-based lexical reader,
source review and new native admission are measured by their own execution
identities; this migration only registers their shared-foundation boundary.
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
PREVIOUS = ROOT / "evidence/attested_mark_recovery_v1"
PREVIOUS_MANIFEST_SHA = "1c47bfee3fa0baa190ec0e0455dfcb2528aec65a6280694956c1e00186948d30"
PREVIOUS_ARCHIVE_SHA = "d04ff4bf22171441e5731bfdb67dd4b4d6e6470db0e75b58977656d42e5172c2"
PREVIOUS_POLICY_SHA = "784ba72cb7738d3639a267e82da0b510fbf1f7f284271b26eac3ffe66c26dad9"
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
    changed = [row["path"] for row in rows if row != previous_rows.get(row["path"])]
    if set(paths) != set(previous_rows) or changed != ["src/nabt/data/framework_foundation.json"]:
        raise ValueError("Migration is limited to discovery; unexpected package source change")
    archive_buffer = io.BytesIO()
    with tarfile.open(fileobj=archive_buffer, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for row in rows:
            raw = (ROOT / row["path"]).read_bytes()
            info = tarfile.TarInfo(row["path"])
            info.size, info.mode, info.mtime = len(raw), 0o644, 0
            archive.addfile(info, io.BytesIO(raw))
    archive_bytes = gzip.compress(archive_buffer.getvalue(), mtime=0)
    manifest = {key: value for key, value in old.items()
                if key not in {"files", "snapshot_sha256", "archive_sha256"}}
    manifest.update(
        utc=datetime.now(timezone.utc).isoformat(),
        repository_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        repository_status=" M src/nabt/data/framework_foundation.json",
        previous_runtime_manifest_sha256=PREVIOUS_MANIFEST_SHA,
        change_scope="Administrative discovery registration for native A116 lexical certification and source-reviewed natural-use acquisition. Exactly one of the same 101 packaged files changes. Lexical tools and Lean changes have separate execution identities. No historical cases, gold, scorers, denominators or thresholds change.",
        changed_runtime_paths=changed,
        files=rows,
        snapshot_sha256=digest(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()),
        archive_filename=names[1], archive_sha256=digest(archive_bytes))
    manifest_bytes = encode(manifest)
    policy = json.loads(old_policy_bytes)
    policy.update(previous_policy_sha256=PREVIOUS_POLICY_SHA,
                  runtime_freeze_sha256=digest(manifest_bytes),
                  runtime_snapshot_sha256=manifest["snapshot_sha256"],
                  runtime_file_count=len(rows),
                  scope="Discovery registration only for the unchanged packaged linguistic runtime. All historical cases, questions, gold, checks, thresholds and residual signatures are retained. New lexical evidence is evaluated separately.")
    policy_bytes = encode(policy)
    name = changed[0]
    with tarfile.open(fileobj=io.BytesIO(old_archive), mode="r:gz") as archive:
        old_registry = archive.extractfile(name).read().decode()
    patch = "".join(difflib.unified_diff(old_registry.splitlines(keepends=True),
        (ROOT / name).read_text().splitlines(keepends=True), fromfile="previous/" + name,
        tofile="current/" + name, n=0)).encode()
    migration = {"schema": "nabt.certified-natural-use.runtime-migration.v1",
        "previous_manifest": str((PREVIOUS / names[0]).relative_to(ROOT)),
        "previous_manifest_sha256": PREVIOUS_MANIFEST_SHA,
        "previous_archive_sha256": PREVIOUS_ARCHIVE_SHA,
        "previous_policy_sha256": PREVIOUS_POLICY_SHA,
        "current_manifest": str((HERE / names[0]).relative_to(ROOT)),
        "current_manifest_sha256": digest(manifest_bytes),
        "current_archive_sha256": digest(archive_bytes),
        "current_policy_sha256": digest(policy_bytes),
        "runtime_file_count": len(rows), "changed_runtime_paths": changed,
        "historical_material_changed": False, "historical_thresholds_changed": False,
        "runtime_calls_performed_by_migration": False,
        "patch_path": str((HERE / names[4]).relative_to(ROOT)), "patch_sha256": digest(patch),
        "scope": manifest["change_scope"]}
    for name, raw in zip(names, (manifest_bytes, archive_bytes, policy_bytes, encode(migration), patch)):
        write_new(HERE / name, raw)
    print(json.dumps(migration, ensure_ascii=False))


if __name__ == "__main__":
    main()
