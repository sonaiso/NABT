import Nabt.ProductiveClauseV1
import ProbeJson

open Lean ProbeJson Nabt.ProductiveClauseV1
namespace ProductiveClauseV1Main

/- Transport validation follows AcquiredSyntaxV3Main without altering the
historical executable. JSON decoding and OS I/O remain explicit test boundaries.
The native parser derives roles from the original text, not supplied fields. -/
def uniqueObjectKeys (text : String) : ProbeM Unit := do
  let mut stack : List (Option (List String)) := []
  let mut quoted := false
  let mut escaped := false
  let mut token : List Char := []
  let mut lastString : Option String := none
  for ch in text.toList do
    if quoted then
      token := ch :: token
      if escaped then escaped := false
      else if ch == '\\' then escaped := true
      else if ch == '"' then
        quoted := false
        lastString := some (String.ofList token.reverse)
        token := []
    else if ch == '"' then
      quoted := true
      token := ['"']
      lastString := none
    else if ch == ':' then
      match stack, lastString with
      | some names :: rest, some encoded =>
        if names.length >= 16 then return ← limited "JSON object exceeds 16 fields"
        let key ← str (← liftParse (Json.parse encoded))
        if names.contains key then return ← ProbeJson.invalid "duplicate JSON object key"
        stack := some (key :: names) :: rest
      | _, _ => pure ()
      lastString := none
    else if ch == '{' then
      stack := some [] :: stack
      lastString := none
    else if ch == '[' then
      stack := none :: stack
      lastString := none
    else if ch == '}' || ch == ']' then
      stack := stack.tail
      lastString := none
    else if !(ch == ' ' || ch == '\t' || ch == '\r' || ch == '\n') then
      lastString := none

def keys (j : Json) (names : List String) : ProbeM Unit := do
  let entries ← liftParse j.getObj?
  if entries.size != names.length || names.any (fun n => (entries.get? n).isNone) then
    ProbeJson.invalid "object fields do not match the versioned schema"
  else pure ()

def metadata (j : Json) : ProbeM String := do
  let s ← str j
  if s.isEmpty || s.length > 512 ||
      s.toList.any (fun c => c.toNat < 32 || (127 ≤ c.toNat && c.toNat ≤ 159)) then
    ProbeJson.invalid "identity must be nonempty, at most 512 scalars, and contain no C0/C1 controls"
  else return s

def request (j : Json) : ProbeM Request := do
  keys j ["text", "source_id", "revision", "scope", "ending", "onset"]
  let text ← str (← field j "text")
  if text.toUTF8.size > 8192 || text.length > 4096 then
    return ← limited "source exceeds syntax budget"
  let sourceId ← metadata (← field j "source_id")
  let revision ← metadata (← field j "revision")
  let scope ← metadata (← field j "scope")
  let ending ← str (← field j "ending")
  if ending != "wasl" && ending != "waqf" then return ← ProbeJson.invalid "unknown ending"
  let onset ← str (← field j "onset")
  if onset != "word_initial" && onset != "connected" then return ← ProbeJson.invalid "unknown onset"
  return ⟨text, sourceId, revision, scope, ending, onset⟩

open Nabt.AlignedAcquisition (Span)
def spanJson (s : Span) : Json := Json.mkObj [
  ("start", toJson s.start), ("end", toJson s.stop),
  ("byte_start", toJson s.byteStart), ("byte_end", toJson s.byteStop),
  ("raw", toJson (String.ofList s.raw))]

def tokenJson (s : Span) : Json :=
  let lexeme := readLexeme (String.ofList s.raw)
  Json.mkObj [
    ("start", toJson s.start), ("end", toJson s.stop),
    ("byte_start", toJson s.byteStart), ("byte_end", toJson s.byteStop),
    ("raw", toJson (String.ofList s.raw)),
    ("lexeme", toJson (lexeme.map Lexeme.label)),
    ("category", toJson (lexeme.map Lexeme.category)),
    ("nominal_case", toJson (lexeme.bind Lexeme.nominalCase))]

def readingJson (f : Frame) (tokens : List Span) : Json :=
  let v := tokens[0]?.getD ⟨0, 0, []⟩
  let s := tokens[f.subjectIndex]?.getD ⟨0, 0, []⟩
  let o := tokens[f.objectIndex]?.getD ⟨0, 0, []⟩
  Json.mkObj [
    ("verb_index", toJson (0 : Nat)), ("subject_index", toJson f.subjectIndex),
    ("object_index", toJson f.objectIndex),
    ("verb_lexeme", toJson "DARABA"), ("subject_lexeme", toJson f.subject.label),
    ("object_lexeme", toJson f.object.label), ("order", toJson f.order.label),
    ("tense", toJson "past"), ("voice", toJson "active"),
    ("subject_case", toJson "nom"), ("object_case", toJson "acc"),
    ("source_words", toJson (tokens.map tokenJson)),
    ("verb_source", tokenJson v), ("subject_source", tokenJson s),
    ("object_source", tokenJson o), ("referents", Json.null), ("world_truth", Json.null)]

def resultJson (r : Result) : Json :=
  let tokens := wordSpans r.request.text
  Json.mkObj [
    ("law_id", toJson lawId), ("text", toJson r.request.text),
    ("source_id", toJson r.request.sourceId), ("revision", toJson r.request.revision),
    ("scope", toJson r.request.scope), ("ending", toJson r.request.ending),
    ("onset", toJson r.request.onset),
    ("status", toJson (status r).label), ("reason", toJson (reason r)),
    ("boundary_valid", toJson (boundaryValid r.request.text)),
    ("source_pieces", toJson ((sourcePieces r.request.text).map spanJson)),
    ("tokens", toJson (tokens.map tokenJson)),
    ("reading_id", toJson (r.reading.map Frame.label)),
    ("reading", (r.reading.map (fun f => readingJson f tokens)).getD Json.null)]

def failureJson (e : Failure) : Json := Json.mkObj [
  ("law_id", toJson lawId),
  ("status", toJson (if e.code == "RESOURCE_LIMIT" then "RESOURCE_EXHAUSTED" else "INVALID_INPUT")),
  ("error", toJson e.code)]

def evaluate (bytes : ByteArray) : ProbeM Json := do
  if bytes.size > maxLineBytes then return ← limited "request exceeds 1 MiB"
  let some text := String.fromUTF8? bytes | ProbeJson.invalid "request must be strict UTF-8"
  preflight text
  uniqueObjectKeys text
  let r ← request (← liftParse (Json.parse text))
  return resultJson (Nabt.ProductiveClauseV1.evaluate r)

def readBounded (path : System.FilePath) : IO ByteArray := do
  let h ← IO.FS.Handle.mk path .read
  h.read (maxLineBytes + 1).toUSize
end ProductiveClauseV1Main

open ProductiveClauseV1Main
def main (args : List String) : IO UInt32 := do
  let out ← IO.getStdout
  match args with
  | [path] =>
    try
      match evaluate (← readBounded path) with
      | .error e => out.putStrLn (failureJson e).compress; return 2
      | .ok result =>
        let encoded := result.compress
        if encoded.toUTF8.size > 8388608 then
          out.putStrLn (failureJson ⟨"RESOURCE_LIMIT", "output exceeds 8 MiB"⟩).compress
          return 2
        out.putStrLn encoded
        return 0
    catch _ =>
      out.putStrLn (failureJson ⟨"INVALID_INPUT", "could not read request"⟩).compress
      return 2
  | _ =>
    out.putStrLn (failureJson ⟨"INVALID_INPUT", "expected one request file"⟩).compress
    return 2
