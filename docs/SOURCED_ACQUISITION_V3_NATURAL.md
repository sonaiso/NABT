# Sourced acquisition v3: bounded natural lexical readings

This specification precedes the implementation and independent v3 matrix.
Law: `nabt.natural-acquisition.v3`. It is additive: historical linguistic-truth
inventories, laws, evaluations and first-run results are not changed.

## Evidence and authority

The existing linguistic-truth inventory and native `linguisticTruth` checker
remain authoritative for their installed conditional calculus. The additive
review is `evidence/sourced_acquisition_v3/natural_sources.json`; its source
files, byte intervals and quotations must be replayed on every call. Its SHA
is pinned in the implementation, never supplied by the caller.

Three lexical senses of **العين** are added: `ayn_eye` (الباصرة),
`ayn_spring` (الجارية), `ayn_gold` (الذهب). The retained linguistic source
explicitly lists all three. Maqayis supplies the eye and spring definitions;
Qatr supplies the restrictive adjective and agreement scope. These are three
installed senses, not all senses of عين. The source's designation report is
preserved; this adapter does not decide between accounts of historical transfer.
Mughni's explicit account of لم as negation, jussive government and past-time
conversion supports the separate negative assertion-polarity annotation.

Candidate retrieval also gains finite tanwin-alif aliases for أسد and عين.
These aliases and marked citation forms are authored finite orthographic and
inflectional interpretations, not claims that every exact surface is quoted
from the retained books. The short Qatr excerpts do not license a general
adjective parser or remove its gender/number and construction conditions.
There is no rule deleting an arbitrary final alif. All compatible installed
candidates remain visible even when a reading is selected. In particular,
roaring or speaking on a pulpit does not by itself prove unique intended
meaning of أسد; such contexts remain unselected here.

The new recognizer supports **bounded literal lexical readings under an
explicit linguistic-convention profile**. It does not certify grammar,
speaker intention, referent identity, the truth of a statement, or reality.
`author_intention_established`, `grammar_certified`, `world_truth_established`
and `all_arabic_complete` are always false. A native supported guard checks
the installed designation and acquired reading premises conditionally; no
general Python-to-Lean acquisition-refinement theorem is claimed.

## Whole-input grammar

One clause is accepted. Leading/trailing ASCII spaces or tabs, one or more
ASCII spaces or tabs between tokens, and a single optional terminal full stop
are allowed. Punctuation separators inside the clause, newlines, questions,
quotation marks, reported speech, or extra tokens prevent
selection. Raw source and exact UTF-8 spans are always preserved. There is no
Unicode normalization, diacritic stripping or token rewrite before matching.

The two adjective families are `جارية` -> `ayn_spring` and `باصرة` ->
`ayn_eye`. There is no natural cue selecting `ayn_gold` in v3.

Unvowelized/lightly marked productions, with `A` one of those adjectives:

| Production | Tokens | Assertion polarity |
|---|---|---|
| Indefinite noun phrase | `عين A` | none |
| Definite noun phrase | `العين الـA` | none |
| Perception | `رأيت عينًا A` or `رأيت عيناً A` | positive |
| Definite perception | `رأيت العين الـA` | positive |
| Negated perception | `لم أر عينًا A` or `لم أر عيناً A` | negative |
| Negated definite perception | `لم أر العين الـA` | negative |
| Drinking | `شرب S من عين جارية` or `شرب S من العين الجارية` | positive |

`S` is exactly `زيد`, `عمرو` or `المسافر`. Other subjects are not silently
mapped to one of them. The drinking production has only the spring adjective;
it does not infer a sense from the verb شرب alone. It has no implicit pronoun
resolution. These slots are a compositional grammar, not a table of complete
benchmark sentences.

The fully marked noun phrases also accept corresponding exact matched cases:

| Case | Indefinite noun | Spring adjective | Eye adjective |
|---|---|---|---|
| nominative | `عَيْنٌ` | `جَارِيَةٌ` | `بَاصِرَةٌ` |
| accusative | `عَيْنًا` or `عَيْناً` | `جَارِيَةً` | `بَاصِرَةً` |
| genitive | `عَيْنٍ` | `جَارِيَةٍ` | `بَاصِرَةٍ` |

The definite equivalents are `الْعَيْنُ/َ/ِ` with matching
`الْجَارِيَةُ/َ/ِ` or `الْبَاصِرَةُ/َ/ِ`. Fully marked perception is
`رَأَيْتُ P_acc`; fully marked negated perception is `لَمْ أَرَ P_acc`.
Fully marked drinking is `شَرِبَ S مِنْ P_gen`, with `S` exactly `زَيْدٌ`,
`عَمْرٌو` or `الْمُسَافِرُ`, and with the spring adjective. Marked and
unmarked productions are not mixed. Case/definiteness mismatches, omitted
adjectives, and appended material retain candidates but give no selected sense.

Negated perception changes only `assertion_polarity`. It does not exclude
the lexical meaning of the mentioned noun. The adapter makes no assertion
that the perception, its negation, or any external event is true.

## API and result contract

`tools.natural_acquisition_v3.evaluate(text, *, source_id="user_text",
revision="1", scope="unspecified", ending="wasl", onset="word_initial")`.
The revision is an opaque caller binding; actual raw UTF-8 SHA-256 is recorded
separately. All bindings must be nonempty bounded strings. Ending is `wasl`
or `waqf`; onset is `word_initial` or `connected`. Boolean/invalid input,
malformed UTF-8 and invalid modes give `INVALID_INPUT`. Native resource limits
remain `RESOURCE_EXHAUSTED`, never linguistic rejection.

The result exposes:

- `status`: `COMPLETE` for the recognized whole semantic grammar after native
  checking; `UNKNOWN` for valid but unsupported text; input/source/native/resource
  failures are separately named. `COMPLETE` here does not mean sound acquisition.
- `source`: original text, source id, opaque revision, raw SHA and byte length.
- `occurrences`: exact byte spans, canonical expression, every compatible
  installed candidate, `selected_sense_ids`, native request/result and checks.
- `semantic_scope_complete`: whole-input bounded semantic recognition/check.
- `selected_sense_ids`: union of the occurrence's selected senses; `[]` if no
  installed whole clause selects a sense.
- `candidate_sense_ids`: sorted union of every occurrence's installed candidate
  sense id; ordering is diagnostic only and supplies no semantic preference.
- `assertion_polarity`: `positive`, `negative`, or `none`; unknown text uses none.
- `source_witnesses`: replayed source identity and the grammar rule used.
- `acquisition`: unchanged result of connected acquisition v3 on the exact
  same bytes and caller binding. `chain_complete` requires that acquisition,
  its native/checking contract and shape licenses as well as semantic completion.

Missing sound acquisition cannot be filled by lexical success. Candidate
retrieval is meaningful on unsupported text and does not create a license.
Changing an occurrence's original span, source id/revision/scope, registry,
source passage, or native response must invalidate the relevant verification.

## Required independent controls

Before runtime implementation, freeze a matrix with positive phrase, perception,
negative perception and drinking substitutions; unmarked and fully marked
forms; mismatched case/definiteness; extra tokens, quotation, negated frames not
in the grammar, unresolved reference, and asad contextual ambiguity. Include
the bare ambiguous `رأيت عيناً` with all three senses and no selection.
Measure semantic reading coverage, complete sound-to-semantic chain coverage,
and false selection separately. Exposed historical natural-use cases remain
exposed diagnostics; a correct refusal of a required positive goal is a miss.
