import Nabt.LicensedInference
import ProbeJson

open Lean ProbeJson Nabt.VerifiedReading
namespace LicensedInferenceMain

/-- Reject ambiguous object fields before the general parser collapses them.
Keys are decoded first, so escaped spellings of the same key also conflict.
This bounded lexical adapter is not a theorem about JSON parser refinement. -/
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
        if names.contains key then return ← invalid "duplicate JSON object key"
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
    invalid "object fields do not match the versioned schema"
  else pure ()
def boundedItems (n : Nat) (f : Json → ProbeM α) (j : Json) : ProbeM (List α) := do
  let xs ← liftParse j.getArr?
  if xs.size > n then return ← limited "certificate array exceeds its limit"
  xs.toList.mapM f

def literal (j : Json) : ProbeM Nabt.VerifiedReading.Literal := do
  keys j ["predicate", "arguments", "positive"]
  return ⟨← str (← field j "predicate"), ← boundedItems 2 str (← field j "arguments"),
    ← boolean (← field j "positive")⟩
def clause (j : Json) : ProbeM Clause := do
  match ← str (← field j "kind") with
  | "fact" =>
    keys j ["kind", "atom"]
    return .fact (← literal (← field j "atom"))
  | "rule" =>
    keys j ["kind", "body", "head"]
    return .rule (← boundedItems 16 literal (← field j "body")) (← literal (← field j "head"))
  | _ => invalid "unknown clause kind"
def source (j : Json) : ProbeM Source := do
  keys j ["identity", "revision", "scope", "text"]
  return ⟨← str (← field j "identity"), ← str (← field j "revision"),
    ← str (← field j "scope"), (← str (← field j "text")).toUTF8.data.toList⟩
def step (p : GroundProgram) (j : Json) : ProbeM GroundStep := do
  keys j ["kind", "index"]
  let kind ← str (← field j "kind")
  let index ← nat (← field j "index")
  if kind == "fact" then
    match p.facts[index]? with
    | some f => return .fact f
    | none => invalid "fact index outside current source"
  else if kind == "rule" then
    match p.rules[index]? with
    | some r => return .rule r
    | none => invalid "rule index outside current source"
  else invalid "unknown proof step kind"
def certificate (expected : Source) (j : Json) : ProbeM Nabt.LicensedInference.Certificate := do
  keys j ["clauses", "query", "steps", "known", "clean_steps", "clean_known"]
  let cs ← boundedItems 256 clause (← field j "clauses")
  let query ← literal (← field j "query")
  let known ← boundedItems 512 (fun j => return (← literal j).lower expected.scope) (← field j "known")
  let p := lower expected cs
  let cp := clean p known
  return ⟨⟨cs, query⟩, ← boundedItems 512 (step p) (← field j "steps"), known,
    ← boundedItems 512 (step cp) (← field j "clean_steps"),
    ← boundedItems 512 (fun j => return (← literal j).lower expected.scope) (← field j "clean_known")⟩

structure Package where
  source : Source
  queryRaw : List UInt8
  certificates : List Nabt.LicensedInference.Certificate

def parsePackage (expected : Source) (j : Json) : ProbeM Package := do
  keys j ["law_id", "source", "query_text", "readings"]
  if (← str (← field j "law_id")) != Nabt.LicensedInference.lawId then return ← invalid "unsupported law"
  return ⟨← source (← field j "source"), (← str (← field j "query_text")).toUTF8.data.toList,
    ← boundedItems 64 (certificate expected) (← field j "readings")⟩

def literalJson (a : Nabt.VerifiedReading.Literal) : Json := Json.mkObj [("predicate", toJson a.predicate),
  ("arguments", toJson a.arguments), ("positive", toJson a.positive)]
def clauseJson : Clause → Json
  | .fact a => Json.mkObj [("kind", toJson "fact"), ("atom", literalJson a)]
  | .rule body head => Json.mkObj [("kind", toJson "rule"),
      ("body", toJson (body.map literalJson)), ("head", literalJson head)]
def verdict (e : Evidence) : String :=
  match Nabt.SemanticInference.classify e.positive e.negative e.cleanPositive e.cleanNegative with
  | .supported => "SUPPORTED" | .refuted => "REFUTED" | .conflict => "CONFLICT"
  | .unknown => "UNKNOWN" | .deferred => "DEFER"
def evidenceJson (e : Evidence) : Json := Json.mkObj [
  ("positive", toJson e.positive), ("negative", toJson e.negative),
  ("clean_positive", toJson e.cleanPositive), ("clean_negative", toJson e.cleanNegative)]
def aggregateJson (a : Nabt.LicensedInference.Aggregate) : Json := Json.mkObj [
  ("credulous_positive", toJson a.credulousPositive), ("credulous_negative", toJson a.credulousNegative),
  ("skeptical_positive", toJson a.skepticalPositive), ("skeptical_negative", toJson a.skepticalNegative),
  ("credulous_clean_positive", toJson a.credulousCleanPositive), ("credulous_clean_negative", toJson a.credulousCleanNegative),
  ("skeptical_clean_positive", toJson a.skepticalCleanPositive), ("skeptical_clean_negative", toJson a.skepticalCleanNegative),
  ("within_reading_conflict", toJson a.withinReadingConflict), ("cross_reading_opposition", toJson a.crossReadingOpposition)]
def response (fields : List (String × Json)) : Json := Json.mkObj (
  [("law_id", toJson Nabt.LicensedInference.lawId), ("authority", toJson "SOURCE_RELATIVE_CONSEQUENCE"),
   ("all_arabic_complete", toJson false), ("world_truth_established", toJson false)] ++ fields)
def failed (status code message : String) : Json := response [
  ("verified", toJson false), ("status", toJson status), ("error", toJson code), ("message", toJson message)]

def evaluate (s : Source) (q : List UInt8) (bytes : ByteArray) : Json :=
  match (do
    let some text := String.fromUTF8? bytes | invalid "certificate must be UTF-8"
    preflight text
    uniqueObjectKeys text
    parsePackage s (← liftParse (Json.parse text)) : ProbeM Package) with
  | .error e => failed (if e.code == "RESOURCE_LIMIT" then "RESOURCE_EXHAUSTED" else "INVALID_INPUT") e.code e.message
  | .ok package =>
    if package.source != s || package.queryRaw != q then
      failed "CERTIFICATE_REJECTED" "BINDING_MISMATCH" "source or query binding changed"
    else match Nabt.LicensedInference.readSource s.raw, Nabt.LicensedInference.readQuery q with
    | none, _ | _, none => failed "UNKNOWN" "OUTSIDE_FRAGMENT" "source or query is outside the declared fragment"
    | some ss, some qa =>
      if ss.length > 256 then failed "RESOURCE_EXHAUSTED" "RESOURCE_LIMIT" "source exceeds 256 statements"
      else match Nabt.LicensedInference.lowerStatements ss with
      | none => failed "UNKNOWN" "UNRESOLVED_REFERENCE" "condition subject is not explicitly identified"
      | some clauses =>
        let r : Nabt.LicensedInference.Reading := ⟨clauses, qa.lower⟩
        if !Nabt.LicensedInference.verify s package.source q package.queryRaw package.certificates then
          failed "CERTIFICATE_REJECTED" "CERTIFICATE_REJECTED" "complete reading and signed closures do not verify"
        else
          let es := package.certificates.map (Nabt.LicensedInference.rowEvidence s)
          let a := Nabt.LicensedInference.aggregate es
          response [("verified", toJson true), ("status", toJson a.status),
            ("source_id", toJson s.identity), ("revision", toJson s.revision), ("source_scope", toJson s.scope),
            ("source_text", toJson (String.fromUTF8! ⟨s.raw.toArray⟩)),
            ("query_text", toJson (String.fromUTF8! ⟨q.toArray⟩)),
            ("reading_count", toJson package.certificates.length),
            ("rows", toJson (package.certificates.map fun c =>
              let e := Nabt.LicensedInference.rowEvidence s c
              Json.mkObj [("clauses", toJson (c.reading.clauses.map clauseJson)),
                ("query", literalJson c.reading.query), ("positive", toJson e.positive),
                ("negative", toJson e.negative), ("clean_positive", toJson e.cleanPositive),
                ("clean_negative", toJson e.cleanNegative), ("status", toJson (verdict e))])),
            ("aggregate", aggregateJson a)]

def readBounded (path : System.FilePath) (limit : Nat) : IO ByteArray := do
  let h ← IO.FS.Handle.mk path .read
  h.read (limit + 1).toUSize

def fixtureEvidence (n : Nat) : Evidence :=
  ⟨n % 2 == 1, n / 2 % 2 == 1, n / 4 % 2 == 1, n / 8 % 2 == 1⟩
def exportFixtures : IO Unit := do
  let lists := [[]] ++ (List.range 16).map (fun i => [fixtureEvidence i]) ++
    (List.range 16).flatMap (fun i => (List.range 16).map (fun j => [fixtureEvidence i, fixtureEvidence j]))
  for es in lists do
    let a := Nabt.LicensedInference.aggregate es
    IO.println (Json.mkObj [("law_id", toJson Nabt.LicensedInference.lawId), ("row_kind", toJson "aggregate_fixture"),
      ("authority", toJson "DIAGNOSTIC_AGGREGATION_ONLY"), ("verified", toJson false),
      ("evidence", toJson (es.map evidenceJson)), ("aggregate", aggregateJson a),
      ("status", toJson a.status)]).compress

end LicensedInferenceMain
open LicensedInferenceMain

def main (args : List String) : IO UInt32 := do
  let out ← IO.getStdout
  match args with
  | ["--export"] => exportFixtures; return 0
  | [sourcePath, queryPath, certificatePath, identity, revision, scope] =>
    try
      let raw ← readBounded sourcePath 65536
      let query ← readBounded queryPath 8192
      let cert ← readBounded certificatePath 1048576
      if raw.size > 65536 || query.size > 8192 || cert.size > 1048576 then
        out.putStrLn (failed "RESOURCE_EXHAUSTED" "RESOURCE_LIMIT" "file exceeds byte budget").compress
        return 2
      if identity.isEmpty || revision.isEmpty || scope.isEmpty then
        out.putStrLn (failed "INVALID_INPUT" "INVALID_INPUT" "identity, revision and scope must be nonempty").compress
        return 2
      let result := evaluate ⟨identity, revision, scope, raw.data.toList⟩ query.data.toList cert
      out.putStrLn result.compress
      return if (result.getObjValAs? Bool "verified").toOption == some true then 0 else 1
    catch e =>
      out.putStrLn (failed "INVALID_INPUT" "IO_ERROR" e.toString).compress
      return 2
  | _ =>
    out.putStrLn (failed "INVALID_INPUT" "INVALID_ARGUMENTS" "expected SOURCE QUERY CERTIFICATE ID REVISION SCOPE").compress
    return 2
