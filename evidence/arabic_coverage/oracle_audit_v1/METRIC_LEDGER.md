# Coverage metric and oracle limitations ledger

This ledger separates fixture conformance, the linguistic validity of fixture
inputs, and implementation coverage. It does not change any original gold
case, expected answer, or denominator. The underlying static audit is in
`question_input_audit.json`, including source bytes, excerpt offsets, and
baseline/current gold digests.

## Current evidence

| Evidence | Classification | What is established | Consequence for reporting |
| --- | --- | --- | --- |
| Original construction fixture: 86 cases, 106 question entries | Frozen benchmark | Current gold is byte-identical to baseline `f0064f0a4baab3cc816087a322aabc0c8fbb2d19`. | Keep the strict denominator of 86. Report exact fixture conformance as such. |
| Original discourse fixture: 86 cases, 74 question entries | Frozen benchmark | Current gold is byte-identical to that baseline. | Keep the strict denominator of 86. |
| `CON-Z10`, first question: `هَلْ مَا ظَنَّ سَامِرٌ بَاسِمًا شُجَاعًا؟` | Confirmed question-input defect under the declared Ibn Hisham norm | The gold requires a complete interpretation, `SUPPORTED`, and a certificate. Ibn Hisham restricts `هل` to positive clause form and explicitly contrasts interrogative hamza with negation. Applying that general restriction to matrix `ما ظن` is an explicit audit inference. | A failure on this question alone is not evidence of failure to understand a grammatical question under this norm. A pass alone is not evidence of source-licensed grammar. Keep the original score and disclose the conflict separately. |
| `CON-K07`, first question: `هَلْ مَا زَالَ سَامِرٌ نَشِيطًا؟` | Unresolved scope, **not** a confirmed defect | Al-Sabban reports the distinction between negative wording and affirmative meaning of `ما زال`. The cited discussion concerns other syntactic operations; it does not decide the licensing of `هل` here. | Do not silently count this as valid or invalid on the strength of a string match. Do not remove it from the denominator. |
| No `هل` followed immediately by the scanned negative forms in original discourse questions | Limited negative scan result | The temporary scan found no candidate among those 74 questions. | This does not certify the grammatical or semantic correctness of every discourse gold question. |
| Four question inputs in independent holdout v1 used `هل` before explicit negation | Authored oracle defect found before execution | The v1 freeze is unchanged. An explicit erratum and separately frozen v2 replace only those question inputs with detached interrogative hamza. The 36 cases, 63 questions, expectations, and evaluator remain unchanged. | Use v2 as the corrected declared input revision. Preserve and disclose v1; do not call v1 an executed failure or the repair a runtime improvement. |
| Historical counts reported to the independent reviewer: construction 71/86 and discourse 56/86 | Prior measurement, not independently rerun here | These are the task's supplied starting measurements. No current runtime gap count is inferred from them in this audit. | Report a new execution separately, with runtime and input digests. Do not subtract an oracle defect to manufacture an improved score. |
| Frozen holdout v2 | Unexecuted independent challenge | Freeze SHA256: `127a5870fcbc8f8823b95f2a9f452cf4cd87de22fcfc62b271efd32bc684c106`. No prediction preceded its freeze. | Runtime gaps and unsafe acceptances remain **pending measurement** until integration is stable and the root authorizes execution. |

## Source scope

The pinned *Mughni al-labib* passage, physical lines 8094–8107, says
`والثاني اختصاصها بالإيجاب` and contrasts prohibited `هل لم يقم` with hamza
examples including `أليس الله بكاف عبده`. The same source, lines 8124 onward,
discusses rhetorical negation expressed by a question with `هل`. The audit
therefore distinguishes **explicit negative clause form** from a negative
answer or the rhetorical effect of an affirmative-form question.

The pinned *Hashiyat al-Sabban* passage, lines 12395–12402, records that
`ما زال` is negative in wording and affirmative in meaning. Lines 47471–47476
include `هل ما أخبرك به هذا الشخص صحيح`, where `ما` is relative, which shows
why the substring `هل ما` alone is not a grammatical verdict. No claim here
covers all historical, modern, or dialectal Arabic usage.

Detached hamza is the published token-input convention used by the independent
test material. The more usual joined spelling requires its own declared input
coverage; no spelling normalization or equivalence is presumed in the score.

## How later runtime findings must be recorded

Each failed case must retain the exact expected and observed results, original
input revision, runtime digest, and raw evidence. Classify a discrepancy as an
implementation gap only after confirming the relevant input and oracle premise.
If the oracle premise is disputed, record that dispute alongside the unchanged
strict result. If both an oracle defect and an independent implementation defect
are present, record both; one does not excuse the other.

A complete score on either finite fixture establishes conformance to those
inputs and expectations. It does not establish completeness for Arabic, the
adequacy of every reference meaning, or equivalence between a source rule and
the implementation that invokes it.

## Post-execution addendum: preserved first holdout v2 run

The first execution against runtime freeze v1 remains unchanged at **34/36**
cases, with **61/63** expected question statuses and one recorded
`unsafe_acceptance` flag. Its result and raw journal are preserved in
`../holdout_runs_v1/`. The result reports valid measurement and unchanged runtime
bytes during that execution.

| First-run finding | Independent classification | Preserved evidence and reporting consequence |
| --- | --- | --- |
| H18 question 2, `مَنْ حَكِيمٌ؟`, returns `UNKNOWN`, no positive proofs, no positive binding groups, and two counterproof receipts for the same accepted negative Nasser claim | Confirmed checker defect in the frozen harness's blanket rule that every `UNKNOWN` must lack counterproofs | `../holdout_postreview_v1/oracle_erratum.json` preserves the exact original failed check and unsafe flag. Both answer validators checked the complete negative claim, substitutions, source proof set, adjective agreement witnesses, and every question interpretation. The original unsafe flag remains in the original result. |
| H19, `كَادَ نَاصِرٌ يَكْتُبُ اليَوْمَ.` | Remaining bounded coverage failure under the authored case oracle | The stored report has zero analyses, `DEFER`, and `COMPLETE_SUPPORTED_CLAUSE_READING`; it supplies no grounded claim. Both requested question statuses become `DEFER`. The failure remains in the denominator and in the reviewed result. The safe abstention is not an unsafe factual assertion. |

The frozen harness did not store a separate inquiry report. To review H18's
complete answer contract, `tools/arabic_coverage_postreview_v1.py` extracted the
exact archived runtime v1, relearned the same frozen lexical premises, and read
**only H18 question 2**. The resulting `question_report_id` exactly matches the
one in the original stored answer. The answer's frozen-runtime replay and both
independent validators pass; the source, inquiry, and all answer receipts were
checked. The supplementary report and hashes are preserved alongside the
erratum. No original prediction, expected status, frozen scorer, or input was
changed.

The explicitly **post-review rescore of those same predictions** is **35/36**,
with one original unsafe flag reclassified as a checker false alarm and zero
remaining unsafe flags. The question-status result remains **61/63**. This is
not a fresh blind score and not a runtime improvement. The first strict result
remains a failure, and H19 remains a failure after the checker correction.
