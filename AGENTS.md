# Working on NABT

NABT is an independent repository. It has no runtime imports, symlinks,
submodules, credentials, writable state, or release dependency in another
experiment. Prior research is cited by immutable source references in
`docs/PROVENANCE.md`.

## Sole supported external input/output boundary

Every new external client, expert agent, RAG, service, or application MUST enter
through `python -m tools.grammar_catalog gateway run --request PATH` and consume
only `nabt.io.result.v1` after `gateway verify` (or `gateway.accept_output`) with
its independently retained request. See `docs/IO_GATEWAY_V1_AR.md` and its
acceptance contract. Never publish a raw owner receipt as a NABT external answer.
Use `gateway catalog` for the derived proof/test map. `formal/theorems.json` and
the compiled reference selected by `integrations/current_proof_references.mk`
remain the only theorem authorities; do not create a competing theorem registry.

The `nabt` kernel CLI, other tool CLIs, Python owners and native executables are
internal developer/replay interfaces. Keep them for frozen evaluations and reuse;
they do not satisfy external admission. Add a fixed gateway adapter when an
external use needs another owner. No client-supplied executable, import path,
proof status, test status or license may determine admission. Preserve the owner's
full alternatives, DEFER/CONFLICT, source conditions and open obligations.
A family/test reference is not a test run or a theorem-to-runtime refinement proof.
This is an application integration boundary, not an OS sandbox against someone
who can import or alter the checkout. Do not claim otherwise.

For genus/property/disposition, masdar, grammatical and causal relation work,
reuse `relations.search/analyze` and `docs/RELATIONAL_RAG_V1_AR.md`.
Keep jamid/mushtaq separate from ontology types, subject from causal agent,
accompaniment from purpose, and succession from causation. Bind optional native
temporal/inference inputs to the original source; preserve open ontology bridges.

For occurrence-local literal/figurative use, reuse `usage_context` on the existing
`neural.graph`/`cognitive.orchestrate` routes and
`docs/USAGE_WITNESS_BRIDGE_V1_AR.md`. Keep `source_use_applications` separate from
world-grounded applications. Do not bypass lower orchestration gates, turn the
single authored identity alignment into a general equivalence proof, or infer
exclusion from a missing reading. Replay the original request after withdrawal.

For article citation acquisition, reuse the native v3 dispatch in the existing
unit agent and `docs/UNIT_ARTICLE_BRIDGE_V1_AR.md`. The prefix selects an owner;
only its complete source-backed reading grants representation. Keep citation
onset separate from connected speech and preserve first-owner failures.

`make check` now uses `GNUmakefile` to include the historical Makefile, current
catalogue checks and required native I/O tests. Do not use `make -f Makefile check`
as a substitute for that release gate. The latter is a historical partial gate.

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

For source-bound mantuq/mafhum and reversible transport, use the existing
`tools.mantuq_inference source/fold/unfold/verify-fold` path documented in
`docs/MANTUQ_SOURCE_FOLD_V1_AR.md`. Retain the complete native source answer,
both full and clean witnesses, and the independently supplied replay inputs.
Do not reassert a tainted derived premise as a clean fact. Unfolding is data
restoration; verification requires fresh native replay. The caller's role plan,
source truth, Arabic reading completeness and `CertifiedBridge` remain separate
obligations. Run the native `mantuq-inference` integration gate for this path.

For source-bound derivation/weak-law applications, reuse
`tools.recursive_bridge read-applications/verify-applications` and the existing
generation/classical owners through `tools.derivation_surface_bridge`.
See `docs/DERIVATION_SURFACE_V1_AR.md` and its preimplementation acceptance
contract. Keep supplied root/class/original-vowel hypotheses, exact occurrence
bindings, alternative derivations and the unchanged conditional receipt.
The medial-alif display projection is bounded and replay-tested; it does not
establish lexical attestation, sense identity or `CertifiedBridge` premises.
Do not route a transformed root through the direct-fill `_shape_reading` path.

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
