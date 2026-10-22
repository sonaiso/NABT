"""Replayable word-shape certificates with no caller-controlled authority.

A certificate records a claim relative to the bundled law. It is neither an
attestation of Arabic usage nor a lexical, syntactic, or semantic judgment.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json
import re
from typing import Any

from .alphabet import ALPHABET_ID, LAW_ID, MAX_CELLS, parse_word, validate_cells
from .codec import encode_cells
from .errors import NabtError, resource_limit
from .machine import Machine, MAX_WEIGHT

_KEYS = frozenset({"schema_version", "certificate_type", "status", "alphabet_id",
                  "law_id", "table_sha256", "mode", "cells", "numeric_code",
                  "cell_length", "consonant_weight", "rank", "start_state", "final_state",
                  "trace", "source_text", "source_sha256"})
_STEP_KEYS = frozenset({"position", "state_before", "cell", "state_after", "weight_delta"})
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)\Z", flags=re.ASCII)


@lru_cache(maxsize=2)
def _machine(mode: str) -> Machine:
    return Machine(mode)


def issue_certificate(cells: Iterable[int], mode: str = "waqf", source_text: str | None = None) -> dict[str, Any]:
    """Issue only complete words from q0, binding optional exact source bytes."""
    values = validate_cells(cells)
    if type(mode) is not str or mode not in {"wasl", "waqf"}:
        raise NabtError("INVALID_MODE", "Mode must be waqf or wasl")
    if source_text is not None and parse_word(source_text) != values:
        raise NabtError("SOURCE_BINDING_MISMATCH", "Source text does not encode the certificate's cells")
    machine = _machine(mode)
    analysis = machine.analyse(values)
    if not analysis.licensed:
        raise NabtError("UNLICENSED_SHAPE", "The word is outside the declared shape law", details=analysis.as_dict())
    rank = machine.rank(values)
    return {
        "schema_version": 1,
        "certificate_type": "WORD_SHAPE",
        "status": "GENERATED_BY_LAW" if source_text is None else "LICENSED_SHAPE",
        "alphabet_id": ALPHABET_ID,
        "law_id": LAW_ID,
        "table_sha256": machine.table_sha256,
        "mode": mode,
        "cells": list(values),
        "numeric_code": str(encode_cells(values)),
        "cell_length": len(values),
        "consonant_weight": analysis.consonant_weight,
        "rank": str(rank),
        "start_state": 0,
        "final_state": analysis.final_state,
        "trace": [step.as_dict() for step in analysis.trace],
        "source_text": source_text,
        "source_sha256": None if source_text is None else sha256(source_text.encode("utf-8")).hexdigest(),
    }


@dataclass(frozen=True)
class VerificationReport:
    valid: bool
    code: str
    message: str
    status: str

    def as_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "status": self.status, "code": self.code, "message": self.message}


def _schema(certificate: object) -> dict[str, Any]:
    if type(certificate) is not dict or len(certificate) != len(_KEYS) or set(certificate) != _KEYS:
        raise NabtError("INVALID_CERTIFICATE_SCHEMA", "Certificate keys do not match the closed schema")
    for field in ("schema_version", "cell_length", "consonant_weight", "start_state", "final_state"):
        if type(certificate[field]) is not int or certificate[field] < 0:
            raise NabtError("INVALID_CERTIFICATE_SCHEMA", f"{field} must be a natural integer")
    if certificate["schema_version"] != 1 or certificate["certificate_type"] != "WORD_SHAPE":
        raise NabtError("INVALID_CERTIFICATE_SCHEMA", "Unsupported certificate version or type")
    for field in ("certificate_type", "status", "alphabet_id", "law_id", "table_sha256", "mode"):
        if type(certificate[field]) is not str or len(certificate[field]) > 128:
            raise NabtError("INVALID_CERTIFICATE_SCHEMA", f"{field} must be a string")
    if certificate["status"] not in {"GENERATED_BY_LAW", "LICENSED_SHAPE"}:
        raise NabtError("INVALID_CERTIFICATE_SCHEMA", "Unsupported certificate status")
    if certificate["cell_length"] > MAX_CELLS or certificate["consonant_weight"] > MAX_WEIGHT:
        raise resource_limit("Certificate exceeds the declared runtime budget")
    if certificate["start_state"] >= 97 or certificate["final_state"] >= 97:
        raise NabtError("INVALID_CERTIFICATE_SCHEMA", "Certificate machine state is out of range")
    if re.fullmatch(r"[0-9a-f]{64}", certificate["table_sha256"]) is None:
        raise NabtError("INVALID_CERTIFICATE_SCHEMA", "Malformed table digest")
    for field in ("numeric_code", "rank"):
        value = certificate[field]
        if type(value) is not str or len(value) > 1024 or _DECIMAL.fullmatch(value) is None:
            raise NabtError("INVALID_CERTIFICATE_SCHEMA", f"{field} must be a bounded canonical decimal string")
    cells, trace = certificate["cells"], certificate["trace"]
    if type(cells) is not list or type(trace) is not list:
        raise NabtError("INVALID_CERTIFICATE_SCHEMA", "Cells and trace must be arrays")
    if len(cells) > MAX_CELLS or len(trace) > MAX_CELLS:
        raise resource_limit("Certificate exceeds the cell budget", maximum=MAX_CELLS)
    validate_cells(cells)
    for step in trace:
        if type(step) is not dict or set(step) != _STEP_KEYS:
            raise NabtError("INVALID_CERTIFICATE_SCHEMA", "Transition trace has an invalid step schema")
        if any(type(v) is not int or v < 0 for v in step.values()):
            raise NabtError("INVALID_CERTIFICATE_SCHEMA", "Transition trace entries must be natural integers")
        if (step["position"] >= MAX_CELLS or step["state_before"] >= 97 or
                step["state_after"] >= 97 or step["cell"] >= 116 or step["weight_delta"] > 1):
            raise NabtError("INVALID_CERTIFICATE_SCHEMA", "Transition trace entry is out of range")
    source, digest = certificate["source_text"], certificate["source_sha256"]
    if source is None:
        if digest is not None:
            raise NabtError("INVALID_CERTIFICATE_SCHEMA", "Source hash has no source text")
    elif type(source) is not str or type(digest) is not str:
        raise NabtError("INVALID_CERTIFICATE_SCHEMA", "Source text and its digest must be paired strings")
    elif re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise NabtError("INVALID_CERTIFICATE_SCHEMA", "Malformed source digest")
    return certificate


def verify_certificate(certificate: object) -> VerificationReport:
    """Rebuild every claim from trusted law and exact payload, then compare it.

    This verifies internal consistency, not authorship. An attacker can create a
    different internally valid public claim; authentication needs an external key.
    """
    try:
        supplied = _schema(certificate)
        if supplied["alphabet_id"] != ALPHABET_ID or supplied["law_id"] != LAW_ID:
            raise NabtError("AUTHORITY_MISMATCH", "Certificate names an unsupported alphabet or law")
        if supplied["start_state"] != 0:
            raise NabtError("UNLICENSED_CONTEXT", "Word certificates must start at the declared initial state")
        expected = issue_certificate(supplied["cells"], supplied["mode"], supplied["source_text"])
        # Canonical serialization preserves the bool/int distinction after strict
        # field validation and prevents extra or forged derived fields passing.
        dump = lambda obj: json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if dump(supplied) != dump(expected):
            raise NabtError("CERTIFICATE_MISMATCH", "A certificate field differs from authoritative replay")
        return VerificationReport(True, "VERIFIED", "Word-shape certificate matches its declared law and source", "VERIFIED_WORD_SHAPE")
    except NabtError as exc:
        return VerificationReport(False, exc.code, exc.message, exc.status)
    except (TypeError, ValueError, UnicodeError, OverflowError) as exc:
        return VerificationReport(False, "INVALID_CERTIFICATE_SCHEMA", f"Invalid certificate representation: {type(exc).__name__}", "REJECT")
