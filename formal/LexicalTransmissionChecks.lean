import Nabt.LexicalTransmission

/-! Synthetic adversarial controls. These are not source-history judgments. -/
open Nabt.LexicalTransmission
namespace LexicalTransmissionChecks

def claim : Claim := ⟨"index", "reading", "context"⟩
def report (work : String) : Report :=
  ⟨claim, work, ⟨work, "revision", "digest", 0, 1, "x"⟩⟩
def review (relation : Relation) : PairReview :=
  ⟨claim, "A", "B", relation, "reviewed synthetic premise"⟩

example : classify [] claim [] = .unassessed := by decide
example : classify [] claim [report "A"] = .identifiedSingleSource := by decide
example : classify [] claim [report "A", report "A"] = .identifiedSingleSource := by decide
example : classify [] claim [report "A", report "B"] = .multipleUnresolved := by decide
example : classify [review .dependent] claim [report "A", report "B"] = .multipleDependent := by decide
example : classify [review .independent] claim [report "A", report "B"] =
    .multipleReviewedIndependent := by decide
example : classify [review .independent] claim [report "A", report "B", report "C"] =
    .multipleUnresolved := by decide
example : classify [review .dependent, review .independent] claim [report "A", report "B"] =
    .inconsistentReviews := by decide
example : classify [{review .independent with evidence := ""}] claim [report "A", report "B"] =
    .multipleUnresolved := by decide
example : classify [{review .independent with claim := {claim with context := "other"}}]
    claim [report "A", report "B"] = .multipleUnresolved := by decide
example : classify [review .independent] claim
    [report "A", {report "B" with claim := {claim with reading := "other"}}] =
    .unassessed := by decide
example : classify [] claim [{report "A" with source := "B"}] = .unassessed := by decide
example : classify [] claim [{report "A" with citation :=
    {(report "A").citation with quotation := ""}}] = .unassessed := by decide
example : (installedReports "قلم" "قول محكي").length = 3 := by decide
example : (installedReports "فهم" "مقام جديد").map (fun r => r.claim.reading) =
    ["lisan:fahm-knowledge", "lisan:fahm-tribe", "maqayis:fahm-knowledge"] := by decide

end LexicalTransmissionChecks
