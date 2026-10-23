# Frozen protocol and execution chronology

This document assembles the recorded protocol and chronology after the runs.
The frozen input/gold bytes and the original result files are unchanged.

## Corpus and scoring

The separate evaluation author read the prior public roadmap, earlier NABT
evaluation reports, and packaged book files. The author did **not** inspect the
new reader or semantic-kernel implementation before the frozen first and reserve
runs. Builders supplied the public syntax, API, and inference/conflict contract.
They did not receive the heldout texts or gold labels before both runs ended.

The authored corpus has sixty episodes, ten in each of six families, with 126
query checkpoints. Each checkpoint's expected logical status is manually
specified. It is not computed with the production reader or kernel. The initial
forty episodes and twenty-episode reserve were partitioned before execution.
The corpus metadata fixes the complete grammar, signed/clean closure policy,
5-second episode budget, and 180-second whole-run budget.

An episode succeeds only if all its admissions, updates, and query checkpoints
succeed. The checker compares the expected status, exact signed ground question,
conditional-world-truth marker, and named residuals where specified. It also
independently replays every returned proof's source/slice hashes, scope, active
source identity, fact steps, grounded rule head/body, premise indices, and
conclusion. It does not call the production certificate verifier for those
checks. This finite checker does not authenticate a source's factual truth or
prove arbitrary Arabic interpretation.

The two explicitly scored missing-premise questions each omit one immediate
literal from a conjunction. They do not constitute a large missing-information
benchmark. More demanding completion-validity checks were added separately
after a root reviewer found a counterexample.

## Immutable input identifiers

| File | SHA-256 |
| --- | --- |
| `controlled_text_benchmark.json` | `1edb63bd0df4e6c35e466b989a9bc4e55d5204d66a4771f6b72f073895419127` |
| `real_source_candidates.json` | `77cf9e1cb3fad8771b822a16db8bb54a15e5ddf03970740dfd7f59f010111b5d` |
| `natural_probe_protocol.json` | `3b8f008114e62ac6d64288af7d402c3cd78aa4668948913784a14ca96979b844` |

## Chronology

1. At **2026-10-22 22:40:22 UTC**, the sixty-episode corpus and fixed 40/20 split
   were announced with their checksum. The raw-book span manifest was selected
   independently and kept private. Its natural-source protocol was separately
   frozen before code execution.
2. At **22:45:47 UTC**, the first runtime snapshot was hashed as
   `454adcd3df89b8f2dd127778aa5122b7e74bff5c5f0a256e02c7091e047d13dc`.
   The initial forty episodes passed **40/40**, with **81/81** checkpoints.
   The twelve raw source probes and thirty-seven adversarial/control probes
   were also run. Original results were retained unchanged.
3. A separate root code review found an unrealizable missing-premise plan and
   two VM issues: empty text programs could evade semantic-scope validation,
   and stopped text errors could lose the active theory snapshot. These were
   reviewer counterexamples, not disclosed hidden corpus cases. Runtime fixes
   were made before opening the reserve; they are post-first-freeze adaptations.
4. At **22:49:28 UTC**, the next runtime was hashed as
   `215e3c72501c2b9f124b3d1e0f9e72323a85c49d6acfcb362c0b06bccc9006cc`
   and archived before reserve execution. The previously unopened twenty
   episodes passed **20/20**, with **45/45** checkpoints.
5. The initial forty were rerun as **regression**, passing again. The raw-source,
   adversarial, missing-plan, parsed-document boundary, and declared fact-only
   baseline runs were recorded separately. The portable published entrypoint
   then reproduced **60/60 episodes and 126/126 checkpoints**.
6. The corpus, gold, tools, and source spans were published only after the
   reserve run. **All future executions on this material are regression runs.**
7. A post-publication portability review found that the historical snapshot
   glob had also pinned four generated `.egg-info` text files. The portable
   replay manifest removes exactly those four records and retains all 29
   authoritative records unchanged. Original 33-file manifests, archives,
   results, and gold were preserved. The default tool and future snapshot
   capture were corrected; a fresh source copy with no packaging metadata
   reproduced all suites. This changes the replay pin, not the runtime or
   the hidden-evaluation chronology. See `portability_review.json`.

The first snapshot was initially recorded as file hashes rather than a commit
or byte archive. Its four subsequently changed files were reconstructed by
reversing known edits. Every one of the 33 reconstructed/copied runtime files
was checked against the original unchanged manifest before archiving. The
reconstruction report and archive checksum make this distinction explicit.

## Separate source and robustness strata

The twelve genuine excerpts are purposefully selected nonpilot passages from
three books already visible in the repository. They are not an unseen-book
sample. They are passed to the reader exactly as originally encoded, including
internal OpenITI markup. Whole-book hashes and original byte intervals remain
separate from excerpt-relative parsing-source identities. A safe unsupported
result receives **zero semantic coverage**.

The thirty-seven public-contract probes comprise 22 altered certificates, seven
source/lifecycle checks, five unsupported/malformed-language checks, two resource
checks, and one valid-certificate control. Three additional probes exercise
caller-forged parsed documents. Seven reviewer-regression scenarios replay each
returned missing plan in a fresh theory. These counts do not enlarge the
sixty-episode language benchmark.

The fact-only baseline receives the same source bytes, reader, scopes, and
update sequence. It retrieves explicit signed facts, without applying any
definition, universal, or conditional rule. It is not a trained model or a
general language-model baseline. Its comparison uses status accuracy and
source-relative answered-query precision/coverage.

Raw denominators and nominal Wilson intervals are in `summary_metrics.json`.
The intervals are descriptive over the selected items; shared templates,
multiple checkpoints per episode, and nonrandom sampling prohibit interpreting
them as population confidence intervals for Arabic.
