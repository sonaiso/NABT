# Training readiness and first CPU execution

This directory records a resource survey, a fixed public-development experiment,
and its actual learned parameters. It is not an Arabic completeness benchmark.
The [Arabic execution plan](../../docs/TRAINING_PLAN_AR.md) gives the staged work,
source/world distinctions, acquisition backlog and compute gates.

## Observed execution

| Measurement | Result | Scope |
|---|---:|---|
| Source cases | 18 | Existing 14 pilot cases plus 4 premise ablations |
| Training candidates | 70 | 14 public source cases; five candidate certificates each |
| Validation candidates | 20 | 4 public relation/multipremise cases kept together |
| Native candidate measurements | 90/90 | 18 originals accepted, 72 altered certificates rejected |
| Validation top-ranked certificate accepted | 4/4 | Tiny public development experiment; shared vocabulary |
| Fixed adversarial input-order baseline | 0/4 top-ranked | Original certificate intentionally last, fixed before training |
| Current deterministic proposer | 18/18 accepted originals | No demonstrated improvement over this stronger baseline |
| First-run logistic loss | 0.517519 → 0.032859 | Epochs 1–120, training data only |
| First-run optimizer time | 0.064690 seconds | CPU logistic SGD, **not** LLM training time |
| Native attempt P50 / P95 | 0.048871 / 0.112597 seconds | First-run measurement on this machine, includes process launch |
| Fresh ranked inference replay | 20/20 attempts measured | Integrated run; all 4 validation outputs rechecked by Lean |
| Linguistic review queue | 36 cases | Four categories; zero automatically admitted Arabic SFT examples |
| Joint source/root/template split | UNMEASURED | Root/template annotations absent; source-only corpus is one group |

`first_run/` is the original run at code commit `e35cb99`, preserved unchanged.
`integrated_run/` was run at `0fe5129` after adding fresh inference replay; it does
not replace the first run. Both have actual weights and loss curves. All 90
candidate checks are retained per run; replay adds 20 checks, not 20 new cases.
The optimized score is never a verdict. A test constructs a forged proof with
the **same feature vector** as a good certificate: the ranker cannot distinguish
them, but Lean rejects it and selection proceeds to the independently verified
certificate. Setup failure keeps 90 null labels and stops optimization.

`source_learning.json` replays NABT's existing source acquisition experiment:
6 rule statements, 3 observations, 1 lexeme, 0 independently held-out examples.
The hypothesis space shrinks 8→4→2→1; withdrawal restores an alternative and
replay restores the prior result. This is conditional finite acquisition.

`native_build.json` records 57 current Lean modules checked using the official
Lean 4.34.1 shared library and the repository's documented public embedding
driver. All source hashes were rechecked, all compiler exit codes were zero,
and three native binaries were built. This is direct compilation evidence;
it does not claim a local Lake run. CI runs the normal pinned Lake path.

## Files and replay

- `resources.json`: seven freshly inspected upstream repository heads and read
  file blob identities. No upstream runtime imports or dependencies added.
- `external_intake.json`: actual tree sizes and concrete data-quality findings;
  these are not imported/qualified linguistic training pairs.
- `protocol.json`: fixed split, optimizer, candidate mutations and stop rules.
- Each run: independent source/query inputs, all candidate certificates and
  receipts, learned weights, loss curve, environment, code hashes and counters.
- `integrated_run/inference_replay.json`: fresh checker results in learned order,
  retaining original indices and every candidate attempt.

```bash
PYTHONPATH=src NABT_VERIFIED_READING="$PWD/formal/.lake/build/bin/verifiedReading" \
  python tools/train_certificate_ranker.py --output-dir artifacts/local/my-new-run
```

An existing output directory is rejected. Reproducing the experiment should
reproduce labels, ordering and weights under the same implementation; timestamps,
timings, executable hashes across platforms and run digests need not match.
This experiment has no hidden linguistic test, neural model, GPU, LoRA, RLVR,
independent human adequacy review or external-world truth measurement. The
corresponding flags remain false or unmeasured. Historical evidence is retained.
