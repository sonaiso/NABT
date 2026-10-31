import Nabt.MeaningPreservation
import ProbeJson

/-!
Strict JSONL adapter for the frozen finite meaning-preservation contract.
The transported string is actually decoded here; it is not accompanied by a
caller-declared reconstruction. After decoding, the decision is the proved
`MeaningPreservation.firstViolation` function. JSON parsing and wire limits
remain executable conformance boundaries.
-/

open Lean ProbeJson Nabt.MeaningPreservation

namespace MeaningPreservationV1Main

def metadataLimit : Nat := 512
def sourceLimit : Nat := 65536
def itemLimit : Nat := 64
def valueDepthLimit : Nat := 32
def reportLimit : Nat := 8388608

def keys (value : Json) (names : List String) : ProbeM Unit := do
  let object ← liftParse value.getObj?
  if object.size != names.length || names.any (fun name => (object.get? name).isNone) then
    invalid "unexpected or missing object field"
  else pure ()

def metadata (value : Json) : ProbeM String := do
  let text ← str value
  if text.utf8ByteSize > metadataLimit then return ← limited "metadata byte limit"
  if text.isEmpty || text.toList.any (fun c =>
      c.toNat < 32 || (127 ≤ c.toNat && c.toNat ≤ 159)) then
    return ← invalid "empty or control-bearing metadata"
  return text

def sourceText (value : Json) : ProbeM String := do
  let text ← str value
  if text.utf8ByteSize > sourceLimit then return ← limited "source byte limit"
  if text.isEmpty then return ← invalid "empty source text"
  return text

def nonemptyArray (parse : Json → ProbeM α) (value : Json) : ProbeM (List α) := do
  let values ← liftParse value.getArr?
  if values.size > itemLimit then return ← limited "collection item limit"
  if values.isEmpty then return ← invalid "empty required collection"
  values.toList.mapM parse

def distinct [DecidableEq α] (values : List α) : ProbeM Unit := do
  if values.eraseDups.length != values.length then invalid "duplicate complete value"
  else pure ()

/-- Root is depth zero. Object keys are not value nodes. An empty container
at depth 32 is permitted; any child there would exceed the bound. -/
def depthAllowed : Nat → Json → Bool
  | 0, .arr values => values.isEmpty
  | 0, .obj values => values.size == 0
  | remaining + 1, .arr values => values.all (depthAllowed remaining)
  | remaining + 1, .obj values => values.all (fun _ value => depthAllowed remaining value)
  | _, _ => true

/-- Bound container nesting before invoking the general parser. A final
postparse value-depth check also counts scalar children. -/
def depthPreflight (line : String) : ProbeM Unit := do
  let mut quoted := false
  let mut escaped := false
  let mut depth := 0
  for ch in line.toList do
    if quoted then
      if escaped then escaped := false
      else if ch == '\\' then escaped := true
      else if ch == '"' then quoted := false
    else if ch == '"' then quoted := true
    else if ch == '{' || ch == '[' then
      depth := depth + 1
      if depth > valueDepthLimit + 1 then return ← limited "JSON value depth limit"
    else if ch == '}' || ch == ']' then depth := depth - 1

/-- Match the existing Python strict-JSON integer budget before schema
rejection. Fractions/exponents are invalid, regardless of mantissa length;
leading zeroes and -0 are invalid before any digit-budget decision. -/
def numericToken (token : List Char) : ProbeM Unit := do
  let negative := token.head? == some '-'
  let unsigned := if negative then token.drop 1 else token
  let digit := fun c : Char => '0' ≤ c && c ≤ '9'
  match unsigned with
  | [] => if negative then invalid "incomplete number" else pure ()
  | first :: rest =>
      if first == '+' then return ← invalid "noncanonical numeric prefix"
      if !digit first then
        if negative then return ← invalid "noncanonical numeric prefix"
        return ()
      if first == '0' then
        if negative || !rest.isEmpty then return ← invalid "noncanonical numeric form"
        return ()
      let digits := unsigned.takeWhile digit
      let remaining := unsigned.drop digits.length
      if remaining.head? == some '.' || remaining.head? == some 'e' ||
          remaining.head? == some 'E' then return ← invalid "fractions and exponents are invalid"
      if digits.length > 16 then return ← limited "JSON integer digit limit"
      let magnitude := digits.foldl (fun value c => value * 10 + (c.toNat - '0'.toNat)) 0
      if magnitude > 9007199254740991 then return ← limited "JSON integer magnitude limit"
      if !remaining.isEmpty then return ← invalid "malformed numeric token"

def numericPreflight (line : String) : ProbeM Unit := do
  let mut quoted := false
  let mut escaped := false
  let mut token : List Char := []
  for ch in line.toList do
    if quoted then
      if escaped then escaped := false
      else if ch == '\\' then escaped := true
      else if ch == '"' then quoted := false
    else if ch == '"' then
      numericToken token.reverse
      token := []
      quoted := true
    else if ch == ' ' || ch == '\t' || ch == '\r' || ch == '\n' ||
        ch == '{' || ch == '}' || ch == '[' || ch == ']' || ch == ':' || ch == ',' then
      numericToken token.reverse
      token := []
    else token := ch :: token
  numericToken token.reverse

/-- Same decoded-key discipline as the existing lifecycle adapter. Parsing
validity is checked first; escaped spellings of the same key still collide. -/
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
          if names.contains key then return ← invalid "duplicate decoded object key"
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

def strictJson (line : String) : ProbeM Json := do
  if line.utf8ByteSize > ProbeJson.maxLineBytes then return ← limited "JSON byte limit"
  if !unicodeEscapesValid line.toList false then return ← invalid "invalid Unicode escape"
  depthPreflight line
  numericPreflight line
  let value ← liftParse (Json.parse line)
  uniqueObjectKeys line
  if !depthAllowed valueDepthLimit value then return ← limited "JSON value depth limit"
  return value

def parseContext (value : Json) : ProbeM Context := do
  keys value ["speaker", "addressee", "time", "place"]
  return ⟨← metadata (← field value "speaker"), ← metadata (← field value "addressee"),
    ← metadata (← field value "time"), ← metadata (← field value "place")⟩

def parseBinding (value : Json) : ProbeM Binding := do
  keys value ["source_id", "revision", "scope", "source_text", "convention"]
  return ⟨← metadata (← field value "source_id"), ← metadata (← field value "revision"),
    ← metadata (← field value "scope"), ← sourceText (← field value "source_text"),
    ← metadata (← field value "convention")⟩

def parseKind (value : Json) : ProbeM TermKind := do
  match ← str value with
  | "entity" => pure .entity
  | "speaker" => pure .speaker
  | "addressee" => pure .addressee
  | "time" => pure .time
  | "place" => pure .place
  | _ => invalid "unknown term kind"

def parseTerm (value : Json) : ProbeM Nabt.MeaningPreservation.Term := do
  keys value ["kind", "value"]
  let kind ← parseKind (← field value "kind")
  match kind with
  | .entity => return ⟨kind, ← metadata (← field value "value")⟩
  | _ =>
      let text ← str (← field value "value")
      if text != "" then return ← invalid "contextual term value must be empty"
      return ⟨kind, text⟩

def parseTense (value : Json) : ProbeM Tense := do
  match ← str value with
  | "past" => pure .past
  | "present" => pure .present
  | "future" => pure .future
  | "unspecified" => pure .unspecified
  | _ => invalid "unknown tense"

def parseVoice (value : Json) : ProbeM Voice := do
  match ← str value with
  | "active" => pure .active
  | "passive" => pure .passive
  | "unspecified" => pure .unspecified
  | _ => invalid "unknown voice"

def parseForce (value : Json) : ProbeM Force := do
  match ← str value with
  | "asserted" => pure .asserted
  | "quoted" => pure .quoted
  | "hypothetical" => pure .hypothetical
  | "question" => pure .question
  | _ => invalid "unknown force"

def parseReading (value : Json) : ProbeM Reading := do
  keys value ["predicate", "subject", "object", "positive", "tense", "voice", "force"]
  let object ← match ← field value "object" with
    | .null => pure none
    | other => (parseTerm other).map some
  return ⟨← metadata (← field value "predicate"), ← parseTerm (← field value "subject"),
    object, ← boolean (← field value "positive"), ← parseTense (← field value "tense"),
    ← parseVoice (← field value "voice"), ← parseForce (← field value "force")⟩

def parsePacket (value : Json) : ProbeM Packet := do
  keys value ["binding", "source_context", "alternatives"]
  let binding ← parseBinding (← field value "binding")
  let context ← parseContext (← field value "source_context")
  let alternatives ← nonemptyArray parseReading (← field value "alternatives")
  distinct alternatives
  return ⟨binding, context, alternatives⟩

def parseCase (value : Json) : ProbeM DecodedCase := do
  keys value ["case_id", "original", "transported_payload"]
  let id ← metadata (← field value "case_id")
  let original ← parsePacket (← field value "original")
  let payload ← str (← field value "transported_payload")
  let decoded ← parsePacket (← strictJson payload)
  return ⟨id, original, payload, decoded⟩

def response (status reason : String) (first second : Option String) (count : Nat) : Json :=
  Json.mkObj [
    ("schema", toJson "nabt.meaning-preservation.native-response.v1"),
    ("law_id", toJson lawId), ("query_id", toJson queryId), ("codec_id", toJson codecId),
    ("status", toJson status), ("reason", toJson reason),
    ("case_id", toJson first), ("other_case_id", toJson second), ("case_count", toJson count),
    ("world_truth_established", toJson false),
    ("whole_arabic_completeness_established", toJson false)]

def errorResponse (failure : Failure) : Json :=
  if failure.code == "RESOURCE_LIMIT" then
    response "RESOURCE_EXHAUSTED" "RESOURCE_LIMIT" none none 0
  else response "INVALID_INPUT" "INVALID_REQUEST" none none 0

def dispatch (value : Json) : ProbeM Json := do
  keys value ["law_id", "query_id", "codec_id", "cases", "recipient_context"]
  if (← str (← field value "law_id")) != lawId then return ← invalid "unknown law"
  if (← str (← field value "query_id")) != queryId then return ← invalid "unknown query"
  if (← str (← field value "codec_id")) != codecId then return ← invalid "unknown codec"
  -- Recipient data is validated metadata, never the origin for term resolution.
  let _ ← parseContext (← field value "recipient_context")
  let cases ← nonemptyArray parseCase (← field value "cases")
  distinct (cases.map DecodedCase.caseId)
  let result := match firstViolation cases with
    | none => response "FINITE_CONTRACT_VERIFIED" "ALL_FINITE_CONTRACTS_PRESERVED"
        none none cases.length
    | some violation => response "CONTRACT_VIOLATION" violation.reason
        (some violation.firstId) violation.otherId cases.length
  if result.compress.utf8ByteSize > reportLimit then return ← limited "report byte limit"
  return result

/-- The Bool is the process-error bit, separate from a semantic disagreement. -/
def processLine (bytes : ByteArray) (oversized : Bool) : Json × Bool :=
  if oversized then (errorResponse ⟨"RESOURCE_LIMIT", "request byte limit"⟩, true)
  else match String.fromUTF8? bytes with
    | none => (errorResponse ⟨"INVALID_INPUT", "invalid UTF-8"⟩, true)
    | some line =>
        match (do dispatch (← strictJson line) : ProbeM Json) with
        | .ok result => (result, false)
        | .error failure => (errorResponse failure, true)

def emit (output : IO.FS.Stream) (bytes : ByteArray) (oversized : Bool) : IO Bool := do
  let (result, failed) := processLine bytes oversized
  output.putStr (result.compress ++ "\n")
  output.flush
  return failed

/-- Discard an oversized line through its terminator, then process the next
request independently. An error anywhere makes the final process exit 2. -/
partial def readLoop (input output : IO.FS.Stream)
    (pending : ByteArray := ByteArray.emptyWithCapacity 0)
    (overflow : Bool := false) (failed : Bool := false) : IO Bool := do
  let chunk ← input.read 1
  if chunk.isEmpty then
    if !pending.isEmpty || overflow then
      let lastFailed ← emit output pending overflow
      return failed || lastFailed
    return failed
  else
    let mut pending := pending
    let mut overflow := overflow
    let mut failed := failed
    for byte in chunk do
      if byte == 10 then
        let lineFailed ← emit output pending overflow
        failed := failed || lineFailed
        pending := ByteArray.emptyWithCapacity 0
        overflow := false
      else if !overflow then
        if pending.size < ProbeJson.maxLineBytes then pending := pending.push byte
        else
          pending := ByteArray.emptyWithCapacity 0
          overflow := true
    readLoop input output pending overflow failed

end MeaningPreservationV1Main

def main : IO UInt32 := do
  let failed ← MeaningPreservationV1Main.readLoop (← IO.getStdin) (← IO.getStdout)
  return if failed then 2 else 0
