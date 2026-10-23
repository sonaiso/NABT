# Unchanged construction gold on v2 and v3

This directory preserves the post-review comparison of the frozen construction
v2 runtime (`0.14.0a1`) and v3 runtime (`0.14.0a2`). The 86 cases and their lexical
source/context premises are unchanged. This is regression on previously opened
material, not a new blind holdout.

The first pair, `results_v2_strict.*` and `results_v3_strict.*`, was measured before
enabling the v3 optional gate. Both valid measurements exited 1 and scored
71/86. `gate_review_preapproval_v1.json` records complete raw readback, identical
checks and unchanged grounded-claim/query semantics before policy approval.

The final pair, `results_v2_final.*` and `results_v3_final.*`, used identical final
evaluator and test bytes. Both optional gates exit 0 while preserving 71/86 and
`strict_pass=false`. The original v2 policy remains separate from the reviewed
v3 policy. Both permit only the existing 15 case IDs and 120 exact coverage
failure signatures. No false accept, invalid certificate, replay failure,
measurement error or incomplete journal is waived.

`comparison.json` binds all result/runtime/adapter/archive identities and records
fresh reconstruction of all 86 case scores from each final raw journal. Each
journal has 87 canonical records and 106 question calls. `gate_review_v1.json`
records the gate-only AST change and 34/34 focused evaluator tests. The original
tool/test bytes before pin and gate changes are retained in this directory;
each measured run also has its exact code archive.

Metrics are unchanged: positives 30/43, boundaries 31/31, ambiguity 4/6, replay
6/6; questions 30/42 SUPPORTED, 29/39 UNKNOWN with a complete query, and 19/19
no-grounded-support controls. The only observed candidate-count change is I09,
four viable candidates to zero, while both versions defer without a claim.

The separate alif-template and attachment regressions are linked by hash from
`comparison.json`. They are authored after the defects were found and frozen
before correction; their 12 and 6 cases are never added to the original gold's
denominator. All old v1/v2 results, including invalid historical attempts, remain
untouched.

## Release status after the separate legacy check

The construction-86 gate above is historical evidence for that bounded suite,
not release approval for v3. The separately preserved legacy discourse pair
regressed from **57/86 to 40/86**, with supported-answer checks **23/45 to 7/45**.
The new adjective agreement guard lacked a source-qualified semantic agreement
profile for context-only personal naming premises. The legacy gate was not
approved. `release_status_v1.json` binds this blocker to the saved legacy
comparison; it does not alter any earlier result or the original gold.

The exact final evaluator and tests are now separately copied and frozen in
`evaluator_freeze_v1.json` before any registration of a corrective v4. A new
16-case authored regression is frozen in `../context_name_review/`; it separates
explicit person-context premises from acquired lexical features and tests the
unknown, conflicting, ambiguous and replay boundaries.
