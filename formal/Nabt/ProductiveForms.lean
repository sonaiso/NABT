import Std

/-!
Productive shapes over already acquired source premises. This proves the
transformations, inverse recovery and enumeration contract. Python's source
acquisition, Unicode parsing and linguistic interpretation remain separate
obligations; this file does not identify an attested target or a true assertion.
The initial vowel is interpreted at ibtida, not an acoustic wasl measurement.
-/
namespace Nabt.ProductiveForms

def lawId := "nabt.productive-forms.v1"

inductive Vowel where
  | a | i | u
  deriving DecidableEq, Repr

inductive Mark where
  | a | i | u | sukun
  deriving DecidableEq, Repr

def medial : Vowel → Mark
  | .a => .a | .i => .i | .u => .u

def initial : Vowel → Mark
  | .u => .u | _ => .i

structure Stem where
  first : Char
  second : Char
  third : Char
  vowel : Vowel
  deriving DecidableEq, Repr

def imperative (s : Stem) : List (Char × Mark) :=
  [('ا', initial s.vowel), (s.first, .sukun),
   (s.second, medial s.vowel), (s.third, .sukun)]

def recover : List (Char × Mark) → Option Stem
  | [('ا', .i), (a, .sukun), (b, .a), (c, .sukun)] => some ⟨a, b, c, .a⟩
  | [('ا', .i), (a, .sukun), (b, .i), (c, .sukun)] => some ⟨a, b, c, .i⟩
  | [('ا', .u), (a, .sukun), (b, .u), (c, .sukun)] => some ⟨a, b, c, .u⟩
  | _ => none

theorem recover_imperative (s : Stem) : recover (imperative s) = some s := by
  cases s with
  | mk a b c v => cases v <;> rfl

theorem imperative_injective : Function.Injective imperative := by
  intro a b h
  have eq := congrArg recover h
  simpa only [recover_imperative, Option.some.injEq] using eq

theorem radicals_preserved (s : Stem) : (imperative s).map Prod.fst =
    ['ا', s.first, s.second, s.third] := rfl

theorem imperative_four_cells (s : Stem) : (imperative s).length = 4 := rfl

theorem imperative_final_sukun (s : Stem) : (imperative s).getLast? =
    some (s.third, .sukun) := rfl

def enumerate (acquired : List Stem) : List (List (Char × Mark)) :=
  acquired.map imperative

theorem enumeration_exact (acquired : List Stem) (output : List (Char × Mark)) :
    output ∈ enumerate acquired ↔ ∃ s ∈ acquired, imperative s = output := by
  simp [enumerate]

theorem withdrawal (acquired : List Stem) (s : Stem) (absent : s ∉ acquired) :
    imperative s ∉ enumerate acquired := by
  intro h
  obtain ⟨other, member, eq⟩ := (enumeration_exact acquired _).mp h
  exact absent (imperative_injective eq ▸ member)

def accusativeAlif (base : List Char) : List Char := base ++ ['ا']

theorem accusative_base_recovered (base : List Char) :
    (accusativeAlif base).take base.length = base := by
  simp [accusativeAlif]

theorem accusative_length (base : List Char) :
    (accusativeAlif base).length = base.length + 1 := by
  simp [accusativeAlif]

structure BoundDerivation where
  sourceBytes : List UInt8
  sourceWitnesses : List Nat
  input : List Char
  output : List Char
  deriving DecidableEq, Repr

def deriveAlif (source : List UInt8) (witnesses : List Nat) (base : List Char) : BoundDerivation :=
  ⟨source, witnesses, base, accusativeAlif base⟩

theorem source_preserved (source : List UInt8) (witnesses : List Nat) (base : List Char) :
    (deriveAlif source witnesses base).sourceBytes = source := rfl

theorem witnesses_preserved (source : List UInt8) (witnesses : List Nat) (base : List Char) :
    (deriveAlif source witnesses base).sourceWitnesses = witnesses := rfl

end Nabt.ProductiveForms
