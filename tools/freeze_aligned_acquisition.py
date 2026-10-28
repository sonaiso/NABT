#!/usr/bin/env python3
"""Pin committed runtime inputs and this machine's native acquisition build.

The independent gold contents are never opened here. Its previously frozen
digest is copied from the evaluator. Outputs are created exclusively.
The evaluator owns first-run chronology checks; this content-pinned snapshot
also works after publication or squash merges replace local commit identities.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.evaluate_aligned_acquisition import (  # noqa: E402
    GOLD_SHA256, INFERENCE_SOURCE_PATH, SPEC_PATH, SPEC_SHA256,
    REQUIRED_NATIVE_PATHS, parse_json, required_freeze_paths,
)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True,
                          capture_output=True, timeout=60).stdout


def local_path(name: str) -> Path:
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT) or path.relative_to(ROOT).as_posix() != name:
        raise ValueError("noncanonical or escaping runtime path: " + name)
    return path


def build_freeze() -> dict:
    commit = git("rev-parse", "HEAD").decode().strip()
    tracked = set(git("ls-files", "-z").decode("utf-8").split("\0")) - {""}
    committed = set(git("ls-tree", "-r", "--name-only", "-z", commit).decode("utf-8").split("\0")) - {""}
    # Read the committed inference registry, not a possibly modified working copy.
    links = parse_json(git("show", commit + ":" + INFERENCE_SOURCE_PATH))
    paths = required_freeze_paths(tracked | committed, links)
    if not paths <= tracked:
        raise ValueError("runtime inputs must be tracked: " + ", ".join(sorted(paths - tracked)))
    files = {}
    for name in sorted(paths):
        current = local_path(name).read_bytes()
        committed = git("show", commit + ":" + name)
        if current != committed:
            raise ValueError("uncommitted runtime input: " + name)
        files[name] = digest(current)
    if files[SPEC_PATH] != SPEC_SHA256:
        raise ValueError("specification differs from the independent content pin")
    native = {}
    for relative in sorted(REQUIRED_NATIVE_PATHS):
        path = local_path(relative)
        if not path.is_file() or not os.access(path, os.X_OK):
            raise ValueError("build the required native executable: " + relative)
        native[relative] = digest(path.read_bytes())
    if git("rev-parse", "HEAD").decode().strip() != commit:
        raise ValueError("HEAD changed while freezing runtime inputs")
    # Detect changes during the snapshot; do not freeze a mixture of file states.
    if any(digest(local_path(name).read_bytes()) != value for name, value in {**files, **native}.items()):
        raise ValueError("runtime inputs changed while freezing")
    return {"schema": "nabt.aligned-acquisition-code-freeze.v1", "commit": commit,
            "spec_sha256": files[SPEC_PATH],
            "gold": {"path": "evidence/aligned_acquisition_v1/gold.json", "sha256": GOLD_SHA256},
            "files": files, "native": native}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = build_freeze()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(manifest, output, ensure_ascii=False, indent=2, allow_nan=False)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    print(json.dumps({"commit": manifest["commit"], "files": len(manifest["files"]),
                      "native": list(manifest["native"]), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
