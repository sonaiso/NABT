# Frozen occurrence–sense–reference holdout v1

This set was authored before the new implementation and without reading its changes or outputs. It contains 20 authored API requests, five paired invariance obligations, and six integrity obligations outside the ordinary-case denominator. The base is PR43 commit `130fa4ba13ed505039d425271a1e5fcf56058f86`. It does not reuse the 25-case benchmark or replace its denominator.

The source catalogue and loading matrix provide lexical candidates, not contextual selections. Per-sense matching/inclusion/entailment expectations mean a conditional dictionary indication if that sense applies; they never assert that a target selects the sense. Exact candidate sets are obligations within the installed catalogue, not all meanings of Arabic. Source-only root interpretations cannot create a licensed surface or headword. A complete authored component string is atomic: its proper substring is not automatically a component.

## Comparison schema

Each `cases[]` item has `id`, `input`, `expect`, `source_basis` and a scope statement. Input is exactly the public five-field API. Token indexes count outer written runs and exclude quoted contents. All non-resource inputs use budget 100000. Logical checks are independent of runtime status spelling. Any adapter must publish the mapping from returned fields/statuses to these logical obligations before comparison; it must not change labels to fit results.

`candidate_sense_ids_exact` compares unordered complete sense identifiers for source-compatible occurrence readings, retaining all same-headword alternatives. Matching/inclusion/entailment identifier lists compare unordered per-sense conditional positive indications. An unresolved sense is not a negative definition. Missing catalogue coverage is separate from no source-backed morphology; both differ from proved absence. The reference must retain its own occurrence and context identity. For the later noun cases, `selected_occurrence_reference_bound=false` always, even when the opening pronoun/demonstrative resolves. The text may mention negation or quoting without receiving a whole-sentence semantic certificate.

`linguistic_candidate_obligation` records a desired dictionary distinction whose current morphology alignment is missing. Report it as a coverage gap, even when conservative abstention is correct under the installed source contract. Do not count a safe stop as achieving that positive linguistic obligation. Resource exhaustion, invalid input, missing source, missing sense and ambiguity must be reported separately. World truth and contextual sense selection remain false on all successful reports.

Report at least (a) candidate acquisition/completeness; (b) conditional indication; (c) initial reference; (d) occurrence/reference separation; (e) safe abstention/scope/resource; (f) unmet linguistic coverage. Publish each case failure. There is no single score for Arabic completeness. An admitted failure may be resolved by a later implementation, but reference changes must get a new version and a disclosed reason independent of output.

## Freeze and independence

`freeze.json` hashes reference, sources, integrity and this protocol before implementation begins. The parent receives only counts, hash and this field schema before initial implementation freezes. Executable adapters are allowed after the implementation interface stabilizes; they must map to these fixed logical labels. Never expose case IDs, expectations, reference paths or input-specific answers to the production API. Source text/raw hashes were checked separately from authored interpretation. This is an independent agent-authored holdout, not an externally blind human judgement or proof of actual word-sense truth.
