# Executable explanation contracts on the existing pilot

## Scope and decision

This batch extends `tools/explainable_pilot.py`, `answer`, and `verify`.
It does not install another parser, inference engine, theorem manifest,
knowledge rank, source catalogue, or external-world observer. The input law
remains `nabt.verified-ground-reading.v1`, checked by the existing native
`verifiedReading` executable. Its exact ground clauses, explicit negation,
complete full closure, and conflict-clean closure remain authoritative.

The proposed method separates four obligations. The pilot can check a narrow
instance of reading fidelity and inference validity now. It can expose source
premises and exact ground application, but cannot authenticate those premises
or identify/measure the corresponding external case. The explanation must
retain this asymmetry instead of assigning one overall confidence number.

## Preimplementation acceptance

The independent authored matrix is
`evidence/explanation_contracts_v1/acceptance_cases.json`, SHA-256
`e5bdc1e1707ca5f610f56ac2e4e3f6af6c2f54f4e7f02842c1b6161d606f0b6a`.
Its nine canonical source/query cases and six boundary obligations precede
implementation. They are public engineering controls, not a blind Arabic
benchmark. Keep the file and the first observations unchanged.

`baseline_answer_v1.json` in that directory was emitted by the old renderer
with the current native checker before the implementation. Its SHA-256 is
`a1f9c0d84a68bf36e15bcb1e9e0eab77b0a077c74a52965052d5319f25d19cb3`.
This is a new baseline; it does not replace the older pilot evidence or its
different executable identity.

## Versioned output and replay

The default answer becomes `nabt.explainable-answer.v2`. It preserves the
existing binding, answer, analysis certificate, native receipt, and limits,
and adds `explanation` with schema `nabt.explanation-contract.v1`.
`answer_version="v1"` retains the previous wire shape. `verify` accepts only
the two installed schemas, rebuilds the corresponding fixed version from
independently supplied source/query/binding/checker, and compares the entire
canonical JSON. An explicitly requested answer version must agree with the
bundle; callers requiring v2 can reject a downgrade. A legacy replay never
claims that a v2 explanation was checked.

Explanation generation happens only after native acceptance. A separate
helper may organize display code, but must not parse, saturate rules, run a
second source-to-meaning conversion, or authorize a result independently.

## Four axes

| Axis | What this batch may report | What remains unestablished |
| --- | --- | --- |
| `reading_fidelity` | Exact canonical source/query reading under the native law | Free Arabic, speaker intention, complete contextual readings |
| `premise_support` | Exact source clauses and retained derivation witnesses | Truth, authenticity, and independence of external premises |
| `inference_validity` | Both checked closures and their query-relative polarities | A new proof of the Python explanation renderer |
| `case_applicability` | Exact predicate, ordered arguments, polarity and bound source scope | External referent, measurement, time/unit validity, normative application |

Source identity is an input binding, not authenticated authorship. An inferred
negative answer is relative to the signed question. Missing support is not
negative support. Neither textual support nor a successful replay grants
action permission.

## Operations, conditions and blockers

Each operation references its existing `cN` source clause and UTF-8 span.
A fact records a source premise. A rule records its original ordered body
and head. Each required premise references its full/clean witness, if any,
and an opposite witness, if any. Distinct source occurrences stay distinct.

Both signs of a contested atom must remain visible. A clause is excluded
from the clean program exactly when its fact, head, or body is contested,
under the existing `VerifiedReading.clean` contract. The explanation also
records actual full/clean trace steps using that clause. A rule whose body
is derivable need not appear in a particular retained proof trace; do not
confuse applicability with actual selected proof use.

All of these diagnostics are projections of accepted clauses, known atoms,
and trace edges. They do not compute a new closure. The output must preserve
the distinction between alternatives across rules and conjunction within a
rule. A bounded backwards traversal of clause syntax may identify relevant
clauses, terminating on already visited atoms. Cycles without a derived seed
do not supply support.

## Residuals and revision

For the question and its opposite, retain the full/clean roots, candidate
clauses, missing antecedents, and conflict exclusions. A local missing
antecedent means it is absent from the checked closure; it is not a claim
that adding it is the only, smallest, sufficient, or legitimate repair.
All matching rule alternatives must stay distinguishable.

Dependency reports traverse existing proof DAG edges. They describe the
retained witness, not every proof, a minimal proof, or a premise necessary
for the conclusion in every derivation. A change to source/query bytes,
identity, revision, scope or the configured checker requires replay.
Changing a witness clause may affect a result, but an alternative proof may
preserve it. Never promise a counterfactual verdict without rerunning it.

## Native protocol boundary

Before building an explanation, success receipts must have the installed
shape and genuine Boolean polarity fields. Their four polarity values must
agree with membership in the accepted full/clean certificate closures, and
their status must agree with the existing `SemanticInference.classify`
contract. A discrepancy is `CHECKER_PROTOCOL_ERROR`, not an epistemic
`UNKNOWN` or a negative answer. This consistency check does not replace
native proof checking or authenticate an arbitrary configured executable.

## Existing foundations and remaining bridges

The reused declarations include `VerifiedReading.verified_source_exact`,
`reading_unique`, `checked_closure_exact`, `execution_exact`, and
`source_to_execution_entails`, with `SemanticInference.model_sound` retaining
its explicit `factsTrue` and `rulesPreserve` premises. The current compiled
proof catalogue remains the only proof-identity authority.

The classical operator/source registries, RationalInquiry, EpistemicMeasurement,
EvidenceLifecycleV1, the progressive licensed algebra, the owner's recursive
algebra, and MeaningPreservation remain existing capabilities. This batch
does not pretend to call them merely by referring to their concepts. In
particular, a book passage is not attached to a ground rule without an
established source-to-operation bridge. Full `CertifiedBridge` realization,
independent premise acquisition, physical case matching, and faithful free
Arabic interpretation remain separate work with their existing contracts.

## Verification and permanent integration

Keep the native-required pilot conformance gate and run the new acceptance
tests there and in the existing formal CI job. Python-only discovery may
skip absent native executables; the dedicated gate must fail if absent.
Run existing pilot/ground-reader tests and the existing pilot evaluator,
then report the old and new denominators separately. Extend the existing
capability reuse metadata with the helper, specification and tests. Do not
edit prior freezes, proof references or first-run measurements.
