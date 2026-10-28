# Evidence lifecycle v1 — independent oracle method

This matrix was authored against the specification, source scope and protocol
frozen in `4b1812127acf452ed72e57686ec02486bebc472c`, after the baseline
`c2c072e17802b62c13109cee7c087b7b58895a1a` and before implementation of the new
law. Its schema is `nabt.evidence-lifecycle.cases.v1` and law ID is
`nabt.evidence-lifecycle.v1`.

The oracle author read `AGENTS.md`, `docs/EVIDENCE_LIFECYCLE_V1_SPEC.md`, and
`acceptance_protocol.json`. Existing EM contracts were consulted for Source,
Key, Query, Origin, Evidence, the allowed kind/axis relation, query-relative
polarity, and wire spellings. These were the historical
`docs/EPISTEMIC_MEASUREMENT_AR.md`, the relevant type/contract definitions in
`formal/Nabt/EpistemicMeasurement.lean` and `formal/Nabt/RationalInquiry.lean`,
and a historical EM authored-reference record for JSON field spellings.
The author did not read or import the new lifecycle implementation or obtain
expected values from a producer, proposed runtime, native checker, simulator,
filter, or graph traversal.

## Authorship and review boundary

The forty scenarios were first designed outside the repository, with manually
written step tables. After the source commit was frozen, the author transcribed
those expectations into `cases.json`. Input-only helpers constructed the
repeated episode, evidence and event fields. Expected Source lists, witness
lists, readiness/blocked/affected lists, receipt statuses, and verification
relations were literal authored data. Shared Source constants represent the
same complete authored values; they are expanded in full in every JSON step.
No helper applied a transition or computed an expected verdict.

A second reviewer checked the design before JSON transcription. The complete
JSON is supplied for independent and lead-agent review before the separate gold
commit. Counts and JSON structure may be checked without executing the law.
These are agent-authored conditional controls, not external human adjudication,
physical observations, a blind test, or an estimate of generalization. The
matrix is exposed to implementers after its freeze.

## Population and denominators

| Population | Count |
|---|---:|
| Scenarios | 40 |
| Families | 5 × 8 |
| Validly formed episodes | 34 |
| Invalid input episodes | 5 |
| Episode-level resource error | 1 |
| Main expected steps in valid episodes | 79 |
| Complete main decision steps | 76 |
| Ledger-budget RESOURCE_LIMIT steps | 3 |
| Historical/current verification pairs | 73 |
| Additional explicit historical-prefix steps for erroneous full episodes | 7 |

The families are `withdrawal`, `lineage`, `conflict`, `qualified_key`, and
`revision_and_absence`. The six error episodes remain in the forty-scenario
contract denominator, and their native error envelopes must be checked as well
as their Python reports. They contribute no accepted main episode steps.
The seven historical-prefix steps are a separate auxiliary oracle and do not
inflate the 79-step denominator. Replaying a receipt in several verification
pairs is not another independent scenario or observation.

`VALID_EPISODE` is an oracle classification, not a new native status field.
Successful native envelopes contain the complete binding and steps; the result
status is the final step's receipt status. `INVALID_INPUT` and an outer
`RESOURCE_LIMIT` instead require an error envelope without accepted binding,
steps, or partial history. Error reasons must be nonempty valid-Unicode strings;
their prose is not an acceptance label.

LC-R06 is validly formed but has an original two-row ledger and budget one.
All three receipts must be `RESOURCE_LIMIT`, with empty witness lists and null
readiness/blocked/affected diagnostics. Its result is not decision-complete.
An exact resource replay can have `replay_matches=true`, but must have
`valid=false`. LC-R08 instead exceeds the active-source cap during an update;
the entire episode is a resource error without an accepted prefix.
`UNKNOWN` and `CONFLICT` remain complete ledger decisions when the ordinary
budget is sufficient. They are neither malformed input nor resource exhaustion.

## What the scenarios distinguish

- W01–W06 cover sole support, surviving independent support, idempotent removal,
  withdrawal/reactivation, loss of a refutation, and source/ledger ordering.
- W07 holds a complete evidence source B against origin A's complete binding A.
  Both sources can be active; the mismatch is blocked dependency readiness,
  not malformed input. W08 makes a grammar row ready without licensing it as an
  observation.
- L01–L04 cover direct, transitive, multiple-parent and shared-parent effects.
  L03 requires reactivation to append C after D. L05 distinguishes a known but
  omitted ancestor from an unknown-origin input error. L06 tests conservative
  ancestry over-sets. L07 keeps query-origin exclusion separate from readiness.
  L08 rejects a closed declared cycle under the new ranked-graph contract;
  it does not reinterpret the historical EM law.
- C01–C05 preserve explicit polarity and the query's own polarity. C06 forbids
  treating a different value as an implicit refutation. C07 fixes all witness
  and diagnostic lists in nonalphabetical ledger order, including blocked
  `[eA,eM]` after the second withdrawal. C08 keeps a ready grammar refutation
  outside the observation relation.
- K01–K07 separate exact time, unit, value, context, place, entity and predicate.
  K08 checks `self_report` versus `observation` on the reported-motive axis;
  it does not assert hidden motive.
- R01 registers a new replacement source but does not rewrite old bindings or
  interpretations. Its subsequent withdrawal of the replacement is valid.
  R02 and R07 contain late invalid updates and prohibit any accepted prefix.
  R03 rejects activating another revision while the identity is active.
  R04 rejects retrospectively registering an earlier target from a future
  replacement. R05 distinguishes an empty ledger from insufficient budget.
  R06 counts the original ledger before filtering at every step. R08 tests
  the active-source cap at an intermediate transition, not a transport-fuzz
  sample.

## Exact expected data and binding

Each expected main step contains `step`, `event_id`, complete ordered
`active_sources`, the full four-field EM receipt, and ordered
`dependency_ready_ids`, `dependency_blocked_ids`, and `affected_ids`.
All Source values retain identity, revision and content. Empty lists and null
are intentionally different. Diagnostic lists follow interpretation order.
Step zero's affected list is empty except that insufficient budget leaves the
entire diagnostic axis null. No expected value is a digest-only source proxy.

The successful native field set and error field set are declared in
`common_contract`. Complete typed equality of the successful binding with the
independently supplied episode is required. All four authority flags are false:
world truth, source authenticity, referents, and all-Arabic completeness.
Missing native checking is unmeasured and cannot pass a scenario.

## Independent historical/current verification

Each verification pair names `receipt_prefix_updates` and
`expected_prefix_updates`. Construct both episodes separately from the case
input, truncating only the updates list to those lengths. Keep the same episode
ID and every other input field. Never obtain the verifier's expected episode
from the receipt being checked.

The pair explicitly states historical replay/validity and current
replay/validity. First verify the receipt against its own separately constructed
historical episode, then against the separately constructed expected episode.
Valid main episodes supply the authored prefix-step oracle through the named
prefix. For a full episode whose outcome is an error, use the explicit
`historical_prefix_expectations` list; do not invent accepted prefix steps from
an error report. L08 has no valid historical prefix and no verification pair.

W03 has an idempotent withdrawal with unchanged results. W04 and R05 return to
the original active list, and R01 eventually reactivates the original revision.
Their older receipts are still not current because the full episode binding
changed. Validity is not defined by equal final witnesses or equal active sets.
Resource replay and complete-decision validity remain separate in R06.

## Preservation and interpretation

Freeze this JSON and this method in a separate commit before new implementation.
Retain the first execution and every failure. Do not edit expected results to
repair a producer or evaluator. Any later erratum must be independent,
versioned, justified, and preserve the original matrix and first outputs.
Require all authored steps and binding/verification checks for scenario credit.
Report scenario, main-step and auxiliary verification denominators separately.

Passing this finite authored matrix would establish the measured conditional
contract only. It would not authenticate collectors or source contents, infer
undeclared copying, prove statistical independence, complete the world bridge,
recover a general semantic candidate space, finish G2/G3, or grant broad project
admission through metadata.
