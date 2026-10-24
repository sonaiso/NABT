import Nabt.VerifiedReading
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

end VerifiedReadingMain
open VerifiedReadingMain

def main (args : List String) : IO UInt32 := do
  let out ← IO.getStdout
  match args with
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
