import Nabt.LisanRules
import Nabt.MaqayisDenotation
import ProbeJson

open Lean ProbeJson Nabt.LexicalDenotation Nabt.LexicalCatalog
namespace LexicalDenotationMain

def citationJson (c : Citation) : Json := Json.mkObj [
  ("work", toJson c.work), ("revision", toJson c.revision),
  ("source_sha256", toJson c.sourceSha256), ("start_byte", toJson c.startByte),
  ("end_byte", toJson c.endByte), ("quotation", toJson c.quotation)]

def senseJson (s : Sense) : Json := Json.mkObj [
  ("id", toJson s.id), ("root", toJson s.root), ("citation", citationJson s.citation),
  ("components", toJson s.components)]

def kinds : List Indication := [.matching, .inclusion, .entailment]

def table : Json := Json.mkObj [
  ("law_id", toJson lawId), ("authority", toJson "CONDITIONAL_INTERPRETATION_ONLY"),
  ("senses", Json.arr (senses.map senseJson).toArray),
  ("necessities", Json.arr (necessities.map fun r => Json.mkObj [
    ("sense_id", toJson r.sense.id), ("target", toJson r.target),
    ("kind", toJson "mental"), ("citation", citationJson r.citation)]).toArray)]

def strings (j : Json) : ProbeM (List String) := do
  let xs ← liftParse j.getArr?
  if xs.size > 64 then return ← limited "at most 64 values"
  xs.toList.mapM fun x => do
    let s ← str x
    if s.utf8ByteSize > 4096 then return ← limited "value exceeds 4096 UTF8 bytes"
    if s.isEmpty then return ← invalid "empty identity"
    return s

def dispatch (j : Json) : ProbeM Json := do
  let obj ← liftParse j.getObj?
  let names := ["root", "target", "proposed_ids"]
  if obj.size != 3 || names.any (fun n => (obj.get? n).isNone) then
    return ← invalid "exactly root, target, proposed_ids required"
  let root ← str (← field j "root")
  if root.isEmpty then return ← invalid "empty root index"
  if root.utf8ByteSize > 128 then return ← limited "root index too long"
  let target ← strings (← field j "target")
  let proposed ← field j "proposed_ids"
  let rows := forRoot root
  let proposedIds ← if proposed == Json.null then pure none else some <$> strings proposed
  let complete := proposedIds.map (fun ids => !rows.isEmpty && decide (ids = rows.map Sense.id))
  return Json.mkObj [
    ("status", toJson (if rows.isEmpty then "UNMEASURED_ROOT" else "CONDITIONAL_INTERPRETATIONS")),
    ("authority", toJson "CONDITIONAL_INTERPRETATION_ONLY"),
    ("all_arabic_senses_enumerated", toJson false),
    ("world_truth_asserted", toJson false),
    ("complete_installed_proposal", toJson complete),
    ("rows", Json.arr (rows.map fun s => Json.mkObj [
      ("sense", senseJson s),
      ("indications", toJson ((kinds.filter (fun k => check necessities s k target)).map Indication.label))]).toArray),
    ("common_indications", toJson ((kinds.filter (fun k => across necessities (rows.map some) k target)).map Indication.label))]

def errorJson (e : Failure) : Json := Json.mkObj [("status",toJson e.code),("message",toJson e.message)]
end LexicalDenotationMain

def main (args : List String) : IO Unit := do
  let output ← IO.getStdout
  if args == ["--export"] then output.putStrLn LexicalDenotationMain.table.compress
  else if args.isEmpty then
    ProbeJson.readLoop LexicalDenotationMain.dispatch LexicalDenotationMain.errorJson
      (← IO.getStdin) output (ByteArray.emptyWithCapacity 0) false
  else throw (IO.userError "usage: lexicalDenotation [--export]")
