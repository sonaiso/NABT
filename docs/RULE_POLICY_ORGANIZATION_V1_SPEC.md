# Rule and policy organization v1 — preimplementation contract

Baseline: `181dec466ccfad5b6a63ec9750f149ea58829eda`.

The user requires rules and policies to be organized before extending operator
receipt projection and the original grammar-application bridge. The repository
already has concept definitions, finite guard learning, inquiry, source
admission, qualified inference, signed certificates, and evidence revision.
This tranche organizes their references; it does not supply the still-open
candidate-rule adoption bridge.

## 1. Existing owners and observed defect

The existing `tools/entropy_framework/registry.json` declares `rule_contract`
and `evidence_freshness`. Before this change, `validate_registry` ignores both.
The retained preimplementation observations demonstrate that deleting either
contract or substituting an unsupported operation vocabulary still returns
valid metadata. The validator already returns `semantic_authority=NONE`;
this is a consistency gap, not evidence of a semantic-authority bypass.

Authoritative owners remain:

- `formal/theorems.json` and the compiled catalogue selected through
  `integrations/current_proof_references.mk` for declaration references.
- The existing `reuse` families and allowlisted entrypoints for navigation.
- `tools/grammar_catalog/catalog.py` for fresh, source-bound catalogue records.
- Existing inquiry, learning, evidence, inference, lifecycle and application
  checkers for their respective operational judgments.

No second rule body, theorem manifest, source registry, dispatch table,
interpretation engine, confidence scale, or action-authorizer is introduced.

## 2. Validate the already-declared base contracts

`validate_registry` and the explicit organization entrypoint shall require the
installed `rule_contract` and `evidence_freshness` shapes. The existing required
field names, five operation kinds, freshness identity names, and fixed policy
invariants are code-owned constraints. A submitted contract cannot shrink its
own required set or replace its operation vocabulary with an authority grant.
Use existing strict scalar/type/duplicate/resource validation helpers.

The five operation kinds remain `FILTER`, `TRANSFORM`, `BIND`, `INFER`,
`MEASURE`. They do not specify a semantic role or an epistemic rank.

Registry schema `nabt.entropy-framework.registry.v2`, version `0.2.0`, remains
supported. A valid legacy registry may omit the newly versioned organization;
it may not omit either already-declared base contract. Standard `reuse`
navigation remains compatible with its existing minimal navigation fixtures.
Ordinary registry validation checks organization structure only, reporting
`DECLARED_REFERENCES_NOT_RESOLVED` or `NOT_DECLARED`. Owner resolution is
performed only by the explicit organization view; structural validity must
not be described as a successful owner lookup or native check.

## 3. Reference-only organization in the existing registry

The optional `rule_contract.organization` object has exactly:

```json
{
  "schema": "nabt.rule-organization.references.v1",
  "profiles": [],
  "relations": []
}
```

Each profile has exactly these fields:

```json
{
  "id": "authored-profile-id",
  "role": "FORMATION_METHOD",
  "operation_kind": "FILTER",
  "subject": {"kind": "reuse_family", "id": "rule-learning"},
  "family_ids": ["rule-learning"],
  "scope": "Authored organizational scope annotation.",
  "phase_contract_refs": {
    "formation": [],
    "adoption": [],
    "application": [],
    "revision": []
  }
}
```

`operation_kind` may be null when no operation is claimed. `role` is one of:

- `DEFINITION_OR_TYPE`
- `FORMATION_METHOD`
- `LANGUAGE_INTERPRETATION_RULE`
- `INFERENCE_LICENSE`
- `EVIDENCE_ADMISSION_POLICY`
- `NORMATIVE_ACTION_POLICY`
- `EVALUATION_GATE`

A reference is exactly `{kind, id}`. Supported kinds are `catalogue_rule`,
`reuse_family`, `compiled_declaration`, `framework_contract`, and
`evaluation_gate`. Framework contract identities are `rule_contract`,
`evidence_freshness`, and `release_policy`. Other identities must resolve
through their existing owners. Caller-supplied path, source hash, version,
scope, approval, authority, or executable overrides are invalid fields.

The profile's scope is an authored annotation. Resolution preserves the
owner's scope independently and returns `scope_relation_established=false`.
The tool does not prove natural-language scope equality or containment.

Phase references name relevant contracts. They are not observations that
formation, adoption, application, or revision actually occurred. A correct
reference does not establish historical formation evidence, a current adoption
decision, case witnesses, source authenticity, or an external-world bridge.

## 4. Typed organizational relations

Each relation is exactly `{from, to, kind, phase}`. Both endpoints are profile
identities; phase is `formation`, `adoption`, `application`, or `revision`.

Kinds are `JUSTIFICATION`, `PREREQUISITE`, `REFERENCE`, `CONFLICT`, `INFERENCE`.
They are authored navigation statements, never executable proof edges.
For `JUSTIFICATION` and `PREREQUISITE`, direction is consumer to prerequisite.
Their combined subgraph must be acyclic, using the existing dependency-order
checker. A cycle split across the two kinds is still a cycle.

Reference, conflict and inference edges may have cycles and remain visible.
Do not apply one DAG constraint to all relations. No transitive inference,
causal law, policy priority, conflict resolution or rule execution follows from
these labels. An unsupported inference-rule cycle remains governed by the
existing inference engine, not by this organizational graph.

Duplicate profiles, duplicate exact references within a list, duplicate
relations, dangling endpoints, malformed values and unknown fields are errors.
Budgets must remain explicit; exhaustion is a resource result, not proof that
the referenced rule, language, concept or policy is invalid.

## 5. Derived report through the existing entrypoint

Add `python -m tools.entropy_framework reuse --organization`, mutually
exclusive with `--family`, `--module`, and `--run`. Existing `--summary` and
append-only `--output` behavior remain available. No registry content is run
as a command and no new dispatch entry is necessary.
The compact summary uses `nabt.rule-organization.summary.v1` and the same
authority/status/nonexecution boundaries. `--output` always stores the full
report, including when the displayed view is a summary.

Report schema is `nabt.rule-organization.report.v1`. Every report retains:

```json
{
  "status": "RESOLVED",
  "authority": "ORGANIZATIONAL_REFERENCE_MAP_ONLY",
  "semantic_authority": "NONE",
  "action_authority": "NONE",
  "runtime_execution_performed": false,
  "scope_relation_established": false
}
```

Other report fields are `base_contracts`, `organization_schema`,
`organization_sha256`, `profiles`, `relations`, `prerequisite_order`,
`role_counts`, `catalogue`, `families`, `inputs`, and `limits`.

Profiles preserve authored fields and add `subject_owner`,
`resolved_phase_contract_refs`, `capability_links`, `lifecycle_evidence`, and
`scope_relation_established`. All four lifecycle evidence entries are
`NOT_OBSERVED`; referenced contracts must not turn them into successful events.
Resolution preserves current owner identity, source/proof boundaries and
source-review status. A recorded compiled snapshot is not a new kernel run.

The catalogue population is the complete existing source catalogue. Retain
each original row, its exact owner scope, profile IDs and mapping status.
Only direct `catalogue_rule` subjects classify that record; a family reference
or phase reference does not silently classify every related rule. Mapped and
unmapped ID sets must be disjoint and cover the original population exactly.
Their counts are organizational coverage, not Arabic coverage, proof counts,
or evidence that an unmapped capability is unimplemented.

When organization is absent, status is `NOT_DECLARED`, its digest is null,
profiles and relations are empty, and catalogue records remain unmapped.
Absence of declared organization is distinct from a deferred runtime judgment.

## 6. Initial bounded slice

The initial eleven profiles reference finite guard learning, inquiry review,
property/schema identities, source-record admission, explicit concept definition,
morphological word-kind definition, a retained textual-discrepancy operator,
signed model soundness, evidence revision, freshness and lifecycle evaluation.

Two direct catalogue subjects are:

- `nabt.morphology.source-policy.v1::word_kind`
- `nabt.classical-rule-inventory.v1::ASSIM-NUN-B-BLOCKED-TEXT`

The latter retains `source_status=textual_discrepancy` while its installed
conditional runtime reference remains visible. Neither status substitutes for
the other. No positive action-authorizing profile is invented. The unclosed
finite-candidate-to-adopted-rule handoff remains an explicit design obligation.

## 7. Independent acceptance and verification

Freeze the authored acceptance matrix before implementation. It covers base
contract omission/weakening, exact owner resolution, unknown/dangling/duplicate
references, scope separation, forbidden identity overrides, typed cycles,
authority/execution injection, legacy omission, complete catalogue population,
and order-preserving identity/coverage invariants.

Keep current learner/inference/source/bridge tests as their respective semantic
oracles. The new tests must not duplicate their implementations or claim to
prove new formation/adoption semantics. Exercise the actual existing entrypoint
and validate error exits as well as successful reports.

Preserve the existing 90-file oracle dependency freeze, runtime freeze,
Makefile, main CI workflow, frozen source policies, historical observations and
preimplementation specification. New tests should use the existing discovered
test path and, where needed, the established capability-reuse workflow.

After organization, two bounded workstreams can proceed: candidate-rule
adoption/application with independent justification; and operator condition/
example projection followed by the actual grammar-application tree and
`CertifiedBridge` obligations. Already installed operators need not wait for
general rule discovery. Their integration requires explicit shared rule and
application identities. Neither this report nor a new field name discharges
those obligations.
