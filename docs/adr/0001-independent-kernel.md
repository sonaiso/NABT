# ADR 0001 — Independent, versioned kernel

Status: accepted for the foundation implementation.

## Decision

NABT is a new repository, not a branch, fork dependency, submodule, or wrapper
around another experiment. It adopts a pinned, explicitly scoped sound-shape
law from the prior SLGE research and independently defines its codec,
operation contracts, implementation, tests, and release gates.

The first release proves and implements the numeric/transition foundation.
It does not promote a generated shape to an attested lexical, morphological,
syntactic, semantic, or factual judgment.

Canonical cells use 29 carriers in A116 order and four states ordered fatha,
damma, kasra, sukun. The adapter to SLGE's place-ordered alphabet is explicit.
Word mode has 116 symbols; a sentence-boundary symbol is not silently admitted.

The runtime ships the finite table exported by Lean and refuses caller-supplied
replacement laws. Formal proofs, checked finite tables, Python conformance
tests, and benchmark measurements are recorded separately.

## Consequences

- Development and runtime are isolated from earlier repositories.
- Linguistic-law changes create a new law version and reviewed migration.
- Additional source profiles and higher functions can be added through typed
  certificates without changing the numeric meaning of existing artifacts.
- The four-shape foundation parser remains narrow and explicit until licensed
  spelling/phonology transformations with exact restoration are implemented.
