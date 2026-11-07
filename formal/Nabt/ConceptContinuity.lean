import Nabt.LexicalDenotation

/-! One definition identity, with source-bound uses and separate evidence.
The adapters reuse SourceSemantics.Formula and the installed indication law.
Changing a research/teaching view never changes the definition or proves an
instance. Equivalence of different source definitions still requires evidence. -/
namespace Nabt.ConceptContinuity
open SourceSemantics

def lawId := "nabt.concept-continuity.v1"

/-- Empty conjunction is represented by a tautology in the existing language. -/
def componentsFormula : List String → Formula
  | [] => .implies (.atom "nabt.empty-conjunction" []) (.atom "nabt.empty-conjunction" [])
  | c :: rest => .both (.atom c [.variable 0]) (componentsFormula rest)

theorem components_meaning (cs : List String) (model : String → List String → Prop)
    (env : Nat → String) :
    (componentsFormula cs).meaning model env ↔ ∀ c ∈ cs, model c [env 0] := by
  induction cs with
  | nil => simp [componentsFormula, Formula.meaning]
  | cons c cs ih => simp [componentsFormula, Formula.meaning, Term.eval, ih]

def lexicalDefinition (s : LexicalDenotation.Sense) : ConceptDefinition :=
  ⟨s.id, componentsFormula s.components⟩

def cardinalDefinition (n : Nat) : ConceptDefinition :=
  ⟨"nabt.cardinal.nonnegative-integer.v1:" ++ toString n,
    .atom "nabt.cardinal.nonnegative-integer.v1" [.name (toString n)]⟩

/-- Context is an occurrence property. The shared definition is not copied
or renamed by a RAG, school, subject, operation or neural head. -/
structure Use where
  definition : ConceptDefinition
  binding : Binding
  view : String
  domain : String
  deriving DecidableEq, Repr

def Use.understanding (u : Use) : Shakhsiyya1Rules.Understanding :=
  ⟨u.binding, u.definition.body⟩

def Use.inView (u : Use) (view domain : String) : Use := {u with view, domain}

theorem view_preserves_identity (u : Use) (view domain : String) :
    (u.inView view domain).definition = u.definition := rfl

theorem view_preserves_understanding (u : Use) (view domain : String) :
    (u.inView view domain).understanding = u.understanding := rfl

theorem view_preserves_grounding (u : Use) (view domain : String)
    (model : String → List String → Prop) (env : Nat → String) :
    Shakhsiyya1Rules.Grounded (u.inView view domain).understanding model env ↔
    Shakhsiyya1Rules.Grounded u.understanding model env := Iff.rfl

theorem lexical_definition_keeps_identity (s : LexicalDenotation.Sense) :
    (lexicalDefinition s).name = s.id := rfl

theorem lexical_definition_meaning (s : LexicalDenotation.Sense)
    (model : String → List String → Prop) (env : Nat → String) :
    (lexicalDefinition s).body.meaning model env ↔
    LexicalDenotation.Meaning s.components (fun c => model c [env 0]) :=
  components_meaning s.components model env

/-- This is the installed lexical law in the same Formula language used by
understanding and MantuqMafhum. Mental premises are not silently discharged. -/
theorem indication_in_shared_language (rs : List LexicalDenotation.Necessity)
    (s : LexicalDenotation.Sense) (k : LexicalDenotation.Indication) (target : List String)
    (model : String → List String → Prop) (env : Nat → String)
    (whole : (lexicalDefinition s).body.meaning model env)
    (rules : LexicalDenotation.RulesHold rs s (fun c => model c [env 0]))
    (accepted : LexicalDenotation.check rs s k target = true) :
    (componentsFormula target).meaning model env := by
  apply (components_meaning target model env).mpr
  exact LexicalDenotation.indication_sound rs s k target _
    ((lexical_definition_meaning s model env).mp whole) rules accepted

theorem inference_uses_same_definition (premises : List Formula) (p : MantuqMafhum.Proof)
    (u : Use) (model : String → List String → Prop) (env : Nat → String)
    (holds : MantuqMafhum.PremisesHold premises model env)
    (checked : MantuqMafhum.infer premises p = some u.definition.body) :
    Shakhsiyya1Rules.Grounded u.understanding model env :=
  MantuqMafhum.infer_sound premises p u.definition.body model env holds checked

/-- The dictionary's mental entailment does not automatically select a
particular source-specific discourse classification such as iqtida. -/
def discourseClass : LexicalDenotation.Indication → Option Shakhsiyya3Rules.Indication
  | .matching => some .matching
  | .inclusion => some .inclusion
  | .entailment => none

theorem matching_class_shared : discourseClass .matching = some .matching := rfl
theorem inclusion_class_shared : discourseClass .inclusion = some .inclusion := rfl
theorem entailment_needs_classification : discourseClass .entailment = none := rfl

theorem shared_definition_does_not_assert_instance (binding : Binding) (view domain : String)
    (env : Nat → String) :
    ¬ Shakhsiyya1Rules.Grounded
      (Use.mk (cardinalDefinition 10) binding view domain).understanding
      (fun _ _ => False) env := by
  simp [Use.understanding, cardinalDefinition, Shakhsiyya1Rules.Grounded, Formula.meaning]

end Nabt.ConceptContinuity
