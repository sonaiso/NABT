# Person and nominal v3 implementation boundary

The frozen language contract remains
`SOURCED_ACQUISITION_V3_PERSON_NOMINAL.md`. This implementation note does not
change its finite surface table, grammar, or independent evaluation population.

`tools/acquired_person_nominal_v3.evaluate` accepts exact source bytes or text
and independently bound task/source/revision/scope/ending/onset. It invokes
`connected_acquisition_v3.read_acquired` freshly and separately runs
`acquiredSyntaxV3` on the original source. The Python syntax proposal and native
result must match as complete typed JSON, including original pieces, token
spans, lexical readings, diagnostics and binding fields.

The public `syntax` receipt is an object with `verified`, `status` and
`native_result`. A verified native result can contain a finite syntax reading
while the composite remains incomplete. In that situation the top-level
`person` and `nominal` remain null. The composite admits a projection only when
source acquisition, native acquisition replay, requested shape verification,
native syntax replay, finite grammar reading and original-source binding all
pass. Missing native/source authority and resource exhaustion remain explicit
failures. `SHAPE_REJECTED` does not assert Arabic ungrammaticality.

Every projection retains exact word and suffix spans in Unicode scalar and
UTF-8 byte coordinates. Pause changes acquired pronunciation but does not
erase the original tāʾ vowel. The first-person projection has no gender value.
The WALAD nominal projection retains individual/collective lexical alternatives
and has null denotation cardinality. All projections have null referents, and
the report explicitly leaves world truth, reference and all-Arabic completion
unestablished.

The native module `Nabt.AcquiredSyntaxV3` defines `Lexical` separately from
`readLexeme`, recursive `LexicalWords` separately from `readWords`, and
`SourceGrammar` separately from `parse`. The grammar combines whole-source
boundary checks, exact raw tokenization, task, and the finite lexical frame.
It is not defined as the parser's success flag. Its main claims are:

| Declaration | Exact scope |
|---|---|
| `lexical_read_exact`, `words_read_exact` | Search succeeds exactly for the declared literal lexical relation, individually and across all source words. |
| `frame_read_exact` | Canonical lexical lists match exactly the declared task/frame pair. |
| `parser_exact`, `parser_sound` | Original-source parser success is equivalent to, and implies, the explicitly declared finite `SourceGrammar`. |
| `source_restoration`, `source_offsets_contiguous` | Original source pieces restore the complete text and retain contiguous scalar/byte coordinates. |
| `person_mapping`, `person_surface_roundtrip` | The three declared tāʾ forms have the stated grammatical person/gender mapping, and both exact aliases parse. |
| `unmarked_no_person` | None of the three declared undecided bare forms is admitted as a unique person. |
| `nominal_both_orders`, `nominal_source_roundtrip` | The finite three-number frame admits both declared orders, including actual short source forms. |
| `nominal_number_mismatch`, `nominal_mismatch_rejected` | The declared ordinary predication relation requires matching number, and canonical mismatched pairs cannot parse as a frame. |
| `verified_binding` | Equality replay binds the complete typed request, including raw source, task, identity, ending and onset. |

`frame_roundtrip` is an internal proof helper. None of these declarations proves
that the authored reading conventions exhaust the cited sources or Arabic.
The JSON transport, compiler/OS boundary, source interpretation, and general
Python-to-Lean refinement are not promoted to formal theorems. Whole-receipt
replay and development counterexamples test those executable boundaries.

`tests/test_acquired_person_nominal_v3.py` is a development suite, separate from
the frozen independent matrix. It covers literal aliases, both nominal orders,
number mismatches, nonpredicative adjacency, unknown/missing/wrong marks,
punctuation and quotation boundaries, undecided hypotheses, raw spans, native
input rejection, source/native failures, exact metadata replay, typed receipt
mutations and incomplete connected realization. Independent evaluation and
later repairs remain separately retained by the v3 coordinator.
