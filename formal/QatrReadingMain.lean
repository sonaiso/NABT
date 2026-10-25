import Nabt.QatrReading
import ProbeJson

open Lean ProbeJson Nabt.QatrReading
open Nabt.Words (Kind DeclensionClass)
namespace QatrReadingMain

def caseLabel : Nabt.Governors.Case → String
  | .nasb => "nasb" | .raf => "raf" | .jarr => "jarr" | .jazm => "jazm"

def rowJson (r : Nabt.InflectionEvidence.Row) : Json := Json.mkObj [
  ("id", toJson (Nabt.Words.classCaseNumber r.cls r.grammaticalCase)),
  ("class", toJson r.cls.label), ("kind", toJson r.cls.kind.label),
  ("case", toJson (caseLabel r.grammaticalCase)),
  ("mark", toJson (observe r.realization).label)]

def result (q : Query) : Json := Json.mkObj [
  ("kind", toJson q.kind.label), ("mark", toJson q.mark.label),
  ("rows", Json.arr ((read q).map rowJson).toArray),
  ("cases", toJson ((casesFor q).map caseLabel))]

def table : Json := Json.mkObj [
  ("law_id", toJson lawId), ("source_sha256", toJson sourceSha256),
  ("scope", toJson "conditional inflection table; supplied declinability and class conditions"),
  ("rows", Json.arr (Nabt.InflectionEvidence.rows.map rowJson).toArray),
  ("queries", Json.arr (([Kind.noun, Kind.verb, Kind.particle].flatMap fun k =>
    marks.map fun m => result ⟨k, m, none⟩)).toArray)]

def parseKind (j : Json) : ProbeM Kind := do
  let s ← str j
  match Nabt.Words.kinds.find? (fun k => k.label == s) with
  | some k => return k
  | none => invalid "unknown kind"

def parseMark (j : Json) : ProbeM Mark := do
  let s ← str j
  match marks.find? (fun m => m.label == s) with
  | some m => return m
  | none => invalid "unknown mark"

def parseClasses (j : Json) : ProbeM (Option (List DeclensionClass)) := do
  if j == Json.null then return none
  let xs ← liftParse j.getArr?
  if xs.size > 15 then return ← limited "too many classes"
  let cs ← xs.toList.mapM fun item => do
    let s ← str item
    match Nabt.Words.declensionClasses.find? (fun c => c.label == s) with
    | some c => pure c
    | none => invalid "unknown class"
  return some cs

def dispatch (j : Json) : ProbeM Json := do
  let obj ← liftParse j.getObj?
  let names := ["kind", "mark", "classes", "proposed"]
  if obj.size != 4 || names.any (fun n => (obj.get? n).isNone) then
    return ← invalid "exactly kind, mark, classes, proposed required"
  let q : Query := ⟨← parseKind (← field j "kind"), ← parseMark (← field j "mark"),
    ← parseClasses (← field j "classes")⟩
  let p ← field j "proposed"
  if p == Json.null then return result q
  let xs ← liftParse p.getArr?
  if xs.size > 60 then return ← limited "too many readings"
  let proposed ← xs.toList.mapM fun item => do
    let n ← nat item
    match Nabt.InflectionEvidence.rows.find? (fun r =>
      Nabt.Words.classCaseNumber r.cls r.grammaticalCase == n) with
    | some r => pure r
    | none => invalid "not a legal class-case identity"
  return Json.mkObj [("result", result q),
    ("complete_proposal", toJson (completeProposal q proposed)),
    ("authority", toJson "CONDITIONAL_TABLE_ONLY")]

def errorJson (e : Failure) : Json := Json.mkObj [
  ("status", toJson e.code), ("message", toJson e.message)]
end QatrReadingMain

def main (args : List String) : IO Unit := do
  let output ← IO.getStdout
  if args == ["--export"] then output.putStrLn QatrReadingMain.table.compress
  else if args.isEmpty then
    ProbeJson.readLoop QatrReadingMain.dispatch QatrReadingMain.errorJson
      (← IO.getStdin) output (ByteArray.emptyWithCapacity 0) false
  else throw (IO.userError "usage: qatrReading [--export]")
