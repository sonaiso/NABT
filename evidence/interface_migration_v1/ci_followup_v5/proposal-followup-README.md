# Follow-up evidence for optional learner import order

`proposal-admission-tests.log` is a **fresh targeted rerun**, captured directly
from the process after the earlier targeted run's console output had not been
saved as a file. It is not a reconstruction or replacement of that earlier run.
The earlier console result was 38 tests in 13.543 seconds; the preserved rerun
reports **38 tests in 14.736 seconds, return code 0, no skips or failures**.

Exact command from the repository root:

```bash
PYTHONPATH=src:. /tmp/nabt-neural-ci-review/bin/python -m unittest tests.test_interface_migration_audit tests.test_foundation_architecture tests.test_neural_morphology_model tests.test_neural_morphology_data -v
```

The interpreter was Python **3.12.14**. `proposal-admission-tests.json` retains
its executable digest, exact argv, environment override, timestamps, raw log
digest and input digests before and after execution. The implementation and
test input files did not change during this rerun. No complete release gates
were rerun as part of this follow-up.

`proposal-differential.json` is a byte-exact copy of the earlier 11-input
comparison from `artifacts/local/proposal-admission-followup/differential.json`.
It compares the published parent `3727825da5dde66f9f69909128626c1915edb484`
with the import-order correction using identical deterministic toy weights.
The public signature and all 11 proposal results were unchanged.

The executable replay script was retained **after** that interactive comparison.
Its validation reproduces the same result bytes and is separately recorded in
`proposal-replay-validation.json`; it is not another independent benchmark.

```bash
PYTHONPATH=src:. /tmp/nabt-neural-ci-review/bin/python evidence/interface_migration_v1/ci_followup_v5/replay_proposal_differential.py --output artifacts/local/proposal-admission-followup/replayed-differential.json
```

Choose a new output path for another replay: the script refuses to overwrite
existing evidence. It checks the parent and corrected implementation digests
before computing proposals. The test demonstrates admission order and proposal
stability; it does not add linguistic coverage, new training or proof authority.
