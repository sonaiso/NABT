import Nabt.ClassicalLanguageEvidence

/-! Selected, class-qualified rules of Matn Qatr al-Nada, lines 55–96.
Attachment categories are exclusive *resolved analyses*. Unknown or competing
attachments must be retained upstream. This is not a suffix-only classifier. -/
namespace Nabt.QatrRules
open ClassicalLanguageEvidence

def lawId := "nabt.qatr-selected.v1"

inductive PastAttachment where
  | ordinary | groupWaw | movingSubjectPronoun
  deriving DecidableEq, Repr
def pastEnding : PastAttachment → Course
  | .ordinary => .fath | .groupWaw => .damm | .movingSubjectPronoun => .waqf

inductive PresentAttachment where
  | ordinary | feminineNun | directEmphasisNun
  deriving DecidableEq, Repr
def presentBuilding : PresentAttachment → Option Course
  | .ordinary => none | .feminineNun => some .waqf | .directEmphasisNun => some .fath

inductive FiveVerbCase where
  | raf | nasb | jazm
  deriving DecidableEq, Repr
inductive NunMark where
  | retained | deleted
  deriving DecidableEq, Repr
def fiveVerbNun : FiveVerbCase → NunMark
  | .raf => .retained | .nasb | .jazm => .deleted

/-- Only for an independently established diptote in genitive position. -/
def diptoteGenitive (hasAl inIdafa : Bool) : Surface :=
  if hasAl || inIdafa then .kasra else .fatha

theorem past_attachment_matters :
    pastEnding .ordinary = .fath ∧ pastEnding .groupWaw = .damm ∧
    pastEnding .movingSubjectPronoun = .waqf := by decide
theorem ordinary_present_not_built : presentBuilding .ordinary = none := rfl
theorem direct_emphasis_builds : presentBuilding .directEmphasisNun = some .fath := rfl
theorem feminine_nun_builds : presentBuilding .feminineNun = some .waqf := rfl
theorem nun_retained_iff_raf (c : FiveVerbCase) :
    fiveVerbNun c = .retained ↔ c = .raf := by cases c <;> decide
theorem deleted_nun_preserves_two_cases :
    fiveVerbNun .nasb = fiveVerbNun .jazm ∧ FiveVerbCase.nasb ≠ .jazm := by decide
theorem diptote_al_exception (idafa : Bool) : diptoteGenitive true idafa = .kasra := by
  cases idafa <;> rfl
theorem diptote_idafa_exception (al : Bool) : diptoteGenitive al true = .kasra := by
  cases al <;> rfl
theorem bare_diptote_genitive : diptoteGenitive false false = .fatha := rfl

end Nabt.QatrRules
