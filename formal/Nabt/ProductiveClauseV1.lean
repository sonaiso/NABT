import Nabt.AcquiredSyntaxV3

/-!
Source-bound active transitive clauses over the independently frozen lexical
scope in evidence/productive_clause_v1. The lexical forms and interpretation
of the sources are authored premises, not consequences of cell identity.

The grammar composes a verb and a nominative/accusative pair in either order.
The parser is exact for this declared relation; this is not completeness for
Arabic. Same-case pairs reject this three-role frame only. Unknown words,
different frames/boundaries and unsupported realization modes defer.
No theorem identifies external people, witnesses a blow, or infers exclusivity.
-/
namespace Nabt.ProductiveClauseV1

def lawId : String := "nabt.productive-clause.v1"

inductive SubjectName | zayd | bakr | khalid | said | qays
  deriving DecidableEq, Repr
inductive ObjectName | zayd | bakr | khalid | said | amr
  deriving DecidableEq, Repr
inductive Order | vso | vos
  deriving DecidableEq, Repr
inductive Lexeme | daraba | nom (name : SubjectName) | acc (name : ObjectName)
  deriving DecidableEq, Repr

def SubjectName.surface : SubjectName → String
  | .zayd => "زَيْدٌ" | .bakr => "بَكْرٌ" | .khalid => "خَالِدٌ"
  | .said => "سَعِيدٌ" | .qays => "قَيْسٌ"
def ObjectName.surface : ObjectName → String
  | .zayd => "زَيْدًا" | .bakr => "بَكْرًا" | .khalid => "خَالِدًا"
  | .said => "سَعِيدًا" | .amr => "عَمْرًا"
def SubjectName.label : SubjectName → String
  | .zayd => "ZAYD" | .bakr => "BAKR" | .khalid => "KHALID"
  | .said => "SAID" | .qays => "QAYS"
def ObjectName.label : ObjectName → String
  | .zayd => "ZAYD" | .bakr => "BAKR" | .khalid => "KHALID"
  | .said => "SAID" | .amr => "AMR"
def Order.label : Order → String | .vso => "VSO" | .vos => "VOS"
def Lexeme.surface : Lexeme → String
  | .daraba => "ضَرَبَ" | .nom n => n.surface | .acc n => n.surface
def Lexeme.label : Lexeme → String
  | .daraba => "DARABA" | .nom n => n.label | .acc n => n.label
def Lexeme.category : Lexeme → String
  | .daraba => "verb" | .nom _ | .acc _ => "proper_name"
def Lexeme.nominalCase : Lexeme → Option String
  | .daraba => none | .nom _ => some "nom" | .acc _ => some "acc"

def subjects : List SubjectName := [.zayd, .bakr, .khalid, .said, .qays]
def objects : List ObjectName := [.zayd, .bakr, .khalid, .said, .amr]
def lexemes : List Lexeme := [.daraba] ++ subjects.map .nom ++ objects.map .acc

/-- One exact declared surface per lexical form; no vowel recovery or aliases. -/
def Lexical (raw : String) (l : Lexeme) : Prop := raw = l.surface
def readLexeme (raw : String) : Option Lexeme :=
  lexemes.find? (fun l => raw == l.surface)

theorem lexical_surface_roundtrip (l : Lexeme) : readLexeme l.surface = some l := by
  cases l with
  | daraba => decide
  | nom n => cases n <;> decide
  | acc n => cases n <;> decide

theorem lexical_read_exact (raw : String) (l : Lexeme) :
    readLexeme raw = some l ↔ Lexical raw l := by
  constructor
  · intro h
    have found := List.find?_some h
    simpa [readLexeme, Lexical, beq_iff_eq] using found
  · intro h
    rw [h]
    exact lexical_surface_roundtrip l

def readWords : List String → Option (List Lexeme)
  | [] => some []
  | raw :: rest => do return (← readLexeme raw) :: (← readWords rest)
def LexicalWords : List String → List Lexeme → Prop
  | [], [] => True
  | raw :: rest, l :: ls => Lexical raw l ∧ LexicalWords rest ls
  | _, _ => False

theorem words_read_exact (raws : List String) (ls : List Lexeme) :
    readWords raws = some ls ↔ LexicalWords raws ls := by
  induction raws generalizing ls with
  | nil => cases ls <;> simp [readWords, LexicalWords]
  | cons raw rest ih =>
    cases ls with
    | nil => cases h : readLexeme raw <;> cases t : readWords rest <;>
        simp [readWords, LexicalWords, h, t]
    | cons l ls =>
      simp only [LexicalWords]
      rw [← lexical_read_exact, ← ih]
      cases h : readLexeme raw <;> cases t : readWords rest <;> simp [readWords, h, t]

theorem lexical_words_surface (raws : List String) (ls : List Lexeme)
    (h : LexicalWords raws ls) : raws = ls.map Lexeme.surface := by
  induction raws generalizing ls with
  | nil => cases ls <;> simp_all [LexicalWords]
  | cons raw rest ih =>
    cases ls with
    | nil => simp [LexicalWords] at h
    | cons l ls =>
      obtain ⟨head, tail⟩ := h
      change raw :: rest = l.surface :: ls.map Lexeme.surface
      change raw = l.surface at head
      rw [head, ih ls tail]

structure Frame where
  subject : SubjectName
  object : ObjectName
  order : Order
  deriving DecidableEq, Repr

def Frame.lexemes (f : Frame) : List Lexeme :=
  match f.order with
  | .vso => [.daraba, .nom f.subject, .acc f.object]
  | .vos => [.daraba, .acc f.object, .nom f.subject]
def Frame.label (f : Frame) : String :=
  "DARABA_" ++ f.subject.label ++ "_" ++ f.object.label ++ "_" ++ f.order.label
def Frame.subjectIndex (f : Frame) : Nat := if f.order == .vso then 1 else 2
def Frame.objectIndex (f : Frame) : Nat := if f.order == .vso then 2 else 1
def readFrame : List Lexeme → Option Frame
  | [v, a, b] => match v, a, b with
    | .daraba, .nom s, .acc o => some ⟨s, o, .vso⟩
    | .daraba, .acc o, .nom s => some ⟨s, o, .vos⟩
    | _, _, _ => none
  | _ => none

theorem frame_roundtrip (f : Frame) : readFrame f.lexemes = some f := by
  rcases f with ⟨s, o, order⟩
  cases order <;> rfl

theorem frame_read_exact (ls : List Lexeme) (f : Frame) :
    readFrame ls = some f ↔ ls = f.lexemes := by
  constructor
  · intro h
    rcases ls with _ | ⟨a, _ | ⟨b, _ | ⟨c, _ | ⟨d, rest⟩⟩⟩⟩
    all_goals try simp [readFrame] at h
    cases a <;> cases b <;> cases c <;> simp_all [Frame.lexemes]
    all_goals subst f; rfl
  · intro h
    rw [h]
    exact frame_roundtrip f

theorem frame_roles_distinct (f : Frame) : f.subjectIndex ≠ f.objectIndex := by
  rcases f with ⟨s, o, order⟩
  cases order <;> simp [Frame.subjectIndex, Frame.objectIndex]

theorem frame_subject_nom (f : Frame) :
    f.lexemes[f.subjectIndex]? = some (.nom f.subject) := by
  rcases f with ⟨s, o, order⟩
  cases order <;> rfl

theorem frame_object_acc (f : Frame) :
    f.lexemes[f.objectIndex]? = some (.acc f.object) := by
  rcases f with ⟨s, o, order⟩
  cases order <;> rfl

theorem both_orders (s : SubjectName) (o : ObjectName) :
    readFrame [.daraba, .nom s, .acc o] = some ⟨s, o, .vso⟩ ∧
    readFrame [.daraba, .acc o, .nom s] = some ⟨s, o, .vos⟩ := ⟨rfl, rfl⟩

theorem same_case_not_licensed (s t : SubjectName) (o p : ObjectName) :
    readFrame [.daraba, .nom s, .nom t] = none ∧
    readFrame [.daraba, .acc o, .acc p] = none := ⟨rfl, rfl⟩

open Nabt.AlignedAcquisition (Span)
def sourcePieces := AcquiredSyntaxV3.sourcePieces
def wordSpans := AcquiredSyntaxV3.wordSpans
def boundaryValid := AcquiredSyntaxV3.boundaryValid
def words (text : String) : List String := (wordSpans text).map (fun s => String.ofList s.raw)

/-- A separate declarative relation: exact source boundaries plus lexical
    interpretation of the frame. It does not call the parser. -/
def SourceGrammar (text : String) (f : Frame) : Prop :=
  boundaryValid text = true ∧ LexicalWords (words text) f.lexemes
def parse (text : String) : Option Frame := do
  if !boundaryValid text then none else readFrame (← readWords (words text))

theorem parser_exact (text : String) (f : Frame) :
    parse text = some f ↔ SourceGrammar text f := by
  unfold SourceGrammar
  rw [← words_read_exact]
  cases hb : boundaryValid text with
  | false => simp [parse, hb]
  | true =>
    cases hr : readWords (words text) with
    | none => simp [parse, hb, hr]
    | some ls =>
      simp only [parse, hb, hr, Bool.not_true, Bool.false_eq_true, ↓reduceIte,
        true_and, Option.some.injEq]
      exact frame_read_exact ls f

theorem parser_sound {text : String} {f : Frame} (h : parse text = some f) :
    SourceGrammar text f := (parser_exact _ _).mp h

theorem parser_complete {text : String} {f : Frame} (h : SourceGrammar text f) :
    parse text = some f := (parser_exact _ _).mpr h

theorem parser_unique {text : String} {f g : Frame}
    (hf : parse text = some f) (hg : parse text = some g) : f = g := by
  exact Option.some.inj (hf.symm.trans hg)

theorem parser_source_words {text : String} {f : Frame} (h : parse text = some f) :
    words text = f.lexemes.map Lexeme.surface :=
  lexical_words_surface _ _ (parser_sound h).2

theorem source_restoration (text : String) :
    String.ofList (((sourcePieces text).map Span.raw).flatten) = text :=
  AcquiredSyntaxV3.source_restoration text

theorem source_offsets_contiguous (text : String) :
    AlignedAcquisition.Contiguous 0 0 (sourcePieces text) :=
  AcquiredSyntaxV3.source_offsets_contiguous text

/-- Only the two known three-word same-case shapes reject this frame. Other
    known-word sequences remain outside the grammar, rather than rejected. -/
def caseConflict : List Lexeme → Bool
  | [.daraba, .nom _, .nom _] => true
  | [.daraba, .acc _, .acc _] => true
  | _ => false

theorem case_conflict_no_frame (ls : List Lexeme) (h : caseConflict ls = true) :
    readFrame ls = none := by
  rcases ls with _ | ⟨a, _ | ⟨b, _ | ⟨c, _ | ⟨d, rest⟩⟩⟩⟩
  all_goals try simp [caseConflict] at h
  cases a <;> cases b <;> cases c <;> simp_all [readFrame]

structure Request where
  text : String
  sourceId : String
  revision : String
  scope : String
  ending : String
  onset : String
  deriving DecidableEq, Repr
def Request.modeAllowed (r : Request) : Bool := r.ending == "wasl" && r.onset == "word_initial"
structure Result where
  request : Request
  reading : Option Frame
  deriving DecidableEq, Repr
def evaluate (r : Request) : Result := ⟨r, if r.modeAllowed then parse r.text else none⟩

inductive Status | licensed | rejectedInScope | defer
  deriving DecidableEq, Repr
def Status.label : Status → String
  | .licensed => "LICENSED_CLAUSE" | .rejectedInScope => "REJECTED_IN_SCOPE" | .defer => "DEFER"
def status (r : Result) : Status :=
  if r.reading.isSome then .licensed
  else if r.request.modeAllowed && boundaryValid r.request.text &&
      ((readWords (words r.request.text)).map caseConflict).getD false then .rejectedInScope
  else .defer
def reason (r : Result) : String :=
  if !r.request.modeAllowed then "MODE_OUTSIDE_DECLARED_SCOPE"
  else if !boundaryValid r.request.text then "BOUNDARY_OUTSIDE_DECLARED_SCOPE"
  else if (readWords (words r.request.text)).isNone then "OUTSIDE_DECLARED_LEXICON"
  else if r.reading.isSome then "DECLARED_ACTIVE_TRANSITIVE_FRAME"
  else if status r == .rejectedInScope then "ROLE_CASE_CONFLICT"
  else "OUTSIDE_DECLARED_GRAMMAR"

theorem evaluated_reading_sound {r : Request} {f : Frame}
    (h : (evaluate r).reading = some f) :
    r.modeAllowed = true ∧ SourceGrammar r.text f := by
  cases hm : r.modeAllowed with
  | false => simp [evaluate, hm] at h
  | true =>
    refine ⟨rfl, ?_⟩
    exact parser_sound (by simpa [evaluate, hm] using h)

theorem unsupported_mode_defers (r : Request) (h : r.modeAllowed = false) :
    status (evaluate r) = .defer := by simp [status, evaluate, h]

def verify (expected : Request) (claimed : Result) : Bool := claimed == evaluate expected
theorem verified_binding {expected : Request} {claimed : Result}
    (h : verify expected claimed = true) :
    claimed = evaluate expected ∧ claimed.request = expected := by
  have he : claimed = evaluate expected := by simpa only [verify, beq_iff_eq] using h
  exact ⟨he, by rw [he]; rfl⟩

theorem verified_reading_sound {expected : Request} {claimed : Result} {f : Frame}
    (checked : verify expected claimed = true) (reading : claimed.reading = some f) :
    expected.modeAllowed = true ∧ SourceGrammar expected.text f := by
  rw [(verified_binding checked).1] at reading
  exact evaluated_reading_sound reading

theorem changed_binding_rejected {expected : Request} {claimed : Result}
    (different : claimed.request ≠ expected) : verify expected claimed = false := by
  apply Bool.eq_false_iff.mpr
  intro accepted
  exact different (verified_binding accepted).2

end Nabt.ProductiveClauseV1
