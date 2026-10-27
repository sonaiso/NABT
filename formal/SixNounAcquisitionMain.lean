import Nabt.SixNounAcquisition
import ProbeJson

open Lean ProbeJson Nabt.SixNounAcquisition
namespace SixNounAcquisitionMain

def sourceJson (source : Nabt.Foundation.Source) : Json := Json.mkObj [
  ("id", toJson source.id), ("revision", toJson source.revision), ("text", toJson source.text)]

def projectionJson (source : Nabt.Foundation.Source) : Json :=
  let p := Nabt.Foundation.project source
  Json.mkObj [("status", toJson (match p.status with
      | .complete => "COMPLETE" | .incomplete => "INCOMPLETE" | .invalid => "INVALID")),
    ("alphabet_id", toJson Nabt.Foundation.alphabetId),
    ("number_domain", toJson Nabt.Foundation.numberDomain),
    ("cells", toJson (p.cells.map Fin.val)), ("number", toJson (toString p.number))]

def prerequisite (name state origin : String) : Json := Json.mkObj [
  ("name", toJson name), ("state", toJson state), ("origin", toJson origin)]

def prerequisites (r : Reading) : List Json := [
  prerequisite "exact_full_form_profile" "affirmed" "exact_source_spelling",
  prerequisite "singular_non_diminutive" "affirmed" "declared_finite_lexical_profile",
  prerequisite "idafa_to_non_speaker_ya" "affirmed" "exact_complement_template",
  prerequisite "fu_meem_removed" (if r.lexeme = .fu then "affirmed" else "not_applicable") "exact_source_spelling",
  prerequisite "dhu_companionship" (if r.lexeme = .dhu then "unknown" else "not_applicable") "not_acquired_from_surface",
  prerequisite "required_case_matches_observed_ending"
    (if r.ending = r.governor.expected then "affirmed" else "denied") "declared_governor_template"]

def readingJson (r : Reading) : Json := Json.mkObj [
  ("governor", toJson r.governor.label), ("lexeme", toJson r.lexeme.label),
  ("ending", toJson r.ending.label), ("complement", toJson r.complement.label),
  ("prefix", toJson r.governor.prefix), ("word", toJson r.word),
  ("complement_text", toJson r.complement.text),
  ("start_byte", toJson r.startByte), ("end_byte", toJson r.endByte),
  ("grammatical_case", toJson r.governor.expected.caseLabel),
  ("observed_case", toJson r.ending.caseLabel),
  ("convention", toJson Nabt.InflectionEvidence.convention),
  ("prerequisites", toJson (prerequisites r)), ("alternatives", toJson (alternatives r))]

def bridgeJson (r : Reading) : Json := Json.mkObj [
  ("profile", toJson orthographicProfile), ("raw", toJson r.render),
  ("canonical", toJson r.canonical), ("cells", toJson (r.projection.cells.map Fin.val)),
  ("number", toJson (toString r.projection.number)),
  ("raw_reconstruction_checked", toJson true),
  ("canonical_projection_complete", toJson (r.projection.status == .complete))]

def dispatch (value : Json) : ProbeM Json := do
  let obj ← liftParse value.getObj?
  if obj.size != 2 || (obj.get? "source").isNone || (obj.get? "context").isNone then
    return ← invalid "expected source and context only; caller features and proof flags are forbidden"
  let rawSource ← field value "source"
  let sourceFields ← liftParse rawSource.getObj?
  if sourceFields.size != 3 || (sourceFields.get? "id").isNone ||
      (sourceFields.get? "revision").isNone || (sourceFields.get? "text").isNone then
    return ← invalid "source must contain exactly id, revision and text"
  let id ← atom (← field rawSource "id")
  let revision ← atom (← field rawSource "revision")
  let text ← str (← field rawSource "text")
  let context ← str (← field value "context")
  if text.utf8ByteSize > 4096 || id.utf8ByteSize > 1024 ||
      revision.utf8ByteSize > 1024 || context.utf8ByteSize > 4096 then
    return ← limited "six-noun source request budget"
  let source : Nabt.Foundation.Source := ⟨id, revision, text⟩
  let original := Nabt.Foundation.project source
  let reading := acquire source
  let certificate := certify source context
  let status := if original.status = .invalid then "INVALID_SOURCE"
    else if certificate.isSome then "CHECKED_SIX_NOUN"
    else if reading.isSome then "DEFER" else "OUTSIDE_EXECUTED_FRAGMENT"
  let residuals := match reading with
    | some r => unresolved r
    | none => if original.status = .invalid then ["INVALID_SOURCE_MARKS_OR_EMPTY"]
      else ["OUTSIDE_EXACT_TEMPLATE_OR_VARIANT_NOT_ACQUIRED"]
  return Json.mkObj [
    ("schema", toJson lawId), ("law_id", toJson lawId),
    ("source", sourceJson source), ("context", toJson context),
    ("source_projection", projectionJson source), ("status", toJson status),
    ("reading", match reading with | none => Json.null | some r => readingJson r),
    ("grammar_certified", toJson certificate.isSome),
    ("foundation_complete", toJson (original.status == .complete)),
    ("orthographic_bridge", match reading with | none => Json.null | some r => bridgeJson r),
    ("unresolved", toJson residuals), ("source_restored", toJson true),
    ("intended_sense_established", toJson false),
    ("external_truth_established", toJson false),
    ("strict_language_accepted", toJson false), ("whole_arabic_complete", toJson false)]

def errorJson (failure : Failure) : Json :=
  Json.mkObj [("status", toJson failure.code), ("message", toJson failure.message)]

end SixNounAcquisitionMain

def main (args : List String) : IO Unit := do
  if !args.isEmpty then throw (IO.userError "usage: sixNounAcquisition (bounded JSONL)")
  ProbeJson.readLoop SixNounAcquisitionMain.dispatch SixNounAcquisitionMain.errorJson
    (← IO.getStdin) (← IO.getStdout) (ByteArray.emptyWithCapacity 0) false
