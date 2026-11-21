import Nabt.QualifiedInference

namespace Lineage
open Nabt.SemanticInference Nabt.QualifiedInference

/-- The four atoms share the exact application key (including bearer, event and context).
The blocker is an explicit negative premise. -/
inductive Field where | validity | cause | condition | blocker
deriving DecidableEq, Repr

def reqs (key : κ) (scope : String) : List (Requirement (κ × Field)) :=
  [⟨.premise, ⟨(key,.validity),true,scope⟩⟩, ⟨.cause, ⟨(key,.cause),true,scope⟩⟩,
   ⟨.condition, ⟨(key,.condition),true,scope⟩⟩, ⟨.blockerAbsence, ⟨(key,.blocker),false,scope⟩⟩]

structure Step (κ γ : Type) where
  key : κ
  origin : γ
  branch : γ

variable {κ γ : Type} [DecidableEq κ] [DecidableEq γ]

def passes (db : List (Atom (κ × Field))) (scope : String) (k : κ) : Bool :=
  assess .causal (reqs k scope) db == .supported

abbrev EdgeKey (κ γ : Type) := String × γ × γ × κ

def edgeKey (bearer : String) (s : Step κ γ) : EdgeKey κ γ :=
  (bearer, s.origin, s.branch, s.key)

def complete (db : List (Atom (EdgeKey κ γ × Field))) (scope bearer : String) (start : γ) :
    List (Step κ γ) → Bool
  | [] => true
  | s :: rest => (s.origin == start) && (s.branch != start) && passes db scope (edgeKey bearer s) &&
                 complete db scope bearer s.branch rest

def fits (start : γ) : List (Step κ γ) → Prop
  | [] => True
  | s :: rest => s.origin = start ∧ s.branch ≠ start ∧ fits s.branch rest

/-- Reference specification mentions every local premise, its opposite, and connected
endpoints. The path is supplied; the store and its starting classification are hypotheses. -/
theorem complete_exact (db : List (Atom (EdgeKey κ γ × Field))) (scope bearer : String)
    (path : List (Step κ γ)) (start : γ) :
    complete db scope bearer start path = true ↔ fits start path ∧
      ∀ s ∈ path, Profile .causal (reqs (edgeKey bearer s) scope) ∧ Present db (reqs (edgeKey bearer s) scope) ∧
        ∀ r ∈ reqs (edgeKey bearer s) scope, r.atom.opposite ∉ db := by
  induction path generalizing start with
  | nil => simp [complete, fits]
  | cons s rest ih =>
    simp [complete, fits, passes, ih, supported_exact]
    constructor
    · rintro ⟨⟨⟨ha,hb⟩,hs⟩,ht,hr⟩
      exact ⟨⟨ha,hb,ht⟩,hs,hr⟩
    · rintro ⟨⟨ha,hb,ht⟩,hs,hr⟩
      exact ⟨⟨⟨ha,hb⟩,hs⟩,ht,hr⟩

def carries (db : List (Atom (EdgeKey κ γ × Field))) (scope bearer : String) (start : γ)
    (permit : EdgeKey κ γ → Bool) (path : List (Step κ γ)) : Bool :=
  complete db scope bearer start path && path.all (fun s => permit (edgeKey bearer s))

/-- For a property already present at the start, test each edge's permission for that property. -/
theorem carries_exact (db : List (Atom (EdgeKey κ γ × Field))) (scope bearer : String) (start : γ)
    (permit : EdgeKey κ γ → Bool) (path : List (Step κ γ)) :
    carries db scope bearer start permit path = true ↔
      complete db scope bearer start path = true ∧ ∀ s ∈ path, permit (edgeKey bearer s) = true := by
  simp [carries]

theorem foreign_cause_insufficient (db : List (Atom (κ × Field))) (scope : String)
    (k : κ) (missing : (⟨(k,Field.cause),true,scope⟩ : Atom (κ × Field)) ∉ db) :
    passes db scope k ≠ true := by
  intro h
  have hs : assess .causal (reqs k scope) db = .supported := by simpa [passes] using h
  exact missing (((supported_exact ..).mp hs).2.1 ⟨.cause,⟨(k,.cause),true,scope⟩⟩
    (by simp [reqs]))

end Lineage
#print axioms Lineage.complete_exact
#print axioms Lineage.carries_exact
#print axioms Lineage.foreign_cause_insufficient
