# Lifecycle v1 measured evidence

- `first_e2d0c2f.zip`: the first forty-scenario lifecycle evaluation, its
  committed freeze, ordered prerequisite replays, complete gate log, static
  architecture checks and three explicitly separate clause demonstrations.
- `first_observations.json`: concise measured counts, identities, comparisons
  and archive hashes. The 200 productive-clause raw payloads equal prior review1.
- `interrupted_prerequisites_e2d0c2f.zip`: an earlier interrupted prerequisite
  attempt. It stopped during exposed v3 evaluation and did not reach the
  lifecycle freeze or matrix; its ATTEMPT_STARTED result is retained unchanged.
- `release_e2d0c2f.zip` and `release_observations.json`: successful original
  `make formal check` in an isolated implementation checkout, retaining all raw
  reports and generated code snapshots. General unit discovery ran 2,835 of
  2,890 tests with 55 documented skips; no new lifecycle test was skipped.
  Post-measurement framework conformance on `57f80e6` is identified separately.
  Exact-head remote CI is a separate prerequisite, not inferred from this log.
- `ci_repair_692c3a4.zip` and `ci_repair_observations.json`: the eight failed
  checks on `d9ce75b`, both original acquisition artifacts, and local validation
  of the test-profile repair. Native-required conformance passes 54 tests with
  no skips. A genuinely shallow Python-only checkout passes 2,461 of 2,658
  tests with 197 explicit skips. A missing-native negative control fails the
  dedicated gate before freeze. Kernel, runtime, evaluator and gold are unchanged;
  neither failed acquisition job reached lifecycle freezing or the forty cases.

Each ZIP has an `archive_manifest.json` with byte counts and SHA-256 digests.
Only the lifecycle matrix is first execution in the successful archive; the
historical matrices are exposed replays. The independently authored new gold
was frozen before implementation but became exposed afterward, not blind.
The reviewer performed read-only code/contract inspection, not this execution.

The 40 scenarios, 79 episode steps, 73 verification pairs, 7 auxiliary historical
steps, 6 native error controls and 50 installed adapter targets are distinct
denominators. The source graph is supplied or installed, not authenticated
external provenance. See `docs/EVIDENCE_LIFECYCLE_V1_RESULTS_AR.md` for scope.
