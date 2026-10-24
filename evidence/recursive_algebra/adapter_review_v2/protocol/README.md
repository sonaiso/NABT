# Recursive-probe duplicate-key protocol review

This is a new transport review record. `adapter_review_v1` and the historical
measurements are unchanged.

## Counterexample

Lean's general JSON parser stores object members in a map. Duplicate names can
therefore overwrite earlier values before typed field validation. Four raw
requests demonstrated the loss in the previously built recursive executable:

- Two top-level `op` fields.
- Two nested `source_id` fields.
- Two nested `evidence_ids` fields.
- An escaped `\u006fp` field followed by literal `op`.

All four previously returned `OK`. The complete raw requests, their old
responses, and the old executable hash are preserved in `before.json`.

## Narrow fix

Only the new recursive executable's transport changed. It checks raw object
keys before invoking the generic JSON parser, decodes their JSON string
escapes, and rejects any repeated decoded key in the same object. Each object
has its own `Std.TreeSet String`; repeated field names in different objects
remain valid. The balanced set avoids quadratic list membership for inputs
with many unique keys. Quoted values are skipped as values, including text
that resembles object syntax.

The new reader retains the existing one-MiB input bound, lexical nesting and
numeric limits, Unicode validation, bounded output, and discard-to-newline
behavior. `ProbeJson.lean` and its older consumers were not modified. Neither
semantic definitions nor the imported or bridge proof modules changed.

After the fix, all four raw requests return `INVALID_INPUT` with the message
`duplicate JSON object key`. A valid source request after a duplicate-key line
is still processed successfully. A separate request containing 40,000 unique
unknown keys exercises balanced-set bookkeeping within the byte budget and
is rejected as an undeclared-field input.

The updated development suite contains **23 passing tests**. Its three added
tests cover literal and escaped duplicate names, duplicate receipt fields,
independent object scopes, escaped string values, and recovery on the next
JSONL line. These are authored protocol regressions, not acquisition results.

The updated executable hash and full after-fix results are in `after.json`.
An initially stale linked executable was detected by checking its hash and
rerunning the raw requests; a clean rebuild of only its reproducible object and
link outputs produced the checked executable. No semantic result was accepted
from the stale build.

To replay without changing the frozen records:

```bash
python evidence/recursive_algebra/adapter_review_v2/protocol/replay.py
python -m unittest discover -s tests -p test_recursive_bridge_probe.py -v
```

The raw pre-parser is an executable protocol guard. This review does not claim
a Lean theorem proving JSON-parser refinement or complete noncanonical-JSON
rejection beyond the declared checks.
