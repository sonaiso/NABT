# NABT meaning preservation v1: independent authored matrix protocol

Status: PREIMPLEMENTATION_AUTHORED_MATRIX_READY_FOR_FREEZE. Source/spec commit:
`168eec4ec205509ef74825c207b0dcef35a23b4a`. Author: evidence review agent, independent of
runtime implementation. The expected results below follow the declared law and
explicit finite interpretations, not the implementation's outputs. This is an
authored and subsequently exposed matrix, not a blind linguistic benchmark.

## Denominator and four families

1. `preservation_positive`: identity, permutation of cases, permutation of whole
   joint alternatives, preservation of source indexical context despite changed
   recipient context, preservation of source indexicals, changed
   JSON serialization whitespace with unchanged relevant distinctions, and
   permitted equality of separately represented cases. Expected local preservation is true; source
   authenticity, all-Arabic completeness and world truth remain false.
2. `counterexamples`: predicate change, subject/object swap, polarity change,
   tense change, voice change, speech-act change, lost alternative, spurious
   alternative, loss of correlated reference choices, source-context rebinding,
   source binding change, and a payload fiber merging two distinguishable
   interpretations. Expected preservation is false or explicit refusal under
   the declared interface. No failure is an Arabic meaninglessness judgment.
3. `input_integrity`: duplicate JSON keys, duplicate case identities, invalid
   scalar/array/object types, extra fields, missing fields, unknown enum member,
   malformed Term, nonempty placeholder value, null subject, invalid object,
   mixed/missing case sets, booleans supplied for numeric budgets, and malformed
   UTF-8/JSON. These are input/protocol failures, never countermodels to a
   well-formed language theorem or grammatical rejection.
4. `scope_resource_and_authority`: unknown law/query versions, absent native
   verifier, failed native execution, bounded-input/budget exhaustion, inability
   to obtain a complete producer result, and forged authority claims. Keep
   invalid input, out-of-scope query, resource exhaustion, native failure,
   unresolved producer and semantic nonpreservation distinct. Positive accepted
   examples must also retain false authority flags.

## Independent finite oracle

For each well-formed example, read a complete `Reading` as one tuple. Resolve
speaker/addressee/time/place Terms only in that case's `source_context`; entity
Terms retain their declared identifier. Include predicate, subject, object,
polarity, tense, voice and force and the declared scope/convention/time/place.
The answer is the set of whole tuples, never a Cartesian product of separate
field alternatives. Each `cases` row supplies the original Packet and an actual
`transported_payload` strict JSON string; both interpreters decode that string.
Compare exact source binding and source context. Identical payload strings must
not merge different original answer sets. There is no caller-supplied observation,
standalone reconstructed Packet or encoding identity.

The installed IDs are `nabt.meaning-preservation.v1`, `joint-readings.v1`, and
`strict-json-packet.v1`. Cases and alternatives contain 1..64 elements; metadata
strings are at most 512 UTF-8 bytes; source text is at most 65,536 bytes; requests
are at most 1 MiB and reports at most 8 MiB. Empty arrays are invalid input;
exceeding a published cap is resource exhaustion. Successful finite contracts
return `FINITE_CONTRACT_VERIFIED`; a semantic failure returns
`CONTRACT_VIOLATION` with the declared reason(s). The matrix fixes these IDs and
distinguishes decoding/protocol errors from a semantic counterexample.

The query retains a Term's `kind` together with its resolved value. An indexical
and an entity with the same resolved string therefore differ in this declared
query. This is an explicit, stronger equivalence than denotation-only equality;
the matrix does not mistake an arbitrary query choice for universal semantics.

`tense` is `past|present|future|unspecified`; `voice` is
`active|passive|unspecified`; `force` is `asserted|quoted|hypothetical|question`.
Entity Terms require a nonempty value; all four indexical kinds require `""`.
The native checker parses every packet first, checks same-payload fibers second,
and then checks binding, source context and joint observations in that order.
Only the first witness is returned. Unknown law/query/codec IDs are invalid
protocol input. Excluded force labels such as `command` remain outside this
installed profile; they do not imply that commands are meaningless in Arabic.

Explicit tuple witnesses will be included in the frozen JSON whenever a
semantic difference is expected. This oracle does not infer the Arabic text's
meaning; test texts are labels accompanying authored structures.

## Research inventory appendix

The provenance-only matrix separately checks exact imported bytes/row identity,
the four different denominators (51 morphology families, 34 composition groups,
15 engineering contracts, 20 nominal templates), the distinction between
template collation and an uncollated display example, pinned related-source
references, and denial of completeness/translation-fidelity/runtime authority.
These are metadata checks and will not be added to runtime preservation counts.

## Concrete authored matrix

`cases.json` contains 73 expectations: 15 positive preservation cases, 20
counterexamples, 26 input-integrity cases and 12 scope/resource/authority cases.
The execution layers are separately counted: 65 public-contract cases, two
native-error controls, and six live productive-adapter cases. The productive
cases reuse the existing finite DARABA law with a fresh complete producer, not
new grammar labels. A missing positive producer result is a coverage miss.

Six adapter cases cover VSO, VOS, repeated lexical names as distinct source
occurrences, unvocalized outside text, a declared NOM/NOM conflict, and a swapped
role payload after a fresh successful projection. No supplied `chain_complete`
flag can replace those existing nine gates. A deferred/rejected producer never
reaches the transport verifier. A role mutation invokes the adapter again with
the exact original source request and a real altered JSON payload.

Each well-formed result keeps world truth, primary-source authenticity, external
referents, whole-Arabic completeness and human interpretation agreement
unestablished. The native response separately keeps its two declared authority
flags false. A null expected diagnostic reason permits implementation-specific
error text; it does not permit a different expected status.

A missing native binary returns `VERIFICATION_UNAVAILABLE`; a native process
that exits unsuccessfully returns `VERIFICATION_FAILED`. Both preserve explicit
absence of verified transport and cannot be replaced by a Python success.

## Freeze sequence and result handling

The source/spec commit must precede the matrix commit. Runtime implementation
must follow both. Freeze this protocol and all exact expected cases before
evaluating the implementation. Preserve the first invocation, including errors
and partial results. A repaired evaluation is an exposed replay with its own
version; retain original expected cases and any reviewed erratum separately.
Report contract agreement, positive-goal coverage, safe abstentions and native
execution separately. No current result is implied by this protocol.
