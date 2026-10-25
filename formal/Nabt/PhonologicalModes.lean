import Std

/-!
Conditional symbolic boundary laws. Source acquisition, vowel interpretation,
Unicode parsing, and acoustic adequacy are outside these theorems. Start and end
are independent: a word may begin an utterance and be paused on simultaneously.
No token here is a claim of attestation or a measurement of a human voice.
-/
namespace Nabt.PhonologicalModes

def lawId := "nabt.phonological-modes.v1"

inductive Vowel where
  | a | i | u
  deriving DecidableEq, Repr

inductive Segment where
  | consonant (label : String)
  | short (vowel : Vowel)
  | long (vowel : Vowel)
  deriving DecidableEq, Repr

inductive Start where
  | ibtida | wasl
  deriving DecidableEq, Repr

inductive End where
  | wasl | waqf
  deriving DecidableEq, Repr

inductive Profile where
  | standardCore | sibawayhiOptions
  deriving DecidableEq, Repr

inductive Ending where
  | stable
  | short (vowel : Vowel)
  | tanwin (vowel : Vowel)
  | feminine (vowel : Vowel)
  | weak (vowel : Vowel)
  | single (vowel : Vowel)
  deriving DecidableEq, Repr

structure Form where
  sourceBytes : List UInt8
  written : String
  body : List Segment
  waslVowel : Option Vowel
  ending : Ending
  deletedRadicals : List String
  deriving DecidableEq, Repr

structure Projection where
  sourceBytes : List UInt8
  written : String
  surface : List Segment
  deletedRadicals : List String
  deriving DecidableEq, Repr

def onset : Start → Option Vowel → List Segment
  | .ibtida, some v => [.consonant "ʔ", .short v]
  | _, _ => []

def suffixes : End → Profile → Ending → List (List Segment)
  | _, _, .stable => [[]]
  | .wasl, _, .tanwin v => [[.short v, .consonant "n"]]
  | .wasl, _, .feminine v => [[.consonant "t", .short v]]
  | .wasl, _, .short v => [[.short v]]
  | .wasl, _, .weak v => [[.short v]]
  | .wasl, _, .single v => [[.short v]]
  | .waqf, _, .tanwin .a => [[.long .a]]
  | .waqf, _, .tanwin _ => [[]]
  | .waqf, _, .feminine _ => [[.consonant "h"]]
  | .waqf, _, .single v => [[.short v, .consonant "h"]]
  | .waqf, .sibawayhiOptions, .weak v => [[], [.short v, .consonant "h"]]
  | .waqf, _, _ => [[]]

def withSource (f : Form) (surface : List Segment) : Projection :=
  ⟨f.sourceBytes, f.written, surface, f.deletedRadicals⟩

def realize (f : Form) (start : Start) (ending : End) (profile : Profile) : List Projection :=
  (suffixes ending profile f.ending).map fun suffix =>
    withSource f (onset start f.waslVowel ++ f.body ++ suffix)

/-- Applicable only after a separate source-bound contact license. -/
def contactKasra (f : Form) : Projection :=
  withSource f (f.body ++ [.short .i])

theorem wasl_onset_empty (v : Option Vowel) : onset .wasl v = [] := by
  cases v <;> rfl

theorem ibtida_wasl_onset (v : Vowel) :
    onset .ibtida (some v) = [.consonant "ʔ", .short v] := rfl

theorem no_inserted_hamza_without_wasl (s : Start) : onset s none = [] := by
  cases s <;> rfl

theorem source_preserved (f : Form) (s : Start) (e : End) (p : Profile)
    (r : Projection) (h : r ∈ realize f s e p) : r.sourceBytes = f.sourceBytes := by
  obtain ⟨x, _, rfl⟩ := List.mem_map.mp h
  rfl

theorem writing_preserved (f : Form) (s : Start) (e : End) (p : Profile)
    (r : Projection) (h : r ∈ realize f s e p) : r.written = f.written := by
  obtain ⟨x, _, rfl⟩ := List.mem_map.mp h
  rfl

theorem deletion_record_preserved (f : Form) (s : Start) (e : End) (p : Profile)
    (r : Projection) (h : r ∈ realize f s e p) : r.deletedRadicals = f.deletedRadicals := by
  obtain ⟨x, _, rfl⟩ := List.mem_map.mp h
  rfl

theorem contact_retains_body (f : Form) :
    (contactKasra f).surface.take f.body.length = f.body := by
  simp [contactKasra, withSource]

theorem contact_adds_only_one_short_vowel (f : Form) :
    (contactKasra f).surface = f.body ++ [.short .i] := rfl

theorem contact_length (f : Form) : (contactKasra f).surface.length = f.body.length + 1 := by
  simp [contactKasra, withSource]

theorem contact_does_not_restore_deleted_record (f : Form) :
    (contactKasra f).deletedRadicals = f.deletedRadicals := rfl

theorem contact_writing_preserved (f : Form) : (contactKasra f).written = f.written := rfl

theorem weak_pause_keeps_both_options (v : Vowel) :
    suffixes .waqf .sibawayhiOptions (.weak v) = [[], [.short v, .consonant "h"]] := rfl

theorem single_pause_requires_support (v : Vowel) (p : Profile) :
    suffixes .waqf p (.single v) = [[.short v, .consonant "h"]] := by
  cases p <;> rfl

theorem feminine_pause_is_h (v : Vowel) (p : Profile) :
    suffixes .waqf p (.feminine v) = [[.consonant "h"]] := by
  cases p <;> rfl

theorem accusative_tanwin_pause_is_long_a (p : Profile) :
    suffixes .waqf p (.tanwin .a) = [[.long .a]] := by
  cases p <;> rfl

theorem pause_alone_cannot_recover_short_case (p : Profile) :
    suffixes .waqf p (.short .a) = suffixes .waqf p (.short .i) := by
  cases p <;> rfl

theorem suffixes_nonempty (e : End) (p : Profile) (k : Ending) :
    suffixes e p k ≠ [] := by
  cases e <;> cases p <;> cases k with
  | stable => decide
  | short v => cases v <;> decide
  | tanwin v => cases v <;> decide
  | feminine v => cases v <;> decide
  | weak v => cases v <;> decide
  | single v => cases v <;> decide

end Nabt.PhonologicalModes
