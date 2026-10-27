import Nabt
import Lean

/-!
Audit of four proposed logical steps, not a new Arabic grammar or a proof of
the impossibility of Arabic coverage. These small countermodels demonstrate
that the stated premises alone do not entail the proposed conclusions.
Existing NABT contracts are inspected and reused without theorem aliases.
-/
namespace CompletenessReview

/-- Two finite nonempty generator domains do not imply a surjective map. -/
theorem finite_generation_need_not_cover :
    ∃ f : Unit × Unit → Bool, ¬ (∀ w : Bool, ∃ input, f input = w) := by
  refine ⟨fun _ => false, ?_⟩
  intro covers
  obtain ⟨_, impossible⟩ := covers true
  cases impossible

def cycleClosed (a b : Bool) : Bool := (!a || b) && (!b || a)

/-- The cycle a→b→a admits both models; the edges do not choose a true seed. -/
theorem a_cycle_has_distinct_models :
    cycleClosed false false = true ∧ cycleClosed true true = true ∧
      (false, false) ≠ (true, true) := by decide

def toyMantuq (q : Fin 3) : Prop := q.val = 0
def toyMafhum (q : Fin 3) : Prop := q.val = 1

/-- Both labelled output classes can be nonempty and still omit a target. -/
theorem two_nonempty_classes_need_not_cover :
    (∃ q, toyMantuq q) ∧ (∃ q, toyMafhum q) ∧
      (∃ q, ¬ toyMantuq q ∧ ¬ toyMafhum q) := by
  exact ⟨⟨⟨0, by decide⟩, rfl⟩, ⟨⟨1, by decide⟩, rfl⟩,
    ⟨⟨2, by decide⟩, by simp [toyMantuq], by simp [toyMafhum]⟩⟩

/-- Set exclusion is not unconditionally Boolean XOR. Domain restrictions
may identify special cases; their validity needs a separate linguistic bridge. -/
theorem set_exclusion_is_not_unconditional_xor :
    ∃ inA inB : Bool, (inA && !inB) ≠ (inA != inB) := by
  exact ⟨false, true, by decide⟩

end CompletenessReview

-- Existing general contracts: no duplicate theorem wrappers are introduced.
#check Nabt.Shakhsiyya3Rules.forward_condition_insufficient
#check Nabt.Shakhsiyya3Rules.contrast_with_necessary_condition
#check Nabt.Shakhsiyya3Rules.countertext_blocks_contrast
#check Nabt.Shakhsiyya3Rules.usual_case_blocks_contrast
#check Nabt.ArabicCoverage.exact_iff_sound_and_complete
#check Nabt.ArabicCoverage.exactness_transfers_with_reference_equivalence
#check Nabt.ArabicCoverage.no_single_interpreter_of_observation_collision
#check Nabt.ArabicCoverage.unique_choice_incomplete_for_ambiguous_input
#check Nabt.LexicalGraph.completed_exact
#check Nabt.LexicalGraph.completed_model_sound
#check Nabt.LexicalGraph.completed_empty_without_seeds

open Lean Elab Command in
run_cmd do
  let names := [``CompletenessReview.finite_generation_need_not_cover,
    ``CompletenessReview.a_cycle_has_distinct_models,
    ``CompletenessReview.two_nonempty_classes_need_not_cover,
    ``CompletenessReview.set_exclusion_is_not_unconditional_xor]
  let allowed := [``propext, ``Classical.choice, ``Quot.sound]
  for name in names do
    match (← getEnv).find? name with
    | some (.thmInfo _) => pure ()
    | _ => throwError "Review claim is not a compiled theorem: {name}"
    let axioms ← collectAxioms name
    for axiomName in axioms do
      unless allowed.contains axiomName do
        throwError "Unapproved review axiom: {axiomName}"
    logInfo m!"NABT_REVIEW_THEOREM {name} AXIOMS {axioms}"
  logInfo "NABT_COMPLETENESS_REVIEW_OK"
