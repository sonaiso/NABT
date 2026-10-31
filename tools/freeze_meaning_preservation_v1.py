#!/usr/bin/env python3
"""Freeze committed meaning-preservation code, evidence and built binaries before evaluation."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import evaluate_meaning_preservation_v1 as evaluator  # noqa: E402


def build_freeze():
    guard = evaluator.load_bootstrap()
    commit = guard.git("rev-parse", "HEAD")
    tracked = set(guard.git("ls-files", "-z").split("\0")) - {""}
    committed = set(guard.git("ls-tree", "-r", "--name-only", "-z", commit).split("\0")) - {""}
    inference = guard.parse_json(guard.git("show", commit + ":" + guard.INFERENCE_SOURCE_PATH, binary=True))
    required = evaluator.required_paths(guard, tracked | committed, inference, evaluator.packets_at(guard, commit))
    if not required <= tracked:
        raise ValueError("required runtime input not tracked: " + ", ".join(sorted(required - tracked)))
    files = {}
    for name in sorted(required):
        raw = guard.local_path(name).read_bytes()
        if raw != guard.git("show", commit + ":" + name, binary=True):
            raise ValueError("runtime input differs from committed freeze: " + name)
        files[name] = evaluator.digest(raw)
    for name, value in {**evaluator.PINS, evaluator.BOOTSTRAP_PATH: evaluator.BOOTSTRAP_SHA256,
                       guard.SPEC_PATH: guard.SPEC_SHA256,
                       guard.GOLD_PATH.relative_to(ROOT).as_posix(): guard.GOLD_SHA256}.items():
        if files.get(name) != value:
            raise ValueError("code-owned content pin differs: " + name)
    if set(files) & evaluator.NATIVE_PATHS:
        raise ValueError("source and native inventories overlap")
    native = {}
    for name in sorted(evaluator.NATIVE_PATHS):
        path = guard.local_path(name)
        if not path.is_file() or not os.access(path, os.X_OK):
            raise ValueError("required native executable unavailable: " + name)
        native[name] = evaluator.digest(path.read_bytes())
    if guard.git("rev-parse", "HEAD") != commit or any(
            evaluator.digest(guard.local_path(name).read_bytes()) != value
            for hashes in (files, native) for name, value in hashes.items()):
        raise ValueError("runtime inputs changed while freezing")
    return {"schema": evaluator.SCHEMA, "evaluator_id": evaluator.EVALUATOR_ID,
        "source_commit": evaluator.SOURCE_COMMIT,
        "matrix_commit": evaluator.MATRIX_COMMIT, "content_pins": evaluator.PINS,
        "bootstrap": {"path": evaluator.BOOTSTRAP_PATH, "sha256": evaluator.BOOTSTRAP_SHA256},
        "baseline": {"schema": "nabt.aligned-acquisition-code-freeze.v1", "commit": commit,
            "spec_sha256": guard.SPEC_SHA256,
            "gold": {"path": guard.GOLD_PATH.relative_to(ROOT).as_posix(), "sha256": guard.GOLD_SHA256},
            "files": files, "native": native}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    document = build_freeze()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps({"commit": document["baseline"]["commit"], "files": len(document["baseline"]["files"]),
                      "native": sorted(document["baseline"]["native"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
