import Nabt.ThinkingRules

/-! The supplied first volume paragraphs 45–46 distinguish understanding a
meaning from grounding/accepting it. This 'concept' is distinct from the
third volume's usuli 'mafhum'. No psychological or theological claim is made
an axiom. Grounding is a proposition that needs evidence, not a JSON flag. -/
namespace Nabt.Shakhsiyya1Rules
open SourceSemantics
def lawId := "nabt.shakhsiyya1-grounded-concept.v1"

structure Understanding where
  binding : Binding
  meaning : Formula

def Grounded (u : Understanding) (model : String → List String → Prop)
    (env : Nat → String) : Prop := u.meaning.meaning model env

theorem understanding_does_not_supply_grounding (binding : Binding) (env : Nat → String) :
    ¬ Grounded ⟨binding, .atom "asserted" []⟩ (fun _ _ => False) env := by
  simp [Grounded, Formula.meaning]

theorem substitution_keeps_grounding (binding : Binding) (f : Formula)
    (replacement : Nat → Term) (model : String → List String → Prop) (env : Nat → String) :
    Grounded ⟨binding, f.subst replacement⟩ model env ↔
    Grounded ⟨binding, f⟩ model (fun n => (replacement n).eval env) :=
  substitution_preserves_meaning model env replacement f

end Nabt.Shakhsiyya1Rules
