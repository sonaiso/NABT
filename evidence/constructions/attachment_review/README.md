# Adverb attachment to the actual claim head

This is a targeted authored regression after read-only review of commit `83c14b2`, frozen before the corrective implementation. It is not a blind holdout or natural-corpus acquisition measurement. The prior 86-case gold and all earlier results are unchanged.

## Same-runner comparison

| Runtime | Passed | False accepts | Execution errors | Strict pass |
|---|---:|---:|---:|---|
| Frozen constructions v2 | 4/6 | 2 | 0 | false |
| Frozen constructions v3 (0.14.0a2) | 6/6 | 0 | 0 | true |

Resolved cases: ATT-B01, ATT-B02. No expectation was weakened or waived.

Both final runs used `run_review.py` SHA `f0a56b9164d7873af42e5b3d2d48e3a32a973ca728972516e4bbf29ea7817637` with the same frozen material SHA `2b3b1db96f8af2d344aa9dbfc2d6606eb418a1dc405ebfd372c1f8e81afdfa23`. The earlier baseline attempt is retained with its exact runner and input archive. The only runner change between that attempt and this comparison added the approved v3 runtime pin; AST comparison excluding the `PINS` assignment confirms unchanged scoring and execution logic.

Each run used a separate process and an archive-extracted runtime. It verified all 74 authoritative files and the approved runtime archive before and after execution, checked imported module origins, archived the exact runner and source material, and re-read the full canonical raw journal after closure. Case order, write-time line hashes, scores and replay identities matched: 6/6 baseline records and 6/6 after records. No incomplete journal is treated as a completed result.

`comparison_v1.json` records all result, runtime, journal, runner and material identities. `initial_review_v1.json` remains the initial review record; its pending-after-measurement field records its time of creation and is superseded by this completed comparison.

## Reproduction

```sh
python evidence/constructions/attachment_review/run_review.py \
  --runtime-root /path/to/extracted/runtime \
  --runtime-freeze evidence/constructions/code_freeze_v3.json \
  --output /new/path/results.json
```

Use a new output path. v3 must exit 0; the preserved v2 baseline exits 1 because the demonstrated defect remains present there.

## Final v4 comparison and artifact recovery

The final comparison is **4/6 → 6/6**, with false accepts **2 → 0** and zero execution errors, using identical final runner bytes. `comparison_v2.json` binds both runtimes and fresh rescoring of every saved report.

Two baseline attempts for this pair have incomplete loose journals and remain explicitly invalid in `artifact_erratum_v4pair_v1.json` and `artifact_erratum_v4pair_v2.json`. A third completed attempt retained all six canonical records inside its independently verified checkpoint archive, although its loose journal later disagreed with the recorded bytes/hash. `archival_recovery_v1.json` preserves the exact metadata facts without assigning an unproved cause. The complete journal was extracted losslessly from that retained archive into `baseline_v2_v4pair_recovered.raw.jsonl.gz`; every record hash and saved score was revalidated. The comparison explicitly uses this recovered archival evidence and the unchanged original result. No original file, report, score, gold or runtime was overwritten.
