# Predicate construction boundary and the lexical status of أمس

Review date: **2026-10-23**. This is a source review and an authored regression
after the implementation author's general construction guard. It is separate
from both the immutable 26-case post-review matrix and the independent evaluator.
No independent case file was read or changed for this note.

## Implemented boundary

An annotation `POS:N` establishes a source-relative lexical noun candidate. It
does not by itself establish whether that candidate is built or inflected, its
case realization, its relation to a new subject, or a property asserted about
that subject. The general guard now requires construction evidence before a
candidate activates the `nominal_predicate`, `inna_predicate`, or `kana_predicate`
role. Missing evidence is an obligation and produces deferral, not a fabricated
construction or a semantic rejection of the lexical item.

`tests/test_discourse_predicate_boundary.py` uses eight explicitly authored TSV
records, with no case or mood labels. The single observations for أمس and باحث
leave their construction unresolved. Their six combinations with the three
predicate frames must retain the lexical candidate, expose the construction
obligation, and produce no activated predicate or asserted claim. Paired
inflection witnesses for the noun معلّم and adjective كريم provide positive
controls, including an إنّ frame. These are instructional premises, not QAC
quotations, a natural corpus, or new blind evaluation material.

## Independent primary-source evidence for أمس

The source files below are the already pinned Alghanem corpus projections. This
review does not change their bytes or the discourse grammar policy.

| Source window | What it supports | What it does not establish |
| --- | --- | --- |
| `sibawayhi.txt` 349–351, within recorded window 336–353 | أمس and غد are names of time; their use need not always be adverbial. | A universal `POS:T` annotation or an actual attachment in every new occurrence. |
| `sibawayhi.txt` 2150–2155, within recorded window 2147–2155 | In the chapter on names occurring as adverbs, أمس and أول من أمس can answer متى with a temporal interpretation. | A date, clock anchor, or automatic property predicate for an arbitrary entity. |
| `qatr.txt` 49–51 | The Hijazi reading of أمس is built on kasra. | That every reading of the spelling أمس has the same construction in all dialects and contexts. |
| `qatr.txt` 158–161 | The discussion of predicate adverbs explicitly limits temporal predication of an entity. | A complete ontology distinguishing every entity, event, metonymic use, or omitted predicate. |
| `sibawayhi.txt` 11453–11460 | The text distinguishes the temporal reading from using أمس as a person's name, where its declension changes. | Permission to blacklist the spelling regardless of the supported reading. |

In particular, a noun annotation does not refute temporal meaning: the lexical
category and the role in a particular sentence are different axes. Conversely,
discovering a temporal lexical candidate does not prove its attachment or license
a calendar interpretation.

## Immutable source coordinates

All byte ranges below are zero-based half-open ranges, preserving the original
UTF-8 bytes including line endings.

| File | File SHA256 |
| --- | --- |
| `src/nabt/data/source_evidence/qatr.txt` | `2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d` |
| `src/nabt/data/source_evidence/sibawayhi.txt` | `a160f940bb194e6fe7e6655d2c7f28e41f1fc648c4c5e340cc4e42306d5cb625` |

| File and inclusive lines | Byte range | Window SHA256 |
| --- | --- | --- |
| `qatr.txt` 49–51 | 1796–2171 | `0a26c9f7f3c026b27891c0182e6d0c29f8b4edbd489d094e1f83bd53b2d32537` |
| `qatr.txt` 158–161 | 12383–12871 | `4b35440cecfa5a5ea0f7d090ed966ebe5dc7743ea5dc4a060e798c52b8a31364` |
| `sibawayhi.txt` 336–353 | 37120–39447 | `701003132e0a7d1e55ac75128175a888ce4975c3fbd0c6a92abad493091ad434` |
| `sibawayhi.txt` 2147–2155 | 249636–250547 | `6fbfc61f2794ed4eec7e52e17692b8e5517a7f04ae58f4a64f15801734f93a15` |
| `sibawayhi.txt` 11453–11460 | 1350566–1351582 | `b05c8398638a1c91cdfeffc06745141730c5227c39d5350013d2df4426e64ff8` |

## Remaining work

The construction guard addresses the missing-evidence bypass. It is not a proof
that a future candidate with known construction is a valid semantic property.
A later bounded grammatical inventory can expose a source-backed temporal
reading of أمس, preserve its dialect and definiteness conditions, and retain
other independently supported readings. That work still needs a separate
attachment/subject-type contract. No such lexical inventory, blanket spelling
exception, new `T` annotation, or calendar inference is implemented by this review.
