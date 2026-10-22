# Independent review of the foundation extension

Review date: 2026-10-22.

Reviewed implementation: `src/nabt/ambiguity.py` and `src/nabt/acquisition.py` in the isolated NABT development checkout, based on baseline commit `f48012ec15aa30746c38c706512fc1403101df3d`.

This review was conducted independently of the implementation work, using read-only inspection and focused adversarial probes. The reviewer did not modify implementation or test files. This evidence document records the review snapshot and the correction retested during that review.

**Result: one concrete trust-boundary defect was found, corrected by the implementing agent, and independently retested. No remaining functional defect was found in the reviewed ambiguity and acquisition implementations.**

## Found and corrected regression

The original `_snapshot` cloned `Leaf` objects but reused `Branch` instances. The frozen dataclasses also exposed mutable `__dict__` dictionaries. Consequently, a caller could alter a retained candidate branch after `CheckedPredictor` acceptance while its stored verification continued to say accepted.

Concrete reproduction before the fix:

```python
candidate = DecisionDAG(acquired.model.nodes)
checked = CheckedPredictor(candidate)

candidate.nodes[-1] is checked.nodes[-1]  # True
candidate.nodes[-1].__dict__["one"] = candidate.nodes[-1].zero
```

After that mutation:

- `checked.verification.accepted` remained `True`.
- For `(state=64, cell=8)`, the admitted predictor returned `(1, 1)`.
- The installed law returned `(96, 1)`.
- Exhaustive rechecking found **3,264 mismatches**.

The implementing agent changed snapshotting to copy both node types and added `slots=True` to the AST, wrapper, and forest classes. Independent retesting established that:

- The candidate and admitted predictor no longer share branch objects.
- AST nodes and the checked wrapper no longer expose mutable `__dict__`.
- Even an explicit `object.__setattr__` mutation of the **original candidate** leaves the owned admitted predictor equal to the installed law on **all 11,252 transitions**.
- The mutated original candidate still produces the expected 3,264 failures when independently rechecked.

This establishes snapshot isolation at the API boundary. It does not claim protection against arbitrary code deliberately rewriting the admitted object's private trusted process state.

## Ambiguity implementation

The reviewer compared the forest with `itertools.product` and the existing `tests.oracle.run`. That oracle uses letter/phase logic rather than the new dynamic program or exported table.

**250 random pattern/mode cases passed**, covering lengths 1–5, mixed explicit and absent marks, both modes, and several carrier classes. Each case checked:

- Exact total count.
- Exact counts by weight.
- Every lexicographic witness rank.
- Membership of every accepted path.
- Agreement between reported residual mark support and actual accepted paths.

The exact-length endpoint handling and zero-cost transitions were correct in the reviewed implementation. Source domains are reconstructed from the source itself; callers cannot attach arbitrary domains or fabricated counts to another source. Unsupported orthography remains deferred, and the strict original reader remains separate.

### Concrete witnesses

| Query | Waqf completions | Wasl completions |
|---|---:|---:|
| `كتب` | 48 | 45 |
| `كا` | 1 | 1 |
| Fully marked `كَتْبْ` | 1 | 0 |

For `كتب` in wasl mode, the positional projections contain **3 × 4 × 4 = 48 combinations**, but the forest retains only **45 licensed paths**. In particular, `(84, 11, 7)` belongs to every positional projection but `contains(...)` correctly returns false. This provides a concrete regression witness that the DAG preserves correlations.

A 128-position query completed successfully. A 129-position query returned `RESOURCE_LIMIT` with status `DEFER`, rather than a false linguistic rejection or recursion failure.

**Scope:** the input interpretation is independent missing-mark alternatives. The machine introduces correlations among the surviving paths. This is not yet an interface for arbitrary user-supplied correlated alternatives, morphological derivations, or root ambiguity.

## Acquisition implementation

The default acquisition run succeeded in the review environment with:

- **27 rounds**.
- **5,994 training examples**.
- **908 DAG nodes**.
- **0 mismatches** in the final exhaustive check.
- Approximately **1.9 seconds** in one measured run.

These measurements describe that run, not a minimum-size or minimum-sample guarantee. Mismatch counts can increase between intermediate rounds because fitting more examples can change behavior elsewhere; acceptance remains gated by the exhaustive final check. The timing is an indicative observation, not a controlled cross-platform benchmark.

Further independent probes passed:

- **112 run comparisons** against the independent oracle across both modes; starting states `0, 1, 4, 35, 36, 64, 95, 96`; and lengths `0, 1, 2, 3, 14, 300, 4096`.
- **100 random sparse fitting problems**, verifying that `_fit` preserves every supplied example. No root/postorder or shared-subtree failure appeared.
- Rejection of Boolean numeric fields, invalid state targets, invalid node types, and self-referential child indices.
- A full check with `counterexample_limit=0` still checked all **11,252** inputs and reported mismatches. Disabling witness storage does not weaken verification.
- Acquisition with `max_rounds=1` returned `DEFER`, no admitted model, and an explicit residual.

The complete checker compares both destination and cost. Final-state maps remain package-owned, so the learned transition procedure does not control mode semantics.

## Proof-status snapshot and scope

At the time of this implementation review, the available formal result was the **generic conditional Lean preservation theorem**: faithful primitive transitions imply equal runs/weights on arbitrary lists. The Python verifier established concrete finite agreement by execution. The appropriate description of that reviewed snapshot was a **finite-verified acquired model supported by a general Lean preservation theorem**.

A separate concrete `LearnedModel.lean` proof was subsequently being checked by another agent when this review document was saved. This review neither evaluates nor denies that additional result. The final proof manifest and proof-status documentation must record whether that exact learned AST subsequently received a Lean kernel proof of faithfulness. A successful concrete proof would strengthen the model's formal status, while remaining distinct from a complete Python-to-Lean refinement proof.

The valid input domain is exactly `state < 97` and `cell < 116`. Fourteen input bits also encode values outside those ranges; the public interface rejects them. Correctness should not be advertised for all possible 14-bit combinations.

One API documentation detail: `CheckedPredictor.run` returns accumulated transition cost even on rejected/dead paths. This agrees with the formal weight function and independent oracle, but differs from `Machine.analyse`, which exposes `consonant_weight=None` for a dead run. It should be described as raw accumulated transition weight when discussing rejected paths.

The reviewed work supports source-preserving alternatives, exact graded counting, ambiguity retention, and acquisition of an implementation of the **existing** law. It does not establish new Arabic rules, lexical attestation, root identification, or semantic understanding.
