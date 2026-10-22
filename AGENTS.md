# Working on NABT

NABT is an independent repository. It has no runtime imports, symlinks,
submodules, credentials, writable state, or release dependency in another
experiment. Prior research is cited by immutable source references in
`docs/PROVENANCE.md`.

## Preserve the contract

- Keep raw source, cell identity, transition effect, and evidence distinct.
- Every public number has an alphabet/version/domain. Reject booleans where
  integers are required; reject malformed or noncanonical encodings.
- A generated sound shape is not automatically an attested word, root,
  syntactic analysis, meaning, or real-world judgment.
- Unknown, invalid input, linguistic rejection, and resource exhaustion are
  separate results. Do not convert exhausted search into a linguistic proof.
- New semantics or changes to the accepted language require a versioned law,
  a documented source/scope, and counterexample tests.
- Keep ambiguity and the information needed for exact source restoration.

## Proof and implementation

- `formal/` is the Lean specification. Use the pinned toolchain.
- No `sorry`, `admit`, custom axioms, `unsafe` proof bypass, or `native_decide`
  is allowed in the formal kernel. Do not hide extra assumptions in a theorem.
- Document a theorem's actual scope. Finite checks, Python tests, and general
  Lean theorems are different forms of evidence.
- Regenerate the transition table from Lean. Do not hand-edit its entries.
- Python proposes/computes and checks certificates against the installed law;
  a caller-provided manifest, hash, or status never grants authority.
- Tests must include independent oracles and boundary/counterexample cases;
  copying a production recurrence into a test is not sufficient evidence.

## Verification

Run `make test`, `make formal`, and `make conformance` for a kernel change.
Use `make benchmark` for performance evidence and record environment and scope.
Run `make check` before a release; record limitations in `docs/PROOF_STATUS.md`.
User authorization governs commits and publishing. Do not alter other repos.
