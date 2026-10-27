import Nabt.LexicalSurfaceBinding
import ProbeJson

open Lean ProbeJson Nabt.LexicalSurfaceBinding
namespace LexicalSurfaceMain

def exact (value : Json) (keys : List String) : ProbeM Unit := do
  let obj ← liftParse value.getObj?
  if obj.size != keys.length || keys.any (fun key => (obj.get? key).isNone) then
    invalid "unexpected or missing field" else pure ()

def label (value : Json) : ProbeM String := do
  let value ← str value
  if value.isEmpty || value.utf8ByteSize > 1024 then invalid "empty or long label"
  else pure value

def text (value : Json) : ProbeM String := do
  let value ← str value
  if value.utf8ByteSize > 65536 then limited "source exceeds 65536 bytes" else pure value

def source (value : Json) : ProbeM Nabt.Foundation.Source := do
  exact value ["id", "revision", "text"]
  return ⟨← label (← field value "id"), ← label (← field value "revision"),
    ← text (← field value "text")⟩

def binding (value : Json) : ProbeM Nabt.Foundation.LayerBinding := do
  exact value ["source", "scope_id", "occurrence_id", "reading_id", "start_byte", "end_byte", "surface"]
  return ⟨← source (← field value "source"), ← label (← field value "scope_id"),
    ← label (← field value "occurrence_id"), ← label (← field value "reading_id"),
    ← nat (← field value "start_byte"), ← nat (← field value "end_byte"),
    ← text (← field value "surface")⟩

def witness (value : Json) : ProbeM Witness := do
  exact value ["id", "binding", "expression", "convention"]
  return ⟨← label (← field value "id"), ← binding (← field value "binding"),
    ← label (← field value "expression"), ← label (← field value "convention")⟩

def frame (value : Json) : ProbeM Nabt.LinguisticTruth.Frame := do
  exact value ["occurrence", "expression", "convention"]
  let occurrence ← field value "occurrence"
  exact occurrence ["source", "revision", "raw", "start_byte", "end_byte", "referent", "time", "context"]
  return ⟨⟨← label (← field occurrence "source"), ← label (← field occurrence "revision"),
    ← text (← field occurrence "raw"), ← nat (← field occurrence "start_byte"),
    ← nat (← field occurrence "end_byte"), ← label (← field occurrence "referent"),
    ← label (← field occurrence "time"), ← label (← field occurrence "context")⟩,
    ← label (← field value "expression"), ← label (← field value "convention")⟩

def dispatch (value : Json) : ProbeM Json := do
  exact value ["source", "frame", "surface", "witnesses"]
  let s ← source (← field value "source")
  let fj ← field value "frame"
  let f ← frame fj
  let surface ← text (← field value "surface")
  let array ← liftParse (← field value "witnesses").getArr?
  if array.size > 128 then return ← limited "witness ledger exceeds 128 rows"
  let ledger ← array.toList.mapM witness
  if (ledger.map (·.id)).eraseDups.length != ledger.length then
    return ← invalid "duplicate witness identity"
  let matched := witnesses s f surface ledger
  let occurrence := occurrenceBinding s f surface
  return Json.mkObj [
    ("schema", toJson lawId), ("source", ← field value "source"), ("frame", fj),
    ("surface", toJson surface), ("projection_status", toJson occurrence.projection.status.label),
    ("cells", toJson (occurrence.projection.cells.map Fin.val)),
    ("number", toJson (toString occurrence.projection.number)),
    ("occurrence_exact", toJson (decide occurrence.Exact)),
    ("witness_count", toJson ledger.length), ("matched_ids", toJson (matched.map (·.id))),
    ("status", toJson (if matched.isEmpty then "NO_EXACT_WITNESS" else "CHECKED_EXACT_SURFACE")),
    ("intended_sense_established", toJson false), ("whole_arabic_complete", toJson false)]

def errorJson (e : Failure) : Json := Json.mkObj [("status", toJson e.code), ("message", toJson e.message)]

end LexicalSurfaceMain

def main (args : List String) : IO Unit := do
  if !args.isEmpty then throw (IO.userError "usage: lexicalSurface (bounded JSONL)")
  ProbeJson.readLoop LexicalSurfaceMain.dispatch LexicalSurfaceMain.errorJson
    (← IO.getStdin) (← IO.getStdout) (ByteArray.emptyWithCapacity 0) false
