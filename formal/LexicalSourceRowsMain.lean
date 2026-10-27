import Nabt.LexicalSourceAcquisition
import ProbeJson

/-! One bounded request carries the complete supplied corpus once. Each response
retains only the requested source rows and their derived witnesses. Filesystem
identity, SHA-256 validation and transport refinement remain adapter premises;
the pure acquisition law checks the actual bytes supplied to it. -/
open Lean ProbeJson Nabt.LexicalSourceAcquisition

namespace LexicalSourceRowsMain

def maxRequestBytes : Nat := 16777216
def maxSourceBytes : Nat := 8388608
def maxRows : Nat := 128

def exact (j : Json) (names : List String) : ProbeM Unit := do
  let entries ← liftParse j.getObj?
  if entries.size != names.length || names.any (fun name => (entries.get? name).isNone) then
    invalid "object fields do not match the versioned schema"

def label (j : Json) : ProbeM String := do
  let value ← str j
  if value.isEmpty then invalid "identity must be nonempty"
  else if value.utf8ByteSize > 1024 then limited "identity exceeds byte budget"
  else return value

def corpus (j : Json) : ProbeM Corpus := do
  exact j ["id", "revision", "text"]
  let id ← label (← field j "id")
  let revision ← label (← field j "revision")
  let text ← str (← field j "text")
  if text.utf8ByteSize > maxSourceBytes then limited "complete source exceeds 8 MiB"
  else return ⟨id, revision, text.toUTF8.data.toList⟩

def span (j : Json) : ProbeM Span := do
  exact j ["start_byte", "end_byte"]
  return ⟨← nat (← field j "start_byte"), ← nat (← field j "end_byte")⟩

def sourceJson (source : Nabt.Foundation.Source) : Json := Json.mkObj [
  ("id", toJson source.id), ("revision", toJson source.revision), ("text", toJson source.text)]

def witnessJson (witness : Nabt.LexicalSurfaceBinding.Witness) : Json :=
  let b := witness.binding
  Json.mkObj [
    ("id", toJson witness.id),
    ("binding", Json.mkObj [
      ("source", sourceJson b.source), ("scope_id", toJson b.scopeId),
      ("occurrence_id", toJson b.occurrenceId), ("reading_id", toJson b.readingId),
      ("start_byte", toJson b.startByte), ("end_byte", toJson b.endByte),
      ("surface", toJson b.surface)]),
    ("expression", toJson witness.expression), ("convention", toJson witness.convention)]

def rowJson (source : Corpus) (row : Acquired) : Json := Json.mkObj [
  ("start_byte", toJson row.span.startByte), ("end_byte", toJson row.span.endByte),
  ("raw_line", toJson row.raw), ("location", toJson row.record.location),
  ("form", toJson row.record.form), ("tag", toJson row.record.tag),
  ("lemma", toJson row.record.lemma),
  ("form_start_byte", toJson row.formStart), ("form_end_byte", toJson row.formEnd),
  ("lemma_start_byte", toJson row.record.lemmaStart),
  ("lemma_end_byte", toJson row.record.lemmaEnd),
  ("witness", witnessJson (row.witness source))]

def envelope (fields : List (String × Json)) : Json := Json.mkObj (
  [("schema", toJson "nabt.lexical-source-rows.v1"), ("law_id", toJson lawId),
   ("source_authenticity_established", toJson false),
   ("intended_sense_established", toJson false)] ++ fields)

def dispatch (j : Json) : ProbeM Json := do
  exact j ["source", "row_spans"]
  let source ← corpus (← field j "source")
  let rawSpans ← liftParse (← field j "row_spans").getArr?
  if rawSpans.size > maxRows then return ← limited "row inventory exceeds 128 spans"
  let spans ← rawSpans.toList.mapM span
  if spans.isEmpty then return ← invalid "row inventory must be nonempty"
  if spans.eraseDups.length != spans.length then
    return ← invalid "repeated source intervals do not supply independent rows"
  if spans.any (fun s => s.endByte - s.startByte > 65536) then
    return ← limited "a requested source row exceeds 64 KiB"
  let some rows := acquireRows source spans |
    return ← invalid "a requested row is not an exact licensed source record"
  return envelope [
    ("source_id", toJson source.id), ("source_revision", toJson source.revision),
    ("source_bytes", toJson source.bytes.length), ("row_count", toJson rows.length),
    ("rows", toJson (rows.map (rowJson source)))]

def failure (error : Failure) : Json := envelope [
  ("error", toJson error.code), ("message", toJson error.message)]

def process (bytes : ByteArray) : Json :=
  match String.fromUTF8? bytes with
  | none => failure ⟨"INVALID_INPUT", "request is not valid UTF-8"⟩
  | some line =>
    match (do
      preflight line
      dispatch (← liftParse (Json.parse line)) : ProbeM Json) with
    | .ok result => result
    | .error error => failure error

/-- Unlike the shared 1 MiB JSONL adapter this dedicated exporter consumes one
request through EOF. The bound is enforced while reading, before JSON parsing. -/
def readRequest (input : IO.FS.Stream) : IO (Except Failure ByteArray) := do
  let mut pending := ByteArray.emptyWithCapacity 0
  let mut finished := false
  while !finished do
    let chunk ← input.read 65536
    if chunk.isEmpty then finished := true
    else if pending.size + chunk.size > maxRequestBytes then
      return .error ⟨"RESOURCE_LIMIT", "request exceeds 16 MiB"⟩
    else pending := pending ++ chunk
  return .ok pending

end LexicalSourceRowsMain

def main : IO UInt32 := do
  let output ← IO.getStdout
  try
    let result ← LexicalSourceRowsMain.readRequest (← IO.getStdin)
    let response := match result with
      | .ok bytes => LexicalSourceRowsMain.process bytes
      | .error error => LexicalSourceRowsMain.failure error
    output.putStrLn response.compress
    return if (response.getObjVal? "error").isOk then 2 else 0
  catch error =>
    output.putStrLn (LexicalSourceRowsMain.failure ⟨"IO_ERROR", error.toString⟩).compress
    return 2
