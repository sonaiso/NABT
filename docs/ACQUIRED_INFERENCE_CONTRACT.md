# Acquisition and the PR 34 inference bridge

Version: `nabt.acquired-inference.v1`. This is an orchestration contract over the
existing `nabt.aligned-acquisition.v1` and `nabt.licensed-inference.v1` laws.
PR 34 was merged at `a3ba5b32e67c25b2a71a6c8ebc8635659e6e7f74`; it is the
actual ancestor of PR 52, not an external implementation to copy.

## Admission

1. Independently bind exact source and query bytes, source identity, revision,
   discourse scope and time. Both acquisition requests use the same canonical
   scope/time encoding as the existing inference runtime. Ending choices remain
   separate for source and query. Do not replace either text with expanded cells.
2. Call the existing acquisition/word/shape pipeline for each input. Missing
   native verification, malformed input and resource exhaustion stop the join.
3. Reuse `tools.licensed_inference.runtime.evaluate` with the original bytes and
   original scope/time. Its native Lean checker independently rereads those bytes
   and verifies the existing signed and clean closure certificates.
4. A complete joined result requires complete acquisition and a licensed shape
   for every source/query word, plus a verified reading and checked closures in
   the PR 34 fragment. Only this result may expose a top-level answer. The old
   word reader's lexical coverage is diagnostic, not a replacement for PR 34's
   source-derived reading contract.
5. A bounded PR 34 inference may be retained as a nested diagnostic when sound
   acquisition is incomplete. Its own authority remains scoped to its law;
   it cannot make the joined result complete. Refusals, failures and exhaustion
   remain distinct. All world-truth/completeness flags stay false.
6. Verification takes independently supplied source, query and all metadata,
   reruns the installed components, and compares the entire typed JSON receipt.
   No caller manifest, status, certificate or alternative executable is trusted.

This is checked composition in the executable adapter, not a new theorem that
Arabic semantics can be decoded from A116 alone, not a new Lean theorem about
Python/JSON refinement, and not a replacement grammar. Existing native laws and
all historical measurement snapshots remain unchanged.

## Regression and source scope

`evidence/aligned_acquisition_v1/integration/cases.json` is a new, exposed
integration regression authored from PR 34's published fragment and this
contract before the adapter implementation. It is not a held-out linguistic
oracle and does not revise the original 72-case matrix. Conditional cases must
retain PR 34's result even where the joined chain is incomplete (notably the
article/hamzat-wasl in `الْحَقَّ`). It must never silently widen either language.

Tests additionally mutate both sources, identity/revision/scope/time/endings,
cell arrays, statuses and native responses; omit each verifier; and check
resource bounds. Current proof/link references must be regenerated from native
Lean into a new evidence directory. Historical epistemic/semantic/source
measurement receipts must not be edited to conceal a stale-reference failure.
