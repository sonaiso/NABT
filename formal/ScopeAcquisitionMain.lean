import Nabt.ScopeAcquisition
import ProbeJson

open Lean ProbeJson Nabt.ScopeAcquisition
namespace ScopeAcquisitionMain

def sourceJson (source : Nabt.Foundation.Source) : Json := Json.mkObj [
  ("id", toJson source.id), ("revision", toJson source.revision), ("text", toJson source.text)]

def projectionJson (source : Nabt.Foundation.Source) : Json :=
  let receipt := Nabt.Foundation.project source
  Json.mkObj [("status", toJson (match receipt.status with
      | .complete => "COMPLETE" | .incomplete => "INCOMPLETE" | .invalid => "INVALID")),
    ("alphabet_id", toJson Nabt.Foundation.alphabetId),
    ("number_domain", toJson Nabt.Foundation.numberDomain),
    ("cells", toJson (receipt.cells.map Fin.val)), ("number", toJson (toString receipt.number))]

def envelopeJson (source : Nabt.Foundation.Source) (e : Envelope) : Json := Json.mkObj [
  ("kind", toJson (match e.kind with
    | .quoted => "quoted_speaker" | .negated => "negated_embedding" | .hypothetical => "hypothetical")),
  ("speaker_label", toJson e.speaker), ("body", toJson e.body), ("tail", toJson e.tail),
  ("full_stop", toJson e.fullStop), ("start_byte", toJson e.startByte), ("end_byte", toJson e.endByte),
  ("prefix", toJson e.prefix), ("suffix", toJson e.suffix),
  ("projects_to_narrator", toJson e.projectsToNarrator),
  ("body_projection", projectionJson (e.bodySource source))]

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
    return ← limited "scope request budget"
  let source : Nabt.Foundation.Source := ⟨id, revision, text⟩
  let envelope := acquire source
  return Json.mkObj [
    ("schema", toJson lawId), ("source", sourceJson source), ("context", toJson context),
    ("source_projection", projectionJson source),
    ("status", toJson (if envelope.isSome then "CHECKED_SCOPE_ENVELOPE" else "OUTSIDE_EXECUTED_SCOPE")),
    ("envelope", match envelope with | none => Json.null | some e => envelopeJson source e),
    ("body_syntax_established", toJson false), ("intended_sense_established", toJson false),
    ("speaker_reference_established", toJson false), ("external_truth_established", toJson false),
    ("strict_language_accepted", toJson false), ("whole_arabic_complete", toJson false)]

def errorJson (failure : Failure) : Json :=
  Json.mkObj [("status", toJson failure.code), ("message", toJson failure.message)]

end ScopeAcquisitionMain

def main (args : List String) : IO Unit := do
  if !args.isEmpty then throw (IO.userError "usage: scopeAcquisition (bounded JSONL)")
  ProbeJson.readLoop ScopeAcquisitionMain.dispatch ScopeAcquisitionMain.errorJson
    (← IO.getStdin) (← IO.getStdout) (ByteArray.emptyWithCapacity 0) false
