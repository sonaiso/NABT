import Nabt
import Lean

/-!
Kernel-checked declaration and transitive-axiom audit. Each advertised theorem
must actually exist as a theorem in the compiled environment. Unknown axioms
raise a Lean error. The three allowed foundational axioms are explicit;
no project axiom and no `sorryAx` are accepted. The secondary scan also checks
all other compiled declarations in the Nabt namespace, including helpers.
-/
open Lean Elab Command

def theoremManifest : List Name := [
  ``Nabt.Law.final_dead,
  ``Nabt.Law.licensed_alive,
  ``Nabt.Law.boundedWords_exact,
  ``Nabt.Law.boundedWords_nodup,
  ``Nabt.Law.wordCount_exact,
  ``Nabt.Cell.decode_encode,
  ``Nabt.Cell.encode_decode,
  ``Nabt.Cell.encode_injective,
  ``Nabt.occurrenceNumber_injective,
  ``Nabt.occurrence_preserves_source,
  ``Nabt.occurrence_distinct_sources,
  ``Nabt.canonical_carriers_size,
  ``Nabt.canonical_carriers_nodup,
  ``Nabt.Count.acceptsAt_nil,
  ``Nabt.Count.acceptsAt_cons,
  ``Nabt.Count.prefix_length,
  ``Nabt.Count.count_eq_enumeration_length,
  ``Nabt.Count.allWords_length,
  ``Nabt.Count.enumeration_sound,
  ``Nabt.Count.allWords_complete,
  ``Nabt.Count.enumeration_complete,
  ``Nabt.Count.allWords_nodup,
  ``Nabt.Count.enumeration_nodup,
  ``Nabt.Count.unrank_rankSpec,
  ``Nabt.Count.rank_unrankSpec,
  ``Nabt.Count.rank_bounded,
  ``Nabt.Law.permutation_bound,
  ``Nabt.Law.permutation_inverse,
  ``Nabt.Law.permutation_inverse_other,
  ``Nabt.Law.permutation_mark,
  ``Nabt.Law.state_closed,
  ``Nabt.Law.step_potential,
  ``Nabt.Law.dead_absorbing,
  ``Nabt.Law.run_dead,
  ``Nabt.Law.bound_aux,
  ``Nabt.Law.suffix_fuel_bound,
  ``Nabt.Law.word_fuel_bound,
  ``Nabt.Law.incorrect_alif_rejected,
  ``Nabt.Law.matching_alif_accepted,
  ``Nabt.Law.repeated_alif_rejected,
  ``Nabt.Law.zero_weight_suffix,
  ``Nabt.Sequence.decodeAux_little,
  ``Nabt.Sequence.decode_encode,
  ``Nabt.Sequence.encode_injective,
  ``Nabt.Sequence.little_decodeAux,
  ``Nabt.Sequence.encode_decode,
  ``Nabt.Sequence.encode_surjective,
  ``Nabt.Sequence.codec_bijective,
  ``Nabt.Sequence.little_append,
  ``Nabt.Sequence.encode_append,
  ``Nabt.Sequence.encode_singleton,
  ``Nabt.Sequence.encode_push,
  ``Nabt.Sequence.kataba_number,
  ``Nabt.Sequence.kutiba_number,
  ``Nabt.Machine.run_append,
  ``Nabt.Machine.weight_append,
  ``Nabt.Machine.licensed_append,
  ``Nabt.Machine.path_compose,
  ``Nabt.Effect.then_assoc,
  ``Nabt.Effect.identity_left,
  ``Nabt.Effect.identity_right,
  ``Nabt.Machine.effect_append
]

run_cmd do
  let env ← getEnv
  let allowed : Array Name := #[``propext, ``Classical.choice, ``Quot.sound]
  let mut observed : Array Name := #[]
  for name in theoremManifest do
    match env.find? name with
    | some (.thmInfo _) => pure ()
    | _ => throwError "Manifest entry is not a compiled theorem: {name}"
    let axioms ← collectAxioms name
    for axiomName in axioms do
      unless allowed.contains axiomName do
        throwError "Unapproved axiom {axiomName} in theorem {name}"
      unless observed.contains axiomName do observed := observed.push axiomName
    logInfo m!"NABT_THEOREM {name} AXIOMS {axioms}"
  for (name, _) in env.constants.toList do
    if name.toString.startsWith "Nabt." then
      let axioms ← collectAxioms name
      for axiomName in axioms do
        unless allowed.contains axiomName do
          throwError "Unapproved axiom {axiomName} in declaration {name}"
  logInfo m!"NABT_THEOREM_COUNT {theoremManifest.length}"
  logInfo m!"NABT_OBSERVED_AXIOMS {observed}"
  logInfo "NABT_AUDIT_OK"
