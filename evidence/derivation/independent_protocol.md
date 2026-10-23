# Independent derivation evaluation protocol v1

This authored source-informed material was frozen before the independent reviewer opened any new NABT derivation implementation. It is not an untouched external corpus or an estimate of Arabic-wide accuracy. The reviewer read pinned source files, the agreed public API and the declared Unicode profiles. No new derivation runtime, generated table or implementation tests were read to choose these inputs or expected outcomes.

## Distinct tasks and denominators

1. **Generate:** supplied root and pattern are operands. Compare the exact generated Unicode surface; do not call that root discovery or attestation.
2. **Parse:** raw text alone enters the reader. Expected pattern/root pairs are required subsets, with named forbidden pairs. Preserve every additional genuine ambiguity. Never pass the fixture's expected root, pattern, class or answer into the parse API.
3. **Semantic classification:** the exact pattern reader must not activate nominal semantics, word class, role or actual case. Categories outside the installed nominal pair remain named coverage gaps; the audit records useful non-Lean suggestions separately.
4. **Observed availability:** the controlled-source paradigm reader uses only the stated per-lexeme assertions. Positive means that the source asserts one quoted nonempty form; negative requires the exact negative sentence; omitted means unknown. The finite categories jamid/partial/full are conditional 1/2/3-form model results, never evidence of universal productivity or lexical truth.
5. **Replay and provenance:** the original report verifies against the original source; a changed witness invalidates it even if its shape or model category is unchanged.

Report parser, generator, boundary, ambiguity, paradigm and replay counts separately. A blanket DEFER baseline fails all positive inclusion/generation cases. An all-accept baseline fails exclusions, profile boundaries and missing-evidence cases. Do not claim that unsupported category cases prove positive coverage for those categories.

## Declared profiles

`stem_exact_v1` consumes the entire stem exactly. The 31 Ishtiqaq stems preserve their pinned Char spelling, including standalone hamza, shadda before its vowel, no Unicode normalization and no final radical mark. The two nominal stems are the explicitly declared faail/mafool projections. The eleven sound imperfect stems are **NEW_SOUND_PROJECTION**: shadda is compressed and long alif has no sukun; these are not the raw Mudari cell sequence and do not claim an ilal proof.

`surface_v1` may separate exactly one allowed final mark into a preserved boundary. The boundary has its own bytes and is not a conclusion about syntactic case. No article, conjunction, future prefix or other clitic is stripped by this profile. Bytes/marks are not canonically reordered. The raw-cell negative cases intentionally differ from the declared written imperfect profile.

The stem profile carries no ninth-form or weak-root projection, quadriliteral, diminutive, instrument, comparative, source-wide masdar or sifa-mushabbaha implementation promise. Their absence is recorded rather than repaired by gold labels. Future sawfa is a separate contextual marker; no `future.*` weight is accepted. The source spelling may be underdetermined even when a candidate exists.

## Independent evidence discipline

The fixture is the oracle input for the evaluator only. Production code must never read it. Adapters may translate result fields after implementation becomes available, but may not change inputs, required candidates, exclusions, marks or expectations to make a run pass. Preserve the first run and its runtime identity even on failure. Any later legitimate scope or oracle correction requires a new version, a named reason and preserved old material/results.

A read case may request named candidate exclusions without claiming that no other analysis exists. Explicit `no_candidates` is used only for inputs whose declared full pattern profile cannot match. For malformed mark sequences an explicit rejection is permitted where stated. Source parsing labels are mapped to model cardinality names for comparison; mere strings in an output are not evidence of validity.

## Formal obligations outside the public reader API

The source Ishtiqaq extractor skips literal checks. The new matcher must prove/check all literals, consume the whole input and bind repeated radical occurrences consistently. Source Mudari II/V contains repeated radical cells, but the written projection represents gemination as shadda, so the public 44-pattern inventory does not expose a custom repeated-slot API. Generic repeated-slot match/mismatch cases belong in the independent Lean conformance layer, and must not be falsely counted as exercised by a public API that lacks that input. A future quadriliteral family requires a fourth independent slot; existing triliteral generation must reject rather than truncate a four-letter root.

## Freeze and measurement

The JSON and this protocol are immutable once their hashes are recorded in `independent_material_freeze_v1.json`. The metadata records pinned source hashes and the audit hashes. It binds this material, not future runtime correctness. No pass rate has been measured by writing the fixture. Optional schema assertions performed at freeze time check the authored material itself only.
