# Source-linked proof identities and retrieval routing

The source catalogue proposes relevant rules. A proposal score, model output,
database row, quotation or theorem name does not establish a grammatical
premise. Existing NABT law checkers remain the authority for their explicitly
bounded conditional transformations.

`formal/Nabt/RuleRouting.lean` adds three composition theorems:

| Declaration | Exact scope |
| --- | --- |
| `schedule_exact` | Filtering ranked IDs to an installed inventory, appending the whole inventory and deduplicating preserves exactly its membership. |
| `checked_schedule_exact` | Filtering that schedule with a fixed checker accepts exactly the same IDs as checking the full inventory. |
| `exhausted_budget_not_complete` | A budget smaller than the schedule length cannot certify a complete scan. |

These are general list theorems. They do not prove that an inventory contains
all Arabic rules, that source interpretation is faithful, or that a free-text
sentence supplies a law's premises. Those are separate obligations. A full
budget is necessary but not sufficient for the Python router's conditional
completion status: missing premises, partial results and evaluation errors
also keep that status incomplete. No source-transfer theorem is duplicated:
`Nabt.BookCoverage.complete_readings_transfer` remains the composition point
when independently established exhaustiveness, fidelity and enumeration
premises are available.

## Canonical theorem references

`formal/ExportProofCatalog.lean` inspects actual compiled theorem types and
proof expressions. It exports structural ASTs after removing binder names and
metadata and renaming universe parameters by their declared position. The
Python tool hashes that encoding, retains direct proof/type dependencies,
source module hashes, source ranges and transitive foundational axioms, and
groups identical encoded statements. It fails on missing/duplicate manifest
entries or unexpected axioms.

This detects **identical normalized statement ASTs**, not all logically or
definitionally equivalent propositions, and never semantic identity of Arabic
rules. A shared witness or similar wording is not a reason to merge rules.
Public theorem names are preserved. Within a group the unique dependency sink
is preferred as canonical; otherwise a documented lexical tie break is used.

The present catalogue contains 1,372 advertised declarations and 1,369 distinct
normalized statement ASTs. Three existing names are retained as aliases of
canonical proofs:

| Public alias | Canonical proof |
| --- | --- |
| `Nabt.TextEvidence.noun_sign_does_not_determine_construction` | `Nabt.Morphology.noun_unknown_keeps_both` |
| `Nabt.SourceSemantics.execution_in_world` | `Nabt.VerifiedReading.source_to_execution_entails` |
| `Nabt.MaqayisDenotation.ilm_ambiguity_retained` | `Nabt.MaqayisRules.root_does_not_determine_sense` |

The first alias now calls its existing canonical proof rather than proving the
same statement again. The other two already delegated. None of these alias
names is counted as an additional distinct statement.

## Reproduction

```sh
python3 tools/proof_catalog.py --output evidence/grammar_catalog_v1/proof_catalog.json
python3 tools/proof_catalog.py --check evidence/grammar_catalog_v1/proof_catalog.json
python3 tools/check_axioms.py --output artifacts/local/proof-catalog-axioms.json
python3 tools/check_rule_routing.py --output artifacts/local/routing-conformance.json
python3 -m unittest discover -s tests -p test_proof_catalog.py -v
```

All three tools accept `--lake /path/to/lake`. The pinned Lean toolchain is
read from `formal/lean-toolchain`; `proof_catalog.py` rebuilds current sources
before inspection. The stored JSON is a review snapshot, not proof authority.

The finite routing conformance suite compares Python with Lean for all 341
rankings of length zero through four over three installed IDs and one unknown
ID, including repetition. It additionally checks 1,705 budget cases and 2,728
checker subsets. This is finite implementation evidence; it is not a
machine-checked refinement theorem for Python, nor an Arabic benchmark.
