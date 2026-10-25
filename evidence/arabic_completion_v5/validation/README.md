# Validation receipts

`summary.json` records the completed local validation of the pinned94-file
runtime. `make_check.log` includes the full unit, conformance, source replay,
native, and unchanged-regression gate output. Strict linguistic failures remain
visible; a regression gate is not a universal-language success flag.

The expanded `release/`, `installed_package/`, and `installed_interfaces/`
records are preserved in `../validation_bundle.zip`, including raw output,
wheel bytes and individual code snapshots. Extract it from the repository root:

```sh
python -m zipfile -e evidence/arabic_completion_v5/validation_bundle.zip .
```

`../validation_bundle_manifest.json` records every member's SHA256 and size.
No credentials or private repository contents are included.

`pre_freeze_incomplete_attempt.json` records an incomplete exploratory test run;
it contributes no passing-test count. The completed, pinned `make check` run
supersedes it without erasing the earlier observation.
