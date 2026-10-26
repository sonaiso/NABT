import Nabt.EpistemicMeasurement
import ProbeJson

/-! Strict bounded JSONL adapter. All registry/ledger/origin records are explicit
premises; authentication belongs to the installed collector. The native check
validates the exact proposed scoped receipt, not physical truth or Arabic-wide
coverage. Raw duplicate object keys and noncanonical integers are rejected. -/

open Lean ProbeJson Nabt.EpistemicMeasurement
namespace EpistemicMeasurementMain

def exactFields (j : Json) (names : List String) : ProbeM Unit := do
  let obj ← liftParse j.getObj?
  if obj.size != names.length || names.any (fun n => (obj.get? n).isNone) then
    invalid "unexpected or missing field"
  else pure ()

def text (j : Json) (limit : Nat := 4096) : ProbeM String := do
  let s ← str j
  if s.isEmpty || s.toList.all Char.isWhitespace || s.toList.any (fun c => c.toNat < 32) then
    return ← invalid "empty or control-bearing identity"
  if s.utf8ByteSize > limit then return ← limited "text byte limit"
  return s

def rawContent (j : Json) : ProbeM String := do
  let s ← str j
  if s.isEmpty || s.toList.all Char.isWhitespace then return ← invalid "empty source content"
  if s.utf8ByteSize > 65536 then return ← limited "source content byte limit"
  return s

def boundedItems (parse : Json → ProbeM α) (limit : Nat) (j : Json) : ProbeM (List α) := do
  let xs ← liftParse j.getArr?
  if xs.size > limit then return ← limited "array limit"
  return ← xs.toList.mapM parse

def distinct (xs : List String) : ProbeM Unit := do
  if xs.eraseDups.length != xs.length then invalid "duplicate identity" else pure ()

def names (j : Json) : ProbeM (List String) := do
  let result ← boundedItems (fun j => text j) 256 j
  distinct result
  return result

def parseAxis (j : Json) : ProbeM Axis := do
  match ← str j with
  | "reported_motive" => pure .reportedMotive
  | "recorded_observation" => pure .recordedObservation
  | "hidden_motive" => pure .hiddenMotive
  | _ => invalid "unknown axis"

def parseKind (j : Json) : ProbeM Kind := do
  match ← str j with
  | "self_report" => pure .selfReport
  | "observation" => pure .observation
  | "lexical" => pure .lexical
  | "grammar" => pure .grammar
  | "hypothetical" => pure .hypothetical
  | "quotation" => pure .quotation
  | _ => invalid "unknown evidence kind"

def parseTime (j : Json) : ProbeM Int := do
  let raw ← text j 32
  let some value := raw.toInt? | return ← invalid "time must be a canonical signed decimal string"
  if toString value != raw then return ← invalid "noncanonical time"
  if value.natAbs > 9007199254740991 then return ← invalid "time exceeds exact integer bound"
  return value

def parseKey (j : Json) : ProbeM Key := do
  exactFields j ["axis", "entity", "predicate", "value", "unit", "context", "time", "place"]
  return ⟨← parseAxis (← field j "axis"), ← text (← field j "entity"),
    ← text (← field j "predicate"), ← text (← field j "value"), ← text (← field j "unit"),
    ← text (← field j "context"), ← parseTime (← field j "time"), ← text (← field j "place")⟩

def parseSource (j : Json) : ProbeM Source := do
  exactFields j ["identity", "revision", "content"]
  return ⟨← text (← field j "identity"), ← text (← field j "revision"),
    ← rawContent (← field j "content")⟩

def parseQuery (j : Json) : ProbeM Query := do
  exactFields j ["key", "positive", "origin"]
  return ⟨← parseKey (← field j "key"), ← boolean (← field j "positive"),
    ← text (← field j "origin")⟩

def parseOrigin (j : Json) : ProbeM Origin := do
  exactFields j ["id", "parents"]
  return ⟨← text (← field j "id"), ← names (← field j "parents")⟩

def parseEvidence (j : Json) : ProbeM Evidence := do
  exactFields j ["id", "source", "key", "positive", "kind", "origin", "ancestry"]
  return ⟨← text (← field j "id"), ← parseSource (← field j "source"),
    ← parseKey (← field j "key"), ← boolean (← field j "positive"),
    ← parseKind (← field j "kind"), ← text (← field j "origin"),
    ← names (← field j "ancestry")⟩

def parseVerdict (j : Json) : ProbeM Verdict := do
  match ← str j with
  | "SUPPORTED" => pure .supported
  | "REFUTED" => pure .refuted
  | "CONFLICT" => pure .conflict
  | "UNKNOWN" => pure .unknown
  | "RESOURCE_LIMIT" => pure .resourceLimit
  | _ => invalid "unknown certificate status"

def parseReceipt (j : Json) : ProbeM Receipt := do
  exactFields j ["status", "support_ids", "refutation_ids", "selected_ids"]
  -- Duplicate, reordered or omitted IDs remain proposed certificates and are
  -- rejected by exact receipt comparison, rather than silently canonicalized.
  return ⟨← parseVerdict (← field j "status"),
    ← boundedItems (fun j => text j) 128 (← field j "support_ids"),
    ← boundedItems (fun j => text j) 128 (← field j "refutation_ids"),
    ← boundedItems (fun j => text j) 128 (← field j "selected_ids")⟩

def validateGraph (ctx : Context) (query : Query) : ProbeM Unit := do
  let ids := ctx.origins.map Origin.id
  distinct ids
  if !ids.contains query.origin then return ← invalid "unknown query origin"
  for node in ctx.origins do
    if node.parents.any (fun parent => !ids.contains parent) then
      return ← invalid "unknown parent origin"
  for evidence in ctx.interpretations do
    if !ids.contains evidence.origin || evidence.ancestry.any (fun id => !ids.contains id) then
      return ← invalid "unknown evidence ancestry origin"

def resultJson (observed : Receipt) (checked : Bool) (invalidCertificate : Bool) : Json :=
  Json.mkObj [
    ("law_id", toJson lawId),
    ("status", toJson (if invalidCertificate then "INVALID_CERTIFICATE" else observed.status.label)),
    ("observed_status", toJson observed.status.label),
    ("support_ids", toJson observed.supportIds),
    ("refutation_ids", toJson observed.refutationIds),
    ("selected_ids", toJson observed.selectedIds),
    ("certificate_checked", toJson checked),
    ("world_truth_established", toJson false),
    ("hidden_motive_established", toJson false),
    ("all_arabic_complete", toJson false)]

def dispatch (j : Json) : ProbeM Json := do
  exactFields j ["query", "active_sources", "origins", "interpretations", "budget", "certificate"]
  let query ← parseQuery (← field j "query")
  let sources ← boundedItems parseSource 128 (← field j "active_sources")
  distinct (sources.map (fun s => s.identity))
  let origins ← boundedItems parseOrigin 256 (← field j "origins")
  let evidence ← boundedItems parseEvidence 128 (← field j "interpretations")
  distinct (evidence.map Evidence.id)
  let ctx : Context := ⟨sources, origins, evidence⟩
  validateGraph ctx query
  let budget ← nat (← field j "budget")
  if budget > 128 then return ← limited "budget exceeds 128"
  let proposed ← field j "certificate"
  let observed := receipt ctx query budget
  match proposed with
  | .null => return resultJson observed false false
  | _ =>
    let candidate ← parseReceipt proposed
    let checked := checkReceipt ctx query budget candidate
    return resultJson observed checked (!checked)

def errorJson (e : Failure) : Json := Json.mkObj [
  ("law_id",toJson lawId), ("status",toJson e.code), ("reason",toJson e.message),
  ("world_truth_established",toJson false), ("hidden_motive_established",toJson false),
  ("all_arabic_complete",toJson false)]

/-- Run only after JSON syntax validation. Lean's object parser overwrites
duplicate keys; retain the raw quoted token and decode it before comparing
keys inside each object. Escaped spellings therefore cannot bypass uniqueness.
This transport check is intentionally local to the new graph protocol. -/
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
      else if c == '"' then
        quoted := false
        lastString := some (String.ofList token.reverse)
    else if c == '"' then
      quoted := true
      token := ['"']
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

/-- Same bounded JSONL recovery as ProbeJson, with the graph-specific raw-key
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
end EpistemicMeasurementMain

def main (args : List String) : IO Unit := do
  if args.isEmpty then
    EpistemicMeasurementMain.readLoop (← IO.getStdin) (← IO.getStdout)
  else throw (IO.userError "usage: epistemicMeasurement")
