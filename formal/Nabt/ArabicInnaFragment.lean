import Nabt.ArabicCoverage

/-!
# Executable, complete case assignment for one declared Arabic fragment

The reference rule is the operative, fully written `إِنَّ` followed by an
overt proper name and a single adjectival predicate. Both lexical readings
must be supplied as singular and triptote, with an explicit written ending. The rule
assigns accusative to the name and nominative to the predicate.

Source of that case rule: the pinned Qatr al-Nada text, physical lines 187–190,
OpenITI/0775AH@61b0c7891699554aeff8dffdb8b1a2a59d2d22ab,
data/0761JamalDinIbnHisham/0761JamalDinIbnHisham.MatnQatrNada/
0761JamalDinIbnHisham.MatnQatrNada.Shamela0011376-ara1.
The full source SHA256 is
2d9241beca1b138187ace8f6782d5eed68f3864f402ec1d5fc90fdeb306ceb9d.

This is completeness of **case analyses in the declared fragment**, not of
all Arabic readings of the same string. Lexical categories, number,
declension, case annotation and witness identities are explicit interpreted
premises. Their acquisition, authenticity, exhaustiveness and applicability
to ordinary language are not proved here. In particular, this module makes
no claim about gender agreement, lexical sense, referent identity, speech
intent or the truth of a statement about the world.

The executable enumerates every pair in the supplied lexical ledger and
compares the complete rendered byte list. There is no unproved tokenization
or lossy normalization premise in `recognize_iff_reference`. Exact spelling,
one ASCII space at each boundary and no final punctuation are part of this
version's input profile. A surface outside the ledger is outside its domain;
an empty result is not a judgment of Arabic ungrammaticality.

Unknown lexical fields retain possible pairs in `pending`. A complete result
cannot be reported while one of those possible pairs is pending. This does
not certify that an external ledger has listed every real lexical reading.
-/

namespace Nabt.ArabicInnaFragment

def lawId : String := "nabt.arabic-inna-case-fragment.v1"

abbrev Bytes := List UInt8

inductive Category where
  | properName | adjective | other | unknown
  deriving DecidableEq, Repr

inductive Number where
  | singular | other | unknown
  deriving DecidableEq, Repr

inductive Declension where
  | triptote | other | unknown
  deriving DecidableEq, Repr

inductive Case where
  | nasb | raf | jarr | unknown
  deriving DecidableEq, Repr

/-- `witness` identifies a declared lexical premise. It is not an acquired
source certificate or an assertion of independence from the target. -/
structure LexicalReading where
  id : String
  witness : String
  surface : Bytes
  category : Category
  number : Number
  declension : Declension
  observedCase : Case
  deriving DecidableEq, Repr

structure Analysis where
  subject : LexicalReading
  predicate : LexicalReading
  deriving DecidableEq, Repr

def innaPrefix : Bytes := "إِنَّ ".toUTF8.toList
def wordSeparator : Bytes := [32]

def nasbEndingBeforeAlif : Bytes := "ًا".toUTF8.toList
def nasbEndingAfterAlif : Bytes := "اً".toUTF8.toList
def rafEnding : Bytes := "ٌ".toUTF8.toList
def jarrEnding : Bytes := "ٍ".toUTF8.toList

/-- This version covers the regular written accusative alif with either
explicit Unicode order, and nominative/genitive tanwin. Other endings remain
outside this written-ending profile. No ending is normalized or rewritten. -/
def WrittenNasb (surface : Bytes) : Prop :=
  nasbEndingBeforeAlif <:+ surface ∨ nasbEndingAfterAlif <:+ surface

def WrittenRaf (surface : Bytes) : Prop := rafEnding <:+ surface
def WrittenJarr (surface : Bytes) : Prop := jarrEnding <:+ surface

instance (surface : Bytes) : Decidable (WrittenNasb surface) := by
  unfold WrittenNasb
  infer_instance

instance (surface : Bytes) : Decidable (WrittenRaf surface) := by
  unfold WrittenRaf
  infer_instance

instance (surface : Bytes) : Decidable (WrittenJarr surface) := by
  unfold WrittenJarr
  infer_instance

def writtenNasb (surface : Bytes) : Bool :=
  nasbEndingBeforeAlif.isSuffixOf surface || nasbEndingAfterAlif.isSuffixOf surface

def writtenRaf (surface : Bytes) : Bool := rafEnding.isSuffixOf surface
def writtenJarr (surface : Bytes) : Bool := jarrEnding.isSuffixOf surface

theorem written_nasb_iff (surface : Bytes) :
    writtenNasb surface = true ↔ WrittenNasb surface := by
  simp [writtenNasb, WrittenNasb]

theorem written_raf_iff (surface : Bytes) :
    writtenRaf surface = true ↔ WrittenRaf surface := by
  simp [writtenRaf, WrittenRaf]

theorem written_jarr_iff (surface : Bytes) :
    writtenJarr surface = true ↔ WrittenJarr surface := by
  simp [writtenJarr, WrittenJarr]

/-- A supplied case tag may confirm or leave open the written observation;
it cannot replace the separate WrittenNasb/WrittenRaf premise. -/
def CaseTagAllows (r : LexicalReading) (expected : Case) : Prop :=
  r.observedCase = expected ∨ r.observedCase = .unknown

instance (r : LexicalReading) (expected : Case) : Decidable (CaseTagAllows r expected) := by
  unfold CaseTagAllows
  infer_instance

/-- Rendering is the complete source of the fragment, not a subsequence. -/
def render (a : Analysis) : Bytes :=
  innaPrefix ++ a.subject.surface ++ wordSeparator ++ a.predicate.surface

/-- The transport separately checks valid UTF-8. This definition only fixes
the literal byte profile used by this source-level theorem. -/
def SurfaceWithin (surface : Bytes) : Prop :=
  surface ≠ [] ∧ ∀ byte ∈ surface,
    byte ≠ 9 ∧ byte ≠ 10 ∧ byte ≠ 13 ∧ byte ≠ 32 ∧ byte ≠ 46 ∧ byte ≠ 59

instance (surface : Bytes) : Decidable (SurfaceWithin surface) := by
  unfold SurfaceWithin
  infer_instance

/-! The reference is a rule relation. It is not defined by parser output. -/

inductive NameCase : LexicalReading → Prop where
  | ofReading (r : LexicalReading)
      (category : r.category = .properName)
      (number : r.number = .singular)
      (declension : r.declension = .triptote)
      (annotation : CaseTagAllows r .nasb)
      (surface : SurfaceWithin r.surface)
      (written : WrittenNasb r.surface) : NameCase r

inductive PredicateCase : LexicalReading → Prop where
  | ofReading (r : LexicalReading)
      (category : r.category = .adjective)
      (number : r.number = .singular)
      (declension : r.declension = .triptote)
      (annotation : CaseTagAllows r .raf)
      (surface : SurfaceWithin r.surface)
      (written : WrittenRaf r.surface) : PredicateCase r

inductive Reference (ledger : List LexicalReading) : Bytes → Analysis → Prop where
  | inna (a : Analysis)
      (subjectMember : a.subject ∈ ledger)
      (predicateMember : a.predicate ∈ ledger)
      (subjectRule : NameCase a.subject)
      (predicateRule : PredicateCase a.predicate) :
      Reference ledger (render a) a

/-! The implementation uses a finite product and Boolean tests. -/

def nameAllowed (r : LexicalReading) : Bool :=
  decide (r.category = .properName ∧ r.number = .singular ∧
    r.declension = .triptote ∧ CaseTagAllows r .nasb ∧ SurfaceWithin r.surface) &&
      writtenNasb r.surface

def predicateAllowed (r : LexicalReading) : Bool :=
  decide (r.category = .adjective ∧ r.number = .singular ∧
    r.declension = .triptote ∧ CaseTagAllows r .raf ∧ SurfaceWithin r.surface) &&
      writtenRaf r.surface

def candidates (ledger : List LexicalReading) : List Analysis :=
  ledger.flatMap fun subject => ledger.map fun predicate => ⟨subject, predicate⟩

def recognizes (source : Bytes) (a : Analysis) : Bool :=
  decide (source = render a) && nameAllowed a.subject && predicateAllowed a.predicate

def recognize (ledger : List LexicalReading) (source : Bytes) : List Analysis :=
  (candidates ledger).filter (recognizes source)

theorem name_allowed_iff (r : LexicalReading) :
    nameAllowed r = true ↔ NameCase r := by
  constructor
  · intro allowed
    have h := Bool.and_eq_true_iff.mp allowed
    have fields := of_decide_eq_true h.1
    exact .ofReading r fields.1 fields.2.1 fields.2.2.1 fields.2.2.2.1
      fields.2.2.2.2 ((written_nasb_iff r.surface).mp h.2)
  · intro reference
    cases reference with
    | ofReading category number declension annotation surface written =>
      simp [nameAllowed, category, number, declension, annotation, surface,
        (written_nasb_iff r.surface).mpr written]

theorem predicate_allowed_iff (r : LexicalReading) :
    predicateAllowed r = true ↔ PredicateCase r := by
  constructor
  · intro allowed
    have h := Bool.and_eq_true_iff.mp allowed
    have fields := of_decide_eq_true h.1
    exact .ofReading r fields.1 fields.2.1 fields.2.2.1 fields.2.2.2.1
      fields.2.2.2.2 ((written_raf_iff r.surface).mp h.2)
  · intro reference
    cases reference with
    | ofReading category number declension annotation surface written =>
      simp [predicateAllowed, category, number, declension, annotation, surface,
        (written_raf_iff r.surface).mpr written]

theorem candidate_membership (ledger : List LexicalReading) (a : Analysis) :
    a ∈ candidates ledger ↔ a.subject ∈ ledger ∧ a.predicate ∈ ledger := by
  cases a
  simp [candidates]

theorem reference_iff (ledger : List LexicalReading) (source : Bytes) (a : Analysis) :
    Reference ledger source a ↔
      a.subject ∈ ledger ∧ a.predicate ∈ ledger ∧ source = render a ∧
        NameCase a.subject ∧ PredicateCase a.predicate := by
  constructor
  · intro licensed
    cases licensed with
    | inna _ subjectMember predicateMember subjectRule predicateRule =>
      exact ⟨subjectMember, predicateMember, rfl, subjectRule, predicateRule⟩
  · rintro ⟨subjectMember, predicateMember, same, subjectRule, predicateRule⟩
    rw [same]
    exact .inna a subjectMember predicateMember subjectRule predicateRule

/-- Soundness and completeness of the executable recognizer on every byte
input and every supplied ledger, not agreement on a list of test sentences. -/
theorem recognize_iff_reference (ledger : List LexicalReading) (source : Bytes)
    (a : Analysis) : a ∈ recognize ledger source ↔ Reference ledger source a := by
  simp only [recognize, List.mem_filter, candidate_membership, recognizes,
    Bool.and_eq_true, decide_eq_true_eq, name_allowed_iff, predicate_allowed_iff,
    reference_iff]
  simp only [and_assoc]

theorem recognize_sound (ledger : List LexicalReading) (source : Bytes)
    (a : Analysis) (recognized : a ∈ recognize ledger source) :
    Reference ledger source a :=
  (recognize_iff_reference ledger source a).mp recognized

theorem recognize_complete (ledger : List LexicalReading) (source : Bytes)
    (a : Analysis) (licensed : Reference ledger source a) :
    a ∈ recognize ledger source :=
  (recognize_iff_reference ledger source a).mpr licensed

/-- A concrete instance of the previously abstract exactness contract. -/
theorem exact_executable_recognizer (ledger : List LexicalReading) :
    ArabicCoverage.ExactWithin (fun _ : Bytes => True) (Reference ledger)
      (fun source a => a ∈ recognize ledger source) := by
  intro source _ a
  exact recognize_iff_reference ledger source a

theorem recognized_restores_whole_source (ledger : List LexicalReading) (source : Bytes)
    (a : Analysis) (recognized : a ∈ recognize ledger source) : source = render a :=
  ((reference_iff ledger source a).mp (recognize_sound ledger source a recognized)).2.2.1

theorem recognized_written_case_pair (ledger : List LexicalReading) (source : Bytes)
    (a : Analysis) (recognized : a ∈ recognize ledger source) :
    WrittenNasb a.subject.surface ∧ WrittenRaf a.predicate.surface := by
  have ref := (reference_iff ledger source a).mp (recognize_sound ledger source a recognized)
  cases ref.2.2.2.1 with
  | ofReading _ _ _ _ _ subjectCase =>
    cases ref.2.2.2.2 with
    | ofReading _ _ _ _ _ predicateCase => exact ⟨subjectCase, predicateCase⟩

/-- An accusative label cannot create a name reading without the independently
checked written accusative ending. This includes forged lexical case tags. -/
theorem missing_written_nasb_blocks_reading (ledger : List LexicalReading) (source : Bytes)
    (a : Analysis) (missing : ¬ WrittenNasb a.subject.surface) :
    a ∉ recognize ledger source := by
  intro recognized
  exact missing (recognized_written_case_pair ledger source a recognized).1

theorem missing_written_raf_blocks_reading (ledger : List LexicalReading) (source : Bytes)
    (a : Analysis) (missing : ¬ WrittenRaf a.predicate.surface) :
    a ∉ recognize ledger source := by
  intro recognized
  exact missing (recognized_written_case_pair ledger source a recognized).2

theorem preserves_every_licensed_alternative (ledger : List LexicalReading) (source : Bytes)
    (first second : Analysis) (left : Reference ledger source first)
    (right : Reference ledger source second) :
    first ∈ recognize ledger source ∧ second ∈ recognize ledger source :=
  ⟨recognize_complete ledger source first left, recognize_complete ledger source second right⟩

theorem no_reading_iff_no_reference (ledger : List LexicalReading) (source : Bytes) :
    recognize ledger source = [] ↔ ∀ a, ¬ Reference ledger source a := by
  simp only [List.eq_nil_iff_forall_not_mem, recognize_iff_reference]

/-! Unresolved premises are retained separately from established case rules. -/

def namePossible (r : LexicalReading) : Bool :=
  decide ((r.category = .properName ∨ r.category = .unknown) ∧
    (r.number = .singular ∨ r.number = .unknown) ∧
    (r.declension = .triptote ∨ r.declension = .unknown) ∧
    CaseTagAllows r .nasb ∧ SurfaceWithin r.surface ∧
    (WrittenNasb r.surface ∨
      ¬ (WrittenNasb r.surface ∨ WrittenRaf r.surface ∨ WrittenJarr r.surface)))

def predicatePossible (r : LexicalReading) : Bool :=
  decide ((r.category = .adjective ∨ r.category = .unknown) ∧
    (r.number = .singular ∨ r.number = .unknown) ∧
    (r.declension = .triptote ∨ r.declension = .unknown) ∧
    CaseTagAllows r .raf ∧ SurfaceWithin r.surface ∧
    (WrittenRaf r.surface ∨
      ¬ (WrittenNasb r.surface ∨ WrittenRaf r.surface ∨ WrittenJarr r.surface)))

def isPending (source : Bytes) (a : Analysis) : Bool :=
  decide (source = render a) && namePossible a.subject && predicatePossible a.predicate &&
    !(nameAllowed a.subject && predicateAllowed a.predicate)

def pending (ledger : List LexicalReading) (source : Bytes) : List Analysis :=
  (candidates ledger).filter (isPending source)

theorem pending_membership (ledger : List LexicalReading) (source : Bytes) (a : Analysis) :
    a ∈ pending ledger source ↔
      a.subject ∈ ledger ∧ a.predicate ∈ ledger ∧ source = render a ∧
      namePossible a.subject = true ∧ predicatePossible a.predicate = true ∧
      ¬ (NameCase a.subject ∧ PredicateCase a.predicate) := by
  have notAllowed : (!(nameAllowed a.subject && predicateAllowed a.predicate)) = true ↔
      ¬ (NameCase a.subject ∧ PredicateCase a.predicate) := by
    rw [← name_allowed_iff, ← predicate_allowed_iff]
    cases nameAllowed a.subject <;> cases predicateAllowed a.predicate <;> decide
  simp only [pending, List.mem_filter, candidate_membership, isPending,
    Bool.and_eq_true, decide_eq_true_eq, notAllowed, and_assoc]

inductive Status where
  | completeWithinFragment | deferLexicalPremises | noReadingInFragment
  deriving DecidableEq, Repr

def status (ledger : List LexicalReading) (source : Bytes) : Status :=
  if (pending ledger source).isEmpty = false then .deferLexicalPremises
  else if (recognize ledger source).isEmpty = false then .completeWithinFragment
  else .noReadingInFragment

theorem pending_blocks_completion (ledger : List LexicalReading) (source : Bytes)
    (a : Analysis) (unresolved : a ∈ pending ledger source) :
    status ledger source = .deferLexicalPremises := by
  have nonempty : (pending ledger source).isEmpty = false := by
    apply List.isEmpty_eq_false_iff.mpr
    intro empty
    simp [empty] at unresolved
  simp [status, nonempty]

theorem completion_has_no_pending (ledger : List LexicalReading) (source : Bytes)
    (complete : status ledger source = .completeWithinFragment) :
    pending ledger source = [] := by
  unfold status at complete
  split at complete
  · contradiction
  · rename_i absent
    simpa using absent

theorem completion_has_reading (ledger : List LexicalReading) (source : Bytes)
    (complete : status ledger source = .completeWithinFragment) :
    recognize ledger source ≠ [] := by
  unfold status at complete
  split at complete
  · contradiction
  · split at complete
    · rename_i found
      exact List.isEmpty_eq_false_iff.mp found
    · contradiction

end Nabt.ArabicInnaFragment
