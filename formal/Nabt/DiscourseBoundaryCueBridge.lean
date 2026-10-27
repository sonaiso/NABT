import Nabt.ScopeAcquisition

/-!
An exact editorial discourse grammar, not a parser for all Arabic negation.
It recognizes a raw `لم ...؛ وأقصد ...` envelope (with either of the two
declared spellings of each marker and an optional final period). The denied
segment and the following first-person cue remain opaque. The conjunction is
retained, not erased. Completeness below is with respect to `Envelope.Exact`,
which is independent of the parser and includes the source/byte/mark bounds.
No word-sense alias, speaker authentication, or external event is established.
-/
namespace Nabt.DiscourseBoundaryCueBridge

def lawId : String := "nabt.discourse-boundary-cue.v1"

def negativePrefix (marked : Bool) : List Char :=
  (if marked then "لَمْ " else "لم ").toList
def conjunction (marked : Bool) : List Char :=
  (if marked then "وَ" else "و").toList
def cuePrefix (marked : Bool) : List Char :=
  (if marked then "أَقْصِدُ " else "أقصد ").toList
def cueLeading (marked : Bool) : List Char := ' ' :: (conjunction marked ++ cuePrefix marked)

structure Envelope where
  markedNegative : Bool
  markedCue : Bool
  denied : List Char
  cueBody : List Char
  fullStop : Bool
  deriving DecidableEq, Repr

def Envelope.cue (e : Envelope) : List Char := cuePrefix e.markedCue ++ e.cueBody
def Envelope.core (e : Envelope) : List Char :=
  (negativePrefix e.markedNegative ++ e.denied) ++
    ('؛' :: (cueLeading e.markedCue ++ e.cueBody))
def Envelope.renderChars (e : Envelope) : List Char :=
  e.core ++ (if e.fullStop then ['.'] else [])
def Envelope.render (e : Envelope) : String := String.ofList e.renderChars
def Envelope.deniedText (e : Envelope) : String := String.ofList e.denied
def Envelope.cueText (e : Envelope) : String := String.ofList e.cue
def Envelope.deniedStart (e : Envelope) : Nat :=
  (String.ofList (negativePrefix e.markedNegative)).utf8ByteSize
def Envelope.deniedEnd (e : Envelope) : Nat := e.deniedStart + e.deniedText.utf8ByteSize
def Envelope.cueStart (e : Envelope) : Nat :=
  (String.ofList ((negativePrefix e.markedNegative ++ e.denied) ++
    ['؛', ' '] ++ conjunction e.markedCue)).utf8ByteSize
def Envelope.cueEnd (e : Envelope) : Nat := e.cueStart + e.cueText.utf8ByteSize

def Envelope.Shape (e : Envelope) : Prop :=
  ScopeAcquisition.plain e.deniedText ∧ ScopeAcquisition.plain (String.ofList e.cueBody)
instance (e : Envelope) : Decidable e.Shape := by unfold Envelope.Shape; infer_instance

/-- Source restoration and byte witnesses are checked in addition to syntax.
Partial A116 projection is retained; only malformed marks are rejected. -/
def Envelope.Exact (source : Foundation.Source) (e : Envelope) : Prop :=
  source.text.toList = e.renderChars ∧ e.Shape ∧
  e.deniedStart < e.deniedEnd ∧ e.deniedEnd < e.cueStart ∧
  e.cueStart < e.cueEnd ∧ e.cueEnd ≤ source.text.utf8ByteSize ∧
  (source.text.toUTF8.data.toList.drop e.deniedStart).take (e.deniedEnd - e.deniedStart) =
    e.deniedText.toUTF8.data.toList ∧
  (source.text.toUTF8.data.toList.drop e.cueStart).take (e.cueEnd - e.cueStart) =
    e.cueText.toUTF8.data.toList ∧
  (Foundation.project source).status ≠ .invalid
instance (source : Foundation.Source) (e : Envelope) : Decidable (e.Exact source) := by
  unfold Envelope.Exact; infer_instance

private def splitBoundary : List Char → Option (List Char × List Char)
  | [] => none
  | c :: cs =>
      if c = '؛' then some ([], cs)
      else match splitBoundary cs with
        | none => none
        | some (left, right) => some (c :: left, right)

private theorem split_boundary_append (left right : List Char) (h : '؛' ∉ left) :
    splitBoundary (left ++ '؛' :: right) = some (left, right) := by
  induction left with
  | nil => simp [splitBoundary]
  | cons c cs ih =>
      have hc : c ≠ '؛' := by intro hc; simp [hc] at h
      have hs : '؛' ∉ cs := by intro hs; exact h (List.mem_cons_of_mem c hs)
      simp [splitBoundary, hc, ih hs]

private def candidateFor (negative cue stop : Bool) (raw : List Char) : Option Envelope := do
  let core := if stop then raw.dropLast else raw
  let (left, right) ← splitBoundary core
  return ⟨negative, cue, left.drop (negativePrefix negative).length,
    right.drop (cueLeading cue).length, stop⟩

private def profiles : List (Bool × Bool × Bool) :=
  [false, true].flatMap fun n => [false, true].flatMap fun c =>
    [false, true].map fun f => (n, c, f)

private def candidates (source : Foundation.Source) : List Envelope :=
  profiles.filterMap fun (n, c, f) => candidateFor n c f source.text.toList

def readings (source : Foundation.Source) : List Envelope :=
  (candidates source).filter fun e => decide (e.Exact source)

def acquire (source : Foundation.Source) : Option Envelope := (readings source).head?

private theorem shape_no_boundary (e : Envelope) (h : e.Shape) :
    '؛' ∉ negativePrefix e.markedNegative ++ e.denied := by
  have hd : '؛' ∉ e.denied := by
    intro hm
    have hf := h.1.2.2.2 '؛' (by simpa [Envelope.deniedText] using hm)
    have : '؛' ∈ "«»\"“”‘’'`()[]{}:؛;.!?؟،,".toList := by decide
    exact hf.2 this
  have hn : '؛' ∉ negativePrefix e.markedNegative := by
    cases e.markedNegative <;> decide
  simpa only [List.mem_append, not_or] using And.intro hn hd

private theorem candidate_render (e : Envelope) (h : e.Shape) :
    candidateFor e.markedNegative e.markedCue e.fullStop e.renderChars = some e := by
  have hc : (if e.fullStop then e.renderChars.dropLast else e.renderChars) = e.core := by
    cases hf : e.fullStop
    · simp only [Envelope.renderChars, hf, Bool.false_eq_true, ↓reduceIte, List.append_nil]
    · simp only [Envelope.renderChars, hf, ↓reduceIte, List.dropLast_append_cons,
        List.dropLast_singleton, List.append_nil]
  have hb := split_boundary_append (negativePrefix e.markedNegative ++ e.denied)
    (cueLeading e.markedCue ++ e.cueBody) (shape_no_boundary e h)
  simp only [candidateFor, hc, Envelope.core, hb]
  change some { e with
    denied := (negativePrefix e.markedNegative ++ e.denied).drop (negativePrefix e.markedNegative).length
    cueBody := (cueLeading e.markedCue ++ e.cueBody).drop (cueLeading e.markedCue).length } = some e
  simp only [List.drop_left]

theorem readings_sound (source : Foundation.Source) (e : Envelope)
    (h : e ∈ readings source) : e.Exact source := by
  have hf := List.mem_filter.mp h
  exact of_decide_eq_true hf.2

/-- Every envelope satisfying the source relation is enumerated. This law is
not conditional on a parser success and does not quantify over an empty list. -/
theorem readings_complete (source : Foundation.Source) (e : Envelope)
    (h : e.Exact source) : e ∈ readings source := by
  apply List.mem_filter.mpr
  refine ⟨?_, decide_eq_true h⟩
  apply List.mem_filterMap.mpr
  refine ⟨(e.markedNegative, e.markedCue, e.fullStop), ?_, ?_⟩
  · cases e.markedNegative <;> cases e.markedCue <;> cases e.fullStop <;> simp [profiles]
  · rw [h.1]
    exact candidate_render e h.2.1

theorem acquired_exact (source : Foundation.Source) (e : Envelope)
    (h : acquire source = some e) : e.Exact source := by
  exact readings_sound source e (List.mem_of_head? h)

theorem exact_has_acquisition (source : Foundation.Source) (e : Envelope)
    (h : e.Exact source) : ∃ result, acquire source = some result := by
  have hm := readings_complete source e h
  cases hr : readings source with
  | nil => simp [hr] at hm
  | cons first rest => exact ⟨first, by simp [acquire, hr]⟩

theorem acquired_restores_source (source : Foundation.Source) (e : Envelope)
    (h : acquire source = some e) : source.text = e.render := by
  have hs := congrArg String.ofList (acquired_exact source e h).1
  simpa [Envelope.render] using hs

theorem acquired_retains_conjunction (source : Foundation.Source) (e : Envelope)
    (h : acquire source = some e) :
    source.text.toList = (negativePrefix e.markedNegative ++ e.denied) ++
      ['؛', ' '] ++ conjunction e.markedCue ++ e.cue ++
      (if e.fullStop then ['.'] else []) := by
  simpa [Envelope.renderChars, Envelope.core, Envelope.cue, cueLeading, List.append_assoc]
    using (acquired_exact source e h).1

theorem acquired_disjoint_spans (source : Foundation.Source) (e : Envelope)
    (h : acquire source = some e) :
    e.deniedStart < e.deniedEnd ∧ e.deniedEnd < e.cueStart ∧
      e.cueStart < e.cueEnd ∧ e.cueEnd ≤ source.text.utf8ByteSize := by
  have hs := (acquired_exact source e h).2.2
  exact ⟨hs.1, hs.2.1, hs.2.2.1, hs.2.2.2.1⟩

theorem acquired_exact_denied_bytes (source : Foundation.Source) (e : Envelope)
    (h : acquire source = some e) :
    (source.text.toUTF8.data.toList.drop e.deniedStart).take (e.deniedEnd - e.deniedStart) =
      e.deniedText.toUTF8.data.toList := (acquired_exact source e h).2.2.2.2.2.2.1

theorem acquired_exact_cue_bytes (source : Foundation.Source) (e : Envelope)
    (h : acquire source = some e) :
    (source.text.toUTF8.data.toList.drop e.cueStart).take (e.cueEnd - e.cueStart) =
      e.cueText.toUTF8.data.toList := (acquired_exact source e h).2.2.2.2.2.2.2.1

theorem acquired_valid_marks (source : Foundation.Source) (e : Envelope)
    (h : acquire source = some e) : (Foundation.project source).status ≠ .invalid :=
  (acquired_exact source e h).2.2.2.2.2.2.2.2

def Envelope.cueSource (source : Foundation.Source) (e : Envelope) : Foundation.Source :=
  ⟨source.id ++ ":cue:" ++ toString e.cueStart, source.revision, e.cueText⟩

theorem cue_number_uses_foundation (source : Foundation.Source) (e : Envelope) :
    Sequence.decode (Foundation.project (e.cueSource source)).number =
      (Foundation.project (e.cueSource source)).cells := Foundation.number_restores_cells _

end Nabt.DiscourseBoundaryCueBridge
