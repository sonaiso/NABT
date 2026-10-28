#!/usr/bin/env python3
"""Freeze committed v2 inputs without interpreting independent matrix cases."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import evaluate_article_acquisition as evaluator  # noqa: E402


def build_freeze():
    guard = evaluator.load_bootstrap()
    commit = guard.git("rev-parse", "HEAD")
    tracked = set(guard.git("ls-files", "-z").split("\0")) - {""}
    committed = set(guard.git("ls-tree", "-r", "--name-only", "-z", commit).split("\0")) - {""}
    inference = guard.parse_json(guard.git("show", commit + ":" + guard.INFERENCE_SOURCE_PATH, binary=True))
    sources = guard.parse_json(guard.git("show", commit + ":" + evaluator.SOURCE_PATH, binary=True))
    paths = evaluator.required_freeze_paths(guard, tracked | committed, inference, sources)
    if not paths <= tracked:
        raise ValueError("runtime inputs must be tracked: " + ", ".join(sorted(paths - tracked)))
    files = {}
    for name in sorted(paths):
        raw = guard.local_path(name).read_bytes()
        if raw != guard.git("show", commit + ":" + name, binary=True):
            raise ValueError("uncommitted runtime input: " + name)
        files[name] = evaluator.digest(raw)
    for name, expected in {**evaluator.content_pins(), guard.SPEC_PATH: guard.SPEC_SHA256,
                           guard.GOLD_PATH.relative_to(guard.ROOT).as_posix(): guard.GOLD_SHA256,
                           evaluator.BOOTSTRAP_PATH: evaluator.BOOTSTRAP_SHA256}.items():
        if files.get(name) != expected:
            raise ValueError("independent content pin differs: " + name)
    native = {}
    if set(files) & evaluator.NATIVE_PATHS:
        raise ValueError("source and native freeze paths must not overlap")
    for name in sorted(evaluator.NATIVE_PATHS):
        path = guard.local_path(name)
        if not path.is_file() or not os.access(path, os.X_OK):
            raise ValueError("build the required native executable: " + name)
        native[name] = evaluator.digest(path.read_bytes())
    if guard.git("rev-parse", "HEAD") != commit or any(
            evaluator.digest(guard.local_path(name).read_bytes()) != value
            for hashes in (files, native) for name, value in hashes.items()):
        raise ValueError("runtime inputs changed while freezing")
    return {"schema": evaluator.SCHEMA,
        "bootstrap": {"path": evaluator.BOOTSTRAP_PATH, "sha256": evaluator.BOOTSTRAP_SHA256},
        "content_pins": evaluator.content_pins(), "matrix_commit": evaluator.MATRIX_COMMIT,
        "baseline": {"schema": "nabt.aligned-acquisition-code-freeze.v1", "commit": commit,
            "spec_sha256": guard.SPEC_SHA256,
            "gold": {"path": guard.GOLD_PATH.relative_to(guard.ROOT).as_posix(), "sha256": guard.GOLD_SHA256},
            "files": files, "native": native}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = build_freeze()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(manifest, output, ensure_ascii=False, indent=2, allow_nan=False)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    print(json.dumps({"commit": manifest["baseline"]["commit"], "files": len(manifest["baseline"]["files"]),
                      "native": sorted(manifest["baseline"]["native"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
