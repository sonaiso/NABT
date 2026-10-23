# Independent derivation review v1

The corrected evaluator passed **96/96 frozen authored cases**. The focused post-open integrity suite passed **16/16 tests**, including its frozen-case loop. No production source was modified by this reviewer. The result is a bounded source-informed review, not a natural-corpus accuracy estimate or evidence of Arabic-wide lexical productivity.

## Material and measurement sequence

The input texts, generation operands, expected inclusions/exclusions and protocol were frozen before the reviewer opened the new derivation implementation. The case-file SHA-256 remains `e2374049ac135a290b4298e4ce0a4eef872a30a5e63fcdbc2c8a638e10059650`. Expectations are lower bounds where genuine additional pattern candidates are possible.

1. Static review found that the first implementation omitted written shape observations inside quotations. Frozen case DER-B25 already required the quoted shape. The owner corrected the implementation to preserve inner original-source byte spans with explicit `MENTION` context, while excluding mentions from future-attachment proposals. This occurred before any runtime measurement; `pre_first_run_review_v1.json` records it. Neither the case nor its expectation changed.
2. The first runtime measurement was saved in `independent_first_run_v1.json`, together with its exact code archive. Its raw 6/96 score is **not a morphology accuracy result**: the evaluator constructed uppercase/hyphenated transport source identifiers, contrary to the existing identifier grammar. Ninety cases therefore rejected before parsing. Two permissive invalid-input cases also counted raw passes under this adapter failure. The separate generation operations passed 48/48.
3. Only the evaluator source-identifier adapter was corrected to stable lowercase identifiers containing underscores. `adapter_erratum_v1.json` records the old/new evaluator hashes and preserved first-run hash. No runtime identifier language, input text, profile, generation operand or frozen expectation was changed.
4. The separately saved `independent_second_run_v1.json` is the **post-adapter-correction** measurement: 96/96. Its sibling archive contains the measured code. The evaluator confirms that its code snapshot did not change while evaluation ran.

## Separate denominators

| Task | Passed / total | Meaning |
|---|---:|---|
| Exact generation operations | 48 / 48 | 44 exact positive construction surfaces plus 4 invalid operand/boundary cases; supplied roots are operands |
| Parsing cases | 74 / 74 | Raw-text reader cases and the reader half of paired roundtrips; generation checks excluded |
| Conditional paradigm availability | 16 / 16 | Exact controlled-source assertions and explicit unknown/negative/conflict boundaries |
| Dedicated changed-source replay | 2 / 2 | Changed source invalidates an old report even when a category/shape is unchanged |
| Semantic restraint on returned shape reports | 74 / 74 | Includes the dedicated shape replay report; the malformed rejected input has no returned report and is excluded |

The nine disjoint case groups are: 44 source-template positives, 19 adversarial boundaries, 2 ambiguity positives, 2 synthetic positives, 2 context boundaries, 5 named category boundaries, 4 generation boundaries, 16 controlled-paradigm cases and 2 source-replay cases. These sum to 96. Task denominators overlap intentionally and must not be summed.

## What was checked independently

The review adapter checks source digests and exact UTF-8 byte spans, the complete outer source partition, all unquoted written occurrences, containment and identity of quoted mentions, ordered non-overlapping occurrence spans, whole-stem reconstruction, explicit boundary retention, per-position literal/radical witnesses, repeated radical agreement, and isolation between occurrences and source blocks. It checks that shape reports confer no lexical attestation, word class, nominal jamid/mushtaq semantics, universal productivity, actual role, actual case or world fact.

The paradigm checker derives positive/negative masks from exact source sentences and enumerates the seven nonempty models of three form-availability bits independently. A missing sentence is unknown, conflicting assertions conflict, unsupported qualifications prevent activation, and two separately named lexical blocks cannot share assertions. This validates the conditional finite law and its source binding; it does not independently establish that the source's lexical claims are true.

The post-open integrity tests additionally attack source/scope/profile replay, repeated identical occurrence spans, literal alignment tampering, mask fabrication, cross-block evidence transfer, semantic-authority fabrication, public-number replay, boolean/non-natural mask inputs, answer operands injected into raw reading, quote-context forgery, and temporal proposals crossing quotes, punctuation or newlines. Blanket deferral and accepting forbidden candidates are shown to fail the measurement.

## Limits and remaining coverage

The frozen positive set was designed for 44 patterns. The installed runtime table later expanded to 71 patterns; this review does not reclassify the five semantic-boundary fixtures as positive coverage for all newly added nominal patterns. Parent-owned formal conformance provides a separate form of evidence for the installed table. Generic repeated-slot and four-independent-slot obligations are described in the frozen coverage matrix; the reviewer did not invent a custom-pattern public API to claim that those obligations were exercised through it.

Exact structural matching yields formal root/pattern candidates, including the VII/ VIII collision in `انْتَبَر`. It does not prove an attested lexical root, intended sense, instrument/place meaning, sifa mushabbaha, masdar identity, comparative use, or actual verbal productivity. The written imperfect profile is the declared new sound projection, not a proof of weak-root transformations or identity with every raw source cell representation. Future sawfa remains contextual evidence rather than a morphological future weight.

The scoped remaining-repository audit is in `source_audit_other.json` and `source_audit_other.md`: seven immutable repository trees, with current heads verified where access was available. Their only tracked Lean file is a generic recovery-metric development; their useful morphology tables and heuristics are explicitly identified as non-Lean candidates. Qeyas/alasmaa remote head checks were unavailable, not evidence that those repositories do not exist. No external source engine or source Lean build was executed by this reviewer.

## Reproduction and identities

Focused command executed successfully:

```sh
PYTHONPATH=src python -m unittest discover -s tests -p test_derivation_review.py -v
```

Fresh measurements require a new output path, for example:

```sh
python tools/derivation_evaluation.py --output artifacts/local/derivation/review.json --capture-code
```

The evaluator refuses to overwrite an existing measured result or archive. Historical results and frozen material must be retained.

| Artifact | SHA-256 |
|---|---|
| First raw result | `abe0db8e133e2819e8289f90c549c69cd33ce10fb23f7cc9c2475df44840c853` |
| First code archive | `049043b0e931b4b1f7b0263c398777f7eb6442a21b9df8b089153c774182a9f4` |
| Adapter erratum | `092e6e7d43df7374bccfc98b114f48e39c4968afc4ff31713e46ef31782f7d7a` |
| Second result | `de7436c489d39a5da879db2146855307a699ba19a1eef398a46d1eb6d7e74821` |
| Second code archive | `400820c6a7e2063617dbc733c49390ca5215de030e18453102abd69f85e4cb20` |
| Second code snapshot inventory | `1a8ce37009f3ce1f27c24425fe87b9ce22c85058c96bf8007e6f6dbd80efe519` |
| Installed derivation table | `0b4d6673c033955490468ad595fc1e988890bba282101e81a80580d3fc1fbf2f` |
