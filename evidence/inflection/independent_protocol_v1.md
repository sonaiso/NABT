# Independent inflection review: frozen protocol v1

Status: **frozen before the first new implementation read**. The associated
74-case material and independent conditional sign matrix are now fixed. This
protocol records a measurement contract, not a benchmark result. It was written without
opening the new inflection reader, corpus learner, formal inflection module, or
generated inflection table. Existing source grammar, the old word law, and
published earlier evaluations may be inspected. The shared repository is at
`880fad4b1c613813ca02e6288bd87a46de90d1e5` when this review begins.

The companion `independent_prior_gap_audit_v1.json` records the exact old
artifacts and source passages used in this diagnosis. No old material or result
is changed by this work.

## 1. The prior failures identify different tasks

| Published result | What the missed cases actually require | What a new sign layer would not establish by itself |
| --- | --- | --- |
| Word pilot 27/30, positive subset 12/15 | The three missed inputs already have installed lexical templates and candidate class/case pairs. Their closed frames remain blocked by `VOCALIZATION_OR_LEXICAL_SELECTION_EVIDENCE`. | Discovery of a new lexeme or root. Releasing a frame on weak evidence would not be a valid acquisition improvement. |
| Morphology regression 39/43 | Four cases retain the expected sole kind candidate but do not license it because the descriptive source contains an unparsed clause. | Four wrong noun/verb classifications. Unconditionally ignoring an unparsed condition would weaken the source contract. The corrected 43-case set is now public regression material. |
| Broader Arabic 0/40 complete episodes | Nominal roles, unsupported clauses and quantifiers, negation, reference, ambiguity, revisions, and scope remain open. | Completion of semantic episodes from a case sign or a corpus role label. |

The old word failures are w15–w17. The old morphology failures are m12, m13,
m32, and m33. Exact expectations, observed blockers, prior file hashes, and the
broader residual counts are in the companion audit. Those examples are public
regressions and cannot be relabeled as this review's held-out transfer data.

## 2. Agreed implementation boundary

The agreed public reader is:

```python
read_inflection(text, *, lexical_model=None, source_id="input", scope="default")
```

The optional model is learned from a source rather than installed as an
answer-bearing policy dictionary:

```python
learn_qac_lexicon(raw_bytes, excluded_verses=tuple(...))
```

The allowed training fields are source FORM and segmentation, POS, LEM, ROOT,
person, gender, number, aspect, and voice. Case/mood labels and syntactic roles
are excluded from predictor input. The learned noun transfer can change only a
licensed terminal case-vowel realization of the same supported stem. Generic
nominal inflection requires at least two distinct terminal vowel witnesses with
the same lemma, root, letters, POS, gender/number features, and internal
vocalization. A single tanwin is insufficient. Declared dual/plural recomposition
requires its explicit number and exact compatible lemma premises. A weak root or
weak-looking noun ending alone cannot license construction or manqus properties. It does
not prove a new lexical meaning. Root and gender are source claims carried by
compatible readings. A proposed plural-to-singular origin requires an actual
singular attestation compatible in lemma and root, not a lemma spelling alone.

Five-verb transfer requires imperfect/person evidence and a compatible source
form. Final-weak deletion requires a full witnessed base and a declared
transformation. A missing final letter is not such a witness. Feminine nun
requires the appropriate person/gender/number and attested suffix. An EMPH tag
does not resolve direct versus separated emphasis attachment. A radical nun
must be supported by a compatible root and surface analysis.

The initial mandatory frame set is closed preposition/object and lam/lan plus
one imperfect. Attached b/k/l require a witnessed segmentation. General idafa
and VSO are not in this first scope. Inna/kana with two independently classified
nouns are separately reported optional extension cases if implemented; they
are not silently added to the mandatory denominator.

The formal sign law covers the 15 existing word classes and their 45 admitted
class/case combinations. It distinguishes signs
`damma`, `fatha`, `kasra`, `sukun`, `waw`, `alif`, `ya`, `nun_retained`,
`nun_deleted`, and `weak_deleted`; realization modes `overt`, `estimated`, and
`deletion`; and `original` versus `substitute` relative to the case. A theorem
over supplied class/case premises is conditional algebra, not a proof that the
reader discovers the premises.

## 3. Separate measurements

There will be no single percentage that treats all these tasks as equivalent.

| Track | Predictor input | Measured output | Claim allowed |
| --- | --- | --- | --- |
| Conditional sign law | Explicit class/case and applicable conditions | Sign, realization mode, origin, admitted domain | Agreement with the finite conditional law |
| Corpus annotation replay | An identified QAC/MASAQ record and its annotations | Restored source fields, spans/record identity, retained ambiguity | Faithful reading of annotated evidence |
| Known-lexeme transfer | Raw test phrase plus allowed source-trained model; target realization absent from training | Supported stem/class/root reading and case-sign alternatives; an actual role/case only inside an admissible closed frame | Transfer to a new written realization of an already witnessed lexeme |
| Unknown-family boundary | Raw test phrase with a model having no compatible family witness | Explicit unknown/candidate alternatives without invented attestation, class, root, or role | Sound abstention outside acquired lexical support |
| Attachment chain | Raw phrase plus independent lexical and segmentation support | A source/occurrence/reading-specific marker-to-target relation and compatible role/case | Bounded composition for the declared frame |
| Withdrawal and adversarial evidence | Removed/replaced source, unsupported scope, conflicting marks, changed boundaries | Recomputed result, preserved alternatives, no stale authority | Evidence sensitivity and exact replay |

Known-lexeme transfer is supervised source transfer. It is not unsupervised
discovery, unseen-root lexical acquisition, or a new natural-language training
method. Unknown-family examples cannot be counted as successful root
acquisition merely because the reader correctly abstains. Authored shapes can
test a structural hypothesis without establishing that an Arabic word or root
is attested.

Within the raw-reader track the report must separate:

1. Positive coverage on cases whose specified evidence supports the requested
   reading and closed frame.
2. Candidate recall and ambiguity retention where the evidence allows multiple
   correlated readings.
3. Wrong activation count, including invented actual roles/cases, omitted
   alternatives, or authority borrowed from a different source/occurrence.
4. Correct abstention on deliberately unsupported or underdetermined cases.
5. Explicitly unsupported challenge coverage, which is not inflated by treating
   every `DEFER` as success.

An overall pass count may summarize a fixed test contract, but all these
denominators remain visible. A positive miss remains a miss even if safe
deferral is preferable to an unsound answer.

## 4. The annotation boundary

QAC is pinned to `Saleh1967/Alghanem` commit
`9d8fa03a51f894416e0abaf3b6821c5ae6441dcd`, file
`corpora/qac/quranic-corpus-morphology-0.4.txt.gz`. The decompressed SHA-256 is
`a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46`.
Its FORM field is a Buckwalter **segment**, and LOCATION includes a segment
coordinate. Passing FORM rows or segment coordinates as the raw test input
would reveal a segmentation answer. Raw test words must be reconstructed under
a documented projection without exposing their component boundaries to the
reader. The reconstruction operation is not itself learned segmentation.

MASAQ's Arabic source is the same pinned repository, `corpora/MASAQ.csv`, SHA-256
`d43d2a813afbe0490254bb26623d6041ed352a273d333e731ddbcda3bd0b6f3a`.
`Word` is the full written word, repeated across component rows.
`Segmented_Word`, `Morph_type`, `Invariable_Declinable`, `Syntactic_Role`,
`Case_Mood`, `Case_Mood_Marker`, `Phrase`, `Phrasal_Function`, and `Notes` are not
raw acquisition evidence. The observed schema has no explicit dependency-head
identifier. A role annotation cannot supply the missing selected attachment.

The source audit reports duplicate MASAQ coordinate tuples. Each annotation
witness therefore needs the dataset hash plus its preserved CSV record index
or byte interval as well as the locator. No duplicate is silently discarded.
Different translated/transformed copies have different source identities.

QAC and MASAQ annotate overlapping Quranic text. Splitting by corpus name does
not produce independent linguistic holdout. All parallel verses, component
rows, and relevant orthographic variants must be grouped together. A future
cross-corpus experiment must disclose shared source text even if its annotation
schema is different.

The evaluator stores gold annotation separately from the input view. It never
passes target class/case, root, role, source locator, segmentation, or an answer
description for the test occurrence to `read_inflection`. Allowed training
claims remain separate from the held-out occurrence's gold.

## 5. Split and blindness rules

Exact new test words, roots, and source locators are authored by the independent
reviewer before the new implementation is opened. The builder initially
receives the task strata, interface requirements, counts, and cryptographic
hashes only. This is procedural independence in a shared workspace, not a claim
of cryptographic access control or an untouched external corpus.

The test set contains 74 raw-reader/control cases: 20 unseen realizations,
12 context/ambiguity cases, 10 nun/nominal boundaries, 8 unknown-family cases,
16 attachment/representation boundaries, and 8 source counterfactuals. The
independent sign matrix has 45 admitted rows and 15 excluded class/case
combinations. These denominators are separate. The freeze manifest fixes every
material hash before the first implementation read. Source-derived examples
and authored grammatical contrasts are labeled separately. An authored
contrast is not presented as a modified Quranic quotation.

For genuine unseen-realization transfer, the excluded verse set must remove
every training occurrence of the held-out target stem realization, including
the same realization under another prefix or suffix when that would disclose
the target transformation. Excluding only one verse while leaving the exact
form elsewhere does not suffice. The retained source must still contain the
necessary independent base witness. The manifest records both checks.

For an unseen-family boundary, all compatible family witnesses must be absent
from allowed training; it is insufficient to remove the exact spelling.
Repeated forms, diacritic variants, parallel source text, and same-lemma/root
links are checked for split leakage. Any folding used for this *audit* is
explicitly named and does not change the runtime's exact source representation.

The frozen training view and its exclusion list have their own hashes. A
read-only source corpus may remain available for provenance, but inference must
not look up held-out rows or their target labels behind the model interface.
Runtime file-access and imported-data inspection after the code freeze checks
this boundary. A clean model trained on redacted case/mood/role fields must
preserve predictions. Poisoning those forbidden fields must not change the
acquired content. Training occurrence identity may change with the full source
hash; that alone is not a semantic failure.

The primary model excludes 48 complete verses after a conservative split-only
orthographic alias audit. Each of the eight positive noun transfers has at least
two retained compatible terminal-vowel witnesses; all 20 target realizations are
absent under the audit profile after exclusions. The audit groups stop/ornament
marks and dagger-alif variants as a leakage precaution. Runtime inputs retain
their exact spelling and the production lookup contract permits only the
declared wasl/bare-alif equivalence. The five absent family roots are separately
checked against the retained source.

No release claim calls this material an untouched natural corpus. The reviewer
has inspected source grammar and corpus annotations to construct and adjudicate
the gold. The independence is from the new implementation, and the transfer
split is explicit and reproducible.

## 6. Required counterexample families

### Sign versus written ending

- A built word's written vowel does not create an inflectional case.
- Dual and sound masculine plural ya retain the nasb/jarr alternatives without
  an independent attachment or role witness.
- The kasra of an added-alif/taa plural can realize nasb or jarr; the origin is
  relative to that case. A diptote fatha has a different ambiguity and requires
  the actual absence/presence of the relevant al/idafa conditions.
- Six-noun letter realization requires all applicable lexical/construction
  conditions, including the relevant possessive attachment. A matching final
  letter or a root label does not establish the construction.
- Maqsur/manqus and weak imperfect estimated signs are not visible marks.
- A missing mark is not a zero-valued visible sign. A missing final radical is
  not a licensed deletion without a base comparison.
- Internal hollow-verb contraction is distinct from deleting a final weak
  radical. A shared weak-root label must not merge the two transformations.

### Nun and segmentation

- Five-verb inflectional nun versus a lexical radical nun.
- Feminine-plural subject nun versus emphasis nun; emphasis needs its actual
  attachment evidence, including direct versus separated attachment.
- Protective nun versus inflectional nun and suffix-pronoun identity.
- Dual/plural noun nun deletion in idafa versus five-verb nun deletion under a
  nasb/jazm governor. General idafa is recorded as a boundary in the first
  release, not inferred from a missing nun.
- Final letter sequences resembling dual/plural/five-verb suffixes do not
  establish the corresponding class.
- A proposed split must restore all original bytes and preserve alternative
  compatible segmentations; matching a substring cannot skip literal material.

### Attachment and authority

- Prefix b/k/l versus the same letter at the beginning of a lexical stem.
- Marker expectation does not manufacture a noun or imperfect-verb class.
- An attached pronoun's role depends on its actual host/attachment; a familiar
  spelling does not select its syntactic position or real-world referent.
- Quotes, punctuation, newlines, and non-horizontal separators do not silently
  transmit governor force across boundaries.
- Single-word analysis does not create an actual phrase role from a unique
  conditional case candidate.
- Model withdrawal or source replacement must remove conclusions that depended
  on that model. A copied status, class code, source hash, or receipt cannot
  substitute for recomputation.
- Distinct occurrences and readings cannot exchange base witnesses, root
  claims, segmentation, nun kind, or attachment evidence.

The source basis for these families is recorded in the companion audit:
Qatr lines 64–95 and 336–345; Alfiyya lines 61–124, 506–517, and 834–849. Exact
source hashes and byte intervals accompany those windows. These are linguistic
premises, not assertions that the new reader already supports every family.

## 7. Scorer boundary and first measurement

The frozen case schema is adapter-independent. Each case records an identifier,
track, raw text, training profile, expected correlated reading obligations,
forbidden activations, source/authoring basis, and the reason the evidence is
sufficient or insufficient. Expected candidate sets may be lower bounds where
genuine homographs exist; actual licensed claims require exact source-qualified
compatibility. Expected fields are never an argument to production code.

The adapter maps the public output schema onto these obligations only after the
gold hash has been saved. It does not modify production code or use production
sign tables as its oracle. Source positions are independently recomputed from
the preserved UTF-8 input. Any full-span or per-reading identity assertion must
use the actual source/occurrence and segmentation.

The first execution archives the evaluator bytes, runtime/table hashes,
training hashes, command/environment, raw per-case output, adapter exceptions,
and aggregate strata. It is preserved even if the score is zero or the adapter
is wrong. A genuine adapter defect is corrected with an explicit erratum and
old/new hashes, then a separately named result. A linguistic failure is not
repaired by changing the gold. Implementation fixes may be measured in later
separate runs; once opened, the frozen set is a public regression.

The final report distinguishes the frozen first run from the release runtime
if any bytes change between them. It retains old 27/30, 39/43, and 0/40 results
as historical measurements until an explicitly named replay is actually run.


## 8. Frozen files and adapter convention

- `independent_cases_v1.json`: 74 adapter-independent cases.
- `independent_split_v1.json`: source pins, 48-verse exclusion closure, model
  counterfactual definitions, independent projection, retained witness locations,
  and per-case leakage diagnostics. Gold/source audit fields never enter the
  predictor.
- `independent_sign_law_v1.json`: independently authored 45 admitted and 15
  excluded class/case combinations.
- `independent_prepare_v1.py`: preparation only; imports no NABT module and never
  reads the new runtime/formal/table. It refuses to overwrite material.
- `independent_freeze_v1.json`: file hashes, counts, blindness statement, and the
  already-announced runtime freeze identity.

The later evaluator accepts `--qac PATH` (original plain or gzip source) and
`--output PATH`. It checks the decompressed source hash, constructs the permitted
models with the frozen exclusions, and calls only the public reader/verifier.
The fixture's role names `preposition_object` and `governed_imperfect` are semantic
labels mapped explicitly to the public API; they are not arguments supplied to
production. A positive `actual_case` obligation is checked at the correlated
reading/assignment, not inferred by collapsing an occurrence's independent
class/case candidate lists.

The source identity counterfactual permits identity changes mandated by changed
source bytes. Its invariant is the semantic content supported by allowed
features. Any failure of a positive case remains in the positive denominator;
metamorphic equality of two uniformly empty outputs cannot erase that failure.
