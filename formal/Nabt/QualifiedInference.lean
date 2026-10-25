import Nabt.SemanticInference
import Nabt.Shakhsiyya3Rules
import Nabt.VerifiedReading

/-!
# Explicit qualified obligations before source-relative inference

A typed obligation labels an already interpreted, scoped, signed atom. Labels
do not derive atoms from words or establish empirical or normative truth.
Preventer absence needs explicit negative support, not absence from a list.
These profiles are an adapter contract, not an exhaustive account of schools.

Reuse `Shakhsiyya3Rules.contrast_with_necessary_condition` for opposition,
`SemanticInference` for signed proof replay and model soundness, and
`VerifiedReading.checked_closure_exact` for finite ground completeness.
-/
namespace Nabt.QualifiedInference
open SemanticInference

def lawId : String := "nabt.qualified-inference.v1"

inductive Role where
  | premise | cause | condition | blockerAbsence | necessaryBridge
  | originRuling | sharedCause | transferBridge
  deriving DecidableEq, Repr

inductive Kind where
  | direct | causal | opposition | analogy
  deriving DecidableEq, Repr

structure Requirement (α : Type) where
  role : Role
  atom : Atom α
  deriving DecidableEq, Repr

def Kind.requiredRoles : Kind → List Role
  | .direct => []
  | .causal => [.cause]
  | .opposition => [.necessaryBridge]
  | .analogy => [.originRuling, .sharedCause, .transferBridge]

/-- A role records the interpretation; it is never evidence for its atom. -/
def Profile (kind : Kind) (requirements : List (Requirement α)) : Prop :=
  requirements ≠ [] ∧
  (∀ role ∈ kind.requiredRoles, ∃ requirement ∈ requirements, requirement.role = role) ∧
  ∀ requirement ∈ requirements,
    requirement.role = .blockerAbsence → requirement.atom.positive = false

instance (kind : Kind) (requirements : List (Requirement α)) :
    Decidable (Profile kind requirements) := by
  unfold Profile
  infer_instance

def profileValid (kind : Kind) (requirements : List (Requirement α)) : Bool :=
  decide (Profile kind requirements)

inductive Verdict where
  | invalid | conflict | refuted | unknown | supported
  deriving DecidableEq, Repr

def Verdict.label : Verdict → String
  | .invalid => "INVALID_PROFILE"
  | .conflict => "CONFLICT"
  | .refuted => "REFUTED_PREMISE"
  | .unknown => "UNKNOWN_PREMISE"
  | .supported => "SUPPORTED_PREMISES"

variable [DecidableEq α]

def Contradicted (known : List (Atom α)) (requirements : List (Requirement α)) : Prop :=
  ∃ requirement ∈ requirements,
    requirement.atom ∈ known ∧ requirement.atom.opposite ∈ known

def Opposed (known : List (Atom α)) (requirements : List (Requirement α)) : Prop :=
  ∃ requirement ∈ requirements, requirement.atom.opposite ∈ known

def Present (known : List (Atom α)) (requirements : List (Requirement α)) : Prop :=
  ∀ requirement ∈ requirements, requirement.atom ∈ known

instance (known : List (Atom α)) (requirements : List (Requirement α)) :
    Decidable (Contradicted known requirements) := by unfold Contradicted; infer_instance
instance (known : List (Atom α)) (requirements : List (Requirement α)) :
    Decidable (Opposed known requirements) := by unfold Opposed; infer_instance
instance (known : List (Atom α)) (requirements : List (Requirement α)) :
    Decidable (Present known requirements) := by unfold Present; infer_instance

def assess (kind : Kind) (requirements : List (Requirement α))
    (known : List (Atom α)) : Verdict :=
  if ¬ Profile kind requirements then .invalid
  else if Contradicted known requirements then .conflict
  else if Opposed known requirements then .refuted
  else if Present known requirements then .supported
  else .unknown

/-- Exact support is both a presence check and an explicit conflict check. -/
theorem supported_exact (kind : Kind) (requirements : List (Requirement α))
    (known : List (Atom α)) :
    assess kind requirements known = .supported ↔
      Profile kind requirements ∧ Present known requirements ∧
      ∀ requirement ∈ requirements, requirement.atom.opposite ∉ known := by
  have noOpposed : (¬ Opposed known requirements) ↔
      ∀ requirement ∈ requirements, requirement.atom.opposite ∉ known := by
    simp [Opposed]
  have contradictionOpposed : Contradicted known requirements → Opposed known requirements := by
    rintro ⟨requirement, member, _, opposite⟩
    exact ⟨requirement, member, opposite⟩
  unfold assess
  split <;> simp_all
  split <;> simp_all
  split <;> simp_all

theorem conflict_exact (kind : Kind) (requirements : List (Requirement α))
    (known : List (Atom α)) :
    assess kind requirements known = .conflict ↔
      Profile kind requirements ∧ Contradicted known requirements := by
  by_cases profile : Profile kind requirements <;>
    by_cases conflict : Contradicted known requirements <;>
    by_cases opposed : Opposed known requirements <;>
    by_cases present : Present known requirements <;>
    simp [assess, profile, conflict, opposed, present]

/-- Missing evidence never licenses an explicit absence-of-preventer premise. -/
theorem missing_obligation_blocks (kind : Kind) (requirements : List (Requirement α))
    (known : List (Atom α)) (requirement : Requirement α)
    (member : requirement ∈ requirements) (missing : requirement.atom ∉ known) :
    assess kind requirements known ≠ .supported := by
  intro accepted
  exact missing (((supported_exact kind requirements known).mp accepted).2.1 requirement member)

/-- Unrelated supported obligations cannot cancel an opposite witness. -/
theorem opposite_obligation_blocks (kind : Kind) (requirements : List (Requirement α))
    (known : List (Atom α)) (requirement : Requirement α)
    (member : requirement ∈ requirements) (opposite : requirement.atom.opposite ∈ known) :
    assess kind requirements known ≠ .supported := by
  intro accepted
  exact ((supported_exact kind requirements known).mp accepted).2.2 requirement member opposite

theorem blocker_requires_explicit_negative (kind : Kind)
    (requirements : List (Requirement α)) (known : List (Atom α))
    (requirement : Requirement α) (member : requirement ∈ requirements)
    (blocker : requirement.role = .blockerAbsence)
    (accepted : assess kind requirements known = .supported) :
    requirement.atom.positive = false ∧ requirement.atom ∈ known ∧
      requirement.atom.opposite ∉ known := by
  obtain ⟨profile, present, clean⟩ := (supported_exact kind requirements known).mp accepted
  exact ⟨profile.2.2 requirement member blocker, present requirement member, clean requirement member⟩

theorem opposition_requires_bridge (requirements : List (Requirement α))
    (known : List (Atom α)) (accepted : assess .opposition requirements known = .supported) :
    ∃ requirement ∈ requirements, requirement.role = .necessaryBridge ∧
      requirement.atom ∈ known ∧ requirement.atom.opposite ∉ known := by
  obtain ⟨profile, present, clean⟩ := (supported_exact .opposition requirements known).mp accepted
  obtain ⟨requirement, member, role⟩ := profile.2.1 .necessaryBridge (by simp [Kind.requiredRoles])
  exact ⟨requirement, member, role, present requirement member, clean requirement member⟩

theorem analogy_requires_transfer_obligations (requirements : List (Requirement α))
    (known : List (Atom α)) (accepted : assess .analogy requirements known = .supported) :
    ∀ role ∈ [Role.originRuling, .sharedCause, .transferBridge],
      ∃ requirement ∈ requirements, requirement.role = role ∧
        requirement.atom ∈ known ∧ requirement.atom.opposite ∉ known := by
  obtain ⟨profile, present, clean⟩ := (supported_exact .analogy requirements known).mp accepted
  intro role member
  obtain ⟨requirement, included, same⟩ := profile.2.1 role member
  exact ⟨requirement, included, same, present requirement included, clean requirement included⟩

structure QualifiedRule (α : Type) where
  source : Source
  name : String
  kind : Kind
  requirements : List (Requirement α)
  head : Atom α
  deriving DecidableEq, Repr

def QualifiedRule.lower (rule : QualifiedRule α) : Rule α :=
  ⟨rule.source, rule.name, rule.requirements.map Requirement.atom, rule.head⟩

/-- Typed guards cannot bypass registered source, scope, or rule membership. -/
theorem supported_replays_existing_rule (program : Program α) (rule : QualifiedRule α)
    (known : List (Atom α)) (admitted : RuleAdmitted program rule.lower)
    (accepted : assess rule.kind rule.requirements known = .supported) :
    applyStep program known (.rule rule.lower) = some (known ++ [rule.head]) := by
  have present := ((supported_exact rule.kind rule.requirements known).mp accepted).2.1
  have body : ∀ atom ∈ rule.lower.body, atom ∈ known := by
    intro atom member
    obtain ⟨requirement, included, same⟩ := List.mem_map.mp member
    subst atom
    exact present requirement included
  rw [applyStep, ite_eq_left ⟨admitted, body⟩]
  rfl

/-- Consequence inherits the original calculus's source and premise conditions. -/
theorem supported_rule_derivable (program : Program α) (rule : QualifiedRule α)
    (known : List (Atom α)) (initial : ∀ atom ∈ known, Derivable program atom)
    (admitted : RuleAdmitted program rule.lower)
    (accepted : assess rule.kind rule.requirements known = .supported) :
    Derivable program rule.head := by
  exact applyStep_sound program known (known ++ [rule.head]) (.rule rule.lower) initial
    (supported_replays_existing_rule program rule known admitted accepted) rule.head (by simp)

/-- Shape of the separately supplied necessary relation Q → P and the
opposition witnesses ¬P, ¬Q. This authenticates neither the relation's source
nor the interpretation of its atoms. -/
def oppositionShape (antecedent consequent absent conclusion : Atom α) : Bool :=
  decide (antecedent.positive = true ∧ consequent.positive = true ∧
    antecedent.scope = consequent.scope ∧ absent = consequent.opposite ∧
    conclusion = antecedent.opposite)

theorem opposition_shape_exact (antecedent consequent absent conclusion : Atom α) :
    oppositionShape antecedent consequent absent conclusion = true ↔
      antecedent.positive = true ∧ consequent.positive = true ∧
      antecedent.scope = consequent.scope ∧ absent = consequent.opposite ∧
      conclusion = antecedent.opposite := by simp [oppositionShape]

/-- A classical interpretation is supplied separately from signed support.
The ordinary signed database need not satisfy this interpretation when it
contains conflicts. -/
def signedMeaning (model : α → String → Prop) (atom : Atom α) : Prop :=
  if atom.positive then model atom.value atom.scope else ¬ model atom.value atom.scope

/-- Reuse the existing necessary-condition theorem; do not infer necessity
from a forward implication or from a role label. -/
theorem checked_opposition_meaning (model : α → String → Prop)
    (antecedent consequent absent conclusion : Atom α)
    (checked : oppositionShape antecedent consequent absent conclusion = true)
    (necessary : model antecedent.value antecedent.scope →
      model consequent.value consequent.scope)
    (missing : signedMeaning model absent) : signedMeaning model conclusion := by
  obtain ⟨antecedentPositive, consequentPositive, _, absentSame, conclusionSame⟩ :=
    (opposition_shape_exact antecedent consequent absent conclusion).mp checked
  subst absent
  subst conclusion
  have missingCondition : ¬ model consequent.value consequent.scope := by
    simpa [signedMeaning, Atom.opposite, consequentPositive] using missing
  have result := Shakhsiyya3Rules.contrast_with_necessary_condition
    (model consequent.value consequent.scope) (model antecedent.value antecedent.scope)
    necessary missingCondition
  simpa [signedMeaning, Atom.opposite, antecedentPositive] using result

end Nabt.QualifiedInference
