# Pinned source inventory and preliminary pilot replay

## Baseline and attribution

The two PR #1 findings were already repaired by
[`3cca86d5c06f21e0ee77738141e267d27bf7718f`](https://github.com/sonaiso/NABT/commit/3cca86d5c06f21e0ee77738141e267d27bf7718f),
which is in the main revision used for this work. That commit replaced checkout
scanning with Git tree/blob reads and wrapped preliminary pilot replay errors.
It also added the existing dirty-checkout test and mocked CLI error tests.
This change preserves that attribution and adds narrower provenance controls
and independent regression cases. It does not reimplement the CLI repair.

Review references:

- [Scan only files and bytes from the pinned commit](https://github.com/sonaiso/NABT/pull/1#discussion_r4354008001).
- [Convert preliminary replay errors into structured contract failures](https://github.com/sonaiso/NABT/pull/1#discussion_r4354008072).

The historical versions of the two affected files at
`0182987c585edb3cb52959c167d3d2b16ebfd211` were exercised in temporary fixtures.
For the CLI reproduction, the historical CLI was placed in an isolated copy of
the current package, and a newline was appended to that copy's `qatr.txt`.
This was a reproduction of the old boundary behavior, not a claim to have run
the complete historical release or its test suite.

| Probe | Before the original repair | Already-repaired baseline |
| --- | --- | --- |
| Tracked Lean source changed after its commit; untracked Lean source added | Inventories both `dirty` and `untracked`; recorded hash differs from pinned source | Inventories only `pinned`; hash matches committed bytes |
| Installed copy of `qatr.txt` changed without changing the policy pin | Exit 1, `ValueError: source digest mismatch: qatr`, traceback | Exit 3, JSON `DEFER / INSTALLED_CONTRACT_FAILED`, no traceback or result on stdout |

No authoritative source fixture or historical evidence file was modified.

## Additional pinned-object controls

`tools/catalog_upstream.py` now resolves the supplied complete lowercase object
ID to a commit and enumerates that commit directly. It rejects shortened IDs,
symbolic revisions, tag object IDs, tree/blob object IDs and missing commits.
The pin may be a full SHA-1 or SHA-256 object ID; the repository must actually
contain that commit. Moving HEAD does not invalidate an available pin.

Every Git operation uses `--no-replace-objects`. A concrete local counterexample
showed why this matters: a `git replace` mapping for a blob made the prior
`cat-file` call return replacement bytes while the inventory still cited the
original commit. The new tests exercise replacements of both a blob and a
commit; neither can change the inventory for the supplied pin.

Independent review found a further counterexample: a loose Git object can be
rewritten as valid zlib data under its old object-ID filename, and `cat-file`
can return those changed bytes. Disabling replacement refs alone is therefore
insufficient. The inventory now recomputes the Git object hash over
`type + space + decimal_size + NUL + payload` and compares it with the object
ID. It starts with the pinned commit, reads the root-tree ID from those checked
bytes, follows entries parsed from each checked tree payload, and finally
checks each source blob. It does not use an unchecked `ls-tree` result to
establish the chain. A valid Git header with forged payload bytes is tested
at the commit, root tree, nested tree and blob levels. This validates the
objects needed for the inventory, rather than claiming a full repository
`fsck`, parent-history audit, or cryptographic collision impossibility.
A separate temporary repository initialized with Git's SHA-256 object format
checks the 64-digit identity path against actual Git-generated objects.

The inventory reads regular-file blobs of modes `100644` and `100755` only.
Symlinks and gitlinks cannot bring external bytes into the scan. Tree paths
must be canonical relative paths; a deliberately malformed Git tree containing
`../Original.lean` is rejected before a source entry is produced. The existing
exclusions for `.lake`, `vendor` and `node_modules` remain in effect.

Repository names must be an unambiguous `owner/name` path. File paths are
percent-encoded in GitHub URLs while the `path` field keeps the original UTF-8
name. Names containing Arabic text, tabs, newlines, `#`, `?` or `%` therefore
remain part of the URL path, rather than becoming a query or fragment. The
SHA-256 field is computed from the exact committed blob bytes.

This is an offline inventory. It does not establish that an arbitrary local
repository belongs to the supplied GitHub owner, authenticate its remote, build
Lean, or grant imported declarations runtime authority. The report continues
to state `SOURCE_INVENTORY_NOT_KERNEL_VERIFICATION` and
`runtime_authority: false`. Its declaration scanner is not a full Lean parser.

## Pilot contract boundary

The existing CLI repair was sufficient and remains unchanged. Its catch order
is material because `NabtError` is a subclass of `ValueError`:

1. Re-raise an existing `NabtError` unchanged.
2. Convert otherwise unclassified `ValueError` or `KeyError` from preliminary
   source loading or `observed_records()` into `INSTALLED_CONTRACT_FAILED`
   with status `DEFER`.
3. Let the established CLI boundary produce JSON and exit 3 for that defer.

The new tests run a copied package in a fresh `python -I -B` subprocess from
outside the checkout. They assert the loaded module's origin, check a pristine
pilot run, corrupt the copied source bytes, and check the structured failure.
A second isolated package has its copied context table emptied, exercising an
actual `KeyError` during record replay after the source files load successfully.
These are package-copy tests, not a claim that a new wheel was built or tested.

A focused in-process test verifies that existing `NabtError` instances raised
while replaying records retain their object identity, status, code, message and
details. Both `REJECT`/exit 2 and `DEFER`/exit 3 are checked. A broken installed
contract remains distinct from a linguistic rejection or a substantive answer.

## Focused validation

Run from the repository root with `PYTHONPATH=src`:

| Command suffix after `python3 -m unittest discover -s tests` | Tests |
| --- | ---: |
| `-p test_upstream_catalog.py -v` | 11 |
| `-p test_pilot_contract_failure.py -v` | 3 |
| `-p test_provenance_tool.py -v` | 1 |
| `-p test_program.py -v` | 18 |
| `-p test_cli.py -v` | 6 |

The focused total is 39 passing tests. This is finite regression evidence for
the tool and CLI boundary; no additional Lean theorem is claimed. Kernel,
linguistic law, package version, historical experiment results, and the two
source-policy fixture files are unchanged by this repair work. Release-wide
gates belong to the integrating change and are reported separately.
