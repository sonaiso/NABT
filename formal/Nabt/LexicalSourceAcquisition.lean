import Nabt.LexicalSurfaceBinding
import Nabt.OccurrenceSense

/-!
# Documentary acquisition from the complete supplied source bytes

This bridge computes a retained QAC row, its FORM and its unique nonempty LEM.
The caller supplies only a complete source value and byte intervals, not the
parsed labels or a certificate constructor. Successful acquisition reconstructs
the record exactly and builds the existing lexical witness from those fields.

The law is deliberately limited to CRLF-terminated, four-column STEM records
whose FORM belongs to LexicalSurfaceBinding's direct carrier/mark-pair domain.
It does not normalize other corpus spellings, authenticate an edition, prove a
corpus annotator correct, or determine the intended sense in a new context.
Hashing, filesystem/JSON transport and native execution remain stated adapter
premises. A declared source revision is an identity label, not a hash proof.
-/
namespace Nabt.LexicalSourceAcquisition

open LexicalSurfaceBinding

def lawId : String := "nabt.lexical-source-acquisition.v1"
def convention : String := "qac_source_annotation_v1"

structure Corpus where
  id : String
  revision : String
  bytes : List UInt8
  deriving DecidableEq, Repr

structure Span where
  startByte : Nat
  endByte : Nat
  deriving DecidableEq, Repr

structure Record where
  location : String
  form : String
  tag : String
  features : List String
  lemma : String
  cells : List Atom
  deriving DecidableEq, Repr

def Record.featuresText (record : Record) : String :=
  String.intercalate "|" record.features

def Record.render (record : Record) : String :=
  record.location ++ "\t" ++ record.form ++ "\t" ++ record.tag ++ "\t" ++
    record.featuresText ++ "\r\n"

def Record.lemmaStart (record : Record) : Nat :=
  let preceding := record.features.takeWhile (fun token => !token.startsWith "LEM:")
  let precedingText := record.location ++ "\t" ++ record.form ++ "\t" ++ record.tag ++ "\t" ++
    String.intercalate "|" preceding ++ (if preceding.isEmpty then "" else "|") ++ "LEM:"
  precedingText.utf8ByteSize

def Record.lemmaEnd (record : Record) : Nat :=
  record.lemmaStart + record.lemma.utf8ByteSize

def Record.LemmaExact (raw : String) (record : Record) : Prop :=
  record.lemmaStart < record.lemmaEnd ∧ record.lemmaEnd ≤ raw.utf8ByteSize ∧
  (raw.toUTF8.data.toList.drop record.lemmaStart).take
    (record.lemmaEnd - record.lemmaStart) = record.lemma.toUTF8.data.toList

instance (raw : String) (record : Record) : Decidable (record.LemmaExact raw) := by
  unfold Record.LemmaExact
  infer_instance

def plainField (text : String) : Prop :=
  text ≠ "" ∧ '\t' ∉ text.toList ∧ '\r' ∉ text.toList ∧ '\n' ∉ text.toList

instance (text : String) : Decidable (plainField text) := by
  unfold plainField
  infer_instance

/-- A source grammar independent of the parser's control flow. Literal record
reconstruction and a singleton LEM token are part of its observable contract. -/
def Record.Valid (raw : String) (record : Record) : Prop :=
  raw = record.render ∧
  plainField record.location ∧ plainField record.form ∧ plainField record.tag ∧
  (∀ token ∈ record.features, plainField token ∧ '|' ∉ token.toList) ∧
  record.features.head? = some "STEM" ∧
  OccurrenceSense.feature "POS" record.features = some (some record.tag) ∧
  OccurrenceSense.feature "LEM" record.features = some (some record.lemma) ∧
  record.features.filter (fun token => token.startsWith "LEM:") = ["LEM:" ++ record.lemma] ∧
  record.lemma ≠ "" ∧
  decodeForm record.form = some record.cells ∧ record.cells ≠ [] ∧ record.LemmaExact raw

instance (raw : String) (record : Record) : Decidable (record.Valid raw) := by
  unfold Record.Valid
  infer_instance

/-- A checked computation, not a constructor that can assert an arbitrary
proposition. It returns only a computed value satisfying a decidable contract. -/
private def enforce {α : Type} (p : α → Prop) [DecidablePred p]
    (candidate : Option α) : Option α :=
  match candidate with
  | none => none
  | some value => if p value then some value else none

private theorem enforce_sound {α : Type} (p : α → Prop) [DecidablePred p]
    (candidate : Option α) (value : α) (accepted : enforce p candidate = some value) :
    p value := by
  cases candidate with
  | none => simp [enforce] at accepted
  | some proposed =>
    by_cases valid : p proposed
    · have same : proposed = value := by simpa [enforce, valid] using accepted
      simpa [same] using valid
    · simp [enforce, valid] at accepted

def parseCandidate (raw : String) : Option Record := do
  let [location, form, tag, tail] := (raw.toList.splitOn '\t').map String.ofList | none
  -- Removal is accepted only when exact reconstruction subsequently proves
  -- that these were precisely the terminal CRLF bytes, not arbitrary trim.
  let featureText := String.ofList (tail.toList.take (tail.length - 2))
  let features := (featureText.toList.splitOn '|').map String.ofList
  let some lemma ← OccurrenceSense.feature "LEM" features | none
  let cells ← decodeForm form
  return ⟨location, form, tag, features, lemma, cells⟩

def parseRecord (raw : String) : Option Record :=
  enforce (Record.Valid raw) (parseCandidate raw)

theorem parsed_record_valid (raw : String) (record : Record)
    (parsed : parseRecord raw = some record) : record.Valid raw :=
  enforce_sound _ _ _ parsed

theorem parsed_record_reconstructs_source (raw : String) (record : Record)
    (parsed : parseRecord raw = some record) : raw = record.render :=
  (parsed_record_valid _ _ parsed).1

theorem parsed_lemma_unique_nonempty (raw : String) (record : Record)
    (parsed : parseRecord raw = some record) :
    record.features.filter (fun token => token.startsWith "LEM:") = ["LEM:" ++ record.lemma] ∧
    record.lemma ≠ "" := by
  have valid := parsed_record_valid _ _ parsed
  exact ⟨valid.2.2.2.2.2.2.2.2.1, valid.2.2.2.2.2.2.2.2.2.1⟩

theorem parsed_form_exact_nonempty (raw : String) (record : Record)
    (parsed : parseRecord raw = some record) :
    decodeForm record.form = some record.cells ∧ record.cells ≠ [] := by
  have valid := parsed_record_valid _ _ parsed
  exact ⟨valid.2.2.2.2.2.2.2.2.2.2.1, valid.2.2.2.2.2.2.2.2.2.2.2.1⟩

theorem parsed_lemma_source_span (raw : String) (record : Record)
    (parsed : parseRecord raw = some record) : record.LemmaExact raw :=
  (parsed_record_valid _ _ parsed).2.2.2.2.2.2.2.2.2.2.2.2

/-- This uses the existing codec theorem, not a second alphabet or induction. -/
theorem parsed_form_roundtrip (raw : String) (record : Record)
    (parsed : parseRecord raw = some record) : encodeForm record.cells = record.form :=
  encodeForm_decode _ _ (parsed_form_exact_nonempty _ _ parsed).1

structure Acquired where
  span : Span
  raw : String
  record : Record
  deriving DecidableEq, Repr

def Acquired.formStart (row : Acquired) : Nat := row.record.location.utf8ByteSize + 1
def Acquired.formEnd (row : Acquired) : Nat := row.formStart + row.record.form.utf8ByteSize

/-- The witness source remains the exact short row. The full-source interval is
retained separately in Acquired; its derived revision binds both coordinates.
No caller-supplied expression, FORM, reading label or proof flag is consumed. -/
def Acquired.witness (corpus : Corpus) (row : Acquired) : Witness :=
  { id := row.record.location
    binding := {
      source := {
        id := "qac:" ++ row.record.location
        revision := corpus.revision ++ ":" ++ toString row.span.startByte ++ ":" ++
          toString row.span.endByte
        text := row.raw }
      scopeId := corpus.revision
      occurrenceId := row.record.location
      readingId := row.record.lemma
      startByte := row.formStart
      endByte := row.formEnd
      surface := row.record.form }
    expression := row.record.lemma
    convention := convention }

def Acquired.Valid (corpus : Corpus) (requested : Span) (row : Acquired) : Prop :=
  row.span = requested ∧
  requested.startByte < requested.endByte ∧
  requested.endByte ≤ corpus.bytes.length ∧
  (requested.startByte = 0 ∨ corpus.bytes[requested.startByte - 1]? = some 10) ∧
  (corpus.bytes.drop requested.startByte).take (requested.endByte - requested.startByte) =
    row.raw.toUTF8.data.toList ∧
  parseRecord row.raw = some row.record ∧
  (row.witness corpus).binding.Exact

instance (corpus : Corpus) (span : Span) (row : Acquired) :
    Decidable (row.Valid corpus span) := by
  unfold Acquired.Valid
  infer_instance

def acquireCandidate (corpus : Corpus) (span : Span) : Option Acquired := do
  if span.startByte ≥ span.endByte || span.endByte > corpus.bytes.length then none
  else
    let bytes := (corpus.bytes.drop span.startByte).take (span.endByte - span.startByte)
    let raw ← String.fromUTF8? ⟨bytes.toArray⟩
    let record ← parseRecord raw
    return ⟨span, raw, record⟩

def acquireRow (corpus : Corpus) (span : Span) : Option Acquired :=
  enforce (Acquired.Valid corpus span) (acquireCandidate corpus span)

theorem acquired_row_valid (corpus : Corpus) (span : Span) (row : Acquired)
    (acquired : acquireRow corpus span = some row) : row.Valid corpus span :=
  enforce_sound _ _ _ acquired

theorem acquired_row_source_bytes (corpus : Corpus) (span : Span) (row : Acquired)
    (acquired : acquireRow corpus span = some row) :
    span.startByte < span.endByte ∧ span.endByte ≤ corpus.bytes.length ∧
    (corpus.bytes.drop span.startByte).take (span.endByte - span.startByte) =
      row.raw.toUTF8.data.toList := by
  have valid := acquired_row_valid _ _ _ acquired
  exact ⟨valid.2.1, valid.2.2.1, valid.2.2.2.2.1⟩

theorem acquired_record_from_source (corpus : Corpus) (span : Span) (row : Acquired)
    (acquired : acquireRow corpus span = some row) : parseRecord row.raw = some row.record :=
  (acquired_row_valid _ _ _ acquired).2.2.2.2.2.1

theorem acquired_lemma_is_unique (corpus : Corpus) (span : Span) (row : Acquired)
    (acquired : acquireRow corpus span = some row) :
    row.record.features.filter (fun token => token.startsWith "LEM:") =
      ["LEM:" ++ (row.witness corpus).expression] ∧ (row.witness corpus).expression ≠ "" :=
  parsed_lemma_unique_nonempty _ _ (acquired_record_from_source _ _ _ acquired)

theorem acquired_lemma_source_span (corpus : Corpus) (span : Span) (row : Acquired)
    (acquired : acquireRow corpus span = some row) : row.record.LemmaExact row.raw :=
  parsed_lemma_source_span _ _ (acquired_record_from_source _ _ _ acquired)

theorem acquired_witness_form_bound (corpus : Corpus) (span : Span) (row : Acquired)
    (acquired : acquireRow corpus span = some row) :
    (row.witness corpus).binding.Exact ∧
    (row.witness corpus).binding.surface = row.record.form ∧
    (row.witness corpus).expression = row.record.lemma :=
  ⟨(acquired_row_valid _ _ _ acquired).2.2.2.2.2.2, rfl, rfl⟩

theorem acquired_witness_cells (corpus : Corpus) (span : Span) (row : Acquired)
    (acquired : acquireRow corpus span = some row) :
    (row.witness corpus).decoded = some row.record.cells ∧ row.record.cells ≠ [] :=
  parsed_form_exact_nonempty _ _ (acquired_record_from_source _ _ _ acquired)

/-- Composition with the existing surface law retains the actual source row
and the actual observed occurrence; neither a label nor the numerical encoding
alone establishes the contextual meaning of that occurrence. -/
theorem acquired_surface_match_retains_source (corpus : Corpus) (span : Span)
    (row : Acquired) (source : Foundation.Source) (frame : LinguisticTruth.Frame)
    (surface : String) (ledger : List Witness)
    (acquired : acquireRow corpus span = some row)
    (matched : checkWitness source frame surface ledger (row.witness corpus) = true) :
    (corpus.bytes.drop span.startByte).take (span.endByte - span.startByte) =
      row.raw.toUTF8.data.toList ∧
    (occurrenceBinding source frame surface).Exact ∧
    surface = renderArabic (row.witness corpus).cells :=
  ⟨(acquired_row_source_bytes _ _ _ acquired).2.2,
    checked_occurrence_exact _ _ _ _ _ matched,
    checked_surface_exact _ _ _ _ _ matched⟩

/-- Batch acquisition is all-or-nothing and preserves every requested row in
order. It never silently filters invalid records or collapses homographs. -/
def acquireMany (corpus : Corpus) : List Span → Option (List Acquired)
  | [] => some []
  | span :: tail => do
      let row ← acquireRow corpus span
      let rest ← acquireMany corpus tail
      return row :: rest

def acquireRows (corpus : Corpus) (spans : List Span) : Option (List Acquired) :=
  if spans ≠ [] ∧ spans.Nodup then acquireMany corpus spans else none

theorem acquireMany_length (corpus : Corpus) (spans : List Span) (rows : List Acquired)
    (accepted : acquireMany corpus spans = some rows) : rows.length = spans.length := by
  induction spans generalizing rows with
  | nil =>
    have same : rows = [] := by simpa [acquireMany] using accepted.symm
    simp [same]
  | cons span tail ih =>
    cases first : acquireRow corpus span with
    | none => simp [acquireMany, first] at accepted
    | some row =>
      cases rest : acquireMany corpus tail with
      | none => simp [acquireMany, first, rest] at accepted
      | some remaining =>
        have same : row :: remaining = rows := by
          simpa [acquireMany, first, rest] using accepted
        rw [← same]
        simpa using congrArg Nat.succ (ih remaining rest)

theorem acquireMany_each (corpus : Corpus) (spans : List Span) (rows : List Acquired)
    (accepted : acquireMany corpus spans = some rows) :
    ∀ row ∈ rows, ∃ span ∈ spans, acquireRow corpus span = some row := by
  induction spans generalizing rows with
  | nil =>
    have same : rows = [] := by simpa [acquireMany] using accepted.symm
    simp [same]
  | cons span tail ih =>
    cases first : acquireRow corpus span with
    | none => simp [acquireMany, first] at accepted
    | some row =>
      cases rest : acquireMany corpus tail with
      | none => simp [acquireMany, first, rest] at accepted
      | some remaining =>
        have same : row :: remaining = rows := by
          simpa [acquireMany, first, rest] using accepted
        rw [← same]
        intro value member
        cases member with
        | head => exact ⟨span, List.mem_cons_self, first⟩
        | tail _ later =>
          obtain ⟨chosen, present, checked⟩ := ih remaining rest value later
          exact ⟨chosen, List.mem_cons_of_mem _ present, checked⟩

theorem acquireMany_preserves_positions (corpus : Corpus) (spans : List Span)
    (rows : List Acquired) (accepted : acquireMany corpus spans = some rows) :
    rows.map Acquired.span = spans := by
  induction spans generalizing rows with
  | nil =>
    have same : rows = [] := by simpa [acquireMany] using accepted.symm
    simp [same]
  | cons span tail ih =>
    cases first : acquireRow corpus span with
    | none => simp [acquireMany, first] at accepted
    | some row =>
      cases rest : acquireMany corpus tail with
      | none => simp [acquireMany, first, rest] at accepted
      | some remaining =>
        have same : row :: remaining = rows := by
          simpa [acquireMany, first, rest] using accepted
        rw [← same]
        simp only [List.map_cons, (acquired_row_valid _ _ _ first).1, ih remaining rest]

theorem acquired_batch_complete (corpus : Corpus) (spans : List Span) (rows : List Acquired)
    (accepted : acquireRows corpus spans = some rows) :
    spans ≠ [] ∧ spans.Nodup ∧ rows.length = spans.length ∧
    ∀ row ∈ rows, ∃ span ∈ spans, row.Valid corpus span := by
  by_cases valid : spans ≠ [] ∧ spans.Nodup
  · have checked : acquireMany corpus spans = some rows := by
      simpa [acquireRows, valid] using accepted
    refine ⟨valid.1, valid.2, acquireMany_length _ _ _ checked, ?_⟩
    intro row member
    obtain ⟨span, present, acquired⟩ := acquireMany_each _ _ _ checked row member
    exact ⟨span, present, acquired_row_valid _ _ _ acquired⟩
  · simp [acquireRows, valid] at accepted

theorem empty_batch_rejected (corpus : Corpus) : acquireRows corpus [] = none := by
  simp [acquireRows]

theorem acquired_batch_preserves_positions (corpus : Corpus) (spans : List Span)
    (rows : List Acquired) (accepted : acquireRows corpus spans = some rows) :
    rows.map Acquired.span = spans := by
  by_cases valid : spans ≠ [] ∧ spans.Nodup
  · apply acquireMany_preserves_positions
    simpa [acquireRows, valid] using accepted
  · simp [acquireRows, valid] at accepted

theorem acquired_batch_nonempty (corpus : Corpus) (spans : List Span) (rows : List Acquired)
    (accepted : acquireRows corpus spans = some rows) : rows ≠ [] := by
  have valid := acquired_batch_complete _ _ _ accepted
  intro empty
  have zero : spans.length = 0 := by simpa [empty] using valid.2.2.1.symm
  cases spans with
  | nil => exact valid.1 rfl
  | cons span tail => simp at zero

end Nabt.LexicalSourceAcquisition
