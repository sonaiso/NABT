# Meaning preservation v1: preimplementation runtime contract draft

Status: exact request schema approved by parent for source/spec and independent matrix freeze. No runtime
implementation has been written by the runtime agent. Base repository:
`sonaiso/NABT@3dbe335a21ac838db3717f03ca2a5b5889e16e54`.

## Audit and deliberately reused components

- `tools/acquired_inference.py` and `tools/acquired_inference_v2.py` already
  compose complete original-source acquisition and shape licenses with the
  independently executed `licensedInference` source/query checker. A nested
  inference never repairs missing acquisition. Do not add another parser.
- `tools/productive_clause_v1.py` already obtains a source-bound, finite
  DARABA VSO/VOS reading through nine gates. Its complete `reading` is the
  first executable producer for this extension. The historical finite grammar
  and its source packet remain unchanged.
- `tools/productive_lifecycle_v1.py` adds dependency readiness and replay. It
  does not supply semantic preservation, source authenticity, or world truth.
- `tools/semantic_axes.py:observe` currently projects syntax, semantic readings,
  and references into separate deduplicated lists. It is a useful historical
  diagnostic, with `query_executed=False` and `verification_kind=PYTHON_REPLAY`.
  It is not used to reconstruct joint alternatives in this extension.
- `src/nabt/discourse_context.py` retains explicit source context and bounded
  reference alternatives. It remains unchanged. Its context schema is not
  silently widened by a new transport context schema.
- `formal/Nabt/SourceSemantics.lean` already proves binder-free substitution,
  closed-singleton reference, time restriction, and source-bound consensus.
  `formal/Nabt/RecursiveLicensedAlgebra.lean` proves conditional realization
  invariants. Neither existing theorem is renamed as the new fiber criterion.

## Claim and trust boundary

The new installed law is `nabt.meaning-preservation.v1`; its fixed query is
`joint-readings.v1` and codec is `strict-json-packet.v1`. It checks a *finite supplied representation contract*:
the declared observations survive reconstruction, whole alternative tuples
remain correlated, and equal complete transported payloads never conflate unequal observations
in the supplied finite domain. The producer's independently checked license,
the finite observation contract, and external truth are three distinct claims.

Successful native status is `FINITE_CONTRACT_VERIFIED`. It never means full
Arabic adequacy, mental equivalence between humans, external referent identity,
source authenticity, physical truth, or exhaustive world ontology. A supplied
hash, receipt, `complete` label, or arbitrary observation column grants no
authority. The query is installed code and is computed from typed readings.

The authored mode has authority `AUTHORED_PREMISES_FINITE_CONTRACT`. It accepts
semantic packets as explicit modeling premises. The productive mode has
authority `PRODUCTIVE_CLAUSE_SOURCE_BOUND_FINITE_CONTRACT` only if its existing
producer chain and the new native transport checker both succeed. This is
source-bound *syntactic-role* preservation, not proof that ZAYD denotes a
particular person or that a hitting event occurred.

## Proposed exact native request schema

```text
Request = {
  law_id: "nabt.meaning-preservation.v1",
  query_id: "joint-readings.v1",
  codec_id: "strict-json-packet.v1",
  cases: [Case],
  recipient_context: Context
}
Case = {
  case_id: String,
  original: Packet,
  transported_payload: String
}
Packet = {
  binding: Binding,
  source_context: Context,
  alternatives: [Reading]
}
Binding = {
  source_id: String, revision: String, scope: String,
  source_text: String, convention: String
}
Context = {speaker: String, addressee: String, time: String, place: String}
Reading = {
  predicate: String,
  subject: Term,
  object: Term | null,
  positive: Boolean,
  tense: "past" | "present" | "future" | "unspecified",
  voice: "active" | "passive" | "unspecified",
  force: "asserted" | "quoted" | "hypothetical" | "question"
}
Term = {
  kind: "entity" | "speaker" | "addressee" | "time" | "place",
  value: String
}
```

All object field sets are exact. All arrays are bounded. A term with kind
`entity` has a nonempty bounded value; all other kinds require `value=""`.
The typed term tag is retained in an observation, alongside its resolved
value, so an opaque token spelling and a contextual reference do not become
interchangeable without a separately installed law. Context values are explicit
symbolic premises, not acquired facts. `unspecified` is an ordinary explicit
symbol, not an invitation to invent a value.

No integers or floats occur in this public native request. Booleans are legal
only at `positive`; `1` is not a Boolean. Reject duplicate object keys,
unexpected fields, nonfinite numbers, malformed UTF-8, unpaired surrogates,
invalid tags, empty IDs, duplicate case IDs, and duplicate complete reading
objects. Metadata strings are nonempty, at most 512 UTF-8 bytes, and exclude
Unicode scalar values 0–31 and 127–159. Whitespace-only metadata otherwise
remains accepted without trimming or normalization. Source text is arbitrary
strict Unicode, nonempty, and at most 65536 UTF-8 bytes; original whitespace
and control characters are retained as source data. Nonentity term values are
exactly the empty string by schema. Case and alternative order are not semantic distinctions. Case IDs
must be nonempty and unique. The installed encoder serializes a Packet to
canonical strict JSON with sorted object keys and compact separators. The
channel carries its complete UTF-8 payload string. The native checker itself
parses that string using the strict JSON parser and validates the decoded
Packet. It never accepts a separate caller-declared decoded object. The decoded
packet must preserve the exact binding and exact original source context.

Initial engineering limits: request 1 MiB, report 8 MiB, 64 cases per request,
64 alternatives per case, metadata 512 UTF-8 bytes, source text 65536 UTF-8
bytes; transported payload 1 MiB and total outer request 1 MiB. Parsed JSON
nesting is at most 32 levels, measured from root depth zero independently for
the outer document and each inner payload. Report size is at most 8 MiB. Exceeding these bounds returns
`RESOURCE_EXHAUSTED`, never a linguistic rejection. Nonempty cases and nonempty alternatives
are required in v1; an empty set is not accepted as proof of meaninglessness.
These are computational limits, not asserted linguistic maxima.

## Installed observation q

For each reading, the installed query computes a whole tuple:

```text
(predicate,
 subject-tag-and-resolved-value,
 optional-object-tag-and-resolved-value,
 positive, tense, voice, force,
 binding.scope, binding.convention,
 source_context.time, source_context.place)
```

Resolution of `speaker`, `addressee`, `time`, and `place` always uses
`source_context`; `recipient_context` never overwrites it. The observation
of a case is the finite set of these whole tuples. Neither the runtime nor
native code independently unions subject/object lists or takes their Cartesian
product. Thus `{(A,X),(B,Y)}` remains distinct from `{(A,Y),(B,X)}` and from
the four-element product of its marginal sets.

Retaining the tag is deliberately conservative: this version proves that the
declared distinctions remain available. It does not implement a universal
equivalence between a resolved pronoun and a proper name. The report must
state that restriction, not call this query the entire meaning of Arabic.

## Finite preservation and recoverability checks

1. Validate the request and every original packet under the installed schema
   and limits. Independently decode each full transported payload into a strict
   Packet. Parse failures and resource results precede semantic comparisons.
2. Compute q from the original and decoded packets independently.
3. For all pairs of original cases with exactly equal full `transported_payload`,
   require equal original observations. Return the first deterministic pair of
   counterexample IDs on failure. This finite fiber check runs before per-case
   preservation so a collision is observable rather than hidden behind its
   inevitable per-case failure. Actual complete string equality determines a
   fiber; no caller label or hash grants equivalence. Different payloads with
   equal observations are permitted.
4. For each case in input order, check exact source binding, then source context,
   then observation equality as sets of whole tuples. Source text itself is
   part of the binding; a hash alone is insufficient. Reordering alternatives
   is permitted; losing, adding, or re-pairing a distinct tuple fails.
5. Return the complete deterministic native decision. Python compares its
   entire typed decision proposal against the native result.

Stable semantic failure reasons are `SOURCE_BINDING_CHANGED`,
`SOURCE_CONTEXT_CHANGED`, `OBSERVATION_CHANGED`, and `FIBER_COLLISION`.
They produce `CONTRACT_VIOLATION`, not `LINGUISTIC_REJECTION`, and retain the
first case ID or pair of IDs. Input and resource failures remain separate.

The native response has exactly these keys:

```text
{
  schema: "nabt.meaning-preservation.native-response.v1",
  law_id, query_id, codec_id,
  status, reason,
  case_id: null | String,
  other_case_id: null | String,
  case_count: Nat,
  world_truth_established: false,
  whole_arabic_completeness_established: false
}
```

Success status is `FINITE_CONTRACT_VERIFIED`, with reason
`ALL_FINITE_CONTRACTS_PRESERVED` and null witness IDs. Invalid input and resource
responses use status/reason pairs `INVALID_INPUT`/`INVALID_REQUEST` and
`RESOURCE_EXHAUSTED`/`RESOURCE_LIMIT`, respectively, with null witness IDs and
case_count zero. Foreign law/query/codec IDs are invalid input, not a
linguistic judgment. The native process exits zero for checked success or a
checked semantic contract violation and exits two for invalid input or resource
failure; the status distinguishes those two failures. The finite count has the declared law/query
as its domain; it never denotes Arabic coverage. Checked observations in the
outer report are Python traces with their actual evidence kind, while the
native decision independently evaluates q and verifies preservation.

The native transport check invokes an actual installed decoder on each payload.
It does not establish a universal decoder for arbitrary ontologies. The abstract
theorem may establish decoder existence on an image; this finite checker
executes strict JSON packet decoding and checks its finite fiber condition.
Canonical encoding is the default producer. Well-formed JSON whitespace and
object key reordering are accepted by the decoder; duplicate keys and malformed
encodings are rejected.

## Productive clause adapter

Add `tools/meaning_preservation_v1.py` and `tools/meaning_preservation_cli.py`.
Keep `src/`, original `Makefile`, existing readers, and existing law constants
unchanged. New additive gate: `tools/meaning_preservation_v1.mk`.

Public proposed API:

```text
evaluate_authored(request) -> Result
evaluate_productive(text, *, source_id, revision, scope, ending, onset,
                    source_context, recipient_context,
                    transported_payload=None) -> Result
verify(result, *, independently_supplied_original_request) -> Verification
```

The productive entry point reopens the original text through installed
`tools.productive_clause_v1.evaluate` with its ordinary binding. Only a
complete nine-gate result supplies the original Case. It projects verb,
subject, and object lexeme IDs, with typed entity terms; positive assertion,
past tense, and active voice are explicit conventions of this already
installed finite grammar. Set `binding.convention=nabt.productive-clause.v1`.
Original spelling, word spans, morphology, reading order, source receipts,
and producer gates remain in the outer receipt even where q deliberately
compares an order-independent role interpretation.

`transported_payload=None` uses the installed canonical encoder to produce an
actual JSON channel payload; a caller may supply a payload for channel-mutation
verification. The native decoder alone derives the reconstruction. The caller cannot
provide the original semantic packet to bypass productive acquisition.
Any incomplete producer outcome propagates before finite certification;
no successful authored/native subresult fills a missing producer gate.

The v1 productive adapter uses this existing producer directly. The acquired
inference bridge is already complete under its own law, but its signed closure
and conditional clauses have different observation structure. Do not silently
coerce them into event role tuples. A future query ID may project its native
rows/closures; current reports explicitly state that no such new bridge is
claimed by this version.

## Outer runtime result and verification

Result includes schema/law/query IDs, mode, status, authority, verified flags,
original input identity, complete producer receipt where applicable, complete
native request/result, checked observations, counterexample, source/recipient
context, and named gates. Constants remain false for `world_truth_established`,
`source_authenticity_established`, `referents_established`,
`all_arabic_complete`, and `human_interpretation_agreement_established`.

The native executable is selected only from the installed build path. Missing
native becomes `VERIFICATION_UNAVAILABLE`. Timeout/native resource result
becomes `RESOURCE_EXHAUSTED`. Process/JSON/result mismatch becomes
`VERIFICATION_FAILED`. There is no Python success fallback and no configurable
caller executable or trusted caller hash. Verification independently resupplies
input, reruns the installed chain, and compares the complete typed receipt.

CLI forms proposed:

```sh
python -m tools.meaning_preservation_cli inventory
python -m tools.meaning_preservation_cli authored --request FILE
python -m tools.meaning_preservation_cli productive --request FILE
python -m tools.meaning_preservation_cli verify --mode authored --request FILE --receipt FILE
```

`authored --request` takes the native request schema above. `productive
--request` takes exactly `text, source_id, revision, scope, ending, onset,
source_context, recipient_context, transported_payload`; payload is either a
string or null for the installed encoder. Ending/onset are passed unchanged
to the existing producer. `verify --mode authored|productive` independently
resupplies the corresponding original request and a separate complete receipt.

The no-file `inventory` command calls the parent-owned installed
`tools.meaning_preservation_inventory.research_inventory()` and presents the
immutable morphology/composition/interpretation inventory with its exact source
identities, counts, and explicit authority boundary. Inventory verification
checks research records and source bytes; it is not language acceptance or
semantic preservation.

`--request` is strict bounded JSON. Stdout is one JSON result; diagnostics go to
stderr. CLI exit policy is fixed: zero for a fully verified finite contract,
verified replay, or a checked inventory; two for `INVALID_INPUT` or
`INVALID_RECEIPT`; three for `CONTRACT_VIOLATION`, `DEFER`, or
`REJECTED_IN_SCOPE`; four for verifier/source/dependency unavailability or
verification failure; five for `RESOURCE_EXHAUSTED`. Missing input files yield
`INPUT_UNAVAILABLE` and exit four. A successful abstention remains separate
from successful positive interpretation.

## Independent golden matrix and adversarial checks

The evidence agent authors the golden matrix before implementation. Runtime
tests may not generate expected observations by calling the production query.
Use hand-authored tuple expectations and independent relational set comparisons
for finite enumerations. Preserve first outputs, source/native hashes, exact
commands, failures, skips, and subsequent exposed repairs separately.

Four required families:

1. Preservation positives: identity; reordered full alternatives; recipient
   context change while source context stays fixed; different payloads for
   equal observations; many-to-one payload mapping only when observations agree;
   complete productive VSO and VOS source flows.
2. Semantic counterexamples: subject/object reversal; polarity flip; quotation
   changed to assertion; tense/voice/context changes; deletion of a distinct
   alternative; crossed role-reference correlations; added Cartesian-product
   alternatives; exactly equal complete payloads with unequal q. Include a redundancy
   control so not every deletion is asserted to make all interpretation fail.
3. Wire and identity: duplicate keys, duplicate IDs, unknown fields, type
   confusion including integer/Boolean, bad Unicode, null versus missing,
   altered source text/revision/scope/convention, mutated native/outer receipt,
   fake caller hashes/status and arbitrary executable fields.
4. Scope and resources: zero/over-budget cases or alternatives; missing or
   timing-out native; malformed native response; upstream acquisition defer;
   upstream scoped negative; full productive success; authored success that
   still has no linguistic/world authority. Count successful abstention as
   safety, separately from requested positive coverage.

Conformance requires genuine native execution and fails if its executable is
absent. Ordinary Python discovery may skip native-only integration methods
and must expose those skip counts. Formal proof catalog/link regeneration and
all existing integration gates remain parent-owned release obligations.
