# Construction release evidence: 0.14.0a1

The final runtime is `constructions_v2`, with 74 frozen source/configuration
files. This directory preserves the complete release checks, pinned source
manifest, installed-package checks and prior attempts without overwriting them.

- `make-check-command.json` records the actual command, timestamps, environment,
  exit 0 and unchanged verification inputs. `make-check.log` records 887 passing
  tests and every required gate. `checks/` contains its unmodified outputs.
- `preflight/` records separate successful formal, complete-table conformance and
  local numeric-kernel benchmark commands. Benchmark timings are not language
  understanding measurements.
- `package/` is the final package built from the corrected README, with 26 CLI
  checks, 31 commands, 74 source/configuration files and 75 installed package
  files (73 runtime files plus two documentation files).
- `attempts/package-readme-first/` preserves the earlier build whose README
  misdescribed the reason for historical P26 deferral. The final wheel changes
  only METADATA and RECORD; all package payloads are byte-identical.
- `attempts/sandbox-first/` preserves the first make-check attempt: all 887 tests
  passed, then Lake could not locate its configuration in that execution
  sandbox. The identical build and full gate passed outside it without source
  edits. It is not the successful full-gate record.

Construction evaluation remains 71/86 (30/43 positives), with 15 exact named
coverage gaps and `strict_pass=false`. The old discourse suite remains 57/86,
with substantive questions declining from 24/45 to 23/45. P26 has complete
reference bindings but lacks construction/class evidence in a retained parse.
The comparison records preserve every earlier score and raw/code snapshot.

The historical query-selection defect is covered by six unchanged regression
tests in the full suite. Rejected or incomplete alternatives cannot select a
query. Conditional Lean contracts and finite conformance do not prove the
whole Python parser, unrestricted Arabic, source truth or world truth.

`validation.json` links actual evidence and its limits. The outputs and source
manifests record exact bytes without a recursive self-hash or a claimed commit
SHA that would have to contain itself. Git and the PR carry the release identity.
