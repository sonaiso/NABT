# Construction evidence and independent evaluation

The final independent construction comparison is **42/86 → 70/86 → 71/86**
for the old discourse-v4 baseline, construction v1, and construction v2.
The final target completes **30/43 positive cases**, **31/31 boundary cases**,
**4/6 ambiguity cases**, and **6/6 separate replay cases**. The strict suite
remains incomplete. The explicit partial regression gate preserves every failed
case/check and never relabels it as linguistic success.

The full explanation, question denominators, measurement history and remaining
gaps are in [CONSTRUCTIONS_EVALUATION.md](../../docs/CONSTRUCTIONS_EVALUATION.md).
The runtime scope is documented separately in
[CONSTRUCTIONS.md](../../docs/CONSTRUCTIONS.md).

## Frozen independent material

| Artifact | Purpose |
|---|---|
| [independent_freeze_v1.json](independent_freeze_v1.json) | Immutable hashes of the 86 cases, protocol and source material; frozen before new implementation inspection |
| [independent_cases_v1.json](independent_cases_v1.json) | 43 positive, 31 boundary, 6 ambiguity and 6 replay cases; expected roles, attachments, qualified claims and answers never enter production inputs |
| [independent_training_v1.tsv](independent_training_v1.tsv) | 140 authored lexical words / 183 segments, in the public QAC-like format; no CASE/MOOD, role, attachment or answer fields |
| [independent_sources_v1.json](independent_sources_v1.json) | Source-informed grammar windows and authored lexical inventory |
| [independent_protocol_v1.md](independent_protocol_v1.md) | Independence, scope, semantic obligations, replay separation and reporting protocol |
| [independent_pre_freeze_validation_v1.json](independent_pre_freeze_validation_v1.json) | Source-format compilation only; no construction predictions were probed before freeze |

These are independently authored composition cases, not quoted QAC examples,
untouched natural-corpus gold, a secret lexical holdout, or an unseen-ending
benchmark. The lexical fixture was available after freezing. Explicit context
identities/traits and source annotations are premises, not acquired world facts.
No gold input, source, expectation, question or denominator was changed after
freezing.

## Runtime and source records

| Artifact | Meaning |
|---|---|
| [code_freeze_v1.json](code_freeze_v1.json), [archive](code_freeze_v1.tar.gz) | First construction runtime, frozen before implementer access to gold |
| [code_freeze_v2.json](code_freeze_v2.json), [archive](code_freeze_v2.tar.gz) | Post-review repair of future kana routing; 74 authoritative files, package version 0.14.0a1 |
| [prior discourse v4](../discourse/code_freeze_v4.json) | Baseline 0.13.0a2, separately extracted for every comparison |
| [source_audit.json](source_audit.json), [source_coverage.json](source_coverage.json) | Primary-source and Lean audit, separate from runtime test gold |
| [source_audit_future_v2.json](source_audit_future_v2.json) | Source review of the future-kana repair |
| [formal_contracts.md](formal_contracts.md) | Conditional law scope, distinct from acquisition and Python correctness |

## Measurement history: keep every attempt

1. `independent_runs/*_first.*` preserve the first baseline and target attempts.
   Their raw logs are complete, but adapter validation errors make the numerical
   scores **invalid as comparative measurements**. The
   [adapter erratum](independent_adapter_erratum_v1.json) binds every original
   artifact and records the corrections without changing gold.
2. `independent_runs/*_adapter_v2.*` preserve the first corrected valid pair,
   42/86 and 70/86. A later independent unit review strengthened the rule against
   answer evidence from an incomplete overall document/question. The
   [second adapter review](independent_adapter_review_v2.json) records that change.
3. `independent_runs/*_adapter_v3.*` preserve the same-adapter three-way comparison
   before adding the optional gate. [independent_comparison_v1.json](independent_comparison_v1.json)
   binds those runs and their complete raw replay.
4. **`independent_runs/*_final.*` are the release comparison**, all made using
   identical final evaluator/test bytes. The linguistic checks match the
   preceding three-way comparison exactly. The
   [final comparison](independent_comparison_v2.json) records scores, differences,
   hashes, exit status, import/runtime verification and fresh raw rescoring.

Each run stem has a result JSON, `raw.jsonl.gz`, `code.tar.gz`, stdout and stderr.
The code archive contains the actual runtime and evaluator/test bytes used in
that run. A result is accepted only after closing and fully decompressing gzip,
checking canonical JSON and write-time line hashes, and reconciling all ordered
case, score, question and error inventories. A complete independent run has
87 raw records, 86 cases and 106 question calls, including the 6 replay questions.

## Findings and gate

- [independent_k06_disclosure_v1.json](independent_k06_disclosure_v1.json) preserves
  the genuine v1 interpretation defect: future kana was treated as an event plus
  hal. Exact-question support did not make the full case correct. The repair
  contributes one post-review gain; it is not a new untouched holdout.
- [independent_diagnosis_v1.json](independent_diagnosis_v1.json) records the original
  16 misses. K06 alone is repaired in v2; the other 15 remain visible.
- [independent_gate_review_v1.json](independent_gate_review_v1.json) freezes the
  15 case IDs / 120 exact failed-check signatures allowed only for runtime v2
  when `--allow-documented-boundaries` is explicitly supplied. Scoring and
  validation definitions are unchanged by the gate addition.

The final partial gate returns success while preserving 71/86 and
`strict_pass=false`. K06, unexpected checks, forbidden accepted claims, replay,
invalid certificates, execution/adapter errors and incomplete evidence logs are
never waived. The default command remains strict and returns exit 1.

Question results must remain separate: **30/42 SUPPORTED**, **29/39 UNKNOWN with
a complete query**, and **19/19 no-grounded-support controls**. Unknown and safe
abstention are not affirmed answers. There are 100 composition/boundary questions
plus 6 separate replay questions.

## Historical regression

[legacy_discourse_review_v1/comparison.json](legacy_discourse_review_v1/comparison.json)
preserves the separate unchanged historical discourse suite: 57/86 for all
three runtimes, 12/30 positives, and substantive questions 24/45 → 23/45.
The 29 no-support controls still pass. The single lost question check is P26;
the total case score does not conceal that loss. Its invalid first truncated-log
attempt and all valid replacement runs remain preserved. These historical cases
are regression material, not fresh held-out evidence for the new implementation.
