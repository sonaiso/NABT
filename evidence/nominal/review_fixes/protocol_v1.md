# PR9 counting fixes: independent regression protocol

This is a new, post-review regression set for Copilot comments `4359983718` and `4359983758`, read from `artifacts/local/nominal-development/pr-review-comments-5.json`. It is separate from the pre-implementation 184-case nominal fixture. No historical fixture, result, code archive or release record is replaced.

The 99 fixed cases are in `cases_v1.json`, SHA-256 `dc67e40341781aa8cd14466b2a606cab6f99d15c6b2ea622cc5115d87588d05b`. They are exercised by two test methods in `tests/test_counting_review_fixes.py` and by that file's optional recording entry point.

## Canonicality and bounded cardinal domain

The 26 canonicality cases distinguish a malformed decimal spelling from a well-formed operand outside the bounded grammatical rule. Both ASCII and Arabic-Indic alphabets are covered.

- Leading-zero strings of lengths two, three, four, five and twenty must raise `NONCANONICAL_CARDINAL_LITERAL` with status `REJECT`. All-zero strings are included.
- Canonical five- and twenty-digit strings remain explicitly deferred outside the bounded rule. The length limit must still precede integer conversion.
- A single zero is a canonical numeric spelling outside this cardinal grammar, not zero padding.
- Three and one thousand remain supported values, with no observed numeral gender supplied by digits.

## Internal and external spacing

The 73 spacing cases use explicit code-point lists in the authored fixture; they do not call the implementation's separator predicate.

Internal LF, CR, vertical tab, form feed, NEXT LINE, LINE SEPARATOR, PARAGRAPH SEPARATOR, FILE SEPARATOR, GROUP SEPARATOR, RECORD SEPARATOR and UNIT SEPARATOR must block the relation. Each is tested between digit and noun, between number word and noun, inside a mixed gap with spaces/tab, and inside a compound numeral.

TAB and all seventeen currently specified Unicode `Zs` characters are positive internal-gap controls. The eleven forbidden internal separators are also tested as leading and trailing material around an otherwise complete phrase. External spacing does not attach two separated internal clauses.

Every returned report must retain the exact source text, partition and digest, replay against that source, and keep actual case, role and world cardinality unestablished.

## Before/after records

The before run imports the tracked runtime from commit `a9efdd7e5a5f9b57aeabce9d3d57fd4bf8a316c2`, extracted into a temporary directory from an archived Git export. It runs the same new test file and the same pinned cases used for the after run. This avoids a race with the parent's concurrent runtime fix.

Both results record all per-case outcomes, the imported runtime file hashes, the test-file digest, the fixture digest and whether runtime bytes stayed fixed during the run. An unsuccessful before result is retained. The after run uses the corrected working-tree runtime. These observations supplement the later 52-file release freeze and repository gates; they do not replace them or change the historical 184-case denominator.
