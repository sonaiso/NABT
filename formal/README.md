# NABT formal kernel

This is a self-contained Lean 4.34.1 project. It uses the Lean distribution and
`Std`, with no Mathlib, old repository checkout, network service, or imported
project axioms. The public interface is the canonical 116-cell alphabet;
accepted strings are licensed by a declared sound-shape model.

## Reproduce the checks

```sh
lake build Nabt exportTable
lake env lean Audit.lean
lake exe exportTable > generated/law.json
```

The default `lake build` also builds both the complete library and the table
exporter. `Audit.lean` checks that every entry in its declaration manifest is an
actual compiled theorem, collects its transitive axioms, and fails on an axiom
outside `propext`, `Classical.choice`, and `Quot.sound`. It additionally checks
every compiled declaration whose name starts with `Nabt.`. The successful
initial audit observed exactly those three standard foundational axioms.
`theorems.json` is the human/tool-readable manifest; the Lean audit enforces
the corresponding declaration list.

## What the theorems establish

| Module | Proven scope |
| --- | --- |
| `Nabt.Cell` | `Fin 29 × Fin 4` and `Fin 116` are inverse representations; an occurrence slot number preserves its position and cell; distinct sources cannot be identified as one occurrence. |
| `Nabt.Sequence` | The bijective base-116 sequence address is a bijection with `Nat`, with both inverses proved. Concatenation satisfies `F(u ++ v) = 116^length(v) * F(u) + F(v)`, and appending a cell satisfies `F(u ++ [a]) = 116*F(u) + a + 1`. |
| `Nabt.Transition` | State transitions and costs compose on paths; state/weight effects form an associative composition with identities. String concatenation preserves this composition. |
| `Nabt.Count` | The recursive count equals the length of a separate specification that enumerates all bounded strings and then filters by weight and final state. The specification is sound, complete within its explicit bound, and duplicate-free for a duplicate-free alphabet. Reference ranking and unranking are inverses; ranks are below the count. |
| `Nabt.Law` | The external-to-SLGE alphabet permutation is invertible and preserves marks. All 97×116 transitions stay inside the state space. The dead state is absorbing. The local potential inequality holds for every live transition, yielding a general bound on accepted suffix length. Specific correct/incorrect alif cases are checked. |
| `Nabt.BoundedLaw` | The bound `3*w + pot(q)` covers **every** licensed string of weight `w` from a live state `q`. The resulting enumeration is exact and duplicate-free, and the count is its cardinality. Zero-cost licensed suffixes are included. |
| `Nabt.Acquisition`, `Nabt.LearnedModel` | Conditional transition-model preservation for all finite sequences, and kernel verification of the specific acquired bit-decision procedure against every primitive transition. |
| `Nabt.Bridges` | Invertible carrier/mark permutations and sequence/number bridges across the declared Alghanem, Mashru and NABT codecs; explicit little-endian versus big-endian distinction. |
| `Nabt.RuleLearning` | Version-space elimination, retention of consistent hypotheses, conditional consensus and progress after distinguishing observations. |
| `Nabt.PropertyEvidence` | Exact replay bindings and readiness, unknown versus false, conflict precedence and per-bit numeric projection of required evidence. |
| `Nabt.Obligations` | Named identity isolation, monotonic positive formulas, inclusion-minimal completion families, soundness/completeness, no-completion characterization and conflict-before-projection. |
| `Nabt.Program` | Instruction-number identity and list assembly roundtrip, compositional domain transitions and typing of compiler forms. Operand decoding and Python refinement are not claimed. |

These are theorem statements about specified mathematical objects. The
manifest count includes supporting lemmas and regression witnesses; it is not
a score for linguistic coverage or intelligence.

## Declared alphabet and law

The canonical carrier order is:

`ا ب ت ث ج ح خ د ذ ر ز س ش ص ض ط ظ ع غ ف ق ك ل م ن ه و ي ء`

The mark order is fatha, damma, kasra, sukun. A cell is `4*carrier + mark`.
`Nabt.Law` explicitly permutes that representation into the source SLGE
carrier order. The public word alphabet is `Fin 116`; it does not contain the
source law's boundary symbol 116. Wasl and waqf use distinct final-state sets.

The transition design was adapted from `Saleh1967/Mashru`, commit
`df6bcc9eb9b536db3684cc8a2eb773c2c9f01136`, file `SLGE/Law.lean`.
The old source is provenance, not a build/runtime dependency. NABT's canonical
permutation and exported interface are explicit local definitions.

The model version is `nabt-sound-shape-v1`; its alphabet version is
`nabt.a116.v1`. Its grouping and transition choices remain declared model
assumptions. Proving closure, counting, and invertibility does not establish
that those choices characterize every Arabic utterance, nor that an accepted
shape is an attested word, triliteral/quadriliteral root, grammatical role, or
meaning. Those require additional licensed evidence and typed layers.

## Export and trust boundary

`ExportTable.lean` emits JSON from the actual compiled definitions of the
state transition, weight, potential, and final predicates. It contains all
97×116 transition/weight pairs, 97 potential values, and both final-state
sets. The initial generated file is 77,563 bytes including its final LF, with
SHA-256:

`14e32ae208ac5ed2f754e83506e72133d0962756ef0c944d12370746febddcdd`

That hash is a byte-integrity measurement, not a Lean cryptography theorem.
Python loads the same exported table under a pinned digest; the repository's
conformance gate rebuilds Lean, regenerates the table, and compares it.

## Explicit implementation proof debts

1. The optimized Python dynamic program and rank/unrank routines are checked
   against independent oracles and the exported tables. They are not extracted
   from Lean, and no theorem currently identifies their execution with the
   reference functions in `Nabt.Count`.
2. Python UTF-8 parsing, Unicode policy, certificate parsing, SHA-256 checking,
   and binary wire serialization have executable checks and tests, not Lean
   proofs in this kernel.
3. The sound-shape law does not prove source attestation, root membership,
   morphology, syntax, semantic reference, or inference licensing. Those
   capabilities must not be inferred from a successful shape certificate.
4. The computational soundness of the Lean toolchain, code generation, host
   environment, and JSON transfer remains part of the trusted computing base.
   The finite proof checks use kernel reduction rather than `native_decide`;
   the axiom audit forbids `sorryAx` and project-specific assumptions.
