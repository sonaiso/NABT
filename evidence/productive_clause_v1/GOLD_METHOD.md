# Independent authored matrix: productive clause v1

## Chronology and authority

The source packet, specification and acceptance protocol were frozen locally in
`34acd468c2568b3236818d1f72b92b9651a6f070`, descended from main
`b7442580e7e681a68a85f40bc247be8ee286e7e3`. This matrix was authored afterwards,
before new accepted-language implementation. Its commit is to be recorded by
the root after independent review. These are local freeze commits; no remote
publication is claimed here.

This matrix is exposed to implementers. It is neither a blind set nor a set of
held-out lexical items. The linguistic frames are synthetic combinations of the
explicitly installed lexical classes. Source quotation, interpretation of a
passage, installation of a fully vocalized reading, and external truth are
distinct obligations.

Pinned inputs:

- `source_scope.json` SHA-256:
  `eb3a1d93730c4a402bce2561afb8934d1f76853ca31fe8ad1167c33ed08d4f17`.
- `acceptance_protocol.json` SHA-256:
  `8adfb5b35af609e152c1c19879fa328ae97e365838e72994ee22500e7db27c25`.
- Original `cases.json` SHA-256:
  `5a6de98a71551c3a1dc0870c15de52b10f50e5233c145c033664c7c500b008f1`.

## How expectations were produced

No `nabt` or proposed production module was imported, invoked or used to produce
expected classifications, cells, roles or spans. Only standard-library text,
JSON and hashing operations were used to emit the literal JSON matrix.

The independent role oracle is the two-row grammar in the frozen specification:
DARABA/NOM/ACC maps indices 0/1/2 to verb/agent/patient, and DARABA/ACC/NOM maps
them to verb/patient/agent. Two installed nominatives or two installed
accusatives fail that particular complete three-role frame. A form or feature
not installed in the frozen contract defers, irrespective of its possible
validity in Arabic. The expectation does not call the runtime's parser or its
case classifier.

Eleven exact lexical-form cell arrays were independently tabulated against the
explicit A116 carrier order and mark order, then reviewed separately from the
implementation. The matrix copies those literal source-scope arrays; it does
not derive them using the acquisition implementation. In particular, ayin with
fatha is 68, and the support alif following accusative tanwin contributes no
extra pronounced cell under this contract. The existing acquisition law must
independently reconstruct and check each array before a joined chain earns
credit.

Word spans are computed from the authored word strings, advancing their Unicode
codepoint lengths and UTF-8 byte lengths plus the single ASCII separator. They
are literal expectations in the committed matrix. The optional final full stop
is not part of the final word. Both coordinate systems are zero-based and
half-open. Every case has its own source ID and scope, including the two
surface variants of the same frame.

## Denominators and combinatorics

The nominative inventory is ZAYD, BAKR, KHALID, SAID, QAYS. The accusative
inventory is ZAYD, BAKR, KHALID, SAID, AMR. Case support is deliberately partial:
QAYS accusative and AMR nominative are not installed. Their outside cases must
not be moved to the negative-in-scope slice after observing the implementation.

The 50 positive frames are the Cartesian product of five nominatives, five
accusatives and two orders. Each frame is rendered without punctuation and with
one final ASCII full stop, yielding 100 source cases. Frame identity includes
subject lexeme, object lexeme and order, but excludes punctuation. Both surface
variants must succeed for a frame to succeed. This is finite compositional
coverage of 50 frames, not 100 distinct grammatical constructions.

The matrix includes repeated lexical names intentionally. Their role IDs bind
different word occurrences. No assertion is made that they denote the same
person, or that they denote different people. World reference and actual event
truth remain unavailable; bare affirmation must not produce exclusivity.

The 50 negative cases are 25 ordered NOM/NOM pairs and 25 ordered ACC/ACC pairs.
Every token is an installed lexical form. `REJECTED_IN_SCOPE` means no licensed
three-role frame under this law, not that the surface cannot be interpreted by
ellipsis, apposition or another Arabic construction outside the law.

The 50 outside cases have five separate ten-case families:

1. Unsupported verbs, voices or verbal forms.
2. Unsupported name/case forms, including nominative Amr, accusative Qays,
   genitive, dual, diptote, feminine or unregistered names.
3. Unsupported structures or operators, including SVO/OVS, omission, extra
   words, conjunction, negation, restriction, interrogation and a preposition.
4. Unsupported marks or boundaries, including absent vocalization, quotations,
   internal punctuation, newline, repeated full stop and nonbreaking space.
5. Supported lexical text under five `waqf` requests and five `connected`
   requests. Those modes are outside this first clause contract.

Outside cell and word-span gold fields are deliberately `null`. They are
unmeasured acquisition axes, not successful null comparisons. The expected
syntax defer and absence of roles/reading remain mandatory. Invalid API values,
invalid JSON/UTF-8, identity tampering and resource exhaustion belong to separate
technical tests; they do not inflate the 200-case linguistic denominator.

## Success and reporting

Keep independent syntax-contract results separate from source-bound complete
chains. A native syntax match alone cannot grant acquisition or complete-chain
credit. Positive-chain success requires the exact independently specified
cells, spans, roles and reading, source-scope validation, acquisition and shape
licenses, native replay, and identical request binding.

The acceptance protocol defines 95/100 positive surfaces, 48/50 complete frame
pairs, zero observed false authorizations on each negative slice, and full
negative/outside bounded-contract agreement. Report every denominator, expected
positive abstention, native unavailability, source error and unmeasured axis.
Do not collapse these into one machine-intelligence score.

The first real evaluation attempt, including any failing preflight, must be
retained. An independent review is required before the matrix freeze. If an
oracle error is found after execution, retain the original file and first
outputs, publish a separately reviewed erratum, and show original and corrected
projections. Finite zero-error observations do not prove Arabic completeness.
