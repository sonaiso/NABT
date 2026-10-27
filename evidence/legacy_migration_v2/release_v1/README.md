# Release v1 byte-preserving evidence

The manifest and numbered ZIP archives restore every captured input byte.
Archives are at most 20 MiB; gzip headers/bodies are segmented and repeated
objects deduplicated without rewriting any original compressed file.
`verification.json` keeps gate scopes separate. Test totals overlap and are
not added together. Earlier seven-mode receipts remain development evidence;
compact replay is local and does not establish a production deployment.
The original main log retains 3040 run / 3023 passed / 17 skipped. The exact
17 skipped test IDs passed in a separate native supplement. The manifest keeps
both raw runs: 3040 distinct tests were verified across two phases, not a
rewritten zero-skip main run. The packager does not run tests or grant authority.

Verify again with the archived `capture_tools/package_legacy_wave1_release.py`
(or the external original): `python package_legacy_wave1_release.py --verify
/path/to/release_v1`. It validates each archive/object/file hash and restores
file bytes in memory. No input or frozen source is modified.
