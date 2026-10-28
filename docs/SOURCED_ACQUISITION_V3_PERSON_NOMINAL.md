# Sourced acquisition v3: person and finite nominal predication

Status: specification proposal; freeze this document and the source packet,
then the independently authored matrix, before implementation or first scoring.
Repository base: `b5f5bf1e09254b0d91b3ac4ed4e7bfe5b772176a`.

Adapter law: `nabt.acquired-person-nominal.v3`.
Native finite grammar law: `nabt.acquired-syntax.v3`.
Proposed implementation owners/files:

- `tools/acquired_person_nominal_v3.py` and its new tests;
- `formal/Nabt/AcquiredSyntaxV3.lean`;
- `formal/AcquiredSyntaxV3Main.lean`, executable `acquiredSyntaxV3`.

This is an additive exact-source bridge. Historical v1/v2 implementations,
source packets, matrices, scores and receipts remain unchanged. It does not
relabel the old person/nominal `UNMEASURED` rows as newly successful rows.

## Authority and source interpretation

The shared acquisition dependency is
`tools.connected_acquisition_v3.read_acquired`. It preserves the original
source and distinguishes citation cells from connected realization. This bridge
must invoke that dependency afresh for every evaluation. It never supplies a
replacement vocalized string to acquisition, syntax, or verification.

The native grammar independently reads the same original text and binding.
It licenses only the finite readings and frames below. Its source-language
reference is the declared finite relation, not unrestricted Arabic. A theorem
of parser exactness proves agreement with that relation; it does not prove
that an authored source interpretation exhausts the book or Arabic.

Source evidence must be copied into the new v3 source packet with exact file
hash, byte span, original text, line coordinates, attribution and separate
authored interpretation. These source files already exist under
`src/nabt/data/source_evidence/`:

| Witness | Source lines | Bounded use and restriction |
|---|---:|---|
| Pronoun and the tāʾ of `قمت` | `qatr.txt` 123–126 | Establishes an attached pronoun example; the unmarked quotation itself is not a byte witness for three unprinted vowels. |
| Three tāʾ vowels | `sabban.txt` 6186–6194 | Explicitly says tāʾ is rounded for speaker, opened for masculine addressee, and broken for feminine addressee. Other dialectal/extensions mentioned there remain outside this table. |
| Nominal subject/predicate | `qatr.txt` 152–164 | Both are nominative; predicate alternatives and fronting exist. Nominative adjacency alone is not sufficient. |
| Ordinary fronted predicate | `ibn_aqil.txt` 1623–1634 | Permits fronting when it introduces no confusion; the finite definite-subject/indefinite-descriptive-predicate frame below is the selected interpretation. |
| Fronting restrictions | `ibn_aqil.txt` 1646–1668 | Retain the distinction from two equally definite/indefinite constituents and from finite verb–subject order. These are not silently admitted. |
| Descriptor alternatives/dispute | `ibn_aqil.txt` 1371–1443 | Interrogative/negative descriptor frames, descriptor-as-subject and school/dialect alternatives are separate domains. They are not inferred from an ordinary two-word frame. |
| Dual and sound plural signs | `qatr.txt` 75–86 | Nominative alif/waaw and oblique yaa under independently identified classes; no suffix-only discovery of a nominal class. |
| Predicate agreement | `ibn_aqil.txt` 7838–7844 | States number and gender agreement in the surrounding relative-predication discussion. Use only for the explicitly declared ordinary human-subject descriptive frame, not a universal Arabic agreement theorem. |
| `ذهب` / `ذاهب` | `ibn_aqil.txt` 5653–5658 | Gives the active-participle example and its pattern; the installed vocalization is an authored reading convention, not a verbatim fully marked quotation. |
| `ولد` and collective ambiguity | `mukhtar_sihah.txt` 13767–13771 | Retains that `ولد` may denote one or a collective, and the occurrence `أولادا`. No actual cardinality follows from grammatical agreement. |
| `الأولاد` occurrence | `sibawayhi.txt` 2112–2115 | Additional finite lexical occurrence; neither the occurrence nor its hash proves external individuals or an exhaustive lexicon. |

The shared source packet must identify which conclusions are explicit in the
passage and which are bounded authored applications. In particular, no passage
above is represented as a verbatim citation of `الولدُ ذاهبٌ`. That sentence is
an authored composition under the finite source-informed grammar.

## Exact lexical surface table

Use literal scalar equality. No NFC/NFD transformation, tatweel removal,
combining-mark reordering, generic vowel omission, regex suffix classification,
or caller-supplied lexical profile is an admission rule.

The short forms below are deliberately enumerated citation spellings. Each
correspondence is a new authored reading convention in the v3 source packet.
The original short form, its spans and its convention ID survive every receipt.
This is not an unvowelized-text acquisition policy.

| Reading ID | Exact full surface | Exact short surface | Finite grammatical projection |
|---|---|---|---|
| `QUMTU` | `قُمْتُ` | `قمتُ` | past verb; first person; singular; gender unspecified |
| `QUMTA` | `قُمْتَ` | `قمتَ` | past verb; second person; singular; masculine |
| `QUMTI` | `قُمْتِ` | `قمتِ` | past verb; second person; singular; feminine |
| `WALAD` | `الْوَلَدُ` | `الولدُ` | definite human noun; ordinary singular agreement; nominative |
| `WALAD_DUAL` | `الْوَلَدَانِ` | `الولدانِ` | definite human noun; dual agreement; nominative |
| `AWLAD` | `الْأَوْلَادُ` | `الأولادُ` | definite human noun; plural agreement; nominative |
| `DHAHIB` | `ذَاهِبٌ` | `ذاهبٌ` | indefinite descriptive predicate; masculine singular; nominative |
| `DHAHIB_DUAL` | `ذَاهِبَانِ` | `ذاهبانِ` | indefinite descriptive predicate; masculine dual; nominative |
| `DHAHIB_PLURAL` | `ذَاهِبُونَ` | `ذاهبونَ` | indefinite descriptive predicate; masculine plural; nominative |

Shared acquisition may additionally acquire independently documented off-case
surfaces, but that does not install them in this nominative grammar. A case or
agreement mismatch is `DEFER` for this frame, not an assertion that the entire
Arabic string is impossible in every context.

For `WALAD`, `number="singular"` describes the ordinary morphological
agreement projection. Always retain
`lexical_cardinality_alternatives=["individual","collective"]` and
`denotation_cardinality=null`. Do not choose an individual sense merely to make
the predicate agree. The two lexical candidates share the same projected
syntactic roles; neither has an identified real-world referent.

`WALAD_DUAL` and `AWLAD` are finite installed readings, not a productive rule
that attaches a suffix to any acquired noun. Their cardinality in the world
also remains null.

## Complete finite frames

### Person

A person input has exactly one lexical word from `QUMTU/QUMTA/QUMTI`, plus
the permitted surrounding separators below. Report the source tāʾ and its
original vowel. Do not obtain person from final A116 cells after pause: all
three final pronunciations may converge while the original written evidence
remains distinct.

Exact undecided forms `قمت`, `قُمْت`, and `قُمْتْ` retain the three *diagnostic*
person hypotheses but have no admitted person reading and no complete chain.
The diagnostic list does not license missing stem vowels, replace the source,
or claim that these three hypotheses exhaust unrestricted Arabic homography.
An explicitly wrong or duplicate vowel is not an undecided form.

For exactly those three undecided surfaces, the ordered diagnostic list is
`[{"reading_id":"QUMTU","person":1,"number":"singular","gender":null},
{"reading_id":"QUMTA","person":2,"number":"singular","gender":"masculine"},
{"reading_id":"QUMTI","person":2,"number":"singular","gender":"feminine"}]`.
For other inputs it is the empty list. These are typed diagnostic projections;
none contains a referent, licensed status, or a replacement source string.

The result never identifies the speaker/addressee, assigns a real-world action,
or resolves discourse reference. `person=1/2` is a grammatical index, not an
entity ID. First-person gender remains JSON null, not a default masculine.

### Nominal predication

There must be exactly two lexical words, one from the definite subject class
`WALAD/WALAD_DUAL/AWLAD` and one from the indefinite descriptive predicate class
`DHAHIB/DHAHIB_DUAL/DHAHIB_PLURAL`. Both must satisfy their exact lexical
entries; both are nominative in those entries; number and gender must match.

Enumerate both orders:

1. `SUBJECT PREDICATE`: subject index 0, predicate index 1;
2. `PREDICATE SUBJECT`: subject index 1, predicate index 0.

Indices refer to original lexical-word order, not character positions.
Roles, case observations and agreement belong to the same analysis and the
same two source occurrences. No role can be borrowed from another reading,
source, revision, scope or order.

Definiteness, lexical class, descriptive-predicate class, whole-clause
exhaustion and the declared source grammar are required in addition to case.
Thus two arbitrary nominatives do not become a predication. An adjective phrase
with a definite predicate, two indefinite nouns, two definite names, a finite
verb followed by a noun, an unknown noun, a PP, an interrogative/negative
descriptor frame, or an extra word is outside this grammar.

The nonasserted lexical alternatives of `WALAD` are preserved on the nominal
projection. No single intended lexical sense, actual number of children, time,
physical departure or truth of the utterance is established. The parser is
complete only for its installed finite ordinary-predication frame. Competing
school/dialect or discourse analyses outside that frame remain declared scope
limits, not silently refuted analyses.

### Separators, quoting and force

The grammar permits surrounding ASCII spaces/tabs and one or more ASCII
spaces/tabs between the two words. It permits at most one final ASCII period
`.` followed by spaces/tabs. A period is retained as a boundary, never dropped
from the source receipt. No other punctuation is an alias for that period.

Newline/CR, comma, semicolon, interrogation/exclamation marks, parentheses,
quotation marks, multiple periods, multiple clauses, leading operators and
trailing text cause `DEFER/OUTSIDE_DECLARED_GRAMMAR` and no admitted reading.
In particular, finding the phrase inside a quotation must not assert it.

## Public interface and stable semantic fields

```python
evaluate(text, *, task, source_id="input", revision="1", scope="default",
         ending="wasl", onset="word_initial") -> dict

verify(report, *, text, task, source_id, revision, scope, ending, onset) -> dict
```

`task` is exactly `"person"` or `"nominal_syntax"`; it selects which installed
grammar is measured, not an expected answer. Text accepts exact UTF-8 `str` or
`bytes` using the shared acquisition input contract. Metadata follows the
existing nonempty bounded identity contract. `ending` and `onset` use the shared
v3 enums; ending changes pronunciation evidence only, never the original
source morphology. Connected admission remains conditional on the shared
acquisition/realization gate, not on syntax alone.

Stable report fields:

```text
schema = "nabt.acquired-person-nominal-result.v3"
law_id = "nabt.acquired-person-nominal.v3"
task, binding, source_sha256
status = LICENSED_PERSON | LICENSED_NOMINAL | DEFER | INVALID_INPUT |
         RESOURCE_EXHAUSTED | VERIFICATION_UNAVAILABLE |
         VERIFICATION_FAILED | SOURCE_EVIDENCE_UNAVAILABLE
verified: bool
chain_complete: bool
acquisition: complete shared v3 acquired-reading receipt
syntax: complete fresh native finite-grammar receipt
gates: object of exact Boolean component checks
blocked_by: list of explicit unmet checks/reasons
person: null or the single licensed grammatical person projection
nominal: null or the licensed common syntactic projection
diagnostic_person_hypotheses: ordered list; never admitted readings
world_truth_established = false
referents_established = false
all_arabic_complete = false
```

On a complete person chain, `/person` contains:

```text
reading_id = QUMTU | QUMTA | QUMTI
category = "verb"
tense = "past"
person = 1 | 2                  # JSON integer, never Boolean
number = "singular"
gender = null | "masculine" | "feminine"
subject_form = "attached_ta"
word_index = 0
source_vowel = "ُ" | "َ" | "ِ"
referent = null
```

On a complete nominal chain, `/nominal` contains:

```text
subject_index = 0 | 1
predicate_index = 1 | 0
subject_lexeme = WALAD | WALAD_DUAL | AWLAD
predicate_lexeme = DHAHIB | DHAHIB_DUAL | DHAHIB_PLURAL
order = "subject_predicate" | "predicate_subject"
number = "singular" | "dual" | "plural"
gender = "masculine"
subject_case = "nominative"
predicate_case = "nominative"
lexical_cardinality_alternatives = ["individual","collective"] for WALAD,
                                 [] otherwise
denotation_cardinality = null
referent = null
```

Every licensed projection additionally contains exact source word/suffix spans
and raw substrings; both Unicode-scalar and UTF-8-byte bounds must restore
those substrings. Semantic field names above are stable for independent JSON
pointer expectations. Projection fields are null when the chain is incomplete,
even if a native syntax diagnostic found a matching frame. The native diagnostic
is retained with its own scoped authority; it cannot promote the composite.

`verified=true` is reserved for a complete composite chain. An exact deferred
report may have `verify(...).replay_matches=true`, but its `valid` is false.
`verify` reruns all installed dependencies against the independently supplied
raw text and every binding field and compares the entire typed JSON report.

## Component gates and failure precedence

1. Validate types, UTF-8, metadata, task, onset, ending and budgets. Reject
   booleans where integers are required. Retain duplicate-key/nonfinite JSON
   protections for native transport and receipt verification.
2. Read and validate the pinned v3 source packet and actual retained source
   bytes/spans. A caller hash, manifest or `verified` Boolean grants no authority.
3. Invoke shared v3 acquisition freshly, with exact original bytes and binding.
   Malformed input, unavailable checker/source, verification failure and
   exhaustion remain distinct; none is a linguistic negative result.
4. Invoke `acquiredSyntaxV3` freshly on original text and the same binding/task.
   Require complete native/Python proposal equality, including tokens, spans,
   readings, ambiguity diagnostics, status and metadata.
5. A complete chain requires complete acquired source, every required citation
   and requested realization/shape handoff verified under the shared v3
   contract, source identity agreement, and a licensed finite native reading.
   Syntax cannot authorize an acquisition debt; acquired cells cannot authorize
   an absent lexical/grammar reading.
6. When one of these positive gates is absent, top-level projections are null
   and `chain_complete=false`. A grammar boundary ordinarily returns DEFER.

Use the shared maximum source budget (8192 UTF-8 bytes / 4096 scalars), the
existing metadata maximum (512 scalars), and an 8 MiB whole-report budget.
Do not truncate a reading set and then call the remaining set complete.

## Formal scope and required claims

The new Lean module must define an explicit finite lexical relation and
ordinary-predication relation separately from the parser. Prove parser
soundness and exactness/completeness for that declared relation, including
the finite person mapping and both admitted nominal orders. Preserve raw
request identity, and show no unique person is licensed for the undecided
person forms. Show number mismatch cannot satisfy this nominal relation.

The source packet pins source interpretation; it does not become an axiom that
all Arabic obeys this finite grammar. JSON parser/OS/native transport refinement
and general Python equivalence remain trust-boundary/testing claims unless
separately proved. Public theorem names and all new native artifacts enter the
root-coordinated current proof catalog after implementation.

## Independent matrix and first result

The independent author reads this frozen contract and source packet, not new
runtime code. Expected fields are JSON-pointer to typed-value maps. Positive
goals require the correct complete source-bound projection, not merely a safe
status or retained diagnostic.

Cover every finite lexical reading, both aliases, all three persons, both
ending modes, both supported onset modes, both nominal orders, singular/dual/
plural, every off-diagonal number mismatch, missing/duplicate/wrong marks,
unknown nouns, definite/indefinite adjacency boundaries, quotations, extra
tokens and source/binding changes. Keep source/receipt mutation and resource
controls in their own denominator. Include the three undecided person forms
with retained diagnostic ambiguity but no admitted complete reading.

Freeze source/spec first, independent matrix second, implementation and native
binaries third. Retain first execution including failures. Every repair run is
an exposed replay, and old v1/v2 reports remain distinct. These finite scores
must not be added to the historical matrices or called overall Arabic accuracy.
