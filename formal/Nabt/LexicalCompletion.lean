import Nabt.LexicalDenotation
import Nabt.ReadingEnumeration
import Nabt.ArabicCoverage

/-! Composition and catalogue-relative completeness. These proofs do not
establish a complete Arabic lexicon, an Arabic sentence grammar, authenticity
of a quotation, or truth of a physical event. Inputs are ordered dictionary
indices with target components. Existing indication and enumeration laws are
reused; no new meaning is inferred by decomposing a gloss into words. -/
namespace Nabt.LexicalCompletion
open LexicalDenotation SourceSemantics

def lawId : String := "nabt.lexical-completion.v1"
def kinds : List Indication := [.matching, .inclusion, .entailment]

structure Slot where
  entry : String
  target : List String
  deriving DecidableEq, Repr

def selected (catalogue : List Sense) (entry : String) : List Sense :=
  catalogue.filter (fun s => s.root == entry)

theorem selected_exact (catalogue : List Sense) (entry : String) (s : Sense) :
    s ∈ selected catalogue entry ↔ s ∈ catalogue ∧ s.root = entry := by
  simp [selected]

def accepts (rules : List Necessity) (s : Sense) (target : List String) : Bool :=
  kinds.any (fun k => check rules s k target)

theorem accepts_exact (rules : List Necessity) (s : Sense) (target : List String) :
    accepts rules s target = true ↔ ∃ k ∈ kinds, Admitted rules s k target := by
  simp [accepts, List.any_eq_true, check_exact]

theorem accepted_indication_sound (rules : List Necessity) (s : Sense)
    (target : List String) (v : String → Prop)
    (whole : Meaning s.components v) (ruleTruth : RulesHold rules s v)
    (accepted : accepts rules s target = true) : Meaning target v := by
  obtain ⟨k, _, h⟩ := (accepts_exact rules s target).mp accepted
  exact indication_sound rules s k target v whole ruleTruth ((check_exact rules s k target).mpr h)

def answers (catalogue : List Sense) (rules : List Necessity) (slot : Slot) : List Sense :=
  (selected catalogue slot.entry).filter (fun s => accepts rules s slot.target)

def Reference (catalogue : List Sense) (rules : List Necessity) (slot : Slot) (s : Sense) : Prop :=
  s ∈ catalogue ∧ s.root = slot.entry ∧ ∃ k ∈ kinds, Admitted rules s k slot.target

theorem answers_exact (catalogue : List Sense) (rules : List Necessity) (slot : Slot) (s : Sense) :
    s ∈ answers catalogue rules slot ↔ Reference catalogue rules slot s := by
  simp [answers, selected_exact, accepts_exact, Reference, and_assoc]

theorem exact_executable_lookup (catalogue : List Sense) (rules : List Necessity) :
    ArabicCoverage.ExactWithin (fun _ : Slot => True) (Reference catalogue rules)
      (fun slot s => s ∈ answers catalogue rules slot) := by
  intro slot _ s
  exact answers_exact catalogue rules slot s

theorem extension_preserves_readings (old extra : List Sense) (entry : String) (s : Sense)
    (member : s ∈ selected old entry) : s ∈ selected (old ++ extra) entry := by
  obtain ⟨h, same⟩ := (selected_exact old entry s).mp member
  exact (selected_exact (old ++ extra) entry s).mpr ⟨List.mem_append_left extra h, same⟩

def targetFormula (context : String) (target : List String) : Formula :=
  MantuqMafhum.conjunction (target.map (componentFormula context))

def alternative (binding : Binding) (context : String) (rules : List Necessity)
    (target : List String) (s : Sense) : ReadingEnumeration.Alternative :=
  ⟨s.id, binding, if accepts rules s target then some [targetFormula context target] else none⟩

theorem alternative_preserves_binding (binding : Binding) (context : String)
    (rules : List Necessity) (target : List String) (s : Sense) :
    (alternative binding context rules target s).binding = binding := rfl

theorem alternative_premise_sound (binding : Binding) (context : String)
    (rules : List Necessity) (target : List String) (s : Sense)
    (model : String → List String → Prop) (env : Nat → String)
    (whole : Meaning s.components (fun c => model c [context]))
    (ruleTruth : RulesHold rules s (fun c => model c [context]))
    (ps : List Formula)
    (ready : (alternative binding context rules target s).premises = some ps) :
    MantuqMafhum.PremisesHold ps model env := by
  simp only [alternative] at ready
  split at ready
  next h =>
    have same : ps = [targetFormula context target] := (Option.some.inj ready).symm
    subst ps
    obtain ⟨k, _, admitted⟩ := (accepts_exact rules s target).mp h
    have nonempty := admitted.2.2.1
    have truth := accepted_indication_sound rules s target (fun c => model c [context]) whole ruleTruth h
    have formula := (formula_bridge target nonempty context model env).mpr truth
    intro f hf
    have : f = targetFormula context target := by simpa using hf
    subst f
    exact formula
  next h => simp at ready

def pool (binding : Binding) (context : String) (catalogue : List Sense)
    (rules : List Necessity) (slot : Slot) : List ReadingEnumeration.Alternative :=
  match selected catalogue slot.entry with
  | [] => [⟨"UNMEASURED:" ++ slot.entry, binding, none⟩]
  | senses => senses.map (alternative binding context rules slot.target)

/-- A missing entry is an explicit unresolved alternative, never an erased slot. -/
theorem missing_entry_retained (binding : Binding) (context : String)
    (catalogue : List Sense) (rules : List Necessity) (slot : Slot)
    (missing : selected catalogue slot.entry = []) :
    pool binding context catalogue rules slot = [⟨"UNMEASURED:" ++ slot.entry, binding, none⟩] := by
  simp [pool, missing]

def ready (pools : List (List ReadingEnumeration.Alternative)) : Bool :=
  !pools.isEmpty && (ReadingEnumeration.count pools != 0) &&
    (ReadingEnumeration.enumerate pools).all (fun row => row.all (fun a => a.premises.isSome))

theorem ready_covers_every_selection (pools : List (List ReadingEnumeration.Alternative))
    (h : ready pools = true) (row : List ReadingEnumeration.Alternative)
    (licensed : ReadingEnumeration.Selects pools row) (a : ReadingEnumeration.Alternative)
    (member : a ∈ row) : a.premises.isSome = true := by
  have all := (Bool.and_eq_true_iff.mp h).2
  have rowCheck := List.all_eq_true.mp all row ((ReadingEnumeration.enumeration_exact pools row).mpr licensed)
  exact List.all_eq_true.mp rowCheck a member

theorem unresolved_selection_blocks (pools : List (List ReadingEnumeration.Alternative))
    (row : List ReadingEnumeration.Alternative) (licensed : ReadingEnumeration.Selects pools row)
    (a : ReadingEnumeration.Alternative) (member : a ∈ row) (missing : a.premises = none) :
    ready pools = false := by
  cases h : ready pools with
  | false => rfl
  | true =>
    have impossible := ready_covers_every_selection pools h row licensed a member
    simp [missing] at impossible

theorem empty_batch_blocks : ready [] = false := by simp [ready]

def boundedReady (limit : Nat) (pools : List (List ReadingEnumeration.Alternative)) : Option Bool :=
  if ReadingEnumeration.count pools > limit then none else some (ready pools)

theorem budget_preserves_verdict (limit : Nat) (pools : List (List ReadingEnumeration.Alternative)) :
    boundedReady limit pools = some true ↔ ReadingEnumeration.count pools ≤ limit ∧ ready pools = true := by
  simp [boundedReady]

/-- Relational composition requires a proved bridge to the next stage's domain.
A hash, a successful test, or a caller Boolean cannot supply this premise. -/
def compose {A B C : Type} (first : A → B → Prop) (second : B → C → Prop) : A → C → Prop :=
  fun a c => ∃ b, first a b ∧ second b c

theorem compose_exact_with_domains {A B C : Type}
    (inputDomain : A → Prop) (middleDomain : B → Prop)
    (r1 a1 : A → B → Prop) (r2 a2 : B → C → Prop)
    (first : ArabicCoverage.ExactWithin inputDomain r1 a1)
    (second : ArabicCoverage.ExactWithin middleDomain r2 a2)
    (handoff : ∀ a, inputDomain a → ∀ b, r1 a b → middleDomain b) :
    ArabicCoverage.ExactWithin inputDomain (compose r1 r2) (compose a1 a2) := by
  intro a ha c
  constructor
  · rintro ⟨b, hab, hbc⟩
    have rb := (first a ha b).mp hab
    exact ⟨b, rb, (second b (handoff a ha b rb) c).mp hbc⟩
  · rintro ⟨b, hab, hbc⟩
    exact ⟨b, (first a ha b).mpr hab, (second b (handoff a ha b hab) c).mpr hbc⟩

def chain {State : Type} : List (State → State → Prop) → State → State → Prop
  | [] => fun a b => a = b
  | step :: steps => compose step (chain steps)

inductive ExactStages {State : Type} :
    List (State → State → Prop) → List (State → State → Prop) → Prop
  | nil : ExactStages [] []
  | cons {a r as rs} : (∀ x y, a x y ↔ r x y) → ExactStages as rs →
      ExactStages (a :: as) (r :: rs)

/-- Structural induction over every finite number of licensed stages. This
closes composition only after exactness of EACH stage has been proved. -/
theorem chain_exact {State : Type} (actual reference : List (State → State → Prop))
    (stages : ExactStages actual reference) :
    ∀ x y, chain actual x y ↔ chain reference x y := by
  induction stages with
  | nil => intro x y; rfl
  | @cons a r as rs same rest ih =>
    intro x y
    constructor
    · rintro ⟨mid, first, tail⟩
      exact ⟨mid, (same x mid).mp first, (ih mid y).mp tail⟩
    · rintro ⟨mid, first, tail⟩
      exact ⟨mid, (same x mid).mpr first, (ih mid y).mpr tail⟩

end Nabt.LexicalCompletion
