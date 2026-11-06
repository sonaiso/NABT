"""Explicit UTF transport into the existing immutable UTF-8 SourceBlob.

Preserve original bytes and scalar offsets. No guessing, normalization, glyph
shaping, acoustic inference or promotion to an A116/grammar certificate.
"""
from hashlib import sha256
import re

from nabt.learning.source_evidence import SourceBlob
from tools.evidence_lifecycle_v1 import _encoded, wire

ENCODINGS = ("utf-8", "utf-16-le", "utf-16-be", "utf-32-le", "utf-32-be")
MAX_BYTES = 8192


def transcode(request):
    _encoded(request, MAX_BYTES * 3)
    if type(request) is not dict or set(request) != {"source_id", "encoding", "hex"}:
        raise ValueError("Supply source_id, explicit encoding and canonical lowercase hex")
    encoding, source_id, text = request["encoding"], request["source_id"], request["hex"]
    if type(encoding) is not str or encoding not in ENCODINGS:
        raise ValueError("Unsupported or implicit encoding")
    if type(source_id) is not str or len(source_id) > 128 or not re.fullmatch(r"[a-z][a-z0-9_]*", source_id):
        raise ValueError("Invalid source identity")
    if type(text) is not str or not 2 <= len(text) <= MAX_BYTES * 2 or not re.fullmatch(r"(?:[0-9a-f]{2})+", text):
        raise ValueError("Invalid hex or source byte budget")
    raw = bytes.fromhex(text)
    decoded = raw.decode(encoding, errors="strict")
    if decoded.encode(encoding, errors="strict") != raw:
        raise ValueError("Nonreversible input")
    utf8 = decoded.encode("utf-8", errors="strict")
    if len(utf8) > MAX_BYTES:
        raise ValueError("UTF-8 derivative exceeds byte budget")
    derivative = SourceBlob(source_id + "_utf8", utf8)
    source_offset = utf8_offset = 0
    spans = []
    for scalar in decoded:
        a, b = len(scalar.encode(encoding)), len(scalar.encode("utf-8"))
        spans.append({"scalar": scalar, "codepoint": ord(scalar),
            "input_byte_span": [source_offset, source_offset + a],
            "utf8_byte_span": [utf8_offset, utf8_offset + b]})
        source_offset += a
        utf8_offset += b
    return {"schema": "nabt.explicit-utf-transport.v1", "origin": {
        "source_id": source_id, "encoding": encoding, "sha256": sha256(raw).hexdigest(), "hex": text},
        "utf8": {"source_id": derivative.source_id, "sha256": derivative.sha256,
                 "hex": utf8.hex(), "text": decoded}, "scalar_map": spans,
        "bom_policy": "PRESERVE_AS_SCALAR_NO_IMPLICIT_ENDIAN_GUESS", "normalization_performed": False,
        "roundtrip_checked": True, "authority": "PYTHON_TRANSPORT_CHECK_ONLY",
        "acoustic_interpretation_established": False, "a116_license_established": False}


def verify(report, *, expected_request):
    _encoded(report, MAX_BYTES * 256)
    return {"valid": wire(report) == wire(transcode(expected_request)),
            "verification": "FRESH_EXPLICIT_ENCODING_REPLAY", "a116_license_established": False}
