import Nabt.Foundation

/-!
# Source-qualified, bounded cue inflection

This algebra preserves reviewed lexical stems and derives only three declared
constructions and witnessed fixed particles. Source transcription and the
linguistic reading of its metadata are explicit premises, not kernel-certified
authorship, tawatur, intention, or truth of an utterance. No caller may supply
the installed ledger through the executable adapter.

The computational renderer is proved equivalent to the role requirements;
the table checker additionally retains the installed recipe and both lexical
witness identities. Neither lemma states completeness of Arabic morphology.
-/
namespace Nabt.QualifiedCueLicensing

def lawId : String := "nabt.qualified-cue-licensing.v1"
def reviewSha256 : String := "22cf92779bb0d2f6e72bdd09743898bc708dbf4997749e9b55ed9c7620eafed6"

inductive Kind where
  | noun | adjective | particle
  deriving DecidableEq, Repr

inductive Inflection where
  | definite | construct | fixed
  deriving DecidableEq, Repr

inductive Gender where
  | masculine | feminine | unspecified
  deriving DecidableEq, Repr

inductive NextRequirement where
  | any | definiteWasl
  deriving DecidableEq, Repr

structure Lexeme where
  id : String
  normal : String
  stem : String
  kind : Kind
  inflection : Inflection
  gender : Gender
  lunar : Bool
  number : Nat
  nextRequirement : NextRequirement := .any
  deriving DecidableEq, Repr

inductive Construction where
  | fixed | baHead | adjective | idafa
  deriving DecidableEq, Repr

structure Recipe where
  construction : Construction
  leftId : String
  rightId : String
  deriving DecidableEq, Repr

structure Form where
  normal : String
  role : String
  surface : String
  lexemeIds : List String
  ruleIds : List String
  nextRequirement : NextRequirement
  deriving DecidableEq, Repr

/-- In this ledger all productive nouns are regular singulars. The type is
deliberately bounded: no dual/plural, diptote, weak-final or solar expansion. -/
def Premises : Construction → Lexeme → Lexeme → Prop
  | .fixed, left, right =>
      left = right ∧ left.kind = .particle ∧ left.inflection = .fixed
  | .baHead, left, right =>
      left = right ∧ left.kind = .noun ∧ left.inflection = .definite ∧
      left.lunar = true ∧ left.number = 1
  | .adjective, left, right =>
      left.kind = .noun ∧ right.kind = .adjective ∧
      left.inflection = .definite ∧ right.inflection = .definite ∧
      left.gender ≠ .unspecified ∧ left.gender = right.gender ∧
      left.lunar = true ∧ right.lunar = true ∧ left.number = 1 ∧ right.number = 1
  | .idafa, left, right =>
      left.kind = .noun ∧ right.kind = .noun ∧
      left.inflection = .construct ∧ right.inflection = .definite ∧
      right.lunar = true ∧ left.number = 1 ∧ right.number = 1

instance (construction : Construction) (left right : Lexeme) :
    Decidable (Premises construction left right) := by
  cases construction <;> unfold Premises <;> infer_instance

def definite (stem : String) : String := "الْ" ++ stem

/-- Stem bytes are retained; the declared role contributes only the stated
article, preposition and case ending. An idafa head gets neither ال nor tanwin. -/
def formula (construction : Construction) (left right : Lexeme) : Form :=
  match construction with
  | .fixed =>
      ⟨left.normal, "grammar", left.stem, [left.id],
        if left.nextRequirement = .definiteWasl then ["bal_connective_kasra"] else [],
        left.nextRequirement⟩
  | .baHead =>
      ⟨left.normal, "expression", "بِ" ++ definite left.stem ++ "ِ", [left.id],
        ["ba_genitive", "regular_genitive", "lunar_article"], .any⟩
  | .adjective =>
      ⟨left.normal ++ " " ++ right.normal, "sense",
        definite left.stem ++ "َ " ++ definite right.stem ++ "َ", [left.id, right.id],
        ["object_accusative", "regular_accusative", "adjective_agreement", "lunar_article"], .any⟩
  | .idafa =>
      ⟨left.normal ++ " " ++ right.normal, "sense",
        left.stem ++ "َ " ++ definite right.stem ++ "ِ", [left.id, right.id],
        ["object_accusative", "regular_accusative", "idafa_genitive",
         "construct_no_article_tanwin", "regular_genitive", "lunar_article"], .any⟩

def render (construction : Construction) (left right : Lexeme) : Option Form :=
  if Premises construction left right then some (formula construction left right) else none

theorem render_exact (construction : Construction) (left right : Lexeme) (form : Form) :
    render construction left right = some form ↔
      Premises construction left right ∧ form = formula construction left right := by
  by_cases h : Premises construction left right
  · simp [render, h, eq_comm]
  · simp [render, h]

theorem checked_adjective_agrees (left right : Lexeme) (form : Form)
    (checked : render .adjective left right = some form) :
    left.kind = .noun ∧ right.kind = .adjective ∧ left.gender = right.gender ∧
      form.surface = definite left.stem ++ "َ " ++ definite right.stem ++ "َ" := by
  obtain ⟨h, rfl⟩ := (render_exact _ _ _ _).mp checked
  exact ⟨h.1, h.2.1, h.2.2.2.2.2.1, rfl⟩

theorem wrong_gender_rejected (left right : Lexeme)
    (different : left.gender ≠ right.gender) : render .adjective left right = none := by
  simp only [render]
  split
  · rename_i h
    exact False.elim (different h.2.2.2.2.2.1)
  · rfl

theorem checked_idafa_case (left right : Lexeme) (form : Form)
    (checked : render .idafa left right = some form) :
    left.inflection = .construct ∧ right.inflection = .definite ∧
      form.surface = left.stem ++ "َ " ++ definite right.stem ++ "ِ" := by
  obtain ⟨h, rfl⟩ := (render_exact _ _ _ _).mp checked
  exact ⟨h.2.2.1, h.2.2.2.1, rfl⟩

theorem checked_ba_genitive (left right : Lexeme) (form : Form)
    (checked : render .baHead left right = some form) :
    left.kind = .noun ∧ left.inflection = .definite ∧
      form.surface = "بِ" ++ definite left.stem ++ "ِ" := by
  obtain ⟨h, rfl⟩ := (render_exact _ _ _ _).mp checked
  exact ⟨h.2.1, h.2.2.1, rfl⟩

def resolve (ledger : List Lexeme) (recipe : Recipe) : Option Form := do
  let left ← ledger.find? (fun row => row.id == recipe.leftId)
  let right ← ledger.find? (fun row => row.id == recipe.rightId)
  render recipe.construction left right

def table (ledger : List Lexeme) (recipes : List Recipe) : List Form :=
  recipes.filterMap (resolve ledger)

/-- Independent relational contract: a checked form has an installed recipe,
both exact lexical identities, role premises and the required rendering. -/
def Licensed (ledger : List Lexeme) (recipes : List Recipe) (form : Form) : Prop :=
  ∃ recipe ∈ recipes, ∃ left ∈ ledger, ∃ right ∈ ledger,
    left.id = recipe.leftId ∧ right.id = recipe.rightId ∧
    Premises recipe.construction left right ∧ form = formula recipe.construction left right

theorem table_sound (ledger : List Lexeme) (recipes : List Recipe) (form : Form)
    (member : form ∈ table ledger recipes) : Licensed ledger recipes form := by
  obtain ⟨recipe, inRecipes, resolved⟩ := List.mem_filterMap.mp member
  unfold resolve at resolved
  cases hleft : ledger.find? (fun row => row.id == recipe.leftId) with
  | none => simp [hleft] at resolved
  | some left =>
      cases hright : ledger.find? (fun row => row.id == recipe.rightId) with
      | none => simp [hleft, hright] at resolved
      | some right =>
          have rendered : render recipe.construction left right = some form := by
            simpa [hleft, hright] using resolved
          have h := (render_exact _ _ _ _).mp rendered
          refine ⟨recipe, inRecipes, left, List.mem_of_find?_eq_some hleft,
            right, List.mem_of_find?_eq_some hright, ?_, ?_, h.1, h.2⟩
          · simpa using List.find?_some hleft
          · simpa using List.find?_some hright

def check (ledger : List Lexeme) (recipes : List Recipe) (form : Form) : Bool :=
  (table ledger recipes).contains form

theorem check_sound (ledger : List Lexeme) (recipes : List Recipe) (form : Form)
    (checked : check ledger recipes form = true) : Licensed ledger recipes form := by
  apply table_sound ledger recipes form
  simpa [check] using checked

theorem empty_ledger_no_license (recipes : List Recipe) (form : Form) :
    check [] recipes form = false := by
  simp [check, table, resolve]

theorem changed_rendering_rejected (ledger : List Lexeme) (recipes : List Recipe) (form : Form)
    (changed : ∀ row ∈ table ledger recipes, row.surface ≠ form.surface) :
    check ledger recipes form = false := by
  apply Bool.eq_false_iff.mpr
  intro checked
  have member : form ∈ table ledger recipes := by simpa [check] using checked
  exact changed form member rfl

/-- Installed reviewed premises, not open certificate constructors. Source
locators, source bytes and editorial extraction steps are bound by the pinned
review hash and replayed by Python before this table can be used. -/
def installedLexemes : List Lexeme := [
  ⟨"ayn_definite", "العين", "عَيْن", .noun, .definite, .feminine, true, 1, .any⟩,
  ⟨"ayn_construct", "عين", "عَيْن", .noun, .construct, .feminine, true, 1, .any⟩,
  ⟨"maa", "الماء", "مَاء", .noun, .definite, .masculine, true, 1, .any⟩,
  ⟨"basira", "الباصرة", "بَاصِرَة", .adjective, .definite, .feminine, true, 1, .any⟩,
  ⟨"la", "لا", "لَا", .particle, .fixed, .unspecified, false, 0, .any⟩,
  ⟨"bal_sukun", "بل", "بَلْ", .particle, .fixed, .unspecified, false, 0, .any⟩,
  ⟨"bal_kasra", "بل", "بَلِ", .particle, .fixed, .unspecified, false, 0, .definiteWasl⟩]

def installedRecipes : List Recipe := [
  ⟨.baHead, "ayn_definite", "ayn_definite"⟩,
  ⟨.adjective, "ayn_definite", "basira"⟩,
  ⟨.idafa, "ayn_construct", "maa"⟩,
  ⟨.fixed, "la", "la"⟩,
  ⟨.fixed, "bal_sukun", "bal_sukun"⟩,
  ⟨.fixed, "bal_kasra", "bal_kasra"⟩]

def installedForms : List Form := table installedLexemes installedRecipes

theorem installed_forms_nonempty : installedForms ≠ [] := by decide +kernel

theorem installed_forms_sound (form : Form) (member : form ∈ installedForms) :
    Licensed installedLexemes installedRecipes form := table_sound _ _ _ member

end Nabt.QualifiedCueLicensing
