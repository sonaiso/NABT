# Final construction v4 comparison (0.14.0a3)

This directory preserves the same-final-adapter comparison of constructions v2 and v4 on the **unchanged original 86 cases**. All prior v1/v2/v3 material, runs, code archives and partial-gate decisions remain historical evidence. In particular, the v3 legacy discourse regression to 40/86 is not hidden by this suite's stable score.

## Original material

Both versions score **71/86**, with **30/43 positives**, **31/31 boundaries**, **4/6 ambiguity**, and **6/6 replay**. Comprehension is **65/80**. Questions remain **30/42 SUPPORTED**, **29/39 UNKNOWN**, and **19/19 no-grounded-support controls**. UNKNOWN is not counted as a supported fact. Both have zero false accepts and measurement errors.

`results_v2_strict.*` and `results_v4_strict.*` preserve the first pin-only strict comparison, before v4's gate approval. `results_v2_final.*` and `results_v4_final.*` use identical final evaluator/test bytes after the separately reviewed v4 gate. Each final raw gzip contains **87 canonical records and 106 question calls**, including the six replay questions. All 86 saved scores per runtime were recomputed from raw reports; all runtime/archive members and code origins were validated.

`comparison.json` binds those runs and records that case checks and grounded claim/query semantics are unchanged. The observed I09 candidate count goes from four to zero, while both versions still defer without a claim; it is not a new successful case. `gate_review_preapproval_v1.json`, `gate_change_v1.json`, and `gate_review_v1.json` preserve the gate review sequence. Only `gate_decision` changed after the strict measurements; semantic scoring and gold stayed fixed. The 37 focused evaluator tests passed.

The default remains strict. The optional v4 mode is `documented_partial_coverage_v3`, bound to the pinned v4 manifest and only the existing **15 cases / 120 failed-check signatures**. Both optional final runs exit 0 while retaining **strict_pass=false**. It cannot waive false accepts, damaged certificates, replay failures, incomplete logs, execution errors, or any unreviewed signature. The v2/v3 policies remain separate and unchanged.

## Separate authored review regressions

| Suite | Baseline | v4 | False accepts before/after |
|---|---:|---:|---:|
| Context-only name premise (v3 baseline) | 11/16 | 16/16 | 0 → 0 |
| Alif internal-template source agreement (v2 baseline) | 10/12 | 12/12 | 2 → 0 |
| Adverb attachment / matrix claim correlation (v2 baseline) | 4/6 | 6/6 | 2 → 0 |

Each pair uses its own identical final runner bytes. These are authored **post-review regressions**, frozen before each correction, not natural corpora or fresh blind holdouts. They are never added to the original 86-case denominator. The context profile remains an explicit premise, not acquired lexical gender/number.

The attachment baseline comparison explicitly uses the complete six-record journal retained in its checkpoint archive, extracted losslessly into a new gzip and revalidated against every original record hash and score. The incomplete loose files and two invalid attempts remain preserved. See `../attachment_review/archival_recovery_v1.json`; no original result or report was overwritten and no unproved cause is assigned.

`checkpoint_final_v1.json` records the externally revalidated authoritative files after the selected measurement jobs exited. Its attachment evidence points to the complete retained archive and recovered gzip, not the incomplete loose journal.

## Separate legacy regression

The legacy discourse v2/v4 comparison is **57/86 → 56/86**, with supported questions **23/45 → 22/45**, no-support **29/29**, and zero false accepts/errors. P16 now defers across incompatible N/ADJ question interpretations; P26 retains unknown source number and unlicensed agreement/idafa roles. That suite has its own reviewed gate. This construction-86 partial gate is not whole-product release approval and does not relabel either legacy limit as a success.
