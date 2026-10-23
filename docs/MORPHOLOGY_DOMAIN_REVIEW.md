# Review of morphology domains and categorical conflicts

This review applies to `nabt.morphology-reader.v2`. It preserves the property
language `nabt.arabic-morphology.v1`, the conditional law `nabt.morphology.v1`,
the generated Lean tables and the frozen evaluation material. The change is a
correction to source-consistency checking in the Python reader. It does not
introduce an additional grammatical classifier or a general Arabic parser.

## Counterexample and correction

The previous reader accepted the following description as `READ`:

```text
قراءة «r1» للفظ «من»:
يدل على معنى غير مستقل.
فعله ماض.
فعله مضارع.
```

It returned a licensed particle kind and built construction. The categorical
helper had correctly detected two incompatible tense assignments, but its
result was inspected for conflicts only inside the verb branch. Selecting the
particle branch therefore concealed the conflicting source statements. The
same problem affected incompatible nun descriptions. A single verbal tense or
positive verbal nun connection also lacked a domain check against a separately
established noun or particle reading.

Version 2 checks categorical consistency before construction branches. Two
distinct values for `tense` or `nun` produce a
`CATEGORICAL_PROPERTY_CONFLICT`, regardless of the proposed word kind. Repeating
the same value retains both source witnesses without creating a contradiction.
When independently supplied kind evidence excludes verbs, an explicit tense
or positive verbal nun connection produces `PROPERTY_DOMAIN_MISMATCH`. Each
record retains the property, competing values or required kind, the exact
support identifiers, and the occurrence and reading identities. Conflict
identifiers are derived from these records; they are integrity addresses and
do not grant linguistic authority.

These checks validate the bounded description language. A description can be
inconsistent within that language even if its spelling occurs in a different
legitimate Arabic reading. Conversely, an invented spelling can carry internally
consistent descriptions without becoming an attested word.

## What is blocked and what remains visible

A contradictory reading receives `CONFLICT`. Candidate calculations remain
visible so that the source of a possible result can still be inspected. The
reader removes positive `LICENSED` approval from that reading's axes and from
its nested diptote cause and genitive predictions. Those objects identify the
source conflicts that block their use. Pending calculations remain pending,
and an out-of-domain axis retains that status; neither becomes an approval.
The diptote and genitive prerequisites explicitly require a consistent source
reading. Genitive realization still requires independent government evidence
and remains unapplied to the occurrence.

The guard is local to a reading. Two descriptions of the same spelling with
different reading identifiers retain separate evidence and occurrence
identities. A contradictory reading can make the document's overall status
`CONFLICT`, but it does not revoke the independently supported axes of another
reading. No tense, nun relation, class or support is copied between them.

Unknown word kind remains unknown: `فعله ماض` by itself does not add a new
positive rule assigning `verb`. The old alternatives remain available until
the existing kind premises are established. Similarly, mere denial of a nun
connection does not assert membership in the verb domain. Thus
`لا تتصل به نون إناث ولا نون توكيد` alone creates no type contradiction for a
noun or particle. Combining that denial with a positive connection still
creates the categorical contradiction described above.

The lexical `event_time` property is excluded from this guard. A noun may
describe temporal or event content while lacking temporal indication by its
form. Nothing in the correction equates the content of a word such as `يوم`
with verbal tense. The stronger `time_in_form` premise remains separate.

## Source contracts and limits

The upstream sources were read at immutable commits, without treating their
successful encoding as acquisition of an unknown property:

| Source | Relevant contract and remaining premise |
|---|---|
| [Alghanem `Qism.lean`](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Qism.lean) | `binaFil`, `murab_iff` and `mabni_iff` concern a verb whose tense and nun connection are supplied. |
| [Mashru `TasnifAlism.lean`](https://github.com/Saleh1967/Mashru/blob/e4c801ffe9171dadedcc3aae23051ea0953ae361/Jisr/TasnifAlism.lean) | `mushtaq_iff` depends on witnessed semantic properties; the file explicitly excludes extracting them from spelling alone. |
| [Mashru `QiraaSimat.lean`](https://github.com/Saleh1967/Mashru/blob/e4c801ffe9171dadedcc3aae23051ea0953ae361/Jisr/QiraaSimat.lean) | `la_dalla_tasturidd` prevents assigning both gender readings of identical `هما` cells by a single-valued cell-only function. |
| [Alghanem `Mamnu.lean`](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Mamnu.lean) | Cause combinations require qualified lexical inputs; a shape match alone supplies neither original description nor the other cause qualifications. |

The fuller audit remains in [MORPHOLOGY_SOURCE_AUDIT.md](MORPHOLOGY_SOURCE_AUDIT.md).
In particular, `SLGE/Simat.slotAttrOK` simplifies imperfect verbs as inflected,
and `Hudud.thabit` checks a finite list under final-haraka changes. Neither is
transported as a universal rule. Semantic genus/quality-bearing classification,
morphological derivation and frozen-verb productivity remain separate axes.

## Verification and version boundary

`tests/test_morphology_domain_review.py` contains post-open counterexample
tests for every kind branch, domain mismatches, consistent repeats, negative
nun descriptions, temporal nouns, separate homographic readings, exact witness
intervals, nested approvals, corrected sources and tampered reports. These are
regression and adversarial tests, not an untouched linguistic holdout. The
existing frozen morphology evaluation cases have not been edited.

Replay recomputes the complete report, including conflict records and their
support. Removing a conflict, changing an approval, changing a support or
presenting a v1 report as a v2 result fails verification. Old reports should
be read again from their original source. The canonical number codec remains
the same representation; its embedded reader version distinguishes the new
report contract. Verification of an honest conflict report attests faithful
replay, not consistency or permission to use its blocked conclusions.
