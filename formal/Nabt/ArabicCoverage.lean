import Std

/-!
# What a language-completeness claim must establish

This module proves general scope, ambiguity and information-boundary results.
It does not define all Arabic, assert that a supplied reference relation is
linguistically adequate, or prove the Python readers equivalent to that relation.
In particular, an exact finite test result is not a proof outside the tested
domain. A complete interpretation may retain several licensed readings.
-/

namespace Nabt.ArabicCoverage

def lawId : String := "nabt.arabic-coverage-obligations.v1"

def SoundWithin {Input Reading : Type}
    (domain : Input → Prop) (reference recognized : Input → Reading → Prop) : Prop :=
  ∀ input, domain input → ∀ reading, recognized input reading → reference input reading

def CompleteWithin {Input Reading : Type}
    (domain : Input → Prop) (reference recognized : Input → Reading → Prop) : Prop :=
  ∀ input, domain input → ∀ reading, reference input reading → recognized input reading

def ExactWithin {Input Reading : Type}
    (domain : Input → Prop) (reference recognized : Input → Reading → Prop) : Prop :=
  ∀ input, domain input → ∀ reading, recognized input reading ↔ reference input reading

/-- Soundness and completeness concern every input and reading in the domain. -/
theorem exact_iff_sound_and_complete {Input Reading : Type}
    (domain : Input → Prop) (reference recognized : Input → Reading → Prop) :
    ExactWithin domain reference recognized ↔
      SoundWithin domain reference recognized ∧ CompleteWithin domain reference recognized := by
  constructor
  · intro exact
    exact ⟨fun input covered reading => (exact input covered reading).mp,
      fun input covered reading => (exact input covered reading).mpr⟩
  · rintro ⟨sound, complete⟩ input covered reading
    exact ⟨sound input covered reading, complete input covered reading⟩

/-- Restricting a certified domain preserves exactness; extending it needs a proof. -/
theorem exact_restricts_to_subdomain {Input Reading : Type}
    (small large : Input → Prop) (reference recognized : Input → Reading → Prop)
    (included : ∀ input, small input → large input)
    (exact : ExactWithin large reference recognized) :
    ExactWithin small reference recognized := by
  intro input covered reading
  exact exact input (included input covered) reading

/-- Formal correctness transfers to a reference only through a separate equivalence. -/
theorem exactness_transfers_with_reference_equivalence {Input Reading : Type}
    (domain : Input → Prop)
    (formalReference intendedReference recognized : Input → Reading → Prop)
    (implementation : ExactWithin domain formalReference recognized)
    (adequacy : ∀ input, domain input → ∀ reading,
      formalReference input reading ↔ intendedReference input reading) :
    ExactWithin domain intendedReference recognized := by
  intro input covered reading
  exact (implementation input covered reading).trans (adequacy input covered reading)

def AgreeOn {Input Output : Type}
    (sample : List Input) (first second : Input → Output) : Prop :=
  ∀ input, input ∈ sample → first input = second input

/-- Any untested point admits two predictors that agree on every observed point. -/
theorem sample_agreement_leaves_untested_point {Input : Type} [DecidableEq Input]
    (sample : List Input) (outside : Input) (unseen : outside ∉ sample) :
    ∃ first second : Input → Bool,
      AgreeOn sample first second ∧ first outside ≠ second outside := by
  refine ⟨fun _ => false, fun input => if input = outside then true else false, ?_, ?_⟩
  · intro input observed
    have distinct : input ≠ outside := by
      intro equal
      exact unseen (equal ▸ observed)
    simp [distinct]
  · simp

/-- No finite prefix of an open natural-number domain determines every next output. -/
theorem every_finite_prefix_has_underdetermined_extension (count : Nat) :
    ∃ first second : Nat → Bool,
      AgreeOn (List.range count) first second ∧ first count ≠ second count := by
  apply sample_agreement_leaves_untested_point
  simp

/-- Identical available evidence cannot determine two different intended outcomes. -/
theorem no_single_interpreter_of_observation_collision {World Input Reading : Type}
    (observe : World → Input) (intended : World → Reading)
    (first second : World) (sameObservation : observe first = observe second)
    (differentReadings : intended first ≠ intended second) :
    ¬ ∃ interpret : Input → Reading, ∀ world, interpret (observe world) = intended world := by
  rintro ⟨interpret, correct⟩
  apply differentReadings
  calc
    intended first = interpret (observe first) := (correct first).symm
    _ = interpret (observe second) := congrArg interpret sameObservation
    _ = intended second := correct second

/-- A complete relation includes all independently licensed alternatives. -/
theorem completeness_preserves_licensed_alternatives {Input Reading : Type}
    (domain : Input → Prop) (reference recognized : Input → Reading → Prop)
    (complete : CompleteWithin domain reference recognized)
    (input : Input) (covered : domain input) (first second : Reading)
    (firstLicensed : reference input first) (secondLicensed : reference input second) :
    recognized input first ∧ recognized input second :=
  ⟨complete input covered first firstLicensed, complete input covered second secondLicensed⟩

/-- Selecting one unique reading would lose completeness when two readings are licensed. -/
theorem unique_choice_incomplete_for_ambiguous_input {Input Reading : Type}
    (domain : Input → Prop) (reference recognized : Input → Reading → Prop)
    (complete : CompleteWithin domain reference recognized)
    (input : Input) (covered : domain input) (first second : Reading)
    (firstLicensed : reference input first) (secondLicensed : reference input second)
    (distinct : first ≠ second) :
    ¬ ∃ only : Reading, ∀ reading, recognized input reading → reading = only := by
  rintro ⟨only, unique⟩
  have firstRecognized := complete input covered first firstLicensed
  have secondRecognized := complete input covered second secondLicensed
  exact distinct ((unique first firstRecognized).trans (unique second secondRecognized).symm)

end Nabt.ArabicCoverage
