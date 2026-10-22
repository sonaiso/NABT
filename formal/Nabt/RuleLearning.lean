import Std

/-!
# Finite version-space rule learning

This is an abstract specification checked with Lean 4.34.1. A model predicts a
Boolean label for an input. An observation either supplies a known Boolean label
or explicitly leaves the label unknown. Learning filters a finite list of models.

The theorems establish the behavior of these Lean definitions. They do not prove
that a Python implementation refines this specification, that the initial list
contains the true rule, that supplied observations are authentic, or that an
Arabic interpretation or an algebraic primitive is correct. Those are explicit
external obligations. In particular, consensus is conditionally correct only
when the true model is a member of the current list.

The candidate list may contain duplicates. No equality decision procedure on
models or inputs, enumeration completeness, probability model, or oracle of
truth is assumed.
-/

namespace Nabt.RuleLearning

universe u v

variable {Model : Type u} {Input : Type v}

/-- An unknown observation records an input without asserting a false label. -/
inductive Observation (Input : Type v) where
  | known (input : Input) (label : Bool)
  | unknown (input : Input)

/-- The executable consistency test for one model and one observation. -/
def agreesWith (eval : Model → Input → Bool) (model : Model)
    (observation : Observation Input) : Bool :=
  match observation with
  | .known input label => eval model input == label
  | .unknown _ => true

/-- Whether an observation is true relative to the explicitly chosen model. -/
def Truthful (eval : Model → Input → Bool) (model : Model)
    (observation : Observation Input) : Prop :=
  match observation with
  | .known input label => eval model input = label
  | .unknown _ => True

/-- Keep exactly the hypotheses consistent with the new observation. -/
def update (eval : Model → Input → Bool) (models : List Model)
    (observation : Observation Input) : List Model :=
  models.filter (fun model => agreesWith eval model observation)

/-- Consensus is absent for an empty space or disagreement among candidates. -/
def consensus (eval : Model → Input → Bool) (models : List Model)
    (input : Input) : Option Bool :=
  match models with
  | [] => none
  | head :: tail =>
      if (head :: tail).all (fun model => eval model input == eval head input) then
        some (eval head input)
      else
        none

/-- The executable Boolean test agrees with the stated semantic condition. -/
@[simp] theorem agreesWith_true_iff (eval : Model → Input → Bool) (model : Model)
    (observation : Observation Input) :
    agreesWith eval model observation = true ↔ Truthful eval model observation := by
  cases observation <;> simp [agreesWith, Truthful]

/-- Exact surviving membership, including both directions. -/
theorem mem_update_iff (eval : Model → Input → Bool) (models : List Model)
    (observation : Observation Input) (model : Model) :
    model ∈ update eval models observation ↔
      model ∈ models ∧ Truthful eval model observation := by
  simp [update]

/-- Unknown observations leave the full list, including its order, unchanged. -/
@[simp] theorem update_unknown (eval : Model → Input → Bool) (models : List Model)
    (input : Input) :
    update eval models (.unknown input) = models := by
  simp [update, agreesWith]

/-- Updating cannot introduce a hypothesis that was not already present. -/
theorem update_subset (eval : Model → Input → Bool) (models : List Model)
    (observation : Observation Input) {model : Model}
    (member : model ∈ update eval models observation) : model ∈ models := by
  exact ((mem_update_iff eval models observation model).mp member).1

/-- Every hypothesis refuted by an observation is absent after the update. -/
theorem inconsistent_absent (eval : Model → Input → Bool) (models : List Model)
    (observation : Observation Input) (model : Model)
    (inconsistent : ¬ Truthful eval model observation) :
    model ∉ update eval models observation := by
  intro member
  exact inconsistent ((mem_update_iff eval models observation model).mp member).2

/-- A true model survives, conditional on both its prior presence and true data. -/
theorem true_model_survives (eval : Model → Input → Bool) (models : List Model)
    (observation : Observation Input) (trueModel : Model)
    (present : trueModel ∈ models) (truthful : Truthful eval trueModel observation) :
    trueModel ∈ update eval models observation := by
  exact (mem_update_iff eval models observation trueModel).mpr ⟨present, truthful⟩

/-- Removing a previously present hypothesis requires inconsistency with the data. -/
theorem removed_only_if_inconsistent (eval : Model → Input → Bool) (models : List Model)
    (observation : Observation Input) (model : Model)
    (present : model ∈ models) (removed : model ∉ update eval models observation) :
    ¬ Truthful eval model observation := by
  intro truthful
  exact removed (true_model_survives eval models observation model present truthful)

/-- An empty space cannot issue consensus, even though universal agreement is vacuous. -/
@[simp] theorem consensus_empty (eval : Model → Input → Bool) (input : Input) :
    consensus eval ([] : List Model) input = none := by
  rfl

/-- Consensus means nonempty unanimous agreement, with no hidden truth assumption. -/
theorem consensus_some_iff (eval : Model → Input → Bool) (models : List Model)
    (input : Input) (label : Bool) :
    consensus eval models input = some label ↔
      models ≠ [] ∧ ∀ model ∈ models, eval model input = label := by
  cases models with
  | nil => simp [consensus]
  | cons head tail =>
      constructor
      · intro agreed
        simp only [consensus] at agreed
        split at agreed
        next allAgree =>
          have headLabel : eval head input = label := Option.some.inj agreed
          refine ⟨by simp, ?_⟩
          intro model member
          have modelHead : eval model input = eval head input := by
            have checked := List.all_eq_true.mp allAgree model member
            simpa using checked
          exact modelHead.trans headLabel
        next disagree =>
          contradiction
      · rintro ⟨_, unanimous⟩
        have headLabel : eval head input = label := unanimous head (by simp)
        have allAgree :
            (head :: tail).all (fun model => eval model input == eval head input) = true := by
          apply List.all_eq_true.mpr
          intro model member
          have modelLabel := unanimous model member
          simp [modelLabel, headLabel]
        change (if (head :: tail).all (fun model => eval model input == eval head input)
                then some (eval head input) else none) = some label
        simp only [allAgree, ite_true]
        exact congrArg some headLabel

/-- Consensus agrees with truth only when the true model is still in the space. -/
theorem consensus_correct_of_true_member (eval : Model → Input → Bool)
    (models : List Model) (input : Input) (label : Bool) (trueModel : Model)
    (present : trueModel ∈ models)
    (agreed : consensus eval models input = some label) :
    eval trueModel input = label := by
  exact ((consensus_some_iff eval models input label).mp agreed).2 trueModel present

/-- A refuted witness in the current list gives strict finite progress. -/
theorem update_strictly_shrinks (eval : Model → Input → Bool) (models : List Model)
    (observation : Observation Input) (witness : Model)
    (present : witness ∈ models) (inconsistent : ¬ Truthful eval witness observation) :
    (update eval models observation).length < models.length := by
  apply List.length_filter_lt_length_iff_exists.mpr
  refine ⟨witness, present, ?_⟩
  intro checked
  exact inconsistent ((agreesWith_true_iff eval witness observation).mp checked)

/-- A distinguishing label keeps its agreeing witness and removes its opponent. -/
theorem distinguishing_observation_progress (eval : Model → Input → Bool)
    (models : List Model) (input : Input) (agreeing opposing : Model)
    (agreeingPresent : agreeing ∈ models) (opposingPresent : opposing ∈ models)
    (disagreement : eval opposing input ≠ eval agreeing input) :
    let observation := Observation.known input (eval agreeing input)
    agreeing ∈ update eval models observation ∧
      opposing ∉ update eval models observation ∧
      (update eval models observation).length < models.length := by
  dsimp
  have truthful : Truthful eval agreeing (.known input (eval agreeing input)) := by
    rfl
  have refuted : ¬ Truthful eval opposing (.known input (eval agreeing input)) := by
    exact disagreement
  exact ⟨true_model_survives eval models _ agreeing agreeingPresent truthful,
    inconsistent_absent eval models _ opposing refuted,
    update_strictly_shrinks eval models _ opposing opposingPresent refuted⟩

end Nabt.RuleLearning
