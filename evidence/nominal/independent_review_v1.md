# Independent nominal, number and weakness review v1

## Frozen material and first measurement

The independent reviewer froze 184 authored, source-informed cases before opening the new nominal runtime, generated nominal table, formal module or implementation tests. The material is not an untouched external corpus and does not estimate Arabic-wide accuracy. Controlled-source claims, supplied root/cardinal operands, raw observations, conditional count-phrase requirements and source-occurrence counts have separate denominators.

The frozen cases remain unchanged:

- `independent_cases_v1.json`: `1c865468207b2238118999f157fccda9aee9f260585f2b3c36ca9b556c3b52b9`.
- `independent_protocol.md`: `d31c2a612e15f68ada1e7f8377a96998ccb8b3236d9870760492cb64945a9b8a`.
- `independent_material_freeze_v1.json`: `fb8caa81febae39762b42613802391c322ef3f0e1afc5c83472a92b964ff9f62`.

The first executable measurement passed **184/184**, with the runtime snapshot unchanged throughout that measurement. No gold or evaluator correction followed that run. Its result and code archive are historical, immutable records:

| Record | SHA-256 |
|---|---|
| `independent_first_run_v1.json` | `42b1e65fea397dd8e26855fc08dc52eccfd24a409fc270193ea8c41fd635a8f0` |
| `independent_first_run_v1.code.tar.gz` | `fbf04ce2f3a60c56a82b99320a74522c38e05156fcffe4ee508ec5d8d181f0a1` |
| Runtime/evaluator/test snapshot manifest | `5a4f204c5b9527608c8057baff317c44d808bf30ecf879d10058a590cf441808` |

The first-run API totals were 53 nominal-reading cases, 41 controlled-source fact cases, 20 supplied-root cases including boundaries, 38 cardinal-rule cases including boundaries, 15 count-phrase cases, 11 source-count cases and six source-replacement cases. The overlapping independent source-structure checks passed 126/126; semantic-restraint checks on returned reports passed 166/166. Rejected malformed operands do not count as positive lexical coverage.

The focused review command was:

```sh
PYTHONPATH=src python -m unittest discover -s tests -p test_nominal_review.py -v
```

It passed 18/18 tests. One test replays the frozen 184-case loop; the other 17 are explicitly post-open checks of the evaluator's negative controls, witness isolation, source identity, missing premises, quotation context, numeric types, alternative readings and report replay. Those additional checks are not added to the frozen denominator. `independent_review_summary_v1.json` records their names and outcome.

## Changes before the first measurement

`independent_pre_first_run_review_v1.json` records the corrections made after material freeze and before the first runtime measurement. The raw nominal reader stopped licensing noun kind merely from tanwin; the generated table pin was installed; candidate pronoun readings were separated from independent descriptive verb readings; and the count-phrase newline guard was restricted to internal gaps. None required a frozen case or expectation change.

The pronoun cases concern the specified reading in the closed inventory. They do not establish exhaustive homograph resolution. In particular, a candidate pronoun reading of `هم` must not manufacture a contradiction with a separately sourced verb reading of the same spelling.

## Identity hardening after the first measurement

After the first archive was saved, the parent incorporated two identity changes requested by the formal review. A direct comparison of every file in the first-run snapshot against the working tree found exactly one changed snapshot file at the time of this note: `src/nabt/nominal.py`.

| File version | SHA-256 |
|---|---|
| `src/nabt/nominal.py` inside the first-run archive | `67b5f45456b8c072a01e5b5cd98077d77326a2d3e607b558dcb1e1df774bdfab` |
| Working-tree version reviewed for this note | `f4ad1a116e5039cf7d9fb90793ee517f46903c0eaaf9144f0b6b36e2e6de6cff` |

The changes are specific:

1. Each reading identity now includes `lexical_source_id`, in addition to the lexical reading identifier and lexical source digest. The earlier full report and lexical link already carried this source identifier, and the frozen source-ID replacement case passed. The new identity also distinguishes the reading's own digest when identical lexical bytes are supplied under different source identifiers.
2. Each written occurrence now carries `segmentation_id`, calculated from its occurrence identity and the explicit profile `WRITTEN_RUN_UNSEGMENTED_V1`. The reading identity includes this value, and the receipt's occurrence/segmentation check verifies the profile-bound identity. This names the intact written run; it does not claim acquired morpheme or clitic segmentation.

These additions change reading identities, receipt identities and byte-exact report encodings. **The first 184/184 score belongs to the archived first-run bytes, not automatically to the later working-tree or release bytes.** Exact historical replay can use the captured archive. The parent will run the unchanged independent material again against the current runtime as a separate release gate and preserve that later result separately. This note does not claim that the later gate has already run or passed.

The independent reviewer did not change the frozen material, first result, first archive, evaluator, tests, production or formal code in response to these identity additions. This note records the provenance difference; it does not replace the historical measurement.

## Scope of the result

Explicit source assertions remain source-relative premises, not independent lexical truth. Weak-root classification is conditional on supplied canonical radicals; any pattern-derived roots remain candidates. Nominal manqus requires its five separate premises and does not follow from root weakness. Cardinal requirements, grammatical number and distinct written occurrences remain separate from real-world object count. No test result authorizes actual syntactic role or actual case.

Full repository checks, Lean conformance, installed-wheel packaging and release verification are separate parent-owned gates. They must be attributed to their own captured runtime and results.
