# Source context beside existing conditional routing receipts

Base: cebb5c472451a1d541ed9b93f56bb6cd2e9d606e (merged PR 64).

Status: preimplementation contract. Freeze this contract and the independent
exposed acceptance matrix before production edits. Subsequent observations must
identify their code, input and oracle versions and retain the first result.

## 1. Purpose and existing owners

The installed conditional operators already return replayable receipts, while
their source inventory retains scope, blockers, boundary descriptions,
diagnostic examples and source passages. Routing currently reduces the
installed catalogue rows to rule identifiers and does not display that context.
This change projects the existing context beside each examined routing row and
adds independent, whole-report replay bound to the original request.

Reuse tools/grammar_catalog/routing.py, its CLI, SearchIndex, and the public
classical_laws.catalog/replay_inventory/evaluate/verify owners. Do not create
another operator registry, evaluator, grammar catalogue, proof catalogue or
general evidence engine. The catalogue remains at its existing schema and
contents; all 125 source-catalogue records remain available.

The context population is the 24 currently installed conditional operators,
joined exactly to their existing inventory entries and namespaced catalogue
keys. Other inventory records do not become executable through projection.
The original 90-file oracle dependency profile, 99-file runtime freeze,
Makefile, main CI workflow, source inventories and prior gold remain unchanged.
No formal module or theorem is added by this projection.

## 2. API and compatibility

The existing evaluate_candidates function gains report_version=2. It accepts
only exact integers 1 and 2; booleans are not versions. Version 2 is the default
and emits nabt.conditional-rule-routing.v2. Version 1 emits the original v1
report for the same inputs and unchanged owners, including its catalogue
identity, schedule, status, receipts and verification objects.

The existing query/search/evaluation composition is centralized in the same
routing module as build_routing_report(index, query, frames_by_rule, *,
budget=None, report_version=2). It performs the current rule search with limit
10, calls the same candidate evaluator and retains the retrieval report.
SearchIndex retains its original resolved root as a private owner attribute so
the existing catalogue validator can replay that same checkout. This adds no
catalogue field or authority and changes no v1 serialized output.

verify_routing_report(report, *, query, frames_by_rule, budget=None,
report_version=2, root=ROOT) builds a fresh source-validated SearchIndex,
recomputes the full report from the independently supplied request and compares
complete typed canonical JSON. Verification supports v2 only. Legacy v1 output
does not claim original-request binding and must be explicitly rejected by this
new verifier rather than silently receiving weaker verification.

## 3. Exact source-context projection

Every examined v2 row carries source_context beside its existing fields.
The receipt and verification objects are unchanged. Missing-premise and
frame-error rows also receive source context, without fabricated receipts.
Unexamined rules remain in pending_rule_ids and are not counted as examined.

The context object has these exact fields:

| Field | Value or owner |
| --- | --- |
| schema | nabt.classical-rule-source-context.v1 |
| authority | AUTHORED_SOURCE_CONTEXT_ONLY |
| semantic_authority | NONE |
| action_authority | NONE |
| rule_key | inventory schema followed by :: and the exact rule ID |
| rule_id | Exact installed conditional operator identity |
| owner | Object containing path, schema and sha256 for the pinned inventory |
| source_scope | Original inventory rule.scope |
| source_blockers | Original rule.blockers |
| boundary_mode | Original rule.boundary_mode |
| source_text_status | Original rule.status |
| interpretation_note | Original rule.interpretation_note |
| positive_cases | Complete original diagnostic array, preserving order and fields |
| negative_cases | Complete original diagnostic array, preserving order and fields |
| source_spans | Complete original span array, preserving raw text and metadata |
| premises_established_from_free_text | false |
| grants_language_license | false |

The owner path is
src/nabt/data/source_evidence/classical_rule_inventory_v1.json. Its identity is
obtained through the installed owner and its code-pinned digest, never from a
submitted report. All original source bytes and selected spans are replayed.
Returned nested objects are detached from caller-owned and cached objects.

Scope and blockers are authored text; there is no claim of a newly parsed
Boolean condition language. Positive/negative diagnostics are not automatically
acquired input frames or independent test cases. Preserve each diagnostic's
own scope, including the statement that a negative example may be outside this
rule without being ungrammatical Arabic.

Source status is separate from current implementation and application status.
In particular, ASSIM-NUN-B-BLOCKED-TEXT keeps its textual_discrepancy and both
inventory passages. Runtime results may carry additional source spans; retain
them in their original receipt rather than replacing them with inventory spans.
No historical implementation.status field is relabelled as current readiness.

## 4. Request identity

V2 includes a request object containing the exact ranked_rule_keys list, a
frames_sha256 over canonical finite ordinary JSON for the complete supplied
frames mapping, and the requested budget, preserving null separately from an
explicit full-inventory integer. build_routing_report also includes the raw
query in this object, without normalizing it into its retrieval projection.

Snapshot request inputs before hashing and evaluation. The same snapshot must
drive both the request identity and the conditional evaluation. Binding covers
unexamined/unused frames as well as examined frames. An equivalent ranking,
duplicate proposal list, or same-result query does not make two requests
identical. The verifier must reject substituted request inputs even when the
visible conditional results coincide.

## 5. Replay and authority

Whole-report verification recomputes retrieval, installed-rule scheduling,
source context, each evaluated conditional receipt and its existing Python
owner verification, row status, pending inventory and aggregate status.
It compares every field, including authority flags and otherwise unused data.
Caller-supplied digests, approval flags, descriptions or rewritten passages do
not become authorities. The verifier returns a digest of the verified complete
report and explicitly scoped verification; it does not issue a grammar or
external-world license, adoption event, action permission or Lean certificate.

The current source index and installed operator inventory must agree on their
identities and join. A supplied or long-lived SearchIndex is not trusted solely
because its type or mutable catalogue digest matches. Validate its catalogue
and records against fresh installed sources, and use a fresh validated index
for v2 query and rule resolution. Reject disagreement or a stale index rather
than attaching context from a different observation. Source replay failure is
a route/source failure, not a malformed-frame result. In v2,
INSTALLED_CONTRACT_FAILED during evaluation or verification propagates as a
global failure; an invalid generated receipt also fails globally. Only bad or
resource-limited caller frames retain the frame-error row path. V1 preserves
its original error handling. Repeated recorded source identities must agree;
these sampled checks do not claim an atomic filesystem snapshot.

The successful verification envelope has exactly: schema
nabt.conditional-rule-routing-verification.v1, valid=true, report_schema
nabt.conditional-rule-routing.v2, report_sha256, catalog_sha256, authority
ROUTING_REPLAY_ONLY, semantic_authority=NONE, action_authority=NONE,
premises_established_from_free_text=false, grants_language_license=false,
exhaustive_language_claim=false, and whole_book_completeness=false.

Ordinary JSON means exact built-in containers/scalars with string object keys,
finite numeric values and valid UTF-8. Reject duplicate serialized object keys,
non-finite numbers, non-JSON coercions and unknown verification schema/version.
Finite floats may appear in retrieval scores or invalid law-frame inputs; they
must not be silently coerced into integers or booleans. JSON-compatible invalid
law frames retain the existing FRAME_ERROR path and its original error type.

## 6. Preserved result distinctions

Keep the current installed fallback schedule. Source context cannot remove a
rule, create a premise, convert missing information into negation, complete a
partial profile, adjudicate a textual discrepancy, discard an attested
alternative or certify an unexamined rule.

CHECKED_CONDITIONAL describes a successfully replayed conditional computation;
its result can still be BLOCKED or OUTSIDE_SCOPE. Missing input remains
MISSING_PREMISES; unknown/unfinished operator output remains PARTIAL according
to the current owner fields. Invalid and resource-limited frames keep their
distinct embedded error records. A truncated scan remains RESOURCE_EXHAUSTED.

The added report does not establish candidate formation history, candidate
adoption, interpretation fidelity, external case applicability or action
authority. It supplies no CertifiedBridge: sourceLicense, hostInventory,
hostLicenses, grammarLicense, realizationAligned and RealizationContracts remain
separate obligations on actual application trees.

## 7. CLI and resource boundaries

The existing route command uses v2 by default and exposes explicit legacy
output:

    python -m tools.grammar_catalog route QUERY --frames PATH [--budget N] [--legacy] [--output PATH]
    python -m tools.grammar_catalog verify-route REPORT --query QUERY --frames PATH [--budget N] [--output PATH]

The verification command requires the report and external query, frames and
budget. It must not recover those trusted inputs from the report. It accepts
only v2 reports, with no legacy-verification option.

The document limits are 8,388,608 UTF-8 bytes, 1,000,000 JSON value nodes and
nesting depth 64. Keep the existing 16,384-byte query limit, maximum 1,000 ranked
keys, integer scan budget within the 24 installed rules, and the conditional
owners' own frame limits. The whole-document limits supplement those existing
limits; they do not make a larger operator frame admissible.

Route and verification input files are bounded before parsing and use strict
JSON parsing. Their output paths must not overwrite an existing file. Global
resource exhaustion uses the
existing NabtError RESOURCE_LIMIT record and CLI exit 3. Invalid input, source
failure and replay mismatch use exit 2 with structured diagnostics. Embedded
operator-frame errors retain their existing row behavior and error types.
Inherited interpreter limits on integer-to/from-decimal JSON conversion also
remain resource limits; do not disable them or call such failure a linguistic
rejection. The writer's byte budget must agree
with the reader's so that a generated file is not rejected solely for
pretty-printing expansion. Catalogue and search semantics remain unchanged.

## 8. Independent acceptance and integration

Freeze literal source projections and linguistic expectations from existing
sources/independent diagnostics before production changes. Keep the previous
v1 command result in evidence/operator_context_v1/baseline as the exact legacy
control. The acceptance population is exposed engineering evidence, not a new
held-out Arabic evaluation or a count of newly proved rules.

The acceptance matrix covers exact projection/identities; unknown versus
blocked hamza; dialect alternatives; nun textual discrepancy; partial
gemination and light-nun profiles; missing frames and budgets; frame errors;
unchanged embedded receipts; wrong-rule context; altered blockers/examples;
receipt/authority tampering; actual source-byte mutation; defensive copying;
original-request substitution; and default/legacy/verification CLI behavior.

New tests are discovered by the existing test suite. Reuse the current
grammar-catalog/routing and proof-reuse checks and update the existing
rule-routing use metadata. Do not weaken old tests, freezes or CI gates.
Record first observations and corrections separately, run targeted owner and
integration checks, then require every triggered CI check on the final
published head before the authorized merge.
