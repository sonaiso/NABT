import Nabt.ClassicalLanguageEvidence

/-! Selected rules from the retained Kitab, lines 111–138 and 234–239.
The grammatical class AND overt primary-ending regime are independent
premises, not inferred from a final vowel. Unqualified marks do not eliminate
class-appropriate cases: substitution and estimation need separate evidence.
See evidence/source_semantics/passages.json for exact edition byte anchors. -/
namespace Nabt.SibawayhiRules
open ClassicalLanguageEvidence

def lawId := "nabt.sibawayhi-selected.v2"

inductive InflectedClass where
  | noun | presentVerb
  deriving DecidableEq, Repr

inductive EndingRegime where
  | unqualified | overtPrimary
  deriving DecidableEq, Repr

def coursesFor : InflectedClass → List Course
  | .noun => [.raf, .nasb, .jarr]
  | .presentVerb => [.raf, .nasb, .jazm]

/-- Unqualified results are an overapproximation, not licensed parses. The
overtPrimary premise excludes substitute/estimated endings and deletion. -/
def readings (kind : InflectedClass) (regime : EndingRegime) (mark : Surface) : List Course :=
  match regime with
  | .unqualified => coursesFor kind
  | .overtPrimary => (coursesFor kind).filter (fun c => decide (c.surface = mark))

theorem noun_has_no_jazm : Course.jazm ∉ coursesFor .noun := by decide
theorem verb_has_no_jarr : Course.jarr ∉ coursesFor .presentVerb := by decide
theorem primary_noun_kasra_is_jarr : readings .noun .overtPrimary .kasra = [.jarr] := by decide
theorem inflected_verb_sukun_is_jazm : readings .presentVerb .overtPrimary .sukun = [.jazm] := by decide
theorem reading_keeps_class_and_mark (kind : InflectedClass) (mark : Surface) (c : Course) :
    c ∈ readings kind .overtPrimary mark ↔ c ∈ coursesFor kind ∧ c.surface = mark := by
  simp [readings]

theorem unqualified_preserves_class_cases (kind : InflectedClass) (mark : Surface) :
    readings kind .unqualified mark = coursesFor kind := rfl

theorem substitute_endings_not_discarded :
    Course.nasb ∈ readings .noun .unqualified .kasra ∧
    Course.jarr ∈ readings .noun .unqualified .fatha := by decide

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
