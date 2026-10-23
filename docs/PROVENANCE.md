# Provenance and scope

NABT was created at the owner's request as a standalone implementation. It
does not import or mutate the previous experiments. References below identify
the research definitions consulted, not runtime dependencies.

| Source | Immutable reference | Reused idea |
| --- | --- | --- |
| Mashru SLGE | `df6bcc9eb9b536db3684cc8a2eb773c2c9f01136` | 97-state sound-shape law; contextual weight; bounded count and ordering |
| Alghanem official branch | `cb3947719edb41cff1cad213ce2585fefe09ae5a` | A116 carrier/state identity; operation-preservation contracts; source/rank separation |
| alghanem-constitution | `f75a43b9f4ed3df059f1feb832f48d96e6f846ba` | Residual restoration and conditional composition boundaries |
| sonaiso/Taaqol-GPT | `91dad107a7d56e6e05cce4ab54c3d63e5bdf5482` | Identity, bounded operation authority, visible residuals, alternative retention, replay at consumption; audited design input only |

Primary definitions:

- https://github.com/Saleh1967/Mashru/blob/df6bcc9eb9b536db3684cc8a2eb773c2c9f01136/SLGE/Law.lean
- https://github.com/Saleh1967/Mashru/blob/df6bcc9eb9b536db3684cc8a2eb773c2c9f01136/SLGE/Count.lean
- https://github.com/Saleh1967/Alghanem/blob/cb3947719edb41cff1cad213ce2585fefe09ae5a/formal/a116/A116/Cells.lean
- https://github.com/Saleh1967/Alghanem/blob/cb3947719edb41cff1cad213ce2585fefe09ae5a/formal/a116/A116/AmaliyyaHafiza.lean

The SLGE place-conflict rule is part of the selected declared model. Formal
correctness relative to this law does not establish that it captures all
attested Arabic or every reading tradition. NABT exposes the law identity in
every result so that source-adequacy work can revise the model transparently.

The symbolic carriers represent a declared Arabic inventory, not a learned
classifier over recorded acoustic waveforms. Sukun is a state, not a fourth
short vowel. Carrier count, cell length, consonant weight, and root arity are
different quantities.

The Taaqol audit and native NABT foundation are documented in
`docs/TAAQOL_FOUNDATION.md` and `evidence/taaqol-audit.md`. No Taaqol runtime,
stage registry, evidence-rank threshold, or integration dependency was imported.
The bit-decision learner and symbolic forest are new native implementations.
The learned procedure preserves the existing law; this provenance reference
does not authorize new linguistic rules or new semantic claims.

The earlier 42-state Alghanem acceptance law is not silently equated to the
97-state law. In particular, NABT's selected law rejects mismatching alif
closures such as `كُاْ`. Higher-language claims remain open until their own
source-backed operations and certificates are implemented.

## Integrated development `0.3.0a1`

The expanded pinned reuse matrix is in [INTEGRATION.md](INTEGRATION.md).
Current bridge definitions were read at Mashru
`e4c801ffe9171dadedcc3aae23051ea0953ae361` and Alghanem
`9d8fa03a51f894416e0abaf3b6821c5ae6441dcd`. Their exact consulted file hashes
are embedded in `src/nabt/bridges.py`; these newer bridge references do not
silently replace the historical sound-law pin above.

The native source-learning modules adapt Qeyas commit
`0ac045125f3d4ed9a984ab2f78a787fe9d014cd9`, including the finite learner at
`6af5840128f685e45ed5ae1070e606303985fb9a`. This is an explicitly selected
review branch, not a claim that the Qeyas work was already merged to main.
The original MIT notice is retained in `NOTICE.md`, and the OpenITI source
fixtures retain their separate data license and exact full-book bytes.

`tools/catalog_upstream.py` can regenerate the textual theorem inventory
from an explicit map of nine pinned local snapshots. The checked-in inventory
contains 4,231 named declaration occurrences, including copies and historical
modules; it does not certify them as 4,231 independent mathematical results.
It performs no kernel build and grants no runtime authority. The actual local
proof manifest and its axiom audit remain separate.

## Text evidence development `0.9.0a1`

GitHub main heads were checked on 2026-10-23 and still match the Mashru
`e4c801ffe9171dadedcc3aae23051ea0953ae361` and Alghanem
`9d8fa03a51f894416e0abaf3b6821c5ae6441dcd` source pins. Selected Lean
declarations were reread; the upstream projects were not rebuilt. The audit
of building, inflection, diptotes and nominal genus/quality remains in
`MORPHOLOGY_SOURCE_AUDIT.md`; its limitations are retained in `TEXT_MORPHOLOGY.md`.

The native `Nabt.TextEvidence` algebra uses identity-bound, externally
activated cue receipts. Its generated finite table is checked against the
Python functions. The new text reader reuses exact source windows from the
installed word/morphology policies, but uses **zero content-word answer
entries**. Ten closed functional-marker spellings remain authored applications
of source-attested grammar; they are not claimed as autonomously learned.

Optional lexical descriptions are read from separate caller-supplied bytes,
not from a per-token answer argument. Exact spelling establishes a candidate
link, not exhaustive sense identification. Contextual al/idafa properties are
excluded from transfer. The semantic jamid/mushtaq axis remains distinct from
etymological derivation and frozen/conjugating verbs. The new independent
material, first run, later review findings and runtime snapshots are retained
under `evidence/text_morphology/`; earlier evidence and gold remain unchanged.
