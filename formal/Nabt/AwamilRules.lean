import Nabt.ClassicalLanguageEvidence

/-! Edition-bound excerpt, Dar al-Minhaj 2009, pp. 40–41. This models
the retained transcription, not an authenticated authorial text or a full
inventory of a hundred factors. Ba has more senses outside these two lines. -/
namespace Nabt.AwamilRules
open ClassicalLanguageEvidence

def lawId := "nabt.awamil-excerpt.v1"
inductive BaSense where
  | attachment | instrument
  deriving DecidableEq, Repr
def quotedBaSenses : List BaSense := [.attachment, .instrument]
def candidates (resolved : Option BaSense) : List BaSense :=
  match resolved with
  | none => quotedBaSenses
  | some sense => [sense]

theorem partition_total : jurjaniPartition.samai + jurjaniPartition.qiyasi +
    jurjaniPartition.manawi = 100 := by decide
theorem bare_ba_retains_alternatives : candidates none = [.attachment, .instrument] := rfl
theorem selected_sense_requires_selection (s : BaSense) : candidates (some s) = [s] := rfl
theorem senses_are_distinct : BaSense.attachment ≠ .instrument := by decide

/-- A count never identifies members, sources, or independent narrators. -/
theorem equal_counts_do_not_identify_inventory :
    (["A", "B"] : List String).length = ["C", "D"].length ∧
    (["A", "B"] : List String) ≠ ["C", "D"] := by decide

end Nabt.AwamilRules
