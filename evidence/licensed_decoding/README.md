# Evidence for source transport and bounded certificate proposals

- `protocol.json`: declared development comparison and separately labelled fault injection.
- `baseline.json`: latest local paired run, with every case, denominator, sample and source hash.
- `baseline-initial.json`: first run before setup-failure reporting was hardened; retained as historical evidence.
- `VALIDATION.json`: exact test command, local scope, source hashes and image provenance.
- `targeted-tests.log`: native execution of the new suites and the prior answer contract suite.

The local contract result is 14/14 for paired statuses, independent native
replay and exact source restoration. The first tampered binding is rejected
in 14/14 cases, and the second correct proposal succeeds in 14/14. The latter
is deliberately injected recovery, not an improvement by a learned model.

The original 14 development cases and their expected statuses were not
changed. Neither these cases nor the supplied design document are a new
hidden evaluation. The 116 identity checks do not assert lexical, phonological
or semantic coverage. No weights were trained and no external model was called.

Local timings include fresh deterministic proposal construction in both arms,
and alternate execution order. A full regression process was also active on
the local host; timings are exploratory and do not establish a latency target.
Native CI runs the suites again and records a fresh measurement in
`artifacts/local/ci/licensed-decoding.json`; its exact run is linked from the PR.

The selected answer can be independently replayed. The measurement report and
its timing/attempt logs are unsigned telemetry, not authenticity certificates.
Raw source transport is not a compression claim or a replacement LLM tokenizer.
