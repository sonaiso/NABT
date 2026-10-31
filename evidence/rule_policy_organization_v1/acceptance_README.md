# Independent acceptance expectations for rule and policy organization

This is an authored, exposed acceptance protocol frozen before implementation.
It tests organizational metadata, owner references, and the opt-in report. It
is not held-out linguistic gold, a measurement result, or a grant of semantic
or action authority. The baseline is
`181dec466ccfad5b6a63ec9750f149ea58829eda` on
`codex/rule-policy-organization-v1`.

## Scope and independence

`acceptance_cases.json` contains fourteen named acceptance groups with literal
expectations and explicit subcases. The seven-profile fixture and its expected
results were authored independently of the future organization resolver. The
complete 125-ID catalogue population and the command rule's existing scope,
title, source passage and theorem reference were read from the existing owner
before implementation; they are frozen as values in the artifact. Expected
results must not be regenerated from the implementation under test.

The existing base `rule_contract` and `evidence_freshness` policies are mandatory
for `validate_registry` and the organization entry point, including a valid
legacy registry with no organization. The organization is optional: omission
reports `NOT_DECLARED`, with no inferred profiles. Ordinary `reuse` remains
compatible with its small navigation-only fixtures and does not acquire a new
catalogue dependency.

This work does not add a semantic kernel, rule adoption bridge, permission
engine, or new alias system. Classification is authored metadata. Resolving a
reference is not evidence that its formation, adoption, application or revision
occurred; all four lifecycle statuses stay `NOT_OBSERVED` in this tranche.

## Fixture protocol

Every case starts from a fresh in-memory fixture. `legacy_registry` means the
valid baseline registry, preserving its base policies and removing only
`rule_contract.organization` if present. `prepared_registry` inserts the frozen
`organization` fixture at that path. Apply the listed RFC 6902
`add`, `remove`, `replace` and `copy` operations without silently repairing
unknown fields, missing identities, duplicates or malformed values.

`organization_report` denotes the implementation exposed by the existing
`reuse --organization` front door; the implementation may choose its internal
function name. The acceptance oracle does not prescribe a second dispatcher.
Use `validate_registry` for base and shape checks and the report resolver for
references requiring existing owner loaders. The structure-only validator
reports `organization_state=DECLARED_REFERENCES_NOT_RESOLVED` or
`NOT_DECLARED`; it must not claim a successful owner lookup. A well-shaped but
unresolved catalogue ID passes this structural check and fails explicit owner
resolution. `report_equals` and catalogue/profile assertions in the artifact
apply only to the full organization report; `validation_expected` applies to
the existing registry validator. The agreed implementation interface is
`tools.entropy_framework.organization.build_organization_report(root=ROOT, *, registry=None)`
and `validate_organization_structure(value)`. An exception must remain a
structured metadata failure; a malformed record does not prove a linguistic
negative.

The fixture digest is the SHA-256 of UTF-8 JSON using `ensure_ascii=False`,
`sort_keys=True`, `separators=(',', ':')` and `allow_nan=False`. Its expected value
is stored literally. Reversing the profile array changes this identity while
preserving coverage, per-ID content and role counts. Canonical object-key order
does not erase list ordering.

Owner scopes are independent output data. A nonempty authored profile scope
may differ from its owner's scope; the report keeps both and sets
`scope_relation_established=false`. The protocol does not ask a metadata
validator to prove linguistic containment. A reference accepts exactly
`{kind, id}`: caller version, hash, source, scope, command and authority overrides
are invalid. Existing owner loaders retain responsibility for source and
compiled-catalogue integrity.

## Acceptance groups

| ID | Required behavior |
| --- | --- |
| RPO01 | Resolve five existing owner kinds and all seven organizational roles, preserve base contracts, and report no execution or authority. |
| RPO02 | Accept valid legacy omission explicitly as `NOT_DECLARED`; keep the whole catalogue unclassified. |
| RPO03 | Reject missing or weakened rule contracts even in legacy input. |
| RPO04 | Reject counterfeit operation vocabularies, kinds and Boolean kind values. |
| RPO05 | Reject absent freshness policy or an omitted source-identity dimension. |
| RPO06 | Reject duplicate profile IDs, exact phase references, family links and relation tuples. |
| RPO07 | Reject unresolved owner IDs, family links and relation endpoints; do not fuzzy-match. |
| RPO08 | Reject empty scopes and reference overrides; preserve a differing authored annotation separately from the owner's scope. |
| RPO09 | Reject wrong schema/version identities and injected source bindings; retain the existing source-replay rejection. |
| RPO10 | Reject cycles in the union of justification and prerequisite edges, including a mixed-kind cycle and self-prerequisite. |
| RPO11 | Permit and preserve reference, inference and conflict cycles as metadata without scheduling or semantic authority. |
| RPO12 | Enforce closed shapes, reject injected events/commands/authority, and prove that report construction does not dispatch execution. |
| RPO13 | Preserve all 125 catalogue IDs: the authored fixture maps one subject; the specified initial slice maps two. Retain source discrepancy and conditional runtime status separately. |
| RPO14 | Preserve ordinary reuse, support organization summary/output, and reject organization combined with family/module/run. |

RPO13 also freezes the specified initial eleven-profile slice, independently
of any implementation-created default metadata: the two direct catalogue
subjects are `nabt.morphology.source-policy.v1::word_kind` and
`nabt.classical-rule-inventory.v1::ASSIM-NUN-B-BLOCKED-TEXT`. All other 123
records remain visible and unmapped. The discrepancy record keeps
`source_status=textual_discrepancy` alongside its installed conditional
runtime reference and false source-fidelity/completeness claims. The word-kind
record keeps its own authored source-policy status and null runtime reference.
The `inquiry-review` profile is an `EVIDENCE_ADMISSION_POLICY`.

The full report schema is `nabt.rule-organization.report.v1`; the compact
summary has distinct schema `nabt.rule-organization.summary.v1`. Both preserve
fixed nonexecution and authority boundaries. `--output` writes the full report,
including when `--summary` changes only the displayed view. The base rule
contract projection excludes its nested organization, preventing recursive
self-embedding when that contract itself is referenced.

No new alias feature is needed for these cases. Where an existing owner carries
source-qualified terms or profiles, preserve them exactly. The terminology
review already identifies that `shakhsiyya3-selected-v1` uses `لحن الخطاب` for
opposition; the organizational layer must not introduce a global alias that
changes the owner's meaning.

## Existing boundaries to reuse

The artifact names existing tests for explicit negation, necessary-condition
bridges, analogy, conflict handling, source withdrawal, resource limits,
observation provenance, source-only recursive bridges and code-owned dispatch.
Their detailed semantic fixtures are not duplicated here. The new tests need
only check that organization does not bypass or replace those owners.

In particular, the tampered-source subcase in RPO09 can be discharged through
an existing source-integrity test plus a narrow assertion that organization
uses the real owner loader. If a direct mutation is needed, mutate an isolated
copy only. Do not alter the installed book corpus to execute an acceptance
case. The listed execution sentinels concern native checks, compilation and
action dispatch, not ordinary deterministic file reads or hashing.

## Freeze and evaluation discipline

The root agent will commit this oracle with the approved specification before
implementation. No implementation or test file is part of this author's
ownership. A correction after exposure must preserve the old artifact and
record why the expectation changed; do not edit expected results merely to fit
an implementation. Future reports must identify the case-file digest, code
revision and evaluator. Missing checks are unmeasured and never successes.

The artifact currently records expectations only. No new acceptance case has
been reported as passing, and no claim about complete Arabic coverage follows
from the 125-record organizational denominator.
