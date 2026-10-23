# Conditional morphology: the formal contract

Law: `nabt.morphology.v1`. Specification: [Morphology.lean](../formal/Nabt/Morphology.lean).
Exporter: [ExportMorphology.lean](../formal/ExportMorphology.lean).
The pinned toolchain is Lean 4.34.1. The module uses NABT and Lean's standard library;
it imports no upstream project at runtime or build time.

## What is established

The module gives a finite, executable algebra for **supplied, source-qualified
grammatical properties**. It keeps construction, nominal semantic denotation,
diptote causes and contextual genitive realization separate. Missing evidence
retains possibilities. Relevant inconsistent evidence is a conflict.

The module's 46 named theorems include exact inverse/candidate contracts,
refinement, typed numerical round trips, conditional grammatical rules and
counterexamples to unsafe inference. The number of theorems is an inventory,
not a measurement of Arabic understanding. Some establish a law for arbitrary
inputs; others verify a finite domain or one counterexample. They are identified
below by their actual scope.

The module does **not** prove that Python extracts a true property from a source,
that a source is authentic, that a shape determines a root, or that these rules
cover every Arabic word or interpretation. Source extraction and replay must be
checked separately against the retained text, occurrence, reading, conditions
and rule version.

The immutable sources and the interpretations used here are recorded in
[MORPHOLOGY_SOURCE_AUDIT.md](MORPHOLOGY_SOURCE_AUDIT.md) and
[source_passages.json](../evidence/morphology/source_passages.json).
The central source contracts are Alghanem `Qism.lean` and `Mamnu.lean`, and
Mashru `AqsamAlism.lean` and `TasnifAlism.lean`. The audit also anchors their
grammar and semantic distinctions to primary passages. The native contracts
deliberately do not inherit every simplification in those programs.

## Separate axes and their premises

| Axis | Input required | Conditional result | What the result does not establish |
|---|---|---|---|
| Word kind | Existing `Words` evidence and preserved reading | noun, verb or particle | A missing classifier result does not establish particlehood. |
| Noun construction | Licensed grammatical resemblance to a particle, positively or negatively established | built or inflected | Unchanged spelling in one observation is not evidence of building. |
| Verb construction | Established tense and nun attachment class | built or inflected | A visible nun alone does not identify its grammatical relation. |
| Particle construction | Established particle reading | built | It does not assign a syntactic role or local grammatical case. |
| Nominal semantic denotation | Universal-noun scope and meaning as genus or bearer of a quality | `jins_jamid` or `mushtaq_quality_bearer` | No etymological root, morphological derivation, verbal productivity or governor role follows automatically. |
| Diptote cause | Qualified lexical factors and the relevant noun reading | Result of the finite cause formula | Absence of a surface tanwin mark does not prove a cause. |
| Diptote genitive sign | Established diptote premises, with al/idhafa evidence | Conditional fatha or kasra, or pending/conflict | The sign table does not establish that this occurrence is genitive. |

### Construction is a relation, not an isolated spelling

`BuiltOn licensed realize` quantifies over the explicitly licensed contexts of
one fixed reading. `singleton_observation_does_not_prove_built` constructs an
ending function which is constant on the one observed context but changes in a
second context. It is a counterexample to inferring general invariance from one
unchanged token, not a complete formal definition of all Arabic building.

This matters for estimated inflection, dual demonstratives and relative `أي`.
The finite list in Alghanem `Hudud.thabit` cannot replace their conditions.
The native noun operation therefore receives a qualified resemblance premise;
it does not look up every demonstrative or relative as automatically built.

### Verb construction

`verb_inflected_iff` establishes the exact conditional rule:

\[
\operatorname{inflected}(t,n)\iff
t=\operatorname{imperfect}\land
(n=\operatorname{none}\lor n=\operatorname{separatedEmphatic}).
\]

Past and imperative readings are built in all four attachment states.
Imperfect readings with direct emphatic nun or feminine-plural nun are built.
The twelve rows enumerate the complete **declared input product**; they do not
assert that every tense/attachment pair is an attested Arabic word.

`VerbQuery.nun = none` means no nun classification has been established.
`VerbQuery.nun = some .none` is an established absence of the relevant nun
relations. `unknown_imperfect_nun_is_not_absent` proves these yield different
candidate sets. `fixed_past_does_not_need_nun` shows that an unknown attachment
does not block a conclusion when the known tense already determines it.

`verbReadings` retains correlated tense/attachment input pairs, while
`verbCandidates` projects their possible construction results. Exact membership
and complete-input theorems describe both operations.

### The scope of الجامد والمشتق in this law

`nominalDenotation` implements the semantic universal-noun division in
Mashru and the pinned primary passage from الشخصية ج3. Its public labels are:

| Code | Label | Meaning in this law |
|---|---|---|
| 0 | `outside_universal_noun` | The universal-noun division is not applicable. |
| 1 | `jins_jamid` | An established universal noun denotes a genus/essence under the cited criterion. |
| 2 | `mushtaq_quality_bearer` | An established universal noun denotes a bearer of a specified quality under that criterion. |

An unknown quality premise retains both codes 1 and 2. A particular noun is not
thereby classified as genus. `semantic_mushtaq_requires_both` makes universal
scope and quality-bearing content explicit. The two orthogonality theorems
show that the semantic input cannot change construction, and a construction
input cannot change semantic denotation.

This module does not implement a proof of root-pattern derivation from spelling,
or the separate classification of a non-conjugating verb as جامد. In particular,
failure to match Alghanem's finite template ledger is not accepted as proof of
semantic genus or absence of every morphological derivation.

## Intrinsic diptote causes and their 2,048 input masks

The bounded cause law retains eleven factors from Alghanem, with qualifications
made explicit by the primary-text audit. In bit order:

`alam, wasf, tanithAlif, muntaha, falan, afal, adl, tarkib, tanith, ajamiOver3, waznFil`.

The cause formula is:

\[
\begin{aligned}
D={}&(\mathrm{tanithAlif}\lor\mathrm{muntaha})\\
 &\lor[\mathrm{wasf}\land(\mathrm{falan}\lor\mathrm{afal}\lor\mathrm{adl})]\\
 &\lor[\mathrm{alam}\land(\mathrm{tarkib}\lor\mathrm{falan}\lor
 \mathrm{tanith}\lor\mathrm{ajamiOver3}\lor\mathrm{waznFil}\lor\mathrm{adl})].
\end{aligned}
\]

Neither al nor tanwin is a cause input. Idhafa is also a separate contextual
property. In contrast with directly transferring Alghanem's full `mamnu`
function, adding al does not erase the stored lexical cause.

Every positive bit means a **source-qualified factor for this reading and this
branch**. For example, `wasf` includes the relevant original description;
`afal` includes its feminine-form condition; `tarkib` means the licensed mixed
compound; and `tanith` must select a licensed proper-name branch, preserving
cases with alternatives. A bare surface pattern or unqualified feminine label
cannot fill these bits. The source audit contains the eleven-factor qualification
table and exceptions.

`CauseInput = Fin 2048` is the typed domain. The export includes every mask from
0 through 2047 and the formula result. This is totality over the Boolean cube,
not attestation that all combinations occur in Arabic, or a theorem that the
source's complete linguistic qualifications can be recovered from those bits.

`CauseQuery` assigns an `Evidence` state to each trait. `cause_candidates_exact`
proves that a mask survives precisely when every one of its bits satisfies the
supplied evidence. `cause_prediction_exact` identifies every projected Boolean
result with a surviving complete mask. The two refinement theorems show that
additional compatible evidence removes candidates and cannot introduce an
unsupported result. Unknown evidence keeps every compatible complete input;
conflict has no completion. A false result remains relative to this qualified
eleven-factor model, rather than a global exclusion of every Arabic exception.

## Contextual genitive realization and computed residuals

The context operation evaluates the positive formula `al OR idhafa` using the
existing `Nabt.Obligations` algebra. Each contextual fact has four evidence
states: unknown, affirmed, denied and conflict. There are sixteen pairs.

| Evidence about al and idhafa | Conditional sign result | Positive plans to establish the override |
|---|---|---|
| Both unknown | pending; fatha and kasra remain possible | `{al}` or `{idhafa}` |
| al affirmed; idhafa unknown | kasra | Empty plan: supplied positive evidence already suffices. |
| al denied; idhafa unknown | pending | `{idhafa}` |
| Both denied | fatha | No admissible positive override completion. |
| Either relevant fact conflicts | conflict | Internal plan arithmetic is not permission to act. |

`fatha_requires_both_negatives` prevents treating missing context as established
absence. `kasra_requires_supported_override` requires an affirmed override and
no relevant conflict. `genitive_singleton_iff` proves that an emitted sign is
exactly the sole remaining sign among all compatible Boolean contexts.

The plans in the table are specifically **positive obligations to establish the
kasra override**. They are not a claim that a pending case can only be resolved
by adding positive facts. Establishing both negative facts can instead resolve
the case to fatha. Runtime explanations must preserve that distinction.

`genitive_residual_sound` and `genitive_residual_complete` specialize the existing
general obligations proofs: a returned plan suffices for the override, and
every admissible successful positive completion contains a returned plan.
They do not license inventing facts. Raw internal plans may be present even
under conflicting support; the conflict verdict takes priority and prevents
their use as a realized grammatical judgment.

The pure `genitiveResult` is a **conditional sign prediction**. The stronger
`realizeDiptote` wrapper requires a `LicensedDiptote` carrying
`ConstructionWitness identity.word .inflected`, and a separately supplied
`GovernmentWitness` for that same `Words.Analysis` in `.jarr`. An unrelated
enum set to `inflected` cannot fill the construction premise. The wrapper
preserves the original occurrence/reading and cause identity. The arbitrary
witness predicates are explicit assumptions whose evidence binding must be
checked by the external reader and replay path; Lean does not manufacture
their authority. The al/idhafa evidence in `GenitiveContext` is also a supplied
input: associating it with this occurrence, reading and context is an external
replay obligation. These contracts are not a proof of the Python parser or of
the authenticity of any extracted source property.

## Numerical interoperability

| Numerical domain | Formula or representation | Bounds |
|---|---|---|
| `nabt.morphology.verb-input.v1` | `4 * tense_code + nun_code` | 0–11 |
| `nabt.morphology.qualified-causes.v1` | Eleven qualified cause bits | 0–2047 |
| `nabt.morphology.diptote-context.v1` | `al_evidence_code + 4 * idhafa_evidence_code` | 0–15 |
| `nabt.morphology.diptote-residual.v1` | Bit 0 means al; bit 1 means idhafa | Plans within these named obligations |

Evidence codes are unknown=0, affirmed=1, denied=2 and conflict=3. Construction
codes are built=0 and inflected=1. Tenses are past=0, imperfect=1 and imperative=2.
Nun codes are none=0, direct-emphatic=1, separated-emphatic=2 and feminine-plural=3.
Genitive result codes are pending=0, fatha=1, kasra=2 and conflict=3. Ending codes
remain the existing `Words` codes; fatha=1 and kasra=2.

Verb-input and genitive-context round-trip/injectivity theorems preserve these
typed pairs and reject out-of-domain natural numbers. These local input codes
do not replace source occurrence identity, reading identity, evidence intervals,
or the runtime's canonical report encoding. The same integer in another domain
is not interchangeable. Runtime APIs must additionally reject booleans where
integers are required and check canonical representation.

The exporter emits the full bounded operations:

| JSON section | Rows | Coverage |
|---|---:|---|
| `verb_rows` | 12 | All complete tense/attachment pairs |
| `verb_partial` | 20 | All Option-valued tense/attachment pairs |
| `noun_rows` | 2 | Both qualified resemblance values |
| `noun_partial` | 4 | All resemblance evidence states |
| `nominal_rows` | 4 | Both universal and quality-bearing Boolean values |
| `nominal_partial` | 16 | Every pair of their evidence states |
| `cause_rows` | 2,048 | All eleven-bit cause assignments |
| `genitive_rows` | 16 | Every al/idhafa evidence pair, signs and residual plans |

## Verification and remaining obligations

The module and exporter compiled successfully under the pinned toolchain during
this change. The exported table is generated by Lean, not entered manually.
Project-level theorem-manifest, axiom-audit, Python-conformance, independent
evaluation and CI results must be recorded by the integration checks; this
document does not claim those runs merely because local Lean compilation passed.

The strategic remaining obligation is extracting and revising the qualified
properties from progressively broader Arabic text. This law enables that work
to be checked at the property-to-conclusion boundary. It does not make an
unread source statement, an arbitrary lexical annotation, or an unverified
certificate into a grammatical proof.
