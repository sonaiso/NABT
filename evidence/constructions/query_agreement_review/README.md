# Restricted person queries and predicate agreement

This review preserves eleven authored cases that were frozen before the new
query implementation. The cases concern a deliberately restricted query
language: a singular source adjective in a nominal `من …؟` question may carry
an explicit person constraint, but the lexical reading of `من` remains without
an acquired gender or number. An answer needs both compatible explicit context
and an independently licensed agreement edge in the proof of the matched source
claim. This is not a general rule about the gender or number of answers to
Arabic `من` questions.

## Frozen material and baseline

`material_freeze_v1.json` pins the authored texts, teaching sources, contexts,
and expectations. Its SHA-256 is
`395f365e0773a0b2530fae9c1bba7f4e1c109b6827c1f175d592700507f287f0`.
The synthetic QAC-shaped records include a shared lemma with distinct masculine
and feminine adjective forms, two different gender readings of one surface,
missing source traits, a noun predicate with the same lemma, and context-only
personal names. No historical evaluation material was changed.

The initial `run_review.py` ran against the extracted, immutable constructions
v3 runtime. `results_v3.json` records **2/11** passing cases. The preserved
boundaries were the ambiguous adjective and the adjective with missing source
traits. All eleven questions remained deferred in that version. Every case
passed source identity, preservation of unknown INTG features, absence of
question assertions, same-source replay, and source/context withdrawal checks.
The runner checked all 74 frozen runtime files before and after execution and
verified the origins of every imported NABT module.

The baseline result SHA-256 is
`fddd38eccfd535cfce7dd7b8f85d1486dcafcb52f284390dceb22950d6891eba`.
The raw reports are retained in `results_v3.raw.jsonl.gz`, SHA-256
`7dcfbe0b85e4aa81d3e889bbf0d800bc2ad6a689a16d498b7f466422bbf9bf7f`.
This baseline predates the final adapter and runtime comparison, if later
records are added; it is not overwritten by them.

The final comparison is preserved in
`../review_fixes_v4/query_agreement_comparison.json`. Both archived runtimes ran
with the same `run_review_v4.py`; its only change from the initial adapter is
the additional approved v4 manifest pin. The repeated v3 case results and
uncompressed raw reports exactly match the initial baseline. **v4 passes all
11 cases**, including independent source/context replay and withdrawal. Its
manifest SHA-256 is
`42476d67e30e7e86506c3e878552966ce9dc784ae1e5d98bec3af50e6f0a1aa5`.
All 74 runtime files were verified before and after both executions.

## Claim-edge counterexample found during implementation review

The separate `claim_edge_supplement/` preserves one additional counterexample
observed on an uncommitted development candidate. In the authored teaching
source, `حكيمة` is an adjective and `حكيم` is a noun, with the same lemma. The
document `هندٌ حكيمةٌ أمسِ وهندٌ حكيمٌ يومَ.` and question
`من حكيمةٌ يومَ؟` initially produced a supported answer for Hind. The agreement
receipt came from the adjective predication qualified by `أمس`, while the
matched `يوم` claim used the ordinary noun predicate.

The supplement freeze SHA-256 is
`c5519dee8842f982b22a1126c8c2c2a48bdf4089c4feed94756fecac69f95298`.
It preserves exact source/context bytes, the expectation, and compressed raw
output. This is explicitly recorded as a development observation, not a pinned
release measurement. The initial live recheck after the qualifier guard is
saved separately in `observed_after_guard_live.json.gz`; it returned
`UNKNOWN`, no bindings or proofs, and valid replay. A final pinned run must
establish the release behavior independently. That final run is now preserved
at `../review_fixes_v4/query_agreement_review/claim_edge_supplement/v4.json`:
**1/1**, with both source document and inquiry licensed, the answer `UNKNOWN`,
no borrowed proof or binding, valid replay, and rejection after source
withdrawal. The earlier development observation and live recheck remain intact.

The bounded correction must prevent an agreement edge from being borrowed
from a different qualified or scoped claim in the same analysis. Rejecting a
multi-claim proof when its relevant claim-edge identity is not unique is a
conservative coverage limit; it does not establish a general graph alignment
algorithm.

## Source and measurement limits

The source audit for the scope of `من` and explicit naming is retained separately
in `../legacy_discourse_review_v2/source_context_sibawayhi.json`. In particular,
the discussion of `من` does not determine the number of its possible referents.
The typed query constraint here is a declared language boundary that is checked
at substitution time, not a lexical feature inferred from the question word.

These authored checks measure specific regressions and evidence boundaries.
They do not measure unrestricted Arabic comprehension, natural corpus recall,
or world truth. Runtime, source evidence, conditional Lean laws, Python
acquisition, and replay remain distinct authorities.
