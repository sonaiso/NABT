# Independent v3 matrix method

Source and all five component specifications were frozen before this matrix.
The final source-dependency freeze is
`d597b8583f21a6b31d709f79ffc8c5008ebc5f80`; its specification predecessor is
`88264da01a37698ae12e5195d0bf32706cd9b5b4`.
The matrix author did not read any new v3 production Python, native Lean
implementation, or evaluator. No NABT producer, acquisition reader, syntax
reader, native executable, semantic recognizer, or inference runtime was
executed to author expected results.

Gold schema: `nabt.sourced-acquisition-gold.v3`.
Gold SHA-256:
`c61c971adc4e88e4626a890f3fb304dfdeafcc3ac6b312e46854e1f3a67ccbee`.

| Family | Cases | Required positive goals |
|---|---:|---:|
| Orthography / connected realization | 50 | 47 |
| Person / category | 27 | 17 |
| Nominal predication | 34 | 18 |
| Conditional / natural meaning | 50 | 27 |
| Total | 161 | 109 |

Entry points: 50 connected representation, 61 person/nominal composition,
40 natural lexical reading, and 10 exposed unchanged PR34 controls. These are
separate APIs and authorities. They must not be treated as 161 examples of
one semantic or grammatical competence. The 40 natural rows measure bounded
lexical readings, preserved candidates, restraint, some complete sound chains,
and explicitly named still-required intention goals separately.

Each `expected` object maps JSON pointers to exact typed JSON values. These
assertions test the published bounded contract. Each `goal` independently
states its `kind`, whether the desired goal is positive, and the exact
`success` assertions needed to acquire it. Correct bounded abstention on a
required positive remains a coverage miss. A diagnostic alternative does not
satisfy a unique person, syntactic-role, or intended-sense goal. The evaluator
must additionally check complete source identity and alignment; a projection
match alone is not a sourceful safety certificate.

The orthography matrix includes every article canonical family and each
installed ordinary case vowel, the finite dual, sun assimilation without an
extra lam/ra, internal hamza retention, one-word initial retention, raw mark
order and wasla variants, an explicit partial alias, ordinary nonarticle joins,
and pause cases. Literal A116 arrays were derived by hand from the declared
carrier order and four states. The assembly helper concatenated separately
hand-authored word and realization-tail literals; it did not parse Arabic,
normalize text, invoke a classifier, or simulate a production recurrence.
Unsupported tanwin/sukun/long-vowel contacts, unlisted readings, malformed
marks, and separator contrasts remain explicit controls or positive debts.

Person rows include all three ta vowels, both complete and finite partial
spellings, wasl/waqf, connected single-word inputs, all three documented
undecided surfaces with the ordered three diagnostic hypotheses, and lexical,
quotation, extra-token and malformed-mark boundaries. Third-person verb goals
remain required positive debts. The isolated `حَمَا` control does not invent
an unsupported six-noun or person analysis.

Nominal rows include singular, dual and plural subjects and predicates, both
finite spelling sets, both constituent orders, all six off-diagonal number
mismatches, case/definiteness/whole-input boundaries, and connected contrasts.
The grammatical agreement number does not resolve the one/collective senses
of `ولد`, nor establish real-world cardinality or reference. A correct native
syntax reading cannot fill a missing connected-pronunciation license.

Natural rows cover both installed restrictive-adjective readings, all named
unmarked subject substitutions, positive and negative perception, fully marked
case patterns, exact orthographic aliases, pause and whitespace, unsupported
syntax, quotation, missing cues and implicit/unknown subjects. They retain the
three installed eye senses or two lion senses when applicable. Candidate
recall, literal lexical selection, a full sound chain, actual author intention,
and truth about the world are distinct. Semantic success on unmarked text
cannot be reported as sound acquisition. An accepted lexical alias whose
pronunciation is not installed remains a sound-chain miss.

The author read the frozen v2 specification/matrix and existing audit evidence
to retain known debts. The ten PR34 rows are disclosed **exposed historical
regressions** for the unchanged source/query composition, covering premises,
negation without inverse implication, changed subjects, quotation, unresolved
subjects, conflict and converse restraint. Historical natural context examples
are also disclosed exposed requirements. No secrecy or independent held-out
lexicon claim is made for these fixtures. Preimplementation independence
concerns the new producer, not ignorance of the project's prior failures.

Authoring checks validated UTF-8, unique IDs, the four family denominators,
entry-point/task enums, Boolean/integer separation, valid pointer keys, literal
cell domains and nonempty goal predicates. Exact hashes of the reviewed inputs
are recorded in `gold.json`. Such checks are not linguistic proof.

Preserve the first evaluation attempt, including preflight or contract failure.
All repair executions are exposed replays. Never change the frozen gold to
follow producer output; a genuine oracle erratum requires separate explicit
versioned evidence and retention of the original measurement. Resource, type,
source mutation, stale import/native, cross-word-span and receipt-tampering tests
belong in separate test denominators and cannot inflate these linguistic counts.
No finite score here certifies grammar generally, all Arabic, acoustics,
external reference, actual author intention, or world truth.
