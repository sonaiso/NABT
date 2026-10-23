# Text morphology release verification

`validation.json` records the successful bounded release check and its limits. Full logs and result files are stored once in `verification-records.tar.gz`; `verification-records-manifest.json` gives every member's byte length and SHA-256. The archive contains 29 files, including the first failed check, the complete final check, the final evaluation/conformance/axiom records and the installed-wheel smoke evidence. The wheel binary and earlier runtime archives are not duplicated.

## Recorded result

- The final `make check` exited successfully: **484 tests**, **421 audited theorems** (26 in `Nabt.TextEvidence`), with only `Classical.choice`, `Quot.sound` and `propext` observed. There are no permitted project axioms.
- Text-evidence correspondence checked **8** kind masks, **64** receipt-activation masks, **121** cue lists of length at most four, **426** deletion checks and **426** duplicate checks.
- The frozen authored text-morphology evaluation passed **40/40** cases: **16/16** positive properties and **24/24** boundary properties. Eighteen later adversarial test methods are recorded separately; they did not enlarge or rewrite the original forty-case score.
- The wheel smoke ran outside the checkout and confirmed new-text reading, exact-source report replay, rejection when the required lexical source is removed, and the existing descriptor reader.

## Integrity and histories

The runtime is the existing `../code_freeze_v1.json` and `../code_freeze_v1.tar.gz`: all **46** authoritative source/configuration/data files matched at release-record construction, including archive-member bytes. `verification-source-manifest.json` separately pins the formal, test, tool, build and example sources. The implementation is committed at `90b733d5af437f3e53b927acba2f2f73e00571a1`; the older freeze baseline is preserved as recorded. The evidence commit is assigned after these release records are written.

The new evaluator's **47-file** snapshot contains those same 46 runtime files plus `tools/text_morphology_evaluation.py`. Its different snapshot hash is intentional, and its runtime projection was checked against the release freeze.

The first full check had one failure: `test_incomplete_runtime_freeze_is_not_an_override` used the historical morphology freeze, so the changed `pyproject.toml` failed its pin before the intended exact-inventory guard. One fixture path was changed to the declared text-morphology freeze. The rejection assertion and runtime were unchanged. The failed log is preserved alongside the successful rerun.

The separate pre-release adversarial review found damm/kasr tanwin accepted on an incompatible alif carrier. The reader now rejects it with `INVALID_ALIF_TANWIN` before issuing a noun receipt. That earlier finding, its first/final code snapshots and the unchanged forty-case material remain in the parent evidence directory.

## Coverage limits

The earlier word profile remains **27/30** (positive capabilities **12/15**, misses `w15`, `w16`, `w17`); morphology descriptors remain **39/43** (documented boundaries `m12`, `m13`, `m32`, `m33`). Governor coverage remains **0/12** in the original scope, **4/5** in its constrained scope and **0/6** for original excerpts. Arabic-syntax coverage remains **0/40** standalone, **8/12** in the declared supplement and **0/8** original excerpts. The text-inquiry regression retains **60/60** controlled episodes and **126/126** query checkpoints, while the twelve natural spans have **0/12** confirmed semantic successes. Passing their regression gates does not erase these gaps.

These are authored bounded properties and public regressions, not an untouched external Arabic corpus, an autonomous learning experiment or a full parsing proof. Lean proves conditional evidence contracts. Python parsing and linguistic activation remain external to that proof. A shape or adjacent governor cannot supply missing lexical classification; a noun sign does not by itself establish inflection, a syntactic role, or a semantic derivation class. The pinned upstream repositories were consulted but not rebuilt as part of this check.

## Reproduction

Use the toolchain in `formal/lean-toolchain` (Lean 4.34.1) and a new output directory. Existing evaluation output is intentionally protected against overwrite:

```bash
make check LAKE=/absolute/path/to/lake \
  EVIDENCE_DIR=artifacts/local/text-morphology-reproduction/verified \
  ARABIC_EVALUATION_DIR=artifacts/local/text-morphology-reproduction/verified/arabic-regression
```

The Makefile defaults to the explicit `text_morphology_v1` runtime pin. Historical pins remain available through their evaluators' supported options. To inspect the archived run, verify the archive checksum from its manifest, list its members with `tar -tzf verification-records.tar.gz`, and extract into a new directory. Each archived member must match its manifest length and SHA-256.

The archive is deterministic for these fixed record bytes: sorted relative paths, USTAR regular files, mode `0644`, zero mtime/uid/gid, empty owner names, and gzip level 9 with zero mtime and an empty filename. Two serializations were compared byte-for-byte. Result timestamps and local timings are preserved as observed, so a fresh experiment is not expected to reproduce the same report hashes.
