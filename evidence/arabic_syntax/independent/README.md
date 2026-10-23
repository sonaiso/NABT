# Independent bounded-Arabic reading evaluation

**The first frozen implementation completed 0/40 standalone-Arabic episodes,
8/12 episodes in a separate declared-profile supplement, and 0/8 original book
excerpts.** Its safe refusals are not counted as understanding. The full report
is [ARABIC_SYNTAX_EVALUATION.md](../../../docs/ARABIC_SYNTAX_EVALUATION.md).

## Data and chronology

- `episodes.json`: forty manually authored episodes, eight in each of five
  strata; 43 question checkpoints.
- `scope_episodes.json`: twelve additional episodes authored after the public
  profile contract was supplied, before implementation exposure; 11 questions.
- `real_excerpts.json`: eight exact, new UTF-8 intervals from the already
  packaged grammatical books, with parent hashes, lines, page markers and
  separate surrounding context. These are selected examples/quotations, not
  unseen books or a random sample of ordinary prose.
- `manual_oracle.json`: hand-authored interpretations of 65 distinct source
  documents. No production reader generated these interpretations.
- `protocol.json`, `evaluator_freeze.json`, `evaluator_preopen_review.json`, and
  `chronology.json`: what was fixed before opening, subsequent checks, and the
  two premeasurement evaluator corrections.
- `gold_review.json` and `independent_gold_review.json`: disclosed linguistic
  reviews before the new runtime was run. Original corpus files are unchanged.
- `dataset_validation.json`: exact source bytes, line numbers, surrounding
  context, and disjointness from the previously published twelve intervals.

The original 40 cases were not rewritten to match the narrower implementation.
The separate supplement makes that narrower contract measurable without
replacing the original denominator. Procedural separation between agents kept
the selected inputs and annotations from builders until the code freeze; this
was not filesystem access-control isolation.

## Immutable results

- `first_results.json`: first new-runtime execution on snapshot
  `4662ac75ded649b9f1d5d4d0e152fa292e4b63e72e6ce55ec924bad9b65e6524`.
- `baseline_full_results.json`: the same frozen material on historical
  controlled-Arabic commit `fd5ebc582b63445cc3f9c60973e98c493e47c56b`.
- `baseline_reader_results.json`: the earlier unique-document baseline check.
- `detailed_counts.json`: counts derived from the preserved first result.
- `candidate_recall.json`: **post-opening exploratory analysis** of exact signed
  atoms in stored alternatives. Candidate presence does not license an answer,
  coherent full reading, or rule.
- `first_evaluator/`: original first-run scripts, including the exact
  independent source/certificate checker.
- `authoring/`: original authored data-building and validation scripts. Their
  historical absolute work paths are retained; the portable replay entrypoint
  below does not depend on those paths.

The runtime freeze and archive are in the parent directory. The first run
verified all 30 authoritative file hashes and the archive hash. No runtime
changes were made between that freeze and the recorded first result.

## Replay

From the repository root:

```sh
PYTHONPATH=src python tools/arabic_syntax_evaluation.py \
  --output-dir /tmp/nabt-arabic-replay
```

Use a new output directory. The tool verifies the published input manifest and
complete runtime freeze before execution. It does not overwrite historical
inputs or results. A deliberately changed runtime requires an explicit new
`--code-freeze`; it remains regression on public data, never a fresh heldout
evaluation.

The regression gate preserves the previously successful bounded cases, exact
source restoration, correct admitted claims and certificate replay. It **does
not** pass the roadmap's 300-episode coverage gate, establish general Arabic
comprehension, or establish the truth of the supplied text in the world.

Original book excerpts and derived source annotations retain the data terms in
[LICENSE-DATA.md](LICENSE-DATA.md). The rest of the benchmark and evaluation code
are newly authored project material under the repository's code license.
