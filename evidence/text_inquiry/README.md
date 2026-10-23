# Text-inquiry evaluation evidence

The final controlled regression passes **60/60 episodes and 126/126 query
checkpoints**. The actual hidden runs were **40/40 on the first snapshot** and
**20/20 on the reserve snapshot after independently discovered review fixes**.
The twelve genuine source excerpts pass **12/12 preservation/nonadmission
checks but 0/12 semantic coverage**. The authored controlled corpus and raw book
passages must not be combined into a natural-language accuracy claim.

See [the full evaluation report](../../docs/TEXT_EVALUATION.md),
[protocol and chronology](PROTOCOL.md), and [data-license notice](LICENSE-DATA.md).
The inputs and manual gold are public now; subsequent runs are regression.

## Inputs and manually authored gold

| Artifact | Contents |
| --- | --- |
| [controlled_text_benchmark.json](controlled_text_benchmark.json) | Sixty independently authored controlled-Arabic episodes, fixed 40/20 split, 126 manual query labels, source update operations, grammar/semantics and budgets |
| [real_source_candidates.json](real_source_candidates.json) | Twelve unmodified excerpts from Qatr, Alfiyya and Sibawayhi, original file hashes, exact byte offsets and excerpt hashes |
| [natural_probe_protocol.json](natural_probe_protocol.json) | Separately frozen raw-source probe method; unsupported handling is separate from semantic coverage |
| [evaluation_authoring_scripts.tar.gz](evaluation_authoring_scripts.tar.gz) | Original authoring and evaluator scripts, including their original local paths; portable replay lives under `tools/` |

The controlled dataset SHA-256 is
`1edb63bd0df4e6c35e466b989a9bc4e55d5204d66a4771f6b72f073895419127`.
The source-manifest SHA-256 is
`77cf9e1cb3fad8771b822a16db8bb54a15e5ddf03970740dfd7f59f010111b5d`.

## Original results and regression results

| Artifact | Result and role |
| --- | --- |
| [results_first40_original.json](results_first40_original.json) | Original hidden first run: 40/40 episodes, 81/81 checkpoints |
| [results_reserve20_original.json](results_reserve20_original.json) | Original unopened reserve: 20/20 episodes, 45/45 checkpoints |
| [results_first40_regression.json](results_first40_regression.json) | First partition rerun after reviewer fixes: 40/40, 81/81 |
| [results_final_published_replay.json](results_final_published_replay.json) | Complete portable regression: 60/60, 126/126 |
| [results_natural_original.json](results_natural_original.json) / [results_natural_final.json](results_natural_final.json) | Raw-source probes: 12/12 safe residuals and exact restoration, 0/12 semantic coverage |
| [results_adversarial_original.json](results_adversarial_original.json) / [results_adversarial_final.json](results_adversarial_final.json) | 37/37 public-contract probes and valid controls; all 22 mutated certificates rejected |
| [results_plan_regressions.json](results_plan_regressions.json) | Seven reviewer scenarios; all seven returned missing plans produced clean answers when asserted |
| [results_document_boundary.json](results_document_boundary.json) | Three caller-forged parsed-document probes; no invented claim admitted |
| [results_fact_baseline.json](results_fact_baseline.json) | Fact-only baseline: 84/126 correct statuses, 28/61 justified answer coverage |
| [program_review.json](program_review.json) | Separate VM review: two confirmed findings corrected and replayed |
| [published_replay_summary.json](published_replay_summary.json) | One portable entrypoint run across every published suite |
| [portability_review.json](portability_review.json) | Post-publication packaging-metadata defect, exact source-only projection, independent audit, and successful fresh-copy replay |
| [summary_metrics.json](summary_metrics.json) | Raw metric denominators and explicitly limited descriptive intervals |

## Runtime snapshots

The snapshot identifier is a SHA-256 over the sorted runtime file manifest; it
is not a Git commit identifier. Both runtime manifests recorded HEAD
`3cca86d5c06f21e0ee77738141e267d27bf7718f` with the new implementation files still
uncommitted. Their file checksums bind the actual implementation tested.

| Snapshot | Manifest and byte archive |
| --- | --- |
| First: `454adcd3df89b8f2dd127778aa5122b7e74bff5c5f0a256e02c7091e047d13dc` | [manifest](code_freeze_first40.json), [reconstruction record](code_freeze_first40_reconstruction.json), [byte archive](code_freeze_first40_reconstructed.tar.gz) |
| Reserve/final: `215e3c72501c2b9f124b3d1e0f9e72323a85c49d6acfcb362c0b06bccc9006cc` | [manifest](code_freeze_reserve20.json), [byte archive](code_freeze_reserve20.tar.gz) |
| Portable source projection: `28f5f1a224a8896eeec3f0de4f920a543428000a154a3d3ed6b75fc7e005cfc9` | [derived manifest](code_freeze_reserve20_portable.json), retaining all 29 authoritative records unchanged |

The first archive was reconstructed after the fixes. All 33 file hashes match
the unchanged original manifest; the record identifies the reconstruction
method. The reserve archive was created before the reserve was opened. The
archives preserve the mixed software/source-data licenses described above.

The historical 33-file manifests include four generated `.egg-info` metadata
files. Those files may be absent in a fresh checkout or rewritten by packaging,
so default replay uses the derived portable manifest. It excludes **only** the
four explicitly recorded metadata paths, preserves all other file hashes and
sizes, and records its exact historical origin. This is a portability correction
to the replay pin, not a runtime change. Historical manifests, archives, scores,
and gold remain unchanged. All suites passed in a fresh copy without metadata.

## Replay

```sh
PYTHONPATH=src python tools/text_inquiry_evaluation.py \
  --output-dir /tmp/nabt-text-evaluation-rerun
```

An explicit data copy can be selected with `--data-root`; it must contain the
unchanged frozen input files. `--code-freeze` selects a recorded runtime
manifest; the default is `code_freeze_reserve20_portable.json`. Use
`--suite controlled --partition reserve20` for a focused replay;
the fact that this was once a reserve does not make a present rerun heldout.

The tool verifies input and runtime hashes, writes results to the selected
separate directory, and exits nonzero if a scored kernel/probe check fails.
Existing historical evidence is not overwritten. See
[artifact_manifest.json](artifact_manifest.json) for checksums of the published
evaluator-owned evidence files.
