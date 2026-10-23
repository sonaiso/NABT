"""Pinned, explicit representation bridges; every result is ENCODING_ONLY.

A cell number has meaning only in its named alphabet. A sequence number also
needs a named codec: SLGE.Core.encL reads the first cell as least significant,
whereas NABT, Alghanem atomNumber and Mashru Dal.Adad read it as most significant.
The SLGE codec here is explicitly encL at radix 116, *not* Ladder.wordEnc.

No upstream runtime, normalizer, validator, residual, or linguistic law is
loaded. The immutable declarations below identify the definitions consulted.
NABT-defined byte transports are labelled as such; they do not claim an
upstream wire format. A successful conversion preserves carrier, mark and
sequence, including empty sequences and shapes rejected by a linguistic law.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, NamedTuple

from .alphabet import ALPHABET_ID, CARRIERS, HARAKAT, MAX_CELLS, validate_cell, validate_cells
from .codec import decode_number as _decode_big
from .codec import encode_cells as _encode_big
from .codec import pack_cells, unpack_cells
from .errors import NabtError, resource_limit

ENCODING_ONLY = "ENCODING_ONLY"
REGISTRY_VERSION = "nabt.source-bridges.v1"
ALGHANEM_CANONICAL_ALPHABET_ID = "alghanem.a116.canonical.v1"
ALGHANEM_BRIDGE_ALPHABET_ID = "alghanem.a116.bridge.v1"
MASHRU_ALPHABET_ID = "mashru.dal.cells.v1"
SLGE_ALPHABET_ID = "mashru.slge.cells.v1"

NABT_NUMBER_CODEC = "nabt.bijective116.v1"
ALGHANEM_CANONICAL_NUMBER_CODEC = "nabt.bijective116.alghanem-canonical.v1"
ALGHANEM_NUMBER_CODEC = "alghanem.bridge.atom-number.v1"
MASHRU_NUMBER_CODEC = "mashru.dal.adad.v1"
SLGE_NUMBER_CODEC = "mashru.slge.encL116.v1"
NABT_FRAME_CODEC = "nabt.frame7.v1"
NABT_CELLS_CODEC = "nabt.cells.v1"

ALGHANEM_COMMIT = "9d8fa03a51f894416e0abaf3b6821c5ae6441dcd"
MASHRU_COMMIT = "e4c801ffe9171dadedcc3aae23051ea0953ae361"


class SourcePin(NamedTuple):
    repository: str
    commit: str
    path: str
    sha256: str
    definitions: tuple[str, ...]

    @property
    def url(self) -> str:
        return f"https://github.com/{self.repository}/blob/{self.commit}/{self.path}"

    def as_dict(self) -> dict[str, object]:
        return {"repository": self.repository, "commit": self.commit,
                "path": self.path, "sha256": self.sha256,
                "definitions": list(self.definitions), "url": self.url}


_A116_CELLS = SourcePin(
    "Saleh1967/Alghanem", ALGHANEM_COMMIT, "formal/a116/A116/Cells.lean",
    "3f4ec0187a22fab3f5ab013e6e62ef6678935983ef8c97c99c903ee08cadf65d",
    ("A116.Cell", "A116.Haraka.index", "A116.cells"))
_A116_NAMES = SourcePin(
    "Saleh1967/Alghanem", ALGHANEM_COMMIT,
    "suspended/src/alghanem/arabic/letter_fingerprint.py",
    "edd3285a0718df360e9d6d100b5a98d120a7e631079f66ef28410673f4da6b70",
    ("LETTER_VOCABULARY",))
_A116_NUMBERING = SourcePin(
    "Saleh1967/Alghanem", ALGHANEM_COMMIT, "formal/a116/A116/Numbering.lean",
    "264d6edea175da54a1df45f332e507b96264c24934fcc346735ae38f41d0fb0a",
    ("A116.Numbering.bridgeIndex", "A116.Numbering.atomNumber"))
_A116_BRIDGE = SourcePin(
    "Saleh1967/Alghanem", ALGHANEM_COMMIT, "gate/bridge.py",
    "6c182d2da2c26d932935b6306232745fac26e877ae9d7dcf32b321feea63fc8f",
    ("ALPHABET", "HARAKAT", "A116"))
_A116_CONTEXTUAL = SourcePin(
    "Saleh1967/Alghanem", ALGHANEM_COMMIT, "gate/contextual.py",
    "676d1a214b5412185100553ba1196121ffa1b4200a989b3706ec7f5d0ecda1a6",
    ("fold_atoms", "unfold_atoms"))
_DAL_CELL = SourcePin(
    "Saleh1967/Mashru", MASHRU_COMMIT, "Dal/Khaliya.lean",
    "135444500327955efb0f6338e71ec374ee92568b41b83c4a1470b385716a4840",
    ("Dal.n", "Dal.fakk"))
_DAL_NAMES = SourcePin(
    "Saleh1967/Mashru", MASHRU_COMMIT, "Dal/Makharij.lean",
    "ba9aa41ce1c57766d2c4bfbefbfb26aab5dab6136afce8e61baea567f1538690",
    ("Dal.hawamil", "Dal.HalaIsm.ila"))
_DAL_NUMBER = SourcePin(
    "Saleh1967/Mashru", MASHRU_COMMIT, "Dal/Adad.lean",
    "0a1959edc743ba6a126a7be128935e014507da7aec856388f4a67c8d0d6e1aa4",
    ("Dal.Adad.adad", "Dal.Adad.fakk"))
_SLGE_LADDER = SourcePin(
    "Saleh1967/Mashru", MASHRU_COMMIT, "SLGE/Ladder.lean",
    "982270fe8d83605a1bbf882f4ff974e608a86e3977f68b29325bf2881d013184",
    ("SLGE.cellEnc", "SLGE.cellDec", "declared carrier order"))
_SLGE_CORE = SourcePin(
    "Saleh1967/Mashru", MASHRU_COMMIT, "SLGE/Core.lean",
    "8fe9b3576d01c463944159158d56ed3a775a2bbb0453fb216e366f102e22f8e3",
    ("SLGE.encL (B := 116)", "SLGE.decL (B := 116)"))


class AlphabetSpec(NamedTuple):
    alphabet_id: str
    carriers: tuple[str, ...]
    marks: tuple[str, ...]
    sources: tuple[SourcePin, ...]
    description: str

    @property
    def size(self) -> int:
        return len(self.carriers) * len(self.marks)

    def as_dict(self) -> dict[str, object]:
        return {"alphabet_id": self.alphabet_id, "registry_version": REGISTRY_VERSION,
                "scope": ENCODING_ONLY, "carriers": list(self.carriers),
                "marks": list(self.marks), "size": self.size,
                "cell_domain": [0, self.size - 1], "description": self.description,
                "sources": [source.as_dict() for source in self.sources]}


_A116_CANONICAL_CARRIERS = tuple("ابتثجحخدذرزسشصضطظعغفقكلمنهويء")
_BRIDGE_CARRIERS = tuple("ءبتثجحخدذرزسشصضطظعغفقكلمنهويا")
_MAKHARIJ_CARRIERS = tuple("ءهاعحغخقكجشيضلنرطدتزسصظذثفبمو")

ALPHABET_REGISTRY: Mapping[str, AlphabetSpec] = MappingProxyType({
    ALPHABET_ID: AlphabetSpec(
        ALPHABET_ID, CARRIERS, HARAKAT, (), "NABT canonical cells; alif first, hamza last."),
    ALGHANEM_CANONICAL_ALPHABET_ID: AlphabetSpec(
        ALGHANEM_CANONICAL_ALPHABET_ID, _A116_CANONICAL_CARRIERS, HARAKAT,
        (_A116_CELLS, _A116_NAMES),
        "Alghanem A116.Cells enumeration, not Numbering.bridgeIndex."),
    ALGHANEM_BRIDGE_ALPHABET_ID: AlphabetSpec(
        ALGHANEM_BRIDGE_ALPHABET_ID, _BRIDGE_CARRIERS, HARAKAT,
        (_A116_NUMBERING, _A116_BRIDGE),
        "Alghanem bridgeIndex and gate.bridge.A116; hamza first, alif last."),
    MASHRU_ALPHABET_ID: AlphabetSpec(
        MASHRU_ALPHABET_ID, _MAKHARIJ_CARRIERS, HARAKAT, (_DAL_CELL, _DAL_NAMES),
        "Mashru Dal cells in its declared makharij carrier order."),
    SLGE_ALPHABET_ID: AlphabetSpec(
        SLGE_ALPHABET_ID, _MAKHARIJ_CARRIERS, HARAKAT, (_SLGE_LADDER,),
        "Mashru SLGE Ladder cellEnc, restricted to 29 carriers and four states."),
})

# Verify the installed declarations once. User material cannot extend them.
for _spec in ALPHABET_REGISTRY.values():
    if (_spec.size != 116 or len(set(_spec.carriers)) != 29
            or set(_spec.carriers) != set(CARRIERS) or _spec.marks != HARAKAT):
        raise RuntimeError("Malformed installed bridge alphabet")
del _spec


class CodecSpec(NamedTuple):
    codec_id: str
    alphabet_id: str
    kind: Literal["cells", "number", "bytes"]
    encoding: str
    description: str
    sources: tuple[SourcePin, ...] = ()
    origin: Literal["NABT", "upstream definition"] = "NABT"

    def as_dict(self) -> dict[str, object]:
        return {"codec_id": self.codec_id, "alphabet_id": self.alphabet_id,
                "registry_version": REGISTRY_VERSION, "scope": ENCODING_ONLY,
                "kind": self.kind, "encoding": self.encoding, "domain": "cell-sequence",
                "maximum_cells": MAX_CELLS, "description": self.description,
                "origin": self.origin,
                "sources": [source.as_dict() for source in self.sources]}


def _codec_registry() -> Mapping[str, CodecSpec]:
    items = [
        CodecSpec(NABT_NUMBER_CODEC, ALPHABET_ID, "number", "bijective116-big",
                  "NABT sequence address: sum((cell+1)*116**(length-1-position))."),
        CodecSpec(ALGHANEM_CANONICAL_NUMBER_CODEC, ALGHANEM_CANONICAL_ALPHABET_ID,
                  "number", "bijective116-big",
                  "NABT-defined number transport for the Alghanem canonical cell order."),
        CodecSpec(ALGHANEM_NUMBER_CODEC, ALGHANEM_BRIDGE_ALPHABET_ID,
                  "number", "bijective116-big", "Alghanem atomNumber / fold_atoms.",
                  (_A116_NUMBERING, _A116_CONTEXTUAL), "upstream definition"),
        CodecSpec(MASHRU_NUMBER_CODEC, MASHRU_ALPHABET_ID, "number", "bijective116-big",
                  "Mashru Dal.Adad.adad over in-domain cells.",
                  (_DAL_NUMBER,), "upstream definition"),
        CodecSpec(SLGE_NUMBER_CODEC, SLGE_ALPHABET_ID, "number", "bijective116-little",
                  "SLGE.Core.encL instantiated at radix 116; NOT Ladder.wordEnc or sylEnc.",
                  (_SLGE_CORE,), "upstream definition"),
        CodecSpec(NABT_FRAME_CODEC, ALPHABET_ID, "bytes", "frame7",
                  "NABT v1 count-prefixed frame; seven bits per cell; zero trailing padding."),
    ]
    for short, alphabet_id in (
        ("nabt", ALPHABET_ID),
        ("alghanem-canonical", ALGHANEM_CANONICAL_ALPHABET_ID),
        ("alghanem-bridge", ALGHANEM_BRIDGE_ALPHABET_ID),
        ("mashru-dal", MASHRU_ALPHABET_ID),
        ("mashru-slge", SLGE_ALPHABET_ID),
    ):
        cell_codec = NABT_CELLS_CODEC if short == "nabt" else f"nabt.cells.{short}.v1"
        items.extend((
            CodecSpec(cell_codec, alphabet_id, "cells", "cells",
                      "Explicit integer cell sequence in the named alphabet."),
            CodecSpec(f"nabt.u8.{short}.v1", alphabet_id, "bytes", "u8",
                      "NABT-defined transport: one byte 0..115 per cell, in sequence order."),
            CodecSpec(f"nabt.utf8-pairs.{short}.v1", alphabet_id, "bytes", "utf8-pairs",
                      "NABT-defined strict UTF-8 carrier/mark pairs; no normalization or BOM."),
        ))
    return MappingProxyType({item.codec_id: item for item in items})


CODEC_REGISTRY = _codec_registry()


def get_alphabet(alphabet_id: str) -> AlphabetSpec:
    if type(alphabet_id) is not str or alphabet_id not in ALPHABET_REGISTRY:
        raise NabtError("UNKNOWN_ALPHABET", "An explicit installed alphabet/version is required")
    return ALPHABET_REGISTRY[alphabet_id]


def get_codec(codec_id: str) -> CodecSpec:
    if type(codec_id) is not str or codec_id not in CODEC_REGISTRY:
        raise NabtError("UNKNOWN_CODEC", "An explicit installed codec/version is required")
    return CODEC_REGISTRY[codec_id]


def _kind(codec_id: str, expected: str) -> CodecSpec:
    spec = get_codec(codec_id)
    if spec.kind != expected:
        raise NabtError("CODEC_KIND_MISMATCH", f"This operation requires a {expected} codec")
    return spec


def cell_parts(cell: int, alphabet_id: str) -> tuple[str, str]:
    """The carrier and exact mark denoted by a cell in its named alphabet."""
    spec = get_alphabet(alphabet_id)
    index, mark = divmod(validate_cell(cell), 4)
    return spec.carriers[index], spec.marks[mark]


def convert_cell(cell: int, source_alphabet: str, target_alphabet: str) -> int:
    source, target = get_alphabet(source_alphabet), get_alphabet(target_alphabet)
    carrier, mark = divmod(validate_cell(cell), 4)
    return 4 * target.carriers.index(source.carriers[carrier]) + mark


def convert_cells(cells: Iterable[int], source_alphabet: str, target_alphabet: str) -> tuple[int, ...]:
    """Total permutation on in-domain cells, preserving order and multiplicity."""
    source, target = get_alphabet(source_alphabet), get_alphabet(target_alphabet)
    permutation = tuple(target.carriers.index(carrier) for carrier in source.carriers)
    return tuple(4 * permutation[cell // 4] + cell % 4 for cell in validate_cells(cells))


def render_cells(cells: Iterable[int], alphabet_id: str) -> str:
    spec = get_alphabet(alphabet_id)
    return "".join(spec.carriers[cell // 4] + spec.marks[cell % 4]
                   for cell in validate_cells(cells))


def encode_number(cells: Iterable[int], codec_id: str) -> int:
    spec = _kind(codec_id, "number")
    values = validate_cells(cells)
    return _encode_big(values[::-1] if spec.encoding == "bijective116-little" else values)


def decode_number(number: int, codec_id: str) -> tuple[int, ...]:
    spec = _kind(codec_id, "number")
    cells = _decode_big(number)
    return cells[::-1] if spec.encoding == "bijective116-little" else cells


def encode_bytes(cells: Iterable[int], codec_id: str) -> bytes:
    spec = _kind(codec_id, "bytes")
    values = validate_cells(cells)
    if spec.encoding == "frame7":
        return pack_cells(values)
    if spec.encoding == "u8":
        return bytes(values)
    if spec.encoding == "utf8-pairs":
        return render_cells(values, spec.alphabet_id).encode("utf-8", errors="strict")
    raise RuntimeError("Malformed installed byte codec")


def decode_bytes(data: bytes, codec_id: str) -> tuple[int, ...]:
    spec = _kind(codec_id, "bytes")
    if type(data) is not bytes:
        raise NabtError("INVALID_BYTES", "Encoded input must be bytes")
    if spec.encoding == "frame7":
        return unpack_cells(data)
    if spec.encoding == "u8":
        if len(data) > MAX_CELLS:
            raise resource_limit("Byte sequence exceeds the cell budget", maximum=MAX_CELLS)
        return validate_cells(tuple(data))
    if spec.encoding != "utf8-pairs":
        raise RuntimeError("Malformed installed byte codec")
    # Each installed carrier and mark is exactly two UTF-8 bytes.
    if len(data) > 4 * MAX_CELLS:
        raise resource_limit("UTF-8 cell sequence exceeds the budget", maximum=MAX_CELLS)
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise NabtError("INVALID_ENCODING", "Input is not strict UTF-8") from exc
    alphabet = get_alphabet(spec.alphabet_id)
    if len(text) % 2:
        raise NabtError("NON_CANONICAL_TEXT", "Expected exact carrier/mark pairs")
    cells = []
    for position in range(0, len(text), 2):
        carrier, mark = text[position:position + 2]
        if carrier not in alphabet.carriers or mark not in alphabet.marks:
            raise NabtError("NON_CANONICAL_TEXT", "Expected exact carrier/mark pairs",
                            details={"position": position})
        cells.append(4 * alphabet.carriers.index(carrier) + alphabet.marks.index(mark))
    return validate_cells(cells)


@dataclass(frozen=True, slots=True)
class BridgeResult:
    """A computation receipt, never a shape, word, semantic or source certificate."""

    source_codec: str
    target_codec: str
    source_cells: tuple[int, ...]
    target_cells: tuple[int, ...]
    value: int | bytes | tuple[int, ...]
    rendered: str

    @property
    def authority(self) -> str:
        return ENCODING_ONLY

    def as_dict(self) -> dict[str, object]:
        source, target = get_codec(self.source_codec), get_codec(self.target_codec)
        if target.kind == "number":
            # Bound decimal conversion; hexadecimal covers the full runtime domain.
            assert type(self.value) is int
            encoding = "decimal" if self.value.bit_length() <= 12000 else "hex"
            value = str(self.value) if encoding == "decimal" else hex(self.value)
        elif target.kind == "bytes":
            assert type(self.value) is bytes
            value, encoding = self.value.hex(), "hex"
        else:
            value, encoding = list(self.target_cells), "integer-cells"
        return {"scope": ENCODING_ONLY, "authority": ENCODING_ONLY,
                "registry_version": REGISTRY_VERSION,
                "source_codec": source.codec_id, "target_codec": target.codec_id,
                "source_alphabet": source.alphabet_id, "target_alphabet": target.alphabet_id,
                "domain": "cell-sequence", "cell_length": len(self.target_cells),
                "source_cells": list(self.source_cells), "target_cells": list(self.target_cells),
                "value": value, "value_encoding": encoding, "text": self.rendered}


def transcode(value: object, source_codec: str, target_codec: str) -> BridgeResult:
    """Decode, permute by exact identity, then encode with two explicit codecs.

    Success says only that the chosen codecs describe the same cell sequence.
    There is no inference of a codec from input, filename, magic, or plausibility.
    """
    source, target = get_codec(source_codec), get_codec(target_codec)
    if source.kind == "number":
        source_cells = decode_number(value, source.codec_id)
    elif source.kind == "bytes":
        source_cells = decode_bytes(value, source.codec_id)
    else:
        source_cells = validate_cells(value)
    target_cells = convert_cells(source_cells, source.alphabet_id, target.alphabet_id)
    if target.kind == "number":
        encoded = encode_number(target_cells, target.codec_id)
    elif target.kind == "bytes":
        encoded = encode_bytes(target_cells, target.codec_id)
    else:
        encoded = target_cells
    return BridgeResult(source.codec_id, target.codec_id, source_cells, target_cells,
                        encoded, render_cells(target_cells, target.alphabet_id))


def convert_number(number: int, source_codec: str, target_codec: str) -> BridgeResult:
    _kind(source_codec, "number")
    _kind(target_codec, "number")
    return transcode(number, source_codec, target_codec)


def convert_bytes(data: bytes, source_codec: str, target_codec: str) -> BridgeResult:
    _kind(source_codec, "bytes")
    _kind(target_codec, "bytes")
    return transcode(data, source_codec, target_codec)
