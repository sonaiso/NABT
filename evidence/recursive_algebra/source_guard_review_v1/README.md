# Equivalent quote spelling for the existing Lean source guard

The complete `validation_v3/full_check.log` shows **1,140 tests passing**, then
the conformance source guard fails with `Unterminated Lean comment/string in
source guard`. The Lean compiler had successfully built the new probe.

The existing lexical guard tracks comments and double-quoted strings but does
not parse Lean character literals. Three valid quote-character literals in the
new duplicate-key scanner left its lexical state open. `quote_spelling.diff`
replaces those three sites with the named constant `jsonQuote := Char.ofNat 34`.
The value is still Unicode U+0022. The scanner, source binding, grammar, proof
modules, fixtures and expected results are unchanged.

The historical source guard itself remains byte-for-byte equal to PR14.
`integrity.json` records its success over all 55 guarded Lean source files.
The original source is preserved in the v2 independent source archive, and the
final v3 independent run compares request/output bytes across the change.

An earlier regular-file log in `validation_v2` stopped before the diagnostic
tail. Its nonzero exit remains a failed attempt. It is not counted as a passing
run, and no failure is attributed to the nominal test where that partial log
happened to end. Later validation uses pipe capture and writes the complete log
only after the command finishes.
