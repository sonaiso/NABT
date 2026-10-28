import Nabt.AlignedAcquisition

/-!
Exact finite original-source person/ordinary nominal grammar. The lexical
relation and frames are authored interpretations in the frozen v3 contract.
No theorem identifies a referent, proves Arabic-wide adequacy, or turns a
syntax reading into an acquisition/phonology license.
-/
namespace Nabt.AcquiredSyntaxV3

def lawId : String := "nabt.acquired-syntax.v3"
inductive Task | person | nominal deriving DecidableEq, Repr
inductive PersonForm | qumtu | qumta | qumti deriving DecidableEq, Repr
inductive Number | singular | dual | plural deriving DecidableEq, Repr
inductive Order | subjectFirst | predicateFirst deriving DecidableEq, Repr
inductive Lexeme
  | qumtu | qumta | qumti | walad | waladDual | awlad | dhahib | dhahibDual | dhahibPlural
  deriving DecidableEq, Repr

def Lexeme.full : Lexeme → String
  | .qumtu => "قُمْتُ" | .qumta => "قُمْتَ" | .qumti => "قُمْتِ"
  | .walad => "الْوَلَدُ" | .waladDual => "الْوَلَدَانِ" | .awlad => "الْأَوْلَادُ"
  | .dhahib => "ذَاهِبٌ" | .dhahibDual => "ذَاهِبَانِ" | .dhahibPlural => "ذَاهِبُونَ"
def Lexeme.short : Lexeme → String
  | .qumtu => "قمتُ" | .qumta => "قمتَ" | .qumti => "قمتِ"
  | .walad => "الولدُ" | .waladDual => "الولدانِ" | .awlad => "الأولادُ"
  | .dhahib => "ذاهبٌ" | .dhahibDual => "ذاهبانِ" | .dhahibPlural => "ذاهبونَ"
def Lexeme.label : Lexeme → String
  | .qumtu => "QUMTU" | .qumta => "QUMTA" | .qumti => "QUMTI"
  | .walad => "WALAD" | .waladDual => "WALAD_DUAL" | .awlad => "AWLAD"
  | .dhahib => "DHAHIB" | .dhahibDual => "DHAHIB_DUAL" | .dhahibPlural => "DHAHIB_PLURAL"
def lexemes : List Lexeme :=
  [.qumtu, .qumta, .qumti, .walad, .waladDual, .awlad, .dhahib, .dhahibDual, .dhahibPlural]

/-- Explicit finite lexical relation, independent of search order. -/
def Lexical (raw : String) (l : Lexeme) : Prop := raw = l.full ∨ raw = l.short
def readLexeme (raw : String) : Option Lexeme :=
  lexemes.find? (fun l => raw == l.full || raw == l.short)

theorem lexical_read_exact (raw : String) (l : Lexeme) :
    readLexeme raw = some l ↔ Lexical raw l := by
  constructor
  · intro h
    have found := List.find?_some h
    simpa [readLexeme, Lexical, Bool.or_eq_true, beq_iff_eq] using found
  · intro h
    rcases h with h | h <;> rw [h] <;> cases l <;> decide

def PersonForm.lexeme : PersonForm → Lexeme
  | .qumtu => .qumtu | .qumta => .qumta | .qumti => .qumti
def PersonForm.person : PersonForm → Nat | .qumtu => 1 | .qumta => 2 | .qumti => 2
def PersonForm.gender : PersonForm → Option String
  | .qumtu => none | .qumta => some "masculine" | .qumti => some "feminine"
def PersonForm.vowel : PersonForm → String | .qumtu => "ُ" | .qumta => "َ" | .qumti => "ِ"
def Number.label : Number → String | .singular => "singular" | .dual => "dual" | .plural => "plural"
def Number.subject : Number → Lexeme | .singular => .walad | .dual => .waladDual | .plural => .awlad
def Number.predicate : Number → Lexeme | .singular => .dhahib | .dual => .dhahibDual | .plural => .dhahibPlural

/-- Both arguments belong to the same declared agreement frame. -/
def OrdinaryPredication (subject predicate : Lexeme) (n : Number) : Prop :=
  subject = n.subject ∧ predicate = n.predicate

theorem nominal_number_mismatch (a b n : Number)
    (h : OrdinaryPredication a.subject b.predicate n) : a = b := by
  cases a <;> cases b <;> cases n <;> simp_all [OrdinaryPredication, Number.subject, Number.predicate]

inductive Frame | person (p : PersonForm) | nominal (n : Number) (o : Order)
  deriving DecidableEq, Repr
def Frame.task : Frame → Task | .person _ => .person | .nominal .. => .nominal
def Frame.lexemes : Frame → List Lexeme
  | .person p => [p.lexeme]
  | .nominal n .subjectFirst => [n.subject, n.predicate]
  | .nominal n .predicateFirst => [n.predicate, n.subject]
def Frame.label : Frame → String
  | .person p => p.lexeme.label
  | .nominal n o => "NOMINAL_" ++ n.label ++
      (if o == .subjectFirst then "_SUBJECT_FIRST" else "_PREDICATE_FIRST")
def frames : List Frame := [.person .qumtu, .person .qumta, .person .qumti,
  .nominal .singular .subjectFirst, .nominal .singular .predicateFirst,
  .nominal .dual .subjectFirst, .nominal .dual .predicateFirst,
  .nominal .plural .subjectFirst, .nominal .plural .predicateFirst]
def readFrame (task : Task) (ls : List Lexeme) : Option Frame :=
  frames.find? (fun f => f.task == task && f.lexemes == ls)

theorem frame_roundtrip (f : Frame) : readFrame f.task f.lexemes = some f := by
  cases f with
  | person p => cases p <;> decide
  | nominal n o => cases n <;> cases o <;> decide

theorem frame_read_exact (task : Task) (ls : List Lexeme) (f : Frame) :
    readFrame task ls = some f ↔ f.task = task ∧ f.lexemes = ls := by
  constructor
  · intro h
    have found := List.find?_some h
    simpa [readFrame, Bool.and_eq_true, beq_iff_eq] using found
  · rintro ⟨ht, hl⟩
    rw [← ht, ← hl]
    exact frame_roundtrip f

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
    | nil => cases h : readLexeme raw <;> cases t : readWords rest <;> simp [readWords, LexicalWords, h, t]
    | cons l ls =>
      simp only [LexicalWords]
      rw [← lexical_read_exact, ← ih]
      cases h : readLexeme raw <;> cases t : readWords rest <;> simp [readWords, h, t]

open Nabt.AlignedAcquisition (Span)
def sourcePieces (text : String) : List Span :=
  Nabt.AlignedAcquisition.locate 0 0 (Nabt.AlignedAcquisition.pieceTexts text.toList)
def wordGroups (text : String) : List (List Span) :=
  (Nabt.AlignedAcquisition.groups (sourcePieces text)).filter
    (fun g => !(g.any Nabt.AlignedAcquisition.boundarySpan))
def wordSpans (text : String) : List Span :=
  (wordGroups text).map (fun g =>
    ⟨(g.head?.map Span.start).getD 0, (g.head?.map Span.byteStart).getD 0,
      (g.map Span.raw).flatten⟩)
def words (text : String) : List String := (wordSpans text).map (fun s => String.ofList s.raw)
def asciiSpace (c : Char) : Bool := c == ' ' || c == '\t'
def boundaryValid (text : String) : Bool :=
  let rev := text.toList.reverse.dropWhile asciiSpace
  let body := if rev.head? == some '.' then rev.tail else rev
  body.all (fun c => !(Nabt.AlignedAcquisition.separator c) || asciiSpace c)

/-- The grammar uses exact source tokenization plus the explicit lexical
relation, not the parser's success flag. Separators remain in sourcePieces. -/
def SourceGrammar (text : String) (task : Task) (f : Frame) : Prop :=
  boundaryValid text = true ∧ f.task = task ∧ LexicalWords (words text) f.lexemes
def parse (text : String) (task : Task) : Option Frame := do
  if !boundaryValid text then none else readFrame task (← readWords (words text))

theorem parser_exact (text : String) (task : Task) (f : Frame) :
    parse text task = some f ↔ SourceGrammar text task f := by
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
      change readFrame task ls = some f ↔ f.task = task ∧ ls = f.lexemes
      rw [frame_read_exact]
      exact and_congr Iff.rfl eq_comm

theorem parser_sound {text : String} {task : Task} {f : Frame}
    (h : parse text task = some f) : SourceGrammar text task f := (parser_exact _ _ _).mp h

theorem source_restoration (text : String) :
    String.ofList (((sourcePieces text).map Span.raw).flatten) = text := by
  simp [sourcePieces, Nabt.AlignedAcquisition.locate_raw,
    Nabt.AlignedAcquisition.pieceTexts_restore]

theorem source_offsets_contiguous (text : String) :
    Nabt.AlignedAcquisition.Contiguous 0 0 (sourcePieces text) :=
  Nabt.AlignedAcquisition.locate_contiguous _ _ _

def undecided (text : String) (task : Task) : Bool :=
  task == .person && boundaryValid text &&
    (words text == ["قمت"] || words text == ["قُمْت"] || words text == ["قُمْتْ"])
theorem unmarked_no_person :
    parse "قمت" .person = none ∧ parse "قُمْت" .person = none ∧ parse "قُمْتْ" .person = none := by decide

theorem person_mapping :
    PersonForm.person .qumtu = 1 ∧ PersonForm.gender .qumtu = none ∧
    PersonForm.person .qumta = 2 ∧ PersonForm.gender .qumta = some "masculine" ∧
    PersonForm.person .qumti = 2 ∧ PersonForm.gender .qumti = some "feminine" := by decide

theorem nominal_both_orders (n : Number) :
    readFrame .nominal [n.subject, n.predicate] = some (.nominal n .subjectFirst) ∧
    readFrame .nominal [n.predicate, n.subject] = some (.nominal n .predicateFirst) := by
  cases n <;> decide

theorem person_surface_roundtrip (p : PersonForm) :
    parse p.lexeme.full .person = some (.person p) ∧
    parse p.lexeme.short .person = some (.person p) := by
  cases p <;> decide

theorem nominal_source_roundtrip (n : Number) :
    parse (n.subject.short ++ " " ++ n.predicate.short) .nominal = some (.nominal n .subjectFirst) ∧
    parse (n.predicate.short ++ " " ++ n.subject.short) .nominal = some (.nominal n .predicateFirst) := by
  cases n <;> decide

theorem nominal_mismatch_rejected (a b : Number) (h : a ≠ b) :
    readFrame .nominal [a.subject, b.predicate] = none := by
  cases a <;> cases b <;> first | exact False.elim (h rfl) | decide

structure Request where
  text : String
  task : Task
  sourceId : String
  revision : String
  scope : String
  ending : String
  onset : String
  deriving DecidableEq, Repr
structure Result where
  request : Request
  reading : Option Frame
  deriving DecidableEq, Repr
def evaluate (r : Request) : Result := ⟨r, parse r.text r.task⟩
def verify (expected : Request) (claimed : Result) : Bool := claimed == evaluate expected
theorem verified_binding {expected : Request} {claimed : Result} (h : verify expected claimed = true) :
    claimed = evaluate expected ∧ claimed.request = expected := by
  have he : claimed = evaluate expected := by simpa only [verify, beq_iff_eq] using h
  exact ⟨he, by rw [he]; rfl⟩

end Nabt.AcquiredSyntaxV3
