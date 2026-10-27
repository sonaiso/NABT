# Full-source acquisition and qualified-cue release

Base: `f7e7ed8adf4db17b9cd2935a22b4014b62a3c6d8` (PR #47).

This is a new runtime/evaluator identity. Historical material, answers, policies,
failures and archived reports have not been overwritten. See
[the Arabic report](../../docs/SOURCE_ACQUISITION_PROGRESS_AR.md) for the laws,
independent denominators and unresolved acquisition bridges.

- `code_freeze_v1.json` / `code_freeze_v1.tar.gz`: the 102-file runtime snapshot.
- `runtime_migration.json` / `.patch`: the explicit previous-to-current change.
- `independent_oracle/runner_freeze_v5.json`: final evaluator dependency snapshot after observed execution;
  it explicitly does not claim to precede the runtime’s first execution.
  Earlier runner and catalogue attempts remain under `runner_attempts/` and
  `catalog_attempts/`, with their reasons. Runner v3 executed `make check -o test`
  successfully but failed the 2888-test gate (two failures, three errors);
  its 292 exact dependency files and the raw gate outcomes are preserved.
- `catalog_references/`: actual compiled-axiom audit and derived catalogue of
  1611 declarations, including 32 additions. The count includes general laws
  and installed-inventory specializations; it is not an Arabic coverage score.
- `local_toolchain/`: observed local compiler discovery workaround and controls.
  It changes current-process executable discovery only, not the Lean kernel.
- `verification.json`: completed commands, exact logs, outcomes and limitations.
- `verification_bundle/`: byte-preserving storage of all recorded current-run
  inputs, raw responses, measurements, logs and retained attempts.
- `verification_attempt_1/`: the complete first run, with its successful
  `make check` and failed 2888-test attempt (two failures, three errors).
  `attempt.json` records the causes and original paths. Its 128 original files
  were restored byte-for-byte; it is not overwritten by the corrected run.
- `operational_attempts/02_output_collision/`: an early replay refused a
  pre-existing output file. Its log, gate command, colliding file and full
  output inventory are retained. Final gates use a separate empty directory.

Restore to a **new** directory:

```sh
python evidence/source_acquisition_v1/pack_verification.py restore \
  evidence/source_acquisition_v1/verification_bundle \
  artifacts/local/restored-source-acquisition
```

The manifest verifies every restored file against its original byte length and
SHA-256. Gzip members retain their original bytes; reports are not regenerated
or recompressed during restoration. Relocation is for inspection; validators
whose receipts bind an original repository-relative path require that layout.
The bundle has byte-preservation authority only, not linguistic authority.

Reproduce the implementation checks with the pinned Lean toolchain and Python
dependencies:

```sh
make source-acquisition-conformance
make check
make test
make -f Makefile -f integrations/grammar_catalog.mk \
  -f integrations/mantuq_inference.mk -f integrations/linguistic_truth.mk \
  -f integrations/licensed_inference.mk grammar-catalog proof-catalog \
  routing-conformance mantuq-inference linguistic-truth licensed-inference
```

`source_row_extraction_kernel_proved` and field-extraction claims have a narrower
meaning than correctness of corpus annotation. The source edition, metadata
interpretation, free-text acquisition of roles/scopes, tawatur, motives, world
truth and whole-Arabic completeness remain separate obligations. No site update
is deployed by this package.
