import Nabt.ContextualReference
import ProbeJson

/-! Strict bounded JSONL transport for the initial-occurrence reference law.
The full retained lexical/context ledger is an explicit premise. The native
comparison checks every ordered result, not authenticity of source acquisition,
truth of the context, the containing clause, or complete Arabic coverage. -/

open Lean ProbeJson Nabt.ContextualReference
namespace ContextualReferenceMain

def exactFields (j : Json) (names : List String) : ProbeM Unit := do
  let obj ← liftParse j.getObj?
  if obj.size != names.length || names.any (fun name => (obj.get? name).isNone) then
    invalid "unexpected or missing field"
  else pure ()

def text (j : Json) (limit : Nat := 4096) : ProbeM String := do
  let value ← str j
  if value.isEmpty || value.toList.all Char.isWhitespace ||
      value.toList.any (fun char => char.toNat < 32) then
    return ← invalid "empty or control-bearing identity"
  if value.utf8ByteSize > limit then return ← limited "text byte limit"
  return value

def rawContent (j : Json) (limit : Nat) : ProbeM String := do
  let value ← str j
  if value.isEmpty || value.toList.all Char.isWhitespace then
    return ← invalid "empty source content"
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

def names (j : Json) (limit : Nat) (unique : Bool := true) : ProbeM (List String) := do
  let result ← boundedItems (fun j => text j) limit j
  if unique then distinct result
  return result

def optionalText (j : Json) : ProbeM (Option String) := do
  match j with
  | .null => pure none
  | _ => return some (← text j)

def entityId (j : Json) : ProbeM String := do
  let value ← text j 64
  let chars := value.toList
  if !(chars.head?.any (fun char => 'a' ≤ char && char ≤ 'z')) ||
      !chars.all (fun char => ('a' ≤ char && char ≤ 'z') ||
        ('0' ≤ char && char ≤ '9') || char == '_') then
    return ← invalid "entity IDs require bounded lowercase ASCII names"
  return value

def optionalEntityId (j : Json) : ProbeM (Option String) := do
  match j with
  | .null => pure none
  | _ => return some (← entityId j)

def contextForm (j : Json) : ProbeM String := do
  let value ← text j 256
  if (clusters value).isNone then return ← invalid "context form requires one Arabic written run"
  return value

def parseGender (j : Json) : ProbeM (Option Nat) := do
  match ← str j with
  | "masculine" => pure (some 0)
  | "feminine" => pure (some 1)
  | "unknown" => pure none
  | _ => invalid "unknown entity gender"

def parseNumber (j : Json) : ProbeM (Option Nat) := do
  match ← str j with
  | "singular" => pure (some 0)
  | "dual" => pure (some 1)
  | "plural" => pure (some 2)
  | "unknown" => pure none
  | _ => invalid "unknown entity number"

def parseEntity (j : Json) : ProbeM Entity := do
  exactFields j ["id", "name", "gender", "number", "kind"]
  let kind ← str (← field j "kind")
  if !["person", "place", "thing", "unknown"].contains kind then
    return ← invalid "unknown entity kind"
  return ⟨← entityId (← field j "id"), ← contextForm (← field j "name"),
    ← parseGender (← field j "gender"), ← parseNumber (← field j "number"), kind⟩

def parseDeixis (j : Json) : ProbeM Deixis := do
  exactFields j ["form", "entity_ids"]
  let ids ← boundedItems entityId 64 (← field j "entity_ids")
  distinct ids
  if ids.isEmpty then return ← invalid "empty deictic candidate list"
  return ⟨← contextForm (← field j "form"), ids⟩

def parseContext (j : Json) : ProbeM Context := do
  exactFields j ["entities", "speaker", "addressee", "deixis", "closed_reference_scope"]
  if j.compress.utf8ByteSize > 65536 then return ← limited "context byte limit"
  let entities ← boundedItems parseEntity 64 (← field j "entities")
  let ids := entities.map Entity.id
  distinct ids
  let speaker ← optionalEntityId (← field j "speaker")
  let addressee ← optionalEntityId (← field j "addressee")
  let deixis ← boundedItems parseDeixis 64 (← field j "deixis")
  if speaker.any (fun id => !ids.contains id) || addressee.any (fun id => !ids.contains id) ||
      deixis.any (fun row => row.entityIds.any (fun id => !ids.contains id)) then
    return ← invalid "context selector refers to an undeclared entity"
  return ⟨entities, speaker, addressee, deixis, ← boolean (← field j "closed_reference_scope")⟩

def parseTarget (j : Json) : ProbeM Target := do
  exactFields j ["id", "revision", "text"]
  return ⟨← text (← field j "id"), ← text (← field j "revision"),
    ← rawContent (← field j "text") 65536⟩

def parseOccurrence (j : Json) : ProbeM Occurrence := do
  exactFields j ["start_byte", "end_byte", "surface"]
  return ⟨← boundedNat (← field j "start_byte"), ← boundedNat (← field j "end_byte"),
    ← text (← field j "surface")⟩

def parseDonor (j : Json) : ProbeM Donor := do
  exactFields j ["id", "source_id", "source_revision", "start_byte", "end_byte", "record"]
  let donor : Donor := ⟨← text (← field j "id"), ← text (← field j "source_id"),
    ← text (← field j "source_revision"), ← boundedNat (← field j "start_byte"),
    ← boundedNat (← field j "end_byte"), ← rawContent (← field j "record") 4096⟩
  if donor.endByte != donor.startByte + donor.record.utf8ByteSize then
    return ← invalid "donor record byte range differs"
  return donor

def parsePos (j : Json) : ProbeM PartOfSpeech := do
  match ← str j with
  | "PRON" => pure .pronoun
  | "DEM" => pure .demonstrative
  | "OTHER" => pure .other
  | _ => invalid "unknown lexical part of speech"

def parseProfile (j : Json) : ProbeM (Option Nabt.PersonEvidence.Profile) := do
  match j with
  | .null => pure none
  | _ =>
    let code ← str j
    let some profile := Nabt.PersonEvidence.profiles.find? (fun row => row.qac == code)
      | return ← invalid "unknown lexical person profile"
    return some profile

def parseAlternative (j : Json) : ProbeM Alternative := do
  exactFields j ["id", "pos", "profile_code", "target_surface", "source_form", "donor_ids"]
  let ids ← names (← field j "donor_ids") 256
  if ids.isEmpty then return ← invalid "alternative lacks retained donors"
  return ⟨← text (← field j "id"), ← parsePos (← field j "pos"),
    ← parseProfile (← field j "profile_code"), ← text (← field j "target_surface"),
    ← text (← field j "source_form"), ids⟩

def parseStatus (j : Json) : ProbeM Status := do
  match ← str j with
  | "RESOLVED" => pure .resolved
  | "AMBIGUOUS" => pure .ambiguous
  | "NO_CANDIDATE" => pure .noCandidate
  | "OPEN_SCOPE" => pure .openScope
  | "UNSUPPORTED_READING" => pure .unsupportedReading
  | "NO_LEXICAL_READING" => pure .noLexicalReading
  | "OUT_OF_SCOPE" => pure .outOfScope
  | "RESOURCE_LIMIT" => pure .resourceLimit
  | "UNRESOLVED_FEATURES" => pure .unresolvedFeatures
  | _ => invalid "unknown proposed status"

def parseReadingResult (j : Json) : ProbeM ReadingResult := do
  exactFields j ["id", "status", "candidate_entity_ids", "bound_entity_id"]
  return ⟨← text (← field j "id"), ← parseStatus (← field j "status"),
    ← names (← field j "candidate_entity_ids") 64 false,
    ← optionalText (← field j "bound_entity_id")⟩

def parseReceipt (j : Json) : ProbeM Receipt := do
  exactFields j ["status", "reading_ids", "candidate_entity_ids", "bound_entity_id", "reading_results"]
  -- Keep proposed order and duplicates: comparison rejects alterations rather
  -- than silently turning a partial or duplicated certificate into a valid one.
  return ⟨← parseStatus (← field j "status"), ← names (← field j "reading_ids") 64 false,
    ← names (← field j "candidate_entity_ids") 64 false,
    ← optionalText (← field j "bound_entity_id"),
    ← boundedItems parseReadingResult 64 (← field j "reading_results")⟩

def readingJson (row : ReadingResult) : Json := Json.mkObj [
  ("id", toJson row.id), ("status", toJson row.status.label),
  ("candidate_entity_ids", toJson row.candidateEntityIds), ("bound_entity_id", toJson row.boundEntityId)]

def resultJson (observed : Receipt) (checked invalidCertificate : Bool) : Json := Json.mkObj [
  ("law_id", toJson lawId),
  ("status", toJson (if invalidCertificate then "INVALID_CERTIFICATE" else observed.status.label)),
  ("observed_status", toJson observed.status.label),
  ("reading_ids", toJson observed.readingIds),
  ("candidate_entity_ids", toJson observed.candidateEntityIds),
  ("bound_entity_id", toJson observed.boundEntityId),
  ("reading_results", Json.arr (observed.readingResults.map readingJson).toArray),
  ("certificate_checked", toJson checked),
  ("whole_clause_checked", toJson false), ("world_truth_established", toJson false),
  ("motive_established", toJson false), ("all_arabic_complete", toJson false)]

def dispatch (j : Json) : ProbeM Json := do
  exactFields j ["source", "occurrence", "context", "donors", "alternatives", "budget", "proposed"]
  let target ← parseTarget (← field j "source")
  let occurrence ← parseOccurrence (← field j "occurrence")
  if occurrence.startByte > target.text.utf8ByteSize || occurrence.endByte > target.text.utf8ByteSize then
    return ← limited "occurrence byte offset exceeds source"
  if !(decide (ExactOccurrence target occurrence)) then
    return ← invalid "occurrence does not reproduce exact nonempty source bytes"
  let raw := target.text.toUTF8
  if (String.fromUTF8? (raw.extract 0 occurrence.startByte)).isNone ||
      (String.fromUTF8? (raw.extract occurrence.endByte raw.size)).isNone then
    return ← invalid "occurrence splits a UTF-8 character"
  let context ← parseContext (← field j "context")
  let donors ← boundedItems parseDonor 256 (← field j "donors")
  let donorIds := donors.map Donor.id
  distinct donorIds
  let alternatives ← boundedItems parseAlternative 64 (← field j "alternatives")
  distinct (alternatives.map Alternative.id)
  for alternative in alternatives do
    if alternative.targetSurface != occurrence.surface then
      return ← invalid "alternative belongs to a different occurrence"
    if alternative.donorIds.any (fun id => !donorIds.contains id) then
      return ← invalid "alternative cites an unknown donor"
  let input : Input := ⟨target, occurrence, context, donors, alternatives⟩
  let budget ← boundedNat (← field j "budget") 256
  let observed := receipt input budget
  match ← field j "proposed" with
  | .null => return resultJson observed false false
  | proposal =>
    let candidate ← parseReceipt proposal
    let checked := checkReceipt input budget candidate
    return resultJson observed checked (!checked)

def errorJson (e : Failure) : Json := Json.mkObj [
  ("law_id", toJson lawId), ("status", toJson e.code), ("reason", toJson e.message),
  ("whole_clause_checked", toJson false), ("world_truth_established", toJson false),
  ("motive_established", toJson false), ("all_arabic_complete", toJson false)]

/-- Run only after JSON syntax validation. Lean's object parser overwrites
duplicate keys; retain the raw quoted token and decode it before comparing
keys inside each object. Escaped spellings therefore cannot bypass uniqueness.
This transport check is intentionally local to the new reference protocol. -/
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
end ContextualReferenceMain

def main (args : List String) : IO Unit := do
  if args.isEmpty then
    ContextualReferenceMain.readLoop (← IO.getStdin) (← IO.getStdout)
  else throw (IO.userError "usage: contextualReference")
