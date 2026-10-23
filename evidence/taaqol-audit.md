# Taaqol-GPT audit for the NABT foundation

**Audited revision:** `91dad107a7d56e6e05cce4ab54c3d63e5bdf5482`.

**Repository:** `https://github.com/sonaiso/Taaqol-GPT/tree/91dad107a7d56e6e05cce4ab54c3d63e5bdf5482`.

**Method:** read-only source/document inspection, dependency inspection, 35 existing test functions executed directly, and focused adversarial probes. No repository files were changed. All paths and line numbers below refer to this pinned revision.

## Decision

Adopt Taaqol's **identity, explicit operation contracts, bounded authority, visible residuals, and ambiguity-preservation discipline** as design requirements for NABT. Do not import its names, stage-completion flags, or `ProofCertificate` labels as proof that NABT already has a general Arabic analyzer or a learning system. The most useful executable material is a small, pure validation kernel plus the pattern of independently replaying a candidate at each consumption boundary.

This checkout contains **no Lean source or Lake project, no trainable model, no optimizer, and no model training pipeline**. Its declared learning loop records observations and changes metadata/ranks. Its native tokenization and corpus runner are bounded scaffolding. The repository itself makes much of this distinction: `README.md:35–46,74–81,118–137` identifies a research alpha, excludes a generic Arabic parser, and separates certificate rank from external truth.

## Guidance and dependency boundary

No applicable `AGENTS.md` exists in this checkout or its ancestors. `CLAUDE.md` provides the repository's agent guidance: pure core, no fabricated missing boundaries, named refusals, no claims about hidden model internals, and no inference from green tests to constitutional success (`CLAUDE.md:106–134,159–208`). This audit did not change its staged roadmap.

`pyproject.toml:33–40` declares no runtime dependencies and lists `jsonschema`, `pytest`, and `ruff` as development extras. **The pure kernel is standard-library based, but that claim does not cover every shipped source module:** `src/taaqqul_slot_geometry/governance/repo_org_projection.py:23` and `governance/slge_sdlc_p0_projection.py:14` import `jsonschema`. The bounded integration tools import the separate `alghanem` and `canonical116` packages; their README explicitly requires the companion checkout (`tools/bounded_integration/README.md:27–43`). NABT can adopt the principles without acquiring these dependencies.

## Reusable strengths

| Capability | Concrete implementation and limit | Suggested NABT use |
|---|---|---|
| Explicit refusal instead of silent success | `core/gamma.py:135–242` checks identity presence, trace, scope, broken slots, layer limits, hidden/blocking residuals, required slots, and rank ceiling in order. | A small total validator over well-formed NABT claims, with named refusal/defer states. |
| Authority cannot silently increase | `core/rank_lattice.py:25–39,83–109` implements an ordinal rank order; `core/transition_gate.py:420–500` consults closure and forbidden transitions before taking the minimum of evidence, identity, gate, and residual ceilings. | Preserve an explicit authority bound on each derivation. These ranks are policy levels, not probabilities or counts. |
| Verdict and audit trace stay coherent | `core/transition_gate.py:240–280` verifies that trace state, failure, consulted closure, and granted rank match the verdict. | Make a proof receipt reconstruct the decision it reports. |
| Lexical alternatives survive | `weight/lexicon_slot_geometry.py:502–555,558–644` keeps every supplied WordNet sense, binds query/source identities, marks multiple senses, retains external-authority limits, and caps candidates. | A parse forest with provenance and unresolved alternatives, rather than prematurely choosing one sense. |
| Alternatives constrain the verdict | `weight/weight_ontology_bridge_c1.py:9–13,432–447` is expressly a carrier-only surface and requires multiple admissible anchors to remain `UNDERDETERMINED` or `SUSPENDED`. | Encode ambiguity as data with consequences for admissible downstream operations. |
| Provenance does not license semantics | `x0r/canonical116_contextual_certificate.py:290–334,363–445` keeps original encoding, canonical inventory validation, morphology, syntax, and reference unresolved when their evidence is unavailable. | Separate byte/source identity, representation, segmentation, lexical identity, reference, and truth obligations. |
| Replay on every consumption boundary | `tools/bounded_integration/admission.py:16–80,100–177,180–196` snapshots candidates, binds question plus artifact plus trust environment, verifies content, preserves alternatives, and revalidates render/serialize/reload. Gamma closes only a TRACE-level review record. | Native NABT proof checker and receipt-bound readout; persisted producer status must not become authority. |

The simulation module also expresses useful preservation checks for source blockers, evidence, trace, rank, and composition (`enriched_simulation_agent/src/sim_agent/laws.py:44–155`). These are checks of provided finite transitions, not a general proof of all operations or all models.

## Reproduced limitations

### 1. Repeating one empty observation can promote a learning rank

`x0r/learning_loop.py:194–269` treats `len(evidences) >= min_evidence_count` as sufficient evidence count, then checks the already-declared contract and its ceiling. `EuclideanLearningEvidence` accepts empty `observations` and opaque source/reference strings (`x0r/transition_contract.py:507–524`). There is no distinct-source, evidence-content, or claim-support validation here.

Probe: using the existing test helper `_contract(rank=3)`, create one evidence object with `evidence_ref='same-unverified-label'`, `source='same-unverified-source'`, `observations=()`, `rank_hint=4`; pass `(e, e)` to `promote_rank_if_evidence_sufficient`.

**Observed:** `RANK_PROMOTED`, rank `4`, duplicated evidence references.

This is a concrete gap for proof-guided acquisition. Counting repeated containers is not counting independent support. `refine_contract` also only appends a note to `effective_description` and evidence labels to residual strings (`learning_loop.py:157–191`); it does not synthesize or verify a new rule.

### 2. Duplicate sources bypass the evidence carrier's single-source cap

`core/evidence_contract.py:128–134` caps a one-element source tuple at `STRONG`, but takes an uncapped join for tuples of length two or more. Duplicating the identical `EvidenceSource` with declared rank `CERTIFICATE` changes aggregate evidence rank from `STRONG` to `CERTIFICATE`.

**Observed:** `EvidenceContract((e,)).evidence_rank == STRONG`; `EvidenceContract((e,e)).evidence_rank == CERTIFICATE`.

This is an evidence aggregation weakness, **not an end-to-end certificate escape**: the generic gate caps its own rank at `STRONG` and forbids the certificate target (`core/transition_gate.py:333–354,442–453`). NABT should still deduplicate evidence identities and track dependence before any graded aggregation.

### 3. Native tokenization is whitespace splitting; routing is a small heuristic

`runtime/istidlal_engine.py:24–30` uses `text.split()`. `runtime/native_stage_registry.py:105–214` has a small exact-surface dictionary, classifies a remaining `ال` prefix as `JamidPath`, and defaults everything else to `RootStemPath`.

| Probe | Observed result |
|---|---|
| `يا` | `ParticleOperatorPath`, hard-coded confidence 0.96 |
| `يَا` | `RootStemPath`, fallback confidence 0.55 |
| `يا،` | `RootStemPath`, fallback confidence 0.55 |
| `the` or `😀` | `RootStemPath`, fallback confidence 0.55 |
| `قال: يا، محمد!` | Tokens `('قال:', 'يا،', 'محمد!')` |

These are not calibrated probabilities. The source text may be retained separately, but these token records do not establish source-byte offsets, clitic segmentation, Arabic morphology, or semantic identity. An identity-preserving NABT front end needs explicit representation and segmentation contracts; destructive normalization must not stand in for them.

### 4. The corpus runner reports stages without invoking their registered operations

`runtime/corpus_runner.py:145–185` evaluates applicability/predecessor/context flags and constructs execution records, but never calls `spec.execution_callable`. `_record_for_stage` manufactures an output ID and `EXECUTED` status when its metadata conditions pass (`:61–129`).

Probe: replace every registered callable in memory with a spy that raises if called; run the one-token corpus `('يا',)`.

**Observed:** zero registered callable invocations; `PATH_CLASSIFICATION` still reported `EXECUTED`. The runner separately calls `classify_token_paths` at line 139, so classification itself did run; the result demonstrates that the registry's callable is not the execution authority and the orchestration does not execute the registered linguistic chain. Downstream deferrals are appropriately visible. Do not treat registry coverage or stage labels as end-to-end linguistic execution coverage.

### 5. GUA proof certificates validate artifact consistency, not semantic soundness

`gua/proof.py:301–368` checks extraction/freeze hashes, trace continuity, the four-domain pilot set, matching suites/realizations, and residual safety. `SharedConstitutionalSuite.passed` checks strings and matching hashes; its legacy-core integrity witness is a constant string (`:20–22,90–114`). `gua/core/transition.py:14–28` accepts nonempty string declarations for source state, target state, evidence requirements, and rank ceiling.

Probe: construct a normal extraction and four default realizations; replace the language transition with `source_state='anything'`, `target_state='certified_external_truth'`, `required_evidence=('unchecked_assertion',)`, `rank_ceiling='CERTIFICATE'`, preserving hashes/traces.

**Observed:** baseline `PASS`; altered semantic declaration also `PASS`; a trace mismatch produces `FAIL`.

This is evidence of the certificate's limited proposition. It proves the artifact chain passes these structural checks; it does not prove the declared evidence entails the target state. The README describes this surface as scaffolding and a pilot, so a fair adoption retains that limitation explicitly.

### 6. “Model” and “safety” surfaces are bounded wrappers

`audit/model_client.py:32–45` specifies only `complete(prompt: str) -> str`. `adapters/in_memory.py:36–68` implements fixed transcript lookup and raises on unknown prompts. It is not a trained learner or generative model.

The safeguards concern typed authority, traces, residual visibility, and forbidden transitions. They are useful epistemic guardrails, but they do not establish operational sandboxing, prompt-injection resistance, general model safety, or automatic fact checking. The imported-evidence admission module explicitly places trusted Python code and configured policies inside its trust boundary (`tools/bounded_integration/admission.py:1–5`). No broader safety claim should be inherited by NABT.

## Finite checking versus generalized proof

The strongest defensible claim for these surfaces is:

> Given these supplied artifacts, declared policies, and trusted checker implementations, this particular candidate satisfies the implemented checks; its remaining alternatives and obligations are visible.

The integration reviewers recompute finite closure and bind explanations/readout, which is stronger than trusting a producer's `PASS`. However, `verify_knowledge.py:3–7,17–63` shares acquisition, question-planning, rendering, and ontology components with Alghanem, and `verify_identity.py:3–4,40–110` consumes configured regex discourse rules. The trusted grammar, source policies, rules, and renderer remain premises. Separate files do not by themselves establish independent semantic derivation.

A generalized NABT theorem would need a formal language and semantics, admissible premise/evidence rules, and a proof that **every derivation accepted by the checker preserves the stated invariant**. That can be an induction over derivation trees. Even such a theorem would prove consequences relative to its premises; correctness of lexical conventions, measurements, external identity, and source claims needs its own evidence. No such Lean theorem is present in this Taaqol revision.

For graded counting in particular, Taaqol's rank lattice is not a cardinality algebra. NABT should distinguish bytes, Unicode scalars, canonical units, graphemes, segments, lexical candidates, referents, and propositions, each with its own identity and counting equivalence. Existing contextual tests correctly refuse interpreting “116” (inventory size) as a word's unit count (`tests/test_canonical116_contextual_certificate.py:204–220`).

## Minimal transfer into NABT

1. Introduce native records for identity, operation contracts, evidence, alternatives, typed residuals, and proof receipts. Preserve byte/source identity separately from normalized or interpreted forms.
2. Have actual operations produce their result and derivation together; the checker recomputes the result and validates prerequisites. A supplied boolean such as `preserved_identity=True` is a premise, not a proof object.
3. Give counting judgments an explicit unit type, equivalence relation, scope, result, and witness. Do not infer a count or semantic rank from the size of a submitted tuple.
4. Retain every compatible interpretation until an evidence-backed rule eliminates it; record what eliminated an alternative and under which context.
5. Acquire evidence only with source binding, supported claim, independence/dependence metadata, revision/revocation policy, and proof obligations. Deduplication is necessary; merely distinct strings are insufficient.
6. Separate test evidence, finite replay certificates, formal invariant proofs, and external truth claims in APIs and user-facing language.

## Validation record

- Verified exact commit and clean working tree before and after inspection.
- The requested focused `python -m pytest` run could not start: `pytest` is not installed in either the primary or system interpreter. No full-suite result is claimed.
- Executed **35 existing zero-argument test functions directly**, without pytest fixtures or monkeypatching test assertions: learning loop (10), native registry/runner (10), WordNet bridge (2), canonical116 contextual certificates (13). All passed.
- Executed the five targeted probes above with standard-library code. Their outcomes demonstrate coverage gaps that coexist with passing current tests.
- Static import inspection found `jsonschema` as the sole non-standard-library import root under `src/` apart from the project itself; external integration tools have additional companion-package imports.

