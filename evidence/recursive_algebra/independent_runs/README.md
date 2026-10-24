# Independent recursive-algebra measurement, final source-guard version 3

The frozen material contains **40 authored cases and 106 assertions**. The
final version-3 run returned **65 PASS, 0 FAIL and 41 UNMEASURED**. There were **19 fully
measured cases, 8 partially measured cases and 13 unmeasured cases**. Every one
of the 45 executed requests passed the evaluator's strict response-integrity
checks: 36 requests to the Lean executable and 9 to the actual Python source
transport. The saved raw-output replay reproduced every score without running
either backend.

`measured_contract_gate` is true, while `strict_complete_pass`,
`acquisition_measured`, and `held_out_arabic_discovery_measured` are false.
These are authored structural/source contracts. They are not a measurement of
independent discovery of Arabic classes, meanings, syntactic roles or cases.

## Evidence and reproduction

- `run_v3.json`: the input-only plans, all expected-versus-observed assertions,
  response-integrity results, and source/probe hashes before and after execution.
- `run_v3.json.plan.json`: requests frozen before execution; no expected answer
  is used by `build_case_plan(operation, input, fixtures)`.
- `run_v3.json.lean.stdin.jsonl`, `.lean.stdout.jsonl`, and `.lean.stderr.log`:
  exact Lean request/response bytes and separate diagnostics.
- `run_v3.json.native.stdin.jsonl`, `.native.stdout.jsonl`, and
  `.native.stderr.log`: exact actual-source-adapter requests and full reports.
- `run_v3.json.code.tar.gz`: the 137 measured source/dependency/material files.
- `replay_v3.json`: digest verification and exact score reproduction from those
  saved transcripts. Repository-relative references permit replay in a new clone.
- `../checker_review_v2/validation.json` and its separate test logs: **34/34**
  evaluator regressions, including mutated gold, typed values, coherent false
  license claims, hidden negatives, stale receipts, false exhaustion and a
  relocated-checkout replay. The checker and these tests are unchanged in v3.
- `run_v1.json`, `run_v2.json`, and all their transcripts, plans, source snapshots
  and original replays remain unchanged. `replay_v1_after_placement_fix.json`
  additionally verifies the older snapshot with the final checker.
- `placement_comparison_v2.json` records equal material, plans, scores and
  byte-identical stdin, stdout and stderr for both backends across versions.
- `source_guard_comparison_v3.json` records the same exact invariants between
  v2 and v3 despite the rebuilt probe binary.

The run used the already-built guarded probe with SHA-256
`1f5c3a85323576b7649b87028ede3540220835640f5cf84a01320c094ec612f1`.
All recorded source and binary hashes remained unchanged during execution.
The exact frozen material SHA-256 is
`2d030838c7fa4ccf5a8f0d45ed554000a197e23a94449648d8011be4bf77a048`.

From the repository root, a fresh measurement is:

```sh
python tools/check_recursive_bridge.py --lake /path/to/pinned/lake \
  --output /new/path/measurement.json
```

The default command builds only `recursiveBridgeProbe` before freezing its
hash. The coordinated recorded run used `--no-build` after the formal agent
provided the compiled binary hash. Output files are created exclusively; a
subsequent measurement must use a new path.

The saved run can be replayed without Lean or subprocess execution:

```sh
python tools/check_recursive_bridge.py \
  --replay evidence/recursive_algebra/independent_runs/run_v3.json \
  --output /new/path/replay.json
```

## What the measured assertions establish

The valid source fixtures preserve every template position, including vowels
and literal letters, while radical positions remain separate sparse fibers.
The symbolic repeated-middle fixture retains three radical slots and four
radical occurrences. Root3, root4 and a lexical seed remain distinct. Joining
only separated radical positions does not satisfy PR14 original adjacency.
Bad UTF-8 byte boundaries are rejected by the actual Python byte-to-scalar
adapter; missing literals, mislabeled slots, aliased positions, foreign source
bytes/revisions, and a boundary recast as a radical fail source binding.

The coincident `nominal.faail` and `grammar.sifa.faa3il` readings are measured
in the actual Python reader's returned forest. Both survive with separate
catalog/reading identity. This is not a forest manufactured by the evaluator
from two successful single-reading echoes. Unicode combining-mark order is
retained exactly by the source view. The `mafool` source transport explicitly
keeps lexical attestation false and syntactic category, role and case unset.

Structural number comparisons preserve rule identity and ordered children;
the same tree in another registry version keeps its raw number but has a
different qualified identity. Source occurrences remain distinct from tree
numbers. The finite enumeration includes all thirteen authored height-two
terms (one leaf, three unary and nine ordered binary), normalizes duplicate
seeds, and reports exhausted search without a linguistic rejection.

The evaluator checks entire returned nodes, source spans and all response
flags. It independently closes negatives over the interpreted ledger, rather
than trusting the reported verdict or only the offered evidence. These closure
checks are exercised by separate development tests; the frozen W cases are
not counted as successful evidence-licensing measurements.

## Exact unmeasured assertions

| Cases | Unmeasured claims | Reason |
| --- | --- | --- |
| A02 | `gap_erased` | The probe rejects original nonadjacency but does not report this specific gap diagnostic. |
| A06 | `licensed` | The actual byte adapter rejects the split UTF-8 interval before a typed grammar assessment exists; no scalar occurrence or license response is invented. |
| A07, A09 | `unaccounted_positions`, `overlap_or_alias_detected` | Whole invalid-binding results are measured; the API does not expose these finer diagnostic labels. |
| W01–W08 | All 19 ledger, withdrawal, support, interface and verdict assertions | Their structural seed uses opaque naturals `[0,1,2]` while the reading root is `كتب`. No carrier map is declared. Replacing the input naturals with Unicode values would change the fixture. The unchanged W01 target is preserved as an `INVALID_SOURCE_BINDING` diagnostic with no invented gate interpretation; later ledger claims are not credited from this already-invalid baseline. |
| I06 | `same_witness_record` | The numeric/tree comparison is measured, but no certificate-record interpretation is supplied for the unmapped ledger fixture. |
| E03 | `raw_kernel_count` | The public operation returns normalized unique candidates; the original kernel's duplicate list length is not exposed. |
| E04 | `certified_search_complete`, `all_unproved_candidates_rejected` | Structural enumeration is measured. The fixture supplies no decision procedure for the arbitrary grammatical certification predicate. |
| U01–U03 | All seven restoration, displaced-text, current-output and inverse assertions | The new probe has no operation consuming these frozen inverse/current-output inputs. Existing PR14 restoration proofs are not substituted for a measurement of these cases. |
| U04 | `same_surface_permitted` | Structural identity and child retention are measured. No arbitrary `Grammar.realize` contract is evaluated by this operation. |
| R02, R03 | All six role/case-scope and foreign-relation assertions | The inputs lack full source endpoints, typed annotated nodes and interpreted relation receipts. None is fabricated. |

## Authorship and exposure

The material was independently authored before the new implementation was
inspected. Before any measurement, `material_v2.json` corrected only the
`katib` input host endpoint from ten to twelve bytes; the original material,
erratum and both freezes remain preserved. Expected assertions were unchanged.

The implementer reported viewing the first 100 lines of the frozen material,
which exposed the `mafool` fixture and alignment, but no expected assertions.
That exposure is recorded in `../independent_v1/IMPLEMENTER_EXPOSURE.json`.
Independent authorship is claimed; complete implementer blindness and held-out
natural-Arabic evaluation are not claimed.

Before this first measurement, evaluator development corrected the string
encoding of numeric source IDs to match the existing source reader's identifier
grammar, and explicitly converted its upstream root string to scalar characters
for comparison with the new transport list. Neither correction changed a
frozen fixture or expected answer. The frozen measurement itself required no
post-output adaptation or rescoring revision.

## Placement correction after the first run

The first run passed this independent contract checker, but the broader
integration check rejected adding `src/nabt/recursive_bridge.py`: the historical
runtime freeze requires an exact inventory of 74 files, even when every old
file's bytes are unchanged. That guard was preserved.

The adapter was therefore moved to `tools/recursive_bridge.py`. The standalone
tool bootstraps the existing runtime and uses absolute imports; it does not
extend the frozen runtime package. The checker now loads that explicit tool
path only inside its isolated worker and includes it in the source snapshot.
The only changed common snapshot file is `tools/check_recursive_bridge.py`;
the removed and added files are the old and new adapter locations.

Version 2 re-ran all 45 backend requests under the same guarded Lean binary.
All request bytes, all output bytes, all assertions and all scores are
identical to version 1. No frozen input, expected answer, source premise,
linguistic policy, observation rule or scoring rule was changed. The full v1
evidence and its old source placement remain available in its original archive.

## Source-guard compatibility correction after version 2

The broader integration check subsequently reached the unchanged repository
source-integrity guard. Its comment/string lexer misread three valid Lean
double-quote character literals in the new raw duplicate-key scanner. The
guard itself was preserved. The probe now names that character once as
`jsonQuote : Char := Char.ofNat 34` and uses it at the three existing sites.
The archived source comparison shows exactly that definition and those three
replacements; no other probe logic changed.

The resulting probe binary was rebuilt and used for version 3. Every request
byte and every stdout/stderr byte from both backends is identical to version 2.
All 106 assertion results and all aggregate scores are also identical. The
only source-snapshot difference is `formal/RecursiveBridgeProbe.lean`; no
material, expectation, checker, Python adapter, semantic proof module or
historical guard was changed for this correction. The two earlier measurements
and their full archives remain preserved.

## Original standalone kernel

The original user-supplied source remains byte-for-byte unchanged. Its separate
validation is in `../original_kernel_validation_v1/`: the exact source compiled
under Lean 4.34.1 and all 32 theorem axiom reports were retained. Their only
reported assumptions are the standard `Classical.choice`, `Quot.sound` and
`propext` axioms. `../independent_v1/kernel_review.md` records the semantic
scope limitations: relative enumeration completeness, proof/evidence identity,
registry qualification, source occurrence, realization contracts and arbitrary
gate predicates must not be conflated.
