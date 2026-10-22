import Std

/-!
# Native source-relative signed inference and proof replay

The generic licensed-rule/replay pattern is adapted from MIT-licensed
`Saleh1967/Mashru@e4c801ffe9171dadedcc3aae23051ea0953ae361:Aql/Qaida.lean`.
Copyright (c) 2026 Saleh1967. The repository MIT license is retained.

Scope: finite *ground* clauses with exact source bindings and explicit signed
atoms. The model theorem is conditional on the admitted facts and rules. These
proofs do not establish Arabic parsing, SHA-256 collision freedom, source truth,
the Python variable-grounding engine, or completeness of backward suggestions.
No other repository is imported.
-/

namespace Nabt.SemanticInference

structure Source where
  identity : String
  digest : String
  scope : String
deriving DecidableEq, Repr

structure Atom (α : Type) where
  value : α
  positive : Bool
  scope : String
deriving DecidableEq, Repr

def Atom.opposite (a : Atom α) : Atom α := {a with positive := !a.positive}

theorem opposite_involution (a : Atom α) : a.opposite.opposite = a := by
  cases a with
  | mk value positive scope => cases positive <;> rfl

theorem opposite_distinct (a : Atom α) : a.opposite ≠ a := by
  intro same
  have polarity := congrArg Atom.positive same
  cases a.positive <;> simp [Atom.opposite] at polarity

theorem scope_identity {a b : Atom α} (different : a.scope ≠ b.scope) : a ≠ b := by
  intro same
  exact different (congrArg Atom.scope same)

structure Fact (α : Type) where
  source : Source
  atom : Atom α
deriving DecidableEq, Repr

structure Rule (α : Type) where
  source : Source
  name : String
  body : List (Atom α)
  head : Atom α
deriving DecidableEq, Repr

structure Program (α : Type) where
  sources : List Source
  facts : List (Fact α)
  rules : List (Rule α)

def FactAdmitted (p : Program α) (f : Fact α) : Prop :=
  f ∈ p.facts ∧ f.source ∈ p.sources ∧ f.atom.scope = f.source.scope

def RuleAdmitted (p : Program α) (r : Rule α) : Prop :=
  r ∈ p.rules ∧ r.source ∈ p.sources ∧ r.body ≠ [] ∧
  r.head.scope = r.source.scope ∧ ∀ a ∈ r.body, a.scope = r.source.scope

instance [DecidableEq α] (p : Program α) (f : Fact α) : Decidable (FactAdmitted p f) := by
  unfold FactAdmitted
  infer_instance

instance [DecidableEq α] (p : Program α) (r : Rule α) : Decidable (RuleAdmitted p r) := by
  unfold RuleAdmitted
  infer_instance

/-- Consequence is licensed by exact admitted facts or exact admitted clauses. -/
inductive Derivable (p : Program α) : Atom α → Prop
  | fact (f : Fact α) : FactAdmitted p f → Derivable p f.atom
  | rule (r : Rule α) : RuleAdmitted p r →
      (∀ a ∈ r.body, Derivable p a) → Derivable p r.head

inductive Step (α : Type) where
  | fact (f : Fact α)
  | rule (r : Rule α)
deriving DecidableEq, Repr

def Step.source : Step α → Source
  | .fact f => f.source
  | .rule r => r.source

variable [DecidableEq α]

def applyStep (p : Program α) (known : List (Atom α)) : Step α → Option (List (Atom α))
  | .fact f => if FactAdmitted p f then some (known ++ [f.atom]) else none
  | .rule r => if RuleAdmitted p r ∧ ∀ a ∈ r.body, a ∈ known then
      some (known ++ [r.head]) else none

def replay (p : Program α) : List (Atom α) → List (Step α) → Option (List (Atom α))
  | known, [] => some known
  | known, step :: steps => match applyStep p known step with
    | none => none
    | some next => replay p next steps

theorem applyStep_sound (p : Program α) (known out : List (Atom α)) (step : Step α)
    (initial : ∀ a ∈ known, Derivable p a)
    (accepted : applyStep p known step = some out) : ∀ a ∈ out, Derivable p a := by
  cases step with
  | fact f =>
    simp only [applyStep] at accepted
    split at accepted
    · rename_i allowed
      cases accepted
      intro a member
      rcases List.mem_append.mp member with old | new
      · exact initial a old
      · simp only [List.mem_singleton] at new
        subst new
        exact Derivable.fact f allowed
    · contradiction
  | rule r =>
    simp only [applyStep] at accepted
    split at accepted
    · rename_i allowed
      cases accepted
      intro a member
      rcases List.mem_append.mp member with old | new
      · exact initial a old
      · simp only [List.mem_singleton] at new
        subst new
        exact Derivable.rule r allowed.1 (fun a ha => initial a (allowed.2 a ha))
    · contradiction

theorem replay_sound (p : Program α) :
    ∀ (steps : List (Step α)) (known out : List (Atom α)),
    (∀ a ∈ known, Derivable p a) → replay p known steps = some out →
    ∀ a ∈ out, Derivable p a := by
  intro steps
  induction steps with
  | nil =>
    intro known out initial accepted
    simp only [replay, Option.some.injEq] at accepted
    subst accepted
    exact initial
  | cons step steps ih =>
    intro known out initial accepted
    simp only [replay] at accepted
    split at accepted
    · contradiction
    · rename_i next checked
      exact ih next out (applyStep_sound p known next step initial checked) accepted

def accepts (p : Program α) (target : Atom α) (steps : List (Step α)) : Bool :=
  match replay p [] steps with
  | none => false
  | some out => decide (target ∈ out)

theorem accepts_sound (p : Program α) (target : Atom α) (steps : List (Step α))
    (accepted : accepts p target steps = true) : Derivable p target := by
  unfold accepts at accepted
  split at accepted
  · contradiction
  · rename_i out checked
    exact replay_sound p steps [] out (by simp) checked target (of_decide_eq_true accepted)

omit [DecidableEq α] in
/-- A semantic interpretation is a separate premise; replay does not create it. -/
theorem model_sound (p : Program α) (meaning : Atom α → Prop)
    (factsTrue : ∀ f, FactAdmitted p f → meaning f.atom)
    (rulesPreserve : ∀ r, RuleAdmitted p r → (∀ a ∈ r.body, meaning a) → meaning r.head)
    {a : Atom α} (derived : Derivable p a) : meaning a := by
  induction derived with
  | fact f admitted => exact factsTrue f admitted
  | rule r admitted _ inductionHypotheses => exact rulesPreserve r admitted inductionHypotheses

omit [DecidableEq α] in
theorem derivable_scope_has_source {p : Program α} {a : Atom α} (derived : Derivable p a) :
    ∃ source ∈ p.sources, a.scope = source.scope := by
  cases derived with
  | fact f admitted => exact ⟨f.source, admitted.2.1, admitted.2.2⟩
  | rule r admitted _ => exact ⟨r.source, admitted.2.1, admitted.2.2.2.1⟩

omit [DecidableEq α] in
theorem no_active_sources_no_consequence (p : Program α) (empty : p.sources = [])
    (a : Atom α) : ¬ Derivable p a := by
  intro derived
  obtain ⟨source, member, _⟩ := derivable_scope_has_source derived
  simp [empty] at member

omit [DecidableEq α] in
theorem derivable_has_fact_ancestor {p : Program α} {a : Atom α} (derived : Derivable p a) :
    ∃ f, FactAdmitted p f := by
  induction derived with
  | fact f admitted => exact ⟨f, admitted⟩
  | rule r admitted _ ih =>
    obtain ⟨premise, member⟩ := List.exists_mem_of_ne_nil r.body admitted.2.2.1
    exact ih premise member

omit [DecidableEq α] in
theorem no_facts_no_consequence (p : Program α) (empty : p.facts = [])
    (a : Atom α) : ¬ Derivable p a := by
  intro derived
  obtain ⟨f, admitted⟩ := derivable_has_fact_ancestor derived
  have member := admitted.1
  simp [empty] at member

theorem applyStep_source_active {p : Program α} {known out : List (Atom α)} {step : Step α}
    (accepted : applyStep p known step = some out) : step.source ∈ p.sources := by
  cases step with
  | fact f =>
    simp only [applyStep] at accepted
    split at accepted
    · rename_i allowed
      exact allowed.2.1
    · contradiction
  | rule r =>
    simp only [applyStep] at accepted
    split at accepted
    · rename_i allowed
      exact allowed.1.2.1
    · contradiction

theorem replay_sources_active (p : Program α) :
    ∀ (steps : List (Step α)) (known out : List (Atom α)),
    replay p known steps = some out → ∀ step ∈ steps, step.source ∈ p.sources := by
  intro steps
  induction steps with
  | nil => simp
  | cons first rest ih =>
    intro known out accepted step member
    simp only [replay] at accepted
    split at accepted
    · contradiction
    · rename_i next checked
      rcases List.mem_cons.mp member with same | tail
      · subst same
        exact applyStep_source_active checked
      · exact ih next out accepted step tail

theorem accepted_dependencies_active (p : Program α) (target : Atom α) (steps : List (Step α))
    (accepted : accepts p target steps = true) : ∀ step ∈ steps, step.source ∈ p.sources := by
  unfold accepts at accepted
  split at accepted
  · contradiction
  · rename_i out checked
    exact replay_sources_active p steps [] out checked

def withdraw (p : Program α) (source : Source) : Program α :=
  {p with sources := p.sources.filter (· != source)}

omit [DecidableEq α] in
theorem withdrawn_source_absent (p : Program α) (source : Source) :
    source ∉ (withdraw p source).sources := by
  simp [withdraw]

theorem withdrawal_rejects_stale_certificate (p : Program α) (source : Source)
    (target : Atom α) (steps : List (Step α))
    (depends : ∃ step ∈ steps, step.source = source) :
    accepts (withdraw p source) target steps = false := by
  cases result : accepts (withdraw p source) target steps with
  | false => rfl
  | true =>
    obtain ⟨step, member, same⟩ := depends
    have active := accepted_dependencies_active (withdraw p source) target steps result step member
    rw [same] at active
    exact False.elim (withdrawn_source_absent p source active)

/-- Ground rule identity includes all its content, not just a list position. -/
def Extends (old newer : Program α) : Prop :=
  (∀ s ∈ old.sources, s ∈ newer.sources) ∧
  (∀ f ∈ old.facts, f ∈ newer.facts) ∧ (∀ r ∈ old.rules, r ∈ newer.rules)

omit [DecidableEq α] in
theorem fact_admission_monotone {old newer : Program α} (grows : Extends old newer)
    {f : Fact α} (admitted : FactAdmitted old f) : FactAdmitted newer f :=
  ⟨grows.2.1 f admitted.1, grows.1 f.source admitted.2.1, admitted.2.2⟩

omit [DecidableEq α] in
theorem rule_admission_monotone {old newer : Program α} (grows : Extends old newer)
    {r : Rule α} (admitted : RuleAdmitted old r) : RuleAdmitted newer r :=
  ⟨grows.2.2 r admitted.1, grows.1 r.source admitted.2.1, admitted.2.2⟩

omit [DecidableEq α] in
theorem derivation_monotone {old newer : Program α} (grows : Extends old newer)
    {a : Atom α} (derived : Derivable old a) : Derivable newer a := by
  induction derived with
  | fact f admitted => exact Derivable.fact f (fact_admission_monotone grows admitted)
  | rule r admitted _ ih => exact Derivable.rule r (rule_admission_monotone grows admitted) ih

theorem applyStep_preserved {old newer : Program α} (grows : Extends old newer)
    (known out : List (Atom α)) (step : Step α)
    (accepted : applyStep old known step = some out) : applyStep newer known step = some out := by
  cases step with
  | fact f =>
    simp only [applyStep] at accepted ⊢
    split at accepted
    · rename_i allowed
      rw [ite_eq_left (fact_admission_monotone grows allowed)]
      exact accepted
    · contradiction
  | rule r =>
    simp only [applyStep] at accepted ⊢
    split at accepted
    · rename_i allowed
      rw [ite_eq_left ⟨rule_admission_monotone grows allowed.1, allowed.2⟩]
      exact accepted
    · contradiction

theorem replay_preserved {old newer : Program α} (grows : Extends old newer) :
    ∀ (steps : List (Step α)) (known out : List (Atom α)),
    replay old known steps = some out → replay newer known steps = some out := by
  intro steps
  induction steps with
  | nil => intro known out accepted; exact accepted
  | cons step steps ih =>
    intro known out accepted
    simp only [replay] at accepted ⊢
    split at accepted
    · contradiction
    · rename_i next checked
      rw [applyStep_preserved grows known next step checked]
      exact ih next out accepted

theorem accepted_proof_preserved {old newer : Program α} (grows : Extends old newer)
    (target : Atom α) (steps : List (Step α)) (accepted : accepts old target steps = true) :
    accepts newer target steps = true := by
  unfold accepts at accepted ⊢
  split at accepted
  · contradiction
  · rename_i out checked
    rw [replay_preserved grows steps [] out checked]
    exact accepted

omit [DecidableEq α] in
/-- No signed counterpart is manufactured in the absence of a corresponding fact or rule. -/
theorem no_rules_iff_fact (p : Program α) (empty : p.rules = []) (a : Atom α) :
    Derivable p a ↔ ∃ f, FactAdmitted p f ∧ f.atom = a := by
  constructor
  · intro derived
    cases derived with
    | fact f admitted => exact ⟨f, admitted, rfl⟩
    | rule r admitted _ =>
      have member := admitted.1
      simp [empty] at member
  · rintro ⟨f, admitted, same⟩
    rw [← same]
    exact Derivable.fact f admitted

def conflictSource : Source := ⟨"example", "declared", "example-scope"⟩
def conflictedAtom (positive : Bool) : Atom Nat := ⟨0, positive, "example-scope"⟩
def unrelatedAtom : Atom Nat := ⟨1, true, "example-scope"⟩
def conflictExample : Program Nat :=
  ⟨[conflictSource], [⟨conflictSource, conflictedAtom true⟩,
                     ⟨conflictSource, conflictedAtom false⟩], []⟩

theorem signed_conflict_does_not_explode : ¬ Derivable conflictExample unrelatedAtom := by
  rw [no_rules_iff_fact conflictExample rfl unrelatedAtom]
  simp [FactAdmitted, conflictExample, conflictedAtom, unrelatedAtom]

theorem conflict_example_has_both_signs :
    Derivable conflictExample (conflictedAtom true) ∧
    Derivable conflictExample (conflictedAtom false) := by
  constructor
  · exact Derivable.fact ⟨conflictSource, conflictedAtom true⟩
      (by simp [FactAdmitted, conflictExample, conflictSource, conflictedAtom])
  · exact Derivable.fact ⟨conflictSource, conflictedAtom false⟩
      (by simp [FactAdmitted, conflictExample, conflictSource, conflictedAtom])

/-- A second ground calculus removes blocked facts and every rule mentioning
a blocked conclusion or premise. Python computes the blocking set separately. -/
def cleanProgram (p : Program α) (blocked : Atom α → Bool) : Program α :=
  {sources := p.sources,
   facts := p.facts.filter (fun f => !blocked f.atom),
   rules := p.rules.filter (fun r => !blocked r.head && r.body.all (fun a => !blocked a))}

omit [DecidableEq α] in
theorem clean_program_subtheory (p : Program α) (blocked : Atom α → Bool) :
    Extends (cleanProgram p blocked) p := by
  refine ⟨fun _ h => h, ?_, ?_⟩
  · intro f member
    exact (List.mem_filter.mp member).1
  · intro r member
    exact (List.mem_filter.mp member).1

omit [DecidableEq α] in
theorem clean_derivation_is_signed {p : Program α} {blocked : Atom α → Bool} {a : Atom α}
    (derived : Derivable (cleanProgram p blocked) a) : Derivable p a :=
  derivation_monotone (clean_program_subtheory p blocked) derived

omit [DecidableEq α] in
theorem clean_derivation_unblocked {p : Program α} {blocked : Atom α → Bool} {a : Atom α}
    (derived : Derivable (cleanProgram p blocked) a) : blocked a = false := by
  cases derived with
  | fact f admitted =>
    have checked := (List.mem_filter.mp admitted.1).2
    simpa using checked
  | rule r admitted _ =>
    have checked := (List.mem_filter.mp admitted.1).2
    simp only [Bool.and_eq_true, Bool.not_eq_true'] at checked
    exact checked.1

omit [DecidableEq α] in
theorem clean_rule_premises_unblocked {p : Program α} {blocked : Atom α → Bool} {r : Rule α}
    (admitted : RuleAdmitted (cleanProgram p blocked) r) :
    ∀ a ∈ r.body, blocked a = false := by
  have checked := (List.mem_filter.mp admitted.1).2
  simp only [Bool.and_eq_true, List.all_eq_true, Bool.not_eq_true'] at checked
  exact checked.2

inductive Verdict where
  | supported | refuted | conflict | unknown | deferred
deriving DecidableEq, Repr

/-- Global conflict first, then the separately checked clean support. -/
def classify (positive negative cleanPositive cleanNegative : Bool) : Verdict :=
  if positive && negative then .conflict
  else if cleanPositive then .supported
  else if cleanNegative then .refuted
  else if positive || negative then .deferred
  else .unknown

theorem conflict_priority (cleanPositive cleanNegative : Bool) :
    classify true true cleanPositive cleanNegative = .conflict := rfl

theorem unknown_is_neither_support : classify false false false false = .unknown := rfl

theorem tainted_support_deferred :
    classify true false false false = .deferred ∧ classify false true false false = .deferred := by
  exact ⟨rfl, rfl⟩

theorem clean_alternative_supported : classify true false true false = .supported := rfl

theorem clean_opposite_refutes : classify false true false true = .refuted := rfl

end Nabt.SemanticInference
