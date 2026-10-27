# Source-preserving acquisition and reader handoff — v1 specification

Status: specification frozen before the new implementation. This is an authored
engineering interpretation, not a claim to have formalized the Arabic books.
Base: NABT a3ba5b32e67c25b2a71a6c8ebc8635659e6e7f74.

## Goal and authority

Add a separate executable path from exact UTF-8 to source-aligned A116 cells,
then hand the *original bytes* to the existing word reader. Keep the strict
`parse_word`, source-bound shape certificates, and existing readers unchanged.
Acquisition completeness, shape acceptance, lexical reading, syntax, and
inference are different claims. No caller Boolean grants any of them.

The initial acquisition law is `nabt.aligned-acquisition.v1`, using
`nabt.a116.v1`. It licenses representation under the declared rules below,
not an acoustic observation, attestation, word category, grammatical judgment,
reference resolution, or world truth. New lexical rules require a later law.
`wasl` selects local word-ending representation; it does not certify the full
connected pronunciation across words. Boundary assimilation remains a debt.

## Exact source and boundaries

Input: strict UTF-8 str/bytes, source_id, revision, scope, and ending `wasl` or
`waqf`. Default wasl. No normalization, trimming, mark sorting, or loss of text.
Maximum 8192 UTF-8 bytes and 4096 code points. Invalid types/scalars are
INVALID_INPUT; exceeding either bound is RESOURCE_EXHAUSTED, never rejection.
Identity strings are nonempty bounded Unicode without controls (max 512 chars).

Explicit separators: ASCII space/tab/CR/LF and `.،؛,:!?؟()[]{}«»"“”`.
Each separator is retained as a one-character boundary piece, with no cells.
Other characters stay in the word; unknown script/mark is DEFER, not deletion.
Word = maximal nonseparator run. Grapheme piece = a head and all following
marks from `ًٌٍَُِّْٰ` until the next nonmark. A leading mark is INVALID_INPUT.
Piece intervals are half-open Unicode code-point AND UTF-8 byte intervals.
Every raw scalar belongs to exactly one piece. Concatenation restores input.
Each emitted cell cites its complete originating piece. Inserted/expanded cells
have a rule ID and the same source span, not a fictitious raw character.
Waqf applies only to the final word, never silently at every word boundary.
Whitespace/punctuation does not assert a syntactic clause or an uttered fact.

## Rule precedence and initial scope

1. More than one vowel/sukun/tanwin (even duplicates), repeated shadda, repeated
   dagger alif, or a mark-headed piece: INVALID_INPUT. One shadda plus sukun is
   INVALID_INPUT (not two licensed silent consonants).
2. Known conventional omitted-alif skeletons `هذا هذه هذان هذين هؤلاء ذلك لكن
   إله الله الرحمن` without an explicit dagger alif: DEFER with
   ORTHOGRAPHIC_LEXICON_REQUIRED for the whole word. This is a conservative debt
   registry, NOT ten implemented normalization rules. Explicit dagger alif
   does not supply other missing marks. No source claim of "11 completed laws".
   Skeletons `أولو أولي أولئك أولاء` always DEFER with
   SILENT_LETTER_LEXICON_REQUIRED: a written waw is not necessarily pronounced.
   This is an authored conservative boundary, not a source-proved catalogue.
3. Canonical 29 carriers with exactly one explicit ordinary mark map to
   `4*carrier_index+state`. Hamza seats أ إ ؤ ئ map to hamza, retaining the raw
   seat. Shadda prepends the same carrier with sukun. Unmarked consonant is
   DEFER/MISSING_VOCALIZATION, including at pause. No inferred case ending.
4. Bare ا/و/ي is licensed only immediately after a previous piece whose ONE
   short vowel is respectively fatha/damma/kasra, in the same word. It emits
   that long-vowel carrier with sukun. No match across a boundary or unresolved
   piece. The previous piece's LAST emitted cell must have the matching short
   vowel state; a piece already expanded by dagger alif cannot license another
   long vowel. No generic treatment of bare waw/ya as a long vowel.
5. Dagger alif U+0670 requires exactly one fatha on a canonical/hamza-seat head;
   emits the marked head (and shadda if present), followed by alif+sukun.
   No dagger+sukun/damma/kasra/tanwin; these combinations are INVALID_INPUT.
   Dagger without any ordinary mark is DEFER/MISSING_VOCALIZATION.
6. Final ى with no marks, immediately after a licensed fatha piece: alif+sukun,
   whose last emitted cell has fatha, with explicit MAQSURA rule. Other
   positions/forms DEFER.
7. Tanwin on a supported head: in wasl, marked head followed by nun+sukun.
   At final-word waqf, dammatan/kasratan become head+sukun, fathatan becomes
   head+fatha then alif+sukun. Preserve shadda. A following bare final ا after
   fathatan is retained as an explicit silent ALIF_TANWIN piece; it is not a
   second alif in the cells. This is an explicitly bounded representation rule.
   In final-word waqf an ordinary explicitly marked final carrier also becomes
   carrier+sukun (preserving shadda); the raw mark remains in its source piece.
   This implements the declared ordinary sukun pause only, not rawm/ishmam or
   every narrated pause. Final hamza after bare alif with fathatan is DEFER:
   this spelling has no implemented licence in v1. This deferral does not
   establish an exceptional phonetic pause.
8. Final ة requires one explicit vowel or tanwin; wasl uses ta with the stated
   vowel (and tanwin expansion); final-word waqf uses ha+sukun. Other ة DEFER.
9. آ, ٱ, bare initial alif (including the article), article-lam assimilation,
   waw-of-plural silent alif, cross-word assimilation, and every unlisted
   transformation: DEFER with named debt. They MUST NOT be guessed from shape.
   Tatweel is retained as DEFER in v1; unsupported combining marks are retained.

Rule output statuses: LICENSED, BOUNDARY, DEFER, INVALID_INPUT. Empty text or a
text containing no word is DEFER/NO_WORD. Any invalid piece makes acquisition
INVALID_INPUT; else any deferred piece makes it DEFER; else ACQUIRED. Word
cells may concatenate licensed pieces for diagnostics, but incomplete word
cells must never be handed off as a complete word or a shape certificate.

## Executable checking and handoff

Lean independently re-reads the exact input, classifies pieces and returns the
complete canonical acquisition result. Python proposes the same result and
compares the WHOLE result, including intervals, raw pieces, rule/status/cells,
word grouping, mode and identity. A missing native checker is
VERIFICATION_UNAVAILABLE, not success. No test fallback grants native authority.
The executable transport has bounded input/output, duplicate-key rejection,
strict Unicode, exact schema, and bool/int separation. Source restoration and
cell-domain validity must be checked for every report, including deferred ones.

The new `read-acquired` command (file input) includes the existing `read_words`
report on the identical original bytes. It cannot use reconstructed spelling
as lexical evidence. It links complete acquired words by exact byte intervals.
For each complete word, reuse `Machine` and the existing shape certificate
checker; that certificate has source_text=null and is bound to the original
word ONLY through the outer checked acquisition receipt. Resource failure is
not shape rejection. No blanket grammar_certified or end-to-end semantic claim.
`verify-acquired` requires independent source input and expected source identity,
revision, scope, and mode; exact replay rejects source/metadata/cell/rule/span,
reader-output, mode, status and authority tampering even after rehashing.

## Four-family independent matrix

An independent author reads this specification and source passages, not the new
implementation, and freezes input/expectations before implementation is read.
At least 12 cases per family, plus resource/type/source-mutation tests:

* Orthography: explicit vs absent vowels/dagger, long-vowel context, shadda,
  tanwin, ة, ى, wasl/waqf, raw Unicode order and unsupported forms.
* Category/person: حَمَى/حَمِيَ/حَمَا and قُمْتُ/قُمْتَ/قُمْتِ, counterexamples,
   source withdrawal/identity. Cells do not acquire a category or referent.
* Predication: nominal clause, fronted predicate, dual/plural and altered case.
  Distinguish representation acquisition from the required syntactic analysis.
* Condition: supplied/absent/negated premise, changed subject, quotation and
  hidden subject. Record existing licensed-inference results separately; no
  normalization may silently change its source or convert mention into fact.

Each row declares the representation expectation AND the desired downstream
goal. The latter may remain UNMEASURED or a coverage MISS. An expected-positive
goal that is deferred is a miss, not a successful acquisition. Report family
denominators, correct representation outcomes, false licenses, positive
acquisition coverage, downstream successes/misses/unmeasured, and resource
outcomes separately. Never merge these into one "accuracy".
Freeze SHA-256 and base/spec identity; preserve first results before fixes.
Subsequent replay is on exposed material. No natija_5 without recorded runs.

## Formal claims to implement

Typed cells are below 116. A successful local rule witnesses its declared
representation relation. Source-piece concatenation equals raw input; offsets
and handoff must match that partition. A verified complete acquisition has no
pending/invalid piece. Exact replay binds source/mode/identity. Composition with
the existing shape checker grants only its installed sound-shape law.
Soundness of the source interpretation and completeness of Arabic remain
independent obligations; tests and declaration counts cannot discharge them.
