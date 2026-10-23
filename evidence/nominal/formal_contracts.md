# Nominal-evidence formal contracts

## Result and verification scope

`formal/Nabt/NominalEvidence.lean` and `formal/ExportNominalEvidence.lean` implement the independent conditional law `nabt.nominal-evidence.v1`. The pinned Lean 4.34.1 toolchain built all 46 configured jobs successfully. The enforcing axiom audit passed for **520** manifest theorems, including **44** new nominal-evidence theorems, and separately scanned every compiled declaration in the NABT namespace. The only observed axioms were `propext`, `Quot.sound`, and `Classical.choice`; no project axioms, `sorry`, `admit`, or `native_decide` were added.

This records a successful formal build and axiom audit, not a completed runtime evaluation or release. Actual logs are `artifacts/local/nominal-formal/axioms.json` and its `.log` sibling. Upstream Mashru was inspected as pinned source, not rebuilt in this audit.

## Generated registry

`src/nabt/data/nominal_evidence.json` was produced directly by `lake env lean --run ExportNominalEvidence.lean`: **33,622 bytes**, SHA-256 `0b0218d75329e1b04302ebdf875a4a43db772d4650b3415bc767f2a6a96d07a8`. `evidence/nominal/law_schema.json` gives every field, enum, bit order and domain.

| Table | Complete finite domain | What it means |
|---|---:|---|
| Profiles | 22 of 24 coded products | Gender × grammatical-number form × definiteness; feminine true sound-masculine class excluded, masculine sound-feminine morphology retained. |
| Receipt activation | 128 masks | Source, scope, occurrence, reading, active, blocker, noun-domain prerequisites. |
| Cardinal rules | 202 rows | 101 quantities (1–99, 100, 1000) × witnessed singular gender. |
| Weak positions | 8 masks | W/Y presence in each supplied canonical triliteral radical slot; masks 3 and 7 remain explicit residuals. |
| Manqus complete models | 32 masks | Five necessary flags; only mask 31 satisfies their conjunction. |
| Pronoun projection | 14 readings | New Unicode spelling projection of the pinned Mashru table; two gender readings for both هما and أنتما. |

## Independent correspondence and authored boundary checks

`tools/check_nominal_conformance.py` rebuilt the Lean targets, reran the exporter, rejected duplicate JSON keys/non-JSON constants, and compared the complete packaged and exported structures with type-sensitive JSON equality. It then checked the installed functions against independently stated semantic relations: all **2,048** constraint subsets; **133** lists of length at most two, with **253** single deletions and **253** duplications; **128** receipt masks; **202** cardinal rows; **8** weak-position classes and **27** bounded public root projections; **32** complete manqus models; and all **14** Unicode pronoun rows and canonical reader probes. The successful result is recorded in `artifacts/local/nominal-formal/conformance.json`.

The gate's receipt/manqus coverage concerns their complete truth tables. It does not certify unrestricted source qualification or the general Unicode partial-mark reader. `tests/test_nominal_laws.py` separately passed **17** authored boundary tests, including Boolean-as-integer rejection, compound-hundreds domain exclusion, masculine sound-feminine morphology, preservation of ambiguous pronouns, final-ya gemination, absence of an observed condition remaining unknown, and rejection of foreign source/scope receipts. No independent evaluation gold was read to construct either the reference relations or these tests.

## What the general theorems establish

Candidate membership is equivalent to admissibility and acceptance by every admitted constraint. Deleting a constraint or receipt cannot narrow the surviving list; duplicate constraints and reordering do not change it. Conflicting masculine/feminine constraints produce an empty list. These are proofs about the actual list-filter definitions, not assertions that a source reader has activated the right linguistic rule.

An accepted receipt has exactly the target binding and a true noun-domain premise. Source identity includes revision; occurrence identity includes byte interval and segmentation. Foreign, inactive or blocked receipts are inert. Raw article, tanwin, suffix and pattern observations are inert. A noun-domain failure produces no nominal profiles. Linguistic truth, source qualification, support-span interpretation and Unicode parsing remain external obligations.

The cardinal support theorem equates membership in the exported quantity list with the supported-domain predicate. Outside that domain the guarded rule returns no result. Zero and composite/unlisted hundreds do not acquire a rule by modulo arithmetic. The counted-case field is a conditional construction requirement; it grants no actual syntactic case or attachment. Cardinal value does not select an ordinal reading or prove a world-entity count.

Weak radical membership is exactly W/Y, and all eight position vectors have distinct class outputs. The generic proof accepts a supplied `Fin 3 → Char`; validating the 28-radical alphabet is a separate boundary. The label `sound` means absence of W/Y, not absence of hamza or doubling. No attestation or reverse weak-letter transformation is proved.

For nominal manqus, acceptance is equivalent to five true flags: noun, inflected, necessary final ya, preceding kasra, and ungeminated final ya. The last flag makes the counterexample **كرسيّ** explicit. The preceding kasra refers to the phonological neighbor, not the last written vowel before a geminate cluster. Positive and negative premises are independent; no observation leaves both possible truth values. An unknown evidence set retains every complete model, while a positive/negative conflict on any feature eliminates them.

Distinct occurrence counting depends only on membership in the supplied ID list. Duplicate IDs and ordering are irrelevant; equal cardinality cannot reconstruct sequence order. Source-inventory binding, linguistic number and world references are not inferred by this arithmetic.

The pronoun inventory is a newly declared Unicode projection of `Jisr.QiraaSimat.damairKhalaya` at `e4c801ffe9171dadedcc3aae23051ea0953ae361`. Inventory uniqueness and the two dual ambiguities are proved for this list. No equivalence theorem between Unicode marks and A116 cells, or between this canonical table and a partial-vocalization reader, is claimed. Gender code 2 is deliberately unspecified in the projection; the upstream table calls it shared. Definiteness comes from a separate qualified pronoun rule.

## Source audit

`evidence/nominal/source_audit_mashru.json` identifies 113 selected declarations across 21 focused source files, and hashes all 120 tracked Lean files against the pinned Git objects. Its Markdown companion explains why semantic noun classes, numeral grammar, encoding, evaluation counts, and denotation agreement must remain separate. The source audit is descriptive provenance; these new NABT proofs do not import an upstream assumption as an axiom.

## Advertised theorem inventory

### Profiles and qualified receipts (20)

- `Nabt.NominalEvidence.profiles_complete`
- `Nabt.NominalEvidence.profile_code_injective`
- `Nabt.NominalEvidence.profile_inventory`
- `Nabt.NominalEvidence.masculine_sound_feminine_retained`
- `Nabt.NominalEvidence.refine_exact`
- `Nabt.NominalEvidence.no_constraint_retains_all`
- `Nabt.NominalEvidence.deletion_cannot_narrow`
- `Nabt.NominalEvidence.duplicate_constraint_idempotent`
- `Nabt.NominalEvidence.constraint_order_irrelevant`
- `Nabt.NominalEvidence.refinement_composes`
- `Nabt.NominalEvidence.contradictory_gender_empty`
- `Nabt.NominalEvidence.activation_exact`
- `Nabt.NominalEvidence.admitted_binding_and_domain`
- `Nabt.NominalEvidence.foreign_receipt_inert`
- `Nabt.NominalEvidence.inactive_or_blocked_inert`
- `Nabt.NominalEvidence.observed_shape_inert`
- `Nabt.NominalEvidence.nonnominal_has_no_profiles`
- `Nabt.NominalEvidence.qualified_candidate_has_domain`
- `Nabt.NominalEvidence.accepted_constraint_has_receipt`
- `Nabt.NominalEvidence.deleting_receipts_cannot_narrow`

### Cardinal (6)

- `Nabt.NominalEvidence.Cardinal.support_exact`
- `Nabt.NominalEvidence.Cardinal.rule_exact`
- `Nabt.NominalEvidence.Cardinal.unsupported_no_rule`
- `Nabt.NominalEvidence.Cardinal.no_zero_or_composite_hundreds`
- `Nabt.NominalEvidence.Cardinal.opposite_involutive`
- `Nabt.NominalEvidence.Cardinal.quantities_inventory`

### Weak (4)

- `Nabt.NominalEvidence.Weak.radical_exact`
- `Nabt.NominalEvidence.Weak.classify_injective`
- `Nabt.NominalEvidence.Weak.root_mask_exact`
- `Nabt.NominalEvidence.Weak.sound_iff_no_weak_slot`

### Manqus (8)

- `Nabt.NominalEvidence.Manqus.accepted_exact`
- `Nabt.NominalEvidence.Manqus.models_complete`
- `Nabt.NominalEvidence.Manqus.partial_exact`
- `Nabt.NominalEvidence.Manqus.unknown_retains_all`
- `Nabt.NominalEvidence.Manqus.unknown_does_not_decide`
- `Nabt.NominalEvidence.Manqus.negative_noun_blocks_acceptance`
- `Nabt.NominalEvidence.Manqus.final_gemination_blocks`
- `Nabt.NominalEvidence.Manqus.contradictory_features_eliminate`

### Occurrence counts (4)

- `Nabt.NominalEvidence.count_depends_on_members`
- `Nabt.NominalEvidence.duplicate_occurrence_idempotent`
- `Nabt.NominalEvidence.occurrence_order_irrelevant`
- `Nabt.NominalEvidence.equal_count_does_not_recover_order`

### Pronoun projection (2)

- `Nabt.NominalEvidence.pronoun_inventory`
- `Nabt.NominalEvidence.dual_pronoun_gender_ambiguous`
