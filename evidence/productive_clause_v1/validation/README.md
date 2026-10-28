# Preserved first executions

The earliest full matrix execution was GitHub push run **40705785054** on
`3d42187e7491e6e74ce89d8f2792efe40ce7d5f8`. PR run **40705964905** followed on
GitHub's merge commit `260d6e52e7c00e9d995a3d60f51be4f8b0b1a4e0`.
The local `phase=first` run followed those CI executions; it means first local
execution, not first globally and not blind evaluation.

The original CI ZIPs are retained byte-for-byte. The local archive contains the
complete generated reports, the full `make check` log, additional build/audit
logs and an internal file hash manifest. `first_observations.json` records
archive identities and compares the three executions. All 200 producer payloads
and the original summaries agree across the three runs.

Original result: 150/200 syntax contracts, 50/100 complete positive surfaces,
25/50 complete frames, 50/50 negative controls and 50/50 outside controls.
The evaluator reported 50 false authorizations. Independent examination of all
raw results identified a **role-list ordering defect in the evaluator**:
the projection used verb/agent/patient order, while gold uses source-word order.
All affected cases are VOS, with correct subject/object indices and source,
cell, shape, acquisition and candidate checks. The reported false-authorized
count is therefore not evidence of 50 wrong producer role assignments.

Keep these reports unchanged. Any corrected evaluation must retain the gold,
producer and language scope, use a new evaluator identity and freeze, and be
labelled exposed. Post-hoc diagnosis of these stored outputs is not another
native execution or independent acceptance experiment.

Local `make check` returned 2 at the new matrix acceptance gate after the
preceding gates completed. Its initial unit suite ran 2794 tests: 2731 passed,
63 skipped, zero failed. Skips concerned optional neural/corpus resources and
separately configured lexical/Qatr native checks; they are not counted as
passes. The new productive runtime, evaluator and framework tests had no skips.

Two additional root-review reproductions retain pre-repair framework CLI
diagnostic failures: a 5000-digit JSON integer and a duplicated lone-surrogate
key. They are transport/resource reporting defects, not linguistic cases or
additional false language authorizations.
