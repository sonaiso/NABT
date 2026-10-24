# Independent Arabic coverage holdout v1

## Purpose and independence

This suite is a new adversarial composition holdout for the NABT coverage work
started from commit `f0064f0a4baab3cc816087a322aabc0c8fbb2d19`. It was authored by
an independent agent before that agent read any pending implementation, ran any
NABT predictions, or inspected the original frozen gold expectations. The
runtime implementers were not given the case-by-case gold before the material
freeze. Broad requested topics and an ambiguity warning were shared, so the
suite is not a secret task definition or a lexical holdout.

The author read `AGENTS.md`, pinned public scope documents, source-law contracts,
primary-source policy records, public example lexical/context formats, the
pinned public `discourse.py` module, the public report-producing tail of
`discourse_reader.py`, and the lexical-model entry point. The baseline API read
included its exposed matching/replay logic. No claim of ignorance of the prior
system is made. No pending patch or new runtime was inspected before freezing.

The new JSON material, lexical TSV, authoring script, this protocol, and the
independent harness are pinned by `freeze.json` before any prediction run.
The complete original construction and discourse gold is untouched. These
36 new cases and their questions must remain separate from both original
86-case denominators.

## What the runtime receives

Every call receives only a case's exact source text, separately named context,
raw authored QAC-format lexical bytes, source identity and scope. Questions are
separate public API inputs. Expected statuses, claim patterns, rationales,
grammar source references and cross-case checks never enter production inputs.

The lexical premise file is authored teaching material. Its locations are
synthetic. It contains lexical forms, lemma/root annotations, morphological
profiles and independently supplied prefix/suffix partitions. It contains no
CASE/MOOD fields, assigned syntactic roles, attachment labels, entity IDs,
answer labels, or test sentence analyses. Explicit full nominal forms prevent
the test from demanding unseen accusative-alif generation. A lexical annotation
is a premise, not a discovered fact or a naturally sampled corpus attestation.

The context is the documented entity/participant context only. Names, identity,
gender, number, kind, speaker, and closure are independently supplied premises.
The context does not contain propositions, roles or answers.

## Oracle and metrics

Cases have five distinct categories:

* **positive**: the complete reading, relevant semantic claims and specified
  answers are required. Safe abstention fails coverage.
* **coverage_challenge**: a requested broader frame with explicit authored
  semantic scope. H17's ordinary matrix `ما` negation is deliberately not
  presented as an already promised API capability or as a theorem about every
  use of `ما`. Safe abstention is a coverage miss, not a false acceptance.
* **ambiguity**: incompatible meaning alternatives lack a disambiguating
  premise. The system must defer rather than select one by position, closeness,
  spelling or a convenient answer.
* **boundary**: a visible grammatical conflict or absent required identity
  prevents the proposed reading. The system must not repair or invent it.
* **force_boundary**: a complete question, wish, hope or quoted mention must be
  recognized without creating an asserted factual claim. Mere failure to parse
  is insufficient to pass these cases.

The oracle checks exact public document status; required or forbidden semantic
claim patterns; specified minimum/maximum claim counts; specified clause force;
exact question status; nonempty grounded proof/counterproof fields when those
statuses require them; report and answer replay; source identity and bytes; and
binding of answer proofs to actual document claims. It does not recompute the
production parser, use private reader helpers, infer semantic success from
source-string echo alone, or allow expected gold to repair runtime output.

An exact same-text question is only one check. Many cases also use a changed
participant, reversed arguments, removed or changed qualifier, bare embedded
property, opposite polarity, or nonassertive-source question. Claim checks and
independent cross-case checks add obligations beyond string replay. Nevertheless
this is a bounded authored API suite, not a complete linguistic parser audit.

The harness reports all case and check failures. It reports category totals,
question statuses by expectation, unsafe acceptances, runtime exceptions,
cross-case checks and replay checks separately. No waiver list changes the
strict result. Exit status zero requires all required case, cross-case and
replay checks, no runtime exceptions, and an unchanged runtime and freeze.
Boundary success is never reported as an affirmative answer.

Report/answer replay is an integrity obligation, not an extra comprehension
case. Context-withdrawal replay and exact-byte cross-context checks have their
own denominator; they are not added to the 36 language cases.

## Scope and qualifications

Primary-source references are pinned in `source_premises.json`. The source
passages support conditional grammar constraints. They do not establish each
new sentence's acquisition, all possible readings, the correctness of this
authored oracle, or the truth of its assertions in the world.

H03-H05 and H09-H14 are compositions beyond isolated source exemplars. H06 and
H12 preserve ambiguity allowed by the available agreement evidence. The PP
case specifically has two masculine, singular, genitive, definite candidates
for the adjective. No undocumented preference for the nearest noun is allowed
to turn that input into a unique meaning.

Queries which drop a modifier are expected to remain unsupported under NABT's
published exact qualified-claim policy. That is a product semantics decision,
not a general linguistic claim that qualified statements never entail weaker
statements. The public ontology offers no independent field for the intended
attachment of H06 or H12. A broader implementation must represent alternatives
or introduce a separately authorized, documented context interface; the test
must not sneak an answer into an existing identity field.

H17 distinguishes denial of a belief from belief in a denial. H16-H20 keep
operator scope, polarity and tense separate. Their controls must not acquire
bare embedded facts even if exact scoped-question matching is supported.

H21 and H22 contain exactly the same utterance bytes, `أَنَا حَكِيمٌ.`, with
different permissible speaker identities. H23 omits the speaker. The expected
owners in H21 and H22 differ. This is a finite counterexample to the claim that
every utterance has a uniquely recoverable intended meaning from its written
form alone. It is not a theorem of general linguistic undecidability and does
not prevent useful conditional inference when the needed context is supplied.

No finite score here proves full understanding of Arabic, pragmatics,
metaphor, all dialects, arbitrary lexical senses, every attachment, world truth,
or all future inputs. Any reported improvement is measured coverage under the
listed premises. Every remaining failure is retained with its exact input.

## Execution and retention

The first runtime execution is delayed until the root agent says the pending
implementation is ready. The harness checks every frozen input hash before
importing NABT, records the complete runtime input inventory before/after,
retains one raw JSONL record for each API call, and refuses to overwrite result
or raw-log files. Ordinary exceptions are captured as failures rather than
disappearing from the denominator.

Run from the repository root, using a fresh output filename:

```sh
PYTHONPATH=src python tools/arabic_coverage_holdout_v1.py \
  --output evidence/arabic_coverage/holdout_v1/runs/first.json
```

The authoring script is provenance, not part of the evaluator. It uses only the
Python standard library and pinned source records; no runtime import or
prediction is needed to build the material. After freezing, errors in material
or the harness require a documented addendum or a new version. Keep the first
result and raw log; never edit a failed expected answer to match a prediction.
