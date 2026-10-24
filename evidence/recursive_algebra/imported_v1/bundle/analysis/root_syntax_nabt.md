# NABT audit: roots and affixes through lexical and recursive syntactic units

## 1. Pin, publication, and method

The final verified public `main` is **171cfa32a4bad0b5f9e8ff856cd98e23028122c7**, PR **#14**, “Add licensed unit derivations and exhaustive binary forests”, committed 2026-10-24 07:24:48 UTC. Its tree is `58b34034fb29cda4a769bf2641efc21bfad091ac`.

The public branch `feat/progressive-unit-algebra` is at **305429171d72c01030850beedec4a723d83bf5a1**. The local clean checkout is on that branch. Its Git tree equals the public main tree exactly, so the inspected local lines below are also lines of the pinned main commit. The earlier `commits/main` and `branches/main` responses returned PR13 at `748bcfc...`; a later branch listing returned PR14, which was then verified by direct immutable Git-commit and tree requests. This report uses PR14 and does not infer the reason for the different responses.

Read-only audit: no checkout, fetch, source edit, commit, or publication was performed. Nineteen inspected source/document blobs were independently hashed against the remote pinned tree; see `root_syntax_nabt_manifest.json`. No full test suite or Lean build was rerun. Two narrowly scoped existing Python reader examples were executed with bytecode writing disabled. Theorems discussed below are claims and proof bodies inspected in the repository, not a new independent build certification of all NABT.

- [Pinned PR14 commit](https://github.com/sonaiso/NABT/commit/171cfa32a4bad0b5f9e8ff856cd98e23028122c7)
- [Published feature commit](https://github.com/sonaiso/NABT/commit/305429171d72c01030850beedec4a723d83bf5a1)

## 2. Root/template recovery: an exact shape relation, not lexical classification

`Derivation.Root n := Fin n → Char`; a `Pattern n` is a list of either literal characters or typed radical slots. `fill` replaces each slot by the corresponding supplied radical. `Complete` requires every slot to occur. `recover` proposes slot values, but returns them only if the pattern is complete and a replay equals the **entire** input text. This checks literals, order, repeated slots, and length. A default value in an absent slot cannot acquire authority because incompleteness is rejected. [Derivation.lean 25–60](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/Derivation.lean#L25-L60)

Relevant exact contracts:

- `recover_exact_iff`: recovery of a given root iff completeness and whole-text replay, lines 113–120.
- `accepted_literal_agrees`, `mismatching_literal_rejected`, `repeated_slots_agree`, and `mismatching_length_rejected`, lines 130–160.
- `fill_injective_complete`: a root is unique **for one fixed complete pattern**, not across different patterns, lines 162–168.
- `readings_sound` and `readings_complete`: soundness and completeness relative to the **supplied pattern list**, lines 170–213. Enlarging that list retains old readings.

[Recovery contracts](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/Derivation.lean#L90-L213)

The same surface is intentionally allowed different roots and templates. `cross_pattern_same_text`, `cross_pattern_roots_distinct`, and `cross_pattern_ambiguity_retained` witness the exact string `انْتَبَر`: `past.VII` yields the root `تبر`, while `past.VIII` yields `نبر`. Both remain. [Derivation.lean 728–750](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/Derivation.lean#L728-L750)

`UnitDiscovery.RootPatternReading` packages a whole `(pattern, root)` alternative as `.tri` or `.quad`. `fitsHost` checks a valid host span, complete slots, and full replay of that host. `rootReadings` filters the supplied proposals without selecting a first reading; `rootReadings_preserve_ambiguity` retains two different matching proposals. The initial interface's arities 3 and 4 are expressly not a theorem about every Arabic nominal root. [UnitDiscovery.lean 588–668](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/UnitDiscovery.lean#L588-L668)

### Actual inventory boundary

The installed runtime table contains **71 declared template contracts: 68 of arity 3 and 3 of arity 4**. The latter are:

1. `grammar.masdar.quad.fa3lala` — فَعْلَلَة.
2. `grammar.diminutive.fu3ay3il` — فُعَيْعِل.
3. `grammar.diminutive.fu3ay3iil` — فُعَيْعِيل.

This is not a complete quadriliteral verb morphology. Arity counts independent target slots; four target slots in a diminutive do not prove that its original lexical base had four radicals or recover deleted base material. The 44 core contracts are in `Derivation.corePatterns`; the remaining nominal inventory is explicitly a new projection from cited grammar passages. [NominalPatterns.lean 4–28](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/NominalPatterns.lean#L4-L28), [four-slot diminutives 131–137](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/NominalPatterns.lean#L131-L137), [catalog explanation](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/docs/DERIVATION.md#L30-L50).

The Python boundary checks an explicit 28-radical carrier; selected imperfect templates further restrict roots to their declared sound-triliteral domain. `generate_derivation` reports `GENERATED_SHAPE` and `attested_word=False`. A label such as “masdar” in catalog metadata is a reading proposal, not a proved semantic category. [derivation.py 99–149](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/src/nabt/derivation.py#L99-L149)

Two executed checks confirm the boundary without adding a benchmark:

| Input, `stem_exact_v1` | Shape result | Retained readings | Linguistic result |
|---|---|---|---|
| `انْتَبَر` | `AMBIGUOUS` | VII/تبر and VIII/نبر | `DEFER`; attested root unknown; noun/verb/particle retained |
| `دَحْرَجَة` | `UNIQUE_IN_PROFILE` | `grammar.masdar.quad.fa3lala` / دحرج | Still `DEFER`; attested root unknown; noun/verb/particle retained |

The runtime explicitly retains `status=DEFER` even for a single shape, with unknown role, case, lexical root attestation, and grammatical attachment. [derivation.py 278–296](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/src/nabt/derivation.py#L278-L296)

## 3. Affixes: a declared vocabulary and separate requirements

`AffixFunctions` defines 34 functions across clitic, inflection, derivation, lexical, and orthographic layers. A declaration includes positions, spelling illustrations, and **strings naming requirements**. `entry` prefixes the requirement `independent_interpreted_source`. Its finite proofs show unique keys, coverage of the declared `Function` datatype, nonempty position lists, and presence of that requirement string. They do not construct or validate a source witness for an Arabic occurrence. [AffixFunctions.lean 7–22, 29–67](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/AffixFunctions.lean#L7-L67), [finite checks 146–161](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/AffixFunctions.lean#L146-L161)

Useful explicit requirements include:

- Triliteral/quadriliteral augmentation: root arity, complete typed pattern, whole-form replay, lexical family, lines 88–93.
- Subject/object/genitive pronoun attachment: qualified host, distinct slot, correlated person profile, attachment and sometimes reference, lines 94–102.
- Nominal dual/plural and five-verb nun: the independently qualified family and case/mood frame; spelling alone is not the family, lines 109–124.
- Definite article versus relative أل: different host and reading conditions, lines 68–71.
- Entire relative, demonstrative, possessive ذو and pronoun lexemes: whole-lexeme readings, not an instruction to strip an initial substring, lines 133–143.

[Affix declarations](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/AffixFunctions.lean#L68-L143)

The partition generator does not import this inventory or use its examples as gates. Noncontiguous root/template slots are explicitly separated from contiguous source segments. Person profiles preserve correlations: `qualifiedCandidates false ... = []`, and plain ت keeps 2MS and 3FS. [PersonEvidence.lean 58–99](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/PersonEvidence.lean#L58-L99)

## 4. Noun / verb / particle: conditional lexical input, not an output of shape recovery

`Words.Kind` declares the three constructors. `LexicalTraits` supplies `independent`, `timeInForm`, and `needsReference`; `kindOf` reads the first two. The theorems explain the classifier **given those witnessed traits**. `capacities_no_fourth` is a theorem over the already declared three-case datatype, not a discovery or universal exhaustion of linguistic kinds from raw signifiers. [Words.lean 39–111](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/Words.lean#L39-L111)

`kindCandidates` intersects allowed sets from already activated, source-licensed cues. `no_cue_retains_all` preserves noun/verb/particle; missing evidence is not a particle cue. `shared_surface_keeps_alternatives` preserves two kinds when all actual cues allow both. [Words.lean 113–148](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/Words.lean#L113-L148)

`Words.Analysis` retains occurrence, segmentation ID, reading ID, kind and optional declension class. `CaseCompatible` reads the existing analysis; a role cannot manufacture a missing kind or class. [Words.lean 373–433](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/Words.lean#L373-L433)

## 5. PR14 provides a recursive conditional proof carrier

The current `LicensedDerivation.Tree` supports atomic occurrences, `join`, `wrap`, `substitute`, and `lift`. It separates original source, original raw segment, remaining source, current output, class, rank, and the full derivation trace. Tags contain opaque natural rule/reading/class IDs plus requirements; their names or numbers do not assign grammatical meaning. [LicensedDerivation.lean 35–106](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/LicensedDerivation.lean#L35-L106)

Structural gates are concrete:

- Atom: full source membership and exact occurrence decomposition.
- Join: same full source and **original-source adjacency** of the two nonoverlapping parts.
- Substitute: a genuinely different replacement, with the displaced child preserved.
- Lift: target class differs from child class.
- Wrap: no source/output change; classification still needs its own interpreted receipt.

[Entry and reconstruction functions](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/LicensedDerivation.lean#L108-L142)

Every composite node needs mandatory requirement 0 plus its declared requirements. Receipt acceptance requires equality of the **entire target tree**, membership in `interpreted`, nonempty support, and valid support spans in registered full sources. Positive support must be offered; known valid negatives are taken from the supplied interpreted ledger, so hiding one from `offered` does not erase it. [Receipt gates 159–206](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/LicensedDerivation.lean#L159-L206)

`Licensed` has an inductive rule for each constructor and requires licensed children plus its own gates. Its Boolean counterpart is characterized by `licensed_iff_structure_and_premises` and `assess_licensed_iff`. `licensed_reconstruct` is proved by induction on the licensed derivation; `licensed_premises_retained` supplies a real admitted positive receipt for each requirement at each composite step. [Licensed 236–259](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/LicensedDerivation.lean#L236-L259), [Boolean equivalence 312–384](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/LicensedDerivation.lean#L312-L384), [preservation 446–520](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/LicensedDerivation.lean#L446-L520)

This is a reusable proof carrier for new typed lexical and syntactic rules, but it does not itself acquire noun, verb, particle, phrase, or clause interpretations. The new labels, rule inventory, and source interpreter remain a separate bridge obligation.

## 6. Identity and uniqueness must be kept at their actual strengths

| Layer | Identity / guard | What does not follow |
|---|---|---|
| Pattern recovery | Root unique for a fixed complete pattern | Unique pattern or lexical root across all analyses |
| `UnitDiscovery.Hypothesis` | Full source, partition, selected part, host, opaque class, claim, rule, occurrence, reading, requirements | Truth of its claim or automatic discovery of the class |
| Runtime shape candidate | Pattern/root/boundary/alignment and source occurrence retained; `candidate_id` names the whole report | Linguistic certainty from `UNIQUE_IN_PROFILE` |
| `LicensedDerivation.UnitKey` | Source, start, raw material, output, interpreted class | Derivation identity: wrap and lift can have the same key but different trees |
| `LicensedDerivation.Receipt` | Entire tree equality, including operations, tags and children | Transfer of a receipt merely because two trees have equal outputs |
| `ArabicReading.selectUniqueComplete` | Exactly one supplied candidate, with `complete=true` | Proof that its supplied candidate universe was exhaustive |
| `BinaryUnitDomain.uniqueWithin` | One licensed tree and explicit rejection of every different generated rival | Global uniqueness outside the declared binary domain |

Hypothesis identity and its receipt guard: [UnitDiscovery.lean 291–340 and 407–440](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/UnitDiscovery.lean#L291-L440). Same unit, different derivations: [LicensedDerivation.lean 639–649](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/LicensedDerivation.lean#L639-L649). Singleton lowering: [ArabicReading.lean 229–284](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/ArabicReading.lean#L229-L284).

The strong new uniqueness guard is genuinely stronger than singleton selection. `CompleteWithin` is a proposition over the whole declared domain, not a caller Boolean. `NecessaryWithin` requires membership, licensing, and uniqueness among licensed members. `exhaustive_rejections_establish_necessity` needs complete candidates and explicit rejection of every rival; a pending rival blocks that rejection certificate. [LicensedDerivation.lean 651–684](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/LicensedDerivation.lean#L651-L684)

`BinaryUnitDomain` discharges the enumeration premise for one fixed full source, one nonempty interval, one fixed tag, and atomic/binary-join trees with original leaf order. `mem_candidates_iff` and `candidates_complete` establish this precise scope. `uniqueWithin_iff` and `generated_necessity` connect the executable decision to necessity in that domain. Pending or invalid rivals block the certificate. It excludes new tags, wraps, lifts, replacements, alternative atomization, and arbitrary lexical/syntactic rule choices. [BinaryUnitDomain.lean 177–215](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/BinaryUnitDomain.lean#L177-L215), [238–250 and 321–337](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/BinaryUnitDomain.lean#L238-L337).

## 7. Practical bridge to the proposed root → morphology → syntax model

The following is an integration proposal, not a claim that NABT already implements it:

1. **Root shape.** Keep `RootPatternReading` with the full typed pattern, formal radicals and exact host replay. Do not flatten noncontiguous radical positions into a fictitious contiguous source piece.
2. **Lexicalization.** Add a separate witnessed step from a shape reading to a noun/verb reading, with lexical-family, attestation and contextual conditions. Also permit independently witnessed whole-lexeme entries for particles, pronouns, or other forms without forcing a root/template analysis onto every lexeme.
3. **Affix application.** Use the inventory as a declared set of possible functions, then require a concrete receipt for the chosen function, host, attachment and allomorph/paradigm. Root-slot insertion is a typed pattern application, not always prefix or suffix concatenation. Contraction, deletion and replacement require retained source correspondences and their own gates.
4. **Typed constituent construction.** Add constructors such as nominal phrase, verbal phrase, prepositional phrase, predication and subclause, with explicit input/output sorts. Their Boolean gates must require the particular frame, attachment, agreement/valency, and source-bound readings. A true Boolean establishes the supplied test; it does not itself acquire its intended grammatical meaning.
5. **Recursive reuse.** Embed each accepted step in `LicensedDerivation`, or give a checked adapter from the independent certified judgement to it. Preserve full child trees, source decomposition and receipts. Keep the complete root/pattern and lexical certificate alongside the tree or in a checked mapping; opaque `readingId` alone is not that mapping.
6. **Outer versus inner assignments.** A clause reused as a constituent can receive an outer local case while preserving its internal word assignments. NABT already models this explicitly in `ClauseAssignment` / `kada_clause_keeps_internal`, rather than applying the outer accusative to the internal imperfect verb. [ConstructionEvidence.lean 125–132](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/ConstructionEvidence.lean#L125-L132)
7. **Claims of uniqueness.** A larger root/affix/lexical/syntactic search needs a newly declared finite domain and a sound/complete generator for all its allowed choices. The existing binary fixed-tag theorem cannot be silently reused as exhaustiveness of that larger grammar.

Existing construction gates are useful bridge checks: `constructionAllowed` requires identity binding, source support, attachment, frame completeness, licensed sense, and an unblocked activation. Its receipts bind exact graph endpoints, full reading bindings and rule ID. Adjacency and observed case alone produce no accepted construction edge. [ConstructionEvidence.lean 238–320](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/ConstructionEvidence.lean#L238-L320), [349–365](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/formal/Nabt/ConstructionEvidence.lean#L349-L365).

## 8. Remaining acquisition obligations

NABT now has a stronger conditional recursive carrier and a genuinely exhausted restricted binary domain. Its roadmap still explicitly leaves source interpretation, lexical class acquisition, root/orthography transformations, nontrivial attachment, roles/case/reference, and a finite broader grammar domain open. Those are the appropriate next obligations for the proposed model, rather than more counts of declared labels. [ROADMAP.md 18–27](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/docs/ROADMAP.md#L18-L27), [54–76](https://github.com/sonaiso/NABT/blob/171cfa32a4bad0b5f9e8ff856cd98e23028122c7/docs/ROADMAP.md#L54-L76).

The audit supports reusing the exact recovery, full identity binding, recursive per-step licensing, and explicit-rival-rejection architecture. It does not support treating declared affix names, template matches, or unique content codes as independently acquired lexical or syntactic truth.
