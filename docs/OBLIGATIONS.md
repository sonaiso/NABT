# Named obligations over a finite positive formula

`nabt.obligations` computes the smallest additional positive premises that
would satisfy a declared formula. It retains each alternative with its full
proposition identities and its bitmask. A three-valued verdict is a projection
of that family; relevant conflicting support is reported before projection.

This is a native, standalone NABT implementation. It makes no runtime import
from Mashru or Alghanem and does not change NABT's installed sound-shape law.
Learning that law's transition implementation and authenticating the premises
of a source-derived linguistic rule remain separate operations.

## Research consulted and limits carried forward

The following actual files were read at the indicated repository revisions:

| Source | Immutable reference | Lesson used |
| --- | --- | --- |
| Mashru `Nizam/Baqi.lean` | [`e4c801ffe9171dadedcc3aae23051ea0953ae361`](https://github.com/Saleh1967/Mashru/blob/e4c801ffe9171dadedcc3aae23051ea0953ae361/Nizam/Baqi.lean) | Bitmask residuals for positive formulas; soundness, completeness, inclusion minimality, and projection; detect conflict outside the three-valued judgment. |
| Alghanem `formal/a116/A116/Baqi.lean` | [`9d8fa03a51f894416e0abaf3b6821c5ae6441dcd`](https://github.com/Saleh1967/Alghanem/blob/9d8fa03a51f894416e0abaf3b6821c5ae6441dcd/formal/a116/A116/Baqi.lean) | Preserve completion alternatives and unknown premises; a bare atom number does not identify a proposition with its arguments and context. |
| Alghanem `docs/adr/0122-baqi.md` and `tests/test_baqi.py` | Same Alghanem revision | Remove equal duplicate plans, state the positive-formula limitation, and check the exact finite test domain using an independent completion oracle. |

Neither earlier formal module establishes the authenticity of arbitrary masks.
Mashru explicitly leaves the connection to sealed deposits open. Alghanem
explicitly names `ATOM_IS_NUMBER_NOT_PROPOSITION`,
`ADNA_KEEPS_EQUAL_DUPLICATES`, and `POSITIVE_FORMULAS_ONLY` as limits. NABT
addresses proposition identity and equal-plan duplication here. Support
authentication belongs to the source checker. Positive-only syntax and
independent-atom semantics are explicit limits of this version.

## Identity before arithmetic

A `Proposition` has seven required, immutable string fields:

| Field | What must remain bound |
| --- | --- |
| `name` | The named predicate or premise. |
| `source` | The source identity used for this claim. |
| `occurrence` | The exact occurrence or argument position. |
| `reading` | The selected reading or analysis. |
| `context` | The context in which this claim is evaluated. |
| `definition` | The definition or rule version giving the premise its meaning. |
| `policy` | The policy version under which the premise is admitted. |

Every field participates in equality and the proposition fingerprint. These
fields are opaque identities: a string that resembles a hash does not
authenticate a source. Distinct sources, occurrences, readings, contexts,
definitions, and policies remain distinct even when display names coincide.
No normalization or equivalence between these identities is guessed.

`PropositionRegistry` snapshots and sorts full identities, rejects duplicate
identities, and assigns bit `i` to entry `i`. Input order therefore does not
change the registry, masks, or replay identity. A mask is meaningful only with
this registry and `nabt.named-positive-obligations.v1`. Masks cannot contain
bits outside the declared registry. Python booleans, floats, negative numbers,
and strings are rejected wherever natural-number masks or budgets are needed.

An `Atom` contains a full `Proposition`, not a name or an integer. Compilation
requires an exact registry match. References to two or more contexts fail with
`CONTEXT_MISMATCH` unless `allowed_contexts` explicitly includes all of them.
Unreferenced registry entries do not combine contexts. Context permission is a
declared computational boundary; it is not proof that a linguistic rule may
transfer evidence between contexts.

## Support and the residual family

The supported syntax is `Constant(True)`, `Constant(False)`, `Atom`, `And`,
and `Or`. `all_of(*terms)` and `any_of(*terms)` build explicitly finite
conjunctions and disjunctions. Empty conjunction is true; empty disjunction is
false. There is no syntactic negation or implicit quantifier over an open world.

Inputs contain separate positive and negative support masks, `K` and `D`.
Neither mask is synthesized from an absent mark, absent record, low score, or
unknown premise. For an atom relevant to the formula:

| Positive support | Negative support | Meaning |
| --- | --- | --- |
| Absent | Absent | Unknown; a positive completion may supply this premise. |
| Present | Absent | Positively supported. |
| Absent | Present | Negatively supported; positive completion cannot supply it. |
| Present | Present | Conflict; stop before projection. |

Relevant means *occurs in the declared syntax*, including an atom under an
absorbing true/false branch. Thus `TRUE OR A` and `FALSE AND A` both report a
conflict when `A` has support on both sides. Simplifying first must not erase
that evidence conflict. Conflict outside the formula's atoms does not change
this claim's status, but appears in `out_of_scope_conflict_mask` and
`out_of_scope_conflicts`. No claim about the consistency of the whole registry
follows from a conflict-free result for one formula.

With no relevant conflict, the residual family `M` follows these laws:

- `M(TRUE) = {0}` and `M(FALSE) = {}`.
- `M(A) = {0}` when positively supported, `{}` when negatively supported,
  and `{bit(A)}` when unknown.
- `M(A AND B) = Min({x OR y : x in M(A), y in M(B)})`.
- `M(A OR B) = Min(M(A) union M(B))`.

Here `OR` between masks is bitwise union. `Min` first removes equal duplicates,
then removes every plan that strictly contains another sufficient plan. Every
returned plan is a set of additional positive premises; it cannot override
negative support. Plans retain their correlations. For example,
`(A OR B) AND (A OR C)` has the alternatives `{A}` and `{B,C}`. It does not
license the singleton plans `{B}` or `{C}`.

Projection is explicitly scoped to this finite formula:

| Result status | Projection | Residual meaning |
| --- | --- | --- |
| `LICENSED` | `P` | The unique minimal plan is the empty mask `0`. Supplied positive premises suffice. |
| `REJECTED` | `N` | No admissible positive completion of this formula exists under the supplied negative premises. |
| `PENDING` | `U` | Nonempty minimal completion plans remain. |
| `CONFLICT` | None | Relevant support contradicts itself; no completion-family projection is asserted. |

`CONFLICT` reports full named conflict residuals and
`plans_complete_within_declared_formula = false`. Its empty plan tuple must not
be read as `REJECTED`. A successful, conflict-free computation has the complete
minimal family for its declared formula and support. `REJECTED` is not a
general linguistic or real-world negative judgment.

A finite universal claim may be represented by `all_of` over its **declared
complete finite atom list**. Its completeness is conditional on that list and
the supplied definition of the claim. The engine neither discovers missing
members of an open domain nor infers that an unobserved proposition is false.
There are also no extra mutual-exclusion constraints between atoms in this
version; a returned mathematical plan is not a proof of joint real-world
realizability.

## API

```python
from nabt.obligations import (
    Proposition, PropositionRegistry, Atom, And, Or, compile_obligations,
)

def named(name):
    # Demonstration identities; they make no source-authentication claim.
    return Proposition(
        name=name, source="demo-source:v1", occurrence="word:3",
        reading="reading:one", context="context:one",
        definition="definition:" + name, policy="policy:v1",
    )

a, b, c = (named(name) for name in ("A", "B", "C"))
registry = PropositionRegistry((a, b, c))
formula = And(Atom(c), Or(Atom(a), Atom(b)))
program = compile_obligations(formula, registry)

result = program.evaluate(positive_mask=registry.mask((c,)), negative_mask=0)
assert result.status == "PENDING"
assert {plan.names for plan in result.minimal_plans} == {("A",), ("B",)}
assert set(result.minimal_plan_masks) == {registry.bit(a), registry.bit(b)}
payload = result.as_dict()
```

`evaluate_obligations(formula, registry, positive_mask, negative_mask, ...)`
is the one-shot equivalent. `minimal_plans` retains full identities;
`plan.names` is only a display convenience and must not be used as a binding
key. Serialization includes masks, named plans, relevant and out-of-scope
conflicts, the registry identity, the program identity, and the replay identity.

The program identity binds the version, canonical registry, exact syntax, and
explicit context permissions. The replay identity additionally binds both
support masks, including their out-of-scope bits. These are reproducibility
identifiers, not signatures, source receipts, or authority to accept evidence.
Operational budgets do not change a mathematical program's identity.

## Replay at consumption

Compilation snapshots named syntax, full registry keys, context permissions,
and budgets into a primitive tuple structure. `evaluate` and the program's
`as_dict` rebuild a fresh validated program from that snapshot, compare every
public derived field, and use the rebuilt program. They do not trust the
immutability annotation or a stored digest by itself.

This detects forced mutation of instructions, relevant masks, named identities,
registry hashes, context metadata, limits, and program hashes. Such mutation
raises `INVALID_COMPILED_OBLIGATIONS`. Replacing instructions by `TRUE` and
supplying a matching replacement digest cannot replace replay of the original
bound syntax. Reconstruction from an entirely different coherent set of
inputs is a different mathematical query; no query authenticates its own
linguistic premises. A trusted consumer must obtain and check those inputs
through its source boundary.

## Bounded work and output

`Limits` makes successful completeness conditional on finishing within the
declared operational budget. The defaults are:

| Budget | Default |
| --- | ---: |
| Registry atoms | 256 |
| Syntax nodes | 8,192 |
| Syntax depth | 128 |
| Minimal plans in an intermediate family | 4,096 |
| Total candidate plans considered across expansions | 100,000 |
| Total containment comparisons | 1,000,000 |
| Result serialized as compact UTF-8 JSON | 8,000,000 bytes |

There are also hard configuration ceilings, a 4,096-atom registry ceiling,
an 8,192-byte limit for each identity field, and a 2,000,000-byte raw identity
budget for the registry. A Cartesian-product size is checked **before** its
candidate masks are constructed. Equal masks are deduplicated before
containment comparisons. The source AST is traversed iteratively, with depth,
node-count, and cycle checks.

Plan count alone does not bound serialization: repeated long identities can
make a small family very large. Result preflight therefore computes the exact
compact UTF-8 JSON size by caching each identity's encoded size and adding its
repetitions arithmetically. It includes JSON escaping of control characters.
It stops when the byte limit is exceeded, without allocating the expanded JSON.
Both `evaluate` and result `as_dict` enforce this limit. Caller-selected pretty
printing or a different character-escaping convention may produce a larger
external representation than this explicitly defined compact encoding.

Every exhausted work or output budget raises
`NabtError(code="RESOURCE_LIMIT", status="DEFER")`. It does not return a
truncated family labelled complete, a negative projection, or a linguistic
rejection. Malformed inputs use separate named `NabtError` codes. Error status
`REJECT` means the input/request was rejected; result status `REJECTED` denotes
the finite-formula algebra described above.

## Formal scope and independent verification

`formal/Nabt/Obligations.lean` compiles with Lean 4.34.1 and imports only `Std`.
Its structural theorems quantify over every finite positive formula, rather
than a fixed small enumeration. Its bitmask theorems quantify over natural
number masks. The principal results are:

| Theorem, under `Nabt.Obligations` | Actual scope |
| --- | --- |
| `identity_context_isolation`, `identity_source_isolation` | Different named-identity fields prevent equality. |
| `Formula.eval_monotone` | Growing positive support preserves truth for positive formulas. |
| `Formula.eval_ext_on_atoms` | Assignment outside a formula's atoms does not affect its value. |
| `union_submask_iff`, `covers_conjoin`, `covers_append` | Bitmask conjunction and disjunction preserve the represented completion sets. |
| `covers_eraseDups`, `covers_minimal` | Equality deduplication and inclusion minimization preserve those sets. |
| `plans_cover_iff` | A negative-disjoint completion succeeds iff it contains a compiled plan. |
| `plans_avoid_negative`, `plans_sound` | Every compiled plan avoids negative support and suffices. |
| `plans_complete` | Every admissible successful completion contains a compiled plan. |
| `plans_antichain`, `plans_minimal_success` | Returned plans are inclusion minimal; no strictly smaller admissible successful plan exists below one. |
| `plans_empty_iff_no_completion`, `projection_rejected_iff` | Empty family means no admissible positive completion of this particular formula. |
| `projection_licensed_iff` | The internal licensed projection agrees with truth under positive support alone. |
| `conflict_precedes_projection`, `conflict_free_projection` | The public mathematical wrapper checks relevant conflicts before projecting. |
| `unknown_atom_pending` | A wholly unknown atom is pending at every bit position. |

The internal projection theorems describe `project(plans(...))`; public
assessment additionally uses `hasConflict`. The separate wrapper theorems
make that premise explicit. No theorem equates a SHA-256 fingerprint with an
authenticated source or proves that a textual identity names a true claim.
Python parsing, snapshot replay, serialization budgets, and the registry-to-bit
assignment are runtime checks, not a claim of extracted or fully verified
Python execution.

`tests/test_obligations.py` uses an independent oracle: enumerate subsets of
unknown **full identities**, evaluate ordinary truth, and retain sufficient
sets minimal under strict set inclusion. It does not call the production
residual recurrence or minimizer. The exact finite test domain is 2,596
distinct syntactic formulas of depth at most two on `TRUE`, `FALSE`, `A`,
and `B`, with all 16 two-atom support environments, including conflicts:
41,536 formula/environment comparisons. Another 250 deterministic larger
formulas use up to six atoms.

Counterexamples and boundary tests cover equal-plan duplication, alternative
correlations, unknown versus negative support, conflict before absorbing
constants, out-of-scope conflict visibility, every proposition identity field,
context mixing, strict number domains, cycles, registry order, forced mutation,
preflight of exponential alternatives, exact output-byte boundaries, control
character escaping, and the long-identity serialization expansion. These
finite tests complement the Lean results; they do not turn a bounded test
domain into a theorem about all Python executions or all Arabic claims.
