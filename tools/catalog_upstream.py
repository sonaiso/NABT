#!/usr/bin/env python3
"""Inventory theorem declarations at pinned local snapshots; never import trust.

The input is an explicit JSON list of {repository, commit, path}. Each commit
must be a full object ID; only its committed regular-file blobs are read,
independently of HEAD, the checkout, the index and local replacement refs.
Declaration extraction is a source inventory, not a Lean build or
an assertion that upstream assumptions hold. No upstream checkout is required
to install or run NABT; this optional tool only refreshes research provenance.
"""

import argparse
import json
import re
import subprocess
import sys
from hashlib import new as new_hash, sha256
from pathlib import Path
from urllib.parse import quote

from check_integrity import lean_code_without_comments_or_strings


def _verified_object(git, kind, object_id):
    """Check the actual Git header and payload, not only the database key."""
    try:
        raw = subprocess.check_output(
            [*git, "cat-file", kind, object_id], stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as error:
        raise ValueError(f"Cannot verify Git object identity: {kind} {object_id}") from error
    algorithm = "sha1" if len(object_id) == 40 else "sha256"
    header = kind.encode("ascii") + b" " + str(len(raw)).encode("ascii") + b"\0"
    if new_hash(algorithm, header + raw).hexdigest() != object_id:
        raise ValueError(f"Git object identity mismatch: {kind} {object_id}")
    return raw


def _committed_lean_files(git, pin):
    """Follow only entries parsed from identity-checked commit/tree payloads."""
    commit = _verified_object(git, "commit", pin)
    first_line = commit.split(b"\n", 1)[0]
    oid_length = len(pin)
    if re.fullmatch(rb"tree [0-9a-f]{" + str(oid_length).encode() + rb"}", first_line) is None:
        raise ValueError("Pinned commit must declare its complete root tree identity")
    pending = [(b"", first_line[5:].decode("ascii"))]
    files = []
    while pending:
        prefix, tree_id = pending.pop()
        tree = _verified_object(git, "tree", tree_id)
        offset = 0
        seen_names = set()
        while offset < len(tree):
            separator = tree.find(b" ", offset)
            terminator = tree.find(b"\0", separator + 1)
            end = terminator + 1 + oid_length // 2
            if separator < offset or terminator < separator or end > len(tree):
                raise ValueError("Malformed committed tree entry")
            mode = tree[offset:separator]
            name = tree[separator + 1:terminator]
            object_id = tree[terminator + 1:end].hex()
            offset = end
            if not name or name in {b".", b".."} or b"/" in name:
                raise ValueError("Committed source path must be a canonical relative path")
            if name in seen_names:
                raise ValueError("Committed tree has duplicate source names")
            seen_names.add(name)
            if mode not in {b"40000", b"100644", b"100755", b"120000", b"160000"}:
                raise ValueError("Unsupported committed tree mode")
            if name in {b".lake", b"vendor", b"node_modules"}:
                continue
            relative = prefix + name
            if mode == b"40000":
                pending.append((relative + b"/", object_id))
            elif mode in {b"100644", b"100755"} and name.endswith(b".lean"):
                files.append((relative.decode("utf-8", "strict"), object_id))
    return files


def catalog(snapshots):
    repositories = []
    total = 0
    pattern = re.compile(
        r"^[ \t]*(?:@\[[^\]\n]*\][ \t]*)*(?:(?:private|protected|noncomputable)\s+)*(?:theorem|lemma)\s+([^\s:({\[]+)",
        re.MULTILINE,
    )
    for item in snapshots:
        repository = item["repository"]
        pin = item["commit"]
        if (not isinstance(repository, str)
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9_.-]+", repository) is None
                or repository.split("/")[-1] in {".", ".."}):
            raise ValueError("Repository must be an unambiguous owner/name GitHub path")
        if not isinstance(pin, str) or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", pin) is None:
            raise ValueError("Snapshot pin must be a complete lowercase commit object ID")
        root = Path(item["path"])
        # git replace can redirect both commits and blobs without changing
        # their reported IDs. Disable replacements for every object read.
        git = ["git", "--no-replace-objects", "-C", str(root)]
        entries = []
        for relative, object_id in sorted(_committed_lean_files(git, pin)):
            raw = _verified_object(git, "blob", object_id)
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
                        "source_url": f"https://github.com/{repository}/blob/{pin}/{quote(relative, safe='/')}",
                    }
                )
        count = sum(len(x["declarations"]) for x in entries)
        total += count
        repositories.append(
            {
                "repository": repository,
                "commit": pin,
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
