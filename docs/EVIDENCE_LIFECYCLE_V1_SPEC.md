# Evidence lifecycle v1: source-bound replay, not world authentication

Status: specification for a new additive law, before implementation. Baseline:
`c2c072e17802b62c13109cee7c087b7b58895a1a` (merged PR58).

The next executable slice of T06/T15/T16 reuses `RationalInquiry.Source` and
`EpistemicMeasurement` rather than changing their historical laws. It adds
source bindings to the declared origin graph, a checked acyclic order, source
withdrawal/reactivation/replacement, and receipts bound to the complete episode.
T11 source preparation proceeds separately. This is not completion of T06's
general candidate regeneration, G2/G3/G4, N6-b, or the 300-loop roadmap goal.

## Authority and compatibility

The new law ID is `nabt.evidence-lifecycle.v1`. The source, key, origin, evidence,
query, polarity and four-way observation classification are the existing types.
The source value contains identity, revision and content, not a caller-provided
trust flag. The authored profile checks a supplied conditional scenario. It does
not authenticate those premises, recover undeclared copying, or establish a
physical observation, a referent, an intention, or statistical independence.

The original EM law accepts closed cycles away from the query. This extension
requires an acyclic declared graph and does not retroactively reinterpret v1.
The all-parents-active rule also matches the lineage policy already implemented
inside `src/nabt/rational_inquiry.py`; the new formal bridge reuses the complete
`RationalInquiry.Source` value through EM, not its unrelated numeric-revision
Python wire format. Historical `src/`, gold, laws and result archives remain.

## Source-bound context

An `OriginBinding` contains `origin_id`, the existing complete `source`, and
a nonnegative integer `rank`. A `SourceBoundContext` contains the existing EM context plus
these bindings. Each origin, including the query origin, has exactly one binding.
No binding may name an unknown origin. Every parent exists and has a smaller
rank than its child. Origin IDs and evidence IDs are unique; active source
identities are unique. Across the complete episode, a source identity/revision
pair cannot name two different contents. Different revisions may coexist in
the historical registry, but only one revision per identity is active.
Parent lists and ancestry lists contain unique known origin IDs. Unknown query
or evidence origins, missing bindings, extra bindings, duplicate list entries,
negative ranks, and non-integer ranks are invalid input. A source need not be
active to occur in the retained binding or interpretation inventory.

The extra dependency readiness predicate on an evidence row requires:

1. Its origin's binding has exactly the same complete source value.
2. Its ancestry contains its origin and is closed under all declared parents.
3. Every member of that ancestry has a binding whose complete source is active.

An ancestry over-set may conservatively suspend an otherwise usable row; this
law does not infer missing real-world ancestry. Query-origin exclusion, exact
key matching and allowed evidence kind remain EM's separate conditions.
Dependency readiness alone never licenses an observation or linguistic reading.

For a valid context with sufficient budget, filter the original interpretation
ledger by this predicate and call the original EM receipt function. Count the
budget against the original ledger BEFORE filtering at every episode step.
Suspending rows cannot turn an exhausted request into a complete search.
The receipt selected IDs must therefore refine the original EM admissibility
relation, while also requiring every declared source ancestor to remain active.

## Episode wire contract

The authored episode has exactly these fields:

```text
schema: "nabt.evidence-lifecycle.episode.v1"
episode_id: nonempty string
query: existing EM Query
active_sources: list of existing complete Source values
origins: list of existing Origin values
interpretations: list of existing Evidence values
bindings: [{origin_id, source, rank}]
budget: nonnegative integer
updates: [{event_id, kind, source, replacement, reason}]
```

Update kinds are `withdraw`, `activate`, and `replace`. `replacement` is null
except for `replace`. Each event ID is unique, with a nonempty reason. Events
are ordered by their position, never by a caller-supplied completion flag.

- `withdraw` removes the exact source value from the active list. Withdrawing
  a registered but already inactive version is an explicit idempotent no-op.
- `activate` appends an exact registered inactive source. Activating an already
  active exact value is a no-op; activating a different revision while the same
  identity is active is invalid and must use `replace`.
- `replace` requires its exact old source to be active, the same identity in
  the replacement, and a different revision. It removes the old value and
  appends the replacement. Old bindings and interpretations are NOT rewritten.
- A withdraw/activate target must already occur in the initial source/binding/
  interpretation inventory or as a preceding replacement. A future event cannot
  retrospectively make an earlier unknown target valid.

Validate the whole episode and all transitions before issuing any result.
Malformed JSON, duplicate decoded keys, bad graph, an invalid update or an
identity/revision content collision yields `INVALID_INPUT`, without an accepted
partial history. An outer transport limit yields `RESOURCE_LIMIT`.

Initial step 0 and every subsequent step retain the active complete source
values. Each step reports:

```text
step, event_id (null at 0), active_sources,
receipt: existing EM {status, support_ids, refutation_ids, selected_ids},
dependency_ready_ids, dependency_blocked_ids, affected_ids
```

Diagnostic ID lists preserve the original interpretation order. `affected_ids`
is the symmetric difference of dependency readiness with the previous step;
step 0 has an empty list. It is not a claim that only those final verdicts can
change. With insufficient ledger budget, the EM receipt is RESOURCE_LIMIT with
empty witness lists, and all three diagnostic lists are null, not empty counts.

The native result carries its law ID, the complete canonical episode binding,
and the exact step list. The Python adapter independently computes a proposal,
compares the whole typed native output, and rejects disagreement. A caller's
status, digest, or snapshot label is never sufficient. Receipt verification
replays the separately supplied current episode and compares the entire result.
An older episode receipt is not current even if its final witness IDs or active
source set happen to match. It can still verify against its historical episode.
Here "current" means the expected episode supplied independently by the verifier,
not a claim that the caller possesses the world's latest state. The expected
episode must never be taken from the receipt being verified.

The successful native envelope has exactly `law_id`, `binding`, `steps`,
`world_truth_established`, `source_authenticity_established`,
`referents_established`, and `all_arabic_complete`; the final four are false.
`binding` is the entire validated episode, not its digest. An error envelope
instead has `law_id`, `status`, `reason`, and the same four false flags, without
partial steps or binding. Event IDs are retained in the corresponding step.

The bounded v1 interface accepts at most 64 origins/bindings, 64 active
sources, 64 interpretations, 16 updates, and rank/budget at most 64. Source
content is at most 16 KiB; identifiers are at most 4096 UTF-8 bytes, episode and
event IDs at most 128 bytes. The active-source cap applies at every step;
exceeding it yields RESOURCE_LIMIT for the episode, not a partial accepted history.
The request limit is 1 MiB, report limit 8 MiB,
JSON nesting limit 32. Integers are exact, booleans are not integers, time keeps
EM's canonical signed decimal-string bound. No silent normalization occurs.
Each parents/ancestry list contains at most 64 entries; reasons contain at most
4096 UTF-8 bytes. Exact-field checks apply to every nested object. Known ancestry
that omits a required ancestor is a dependency failure, not malformed input.
Exceeding any collection, rank, budget, byte, nesting or report cap is
`RESOURCE_LIMIT`; malformed types, negative numbers where naturals are required,
bad enum values, duplicate IDs/keys and invalid source transitions are
`INVALID_INPUT`. Nonempty identity strings reject ASCII control characters;
raw source content may contain newlines. JSON floats/noncanonical numbers and
unpaired surrogates are invalid input; excessive integer digit budget is a
resource limit. The generic integer parser permits at most 16 decimal digits
(excluding the minus sign), and exact magnitude at most 2^53-1.
Missing native verification is `UNMEASURED`; timeout or native disagreement is
reported explicitly and cannot produce an accepted current receipt.

The additive Python API is `evaluate_episode(episode)`,
`propose_episode(episode)` (explicitly untrusted), and
`verify_episode(report, *, expected_episode)`. The evaluated report has schema
`nabt.evidence-lifecycle.result.v1`, `law_id`, `status`, `native_checked`,
`decision_complete`, `evidence_class="AUTHORED_SCENARIO"`, `observed`,
`execution`, and the four false authority flags above. `observed` is the complete
checked native envelope, or null if it was not checked. `execution` retains the
validated input, proposal, actual native result, measured code/native/input
identities and any error. Unvalidated arbitrary objects are not echoed as input.
For a checked episode, `status` is the final step's receipt status and
`decision_complete` is false on RESOURCE_LIMIT. This completion is relative to
the supplied ledger; UNKNOWN and CONFLICT are complete, distinct outcomes.

Verification reports `replay_matches` separately from `valid`: valid requires
an exact fresh replay, successful native verification and decision_complete.
It does not require a SUPPORTED verdict and does not assert truth. A reproducible
RESOURCE_LIMIT report may replay but is not a complete current decision. Error
reason strings are explanatory, not acceptance labels; the frozen oracle checks
their nonempty typed presence, the error class, and absence of partial results.

## Actual productive-clause connection

An additional installed adapter reopens the existing productive-clause scope,
retained source bytes and spans, and reruns the existing nine-gate clause reader.
It constructs its own source dependency graph; the caller supplies raw sentence,
its ordinary source binding, and withdrawal/reactivation events naming installed
source IDs, not a ready-made grammar verdict or arbitrary dependency graph.

The graph represents the input, source-scope interpretation and the retained
grammar witnesses separately. A grammar dependency row may appear in the native
dependency-ready list, but `kind=grammar` stays excluded from EM observations.
The adapter uses ONLY dependency readiness to qualify the independently checked
clause chain. Complete source availability AND the existing nine gates are
required for a current complete chain. A suspended licensed clause keeps its
syntactic candidate and scoped structural count as pending. Unknown/out-of-scope
counts remain null. No semantic Omega-completeness is inferred from this count.

Replacing a retained book or source interpretation requires a new independently
reviewed installed version; this fixed adapter offers withdrawal/reactivation
only. The generic authored episode tests replacement as a conditional contract.
This connection does not turn the sentence itself into an observation of a hit.

Retained books and scope packets exceed the per-Source content bound. The adapter
therefore reopens and checks their complete bytes and exact passages in Python,
then builds canonical file descriptors and separate passage Source values whose
content contains the actual retained quotation. The descriptors are computed
from the installed packet, never accepted as a caller's evidence. Lean checks
these projected source values and their dependencies; it does not read or prove
the authenticity of the full book files. The receipt preserves this boundary
and binds the installed code/native identities used in the replay.

## Frozen acceptance and evidence

Freeze this specification/source scope/protocol first, then an independently
authored 40-scenario matrix before accepted-language implementation. Five groups
of eight cover withdrawal, lineage, qualified polarity conflict, time/unit/key
differences, and replacement/missing evidence/resource conditions. Expectations
include every step's complete source state, ordered witnesses, dependency-ready
and blocked IDs, affected IDs, and historical/current receipt behavior.

A scenario passes only if every expected step and binding check passes. Publish
scenario and step denominators separately. Require 40/40 scenario contracts and
zero observed unauthorized current decisions. Do not replace failed scenarios,
drop pending positives, or count transport fuzz cases as observation scenarios.
The matrix is authored, exposed after freeze, and not a blind world-truth study.

Preserve the first execution and each subsequent repair as separate artifacts.
Freeze exact validated source bytes and native hashes before imports/execution,
reuse the established acquisition bootstrap boundary, and retain gold unchanged.
Run existing productive-clause 200 and v1/v2/v3 regressions, new lifecycle and
actual-clause connection tests, Lean audit, conformance, all proof/source links,
and the full release checks. Required new-suite skips are failures of readiness.

## Management and remaining work

Registry/report v2 separates reported measurement from admission readiness.
G1's recorded 200-case result is measured; its general admission remains blocked
by unmet requirements and is never granted by metadata. Scoped deliveries are
separate child tasks with explicit executable dependencies; unfinished parent
tasks remain open. T10's static snapshot run did not execute T06 and must not
claim otherwise. Preserve the v1 registry hash and migration rationale.

T11 preparation records actual source bytes/positions and current Designation
projections only. Unknown community/time fields remain null. It does not create
120 contextual usage cases or infer a `used` judgment for a new occurrence.
General candidate regeneration, interval time, unit conversion, single-valued
predicate conflict, external referents, actual independent observations, G2/G3
and broad project gate admission remain open.
