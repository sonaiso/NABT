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
  ("canonical_projection_complete", toJson (r.projection.status == Nabt.Foundation.Status.complete))]

def faceJson (face : Nabt.RecursiveLicensedAlgebra.Face) : Json := Json.mkObj [
  ("category", toJson (match face.category with
    | .root3 => "root3" | .root4 => "root4" | .noun => "noun" | .verb => "verb"
    | .particle => "particle" | .nounPhrase => "nounPhrase" | .verbPhrase => "verbPhrase"
    | .semiClause => "semiClause" | .nominalClause => "nominalClause"
    | .verbalClause => "verbalClause" | .clause => "clause" | .pending => "pending")),
  ("state", toJson face.state), ("position", toJson face.position), ("residual", toJson face.residual)]

def nodePrerequisites (r : Reading) (node : TraceNode) : List Json :=
  let exact := prerequisite "exact_source_interval" "affirmed" "native_source_slice"
  let profile := prerequisite "declared_finite_profile" "affirmed" "authored_profile_not_general_classification"
  let interfaces := prerequisite "child_interfaces_match" "affirmed" "native_grammar"
  match node with
  | .prefixNode | .noun | .complement => [exact, profile,
      prerequisite "declared_lexical_slot_allowed" "affirmed" "native_grammar"]
  | .idafa => [exact, profile, interfaces,
      prerequisite "ordered_noun_complement_children" "affirmed" "native_grammar"]
  | .sentence => [exact, profile, interfaces] ++ prerequisites r

/-- Authored passage linkage only. The runtime verifies bytes of this frozen
review; Lean does not infer historical authenticity or interpret the books. -/
def nodePassages (r : Reading) (node : TraceNode) : List String :=
  let governor := match r.governor with
    | .arrival => "qatr_subject" | .seeing => "qatr_object" | .passing => "qatr_genitive"
  let noun := ["qatr_six_inventory_case", "alfiyya_idafa_non_speaker"] ++
    (match r.lexeme with
    | .ab | .akh | .ham => ["alfiyya_variants"]
    | .fu | .dhu => ["alfiyya_dhu_fum"]
    | .han => ["alfiyya_han", "sibawayhi_han_report"])
  match node with
  | .prefixNode => [governor]
  | .noun => noun
  | .complement => ["qatr_genitive"]
  | .idafa => ["qatr_genitive", "alfiyya_idafa_non_speaker"]
  | .sentence => [governor] ++ noun

def nodeJson (source : Nabt.Foundation.Source) (context : String)
    (cert : Certificate source context) (node : TraceNode) : Json :=
  let r := cert.reading
  Json.mkObj [
    ("node_id", toJson node.id), ("law_id", toJson lawId),
    ("source", sourceJson source), ("context", toJson context),
    ("scope", toJson "INSTALLED_EXACT_SPELLING_COMMON_LETTER_PROFILE"),
    ("orthographic_profile", toJson orthographicProfile),
    ("alphabet_id", toJson Nabt.Foundation.alphabetId),
    ("number_domain", toJson Nabt.Foundation.numberDomain),
    ("rule_id", toJson node.ruleId), ("children", toJson (node.children.map TraceNode.id)),
    ("rule_source_review_sha256", toJson "315e6c067d9bacded9661bef043594be90437b73f1f695842d1d087d0dac0b8e"),
    ("passage_ids", toJson (nodePassages r node)),
    ("start_byte", toJson (node.startByte r)), ("end_byte", toJson (node.endByte r)),
    ("raw", toJson (node.raw r)),
    ("input_cells", toJson (node.children.map fun child => (child.atoms r).map Fin.val)),
    ("output_cells", toJson ((node.atoms r).map Fin.val)),
    ("output_number", toJson (toString (node.number r))),
    ("input_faces", toJson (node.children.map fun child => faceJson (child.tree.face (grammar r)))),
    ("output_face", faceJson (node.tree.face (grammar r))),
    ("prerequisites", toJson (nodePrerequisites r node)),
    ("alternatives", toJson (alternatives r)), ("unresolved", toJson (unresolved r)),
    ("licensed", toJson true)]

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
  let status := if original.status = Nabt.Foundation.Status.invalid then "INVALID_SOURCE"
    else if certificate.isSome then "CHECKED_SIX_NOUN"
    else if reading.isSome then "DEFER" else "OUTSIDE_EXECUTED_FRAGMENT"
  let residuals := match reading with
    | some r => unresolved r
    | none => if original.status = Nabt.Foundation.Status.invalid then ["INVALID_SOURCE_MARKS_OR_EMPTY"]
      else ["OUTSIDE_EXACT_TEMPLATE_OR_VARIANT_NOT_ACQUIRED"]
  return Json.mkObj [
    ("schema", toJson lawId), ("law_id", toJson lawId),
    ("source", sourceJson source), ("context", toJson context),
    ("source_projection", projectionJson source), ("status", toJson status),
    ("reading", match reading with | none => Json.null | some r => readingJson r),
    ("grammar_certified", toJson certificate.isSome),
    ("node_trace", match certificate with
      | none => toJson ([] : List Json)
      | some cert => toJson (traceNodes.map (nodeJson source context cert))),
    ("foundation_complete", toJson (original.status == Nabt.Foundation.Status.complete)),
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
