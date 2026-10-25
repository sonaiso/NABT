import Nabt.LexicalDenotation
import Nabt.QualifiedInference

/-!
# Convention-relative literal and figurative usage

Designation and relation ledgers are interpreted premises installed by the
source-replaying adapter. Citations retain identity; they do not prove a
designation, intended sense, or external fact. The finite ledger is enumerated
exactly, then QualifiedInference checks signed evidence. This is not unrestricted
Arabic parsing or completeness. Transfer is history, not automatically metaphor.
-/
namespace Nabt.LinguisticTruth
open SemanticInference

def lawId : String := "nabt.linguistic-truth.v1"
inductive Origin where
  | original | transferred
  deriving DecidableEq, Repr
def Origin.label : Origin → String
  | .original => "original" | .transferred => "transferred"
structure Designation where
  id : String
  expression : String
  sense : String
  convention : String
  origin : Origin
  citation : LexicalDenotation.Citation
  deriving DecidableEq, Repr
structure Frame where
  occurrence : LexicalDenotation.Occurrence
  expression : String
  convention : String
  deriving DecidableEq, Repr
/-- The source supports this relation type, not unrestricted similarity. -/
structure Relation where
  designation : Designation
  targetSense : String
  kind : String
  citation : LexicalDenotation.Citation
  deriving DecidableEq, Repr
structure Candidate where
  designation : Designation
  intendedSense : String
  relation : Option Relation
  deriving DecidableEq, Repr

def Candidate.literal (d : Designation) : Candidate := ⟨d, d.sense, none⟩
def Candidate.figurative (r : Relation) : Candidate := ⟨r.designation, r.targetSense, some r⟩
inductive UsageKind where
  | literal (origin : Origin) | figurative
  deriving DecidableEq, Repr
def UsageKind.label : UsageKind → String
  | .literal .original => "literal_original"
  | .literal .transferred => "literal_transferred"
  | .figurative => "figurative"

def Matches (f : Frame) (d : Designation) : Prop :=
  d.expression = f.expression ∧ d.convention = f.convention
instance (f : Frame) (d : Designation) : Decidable (Matches f d) := by
  unfold Matches; infer_instance
def Related (r : Relation) : Prop := r.targetSense ≠ r.designation.sense ∧ r.kind ≠ ""
instance (r : Relation) : Decidable (Related r) := by unfold Related; infer_instance

/-- Structural classification, before accepting evidence. -/
def shape (f : Frame) (c : Candidate) : Option UsageKind :=
  if ¬ Matches f c.designation then none else
  match c.relation with
  | none => if c.intendedSense = c.designation.sense then
      some (.literal c.designation.origin) else none
  | some r => if r.designation = c.designation ∧ r.targetSense = c.intendedSense ∧ Related r
      then some .figurative else none

def enumerate (f : Frame) (ds : List Designation) (rs : List Relation) : List Candidate :=
  (ds.filter (fun d => decide (Matches f d))).map Candidate.literal ++
  (rs.filter (fun r => decide (r.designation ∈ ds ∧ Matches f r.designation ∧ Related r))).map
    Candidate.figurative

/-- Declarative membership does not call the enumerator. -/
def Compatible (f : Frame) (ds : List Designation) (rs : List Relation) (c : Candidate) : Prop :=
  (∃ d ∈ ds, Matches f d ∧ Candidate.literal d = c) ∨
  (∃ r ∈ rs, r.designation ∈ ds ∧ Matches f r.designation ∧ Related r ∧
    Candidate.figurative r = c)

theorem enumeration_exact (f : Frame) (ds : List Designation) (rs : List Relation)
    (c : Candidate) : c ∈ enumerate f ds rs ↔ Compatible f ds rs c := by
  simp [enumerate, Compatible, List.mem_filter, and_assoc]
theorem enumeration_sound (f : Frame) (ds : List Designation) (rs : List Relation)
    (c : Candidate) (member : c ∈ enumerate f ds rs) : Compatible f ds rs c :=
  (enumeration_exact f ds rs c).mp member
theorem enumeration_complete (f : Frame) (ds : List Designation) (rs : List Relation)
    (c : Candidate) (licensed : Compatible f ds rs c) : c ∈ enumerate f ds rs :=
  (enumeration_exact f ds rs c).mpr licensed

def completeProposal (f : Frame) (ds : List Designation) (rs : List Relation)
    (proposed : List Candidate) : Bool := decide (proposed = enumerate f ds rs)
theorem complete_proposal_exact (f : Frame) (ds : List Designation) (rs : List Relation)
    (proposed : List Candidate) : completeProposal f ds rs proposed = true ↔
      proposed = enumerate f ds rs := by simp [completeProposal]
theorem omitted_candidate_rejected (f : Frame) (ds : List Designation) (rs : List Relation)
    (proposed : List Candidate) (c : Candidate) (licensed : Compatible f ds rs c)
    (omitted : c ∉ proposed) : completeProposal f ds rs proposed = false := by
  apply Bool.eq_false_iff.mpr
  intro accepted
  have same := (complete_proposal_exact f ds rs proposed).mp accepted
  exact omitted (same ▸ enumeration_complete f ds rs c licensed)

/-- Counts inspected ledger entries, not CPU instructions or Arabic coverage. -/
def boundedEnumerate (budget : Nat) (f : Frame) (ds : List Designation) (rs : List Relation) :
    Option (List Candidate) :=
  if ds.length + rs.length ≤ budget then some (enumerate f ds rs) else none
theorem bounded_exact (budget : Nat) (f : Frame) (ds : List Designation) (rs : List Relation)
    (cs : List Candidate) : boundedEnumerate budget f ds rs = some cs ↔
      ds.length + rs.length ≤ budget ∧ cs = enumerate f ds rs := by
  by_cases enough : ds.length + rs.length ≤ budget <;> simp [boundedEnumerate, enough, eq_comm]
theorem exhaustion_has_no_candidates (budget : Nat) (f : Frame)
    (ds : List Designation) (rs : List Relation) (exhausted : budget < ds.length + rs.length) :
    boundedEnumerate budget f ds rs = none := by
  simp [boundedEnumerate, Nat.not_le_of_lt exhausted]

/-- Fully bound propositions, not authorizing role names or truth flags. -/
inductive Judgment where
  | established (designation : Designation)
  | used (frame : Frame) (sense : String)
  | related (relation : Relation)
  | excludes (frame : Frame) (designation : Designation)
  deriving DecidableEq, Repr

def obligation (f : Frame) (j : Judgment) : QualifiedInference.Requirement Judgment :=
  ⟨.premise, ⟨j, true, f.occurrence.context⟩⟩
def requirements (f : Frame) (c : Candidate) : List (QualifiedInference.Requirement Judgment) :=
  [obligation f (.established c.designation), obligation f (.used f c.intendedSense)] ++
  match c.relation with
  | none => []
  | some r => [obligation f (.related r), obligation f (.excludes f c.designation)]

theorem requirements_profile (f : Frame) (c : Candidate) :
    QualifiedInference.Profile .direct (requirements f c) := by
  cases h : c.relation <;>
    simp [QualifiedInference.Profile, QualifiedInference.Kind.requiredRoles, requirements,
      h, obligation]

def assess (f : Frame) (c : Candidate) (known : List (Atom Judgment)) : QualifiedInference.Verdict :=
  if shape f c = none then .invalid
  else QualifiedInference.assess .direct (requirements f c) known

/-- Reuses the existing signed checker; this is no second inference calculus. -/
theorem supported_exact (f : Frame) (c : Candidate) (known : List (Atom Judgment)) :
    assess f c known = .supported ↔ shape f c ≠ none ∧
      QualifiedInference.Present known (requirements f c) ∧
      ∀ r ∈ requirements f c, r.atom.opposite ∉ known := by
  by_cases valid : shape f c = none
  · simp [assess, valid]
  · simp only [assess, valid, ↓reduceIte, QualifiedInference.supported_exact]
    simp [valid, requirements_profile]
theorem used_sense_required (f : Frame) (c : Candidate) (known : List (Atom Judgment))
    (accepted : assess f c known = .supported) :
    (obligation f (.used f c.intendedSense)).atom ∈ known := by
  exact ((supported_exact f c known).mp accepted).2.1 _ (by simp [requirements])
theorem figurative_requires_exclusion (f : Frame) (c : Candidate) (r : Relation)
    (known : List (Atom Judgment)) (relation : c.relation = some r)
    (accepted : assess f c known = .supported) :
    (obligation f (.excludes f c.designation)).atom ∈ known := by
  exact ((supported_exact f c known).mp accepted).2.1 _ (by simp [requirements, relation])
theorem figurative_requires_relation (f : Frame) (c : Candidate) (r : Relation)
    (known : List (Atom Judgment)) (relation : c.relation = some r)
    (accepted : assess f c known = .supported) :
    (obligation f (.related r)).atom ∈ known := by
  exact ((supported_exact f c known).mp accepted).2.1 _ (by simp [requirements, relation])
theorem opposite_blocks (f : Frame) (c : Candidate) (known : List (Atom Judgment))
    (r : QualifiedInference.Requirement Judgment) (member : r ∈ requirements f c)
    (opposite : r.atom.opposite ∈ known) : assess f c known ≠ .supported := by
  intro accepted
  exact ((supported_exact f c known).mp accepted).2.2 r member opposite
theorem changed_convention_rejected (f : Frame) (c : Candidate)
    (different : c.designation.convention ≠ f.convention) (known : List (Atom Judgment)) :
    assess f c known = .invalid := by
  simp [assess, shape, Matches, different]
theorem literal_keeps_origin (f : Frame) (d : Designation) (matched : Matches f d) :
    shape f (.literal d) = some (.literal d.origin) := by
  simp [shape, Candidate.literal, matched]

theorem literal_supported_by_explicit_evidence (f : Frame) (d : Designation)
    (matched : Matches f d) :
    assess f (.literal d) ((requirements f (.literal d)).map (·.atom)) = .supported := by
  apply (supported_exact f (.literal d) _).mpr
  refine ⟨by simp [literal_keeps_origin f d matched], ?_, ?_⟩
  · intro requirement member
    exact List.mem_map.mpr ⟨requirement, member, rfl⟩
  · simp [requirements, Candidate.literal, obligation, Atom.opposite]

theorem changed_frame_cannot_borrow_usage (f g : Frame) (d : Designation)
    (different : f ≠ g) :
    assess g (.literal d) ((requirements f (.literal d)).map (·.atom)) ≠ .supported := by
  intro accepted
  have used := used_sense_required g (.literal d) _ accepted
  simp [requirements, Candidate.literal, obligation] at used
  exact different used.1.symm

theorem no_evidence_no_support (f : Frame) (c : Candidate) : assess f c [] ≠ .supported := by
  intro accepted
  have used := used_sense_required f c [] accepted
  simp at used

/-- Literal classification has a concrete countermodel to external existence. -/
theorem literal_support_with_false_world (f : Frame) (d : Designation)
    (matched : Matches f d) (concept context : String) (env : Nat → String) :
    ∃ model : String → List String → Prop,
      assess f (.literal d) ((requirements f (.literal d)).map (·.atom)) = .supported ∧
      ¬ (LexicalDenotation.componentFormula context concept).meaning model env := by
  exact ⟨fun _ _ => False, literal_supported_by_explicit_evidence f d matched,
    LexicalDenotation.definition_does_not_assert_world concept context env⟩

/-- Linguistic classification supplies no fact in an arbitrary outside model. -/
theorem usage_does_not_assert_world (f : Frame) (c : Candidate)
    (known : List (Atom Judgment)) (_accepted : assess f c known = .supported)
    (concept context : String) (env : Nat → String) :
    ¬ (LexicalDenotation.componentFormula context concept).meaning (fun _ _ => False) env :=
  LexicalDenotation.definition_does_not_assert_world concept context env

end Nabt.LinguisticTruth
