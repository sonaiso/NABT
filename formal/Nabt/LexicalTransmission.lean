import Nabt.LexicalCatalog

/-! Documentary transmission, separate from lexical interpretation and truth.
Pair reviews are premises about the exact claim and named source families.
Different books, repeated files, and distinct readings never supply independence
or tawatur by themselves. The installed ledger has no independence judgments. -/
namespace Nabt.LexicalTransmission

def lawId := "nabt.lexical-transmission.v1"

structure Claim where
  entry : String
  reading : String
  context : String
  deriving DecidableEq, Repr

structure Report where
  claim : Claim
  source : String
  citation : LexicalDenotation.Citation
  deriving DecidableEq, Repr

inductive Relation where
  | dependent | independent
  deriving DecidableEq, Repr

structure PairReview where
  claim : Claim
  left : String
  right : String
  relation : Relation
  evidence : String
  deriving DecidableEq, Repr

def pairReviewed (ledger : List PairReview) (claim : Claim)
    (a b : String) (relation : Relation) : Bool :=
  ledger.any fun r => decide (r.claim = claim ∧ r.relation = relation ∧
    r.evidence ≠ "" ∧ a ≠ b ∧
    ((r.left = a ∧ r.right = b) ∨ (r.left = b ∧ r.right = a)))

def sources (reports : List Report) : List String :=
  (reports.map Report.source).eraseDups

def allIndependent (ledger : List PairReview) (claim : Claim) (ids : List String) : Bool :=
  ids.all fun a => ids.all fun b => a == b || pairReviewed ledger claim a b .independent

def anyDependent (ledger : List PairReview) (claim : Claim) (ids : List String) : Bool :=
  ids.any fun a => ids.any fun b => pairReviewed ledger claim a b .dependent

def anyConflict (ledger : List PairReview) (claim : Claim) (ids : List String) : Bool :=
  ids.any fun a => ids.any fun b => pairReviewed ledger claim a b .dependent &&
    pairReviewed ledger claim a b .independent

def validReports (claim : Claim) (reports : List Report) : Bool :=
  !reports.isEmpty && reports.all fun r => decide
    (r.claim = claim ∧ r.source ≠ "" ∧ r.source = r.citation.work ∧
     r.citation.quotation ≠ "" ∧ r.citation.startByte < r.citation.endByte)

inductive Status where
  | unassessed | identifiedSingleSource | multipleUnresolved
  | multipleDependent | multipleReviewedIndependent | inconsistentReviews
  deriving DecidableEq, Repr

def Status.label : Status → String
  | .unassessed => "UNASSESSED"
  | .identifiedSingleSource => "IDENTIFIED_SINGLE_SOURCE_REPORT"
  | .multipleUnresolved => "MULTIPLE_SOURCES_INDEPENDENCE_UNASSESSED"
  | .multipleDependent => "MULTIPLE_SOURCES_DEPENDENCY_RECORDED"
  | .multipleReviewedIndependent => "MULTIPLE_SOURCES_INDEPENDENT_UNDER_REVIEW_PREMISES"
  | .inconsistentReviews => "INCONSISTENT_DEPENDENCY_REVIEWS"

def classify (ledger : List PairReview) (claim : Claim) (reports : List Report) : Status :=
  let ids := sources reports
  if !validReports claim reports then .unassessed
  else if ids.length = 1 then .identifiedSingleSource
  else if ids.length < 2 then .unassessed
  else if anyConflict ledger claim ids then .inconsistentReviews
  else if anyDependent ledger claim ids then .multipleDependent
  else if allIndependent ledger claim ids then .multipleReviewedIndependent
  else .multipleUnresolved

theorem invalid_reports_unassessed (ledger : List PairReview) (claim : Claim)
    (reports : List Report) (h : validReports claim reports = false) :
    classify ledger claim reports = .unassessed := by simp [classify, h]

theorem empty_reports_unassessed (ledger : List PairReview) (claim : Claim) :
    classify ledger claim [] = .unassessed := by simp [classify, validReports]

theorem single_family_is_single (ledger : List PairReview) (claim : Claim)
    (reports : List Report) (valid : validReports claim reports = true)
    (one : (sources reports).length = 1) :
    classify ledger claim reports = .identifiedSingleSource := by
  simp [classify, valid, one]

theorem duplicate_report_keeps_one_source (r : Report) : sources [r, r] = [r.source] := by
  simp [sources, List.eraseDups, List.eraseDupsBy, List.eraseDupsBy.loop]

theorem independent_requires_review (ledger : List PairReview) (claim : Claim)
    (reports : List Report)
    (h : classify ledger claim reports = .multipleReviewedIndependent) :
    validReports claim reports = true ∧ 2 ≤ (sources reports).length ∧
      anyConflict ledger claim (sources reports) = false ∧
      anyDependent ledger claim (sources reports) = false ∧
      allIndependent ledger claim (sources reports) = true := by
  unfold classify at h
  dsimp only at h
  split at h
  · contradiction
  · rename_i good
    have valid : validReports claim reports = true := by simpa using good
    split at h
    · contradiction
    · split at h
      · contradiction
      · rename_i count
        split at h
        · contradiction
        · rename_i conflict
          split at h
          · contradiction
          · rename_i dependent
            split at h
            · rename_i independent
              exact ⟨valid, Nat.le_of_not_gt count, by simpa using conflict,
                by simpa using dependent, independent⟩
            · contradiction

theorem independent_each_pair (ledger : List PairReview) (claim : Claim)
    (ids : List String) (h : allIndependent ledger claim ids = true)
    (a b : String) (ha : a ∈ ids) (hb : b ∈ ids) (different : a ≠ b) :
    pairReviewed ledger claim a b .independent = true := by
  have row := List.all_eq_true.mp h a ha
  have pair := List.all_eq_true.mp row b hb
  simpa [different] using pair

theorem pair_review_has_bound_evidence (ledger : List PairReview) (claim : Claim)
    (a b : String) (relation : Relation)
    (h : pairReviewed ledger claim a b relation = true) :
    ∃ r ∈ ledger, r.claim = claim ∧ r.relation = relation ∧ r.evidence ≠ "" ∧ a ≠ b ∧
      ((r.left = a ∧ r.right = b) ∨ (r.left = b ∧ r.right = a)) := by
  simpa [pairReviewed] using h

theorem no_review_no_pair (claim : Claim) (a b : String) (relation : Relation) :
    pairReviewed [] claim a b relation = false := by simp [pairReviewed]

theorem different_claim_blocks (claim : Claim) (reports : List Report)
    (r : Report) (member : r ∈ reports) (different : r.claim ≠ claim) :
    validReports claim reports = false := by
  apply Bool.eq_false_iff.mpr
  intro h
  have each := List.all_eq_true.mp (Bool.and_eq_true_iff.mp h).2 r member
  simp only [decide_eq_true_eq] at each
  exact different each.1

/-- Imported attributions are not a historical assessment of authors or chains. -/
def installedReviews : List PairReview := []

def reportOf (context : String) (s : LexicalDenotation.Sense) : Report :=
  ⟨⟨s.root, s.id, context⟩, s.citation.work, s.citation⟩

def installedReports (entry context : String) : List Report :=
  (LexicalCatalog.forRoot entry).map (reportOf context)

theorem installed_readings_preserved (entry context : String) :
    (installedReports entry context).map (fun r => r.claim.reading) =
      (LexicalCatalog.forRoot entry).map LexicalDenotation.Sense.id := by
  simp [installedReports, reportOf, List.map_map]

theorem context_preserved (context : String) (s : LexicalDenotation.Sense) :
    (reportOf context s).claim.context = context := rfl

end Nabt.LexicalTransmission
