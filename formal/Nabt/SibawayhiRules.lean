import Nabt.ClassicalLanguageEvidence

/-! Selected rules from the retained Kitab, lines 111–138 and 234–239.
The grammatical class is a premise, not inferred from a final vowel.
See evidence/source_semantics/passages.json for exact edition byte anchors. -/
namespace Nabt.SibawayhiRules
open ClassicalLanguageEvidence

def lawId := "nabt.sibawayhi-selected.v1"

inductive InflectedClass where
  | noun | presentVerb
  deriving DecidableEq, Repr

def coursesFor : InflectedClass → List Course
  | .noun => [.raf, .nasb, .jarr]
  | .presentVerb => [.raf, .nasb, .jazm]

/-- Preserve the ambiguity of surface marks until the regime is known. -/
def readings (kind : InflectedClass) (mark : Surface) : List Course :=
  (coursesFor kind).filter (fun c => decide (c.surface = mark))

theorem noun_has_no_jazm : Course.jazm ∉ coursesFor .noun := by decide
theorem verb_has_no_jarr : Course.jarr ∉ coursesFor .presentVerb := by decide
theorem noun_kasra_is_jarr : readings .noun .kasra = [.jarr] := by decide
theorem inflected_verb_sukun_is_jazm : readings .presentVerb .sukun = [.jazm] := by decide
theorem reading_keeps_class_and_mark (kind : InflectedClass) (mark : Surface) (c : Course) :
    c ∈ readings kind mark ↔ c ∈ coursesFor kind ∧ c.surface = mark := by
  simp [readings]

/-- Isnad requires both roles; mere token count supplies neither role. -/
structure Isnad where
  musnad : Option String
  musnadIlayh : Option String

def complete (i : Isnad) : Bool :=
  i.musnad.isSome && i.musnadIlayh.isSome

theorem incomplete_predication (subject : Option String) :
    complete ⟨none, subject⟩ = false := rfl
theorem complete_requires_both (i : Isnad) (h : complete i = true) :
    i.musnad.isSome = true ∧ i.musnadIlayh.isSome = true := by
  simpa [complete] using h

end Nabt.SibawayhiRules
