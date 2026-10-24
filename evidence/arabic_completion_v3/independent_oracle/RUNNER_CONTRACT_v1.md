# First measured execution adapter

This adapter was authored after the 24-case material freeze and the runtime
freeze, before any prediction on the 24 cases. Five structural/unit tests use
post-freeze development fixtures and an explicitly authored object-owner graph.
They do not execute the 24 inputs and do not claim random or statistical blindness.

Run from the repository root:

```sh
python evidence/arabic_completion_v3/independent_oracle/run_oracle_v1.py --output-dir artifacts/local/arabic_completion_oracle_first_v1
```

The directory must be new and inside the repository. The tool never overwrites
an attempt. Runtime and runner freezes may be specified with `--runtime-freeze`
and `--runner-freeze`; this version accepts only the declared runtime/material
identities. Exit 0 requires all strict checks. Exit 1 preserves an unsuccessful
measurement. There is no residual/debt allowlist and no original-86 score waiver.

The public API receives the selected raw lexical model, text, source ID, scope
and context only. Each of 24 documents and 29 queries is independently scored.
All actual learn/read/ask/replay calls are logged canonically in `raw.jsonl.gz`;
case observations, original certificates, errors and mutation before/after
objects are also retained. The finalizer reopens the gzip and checks record
count, exact canonical serialization, byte lengths and per-record hashes.

`result.json` separates 22 fixed cases from 2 conditional provenance probes.
Safe deferral fails a positive case. Provenance abstention is not counted as
language coverage. Question statuses are separate from certificate validity;
a valid negative counterproof on UNKNOWN is permitted and fully checked by
the independent answer validator. Runtime/compiler replay is a separate gate
from raw-premise, source-graph and oracle comparison; it does not prove Arabic
completeness or independence of the production compiler.

New morphology and sense receipts are audited by the independently reviewed
source helper. The extra scorer links modifier dependencies to the accepted
claim, its proof analysis, exact governor/target spans, activated assignments
and references. A unary nisba adapter can identify its sole participant. A
transitive tamyiz cannot use that adapter: it must expose its object endpoint.
Unknown nominal traits are tracked against raw annotations. A newly advertised
feature derivation without a reviewed checker remains unresolved.

All 18 predeclared mutation/control recipes have a separate result inventory.
They are not extra language cases. A recipe whose necessary positive witness
is unavailable is UNEXERCISED; an adapter exception is ERROR; only an actual
refusal of the mutation after a passing control is PASS. V-T05 explicitly needs
a separately fixed temporal teaching premise that is not in the 24-case input
material; it remains UNEXERCISED rather than introducing an uncounted language
case. The full strict flag also requires these mutation obligations, so an
unexercised control cannot be advertised as a complete gate.

The run records source/helper/runner inventories before and after, captures
all runtime and checker dependencies with the material in a code archive,
and records context-changed document and answer replays for P04/P05. A failed
run, oracle correction, or scorer correction is preserved under a new result
identity. Nothing in this adapter changes the frozen material or old gold.
