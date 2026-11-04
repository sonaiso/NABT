"""Append-only events plus atomically replaced current state, never a proof."""
from __future__ import annotations

import json
import os
from pathlib import Path
import time

from .policy import canonical, digest, require


def write_json(path, value):
    path.write_bytes(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode() + b"\n")


def create_directory(root, destination):
    destination = Path(destination).absolute()
    allowed = root / "artifacts/local/repo-agent"
    require(".." not in destination.parts and destination.is_relative_to(allowed) and destination != allowed,
            "INVALID_INPUT", "run directories must be new children of artifacts/local/repo-agent")
    current = root
    for part in destination.relative_to(root).parts:
        current = current / part
        require(not current.is_symlink(), "PROTECTED_PATH", "state path cannot contain symlinks")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(exist_ok=False)
    return destination


class Journal:
    def __init__(self, directory, report):
        self.directory, self.report, self.previous, self.sequence = directory, report, None, 0

    def event(self, kind, **data):
        value = {"sequence": self.sequence, "previous": self.previous,
                 "time_ns": time.time_ns(), "kind": kind, "data": data}
        value["sha256"] = digest(canonical(value))
        with (self.directory / "events.jsonl").open("ab") as handle:
            handle.write(canonical(value) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.previous, self.sequence = value["sha256"], self.sequence + 1
        self.report["event_tail"] = self.previous
        self.report["status"] = kind
        temporary = self.directory / "state.next"
        write_json(temporary, self.report)
        temporary.replace(self.directory / "state.json")


def validate_journal(directory, tail):
    require((directory / "events.jsonl").stat().st_size <= 1048576,
            "REPLAY_MISMATCH", "event history exceeds budget")
    previous = None
    events = []
    for index, line in enumerate((directory / "events.jsonl").read_bytes().splitlines()):
        row = json.loads(line)
        require(type(row) is dict and set(row) == {"sequence", "previous", "time_ns", "kind", "data", "sha256"},
                "REPLAY_MISMATCH", "invalid event fields")
        claimed = row.pop("sha256", None)
        require(type(row["sequence"]) is int and row["sequence"] == index
                and type(row["time_ns"]) is int and row["time_ns"] > 0
                and row["previous"] == previous
                and digest(canonical(row)) == claimed, "REPLAY_MISMATCH", "event history changed")
        previous = claimed
        events.append(row)
    require(previous is not None and previous == tail, "REPLAY_MISMATCH", "event tail changed")
    return events
