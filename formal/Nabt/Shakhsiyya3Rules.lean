import Std

/-! Selected interpretation of the supplied third volume, paragraphs 401,
549–588 in the pinned extraction. This is that source's classification, not
an assertion of agreement between all schools of interpretation. -/
namespace Nabt.Shakhsiyya3Rules

def lawId := "nabt.shakhsiyya3-indications.v1"

inductive Indication where
  | matching | inclusion | requirement | alert | allusion | agreement | opposition
  deriving DecidableEq, Repr
inductive Layer where
  | mantuq | mafhum
  deriving DecidableEq, Repr
def Indication.layer : Indication → Layer
  | .matching | .inclusion => .mantuq
  | _ => .mafhum

theorem mantuq_exact (k : Indication) :
    k.layer = .mantuq ↔ k = .matching ∨ k = .inclusion := by
  cases k <;> simp [Indication.layer]

inductive ContrastKind where
  | attribute | condition | endpoint | number | name | innama
  deriving DecidableEq, Repr

/-- The flags are qualified premises, not inferred from a surface token.
The two inhibitors are drawn from the source's explicit exceptions. -/
def permitsContrast (k : ContrastKind) (qualified overridden usualCase : Bool) : Bool :=
  (match k with
   | .attribute | .condition | .endpoint | .number => true
   | .name | .innama => false) && qualified && !overridden && !usualCase

theorem names_do_not_license_contrast (q o u : Bool) :
    permitsContrast .name q o u = false := by simp [permitsContrast]
theorem innama_alone_does_not_license_contrast (q o u : Bool) :
    permitsContrast .innama q o u = false := by simp [permitsContrast]
theorem countertext_blocks_contrast (k : ContrastKind) (q u : Bool) :
    permitsContrast k q true u = false := by cases k <;> simp [permitsContrast]
theorem usual_case_blocks_contrast (k : ContrastKind) (q o : Bool) :
    permitsContrast k q o true = false := by cases k <;> simp [permitsContrast]

/-- A material forward implication alone does not license denying its result.
A source-specific necessary-condition bridge must be justified separately. -/
theorem forward_condition_insufficient :
    ∃ P Q : Prop, (P → Q) ∧ ¬ P ∧ Q := ⟨False, True, False.elim, id, True.intro⟩

theorem contrast_with_necessary_condition (P Q : Prop)
    (necessary : Q → P) (absent : ¬ P) : ¬ Q := fun q => absent (necessary q)

end Nabt.Shakhsiyya3Rules
