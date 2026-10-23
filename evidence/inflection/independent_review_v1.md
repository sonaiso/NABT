# Independent inflection evaluation: first result and review

## Measured result

The unchanged **v0.12.0a1** runtime passed **66/74** authored cases and **60/60** independently specified conditional sign-law checks. The first result is preserved in `independent_first_run_v1.json`, its raw outputs in the corresponding `.raw.jsonl.gz`, and the exact runtime plus adapter in `.code.tar.gz`. The corrected-adapter replay, `independent_second_run_v1.json`, produced the same score and the same eight failing case IDs. Neither run had a production execution error or an adapter execution error.

| Stratum | Passed | Total |
|---|---:|---:|
| Unseen realizations after whole-verse exclusions | 19 | 20 |
| Known-form context and ambiguity | 10 | 12 |
| Nun and nominal boundaries | 5 | 10 |
| Unknown-family abstention | 8 | 8 |
| Attachment and representation boundaries | 16 | 16 |
| Source counterfactuals | 8 | 8 |

No false accept was detected by the corrected checks in these cases. This is a result for the frozen authored set and its predicates, not an unrestricted accuracy estimate. ROOT, POS and other permitted lexical descriptions were learned from source annotations. The raw prediction input did not receive target classes, roles, case/mood labels, roots, or segment answers. The 20 realization targets were absent under the declared conservative split audit after excluding 48 complete verses; 126,441 training rows and 76,369 source words remained.

## The eight misses

**INF-T15 and INF-K10 have an unavailable training premise.** The sole dual imperfect full base for `ROOT:sjd` is QAC 55:6:3: `yasojuda` plus `Ani`. Whole verse 55:6 was excluded by the joint closure for the singular-looking target stem in INF-T10. The frozen split already records the K10 realization as absent after exclusions. Other persons of the same lexeme cannot satisfy the declared complete retained-dual-base premise. The positive gold expectations remain unchanged, but these two cases cannot fairly be described as a failure to apply an available full-base rule. They expose a limitation of the authored positive set after its global split. They are not repaired by adding the excluded witness back into training.

**INF-K04 exposes the plural-lemma boundary.** QAC gives `مُفْلِحُون` as the lemma of its MP readings. The first learner accepts the masculine plural letter paradigm only through exact recomposition from a singular-looking lemma. It therefore leaves class and construction unresolved even though both `ـُونَ` and `ـِينَ` source forms are present. An independently witnessed pair can support a new conditional letter-paradigm rule while leaving the singular witness absent. That rule must agree on lemma, root, POS, gender, number and internal template, and must verify the preceding damma/kasra. This is not permission to classify every spelling ending in waw/nun or ya/nun.

**INF-B01 and INF-B04 expose missing full suffix-chain readings.** Source words `يَحْمِلْنَهَا` and `أَكْفِلْنِيهَا` are retained, but v1 stores only the verbal stem and, where qualified, its subject suffix. A trailing object suffix is not represented in the complete transferable form. The input written run consequently loses its source-attested verb reading. The proposed bounded repair preserves exact full-chain kind and segmentation while leaving its construction and declension classes unresolved. It does not infer a role for the object suffix or acquire protective-nun semantics.

**INF-B03 exposes a representation limit.** `يُؤْمِنُونَ` has a source-root nun and a later inflectional nun. v1 has one scalar nun field and preserves only the latter. The needed result is a single correlated reading with two source-bound positions. Collecting one label from each of two alternative readings would not satisfy the requirement.

**INF-B05 and INF-B06 expose overbroad withholding of emphasis evidence.** v1 skips an entry whenever its source word includes an `EMPH` suffix. That safely avoids inferring directness, but also loses the verb kind and the source-qualified emphasis candidate. The proposed repair retains those observations with construction, classes and directness unresolved. An adjacent governor cannot fill the missing construction premise.

Exact source locations, byte windows and record digests for these diagnoses are saved in `independent_review_v1.json`. The two unavailable-premise cases and the six implementation coverage gaps remain separately identified there. The strict denominator stays 74.

## Adapter erratum and preserved replay

A separate reviewer showed that the first adapter could accept a report whose activated relation carried a different case/domain than its correct reading assignment, or whose head occurrence/reading/rule identity had been replaced. The original predictions and all first-run files were preserved. `independent_adapter_erratum_v1.json` records the old and new adapter hashes and the unchanged runtime snapshot.

The revised checker validates the governor-to-law mapping, the case domain implied by construction, the exact head/dependent reading and occurrence bindings, attached-prefix segmentation, support endpoints, and the agreement of activated relation and assignment. Negative mutation tests cover the discovered defects. The same a1 runtime was then measured again before any a2 runtime change: **66/74, 60/60, the same eight misses, no detected false accept**. A zero count is qualified by the checks actually performed; preserving and strengthening the checker does not retroactively turn the first adapter into a complete verifier.

## Follow-up scope

The 22 cases in `independent_post_review_cases_v1.json` were authored after these results and before reading a2 code. They are explicitly **post-review regression tests**, not a new blind score. Their miniature QAC-format sources are authored source assertions, not quotations from Quran verses. The original 74 cases, split, source audits, first and second results, and all historical code archives remain immutable.

The earlier broad semantic episode result, 0/40, is not reclassified by this work. Source-conditioned signs and local closed-frame attachments do not establish external reference, arbitrary clause interpretation, or world truth.
