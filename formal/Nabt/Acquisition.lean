import Nabt.Transition

/-!
A proposed transition predictor factors through an explicit feature space.
Its correctness contract covers every state and symbol of the installed
machine, including states that are absent from any training sample. The
compiler retains that machine's final-state predicate. All semantic
equivalence results below require the pointwise correctness contract.

The types need not be finite for these theorems. An exhaustive check of a
particular finite instance is separate evidence for its `Faithful` premise;
these theorems do not infer that premise from samples or from a status label.
-/
namespace Nabt

structure TransitionPredictor (Q A F : Type) where
  feature : Q → A → F
  predict : F → Q × Nat

namespace TransitionPredictor
variable {Q A F : Type} (P : TransitionPredictor Q A F) (M : Machine Q A)

/-- Exact agreement with both the successor and the transition cost. -/
def Faithful : Prop :=
  ∀ q a, P.predict (P.feature q a) = (M.step q a, M.cost q a)

/-- Install the proposed transitions while retaining the installed final states. -/
def compile : Machine Q A where
  step q a := (P.predict (P.feature q a)).1
  cost q a := (P.predict (P.feature q a)).2
  final := M.final

theorem final_eq (q : Q) : (P.compile M).final q = M.final q := rfl

theorem one_step_eq (h : P.Faithful M) (q : Q) (a : A) :
    ((P.compile M).step q a, (P.compile M).cost q a) =
      (M.step q a, M.cost q a) := by
  change P.predict (P.feature q a) = _
  exact h q a

theorem step_eq (h : P.Faithful M) (q : Q) (a : A) :
    (P.compile M).step q a = M.step q a :=
  congrArg Prod.fst (P.one_step_eq M h q a)

theorem cost_eq (h : P.Faithful M) (q : Q) (a : A) :
    (P.compile M).cost q a = M.cost q a :=
  congrArg Prod.snd (P.one_step_eq M h q a)

/-- Exact successor states for arbitrary finite input lists and every start state. -/
theorem run_eq (h : P.Faithful M) (q : Q) (xs : List A) :
    (P.compile M).run q xs = M.run q xs := by
  induction xs generalizing q with
  | nil => rfl
  | cons a xs ih =>
    simp only [Machine.run, P.step_eq M h]
    exact ih (M.step q a)

/-- Exact accumulated costs, with no bound on the input-list length. -/
theorem weight_eq (h : P.Faithful M) (q : Q) (xs : List A) :
    (P.compile M).weight q xs = M.weight q xs := by
  induction xs generalizing q with
  | nil => rfl
  | cons a xs ih =>
    simp only [Machine.weight, P.cost_eq M h, P.step_eq M h, ih]

theorem acceptance_eq (h : P.Faithful M) (q : Q) (xs : List A) :
    (P.compile M).final ((P.compile M).run q xs) =
      M.final (M.run q xs) := by
  change M.final ((P.compile M).run q xs) = _
  rw [P.run_eq M h]

/-- The installed license is preserved, conditional on exact transition agreement. -/
theorem licensed_iff (h : P.Faithful M) (q : Q) (xs : List A) :
    (P.compile M).Licensed q xs ↔ M.Licensed q xs := by
  unfold Machine.Licensed
  rw [P.acceptance_eq M h]

/-- Equality of whole-list effects as functions of every possible start state. -/
theorem effect_eq (h : P.Faithful M) (xs : List A) :
    (P.compile M).effect xs = M.effect xs := by
  simp only [Machine.effect]
  congr 1
  · funext q
    exact P.run_eq M h q xs
  · funext q
    exact P.weight_eq M h q xs

/-- A feature may identify inputs only when their required outputs agree. -/
theorem target_eq_of_feature_eq (h : P.Faithful M)
    {q₁ q₂ : Q} {a₁ a₂ : A}
    (same : P.feature q₁ a₁ = P.feature q₂ a₂) :
    (M.step q₁ a₁, M.cost q₁ a₁) = (M.step q₂ a₂, M.cost q₂ a₂) := by
  calc
    (M.step q₁ a₁, M.cost q₁ a₁) = P.predict (P.feature q₁ a₁) := (h q₁ a₁).symm
    _ = P.predict (P.feature q₂ a₂) := congrArg P.predict same
    _ = (M.step q₂ a₂, M.cost q₂ a₂) := h q₂ a₂

/-- A collision with different successor/cost pairs refutes the contract. -/
theorem not_faithful_of_conflicting_collision
    {q₁ q₂ : Q} {a₁ a₂ : A}
    (same : P.feature q₁ a₁ = P.feature q₂ a₂)
    (different : (M.step q₁ a₁, M.cost q₁ a₁) ≠ (M.step q₂ a₂, M.cost q₂ a₂)) :
    ¬ P.Faithful M := by
  intro h
  exact different (P.target_eq_of_feature_eq M h same)

end TransitionPredictor

/--
Exact restoration from an encoding and its residual makes their pair
injective. This does not assert that the encoding alone is injective, or
that a restoration function exists for a particular proposed encoding.
-/
theorem encode_residue_injective {X Code Residue : Type}
    (encode : X → Code) (residue : X → Residue)
    (restore : Code → Residue → X)
    (restores : ∀ x, restore (encode x) (residue x) = x) :
    Function.Injective (fun x => (encode x, residue x)) := by
  intro x y same
  have code_eq : encode x = encode y := congrArg Prod.fst same
  have residue_eq : residue x = residue y := congrArg Prod.snd same
  calc
    x = restore (encode x) (residue x) := (restores x).symm
    _ = restore (encode y) (residue y) := by rw [code_eq, residue_eq]
    _ = y := restores y

end Nabt
