"""Versioned source transport and an optional, strictly scoped A116 word view.

Byte restoration establishes identity, not a word's linguistic admissibility.
The current alphabet order is retained; no Unicode normalization is performed.
"""
from __future__ import annotations

import hashlib
import json
import re

from .alphabet import ALPHABET_ID, CARRIERS, HARAKAT, parse_word
from .codec import encode_cells, pack_cells
from .errors import NabtError, resource_limit

SCHEMA = "nabt.source-envelope.v1"
WORD_SCHEMA = "nabt.a116-word-view.v1"
MAX_BYTES = 65536


def _wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _binding(identity, revision, scope):
    for value in (identity, revision, scope):
        if type(value) is not str or not value or "\0" in value:
            raise NabtError("INVALID_BINDING", "Binding fields must be nonempty UTF-8 strings")
        try:
            size = len(value.encode("utf-8"))
        except UnicodeError as exc:
            raise NabtError("INVALID_BINDING", "Binding is not UTF-8") from exc
        if size > 256:
            raise resource_limit("Binding exceeds 256 bytes")
    return {"source_id": identity, "revision": revision, "scope": scope}


def encode_source(raw, *, identity="text", revision="1", scope="default"):
    if type(raw) is not bytes:
        raise NabtError("INVALID_BYTES", "Source must be independent bytes")
    if len(raw) > MAX_BYTES:
        raise resource_limit("Source exceeds 65536 bytes")
    try:
        raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise NabtError("INVALID_UTF8", "Source is not UTF-8") from exc
    return {"schema": SCHEMA, "binding": _binding(identity, revision, scope),
            "encoding": "UTF-8", "normalization": "none", "byte_length": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(), "raw_hex": raw.hex()}


def restore_source(envelope):
    """Validate transport consistency only; authenticity needs independent bytes."""
    if type(envelope) is not dict or envelope.get("schema") != SCHEMA:
        raise NabtError("INVALID_ENVELOPE", "Unsupported source envelope")
    encoded = envelope.get("raw_hex")
    if type(encoded) is not str:
        raise NabtError("INVALID_ENVELOPE", "Missing raw hex")
    if len(encoded) > 2 * MAX_BYTES:
        raise resource_limit("Encoded source exceeds its byte budget")
    if re.fullmatch(r"(?:[0-9a-f]{2})*", encoded) is None:
        raise NabtError("NONCANONICAL_HEX", "Hex must be lowercase, even and without whitespace")
    binding = envelope.get("binding")
    if type(binding) is not dict or set(binding) != {"source_id", "revision", "scope"}:
        raise NabtError("INVALID_BINDING", "Incomplete or extended source binding")
    raw = bytes.fromhex(encoded)
    expected = encode_source(raw, identity=binding["source_id"],
                             revision=binding["revision"], scope=binding["scope"])
    try:
        equal = _wire(envelope) == _wire(expected)
    except (ValueError, TypeError, RecursionError) as exc:
        raise NabtError("INVALID_ENVELOPE", "Envelope is not finite UTF-8 JSON") from exc
    if not equal:
        raise NabtError("ENVELOPE_MISMATCH", "Envelope metadata does not match its bytes")
    return raw


def verify_source(raw, envelope, *, identity="text", revision="1", scope="default"):
    expected = encode_source(raw, identity=identity, revision=revision, scope=scope)
    restored = restore_source(envelope)
    if restored != raw or _wire(envelope) != _wire(expected):
        raise NabtError("SOURCE_BINDING_MISMATCH", "Envelope differs from independent source or binding")
    return True


def word_view(raw, *, identity="text", revision="1", scope="default"):
    """One exact word, not tokenization, ranking by meaning, or a sound-law check."""
    source = encode_source(raw, identity=identity, revision=revision, scope=scope)
    registry = {"alphabet_id": ALPHABET_ID, "carriers": list(CARRIERS), "states": list(HARAKAT)}
    result = {"schema": WORD_SCHEMA, "source": source, "registry": registry,
              "registry_sha256": hashlib.sha256(_wire(registry)).hexdigest(),
              "scope": "cell_identity_only", "linguistic_admissibility_established": False}
    try:
        cells = parse_word(raw.decode("utf-8"))
    except NabtError as exc:
        result.update(outcome=exc.status, error=exc.code)
        return result
    # Hex avoids Python/JSON decimal-digit limits at the existing 4096-cell bound.
    result.update(outcome="ENCODED", cells=list(cells),
                  number_hex=format(encode_cells(cells), "x"),
                  packed_hex=pack_cells(cells).hex())
    return result
