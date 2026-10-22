# Provenance and scope

NABT was created at the owner's request as a standalone implementation. It
does not import or mutate the previous experiments. References below identify
the research definitions consulted, not runtime dependencies.

| Source | Immutable reference | Reused idea |
| --- | --- | --- |
| Mashru SLGE | `df6bcc9eb9b536db3684cc8a2eb773c2c9f01136` | 97-state sound-shape law; contextual weight; bounded count and ordering |
| Alghanem official branch | `cb3947719edb41cff1cad213ce2585fefe09ae5a` | A116 carrier/state identity; operation-preservation contracts; source/rank separation |
| alghanem-constitution | `f75a43b9f4ed3df059f1feb832f48d96e6f846ba` | Residual restoration and conditional composition boundaries |

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

The earlier 42-state Alghanem acceptance law is not silently equated to the
97-state law. In particular, NABT's selected law rejects mismatching alif
closures such as `كُاْ`. Higher-language claims remain open until their own
source-backed operations and certificates are implemented.
