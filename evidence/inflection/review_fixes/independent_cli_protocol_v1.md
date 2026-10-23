# Independent CLI compression and input-budget review, v1

## Independence and scope

This is a new, separately identified post-publication regression set. The author
read the immutable a2 CLI and its existing error/source-budget contracts, but
has not read the repair or invoked either revision on these cases before this
material freeze. It does not change the original 74 cases, the later 22 cases,
their scores, or any historical code freeze. It is not a linguistic holdout.

The material has 32 cases: three malformed gzip forms across four corpus
consumers (12), missing corpus/source controls (6), valid plain/gzip smoke
checks (8), and exact-limit/one-over/moderately-oversized source checks for
read and verify (6). The two-row QAC-style input is an authored source fixture;
it is not a Quran excerpt. The two compatible nominal forms support the small
preposition phrase used only as a CLI smoke control.

## Frozen behavioral expectations

Malformed gzip data is invalid input: a JSON object names an INVALID_* code,
status REJECT and exit 2, with no Python traceback. The exact new compression
code is deliberately not prescribed. The fixtures separately produce EOFError,
zlib.error and gzip.BadGzipFile in the standard library, confirmed without
importing NABT. Files absent on disk retain the existing DEFER/IO_ERROR/exit 3
contract. Ordinary valid corpus/read/verification commands remain successful.

The source byte limit is 8192. A valid 8192-byte source remains readable and
verifiable. Sources of 8193 and 32781 bytes return a structured
DEFER/RESOURCE_LIMIT/exit 3. Verification may emit its existing result object
on stdout; a boundary helper may emit the equivalent named error on stderr.
The check accepts either single JSON channel, not a prescribed helper location.

## Independent I/O budget observation

Run each CLI command in a fresh isolated Python subprocess, explicitly selecting
the runtime's src directory and recording all loaded nabt module origins. The
parent never imports production modules. Each oversized-source case monitors
only the actual source file through general file/stream read wrappers. Preserve
requested sizes and actual returned bytes. The cumulative returned source
bytes must be at most 8193, each read request must be bounded by 8193, and an
unbounded request is not acceptable. No particular number of reads is required:
8193 in one read, several bounded reads with that aggregate limit, or refusal
after metadata inspection without a read all satisfy the observation contract.
The monitor records rather than enforcing the limit, so the a2 defect remains
observable. It must not replace the input with a truncating fake.

The actual oversized file is moderate (32781 bytes), not a memory exhaustion
exercise. The one-over case checks the boundary; the larger case distinguishes
an unbounded full read from a bounded limit-plus-one probe. Read the exact
8192-byte positive as a guard against rejecting every source without inspection.

## Verification and evidence

A verify smoke report is prepared through the selected revision's own CLI from
the matching valid source and plain corpus. Its raw output is preserved. The
invalid/oversized verify cases use a valid small report so they reach the
relevant input boundary. Runtime-dependent report bytes are not frozen answers.

Validate the runtime through explicit manifest/snapshot/archive pins and the
complete authoritative inventory, reusing the independently reviewed snapshot
checker. Never accept a caller-recomputed manifest as its own authority. Before
running a case, archive the selected runtime, runner, checker and exact frozen
fixtures/protocol. Refuse to overwrite outputs. Preserve complete stdout,
stderr, exit status, source I/O trace and module origins for every command.

Retain the first a2 baseline even if it fails. Do not alter gold to match a fix.
A later a3 allowlist addition may change only the trusted snapshot pins and
default, with the same behavioral scorer. If an adapter defect is found, retain
the failed measurement and document a separate erratum and replay. Keep these
CLI results separate from the 74/22 morphology metrics.
