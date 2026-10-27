"""Shared installed identity and lossless, partial A116 source projection.

This module does not infer missing marks, expand shadda/tanwin/long alif, or
license a word.  The number encodes only the explicitly representable cells;
source bytes and their full partition remain indispensable, including when
two different sources have the same projected number.  Every admission checks
the package-owned law again: warming Machine's cache cannot hide changed bytes.
"""
from __future__ import annotations

from functools import lru_cache, wraps
from hashlib import sha256
from importlib.resources import files
import json
import re
from typing import Any, Callable

from . import alphabet
from .errors import NabtError, resource_limit

LAW_ID = "nabt.foundation.v1"
TRANSFORM_LAW_ID = "nabt.foundation.cell-transform.v1"
NUMBER_DOMAIN = "nabt.foundation.projected-cells.bijective116.v1"
MAX_SOURCE_BYTES = 65_536
MAX_RECEIPT_BYTES = 524_288
SEPARATORS = frozenset(' \t\r\n.،؛,:!?؟()[]{}«»"“”')
_STATE_MARKS = {"fatha": "َ", "damma": "ُ", "kasra": "ِ", "sukun": "ْ"}
_EXECUTION_CACHE: tuple | None = None


@lru_cache(maxsize=1)
def _installed_json(raw: bytes) -> dict:
    """Private parse cache keyed by exact freshly authenticated bytes."""
    return json.loads(raw)


def _check_execution(execution: Any, installed: dict, digest: str) -> None:
    """Cache only a checked frozen table with unchanged immutable field objects."""
    global _EXECUTION_CACHE
    from . import machine
    if type(execution) is not machine._Table:
        raise ValueError("execution law is not the installed table type")
    identity = (execution, execution.transitions, execution.potentials, execution.wasl, execution.waqf)
    if (_EXECUTION_CACHE is not None and _EXECUTION_CACHE[-1] == digest
            and execution.digest == digest
            and all(old is new for old, new in zip(_EXECUTION_CACHE[:-1], identity))):
        return
    if (type(execution.transitions) is not tuple
            or any(type(row) is not tuple or any(type(edge) is not tuple
                or len(edge) != 2 or any(type(value) is not int for value in edge)
                for edge in row) for row in execution.transitions)
            or type(execution.potentials) is not tuple
            or type(execution.wasl) is not tuple or type(execution.waqf) is not tuple
            or any(type(value) is not int for value in execution.potentials)
            or any(type(value) is not bool for value in execution.wasl + execution.waqf)
            or execution.digest != digest
            or execution.transitions != tuple(tuple(tuple(edge) for edge in row)
                                             for row in installed["transitions"])
            or execution.potentials != tuple(installed["pot"])
            or execution.wasl != tuple(installed["final_wasl"])
            or execution.waqf != tuple(installed["final_waqf"])):
        raise ValueError("cached execution law differs from installed bytes")
    # Keep strong references: an object ID alone could be reused after GC.
    _EXECUTION_CACHE = identity + (digest,)


def require_foundation(surface_id: str) -> dict:
    """Fail closed against installed authority, never a caller's manifest.

    ``surface_id`` is a bounded diagnostic label, not a selection of a law.
    The public-surface registry is maintained separately by the architecture
    audit. Fresh disk bytes and cached execution data must agree on every call.
    """
    # Public codec entry points themselves use this guard. Importing codec or
    # Machine while their modules initialize would create an admission cycle.
    from . import codec, machine
    if (type(surface_id) is not str or
            re.fullmatch(r"[a-z][a-z0-9_.:-]{0,255}", surface_id) is None):
        raise NabtError("INVALID_FOUNDATION_SURFACE", "Use a bounded public-surface identifier")
    try:
        raw = files("nabt").joinpath("data/law.json").read_bytes()
    except OSError as exc:
        raise NabtError("FOUNDATION_UNAVAILABLE", "The installed core law is unavailable", status="DEFER") from exc
    try:
        digest = sha256(raw).hexdigest()
        if digest != machine.EXPECTED_TABLE_SHA256:
            raise ValueError("installed law bytes changed")
        installed = _installed_json(raw)
        expected = {"schema_version": 1, "alphabet_id": alphabet.ALPHABET_ID,
                    "law_id": alphabet.LAW_ID, "carriers": list(alphabet.CARRIERS),
                    "states": list(alphabet.STATE_NAMES), "alphabet_size": alphabet.ALPHABET_SIZE,
                    "state_count": machine.STATE_COUNT, "start_state": 0,
                    "dead_state": machine.DEAD_STATE}
        for key, value in expected.items():
            if type(installed.get(key)) is not type(value) or installed.get(key) != value:
                raise ValueError("installed core identity differs: " + key)
        if (alphabet.ALPHABET_ID != "nabt.a116.v1" or alphabet.LAW_ID != "nabt-sound-shape-v1"
                or type(alphabet.ALPHABET_SIZE) is not int or type(codec.BASE) is not int
                or alphabet.ALPHABET_SIZE != codec.BASE
                or alphabet.ALPHABET_SIZE != len(alphabet.CARRIERS) * len(alphabet.HARAKAT)
                or tuple(_STATE_MARKS.get(name) for name in alphabet.STATE_NAMES) != alphabet.HARAKAT
                or machine.ALPHABET_ID != alphabet.ALPHABET_ID
                or machine.LAW_ID != alphabet.LAW_ID or machine.CARRIERS != alphabet.CARRIERS
                or machine.STATE_NAMES != alphabet.STATE_NAMES
                or codec.ALPHABET_ID != alphabet.ALPHABET_ID):
            raise ValueError("runtime core identity differs")
        _check_execution(machine._load_table(), installed, digest)
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise NabtError("FOUNDATION_INTEGRITY", "The installed A116 foundation does not replay") from exc
    return {"foundation_id": LAW_ID, "alphabet_id": alphabet.ALPHABET_ID,
            "shape_law_id": alphabet.LAW_ID, "number_domain": NUMBER_DOMAIN,
            "alphabet_size": alphabet.ALPHABET_SIZE, "law_table_sha256": digest,
            "surface_id": surface_id, "authority": "REPRESENTATION_FOUNDATION_ONLY"}


def foundation_guard(surface_id: str) -> Callable:
    """Guard an entry point without modifying its domain result or signature."""
    def decorate(function: Callable) -> Callable:
        @wraps(function)
        def guarded(*args: Any, **kwargs: Any) -> Any:
            require_foundation(surface_id)
            return function(*args, **kwargs)
        return guarded
    return decorate


def _mark(char: str) -> bool:
    n = ord(char)
    return 0x064B <= n <= 0x065F or n == 0x0670 or 0x06D6 <= n <= 0x06ED


def _vowel(char: str) -> bool:
    return 0x064B <= ord(char) <= 0x0650 or char == "ْ"


def _label(value: Any, name: str) -> str:
    if (type(value) is not str or not value or len(value) > 256
            or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        raise NabtError("INVALID_FOUNDATION_SOURCE", "Use a nonempty bounded " + name)
    try:
        value.encode("utf-8", "strict")
    except UnicodeError as exc:
        raise NabtError("FOUNDATION_SOURCE_ENCODING", "Source labels must be valid Unicode") from exc
    return value


def _decimal(number: int) -> str:
    """Bounded decimal transport without changing Python's process-wide limit."""
    if number == 0:
        return "0"
    chunks = []
    while number:
        number, chunk = divmod(number, 1_000_000_000)
        chunks.append(chunk)
    return str(chunks[-1]) + "".join(f"{chunk:09d}" for chunk in reversed(chunks[:-1]))


def _source_text(text: str | bytes) -> tuple[str, bytes]:
    if type(text) not in (str, bytes):
        raise NabtError("INVALID_FOUNDATION_SOURCE", "Source must be exact str or UTF-8 bytes")
    if len(text) > MAX_SOURCE_BYTES:
        raise resource_limit("Foundation source exceeds its byte budget", maximum_bytes=MAX_SOURCE_BYTES)
    try:
        raw = text.encode("utf-8", "strict") if type(text) is str else text
        text = raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise NabtError("FOUNDATION_SOURCE_ENCODING", "Source must contain valid UTF-8") from exc
    if len(raw) > MAX_SOURCE_BYTES:
        raise resource_limit("Foundation source exceeds its byte budget", maximum_bytes=MAX_SOURCE_BYTES)
    return text, raw


def _source_clusters(text: str):
    """Yield exact byte intervals for the shared representation partition.

    These are carrier/mark clusters and separators, not grammatical words.
    Boundary checks use this scan without projecting unrelated source material
    or imposing the selected occurrence's cell/receipt budgets on that material.
    """
    i = offset = 0
    while i < len(text):
        start = i
        char = text[i]
        i += 1
        if char not in SEPARATORS:
            while i < len(text) and _mark(text[i]):
                i += 1
        surface = text[start:i]
        end = offset + len(surface.encode("utf-8"))
        yield offset, end, surface
        offset = end


def inspect_source(text: str | bytes, *, source_id: str = "input", revision: str = "1") -> dict:
    """Partition exact UTF-8; project only complete canonical carrier/mark pairs.

    COMPLETE concerns this representation alone. Unsupported but nonconflicting
    clusters remain PARTIAL. Malformed marks remain INVALID, even if neighboring
    clusters were representable. Resource exhaustion is an exception, not one
    of these linguistic/representation results.
    """
    from . import codec
    require_foundation("foundation.inspect_source")
    source_id, revision = _label(source_id, "source ID"), _label(revision, "revision")
    text, raw = _source_text(text)
    pieces, cells, issues = [], [], []
    invalid = not text
    if not text:
        issues.append({"code": "EMPTY_SOURCE", "start_byte": 0, "end_byte": 0})
    for offset, end, surface in _source_clusters(text):
        char = surface[0]
        kind, cell, code = "residual", None, None
        if char in SEPARATORS:
            kind = "separator"
        elif _mark(char):
            code, invalid = "MARK_WITHOUT_CARRIER", True
        else:
            marks = surface[1:]
            if len(marks) != len(set(marks)) or sum(_vowel(mark) for mark in marks) > 1:
                code, invalid = "CONFLICTING_MARKS", True
            elif char in alphabet.CARRIERS and len(marks) == 1 and marks in alphabet.HARAKAT:
                kind = "cell"
                cell = alphabet.cell_id(char, alphabet.HARAKAT.index(marks))
                cells.append(cell)
                if len(cells) > alphabet.MAX_CELLS:
                    raise resource_limit("Foundation projection exceeds its cell budget", maximum_cells=alphabet.MAX_CELLS)
            elif char in alphabet.CARRIERS and not marks:
                code = "MISSING_VOCALIZATION"
            else:
                code = "UNSUPPORTED_ORTHOGRAPHY"
        pieces.append({"kind": kind, "text": surface, "start_byte": offset, "end_byte": end, "cell": cell})
        if code is not None:
            issues.append({"code": code, "start_byte": offset, "end_byte": end})
    result = {"law_id": LAW_ID, "alphabet_id": alphabet.ALPHABET_ID, "number_domain": NUMBER_DOMAIN,
            "source": {"id": source_id, "revision": revision, "text": text}, "raw_utf8": list(raw),
            "status": "INVALID" if invalid else "PARTIAL" if issues else "COMPLETE",
            "pieces": pieces, "cells": cells, "number": _decimal(codec.encode_cells(cells)), "issues": issues}
    wire = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(wire.encode("utf-8")) > MAX_RECEIPT_BYTES:
        raise resource_limit("Foundation receipt exceeds its byte budget", maximum_receipt_bytes=MAX_RECEIPT_BYTES)
    return result


def validate_source(text: str | bytes) -> None:
    """Reject malformed marks, never an unimplemented spelling projection."""
    receipt = inspect_source(text)
    if receipt["status"] == "INVALID":
        raise NabtError("FOUNDATION_SOURCE_INVALID", "Source contains malformed or conflicting marks",
                        details={"issues": receipt["issues"]})


def verify_source_receipt(receipt: Any, *, text: str | bytes | None = None,
                          source_id: str | None = None, revision: str | None = None) -> bool:
    """Replay exact representation; optional expected input binds external identity.

    With no expected input this checks internal coherence only. A self-consistent
    receipt or a caller-chosen revision never establishes source authority.
    """
    require_foundation("foundation.verify_source_receipt")
    try:
        if type(receipt) is not dict or type(receipt.get("source")) is not dict:
            return False
        source = receipt["source"]
        fresh = inspect_source(source["text"] if text is None else text,
                               source_id=source["id"] if source_id is None else source_id,
                               revision=source["revision"] if revision is None else revision)
        # JSON's typed representation distinguishes bool from int and rejects
        # exotic objects; Python equality alone treats True and 1 as identical.
        wire = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True,
                                         separators=(",", ":"), allow_nan=False)
        return wire(receipt) == wire(fresh)
    except (NabtError, KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        return False


def make_transform(binding: dict, operation: dict) -> dict:
    """Compute a numeric cell operation bound to one exact source/reading span.

    This supplies no morphological rule or semantic license. Appended cells are
    explicit operation operands, not inferred letters in the original source.
    """
    from copy import deepcopy
    from . import codec
    require_foundation("foundation.make_transform")
    keys = {"source", "scope_id", "occurrence_id", "reading_id", "start_byte", "end_byte", "surface"}
    if type(binding) is not dict or set(binding) != keys:
        raise NabtError("INVALID_INPUT", "Transform needs an exact source, scope, occurrence and reading binding")
    source = binding["source"]
    if type(source) is not dict or set(source) != {"id", "revision", "text"} or type(source["text"]) is not str:
        raise NabtError("INVALID_INPUT", "Transform source must contain exact id, revision and text")
    _label(source["id"], "source ID")
    _label(source["revision"], "revision")
    for key in ("scope_id", "occurrence_id", "reading_id"):
        _label(binding[key], key)
    _, raw = _source_text(source["text"])
    start, end, surface = binding["start_byte"], binding["end_byte"], binding["surface"]
    if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(raw)
            or type(surface) is not str):
        raise NabtError("INVALID_INPUT", "Transform span must name a nonempty UTF-8 source interval")
    _, surface_raw = _source_text(surface)
    if raw[start:end] != surface_raw:
        raise NabtError("INVALID_INPUT", "Transform surface does not replay its source byte interval")
    boundaries = {0}
    boundaries.update(stop for _, stop, _ in _source_clusters(source["text"]))
    if start not in boundaries or end not in boundaries:
        raise NabtError("INVALID_INPUT", "Transform span cuts a carrier/mark cluster in its full source")
    projected = inspect_source(surface, source_id=source["id"], revision=source["revision"])
    if projected["status"] == "PARTIAL":
        raise NabtError("INCOMPLETE_PROJECTION", "Transform requires explicit cells for its entire bound occurrence", status="DEFER")
    if projected["status"] == "INVALID":
        raise NabtError("INVALID_SOURCE", "Transform occurrence contains malformed source marks")
    if type(operation) is not dict or type(operation.get("op")) is not str:
        raise NabtError("INVALID_INPUT", "Use a typed cell operation")
    input_cells = tuple(projected["cells"])
    input_number = codec.encode_cells(input_cells)
    if operation == {"op": "keep"}:
        output_number = input_number
    elif set(operation) == {"op", "suffix"} and operation["op"] == "append":
        if type(operation["suffix"]) is not list:
            raise NabtError("INVALID_INPUT", "Append suffix must be an array of cells")
        suffix = alphabet.validate_cells(operation["suffix"])
        output_number = codec.append_numbers(input_number, codec.encode_cells(suffix))
    elif set(operation) == {"op", "index", "cell"} and operation["op"] == "replace":
        index = operation["index"]
        if type(index) is not int or not 0 <= index < len(input_cells):
            raise NabtError("INVALID_INPUT", "Replacement index must name an input cell")
        output_number = codec.replace_cell(input_number, index, alphabet.validate_cell(operation["cell"]))
    else:
        raise NabtError("INVALID_INPUT", "Use exactly keep, append or replace and its declared fields")
    output_cells = codec.decode_number(output_number)
    result = {"law_id": TRANSFORM_LAW_ID, "alphabet_id": alphabet.ALPHABET_ID, "number_domain": NUMBER_DOMAIN,
              "binding": deepcopy(binding), "operation": deepcopy(operation),
              "input_cells": list(input_cells), "output_cells": list(output_cells),
              "input_number": _decimal(input_number), "output_number": _decimal(output_number)}
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if len(encoded.encode("utf-8")) > MAX_RECEIPT_BYTES:
        raise resource_limit("Transform receipt exceeds its byte budget", maximum_receipt_bytes=MAX_RECEIPT_BYTES)
    return result


def check_transform(binding: dict, operation: dict, receipt: Any) -> bool:
    """Check against independent expected input, never the receipt's own binding."""
    require_foundation("foundation.check_transform")
    try:
        expected = make_transform(binding, operation)
        wire = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True,
                                         separators=(",", ":"), allow_nan=False)
        return type(receipt) is dict and wire(receipt) == wire(expected)
    except (NabtError, KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        return False
