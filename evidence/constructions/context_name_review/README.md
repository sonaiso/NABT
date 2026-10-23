# Context-only name agreement regression

This is a compact **authored post-review regression**, frozen before the corrective helper was implemented. It is not a natural corpus, a blind holdout, or evidence that lexical gender was acquired. The names **نِبْرَاس** and **رِهَام** are fresh relative to the earlier discourse/construction gold. Their identity, person kind, gender and number are explicit, replayed context premises. The training sources supply adjective morphology and the source-PN/common-noun controls, without CASE/MOOD, roles, attachments or answers.

## Frozen scope

`material_freeze_v1.json` binds 16 cases and every input byte: four positive controls, ten boundaries and two context replay cases. Positive context-only names require one uniquely resolved named person, explicit gender and singular number, a source-qualified adjective and correlated predication. The contextual semantic profile must be recorded as such; the name reading's lexical gender/number, construction and case are not filled by that premise.

The boundaries retain mismatching adjectives; missing gender/number/person kind; two same-name individuals, including an unknown competitor; an independently sourced PN contradicting context; a sourced PN with unknown traits; and an ordinary noun with unknown lexical traits. The narrow fix must not override or fill those sourced noun profiles. Context change and withdrawal must invalidate both old document and answer certificates.

## Preserved v3 baseline

`results_baseline_v3_attempt1.json` and its complete journal/input/runner archives were produced solely from the pinned extracted constructions v3 runtime. The result is **11/16**, with **zero false accepts and zero execution errors**. All ten boundaries and the independent source-PN positive pass. Context-only positive cases P01/P02/P03 and replay cases R01/R02 lack the original licensed claim. The journal contains all 16 records, was reread after closure, and every score was recalculated from its saved reports.

`baseline_review_v1.json` lists the failed checks without changing the material. `runner_freeze_v1.json` preserves exact runner and focused test bytes before any v4 registration. The later comparison must rerun this baseline with the same final runner used for the corrected archive.

## Development validation, not a frozen measurement

`development_tests_attempt1.json/.log` record **16/16 focused unit tests** against the corrected but still mutable checkout. The file and runner hashes are recorded. This is a development check, not the formal after-runtime measurement. Tests cover the same independent frozen material through the public reader/ask/replay APIs.

A read-only review of the corrected helper found the intended narrow premise: only the exact context naming reading, with one resolved named reference and explicit person/singular/gender traits, supplies a local semantic profile. The stored lexical reading remains unchanged. Source N/PN readings are excluded even if their features are unknown. Every accepted contextual agreement carries entity ID, context hash, reference ID and the four used context fields. General plural, nonperson or unknown-trait semantic agreement remains outside this correction.

No historical 86-case gold, runtime freeze or result was overwritten. The separate construction-86 v3 gate does not waive the independently measured legacy 57/86 to 40/86 regression.

## Final v4 comparison

The frozen v4 run and its baseline use the same final runner bytes. The result is **11/16 → 16/16**, with false accepts **0 → 0** and zero execution errors. `comparison_v1.json` binds both approved runtime snapshots, result and raw hashes, exact runner/input archives, and a fresh rescore of every saved report after journal closure. Earlier v2/v3 results and all material remain unchanged. This remains an authored post-review regression; it is not added to the original 86-case denominator.
