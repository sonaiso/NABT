# Independent construction evaluation — frozen authored protocol v1

## Independence and scope

This material was authored by the evaluation agent before reading the new
construction implementation, generated construction law, or developer examples.
The agent read the published 0.13.0a2 discourse interface, the previous release's
source conventions, and primary grammar passages. The baseline archive was
extracted independently and its 67 authoritative files checked against the pinned
discourse v4 manifest. Only the old public learner was invoked before freezing,
to confirm that the authored lexical TSV parses; no new or old construction
predictions were used to choose expectations.

The evaluator subsequently receives the same raw input, explicit lexical source,
and explicit communicative context as the production interface. Expected roles,
attachments, scopes, and answers are held in this directory and are never passed
to the reader, learner, context, or grammar policy. The independent source fixture
may be disclosed after this freeze so developers can inspect its format. The
remaining material remains unopened by the runtime developer until the first
runtime freeze. A source fixture disclosed at that point is not a secret lexical
holdout; this evaluation measures new composition from supplied lexical premises.

This is independently authored, source-informed test material. It is not an
untouched external corpus, an Arabic-wide coverage estimate, or human-adjudicated
natural-language gold. All examples are new compositions, not quoted QAC clauses.
The baseline is 0.13.0a2, discourse freeze v4, manifest SHA-256
`f1e035f7d20395abb82c2e87ac42f374630bef6bab71a22490873c7a08e8e519`.

## Frozen inputs and supplied authority

`independent_cases_v1.json` has 86 cases: 80 comprehension cases (43 positive,
31 boundary, and 6 ambiguity cases) and six replay episodes. There are 106
questions including the six replay questions. Case identifiers have prefixes C
(controls), K (kana), I (inna), Z (cognitive verbs), A (approximation/hope/onset),
D (idafa), N (na't), H (hal), M (tamyiz), B (badal), W (tawkeed), and R (replay).

`independent_training_v1.tsv` supplies 140 authored lexical words in 183 segments
using the public QAC-like four-column format. These are explicit authored source
claims, not QAC quotations or claims of corpus frequency. Supplied fields are
FORM, POS, lemma, root, gender, number, person, aspect, and attested prefix/suffix
segmentation. There are no CASE/MOOD labels, construction labels, syntactic roles,
attachment targets, coreference answers, expected query answers, or policy labels.
Terminal forms and full clitic hosts are written source attestations; the reader
must still discover their use and attachment in each fresh input. All three noun
endings may occur in the source. This is not an unseen-ending test.

Temporal T entries are deliberately authored temporal lexical premises. They do
not purport to be original QAC T annotations. The source distinguishes ADJ and N;
this is supplied lexical authority, not newly acquired derivational semantics.
An N annotation alone does not establish every jamid/masdar sense or every
tamyiz relation. The positive tamyiz cases ask whether the new source-backed
construction machinery can establish the licensed ratio relation; an unresolved
premise is a coverage miss, not grounds to silently add a per-case role label.

Context contains only explicit entity IDs, names, gender, number, kind, and closed
reference scope. A name is a naming premise, not a predicate, role, case, or world
fact. The nested-idafa case supplies the bare house name separately in its own
context. The prepositional-idafa case explicitly describes its door referent as
a place; that classification must not be inferred from the spelling. The source
does not equate two context IDs merely because their names can be appositional.

`independent_sources_v1.json` preserves the primary grammar windows as exact
bytes, ranges, and SHA-256 hashes, plus the authored lexical-word inventory.
The texts remain governed by their existing source licenses. The source-audit
agent's separate construction audit informed the limits, but its claims are not
runtime input answers.

## What counts as comprehension

Positive cases require a complete compatible analysis of the bounded input, the
listed roles and cases, the listed attachments, the qualified semantic result,
and the specified answers. A successfully verified DEFER report is not positive
comprehension. Case success is the conjunction of all frozen requirements.
Component totals are also reported so that a role failure is not hidden by an
unrelated successful query or replay.

Expected role and relation names are neutral semantic labels. The adapter may
document an explicit mapping from public output names to these labels. It may
not infer a role merely from the expected position, invent an absent relation,
or turn a proposed relation into an activated one. Every activated role, sign,
reference, and scope must be linked to the same viable analysis and reading.
Candidate alternatives from different analyses cannot be pooled into a success.

Anchors are frozen UTF-8 byte spans. `occurrence_or_licensed_stem` permits the
public occurrence span or its explicit licensed lexical stem span. It does not
permit arbitrary substrings. Governors, dependents, and return owners are checked
against their own spans/identities. The clausal predicate in the approximation
family has local nasb while its inner imperfect has a separate raf or nasb
requirement. The two must not be collapsed into a single token case.

`required_claims` requires the exact semantic fields: predicate lemma, predicate
kind, voice, argument IDs, polarity, tense, time, place, and restriction. Source
identity and evidence must remain bound through the public certificate. Permitted
representation mapping may normalize a time object to its source-qualified form,
but may not erase a qualifier or operator. A word's root cannot replace its lemma.

`required_scopes` requires the matrix operator family, source lemma or specified
surface, aspect when listed, matrix participant, polarity, and full embedded
proposition to remain in one accepted scoped claim. Plain kana preserves the
published past-property projection, with the operator retained in its relation.
Other kana sisters, cognitive verbs, approximation, hope, and onset preserve the
declared operator semantics. Inna's plain emphasis projection remains permitted.
Wish and hope particles do not assert their bare complements. This contract does
not claim that every use of a knowledge verb is philosophically nonfactive; it
tests the explicitly bounded source-relative projection agreed for this reader.

`required_qualifications` requires the named dependent, semantic owner, and event
or predicate attachment in the same accepted qualified claim. Removing idafa,
na't, hal, tamyiz, time, or place from a question does not automatically preserve
support under the declared strict-qualification equality law. A hal property
must not become a permanent property of its owner. `forbidden_claims` checks
top-level admitted facts, not the nested propositions retained inside a scope.

## Ambiguity and boundaries

The declared reader is bounded. Safe DEFER is allowed on unsupported material;
it is not a claim that the sentence is impossible Arabic. In particular, rare
كاد + أن must not be categorically rejected merely because the common form lacks
أن. Boundaries involving case, definiteness, or leftover material constrain the
declared complete single-clause reading, not every ellipsis, cut adjective,
quotation, or alternate construction allowed elsewhere in Arabic.

Frozen Boolean/list requirements have these meanings:

- `no_grounded_claims`: no admitted top-level proposition from this incomplete or
  nonassertive input. A retained candidate analysis is allowed.
- `required_force`: the input must retain the named question/wish/hope force in
  an applicable analysis or clause; it must not be silently treated as assertion.
- `forbid_unique_cognitive_reading_from_lemma_alone`: compatible perceptual/full
  and cognitive interpretations remain alternatives, or the system abstains.
- `forbid_bare_embedded_property`: no unqualified matrix-external property is
  admitted from a cognitive/perceptual candidate.
- `no_categorical_linguistic_rejection`: absence from the reader's bounded profile
  cannot yield a claimed general Arabic impossibility.
- `preserve_idafa_chain_order`: the nested head-to-complement edges must be
  distinct, ordered, and source anchored; an unordered ownership bag is not one.
- `forbid_activated_idafa`, `forbid_activated_hal`, `forbid_activated_tamyiz`,
  `forbid_activated_badal_part`, and `forbid_activated_tawkeed`: no licensed
  relation or actual assignment of the named type. Unactivated candidates are
  permitted and must not produce accepted facts.
- `hal_owner_candidates`: all listed compatible owners must be retained as
  candidates in their own analyses; source gender may exclude incompatible owners.
  `forbid_arbitrary_unique_hal_owner` forbids promoting one of those alternatives
  without an additional source premise.
- `required_relation_candidates`: at least the listed candidate alternatives are
  represented. This is a candidate-coverage requirement, not permission to activate
  them or merge their referents.
- `forbid_context_identity_merge`: distinct input IDs are not equated or replaced
  by one another merely through case agreement or juxtaposition.
- `forbid_whole_from_part`: a part reading does not admit the corresponding
  whole-object event.
- `forbid_arbitrary_unique_badal_reading`: an unsupported intention such as
  correction or identical-reference apposition cannot be selected as certain.

The evaluator must implement every frozen requirement or report an adapter error.
It must never silently ignore a requirement it does not understand. Retaining a
safe DEFER can pass an absence-of-authority check while failing required candidate
coverage. Such cases are not counted as positive understanding.

## Questions and replay

`SUPPORTED` requires a complete matching query and an admitted positive proof.
`UNKNOWN` requires a complete matching query without a proof or counterproof for
that fully qualified proposition. `NO_GROUNDED_SUPPORT` is a boundary check: DEFER
or UNKNOWN is acceptable, but SUPPORTED, REFUTED, INCONSISTENT, or a grounded
binding is not. A query marked complete must not gain credit from parse failure.
Source question input must never become evidence for its own answer.

The six R cases are scored in a separate replay denominator. They require a
valid original read and answer certificate and rejection after the exact frozen
premise mutation: text, question, context, lexical-source withdrawal, scope, or
source ID. A changed question invalidates the answer certificate, not the
unchanged source reading. Mutation payloads are frozen in the material. Replay
success is never added to comprehension totals.

## Measurement and retention

Freeze the material, source, source audit, and this protocol before reading new
runtime code. Record hashes, counts, the baseline manifest, and the independence
statement in `independent_freeze_v1.json`. Do not change these files to improve
measured results. Any later issue in the authored expectations must be disclosed
as an erratum and separately scored, leaving the original first run intact.

The first run and any adapter defect are preserved with raw reports, output,
adapter source, dependency hashes, and the exact approved runtime snapshot. Run
the same final adapter against the old and new frozen runtimes in fresh isolated
processes. Do not let imported modules from the checkout substitute for the
selected runtime. Verify the complete authoritative inventory and archive pins;
a self-consistent arbitrary manifest is not an approved baseline.

Report strict case totals, positive/boundary/ambiguity components, roles/cases,
attachments, semantic scopes, actual question outcomes, and replay separately.
List every miss, false acceptance, and adapter error. No comparison gate may turn
partial linguistic coverage into complete success. Post-review repairs and their
extra examples must be labelled as such; the first held-out authored measurement
and historical discourse/inflection/nominal evidence remain immutable.
