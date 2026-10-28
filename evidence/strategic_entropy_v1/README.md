# Strategic coherence observations, v1

See [the Arabic analysis](../../docs/CODE_ENTROPY_AR.md) and the prior
[measurement contract](../../docs/CODE_ENTROPY_CONTRACT.md).

- `before.json.gz`, `after.json.gz`: identical static analyzer, immutable Git
  trees `a14332a` and `180c198`; inventories, locations, hashes, graphs, clone
  candidates and limits are included. Entropy is not a quality score.
- `traceability.json.gz`: source-matching stored formal catalogue, direct
  theorem projections, authored link denominators and five source files / 23
  exact passage identities. `reproduce_traceability.py` replays this observation
  using explicitly trusted catalogue APIs; it does not rebuild Lean.
- `inventory_regression.zip`: independent synthetic Git fixture comparing both
  immutable evaluator versions, source copies, script, receipt and log. Extract
  under `artifacts/local/<new-directory>` to retain the script's repository-root
  relationship; use another fresh such directory for reruns. No native fixture
  executes; overridden pins and scope are recorded.
- `acquisition-freeze.json`, `acquisition-regression.json.gz`: exposed replay of
  the original independent matrix, not a new held-out test or new language law.
- `gate_reports.zip`, `validation_logs.zip`: native/reference gates, exposed
  composition results, full tests and process receipt.
- `verification.json`: exact counts, implementation commit, artifact hashes,
  commands, preserved paths, environment and limits.

Historical evidence and current proof-reference selection are unchanged. Do not
merge representation accuracy, positive-goal coverage, link completeness and
formal theorem counts into one certification score. The local native execution
uses the previously documented host `/proc` path adapter; CI checks the pinned
Lean toolchain independently without that adapter.
