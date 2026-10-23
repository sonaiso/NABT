# Independent discourse evaluation protocol v1

## Independence and intended claim

This is an authored, source-informed evaluation by the independent review agent.
It was written without opening the new discourse/person runtime, new formal
files, generated tables, developer examples, or any new predictions. The author
read the public `ab490a8` / 0.12.0a3 interfaces and published historical results,
the pinned QAC source, and pinned primary grammar/Lean sources. The implementation
team received API/scope questions and this protocol's design, but not the fresh
lexical targets or answers before the material freeze. Shared-workspace separation
is procedural, not a filesystem access-control claim. The data are neither an
untouched natural corpus nor human-adjudicated gold, and the result must not be
reported as general Arabic comprehension accuracy.

The material contains **86 cases**, **74 question calls**, and separate read,
reference, morphology, query, replay, and invalid-input obligations. There are
30 designated positive episodes, four withheld-realization transfer episodes,
32 boundary episodes, eight acquisition controls, and 12 replay/context cases.
Some boundary cases deliberately require a positive sub-result as well as a
forbidden overreach. The denominator and every such obligation stay fixed.
The scorer must report individual layers and must not relabel a missed positive
as a successful abstention or combine all safe deferrals with end-to-end gains.

## Public interface contract frozen before implementation inspection

The intended public operations are `read_discourse(text, lexical_model=...,
context=..., source_id=..., scope=...)`, `ask_discourse(text, question, ...)`,
and independent replay of reports and answers against the original text,
question, lexical model, context, source identity, and scope. Concrete output
field names are an adapter concern; semantic expectations below are fixed.
An adapter correction cannot change a word, context premise, source exclusion,
expected claim, expected answer, or expected blocker in the material.

Context is a strict canonical JSON premise with named entities, optional
speaker/addressee IDs, deictic mappings, and an explicit closed-reference-scope
boolean. It contains no predicate, role, answer, valency, or case labels.
The supplied name is a naming/noun premise; its missing grammatical properties
are not acquired facts. Grammatical case/sign checks in the gold target words
with independent lexical evidence; the gold does not supply declension labels
for newly authored names. Group participants are one explicit entity ID and do
not license invented members. Repeated names with distinct IDs remain ambiguous.

Claims and questions compare **predicate lemma, predicate kind, voice, ordered
entity arguments, polarity, tense, time, place, restriction, and scope**.
`predicate_bw` in the gold identifies the exact QAC lemma field and the accompanying
Unicode value is its declared projection. It is not a root synonym or a policy
answer. `property`, `event`, and `location` predicates are distinct; an active
actor cannot be replaced by a passive patient. No claim establishes world truth.

## Source partition and leakage controls

The source is QAC 0.4 decoded SHA-256
`a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46`.
`independent_source_inventory_v1.json` records the source hash, exact record
locations/byte spans, full word segment recompositions, and the source profiles.
The raw scan that selected witnesses imported no NABT code.

`qac_full` uses source-known lexemes in newly authored texts and contexts. It
does not claim that the lexemes were never seen by the learner. `qac_form_holdout`
excludes a fixed **union of 83 complete verses**, selected by four terminal FORM
realizations, before learning. The excluded forms are absent from the retained
source, while compatible independently recorded u/i forms of each lemma remain.
The inventory records those witnesses **after the joint split**. This avoids
the old inflection benchmark's T15/K10 premise-closure failure. The four cases
measure transfer to an unseen terminal realization of a known lemma/root family,
not unseen-family induction. A separate unknown-family case requires abstention.

The learner receives raw source bytes and exclusions only. It does not receive
this file, case IDs, questions, expected roles, claims, answers, or manual source
inventory classifications. Context has its separately declared restricted
schema. Source POS/LEM/ROOT/person/gender/number/aspect/voice and segmentation
remain supervised annotations; successful use of them is not raw acquisition of
those labels. CASE/MOOD erase/poison comparisons change source identity, so they
compare semantic outputs rather than proof fingerprints. They must not supply
CASE/MOOD to the predictor indirectly through expected conclusions.

No normalized copy of the test answer is admitted as source. The unknown-family,
source-withdrawal, wrong-case, tense-mismatch, and participant-mutation cases
check this separation. Historical 74/22/32, morphology/word gold, and broader
40/12/8 data remain untouched. Any historical rerun is explicitly published
regression, never a newly held-out result.

## Meaning of expected fields

- `required_claims`: a complete current-source assertion with all listed
  qualification fields. It must have a replayable proof tied to one coherent
  reading/event. A parser candidate, source annotation, or a property found only
  inside an unresolved alternative is insufficient.
- `forbidden_claims`: exact overreaches forbidden in admitted/accepted claims.
  `no_grounded_claims` forbids all admitted entity-grounded claims, including
  invented subjects. Retained mention, question, or morphological candidates
  are allowed and are not counted as assertions.
- `required_readings`: source-byte-anchored observations. Multiple requirements
  with the same span may require different alternatives, as in the ت person
  ambiguity. Within one requirement its features, role, case, and reference
  must all belong to the **same** reading. A role must bind its actual clause,
  governor, case domain, occurrence, sign witness, and support records.
- Reference `candidates` is an exact set within the declared bounded context:
  unknown gender/number keeps competitors, compatible antecedents are all
  retained, and repeated mentions of the same entity are deduplicated by ID.
  `bound: null` prohibits an asserted selected referent. An explicit `bound`
  requires the declared speaker/addressee/deictic premise or a closed, adequate,
  unique prior-reference witness. No nearest-candidate shortcut is allowed.
- `SUPPORTED`, `REFUTED`, and `CONFLICT` require support for the requested signed
  qualified proposition, its opposite, or both respectively. No absence-based
  refutation. `BINDINGS` requires exactly the listed binding set, with a current
  proof per binding and the question's variable position retained. Place/time
  answers retain the underlying event/tense rather than answer an unrelated
  predicate. Closed time labels in this data are اليوم / أمس / غدا, identified
  by their source spans and exact supported reading; this does not permit
  arbitrary diacritic/root normalization of lexical predicates.
- `NO_GROUNDED_SUPPORT` accepts only a result without accepted positive or
  negative support for the requested proposition/binding. An explicit unknown,
  out-of-scope, or deferred result may satisfy the safety condition. A crash,
  invalid-source diagnostic on a valid input, or a report containing a contrary
  accepted proof does not. Such success is a blocker result, not positive
  question understanding.
- `force` records a known scope/force requirement. An imperative can be
  nonassertive without choosing order versus request versus prayer. The primary
  source does not determine pragmatic intent from the imperative alone.
- `restriction_must_be_preserved` means any accepted restricted claim retains
  the source restriction; no unknown global universe is negated. A separately
  justified positive entailment is not prohibited merely because the source
  also carries restriction.
- `no_material_implication` prohibits converting an unsupported causal fragment
  into an ordinary inference rule. It does not deny that separately complete
  asserted causal clauses can have source-qualified content.
- `distinct_nun_positions` requires both nun kinds within one reading, with
  distinct, complete, current-source Arabic clusters. A present nun span must
  include its combining marks and lie within its host stem/segmentation. A
  deleted nun has no nonempty invented source span. Reading alternatives cannot
  be pooled to manufacture this evidence.
- `forbid_inflected_case_without_complete_witness`,
  `forbid_person_promotion_from_final_t`, and `forbid_predicate_from_root` are
  authority checks. The scorer must inspect the corresponding support/reading
  authority rather than ignore these fields. Raw spelling observations remain
  allowed; asserted class/role/meaning needs its declared independent premise.
- Replay cases first require the unmodified result to verify, then require old
  report/answer rejection under the specified source/context/question/model
  mutation. Omitted versus explicitly withdrawn lexical model must be distinct.
  Question-only mutation applies to answer verification; it does not require an
  otherwise unmodified source report to become invalid.
- Invalid context cases require a named structured invalid-input diagnostic,
  no traceback, and no source report/answer admission. Valid duplicate names are
  tested separately from invalid duplicate IDs. Strict booleans reject integer 1.

## Primary-source interpretation boundaries

The source audit records exact pins and windows. Ihala/IhalaHasr prove laws over
supplied features, rank/context, and candidate domains; their singleton is not
an unsupplied real-world referent. A relative clause needs a compatible return,
but classical grammar licenses some hidden/deleted returns under other premises.
The missing-written-return case therefore tests the declared bounded reader,
not a universal rejection of valid Arabic. Dual demonstratives and relative
forms have their stated inflection exceptions; no general assertion that every
deictic/relative is built may be introduced by the scorer.

Temporal qualifiers require a governing event/state predicate. A time word alone
must not manufacture a predicate for an entity. A compound temporal idafa is
outside the declared first scope and must not be erased to admit an unqualified
event. Question, wish, hope, causal fragments, and unresolved scope cannot leak
their embedded payload as an ordinary accepted fact.

## Measurement and preserved history

1. Freeze case JSON, source inventory, source audit, and this protocol before
   opening new implementation files. Publish only counts and hashes to the
   implementation team at that point.
2. After an approved runtime freeze, build a read-only adapter against public
   output fields. Pin every gold artifact by hard-coded SHA-256 and verify the
   approved runtime manifest, snapshot, archive, actual inventory, and import
   origins. A self-consistent arbitrary manifest is not authority.
3. Run every case without changing inputs or exclusions. Preserve first raw
   reports, answers, source/profile receipts, adapter source archive, runtime
   origin, version, output hash, timings, and every failure reason. Resource,
   adapter, invalid-input, scope, coverage, and false-accept failures are distinct.
4. Add adversarial scorer tests that alter claim polarity/qualification,
   reference/reading IDs, governor/case linkage, proof identity, or the requested
   variable. A matching noun/role elsewhere cannot repair a false certificate.
5. If the adapter is wrong, retain its first raw measurement and archive, write
   an explicit erratum, correct only the adapter, then rerun the unchanged
   runtime/gold. If runtime changes after opened feedback, preserve the earlier
   result and compare the same final adapter on pinned before/after runtimes.
   Later performance is a post-review comparison, not another untouched holdout.
6. Report strict episode completion and separate positive-reference/query,
   form-transfer, acquisition-control, blocker, replay, and invalid-context
   counts. Every positive answer must be tied to its exact claim/query and
   current proof. No false acceptance receives a documented-boundary waiver.

The public a3 historical baseline reports 0/40 broader episodes, 8/12 scope
supplement episodes, and 0/8 original excerpts. That published denominator is
preserved. A new discourse score must identify its new interface, premises, and
material; it cannot be presented as a replacement score for the historical
benchmark without actually running that published regression separately.
