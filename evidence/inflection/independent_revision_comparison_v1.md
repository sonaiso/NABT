# Inflection revision comparison: identical final evaluator

The frozen original set improves from **66/74 on 0.12.0a1 to 72/74 on
0.12.0a2**. The separate post-review regression set improves from **11/22 to
22/22**. Both comparisons use the same final evaluator and test bytes. The
original set still fails the strict gate: `INF-T15` and `INF-K10` require a
complete source base that the frozen exclusion split removes.

These are counts of cases satisfying their specified predicates, including
abstention and source-integrity predicates. They are not an estimate of accuracy
on unrestricted Arabic.

The machine-readable comparison, all result hashes, raw-log hashes and code
archive hashes are in
[`independent_revision_comparison_v1.json`](independent_revision_comparison_v1.json).

## Results

| Measurement | a1 | a2 | Interpretation |
| --- | ---: | ---: | --- |
| Original authored set | 66/74 | 72/74 | Frozen original expectations, no gold changes |
| Unseen realization stratum | 19/20 | 19/20 | Complete dual base for the remaining case is excluded |
| Known form/context/ambiguity | 10/12 | 11/12 | Paired plural letter paradigm recovered |
| Nun and nominal boundaries | 5/10 | 10/10 | Full suffix chains and correlated nun evidence preserved |
| Unknown-family abstention | 8/8 | 8/8 | Unknown roots are not supplied from policy |
| Attachment/representation boundaries | 16/16 | 16/16 | Unsupported attachments remain inactive |
| Source counterfactuals | 8/8 | 8/8 | Hidden case/mood changes and source withdrawal checked |
| Conditional sign law | 60/60 | 60/60 | 45 admitted rows and 15 excluded class/case pairs |
| Separate post-review regressions | 11/22 | 22/22 | Authored source fixtures; not a new held-out corpus |
| Measured false accepts in original set | 0 | 0 | Bounded by the frozen predicates |
| Execution/adapter errors in original set | 0/0 | 0/0 | No exceptional cases removed from the denominator |

The a1 post-review failures are all coverage misses. The a2 post-review result
has no failures. No case regresses in either comparison.

## What improved

Six original cases improve: `INF-K04`, `INF-B01`, `INF-B03`, `INF-B04`,
`INF-B05` and `INF-B06`. Their diagnoses were recorded before the a2 repair in
[`independent_review_v1.json`](independent_review_v1.json).

- **Plural letter paradigm:** a compatible source pair ending in ـُونَ / ـِينَ
  can support the letter-declension class even when its source lemma is itself
  plural. The regression checks require agreement on lemma, root, POS, gender,
  number and internal template, including the preceding vowel. They do not
  manufacture a singular witness or classify the plural as semantically sound
  or broken. The generated alternate form also changes the preceding vowel.
- **Complete attested suffix chains:** the source-qualified verb reading and
  segmentation survive for a complete written form with additional suffixes.
  The incomplete construction proof remains explicit: these readings keep
  construction unresolved and do not acquire governor activation. A generic
  QAC `PRON` suffix does not by itself establish an object role or protective
  nun semantics.
- **Nun correlation and positions:** radical and retained inflectional nuns
  can coexist in one reading. Each present nun restores its own complete raw
  source cluster, including combining marks. A deleted nun cannot invent a
  nonempty observed span. Evidence pooled across alternative readings is
  insufficient.
- **Emphasis evidence:** a source `EMPH` suffix preserves a verb/emphasis
  candidate without proving emphatic directness or full construction.

The post-review set independently exercises these repairs with different
authored forms and explicit premise counterexamples. Its eleven improvements
are `POST-P01`–`POST-P03`, `POST-S01`–`POST-S03`, `POST-E01`–`POST-E03`,
`POST-R01` and `POST-R02`. The nine paired-premise negatives and the two
remaining nun controls already passed on a1 and still pass on a2.

## The two unresolved original cases

`INF-T15` (`لَمْ يَسْجُدَا`) and `INF-K10` (`يَسْجُدَانِ`) require the retained
dual imperfect base. The only such full base in the pinned QAC data is
`yasojuda` + `Ani`, at locations `(55:6:3:1)` and `(55:6:3:2)`. The frozen
global exclusion closure for `INF-T10` removes verse `55:6`. Other persons do
not witness this dual base. The split already records that the K10 target is
absent after exclusions; this is not a newly substituted split.

The positive gold remains unchanged, the missing base is not restored, and
both cases remain failures in the denominator of 74. All four comparison runs
were performed without the optional documented-boundary gate. Consequently,
the saved a2 original report has both `strict_pass=false` and `gate_pass=false`.
The separately configured CI option may admit only these two documented
coverage IDs, while preserving the strict score and rejecting any false
accept, execution error, adapter error or unexpected miss. The separate
post-review run passes strictly.

## Comparable executable evidence

The original a1 first result and its corrected-adapter replay remain immutable.
The independent scorer review had found missing correlation checks between
relation case/domain, the reading assignment, the governor endpoint and its
rule. Those corrections and their unchanged 66/74 same-a1 result are recorded
in [`independent_adapter_erratum_v1.json`](independent_adapter_erratum_v1.json).

Before the four measurements reported here, the evaluator was further hardened
to require complete nun clusters, same-reading nun correlation, explicit
runtime origin isolation, exact allowlisted manifests and complete archive
inventories. Sixteen focused adapter tests passed. The final code freeze is
[`independent_adapter_freeze_v2.json`](independent_adapter_freeze_v2.json).

An additional original74 a1 replay was requested after that adapter freeze so
the original a1/a2 comparison also uses identical final bytes. It is saved as
`independent_final_adapter_a1_v1.json`; the immutable freeze's earlier planned
filename list was not retrospectively edited. This replay again scores 66/74
with exactly the original eight missed cases.

The final evaluator SHA-256 is
`da20bf9f22b522b97aab70879efd123e52e42c6b464b957592af4885a639acfa`.
The focused test SHA-256 is
`32d151eebb954ff9d9165ac171ef901e9b5e69c622356fc3aa6edadc960a4990`.
All four run snapshots contain those exact bytes.

a1 is loaded from its separately extracted pinned archive. Fresh processes and
loaded-module origin checks prevent current a2 imports from contaminating a1
measurements. Each run checks all 58 authoritative runtime files and every tar
member, then preserves the selected runtime plus evaluator/tests before making
predictions. The two immutable runtime snapshots are:

| Runtime | Snapshot SHA-256 |
| --- | --- |
| a1 | `aaac387085d745b89f0260eb1905d66dade8a710e483034442e7957972243ede` |
| a2 | `818a1a90e0710daf951bc8108b32f37978938361c0f8f92032840872640c52f3` |

Three named existing documentation/Git metadata paths are outside the historical
authoritative inventory: `src/nabt/data/source_evidence/README.md`,
`src/nabt/data/source_evidence/LICENSE-DATA.md` and
`src/nabt/data/source_evidence/.gitattributes`. Every run records those exact
exemptions. They do not exempt an arbitrary directory or file extension, and
the archived runtime still has the exact authoritative member inventory.

## Limits of the evidence

The first a1 result is the original independent test of this source-informed
contract, authored and frozen before the reviewer read the new implementation.
The a2 result is a replay after disclosed repairs. It is not a second untouched
holdout result. The post-review examples
were frozen before reading a2 implementation/output, but after the repair
contracts were known; their miniature QAC-format source assertions are authored
fixtures, not Quran passages or a natural corpus.

The source learner uses permitted QAC POS, lemma, root and morphology fields;
CASE, MOOD and role labels are excluded. Transfer from those source claims to
new written forms and bounded attachments does not establish unsupervised root
or lexical acquisition. Unknown-family abstentions remain part of the test.
The earlier broader failures involving reference, semantics and scope are not
resolved by these sign laws and closed grammatical frames.

No runtime, formal table, original gold, post-review gold, historical result or
historical freeze was edited by this evaluation step.
