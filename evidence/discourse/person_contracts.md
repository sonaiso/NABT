# Person and morphology bridge: proof and source scope

This record describes the new conditional law `nabt.person-evidence.v1` and
the source bridge `nabt.source-person-bridge.v1`. It is not a release-success
record or a claim to parse unrestricted Arabic.

## Installed finite contract

`formal/Nabt/PersonEvidence.lean` is independent native Lean code.
`formal/ExportPersonEvidence.lean` exports the complete installed registry at
`src/nabt/data/person_evidence.json`. Its SHA-256 is
`f77c9b65b3a7b638166b5807fff1218cb30079d2d301c815b1b512a665858d15`.

| Inventory | Size | Meaning |
|---|---:|---|
| Correlated person profiles | 14 | Person 1/2/3; gender 0 masculine, 1 feminine, 2 unspecified; number 0 singular, 1 dual, 2 plural |
| Family/prefix combinations | 20 | Five already-qualified families crossed with أ/ن/ي/ت, including impossible combinations with no candidates |
| Separate pronoun readings | 14 | Existing NominalEvidence Unicode projection, preserving هما/أنتما gender alternatives and first-person unspecified gender |
| Attached allomorph readings | 20 | Declared Unicode forms with a host-domain restriction for ي/ني, not a raw suffix parser |

The five families are plain, dual, masculine plural, addressed feminine
singular, and feminine plural. They are whole correlated readings. In the
plain family, ت admits 2MS and 3FS. In the dual family, it admits 2MD, 2FD,
and 3FD. The first-person prefixes have no five-verb family reading. Bare
ا is not silently treated as أ.

The 24 audited theorems establish inventory domains/uniqueness, filter
membership, qualified versus unqualified use, the named ambiguity
counterexamples, evidence deletion widening the surviving list, rejection
of contradictory filters, and receipt identity/support/block isolation.
The arbitrary receipt identity has source, scope, occurrence, and reading
fields. Its equality check cannot establish the correctness of an external
parser or the truth of a source annotation. There is no theorem deriving
the lexical family from the first letter of a new word.

The shared audit at
`artifacts/local/discourse-development/axioms.json` and its `.log` passed
for 625 declarations: the historical 561, 40 DiscourseEvidence theorems,
and these 24 PersonEvidence theorems. The reported axioms are only
`Classical.choice`, `Quot.sound`, and `propext`. This is a kernel audit of
the declared contracts, not a proof of the Python bridge.

## Relation to upstream Lean and primary grammar

The exact source paths, hashes, declaration boundaries, and repository pins
are in `evidence/discourse/source_audit.json` and `source_audit.md`.
The relevant checkouts are Mashru at
`e4c801ffe9171dadedcc3aae23051ea0953ae361` and Alghanem at
`9d8fa03a51f894416e0abaf3b6821c5ae6441dcd`.

* Mashru `SLGE/Maqam.lean` and `Jisr/QiraaSimat.lean` supply the finite
  correlated pronoun inventory and its ambiguity examples. QiraaSimat
  expressly does not build attached-pronoun or imperfect-prefix reading.
* Alghanem `formal/a116/A116/Mudari.lean` generates forms from supplied
  root, form, vowel, prefix, and ending premises. Its `anayt` inventory is
  not an inverse person classifier or a lexical-root acquisition theorem.
* The installed primary `alfiyya.txt` has the directly connected emphasis
  and feminine-nun construction distinction at lines 66–67, five-verb
  retention/deletion at 93–94, the separate/attached pronoun material at
  105–119, and verbal protection nun before first-person ya at 120–123.
  These passages support the declared grammatical rule; they do not verify
  the source adapter's segmentation of an arbitrary word.
* QAC's primary morphological-feature documentation explicitly defines
  active as the default voice when no voice is marked. The new bridge
  records `QAC_DEFAULT_ACTIVE_ABSENT_PASS` for this format decoding only.
  Its evidence and retrieved-byte hash are in `source_audit.json` under
  `qac_voice_documentation`. No corresponding default case or mood is
  acquired: NOM/ACC/GEN and every MOOD field remain masked.

The new Unicode allomorph inventory and prefix-family projection are stated
as native bounded contracts. They are not claimed equivalent to an A116
parser, QAC annotation inventory, or upstream general inflection theorem.

## Source bridge and API

`src/nabt/person_evidence.py` exposes:

```python
person_catalog()
person_candidates(surface, *, lexical_model=None)
```

The public learner input is the existing `QacLexicon`: immutable original
QAC bytes, exact source identity, and explicit excluded verses. The module
validates it through the existing lexical adapter and reconstructs its own
source partitions from the raw records. Caller-provided entries, statuses,
and hashes are not accepted as evidence. Full bytes, not an asserted digest,
key the memoized source compilation.

A result retains the whole person profile, aspect, voice and voice basis,
lemma/root annotations, family, rule IDs, source receipts, source-relative
parts, and independent nun readings. `person_name`, `gender_name`, and
`number_name` provide readable forms. Partial nominal gender/number evidence
survives even when no complete person profile is available. A named noun's
third-person profile is a grammatical profile, not an identified individual.

`parts` and visible `nun_readings` carry offsets relative to the exact input
surface. The consuming reader must bind these to its source, scope,
occurrence, and reading identity. Every visible nun span covers its actual
letter and marks. Deleted or unresolved nuns have no invented span.

`segmentation_licensed` is distinct from unresolved discourse obligations.
For example, an unknown referent does not invalidate the spelling partition
of أنا. A licensed hollow shortening can still require an external jussive
context. An annotation-only attached word with no independent complete host
does not license a grammatical attachment.

The module emits no `actual_role`, `actual_case`, `local_case`, or referent.
`class_candidates` and `possible_cases` remain conditional morphology data.
They must be checked against the actual host realization and a separately
licensed relation before assignment.

## Licensed transfers and boundaries

### Complete verbal families

Imperfect prefix substitution requires a source-backed verb, root and lemma
annotations, a compatible source person, a complete family, and the declared
prefix/vowel geometry. It preserves the body and stays within the witnessed
family. It does not grow dual/plural suffixes from a plain singular form.
The dual, masculine-plural, addressed-feminine, and feminine-plural families
have separate terminal geometry checks. A full retained five-verb form is
required before its deleted-nun candidate can be projected.

The projection does not collapse bare alif into hamza or repair an adjacent
hamza collision into madda. T-shaped readings remain alternatives; a later
desired role does not authorize deleting one of them.

### Attached pronouns and lexical capacity

Attached words retain source STEM/SUFFIX partitions. PRON alone does not
establish an object: the source person, aspect, and actual subject-suffix
shape are checked first. Thus كتبتُ is retained as a whole source word with
a subject suffix and supplies no transitivity witness. Its truncated كتب
does not acquire first-person morphology.

A verbal-object or nominal-possessive attachment additionally requires an
independent complete host with matching lemma, root, aspect, voice, and
body/profile geometry. The source group containing the attached word cannot
serve as its own independent bare-host witness. Active verbal object
capacity is passed only to the matching complete lexical body, including
its qualified prefix variants. A shared root alone cannot transfer that
capacity to another derived form. The capacity record is not an assigned
object or a claim that every use of that lexeme is transitive.

The same source-established kaf slot preserves the ka/ki gender contrast
when the new word omits its vowel. Dual suffixes retain both genders.
Hu/hi is a phonologically conditioned allomorph; this bounded bridge keeps
the attested vowel after the unchanged host instead of switching it freely.
Unsupported subject/object ambiguity is retained as `unknown` with an
unlicensed attachment. Nominal possessive attachment makes no ownership
claim about the world.

Attached candidates preserve `host_form`, `host_variant`, and
`host_end_cluster`. This prevents the movement of the final pronoun from
being mistaken for the case/mood sign of its host. The source reader must
extract the actual host slice from the new text, rather than copy the
training form's vowels into the new occurrence.

### Nun functions

Protective nun requires a verb, an independently witnessed complete host,
a first-person singular source suffix, and the literal source partition ني.
The source's unspecified or conflicting suffix does not supply it.

Direct emphasis requires a complete ordinary imperfect host, its plain
person family, no intervening subject suffix, a witnessed final fatha, and
one complete source-emphasis nun with the appropriate heavy/light shape.
Visible adjacency alone cannot license directness. The separated case is
currently bounded to the visible dual alif, a retained full dual base, and
the witnessed heavy-nun shape. This establishes separation, while its sign
realization remains explicitly unimplemented: no raf/nasb/jazm sign is
exported from the collision-driven absence of the inflection nun.

Other EMPH partitions remain unresolved, including an EMPH annotation on
alif without a visible nun. Root-final nun, five-verb nun, feminine subject
nun, protective nun, and emphasis are separate entries and positions in
one correlated reading.

### Weak forms

Existing qualified weak-final full/deleted forms retain their original
source premises. A new hollow-short projection is limited to an independently
attested four-carrier imperfect of a supplied triliteral root with only its
middle radical weak, the appropriate literal long-vowel geometry, and a
final sukun in the short reading. It supplies a jussive-only conditional
candidate. It does not recover a root from a short shape, resolve a broader
weak paradigm, or assume that a missing word is unattested.

## Validation recorded so far

`tools/check_person_conformance.py` builds Lean, exports the full JSON anew,
compares complete canonical JSON with type distinctions intact, and checks
an independent named paradigm/allomorph oracle. It then checks the installed
runtime registry and catalog identity. The saved passing report is
`artifacts/local/discourse-development/person-conformance.json`.

The 28 authored tests in `tests/test_person_evidence.py` cover the person
ambiguities and source withdrawal, prefix/hamza boundaries, complete
five-verb prerequisites, distinct nun spans, attached-subject counterexample,
object/possessive independent-host requirements, protective nun, limited
emphasis directness, hollow shortening, nominal partial features, duplicate
source witnesses, and case/mood poisoning that changes provenance without
changing person semantics. They do not read the independently authored
evaluation material and are not a measurement of unrestricted Arabic.

The integration review separately identified the need to avoid legacy
person rows bypassing the new source gate, convert relative nun offsets,
keep segmentation separate from reference obligations, preserve host
variants, and restrict the singular-verb VSO number exception. These are
reader-integration requirements; the finite Lean proof does not discharge
them. Final release/evaluation evidence is recorded separately after the
runtime is frozen.
