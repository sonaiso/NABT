# Review of the actual-source adapter

Reviewed on 2026-10-24. This directory records a development audit of the new
source transport and executable Lean projection. It is separate from the frozen
external 40-case material, the imported 32-theorem proof core, and all historical
Arabic acquisition measurements. No acquisition score is inferred from it.

## Findings and resolutions

1. **Report-local witness IDs were insufficient in a bare Lean response.** The
   initial `frame_request` retained numeric evidence IDs but did not carry the
   report that gave those IDs their meaning. Ordered reading records,
   relations, and references were also retained only in the Python transport.
   A bare typed projection therefore could not be described as preserving the
   complete upstream analysis or its witness records.

   **Resolution:** `assess_recursive_source` exports the complete replayed
   transport, the exact typed request, and the Lean assessment together. Its
   evidence namespace contains the transport schema, complete report ID, and
   evidence-number domain. `verify_recursive_assessment` rereads the external
   text and independently supplied corpus/context, rebuilds the request, runs
   Lean, and compares the complete result. The exported envelope expressly
   identifies the narrower typed projection. Bare request builders remain
   available for interoperability and do not claim complete witness transport.

2. **Python numeric aliases weakened the exact response comparison.** Python
   considers `True == 1` and `1.0 == 1`; ordinary dictionary equality consequently
   accepted a mocked response whose `atomization_id` changed from an integer to
   a Boolean or float. The real Lean executable emitted the correct values,
   but the Python response guard did not enforce its claimed typed identity.

   **Resolution:** the bridge compares canonical strict JSON bytes for the
   returned node and structural tree. The enumeration guard also binds the
   exact typed height. Both numeric-alias counterexamples now produce a
   `RECURSIVE_PROBE_FAILED` deferral. The frozen observations include these
   adversarial checks.

3. **The Python transport and Lean projection have different limits.** The
   full source transport accepts inputs outside the smaller Lean executable
   domain. Earlier, a frame source spine could be constructed before that
   difference was discovered.

   **Resolution:** projection preflight checks the complete source's 256-scalar
   limit and the 127-node host/core limits before constructing the projected
   spine. Larger full transports can still be valid; an exhausted projection
   is a deferral, not a grammatical rejection.

4. **General source preservation must permit real substitutions.** Requiring
   a PR14 host's output to equal its raw source would exclude every genuine
   substitution.

   **Resolution:** the formal bridge binds the original raw source and retains
   the entire effect tree, including its replacement and displaced child.
   Source reconstruction is proved from the existing structural gates.
   `CertifiedBridge` separately requires a supplied PR14 context with the same
   source inventory, a PR14 `Licensed` proof for every retained host, the
   imported grammar's `Certified` proof, and realization/section agreement at
   every annotated node. The executable does not fabricate these obligations.

## Actual pipeline observations

All eleven proposals generated from five supported examples passed complete
transport replay, exact typed node roundtrip, and original-source binding:

| Source | Retained proposals | Observation |
| --- | ---: | --- |
| `مَكْتُوبٌ` | 1 | Root `كتب`; radical positions `2,4,7`; all eight stem positions retained in the complete source host. |
| `كَاتِبٌ` | 2 | `grammar.sifa.faa3il` and `nominal.faail` remain distinct despite equal roots and shapes. |
| `انْتَبَر` | 2 | `past.VII` with `تبر` and `past.VIII` with `نبر` remain correlated alternatives. |
| `إنَّ هذا عالم.` | 2 | Qualified inna frames retain accusative local case for the demonstrative subject and nominative inflected case for the predicate. |
| `هل أنت عالم؟` | 4 | The two unqualified analyses have no projected actual roles or section; the two qualified analyses retain their original roles and case domains. |

Every Lean verdict is `SOURCE_ONLY`. The new source spine is explicitly a
reconstruction of source order. It does not claim to recover the absent original
syntax tree, acquire lexical attestation, discover a grammar, or prove a
world-level assertion. The interpreter ledgers produced by the actual-source
adapter are empty. Original source and upstream evidence records are retained for review,
without converting it into invented recursive gate receipts.

The complete, reviewable inna example is `inna_assessment.json`. The compact
observations, source-file hashes, and adversarial results are
`observations.json`. They are frozen records of this review. To rerun without
overwriting those records:

```bash
cd formal
lake build recursiveBridgeProbe
cd ..
python evidence/recursive_algebra/adapter_review_v1/replay.py
```

The development contract tests are `tests/test_recursive_bridge_probe.py`.
The root-owned full transport and interop tests are
`tests/test_recursive_source_bridge.py`. The arithmetic and source bridge's
general proofs compile with the pinned Lean 4.34.1 toolchain. The fast Cantor
encoding is proved equivalent to the supplied recursive encoding, and the
preflight bit budget is a proved upper bound. Numbering remains scoped to its
declared structural registry; it is not a linguistic license or a globally
unique source-occurrence identity.
