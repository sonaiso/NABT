import Nabt.ConnectedAcquisitionV3
import ProbeJson

open Lean ProbeJson Nabt.ConnectedAcquisitionV3
namespace ConnectedAcquisitionV3Main

/- The bounded transport guards and unchanged piece/word serializers below
are copied from AlignedAcquisitionMain.lean to preserve that v1 file exactly.
Importing its executable module would also import its global main declaration.
These adapter checks are not a theorem about JSON parser refinement. -/
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
  if s.isEmpty || s.length > 512 || s.toList.any (fun c => c.toNat < 32 || (127 ≤ c.toNat && c.toNat ≤ 159)) then
    ProbeJson.invalid "identity must be nonempty, at most 512 scalars, and contain no C0/C1 controls"
  else return s

def request (j : Json) : ProbeM Request := do
  keys j ["text", "source_id", "revision", "scope", "ending", "onset"]
  let text ← str (← field j "text")
  if text.toUTF8.size > 8192 || text.length > 4096 then return ← limited "source exceeds acquisition budget"
  let sourceId ← metadata (← field j "source_id")
  let revision ← metadata (← field j "revision")
  let scope ← metadata (← field j "scope")
  let ending ← str (← field j "ending")
  let ending ← match ending with
    | "wasl" => pure Nabt.AlignedAcquisition.Ending.wasl
    | "waqf" => pure Nabt.AlignedAcquisition.Ending.waqf
    | _ => ProbeJson.invalid "ending must be wasl or waqf"
  let onset ← str (← field j "onset")
  let onset ← match onset with
    | "word_initial" => pure Nabt.AlignedAcquisitionV2.Onset.wordInitial
    | "connected" => pure Nabt.AlignedAcquisitionV2.Onset.connected
    | _ => ProbeJson.invalid "onset must be word_initial or connected"
  let r : Request := ⟨⟨text, sourceId, revision, scope, ending⟩, onset⟩
  if (words (citation r).groups).length > 32 then return ← limited "source exceeds 32 words"
  return r

def statusString : Nabt.AlignedAcquisition.Status → String
  | .licensed => "LICENSED" | .boundary => "BOUNDARY"
  | .deferred => "DEFER" | .invalid => "INVALID_INPUT"

def readingFields (r : Option Reading) : List (String × Json) := [
  ("reading_id", match r with | some r => toJson r.id | none => Json.null),
  ("source_passages", toJson ((r.map Reading.passages).getD []))]

def pieceFields (e : Nabt.AlignedAcquisition.Entry) (r : Option Reading) : List (String × Json) := [
  ("start", toJson e.span.start), ("end", toJson e.span.stop),
  ("byte_start", toJson e.span.byteStart), ("byte_end", toJson e.span.byteStop),
  ("raw", toJson (String.ofList e.span.raw)), ("status", toJson (statusString e.decision.status)),
  ("rule", toJson e.decision.rule), ("cells", toJson (e.decision.cells.map (·.val)))] ++ readingFields r

def wordJson (es : List Nabt.AlignedAcquisition.Entry) : Json :=
  let first := es.head?.map Nabt.AlignedAcquisition.Entry.span
  let last := es.getLast?.map Nabt.AlignedAcquisition.Entry.span
  Json.mkObj ([("start", toJson (first.map Nabt.AlignedAcquisition.Span.start |>.getD 0)),
    ("end", toJson (last.map Nabt.AlignedAcquisition.Span.stop |>.getD 0)),
    ("byte_start", toJson (first.map Nabt.AlignedAcquisition.Span.byteStart |>.getD 0)),
    ("byte_end", toJson (last.map Nabt.AlignedAcquisition.Span.byteStop |>.getD 0)),
    ("raw", toJson (rawWord es)),
    ("status", toJson (Nabt.AlignedAcquisition.status es)),
    ("cells", toJson ((Nabt.AlignedAcquisition.emitted es).map (·.val)))] ++ readingFields (reading es))

def annotatedEntries (gs : List (List Nabt.AlignedAcquisition.Entry)) :
    List (Nabt.AlignedAcquisition.Entry × Option Reading) :=
  gs.flatMap fun es => es.map fun e => (e, reading es)

def acquisitionJson (r : Result) : Json := Json.mkObj [
  ("law_id", toJson lawId), ("alphabet_id", toJson alphabetId),
  ("source_id", toJson r.request.base.sourceId), ("revision", toJson r.request.base.revision),
  ("scope", toJson r.request.base.scope),
  ("ending", toJson (if r.request.base.ending == .wasl then "wasl" else "waqf")),
  ("onset", toJson (if r.request.onset == .wordInitial then "word_initial" else "connected")),
  ("text", toJson r.request.base.text), ("status", toJson r.citation.status), ("reason", toJson r.citation.reason),
  ("pieces", toJson ((annotatedEntries r.citation.groups).map fun (e, rd) => Json.mkObj (pieceFields e rd))),
  ("words", toJson ((words r.citation.groups).map wordJson))]

def realizedPieces (intervals : Bool) : Nat →
    List (Nabt.AlignedAcquisition.Entry × Option Reading) → List Json
  | _, [] => []
  | start, (e, rd) :: rest =>
    let stop := start + e.decision.cells.length
    Json.mkObj (pieceFields e rd ++ [
      ("cell_start", if intervals then toJson start else Json.null),
      ("cell_end", if intervals then toJson stop else Json.null)]) :: realizedPieces intervals stop rest

def joinJson (r : Result) (index : Nat) (left right : List Nabt.AlignedAcquisition.Entry) : Json :=
  let lo := (left.getLast?.map Nabt.AlignedAcquisition.Entry.span).getD ⟨0, 0, []⟩
  let hi := (right.head?.map Nabt.AlignedAcquisition.Entry.span).getD ⟨0, 0, []⟩
  let joined := continuous r.request r.citation.groups
  let guarded := joined && shortFinal left
  let article := (reading right).any (fun rd => rd.article != .none)
  let elided := r.request.onset == .connected && guarded && article
  let status := if r.request.onset == .wordInitial then "CITATION_BOUNDARY"
    else if guarded then "JOINED" else "DEFER"
  let rule := if r.request.onset == .wordInitial then "CITATION_BOUNDARY"
    else if !joined then "BOUNDARY_CONTINUITY_UNLICENSED"
    else if !shortFinal left then "CONTACT_REPAIR_NOT_IMPLEMENTED"
    else if elided then "ARTICLE_WASL_ELISION" else "ONSET_UNCHANGED"
  Json.mkObj [("left_word", toJson index), ("right_word", toJson (index + 1)),
    ("status", toJson status), ("rule", toJson rule), ("elided", toJson elided),
    ("span", Json.mkObj [("start", toJson lo.stop), ("end", toJson hi.start),
      ("byte_start", toJson lo.byteStop), ("byte_end", toJson hi.byteStart),
      ("raw", toJson (String.ofList ((r.request.base.text.toList.drop lo.stop).take (hi.start - lo.stop))))])]

def joinsJson (r : Result) : Nat → List (List Nabt.AlignedAcquisition.Entry) → List Json
  | index, left :: right :: rest => joinJson r index left right :: joinsJson r (index + 1) (right :: rest)
  | _, _ => []

def realizationJson (r : Result) : Json := Json.mkObj [
  ("mode", toJson (if r.request.onset == .wordInitial then "word_initial" else "connected")),
  ("status", toJson (if r.realization.status == "ACQUIRED" then "REALIZED" else r.realization.status)),
  ("pieces", toJson (realizedPieces (r.request.onset == .connected && r.status == "ACQUIRED") 0
    (annotatedEntries r.realization.groups))),
  ("words", toJson ((words r.realization.groups).map wordJson)),
  ("joins", toJson (joinsJson r 0 (words r.citation.groups))),
  ("phrase_cells", toJson (r.phraseCells.map (·.val)))]

def resultJson (r : Result) : Json := Json.mkObj [
  ("law_id", toJson lawId), ("alphabet_id", toJson alphabetId),
  ("onset", toJson (if r.request.onset == .wordInitial then "word_initial" else "connected")),
  ("status", toJson r.status), ("acquisition", acquisitionJson r), ("realization", realizationJson r)]

/-- Transport is bounded and tested, not a theorem of JSON/compiler refinement. -/
def failureJson (e : Failure) : Json := Json.mkObj [
  ("law_id", toJson lawId), ("alphabet_id", toJson alphabetId),
  ("status", toJson (if e.code == "RESOURCE_LIMIT" then "RESOURCE_EXHAUSTED" else "INVALID_INPUT")),
  ("error", toJson e.code)]

def evaluate (bytes : ByteArray) : ProbeM Json := do
  if bytes.size > maxLineBytes then return ← limited "request exceeds 1 MiB"
  let some text := String.fromUTF8? bytes | ProbeJson.invalid "request must be strict UTF-8"
  preflight text
  uniqueObjectKeys text
  let r ← request (← liftParse (Json.parse text))
  let result := acquire r
  if result.phraseCells.length > 4096 then return ← limited "phrase cell budget"
  return resultJson result

def readBounded (path : System.FilePath) : IO ByteArray := do
  let h ← IO.FS.Handle.mk path .read
  h.read (maxLineBytes + 1).toUSize

end ConnectedAcquisitionV3Main
open ConnectedAcquisitionV3Main

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
