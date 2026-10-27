import Nabt.Cell
import Nabt.Law

/-!
Source-preserving, deliberately partial acquisition of A116 representations.
This law does not assert acoustic, lexical, syntactic or world-truth authority.
The exact Unicode scalars are partitioned before any representation is assigned.
-/
namespace Nabt.AlignedAcquisition

set_option maxRecDepth 20000
set_option maxHeartbeats 2000000

def lawId := "nabt.aligned-acquisition.v1"
def alphabetId := "nabt.a116.v1"

inductive Ending | wasl | waqf deriving DecidableEq, Repr
inductive Status | licensed | boundary | deferred | invalid deriving DecidableEq, Repr

structure Request where
  text : String
  sourceId : String
  revision : String
  scope : String
  ending : Ending
  deriving DecidableEq, Repr

structure Decision where
  status : Status
  rule : String
  cells : List Atom
  deriving DecidableEq, Repr

def licensed (rule : String) (cells : List Atom) : Decision := ⟨.licensed, rule, cells⟩
def deferred (rule : String) : Decision := ⟨.deferred, rule, []⟩
def invalid (rule : String) : Decision := ⟨.invalid, rule, []⟩

def isMark (c : Char) : Bool := "ًٌٍَُِّْٰ".toList.contains c
def isVowel (c : Char) : Bool := "ًٌٍَُِْ".toList.contains c
def separator (c : Char) : Bool := " \t\r\n.،؛,:!?؟()[]{}«»\"“”".toList.contains c

/-- A right fold attaches only recognized marks to their preceding head. -/
def prependPiece (c : Char) (ps : List (List Char)) : List (List Char) :=
  if separator c then [c] :: ps
  else match ps with
  | p :: rest => if p.all isMark then (c :: p) :: rest else [c] :: ps
  | [] => [[c]]

def pieceTexts (cs : List Char) : List (List Char) := cs.foldr prependPiece []

private theorem prependPiece_flatten (c : Char) (ps : List (List Char)) :
    (prependPiece c ps).flatten = c :: ps.flatten := by
  by_cases hs : separator c = true
  · simp [prependPiece, hs]
  · cases ps with
    | nil => simp [prependPiece, hs]
    | cons p rest =>
      by_cases hp : p.all isMark = true <;> simp [prependPiece, hs, hp]

theorem pieceTexts_restore (cs : List Char) : (pieceTexts cs).flatten = cs := by
  induction cs with
  | nil => rfl
  | cons c cs ih => simpa only [pieceTexts, List.foldr_cons, prependPiece_flatten] using congrArg (c :: ·) ih

structure Span where
  start : Nat
  byteStart : Nat
  raw : List Char
  deriving DecidableEq, Repr

def Span.stop (p : Span) : Nat := p.start + p.raw.length
def Span.byteStop (p : Span) : Nat := p.byteStart + (String.ofList p.raw).utf8ByteSize

def locate : Nat → Nat → List (List Char) → List Span
  | _, _, [] => []
  | cp, bp, raw :: rest =>
    let p : Span := ⟨cp, bp, raw⟩
    p :: locate p.stop p.byteStop rest

theorem locate_raw (cp bp : Nat) (ps : List (List Char)) :
    (locate cp bp ps).map Span.raw = ps := by
  induction ps generalizing cp bp with
  | nil => rfl
  | cons p ps ih => simp only [locate, List.map_cons, ih]

/-- Both coordinate systems advance by the exact originating raw piece. -/
def Contiguous : Nat → Nat → List Span → Prop
  | _, _, [] => True
  | cp, bp, p :: rest => p.start = cp ∧ p.byteStart = bp ∧ Contiguous p.stop p.byteStop rest

theorem locate_contiguous (cp bp : Nat) (ps : List (List Char)) :
    Contiguous cp bp (locate cp bp ps) := by
  induction ps generalizing cp bp with
  | nil => trivial
  | cons p ps ih => exact ⟨rfl, rfl, ih _ _⟩

def boundarySpan (p : Span) : Bool := p.raw.head?.any separator

def prependGroup (p : Span) (gs : List (List Span)) : List (List Span) :=
  if boundarySpan p then [p] :: gs
  else match gs with
  | g :: rest => if g.any boundarySpan then [p] :: gs else (p :: g) :: rest
  | [] => [[p]]

def groups (ps : List Span) : List (List Span) := ps.foldr prependGroup []

private theorem prependGroup_flatten (p : Span) (gs : List (List Span)) :
    (prependGroup p gs).flatten = p :: gs.flatten := by
  by_cases hb : boundarySpan p = true
  · simp [prependGroup, hb]
  · cases gs with
    | nil => simp [prependGroup, hb]
    | cons g rest =>
      by_cases hg : g.any boundarySpan = true <;> simp [prependGroup, hb, hg]

theorem groups_restore (ps : List Span) : (groups ps).flatten = ps := by
  induction ps with
  | nil => rfl
  | cons p ps ih => simpa only [groups, List.foldr_cons, prependGroup_flatten] using congrArg (p :: ·) ih

structure Entry where
  span : Span
  decision : Decision
  deriving DecidableEq, Repr

def carrier (c : Char) : Option Carrier :=
  if "أإؤئ".toList.contains c then some ⟨28, by decide⟩
  else
    let i := canonicalCarriers.idxOf (String.singleton c)
    if h : i < 29 then some ⟨i, h⟩ else none

def atom (c : Carrier) (m : Mark) : Atom := Cell.encode ⟨c, m⟩
def expanded (c : Carrier) (m : Mark) (shadda : Bool) : List Atom :=
  (if shadda then [atom c ⟨3, by decide⟩] else []) ++ [atom c m]

/-- The declared local representation, with one slot or the shadda two-slot expansion. -/
inductive MarkedExpansion : Carrier → Mark → Bool → List Atom → Prop
  | single (c : Carrier) (m : Mark) : MarkedExpansion c m false [atom c m]
  | geminate (c : Carrier) (m : Mark) :
      MarkedExpansion c m true [atom c ⟨3, by decide⟩, atom c m]

theorem expanded_sound (c : Carrier) (m : Mark) (shadda : Bool) :
    MarkedExpansion c m shadda (expanded c m shadda) := by
  cases shadda
  · exact .single c m
  · exact .geminate c m

def ordinary : Char → Option Mark
  | 'َ' => some ⟨0, by decide⟩ | 'ُ' => some ⟨1, by decide⟩
  | 'ِ' => some ⟨2, by decide⟩ | 'ْ' => some ⟨3, by decide⟩ | _ => none

def tanwin : Char → Option Mark
  | 'ً' => some ⟨0, by decide⟩ | 'ٌ' => some ⟨1, by decide⟩
  | 'ٍ' => some ⟨2, by decide⟩ | _ => none

def rawVowels (p : Span) : List Char := p.raw.tail.filter isVowel

def previousShort (prev : Option Entry) (mark : Nat) : Bool :=
  match prev with
  | none => false
  | some e =>
    e.decision.status == .licensed &&
    (match rawVowels e.span with | [c] => (ordinary c).any (fun m => m.val == mark) | _ => false) &&
    e.decision.cells.getLast?.any (fun a => a.val % 4 == mark)

def debt (ps : List Span) : Option String :=
  let raw := ps.flatMap Span.raw
  let skeleton := String.ofList (raw.filter (fun c => !isMark c))
  if ["أولو", "أولي", "أولئك", "أولاء"].contains skeleton then some "SILENT_LETTER_LEXICON_REQUIRED"
  else if ["هذا", "هذه", "هذان", "هذين", "هؤلاء", "ذلك", "لكن", "إله", "الله", "الرحمن"].contains skeleton &&
      !raw.contains 'ٰ' then some "ORTHOGRAPHIC_LEXICON_REQUIRED"
  else none

/-- Invalid mark evidence outranks every lexical debt and representation rule. -/
def malformed (p : Span) : Option String :=
  if p.raw.head?.any isMark then some "MARK_WITHOUT_CARRIER"
  else if (rawVowels p).length > 1 || (p.raw.filter (· == 'ّ')).length > 1 ||
      (p.raw.filter (· == 'ٰ')).length > 1 then some "CONFLICTING_MARKS"
  else if p.raw.contains 'ّ' && p.raw.contains 'ْ' then some "SHADDA_WITH_SUKUN"
  else if p.raw.contains 'ٰ' && (rawVowels p).any (· != 'َ') then some "DAGGER_VOWEL_CONFLICT"
  else none

def tanwinCells (c : Carrier) (m : Mark) (shadda pause : Bool) : List Atom :=
  if pause then
    if m.val == 0 then expanded c ⟨0, by decide⟩ shadda ++ [atom ⟨0, by decide⟩ ⟨3, by decide⟩]
    else expanded c ⟨3, by decide⟩ shadda
  else expanded c m shadda ++ [atom ⟨24, by decide⟩ ⟨3, by decide⟩]

/-- Tanwin licenses only the enumerated wasl or ordinary-pause expansions. -/
inductive TanwinExpansion : Carrier → Mark → Bool → Bool → List Atom → Prop
  | connected (c : Carrier) (m : Mark) (s : Bool) (cs : List Atom)
      (h : MarkedExpansion c m s cs) :
      TanwinExpansion c m s false (cs ++ [atom ⟨24, by decide⟩ ⟨3, by decide⟩])
  | fathaPause (c : Carrier) (m : Mark) (s : Bool) (cs : List Atom)
      (hm : m.val = 0) (h : MarkedExpansion c ⟨0, by decide⟩ s cs) :
      TanwinExpansion c m s true (cs ++ [atom ⟨0, by decide⟩ ⟨3, by decide⟩])
  | otherPause (c : Carrier) (m : Mark) (s : Bool) (cs : List Atom)
      (hm : m.val ≠ 0) (h : MarkedExpansion c ⟨3, by decide⟩ s cs) :
      TanwinExpansion c m s true cs

theorem tanwinCells_sound (c : Carrier) (m : Mark) (s pause : Bool) :
    TanwinExpansion c m s pause (tanwinCells c m s pause) := by
  cases pause
  · exact .connected c m s _ (expanded_sound c m s)
  · by_cases hm : m.val = 0
    · simpa [tanwinCells, hm] using TanwinExpansion.fathaPause c m s _ hm (expanded_sound c ⟨0, by decide⟩ s)
    · simpa [tanwinCells, hm] using TanwinExpansion.otherPause c m s _ hm (expanded_sound c ⟨3, by decide⟩ s)

def classifyPiece (wordDebt : Option String) (pause initial : Bool)
    (prev : Option Entry) (p : Span) (rest : List Span) : Decision := Id.run do
  if boundarySpan p then return ⟨.boundary, "BOUNDARY", []⟩
  if let some rule := malformed p then return invalid rule
  if let some rule := wordDebt then return deferred rule
  let head := p.raw.headD '\x00'
  let marks := p.raw.tail
  let vs := rawVowels p
  let shadda := marks.contains 'ّ'
  let dagger := marks.contains 'ٰ'
  let final := rest.isEmpty
  let beforeSilentAlif := match rest with | [q] => q.raw == ['ا'] | _ => false
  let atPause := pause && (final || (vs == ['ً'] && beforeSilentAlif))
  if head == 'ـ' then return deferred "TATWEEL_UNSUPPORTED"
  if head == 'آ' then return deferred "MADDA_REQUIRED"
  if head == 'ٱ' then return deferred "HAMZAT_WASL_REQUIRED"
  if head == 'ى' then
    if final && marks.isEmpty && previousShort prev 0 then
      return licensed "MAQSURA" [atom ⟨0, by decide⟩ ⟨3, by decide⟩]
    return deferred "MAQSURA_CONTEXT_REQUIRED"
  if head == 'ة' then
    if !final then return deferred "TA_MARBUTA_CONTEXT_REQUIRED"
    if dagger then return deferred "TA_MARBUTA_CONTEXT_REQUIRED"
    match vs with
    | [v] =>
      if v == 'ْ' then return deferred "TA_MARBUTA_CONTEXT_REQUIRED"
      if let some m := ordinary v then
        if pause then return licensed "TA_MARBUTA_WAQF" (expanded ⟨25, by decide⟩ ⟨3, by decide⟩ shadda)
        return licensed "TA_MARBUTA_WASL" (expanded ⟨2, by decide⟩ m shadda)
      if let some m := tanwin v then
        if pause then return licensed "TA_MARBUTA_WAQF" (expanded ⟨25, by decide⟩ ⟨3, by decide⟩ shadda)
        return licensed "TA_MARBUTA_WASL" (tanwinCells ⟨2, by decide⟩ m shadda false)
      return deferred "TA_MARBUTA_CONTEXT_REQUIRED"
    | _ => return deferred "TA_MARBUTA_CONTEXT_REQUIRED"
  let some c := carrier head | return deferred "UNSUPPORTED_CHARACTER"
  if marks.isEmpty then
    if head == 'ا' && final && prev.any (fun e => e.decision.status == .licensed && rawVowels e.span == ['ً']) then
      return licensed "ALIF_TANWIN" []
    if head == 'ا' || head == 'و' || head == 'ي' then
      let m := if head == 'ا' then 0 else if head == 'و' then 1 else 2
      if previousShort prev m then return licensed "LONG_VOWEL" [atom c ⟨3, by decide⟩]
      if head == 'ا' && initial then return deferred "HAMZAT_WASL_REQUIRED"
      if head == 'ا' && final && prev.any (fun e => e.span.raw.head? == some 'و') then
        return deferred "PLURAL_ALIF_REQUIRED"
      return deferred "LONG_VOWEL_CONTEXT_REQUIRED"
    if head == 'ل' && prev.any (fun e => e.span.raw == ['ا']) then return deferred "ARTICLE_LAM_REQUIRED"
    return deferred "MISSING_VOCALIZATION"
  match vs with
  | [] => return deferred "MISSING_VOCALIZATION"
  | v :: _ =>
    if dagger then
      return licensed "DAGGER_ALIF" (expanded c ⟨0, by decide⟩ shadda ++ [atom ⟨0, by decide⟩ ⟨3, by decide⟩])
    if let some m := tanwin v then
      if (final || beforeSilentAlif) && c.val == 28 && m.val == 0 && prev.any (fun e => e.span.raw == ['ا']) then
        return deferred "HAMZA_TANWIN_EXCEPTION"
      return licensed (if atPause then "TANWIN_WAQF" else "TANWIN_WASL") (tanwinCells c m shadda atPause)
    if let some m := ordinary v then
      if atPause then return licensed "ORDINARY_WAQF" (expanded c ⟨3, by decide⟩ shadda)
      return licensed (if shadda then "SHADDA" else if "أإؤئ".toList.contains head then "HAMZA_SEAT" else "MARKED_CARRIER")
        (expanded c m shadda)
    return deferred "UNSUPPORTED_CHARACTER"

def classifyWord (wordDebt : Option String) (pause : Bool) : Bool → Option Entry → List Span → List Entry
  | _, _, [] => []
  | initial, prev, p :: rest =>
    let e : Entry := ⟨p, classifyPiece wordDebt pause initial prev p rest⟩
    e :: classifyWord wordDebt pause false (some e) rest

private theorem classifyWord_spans (d : Option String) (pause initial : Bool) (prev : Option Entry) (ps : List Span) :
    (classifyWord d pause initial prev ps).map Entry.span = ps := by
  induction ps generalizing initial prev with
  | nil => rfl
  | cons p ps ih => simp only [classifyWord, List.map_cons, ih]

def wordGroup (g : List Span) : Bool := !g.isEmpty && !g.any boundarySpan

def classifyGroups (ending : Ending) : List (List Span) → List (List Entry)
  | [] => []
  | g :: rest =>
    classifyWord (debt g) (ending == .waqf && !rest.any wordGroup) true none g :: classifyGroups ending rest

private theorem classifyGroups_spans (ending : Ending) (gs : List (List Span)) :
    ((classifyGroups ending gs).flatten.map Entry.span) = gs.flatten := by
  induction gs with
  | nil => rfl
  | cons g gs ih => simp [classifyGroups, classifyWord_spans, ih]

structure Result where
  request : Request
  groups : List (List Entry)
  deriving DecidableEq, Repr

def acquire (r : Request) : Result :=
  ⟨r, classifyGroups r.ending (groups (locate 0 0 (pieceTexts r.text.toList)))⟩

def Result.entries (r : Result) : List Entry := r.groups.flatten

def complete (es : List Entry) : Bool := !es.isEmpty && es.all (fun e => e.decision.status == .licensed)
def emitted (es : List Entry) : List Atom := es.flatMap (fun e => e.decision.cells)
def handoff (es : List Entry) : Option (List Atom) := if complete es then some (emitted es) else none

def wordEntries (r : Result) : List (List Entry) :=
  r.groups.filter (fun g => !g.isEmpty && !g.any (fun e => e.decision.status == .boundary))

def status (es : List Entry) : String :=
  if es.any (fun e => e.decision.status == .invalid) then "INVALID_INPUT"
  else if es.any (fun e => e.decision.status == .deferred) then "DEFER"
  else "ACQUIRED"

def Result.status (r : Result) : String := if (wordEntries r).isEmpty then "DEFER" else Nabt.AlignedAcquisition.status r.entries

def Result.reason (r : Result) : String :=
  if (wordEntries r).isEmpty then "NO_WORD"
  else if r.status == "INVALID_INPUT" then "INVALID_PIECE"
  else if r.status == "DEFER" then "DEFERRED_PIECE"
  else "COMPLETE_ACQUISITION"

private theorem status_complete (es : List Entry) (h : status es = "ACQUIRED") :
    ∀ e ∈ es, e.decision.status = .licensed ∨ e.decision.status = .boundary := by
  unfold status at h
  split at h
  · contradiction
  next hi =>
    split at h
    · contradiction
    next hd =>
      simp only [List.any_eq_true, beq_iff_eq] at hi hd
      intro e he
      have hni : e.decision.status ≠ .invalid := fun hi' => hi ⟨e, he, hi'⟩
      have hnd : e.decision.status ≠ .deferred := fun hd' => hd ⟨e, he, hd'⟩
      cases hs : e.decision.status <;> simp_all

theorem acquired_no_pending {r : Result} (h : r.status = "ACQUIRED") :
    ∀ e ∈ r.entries, e.decision.status = .licensed ∨ e.decision.status = .boundary := by
  unfold Result.status at h
  split at h
  · contradiction
  · exact status_complete _ h

theorem acquire_spans (r : Request) :
    (acquire r).entries.map Entry.span = locate 0 0 (pieceTexts r.text.toList) := by
  simp only [acquire, Result.entries, classifyGroups_spans, groups_restore]

theorem acquire_restores_source (r : Request) :
    String.ofList (((acquire r).entries.map (fun e => e.span.raw)).flatten) = r.text := by
  have h := congrArg (List.map Span.raw) (acquire_spans r)
  simp only [List.map_map, locate_raw, Function.comp_def] at h
  rw [h, pieceTexts_restore, String.ofList_toList]

theorem acquire_offsets_contiguous (r : Request) :
    Contiguous 0 0 ((acquire r).entries.map Entry.span) := by
  rw [acquire_spans]
  exact locate_contiguous _ _ _

theorem emitted_cells_bounded (es : List Entry) (a : Atom) (_ : a ∈ emitted es) : a.val < 116 := a.isLt

theorem handoff_complete {es : List Entry} {cells : List Atom} (h : handoff es = some cells) :
    es ≠ [] ∧ (∀ e ∈ es, e.decision.status = .licensed) ∧ cells = emitted es := by
  unfold handoff at h
  split at h
  next hc =>
    have parts : es ≠ [] ∧ (∀ e ∈ es, e.decision.status = .licensed) := by
      simpa [complete] using hc
    exact ⟨parts.1, parts.2, (Option.some.inj h).symm⟩
  next hc => contradiction

/-- Exact replay is bound to the entire request, including identity and ending. -/
def verify (expected : Request) (claimed : Result) : Bool := claimed == acquire expected

theorem verified_binding {expected : Request} {claimed : Result} (h : verify expected claimed = true) :
    claimed = acquire expected ∧ claimed.request = expected := by
  have he : claimed = acquire expected := by simpa only [verify, beq_iff_eq] using h
  exact ⟨he, by rw [he]; rfl⟩

/-- Shape checking consumes only complete acquired cells, under the existing law. -/
def checkedHandoff (wasl : Bool) (es : List Entry) : Bool :=
  match handoff es with
  | none => false
  | some cells => (Law.machine wasl).final ((Law.machine wasl).run 0 cells)

theorem checkedHandoff_sound {wasl : Bool} {es : List Entry} (h : checkedHandoff wasl es = true) :
    ∃ cells, handoff es = some cells ∧ (Law.machine wasl).Licensed 0 cells ∧
      es ≠ [] ∧ (∀ e ∈ es, e.decision.status = .licensed) := by
  unfold checkedHandoff at h
  cases he : handoff es with
  | none => simp only [he, Bool.false_eq_true] at h
  | some cells =>
    simp only [he] at h
    have hc := handoff_complete he
    exact ⟨cells, rfl, h, hc.1, hc.2.1⟩

end Nabt.AlignedAcquisition
