# Construction reader: initial independent code review

This review used the implementation and authored development fixtures.
It did not open the independent evaluation material. The runtime was still
being developed; the diagnostic records below are not immutable release
snapshots or a language score. No runtime file was changed by this reviewer.

The native law and finite adapter checks are recorded separately in
`formal_contracts.md`. Passing those checks does not establish the reader's
acquisition of their premises.

All diagnostic records and authored input files referenced below are preserved
byte-for-byte in
[authored_review_records.tar.gz](pre_freeze_review_artifacts/authored_review_records.tar.gz),
with their original repository-relative paths and individual lengths/hashes in
[manifest.json](pre_freeze_review_artifacts/manifest.json). The deterministic
archive contains 15 files (157,399 uncompressed bytes), occupies 9,681 bytes,
and has SHA-256
`7dcb30e57bd61c5a2b35f81f2ba644e104c1e4bc796cf0629eb2ca829a4622ba`.
Thus references to `artifacts/local/...` below also identify the corresponding
members of this committed evidence archive; keeping a local workspace is not
required to retain the review records.

## Reproduced findings sent to the reader owner

The first four observations used construction-reader SHA-256
`67fdcff1c75e315b24a1ac155f9ba7ed571c44a787e1f234192a1e883e086ed5`.
Their output is preserved in
`artifacts/local/construction-development/review-authored-counterexamples-v3.json`.
The additional teaching rows and context are in `review-authored-extra-v3.tsv`
and `review-authored-context-v3.json` in the same directory. The teaching rows
are appended to `examples/discourse_training.tsv`; they are authored fixtures,
not quotations from QAC.

1. **Operator person was not enforced.** With a source-attested first-person
   `كُنْتُ`, `كُنْتُ زيدٌ رحمةً.` became `LICENSED_DISCOURSE` and asserted
   the past property رحمة of Zayd. The initial `_operator_obligations`
   admitted a third-person subject because its membership check included
   `3` independently of the operator's person. A bounded operator-before-
   overt-subject frame needs its own licensed agreement regime; the first-
   person source cannot be silently interpreted as a third-person operator.

2. **Passive input entered an active operator frame.** With source `PASS`,
   `ظُنَّ زيدٌ هذه كريمةً.` became licensed with `zanna_subject`, two active-
   frame objects, and a scoped belief attributed to Zayd. Source matching in
   `_operator_candidates` did not reject the unsupported passive frame.
   Voice and any subject/object suffix geometry must remain part of the
   frame's admission conditions.

3. **A competing lexical sense was discarded.** `رَأَى زيدٌ هذه كريمةً.`
   became licensed with only `sense=certainty`. The supplied source also
   contained a full object-pronoun witness for رأى. The same observed case
   pattern supports visual رأى plus a hal; the initial early return from
   `operator_frames` prevented that competing production from surviving.
   The source policy itself distinguishes visual رأى from the two-object
   cognitive sense (Sibawayhi 406–409, within `zanna_sisters`). An adjacent
   nominal/adjectival accusative does not settle that distinction. Preserve
   the unresolved sense or the competing readings unless another witness
   licenses the cognitive use.

4. **`لا` with a perfect continuative was asserted without a force gate.**
   `لا زال زيدٌ رحمةً.` became an asserted, past, continuative scoped claim.
   The source audit independently confirmed a supplicative reading:
   Sibawayhi 9008 and 9010–9011, and Sharh Ibn Aqil 1875–1878. A preceding
   `لا` is not enough to choose `ASSERT` for this perfect form. The force
   alternative must remain unresolved or be independently licensed.

The fifth observation used construction-reader SHA-256
`e136edd1214b5d0581871c514037c6ec9cea05f35f67e3c9c5e366faad34fbd3`.
It is preserved in `review-authored-tamyiz-time.json`, with teaching rows
in `review-authored-tamyiz-time.tsv` in the same local directory.

5. **Noun POS and a verb list did not license nisba tamyiz.** The teaching
   source supplied اشتعل as a verb and ساعة as a singular noun through two
   terminal realizations. `اشتعل كتابٌ ساعةً.` became licensed with a
   `tamyiz/nisba` relation and an empty time field. Here ساعة is a duration
   adjunct. The initial branch accepted any singular `N` after one of
   امتلأ/اشتعل/طاب, although noun POS does not establish that particular use
   as a specification of the relation. A witnessed construction/use or an
   unresolved alternative is required; excluding one counterexample word
   would not repair the general missing premise.

The reader owner was sent each finding before freezing. This initial record
does not claim that later fixes have passed an independent recheck.

## Evidence-boundary observation

The initial composed-idafa path converted `not any(tanwin glyph)` and
`not any(present nominal-nun receipt)` directly to `denied`. In an unvocalized
text or absent receipt list, these are missing observations. They are not
negative witnesses consumed by `idafa_head_status`.

The existing simple-idafa path already licensed an unvocalized conditional
reading such as `كتاب زيد كريم`. No separate wrong semantic result for that
historical path was established by this review. The actionable difference
was the new path's claim to have witnessed absence. Its premises must either
come from explicit supported realization evidence, remain possible, or be
described as conditional candidate constraints; they cannot be relabeled
observations. Preserving an older declared conditional profile does not
justify reporting an unobserved trait as negative evidence in the new law.

## Positive separation check

The initial reader correctly kept two distinct assignments for both authored
examples `كاد زيدٌ يكتبُ.` and `كاد زيدٌ أن يكتبَ.`:

- The predicate clause received local nasb, with domain `clause_local_case`.
- The internal imperfect received raf without أن, and nasb under its own
  witnessed أن relation.
- The output claim retained the outer proximity scope and did not emit the
  embedded event as a bare source assertion.

These observations are in
`artifacts/local/construction-development/review-authored-counterexamples.json`.
They confirm the tested separation only, not every clausal construction.

## Confirmed pre-freeze recheck

The same five authored counterexamples were rerun after the reader owner's
corrections. The initial files above were preserved. The new record is
`artifacts/local/construction-development/review-fixed-counterexamples.json`,
SHA-256 `4465f7eefd4d75eeefd4c0731c263df436fc2d6e3edaadb2b2b6ee5ded2825a9`.
It records the hashes of the six reader/source modules inspected at that time.

All five now return `DEFER` with an empty top-level claim list:

| Authored counterexample | Retained reason |
|---|---|
| `كُنْتُ زيدٌ رحمةً.` | `CONSTRUCTION_CONFLICT` |
| `ظُنَّ زيدٌ هذه كريمةً.` | `PASSIVE_OPERATOR_REQUIRES_DIFFERENT_ARGUMENT_FRAME` |
| `رَأَى زيدٌ هذه كريمةً.` | `POLYSEMOUS_OPERATOR_SENSE_REQUIRES_INDEPENDENT_CONTEXT` |
| `لا زال زيدٌ رحمةً.` | `CONTINUATIVE_LA_PERF_PRAYER_OR_ASSERTION_REQUIRES_CONTEXT` |
| `اشتعل كتابٌ ساعةً.` | `TAMYIZ_VERSUS_OTHER_NOMINAL_USE_REQUIRES_SOURCE_FRAME` |

The four operator cases also retain `CONSTRUCTION_LAW_GATE`. The nisba
correction obtains the exact exemplified verb/unit pairs from the replayed
primary paragraph; it does not blacklist the example word ساعة. Inspection
also confirmed that the new composed-idafa production requires an overt
terminal realization and class-qualified nun evidence. It no longer calls a
missing mark or a missing receipt an observed negative. The historical simple
conditional idafa profile remains separately bounded.

## Additional quantified-prefix finding and correction

Review of the new counted-tens branch found one further concrete error.
With `examples/construction_training.tsv` and an authored full `kataba` + `ka`
object-pronoun witness, both `كتب زيدٌ عشرين كتابًا.` and
`كتب زيدٌ بعشرين كتابًا.` initially returned `LICENSED_DISCOURSE` with the
same semantic arguments and restrictions. The second assigned `بعشرين` the
role `direct_object` and case `nasb`: the numeral filter did not exclude its
licensed `prefix_relation`, so the preposition was lost from the interpretation.

The owner added that exclusion and a focused regression test. This reviewer
reran the prefixed counterexample once: it now returns `DEFER`, no claims,
and no complete analysis. The new record is
`artifacts/local/construction-development/review-quantified-prefix-recheck.json`,
SHA-256 `b566f26c1d5900adb06191764e257dfc7ea365716774509f0989b692bf556859`.
It preserves the exact extra teaching rows, current module hash, and a reduced
record of the initial tool output. The initial full report for this additional
case was not saved; the record does not claim otherwise.

## Final bounded inspection of the new bridges and gate

The following are code-review findings, not new Lean parser theorems:

- The operator gate recomputes span identities against the original source
  bytes. Its edges use the selected reading IDs and exact operator/target
  occurrences. It checks the family's required roles, cases and head spans,
  whole-token coverage, replayed source-policy support, unresolved obligations,
  and assignment compatibility before the finite law can activate. Referent
  resolution remains a separate gate. No caller-supplied gate result is used.
- The nominal carrier bridge requires both an independently attested complete
  accusative-alif form and a matching ordinary paired base paradigm. It matches
  POS, lemma, root, gender, number and internal template, preserves source
  receipts and observed base/carrier spans, rejects a marked final alif in this
  profile, and rebinds nun receipts to the resulting reading ID. It does not
  generate an absent carrier or assign a dependency by itself.
- Source-qualified spatial readings now include the lexical source ID and
  supports in their reading identity. Inspection of `زيدٌ فوقَ المكتبِ.`
  confirmed separate accusative adverb and local nominative phrase assignments,
  with their reading IDs present in the same analysis. The relation remains a
  source-relative spatial qualification; no ownership or coordinate is created.
- Quantified nominal arguments remain structured terms, not newly invented
  entity IDs. The query matcher now checks that `?person` and `?place` bind
  strings with the corresponding explicitly supplied entity kind; a structured
  quantified term cannot reach a dictionary lookup as an entity identifier.

No additional material defect was established in this bounded review after
the quantified-prefix correction. This is not a general completeness claim,
a release gate, or a score on the independent evaluation. The independent gold
was not opened, and the reviewer made no runtime changes.
