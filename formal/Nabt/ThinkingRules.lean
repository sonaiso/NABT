import Nabt.SourceSemantics
import Nabt.RationalInquiry

/-! A software evidence contract inspired by the supplied Thinking paragraphs
26–28. It is not a biological theory or proof that perception is infallible.
The reviewed ledger and its interpretation are explicit premises. -/
namespace Nabt.ThinkingRules
open SourceSemantics ClassicalLanguageEvidence

def lawId := "nabt.thinking-source-information.v1"
inductive Basis where
  | information | priorOpinion
  deriving DecidableEq, Repr
structure Information where
  binding : Binding
  basis : Basis
  proposition : Formula
  citation : Passage
  deriving DecidableEq, Repr

def Admitted (expected : Binding) (sources : List Source)
    (reviewed : List Information) (item : Information) : Prop :=
  item ∈ reviewed ∧ item.binding = expected ∧ item.basis = .information ∧
  Attested sources item.citation
instance (b : Binding) (ss : List Source) (rs : List Information) (i : Information) :
    Decidable (Admitted b ss rs i) := by unfold Admitted; infer_instance

def acquire (b : Binding) (ss : List Source) (rs : List Information) : List Information :=
  rs.filter (fun i => decide (Admitted b ss rs i))

theorem acquire_exact (b : Binding) (ss : List Source) (rs : List Information) (i : Information) :
    i ∈ acquire b ss rs ↔ Admitted b ss rs i := by
  simp only [acquire, List.mem_filter, decide_eq_true_eq]
  exact ⟨fun h => h.2, fun h => ⟨h.1, h⟩⟩

theorem opinion_cannot_supply_premise (b : Binding) (ss : List Source)
    (rs : List Information) (i : Information) (opinion : i.basis = .priorOpinion) :
    i ∉ acquire b ss rs := by
  intro member
  have h := ((acquire_exact b ss rs i).mp member).2.2.1
  simp [opinion] at h

theorem acquired_keeps_source (b : Binding) (ss : List Source)
    (rs : List Information) (i : Information) (h : i ∈ acquire b ss rs) :
    Attested ss i.citation := ((acquire_exact b ss rs i).mp h).2.2.2

theorem withdrawn_information_unavailable (b : Binding) (ss : List Source)
    (rs : List Information) (i : Information) (gone : i.citation.source ∉ ss) :
    i ∉ acquire b ss rs := by
  intro member
  exact gone (acquired_keeps_source b ss rs i member).1

end Nabt.ThinkingRules
