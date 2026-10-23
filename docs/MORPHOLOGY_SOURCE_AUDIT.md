# Morphology source audit: construction, inflection, diptotes and derivation

Date: 2026-10-23. Target baseline: `sonaiso/NABT@34afbd4fb7adc16471ee7be8dcd48d945a65ad90`.

## Finding

The source repositories contain reusable algebraic contracts for these topics, but several of their inputs are supplied classifications. Recovering an encoded classification is different from establishing that classification from a new text. NABT must preserve that distinction when reusing the contracts.

The most useful composition is:

1. Preserve the exact occurrence and its possible readings.
2. Extract a property with its source statement, scope and conditions.
3. Apply a rule only to a reading for which those conditions are evidenced.
4. Preserve alternatives and named missing conditions.
5. Replay both extraction and rule application from the bound text and policy.

The numerical identity of an occurrence is a sound address for this computation. It does not by itself establish an inflection class, a lexical origin or a grammatical role. The existing contracts are particularly valuable because some of them already state this limitation explicitly.

This document audits source code and primary-text bytes. It does **not** attest that upstream Lean projects were rebuilt during this audit, that every repository was reviewed in full, or that a general Arabic extractor is complete.

## Immutable evidence and scope

All source reads used `git show <full-commit>:<path>` or the pinned Git tree. No source claim in this audit depends on an uncommitted source working tree.

The machine-readable companion is [source_passages.json](../evidence/morphology/source_passages.json). It contains:

- 23 exact passages from the three primary grammar texts packaged in the NABT baseline, plus five short primary passages from الشخصية ج3 in the pinned Alghanem corpus;
- zero-based UTF-8 byte intervals, one-based inclusive line intervals, full-file hashes and passage hashes;
- full pins and hashes for 12 selected upstream Lean files, with selected declaration lines;
- a nine-repository inventory, explicitly distinguishing a selected source review from a filename/content search.

The three primary files are pinned to the NABT baseline above:

| File | SHA-256 |
|---|---|
| `src/nabt/data/source_evidence/qatr.txt` | `2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d` |
| `src/nabt/data/source_evidence/alfiyya.txt` | `13b351a0a02d9060fdedbb5db568544718eb4e89bef323f5572b8a26c0921ca0` |
| `src/nabt/data/source_evidence/sibawayhi.txt` | `a160f940bb194e6fe7e6655d2c7f28e41f1fc648c4c5e340cc4e42306d5cb625` |

Their working-tree bytes matched these pinned objects when the passage artifact was generated. A hash is an integrity check, not linguistic authority. The interpretations stored next to excerpts are this audit's judgments; `text` is the exact source text, including transcription markers.

The additional primary semantic source is `Alghanem@9d8fa03a51f894416e0abaf3b6821c5ae6441dcd:corpora/nabhani/shakhsiyya_j3.txt.gz`. Its compressed Git blob SHA-256 is `bad1ad74dea557322854a57d62c7624b42655eb41dec575ea8bac9c9a792f622`, and the decompressed content hash is `dd57e74bec43534ceec90797ad050cb104a16925b6d0bf0304796d42e70c425e`. Its excerpt offsets address the **decompressed** bytes, as stated in the JSON. This book is not packaged in the NABT baseline. An installed runtime that relies on these passages must package the checked excerpts and preserve this origin, rather than resolving a mutable external checkout at runtime.

### Correction found during independent source review

The first version of `alfiyya_diptote_genitive` erroneously selected line **91**, which is the page marker `PageV01P011`. The actual genitive verse is line **92**. The byte/hash verification was correct for the selected bytes, but the selected bytes did not support the associated claim. Parent review detected the semantic mismatch. The passage is now corrected, and `CORRECTION_ALFIYYA_GENITIVE_LINE` preserves the erroneous span/hash and the reason for replacement in the JSON. No frozen independent evaluation source was edited. Integrity checks must be accompanied by a relevance review; valid hashes alone cannot prove source support.

The substantive Lean review uses:

- [Mashru at e4c801f](https://github.com/Saleh1967/Mashru/tree/e4c801ffe9171dadedcc3aae23051ea0953ae361).
- [Alghanem at 9d8fa03](https://github.com/Saleh1967/Alghanem/tree/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd).

The inventory also checks pinned Taaqol-GPT, Qeyas, alasmaa, alghanem-constitution, dal-madlul-constitution, hamil-constitution and hamil-hala-zaman-program for Lean files and selected morphology terms. At these pins, Taaqol-GPT, Qeyas, alasmaa and the three carrier/sign constitutions have no `.lean` files. Alghanem-constitution has one, without the selected morphology terms. This is a scoped inventory result, not a finding that those repositories have no useful non-Lean learning, identity or provenance machinery. Qeyas here is the recorded source snapshot `f20c1ee1cd7f8f3fb8e1c90c79bb8bf6f1138cc7`, not a claim about later reviewed branches.

## What the existing Lean actually licenses

| Source | Contract present in the pinned file | Premises still required | NABT reuse decision |
|---|---|---|---|
| Mashru `Jisr/JisrDal.lean` | `hukm` reads endings after a `Bab` is supplied. `mamnu_fatha` preserves accusative/genitive ambiguity; `mamnu_bi_al` reads genitive kasra in the al/idafa context. | The word's lexical inflection class and the presence of al/idafa are already known. | Reuse the separation between class, surface ending and contextual case. Build the class evidence before calling the contract. |
| Mashru `Jisr/QiraaSimat.lean` | `qiraa_min_raqm` and `qiraa_min_annEnc` read deposited pronoun traits from decoded cells. `la_dalla_tasturidd` proves that identical cells for `هما` cannot recover both gender readings by a single-valued function. | A deposited pronoun table and its cells/traits; the file explicitly excludes general tense, definiteness and building extraction. | Preserve candidate sets. Never reinterpret successful decoding as independent property acquisition. |
| Mashru `SLGE/Simat.lean` | `attr_value` gives injectivity of supplied annotations. `mahall_mabni` separates a built form from its syntactic position in finite examples. | Supplied `Attr`, frame membership and the file's simplified slot rules. | Reuse identity and the surface/local-role distinction; do not universalize the tense-to-building simplification. |
| Mashru `SLGE/Simat2.lean` | `ext_value` preserves encoded extensions; `linkOK2` uses an already supplied جامد flag to control predicate agreement. | Jamid status, agreement features and frame are inputs. `extAt`/`e0` default this flag to `false`. | Keep absent evidence unknown. Do not convert a default false flag into proved مشتق. |
| Mashru `Dal/AqsamAlism.lean`, `Jisr/TasnifAlism.lean` | An exhaustive finite semantic classification and conditional theorems such as `mushtaq_iff`. | `yamnaShirka`, `istiwa`, `dhuSifa`, `muftaqir` are supplied semantic properties. The header explicitly says they are deposited with witnesses, not extracted from the word. | Preserve semantic genus/attribute classification as its own axis, with its own evidence. |
| Alghanem `A116/Qism.lean` | `binaFil`, `murab_iff`, `mabni_iff` distinguish past, command and imperfect; direct emphatic nun, separated emphatic nun and female nun are separate constructors. | Verb tense and the kind/attachment of nun. | Reuse this conditional structure. Do not infer nun kind from the last carrier alone. |
| Alghanem `A116/Mamnu.lean` | Boolean cause combinations, finite shape predicates and conditional genitive reading. | Supplied proper-name/description/other causes and surface features; original description and feminine conditions are not fully encoded. | Split lexical diptote eligibility from surface realization and keep missing cause evidence explicit. |
| Alghanem `A116/Hudud.lean` | `n_inj`, `jins_separates`, `kalima_inj`, `nFi_inj` preserve distinct identities. `thabit` checks final-haraka changes against a finite list. | The category was supplied to the encoding; list entries and spelling forms were deposited. | Reuse identity contracts. Do not promote finite-list invariance to a universal grammatical building theorem. |
| Alghanem `A116/RootGrade.lean` | Complete enumeration and numbering by radical degree; `khumasi_jamid` follows the defined degree classification. | A justified count of **original radicals**, not written cells; the gate also includes recorded owner choices. | Keep radical analysis separate from spelling length and from nominal semantic genus. |
| Alghanem `A116/Dalalat.lean` | `shuroot_thalatha`, `mushtaq_la_yakfi`, `kulli_la_yuayyin`, `wazn_la_yuayyin_mutawaa` separate a descriptive form from causal/usage claims. | Deposited meanings, mental implications and source witnesses. | Preserve these non-implication boundaries. An agent-noun pattern alone does not license causality or every lexical derivative. |

The inventory of `Madlul/Jamad.lean` is deliberate: that file concerns physical الجماد, including material states. Its name must not be counted as a theorem about morphological الجامد.

### A concrete unsafe transfer: every imperfect is inflected

Mashru `SLGE/Simat.lean`, `slotAttrOK`, accepts the verb building flag through `mb == (tn != 1)`. Within that checker, every imperfect tense value therefore has `mb = false`. That is a model restriction, not the complete language rule.

Qatr lines 65–69 and Alfiyya lines 65–67 expressly include built imperfects with female nun or **direct** emphatic nun. Alghanem `Qism.binaFil` models this distinction. NABT should carry the attachment evidence and retain the named unknown when the text cannot establish it. A visible nun, an emphatic mark or a suffix-like spelling is insufficient alone.

### A concrete unsafe transfer: finite invariance proves building

Alghanem `Hudud.mabniyyat` includes `هَذَانِ` and `هَاتَيْنِ` in the demonstrative list and `أَيُّ` in relative/interrogative lists. `thabit` proves that changing the **final haraka** either returns a listed form unchanged or leaves the finite list. This statement can be true without proving that every listed linguistic item is invariant under grammatical case.

The paired primary passages provide the missing boundaries:

- `alfiyya_dual_demonstratives`, lines 137–144, distinguishes `ذان/تان` from `ذين/تين`.
- `alfiyya_relative_noun_exceptions`, lines 146–160, gives dual relative behavior and conditions on relative `أي`.

No universal rule `relative ⇒ built` or `demonstrative ⇒ built` is licensed by those finite lists. A safe transfer preserves the list as attestations and the numerical identities as identities, while giving exception-sensitive grammatical rules separate evidence.

## Primary-text constraints to implement

### The word-kind definition precedes its inflection rules

The noun/verb/particle enumeration in Qatr is not by itself a definition of the reader's `independent` and `time_in_form` properties. The primary definitions for those properties are in الشخصية ج3 line 373, anchored separately as `j3_particle_definition`, `j3_verb_definition` and `j3_noun_definition`.

The time condition concerns what the word indicates **by its morphological form**. A lexical meaning involving time does not automatically establish a verb: the source expressly distinguishes lexical temporal meaning from temporal indication by form. A parser may treat an explicit claim of no temporal meaning as sufficient for no temporal indication by form, but a bare claim of an event associated with time does not justify setting `time_in_form = true`. That stronger property needs its own qualified clause or derivation.

### الاسم: inflection, building and estimated endings

`qatr_noun_inflection_building` defines معرب by ending changes **because of governors**, and مبني by the contrary. Its `قبل/بعد` example also has explicit conditions: omitted complement with its meaning intended. A constant observed ending in one sentence does not establish building.

`qatr_estimated_cases` supplies an equally important counterexample to a surface-only rule: maqsur, manqus and other forms may carry estimated inflection. NABT must keep at least the following distinctions:

- inflection/building status;
- syntactic case or local grammatical position;
- realized mark or an estimated mark;
- lexical subclass and the evidence selecting it.

A built word can have a syntactic position; a word without a changed visible haraka can still be inflected. The current primary passages establish these distinctions, not a complete classifier for every Arabic noun.

### الفعل: status depends on tense and attachments

`qatr_past_building` licenses past building and records the waw-al-jamaa and moving raised-pronoun conditions for its ending. `qatr_imperative_building` licenses command building while distinguishing sound, weak-final and nun-deletion forms. `qatr_imperfect_nun` licenses the imperfect cases described above.

Thus these are different operations:

1. Find evidence that this reading is a verb and determine its tense.
2. Find attachment evidence and its scope.
3. Determine building/inflection.
4. Determine the realized mark, if the relevant subclass is established.

The first three do not automatically complete the fourth. In particular, a contract returning `mabni` cannot by itself justify a final-sukun explanation for every command form.

### الحرف: building follows an established word class

`qatr_particle_building` and `alfiyya_inflection_building` state particle building. Qatr first distinguishes the particle from noun/verb signs. This does not make failure of an incomplete recognizer a proof that an unknown word is a particle. The positive classification or a complete applicable exclusion argument must precede the building judgment.

### الممنوع من الصرف: cause and case realization are separate

The source-supported structure is:

\[
\text{established diptote cause} + \text{established genitive context}
\longrightarrow
\begin{cases}
\text{kasra},&\text{with al or idafa},\\
\text{fatha},&\text{without those overrides, within the covered class}.
\end{cases}
\]

`qatr_diptote_genitive` and `alfiyya_diptote_genitive` establish the override. Adding al does not justify deleting the record of the lexical diptote cause. Mashru's `Bab.mamnu (alAwIdafa)` keeps that distinction more directly than Alghanem's `mamnu = !tanwin && !al && causes`, which folds eligibility and its current surface environment together.

`alfiyya_diptote_causes` must remain available in full when establishing causes. It contains conditions not captured by an unqualified pattern label:

- the relevant adjective status is original, not merely incidental;
- أفعل/فعلان descriptions have feminine-form conditions;
- proper-name causes have qualification and length conditions;
- some feminine proper names admit alternatives;
- poetic or comparable exceptional use is recorded.

Consequently, `matches_afal_shape` is a shape observation, `is_original_description` is a lexical proposition, and `genitive_under_preposition` is contextual evidence. They require distinct derivations. Missing lexical evidence must not be replaced by `false`, and absence of tanwin in a particular spelling must not be treated as a complete proof of diptote status.

#### Qualification of the eleven positive `Mamnu.Sifat` fields

The following table specifies the evidence that a safe translation would have to preserve. It is a source audit, not an assertion that all eleven extractors are implemented.

| Upstream field | What a lexical statement/witness must establish | Source boundary |
|---|---|---|
| `alam` | Proper-name use in the relevant reading. | Proper-name status alone is not a cause pair. A previously proper name used indefinitely can change the result (Alfiyya 878). |
| `wasf` | The relevant original descriptive use, with the conditions of its partner cause. | Incidental descriptive use is explicitly distinguished (854–859). A syntactic adjective label alone is insufficient. |
| `tanithAlif` | The alif is an alif of femininity in the lexical analysis. | This cause stands by itself (853); merely ending in alif does not establish the property. |
| `muntaha` | An established plural construction of the مفاعل/مفاعيل class or an independently licensed analogue. | The source qualifies the plural pattern and treats سراويل separately (862–865). A positional carrier pattern alone does not establish pluralhood. |
| `falan` | Added alif and nun in the relevant فعلان construction; for its descriptive path, the feminine-ta exclusion. | The descriptive and proper-name paths have different qualifications (854, 867). |
| `afal` | An original descriptive أفعل construction whose feminine is not formed with ta. | Both original description and the feminine condition appear together (855–857). |
| `adl` | The specific lexical alteration and its allowed description/proper-name class. | Descriptive examples مثنى/ثلاث/أخر and the one-to-four pattern family are explicit; proper-name and سحر conditions have their own passages (859–861, 874–875). A generic “altered” label should remain pending. |
| `tarkib` | A **mixed compound** proper name, تركيب مزج. | A generic compound or إضافة is insufficient (866). |
| `tanith` | A feminine proper name together with a licensed branch: ta-marked, or a qualified unmarked case. | Ta-marked names have a direct branch; bare feminine names require length/other qualifications, and Hind-like cases have alternatives (868–870). A universal `alam && feminine` shortcut is unsafe. |
| `ajamiOver3` | Foreign origin **and original proper-name status**, with length above three. | Contemporary borrowing, foreign spelling or a bare length test is insufficient (871). |
| `waznFil` | A proper name on a pattern specific to verbs or predominantly verbal. | Any shared noun/verb shape does not suffice (872). |

The remaining upstream fields, `tanwin` and `al`, are contextual observations. They must not be filled negatively merely because the parser has no observation. Idafa also needs its own positive contextual evidence, which `Mamnu.Sifat` itself does not represent. For a first implementation, the two self-sufficient causes can be supported through explicit lexical witnesses while the qualified pairs return their named missing premises.

### الجامد والمشتق: preserve three axes

These repositories use related vocabulary in different domains. A single Boolean would silently merge their claims.

| Axis | Evidence needed | What it must not determine automatically |
|---|---|---|
| Nominal derivational form: مصدر، اسم فاعل، اسم مفعول، صفة مشبهة، etc. | Source-supported construction, lexical relation and relevant pattern/usage constraints. | Grammatical role, agreement, action on an object or causal implication. |
| Semantic genus versus bearer of a property in a universal concept | The `dhuSifa` distinction in Mashru's semantic classification, with meaning evidence. | Original radicals, productivity of a verb or the noun's inflection status. |
| Verbal/non-verbal productivity by radical analysis | Evidence of original radicals and the scoped lexical paradigm. | Every string's class from its written length, or the semantic genus of every noun. |

`qatr_derived_nouns` and `alfiyya_derived_noun_action` explicitly separate form examples from conditions for syntactic action. A source that identifies an اسم فاعل does not automatically establish that it governs an object in the current context. `alfiyya_jamid_predicate` is a predicate-context rule, not an unrestricted extractor of lexical derivation.

`sibawayhi_radical_degree` discusses original and augmented forms. It cannot license “five written letters ⇒ جامد”. `sibawayhi_mutawaa_usage` and Alghanem's corresponding non-determination theorem also prevent an unqualified “same pattern ⇒ same available lexical derivative” rule.

The primary semantic discussion quoted in Mashru's comments refers to الشخصية ج3. This audit also located that text in Alghanem's pinned corpus: `j3_kulli_definition` anchors the relevant definition within line 375, and `j3_genus_derived` anchors line 376. These support the conditional universal-genus/property-bearing distinction directly. They do not collapse nominal derivational morphology, inflection and verbal productivity into that semantic classification; nor does a failure to find a derivational template establish genus status.

## NABT integration requirements

The extension should attach properties to an **occurrence reading**, not merely to an unscoped word string. A source statement can justify one reading while another remains possible.

For each inferred property, retain:

- immutable source identity and exact evidence span;
- the parsed proposition or lexical construction that the span supports;
- the occurrence/reading that it applies to;
- positive conditions, blockers and unresolved premises;
- the exact rule version and downstream consequences;
- an explanation that replay can reconstruct from these inputs.

Arithmetic numbering should preserve that typed structure. Re-encoding a caller-provided `mabni`, `mamnu` or `mushtaq` field cannot create the evidence that the field lacks. Likewise, a supplied source reference must actually bind to the statement that supports the property.

When a feature is unavailable, the correct residual is named: for example, “direct attachment of emphatic nun unestablished”, “original descriptive use unestablished”, or “idafa relation unestablished”. An explicit contradiction should remain different from an unavailable premise.

The initial extractor can have a deliberately narrow, published text grammar. A new lexical symbol introduced by a supported declaration can then be classified without a dedicated answer table. This demonstrates extraction within that grammar. It must not be reported as unrestricted understanding of prose, as a hidden evaluation, or as acquisition of every Arabic construction.

## Independent release checks suggested by the sources

The following are semantic acceptance cases, not a report that they have already run:

| Case | Required behavior |
|---|---|
| New noun with no source classification | Keep status unresolved; do not assume ordinary inflection. |
| Imperfect with female nun versus direct versus separated emphatic nun | Preserve the attachment distinction and apply the corresponding status rule. |
| Word ending in nun without an attachment analysis | Do not use its final carrier as proof of female/emphatic nun. |
| Dual demonstrative or relative `أي` | Preserve source exception conditions; no blanket built classification from Hudud list membership. |
| Diptote under genitive, then the same lexical class with al/idafa | Change the genitive realization while retaining the lexical cause and its provenance. |
| أفعل-shaped string without lexical adjective evidence | Record a shape candidate; retain missing conditions for the diptote claim. |
| Derived noun whose source action conditions are missing | Retain its supported class without assigning an unsupported governor role. |
| Source says جامد on one semantic axis only | Do not project it to all other jamid axes. |
| One evidence span replaced by a statement about another token | Reject or recompute the affected property; the old proof must not replay. |
| Added, removed or contradicted attachment/cause evidence | Recompute exactly the dependent conclusions and preserve unaffected occurrence identities. |

The first strategic milestone is therefore a bounded acquisition-and-revision path with source-bound extraction and replay. The source audit supplies its contracts and counterexamples; implementation and measured results belong in the runtime, formal and evaluation artifacts accompanying this change.
