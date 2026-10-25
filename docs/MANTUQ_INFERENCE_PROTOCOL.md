# Conditional inference request v1

The optional `tools.mantuq_inference` adapter evaluates explicit structured
assumptions. It does not parse those assumptions out of the supplied Arabic text.
The installed source inventory determines method profiles; it does not certify
the classification, legal ruling, causal relationship, or empirical truth of a
new occurrence. No language-model API is called.

```sh
PYTHONPATH=src python -m tools.mantuq_inference catalogue
PYTHONPATH=src python -m tools.mantuq_inference search 'مفهوم المخالفة'
PYTHONPATH=src python -m tools.mantuq_inference evaluate examples/mantuq_inference_guarded.json
PYTHONPATH=src python -m tools.mantuq_inference pipeline 'السبب والشرط والمانع' examples/mantuq_inference_plans.json --limit 1
PYTHONPATH=src python tools/check_qualified_inference.py
```

The last two commands require the pinned Lean executables `verifiedReading`,
`classicalSemanticProbe`, and, for conformance, `exportQualifiedInference`.
Use the repository's pinned Lake toolchain to build those targets. Missing or
failed native verification cannot produce `SUPPORTED`.

Every request has exactly these required fields:

| Field | Meaning |
| --- | --- |
| `schema` | `nabt.mantuq-inference-request.v1` |
| `policy_id` | One of the nine installed policy IDs below |
| `binding` | Exact `source_id`, `source_text`, `scope`, `context`, `time` strings |
| `conclusion` | A signed atom: `predicate`, `arguments` string array, `positive` boolean |
| `readings` | Nonempty array of every supplied alternative interpretation |

For opposition, `contrast_kind` is additionally required: `attribute`,
`condition`, `endpoint`, or `number`. The source profile rejects `name` and
`innama` as sufficient licenses for opposition. This is the selected source's
classification, not an assertion of universal agreement among schools.

A reading has `reading_id`, `requirements`, `hypotheses`, and `bridge`.
Each requirement has `slot` and `atom`. Hypotheses are signed atoms, or `null`
when the entire reading is incomplete. Missing evidence is represented by its
absence from `hypotheses`; removing a mandatory requirement is malformed input.
Distinct slots cannot alias the same unsigned proposition. Extra independent
guards may use `condition:<name>` or `blockerAbsence:<name>`.

| Policy | Mandatory slots |
| --- | --- |
| `matching` | `premise` |
| `inclusion`, `requirement`, `alert`, `allusion`, `agreement` | `premise`, `transferBridge` |
| `opposition` | `premise`, `necessaryBridge`, `qualified`, `countertextAbsence`, `usualCaseAbsence` |
| `guarded_cause` | `cause`, `condition`, `blockerAbsence` |
| `analogy` | `originRuling`, `sharedCause`, `transferBridge`, `condition`, `blockerAbsence` |

Every blocker-absence slot requires a negative atom. `qualified` requires a
positive atom. The absence of a positive blocker observation is insufficient:
the negative proposition must be explicitly present. A blocker applies to this
declared causal path; it does not establish that every other cause is blocked.

The bridge is either `null` or:

```json
{"body": ["the exact requirement atoms in declared order"],
 "head": "the exact requested conclusion atom",
 "basis": "caller_assumption"}
```

The strings above describe positions; the actual payload contains atom objects.
The adapter never fabricates this implication from satisfied slots. Merely
naming an atom `transferBridge` or `necessaryBridge` supplies no semantic proof.
The full implication must still be supplied, and its truth remains a hypothesis.

An opposition reading also needs `necessary_relation`, either `null` or an
object with `kind: "necessary"`, `antecedent: Q`, `consequent: P`, and
`basis: "caller_assumption"`. Both `Q` and `P` must be positive atoms, the
`premise` requirement must be the explicit opposite of `P`, and the requested
conclusion must be the opposite of `Q`. This checks the shape of the conditional
argument `Q → P, ¬P ⊢ ¬Q`. A forward rule `P → Q` cannot be substituted. The
relation's interpretation and truth are still explicit assumptions; no source
classification is inferred from a vector score or a surface conditional token.

`evaluate(payload, budget=EvaluationBudget(...))` returns:

| Status | Meaning |
| --- | --- |
| `SUPPORTED` | All supplied readings have clean required support, explicit bridges, and a native conditional consequence certificate |
| `UNKNOWN` | An obligation, bridge, typed necessity relation, or complete reading is missing |
| `REFUTED` | A required premise is explicitly opposed, or this source profile disallows the contrast; this does not negate the requested conclusion |
| `CONFLICT` | A relevant proposition has support for both signs, including a derivable conclusion opposed by an explicit hypothesis |
| `INCONSISTENT_READINGS` | Some supplied readings support the application and others oppose its requirements |
| `INVALID` | Malformed or uninstalled input, aliasing slots, changed bridge, or unauthorized fields |
| `RESOURCE_EXHAUSTED` | A declared count bound or native verification timeout was reached |
| `SOURCE_ERROR` | Installed source replay failed |
| `VERIFICATION_UNAVAILABLE` | Native verification could not certify the consequence |

`declared_request_scan_complete` refers only to this selected policy's supplied
readings. It does not enumerate Arabic interpretations. The separate hybrid
pipeline scans all installed policy IDs even when display ranking omits a policy.
Missing policy plans remain unknown.
The `pipeline` input file maps each selected policy ID to its complete structured
request. `--limit` affects displayed search candidates only; `--max-policies`
limits the actual scan and produces explicit resource exhaustion when incomplete.

The native proof operates on a `generated_assumption_transcript`. It includes
the caller's signed hypotheses and explicit bridge, encoded as bounded controlled
language. The exact source/context/time binding is included in each atom's
identity and retained in a lookup. The native checker rereads the generated bytes
and checks the signed proof and finite closure. Hash collisions within the atom
lookup fail closed; collision freedom is not a mathematical theorem here.

Consequently `world_truth_established`, `semantic_bridge_proved`,
`occurrence_classification_proved`, `source_to_requirements_proved`,
`reading_enumeration_proved`, and `all_arabic_complete` remain false even when the
conditional result is supported. The 3,034 native/Python conformance cases are a
finite implementation check, separate from Lean's general conditional theorems
and from Arabic-language evaluation.
