# Nominal release validation

Version 0.11.0a1: 576 tests, 520 audited theorems, 184/184 authored independent cases, full make check exit 0, and installed-wheel correspondence.

validation.json records exact runtime and verification inputs. verification-artifacts.tar.gz retains full logs, reports, and both documented wheel builds; verification-artifact-manifest.json lists every member and digest. The first 15 CLI smoke checks cover runtime-identical package files. The final rebuild binds distribution metadata to the final README. Prior corpus coverage gaps remain visible.
