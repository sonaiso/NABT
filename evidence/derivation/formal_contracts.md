# Derivation contracts and proof scope

Recorded 2026-10-23 against Lean **4.34.1**. This report records a successful
native build, Lean export, axiom audit, source-template comparison, and focused
runtime review. It does **not** certify the later full repository gate, an
installed wheel, or a release. The complete theorem inventory remains
[`formal/theorems.json`](../../formal/theorems.json).

## Installed law and provenance

The generated `nabt.derivation-patterns.v1` registry contains **71 patterns**:
31 exact Ishtiqaq templates, 2 new nominal Unicode projections, 11 new sound
imperfect Unicode projections, and 27 new primary-grammar projections. There
are 68 three-slot patterns and 3 four-slot patterns. The exact profile is
`stem_exact_v1`; the carrier identifier is `nabt.arabic-radicals28.v1`.

The same generated JSON contains the separately named
`nabt.verb-paradigm-availability.v1` law: **64 rows**, ordered by positive mask
then negative mask, with index `positive * 8 + negative`. Bit positions are
past, imperfect, imperative. This law does not classify nominal jamid/mushtaq.

The installed file has **28,213 bytes**, including its final newline, and SHA-256:

`0b4d6673c033955490468ad595fc1e988890bba282101e81a80580d3fc1fbf2f`

The upstream source is Alghanem commit
`9d8fa03a51f894416e0abaf3b6821c5ae6441dcd`. The source audit records exact file
and declaration hashes in
[`source_audit_alghanem.json`](source_audit_alghanem.json), with readable scope
in [`source_audit_alghanem.md`](source_audit_alghanem.md). A direct comparison
of all **31** exported `LEAN_TEMPLATE` token lists against the pinned
`formal/a116/A116/Ishtiqaq.lean` declarations passed. It checked every slot,
literal code point and combining-mark order. The omitted final mark and the
source's bare hamza spelling remain unchanged. This is a source-content
comparison; it is not a fresh build or axiom audit of upstream Alghanem.

`NEW_NOMINAL_PROJECTION` names the two QiraaMadlul orthographic projections.
`NEW_SOUND_PROJECTION` names the eleven Mudari-based imperfect projections:
shadda compression, omission of madd sukun and omission of the final mark are
new explicit choices. Their runtime domain excludes hamza/waw/yaa and equal
second/third radicals; alif is outside the radical carrier. No upstream weak
root, hamza, assimilation or ilal theorem is claimed for this projection.
The source31 and nominal shape patterns permit weak radical substitutions
without claiming their actual Arabic realization. The 27 additional shapes
are `NEW_GRAMMAR_PROJECTION`, documented in
[`nominal_pattern_sources.json`](nominal_pattern_sources.json).

## General inverse contract

In [`Nabt/Derivation.lean`](../../formal/Nabt/Derivation.lean), `Root n` is
`Fin n → Char`, and `Pattern n` is a list of literal characters or typed
radical slots. `fill` is total. `recover` proposes each radical at its first
slot occurrence, then checks that every slot occurs and that the complete
replay equals the entire input:

```text
recover pattern text = some root
  ↔ Complete pattern ∧ fill pattern root = text
```

This theorem ranges over arbitrary arity, characters, patterns and text.
It checks literal positions, repeated-slot agreement and full length.
An absent slot cannot acquire authority from the proposal's default value.
A complete fixed pattern has an injective fill, and recovery of its fill
returns its supplied root. Uniqueness across different patterns is explicitly
false: `past.VII` with ت ب ر and `past.VIII` with ن ب ر produce the same
`انْتَبَر` stem. Both readings remain in the result list. These are formal
root candidates; the theorem does not assert that either is an attested word.

The four-slot nominal shapes use independent slots. In particular the fourth
quadriliteral slot cannot silently alias the third. A diminutive shape does
not recover the length or original radicals of an unobserved nominal base.

## Inventory of the 55 added theorems

The baseline **421** theorem entries are preserved. The added declarations
are grouped below; all occur in the compiled audit manifest.

| Namespace/group | Count | Contract |
| --- | ---: | --- |
| `Derivation`: fill and proposal | 4 | `fill_length`, `fill_append`, `firstSlot_fill`, `proposedRoot_fill_complete` |
| `Derivation`: exact recovery | 5 | `recover_refills`, `recover_requires_complete`, `recover_fill`, `recover_exact_iff`, `incomplete_rejected` |
| `Derivation`: position and rejection | 5 | `fill_at`, `accepted_literal_agrees`, `mismatching_literal_rejected`, `repeated_slots_agree`, `mismatching_length_rejected` |
| `Derivation`: fixed-pattern uniqueness | 1 | `fill_injective_complete` |
| `Derivation`: reading lists | 5 | `mem_readings_iff`, `readings_sound`, `readings_complete`, `no_patterns_no_readings`, `retained_readings_monotone` |
| `Derivation`: core inventory and ambiguity | 6 | `core_pattern_count`, `core_pattern_ids_unique`, `core_patterns_complete`, `cross_pattern_same_text`, `cross_pattern_roots_distinct`, `cross_pattern_ambiguity_retained` |
| `Derivation.Paradigm`: mask encoding | 2 | `mask_roundtrip`, `bounded_code_roundtrip` |
| `Derivation.Paradigm`: model relation | 4 | `model_membership`, `complete_models_nonempty`, `positive_assertion_preserved`, `negative_assertion_preserved` |
| `Derivation.Paradigm`: conflict and deletion | 3 | `conflicting_assertions_eliminate_models`, `conflicting_assertions_never_classify`, `deleting_assertions_cannot_narrow` |
| `Derivation.Paradigm`: finite availability boundaries | 6 | `no_assertion_keeps_all_models`, `past_alone_does_not_entail_jamid`, `past_with_two_explicit_absences_is_jamid`, `two_forms_with_third_absent_are_partial`, `all_available_models_full`, `all_absent_outside_verb_domain` |
| `Derivation.Paradigm`: identity binding | 2 | `foreign_binding_does_not_classify`, `all_forms_full_conditional_on_same_lexeme` |
| `NominalPatterns`: inventory and inverse | 6 | `pattern_count`, `pattern_ids_unique`, `patterns_complete`, `pattern_recovery`, `combined_pattern_count`, `combined_pattern_ids_unique` |
| `NominalPatterns`: overlap and fourth slot | 6 | `sifa_faail_same_shape`, `sifa_faail_same_fill`, `sifa_faail_ids_distinct`, `sifa_masdar_same_shape`, `sifa_masdar_ids_distinct`, `quad_fourth_slot_distinguishes` |

The catalog counts, unique identities, finite masks and concrete overlaps are
finite proofs. The inverse, position, list, evidence-deletion and conditional
binding contracts are general theorems. Neither group proves linguistic
activation of a pattern name.

## Conditional availability and source identity

A complete model is one of the seven nonempty assignments of three Boolean
availability cells. The class labels are explicitly defined by count:
one available cell → `jamid`, two → `partial`, three → `full`. The zero-cell
model is outside this assumed verb domain. Enumerating these seven assignments
does not claim that all seven are attested Arabic paradigm types.

Positive and negative premises restrict this domain. Unknown is neither
positive nor negative. With only past asserted present, models **1,3,5,7**
survive, retaining all three classes. Explicit contrary premises at a cell
remove every model. Deleting premises cannot narrow the survivors. All three
positive cells with no negative premises yield `full`, conditional on the
same source/lexeme binding. A foreign binding retains all class alternatives.
The truth of availability, grammatical category and same-lexeme reference is
an external premise, not a consequence of identifier equality.

An independent bitwise/popcount comparison passed for all **64** exported
rows. Runtime `availability_candidates` consumes the installed pinned table
and rejects Boolean aliases and out-of-range masks; source reading creates
masks from explicit assertions, never from the absence of text.

## Runtime correspondence review

The inspected `src/nabt/derivation.py` implements the same first-occurrence
proposal and full replay. It adds the declared Arabic radical restrictions.
It retains every accepted pattern identity, optional final boundary and source
span. The source reader performs no Unicode normalization. The exact stem
and the `surface_v1` boundary extension are separate profiles; optional marks
never establish case or mood. Fathatanwin/support-alif realization is deferred.
Quoted shape mentions remain marked as mentions. Future adjacency remains an
unactivated attachment proposal, without a future template or a tense claim.

`src/nabt/verb_paradigm.py` derives source digest, scope and header span from
the supplied bytes. Each header occurrence defines a separate reading;
identical lexical labels in different blocks are not merged. Assertions are
rebuilt within that reading. Unparsed clauses block classification, and
unscoped clauses suspend all blocks. This provides an explicit source-relative
premise language, not automatic proof that quoted forms are conjugations of
the same lexical verb.

No blocking mismatch was found in this focused code review. No runtime file
was edited by this review. The Lean theorem does **not** prove `_scan`,
`_clusters`, UTF-8 span construction, the source grammar parser, Python resource
bounds, or all runtime inputs. Those require separate correspondence and
boundary checks. Likewise, `verify(report)` replays its embedded source;
a claim about an independently expected source must supply `text`, `source_id`
and `scope` (and the expected derivation `profile`). Replay/hash agreement is
structural consistency, never a proof of a source assertion's truth.

## Executed checks and reproduction

The following completed with exit 0 using the pinned toolchain:

```sh
cd formal
/tmp/nabt-tools/lean-4.34.1-linux/bin/lake build
/tmp/nabt-tools/lean-4.34.1-linux/bin/lake env lean --run ExportDerivation.lean
/tmp/nabt-tools/lean-4.34.1-linux/bin/lake env lean Audit.lean
```

The final audit execution log is
`artifacts/local/derivation/axiom-audit.log` (local gate evidence). Its last
records are:

```text
NABT_THEOREM_COUNT 476
NABT_OBSERVED_AXIOMS [propext, Quot.sound, Classical.choice]
NABT_AUDIT_OK
```

No `sorry`, `admit`, custom axiom or `native_decide` is used. The audit inspects
the registered theorem names and all declarations under `Nabt.` against the
standard allowed axiom set. This is an axiom dependency check, not an assertion
that standard classical principles are absent.

The separate local conformance result
`artifacts/local/derivation/conformance-first.json` reports 71 catalog rows,
1,980 bounded preimage checks, 12,951 literal/length counterexamples,
213 radical-domain counterexamples, 2 repeated-slot checks, and all 64
availability rows. This is bounded runtime correspondence, not unrestricted
Arabic coverage. The full repository gate and release record remain separate.

### Reviewed source and execution hashes

These hashes identify this report's inspected revisions; they are not a
replacement for a runtime freeze or a release manifest.

| File | SHA-256 |
| --- | --- |
| `formal/Nabt/Derivation.lean` | `31167f71ec53948fd41a58a399f0949720618b6b1822a3975476369da9ccec87` |
| `formal/Nabt/NominalPatterns.lean` | `6112e3d2c5ace37967d76b1d981188c546e4967abdce10503a89c561ce7dbed9` |
| `formal/ExportDerivation.lean` | `55fbed0027125cabfd544c695af197deb86cbb1eaa937bc5c865eae6b376c778` |
| `formal/Audit.lean` | `fa351c35c88a140b9016a383b926b3f0cf6ec5ca34dec3a1c765e97d936f7a2c` |
| `formal/theorems.json` | `61ced2da24e3ef81f7639fe93ac5f4271b0782e8646e1e1e2ade39bfa183720b` |
| `src/nabt/data/derivation_patterns.json` | `0b4d6673c033955490468ad595fc1e988890bba282101e81a80580d3fc1fbf2f` |
| `src/nabt/derivation.py` | `cf9b911f2d69eba5413acfa3e46bffe1e724b1e49b107d642e5360422420d2f2` |
| `src/nabt/verb_paradigm.py` | `18234ee76da3d43576409fc66138aff60a2f6e7922d1304a92cc25d1a23bdb28` |
| `artifacts/local/derivation/axiom-audit.log` | `35dfe965648a96211b25765402f86166697b8acb687e821cbaa3d6a9717950a3` |
