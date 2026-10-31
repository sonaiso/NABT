# Meaning-preservation v1 — formal contract draft

Status: proposal agreed in scope and wire schema by the integration and runtime owners; **not an implementation** and not a proof result. This document is outside the repository until source/protocol and independent cases are frozen.

Base inspected: `sonaiso/NABT` at `3dbe335a21ac838db3717f03ca2a5b5889e16e54`; pinned `leanprover/lean4:v4.34.1`. Root AGENTS.md and CLAUDE.md apply. No nested instructions were found under formal/ or docs/. Existing historical `src/` and Makefile remain untouched.

## 1. Existing formal results to reuse

| Existing module / declaration | Actual scope | Consequence for this addition |
| --- | --- | --- |
| `RecursiveLicensedAlgebra.Tree`, `Seed` | Finite structural derivation trees, ordered children and registry-local rule IDs. | Reuse these trees instead of creating another morphology/syntax AST. |
| `RecursiveLicensedAlgebra.licensed_induction` | Constructor-local invariant induction on certified trees. | Do not repeat this result under a new name. |
| `RecursiveLicensedAlgebra.certified_realization_sound` | Surface/face property assuming every local realization contract. | Already establishes the generic local-invariant principle; new work must state actual semantic transport equations. |
| `RecursiveLicensedAlgebra.licensed_candidates_iff` | Exactly the licensed supported trees at a supplied finite height bound. | No new claim of all-Arabic enumeration. |
| `RecursiveLicensedAlgebra.every_finite_licensed_tree_eventually_generated` | Eventual generation of a finite licensed tree within the supplied inventory. | Does not establish adequacy/completeness of the inventory itself. |
| `RecursiveSourceBridge.CertifiedBridge` | Separate source, host, grammatical license, and realization alignment obligations. | Keep original-source reconstruction and semantic transport as separate obligations. |
| `ArabicCoverage.ExactWithin`, `exact_iff_sound_and_complete` | Equality of recognized and reference reading relations in an independently stated domain. | Reuse for the new conditional text-to-observation bridge. |
| `ArabicCoverage.exactness_transfers_with_reference_equivalence` | External adequacy is a separate equivalence premise. | Do not treat an installed law name as adequacy evidence. |
| `ArabicCoverage.no_single_interpreter_of_observation_collision` | A conflicting observation collision prevents a decoder correct everywhere. | Reuse for impossibility. Add only the missing sufficiency/unique-on-image characterization. |
| `ArabicCoverage.completeness_preserves_licensed_alternatives` | A complete reader retains all reference alternatives. | Preserve whole alternatives in the native contract; never form an independent Cartesian product. |
| `SourceSemantics.substitution_preserves_meaning` | Binder-free atom/conjunction/implication substitution under a given model. | Do not claim quantifier binding or capture avoidance has now been proved. |
| `SourceSemantics.consensus_all` | Agreement of all **supplied** candidates and exact bindings. | Candidate enumeration completeness remains separate. |
| `LexicalGraph.completed_exact` | Completed finite ground Horn closure equals derivability. | No duplicate closure engine. |
| `LexicalGraph.completed_model_sound` | Conditional on `factsTrue` and `rulesPreserve`. | Never convert transport or ledger acceptance into world truth. |
| `LinguisticTruth.usage_does_not_assert_world` | Linguistic usage classification supplies no arbitrary world fact. | Preserve this boundary in output claims. |

## 2. Proposed module and imports

`formal/Nabt/MeaningPreservation.lean`, namespace `Nabt.MeaningPreservation`, law ID `nabt.meaning-preservation.v1`.

Imports: `Nabt.RecursiveLicensedAlgebra` and `Nabt.ArabicCoverage`. The integration owner adds the module to `formal/Nabt.lean`, regenerates the theorem catalog and all source/proof crosslinks, and moves the seven current selectors together to a new evidence version. This agent does not alter selectors.

### 2.1 Partial semantic algebra and homomorphism

`PartialAlgebra (A : Type)` consists of:

- `seed : Seed → Option A`;
- `unary : Nat → A → Option A`;
- `binary : Nat → A → A → Option A`.

`eval` evaluates a finite existing `Tree`, retaining failure as `none`. This is a single-carrier partial algebra; separate semantic sorts may be represented by tagged values. This v1 does **not** claim a newly proved intrinsically typed signature calculus.

For algebras `A`, `B` and `h : α → β`, `Hom A B h` explicitly requires:

```text
map h (A.seed s) = B.seed s
map h (A.unary r a) = B.unary r (h a)
map h (A.binary r a b) = B.binary r (h a) (h b)
```

These are equalities of `Option` results, not equations merely conditional on successful source evaluation. They therefore include reflection of definedness on transported inputs. Target behavior outside the image of `h` is unconstrained.

Planned general theorem: `eval_transport` proves

```text
Option.map h (eval A tree) = eval B tree
```

by structural induction. A short corollary states that source and target evaluation are undefined together. No injectivity of `h` is assumed. The proof does not identify `none` with a meaningless Arabic expression; it means undefined by these supplied algebra operations. In particular the generic theorem does not claim that algebra definedness equals `RecursiveLicensedAlgebra.Certified`; such an application requires an independently supplied correspondence.

### 2.2 Independent observational fidelity

Let queries be `Q`, outcomes `O`, and independently specified observations be `observeA : α → Q → O` and `observeB : β → Q → O`.

`Faithful h observeA observeB` requires:

```text
∀ a q, observeB (h a) q = observeA a q
```

Planned theorem: `observed_eval_preserved` combines `Hom` with `Faithful`, retaining `none`, to prove exact equality of observed results for each query. Homomorphism alone is insufficient; the independent observation equation is a separate explicit premise.

Fidelity is relative to the supplied observation family. It does not prove that the query family contains every distinction needed by Arabic, a human reader, or all future contexts. Quotient composition requires congruence; raw agreement under a limited query family does not imply congruence. Do not silently introduce a quotient operator algebra.

### 2.3 Recovery and necessary distinctions

For `encode : X → R` and `query : X → Y`, define:

```text
FiberCompatible encode query :=
  ∀ x y, encode x = encode y → query x = query y

Image encode := { r : R // ∃ x, encode x = r }
```

Planned theorem: `unique_decoder_on_image_iff`:

```text
(there exists a unique d : Image encode → Y
 such that ∀ x, d ⟨encode x, witness x⟩ = query x)
↔ FiberCompatible encode query
```

The sufficiency proof may use ordinary Lean classical choice to select a witness of an image element; fiber compatibility proves witness independence. It is an existence/uniqueness theorem, **not an executable decoder extraction** or a cognition theorem. Restricting the decoder to the image avoids an unadvertised inhabitant/default assumption for unreachable representations. Empty source domains remain valid.

The previously proved collision impossibility is reused, not copied as a fresh mathematical contribution. A finite checker may compute compatible fibers for supplied rows; it does not prove the infinite premise from samples.

### 2.4 Conditional bridge to textual exactness

Reuse `ArabicCoverage.ExactWithin` with:

- an independently described input domain;
- a reference relation over complete source readings;
- a source recognizer exactly matching that relation in the domain;
- a target relation exactly equal to the image of the source relation under `h`;
- explicit independent observational fidelity.

The resulting target observation relation equals the reference observation relation within the domain. The theorem preserves the complete **joint reading** before observation; it does not obtain parser completeness by definition or manufacture joint readings from per-field marginals. Query values can themselves be complete functions/vectors, so correlations required by the contract are retained.

Any transfer to an intended reference still uses the existing separate reference-equivalence theorem. No new reference is declared to be all of Arabic.

## 3. Native boundary — agreed schema

Executable: `formal/MeaningPreservationV1Main.lean`, Lake target `meaningPreservationV1`. It imports the formal module and the existing bounded `ProbeJson` adapter. It is a finite contract checker, not a generic Arabic parser or external-truth oracle.

The request has exactly:

```text
{law_id: "nabt.meaning-preservation.v1",
 query_id: "joint-readings.v1",
 codec_id: "strict-json-packet.v1",
 cases: [Case],
 recipient_context: Context}

Case := {case_id: String, original: Packet, transported_payload: String}
Packet := {binding: Binding, source_context: Context, alternatives: [Reading]}
Binding := {source_id, revision, scope, source_text, convention}
Context := {speaker, addressee, time, place}
Reading := {predicate, subject: Term, object: Term|null,
            positive: Bool, tense, voice, force}
Term := {kind, value}
```

The installed codec actually parses `transported_payload` into a Packet. No independently supplied reconstructed reading or observation vector is accepted. The installed Python producer provides canonical JSON by default, but arbitrary valid JSON formatting is accepted on decoding. Fiber equality concerns the **entire transported string**, not an ID, hash, source label, or caller-provided equality claim. Two differently formatted strings are distinct representations even when they decode to the same observation.

`kind` is one of `entity`, `speaker`, `addressee`, `time`, `place`. Entity values are nonempty strings; all other term values are exactly `""`. Deictic terms resolve from the **source context**, never from recipient metadata. Their tags remain in the observation alongside resolved values; this version makes no pronoun/proper-name equivalence claim.

`tense` is `past|present|future|unspecified`; `voice` is `active|passive|unspecified`; `force` is `asserted|quoted|hypothetical|question`.

Every metadata string is nonempty and at most 512 UTF-8 bytes, except source_text, which is nonempty and at most 65536 UTF-8 bytes. Metadata forbids scalar values 0–31 and 127–159; source_text permits arbitrary strict Unicode. Whitespace-only metadata is permitted if it contains no forbidden control scalar; no trimming or normalization occurs. Arrays of cases and alternatives contain 1–64 entries. Duplicate case IDs and duplicate exact Reading objects are invalid. Alternative list order is immaterial.

The installed observation of a Packet is the **set of whole tuples**:

```text
(predicate, resolved-tagged-subject, resolved-tagged-optional-object,
 positive, tense, voice, force, binding.scope, binding.convention,
 source_context.time, source_context.place)
```

No field marginals or Cartesian product is used. In addition to preserving this observation set, the full binding and full source context must be exactly equal after decoding.

Native validation order is deterministic:

1. Strictly parse all originals and transported packets; reject duplicate **decoded** JSON keys, unknown/missing keys, malformed strings/booleans/enums, empty required arrays, and invalid UTF-8/surrogate escapes. Enforce 1 MiB request line, 1 MiB transported payload, JSON value depth at most 32 (root value at depth 0; each object field value or array element increases depth by 1), 64 cases/alternatives, and per-string limits. Apply preflight and duplicate-key validation to the inner transported JSON as well as the outer request.
2. Before per-case comparisons, test every pair of cases whose full transported strings are equal. Different original observation sets yield `CONTRACT_VIOLATION/FIBER_COLLISION`, with the first ordered pair as witness.
3. In input order, compare exact binding, source context, and observation set. The first failed obligation yields `SOURCE_BINDING_CHANGED`, `SOURCE_CONTEXT_CHANGED`, or `OBSERVATION_CHANGED` respectively.
4. Otherwise return `FINITE_CONTRACT_VERIFIED/ALL_FINITE_CONTRACTS_PRESERVED`.

The check core, including finite fiber compatibility and per-case preservation, belongs in `Nabt.MeaningPreservation`, not only in Main. `check_exact` relates the Boolean decision to its explicit Lean contract. A further theorem extracts `FiberCompatible` on the finite subtype of supplied cases. The codec/parser is an executable conformance boundary; this does not claim a proved JSON parser refinement.

The response has exactly:

```text
{schema: "nabt.meaning-preservation.native-response.v1",
 law_id: "nabt.meaning-preservation.v1",
 query_id: "joint-readings.v1",
 codec_id: "strict-json-packet.v1",
 status: String, reason: String,
 case_id: String|null, other_case_id: String|null,
 case_count: Nat,
 world_truth_established: false,
 whole_arabic_completeness_established: false}
```

Allowed statuses are `FINITE_CONTRACT_VERIFIED`, `CONTRACT_VIOLATION`, `INVALID_INPUT`, and `RESOURCE_EXHAUSTED`. Success witnesses are null. Parse/resource failures have case_count=0 and fixed reason `INVALID_REQUEST` / `RESOURCE_LIMIT` respectively. Per-case violations have only case_id, fiber violations have both IDs. Successful/violating semantic checks report the supplied case count. The native response cap is 8 MiB (the response is ordinarily much smaller).

The native executable accepts JSONL on stdin and emits one JSON result per request line. The ordinary runtime submits one canonical JSON line, so pretty-formatted request files are parsed by the outer CLI before this handoff. Native exit is 0 for finite verification or semantic contract violation, and 2 for invalid input or resource exhaustion. For a multi-line session, any invalid/resource request makes the final exit 2 while subsequent requests continue to receive independent responses.

The parent adapter must fail closed on absent native execution, malformed native response, or version mismatch. It must not convert a native error into a Python success. Empty/incomplete input rejection does not assert that an Arabic expression is meaningless. Positive verification applies to these finite packet encodings and supplied readings, not independent linguistic adequacy, all-Arabic coverage, author intention, or external truth.

## 4. Independent preimplementation matrix requirements

The oracle must be authored from this contract and direct mathematical examples, with no import of producer code and no recomputation using a copied recurrence. Preserve its first execution and subsequent exposed replays separately.

| Family | Required independently expected controls |
| --- | --- |
| Local algebra contracts | Correct transport; unary and binary argument order; undefined source preserved; target incorrectly defines a source-undefined operation; homomorphic mapping that fails independent observations. |
| Fibers / information loss | Identity; safe many-to-one with equal whole observation vectors; conflicting merge; empty domain for the mathematical theorem (not positive text interpretation); unused target representations irrelevant; distinct inputs with same source evidence require nonunique reading retention. |
| Joint readings / context | Two correlated pairs retained; extra Cartesian combinations rejected; deleted alternative rejected; reordered alternative set harmless if set semantics declared; changed time/source/context blocked; quotation/assertion/question distinction retained when queried. |
| Boundary / evidence | Unknown schema/law/operator/key; duplicate row/query IDs; booleans rejected as natural numbers; null/missing observation; invalid UTF-8/surrogates; line/depth/item exhaustion; native absence/malformed response fail closed; forged world-truth flag rejected. |

Do not report these cases as measured until the evaluator actually runs. Generic structural proofs and these finite authored observations have separate evidence labels.

## 5. Required checks and integration responsibilities

Formal owner after freeze: implement only the new Lean module and native executable; check under the pinned toolchain; inspect theorem axioms; no `sorry`, `admit`, custom axioms, `unsafe` proof bypass, or `native_decide` in the proof kernel.

Integration owner: add imports/Lake target and catalog, regenerate immutable proof/source evidence version, update selectors together, run `make test`, `make formal`, `make conformance`, the aligned-acquisition integration and existing catalog/routing/inference gates, plus a dedicated new native gate which must require the executable. Preserve historical files and first execution evidence. A release additionally requires `make check` and all CI checks on the final published head.

The JSON parser/native wire adapter remains an executable boundary tested by conformance; the general theorems do not claim its parser refinement is proved.
