# Native governor contracts and numerical interoperability

## Scope and source

`Nabt.Governors` is native NABT code. Its finite inventory and equations adapt
the MIT-licensed pinned Mashru modules described in
[MASHRU_AWAMIL_AUDIT.md](MASHRU_AWAMIL_AUDIT.md). The copyright and permission
notice are retained in [NOTICE.md](../NOTICE.md). No Mashru import, checkout,
network access, or runtime process is required by the installed model.

The law ID is `nabt.governors.v1`. Its source table has 100 ordered rows,
96 distinct exact labels and 13 classes. These are inventory properties,
not Arabic coverage scores. Class lookup does not normalize a surface word
or establish a class's activation conditions. In particular, metalinguistic
labels such as `حتى (جر)` must not be treated as a tokenizer vocabulary.

## Mathematical types and numerical identity

`Case` has four constructors with codes 0=nasb, 1=raf, 2=jarr, 3=jazm.
`Role` has nine constructors with the upstream codes 0,1,2,6,9,10,11,12,13.
Its grammatical category is noun or verb. `GovernorClass` is a closed type
with codes 1 through 13. Decoding an unknown code returns `none`, unlike
the upstream natural-number equation function's empty-constraint fallback.

There are two different uses of a four-way code:

- `case_cell_mark` proves a numerical identity for a deliberately constructed
  NABT Cell: the mark component is the supplied case code. This is conditional
  on choosing the ordinary single-mark representation. It does not prove
  that a word's surface vowel invariably equals its grammatical case.
- `roleMarkNumber r c = 4 * r.code + c.code` encodes a syntactic-role/case
  pair in domain `nabt.governors.role-mark.v1`. Its inverse first divides by
  four, then decodes the role and residue. It is injective on the typed pair
  and bounded below 56. Codes belonging to unused role numbers are rejected.

The second number is not a Cell number. For example, the number 0 is a valid
primary-role/nasb code and a valid Cell code in a different domain; equality
of unqualified integers gives no permission to exchange these values.

All 36 typed role/case pairs can be encoded. Category admissibility is a
separate predicate: 27 are allowed and nine are not. The numerical codec
does not conceal this difference by deleting observable disallowed cases.

## Partial evidence, complete checks, and alternatives

The formal assignment has type:

```lean
Assignment := Role → Option Case
```

`none` means that no case observation has been supplied for that role.
It does not mean a negative observation or a false proposition.

For an equation `(r,c)`:

\[
\operatorname{checkEquation}(a,r,c)\iff a(r)=\operatorname{some}(c).
\]

For a link `(r,s)`, the complete check requires an actually observed common
case:

\[
\operatorname{checkLink}(a,r,s)
\iff \exists c,\;a(r)=\operatorname{some}(c)\land a(s)=\operatorname{some}(c).
\]

`checkAlternative` is the conjunction of every fixed equation and every
link. `Satisfies` is a separately stated proposition about the observations.
`checkAlternative_iff` proves their equivalence for arbitrary assignments,
equation lists and link lists. `completeAlternatives_exact` then proves:

\[
e\in\operatorname{completeAlternatives}(g,a)
\iff e\in\operatorname{equations}(g)\land\operatorname{Satisfies}(a,e,\operatorname{links}(g)).
\]

The separately named soundness and completeness theorems are the two
directions of that exact characterization. This is completeness of checking
the declared constraints. It says nothing about discovering all parses of
Arabic text.

`viableAlternative` leaves an equation unresolved when its role is unknown,
and leaves an equality link unresolved if either endpoint is unknown. It
rejects a constraint when the supplied observations conflict. Every complete
alternative remains viable (`completeAlternatives_retained`). No arbitrary
branch is selected when several alternatives survive.

| Observation supplied to class 2 | Complete alternatives | Viable alternatives |
|---|---|---|
| Both roles unknown | None | One, with both equations still needed |
| Primary unknown, complement raf | None | One, requiring primary nasb |
| Primary nasb, complement raf | One | The same one |
| Primary raf, complement nasb | None | None |

The checker tests only the equations and links of the class. An extra
unmentioned role does not affect the result. It does not globally revalidate
the category of every supplied role. `equations_closed` proves that the
constants imposed by the declared class equations are themselves
category-admissible; separate linguistic evidence must justify each input
role and the applicability of the class.

Classes 11 and 12 have an empty equation alternative and no equality links.
That empty alternative satisfies these case constraints vacuously. It is
**not** a parse, an active conditional or interrogative, a license to assert
content, or a world-truth judgment. Class 8 also has an empty equation
alternative but a nonempty equality link, so it still needs observations on
both linked roles for completion.

## What the 34 governor theorems establish

| Group | Representative declarations | Quantification and limit |
|---|---|---|
| Case and role identity | `case_decode_code`, `role_code_injective`, `case_cell_mark` | All values of the declared types; a representation contract |
| Numerical pair identity | `roleMark_decode`, `roleMark_injective`, `roleMark_bound` | Every typed role/case pair; no semantic inference from an untyped integer |
| Class identity | `class_decode_code`, `class_codes_exact` | Thirteen declared classes; unknown natural numbers have no class |
| Equation closure | `equations_closed`, `distinct_nasikh_equations` | The declared equations; not context-dependent activation conditions |
| Inventory | `inventory_rows_exact`, `inventory_labels_exact`, `ambiguous_labels_retained` | The explicit source-derived list, with duplicate labels preserved |
| Lookup | `lookup_exact` | Every row and exact label; lookup produces all matching table rows |
| Constraint checking | `checkAlternative_iff`, `completeAlternatives_sound`, `completeAlternatives_complete` | All assignments, alternatives and links within the stated model |
| Missing and contrary evidence | `unknown_equation_pending`, `conflicting_equation_rejected`, `completeAlternatives_retained` | Missing remains pending; observed disagreement removes an alternative |
| Conjunction | `conjunction_propagates` | Every finite chain length, given equal adjacent cases |

The proof count includes finite inventory witnesses and general contracts;
it is not a measure of language understanding. Four additional Program
theorems cover opcode 36, three distinct profile identities, and prevention
of entering a new profile from an already established theory/learner domain.
The existing generic opcode roundtrip and profile-compiler contracts now
range over the third profile as well.

## Executable export and conformance boundary

[ExportGovernors.lean](../formal/ExportGovernors.lean) exports:

- `schema_version`, `law_id`, `mark_codes`;
- typed `roles` and all 13 `classes`, including complete alternative and link lists;
- all 100 source-order `entries` with stable 1-based row IDs;
- `role_mark_number_domain` and all 36 `role_mark_codes`, each with a separate `allowed` flag;
- `assignment_probes`: 197 assignments enumerated over every role relevant
  to each class, with each role either unknown or one of four cases. A
  class has at most two relevant roles in this inventory. Each probe exports
  complete and viable alternatives from the actual Lean definitions.

The checked-in [governors.json](../src/nabt/data/governors.json) has the same
eight executable fields plus `source`. It does not contain the probes.
`source` is documentary provenance, verified through pinned Git blob bytes;
neither hashing nor the historical truth of its linguistic sources is a
theorem here. The exporter deliberately has no claim to create that authority.

The Python conformance boundary is comparison with Lean's executable export.
A matching result checks these finite observations of the implementation.
It does not prove a general refinement of the Python code, JSON codec,
Unicode decoder or text reader. Adversarial and held-out reading tests remain
necessary for those boundaries and must be reported separately.

## Validation performed for this transfer

Using the repository's `tools/bootstrap_lean.py`, the official Lean 4.34.1
archive was checked against its pinned SHA-256. The compiler identifies its
commit as `5045d0056413266e57c625dcd7c365b10e377c52`.

Executed successfully:

```bash
cd formal
lake build
lake env lean Audit.lean
lake env lean --run ExportGovernors.lean
lake env lean --run ExportArabicReading.lean
```

The complete native build succeeded. The theorem manifest and compiled audit
contain **296** declarations: the prior 258 plus 34 Governors and four Program
theorems. `Audit.lean` reported `NABT_AUDIT_OK` and only the permitted
`propext`, `Quot.sound`, and `Classical.choice` axioms. Every executable field
in `governors.json` matched the Lean export structurally; the export contained
197 assignment probes and 36 pair codes with 27 admissible flags. Existing
entry opcodes 30 and 35 remained unchanged, and opcode 36 exported
`nabt.arabic-governors.v1`.

These commands validate the formal layer and its export. Runtime reading
accuracy, certificate rejection tests and independent held-out results are
separate measurements; this document does not substitute for them.
