# Current-model explainable pilot

This additive pilot runs the existing deterministic ground-reading proposer
through the native Lean verifier, then emits a versioned answer and source-linked
analysis certificate. It does not train a neural model or expand the accepted law.

- [Contract and conditional 12-week protocol](../../docs/EXPLAINABLE_PILOT.md).
- [Executable development cases](cases.json): 14 status cases, 4 source ablations.
- [Measured current baseline](baseline.json): case denominators, 14 named attacks,
  code/data hashes, native replay and local timing samples.
- [Latest boundary follow-up](JSON_BOUNDARY_REVIEW.json) and
  [remeasured baseline](baseline-after-json-boundary.json): finite JSON, Unicode
  and programmatic replay budgets; 14 native contract tests without skips.
- [Example answer with embedded analysis certificate](example-answer.json).
- [Measurable goals and model-scaling rule](goals.json).
- [Validation record](VALIDATION.json): exact base, builds, tests, separate free
  Arabic regression results, and the archive manifest.

The development result is 14/14 matching statuses, 14/14 native replays and byte
roundtrips, 14/14 rejected attacks and 4/4 source ablations. Decisive answers are
9/14; all 9 match the authored expectations. The five other cases intentionally
exercise UNKNOWN, CONFLICT or DEFER. Neither that precision nor that coverage
estimates accuracy on general Arabic. No new hidden test or human review occurred.

On the current integrated runtime, a fresh run of the existing directed Arabic
suite retains 14/22 fixed cases and 19/29 question statuses, with strict coverage
still failing. Two conditional provenance cases are separate (one correct
abstention, one unresolved review); six separate source-premise controls pass
6/6 and do not inflate the 22-case denominator. The legacy 36-case suite scores
35/36 in its original scorer and 36/36 after the repository's existing H18
erratum review and 103 certificate replays. These are reproduced baselines,
not gains from the new answer wrapper or a new blind experiment.

Reproduce with `make explainable-pilot` on a normal pinned Lean installation.
The example records the particular local native executable fingerprint. Reissue
it using the documented `answer` command when using another compiled executable;
v1 replay deliberately requires the recorded executable fingerprint as well as
checking the proof again. The original source/query are the existing repository
example files, not text extracted from the untrusted answer.

The archive retains run evidence, including raw free-reader records. Large
duplicated runtime code archives produced by the historical evaluators are
excluded: their source is pinned by the validation base and input inventories.
Re-run the supplied commands from that base plus this change for fresh artifacts.
Historical frozen corpora remain development/regression material for this pilot,
even when their original filenames contain `holdout` or `independent`.

The recorded timings include subprocess startup and executable hashing under
concurrent local validation load. Small timing differences are not a measured
speedup. Training gain, LLM cost and internal model causality remain unmeasured.
