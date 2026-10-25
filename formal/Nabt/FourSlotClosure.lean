import Nabt.Law
import Nabt.Sequence

/-!
# Conditional bounded closure and a counterexample in NABT's actual law

A bound applies to effect representatives, never to original source text.
The full effect includes state transition and input-dependent weight at every
entry state. The generic theorem makes its one-step-closure premise explicit;
no claim is made that this premise holds for Arabic. In fact the current
weighted NABT law has a licensed length-five counterexample at bound four.
-/
namespace Nabt.FourSlotClosure

def lawId : String := "nabt.effect-closure.v1"

variable {Q A : Type}

def Equivalent (M : Machine Q A) (xs ys : List A) : Prop :=
  M.effect xs = M.effect ys

theorem equivalent_refl (M : Machine Q A) (xs : List A) :
    Equivalent M xs xs := rfl

theorem equivalent_symm (M : Machine Q A) {xs ys : List A}
    (h : Equivalent M xs ys) : Equivalent M ys xs := h.symm

theorem equivalent_trans (M : Machine Q A) {xs ys zs : List A}
    (h₁ : Equivalent M xs ys) (h₂ : Equivalent M ys zs) :
    Equivalent M xs zs := h₁.trans h₂

/-- Equal effects can replace each other under both left and right contexts. -/
theorem equivalent_context (M : Machine Q A) {xs ys : List A}
    (h : Equivalent M xs ys) (before after : List A) :
    Equivalent M (before ++ xs ++ after) (before ++ ys ++ after) := by
  unfold Equivalent at *
  simp only [Machine.effect_append]
  rw [h]

def HasRepresentative (M : Machine Q A) (bound : Nat) (xs : List A) : Prop :=
  ∃ ys, ys.length ≤ bound ∧ Equivalent M xs ys

/-- This is the independently required closure certificate, not a conclusion
from the number of alphabet symbols or a finite count of length-three words. -/
def OneStepClosed (M : Machine Q A) (bound : Nat) : Prop :=
  ∀ (a : A) (xs : List A), xs.length ≤ bound →
    HasRepresentative M bound (a :: xs)

/-- Structural induction: reduce the tail, prepend its generator, then apply
one-step closure to a representative that is already within the bound. -/
theorem all_lengths_of_one_step (M : Machine Q A) (bound : Nat)
    (closed : OneStepClosed M bound) (xs : List A) :
    HasRepresentative M bound xs := by
  induction xs with
  | nil => exact ⟨[], Nat.zero_le _, rfl⟩
  | cons a xs ih =>
    obtain ⟨ys, short, same⟩ := ih
    obtain ⟨zs, zshort, zsame⟩ := closed a ys short
    refine ⟨zs, zshort, ?_⟩
    have prefixed := equivalent_context M same [a] []
    have step : Equivalent M (a :: xs) (a :: ys) := by simpa using prefixed
    exact equivalent_trans M step zsame

/-- Equality of bounded closures at levels k and k+1 is sufficient. -/
theorem all_lengths_of_successor_level (M : Machine Q A) (bound : Nat)
    (stable : ∀ xs : List A, xs.length ≤ bound + 1 →
      HasRepresentative M bound xs) (xs : List A) :
    HasRepresentative M bound xs := by
  apply all_lengths_of_one_step M bound ?_ xs
  intro a ys short
  apply stable
  simp only [List.length_cons]
  omega

theorem four_slot_conditional (M : Machine Q A)
    (stable : ∀ xs : List A, xs.length ≤ 5 → HasRepresentative M 4 xs)
    (xs : List A) : HasRepresentative M 4 xs :=
  all_lengths_of_successor_level M 4 stable xs

/-- A contradiction proof refutes alleged non-representability only AFTER
one-step closure has independently been supplied. -/
theorem no_counterexample_of_one_step (M : Machine Q A) (bound : Nat)
    (closed : OneStepClosed M bound) :
    ¬ ∃ xs : List A, ¬ HasRepresentative M bound xs := by
  intro counterexample
  obtain ⟨xs, notRepresentable⟩ := counterexample
  exact notRepresentable (all_lengths_of_one_step M bound closed xs)

/-- An executable reduction needs supplied computations AND their proofs.
Existential closure alone is not presented as an implemented lookup table. -/
structure CertifiedStep (M : Machine Q A) (bound : Nat) where
  apply : A → List A → List A
  short : ∀ a xs, xs.length ≤ bound → (apply a xs).length ≤ bound
  sound : ∀ a xs, xs.length ≤ bound → Equivalent M (a :: xs) (apply a xs)

def reduce (M : Machine Q A) (bound : Nat) (step : CertifiedStep M bound) :
    List A → List A
  | [] => []
  | a :: xs => step.apply a (reduce M bound step xs)

theorem reduce_short (M : Machine Q A) (bound : Nat)
    (step : CertifiedStep M bound) (xs : List A) :
    (reduce M bound step xs).length ≤ bound := by
  induction xs with
  | nil => exact Nat.zero_le _
  | cons a xs ih => exact step.short a _ ih

theorem reduce_sound (M : Machine Q A) (bound : Nat)
    (step : CertifiedStep M bound) (xs : List A) :
    Equivalent M xs (reduce M bound step xs) := by
  induction xs with
  | nil => rfl
  | cons a xs ih =>
    have prefixed := equivalent_context M ih [a] []
    have same : Equivalent M (a :: xs) (a :: reduce M bound step xs) := by
      simpa using prefixed
    exact equivalent_trans M same (step.sound a _ (reduce_short M bound step xs))

structure SourceRecord (A : Type) where
  version : String
  sourceBytes : List UInt8
  witnesses : List Nat
  original : List A

structure ReductionRecord (A : Type) where
  source : SourceRecord A
  representative : List A

def reduceSource (M : Machine Q A) (bound : Nat) (step : CertifiedStep M bound)
    (source : SourceRecord A) : ReductionRecord A :=
  ⟨source, reduce M bound step source.original⟩

theorem source_identity_preserved (M : Machine Q A) (bound : Nat)
    (step : CertifiedStep M bound) (source : SourceRecord A) :
    (reduceSource M bound step source).source = source := rfl

theorem source_reduction_sound (M : Machine Q A) (bound : Nat)
    (step : CertifiedStep M bound) (source : SourceRecord A) :
    Equivalent M source.original (reduceSource M bound step source).representative :=
  reduce_sound M bound step source.original

/-- Merely having 116 generators allows unboundedly many effect types. -/
def countingMachine : Machine Unit (Fin 116) :=
  ⟨fun _ _ => (), fun _ _ => 1, fun _ => true⟩

theorem counting_weight (xs : List (Fin 116)) :
    countingMachine.weight () xs = xs.length := by
  induction xs with
  | nil => rfl
  | cons a xs ih =>
    change 1 + countingMachine.weight () xs = xs.length + 1
    omega

def fiveGenerators : List (Fin 116) := List.replicate 5 0

theorem alphabet_116_does_not_imply_four :
    ¬ HasRepresentative countingMachine 4 fiveGenerators := by
  rintro ⟨ys, short, same⟩
  have weights := congrArg (fun effect : Effect Unit => effect.weight ()) same
  change countingMachine.weight () fiveGenerators = countingMachine.weight () ys at weights
  rw [counting_weight, counting_weight] at weights
  simp [fiveGenerators] at weights
  omega

theorem law_cost_le_one (q : Nat) (a : Atom) : Law.cost q a ≤ 1 := by
  unfold Law.cost Law.rawCost
  split
  · omega
  · split <;> omega

theorem law_weight_le_length (mode : Bool) (q : Nat) (xs : List Atom) :
    (Law.machine mode).weight q xs ≤ xs.length := by
  induction xs generalizing q with
  | nil => simp [Machine.weight]
  | cons a xs ih =>
    have hc := law_cost_le_one q a
    have ht := ih (Law.step q a)
    simp only [Machine.weight, Law.machine, List.length_cons] at *
    omega

/-- The full effect has arbitrarily large weights; no fixed bound can preserve
all of it, independently of whether a state-only quotient happens to stabilize. -/
theorem repeated_kaf_weight (mode : Bool) (q n : Nat) :
    (Law.machine mode).weight q (List.replicate n (⟨84, by decide⟩ : Atom)) = n := by
  have cost : ∀ entry, Law.cost entry (⟨84, by decide⟩ : Atom) = 1 := by
    intro entry
    simp [Law.cost, Law.rawCost, Law.toSlge, Law.toSlgeCarrier]
  induction n generalizing q with
  | zero => rfl
  | succ n ih =>
    simp only [List.replicate_succ, Machine.weight, Law.machine]
    rw [cost]
    have tail := ih (Law.step q ⟨84, by decide⟩)
    simp only [Law.machine] at tail
    rw [tail]
    omega

theorem current_law_no_fixed_bound (mode : Bool) (bound : Nat) :
    ¬ ∀ xs : List Atom, HasRepresentative (Law.machine mode) bound xs := by
  intro all
  obtain ⟨ys, short, same⟩ := all (List.replicate (bound + 1) ⟨84, by decide⟩)
  have weights := congrArg (fun effect : Effect Nat => effect.weight 0) same
  change (Law.machine mode).weight 0 (List.replicate (bound + 1) ⟨84, by decide⟩) =
    (Law.machine mode).weight 0 ys at weights
  rw [repeated_kaf_weight] at weights
  have upper := law_weight_le_length mode 0 ys
  omega

/-- Five canonical kaf/fatha cells: a sound-shape witness, not an attested word. -/
def fiveKaf : List Atom := List.replicate 5 ⟨84, by decide⟩

/-- If n means NABT's injective sequence number, identity itself rules out
replacing a five-cell payload by any payload of length at most four. -/
theorem sequence_number_not_four_bounded (ys : List Atom) (short : ys.length ≤ 4) :
    Sequence.encode fiveKaf ≠ Sequence.encode ys := by
  intro same
  have lengths := congrArg List.length (Sequence.encode_injective same)
  simp [fiveKaf] at lengths
  omega

theorem five_kaf_weight : (Law.machine false).weight 0 fiveKaf = 5 := by decide

theorem five_kaf_licensed : (Law.machine false).Licensed 0 fiveKaf := by decide

/-- Under NABT's CURRENT full state-and-weight effect, a four-cell bound is
false even within the declared licensed sound-shape language. -/
theorem current_law_not_four_bounded :
    ¬ HasRepresentative (Law.machine false) 4 fiveKaf := by
  rintro ⟨ys, short, same⟩
  have weights := congrArg (fun effect : Effect Nat => effect.weight 0) same
  change (Law.machine false).weight 0 fiveKaf = (Law.machine false).weight 0 ys at weights
  rw [five_kaf_weight] at weights
  have upper := law_weight_le_length false 0 ys
  omega

theorem current_law_not_closed_at_four :
    ¬ OneStepClosed (Law.machine false) 4 := by
  intro closed
  exact current_law_not_four_bounded
    (all_lengths_of_one_step (Law.machine false) 4 closed fiveKaf)

end Nabt.FourSlotClosure
