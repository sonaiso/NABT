# Reproduction gate for one preserved partial result

```sh
python evidence/arabic_completion_v3/independent_oracle/run_regression_v2.py --output-dir artifacts/local/arabic_completion_oracle_regression_v2
```

The output directory must be new. The wrapper always executes the frozen v1
producer afresh, preserving its strict result and raw journal. It then calls
the v2 post-review checker on those new files. Historical success alone cannot
satisfy this command.

The post-review admits only the already documented occurrence-schema correction.
Every raw public API payload and ordered observation must be byte-identical
(after decompression) to the preserved first trace. This includes all 171 API
calls, source inputs, report/answer bodies, context-change replays, case scores
and original mutation observations. No raw field is ignored. Gzip container
timestamps can differ; the decompressed payload and per-line canonical hashes
cannot. The absolute checkout root and result timestamps/output location are
metadata outside that trace. All relative code paths, contents, hashes and
source/helper inventories remain fixed, and the measured code archive is
opened and verified member by member.

All 24 observations are then freshly rescored by the independent validators
and v2 adapter. Only `connected_partition_and_profiles` for P01–P06 may change.
It must establish one exact source-bound occurrence and the full partition;
it does not declare an attached host licensed. Every other check, question,
trait trace, unresolved case and raw prediction remains unchanged. The only
case restored to pass is the negative P03. V-P02 becomes an exercised rejection
of a deliberately overlapping suffix; the other mutation outcomes remain.

The gate preserves **14/22** fixed cases, **19/29** matching question statuses,
N03 correct abstention, N06 unresolved independent review, and five unexercised
mutation/control recipes. Their failures are neither deleted nor counted as
language understanding. The strict flag remains false. The regression gate
requires the exact residual-check inventory, all independent certificate checks,
no execution/scoring error, no unsafe check failure, and unchanged approved
runtime/material/helpers. Any new payload, authority claim, error or integrity
failure stops the gate and requires a separate review/version.

The regression policy is deliberately stricter than a score threshold. It is
specific to this frozen partial implementation and authored input domain; it
cannot authorize a changed runtime, stronger linguistic claim, new language
case, or complete Arabic understanding.
