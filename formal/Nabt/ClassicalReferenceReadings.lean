import Std

/-!
Conditional reading relations, not a parser or a certificate of source acquisition.
`freeIshtighal` presupposes a free introductory context without a construction that
forces one case. `matchedDescription` presupposes the licensed description and
overt noun agree in number. `interpretiveAn` presupposes the source's conditions
for explanatory أن, in the analysis that admits it. Observed endings are evidence
filters. None of these premises is established by accepting a caller's label.
-/
namespace Nabt.ClassicalReferenceReadings

def lawId := "nabt.classical-conditional-readings.v1"

inductive Ending where
  | nominative | accusative | genitive | jussive
  deriving DecidableEq, Repr

inductive Number where
  | singular | dual | plural
  deriving DecidableEq, Repr

inductive Frame where
  | freeIshtighal (observed : Option Ending)
  | matchedDescription (number : Number) (observed : Option Ending)
  | interpretiveAn (hasLa : Bool) (observed : Option Ending)
  deriving DecidableEq, Repr

inductive Reading where
  | topic | omittedVerb | descriptionSubject | frontedPredicate
  | anInterpretiveIndicative | anInterpretiveJussive | anMasdariyyaSubjunctive
  deriving DecidableEq, Repr

def observed : Frame → Option Ending
  | .freeIshtighal e | .matchedDescription _ e | .interpretiveAn _ e => e

def ending : Reading → Ending
  | .omittedVerb | .anMasdariyyaSubjunctive => .accusative
  | .anInterpretiveJussive => .jussive
  | _ => .nominative

-- A declarative relation, defined independently of the executable candidate list.
def Admissible : Frame → Reading → Prop
  | .freeIshtighal _, .topic => True
  | .freeIshtighal _, .omittedVerb => True
  | .matchedDescription n _, .descriptionSubject => n = .singular
  | .matchedDescription _ _, .frontedPredicate => True
  | .interpretiveAn _ _, .anInterpretiveIndicative => True
  | .interpretiveAn hasLa _, .anInterpretiveJussive => hasLa = true
  | .interpretiveAn _ _, .anMasdariyyaSubjunctive => True
  | _, _ => False

def EndingMatches (e : Option Ending) (r : Reading) : Prop :=
  match e with
  | none => True
  | some value => value = ending r

def Licensed (f : Frame) (r : Reading) : Prop :=
  Admissible f r ∧ EndingMatches (observed f) r

def candidates : Frame → List Reading
  | .freeIshtighal _ => [.topic, .omittedVerb]
  | .matchedDescription .singular _ => [.descriptionSubject, .frontedPredicate]
  | .matchedDescription _ _ => [.frontedPredicate]
  | .interpretiveAn true _ =>
      [.anInterpretiveIndicative, .anInterpretiveJussive, .anMasdariyyaSubjunctive]
  | .interpretiveAn false _ => [.anInterpretiveIndicative, .anMasdariyyaSubjunctive]

def endingOK (e : Option Ending) (r : Reading) : Bool :=
  match e with
  | none => true
  | some value => value == ending r

def enumerate (f : Frame) : List Reading :=
  (candidates f).filter (endingOK (observed f))

theorem candidates_exact (f : Frame) (r : Reading) :
    r ∈ candidates f ↔ Admissible f r := by
  cases f with
  | freeIshtighal e => cases r <;> simp [candidates, Admissible]
  | matchedDescription n e => cases n <;> cases r <;> simp [candidates, Admissible]
  | interpretiveAn b e => cases b <;> cases r <;> simp [candidates, Admissible]

theorem ending_exact (e : Option Ending) (r : Reading) :
    endingOK e r = true ↔ EndingMatches e r := by
  cases e <;> simp [endingOK, EndingMatches]

theorem enumeration_exact (f : Frame) (r : Reading) :
    r ∈ enumerate f ↔ Licensed f r := by
  simp [enumerate, List.mem_filter, candidates_exact, ending_exact, Licensed]

theorem enumeration_sound (f : Frame) (r : Reading)
    (h : r ∈ enumerate f) : Licensed f r := (enumeration_exact f r).mp h

theorem enumeration_complete (f : Frame) (r : Reading)
    (h : Licensed f r) : r ∈ enumerate f := (enumeration_exact f r).mpr h

def CoversAll (f : Frame) (proposal : List Reading) : Prop :=
  ∀ r, Licensed f r → r ∈ proposal

theorem missing_reading_rejected (f : Frame) (r : Reading) (proposal : List Reading)
    (licensed : Licensed f r) (missing : r ∉ proposal) : ¬ CoversAll f proposal := by
  intro complete
  exact missing (complete r licensed)

theorem deleting_any_reading_rejected (f : Frame) (r : Reading)
    (member : r ∈ enumerate f) :
    ¬ CoversAll f ((enumerate f).filter (fun other => other != r)) := by
  apply missing_reading_rejected f r _ (enumeration_sound f r member)
  simp

def rank : Reading → Nat
  | .topic => 0 | .omittedVerb => 1 | .descriptionSubject => 2
  | .frontedPredicate => 3 | .anInterpretiveIndicative => 4
  | .anInterpretiveJussive => 5 | .anMasdariyyaSubjunctive => 6

theorem rank_injective : Function.Injective rank := by
  intro a b h
  cases a <;> cases b <;> simp_all [rank]

theorem candidates_ordered (f : Frame) :
    (candidates f).Pairwise (fun a b => rank a < rank b) := by
  cases f with
  | freeIshtighal e => simp [candidates, rank]
  | matchedDescription n e => cases n <;> simp [candidates, rank]
  | interpretiveAn b e => cases b <;> simp [candidates, rank]

theorem enumeration_ordered (f : Frame) :
    (enumerate f).Pairwise (fun a b => rank a < rank b) := by
  exact (candidates_ordered f).filter _

theorem enumeration_nodup (f : Frame) : (enumerate f).Nodup := by
  apply (enumeration_ordered f).imp
  intro a b h eq
  subst b
  exact Nat.lt_irrefl _ h

theorem distinct_analyses_not_merged (a b : Reading) (h : a ≠ b) : rank a ≠ rank b := by
  intro eq
  exact h (rank_injective eq)

theorem no_jussive_without_la (e : Option Ending) :
    Reading.anInterpretiveJussive ∉ enumerate (.interpretiveAn false e) := by
  rw [enumeration_exact]
  simp [Licensed, Admissible]

theorem dual_description_excludes_subject (e : Option Ending) :
    Reading.descriptionSubject ∉ enumerate (.matchedDescription .dual e) := by
  rw [enumeration_exact]
  simp [Licensed, Admissible]

end Nabt.ClassicalReferenceReadings
