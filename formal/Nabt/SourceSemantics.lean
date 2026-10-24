import Nabt.SibawayhiRules
import Nabt.QatrRules
import Nabt.AwamilRules
import Nabt.MaqayisRules
import Nabt.VerifiedReading

/-!
Source-relative semantic contracts. These are general theorems about the
specified structures, not a proof that the free reader enumerates all Arabic
readings or interprets a classical passage correctly. In particular, a world
model is an explicit premise of `execution_in_world`, never a Boolean flag
accepted from a certificate. Exact citations prove textual occurrence only.
-/
namespace Nabt.SourceSemantics

def lawId := "nabt.source-semantics.v1"

inductive SelectedLaw where
  | sibawayhi | qatr | awamil | maqayis
  deriving DecidableEq, Repr
def SelectedLaw.work : SelectedLaw → ClassicalLanguageEvidence.Work
  | .sibawayhi => .sibawayhi | .qatr => .qatr
  | .awamil => .jurjaniAwamil | .maqayis => .maqayis
def SelectedLaw.version : SelectedLaw → String
  | .sibawayhi => SibawayhiRules.lawId | .qatr => QatrRules.lawId
  | .awamil => AwamilRules.lawId | .maqayis => MaqayisRules.lawId

/-- The edition and all source bytes remain inside Passage. This binds a
declared interpretation to a work; it does not certify the interpretation. -/
def ruleBound (inventory : List ClassicalLanguageEvidence.Source)
    (law : SelectedLaw) (p : ClassicalLanguageEvidence.Passage) : Bool :=
  ClassicalLanguageEvidence.attested inventory p && decide (p.source.work = law.work)

theorem bound_rule_keeps_work_and_passage (inventory : List ClassicalLanguageEvidence.Source)
    (law : SelectedLaw) (p : ClassicalLanguageEvidence.Passage)
    (h : ruleBound inventory law p = true) :
    ClassicalLanguageEvidence.Attested inventory p ∧ p.source.work = law.work := by
  simpa [ruleBound, ClassicalLanguageEvidence.attested] using h

theorem wrong_work_cannot_supply_rule (inventory : List ClassicalLanguageEvidence.Source)
    (law : SelectedLaw) (p : ClassicalLanguageEvidence.Passage)
    (wrong : p.source.work ≠ law.work) : ruleBound inventory law p = false := by
  simp [ruleBound, wrong]

inductive Term where
  | name (value : String)
  | variable (index : Nat)
  deriving DecidableEq, Repr

def Term.eval (env : Nat → String) : Term → String
  | .name s => s | .variable n => env n
def Term.subst (replacement : Nat → Term) : Term → Term
  | .name s => .name s | .variable n => replacement n

theorem term_substitution (env : Nat → String) (replacement : Nat → Term) (t : Term) :
    (t.subst replacement).eval env = t.eval (fun n => (replacement n).eval env) := by
  cases t <;> rfl

inductive Formula where
  | atom (concept : String) (args : List Term)
  | both (left right : Formula)
  | implies (premise conclusion : Formula)
  deriving DecidableEq, Repr

def Formula.meaning (model : String → List String → Prop) (env : Nat → String) : Formula → Prop
  | .atom c args => model c (args.map (Term.eval env))
  | .both a b => a.meaning model env ∧ b.meaning model env
  | .implies a b => a.meaning model env → b.meaning model env
def Formula.subst (replacement : Nat → Term) : Formula → Formula
  | .atom c args => .atom c (args.map (Term.subst replacement))
  | .both a b => .both (a.subst replacement) (b.subst replacement)
  | .implies a b => .implies (a.subst replacement) (b.subst replacement)

theorem substitution_preserves_meaning (model : String → List String → Prop)
    (env : Nat → String) (replacement : Nat → Term) (f : Formula) :
    (f.subst replacement).meaning model env ↔
    f.meaning model (fun n => (replacement n).eval env) := by
  induction f with
  | atom c args =>
    have eq : (args.map (Term.subst replacement)).map (Term.eval env) =
        args.map (Term.eval (fun n => (replacement n).eval env)) := by
      simp only [List.map_map]
      apply List.map_congr_left
      intro t _
      exact term_substitution env replacement t
    simp only [Formula.subst, Formula.meaning, eq]
  | both a b ha hb => simp only [Formula.subst, Formula.meaning, ha, hb]
  | implies a b ha hb => simp only [Formula.subst, Formula.meaning, ha, hb]

/-- A hygienic, binder-free definition body. It may contain variables but
cannot call itself or other definitions. Definitions do not assert instances. -/
structure ConceptDefinition where
  name : String
  body : Formula
  deriving DecidableEq, Repr
def ConceptDefinition.expand (d : ConceptDefinition) (args : Nat → Term) : Formula :=
  d.body.subst args

theorem definition_expansion (d : ConceptDefinition) (args : Nat → Term)
    (model : String → List String → Prop) (env : Nat → String) :
    (d.expand args).meaning model env ↔
    d.body.meaning model (fun n => (args n).eval env) :=
  substitution_preserves_meaning model env args d.body

theorem definition_is_not_an_instance (env : Nat → String) :
    ¬ (Formula.atom "عالم" [.variable 0]).meaning (fun _ _ => False) env := by
  simp [Formula.meaning]

/-- Entity IDs are chosen only from a closed singleton candidate set.
Unresolved rivals cannot be silently dropped by this operation. -/
def resolveReference (closed : Bool) (candidates : List String) : Option String :=
  if closed then match candidates with | [value] => some value | _ => none else none

theorem open_reference_unresolved (candidates : List String) :
    resolveReference false candidates = none := rfl
theorem reference_requires_closed_singleton (closed : Bool) (candidates : List String) (value : String)
    (h : resolveReference closed candidates = some value) :
    closed = true ∧ candidates = [value] := by
  cases closed with
  | false => simp [resolveReference] at h
  | true =>
    constructor
    · rfl
    · cases candidates with
      | nil => simp [resolveReference] at h
      | cons x xs =>
        cases xs with
        | nil => simpa [resolveReference] using h
        | cons y ys => simp [resolveReference] at h

structure Interval where
  first : Int
  last : Int
  deriving DecidableEq, Repr
def Interval.Within (small big : Interval) : Prop :=
  small.first ≤ small.last ∧ big.first ≤ small.first ∧ small.last ≤ big.last
instance (a b : Interval) : Decidable (a.Within b) := by unfold Interval.Within; infer_instance
def Interval.Holds (i : Interval) (event : Int → Prop) : Prop :=
  ∀ t, i.first ≤ t → t ≤ i.last → event t

theorem time_restriction_sound (small big : Interval) (event : Int → Prop)
    (contained : small.Within big) (holds : big.Holds event) : small.Holds event := by
  intro t lo hi
  exact holds t (Int.le_trans contained.2.1 lo) (Int.le_trans hi contained.2.2)
theorem time_cannot_be_erased :
    (Interval.mk 0 0).Holds (fun t => t = 0) ∧ ¬ (∀ t : Int, t = 0) := by
  constructor
  · intro t lo hi; exact Int.le_antisymm hi lo
  · intro h; have impossible := h 1; contradiction

/-- The full source, context and lexical model are part of a binding, not
just caller-supplied hashes. Canonical serialization belongs to the adapter. -/
structure Binding where
  source : List UInt8
  sourceId : String
  scope : String
  context : List UInt8
  lexicon : List UInt8
  deriving DecidableEq, Repr
structure Candidate (α : Type) where
  binding : Binding
  meaning : Option α
  deriving DecidableEq, Repr

/-- Consensus over the *supplied* candidate set. Enumeration completeness is
not established by this checker. None is a blocking incomplete reading. -/
def consensus [DecidableEq α] (expected : Binding) (readings : List (Candidate α)) : Option α :=
  match readings with
  | [] => none
  | first :: rest => do
    let value ← first.meaning
    if (first :: rest).all (fun c => decide (c.binding = expected ∧ c.meaning = some value))
      then some value else none

theorem consensus_all [DecidableEq α] (expected : Binding) (readings : List (Candidate α)) (value : α)
    (accepted : consensus expected readings = some value) :
    readings ≠ [] ∧ ∀ r ∈ readings, r.binding = expected ∧ r.meaning = some value := by
  cases readings with
  | nil => simp [consensus] at accepted
  | cons first rest =>
    constructor
    · simp
    · cases hm : first.meaning with
      | none => simp [consensus, hm] at accepted
      | some out =>
        simp only [consensus, hm] at accepted
        change (if (first :: rest).all (fun c => decide (c.binding = expected ∧ c.meaning = some out))
          then some out else none) = some value at accepted
        split at accepted
        · rename_i h
          have eq : out = value := Option.some.inj accepted
          subst out
          intro r mem
          exact of_decide_eq_true (List.all_eq_true.mp h r mem)
        · contradiction

theorem incomplete_reading_blocks [DecidableEq α] (expected : Binding)
    (readings : List (Candidate α)) (r : Candidate α) (member : r ∈ readings)
    (incomplete : r.meaning = none) : consensus expected readings = none := by
  cases h : consensus expected readings with
  | none => rfl
  | some value =>
    have impossible := (consensus_all expected readings value h).2 r member
    simp [incomplete] at impossible

theorem changed_binding_blocks [DecidableEq α] (expected : Binding)
    (readings : List (Candidate α)) (r : Candidate α) (member : r ∈ readings)
    (changed : r.binding ≠ expected) : consensus expected readings = none := by
  cases h : consensus expected readings with
  | none => rfl
  | some value => exact False.elim (changed ((consensus_all expected readings value h).2 r member).1)

open ClassicalLanguageEvidence in
inductive EvidenceTree where
  | leaf (passage : Passage)
  | join (left right : EvidenceTree)
  deriving DecidableEq, Repr
def EvidenceTree.leaves : EvidenceTree → List ClassicalLanguageEvidence.Passage
  | .leaf p => [p]
  | .join l r => l.leaves ++ r.leaves
def EvidenceTree.valid (inventory : List ClassicalLanguageEvidence.Source) : EvidenceTree → Bool
  | .leaf p => ClassicalLanguageEvidence.attested inventory p
  | .join l r => l.valid inventory && r.valid inventory

theorem recursive_evidence_exact (inventory : List ClassicalLanguageEvidence.Source) (tree : EvidenceTree) :
    tree.valid inventory = true ↔
    ∀ p ∈ tree.leaves, ClassicalLanguageEvidence.Attested inventory p := by
  induction tree with
  | leaf p => simp [EvidenceTree.valid, EvidenceTree.leaves, ClassicalLanguageEvidence.attested]
  | join l r hl hr =>
    simp only [EvidenceTree.valid, Bool.and_eq_true_iff, hl, hr,
      EvidenceTree.leaves, List.mem_append]
    constructor
    · rintro ⟨left, right⟩ p (mem | mem)
      · exact left p mem
      · exact right p mem
    · intro all
      exact ⟨fun p mem => all p (Or.inl mem), fun p mem => all p (Or.inr mem)⟩

theorem recursive_withdrawal_blocks (inventory : List ClassicalLanguageEvidence.Source)
    (tree : EvidenceTree) (p : ClassicalLanguageEvidence.Passage) (member : p ∈ tree.leaves)
    (withdrawn : p.source ∉ inventory) : tree.valid inventory = false := by
  cases h : tree.valid inventory with
  | false => rfl
  | true =>
    have attested := (recursive_evidence_exact inventory tree).mp h p member
    exact False.elim (withdrawn attested.1)

/-- The world bridge is conditional on independent semantic adequacy.
There is intentionally no executable flag that supplies this premise. -/
theorem execution_in_world (s : VerifiedReading.Source) (q : List UInt8)
    (c : VerifiedReading.Certificate) (e : VerifiedReading.Evidence)
    (ran : VerifiedReading.execute s q c = some e) (positive : e.positive = true)
    (world : VerifiedReading.GroundAtom → Prop)
    (adequacy : VerifiedReading.SourceMeaning s world) :
    world (c.query.lower s.scope) :=
  VerifiedReading.source_to_execution_entails s q c e ran positive world adequacy

theorem a_written_fact_needs_world_evidence (s : VerifiedReading.Source) (a : VerifiedReading.Literal) :
    ¬ VerifiedReading.TextMeaning s [.fact a] (fun _ => False) := by
  intro h
  exact h (.fact a) (by simp)

end Nabt.SourceSemantics
