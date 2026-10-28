import Nabt.EvidenceLifecycleV1
import ProbeJson

/-! Strict bounded wire adapter for the additive lifecycle law. Parsing and
serialization are executable boundaries, not an additional truth theorem.
Historical ProbeJson and EM executables retain their original limits. -/

open Lean ProbeJson Nabt.EpistemicMeasurement Nabt.EvidenceLifecycleV1
namespace EvidenceLifecycleV1Main

/-- Frozen scalar policy shared with the v1 Python adapter. Do not depend on
the Unicode whitespace tables of either host runtime; mixed strings retain
their exact source bytes. This changes no historical EM transport. -/
def blankScalar (c : Char) : Bool :=
  let n := c.toNat
  (9 ≤ n && n ≤ 13) || (28 ≤ n && n ≤ 32) ||
    n == 133 || n == 160 || n == 5760 || (8192 ≤ n && n ≤ 8202) ||
    n == 8232 || n == 8233 || n == 8239 || n == 8287 || n == 12288

def keys (j : Json) (names : List String) : ProbeM Unit := do
  let object ← liftParse j.getObj?
  if object.size != names.length || names.any (fun name => (object.get? name).isNone) then
    invalid "unexpected or missing object field"
  else pure ()

def text (j : Json) (limit : Nat := 4096) : ProbeM String := do
  let value ← str j
  if value.isEmpty || value.toList.all blankScalar ||
      value.toList.any (fun c => c.toNat < 32 || c.toNat == 127) then
    return ← invalid "empty or ASCII-control-bearing identity"
  if value.utf8ByteSize > limit then return ← limited "identity byte limit"
  return value

def content (j : Json) : ProbeM String := do
  let value ← str j
  if value.isEmpty || value.toList.all blankScalar then return ← invalid "empty source content"
  if value.utf8ByteSize > 16384 then return ← limited "source content byte limit"
  return value

def array (parse : Json → ProbeM α) (limit : Nat) (j : Json) : ProbeM (List α) := do
  let values ← liftParse j.getArr?
  if values.size > limit then return ← limited "collection item limit"
  values.toList.mapM parse

def distinct (values : List String) : ProbeM Unit := do
  if values.eraseDups.length != values.length then invalid "duplicate identity" else pure ()

def names (j : Json) : ProbeM (List String) := do
  let values ← array (fun j => text j) 64 j
  distinct values
  return values

def boundedNat (j : Json) (limit : Nat) : ProbeM Nat := do
  let value ← nat j
  if value > limit then return ← limited "natural number bound"
  return value

def parseSource (j : Json) : ProbeM Source := do
  keys j ["identity", "revision", "content"]
  return ⟨← text (← field j "identity"), ← text (← field j "revision"), ← content (← field j "content")⟩

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
  if value.natAbs > 9007199254740991 then return ← invalid "time exceeds exact integer domain"
  return value

def parseKey (j : Json) : ProbeM Key := do
  keys j ["axis", "entity", "predicate", "value", "unit", "context", "time", "place"]
  return ⟨← parseAxis (← field j "axis"), ← text (← field j "entity"),
    ← text (← field j "predicate"), ← text (← field j "value"), ← text (← field j "unit"),
    ← text (← field j "context"), ← parseTime (← field j "time"), ← text (← field j "place")⟩

def parseQuery (j : Json) : ProbeM Query := do
  keys j ["key", "positive", "origin"]
  return ⟨← parseKey (← field j "key"), ← boolean (← field j "positive"), ← text (← field j "origin")⟩

def parseOrigin (j : Json) : ProbeM Origin := do
  keys j ["id", "parents"]
  return ⟨← text (← field j "id"), ← names (← field j "parents")⟩

def parseEvidence (j : Json) : ProbeM Evidence := do
  keys j ["id", "source", "key", "positive", "kind", "origin", "ancestry"]
  return ⟨← text (← field j "id"), ← parseSource (← field j "source"),
    ← parseKey (← field j "key"), ← boolean (← field j "positive"),
    ← parseKind (← field j "kind"), ← text (← field j "origin"), ← names (← field j "ancestry")⟩

def parseBinding (j : Json) : ProbeM OriginBinding := do
  keys j ["origin_id", "source", "rank"]
  return ⟨← text (← field j "origin_id"), ← parseSource (← field j "source"),
    ← boundedNat (← field j "rank") 64⟩

def parseUpdateKind (j : Json) : ProbeM UpdateKind := do
  match ← str j with
  | "withdraw" => pure .withdraw
  | "activate" => pure .activate
  | "replace" => pure .replace
  | _ => invalid "unknown update kind"

def parseUpdate (j : Json) : ProbeM Update := do
  keys j ["event_id", "kind", "source", "replacement", "reason"]
  let replacement ← field j "replacement"
  return ⟨← text (← field j "event_id") 128, ← parseUpdateKind (← field j "kind"),
    ← parseSource (← field j "source"),
    ← (match replacement with | .null => pure none | other => some <$> parseSource other),
    ← text (← field j "reason")⟩

def parseEpisode (j : Json) : ProbeM Episode := do
  keys j ["schema", "episode_id", "query", "active_sources", "origins", "interpretations",
    "bindings", "budget", "updates"]
  if (← str (← field j "schema")) != schema then return ← invalid "unknown episode schema"
  let episodeId ← text (← field j "episode_id") 128
  let query ← parseQuery (← field j "query")
  let active ← array parseSource 64 (← field j "active_sources")
  let origins ← array parseOrigin 64 (← field j "origins")
  let interpretations ← array parseEvidence 64 (← field j "interpretations")
  let bindings ← array parseBinding 64 (← field j "bindings")
  let budget ← boundedNat (← field j "budget") 64
  let updates ← array parseUpdate 16 (← field j "updates")
  return ⟨episodeId, query, ⟨⟨active, origins, interpretations⟩, bindings⟩, budget, updates⟩

def sourceJson (source : Source) : Json := Json.mkObj [
  ("identity", toJson source.identity), ("revision", toJson source.revision), ("content", toJson source.content)]

def kindLabel : Kind → String
  | .selfReport => "self_report"
  | .observation => "observation"
  | .lexical => "lexical"
  | .grammar => "grammar"
  | .hypothetical => "hypothetical"
  | .quotation => "quotation"

def keyJson (key : Key) : Json := Json.mkObj [
  ("axis", toJson key.axis.label), ("entity", toJson key.entity), ("predicate", toJson key.predicate),
  ("value", toJson key.value), ("unit", toJson key.unit), ("context", toJson key.context),
  ("time", toJson (toString key.time)), ("place", toJson key.place)]

def queryJson (query : Query) : Json := Json.mkObj [
  ("key", keyJson query.key), ("positive", toJson query.positive), ("origin", toJson query.origin)]

def originJson (origin : Origin) : Json := Json.mkObj [
  ("id", toJson origin.id), ("parents", toJson origin.parents)]

def evidenceJson (evidence : Evidence) : Json := Json.mkObj [
  ("id", toJson evidence.id), ("source", sourceJson evidence.source), ("key", keyJson evidence.key),
  ("positive", toJson evidence.positive), ("kind", toJson (kindLabel evidence.kind)),
  ("origin", toJson evidence.origin), ("ancestry", toJson evidence.ancestry)]

def bindingJson (binding : OriginBinding) : Json := Json.mkObj [
  ("origin_id", toJson binding.originId), ("source", sourceJson binding.source), ("rank", toJson binding.rank)]

def updateKindLabel : UpdateKind → String
  | .withdraw => "withdraw"
  | .activate => "activate"
  | .replace => "replace"

def updateJson (update : Update) : Json := Json.mkObj [
  ("event_id", toJson update.eventId), ("kind", toJson (updateKindLabel update.kind)),
  ("source", sourceJson update.source),
  ("replacement", (update.replacement.map sourceJson).getD Json.null), ("reason", toJson update.reason)]

def episodeJson (episode : Episode) : Json := Json.mkObj [
  ("schema", toJson schema), ("episode_id", toJson episode.episodeId), ("query", queryJson episode.query),
  ("active_sources", toJson (episode.initial.base.activeSources.map sourceJson)),
  ("origins", toJson (episode.initial.base.origins.map originJson)),
  ("interpretations", toJson (episode.initial.base.interpretations.map evidenceJson)),
  ("bindings", toJson (episode.initial.bindings.map bindingJson)),
  ("budget", toJson episode.budget), ("updates", toJson (episode.updates.map updateJson))]

def receiptJson (receipt : Receipt) : Json := Json.mkObj [
  ("status", toJson receipt.status.label), ("support_ids", toJson receipt.supportIds),
  ("refutation_ids", toJson receipt.refutationIds), ("selected_ids", toJson receipt.selectedIds)]

def stepJson (step : Step) : Json := Json.mkObj [
  ("step", toJson step.step), ("event_id", toJson step.eventId),
  ("active_sources", toJson (step.activeSources.map sourceJson)), ("receipt", receiptJson step.receipt),
  ("dependency_ready_ids", toJson step.dependencyReadyIds),
  ("dependency_blocked_ids", toJson step.dependencyBlockedIds), ("affected_ids", toJson step.affectedIds)]

def falseFlags : List (String × Json) := [
  ("world_truth_established", toJson false), ("source_authenticity_established", toJson false),
  ("referents_established", toJson false), ("all_arabic_complete", toJson false)]

def reportJson (report : Report) : Json := Json.mkObj ([
  ("law_id", toJson Nabt.EvidenceLifecycleV1.lawId), ("binding", episodeJson report.binding),
  ("steps", toJson (report.steps.map stepJson))] ++ falseFlags)

def errorJson (error : Failure) : Json := Json.mkObj ([
  ("law_id", toJson Nabt.EvidenceLifecycleV1.lawId), ("status", toJson error.code),
  ("reason", toJson error.message)] ++ falseFlags)

def dispatch (j : Json) : ProbeM Json := do
  let episode ← parseEpisode j
  match evaluate episode with
  | .error (.invalid reason) => invalid reason
  | .error (.resourceLimit reason) => limited reason
  | .ok report =>
    let output := reportJson report
    if output.compress.utf8ByteSize > 8388608 then return ← limited "report exceeds 8 MiB"
    return output

/-- Decode each key before comparison, including escaped spellings. -/
def uniqueObjectKeys (line : String) : ProbeM Unit := do
  let mut stack : List (Option (List String)) := []
  let mut quoted := false
  let mut escaped := false
  let mut token : List Char := []
  let mut lastString : Option String := none
  for ch in line.toList do
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
        let key ← str (← liftParse (Json.parse encoded))
        if names.contains key then return ← invalid "duplicate decoded JSON object key"
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

/-- Local wire bounds are stricter than the historical ProbeJson defaults.
All raw numeric fields are naturals; signed time is a canonical string. -/
def preflight (line : String) : ProbeM Unit := do
  let characters := line.toList
  if !unicodeEscapesValid characters false then return ← invalid "invalid Unicode escape or unpaired surrogate"
  let mut quoted := false
  let mut escaped := false
  let mut depth := 0
  let mut digits := 0
  let mut number := 0
  let mut leadingZero := false
  let mut negative := false
  for ch in characters do
    if quoted then
      if escaped then escaped := false
      else if ch == '\\' then escaped := true
      else if ch == '"' then quoted := false
    else if '0' ≤ ch && ch ≤ '9' then
      if digits == 0 then leadingZero := ch == '0'
      digits := digits + 1
      if digits > 16 then return ← limited "JSON integer exceeds 16 digits"
      if leadingZero && digits > 1 then return ← invalid "noncanonical integer"
      number := number * 10 + (ch.toNat - '0'.toNat)
      if number > 9007199254740991 then return ← limited "JSON integer exceeds exact magnitude budget"
    else if ch == '-' && digits == 0 && !negative then
      -- Count transport digits/magnitude before rejecting a bounded signed
      -- token as an invalid natural. No signed numeric payload is accepted.
      negative := true
    else
      if negative || ch == '-' || ch == '+' || (digits > 0 && (ch == '.' || ch == 'e' || ch == 'E')) then
        return ← invalid "numeric fields require canonical unsigned integers"
      digits := 0
      number := 0
      leadingZero := false
      if ch == '"' then quoted := true
      else if ch == '{' || ch == '[' then
        depth := depth + 1
        if depth > 32 then return ← limited "JSON nesting exceeds 32 levels"
      else if ch == '}' || ch == ']' then depth := depth - 1
  if negative then return ← invalid "numeric fields require canonical unsigned integers"

def processLine (bytes : ByteArray) (oversized : Bool) : Json :=
  if oversized then errorJson ⟨"RESOURCE_LIMIT", "input line exceeds 1 MiB"⟩
  else match String.fromUTF8? bytes with
  | none => errorJson ⟨"INVALID_INPUT", "input line is not valid UTF-8"⟩
  | some line =>
    match (do
      preflight line
      let request ← liftParse (Json.parse line)
      uniqueObjectKeys line
      dispatch request : ProbeM Json) with
    | .ok result => result
    | .error error => errorJson error

def emit (output : IO.FS.Stream) (bytes : ByteArray) (oversized : Bool) : IO Unit := do
  output.putStr ((processLine bytes oversized).compress ++ "\n")
  output.flush

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
        if pending.size < maxLineBytes then pending := pending.push byte
        else
          pending := ByteArray.emptyWithCapacity 0
          overflow := true
    readLoop input output pending overflow

end EvidenceLifecycleV1Main

def main : IO Unit := do
  EvidenceLifecycleV1Main.readLoop (← IO.getStdin) (← IO.getStdout)
