import Nabt.QualifiedInference

namespace UsulLedger
open Nabt.SemanticInference Nabt.QualifiedInference

def caseRequirements (validity cause condition absence : Atom α) : List (Requirement α) :=
  [⟨.premise,validity⟩, ⟨.cause,cause⟩, ⟨.condition,condition⟩, ⟨.blockerAbsence,absence⟩]

/-- The source-qualified owner must have support for all four exact atoms.
In particular, absence of the blocker is negative evidence and its opposite
cannot also be in the admitted store. -/
theorem qualified_case_evidence [DecidableEq α] (v c s b : Atom α) (known : List (Atom α))
    (pass : assess .causal (caseRequirements v c s b) known = .supported) :
    v ∈ known ∧ c ∈ known ∧ s ∈ known ∧ b.positive = false ∧ b ∈ known ∧ b.opposite ∉ known := by
  have p := ((supported_exact ..).mp pass).2.1
  have hv := p ⟨.premise,v⟩ (by simp [caseRequirements])
  have hc := p ⟨.cause,c⟩ (by simp [caseRequirements])
  have hs := p ⟨.condition,s⟩ (by simp [caseRequirements])
  have hb := blocker_requires_explicit_negative .causal (caseRequirements v c s b) known
    ⟨.blockerAbsence,b⟩ (by simp [caseRequirements]) rfl pass
  exact ⟨hv,hc,hs,hb⟩

end UsulLedger
#print axioms UsulLedger.qualified_case_evidence
