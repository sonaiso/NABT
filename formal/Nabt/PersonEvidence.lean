import Nabt.NominalEvidence

/-!
Correlated person features under an independently established verbal family.
The table is a new, bounded Unicode projection. It does not identify an
imperfect from its first letter, validate QAC annotations, infer a lexical
root, settle a referent, or assign a syntactic role or case.

The five families must be licensed from complete morphological evidence.
In particular, feminine-singular addressing is its own five-verb family;
plain ta preserves 2MS/3FS and dual ta preserves three correlated profiles.
Attached forms are declared allomorphs, not a suffix segmentation algorithm.
-/

namespace Nabt.PersonEvidence

def lawId : String := "nabt.person-evidence.v1"

structure Profile where
  qac : String
  person : Nat
  gender : Nat
  number : Nat
  deriving DecidableEq, Repr, BEq

def profiles : List Profile := [
  ⟨"1S", 1, 2, 0⟩, ⟨"1P", 1, 2, 2⟩,
  ⟨"2MS", 2, 0, 0⟩, ⟨"2MD", 2, 0, 1⟩, ⟨"2MP", 2, 0, 2⟩,
  ⟨"2FS", 2, 1, 0⟩, ⟨"2FD", 2, 1, 1⟩, ⟨"2FP", 2, 1, 2⟩,
  ⟨"3MS", 3, 0, 0⟩, ⟨"3MD", 3, 0, 1⟩, ⟨"3MP", 3, 0, 2⟩,
  ⟨"3FS", 3, 1, 0⟩, ⟨"3FD", 3, 1, 1⟩, ⟨"3FP", 3, 1, 2⟩]

inductive Family where
  | plain | dual | masculinePlural | feminineSingular | femininePlural
  deriving DecidableEq, Repr, BEq

def families : List Family := [.plain, .dual, .masculinePlural,
  .feminineSingular, .femininePlural]

def Family.label : Family → String
  | .plain => "plain"
  | .dual => "dual"
  | .masculinePlural => "masculine_plural"
  | .feminineSingular => "feminine_singular"
  | .femininePlural => "feminine_plural"

def Family.codes : Family → List String
  | .plain => ["1S", "1P", "2MS", "3MS", "3FS"]
  | .dual => ["2MD", "2FD", "3MD", "3FD"]
  | .masculinePlural => ["2MP", "3MP"]
  | .feminineSingular => ["2FS"]
  | .femininePlural => ["2FP", "3FP"]

def Family.fiveVerb : Family → Bool
  | .dual | .masculinePlural | .feminineSingular => true
  | _ => false

def prefixes : List String := ["أ", "ن", "ي", "ت"]

def prefixCodes (pre : String) : List String :=
  if pre == "أ" then ["1S"]
  else if pre == "ن" then ["1P"]
  else if pre == "ي" then ["3MS", "3MD", "3MP", "3FP"]
  else if pre == "ت" then ["2MS", "2MD", "2MP", "2FS", "2FD", "2FP", "3FS", "3FD"]
  else []

def candidates (family : Family) (pre : String) : List Profile :=
  profiles.filter fun p => family.codes.contains p.qac && (prefixCodes pre).contains p.qac

def qualifiedCandidates (qualified : Bool) (family : Family) (pre : String) : List Profile :=
  if qualified then candidates family pre else []

def refine (ps : List Profile) (evidence : List (Profile → Bool)) : List Profile :=
  ps.filter fun p => evidence.all (fun test => test p)

theorem profile_count : profiles.length = 14 := by decide
theorem profile_codes_unique : (profiles.map Profile.qac).Nodup := by decide
theorem profile_domains : profiles.all (fun p =>
    1 ≤ p.person && p.person ≤ 3 && p.gender ≤ 2 && p.number ≤ 2) = true := by decide

theorem candidate_membership (p : Profile) (family : Family) (pre : String) :
    p ∈ candidates family pre ↔ p ∈ profiles ∧
      (family.codes.contains p.qac && (prefixCodes pre).contains p.qac) = true := by
  simp [candidates]

theorem candidates_from_inventory (p : Profile) (family : Family) (pre : String)
    (h : p ∈ candidates family pre) : p ∈ profiles :=
  (candidate_membership p family pre).mp h |>.1

theorem unqualified_prefix_no_person (family : Family) (pre : String) :
    qualifiedCandidates false family pre = [] := by rfl

theorem qualified_agrees (family : Family) (pre : String) :
    qualifiedCandidates true family pre = candidates family pre := by rfl

theorem plain_ta_ambiguous : (candidates .plain "ت").map Profile.qac = ["2MS", "3FS"] := by decide
theorem dual_ta_correlated : (candidates .dual "ت").map Profile.qac = ["2MD", "2FD", "3FD"] := by decide
theorem dual_ya_correlated : (candidates .dual "ي").map Profile.qac = ["3MD"] := by decide
theorem bare_alif_not_hamza : candidates .plain "ا" = [] := by decide
theorem no_first_person_five_verbs : families.all (fun family =>
    !family.fiveVerb || ((candidates family "أ").isEmpty && (candidates family "ن").isEmpty)) = true := by decide
theorem all_profiles_covered : (families.flatMap fun family =>
    prefixes.flatMap fun pre => candidates family pre).length = 14 := by decide

theorem refine_membership (p : Profile) (ps : List Profile) (es : List (Profile → Bool)) :
    p ∈ refine ps es ↔ p ∈ ps ∧ es.all (fun test => test p) = true := by
  simp [refine]

theorem empty_evidence_identity (ps : List Profile) : refine ps [] = ps := by
  simp [refine]

theorem deletion_widens (p : Profile) (ps : List Profile) (less more : List (Profile → Bool))
    (subset : ∀ test ∈ less, test ∈ more) (h : p ∈ refine ps more) : p ∈ refine ps less := by
  rw [refine_membership] at h ⊢
  exact ⟨h.1, List.all_eq_true.mpr fun test ht => (List.all_eq_true.mp h.2) test (subset test ht)⟩

theorem contradictory_evidence_empty (ps : List Profile) (test : Profile → Bool) :
    refine ps [test, fun p => !(test p)] = [] := by
  simp [refine]

/-- Numeric identities stand for checked source/scope/occurrence/reading IDs.
Equality cannot establish that an external parser supplied the right witness. -/
structure Identity where
  source : Nat
  scope : Nat
  occurrence : Nat
  reading : Nat
  deriving DecidableEq, Repr, BEq

structure Receipt where
  identity : Identity
  active : Bool
  blocked : Bool
  supports : List Nat

def accepts (target : Identity) (r : Receipt) : Bool :=
  decide (r.identity = target) && r.active && !r.blocked && !r.supports.isEmpty

theorem accepted_identity (target : Identity) (r : Receipt) (h : accepts target r = true) :
    r.identity = target := by
  simp [accepts] at h
  exact h.1.1.1

theorem foreign_identity_rejected (target : Identity) (r : Receipt) (h : r.identity ≠ target) :
    accepts target r = false := by simp [accepts, h]

theorem unsupported_receipt_rejected (target : Identity) (r : Receipt) (h : r.supports = []) :
    accepts target r = false := by simp [accepts, h]

theorem blocked_receipt_rejected (target : Identity) (r : Receipt) (h : r.blocked = true) :
    accepts target r = false := by simp [accepts, h]

structure AttachedForm where
  surface : String
  qac : String
  host : String
  deriving DecidableEq, Repr

/-- New declared Unicode allomorph inventory. `host` limits the 1S form;
other rows still need independent source segmentation and host licensing. -/
def attachedForms : List AttachedForm := [
  ⟨"ي", "1S", "noun"⟩, ⟨"نِي", "1S", "verb"⟩, ⟨"نَا", "1P", "either"⟩,
  ⟨"كَ", "2MS", "either"⟩, ⟨"كِ", "2FS", "either"⟩,
  ⟨"كُمَا", "2MD", "either"⟩, ⟨"كُمَا", "2FD", "either"⟩,
  ⟨"كُمْ", "2MP", "either"⟩, ⟨"كُنَّ", "2FP", "either"⟩,
  ⟨"هُ", "3MS", "either"⟩, ⟨"هِ", "3MS", "either"⟩, ⟨"هَا", "3FS", "either"⟩,
  ⟨"هُمَا", "3MD", "either"⟩, ⟨"هُمَا", "3FD", "either"⟩,
  ⟨"هِمَا", "3MD", "either"⟩, ⟨"هِمَا", "3FD", "either"⟩,
  ⟨"هُمْ", "3MP", "either"⟩, ⟨"هِمْ", "3MP", "either"⟩,
  ⟨"هُنَّ", "3FP", "either"⟩, ⟨"هِنَّ", "3FP", "either"⟩]

theorem attached_count : attachedForms.length = 20 := by decide
theorem attached_profiles_known : attachedForms.all (fun a =>
    (profiles.map Profile.qac).contains a.qac) = true := by decide
theorem kaf_gender_ambiguity : (attachedForms.filter (fun a =>
    a.surface == "كَ" || a.surface == "كِ")).map AttachedForm.qac = ["2MS", "2FS"] := by decide

end Nabt.PersonEvidence
