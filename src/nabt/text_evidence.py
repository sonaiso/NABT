"""Finite receipt/candidate algebra exported by the native Lean specification.

A cue code denotes an already witnessed grammatical constraint. Neither a
prefix observation nor a governor's expected argument can mint such a cue.
The source reader owns receipt construction; callers cannot submit evidence
objects to the public text reader in place of source bytes.
"""

from hashlib import sha256
from importlib.resources import files
import json

from .errors import NabtError, natural

LAW_ID = "nabt.text-evidence.v1"
EXPECTED_TABLE_SHA256 = "047d2409b280e488f4af3d635de190752a30938dbc47f053db4ae7670ef9d3ae"
KINDS = ("noun", "verb", "particle")


def installed_table():
    try:
        raw = files("nabt").joinpath("data/text_evidence.json").read_bytes()
        if sha256(raw).hexdigest() != EXPECTED_TABLE_SHA256:
            raise ValueError("text evidence table pin differs")
        return json.loads(raw)
    except (OSError, ValueError) as error:
        raise NabtError("INSTALLED_CONTRACT_FAILED", "Text-evidence table cannot be replayed", status="DEFER") from error


def kind_candidates(cues: tuple[int, ...]) -> tuple[str, ...]:
    if type(cues) is not tuple or len(cues) > 128:
        raise NabtError("INVALID_TEXT_CUES", "Use a bounded tuple of witnessed cue codes")
    mask = 0
    for cue in cues:
        natural(cue, "cue", maximum=2)
        mask |= 1 << cue
    return tuple(KINDS[kind] for kind in installed_table()["kind_rows"][mask]["candidates"])


def receipt_activated(flags: tuple[bool, ...]) -> bool:
    if type(flags) is not tuple or len(flags) != 6 or any(type(flag) is not bool for flag in flags):
        raise NabtError("INVALID_TEXT_RECEIPT", "Receipt activation needs six actual Boolean flags")
    mask = sum(1 << i for i, flag in enumerate(flags) if flag)
    return installed_table()["receipt_rows"][mask]["activated"]
