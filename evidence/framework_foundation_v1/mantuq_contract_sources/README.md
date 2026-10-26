# Preserved Mantuq benchmark authoring policy

`AGENTS.v1.md` contains the exact original `AGENTS.md` bytes named by the
immutable `evidence/mantuq_inference_v1/benchmark_gold.json` contract ledger.
Its SHA-256 remains
`1206aa452a00f5a3280123500a08c1c4be35e6191552eccd7526e57e9cbfa14b`.

The current root `AGENTS.md` adds the shared A116 foundation requirements.
This control-document change does not change the benchmark's structured
premises, expected outcomes, counts, profiles, scoring, or success condition.
The original gold remains byte-identical with its original digest and all
34 cases. This is a replay of a known diagnostic, not a new blind evaluation.

`../mantuq_benchmark_contracts_v1.json` records this one reviewed migration.
The benchmark code pins that manifest, checks the retained original policy
against the gold's original hash, and separately checks the current policy
against its reviewed hash. The four other historical contracts are still
checked at their original paths with their original hashes. A changed
manifest, retained policy, current policy, or formal contract fails closed.
The execution evidence records both bindings before and after the run.

Any later policy or contract change requires an explicit reviewed migration;
neither a caller-provided manifest nor a matching case count grants an exception.
