# Versioned continuation after a source-premise guard correction

This directory adds a new execution and review protocol. Every historical
material, result, raw journal, runner, review, and freeze remains unchanged.
The approved runtime is the separately pinned `code_freeze_v2.json`; it
enforces the previously declared raw form-I `hasiba` premise. Historical
freezes are not rewritten to authorize it.

## Same 24 authored inputs

The original material freeze remains
`78589ad292f747a27b76cf08c56848377f93fe370b6fa9f0229951fa8f443a3f`.
There are still 22 fixed cases, two conditional provenance probes, and 29
questions. The new producer uses the already reviewed v2 scorer directly.
Its public call sequence and all public inputs, returns, source/context
records, and cross-context observations must be exactly identical to the
preserved first trace. No public field is normalized, omitted, or replaced.

The expected new raw journal is constructed before execution: retain every
public call and case record from the first trace; substitute only the exact
case scores and mutation receipts already preserved by postreview v2. The
independent review then recomputes those scores and all mutation receipts.
The mutation adapter consumes canonical case records; the separate cross
record retains context-change replay receipts. New byte differences stop the
gate and preserve the attempted output for another explicit review/version.

The result must retain **14/22** fixed cases, **19/29** matching question
statuses, 29 independently validated answers, N03 correct abstention, N06
unresolved independent review, 13 exercised mutations, and five UNEXERCISED
recipes. It must preserve the complete residual-check inventory. Neither
probe nor an unavailable mutation is counted as successful understanding.
The strict coverage flag stays false.

## Separate source counterexamples

The independently authored six-case source suite has its own frozen material
and its own result. Two controls supply fully vocalized active perfect 3MS
form-I `Hasiba`. Four counterexamples supply a form-II annotation, no source
vowels, a contrary medial vowel, or a passive source. The target sentence
does not change. Target vowels, target roles, a lemma label, and a plausible
two-complement construction cannot replace the independently observed raw
source premise.

Both controls require an accepted scoped belief, support for the belief
question, and UNKNOWN for the embedded factual question. The four negative
cases require DEFER and no accepted belief or sense witness. Missing reports,
thrown exceptions, failed replay, invented authority, and validator failure
are unconditional failures; they are never successful refusals. All 34
public calls and six case observations are bound and independently rescored.
These cases and their four questions do not enter either old denominator.

## Execution, archives, and gate

```sh
python -m unittest discover -s evidence/arabic_completion_v3/independent_oracle/continuation_v3 -p 'test_*.py'
python evidence/arabic_completion_v3/independent_oracle/continuation_v3/run_regression_v3.py --output-dir artifacts/local/arabic_completion_oracle_continuation_v3
```

The output directory must be new and inside the repository. Both producers
always execute afresh. Code archives, complete canonical raw journals,
per-record inventories, runtime/dependency fingerprints before and after,
strict results, independent reviews, and a final `regression.json` are kept.
The original producer remains runnable only against its original archive
and dependencies; its historical tests are not silently repinned for the
new checkout.

All runtime, code, source, and result pins are exact. Snapshot comparison
allows only relocation of the absolute checkout root; file contents,
relative paths, versions, types, and inventories cannot differ. Archives
are opened and every member verified. The historical result is a comparison
reference, not evidence that a fresh execution succeeded.

`regression_gate_pass=true` requires the exact retained partial result and
all six separate source cases to pass, with no execution, integrity, safety,
or new-authority failure. It is not strict coverage success, a new blind
experiment, a corpus prevalence estimate, or a proof of universal Arabic
understanding. The primary dictionary passage and authored raw premises
have distinct authority, documented in the separate material contract.
