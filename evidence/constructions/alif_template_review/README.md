# Accusative-alif source template binding

This is a targeted authored regression after read-only review of commit `83c14b2`, frozen before the corrective implementation. It is not a blind holdout or natural-corpus acquisition measurement. The prior 86-case gold and all earlier results are unchanged.

## Same-runner comparison

| Runtime | Passed | False accepts | Execution errors | Strict pass |
|---|---:|---:|---:|---|
| Frozen constructions v2 | 10/12 | 2 | 0 | false |
| Frozen constructions v3 (0.14.0a2) | 12/12 | 0 | 0 | true |

Resolved cases: ALIF-B01, ALIF-B04. No expectation was weakened or waived.

Both final runs used `run_review.py` SHA `199d08eb7e3fc3461a1e718929f3fa7a48000d4937fc11898c3248a67f0e652e` with the same frozen material SHA `69b3c68be10770ecc6288bdacec64591474e3b8685d53ca2971f568925198c45`. The earlier baseline attempt is retained with its exact runner and input archive. The only runner change between that attempt and this comparison added the approved v3 runtime pin; AST comparison excluding the `PINS` assignment confirms unchanged scoring and execution logic.

Each run used a separate process and an archive-extracted runtime. It verified all 74 authoritative files and the approved runtime archive before and after execution, checked imported module origins, archived the exact runner and source material, and re-read the full canonical raw journal after closure. Case order, write-time line hashes, scores and replay identities matched: 12/12 baseline records and 12/12 after records. No incomplete journal is treated as a completed result.

`comparison_v1.json` records all result, runtime, journal, runner and material identities. `initial_review_v1.json` remains the initial review record; its pending-after-measurement field records its time of creation and is superseded by this completed comparison.

## Reproduction

```sh
python evidence/constructions/alif_template_review/run_review.py \
  --runtime-root /path/to/extracted/runtime \
  --runtime-freeze evidence/constructions/code_freeze_v3.json \
  --output /new/path/results.json
```

Use a new output path. v3 must exit 0; the preserved v2 baseline exits 1 because the demonstrated defect remains present there.

## Final v4 comparison

The frozen v4 run and its baseline use the same final runner bytes. The result is **10/12 → 12/12**, with false accepts **2 → 0** and zero execution errors. `comparison_v2.json` binds both approved runtime snapshots, result and raw hashes, exact runner/input archives, and a fresh rescore of every saved report after journal closure. Earlier v2/v3 results and all material remain unchanged. This remains an authored post-review regression; it is not added to the original 86-case denominator.
