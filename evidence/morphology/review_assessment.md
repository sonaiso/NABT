# Independent morphology review

## Result and measured scope

The source-corrected material obtains **39 / 43 raw case successes**. The four
remaining cases are explicit conservative coverage limits: an unparsed clause
blocks approval of an earlier positive kind candidate. The candidate remains
present and the result is `DEFER`. The named regression gate permits exactly
that behavior in those four cases; it does not alter the raw score.

| Case family | Successful / total |
|---|---:|
| Conditional property-to-class inference | 16 / 16 |
| Missing information versus explicit negative evidence | 6 / 6 |
| Contradictory evidence | 3 / 3 |
| Separate readings of the same written lexeme | 2 / 2 |
| Duplicate reading identity rejection | 1 / 1 |
| Transfer to another lexical identifier | 2 / 2 |
| Retraction and recomputation | 2 / 2 |
| Certificate attacks | 5 / 5 |
| Temporal content versus time indicated by form | 1 / 1 |
| Other scope boundaries | 1 / 5 |

These cases measure a **controlled metalinguistic source dossier**. Its
descriptions provide conditional premises. The machine computes consequences
without a table assigning the desired answer to each test lexeme. The cases
do not establish that those descriptions are true of unrestricted Arabic,
that the system extracts them from ordinary prose, or that it independently
acquires an etymological derivation. A phrase such as `فعله مضارع` supplies a
tense label; the inference being tested is construction under the separate
nun context.

Nine additional review test methods pass, including the 43-case regression
contract as subtests. They cover the deliberately narrow boundary allowance,
numeric certificate tampering, source/scope identity, a built noun with a
conditional diptote cause, and refusal to turn a conditional sign into an
actual grammatical role. They are post-open adversarial tests, not hidden
accuracy measurements.

## Freeze, correction, and actual outputs

1. `independent_cases_v1.json` was frozen before the reviewer opened the new
   runtime and formal implementation. Its SHA-256 is
   `4425a249fe64b627c36671a39a88fec79ad8ac0c9f3ce710bab726045ccc2f81`.
   Pinned primary passages and exact test text bytes are included.
2. A source audit caught a real defect in the preliminary grammar: a
   reference to an event associated with time does not establish time
   indicated **by form**. Shakhsiyya j3 line 373 explicitly distinguishes
   these. Runtime/formal files had been opened by then, and executable
   policy/table files were not yet available for an earlier run.
3. V1 was retained. V2 adds the missing qualifier by one uniform substitution
   to ten inputs, keeps all 42 original expected outcomes, and adds the bare
   temporal-content counterexample. Its SHA-256 is
   `0f17e68a4d7a33d4afa64bb645ba88c55ac1d0e3248de241f1c1028442d37ea4`.
   **V2 is a source-corrected regression set, not an untouched holdout.**
   `review_grammar_erratum_v1.json` records the transformation.
4. The first actual runs remain in `review_first_v1_diagnostic.json`
   (**29 / 42**, under the stricter corrected grammar) and
   `review_first_v2.json` (**39 / 43**). Neither output was relabeled as a
   successful run.
5. A subsequent domain correction separated a conditional diptote-cause
   result from the actual class of an inflected noun. Evaluator version 1.1
   maps the frozen field `diptote_intrinsic` to the new, explicitly conditional
   `cause_prediction`. The generic projection and the unchanged gold are
   documented in `review_adapter_mapping_v1.json`. The first evaluator is
   retained as `review_evaluator_v1.py` for inspection.
6. `review_final_v2.json` records the post-review actual result, package and
   formal file hashes, loaded module origins, evaluator hash, case hash,
   per-property observations, and the elapsed time of that one run. Later
   release verification must rerun on the final package snapshot; a hash of
   a different snapshot is not interchangeable evidence.
   Evaluator 1.2 additionally enforces the frozen manifest
   `8449c5c4bf32549c6147de006b0586d41cb4c6f656e2764c63e3437a35b7bffd`,
   the exact runtime inventory and bytes, and all archived member bytes.
   The final 39 / 43 run passed those checks. The preceding 1.1 evaluator is
   retained as `review_evaluator_v1_1.py`.

## Four retained coverage limits

| ID | Unparsed clause | Required stronger behavior in the authored case | Current behavior |
|---|---|---|---|
| m12 | `آخره نون` | Preserve an approved kind while keeping the nun-dependent construction pending | Correct kind candidate retained; approval deferred |
| m13 | `هو اسم معرب` | Keep previously established noun kind; do not treat an output label as property-based acquisition | Correct noun candidate retained; approval deferred |
| m32 | `هو علم` | Keep noun kind; properness alone must not prove a qualified diptote cause | Correct noun candidate retained; approval deferred |
| m33 | `آخره ألف` | Keep noun kind; a bare final alif must not prove feminine alif | Correct noun candidate retained; approval deferred |

The reader cannot safely decide whether an unknown clause qualifies or
contradicts the earlier description, so it blocks approval. The release
allowance is deliberately narrower than accepting all deferrals: only these
four IDs, only the `kind` check, only the correct singleton candidate, and
only an explicit unparsed-source blocker are permitted. Every other check
must pass. A blanket-deferring implementation fails the positive cases.

## Contracts checked in source and code review

- Unknown evidence is distinct from denied evidence. The imperfect retains
  construction alternatives until its relevant nun context is supplied.
  Direct and separated emphatic nun are different contexts.
- A cause supported by the qualified diptote formula is separate from an
  actual diptote classification. The latter requires an established
  inflected noun. A built noun cannot acquire the class simply because its
  dossier supplies a strong cause trait.
- Al and idafa affect the **conditional genitive sign**. They do not delete
  the cause. The reader sets `applied_to_occurrence = False` and preserves the
  independent genitive-case requirement. Unknown source qualifications block
  nested sign approval too.
- The initial Lean actual-realization description required genitive
  government, while its type did not yet carry that premise. The final
  wrapper now takes a `GovernmentWitness` of `.jarr` for the same word. Its
  inflection evidence is also bound through `ConstructionWitness` to that
  word, rather than being a free enum argument.
- Nominal `jins_jamid` / `mushtaq` is the cited semantic division of a
  **universal noun**. It is distinct from root derivation, verb conjugability,
  physical solids, and syntactic role. The unsupported axes remain named.
- A report's source ID, full source hash, exact byte spans, reading identity,
  occurrence identity, and scope are checked. A certificate for another
  source, altered reading, altered conclusion, or unrelated support span is
  rejected. Malformed certificates produce structured failures.
- Canonical numeric encoding preserves the checked report. Changing a
  conclusion inside a newly encoded canonical number does not authorize it.
  The number's existence and size are not linguistic evidence.

## Limits of this review

The certificate verifier reconstructs the report from its source through the
installed reader. That rejects certificate tampering, but producer and replay
still share parsing logic. The separately authored source cases and the
finite Lean conformance table address different failure modes; neither turns
the shared parser into an independently proved natural-language reader.

The source-qualified diptote traits are premises, not automatically discovered
suffix interpretations. A negative result is relative to the installed
qualified factor model. No claim is made that all possible Arabic causes,
dialects, derivations, constructions, or exceptions have been covered.

The next independent proficiency measurement needs a separately reserved set
of ordinary Arabic source passages and expert annotations that are absent
from the extraction policy. It must measure extraction of the properties
themselves, preserve alternative readings, and replay changed or withdrawn
evidence. This review establishes the controlled bridge and its declared
boundaries; it does not substitute that future measurement.

## Reproduction

```sh
PYTHONPATH=src python -m unittest discover -s tests -p test_morphology_review.py -v
python tools/morphology_evaluation.py --material v1 --diagnostic --output evidence/morphology/review_v1_rerun.json
python tools/morphology_evaluation.py --material v2 --allow-documented-boundaries --output evidence/morphology/review_v2_rerun.json
```

Omit `--allow-documented-boundaries` to require every raw case expectation;
the current 39 / 43 result then exits unsuccessfully as it should. The
elapsed-time field is one observed execution, not a latency benchmark.
