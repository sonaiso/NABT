import Nabt.LearnedModelData
import Nabt.Law
import Nabt.Acquisition

/-!
Verification of the particular learned decision DAG in `LearnedModelData`.
The finite theorem compares its actual predictions with the installed law
for all 97 states and all 116 alphabet atoms, using kernel reduction.

The total predictor below uses that DAG only for states below 97. For all
other natural-number states it explicitly falls back to the installed law.
Its final-state predicate is also inherited from that law. Consequently its
all-state and arbitrary-list equivalences do not assume that an unverified
learned rule generalizes beyond the exhaustively checked finite domain.
-/
namespace Nabt.LearnedModel

set_option maxRecDepth 100000
set_option maxHeartbeats 10000000

/-- Exhaustive kernel-checked agreement of the particular generated DAG. -/
theorem finite_correct : ∀ q : Fin 97, ∀ a : Atom,
    LearnedData.predict (q.val * 128 + a.val) =
      (Law.step q.val a, Law.cost q.val a) := by
  decide +kernel

/-- The finite learned predictor, with an explicit installed-law fallback. -/
def predictor : TransitionPredictor Nat Atom (Nat × Atom) where
  feature q a := (q, a)
  predict input :=
    if input.1 < 97 then
      LearnedData.predict (input.1 * 128 + input.2.val)
    else
      (Law.step input.1 input.2, Law.cost input.1 input.2)

theorem faithful (mode : Bool) : predictor.Faithful (Law.machine mode) := by
  intro q a
  change (if q < 97 then LearnedData.predict (q * 128 + a.val)
    else (Law.step q a, Law.cost q a)) = (Law.step q a, Law.cost q a)
  by_cases hq : q < 97
  · rw [ite_eq_left hq]
    exact finite_correct ⟨q, hq⟩ a
  · rw [ite_eq_right hq]

def machine (mode : Bool) : Machine Nat Atom :=
  predictor.compile (Law.machine mode)

theorem one_step_eq (mode : Bool) (q : Nat) (a : Atom) :
    ((machine mode).step q a, (machine mode).cost q a) =
      (Law.step q a, Law.cost q a) :=
  predictor.one_step_eq (Law.machine mode) (faithful mode) q a

theorem run_eq (mode : Bool) (q : Nat) (xs : List Atom) :
    (machine mode).run q xs = (Law.machine mode).run q xs :=
  predictor.run_eq (Law.machine mode) (faithful mode) q xs

theorem weight_eq (mode : Bool) (q : Nat) (xs : List Atom) :
    (machine mode).weight q xs = (Law.machine mode).weight q xs :=
  predictor.weight_eq (Law.machine mode) (faithful mode) q xs

theorem acceptance_eq (mode : Bool) (q : Nat) (xs : List Atom) :
    (machine mode).final ((machine mode).run q xs) =
      (Law.machine mode).final ((Law.machine mode).run q xs) :=
  predictor.acceptance_eq (Law.machine mode) (faithful mode) q xs

theorem licensed_iff (mode : Bool) (q : Nat) (xs : List Atom) :
    (machine mode).Licensed q xs ↔ (Law.machine mode).Licensed q xs :=
  predictor.licensed_iff (Law.machine mode) (faithful mode) q xs

theorem effect_eq (mode : Bool) (xs : List Atom) :
    (machine mode).effect xs = (Law.machine mode).effect xs :=
  predictor.effect_eq (Law.machine mode) (faithful mode) xs

end Nabt.LearnedModel
