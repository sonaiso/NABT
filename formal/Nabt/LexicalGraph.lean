import Nabt.VerifiedReading
import Nabt.LexicalDenotation

/-!
Finite source-relative lexical inference reuses NABT's existing signed Horn
replay and closure calculus. A reference/opposition graph is not a proof graph.
The algorithm removes a rule after its first activation; bounded execution
therefore terminates even when the lexical reference graph contains cycles.
Truth of seed interpretations and preservation by admitted rules remain
explicit model premises. No theorem here establishes source authenticity,
Arabic lexical coverage, source-root identity, or external-world truth.
-/
namespace Nabt.LexicalGraph
open SemanticInference VerifiedReading

def lawId : String := "nabt.lexical-graph.v1"

inductive Dimension where
  | matching | inclusion | mental | definitionReference | oppositionReference
  deriving DecidableEq, Repr

def Dimension.inferential : Dimension → Bool
  | .matching | .inclusion | .mental => true
  | .definitionReference | .oppositionReference => false

theorem reference_is_not_inference (d : Dimension)
    (reference : d = .definitionReference ∨ d = .oppositionReference) :
    d.inferential = false := by rcases reference with rfl | rfl <;> rfl

structure Node where
  id : String
  senseId : String
  component : String
  scope : String
  deriving DecidableEq, Repr

def Node.atom (n : Node) : GroundAtom := ⟨(n.id, [n.senseId, n.component]), true, n.scope⟩

structure Edge where
  id : String
  source : String
  dimension : Dimension
  body : List Node
  head : Node
  deriving DecidableEq, Repr

def Edge.Admitted (activeSources : List String) (e : Edge) : Prop :=
  e.dimension.inferential = true ∧ e.source ∈ activeSources ∧ e.body ≠ [] ∧
    ∀ n ∈ e.body, n.scope = e.head.scope ∧ n.senseId = e.head.senseId

instance (activeSources : List String) (e : Edge) : Decidable (e.Admitted activeSources) := by
  unfold Edge.Admitted
  infer_instance

def Edge.sourceBinding (e : Edge) : SemanticInference.Source := ⟨e.source, lawId, e.head.scope⟩
def Edge.lower (activeSources : List String) (e : Edge) : Option (Rule (String × List String)) :=
  if e.Admitted activeSources then
    some ⟨e.sourceBinding, e.id, e.body.map Node.atom, e.head.atom⟩ else none

theorem lowered_edge_guards (activeSources : List String) (e : Edge)
    (r : Rule (String × List String)) (lowered : e.lower activeSources = some r) :
    e.Admitted activeSources ∧ r.source = e.sourceBinding ∧ r.name = e.id ∧
      r.body = e.body.map Node.atom ∧ r.head = e.head.atom := by
  unfold Edge.lower at lowered
  split at lowered
  · rename_i admitted
    cases lowered
    exact ⟨admitted, rfl, rfl, rfl, rfl⟩
  · contradiction

theorem reference_edge_not_lowered (activeSources : List String) (e : Edge)
    (reference : e.dimension = .definitionReference ∨ e.dimension = .oppositionReference) :
    e.lower activeSources = none := by
  have disabled := reference_is_not_inference e.dimension reference
  simp [Edge.lower, Edge.Admitted, disabled]

theorem node_atom_preserves_identity (a b : Node) (same : a.atom = b.atom) : a = b := by
  cases a
  cases b
  simp only [Node.atom, Atom.mk.injEq, Prod.mk.injEq, List.cons.injEq,
    and_true, true_and] at same
  simp only [Node.mk.injEq]
  exact ⟨same.1.1, same.1.2.1, same.1.2.2, same.2⟩

def ready (p : GroundProgram) (known : List GroundAtom) (r : Rule (String × List String)) : Bool :=
  decide (RuleAdmitted p r ∧ (∀ a ∈ r.body, a ∈ known) ∧ r.head ∉ known)

structure Scan where
  known : List GroundAtom
  steps : List GroundStep
  finished : Bool

/-- Each productive activation consumes one unit and removes that rule.
Zero fuel can still certify a fixed point when no rule is enabled. -/
def scan (p : GroundProgram) : Nat → List (Rule (String × List String)) →
    List GroundAtom → Scan
  | 0, pending, known =>
    match pending.find? (ready p known) with
    | none => ⟨known, [], true⟩
    | some _ => ⟨known, [], false⟩
  | n + 1, pending, known =>
    match pending.find? (ready p known) with
    | none => ⟨known, [], true⟩
    | some r =>
      let next := scan p n (pending.erase r) (known ++ [r.head])
      ⟨next.known, .rule r :: next.steps, next.finished⟩

theorem scan_activation_bound (p : GroundProgram) (fuel : Nat)
    (pending : List (Rule (String × List String))) (known : List GroundAtom) :
    (scan p fuel pending known).steps.length ≤ fuel := by
  induction fuel generalizing pending known with
  | zero => simp [scan]; split <;> simp
  | succ n ih =>
    simp only [scan]
    split
    · simp
    · rename_i r found
      simpa using Nat.succ_le_succ (ih (pending.erase r) (known ++ [r.head]))

theorem scan_preserves_known (p : GroundProgram) (fuel : Nat)
    (pending : List (Rule (String × List String))) (known : List GroundAtom) :
    ∀ a ∈ known, a ∈ (scan p fuel pending known).known := by
  induction fuel generalizing pending known with
  | zero => intro a member; simp [scan]; split <;> exact member
  | succ n ih =>
    intro a member
    simp only [scan]
    split
    · exact member
    · exact ih _ _ a (List.mem_append_left _ member)

theorem scan_replays (p : GroundProgram) (fuel : Nat)
    (pending : List (Rule (String × List String))) (known : List GroundAtom) :
    replay p known (scan p fuel pending known).steps = some (scan p fuel pending known).known := by
  induction fuel generalizing pending known with
  | zero => simp [scan]; split <;> rfl
  | succ n ih =>
    simp only [scan]
    split
    · rfl
    · rename_i r found
      have enabled : ready p known r = true := List.find?_some found
      have h : RuleAdmitted p r ∧ (∀ a ∈ r.body, a ∈ known) ∧ r.head ∉ known := of_decide_eq_true enabled
      have admitted : RuleAdmitted p r ∧ (∀ a ∈ r.body, a ∈ known) := ⟨h.1, h.2.1⟩
      simp only [replay, applyStep, ite_eq_left admitted]
      exact ih _ _

/-- A rule can fire at most once, hence its count is a sufficient fuel bound.
This bounds admitted execution, not the number of Arabic roots. -/
theorem scan_finishes_by_rule_count (p : GroundProgram) (fuel : Nat)
    (pending : List (Rule (String × List String))) (known : List GroundAtom)
    (enough : pending.length ≤ fuel) : (scan p fuel pending known).finished = true := by
  induction fuel generalizing pending known with
  | zero =>
    have empty : pending = [] := List.length_eq_zero_iff.mp (Nat.eq_zero_of_le_zero enough)
    simp [scan, empty]
  | succ n ih =>
    simp only [scan]
    split
    · rfl
    · rename_i r found
      have member := List.mem_of_find?_eq_some found
      have erased := List.length_erase_of_mem member
      apply ih
      omega

/-- Already removed rules have their heads in the accumulated evidence. -/
def Covered (p : GroundProgram) (pending : List (Rule (String × List String)))
    (known : List GroundAtom) : Prop :=
  ∀ r ∈ p.rules, r ∈ pending ∨ r.head ∈ known

theorem covered_after_activation (p : GroundProgram)
    (pending : List (Rule (String × List String))) (known : List GroundAtom)
    (r : Rule (String × List String)) (covered : Covered p pending known) :
    Covered p (pending.erase r) (known ++ [r.head]) := by
  intro s member
  rcases covered s member with waiting | present
  · by_cases same : s = r
    · subst s; exact Or.inr (by simp)
    · exact Or.inl ((List.mem_erase_of_ne same).mpr waiting)
  · exact Or.inr (List.mem_append_left _ present)

theorem no_enabled_closed (p : GroundProgram)
    (pending : List (Rule (String × List String))) (known : List GroundAtom)
    (covered : Covered p pending known)
    (facts : ∀ f, FactAdmitted p f → f.atom ∈ known)
    (none : pending.find? (ready p known) = none) : Closed p known := by
  constructor
  · apply List.all_eq_true.mpr
    intro f _
    exact decide_eq_true (facts f)
  · apply List.all_eq_true.mpr
    intro r member
    apply decide_eq_true
    intro admitted body
    rcases covered r member with waiting | present
    · have disabled := List.find?_eq_none.mp none r waiting
      apply Classical.byContradiction
      intro absent
      exact disabled (decide_eq_true ⟨admitted, body, absent⟩)
    · exact present

theorem finished_scan_closed (p : GroundProgram) (fuel : Nat)
    (pending : List (Rule (String × List String))) (known : List GroundAtom)
    (covered : Covered p pending known)
    (facts : ∀ f, FactAdmitted p f → f.atom ∈ known)
    (finished : (scan p fuel pending known).finished = true) :
    Closed p (scan p fuel pending known).known := by
  induction fuel generalizing pending known with
  | zero =>
    cases found : pending.find? (ready p known) with
    | none => simpa only [scan, found] using no_enabled_closed p pending known covered facts found
    | some r => simp only [scan, found] at finished; contradiction
  | succ n ih =>
    cases found : pending.find? (ready p known) with
    | none => simpa only [scan, found] using no_enabled_closed p pending known covered facts found
    | some r =>
      simp only [scan, found] at finished ⊢
      exact ih _ _ (covered_after_activation p pending known r covered)
        (fun f admitted => List.mem_append_left _ (facts f admitted)) finished

def initialFacts (p : GroundProgram) : List (Fact (String × List String)) :=
  p.facts.filter (fun f => decide (FactAdmitted p f))

def initialKnown (p : GroundProgram) : List GroundAtom := (initialFacts p).map Fact.atom
def initialSteps (p : GroundProgram) : List GroundStep := (initialFacts p).map Step.fact

theorem admitted_initial_present (p : GroundProgram) (f : Fact (String × List String))
    (admitted : FactAdmitted p f) : f.atom ∈ initialKnown p := by
  apply List.mem_map.mpr
  exact ⟨f, List.mem_filter.mpr ⟨admitted.1, decide_eq_true admitted⟩, rfl⟩

theorem facts_replay (p : GroundProgram) (facts : List (Fact (String × List String)))
    (known : List GroundAtom) (admitted : ∀ f ∈ facts, FactAdmitted p f) :
    replay p known (facts.map Step.fact) = some (known ++ facts.map Fact.atom) := by
  induction facts generalizing known with
  | nil => simp [replay]
  | cons f fs ih =>
    have first := admitted f (by simp)
    simp only [List.map_cons, replay, applyStep, ite_eq_left first]
    simpa [List.append_assoc] using ih (known ++ [f.atom]) (fun f member => admitted f (by simp [member]))

theorem initial_replays (p : GroundProgram) :
    replay p [] (initialSteps p) = some (initialKnown p) := by
  simpa [initialSteps, initialKnown] using facts_replay p (initialFacts p) []
    (fun f member => of_decide_eq_true (List.mem_filter.mp member).2)

theorem replay_append (p : GroundProgram) (known middle final : List GroundAtom)
    (left right : List GroundStep)
    (first : replay p known left = some middle)
    (second : replay p middle right = some final) :
    replay p known (left ++ right) = some final := by
  induction left generalizing known with
  | nil => simp only [replay, Option.some.injEq] at first; subst middle; exact second
  | cons step rest ih =>
    cases applied : applyStep p known step with
    | none => simp only [replay, applied] at first; contradiction
    | some next =>
      simp only [List.cons_append, replay, applied] at first ⊢
      exact ih _ first

def result (p : GroundProgram) (budget : Nat) : Scan := scan p budget p.rules (initialKnown p)
def trace (p : GroundProgram) (budget : Nat) : List GroundStep :=
  initialSteps p ++ (result p budget).steps

theorem completed_certificate (p : GroundProgram) (budget : Nat)
    (finished : (result p budget).finished = true) :
    checkClosure p (trace p budget) (result p budget).known = true := by
  apply decide_eq_true
  constructor
  · exact replay_append p [] (initialKnown p) _ _ _ (initial_replays p)
      (scan_replays p budget p.rules (initialKnown p))
  · exact finished_scan_closed p budget p.rules (initialKnown p)
      (fun _ member => Or.inl member) (admitted_initial_present p) finished

/-- Soundness and least-fixed-point completeness inherit the existing checked
closure theorem; no separate notion of semantic consequence is introduced. -/
theorem completed_exact (p : GroundProgram) (budget : Nat)
    (finished : (result p budget).finished = true) (a : GroundAtom) :
    a ∈ (result p budget).known ↔ Derivable p a :=
  checked_closure_exact p (trace p budget) (result p budget).known
    (completed_certificate p budget finished) a

theorem completed_empty_without_seeds (p : GroundProgram) (budget : Nat)
    (finished : (result p budget).finished = true) (empty : p.facts = []) :
    (result p budget).known = [] := by
  apply List.eq_nil_iff_forall_not_mem.mpr
  intro a member
  exact no_facts_no_consequence p empty a ((completed_exact p budget finished a).mp member)

theorem completed_model_sound (p : GroundProgram) (budget : Nat)
    (finished : (result p budget).finished = true) (meaning : GroundAtom → Prop)
    (factsTrue : ∀ f, FactAdmitted p f → meaning f.atom)
    (rulesPreserve : ∀ r, RuleAdmitted p r → (∀ a ∈ r.body, meaning a) → meaning r.head)
    (a : GroundAtom) (member : a ∈ (result p budget).known) : meaning a :=
  model_sound p meaning factsTrue rulesPreserve ((completed_exact p budget finished a).mp member)

end Nabt.LexicalGraph
