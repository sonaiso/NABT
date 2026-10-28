# Recorded execution attempts

These are distinct attempts; no failed result was overwritten or relabelled.

- `pre-gold-full-check-2463c6c`: the initial full `make check` ran 2710 unit
  tests (2647 passed, 63 skipped), then stopped at the historical completion
  oracle's archive-integrity guard before any v3 gold execution. Its strict
  archive was truncated after capture. `archive-diagnosis.json` records the
  exact prefix and SHA reconstruction proof; damaged and intact comparison
  archives are retained. Source contents did not diverge. A host synchronization
  race is suspected; the particular writer was not proved.
- `first-matrix-ab8640b`: resumed the remaining Make prerequisites with the 26
  already completed targets marked old. The separate build-order repair's five
  tests passed. The historical oracle then passed without changing its guards.
  This attempt reached the **first actual v3 matrix execution**: original
  projections 158/161, stored positive goals 90/109, negative controls 52/52,
  three oracle-relative false-authorization flags. All frozen source/native and
  before/after checks passed. The three rows contain the independently confirmed
  A116 gold typo documented in `../gold_erratum_v1.json`; raw evidence remains
  unchanged. Every subsequent evaluation is exposed.
- `exposed-review1-eee0016`: all 114 targeted checks passed, the reviewed matrix
  passed 161/161 contracts with 90/109 positive goals, 52/52 negative controls,
  zero false authorizations and 45 complete chains. All 161 producer reports
  are identical to their first-run counterparts. Original projections remain
  158/161 alongside the corrected projections. The resumed Make check and its
  final integrity recipe exited 0; the command records the 57 previously
  completed root prerequisites. No gate was waived or its assertion weakened.

`measured_summary.json` provides the measured denominators and the 19 misses.
`entropy/` contains independently recomputed descriptive coupling measurements
at the exact measured commit; entropy is not a quality/completeness threshold.

Each directory includes the exact command, elapsed time, exit status, original
log SHA, gzip-compressed stdout, artifact inventory, and outcome archive.
`outcomes.tar.gz` preserves generated outcomes and raw traces. Redundant
historical source/code snapshot tarballs are normally inventoried by SHA instead
of duplicated; the two archives involved in the truncation diagnosis are
explicitly retained as additional files. The v3 freeze and result also have
direct copies for review.

The local host required a readlink compatibility shim for Lean's lookup of its
own executable. It redirects only `/proc/<own-pid>/exe` to `/proc/self/exe`.
This is an environment assumption, not a proof rule or kernel override. The
runtime, standard library, operating system, and compiled executables remain
trusted execution assumptions. Normal CI uses its pinned Lean installation.
