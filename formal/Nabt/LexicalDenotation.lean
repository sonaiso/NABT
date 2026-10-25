import Nabt.MantuqMafhum

/-! Three indications over an explicitly interpreted, sense-specific definition.
The component inventory and mental-necessity ledger are premises, not outputs
of a stemmer. Mental association is not a fact about an outside individual.
See docs/LEXICAL_DENOTATION.md for sources and the interpretation boundary. -/
namespace Nabt.LexicalDenotation

def lawId := "nabt.lexical-denotation.v1"

structure Citation where
  work : String
  revision : String
  sourceSha256 : String
  startByte : Nat
  endByte : Nat
  quotation : String
  deriving DecidableEq, Repr

structure Sense where
  id : String
  root : String
  citation : Citation
  components : List String
  deriving DecidableEq, Repr

inductive RelationKind where
  | mental | namingReason | externalOnly
  deriving DecidableEq, Repr

structure Necessity where
  sense : Sense
  target : String
  kind : RelationKind
  citation : Citation
  deriving DecidableEq, Repr

inductive Indication where
  | matching | inclusion | entailment
  deriving DecidableEq, Repr

def Indication.label : Indication → String
  | .matching => "mutabaqa" | .inclusion => "tadammun" | .entailment => "iltizam"

def Subset (a b : List String) : Prop := ∀ x ∈ a, x ∈ b
instance (a b : List String) : Decidable (Subset a b) := by unfold Subset; infer_instance
def Whole (a b : List String) : Prop := Subset a b ∧ Subset b a
instance (a b : List String) : Decidable (Whole a b) := by unfold Whole; infer_instance
def Part (a b : List String) : Prop := Subset a b ∧ ∃ x ∈ b, x ∉ a
instance (a b : List String) : Decidable (Part a b) := by unfold Part; infer_instance

/-- Exact full Sense identity prevents a rule for one edition/sense from
silently licensing another. Only mental rules count, never naming causes. -/
def Required (rules : List Necessity) (s : Sense) (target : List String) : Prop :=
  ∃ r ∈ rules, r.sense = s ∧ r.kind = .mental ∧ target = [r.target] ∧
    r.target ∉ s.components ∧ r.citation.quotation ≠ ""
instance (rs : List Necessity) (s : Sense) (t : List String) : Decidable (Required rs s t) := by
  unfold Required; infer_instance

def Admitted (rules : List Necessity) (s : Sense) (k : Indication) (t : List String) : Prop :=
  s.citation.quotation ≠ "" ∧ s.components ≠ [] ∧ t ≠ [] ∧
    match k with
    | .matching => Whole t s.components
    | .inclusion => Part t s.components
    | .entailment => Required rules s t
instance (rs : List Necessity) (s : Sense) (k : Indication) (t : List String) :
    Decidable (Admitted rs s k t) := by
  unfold Admitted; cases k <;> infer_instance

def check (rs : List Necessity) (s : Sense) (k : Indication) (t : List String) : Bool :=
  decide (Admitted rs s k t)

theorem check_exact (rs : List Necessity) (s : Sense) (k : Indication) (t : List String) :
    check rs s k t = true ↔ Admitted rs s k t := by simp [check]

theorem empty_target_rejected (rs : List Necessity) (s : Sense) (k : Indication) :
    check rs s k [] = false := by simp [check, Admitted]

theorem missing_definition_rejected (rs : List Necessity) (s : Sense) (k : Indication)
    (t : List String) (missing : s.components = []) : check rs s k t = false := by
  simp [check, Admitted, missing]

theorem matching_inclusion_disjoint (a b : List String) : ¬ (Whole a b ∧ Part a b) := by
  rintro ⟨whole, _, x, hb, ha⟩
  exact ha (whole.2 x hb)

/-- Completeness is only relative to an explicit component inventory. -/
theorem internal_partition (a b : List String) (sub : Subset a b) : Whole a b ∨ Part a b := by
  classical
  by_cases reverse : Subset b a
  · exact Or.inl ⟨sub, reverse⟩
  · apply Or.inr
    refine ⟨sub, ?_⟩
    apply Classical.byContradiction
    intro absent
    apply reverse
    intro x member
    apply Classical.byContradiction
    intro missing
    exact absent ⟨x, member, missing⟩

theorem internal_entailment_disjoint (rs : List Necessity) (s : Sense) (t : List String) :
    ¬ (Subset t s.components ∧ Required rs s t) := by
  rintro ⟨sub, r, _, eq, _, target, outside, _⟩
  subst t
  exact outside (sub r.target (by simp))

theorem no_necessity_without_ledger (s : Sense) (t : List String) :
    check [] s .entailment t = false := by simp [check, Admitted, Required]

theorem necessity_preserves_sense (rs : List Necessity) (s : Sense) (t : List String)
    (h : check rs s .entailment t = true) :
    ∃ r ∈ rs, r.sense = s ∧ r.kind = .mental ∧ t = [r.target] ∧
      r.target ∉ s.components ∧ r.citation.quotation ≠ "" :=
  ((check_exact rs s .entailment t).mp h).2.2.2

/-- Components are conceptual predicates at a fixed interpretation/context.
For entailment, validity of the supplied mental rule is an explicit premise. -/
def Meaning (components : List String) (v : String → Prop) : Prop :=
  ∀ c ∈ components, v c
def RulesHold (rs : List Necessity) (s : Sense) (v : String → Prop) : Prop :=
  ∀ r ∈ rs, r.sense = s → r.kind = .mental → Meaning s.components v → v r.target

theorem indication_sound (rs : List Necessity) (s : Sense) (k : Indication)
    (t : List String) (v : String → Prop) (whole : Meaning s.components v)
    (rulesHold : RulesHold rs s v) (accepted : check rs s k t = true) : Meaning t v := by
  have h := ((check_exact rs s k t).mp accepted).2.2.2
  cases k with
  | matching => exact fun c hc => whole c (h.1 c hc)
  | inclusion => exact fun c hc => whole c (h.1 c hc)
  | entailment =>
    obtain ⟨r, member, eq, mental, target, _, _⟩ := h
    subst t
    intro c hc
    have same : c = r.target := by simpa using hc
    subst c
    exact rulesHold r member eq mental whole

theorem component_order_irrelevant (a b : String) : Whole [a,b] [b,a] := by
  simp [Whole, Subset, or_comm]
theorem component_duplicates_irrelevant (a : String) : Whole [a,a] [a] := by
  simp [Whole, Subset]

/-- All supplied readings survive. None stands for an unresolved interpretation.
This checker does not claim that a free reader enumerates every Arabic sense. -/
def across (rs : List Necessity) (readings : List (Option Sense))
    (k : Indication) (t : List String) : Bool :=
  !readings.isEmpty && readings.all (fun r => match r with
    | none => false | some s => check rs s k t)

theorem across_each (rs : List Necessity) (readings : List (Option Sense))
    (k : Indication) (t : List String) (accepted : across rs readings k t = true)
    (s : Sense) (member : some s ∈ readings) : check rs s k t = true := by
  have h := (Bool.and_eq_true_iff.mp accepted).2
  exact List.all_eq_true.mp h (some s) member

theorem unresolved_blocks (rs : List Necessity) (readings : List (Option Sense))
    (k : Indication) (t : List String) (unknown : none ∈ readings) :
    across rs readings k t = false := by
  apply Bool.eq_false_iff.mpr
  intro accepted
  have h := List.all_eq_true.mp (Bool.and_eq_true_iff.mp accepted).2 none unknown
  simp at h

structure Occurrence where
  source : String
  revision : String
  raw : String
  startByte : Nat
  endByte : Nat
  referent : String
  time : String
  context : String
  deriving DecidableEq, Repr

structure Reading where
  occurrence : Occurrence
  senses : List (Option Sense)
  deriving DecidableEq, Repr

def verify (rs : List Necessity) (expected supplied : Reading)
    (k : Indication) (t : List String) : Bool :=
  decide (supplied = expected) && across rs expected.senses k t

theorem verify_preserves_every_binding (rs : List Necessity) (expected supplied : Reading)
    (k : Indication) (t : List String) (h : verify rs expected supplied k t = true) :
    supplied = expected ∧ across rs expected.senses k t = true := by
  simpa [verify] using h
theorem changed_reading_rejected (rs : List Necessity) (expected supplied : Reading)
    (k : Indication) (t : List String) (changed : supplied ≠ expected) :
    verify rs expected supplied k t = false := by simp [verify, changed]

/-- Connect the component interpretation to NABT's existing formula semantics.
The context (including source/sense/referent/time) is an atom argument, so it
cannot be discarded by this bridge. -/
def componentFormula (context component : String) : SourceSemantics.Formula :=
  .atom component [.name context]

theorem formula_bridge (cs : List String) (nonempty : cs ≠ []) (context : String)
    (model : String → List String → Prop) (env : Nat → String) :
    (MantuqMafhum.conjunction (cs.map (componentFormula context))).meaning model env ↔
    Meaning cs (fun c => model c [context]) := by
  rw [MantuqMafhum.conjunction_meaning _ (by simpa using nonempty)]
  simp [Meaning, componentFormula, SourceSemantics.Formula.meaning, SourceSemantics.Term.eval]

theorem source_definition_to_formula (rs : List Necessity) (s : Sense) (k : Indication)
    (t : List String) (context : String) (model : String → List String → Prop)
    (env : Nat → String) (accepted : check rs s k t = true)
    (sourceMeaning : (MantuqMafhum.conjunction
      (s.components.map (componentFormula context))).meaning model env)
    (rulesHold : RulesHold rs s (fun c => model c [context])) :
    (MantuqMafhum.conjunction (t.map (componentFormula context))).meaning model env := by
  have conditions := (check_exact rs s k t).mp accepted
  apply (formula_bridge t conditions.2.2.1 context model env).mpr
  apply indication_sound rs s k t (fun c => model c [context])
  · exact (formula_bridge s.components conditions.2.1 context model env).mp sourceMeaning
  · exact rulesHold
  · exact accepted

theorem definition_does_not_assert_world (c context : String) (env : Nat → String) :
    ¬ (componentFormula context c).meaning (fun _ _ => False) env := by
  simp [componentFormula, SourceSemantics.Formula.meaning]

end Nabt.LexicalDenotation
