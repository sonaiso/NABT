import Nabt.OccurrenceSense
import ProbeJson

/-! Bounded transport for occurrence-bound dictionary candidates. Native checks
are relative to the retained, source-replayed STEM ledger. The installed full
catalogue and candidate links can be exported for runtime drift comparison. -/
open Lean ProbeJson Nabt.OccurrenceSense
namespace OccurrenceSenseMain

def exactFields (j : Json) (names : List String) : ProbeM Unit := do
  let obj ← liftParse j.getObj?
  if obj.size != names.length || names.any (fun name => (obj.get? name).isNone) then
    invalid "unexpected or missing field"
  else pure ()

def text (j : Json) (limit : Nat := 4096) : ProbeM String := do
  let value ← str j
  if value.isEmpty || value.toList.all spacing ||
      value.toList.any (fun char => char.toNat < 32) then
    return ← invalid "empty or control-bearing identity"
  if value.utf8ByteSize > limit then return ← limited "text byte limit"
  return value

def rawContent (j : Json) (limit : Nat) : ProbeM String := do
  let value ← str j
  if value.isEmpty || value.toList.all spacing then return ← invalid "empty source content"
  if value.utf8ByteSize > limit then return ← limited "source content byte limit"
  return value

def boundedNat (j : Json) (limit : Nat := 9007199254740991) : ProbeM Nat := do
  let value ← nat j
  if value > limit then return ← limited "integer exceeds declared bound"
  return value

def boundedItems (parse : Json → ProbeM α) (limit : Nat) (j : Json) : ProbeM (List α) := do
  let values ← liftParse j.getArr?
  if values.size > limit then return ← limited "array limit"
  return ← values.toList.mapM parse

def distinct (values : List String) : ProbeM Unit := do
  if values.eraseDups.length != values.length then invalid "duplicate identity" else pure ()

def optionalText (j : Json) : ProbeM (Option String) := do
  match j with
  | .null => pure none
  | _ => return some (← text j)

def parseTarget (j : Json) : ProbeM Nabt.ContextualReference.Target := do
  exactFields j ["id", "revision", "text"]
  return ⟨← text (← field j "id"), ← text (← field j "revision"),
    ← rawContent (← field j "text") 65536⟩

def parseOccurrence (j : Json) : ProbeM Nabt.ContextualReference.Occurrence := do
  exactFields j ["start_byte", "end_byte", "surface"]
  return ⟨← boundedNat (← field j "start_byte"), ← boundedNat (← field j "end_byte"),
    ← text (← field j "surface")⟩

def parseDonor (j : Json) : ProbeM Nabt.ContextualReference.Donor := do
  exactFields j ["id", "source_id", "source_revision", "start_byte", "end_byte", "record"]
  return ⟨← text (← field j "id"), ← text (← field j "source_id"),
    ← text (← field j "source_revision"), ← boundedNat (← field j "start_byte"),
    ← boundedNat (← field j "end_byte"), ← rawContent (← field j "record") 4096⟩

def parseQuery (j : Json) : ProbeM (List String) := do
  let query ← boundedItems (fun j => text j 2048) 32 j
  if query.isEmpty then return ← invalid "at least one target component required"
  distinct query
  return query

def parseBinding (j : Json) : ProbeM Binding := do
  exactFields j ["source", "occurrence", "token_index", "context_binding", "target"]
  return ⟨← parseTarget (← field j "source"), ← parseOccurrence (← field j "occurrence"),
    ← boundedNat (← field j "token_index") 127,
    ← rawContent (← field j "context_binding") 65536, ← parseQuery (← field j "target")⟩

def parseStatus (j : Json) : ProbeM Status := do
  match ← str j with
  | "CANDIDATES_ONLY" => pure .candidatesOnly
  | "PARTIAL_CANDIDATES" => pure .partialCandidates
  | "NO_DICTIONARY_CANDIDATE" => pure .noDictionaryCandidate
  | "NO_MORPHOLOGY_READING" => pure .noMorphologyReading
  | "RESOURCE_LIMIT" => pure .resourceLimit
  | _ => invalid "unknown proposed status"

def parseSense (j : Json) : ProbeM SenseResult := do
  exactFields j ["id", "mutabaqa", "tadammun", "iltizam"]
  let id ← text (← field j "id")
  let some sense := Nabt.LexicalCompletionCatalog.senses.find? (fun sense => sense.id == id)
    | return ← invalid "proposed sense outside the installed catalogue"
  return ⟨sense, ← boolean (← field j "mutabaqa"), ← boolean (← field j "tadammun"),
    ← boolean (← field j "iltizam")⟩

def parseReading (j : Json) : ProbeM ReadingResult := do
  exactFields j ["source_form", "lemma_bw", "root_bw", "pos", "donor_ids", "status", "senses"]
  let key : MorphologyKey := ⟨← text (← field j "source_form"),
    ← optionalText (← field j "lemma_bw"), ← optionalText (← field j "root_bw"),
    ← text (← field j "pos")⟩
  let donors ← boundedItems (fun j => text j) 4096 (← field j "donor_ids")
  let senses ← boundedItems parseSense 64 (← field j "senses")
  let status ← str (← field j "status")
  if status != (if senses.isEmpty then "UNMATCHED_READING" else "CANDIDATES_ONLY") then
    return ← invalid "proposed reading status disagrees with candidate inventory"
  return ⟨key, donors, senses⟩

def parseReceipt (j : Json) : ProbeM Receipt := do
  exactFields j ["binding", "budget", "status", "readings"]
  return ⟨← parseBinding (← field j "binding"), ← boundedNat (← field j "budget") 1000000,
    ← parseStatus (← field j "status"),
    ← boundedItems parseReading 256 (← field j "readings")⟩

def sourceJson (source : Nabt.ContextualReference.Target) : Json := Json.mkObj [
  ("id", toJson source.id), ("revision", toJson source.revision), ("text", toJson source.text)]

def occurrenceJson (occurrence : Nabt.ContextualReference.Occurrence) : Json := Json.mkObj [
  ("start_byte", toJson occurrence.startByte), ("end_byte", toJson occurrence.endByte),
  ("surface", toJson occurrence.surface)]

def bindingJson (binding : Binding) : Json := Json.mkObj [
  ("source", sourceJson binding.source), ("occurrence", occurrenceJson binding.occurrence),
  ("token_index", toJson binding.tokenIndex), ("context_binding", toJson binding.contextBinding),
  ("target", toJson binding.target)]

def senseResultJson (row : SenseResult) : Json := Json.mkObj [
  ("id", toJson row.sense.id), ("mutabaqa", toJson row.mutabaqa),
  ("tadammun", toJson row.tadammun), ("iltizam", toJson row.iltizam)]

def readingJson (row : ReadingResult) : Json := Json.mkObj [
  ("source_form", toJson row.key.sourceForm), ("lemma_bw", toJson row.key.lemmaBW),
  ("root_bw", toJson row.key.rootBW), ("pos", toJson row.key.pos),
  ("donor_ids", toJson row.donorIds),
  ("status", toJson (if row.senses.isEmpty then "UNMATCHED_READING" else "CANDIDATES_ONLY")),
  ("senses", Json.arr (row.senses.map senseResultJson).toArray)]

def resultJson (observed : Receipt) (checked invalidCertificate : Bool) : Json := Json.mkObj [
  ("law_id", toJson lawId), ("binding", bindingJson observed.binding),
  ("budget", toJson observed.budget),
  ("status", toJson (if invalidCertificate then "INVALID_CERTIFICATE" else observed.status.label)),
  ("observed_status", toJson observed.status.label),
  ("readings", Json.arr (observed.readings.map readingJson).toArray),
  ("certificate_checked", toJson checked), ("contextual_sense_selected", toJson false),
  ("whole_clause_checked", toJson false), ("world_truth_established", toJson false),
  ("reference_transferred", toJson false), ("all_arabic_complete", toJson false)]

def citationJson (citation : Nabt.LexicalDenotation.Citation) : Json := Json.mkObj [
  ("work", toJson citation.work), ("revision", toJson citation.revision),
  ("source_sha256", toJson citation.sourceSha256), ("start_byte", toJson citation.startByte),
  ("end_byte", toJson citation.endByte), ("quotation", toJson citation.quotation)]

def senseJson (sense : Nabt.LexicalDenotation.Sense) : Json := Json.mkObj [
  ("id", toJson sense.id), ("root", toJson sense.root), ("citation", citationJson sense.citation),
  ("components", toJson sense.components)]

def catalogueJson : Json := Json.mkObj [
  ("law_id", toJson "nabt.lexical-completion.v1"),
  ("catalogue_id", toJson Nabt.LexicalCompletionCatalog.catalogueId),
  ("semantic_law", toJson Nabt.LexicalDenotation.lawId),
  ("senses", Json.arr (Nabt.LexicalCompletionCatalog.senses.map senseJson).toArray),
  ("necessities", Json.arr (Nabt.LexicalCompletionCatalog.necessities.map fun row => Json.mkObj [
    ("sense_id", toJson row.sense.id), ("target", toJson row.target),
    ("kind", toJson "mental"), ("citation", citationJson row.citation)]).toArray)]

def table : Json := Json.mkObj [
  ("law_id", toJson lawId), ("matrix_sha256", toJson matrixSha256),
  ("catalogue_sha256", toJson catalogueSha256),
  ("links", Json.arr (links.map fun row => Json.mkObj [
    ("lemma_bw", toJson row.lemmaBW), ("root_bw", toJson row.rootBW),
    ("pos", toJson row.pos), ("sense_id", toJson row.senseId)]).toArray),
  ("catalogue", catalogueJson)]

def dispatch (j : Json) : ProbeM Json := do
  exactFields j ["source", "occurrence", "token_index", "context_binding", "donors", "target", "budget", "proposed"]
  let binding : Binding := ⟨← parseTarget (← field j "source"),
    ← parseOccurrence (← field j "occurrence"), ← boundedNat (← field j "token_index") 127,
    ← rawContent (← field j "context_binding") 65536, ← parseQuery (← field j "target")⟩
  let some runs := writtenRuns binding.source.text | return ← invalid "unterminated outer quotation"
  if runs.length > 128 then return ← limited "too many outer written runs"
  if !(decide binding.Exact) then
    return ← invalid "occurrence is not the exact selected outer written run"
  let donors ← boundedItems parseDonor 4096 (← field j "donors")
  distinct (donors.map Nabt.ContextualReference.Donor.id)
  distinct (donors.map Nabt.ContextualReference.Donor.record)
  let input : Input := ⟨binding, donors⟩
  if !(decide input.Valid) then
    return ← invalid "unsupported, mismatched, or malformed source STEM record"
  let budget ← boundedNat (← field j "budget") 1000000
  let observed := receipt input budget
  match ← field j "proposed" with
  | .null => return resultJson observed false false
  | proposal =>
    let candidate ← parseReceipt proposal
    let checked := checkReceipt input budget candidate
    return resultJson observed checked (!checked)

def errorJson (error : Failure) : Json := Json.mkObj [
  ("law_id", toJson lawId), ("status", toJson error.code), ("reason", toJson error.message),
  ("certificate_checked", toJson false), ("contextual_sense_selected", toJson false),
  ("whole_clause_checked", toJson false), ("world_truth_established", toJson false),
  ("reference_transferred", toJson false), ("all_arabic_complete", toJson false)]

-- The duplicate-key-aware bounded JSONL loop is copied unchanged from the
-- existing contextual reference transport; historical parser behavior is intact.

def uniqueObjectKeys (line : String) : ProbeM Unit := do
  let mut quoted := false
  let mut escaped := false
  let mut token : List Char := []
  let mut lastString : Option String := none
  let mut objects : List (List String) := []
  for c in line.toList do
    if quoted then
      token := c :: token
      if escaped then escaped := false
      else if c == '\\' then escaped := true
      else if c == (Char.ofNat 34) then
        quoted := false
        lastString := some (String.ofList token.reverse)
    else if c == (Char.ofNat 34) then
      quoted := true
      token := [(Char.ofNat 34)]
      lastString := none
    else if c == '{' then
      objects := [] :: objects
      lastString := none
    else if c == '}' then
      objects := objects.tail
      lastString := none
    else if c == ':' then
      let some raw := lastString | return ← invalid "object key missing"
      let key ← str (← liftParse (Json.parse raw))
      let keys :: rest := objects | return ← invalid "object key outside object"
      if keys.contains key then return ← invalid "duplicate object key"
      objects := (key :: keys) :: rest
      lastString := none
    else if !c.isWhitespace then lastString := none

def processLine (bytes : ByteArray) (oversized : Bool) : Json :=
  if oversized then errorJson ⟨"RESOURCE_LIMIT", "input line exceeds 1 MiB"⟩
  else match String.fromUTF8? bytes with
    | none => errorJson ⟨"INVALID_INPUT", "input line is not valid UTF-8"⟩
    | some line =>
      match (do
        ProbeJson.preflight line
        let request ← liftParse (Json.parse line)
        uniqueObjectKeys line
        dispatch request : ProbeM Json) with
      | .ok result => result
      | .error failure => errorJson failure

def emit (output : IO.FS.Stream) (bytes : ByteArray) (oversized : Bool) : IO Unit := do
  output.putStr ((processLine bytes oversized).compress ++ "\n")
  output.flush

/-- Same bounded JSONL recovery as ProbeJson, with the reference-specific raw-key
check before dispatch. No historical executable changes its parser contract. -/
partial def readLoop (input output : IO.FS.Stream)
    (pending : ByteArray := ByteArray.emptyWithCapacity 0) (overflow : Bool := false) : IO Unit := do
  let chunk ← input.read 1
  if chunk.isEmpty then
    if !pending.isEmpty || overflow then emit output pending overflow
  else
    let mut pending := pending
    let mut overflow := overflow
    for byte in chunk do
      if byte == 10 then
        emit output pending overflow
        pending := ByteArray.emptyWithCapacity 0
        overflow := false
      else if !overflow then
        if pending.size < ProbeJson.maxLineBytes then pending := pending.push byte
        else
          pending := ByteArray.emptyWithCapacity 0
          overflow := true
    readLoop input output pending overflow
end OccurrenceSenseMain

def main (args : List String) : IO Unit := do
  if args == ["--export"] then
    (← IO.getStdout).putStrLn OccurrenceSenseMain.table.compress
  else if args.isEmpty then
    OccurrenceSenseMain.readLoop (← IO.getStdin) (← IO.getStdout)
  else throw (IO.userError "usage: occurrenceSense [--export]")
