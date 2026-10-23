# Existing independent material: query-selection release comparison

This is a post-review regression comparison of the unchanged 86 independently authored discourse cases and 74 questions. It is not a new blind evaluation or an extension of the gold. All earlier material, source exclusions, results, adapter errata and code snapshots remain unchanged.

A read-only scan of the 74 saved v3 inquiries found no question whose first analysis was rejected while another viable analysis remained. The new query-selection defect is therefore directly tested by the separately frozen source-review material in `../query_selection_review/`. An unchanged score on these 86 cases demonstrates preservation of this bounded historical profile, not proof that this material exposes the reported defect.

Both runs use identical evaluator and evaluator-test bytes. The only evaluator changes are an approved v4 manifest/snapshot/archive pin, the CLI default snapshot, and the runtime to which the existing documented-boundary policy applies. All measurement/semantic-scoring functions are AST-identical; the exact 29-case-and-check boundary set is unchanged. No semantic policy or answer is supplied to runtime.

V3 is loaded from a hash-verified 67-member archive in an isolated runtime root. V4 is loaded from the live root and must match its approved 67-file freeze. Fresh subprocesses, hard pins, archive inventory validation, code/raw captures and final byte rechecks remain enforced. Outputs are written to new paths in this directory with overwrite refusal.

The v3 run uses strict gate mode because its old partial-gate approval remains historical. The v4 run requests the same documented-boundary release policy for the newly approved runtime. Gate mode changes only the release decision; strict episode/query checks and all failures are measured identically. Partial completion must retain strict_pass=false and coverage_complete=false; no false acceptance, replay/integrity error or new failed check is waived.

After the runs, preserve the two result JSON files, both raw logs, both runtime/evaluator/test code archives and a comparison ledger. Add v4/a2 findings to docs/DISCOURSE_EVALUATION.md only. Do not rewrite previous independent_review records or previous retention manifests.
