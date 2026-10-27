import Nabt.Foundation
import Nabt.LinguisticTruth

/-! A116-bound composition of the existing lexical calculus. This module proves
the finite, conditional contract; it does not certify the acquisition or truth
of the supplied lexical ledger, context, or signed premises. A complete direct
projection is deliberately required: an orthographic residual cannot be turned
into an A116 derivation by attaching a Boolean or a digest. -/
namespace Nabt.CertifiedLexical
open LinguisticTruth

def lawId : String := "nabt.certified-lexical.v1"

/-- The occurrence stores the entire raw source, with an exact cluster-bound
byte interval. The expression is a lexical label, not a replacement source. -/
def SourceBound (source : Foundation.Source) (frame : Frame) : Prop :=
  frame.occurrence.source = source.id ∧
  frame.occurrence.revision = source.revision ∧
  frame.occurrence.raw = source.text ∧
  frame.occurrence.startByte < frame.occurrence.endByte ∧
  frame.occurrence.endByte ≤ source.text.utf8ByteSize ∧
  frame.occurrence.startByte ∈ Foundation.sourceBoundaries source ∧
  frame.occurrence.endByte ∈ Foundation.sourceBoundaries source ∧
  frame.occurrence.context ≠ "" ∧ frame.expression ≠ "" ∧ frame.convention ≠ ""

instance (source : Foundation.Source) (frame : Frame) : Decidable (SourceBound source frame) := by
  unfold SourceBound
  infer_instance

/-- Only the exact nonempty, fully enumerated finite candidate set is licensed.
Its intended senses need separate signed evidence in the inherited calculus. -/
def Ready (source : Foundation.Source) (cells : List Nabt.Atom) (frame : Frame)
    (designations : List Designation) (relations : List Relation)
    (proposed : List Candidate) (budget : Nat) : Prop :=
  (Foundation.project source).status = .complete ∧
  cells = (Foundation.project source).cells ∧ cells ≠ [] ∧
  SourceBound source frame ∧
  designations.length + relations.length ≤ budget ∧
  proposed = enumerate frame designations relations ∧ proposed ≠ []

instance (source : Foundation.Source) (cells : List Nabt.Atom) (frame : Frame)
    (ds : List Designation) (rs : List Relation) (cs : List Candidate) (budget : Nat) :
    Decidable (Ready source cells frame ds rs cs budget) := by
  unfold Ready
  infer_instance

def checkCandidates (source : Foundation.Source) (cells : List Nabt.Atom) (frame : Frame)
    (ds : List Designation) (rs : List Relation) (cs : List Candidate) (budget : Nat) : Bool :=
  decide (Ready source cells frame ds rs cs budget)

def accepted (source : Foundation.Source) (cells : List Nabt.Atom) (frame : Frame)
    (ds : List Designation) (rs : List Relation)
    (known : List (SemanticInference.Atom Judgment))
    (cs : List Candidate) (budget : Nat) : List Candidate :=
  if checkCandidates source cells frame ds rs cs budget then
    cs.filter (fun candidate => assess frame candidate known == .supported)
  else []

theorem candidate_check_exact (source : Foundation.Source) (cells : List Nabt.Atom)
    (frame : Frame) (ds : List Designation) (rs : List Relation)
    (cs : List Candidate) (budget : Nat) :
    checkCandidates source cells frame ds rs cs budget = true ↔
      Ready source cells frame ds rs cs budget := by simp [checkCandidates]

theorem checked_projection_complete (source : Foundation.Source) (cells : List Nabt.Atom)
    (frame : Frame) (ds : List Designation) (rs : List Relation)
    (cs : List Candidate) (budget : Nat)
    (checked : checkCandidates source cells frame ds rs cs budget = true) :
    (Foundation.project source).status = .complete :=
  ((candidate_check_exact _ _ _ _ _ _ _).mp checked).1

theorem checked_cells_exact (source : Foundation.Source) (cells : List Nabt.Atom)
    (frame : Frame) (ds : List Designation) (rs : List Relation)
    (cs : List Candidate) (budget : Nat)
    (checked : checkCandidates source cells frame ds rs cs budget = true) :
    cells = (Foundation.project source).cells :=
  ((candidate_check_exact _ _ _ _ _ _ _).mp checked).2.1

theorem checked_source_bound (source : Foundation.Source) (cells : List Nabt.Atom)
    (frame : Frame) (ds : List Designation) (rs : List Relation)
    (cs : List Candidate) (budget : Nat)
    (checked : checkCandidates source cells frame ds rs cs budget = true) :
    SourceBound source frame :=
  ((candidate_check_exact _ _ _ _ _ _ _).mp checked).2.2.2.1

theorem partial_source_cannot_certify (source : Foundation.Source) (cells : List Nabt.Atom)
    (frame : Frame) (ds : List Designation) (rs : List Relation)
    (cs : List Candidate) (budget : Nat)
    (incomplete : (Foundation.project source).status ≠ .complete) :
    checkCandidates source cells frame ds rs cs budget = false := by
  apply Bool.eq_false_iff.mpr
  exact fun checked => incomplete (checked_projection_complete _ _ _ _ _ _ _ checked)

theorem changed_source_cannot_certify (source : Foundation.Source) (cells : List Nabt.Atom)
    (frame : Frame) (ds : List Designation) (rs : List Relation)
    (cs : List Candidate) (budget : Nat)
    (changed : frame.occurrence.raw ≠ source.text) :
    checkCandidates source cells frame ds rs cs budget = false := by
  apply Bool.eq_false_iff.mpr
  exact fun checked => changed (checked_source_bound _ _ _ _ _ _ _ checked).2.2.1

theorem empty_proposal_cannot_certify (source : Foundation.Source) (cells : List Nabt.Atom)
    (frame : Frame) (ds : List Designation) (rs : List Relation) (budget : Nat) :
    checkCandidates source cells frame ds rs [] budget = false := by
  simp [checkCandidates, Ready]

theorem accepted_exact (source : Foundation.Source) (cells : List Nabt.Atom)
    (frame : Frame) (ds : List Designation) (rs : List Relation)
    (known : List (SemanticInference.Atom Judgment))
    (cs : List Candidate) (budget : Nat) (candidate : Candidate) :
    candidate ∈ accepted source cells frame ds rs known cs budget ↔
      Ready source cells frame ds rs cs budget ∧ candidate ∈ cs ∧
        assess frame candidate known = .supported := by
  by_cases ready : Ready source cells frame ds rs cs budget
  · simp [accepted, checkCandidates, ready]
  · simp [accepted, checkCandidates, ready]

/-- The enumerator and the independent declarative membership predicate agree
on this installed finite ledger. This is not completeness for Arabic. -/
theorem accepted_sound_and_complete (source : Foundation.Source) (cells : List Nabt.Atom)
    (frame : Frame) (ds : List Designation) (rs : List Relation)
    (known : List (SemanticInference.Atom Judgment))
    (cs : List Candidate) (budget : Nat) (candidate : Candidate)
    (ready : Ready source cells frame ds rs cs budget) :
    candidate ∈ accepted source cells frame ds rs known cs budget ↔
      Compatible frame ds rs candidate ∧ assess frame candidate known = .supported := by
  simp only [accepted_exact, ready, true_and]
  have same := ready.2.2.2.2.2.1
  rw [same, enumeration_exact]

theorem accepted_requires_usage_premise (source : Foundation.Source) (cells : List Nabt.Atom)
    (frame : Frame) (ds : List Designation) (rs : List Relation)
    (known : List (SemanticInference.Atom Judgment))
    (cs : List Candidate) (budget : Nat) (candidate : Candidate)
    (member : candidate ∈ accepted source cells frame ds rs known cs budget) :
    (obligation frame (.used frame candidate.intendedSense)).atom ∈ known :=
  used_sense_required frame candidate known
    ((accepted_exact _ _ _ _ _ _ _ _ _).mp member).2.2

theorem checked_candidates_retain_every_compatible (source : Foundation.Source)
    (cells : List Nabt.Atom) (frame : Frame) (ds : List Designation) (rs : List Relation)
    (cs : List Candidate) (budget : Nat)
    (checked : checkCandidates source cells frame ds rs cs budget = true)
    (candidate : Candidate) (compatible : Compatible frame ds rs candidate) :
    candidate ∈ cs := by
  have ready := (candidate_check_exact _ _ _ _ _ _ _).mp checked
  rw [ready.2.2.2.2.2.1]
  exact enumeration_complete frame ds rs candidate compatible

theorem checked_cells_reversible (source : Foundation.Source) (cells : List Nabt.Atom)
    (frame : Frame) (ds : List Designation) (rs : List Relation)
    (cs : List Candidate) (budget : Nat)
    (checked : checkCandidates source cells frame ds rs cs budget = true) :
    Nabt.Sequence.decode (Nabt.Sequence.encode cells) = (Foundation.project source).cells := by
  rw [Nabt.Sequence.decode_encode]
  exact checked_cells_exact _ _ _ _ _ _ _ checked

end Nabt.CertifiedLexical
