# Independent discourse review ledger

This ledger accompanies [DISCOURSE_EVALUATION.md](../../docs/DISCOURSE_EVALUATION.md). The machine-readable three-runtime comparison is [independent_comparison_v1.json](independent_comparison_v1.json). All gold, source splits, historical raw outputs and runtime freezes remain unchanged.

## Final same-adapter comparison

| Measure | v1 | v2 | v3 |
|---|---:|---:|---:|
| Strict complete episodes | 68/86 | 57/86 | 57/86 |
| Positive episodes (P) | 19/30 | 12/30 | 12/30 |
| Withheld terminal realizations (T) | 4/4 | 2/4 | 2/4 |
| Boundary episodes (B) | 26/32 | 24/32 | 24/32 |
| Lexical/acquisition controls (L) | 7/8 | 7/8 | 7/8 |
| Replay and invalid context (V) | 12/12 | 12/12 | 12/12 |
| Substantive questions | 36/45 | 24/45 | 24/45 |
| No-support question controls | 29/29 | 29/29 | 29/29 |
| All question obligations | 65/74 | 53/74 | 53/74 |
| Forbidden accepted claims / integrity false accepts | 1 | 2 | 0 |
| Outer / question execution errors | 0 / 0 | 0 / 0 | 0 / 0 |


| Snapshot | Result path | Result SHA-256 |
|---|---|---|
| v1 | `evidence/discourse/independent_runs/independent_v1_release_adapter.json` | `64dd4ba5facccf132b393c45c9c253b12348bd0895d0835d22788505f07e8d43` |
| v2 | `evidence/discourse/independent_runs/independent_v2_release_adapter.json` | `c2c287c95bd4c04fc462547318fc4b953e5c86cefeb9b5b5977494dd8342e524` |
| v3 | `evidence/discourse/independent_runs/independent_v3_post_review.json` | `f2f8303be15bc29e79226531e8a4f21db52813283c572974d933f55ffeed833d` |


Each result records the exact raw-log and code-archive filenames and SHA-256 values. The comparison JSON copies and verifies those references. The code archive contains the approved 67-file runtime plus measured evaluator and evaluator-test bytes. v1/v2 were imported from isolated extracted archives; v3 was measured from the live root matching its hard-pinned freeze. No result claims that a caller-provided hash alone establishes authority.

The identical measurement adapter is `tools/discourse_evaluation.py` SHA `def52e02a1e552b03b510323b89a036395f64e8c2ea0c3ac2648a92b1fa6a7b7`; evaluator tests are `tests/test_discourse_evaluator.py` SHA `a4cc8e96ad1d14f80b8c69c69e2dd854b1e142bac280b4ecd8941f3db51ec8c6`. The pre-run release metadata records 26 passing focused tests and all three planned output paths. The final strict results deliberately do not turn partial coverage into a gate pass.

## Frozen material

| Material | SHA-256 |
|---|---|
| `independent_cases_v1.json` | `52c73bcd8cba3a500f3dc612b861aff1a174b1a094e412c87bbf919f60ffd0d4` |
| `independent_source_inventory_v1.json` | `db5a1478702363f5c32c1fc53eb1b02f7b57e05456fc297ab5610e6bec4aa903` |
| `independent_source_audit_v1.json` | `0ac880b052a6bf6f74dba357e9b94369d57abdbf99fa0535f0b34bc3f0a43336` |
| `independent_protocol_v1.md` | `8e1976e63f6e7114df5a00f9c288a339b57cb5b25e70eea70bf30fc035a65995` |
| `independent_freeze_v1.json` | `3f65aa1c7fca3f6d5d4685654ebecbfc4c260c9920c562d8c5cad3dd41dccfe5` |


The material was independently authored before implementation inspection, using public a3 interfaces and exact primary sources. It comprises 86 episodes and 74 questions. It is not human-adjudicated gold or an untouched natural corpus. The four realization transfers exclude 83 complete verses jointly; they retain necessary compatible source forms and test known-family transfer, not arbitrary root or semantic induction. Shared-workspace independence is procedural.

## Preserved first attempts and corrections

All artifacts below have byte-for-byte retained copies in `evidence/discourse/independent_runs/`. The original files under `artifacts/local/discourse-evaluation/` also remain unchanged:

| Preserved stage | Artifact SHA-256 | Meaning |
|---|---|---|
| `independent_v1_first.aborted.json` | `0c93f2e4ed5e1f0c00dcd023c005f602bf900539979fc192badab5b7128a7ba8` | Aborted finalization; raw/code archives retained. |
| `independent_v1_first.recovered.json` | `794f2f31bdc6168a23692c36cfaee1e0d2d230269bc775c9a24ae1c662e4ad4c` | Recovered diagnostic score only; measurement_valid=false. |
| `independent_v1_adapter_corrected.json` | `691d743fc3de94526e4dca174502358deeafffdcea100d24663c078094e0be1e` | Completed v1 after operator adapter correction. |
| `independent_v1_final_adapter.json` | `e3acdada2665d313ca538b344d47d2b5141ca57c3c7df22d0e55fb7ff958a6b4` | v1 after role/reference/answer mutation hardening. |
| `independent_v2_post_review.json` | `41ee3e7a07ddccbfe4f0b5604c6c6f116388a1b77534c7ce6acece83384fdd97` | v2 with the same hardened adapter; two false acceptances. |


The abort was a concurrent overwrite of the old shared test filename. No original final `independent_v1_first.json` existed. The original raw `.jsonl.gz`, `.code.tar.gz`, abort metadata and explicitly invalid recovered score were retained. Test ownership was separated; the runtime was unchanged.

The operator adapter correction is [independent_adapter_erratum_v1.json](independent_adapter_erratum_v1.json). A closed qualified operator does not need noun/verb lexical stem fields. Three old integrity failures were adapter KeyErrors. P21/B23 then passed; L03 still failed its genuine actual-case obligation. B21 remained a true runtime false acceptance.

The mutation hardening is [independent_adapter_erratum_v2.json](independent_adapter_erratum_v2.json). Seven proven weaknesses were corrected on independent synthetic evaluator fixtures, without changing gold. An offline preliminary role/kind mapping attempt and its corrected output are preserved and labeled as adapter-development review, not runtime measurement. The peer reviewer reran the seven focused mutation tests and confirmed rejection of all seven forged certificates.

The [common-adapter metadata](independent_adapter_release_v1.json) adds the v3 pin/default, the source-prefix receipt check, and the opt-in case/check boundary policy. This comparison reruns v1/v2/v3 with identical measured bytes. The later gate-only revision and its extra focused test are separate; no historical report is overwritten.

## Runtime findings, including coverage regression

V1 B21 admitted an أمس property with unknown predicate construction and no fulfilled رفع assignment. V2's general construction guard prevents that claim, without pretending that QAC's `N` labels for أمس have become temporal `T` evidence. The same guard reduces positive coverage. V1 remains 68/86 and v2/v3 remain 57/86; the earlier v1 accepted outputs are not retrospectively rewritten.

V2 B04/B05 then exposed unsafe reference closure: a DEFER middle clause mentioning سهيل was omitted from the licensed mention index, leaving only حازم for the following هو. The reader incorrectly treated that incomplete set as closed. V3 sets `source_prefix_complete=false` after any prior DEFER clause and prevents antecedent closure. B04/B05 lose their forbidden claim but remain strict misses. P09 acquires additional missed positive/reference checks through the same conservative rule. Direct context names and speaker/addressee/deixis remain independently justified premises.

The six-case source-prefix regression is separately frozen in `prefix_scope_review/` and records 2/6 before versus 6/6 after. It is post-review authored evidence with explicit lexical premises, not additional independent holdout material. The earlier 26-case post-review matrix likewise remains separate.

## Every v3 strict miss

| Case | v3 failed checks | Interpretation |
|---|---|---|
| DSC-P02 | `required_claim:0`, `question:0` | V2/v3 retain an incomplete predicate-construction alternative. The complete claim/query is deferred under the general evidence guard; positive coverage is not restored by discarding that alternative. |
| DSC-P03 | `required_claim:0`, `question:0` | V2/v3 retain an incomplete predicate-construction alternative. The complete claim/query is deferred under the general evidence guard; positive coverage is not restored by discarding that alternative. |
| DSC-P08 | `required_claim:0`, `reading:0`, `question:0` | V2/v3 retain an incomplete predicate-construction alternative. The complete claim/query is deferred under the general evidence guard; positive coverage is not restored by discarding that alternative. |
| DSC-P09 | `required_claim:0`, `reading:0`, `question:0` | V3 retains the existing question miss and additionally blocks the required pronoun claim/reference because the preceding نوف راضية clause is DEFER. This is the conservative source-prefix rule, not a new false acceptance. |
| DSC-P12 | `required_claim:0`, `question:0` | V2/v3 retain an incomplete predicate-construction alternative. The complete claim/query is deferred under the general evidence guard; positive coverage is not restored by discarding that alternative. |
| DSC-P13 | `required_claim:0`, `reading:0`, `question:0` | The input حازمًا has an extra written accusative alif relative to the declared context name حازم; v1 produces no name reading. The promised conservative name matching did not authorize arbitrary letter deletion. The positive remains a strict miss. |
| DSC-P14 | `required_claim:0`, `reading:0`, `question:0` | V1 admitted the kana claim and answered its question despite unknown حكيمًا construction and missing actual nasb. V2/v3 now defer that claim/query as well; all three frozen obligations remain strict misses. |
| DSC-P15 | `required_claim:0`, `reading:0`, `question:0` | V1 admitted the laysa negative claim and polar refutation despite missing construction/actual nasb. V2/v3 block admission under the general guard. The negative claim, role/case and refutation obligations remain unfulfilled. |
| DSC-P17 | `required_claim:1`, `question:0` | V2/v3 retain an incomplete predicate-construction alternative. The complete claim/query is deferred under the general evidence guard; positive coverage is not restored by discarding that alternative. |
| DSC-P18 | `required_claim:0`, `required_claim:1`, `question:0`, `question:1` | V2/v3 retain an incomplete predicate-construction alternative. The complete claim/query is deferred under the general evidence guard; positive coverage is not restored by discarding that alternative. |
| DSC-P22 | `required_claim:0`, `question:0` | All four QAC أمس lemma records are POS:N, not T. The current temporal index does not obtain a temporal witness from this source; the third token is instead considered an unlicensed object. Do not relabel QAC N as acquired T. |
| DSC-P23 | `required_claim:0`, `question:0` | All five QAC غد lemma records are POS:N, not T. Future marker and imperfect are present but the temporal complement is not acquired, so the complete qualified assertion is deferred. |
| DSC-P24 | `required_claim:0`, `question:0` | Today is lexically read but occurs between named subject and predicate. The initial temporal reduction covers a trailing adverb, leaving this complete three-run nominal frame unparsed. |
| DSC-P25 | `required_claim:0`, `reading:0`, `question:0` | The frozen case contains a nominal relative clause with explicit هو return. The initial implementation covers a different bounded implicit singular verbal return, so no complete relative analysis is produced. |
| DSC-P26 | `required_claim:0` | The runtime licenses idafa and the repeated-idafa question. Its claim preserves restriction [{kind:idafa,complement:h}], whereas the frozen gold requests restriction:[]. The strict miss is retained. Removing the source qualification or changing gold to force success is not justified. |
| DSC-P27 | `required_claim:0`, `reading:0`, `question:0` | The accusative proper-name token سهيلًا has no context-name reading. The intended valency witnesses are full QAC forms; unsupported recitation/host geometry must not be silently stripped. No direct object is licensed. |
| DSC-P28 | `required_claim:1`, `reading:0`, `question:0` | The full new host أكرمه receives no reading; the intended source includes fa>akoramahu, with a recitation marker and a separate >akoramani witness. The independently grounded preceding nominal clause succeeds, but attached-object binding and event do not. |
| DSC-P30 | `question:0` | The source assertion succeeds. The question hamza attached to the context name does not produce a complete question reading. |
| DSC-T02 | `required_claim:0`, `question:0` | V2/v3 retain an incomplete predicate-construction alternative. The complete claim/query is deferred under the general evidence guard; positive coverage is not restored by discarding that alternative. |
| DSC-T04 | `required_claim:0`, `question:0` | V2/v3 retain an incomplete predicate-construction alternative. The complete claim/query is deferred under the general evidence guard; positive coverage is not restored by discarding that alternative. |
| DSC-B04 | `required_claim:1`, `reading:0` | V2 falsely narrowed the prior-reference set after omitting a DEFER middle clause. V3 removes the forbidden grounded claim, but the exact frozen candidate/positive obligations remain unfulfilled; do not count safe abstention as a complete episode. |
| DSC-B05 | `reading:0` | V2 falsely narrowed the prior-reference set after omitting a DEFER middle clause. V3 removes the forbidden grounded claim, but the exact frozen candidate/positive obligations remain unfulfilled; do not count safe abstention as a complete episode. |
| DSC-B14 | `force_preserved` | No reading is produced for the independently authored imperative spelling. No fact is asserted, but preserving request force is not demonstrated by abstention alone. |
| DSC-B15 | `force_preserved` | The accusative name has no reading; no complete wish analysis is retained. Absence of asserted facts passes while the separate force-preservation obligation fails. |
| DSC-B16 | `force_preserved` | The accusative name has no reading; no complete hope analysis is retained. Absence of asserted facts passes while the separate force-preservation obligation fails. |
| DSC-B19 | `question:0` | The attached conjunction plus context name وسهيل has no reading. The whole coordinated source is deferred, so the explicit negative first conjunct is not available to answer the question. |
| DSC-B24 | `required_claim:0` | V2/v3 retain an incomplete predicate-construction alternative. The complete claim/query is deferred under the general evidence guard; positive coverage is not restored by discarding that alternative. |
| DSC-B25 | `required_claim:0` | Same future/غدا input as P23 with a nonpast/today query. The wrong unqualified query is not supported, but the requested source-qualified future assertion is also missing. |
| DSC-L03 | `reading:0` | The source-licensed verb and both radical nun and deleted raf nun are present with correct empty deletion span. Its jazm assignment is left inactive because the subject reference is unresolved. This is a role/case activation gap, not failure to acquire the two nun categories. |


The P26 gold/runtime qualification mismatch remains in the denominator: preserving an idafa restriction is not grounds for silently erasing it to match the frozen unqualified expected claim. L03's two nun categories and conditional جزم sign are already acquired from witnesses; the remaining missing actual case is downstream of unresolved reference/syntax.

## Gate decision and policy

Strict complete coverage remains false. The optional release gate is restricted to the exact approved v3 runtime, complete 86-case inventory, zero false accepts, zero outer/question errors, and the fixed case-and-failed-check allowlist in the evaluator. It never permits integrity/replay failures or an unlisted failed check. The saved strict comparison is not rewritten after a policy decision. Any additional coverage exception requires a named diagnosis, retained prior output, and a separate policy record; it does not improve the strict score.

The first application of the opt-in policy to the saved v3 report rejected P09's additional `required_claim:0` and `reading:0` misses. [independent_gate_before_p09.json](independent_gate_before_p09.json) preserves that decision and the relevant v2/v3 clause/reference traces. [independent_gate_revision_v1.json](independent_gate_revision_v1.json) authorizes exactly those two positive-coverage signatures, retaining the existing `question:0` signature. The revision proves AST identity of every measurement/scoring function and records the exact source diff, old/new adapter hashes, and 27 passing focused tests. No other case or safety condition changes. A separate v3 opt-in rerun verifies the release policy; the original three-runtime strict comparison remains the linguistic measurement.

That [opt-in rerun](independent_runs/independent_v3_gate_reviewed.json) completed at 57/86 with zero false accepts, zero unexpected failed checks, and 29 explicitly documented incomplete cases. It emits `gate_pass:true`, `strict_pass:false`, and `coverage_complete:false`. Its result SHA-256 is `39ca85bd6f1b2edf88aa4ae2662b968b60ecf03cc6159c3f8a02430b78518a0f`. The 86 raw records match the pre-policy v3 records exactly after removing only the nonsemantic `score.seconds` field. [independent_gate_verification_v1.json](independent_gate_verification_v1.json) preserves the comparison and all artifact hashes.

The release-policy evaluator SHA-256 is `ac5d26d3ffbe83b86534eee102064381bc89991acebffc40b6148bdcbda6d46e`; its 27-test file is `163db3d79545e1d51016a640e85458c02bf9372049b1cba4e19ab102cdff16fe`. These differ from the common three-runtime adapter only in the explicit P09 boundary policy and its focused test. [independent_retention_manifest_v1.json](independent_retention_manifest_v1.json) verifies 27 retained files against their unchanged originals, including the gate rerun, all first attempts and all before/after runtime code archives.

This ledger intentionally distinguishes: a valid certificate; a safely blocked overreach; successful recognition of force/reference; a complete positive episode; and a world fact. Only the bounded conditional propositions are in scope here.

## Published regressions

The v2 release rerun recorded broad Arabic 0/40 episodes (0/43 questions), declared scope 8/12 (9/11 questions), excerpts 0/8 semantic reads, and controlled text 60/60 with 126/126 query checkpoints. Source receipts are under `artifacts/local/discourse-release-check/arabic-regression/` and `text-regression/controlled_rerun.json`. These are old published materials, not new holdouts. Their denominators and supplied premises differ from the 86 discourse cases.

The historical word, morphology, nominal, and inflection materials remain immutable. No 0/40-to-12/30 percentage improvement is inferred. Release-level make-check and wheel evidence are maintained separately by the release owner; this evaluator report does not substitute its focused tests for those gates.
