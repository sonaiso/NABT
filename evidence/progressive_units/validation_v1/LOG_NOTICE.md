# Axiom stdout/log name collision

The first wrapper opened `axioms.log` for command stdout, while
`tools/check_axioms.py --output axioms.json` independently writes its complete
Lean audit to that same suffix. The printed JSON summary consequently overwrote
the beginning of the raw Lean log. The audit itself returned success after
checking all 829 declarations; `axioms.json` remains the actual machine report,
but this first `axioms.log` is not a complete transcript.

Both original files and the original wrapper command record are preserved.
The axiom command is rerun unchanged under `validation_v2` with distinct
`axioms.stdout.log` and `axioms.log` paths. No source, theorem, premise, result,
or test material is changed for that rerun. The validation summary must cite
the complete second audit log, not the truncated first transcript.
