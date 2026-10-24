# Independent completion oracle, version 1

## Purpose and independence

This is a directed reference for four proposed areas of Arabic coverage:
geminated noun identity, nominal number evidence, tamyiz attachment and scope,
and verbs with attached participants. It contains **24 authored cases**, six
per family. It neither replaces the original construction/discourse gold nor
changes either original denominator of 86. A new failure cannot be excused by
this material or by a high score on another family.

The author read `AGENTS.md`, the original gold, retained runtime-v2 residual
reports, existing independent validators, public teaching-input conventions,
and pinned primary source texts. That prior-system exposure is intentional
and disclosed. No post-change runtime implementation or predictions were read
before freezing this material. The parent disclosed proposed narrow context
name and N/ADJ morphology bridges; general counterexamples were discussed.
No statistical blind experiment, random sample, secret task definition, or
lexical holdout is claimed. The author is independent of the pending runtime
implementation, not ignorant of the public system and prior results.

The pre-change merged main is
`d791fd7730cde2256dfac8a27687010b392876b3`; its tree matches the prior PR head
`9f776b598e4f61012e0b6577cd92351ab29eae42`. Source passages and audit-input
identities are obtained from that immutable Git version. The authoring code
uses only the Python standard library and Git reads. It never imports NABT,
calls its reader, asks a validator to accept a prediction, or runs a model.

## Four kinds of authority

These must remain distinct in every result:

1. **Primary grammatical passages.** `source_premises.json` records exact
   previously deposited source bytes, offsets, authorship, hashes, scope and
   primary URLs. A passage can justify a conditional rule without attesting a
   new target word or an intended reference in a particular sentence.
2. **Authored lexical premises.** Three small QAC-format teaching profiles
   provide source forms, roots, lemmas, POS, morphology and segment boundaries.
   Their locations are synthetic. They are not quotations or naturally
   occurring corpus observations. No `CASE`, `MOOD`, dependency, attachment,
   reference identity, gold answer or target-clause analysis is supplied.
3. **Authored identity/context premises.** Context supplies only the public
   entity catalogue, declared traits, speaker/addressee and closure fields.
   Naming an entity does not acquire its declension, shadda, lexical number,
   word sense, an antecedent mention, or a true proposition.
4. **The oracle.** Expected claims, relations, candidate sets, constraints and
   explanations are the author's judgments under this declared domain. They
   are never runtime inputs. Errors in this layer must be recorded separately
   from parser gaps and corrected by a versioned erratum, never overwritten.

The QAC primary documentation defines S, D and P and explains pronoun profiles.
Its morphological-features page does not state a default from omitted number
to singular. Its explicit voice/mood defaults do not authorize inventing a
number default. This limited source finding is not a claim that every QAC
resource was exhaustively searched.

## Material and public inputs

`cases.json` is the reference; `contexts.json` is the supplied context map;
`lexical_profiles.json` identifies each exact TSV profile. A runtime call may
receive only the case's text, source ID, scope, selected context, and the model
learned from the selected raw TSV. A question is a separate query input.

The base teaching corpus intentionally includes every أكرم verb occurrence
inside a connected word with a separately supplied object suffix. A detached
host is not taught as a whole word. The host's person and the suffix's person
are separate observations. QAC notation is used as an input format; the
synthetic word locations do not claim historical authority.

N03 withdraws only S from the matching feminine-singular adjective records.
N06 supplies both N and ADJ paradigms for the same lemma, with a number feature
present only on ADJ. These controls cannot be answered by copying a feature
from the desired contextual person or from a neighboring lexical reading.

All fixed-status cases are evaluated within the specified direct constructions.
Marked poetry, corrective ellipsis, quotation of a word as a name, homonymous
proper-name reinterpretation without an alias premise, exceptional invariant
adjectives, and arbitrary pragmatic accommodation are outside those probes.
They are not declared impossible in Arabic.

## Denominators and outcomes

There are **22 cases with fixed document-status obligations** and **two
provenance probes**, N03 and N06. The latter must not be reported as successful
language coverage merely because the system defers. Their obligation is to
preserve the source evidence and alternatives and to justify any new inference.
They do not prohibit a genuinely independent, source-backed future derivation.

The execution report must show all 24 cases and separate at least:

- positive and coverage-challenge successes/failures;
- boundary, missing-context and ambiguity integrity;
- recognition of complete nonassertive force;
- the two conditional provenance outcomes: checked derivation, correct
  abstention, unsupported inference, or unresolved independent review;
- every question status, source/answer replay, runtime error and unsafe claim;
- cross-case checks, which have their own denominator and are not extra
  language cases.

Safety is not inferred from a `DEFER` label. The underlying claims, activated
roles, bound references and evidence receipts must also obey the constraints.
Conversely, safe abstention fails a positive coverage expectation. A crash,
invalid input, resource exhaustion and a linguistic rejection are different
results and must remain distinct.

`UNKNOWN` for a query that drops a qualification uses NABT's existing exact
qualified-claim policy. The source passage does not prove that natural-language
entailment cannot weaken a description. The scorer must not repeat the former
H18 error: an unknown variable answer may retain valid negative counterproofs
without returning any positive binding. Any such counterproof still needs
complete independent validation.

## Checks specified before prediction

The extraction/scoring contract is semantic, not a copy of runtime branches:

- Preserve source bytes, IDs, scope, model inputs and context identities.
  Content hashes alone are not proof of linguistic correctness.
- Match required/forbidden claim patterns against accepted claims, preserving
  the full qualification. Event argument order matters. Do not infer success
  from exact-text question echo.
- Check each required modifier relation against the same accepted claim's
  proof analysis, the exact governor/dependent/target readings and spans,
  active assignments and resolved references. A lexical lemma elsewhere in
  the sentence does not establish that relation.
- Gemination evidence must come from the same learned reading and complete
  target occurrence. An entirely unvocalized identity label may be underspecified;
  a contrary explicitly marked identity label must not enter that bridge.
- Number and gender must keep their recorded origin. Case-pattern transport
  between compatible nominal readings, if independently justified, must not
  silently transport POS, semantic sense, gender, number or a referent.
- A tamyiz qualifier must preserve its actual owner. T03 deliberately places
  the owner in the direct object, while T01/T02/T06 use intransitive subjects.
  Membership in `claim.args` is necessary in these examples but insufficient
  to prove which argument owns the qualifier.
- Attached subject morphology and object-pronoun morphology require separate
  source partitions and reference obligations. Neither a bare lemma nor a
  suffix's person grants a whole verb's complete person/aspect/voice profile.
- Ambiguity cases must retain every specified possible identity. Unknown
  features do not mean incompatible features. The nearest compatible identity
  is not automatically the intended one.
- Each question must retain all viable complete interpretations. Evidence
  cannot be borrowed from another analysis, clause, relative-clause predicate,
  query pattern or context. Subresults and all signed receipts must be checked
  before computing consensus; incomplete alternatives are not dropped.
- Replay every document and answer using the frozen runtime, and reject replay
  against changed speaker context for P04/P05. Replay verifies a certificate
  against that implementation; it is separate from independent oracle checking.

`adversarial_checks.json` adds predeclared mutation/control recipes for these
boundaries. They are separate validator obligations, not hidden extra cases in
the 24-language-case denominator. Their positive certificates may be collected
after the material is frozen; expected refusal conditions are already fixed.

## Execution, freeze, and review procedure

1. Run `author_material.py` to materialize the authored files, then review
   their text and static integrity. This invokes no runtime predictions.
2. Freeze every authored file using `freeze_material.py`. Verify the resulting
   hashes before constructing any model or asking the pending runtime to read
   these cases. The freeze does not itself authorize a runtime's release.
3. Author or review the public-API execution adapter against this contract
   before its first prediction. Pin its code and the candidate runtime
   separately. It must log every call and keep original failures and exceptions.
   If an output field needed for a predeclared check is unavailable, report
   that check as unvalidated; do not invent a success or change the expectation.
4. Run only after the parent declares the candidate snapshot ready. Preserve
   original raw observations, scorer version, complete inputs, runtime inventory,
   and all denominators. Do not replace the earlier original-86 or holdout-v2
   artifacts, or infer permission to waive any original check.
5. If an oracle defect is discovered, retain the first result and original
   freeze; issue a separate sourced erratum and explicitly labeled rescore.
   Such a rescore is not a new independent prediction experiment.

The two same-text speaker cases are a concrete ambiguity counterexample:
text alone does not distinguish the two permitted actors. The source-bound
context resolves that particular ambiguity. Neither the example nor any
finite score proves full Arabic understanding or general undecidability.

## Review limits and the original metrics

The retained original construction result was 80/86 and discourse 63/86.
Those are observed scores under their frozen oracles, not a list of 29 proven
errors in Arabic. CON-Z10 has the earlier documented هل + explicit matrix
negation input defect under the selected Ibn Hisham norm. CON-Z02/Z07 have
unresolved occurrence-level sense obligations. Other retained residuals mix
acquisition, complete-form composition, reference, lexical agreement and scope.
The new audit records these categories without changing old gold or scores.

The current checks remain conditional on adequate lexical/reference premises
and on the separate source/certificate audit. A formal iff for a small grammar
may prove completeness within that grammar while leaving word acquisition and
membership in that grammar as independent obligations. This suite does not
close those obligations by giving the runtime the expected analysis.
