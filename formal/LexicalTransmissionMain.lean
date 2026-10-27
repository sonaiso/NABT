import Nabt.LexicalTransmission
import ProbeJson

open Lean ProbeJson Nabt.LexicalTransmission
namespace LexicalTransmissionMain

def citationJson (c : Nabt.LexicalDenotation.Citation) : Json := Json.mkObj [
  ("work", toJson c.work), ("revision", toJson c.revision),
  ("source_sha256", toJson c.sourceSha256), ("start_byte", toJson c.startByte),
  ("end_byte", toJson c.endByte), ("quotation", toJson c.quotation)]

def reportJson (r : Report) : Json := Json.mkObj [
  ("entry", toJson r.claim.entry), ("sense_id", toJson r.claim.reading),
  ("context", toJson r.claim.context), ("source_family", toJson r.source),
  ("citation", citationJson r.citation),
  ("documentary_status", toJson (classify installedReviews r.claim [r]).label)]

def table : Json := Json.mkObj [
  ("law_id", toJson lawId),
  ("reports", toJson (Nabt.LexicalCatalog.senses.map (fun s => reportJson (reportOf "" s)))),
  ("dependency_reviews", toJson ([] : List String))]

def dispatch (j : Json) : ProbeM Json := do
  let obj ← liftParse j.getObj?
  if obj.size != 2 || ["entry", "context"].any (fun n => (obj.get? n).isNone) then
    return ← invalid "exactly entry and context required"
  let entry ← str (← field j "entry")
  let context ← str (← field j "context")
  if entry.isEmpty then return ← invalid "empty lexical index"
  if entry.utf8ByteSize > 128 || context.utf8ByteSize > 65536 then
    return ← limited "entry or context exceeds byte limit"
  let reports := installedReports entry context
  let ids := sources reports
  return Json.mkObj [
    ("law_id", toJson lawId), ("entry", toJson entry), ("context", toJson context),
    ("status", toJson (if reports.isEmpty then "UNMEASURED_ROOT" else "DOCUMENTARY_REPORTS")),
    ("reports", toJson (reports.map reportJson)),
    ("source_families", toJson ids),
    ("dependency_reviews", toJson ([] : List String)),
    ("source_relationship_status", toJson
      (if ids.length < 2 then "NOT_A_MULTISOURCE_ASSESSMENT" else "INDEPENDENCE_UNASSESSED")),
    ("cross_source_sense_alignment_established", toJson false),
    ("tawatur_established", toJson false),
    ("historical_authenticity_established", toJson false),
    ("intended_sense_established", toJson false),
    ("world_truth_established", toJson false),
    ("strict_language_accepted", toJson false)]

def errorJson (e : Failure) : Json :=
  Json.mkObj [("status", toJson e.code), ("message", toJson e.message)]
end LexicalTransmissionMain

def main (args : List String) : IO Unit := do
  let output ← IO.getStdout
  if args == ["--export"] then output.putStrLn LexicalTransmissionMain.table.compress
  else if args.isEmpty then
    ProbeJson.readLoop LexicalTransmissionMain.dispatch LexicalTransmissionMain.errorJson
      (← IO.getStdin) output (ByteArray.emptyWithCapacity 0) false
  else throw (IO.userError "usage: lexicalTransmission [--export]")
