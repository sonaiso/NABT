# Licensed inference evidence v1

This directory describes the finite `nabt.licensed-inference.v1` source reader,
its Lean proof contracts, source motivations, and measured boundaries. It does
not assert complete Arabic comprehension, faithful formalization of whole books,
or the truth of source assertions in the external world.

- `source_links.json`: pinned eight-source, sixteen-passage review; scholarly
  interpretation is distinct from exact byte replay.
- `sources/shakhsiyya3_condition_profile.txt`: exact retained user-provided
  source paragraphs 574 and 576; this profile is documented, not activated as
  a generic converse-of-conditional rule.
- `original_recheck.json`: scoped optional replay against the original artifact,
  when available; routine fresh-clone checks replay retained bytes only.
- `proof_catalog.json`, `proof_links.json`: actual compiled declarations and
  references; nineteen new declarations, with no new normalized duplicates.
- `grammar_link_summary.json`, `mantuq_proof_links.json`,
  `linguistic_proof_links.json`: current links for existing layers. Earlier
  versioned directories remain unchanged.
- `axioms.json` and `axioms.log`: actual kernel audit of all 1422 declarations.
- `conformance.json`: 410 source/query executions and 273 calculation-only
  aggregation fixtures. `conformance_before_transport_review.json` records the
  earlier native version; it is not evidence for the hardened binary.
- `independent_gold.json` and `independent_freeze.json`: independently authored
  fixed 38-case denominator, before the new implementation was read or run.
- `independent_initial.json`, `independent_revision.json`, and the intermediate
  reports: retained history of observer correction and native transport review.
- `independent_final.json`: final hardened-binary run, 37 pass / 1 fail /
  0 unmeasured; the positive out-of-vocabulary case remains a failure.
- `validation.json` and `targeted_tests.log`: targeted execution receipt;
  full repository and CI gates are separate runs, not inferred from this file.

Reproduce with the pinned Lean toolchain:

```bash
make -f Makefile -f integrations/grammar_catalog.mk \
  -f integrations/mantuq_inference.mk -f integrations/linguistic_truth.mk \
  -f integrations/licensed_inference.mk formal check LAKE=/path/to/lake
```

Generated replay outputs belong under `EVIDENCE_DIR`; the gate compares stored
receipts and never silently overwrites them. Native binary hashes describe the
recorded build environment and may differ in a fresh build; the source and
proof identities are replayed locally. The direct JSON/file adapter has tests,
not a general Lean parser/compiler refinement theorem.
