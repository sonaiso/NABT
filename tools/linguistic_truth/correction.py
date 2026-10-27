"""Replay the source for the v2 bounded negative بل reading.

This is the reading reported in Mughni; adjacent text records disagreement.
It is not an empirical verification or a universal account of every بل.
"""
import hashlib
from pathlib import Path

CITATION = {
    "path": "src/nabt/data/source_evidence/mughni.txt",
    "source_sha256": "f37ac2bb4b273f59169053dd0ac2abf50a52846a7e87ddf689ee5c0b87f77e7d",
    "start_byte": 232015,
    "end_byte": 232141,
    "quotation": "وإن تقدمها نفي أو نهي فهي لتقرير ما قبلها على\n~~حالته وجعل ضده لما بعده",
}


def replay_correction_source(root):
    raw = (Path(root) / CITATION["path"]).read_bytes()
    if (hashlib.sha256(raw).hexdigest() != CITATION["source_sha256"]
            or raw[CITATION["start_byte"]:CITATION["end_byte"]] != CITATION["quotation"].encode()):
        raise ValueError("CORRECTION_SOURCE_CHANGED")
    return dict(CITATION)
