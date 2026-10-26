import Nabt.Foundation

/-!
Exact, bounded discourse envelopes acquired from the source string itself.
The accepted surface grammar is deliberately explicit: a reported quotation
`قَالَ label: «body»`, `لَيْسَ صَحِيحًا أَنِّي body`, or
`إِنْ قُلْتُ body فَلَا tail`, optionally followed by one full stop.
The opaque body is not parsed as an Arabic proposition by this module. The
source-bound envelope, its byte interval, and the prohibition on projecting
its body into the narrator's assertions are the precise checked claims.
The quote label is a textual label, never an authenticated person/reference.
-/
namespace Nabt.ScopeAcquisition

def lawId : String := "nabt.scope-acquisition.v1"

inductive Kind where
  | quoted | negated | hypothetical
  deriving DecidableEq, Repr

structure Envelope where
  kind : Kind
  speaker : String
  body : String
  tail : String
  fullStop : Bool
  deriving DecidableEq, Repr

def Envelope.prefix (e : Envelope) : String := match e.kind with
  | .quoted => "قَالَ " ++ e.speaker ++ ": «"
  | .negated => "لَيْسَ صَحِيحًا أَنِّي "
  | .hypothetical => "إِنْ قُلْتُ "

def Envelope.suffix (e : Envelope) : String :=
  (match e.kind with
    | .quoted => "»"
    | .negated => ""
    | .hypothetical => " فَلَا " ++ e.tail) ++ (if e.fullStop then "." else "")

def Envelope.render (e : Envelope) : String := e.prefix ++ e.body ++ e.suffix
def Envelope.startByte (e : Envelope) : Nat := e.prefix.utf8ByteSize
def Envelope.endByte (e : Envelope) : Nat := e.startByte + e.body.utf8ByteSize

/-- A bounded opaque segment. Nested delimiters and another sentence are not
silently stripped. Uncovered nested syntax must use a later licensed grammar. -/
def plain (s : String) : Prop := s ≠ "" ∧
  s.toList.head? ≠ some ' ' ∧ s.toList.getLast? ≠ some ' ' ∧
  (∀ c ∈ s.toList, c.toNat ≥ 32 ∧ c ∉ "«»\"“”‘’'`()[]{}:؛;.!?؟،,".toList)
instance (s : String) : Decidable (plain s) := by unfold plain; infer_instance

/-- Structural character recursion avoids opaque byte-search shortcuts and
keeps the parser's finite examples reducible by the kernel. -/
private def splitFirst (sep : List Char) : List Char → Option (List Char × List Char)
  | [] => none
  | c :: rest =>
      if sep.isPrefixOf (c :: rest) then some ([], (c :: rest).drop sep.length)
      else match splitFirst sep rest with
        | none => none
        | some (left, right) => some (c :: left, right)

private def splitOnce (raw sep : String) : Option (String × String) := do
  let (left, right) ← splitFirst sep.toList raw.toList
  if (splitFirst sep.toList right).isSome then none
  else some (String.ofList left, String.ofList right)

def Envelope.Shape (e : Envelope) : Prop :=
  plain e.body ∧
  match e.kind with
  | .quoted => plain e.speaker ∧ ' ' ∉ e.speaker.toList ∧ e.tail = ""
  | .negated => e.speaker = "" ∧ e.tail = ""
  | .hypothetical => e.speaker = "" ∧ plain e.tail ∧
      splitFirst " فَلَا ".toList e.body.toList = none
instance (e : Envelope) : Decidable e.Shape := by
  unfold Envelope.Shape
  cases e.kind <;> infer_instance

def Envelope.Exact (source : Foundation.Source) (e : Envelope) : Prop :=
  source.text = e.render ∧ e.Shape ∧
  e.startByte < e.endByte ∧ e.endByte ≤ source.text.utf8ByteSize ∧
  (source.text.toUTF8.data.toList.drop e.startByte).take (e.endByte - e.startByte) =
    e.body.toUTF8.data.toList ∧ (Foundation.project source).status ≠ .invalid
instance (source : Foundation.Source) (e : Envelope) : Decidable (e.Exact source) := by
  unfold Envelope.Exact; infer_instance

private def removePrefix (leading raw : String) : Option String :=
  if raw.startsWith leading then some (String.ofList (raw.toList.drop leading.length)) else none

def candidate (raw : String) : Option Envelope := do
  let fullStop := raw.endsWith "."
  let core := if fullStop then String.ofList (raw.toList.take (raw.length - 1)) else raw
  if core.startsWith "قَالَ " then
    let remainder ← removePrefix "قَالَ " core
    let (speaker, quoted) ← splitOnce remainder ": «"
    if !quoted.endsWith "»" then none else
      some ⟨.quoted, speaker, String.ofList (quoted.toList.take (quoted.length - 1)), "", fullStop⟩
  else if core.startsWith "لَيْسَ صَحِيحًا أَنِّي " then
    let body ← removePrefix "لَيْسَ صَحِيحًا أَنِّي " core
    some ⟨.negated, "", body, "", fullStop⟩
  else if core.startsWith "إِنْ قُلْتُ " then
    let remainder ← removePrefix "إِنْ قُلْتُ " core
    let (body, tail) ← splitOnce remainder " فَلَا "
    some ⟨.hypothetical, "", body, tail, fullStop⟩
  else none

def acquire (source : Foundation.Source) : Option Envelope :=
  match candidate source.text with
  | none => none
  | some e => if e.Exact source then some e else none

theorem acquired_exact (source : Foundation.Source) (e : Envelope)
    (h : acquire source = some e) : e.Exact source := by
  unfold acquire at h
  cases hc : candidate source.text with
  | none => simp [hc] at h
  | some proposed =>
      by_cases hv : proposed.Exact source
      · have same : proposed = e := by simpa [hc, hv] using h
        simpa [same] using hv
      · simp [hc, hv] at h

theorem acquired_restores_source (source : Foundation.Source) (e : Envelope)
    (h : acquire source = some e) : source.text = e.render := (acquired_exact _ _ h).1

theorem acquired_nonempty_byte_interval (source : Foundation.Source) (e : Envelope)
    (h : acquire source = some e) :
    e.startByte < e.endByte ∧ e.endByte ≤ source.text.utf8ByteSize :=
  ⟨(acquired_exact _ _ h).2.2.1, (acquired_exact _ _ h).2.2.2.1⟩

theorem acquired_exact_body_bytes (source : Foundation.Source) (e : Envelope)
    (h : acquire source = some e) :
    (source.text.toUTF8.data.toList.drop e.startByte).take (e.endByte - e.startByte) =
      e.body.toUTF8.data.toList := (acquired_exact _ _ h).2.2.2.2.1

theorem acquired_valid_marks (source : Foundation.Source) (e : Envelope)
    (h : acquire source = some e) : (Foundation.project source).status ≠ .invalid :=
  (acquired_exact _ _ h).2.2.2.2.2

/-- The extracted scope is not a proposition of the narrator. A downstream
calculus may retain it under quotation/negation/condition but cannot use this
envelope as a license for an unqualified positive premise. -/
def Envelope.projectsToNarrator (_e : Envelope) : Bool := false

theorem no_unqualified_projection (source : Foundation.Source) (e : Envelope)
    (_h : acquire source = some e) : e.projectsToNarrator = false := rfl

def Envelope.bodySource (source : Foundation.Source) (e : Envelope) : Foundation.Source :=
  ⟨source.id ++ ":body:" ++ toString e.startByte, source.revision, e.body⟩

theorem body_number_uses_foundation (source : Foundation.Source) (e : Envelope) :
    Sequence.decode (Foundation.project (e.bodySource source)).number =
      (Foundation.project (e.bodySource source)).cells := Foundation.number_restores_cells _

theorem quote_label_retained (source : Foundation.Source) (e : Envelope)
    (h : acquire source = some e) (quoted : e.kind = .quoted) :
    source.text = "قَالَ " ++ e.speaker ++ ": «" ++ e.body ++ "»" ++
      (if e.fullStop then "." else "") := by
  simpa [Envelope.render, Envelope.prefix, Envelope.suffix, quoted, String.append_assoc]
    using acquired_restores_source source e h

theorem acquired_body_nonempty (source : Foundation.Source) (e : Envelope)
    (h : acquire source = some e) : e.body ≠ "" := (acquired_exact _ _ h).2.1.1.1

end Nabt.ScopeAcquisition
