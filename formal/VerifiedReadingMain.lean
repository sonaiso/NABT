import Nabt.VerifiedReading
import Nabt.RelationalBridge
import ProbeJson

/-! File-based adapter: source/question bytes come from explicit paths, never
from an untrusted certificate's claimed binding. IO/JSON and the Lean compiler
remain in the stated trusted computing base. -/
open Lean ProbeJson Nabt.VerifiedReading
namespace VerifiedReadingMain

def keys (j : Json) (names : List String) : ProbeM Unit := do
  let entries ← liftParse j.getObj?
  if entries.size != names.length || names.any (fun n => (entries.get? n).isNone) then
    return ← invalid "object fields do not match the versioned schema"

def boundedItems (n : Nat) (f : Json → ProbeM α) (j : Json) : ProbeM (List α) := do
  let xs ← liftParse j.getArr?
  if xs.size > n then return ← limited "certificate array exceeds its limit"
  xs.toList.mapM f

def literal (j : Json) : ProbeM Nabt.VerifiedReading.Literal := do
  keys j ["predicate", "arguments", "positive"]
  return ⟨← str (← field j "predicate"),
    ← boundedItems 2 str (← field j "arguments"), ← boolean (← field j "positive")⟩

def clause (j : Json) : ProbeM Clause := do
  let kind ← str (← field j "kind")
  if kind == "fact" then
    keys j ["kind", "atom"]
    return .fact (← literal (← field j "atom"))
  else if kind == "rule" then
    keys j ["kind", "body", "head"]
    return .rule (← boundedItems 16 literal (← field j "body")) (← literal (← field j "head"))
  else invalid "unknown clause kind"

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

def certificate (expected : Source) (j : Json) : ProbeM Certificate := do
  keys j ["law_id", "source", "query_text", "clauses", "query", "steps", "known", "clean_steps", "clean_known"]
  if (← str (← field j "law_id")) != lawId then return ← invalid "unsupported law"
  let cs ← boundedItems 256 clause (← field j "clauses")
  let known ← boundedItems 512 (fun j => return (← literal j).lower expected.scope) (← field j "known")
  let p := lower expected cs
  let cp := clean p known
  return {
    source := ← source (← field j "source")
    queryRaw := (← str (← field j "query_text")).toUTF8.data.toList
    clauses := cs
    query := ← literal (← field j "query")
    steps := ← boundedItems 512 (step p) (← field j "steps")
    known := known
    cleanSteps := ← boundedItems 512 (step cp) (← field j "clean_steps")
    cleanKnown := ← boundedItems 512 (fun j => return (← literal j).lower expected.scope) (← field j "clean_known") }

def verdict (e : Evidence) : String :=
  match Nabt.SemanticInference.classify e.positive e.negative e.cleanPositive e.cleanNegative with
  | .supported => "SUPPORTED" | .refuted => "REFUTED" | .conflict => "CONFLICT"
  | .unknown => "UNKNOWN" | .deferred => "DEFER"

def response (fields : List (String × Json)) : Json := Json.mkObj (
  [("law_id", toJson lawId), ("scope", toJson "canonical_ground_source_entailment"),
   ("all_arabic_complete", toJson false), ("world_truth_established", toJson false)] ++ fields)

def failed (code message : String) : Json := response [
  ("verified", toJson false), ("error", toJson code), ("message", toJson message)]

def evaluate (s : Source) (q : List UInt8) (bytes : ByteArray) : Json :=
  match (do
    let some text := String.fromUTF8? bytes | invalid "certificate must be UTF-8"
    preflight text
    let j ← liftParse (Json.parse text)
    certificate s j : ProbeM Certificate) with
  | .error e => failed e.code e.message
  | .ok c => match execute s q c with
    | none => failed "CERTIFICATE_REJECTED" "source, reading or complete proof does not verify"
    | some e => response [
        ("verified", toJson true), ("status", toJson (verdict e)),
        ("source_id", toJson s.identity), ("revision", toJson s.revision),
        ("source_scope", toJson s.scope),
        ("source_text", toJson (render c.clauses)),
        ("query_text", toJson (String.fromUTF8! ⟨q.toArray⟩)),
        ("positive", toJson e.positive), ("negative", toJson e.negative),
        ("clean_positive", toJson e.cleanPositive), ("clean_negative", toJson e.cleanNegative)]

def readBounded (path : System.FilePath) (limit : Nat) : IO ByteArray := do
  let h ← IO.FS.Handle.mk path .read
  let bytes ← h.read (limit + 1).toUSize
  return bytes

def relationalFrame (j : Json) : ProbeM Nabt.RelationalBridge.Frame := do
  keys j ["reading_id", "stage", "occurrence_id", "entity", "kind", "property", "event",
    "time", "place", "cause", "start", "stop", "surface"]
  let rid ← str (← field j "reading_id")
  let some reading := Nabt.RelationalBridge.readings.find? (fun r => r.label == rid)
    | invalid "unknown installed relational reading"
  let stage ← match ← str (← field j "stage") with
    | "disposition" => pure Nabt.RelationalBridge.Stage.disposition
    | "occurrence" => pure .occurrence | "causality" => pure .causality
    | _ => invalid "unknown relational stage"
  let name (key : String) : ProbeM String := do
    let s ← str (← field j key)
    if !validName s || s.utf8ByteSize > 512 then return ← invalid "invalid relational identity"
    return s
  return ⟨reading, stage, ← name "occurrence_id", ← name "entity", ← name "kind",
    ← name "property", ← name "event", ← name "time", ← name "place", ← name "cause",
    ← nat (← field j "start"), ← nat (← field j "stop"), ← str (← field j "surface")⟩

def schemaJson (r : Nabt.RelationalBridge.Reading) : Json :=
  let s := Nabt.RelationalBridge.meaningSchema r
  Json.mkObj [("sense", toJson s.sense),
    ("slots", toJson (s.slots.map (·.label))),
    ("relations", toJson (s.relations.map fun (left, relation, right) =>
      Json.mkObj [("left", toJson left.label), ("relation", toJson relation), ("right", toJson right.label)]))]

def schemaCatalogue : Json := response [
  ("verified", toJson true), ("continuity_law_id", toJson Nabt.RelationalBridge.continuityLawId),
  ("schemas", toJson (Nabt.RelationalBridge.readings.map fun r => Json.mkObj [
    ("reading_id", toJson r.label), ("spellings", toJson r.spellings),
    ("schema", schemaJson r)])),
  ("schema_scope", toJson "INSTALLED_INTERPRETED_MEANING_SCHEMAS_NOT_WORLD_EXISTENCE")]

def binding (j : Json) : ProbeM (Nabt.RelationalBridge.SemanticSlot × Nabt.RelationalBridge.SlotBinding) := do
  keys j ["slot", "state", "value"]
  let name ← str (← field j "slot")
  let some slot := (Nabt.RelationalBridge.meaningSchema .yellowPast).slots.find? (fun s => s.label == name)
    | invalid "unknown schema slot"
  let state ← str (← field j "state")
  let value ← str (← field j "value")
  let v ← match state with
    | "unbound_variable" =>
      if value != "" then invalid "unbound variable cannot assert a value" else pure .unbound
    | "unknown_in_occurrence" =>
      if value != "" then invalid "unknown occurrence cannot assert a value" else pure .unknown
    | "bound_value" =>
      if !validName value || value.utf8ByteSize > 512 then invalid "invalid bound value" else pure (.bound value)
    | _ => invalid "physical slot state cannot be inapplicable or caller certified"
  return (slot, v)

def evaluateSchema (bytes : ByteArray) : Json :=
  match (do
    let some text := String.fromUTF8? bytes | invalid "schema request must be UTF-8"
    preflight text
    let j ← liftParse (Json.parse text)
    keys j ["reading_id", "bindings"]
    let rid ← str (← field j "reading_id")
    let some r := Nabt.RelationalBridge.readings.find? (fun r => r.label == rid)
      | invalid "unknown installed reading"
    let bs ← boundedItems 6 binding (← field j "bindings")
    return (r, bs) : ProbeM (Nabt.RelationalBridge.Reading × List
      (Nabt.RelationalBridge.SemanticSlot × Nabt.RelationalBridge.SlotBinding))) with
  | .error e => failed e.code e.message
  | .ok (r, bs) => response [
      ("verified", toJson true), ("continuity_law_id", toJson Nabt.RelationalBridge.continuityLawId),
      ("structurally_valid", toJson (Nabt.RelationalBridge.validInstance r ⟨Nabt.RelationalBridge.meaningSchema r, bs⟩)),
      ("schema", schemaJson r), ("reading_id", toJson r.label),
      ("bindings", toJson (bs.map fun (slot, value) => Json.mkObj [
        ("slot", toJson slot.label),
        ("state", toJson (match value with | .unbound => "unbound_variable" | .unknown => "unknown_in_occurrence" | .bound _ => "bound_value")),
        ("value", toJson (match value with | .bound v => v | _ => ""))])),
      ("binding_evidence_checked", toJson false)]

def evaluateRelational (s : Source) (q : List UInt8) (cert frameBytes targetBytes : ByteArray) : Json :=
  match (do
    let some ct := String.fromUTF8? cert | invalid "certificate must be UTF-8"
    let some ft := String.fromUTF8? frameBytes | invalid "frame must be UTF-8"
    let some target := String.fromUTF8? targetBytes | invalid "target must be UTF-8"
    preflight ct
    preflight ft
    let c ← certificate s (← liftParse (Json.parse ct))
    let f ← relationalFrame (← liftParse (Json.parse ft))
    if (Nabt.RelationalBridge.targetKey target).length > 512 then
      return ← limited "exact target key exceeds controlled-name budget"
    return (c, f, target) : ProbeM (Certificate × Nabt.RelationalBridge.Frame × String)) with
  | .error e => failed e.code e.message
  | .ok (c, f, target) =>
    if !verify s q c then failed "CERTIFICATE_REJECTED" "source reading or full/clean closure rejected"
    else
      let reqs := Nabt.RelationalBridge.requirementsV2 s.scope target f
      let qualified := Nabt.QualifiedInference.assess (Nabt.RelationalBridge.kind f) reqs c.known
      response [
        ("verified", toJson true), ("bridge_law_id", toJson Nabt.RelationalBridge.applicationLawId),
        ("licensed", toJson (Nabt.RelationalBridge.checkV2 s q c target f)),
        ("legacy_v1_licensed", toJson (Nabt.RelationalBridge.check s q c target f)),
        ("semantic_schema", schemaJson f.reading),
        ("qualified_verdict", toJson qualified.label),
        ("occurrence_bound", toJson (Nabt.RelationalBridge.occurrenceBound target f)),
        ("reading_candidates", toJson ((Nabt.RelationalBridge.candidates f.surface).map (·.label))),
        ("selected_reading", toJson f.reading.label), ("sense", toJson f.reading.sense),
        ("target_text", toJson target), ("source_text", toJson (render c.clauses)),
        ("source_id", toJson s.identity), ("revision", toJson s.revision), ("source_scope", toJson s.scope),
        ("requirements", toJson (reqs.map fun r => Json.mkObj [
          ("predicate", toJson r.atom.value.1), ("arguments", toJson r.atom.value.2),
          ("positive", toJson r.atom.positive), ("scope", toJson r.atom.scope),
          ("present", toJson (c.known.contains r.atom)),
          ("clean", toJson (c.cleanKnown.contains r.atom)),
          ("opposed", toJson (c.known.contains r.atom.opposite))])),
        ("grammar_acquisition_proved", toJson false),
        ("source_interpretation", toJson "DECLARED_CONTROLLED_RELATIONAL_PREDICATES")]

end VerifiedReadingMain
open VerifiedReadingMain

def main (args : List String) : IO UInt32 := do
  let out ← IO.getStdout
  match args with
  | ["relational-schemas"] =>
    out.putStrLn schemaCatalogue.compress
    return 0
  | ["relational-schema", requestPath] =>
    try
      let bytes ← readBounded requestPath 16384
      if bytes.size > 16384 then
        out.putStrLn (failed "RESOURCE_LIMIT" "schema request byte budget").compress
        return 2
      let result := evaluateSchema bytes
      out.putStrLn result.compress
      return if (result.getObjValAs? Bool "verified").toOption == some true then 0 else 1
    catch e =>
      out.putStrLn (failed "IO_ERROR" e.toString).compress
      return 2
  | ["relational", sourcePath, queryPath, certificatePath, framePath, targetPath, identity, revision, scope] =>
    try
      let raw ← readBounded sourcePath 65536
      let query ← readBounded queryPath 8192
      let cert ← readBounded certificatePath 1048576
      let frameBytes ← readBounded framePath 16384
      let target ← readBounded targetPath 32768
      if raw.size > 65536 || query.size > 8192 || cert.size > 1048576 || frameBytes.size > 16384 || target.size > 32768 then
        out.putStrLn (failed "RESOURCE_LIMIT" "relational input byte budget").compress
        return 2
      if identity.isEmpty || revision.isEmpty || scope.isEmpty then
        out.putStrLn (failed "INVALID_INPUT" "missing independent source identity").compress
        return 2
      let result := evaluateRelational ⟨identity, revision, scope, raw.data.toList⟩ query.data.toList cert frameBytes target
      out.putStrLn result.compress
      return if (result.getObjValAs? Bool "verified").toOption == some true then 0 else 1
    catch e =>
      out.putStrLn (failed "IO_ERROR" e.toString).compress
      return 2
  | [sourcePath, queryPath, certificatePath, identity, revision, scope] =>
    try
      let raw ← readBounded sourcePath 65536
      let query ← readBounded queryPath 8192
      let cert ← readBounded certificatePath 1048576
      if raw.size > 65536 || query.size > 8192 || cert.size > 1048576 then
        out.putStrLn (failed "RESOURCE_LIMIT" "file exceeds byte budget").compress
        return 2
      if identity.isEmpty || revision.isEmpty || scope.isEmpty then
        out.putStrLn (failed "INVALID_INPUT" "source identity, revision and scope must be nonempty").compress
        return 2
      let result := evaluate ⟨identity, revision, scope, raw.data.toList⟩ query.data.toList cert
      out.putStrLn result.compress
      return if (result.getObjValAs? Bool "verified").toOption == some true then 0 else 1
    catch e =>
      out.putStrLn (failed "IO_ERROR" e.toString).compress
      return 2
  | _ =>
    out.putStrLn (failed "INVALID_ARGUMENTS" "expected SOURCE QUERY CERTIFICATE ID REVISION SCOPE").compress
    return 2
