import Nabt.ProductiveForms

/-!
Additional sound Form-I imperative subject profiles. The lexical and classical
source premises are external obligations checked by Python. In particular,
this does not validate arbitrary root letters, attest generated words, or
resolve the gender of a dual addressee. The two dual profiles intentionally
have the same surface. Inflection nun is absent; feminine-subject nun remains.
-/
namespace Nabt.ImperativeParadigm
open Nabt.ProductiveForms

def lawId := "nabt.sound-imperative-paradigm.v1"

inductive Subject where
  | fs | md | fd | mp | fp
  deriving DecidableEq, Repr

def subjects : List Subject := [.fs, .md, .fd, .mp, .fp]

def code : Subject → String
  | .fs => "2FS" | .md => "2MD" | .fd => "2FD" | .mp => "2MP" | .fp => "2FP"

def gender : Subject → Nat
  | .md | .mp => 0 | _ => 1

def number : Subject → Nat
  | .fs => 0 | .md | .fd => 1 | _ => 2

def finalMark : Subject → Mark
  | .fs => .i | .md | .fd => .a | .mp => .u | .fp => .sukun

abbrev Cell := Char × Option Mark

def suffix : Subject → List Cell
  | .fs => [('ي', none)]
  | .md | .fd => [('ا', none)]
  | .mp => [('و', none), ('ا', none)]
  | .fp => [('ن', some .a)]

def imperative (s : Stem) (p : Subject) : List Cell :=
  [('ا', some (initial s.vowel)), (s.first, some .sukun),
   (s.second, some (medial s.vowel)), (s.third, some (finalMark p))] ++ suffix p

/-- The nun-final feminine plural needs a separate idgham and span law. -/
def qualified (s : Stem) (p : Subject) : Option (List Cell) :=
  if s.third = 'ن' ∧ p = .fp then none else some (imperative s p)

theorem nun_final_feminine_plural_deferred (s : Stem) (h : s.third = 'ن') :
    qualified s .fp = none := by simp [qualified, h]

theorem other_subject_licensed (s : Stem) (p : Subject) (h : p ≠ .fp) :
    qualified s p = some (imperative s p) := by simp [qualified, h]

theorem non_nun_final_licensed (s : Stem) (p : Subject) (h : s.third ≠ 'ن') :
    qualified s p = some (imperative s p) := by simp [qualified, h]

def recover (p : Subject) : List Cell → Option Stem
  | ('ا', some .i) :: (a, some .sukun) :: (b, some .a) :: (c, m) :: tail =>
      if m = some (finalMark p) ∧ tail = suffix p then some ⟨a, b, c, .a⟩ else none
  | ('ا', some .i) :: (a, some .sukun) :: (b, some .i) :: (c, m) :: tail =>
      if m = some (finalMark p) ∧ tail = suffix p then some ⟨a, b, c, .i⟩ else none
  | ('ا', some .u) :: (a, some .sukun) :: (b, some .u) :: (c, m) :: tail =>
      if m = some (finalMark p) ∧ tail = suffix p then some ⟨a, b, c, .u⟩ else none
  | _ => none

theorem recover_imperative (s : Stem) (p : Subject) :
    recover p (imperative s p) = some s := by
  cases s with
  | mk a b c v => cases v <;> simp [imperative, recover, initial, medial]

theorem stem_injective (p : Subject) : Function.Injective (fun s => imperative s p) := by
  intro a b h
  have eq := congrArg (recover p) h
  simpa only [recover_imperative, Option.some.injEq] using eq

theorem radical_prefix_preserved (s : Stem) (p : Subject) :
    ((imperative s p).take 4).map Prod.fst = ['ا', s.first, s.second, s.third] := by
  simp [imperative]

theorem prefix_vowel_independent_of_subject (s : Stem) (p q : Subject) :
    (imperative s p).take 3 = (imperative s q).take 3 := by
  simp [imperative]

theorem dual_surface_preserves_ambiguity (s : Stem) :
    imperative s .md = imperative s .fd := rfl

theorem dual_profiles_distinct : Subject.md ≠ Subject.fd := by decide

theorem female_plural_retains_subject_nun (s : Stem) :
    (imperative s .fp).getLast? = some ('ن', some .a) := rfl

theorem female_plural_stem_sukun : finalMark .fp = .sukun := rfl

theorem male_plural_separator (s : Stem) :
    (imperative s .mp).getLast? = some ('ا', none) := rfl

def enumerateShapes (acquired : List Stem) : List (Subject × List Cell) :=
  acquired.flatMap fun s => subjects.map fun p => (p, imperative s p)

theorem enumeration_exact (acquired : List Stem) (p : Subject) (out : List Cell) :
    (p, out) ∈ enumerateShapes acquired ↔ ∃ s ∈ acquired, imperative s p = out := by
  simp [enumerateShapes, subjects]
  cases p <;> simp [eq_comm]

theorem withdrawal (acquired : List Stem) (s : Stem) (p : Subject)
    (absent : s ∉ acquired) : (p, imperative s p) ∉ enumerateShapes acquired := by
  intro h
  obtain ⟨other, member, eq⟩ := (enumeration_exact acquired p _).mp h
  exact absent (stem_injective p eq ▸ member)

structure BoundForm where
  sourceBytes : List UInt8
  sourceWitnesses : List Nat
  profile : Subject
  form : List Cell
  deriving DecidableEq, Repr

def derive (raw : List UInt8) (witnesses : List Nat) (s : Stem) (p : Subject) : BoundForm :=
  ⟨raw, witnesses, p, imperative s p⟩

theorem source_preserved (raw : List UInt8) (w : List Nat) (s : Stem) (p : Subject) :
    (derive raw w s p).sourceBytes = raw := rfl

theorem witnesses_preserved (raw : List UInt8) (w : List Nat) (s : Stem) (p : Subject) :
    (derive raw w s p).sourceWitnesses = w := rfl

end Nabt.ImperativeParadigm
