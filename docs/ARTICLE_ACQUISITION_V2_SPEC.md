# Finite article acquisition and original-source inference — v2

Status: contract to freeze before independent cases and implementation.
Base: `ddf92947dd84172f7200ce3b3041287b9031e150` (PR 54 and subsequent empty-plan PR 55 merged).
Law: `nabt.aligned-acquisition.v2`; alphabet `nabt.a116.v1`.
Composite law: `nabt.acquired-inference.v2`. This is an additive, bounded
interpretation, not a general Arabic article recognizer or connected pronunciation.
V1 source, law, native CLI, receipts and frozen matrix remain unchanged.

## Independent onset and ending

The request retains exact `text`, `source_id`, `revision`, `scope`, and `ending`
from v1, and requires `onset`: `word_initial` or `connected`. Python entry
points may default to `word_initial`; every native request and returned receipt
contains it explicitly. Ending `wasl`/`waqf` still governs the local ending,
with waqf only at the final word. It never licenses an onset policy.

`word_initial` represents each word as separately begun/cited, including words
inside a multiword source. It is not a transcription of uninterrupted speech.
`connected` is recognized but unsupported: every nonboundary, nonmalformed
piece is DEFER/CONNECTED_ONSET_NOT_IMPLEMENTED. No composite authority is
possible in this mode. Unknown onset values are INVALID_INPUT. Source, Unicode,
budgets, separators, partition, exact reconstruction and offset rules remain v1.

## Finite reading witness, not a guessed prefix

The shape ا + لْ does not establish article identity: الْعَبْ may be an imperative
with initial kasra. License only the following installed finite readings,
interpreted in `evidence/article_acquisition_v2/source_evidence.json`:

| Reading ID | Required stem pieces, excluding the article |
|---|---|
| ARTICLE_HAQQ | حَ ; ق with exactly one shadda and one explicit case vowel |
| ARTICLE_QAWM | قَ ; وْ ; م with one explicit case vowel |
| ARTICLE_GHULAM | غُ ; لَ ; bare ا ; م with one explicit case vowel |

The explicit case vowel is one of fatha/damma/kasra, never sukun or tanwin.
Both orders of shadda and the vowel are accepted; raw order is preserved.
No other stem marks, extra pieces, missing vowels, inferred case or suffix are
licensed by this registry. The complete word must be exactly:

1. Initial ا or ٱ with no marks or exactly fatha.
2. ل with exactly sukun.
3. One complete stem from the table.

Acceptance of U+0671, raw mark order, the finite vocalized signatures and A116
mapping are authored engineering/reading conventions, not spellings quoted from
unvocalized source extracts. The books support article identity/examples and
initial fatha; supplied stem vowels are required input, not filled by a lexicon.
Final vowel variants describe representations, not acquired syntactic case roles.
No noun category, definiteness judgment, or world fact follows from these cells.

## Decisions and precedence

First partition the original source exactly as v1. In `word_initial` mode:

1. Preserve boundary and malformed-piece precedence from v1, including duplicate
   vowels/shadda, shadda+sukun and dagger conflicts. Malformed stays INVALID_INPUT.
2. Preserve v1 whole-word omitted/silent-letter debts.
3. A finite reading match licenses only its onset piece as hamza+fatha, cell
   `[112]`, with rule `<READING_ID>_INITIAL`. Keep that piece's original raw
   scalar/marks and exact span; the rule depends on the entire checked word.
   All remaining pieces use the unchanged v1 classifier and final-word pause.
4. For an article-shaped word (initial head ا/ٱ followed by head ل) outside the
   finite table, every nonmalformed piece is DEFER/ARTICLE_READING_NOT_LICENSED,
   unless the earlier whole-word debt applies. This is a scope boundary, not a
   declaration that the word is linguistically invalid. Sun letters, clitic
   prefixes, generic hamzat-wasl verbs/nouns and all other expansions are debts.
5. Other words use v1 decisions. Never replace original text with an expanded
   spelling before any reader or inference call.

For `connected`, malformed and boundary decisions remain first; every other
piece is deferred by the mode rule, with no emitted cells. Empty/no-word text
remains DEFER/NO_WORD. V2 acquisition JSON retains the v1 structural fields,
uses the v2 law ID and adds `onset`; word/piece schemas otherwise stay unchanged.
The first-piece rule identifies the finite reading; no caller-supplied witness
or Boolean can select an article reading.

## Checking, shape and composition

Python proposes; the new native `alignedAcquisitionV2` independently reproduces
the entire result from original input. Exact JSON/type/duplicate-key and resource
controls remain. Missing native replay fails closed. Shape handoff uses the
unchanged q0-based installed machine; citation hamza supplies a licensed onset.
Do not delete an onset and bypass the resulting silent-start shape rejection.

The v2 reader/composite receipts have distinct schemas/law IDs and bind onset
independently of ending. Source inventory is content-pinned. Source and query
share an explicit onset, original metadata/scope/time, and exact original bytes.
Complete acquisition and shape licenses on both sides, independently checked
PR 34 readings/closures, and matching identity are required. PR 34 vocabulary
and semantics are unchanged: new acquired spellings do not automatically enter
its language. UNKNOWN/CONFLICT are measured results within that law; unavailable
reading remains DEFER, not a successful negative inference. Verification compares
the complete receipt against independent source/query and every binding.

## Formal obligations

Prove exact span preservation, restoration and contiguous offsets; verified
request/onset binding; no pending piece on acquired results; finite-witness
necessity for every article onset license; emitted onset exactly hamza+fatha;
no complete nonempty handoff in connected mode; complete shape handoff under
the existing law. State these as implementation-relative theorems, not proofs
of source interpretation or general Python/Lean composition. Preserve standard
kernel checking and existing axiom policy. Register meaningful public theorems
and explicit new-law source links. Move all five current compiled/link snapshots
together after formal changes, preserving every historical snapshot.

## Independent matrix and first execution

An independent author reads this contract, source registry, alphabet and existing
v1/PR34 specification, not new implementation. Freeze at least twelve cases in
each of the four families: orthography, person/category, nominal predication,
and conditional inference. Include all finite entries and onset/ending contrasts,
ambiguous imperatives, missing/wrong/duplicate marks, source/identity mutations,
unlisted/sun forms, punctuation, premise absence/negation/subject change,
quotation and unresolved subject. Author expected cell arrays independently.

Matrix schema `nabt.article-acquisition-gold.v1`: `cases` contains unique `id`,
`family`, exact `text`, `ending`, `onset`, and `expected` with `acquisition_status`
and optional `word_cells`. Each `goal` has `kind` (acquisition, person,
nominal_syntax, conditional_inference), `positive` Boolean; conditional goals
also have `query`, `query_ending` (wasl/waqf), `expected_status`, and
`expected_chain_complete`. The row ending applies to the source; query_ending
is independently explicit, and onset is shared. Person and
nominal goals remain UNMEASURED; required positives remain coverage misses.
Top-level authorship/method/source metadata may accompany schema/cases and is
not an executable rule. Type/resource/source-identity/receipt mutation checks
are separate boundary tests; they do not inflate the linguistic case denominator.
For conditional cases the evaluator invokes the full v2 composite and independently
checks exact status and chain expectation, rather than reporting nested inference
success as a joined answer. Acquisition positives count verified complete sources;
conditional positives require a verified complete chain supporting the query.

Commit contract/registry, then independent gold, before new implementation. Do not
read gold contents during implementation. Freeze committed code and all native
binaries before first execution. Retain the first result even if it fails;
subsequent repair runs are exposed. No relabeling cases to pass. Source inventory,
initial snapshot binding, fresh source-only imports, native replay, independent
alignment checks and exclusive outputs remain required. Record preflight failures
as attempts too. Preserve old v1 replay counts separately and do not combine them
with new coverage. No aggregate Arabic accuracy or fabricated certification flag.
