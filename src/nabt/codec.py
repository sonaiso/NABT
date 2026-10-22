"""Exact numeric and framed seven-bit codecs; these establish identity only."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .alphabet import ALPHABET_ID, MAX_CELLS, validate_cell, validate_cells
from .errors import NabtError, natural, resource_limit

BASE = 116
MAGIC = b"NABT\x01"
HEADER_SIZE = len(MAGIC) + 4


def encode_cells(cells: Iterable[int]) -> int:
    """Bijective positional encoding: append a as n -> 116*n + a + 1."""
    n = 0
    for a in validate_cells(cells):
        n = BASE * n + a + 1
    return n


def decode_number(number: int) -> tuple[int, ...]:
    n = natural(number, "number")
    if n.bit_length() > 7 * MAX_CELLS + 1:
        raise resource_limit("Numeric code exceeds the decoding budget", maximum_cells=MAX_CELLS)
    cells = []
    while n:
        if len(cells) >= MAX_CELLS:
            raise resource_limit("Numeric code exceeds the decoding budget", maximum_cells=MAX_CELLS)
        n, a = divmod(n - 1, BASE)
        cells.append(a)
    return tuple(reversed(cells))


def append_numbers(left: int, right: int) -> int:
    u, v = decode_number(left), decode_number(right)
    if len(u) + len(v) > MAX_CELLS:
        raise resource_limit("Concatenation exceeds the cell budget", maximum=MAX_CELLS)
    return BASE ** len(v) * left + right


def _offset(length: int) -> int:
    return (BASE ** length - 1) // (BASE - 1)


def split_number(number: int, left_length: int) -> tuple[int, int]:
    cells = decode_number(number)
    natural(left_length, "left_length", maximum=len(cells))
    right_length = len(cells) - left_length
    digits = number - _offset(len(cells))
    prefix, suffix = divmod(digits, BASE ** right_length)
    return _offset(left_length) + prefix, _offset(right_length) + suffix


def replace_cell(number: int, index: int, cell: int) -> int:
    cells = decode_number(number)
    natural(index, "index")
    if index >= len(cells):
        raise NabtError("OUTSIDE_DOMAIN", "Replacement index is outside the sequence")
    a = validate_cell(cell)
    return number + (a - cells[index]) * BASE ** (len(cells) - 1 - index)


def pack_cells(cells: Iterable[int]) -> bytes:
    """Frame the cell count, then pack exactly seven bits per cell, MSB first."""
    values = validate_cells(cells)
    buffer = 0
    bits = 0
    body = bytearray()
    for a in values:
        buffer = (buffer << 7) | a
        bits += 7
        while bits >= 8:
            bits -= 8
            body.append((buffer >> bits) & 255)
            buffer &= (1 << bits) - 1
    if bits:
        body.append(buffer << (8 - bits))
    return MAGIC + len(values).to_bytes(4, "big") + bytes(body)


def unpack_cells(data: bytes) -> tuple[int, ...]:
    if type(data) is not bytes:
        raise NabtError("INVALID_BYTES", "Packed cells must be bytes")
    if len(data) > HEADER_SIZE + (7 * MAX_CELLS + 7) // 8:
        raise resource_limit("Packed input exceeds the decoding budget")
    if len(data) < HEADER_SIZE or data[:len(MAGIC)] != MAGIC:
        raise NabtError("INVALID_FRAME", "Missing or unsupported NABT bit-frame header")
    count = int.from_bytes(data[len(MAGIC):HEADER_SIZE], "big")
    if count > MAX_CELLS:
        raise resource_limit("Declared cell count exceeds the budget", maximum=MAX_CELLS)
    expected = HEADER_SIZE + (7 * count + 7) // 8
    if len(data) != expected:
        raise NabtError("INVALID_FRAME_LENGTH", "Packed body length does not match its cell count")
    body = data[HEADER_SIZE:]
    unused = (-7 * count) % 8
    if body and unused and body[-1] & ((1 << unused) - 1):
        raise NabtError("NON_CANONICAL_PADDING", "Unused trailing bits must be zero")
    result = []
    buffer = bits = 0
    for byte in body:
        buffer = (buffer << 8) | byte
        bits += 8
        while bits >= 7 and len(result) < count:
            bits -= 7
            result.append(validate_cell((buffer >> bits) & 127))
            buffer &= (1 << bits) - 1
    return tuple(result)


@dataclass(frozen=True)
class OccurrenceIdentity:
    """A position is meaningful only inside a named source and analysis version."""

    source_id: str
    analysis_version: str
    position: int
    cell: int

    def __post_init__(self) -> None:
        for label, value in (("source_id", self.source_id), ("analysis_version", self.analysis_version)):
            if type(value) is not str or not value or len(value) > 1024:
                raise NabtError("INVALID_IDENTITY", f"{label} must be a non-empty bounded string")
        natural(self.position, "position")
        validate_cell(self.cell)

    @property
    def local_number(self) -> int:
        return BASE * self.position + self.cell

    def as_dict(self) -> dict[str, object]:
        return {"alphabet_id": ALPHABET_ID, "source_id": self.source_id,
                "analysis_version": self.analysis_version, "position": self.position,
                "cell": self.cell, "local_number": self.local_number}
