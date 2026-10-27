import Nabt.DiscourseBoundaryCueBridge
import ProbeJson

open Lean ProbeJson Nabt.DiscourseBoundaryCueBridge
namespace DiscourseBoundaryCueMain

def sourceJson (source : Nabt.Foundation.Source) : Json := Json.mkObj [
  ("id", toJson source.id), ("revision", toJson source.revision), ("text", toJson source.text)]

def projectionJson (source : Nabt.Foundation.Source) : Json :=
  let receipt := Nabt.Foundation.project source
  Json.mkObj [("status", toJson (match receipt.status with
      | .complete => "COMPLETE" | .incomplete => "INCOMPLETE" | .invalid => "INVALID")),
    ("alphabet_id", toJson Nabt.Foundation.alphabetId),
    ("number_domain", toJson Nabt.Foundation.numberDomain),
    ("cells", toJson (receipt.cells.map Fin.val)), ("number", toJson (toString receipt.number))]

def envelopeJson (e : Envelope) : Json := Json.mkObj [
  ("negation_prefix", toJson (String.ofList (negativePrefix e.markedNegative))),
  ("denied_body", toJson e.deniedText), ("boundary", toJson "؛ "),
  ("conjunction", toJson (String.ofList (conjunction e.markedCue))),
  ("cue_prefix", toJson (String.ofList (cuePrefix e.markedCue))),
  ("cue_body", toJson (String.ofList e.cueBody)),
  ("denied_start_byte", toJson e.deniedStart), ("denied_end_byte", toJson e.deniedEnd),
  ("cue_text", toJson e.cueText),
  ("cue_start_byte", toJson e.cueStart), ("cue_end_byte", toJson e.cueEnd),
  ("full_stop", toJson e.fullStop), ("projects_denied_to_positive", toJson false)]

def dispatch (value : Json) : ProbeM Json := do
  let obj ← liftParse value.getObj?
  if obj.size != 2 || (obj.get? "source").isNone || (obj.get? "context").isNone then
    return ← invalid "expected source and context only; no caller scope or checker flags"
  let valueSource ← field value "source"
  let sourceFields ← liftParse valueSource.getObj?
  if sourceFields.size != 3 || (sourceFields.get? "id").isNone ||
      (sourceFields.get? "revision").isNone || (sourceFields.get? "text").isNone then
    return ← invalid "source must contain exactly id, revision and text"
  let id ← atom (← field valueSource "id")
  let revision ← atom (← field valueSource "revision")
  let text ← atom (← field valueSource "text")
  let context ← atom (← field value "context")
  if text.utf8ByteSize > 16384 || id.utf8ByteSize > 1024 ||
      revision.utf8ByteSize > 1024 || context.utf8ByteSize > 4096 then
    return ← limited "discourse boundary request budget"
  let source : Nabt.Foundation.Source := ⟨id, revision, text⟩
  let all := readings source
  return Json.mkObj [
    ("schema", toJson lawId), ("source", sourceJson source), ("context", toJson context),
    ("source_projection", projectionJson source),
    ("status", toJson (if all.isEmpty then "OUTSIDE_EXECUTED_DISCOURSE" else "CHECKED_DISCOURSE_BOUNDARY")),
    ("envelope", match all.head? with | none => Json.null | some e => envelopeJson e),
    ("licensed_envelope_count", toJson all.length),
    ("denied_body_syntax_established", toJson false),
    ("cue_body_syntax_established", toJson false),
    ("intended_sense_established", toJson false),
    ("external_truth_established", toJson false),
    ("strict_language_accepted", toJson false), ("whole_arabic_complete", toJson false)]

def errorJson (failure : Failure) : Json :=
  Json.mkObj [("status", toJson failure.code), ("message", toJson failure.message)]

end DiscourseBoundaryCueMain

def main (args : List String) : IO Unit := do
  if !args.isEmpty then throw (IO.userError "usage: discourseBoundaryCue (bounded JSONL)")
  ProbeJson.readLoop DiscourseBoundaryCueMain.dispatch DiscourseBoundaryCueMain.errorJson
    (← IO.getStdin) (← IO.getStdout) (ByteArray.emptyWithCapacity 0) false
