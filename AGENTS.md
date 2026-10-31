# Working on NABT

NABT is an independent repository. It has no runtime imports, symlinks,
submodules, credentials, writable state, or release dependency in another
experiment. Prior research is cited by immutable source references in
`docs/PROVENANCE.md`.

## Start from the installed capabilities

Before proposing or implementing a new representation, reader, inference path,
or orchestration layer:

1. Read `docs/NABT_FOUNDATION_REUSE_AR.md` and the relevant sections of
   `docs/PROGRESSIVE_UNITS.md`. A116, reusable transition effects, progressive
   licensed units, and the owner's recursive algebra are existing foundations.
2. Run `python -m tools.entropy_framework reuse`, then select the relevant
   module or family. This command derives declarations from the current
   compiled catalogue selected by `integrations/current_proof_references.mk`;
   it is not a second theorem registry or a grant of semantic authority.
   For rule, concept or policy work, also run
   `python -m tools.entropy_framework reuse --organization --summary` and read
   `docs/NABT_RULE_POLICY_ORGANIZATION_AR.md`. Keep formation, adoption,
   application and revision contracts separate from evidence that those events
   occurred. Unmapped catalogue records remain available; a resolved reference
   does not authorize an inference, external-world claim or action.
   For conditional operator routing, consult `docs/OPERATOR_CONTEXT_V1_AR.md`:
   source scope, blockers and diagnostics belong beside the unchanged receipt.
   Recheck v2 reports against the external query, complete frame mapping and
   requested budget. Legacy v1 output is not an original-request certificate;
   source diagnostics are not application premises or universal rejections.
3. Inspect the existing implementation, input premises, native checker, replay
   entry point, counterexamples, and recorded open bridge obligations. Extend
   that path when it meets the task. Explain a concrete unmet obligation before
   introducing another implementation of the same operation.
4. Exercise the existing entry point on the task's actual inputs. Keep static
   references, available executables, successful process execution, and checked
   semantic results distinct. Do not turn an unmapped consumer into a claim
   that a theorem has no executable use, or an executable into a claim that
   the default reader consumes it.
5. Update the existing reuse metadata and its discovered tests when adding or
   moving a formal module, consumer, or entry point. Record which installed
   contracts and consumers the change reuses, the verification performed, and
   any remaining bridge obligation in the change description or task record.

The complete theorem manifest remains `formal/theorems.json`; compiled proof
identity remains the existing proof catalogue. Data-only modules, preservation
theorems, impossibility/counterexample theorems, and executable checkers have
different roles. A source-reconstruction tree does not discharge
`RecursiveSourceBridge.CertifiedBridge` without its actual grammar, host,
premise, and realization obligations. Consult
`docs/NABT_CAPABILITY_REUSE_AR.md` for the maintained operational workflow.

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
