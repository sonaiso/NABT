# PR3 query and independent replay boundary review

## Scope and result

The five reported defects were reproduced locally against commit
`b6ba0c6d960a3627d2841955fa8aeb369d54794c`, using an archived checkout rather
than the files being repaired. The corrected implementation passes the 19
independently authored tests in
[`tests/test_review_defect_regressions.py`](../tests/test_review_defect_regressions.py).

One defect affected the production Arabic question path: admitted relation
declarations were not carried into question reading. Four defects affected the
independent evaluation path. The production certificate verifier already
rejected the tested forged source clause and constant substitution. The review
therefore does **not** claim that those evaluation defects were also production
certificate-acceptance defects.

This is a correctness review of a bounded, public regression profile. These
tests are neither new hidden evaluation material nor general Arabic coverage
evidence. They do not constitute a new Lean theorem.

## Preserved baseline evidence

The original published evaluation files were not rewritten. The review adds:

- [`baseline_reproductions.py`](../evidence/arabic_syntax/review_fixes/baseline_reproductions.py):
  the exact local reproduction script used against the archived baseline.
- [`baseline_results.json`](../evidence/arabic_syntax/review_fixes/baseline_results.json):
  its observed results, including the explicit `old_gate_passed` fields.

The tests deliberately alter returned answers or certificate fields at the
evaluation boundary. They establish that the old checker could accept these
incorrect variants; they do not claim that the unmodified runtime naturally
emitted every variant.

To reproduce those historical observations, run the preserved script with the
baseline checkout as the working directory and its source and tools on the
Python path:

```sh
cd /path/to/b6ba0c6-checkout
PYTHONPATH=src:tools python /path/to/current/NABT/evidence/arabic_syntax/review_fixes/baseline_reproductions.py
```

Running that script against the corrected implementation instead would answer
a different question. Its labels explicitly describe the historical evaluator.

## Findings and corrected boundaries

| Reported defect | Observed baseline behavior | Corrected behavior checked independently |
| --- | --- | --- |
| Declared relation omitted from question context | `علاقة يراجع. سالم يراجع تقرير.` was admitted, but `هل سالم يراجع تقرير؟` raised `INVALID_QUERY`. | The same admitted source yields `SUPPORTED` for the exact binary atom `يراجع(سالم, تقرير)`, with a production-verifiable certificate. |
| Rule not bound to its cited statement | The frozen s07 rule was accepted with a correctly hashed two-byte fragment instead of its complete implication. Missing, reversed, and duplicated component spans also passed. | The independent checker requires the complete annotated statement, its ordered components, and the rule licensed by that statement. Fragment and component mutations fail. A separate two-statement fixture confirms that an implication cannot cite the neighboring fact statement, even with correct source hashes and a recomputed clause ID. |
| Bindings could rename constants | The independent checker accepted `{ريان: أثير}` on the ground rule about `ريان`, using a valid fact about `أثير`. An extraneous identity binding `{ريان: ريان}` also passed. | The binding domain must equal the rule's body variables. Constants, missing or extra variables, non-ground values, empty values, boolean values, and an unbound head are rejected. A valid manually constructed universal-rule certificate remains accepted. |
| Answer evidence could be absent or prove another target | Empty proof dictionaries, a null query proof, a valid proof of the premise `حاضر(ريان)` attached to the answer for `شاهد(ريان)`, and a signed proof under `SUPPORTED` all left the old gate passing with unchanged published summary counts. | Required proof slots are checked against status and support flags. Every proof is checked against the externally expected target and polarity. `SUPPORTED`/`REFUTED` require clean evidence. Missing, null, wrong-target, wrong-polarity, and wrong-kind variants fail. |
| Malformed evidence could remain a safety success | On already-uncovered s03, a certificate without `steps` raised `KeyError`, but both safety flags remained true and the old gate still passed with the same summary. | Malformed returned evidence fails certificate validation and safety regardless of existing coverage. Unexpected `KeyError`, `TypeError`, `ValueError`, and `RuntimeError` injected into the returned-answer checker also fail replay and the gate. |

### Why the already-uncovered case matters

Dropping an already-covered case can make an aggregate gate fail for an
unrelated reason, masking a deficient certificate check. The s03 regression
avoids that ambiguity: s03 was already incomplete and returned `OUT_OF_SCOPE`
before the injected malformed certificate. The baseline still reported
`independent_certificates_pass = true` and
`admitted_claims_licensed = true`. Its aggregate summary remained identical.

The corrected test checks the two safety flags directly, the recorded
`returned_answer_validation` stage, and the final gate. A lower coverage count
alone is not considered evidence that the defect was fixed.

## Production verifier versus answer validator

The baseline production verifier was exercised using live admitted sources
and certificates from their actual program. This avoids attributing a rejection
to a never-admitted snapshot rather than to the reviewed defect.

| Local variant | Baseline production result |
| --- | --- |
| Rule reduced to a two-byte source fragment | `REJECT`, `STALE_OR_FORGED_CLAUSE` |
| Ground constant retargeted from `ريان` to `أثير` | `REJECT`, `INVALID_CERTIFICATE` |
| Valid one-step premise certificate whose own target is `حاضر(ريان)` | `VERIFIED` for that target |

The last result is correct. A standalone certificate verifier checks the
certificate's stated target. The surrounding answer or VM receipt contract
must additionally bind that target to the externally requested question.
Checking a valid premise proof is not evidence that it answers the conclusion
question. The independent evaluator now performs that additional check.

Boolean premise and conclusion indices were already rejected by the old
independent checker. Their tests preserve an existing boundary; they are not
counted as newly repaired defects.

## How the tests avoid circular expected answers

The main positive witness is the published s07 certificate, frozen before the
fix. Its expected meaning is not regenerated by the repaired reader. Mutations
retain valid source hashes where relevant so that a checksum mismatch cannot
stand in for the semantic statement check.

The neighboring-statement test supplies explicit byte offsets and component
roles for the two literal Arabic statements. It does not call the runtime
reader or the annotation constructor to infer its expectations. The original
correct statement is accepted before the rule is pointed at the other
statement. Clause numbers are recomputed according to the public wire format
to isolate the statement boundary from stale-number rejection.

The variable-binding fixture is a manually constructed proof over the existing
s08 semantic gold. It checks proof replay only: the runtime still defers that
bare universal source, so its helper-level acceptance is not counted as an
end-to-end Arabic reading success. A correct binding is accepted before the
invalid domains and values are tested.

A separate clean/signed control adds an active opposing fact that is not cited
by the original proof. The old clean derivation must fail when its premise is
contested, while the same finite derivation labeled `signed` remains a valid
record of positive support. That signed proof cannot authorize a clean
`SUPPORTED` answer.

## Corrected review execution

```sh
PYTHONPATH=src python -m unittest tests.test_review_defect_regressions -v
```

Observed review result: **19 tests passed**, including the parameterized
counterexamples described above. The suite also executes the real independent
runner with local mutations, so required evidence and malformed-input checks
are verified through the evaluation boundary rather than only through a
helper called in isolation.

The corrected checker was inspected for closed certificate/step/clause shapes,
exact integer indices, complete rule-variable binding, externally supplied
query polarity, active-program identity, source-statement correspondence, and
the distinction between pre-result query failure and post-result validation
failure. The corrected implementation uses separately versioned statement
annotations; the review does not relabel those post-evaluation annotations as
originally hidden material.

This report records the focused correctness review. The release's full test,
Lean, conformance, versioned runtime snapshot, and public-regression receipts
are separate artifacts maintained by the integration run. Historical success
counts are not retroactively re-certified by these fixes.
