# Lifecycle v1 implementation notes and adapter projection erratum

These notes preserve the source/specification freeze `4b181212` and independent
forty-scenario freeze `1295da33` unchanged. They record decisions discovered
before the first acceptance execution. They are not new world evidence.

## Adapter projection erratum 1: absent retained line coordinates

An initial synthetic adapter probe stopped with `KeyError` before issuing an
accepted result. Direct inspection confirmed that exactly three passages in
the already pinned acquisition packet have byte coordinates and quotations but
no line-number fields. The frozen adapter specification's uniform quotation
record did not describe this omission. Its table is supplemented as follows:

| Passage ID | Retained byte interval, end exclusive | Span SHA-256 |
|---|---|---|
| `natural_eye_senses` | 23851–23924 | `0102881b6f3c82377e358f146bb7b654436c3ac22c51ddc8415046ee6cd328d9` |
| `natural_eye_definition` | 2420979–2421086 | `90c818767a50f83bedaff3d596a7879bfb4a6bba99a021dc99c019a8d2052866` |
| `natural_spring_definition` | 2423390–2423473 | `309f01952c8644557ab3ce774a181ec97c244dd6b21ac4e178cf3f25ac74b767` |

For these three named records only, the adapter emits `line_start=null` and
`line_end=null`. For every other passage, the installed line coordinates remain
required and checked. A missing expected coordinate is not silently converted
to null. Exact retained file bytes, full-file hash, byte interval, quotation and
span hash are still checked for all 38 passages. No line numbers are invented,
no retained source packet is edited, and no evidence is promoted in rank.

The acquisition packet remains
`evidence/sourced_acquisition_v3/source_evidence.json`, SHA-256
`64d6d40943ed59a34d16a58de92e11f8672cbdc7ed47ec15f4e341d07594e423`.
This changes the interpretation of three adapter projection fields before its
first accepted implementation. It does not alter the generic lifecycle law,
the forty expected episodes, historical acquisition outcomes, or PCV1 grammar.
Adapter tests must check the exact three null pairs and the failure of a missing
line field elsewhere. The first failed development probe is distinct from the
still-unexecuted frozen acceptance matrix.

## Raw integer cap interpretation

The generic JSON parser applies its 16-digit and absolute-magnitude
`2^53-1` transport budgets before field-specific natural-number validation.
Exceeding either budget yields `RESOURCE_LIMIT`, including an oversized
negative integer. A bounded negative number in a natural field yields
`INVALID_INPUT`; `-0`, floats and exponent notation are noncanonical input.
The existing EM canonical time **string** contract remains unchanged: a time
outside its exact domain is `INVALID_INPUT`. Python and native boundary tests
exercise these distinctions. This resolves an error-class ambiguity; it does
not authorize new semantic input or change the independent matrix.

## Proof boundary

The new parser defines blank text using a shared explicit scalar set:
9–13, 28–32, 133, 160, 5760, 8192–8202, 8232, 8233, 8239, 8287 and 12288.
This closes a preacceptance difference between Python's Unicode whitespace and
Lean's narrower `Char.isWhitespace`. A text consisting only of these scalars is
invalid. Mixed whitespace and nonblank text is preserved exactly; no trimming
or normalization occurs. ASCII controls remain forbidden in identities, while
source content can contain line breaks. Existing historical EM parsers are
unchanged. Independent synthetic tests cover nonbreaking spaces and mixed text.

The added Lean theorems refine the existing EM admissibility relation, constrain
declared ancestry, preserve the original ledger budget, and bind receipts to
their whole episode. The parser and file-replay adapters are executable checks.
Neither the proofs nor a matching file hash establish authorship, undisclosed
source dependence, actual reference, intention or external-world truth.
