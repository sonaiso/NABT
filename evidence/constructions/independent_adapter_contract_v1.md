# Construction evaluator representation contract v1

The gold freeze is `5e4e9856b00ee648888e58c84e62c0a334cd3875d14cea326273d7c0f732254e`.
This adapter description was written after freezing those inputs and before the
first prediction run. It does not amend the gold or grant new source authority.

The public entry points are `read_discourse`, `ask_discourse`, `verify_discourse`,
and `verify_discourse_answer`. A fresh process loads an approved immutable runtime
and the frozen authored lexical TSV. The source model receives no expected case,
role, dependency, semantic result, or answer. Runtime manifests require explicit
manifest/snapshot/archive pins and exact authoritative inventory, before and after
measurement. Results, raw reports, runtime plus evaluator archives are new files.

## Explicit representation correspondences

- `zanna_subject` is the neutral gold `active_subject` of the matrix cognitive
  verb; its own source governor and raf assignment remain mandatory.
- Gold relation `zanna_predication` uses the explicit public operator relation's
  object1/object2 endpoints. Gold `clausal_predicate` uses the kada operator's
  complement span and separately exposed inner verb span. Local nasb and inner
  verb raf/nasb remain independent checks.
- A preposition dependency may be represented by the explicit public assignment
  role plus `head_span` and dependent `span`. The adapter does not infer it from
  adjacency or expected positions.
- The nominal-subject assignment has no governor in the baseline API. Its
  reciprocal predicate assignment explicitly points to that subject. That
  observed endpoint is accepted for the gold's two-sided nominal relation.
- Closed operator lemmas may be exposed without short marks. Only those closed
  operator spellings use the transparent mark-removal correspondence; content
  predicates, roots, entity IDs, and general source text retain exact identity.
  `PERF`/`IMPF` map to `perfect`/`imperfect`; `inception` maps to `onset`.
- Within an explicit operator scope only, `relative_to_operator` represents no
  independently specified embedded nominal tense, and `relative_nonpast`
  represents the imperfect inside kada. A nominal kana-sister complement may
  repeat the outer operator tense; it is the same inherited tense, not a second
  independent date. Root confirmed this interpretation before measurement. The
  outer operator tense is compared explicitly, and query proof equality still
  compares every original field, including the embedded representation. No
  mapping here permits a scoped proposition to become an unqualified fact.
- The three frozen temporal labels map only from their exact qualified lexical
  representation. `اليوم` is not collapsed with indefinite `يومًا`, and no
  general article, hamza, word, or root normalization is introduced.
- A licensed stem endpoint may occupy the declared source occurrence's explicit
  stem subspan. Arbitrary substrings are rejected. An accusative-alif reference
  must retain its written source span and tie the base spelling to the same
  carrier-qualified reading and source receipts; no blanket alif deletion occurs.

## Safety and measurement

Source/context hashes and every byte span are verified. Analysis, clause, report,
reference, and answer identities are recomputed independently. A source receipt
must cover a full original lexical record. Roles, cases, signs, governors,
references, semantic predicates, and accepted proofs are correlated within the
same analysis. A separate coherence check prevents combining separately passing
role and dependency observations from different alternatives.

Question validation uses the original independently read question, viable
analyses, complete qualified claim equality, proof signs and binding domains.
Replay success remains a separate six-case denominator. The comprehension
denominator remains 80; its 100 questions are also split by expected outcome.

The command is:

```sh
python tools/construction_evaluation.py \
  --runtime-root PATH \
  --runtime-freeze PATH \
  --output NEW_RESULT_FILE
```

Default behavior is strict: exit zero requires all 86 cases, no false acceptance,
and no runtime/adapter execution errors. There is no premeasurement waiver list.
Any later gate exception needs an explicitly reviewed runtime pin, case ID, and
failed-check signature, while preserving the strict coverage result. An output
with execution errors is marked `measurement_valid=false`; its raw false-accept
count must not be interpreted as evidence of absence of false acceptance.
