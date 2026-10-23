# Inflection evidence: formal contract and verification scope

## What the extension establishes

`formal/Nabt/InflectionEvidence.lean` adds the independent law
`nabt.inflection-evidence.v1`. It imports the existing `Words`, `Morphology`
and `TextEvidence` contracts without changing their tables or semantics.
Its sign convention is explicitly `common_letter_substitution`. The
traditional letter account of the six nouns is therefore a declared choice,
not a claim that every grammatical account analyzes those signs identically.
A declension class is a supplied, qualified premise, including its eligibility
conditions. The module does not infer that premise from a word ending.

The 45 class/case rows preserve the exact validity domain and surface column
of `Words.ending`. Separate fields record grammatical sign, realization mode
and whether the sign is original or a substitute **relative to the supplied
case**. Thus kasra is original for genitive but substitute for the accusative
of the sound feminine plural. In a weak-final jussive the remaining vowel is
kept in the surface column; deletion of the weak carrier is the sign.
An estimated vowel is likewise distinct from its visible carrier.

The base diptote-genitive row has the bare-diptote convention. It cannot be
selected as the actual contextual realization without independent context.
The separate 16-row projection reuses `Morphology.GenitiveContext` and its
four evidence states. Unknown article/construct status retains fatha and
kasra alternatives. Fatha alone requires both explicit negative premises;
affirmed article or construct status allows kasra, and conflicting evidence
has no realization. Absence of a premise is not a negative premise.

Seven nun kinds are an inventory of typed readings. That inventory has no
case or role output. Eleven relation rows give conditional noun/verb and
case requirements. Their presence in the table does not mean the text
reader acquires all eleven relations. In particular, agreement on a case
does not identify a role: active and passive subjects remain distinct
relations with the same nominative requirement.

## Receipt and segmentation boundaries

`Receipt.admissible` checks exact head/target bindings, valid and disjoint
endpoint spans in the same declared source revision and scope, the relation
rule code, active/unblocked status, nonempty support from the declared source,
compatible word kind and known construction. The binding carries source,
revision, scope, occurrence, segmentation, reading and byte coordinates.
The exported 256-row Boolean gate is linked to this general checker through
`activation_exact`; it is not evidence that caller-supplied flags are true.
The runtime must compute the flags from the same endpoints that it records.

Support checking is structural: source identity, revision and nonempty span.
It does not prove that a source is authentic, that its annotation is correct,
that a span entails a grammatical relation, or that Python parsed the source
correctly. Those are external premises and separate replay obligations.
Neither an observed sign nor an observed nun kind enters the accepted
relation list.

Case candidates intersect the requirements of admitted relation receipts.
Deleting evidence cannot narrow the candidates; duplicate evidence has no
additional effect. With no admitted relation, all four cases remain possible
and no case is selected. Conflicting requirements yield no assignment.
A selected case has an actual admitted receipt in the input. Unknown
construction blocks assignment. A built target can receive a `local_case`;
it cannot receive `inflected_case` from its building vowel.

Exact segmentation proves preservation of elements and total length through
concatenation of nonempty parts. `LicensedSegmentation` additionally requires
an independent grammatical `License`. Exact byte reconstruction does not
establish that license, identify a morpheme, or choose the unique parse.

## Audited declarations

The extension adds **41** named theorems to `formal/Audit.lean` and
`formal/theorems.json`, taking the existing inventory from 520 to **561**.
The names have namespace `Nabt.InflectionEvidence`.

| Group | Count | Main declarations and precise scope |
|---|---:|---|
| Signs and old surface law | 9 | `realization_surface_exact`, `realization_domain_exact`, `mem_rows_exact`, `original_relative_to_case`; row count and concrete ambiguity/counterexample propositions are finite checks |
| Filtering | 3 | `filtered_rows_exact`, `deletion_widens_rows`, `duplicate_row_constraint` for arbitrary candidate lists and Boolean constraints |
| Diptote context | 3 | `diptote_candidates_exact`, `diptote_unknown_does_not_assert_absence`, `diptote_conflict_blocks` |
| Distinct grammatical domains | 2 | `same_case_does_not_identify_relation`, `built_cannot_be_inflected_case` |
| Receipt prerequisites | 8 | `activation_exact`, admitted identities/context/nonempty support, foreign endpoint/blocker/unknown construction/wrong kind rejection |
| Contextual case | 13 | Exact intersection, observations without authority, empty evidence, admitted witnesses, deletion/duplication, singleton selection, conflict and built/local boundaries |
| Segmentation | 3 | Element preservation, length preservation and impossibility of constructing an explicitly unlicensed segmentation |

The axiom audit recorded in
`artifacts/local/inflection-formal/axioms.json` and `axioms.log` passed for
all 561 listed theorems and scanned all compiled `Nabt.*` declarations.
The observed axioms are only `Classical.choice`, `Quot.sound` and `propext`.
No project axiom, `sorry`, `admit` or `native_decide` is used. A theorem about
the defined conditional relation is not a proof of Arabic coverage or a
proof of the external learner's premise acquisition.

## Generated table and correspondence

`formal/ExportInflectionEvidence.lean` generated
`src/nabt/data/inflection_evidence_table.json` directly. The file has 14,136
bytes and SHA-256:

```text
f8bc2f04fc1225a4f495d71a4c283289a3e8e9c74b9949008eb51e6445e7deb5
```

It contains 45 sign rows, 16 diptote contexts, 7 nun kinds, 11 conditional
relations, 256 receipt masks and 2 construction-domain rows. The new
`exportInflectionEvidence` Lake executable is part of the default build;
the recorded build completed successfully with 51 jobs.

`tools/check_inflection_conformance.py` rebuilds Lean, exports afresh and
compares the complete JSON with the packaged table. Comparison distinguishes
Booleans, integers and floats and rejects duplicate JSON keys. Independent
named grammatical families check all sign rows and 165 conditional surface
inverse projections. Set-valued evidence gives the independent diptote
reference; named prerequisites give the receipt reference.

The same gate checks the Python **table adapters** against those independent
references: 16 sign contexts, 60 individual class/case projections, one
caller-order check, two empty-domain checks, 66 relation/kind/construction
combinations and 256 receipt masks. This is explicitly not a reader,
segmentation-acquisition, learner, corpus-truth or free-Arabic test.
`tests/test_inflection_laws.py` supplies 19 authored boundary tests.

Scoped results are preserved at:

- `artifacts/local/inflection-formal/conformance.json`: finite export gate.
- `artifacts/local/inflection-formal/conformance-runtime.json`: finite export
  and table-adapter correspondence, both passed.

These records precede the release freeze and full repository gates. They
make no claim that a final release, held-out evaluation or unrestricted
dependency parser has passed. Source provenance and competing grammatical
accounts are documented separately in `docs/INFLECTION_SOURCE_AUDIT.md` and
`evidence/inflection/source_*`.

The subsequent a2 release repeated the full repository gates with 657 tests
and the 561-theorem audit. Published copies of the final conformance and axiom
reports, the check log, and the installed-package evidence are bound in
[release/validation.json](release/validation.json). This later record does
not change the scope of any theorem or of the pre-freeze checks above.

## Reproduce the scoped checks

```sh
PYTHONPATH=src python -m unittest discover -s tests -p test_inflection_laws.py -v
python tools/check_inflection_conformance.py --lake /path/to/pinned/lake
```

The pinned toolchain for this evidence is Lean 4.34.1. The axiom audit uses
the repository's existing audit tool and registered theorem inventory; the
conformance tool does not replace that audit or the full release gates.
