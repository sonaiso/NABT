"""Fail-closed pins and write boundaries for published evaluation replay.

The artifact pin belongs to the published v0.4 experiment. A new runtime
snapshot is allowed explicitly; it never changes the identity of its gold or
turns a public regression run into a new held-out experiment.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re


ROOT = Path(__file__).resolve().parents[2]
PUBLISHED = ROOT / "evidence/text_inquiry"
ARTIFACT_MANIFEST_SHA256 = "6d64e66f0f197d8c6bf4399724b74a4203ac56a52a37528d97d66723f38ea9b9"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _relative_file(root: Path, name: object) -> Path:
    if type(name) is not str or not name or "\\" in name:
        raise ValueError("Invalid manifest path")
    parts = PurePosixPath(name)
    if parts.is_absolute() or parts.as_posix() != name or any(p in {".", ".."} for p in parts.parts):
        raise ValueError("Manifest paths must be canonical relative paths")
    path = root / name
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Manifest path is absent or escapes its root: " + name)
    return path


def authoritative_paths(root: Path = ROOT) -> set[str]:
    """The explicit runtime selection used by snapshot.py, independently checked."""
    paths = {root / "pyproject.toml"}
    for path in (root / "src").rglob("*"):
        if (path.is_file() and path.suffix in {".py", ".json", ".txt"}
                and not any(part.endswith((".egg-info", ".dist-info"))
                            for part in path.relative_to(root).parts[:-1])):
            paths.add(path)
    return {path.relative_to(root).as_posix() for path in paths}


def evaluator_identity() -> list[dict]:
    """Record helper changes as well as the entrypoint's own checksum."""
    paths = sorted((ROOT / "tools/text_evaluation").glob("*.py"))
    paths.append(ROOT / "tools/text_inquiry_evaluation.py")
    return [{"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path)} for path in paths]


def verify_published_inputs(data: Path = PUBLISHED) -> dict:
    data = data.resolve()
    manifest_path = data / "artifact_manifest.json"
    if digest(manifest_path) != ARTIFACT_MANIFEST_SHA256:
        raise ValueError("Published artifact manifest checksum differs")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        path = _relative_file(data, entry["path"])
        if path.stat().st_size != entry["bytes"] or digest(path) != entry["sha256"]:
            raise ValueError("Published frozen artifact differs: " + entry["path"])
    return {"artifact_manifest_sha256": ARTIFACT_MANIFEST_SHA256,
            "artifacts_checked": len(manifest["files"])}


def verify_code_freeze(path: Path, root: Path = ROOT) -> dict:
    freeze = json.loads(path.read_text(encoding="utf-8"))
    files = freeze.get("files")
    if type(files) is not list or not files:
        raise ValueError("A runtime freeze must contain a nonempty complete file inventory")
    seen = set()
    for entry in files:
        if type(entry) is not dict or set(entry) != {"path", "sha256", "bytes"}:
            raise ValueError("Malformed runtime freeze file record")
        name = entry["path"]
        item = _relative_file(root, name)
        if name in seen:
            raise ValueError("Duplicate runtime freeze path: " + name)
        seen.add(name)
        if (type(entry["bytes"]) is not int or entry["bytes"] < 0
                or type(entry["sha256"]) is not str
                or re.fullmatch("[0-9a-f]{64}", entry["sha256"]) is None):
            raise ValueError("Malformed runtime freeze length or checksum")
        if item.stat().st_size != entry["bytes"] or digest(item) != entry["sha256"]:
            raise ValueError("Implementation differs from code freeze: " + name)
    if seen != authoritative_paths(root):
        raise ValueError("Runtime freeze does not cover exactly the authoritative source/configuration/data inventory")
    if freeze.get("snapshot_sha256") != _canonical_hash(files):
        raise ValueError("Runtime snapshot checksum differs from its file inventory")
    return freeze


def require_output(path: Path, *, data: Path = PUBLISHED, freeze: Path | None = None) -> Path:
    """Reject overwrite and any destination within an input/history tree."""
    target = path.resolve()
    if any(target == tree.resolve() or target.is_relative_to(tree.resolve())
           for tree in (PUBLISHED, data)):
        raise ValueError("Evaluation output cannot be inside published history or frozen input data")
    if freeze is not None and target == freeze.resolve():
        raise ValueError("Evaluation output cannot overwrite its runtime freeze")
    if path.exists() or path.is_symlink():
        raise ValueError("Evaluation output already exists; choose a new output location")
    return target


def prepare_output_directory(path: Path, *, data: Path, freeze: Path) -> Path:
    target = path.resolve()
    if any(target == tree.resolve() or target.is_relative_to(tree.resolve())
           for tree in (PUBLISHED, data)):
        raise ValueError("Evaluation output cannot be inside published history or frozen input data")
    if freeze.resolve().is_relative_to(target):
        raise ValueError("Evaluation output directory contains its runtime freeze")
    if path.is_symlink() or (path.exists() and (not path.is_dir() or any(path.iterdir()))):
        raise ValueError("Use a new or empty output directory; existing reports are never overwritten")
    target.mkdir(parents=True, exist_ok=True)
    return target


def write_report(path: Path, report: object, *, data: Path = PUBLISHED,
                 freeze: Path | None = None) -> None:
    target = require_output(path, data=data, freeze=freeze)
    with target.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
