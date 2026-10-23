#!/usr/bin/env python3
"""Compare fresh Lean Arabic entry/mood tags with Python and finite cell envelopes.

The envelope checks exercise the existing cell codec on exported examples.
They do not equate Python's UTF-8 reading packet with the Lean cell envelope,
and do not establish parser refinement or general Arabic interpretation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nabt.arabic_reader import LANGUAGE_ID, Mood, encode_cell_envelope, decode_cell_envelope
from nabt.program import Opcode
from nabt.text_ir import LANGUAGE_ID as CONTROLLED_LANGUAGE_ID


def check_table(table: dict) -> dict:
    if type(table) is not dict or set(table) != {
        "schema_version", "language_id", "moods", "entry_profiles", "envelope_domain", "envelopes"
    }:
        raise ValueError("Unexpected Lean export shape")
    if type(table["schema_version"]) is not int or table["schema_version"] != 1:
        raise ValueError("Unsupported Lean export version")
    if table["language_id"] != LANGUAGE_ID:
        raise ValueError("Arabic language profile differs from Lean")
    expected_moods = [{"name": mood.name, "code": int(mood)} for mood in Mood]
    # Canonical JSON comparison distinguishes booleans from integer tags.
    if json.dumps(table["moods"], sort_keys=True) != json.dumps(expected_moods, sort_keys=True):
        raise ValueError("Python speech-force tags differ from Lean")
    profiles = [
        {"name": "START_TEXT", "opcode": int(Opcode.START_TEXT), "language_id": CONTROLLED_LANGUAGE_ID},
        {"name": "START_ARABIC", "opcode": int(Opcode.START_ARABIC), "language_id": LANGUAGE_ID},
    ]
    if json.dumps(table["entry_profiles"], sort_keys=True) != json.dumps(profiles, sort_keys=True):
        raise ValueError("Python entry opcodes or profiles differ from Lean")
    if table["envelope_domain"] != "nabt.arabic-reading-envelope.b116.v1":
        raise ValueError("Unexpected cell-envelope domain")
    envelopes = table["envelopes"]
    if type(envelopes) is not list or len(envelopes) != 48:
        raise ValueError("Expected eight moods and six declared payloads")
    seen = set()
    for example in envelopes:
        if type(example) is not dict or set(example) != {"mood", "payload", "number"}:
            raise ValueError("Unexpected envelope example")
        mood = Mood[example["mood"]]
        payload = example["payload"]
        if type(payload) is not list or type(example["number"]) is not int:
            raise ValueError("Noncanonical envelope data")
        encoded = encode_cell_envelope(mood, tuple(payload))
        if example["number"] != encoded:
            raise ValueError("Cell-envelope arithmetic differs from Lean")
        decoded_mood, decoded_payload = decode_cell_envelope(example["number"])
        if tuple(payload) != decoded_payload or decoded_mood != mood:
            raise ValueError("Cell-envelope inverse differs from its declared payload")
        key = (mood.name, tuple(payload))
        if key in seen:
            raise ValueError("Duplicate exported example")
        seen.add(key)
    payload_set = {(), (0,), (115,), (84, 8, 4), (85, 10, 4), (0, 115, 0)}
    if seen != {(mood.name, payload) for mood in Mood for payload in payload_set}:
        raise ValueError("Missing or additional mood/payload combination")
    return {
        "ok": True,
        "mood_tags": len(expected_moods),
        "entry_profiles": len(profiles),
        "finite_cell_envelopes": len(envelopes),
        "scope": "fresh Lean tags and finite cell-codec examples; not Python parser refinement",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default="lake")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        execution = subprocess.run(
            [args.lake, "env", "lean", "--run", "ExportArabicReading.lean"],
            cwd=ROOT / "formal", check=True, capture_output=True, text=True,
        )
        report = check_table(json.loads(execution.stdout))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        if isinstance(exc, subprocess.CalledProcessError):
            print(exc.stdout or "")
            print(exc.stderr or "")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
