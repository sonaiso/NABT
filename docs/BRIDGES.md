# Explicit numerical bridges

The installed bridge registry is `nabt.source-bridges.v1`. Every conversion
has scope and authority **`ENCODING_ONLY`**. It preserves a sequence of exact
carrier/mark pairs. It does not assert a licensed shape, a word, a root,
attestation, meaning, syntax or a real-world judgment.

The runtime does not import an upstream repository. It uses immutable,
versioned declarations in `src/nabt/bridges.py`, with repository, commit,
file, SHA-256 and definition names for each consulted upstream source.

## Source pins and distinct orders

| Source | Exact commit | Definitions consulted |
| --- | --- | --- |
| Saleh1967/Alghanem | `9d8fa03a51f894416e0abaf3b6821c5ae6441dcd` | `formal/a116/A116/Cells.lean`, `Numbering.lean`, `gate/bridge.py`, `gate/contextual.py`, and the declared `LETTER_VOCABULARY` in `suspended/src/alghanem/arabic/letter_fingerprint.py` |
| Saleh1967/Mashru | `e4c801ffe9171dadedcc3aae23051ea0953ae361` | `Dal/Khaliya.lean`, `Dal/Makharij.lean`, `Dal/Adad.lean`, `SLGE/Core.lean`, `SLGE/Ladder.lean` |

The suspended Alghanem file supplies carrier names only. Its runtime,
normalization, source handling and linguistic claims are not adopted.

Every alphabet uses `4 * carrier_index + mark_index`, with mark order
fatha, damma, kasra, sukun (`َ`, `ُ`, `ِ`, `ْ`). Cell IDs are `0..115`.

| Alphabet ID | Carrier order |
| --- | --- |
| `nabt.a116.v1` | `ا ب ت ث ج ح خ د ذ ر ز س ش ص ض ط ظ ع غ ف ق ك ل م ن ه و ي ء` |
| `alghanem.a116.canonical.v1` | Same order as NABT, explicitly tied to `A116.Cells` |
| `alghanem.a116.bridge.v1` | `ء ب ت ث ج ح خ د ذ ر ز س ش ص ض ط ظ ع غ ف ق ك ل م ن ه و ي ا` |
| `mashru.dal.cells.v1` | `ء ه ا ع ح غ خ ق ك ج ش ي ض ل ن ر ط د ت ز س ص ظ ذ ث ف ب م و` |
| `mashru.slge.cells.v1` | Same declared carrier order as Mashru Dal, with its own source identity |

Alghanem's canonical enumeration and `Numbering.bridgeIndex` are different
registries. Exactly eight of their 116 cells differ: the four alif cells and
the four hamza cells. The conversion explicitly exchanges those rows.

Mashru's makharij order is a larger permutation. For example, `كَتَبَ` is
`(84, 8, 4)` in NABT and `(32, 72, 104)` in Mashru Dal. Their numeric addresses
are consequently different.

## Numeric codecs

Each number needs a codec ID in addition to its value. Bare names such as
`A116`, `SLGE` or `utf-8`, absent codec IDs, and unknown versions are rejected.

| Codec ID | Alphabet | Definition |
| --- | --- | --- |
| `nabt.bijective116.v1` | NABT | Big-endian bijective base 116 |
| `nabt.bijective116.alghanem-canonical.v1` | Alghanem canonical | NABT-defined big-endian transport for this alphabet |
| `alghanem.bridge.atom-number.v1` | Alghanem bridge | `Numbering.atomNumber` / `contextual.fold_atoms` |
| `mashru.dal.adad.v1` | Mashru Dal | `Dal.Adad.adad`, restricted to in-domain cells |
| `mashru.slge.encL116.v1` | Mashru SLGE cells | `SLGE.Core.encL` explicitly instantiated at radix 116 |

The first four codecs use

\[
F(d_0,\ldots,d_{n-1}) = \sum_{i=0}^{n-1}(d_i+1)116^{n-1-i}.
\]

SLGE `encL 116` uses

\[
L(d_0,\ldots,d_{n-1}) = \sum_{i=0}^{n-1}(d_i+1)116^i.
\]

It is little-endian with respect to the sequence: the first cell is least
significant. Conversion reverses numeric significance while preserving the
logical sequence and its rendering. SLGE `Ladder.wordEnc` uses radix 148944
over syllable IDs; it is not a cell-sequence codec and is not registered here.
Neither syllable rank nor word rank is silently interpreted as a cell number.

Zero encodes the empty sequence. Numbers `1..116` encode single cells.
This does not make a single cell a licensed word. For example, number `1`
means `اَ` in NABT but `ءَ` in Alghanem bridge order. The Alghanem-to-NABT
conversion of number `1` is `113`.

## Bytes and cell lists

The native `nabt.frame7.v1` codec retains the established NABT binary format:

1. Five magic/version bytes, `4e 41 42 54 01`.
2. An unsigned four-byte big-endian cell count.
3. Exactly seven bits per cell in sequence order, most significant bit first.
4. Zero padding to the end of the final byte.

The count must match the payload length exactly. Cell codes `116..127`,
truncation, extra bytes and nonzero padding are rejected. This frame is bound
to NABT's alphabet; it is not relabelled as an external format.

For each alphabet, the following additional **NABT-defined** transports are
available. They are explicitly labelled as local transports, not upstream
wire protocols:

| Suffix | Alphabet |
| --- | --- |
| `nabt` | `nabt.a116.v1` |
| `alghanem-canonical` | `alghanem.a116.canonical.v1` |
| `alghanem-bridge` | `alghanem.a116.bridge.v1` |
| `mashru-dal` | `mashru.dal.cells.v1` |
| `mashru-slge` | `mashru.slge.cells.v1` |

- `nabt.u8.<suffix>.v1`: one byte `0..115` per cell in logical sequence order.
- `nabt.utf8-pairs.<suffix>.v1`: strict UTF-8 of exact carrier/mark pairs.
- `nabt.cells.<suffix>.v1`: an integer cell sequence. The native NABT spelling
  of this ID is `nabt.cells.v1`.

UTF-8 pairs preserve the exact carriers and marks. They accept the empty
sequence, but do not trim, normalize Unicode, drop tatweel, expand shadda,
guess absent marks, strip a BOM, or fold hamza spellings. Unsupported input
is rejected. The bytes are interpreted only by the caller's named codec.

## Python interface

```python
from nabt.bridges import (
    ALGHANEM_NUMBER_CODEC, MASHRU_NUMBER_CODEC, NABT_NUMBER_CODEC,
    NABT_FRAME_CODEC, convert_number, transcode,
)

hamza = convert_number(1, ALGHANEM_NUMBER_CODEC, NABT_NUMBER_CODEC)
assert hamza.value == 113
assert hamza.rendered == "ءَ"
assert hamza.authority == "ENCODING_ONLY"

kataba = convert_number(452621, MASHRU_NUMBER_CODEC, NABT_NUMBER_CODEC)
assert kataba.value == 1144809
assert kataba.source_cells == (32, 72, 104)
assert kataba.target_cells == (84, 8, 4)
assert kataba.rendered == "كَتَبَ"

packet = transcode(452621, MASHRU_NUMBER_CODEC, NABT_FRAME_CODEC)
restored = transcode(packet.value, NABT_FRAME_CODEC, MASHRU_NUMBER_CODEC)
assert restored.value == 452621
```

`get_alphabet` and `get_codec` return immutable installed specifications.
`convert_cell` and `convert_cells` take explicit source and target alphabet
IDs. `encode_number`, `decode_number`, `encode_bytes` and `decode_bytes` take
an explicit codec ID and operate in that codec's alphabet.

`transcode` connects any two registered representations. Its `BridgeResult`
records source and target codec IDs, both cell sequences, target value and
common rendered text. `convert_number` and `convert_bytes` restrict both
ends to their respective representation kinds. `BridgeResult.as_dict()` is
JSON-safe: numbers are decimal strings, or hexadecimal beyond the bounded
decimal output budget; bytes are hexadecimal; cell sequences are lists.

Results are computation receipts, not authorization certificates. Consumers
must decode and validate original material using their own installed codec
and law. A user-constructed receipt cannot grant shape or semantic authority.

## Bounds and validation

All public cell and number inputs require actual integers. Booleans, floats,
negative numbers, and integers outside a cell's domain are rejected.
Sequences have a runtime maximum of 4096 cells, including when decoded from
numbers or bytes. Resource exhaustion is `RESOURCE_LIMIT` with status
`DEFER`, distinct from malformed input and linguistic rejection.

A bridge is total on in-domain cell sequences within that resource budget.
It intentionally converts numerically valid sequences such as `بْ` or
`كُاْ` even when NABT's selected sound-shape law rejects them. The bridge's
receipt remains `ENCODING_ONLY`; shape analysis is a separate computation.

## Evidence and scope

`formal/Nabt/Bridges.lean` checks the finite carrier tables against their
declared names, proves cell permutations and inverse conversion, and proves
preservation of carrier, mark, order, multiplicity, length and append for
arbitrary finite sequences. Numeric conversion has universal inverse,
composition, bijectivity and sequence-preservation theorems over `Nat`.
The eight-cell Alghanem discrepancy and differing Mashru/NABT `كَتَبَ`
addresses are explicit checked witnesses.

These proofs are local to NABT and use its existing sequence-code proofs.
No upstream theorem is loaded as an assumption. The byte parsers, strict
Python type boundary and resource limits are runtime properties covered by
tests, not represented as Lean byte-parsing theorems.

`tests/test_bridges.py` independently declares the spellings and uses a
positional-sum encoder and fixed-length-interval decoder. It exhausts all
116 cells in all 25 alphabet pairs, all 13,573 addresses of lengths zero
through two for each of the five numeric codecs, and every pair of the 21
registered representations on an alif/hamza-containing sequence. It also
checks longer sequences, repeats, all reserved byte values, frame padding,
malformed UTF-8, unsupported source spellings, wrong kinds, unknown codecs,
maximum-size sequences and resource-exhaustion status.
