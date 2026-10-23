# Future operator review after the first code freeze

The implementer had not opened the independent construction gold before
`code_freeze_v1.json` was captured. The evaluator later disclosed `CON-K06`
in `independent_k06_disclosure_v1.json`, together with its unchanged input,
gold, relevant training witnesses and observed output.

The v1 reader admitted `سَوْفَ يَكُونُ سَامِرٌ شُجَاعًا.` as an event for
كان with a hal qualification. Its self-question could therefore succeed on
the wrong interpretation. This is an actual positive-interpretation error;
the finite counter of forbidden facts alone must not describe it as correct.
The separately reported scorer errors in the first measurement are not this
runtime error and do not repair it.

## Cause and correction

Operator recognition ran before the old future-prefix production. Seeing
سوف first caused it to skip the source-qualified يكون. The generic event
modifier path could then interpret the remainder as an event plus hal.

The corrected reader recognizes an explicit سوف before selecting an operator,
requires that operator's independently witnessed imperfect reading, and keeps
future tense on the property or scoped claim. The same operator's own raf is
checked separately from its subject/predicate cases. An incompatible perfect
or visible nonindicative ending cannot fall through to the generic event path.
The gate records consumption of the exact future-marker span. The source
premises are the replayed imperfect-indicative passage (Qatr 96–98), the
tense passage, and the existing `deictic_adverbs` passage (Sibawayhi
18510–18520), whose opening explicitly assigns سوف to what has not happened
yet. The future and inflection witnesses remain distinct; no
case label or expected answer is added to acquisition data.

The authored regression uses different content words from the disclosure:
`سوف يكونُ زيدٌ حكيمًا.` and `يكونُ زيدٌ حكيمًا.`. It checks actual kana
roles, the operator's own mood, future versus nonpast answers, and contrary
perfect/subjunctive forms. It does not change the independent gold. A later
measurement of the corrected runtime is explicitly a post-review result on
opened material, with a separate code freeze; v1 remains intact.

This correction covers a separate explicit سوف and a source-qualified
imperfect operator. It is not a general temporal, modal, attached-prefix or
ellipsis parser. No new Lean theorem is claimed for the Python recognition
change; the conditional construction law remains the same.
