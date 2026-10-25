import Nabt.InflectionEvidence
import Nabt.QatrRules

/-!
Qatr al-Nada, pinned OpenITI text, lines 54–95. Conditional inflection
readings, not lexical classification or all-book/Arabic completeness.
Reuse NABT's 45 class/case realizations rather than creating a rival grammar.
The six-noun and bare-diptote classes INCLUDE their grammatical conditions.
An estimated movement is deliberately erased: its annotation must not leak
the answer into a purported observation. Class membership is optional evidence.
Source identity is full bytes, not a caller-provided hash or truth flag.
-/
namespace Nabt.QatrReading
open Words (Kind DeclensionClass)
open Governors (Case)
open InflectionEvidence (Row Realization Sign Mode)

def lawId : String := "nabt.qatr-reading.v1"
def sourceSha256 : String := "2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d"

inductive Mark where
  | damma | fatha | kasra | sukun | waw | alif | ya
  | nunRetained | nunDeleted | weakDeleted | hidden
  deriving DecidableEq, Repr

def marks : List Mark := [.damma, .fatha, .kasra, .sukun, .waw, .alif, .ya,
  .nunRetained, .nunDeleted, .weakDeleted, .hidden]

def Mark.label : Mark → String
  | .damma => "damma" | .fatha => "fatha" | .kasra => "kasra" | .sukun => "sukun"
  | .waw => "waw" | .alif => "alif" | .ya => "ya"
  | .nunRetained => "nun_retained" | .nunDeleted => "nun_deleted"
  | .weakDeleted => "weak_deleted" | .hidden => "hidden"

def observe (r : Realization) : Mark :=
  if r.mode = .estimated then .hidden else
    match r.sign with
    | .damma => .damma | .fatha => .fatha | .kasra => .kasra | .sukun => .sukun
    | .waw => .waw | .alif => .alif | .ya => .ya
    | .nunRetained => .nunRetained | .nunDeleted => .nunDeleted
    | .weakDeleted => .weakDeleted

structure Query where
  kind : Kind
  mark : Mark
  classes : Option (List DeclensionClass)
  deriving DecidableEq, Repr

def permits (q : Query) (row : Row) : Bool :=
  row.cls.kind == q.kind && observe row.realization == q.mark &&
    match q.classes with | none => true | some cs => cs.contains row.cls

def read (q : Query) : List Row := InflectionEvidence.rows.filter (permits q)

/-- Independent specification: legal realization plus supplied observations. -/
def Compatible (q : Query) (row : Row) : Prop :=
  InflectionEvidence.realize row.cls row.grammaticalCase = some row.realization ∧
  row.cls.kind = q.kind ∧ observe row.realization = q.mark ∧
  (match q.classes with | none => True | some cs => row.cls ∈ cs)

theorem read_exact (q : Query) (row : Row) : row ∈ read q ↔ Compatible q row := by
  cases q with
  | mk kind mark classes =>
    cases classes <;>
      simp [read, permits, Compatible, InflectionEvidence.mem_rows_exact, and_assoc]

theorem read_sound (q : Query) (row : Row) (h : row ∈ read q) : Compatible q row :=
  (read_exact q row).mp h

theorem read_complete (q : Query) (row : Row) (h : Compatible q row) : row ∈ read q :=
  (read_exact q row).mpr h

theorem unknown_class_preserves (kind : Kind) (mark : Mark)
    (cs : List DeclensionClass) (row : Row)
    (h : row ∈ read ⟨kind, mark, some cs⟩) : row ∈ read ⟨kind, mark, none⟩ := by
  rw [read_exact] at h ⊢
  exact ⟨h.1, h.2.1, h.2.2.1, trivial⟩

theorem narrow_classes (kind : Kind) (mark : Mark)
    (small large : List DeclensionClass) (hsub : ∀ c ∈ small, c ∈ large)
    (row : Row) (h : row ∈ read ⟨kind, mark, some small⟩) :
    row ∈ read ⟨kind, mark, some large⟩ := by
  rw [read_exact] at h ⊢
  exact ⟨h.1, h.2.1, h.2.2.1, hsub _ h.2.2.2⟩

theorem closed_empty_is_not_unknown (kind : Kind) (mark : Mark) :
    read ⟨kind, mark, some []⟩ = [] := by simp [read, permits]

def casesFor (q : Query) : List Case :=
  Words.allCases.filter fun c => (read q).any fun row => row.grammaticalCase == c

theorem case_exact (q : Query) (c : Case) :
    c ∈ casesFor q ↔ ∃ row, Compatible q row ∧ row.grammaticalCase = c := by
  simp [casesFor, Words.mem_allCases, List.any_eq_true, read_exact]

theorem five_verb_two_readings :
    casesFor ⟨.verb, .nunDeleted, none⟩ = [.nasb, .jazm] := by decide

theorem feminine_plural_two_readings :
    casesFor ⟨.noun, .kasra, some [.iJamF]⟩ = [.nasb, .jarr] := by decide

theorem dual_two_readings :
    casesFor ⟨.noun, .ya, some [.iMuthanna]⟩ = [.nasb, .jarr] := by decide

theorem estimated_erases_case :
    casesFor ⟨.noun, .hidden, some [.iMaqsur]⟩ = [.nasb, .raf, .jarr] := by decide

theorem weak_deletion_not_damma :
    casesFor ⟨.verb, .weakDeleted, none⟩ = [.jazm] ∧
    casesFor ⟨.verb, .damma, none⟩ = [.raf] := by decide

/-- A completed proposal is an exact SET of rows. Duplicates do not add readings.
No ranking score can remove a compatible row. This is finite-table completeness. -/
def completeProposal (q : Query) (proposed : List Row) : Bool :=
  (read q).all proposed.contains && proposed.all (read q).contains

theorem complete_proposal_iff (q : Query) (proposed : List Row) :
    completeProposal q proposed = true ↔
      (∀ row ∈ read q, row ∈ proposed) ∧ (∀ row ∈ proposed, row ∈ read q) := by
  simp [completeProposal, List.all_eq_true]

theorem omission_rejected (q : Query) (proposed : List Row) (row : Row)
    (valid : row ∈ read q) (missing : row ∉ proposed) :
    completeProposal q proposed = false := by
  cases h : completeProposal q proposed
  · rfl
  · exact False.elim (missing (((complete_proposal_iff q proposed).mp h).1 row valid))

structure Binding where
  source : List UInt8
  passage : List UInt8
  occurrence : List UInt8
  context : List UInt8
  deriving DecidableEq, Repr

structure Certificate where
  binding : Binding
  query : Query
  readings : List Row
  deriving DecidableEq, Repr

def verify (trusted : Binding) (premises : Query) (cert : Certificate) : Bool :=
  cert.binding == trusted && cert.query == premises && completeProposal premises cert.readings

theorem verify_exact (b : Binding) (q : Query) (c : Certificate) :
    verify b q c = true ↔ c.binding = b ∧ c.query = q ∧
      (∀ r ∈ read q, r ∈ c.readings) ∧ (∀ r ∈ c.readings, r ∈ read q) := by
  simp [verify, complete_proposal_iff, and_assoc]

theorem source_preserved (b : Binding) (q : Query) (c : Certificate)
    (h : verify b q c = true) : c.binding.source = b.source := by
  exact congrArg Binding.source ((verify_exact b q c).mp h).1

theorem premises_preserved (b : Binding) (q : Query) (c : Certificate)
    (h : verify b q c = true) : c.query = q := ((verify_exact b q c).mp h).2.1

theorem changed_binding_rejected (b : Binding) (q : Query) (c : Certificate)
    (h : c.binding ≠ b) : verify b q c = false := by simp [verify, h]

inductive ImperativeClass where
  | sound | weak | five
  deriving DecidableEq, Repr

def imperativeMark : ImperativeClass → Mark
  | .sound => .sukun | .weak => .weakDeleted | .five => .nunDeleted

theorem imperative_exceptions : imperativeMark .sound = .sukun ∧
    imperativeMark .weak = .weakDeleted ∧ imperativeMark .five = .nunDeleted := by decide

theorem qatr_five_verb_bridge (c : QatrRules.FiveVerbCase) :
    let grammaticalCase := match c with | .raf => Case.raf | .nasb => .nasb | .jazm => .jazm
    InflectionEvidence.signFor .fKhamsaW grammaticalCase =
      (match QatrRules.fiveVerbNun c with | .retained => Sign.nunRetained | .deleted => .nunDeleted) := by
  cases c <;> rfl

end Nabt.QatrReading
