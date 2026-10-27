#!/usr/bin/env python3
"""Losslessly preserve repeated verification files; this grants no proof authority.

Gzip headers are stored separately from their original compressed body. No
decompression/recompression is needed to restore the exact original bytes.
Published archives are inputs only; output directories must not already exist.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

_SCHEMA = "nabt.verification-byte-bundle.v1"
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_LIMIT = 1024 * 1024 * 1024


def _digest(raw):
    return sha256(raw).hexdigest()


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _path(name):
    _require(type(name) is str and bool(name) and name not in (".", ".."),
             "Nonempty relative path required")
    path = PurePosixPath(name)
    _require(not path.is_absolute() and path.as_posix() == name
             and all(part not in ("", ".", "..") for part in path.parts)
             and "\\" not in name and "\0" not in name, "Unsafe path")
    return path


def _parts(raw):
    """Split a recognizable gzip header; all other bytes stay one opaque object."""
    if len(raw) < 18 or raw[:3] != b"\x1f\x8b\x08" or raw[3] & 0xe0:
        return [raw]
    flags, offset = raw[3], 10
    if flags & 4:
        if offset + 2 > len(raw):
            return [raw]
        offset += 2 + int.from_bytes(raw[offset:offset + 2], "little")
    for flag in (8, 16):
        if flags & flag:
            end = raw.find(b"\0", offset)
            if end < 0:
                return [raw]
            offset = end + 1
    if flags & 2:
        offset += 2
    return [raw[:offset], raw[offset:]] if offset < len(raw) - 8 else [raw]


def _inventory(root):
    files = []
    for path in root.rglob("*"):
        _require(not path.is_symlink(), "Symlinks cannot enter a byte bundle")
        if path.is_file():
            files.append(path)
        else:
            _require(path.is_dir(), "Only regular files can enter a byte bundle")
    return sorted(files)


def _pack(source, output):
    source = source.resolve(strict=True)
    _require(source.is_dir(), "Source must be a directory")
    _require(not output.exists() and not output.is_symlink(), "Output must be new")
    _require(not output.resolve().is_relative_to(source), "Bundle must be outside its input")
    objects, rows = {}, []
    files = _inventory(source)
    _require(sum(path.stat().st_size for path in files) <= _LIMIT, "Bundle byte limit exceeded")
    for path in files:
        raw = path.read_bytes()
        parts = _parts(raw)
        segments = []
        for part in parts:
            digest = _digest(part)
            _require(digest not in objects or objects[digest] == part, "Object hash collision")
            objects[digest] = part
            segments.append(digest)
        name = str(path.relative_to(source))
        _path(name)
        rows.append({"path": name, "bytes": len(raw), "sha256": _digest(raw),
                     "segments": segments})
    _require(_inventory(source) == files, "Input inventory changed during capture")
    for row in rows:
        raw = (source / row["path"]).read_bytes()
        _require(len(raw) == row["bytes"] and _digest(raw) == row["sha256"],
                 "Input changed during capture")
    output.mkdir(parents=True)
    archive = output / "objects.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as saved:
        for digest, raw in sorted(objects.items()):
            info = zipfile.ZipInfo("objects/" + digest)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            saved.writestr(info, raw)
    manifest = {"schema": _SCHEMA, "authority": "byte-preservation-only",
                "archive": {"path": archive.name, "sha256": _digest(archive.read_bytes()),
                            "bytes": archive.stat().st_size},
                "objects": {digest: len(raw) for digest, raw in sorted(objects.items())},
                "files": rows}
    with (output / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return manifest


def _restore(bundle, output):
    _require(not output.exists() and not output.is_symlink(), "Restore output must be new")

    def unique(pairs):
        obj = {}
        for key, value in pairs:
            _require(key not in obj, "Duplicate manifest field")
            obj[key] = value
        return obj

    manifest = json.loads((bundle / "manifest.json").read_bytes(), object_pairs_hook=unique)
    _require(set(manifest) == {"schema", "authority", "archive", "objects", "files"}
             and manifest["schema"] == _SCHEMA
             and manifest["authority"] == "byte-preservation-only", "Unsupported bundle")
    archive = manifest["archive"]
    _require(type(archive) is dict and set(archive) == {"path", "sha256", "bytes"}
             and archive["path"] == "objects.zip" and type(archive["bytes"]) is int
             and 0 <= archive["bytes"] <= _LIMIT, "Invalid archive descriptor")
    raw = (bundle / "objects.zip").read_bytes()
    _require(len(raw) == archive["bytes"] and _digest(raw) == archive["sha256"], "Archive changed")
    objects, files = manifest["objects"], manifest["files"]
    _require(type(objects) is dict and all(type(k) is str and _HASH.fullmatch(k)
             and type(n) is int and 0 <= n <= _LIMIT for k, n in objects.items()), "Invalid object inventory")
    _require(sum(objects.values()) <= _LIMIT and type(files) is list, "Object byte limit exceeded")
    names, used, total = set(), set(), 0
    for row in files:
        _require(type(row) is dict and set(row) == {"path", "bytes", "sha256", "segments"}, "Invalid file row")
        path = _path(row["path"])
        _require(row["path"] not in names and type(row["bytes"]) is int and 0 <= row["bytes"] <= _LIMIT
                 and type(row["sha256"]) is str and _HASH.fullmatch(row["sha256"]), "Invalid file identity")
        _require(type(row["segments"]) is list and 1 <= len(row["segments"]) <= 2
                 and all(type(k) is str and k in objects for k in row["segments"]), "Invalid file segments")
        _require(sum(objects[k] for k in row["segments"]) == row["bytes"], "File size mismatch")
        names.add(path.as_posix())
        used.update(row["segments"])
        total += row["bytes"]
    _require(total <= _LIMIT and used == set(objects), "Incomplete object inventory or byte limit")
    _require(all(parent.as_posix() not in names for name in names
                 for parent in PurePosixPath(name).parents if parent.as_posix() != "."), "Conflicting file paths")
    payloads = {}
    with zipfile.ZipFile(bundle / "objects.zip") as saved:
        members = saved.infolist()
        _require(len(members) == len(objects) and {m.filename for m in members}
                 == {"objects/" + k for k in objects}, "Archive object inventory changed")
        for member in members:
            key = member.filename.removeprefix("objects/")
            _require(member.file_size == objects[key] and not member.is_dir(), "Object size changed")
            payload = saved.read(member)
            _require(_digest(payload) == key, "Object bytes changed")
            payloads[key] = payload
    restored = []
    for row in files:
        payload = b"".join(payloads[key] for key in row["segments"])
        _require(_digest(payload) == row["sha256"], "Restored file bytes differ")
        restored.append((row["path"], payload))
    output.mkdir(parents=True)
    for name, payload in restored:
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(payload)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("pack", "restore"))
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest = (_pack if args.operation == "pack" else _restore)(args.input, args.output)
    print(json.dumps({"schema": _SCHEMA, "operation": args.operation,
                      "files": len(manifest["files"]), "objects": len(manifest["objects"]),
                      "source_bytes": sum(row["bytes"] for row in manifest["files"]),
                      "object_bytes": sum(manifest["objects"].values()),
                      "authority": "byte-preservation-only"}))


if __name__ == "__main__":
    main()
