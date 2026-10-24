import Std

/-! A selected lexical entry: علم, retained Maqayis lines 27039–27065.
The five glosses below are a deliberately partial inventory. The author's
proposed common origin is not a claim that every token has one meaning. -/
namespace Nabt.MaqayisRules

def lawId := "nabt.maqayis-ilm-selected.v1"
inductive Sense where
  | mark | flag | mountain | lipCleft | knowledge
  deriving DecidableEq, Repr
def senses : List Sense := [.mark, .flag, .mountain, .lipCleft, .knowledge]

structure Occurrence where
  source : String
  revision : String
  offset : Nat
  spelling : String
  deriving DecidableEq, Repr

structure Selection where
  occurrence : Occurrence
  sense : Sense
  deriving DecidableEq, Repr

/-- A lexical entry proposes senses. Only an explicit occurrence-bound
context reading selects one; the correctness of that reading remains stated. -/
def resolve (target : Occurrence) (selection : Selection) : Option Sense :=
  if selection.occurrence = target then some selection.sense else none

theorem different_occurrence_rejected (target : Occurrence) (selection : Selection)
    (different : selection.occurrence ≠ target) : resolve target selection = none := by
  simp [resolve, different]
theorem resolution_preserves_occurrence (target : Occurrence) (selection : Selection) (s : Sense)
    (h : resolve target selection = some s) :
    selection.occurrence = target ∧ selection.sense = s := by
  unfold resolve at h
  split at h
  · exact ⟨by assumption, Option.some.inj h⟩
  · contradiction
theorem root_does_not_determine_sense :
    Sense.flag ∈ senses ∧ Sense.knowledge ∈ senses ∧ Sense.flag ≠ Sense.knowledge := by decide

end Nabt.MaqayisRules
