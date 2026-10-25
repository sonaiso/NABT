import Nabt.LexicalCompletion
import Nabt.LexicalCompletionCatalog
import ProbeJson

open Lean ProbeJson Nabt Nabt.LexicalDenotation Nabt.LexicalCompletion
namespace LexicalCompletionMain
open LexicalCompletionCatalog

def citationJson (c : Citation) : Json := Json.mkObj [
  ("work", toJson c.work), ("revision", toJson c.revision),
  ("source_sha256", toJson c.sourceSha256), ("start_byte", toJson c.startByte),
  ("end_byte", toJson c.endByte), ("quotation", toJson c.quotation)]

def senseJson (s : Sense) : Json := Json.mkObj [
  ("id", toJson s.id), ("root", toJson s.root), ("citation", citationJson s.citation),
  ("components", toJson s.components)]

def table : Json := Json.mkObj [
  ("law_id", toJson LexicalCompletion.lawId), ("catalogue_id", toJson catalogueId),
  ("semantic_law", toJson LexicalDenotation.lawId),
  ("senses", Json.arr (senses.map senseJson).toArray),
  ("necessities", Json.arr (necessities.map fun r => Json.mkObj [
    ("sense_id", toJson r.sense.id), ("target", toJson r.target),
    ("kind", toJson "mental"), ("citation", citationJson r.citation)]).toArray)]

def exactFields (j : Json) (names : List String) : ProbeM Unit := do
  let obj ← liftParse j.getObj?
  if obj.size != names.length || names.any (fun n => (obj.get? n).isNone) then
    invalid "unexpected or missing field"
  else pure ()

def text (j : Json) (limit : Nat) : ProbeM String := do
  let s ← str j
  if s.isEmpty || s.toList.all Char.isWhitespace || s.toList.any (fun c => c.toNat < 32) then
    return ← invalid "empty or control-bearing identity"
  if s.utf8ByteSize > limit then return ← limited "text byte limit"
  return s

def parseSlot (j : Json) : ProbeM Slot := do
  exactFields j ["entry", "target"]
  let entry ← text (← field j "entry") 128
  let xs ← liftParse (← field j "target").getArr?
  if xs.size > 64 then return ← limited "target component limit"
  let target ← xs.toList.mapM (fun s => text s 4096)
  return ⟨entry, target⟩

def maxCombinations : Nat := 512

def dispatch (j : Json) : ProbeM Json := do
  exactFields j ["slots"]
  let xs ← liftParse (← field j "slots").getArr?
  if xs.isEmpty then return ← invalid "at least one ordered slot required"
  if xs.size > 8 then return ← limited "at most eight ordered slots"
  let slots ← xs.toList.mapM parseSlot
  -- A binding to this dictionary request, not to a parsed Arabic occurrence.
  let binding : SourceSemantics.Binding := ⟨j.compress.toUTF8.toList,
    LexicalCompletion.lawId, "ordered-dictionary-slots", [], table.compress.toUTF8.toList⟩
  let pools := slots.zipIdx |>.map fun (slot, i) =>
    pool binding (toString i) senses necessities slot
  let count := ReadingEnumeration.count pools
  let verdict := boundedReady maxCombinations pools
  let rows := if verdict.isNone then [] else ReadingEnumeration.enumerate pools
  let rowReady := fun row : List ReadingEnumeration.Alternative =>
    row.all (fun a => a.premises.isSome)
  let unknown := slots.any (fun slot => (selected senses slot.entry).isEmpty)
  let unresolved := slots.any (fun slot => (selected senses slot.entry).any (fun s => s.components.isEmpty))
  let status := if verdict.isNone then "RESOURCE_EXHAUSTED"
    else if unknown then "UNMEASURED_ENTRY"
    else if unresolved then "UNMEASURED_DEFINITION"
    else if verdict == some true then "CONDITIONAL_ALL_READINGS"
    else if rows.any rowReady then "CONDITIONAL_SOME_READINGS"
    else "NO_LICENSE_FOR_TARGETS"
  return Json.mkObj [
    ("law_id", toJson LexicalCompletion.lawId), ("status", toJson status),
    ("combination_count", toJson count), ("combination_limit", toJson maxCombinations),
    ("all_installed_combinations_checked", toJson verdict.isSome),
    ("all_targets_licensed", toJson verdict),
    ("slots", Json.arr (slots.zipIdx |>.map fun (slot, i) => Json.mkObj [
      ("position", toJson i), ("entry", toJson slot.entry), ("target", toJson slot.target),
      ("readings", Json.arr ((selected senses slot.entry).map fun s => Json.mkObj [
        ("sense_id", toJson s.id), ("definition_present", toJson (!s.components.isEmpty)),
        ("indications", toJson ((kinds.filter (fun k => check necessities s k slot.target)).map Indication.label))]).toArray)]).toArray),
    ("combinations", Json.arr (rows.map fun row => Json.mkObj [
      ("sense_ids", toJson (row.map ReadingEnumeration.Alternative.identity)),
      ("targets_licensed", toJson (rowReady row))]).toArray)]

def errorJson (e : Failure) : Json := Json.mkObj [("status",toJson e.code),("message",toJson e.message)]
end LexicalCompletionMain

def main (args : List String) : IO Unit := do
  let output ← IO.getStdout
  if args == ["--export"] then output.putStrLn LexicalCompletionMain.table.compress
  else if args.isEmpty then
    ProbeJson.readLoop LexicalCompletionMain.dispatch LexicalCompletionMain.errorJson
      (← IO.getStdin) output (ByteArray.emptyWithCapacity 0) false
  else throw (IO.userError "usage: lexicalCompletion [--export]")
