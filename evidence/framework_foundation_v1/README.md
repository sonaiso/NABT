# Framework foundation runtime and review 2

This is a new registered runtime snapshot for the shared A116 foundation. It
does not replace `evidence/arabic_completion_v6`, republish a blind experiment,
or alter historical cases, gold labels, thresholds, denominators, or allowed
failure signatures.

The exact authoritative inventory contains **101 files**: `pyproject.toml`
and all authoritative `.py`, `.json`, and `.txt` files under `src`. The two
added paths relative to the preserved 99-file v6 snapshot are
`src/nabt/foundation.py` and `src/nabt/data/framework_foundation.json`.
Thirty-eight inventory records changed or were added in the first snapshot. Build metadata, tools,
Lean sources, test files, unrelated scratch files and credentials are not
part of this runtime archive. Lean proof-catalogue and evaluator identities
are recorded and verified by their separate existing checks.

The archive was captured after the runtime and architecture owners declared
their source changes stable. Capture selected tracked authoritative files
plus the two explicitly reviewed new runtime files, rejected additional
untracked runtime files and symlinks, and checked the complete inventory and
bytes again after writing. The stored working-tree status is restricted to
the authoritative inventory. `verify_code_freeze` remains unchanged and
requires exact inventory equality and matching source bytes.

The first observed foundation snapshot remains intact. Review 2 changes only
`src/nabt/foundation.py` and `src/nabt/data/framework_foundation.json` relative
to that snapshot. The runtime correction prevents a transform binding from
cutting through an original source cluster: a slice of `قُمْتُّ` ending before
the final shadda cannot masquerade as the complete surface `قُمْتُ`.
The registry also inventories all Python module paths and public declarations.
Both reviews retain the same 101-file authoritative runtime inventory.

| Artifact | SHA-256 |
|---|---|
| Current `code_freeze_v2.json` | `a192d915f933a8f98ddb4d166f741be4ab976d34cc2c13be71eb940f08ca06e4` |
| Current ordered runtime inventory | `36fba6536d27a077bba568c024ac0eabb22c1defbaec17ae45c665083e361766` |
| Current `code_freeze_v2.tar.gz` | `6da895ca88448dd9261f6acf0e5fe244fef311ef6dfe785acda9307a6b928598` |
| Current `regression_policy_v2.json` | `20b8eb82e9df6dd52905d1dd3bde2716fec819302b9a538a6f0965aa42dde275` |
| Preserved `code_freeze_v1.json` | `00b06260322f06a6394b3a1164aa78833758a86f1c71c232433d1ab786077447` |
| Preserved first ordered runtime inventory | `9f497aa3f3083d7e8073b77e21599445add23ef139b3c419372178be91a954e9` |
| Preserved `code_freeze_v1.tar.gz` | `168c7a1a90761cb0d90c90f4f0f0f4ce80e955813448f7c519696b94b20c6f2f` |
| Preserved `regression_policy_v1.json` | `08928857043652240209630b5e424ba7c6c8d28cbb8f02c4390d9caee5749d65` |
| Preserved v6 manifest | `31bd37d919364742033a08ab4cb557e93b92280539dd7a55364763cae236dfec` |
| Preserved v6 policy | `5e73cfdae07cdb60a2f93c8cc9961a9ee283d85471f24b5b61eabcb3c3647657` |

The current version selector is `framework_foundation_v1_review2`. Word, morphology,
inflection, construction, discourse, governor, and construction-package
verifiers add explicit new pins while retaining all historical registrations.
Current selectors use this manifest; supplying a historical manifest against
the current files still fails. A caller-recomputed hash cannot register a
runtime in these pinned evaluators.

Both foundation regression policies preserve the complete v6 `suites` object. The new
`tools/framework_foundation_gate.py` applies the same exact-case inventory,
failure signatures, raw-journal requirements and zero-false-acceptance rules
to the new runtime identity. Tests explicitly reject fabricated denominators,
missing cases, false acceptance and the old runtime under the new policy.

`tools/framework_foundation_postreview.py` is a separate continuation for the
same published Arabic holdout: 36 cases and 63 questions. The v7 tool remains
unchanged. The new continuation changes the runtime pins and inventory count,
records the new gate identity, and retains all material checks and the prior
documented H18 checker correction. Registration alone does not establish a
successful replay; complete raw observations and certificate replay remain
required.

The active directed regression runner is
`independent_oracle/run_regression_v1.py`. It reuses the unchanged historical
material: 24 directed cases, 22 fixed obligations, two conditional provenance
probes and 29 questions, with six separate source counterexamples and four
questions. Historical runner files and freezes remain intact. This is a
regression continuation over published material, not a new blind evaluation.

`independent_oracle/runner_freeze_v1.json` pins exactly 74 dependencies, including
the current evaluator helpers, gate, policy, Makefile and CI workflow. Its
SHA-256 is `bfceeccfe85fae87156a3be23c2e85af58db138fa0b63b34934c6db6195f9b8e`.
The predecessor is the preserved v6 review-2 runner freeze with SHA-256
`6e8dde893aa919dec0dd23e37a7882b228d45d977743526ef2178483599fabb3`.
The verifier checks complete dependency inventory equality as well as file
hashes and explicit predecessor lineage. Generation uses fixed reviewed paths
and refuses to overwrite an existing freeze; a recomputed caller manifest
does not authorize a different runtime or omitted dependency.

The focused migration checks passed **18/18 tests in 27.668 seconds**:
`tests.test_framework_foundation_freeze`, `tests.test_rational_inquiry_freeze`
and `tests.test_completion_v6_gate`. These cover current registrations,
preserved historical hashes, rejection of older freezes against current source,
unchanged regression policies and directed-runner evidence integrity. They
do not report a new linguistic success rate.

Reproduce the broader migration checks with:

```sh
PYTHONPATH=src:. python3 -m unittest \
  tests.test_framework_foundation_freeze \
  tests.test_rational_inquiry_freeze \
  tests.test_recursive_source_bridge \
  tests.test_arabic_evaluation \
  tests.test_arabic_coverage_package_verifier \
  tests.test_text_evaluation_safety \
  tests.test_completion_v6_gate -v
```

Full release verification is still `make check`; these migration tests do not
substitute for the production benchmarks or broaden their coverage claims.
