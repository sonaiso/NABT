# Inflection reader: independent review before the freeze

## Scope and method

This review inspected `src/nabt/inflection.py`, `corpus_evidence.py` and
`inflection_reader.py` against the conditional Lean contracts. It did not
read independent evaluation gold, choose held-out answers, or change runtime
code. The implementation owner made the corrections below. The checks in
this report are source inspections, except for the separately identified
executed law and table-adapter gates.

The review does not certify a general Arabic parser. The reader's declared
grammar acquires a bounded set of preposition, lam and lan attachments.
The eleven relations in the law remain conditional requirements; the reader
does not acquire all eleven merely because they occur in that table.

## Findings and disposition

| Finding | Concrete failure or risk | Disposition checked in source |
|---|---|---|
| Endpoint recorded at the wrong extent | In an attached preposition, the head lies inside the written occurrence. The old receipt recorded that whole occurrence as dependent while testing disjointness against a different, narrower stem span. | Corrected. `_relation` records the dependent `span` as `stem_span`, retains `occurrence_span` separately, includes `reading_id`, and tests disjointness against the recorded span. |
| Rule-match bit duplicated kind compatibility | Bit 1 is `rule_match` in Lean; using the kind-compatible Boolean for both bit 1 and bit 6 does not explicitly check the declared rule-to-relation mapping. | Corrected. The source maps `min_preposition` to `preposition_object`, `lam_activation` to `imperfect_jussive`, and `subjunctive_lan` to `imperfect_subjunctive`; bit 1 checks that mapping independently of kind. The head binding records `rule_id` and `occurrence_id`. |
| One tanwin promoted construction | A single tanwin observation is insufficient to establish inflection; built tanwin-bearing forms are a counterexample to that general implication. | Corrected. Construction no longer follows from tanwin alone. A qualified number/lemma recomposition or a pair of distinct terminal-vowel families is required. |
| Weak noun shape promoted construction | A final weak carrier with a plausible root does not by itself establish all noun/inflection/necessary-carrier prerequisites. | Corrected for construction: the weak nominal class observation alone no longer selects `inflected`. |
| Homographic witnesses crossed feature identities | Combining terminal forms by lemma/root/consonantal spelling alone can mix POS, gender, number or internal vocalization readings. | Tightened. `nominal_key` includes lemma, root, spelling, POS, gender, number and internal template. Construction-support records are retained. |
| Unknown plural form became broken plural | Failure to recognize a sound plural, even with a separately attested singular, is not a proof of broken plural; annexed and unsupported formations remain possible. | Corrected. The complement-of-recognizer inference was removed. Singular witnesses remain source-relative alternatives, with POS compatibility. |
| Contradictory prefix marks were stripped | A prefixed form such as a geminated preposition or an explicitly conflicting article mark could have received a licensed segmentation after stripping those marks. | Corrected. Prefix and article alternatives use `plain_marks`; explicit conflicting vowels, shadda and dagger alif block the affected alternative. Missing marks remain missing evidence. |
| Weak deletion ignored carrier geometry | A weak root plus an arbitrary final carrier is insufficient to license deletion. A geminated final carrier or incompatible preceding vowel can invalidate the projection. | Corrected. Full-base transfer requires a non-geminated final carrier and the corresponding preceding fatha/damma/kasra before alif/waw/yaa. The full base and its records are retained. |
| Deleted nominal yaa fell into ordinary-noun fallback | A form such as `قاضٍ`, with a yaa-final lemma/root, must not become `iSahih` merely because its written final yaa is absent and tanwin is present. | Corrected with an explicit `DELETED_NOMINAL_YAA_UNIMPLEMENTED` boundary: no declension-class selection or inferred construction for that path. |
| Built forms allowed a mutable final vowel | A known built feminine-subject or past reading must not acquire arbitrary final-vowel alternatives through the inflected lookup profile. | Corrected. Built templates preserve the final mark and matching uses `mutable_last=False` for built readings. |

## Conditional premises that remain external

The paired terminal-form rule is an **empirical reading hypothesis**, not a
Lean theorem that a lexeme is always inflected. Even a fixed lemma, root and
internal spelling can have context-dependent construction; `قبلُ`/`قبلِ`
and `بعدُ`/`بعدِ` illustrate why a generic implication from two terminal
vowels would be too strong. The implementation must present its evidence
basis and narrow frame scope, retain unresolved alternatives and defer
unsupported constructions. The proof does not infer a universal lexical
construction from this observation.

A retained lemma/root annotation is a premise from a particular corpus
record, not an independently established etymological root or meaning.
`weak_root_profile` classifies supplied radical positions conditionally.
The weak-deletion transfer additionally requires a qualified imperfect,
person and full-base form. It never concludes that an arbitrary short
written form is a jussive merely because a weak carrier is absent.

Similarly, singular witnesses are separately observed source forms with
compatible lexical annotations. They are not generated singulars, an
automatic broken-plural classification, or an assertion about external
entities. Unrecognized dual/plural paradigms require explicit boundaries.

The Python receipt includes heterogeneous provenance: grammar passages,
new head/dependent occurrences and external training records. For the Lean
support-span abstraction, the occurrence spans are the same-source textual
witnesses; corpus and grammar records justify external lexical/rule premises.
The formal `SupportSpan.validFor` predicate alone does not authenticate those
external records or establish their linguistic truth.

`lexical_index` accepts the typed source object and recompiles from its raw
bytes, exclusions and declared source identity. It does not accept a caller
dictionary of successful analyses. The report verifier regenerates the
report from text plus independently supplied lexical evidence and compares
the complete strict serialization. Thus a report's claimed hash or status
does not itself grant authority. This is a source-replay property, not proof
that the source annotation is correct.

## Executed checks, distinct from this source review

- The 19 authored law boundary tests passed.
- The fresh Lean export matched the complete packaged JSON, with
  type-sensitive comparison and independent finite references.
- Table adapters passed 16 sign-context comparisons, 60 class/case
  projections, 66 relation/kind/construction combinations and all 256
  receipt masks, plus order and empty-domain checks.
- The axiom audit passed for 561 registered theorems, including the 41 new
  inflection theorems, using only the three standard axioms documented in
  `formal_contracts.md`.

These results are recorded under `artifacts/local/inflection-formal/`.
They do not constitute a final frozen-runtime evaluation. The complete
repository gates and independent held-out evaluation are run by the release
owner. No additional optional full gate was run during this review.

The final rule/endpoint correction was inspected after creation of the
58-file runtime freeze `evidence/inflection/code_freeze_v1.json`:

```text
manifest_sha256 fe93f8ebebb21078113462244052da93c102f4d5a673c2636c0cab27e0ffa103
snapshot_sha256 aaac387085d745b89f0260eb1905d66dade8a710e483034442e7957972243ede
```

The three reviewed runtime files and generated inflection table had their
SHA-256 hashes and byte lengths checked against the manifest. All matched. This check binds
this source review to the freeze; it does not replace verification of the
complete freeze archive or the release tests. All ten findings above have
their recorded correction or explicit boundary in that reviewed source.
