# Independent text-morphology review protocol

## Freeze and independence

The reviewer authored the 40 cases in `independent_cases_v1.json` after reading
NABT `AGENTS.md`, `docs/WORD_READING.md`, `docs/MORPHOLOGY_SOURCE_AUDIT.md`, the
existing v1 morphology description grammar, and selected pinned primary grammar
passages. The reviewer did **not** open the new `src/nabt/text_morphology.py`
implementation before freezing this material. The parent supplied the planned
scope and API; that planning information is explicitly part of the authoring
context. This is an independent, authored test set. It is not a hidden natural
corpus, an untouched generalization benchmark, or evidence of complete Arabic
understanding.

The frozen JSON expresses properties rather than prescribing report field
names. An evaluator may adapt only the projection from the public report API to
those properties. It may not alter the input text or expected meaning to fit an
implementation. Any source correction must preserve v1 and state the reason,
old bytes, new bytes, and when the correction was made. A known limitation
remains a raw failure unless the declared acceptance property itself is met.

## Expected scope

Terminal well-formed tanwin supports noun kind across unfamiliar stems within
the declared unquoted, non-poetic spelling scope. It does not identify the
inflection subtype or establish that the noun is inflected: `صَهٍ` is the named
counterexample. Two fath-tanwin spellings around an orthographic support alif
are tested independently. Unknown spellings are not classified as particles.

Fully vocalized `لَمْ`, `لَنْ`, and `سَوْفَ` may open a candidate link to an
adjacent imperfect-compatible form on the same line, without crossing a quote
or punctuation boundary. Such a candidate is not a licensed lexical verb, an
actual syntactic role, or an assigned case. A visible nun does not establish its
attachment type. The raw prefix `ال` does not prove article segmentation; the
verb `الْتَقَى` prevents that shortcut.

Optional lexical evidence uses the pre-existing explicit description language.
The lexical symbol remains open. Exact source descriptions may license
construction and the limited universal-nominal genus/property distinction,
qualified diptote causes, and tense/nun premises. Exact matching in this v1 does
not erase vowels. Separate source readings remain alternatives. Source-local
`al` and `idhafa` observations must not migrate to a fresh text occurrence.
Semantic genus is not etymological root analysis; a property-bearing noun is not
a licensed agent role.

## Evaluation and attacks

Every case checks the global source/facts/role boundary as well as its named
properties. Positive capabilities and restraint/boundary cases are reported
separately. A reader that defers everything must fail positive tests. A reader
that labels every target after a marker as a verb must fail candidate/lexical
separation tests. Full raw scores, individual failures, and the code snapshot
are preserved on the first usable evaluator run.

After the fixture freeze, adversarial review tests may inspect implementation.
They should cover changed report fields, source and scope swaps, changed lexical
source bytes, removal or contradiction of a lexical witness, distinct occurrence
IDs, and numeral encoding where exposed. These are post-open adversarial tests,
not members of the frozen pre-open 40-case material. Replay is an independent
check against a submitted report; invoking the production reader twice does not
make it an independent linguistic implementation.
