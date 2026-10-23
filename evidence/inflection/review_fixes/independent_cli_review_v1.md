# Independent CLI review: compression failures and bounded source reads

The frozen 32-case CLI set scores **16/32 on 0.12.0a2 and 32/32 on
0.12.0a3**, using exactly the same runner and snapshot-checker bytes. Both first
runs are preserved, including stdout/stderr bytes, exit statuses, I/O traces,
loaded-module origins and source/code archives. There were no harness errors
or regressed cases. This set is separate from the original 74 and post-review
22 linguistic/source-evidence cases.

## Independence and material

The author read the immutable a2 CLI and its existing diagnostic/budget
contracts, then authored and froze the cases and protocol before any CLI
prediction or reading the fix. Standard-library decompression alone confirmed
that the three malformed fixtures produce `EOFError`, `zlib.error` and
`gzip.BadGzipFile`, respectively. The exact new error code was not prescribed:
the frozen expectation required a named `INVALID_*` error, `REJECT`, exit 2
and no traceback.

The authored two-row QAC-format fixture supports a small preposition phrase
for positive CLI controls. It is not a Quran excerpt or a new natural-corpus
evaluation. Verification reports are generated through each selected runtime
from the valid source and preserved in the raw log. They are setup artifacts,
not frozen answer labels supplied to the predictor.

The material freeze is
[`independent_cli_freeze_v1.json`](independent_cli_freeze_v1.json), SHA-256:

`0621a6e6280549d747e4df8983249fd840909f11e91047f06b6d3f589657d5a5`.

The runner/helper freeze is
[`independent_cli_runner_freeze_v1.json`](independent_cli_runner_freeze_v1.json).
The a3 manifest pin and default were added before either first run, so there is
no before/after adapter-version difference. A byte comparison against the
archived general evaluator confirms that its only changes were the explicit
v3 manifest/snapshot/archive pin and the default freeze path. Its behavioral
scoring logic is unchanged.

## Results by boundary

| Boundary | Cases | a2 | a3 |
| --- | ---: | ---: | ---: |
| Truncated gzip, corrupt deflate and bad magic across four corpus consumers | 12 | 0/12 | 12/12 |
| Missing corpus | 4 | 4/4 | 4/4 |
| Missing raw source | 2 | 2/2 | 2/2 |
| Valid plain/gzip audit, learning, reading and verification | 8 | 8/8 | 8/8 |
| Valid source exactly 8192 bytes, read and verify | 2 | 2/2 | 2/2 |
| Source 8193 bytes, read and verify | 2 | 0/2 | 2/2 |
| Source 32781 bytes, read and verify | 2 | 0/2 | 2/2 |
| **Total** | **32** | **16/32** | **32/32** |

The four corpus consumers are `audit-corpus`, `learn-qac-lexicon`,
`read-inflection --qac` and `verify-inflection --qac`.

On a2, the EOF and deflate fixtures produce eight uncaught exception
tracebacks and exit 1. The bad-magic fixture is caught as an `OSError`, but
becomes `IO_ERROR`/`DEFER`/exit 3 rather than an invalid-compression result in
four commands. On a3, all twelve cases produce
`INVALID_CORPUS_COMPRESSION`/`REJECT`/exit 2 without a traceback. Ordinary
missing files keep the existing `IO_ERROR`/`DEFER`/exit 3 diagnostic.

## Actual source I/O

The monitor observes the real source file; it does not truncate the file or
enforce the budget on the runtime's behalf. It records Python stream read
requests, returned bytes and explicit `os.read` on that file. The frozen
predicate accepts any sequence whose total returned bytes and every bounded
request are at most 8193, including a metadata-based refusal without reading.
It does not require one particular helper or one read call. Independent
synthetic scorer controls accepted metadata-only refusal, `4096 + 4096 + 1`
and one 8193-byte read, while rejecting unbounded requests and excess totals.

| Oversized source | a2 read and verify | a3 read and verify |
| --- | --- | --- |
| 8193 bytes | Unbounded request; all 8193 bytes returned | Bounded request of 8193; 8193 returned |
| 32781 bytes | Unbounded request; all 32781 bytes returned | Bounded request of 8193; 8193 returned |

Both versions eventually emit `RESOURCE_LIMIT`/`DEFER`/exit 3 for these
sources. The behavioral difference is whether the resource boundary is applied
before reading the whole oversized file. The larger fixture makes that
difference observable; checking only the diagnostic would miss the a2 bug.
The exact 8192-byte positive remains readable and verifiable on both versions.

This measures application read requests and returned bytes. It does not claim
physical filesystem prefetch accounting or a process-wide memory bound.

## Preserved executable evidence

The parent evaluator never imports production modules. Each command runs in a
fresh isolated Python subprocess with an explicit source root, and every
loaded `nabt` module origin must lie under that root. a2 uses its separately
extracted pinned archive; a3 uses the matching final source tree. The snapshot
checker verifies the explicit manifest/snapshot/archive allowlist, every
authoritative file and every archive member before predictions.

| Item | SHA-256 |
| --- | --- |
| CLI runner | `db3c3ee71443e3052da149a18d0a35c7d21ca87ea9585efb1e62c05d742d4752` |
| General evaluator/snapshot checker | `3417feab4c108859a2657bde192f0eb52a4d3f954fb7c1826756b2a634837402` |
| a2 first result | `c9769d1e48ef8547d37ad55b31d51a2ddd4abab7ae6ee69fdd3eb7cf9d26c9b3` |
| a3 first result | `9a921b40d912d698a003b20e7996b53a01f6339264d4350823d18719ef485018` |

The full comparison and sidecar hashes are in
[`independent_cli_comparison_v1.json`](independent_cli_comparison_v1.json).
The preserved reports are
[`independent_cli_a2_first_v1.json`](independent_cli_a2_first_v1.json) and
[`independent_cli_a3_first_v1.json`](independent_cli_a3_first_v1.json).

Reproduction against the current pinned runtime:

```sh
python tools/inflection_cli_evaluation.py \
  --runtime-freeze evidence/inflection/code_freeze_v3.json \
  --output /tmp/nabt-inflection-cli-a3-review.json
```

For a2, additionally select its extracted tree with `--runtime-root` and its
`code_freeze_v2.json`. The runner refuses to overwrite result/raw/code files.
Its exit status is 0 only if both verification setups and all 32 cases pass;
otherwise it saves the measurement and exits 1. There are no boundary waivers
for this CLI gate.

The a2 runtime freeze, original/post-review gold and prior a2 linguistic result
hashes were rechecked unchanged. No runtime or formal code was edited by this
reviewer. These CLI repairs do not alter the interpretation or denominator of
the 74/22 source-evidence measurements.
