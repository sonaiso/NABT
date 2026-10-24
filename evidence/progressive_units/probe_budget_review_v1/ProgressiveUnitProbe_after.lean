import Nabt.LicensedDerivation
import Nabt.ProsodicUnits
import Nabt.UnitCarrier
import Nabt.BinaryUnitDomain
import ProbeJson

/-!
Executable bounded adapter for progressive source-bound constructions and
ordered C/V proposals. The interpreter inventory is supplied explicitly; this
program never treats a generated proposal, numeric address, or caller status
as linguistic evidence. The older frozen Python runtime is not altered.
-/

open Lean ProbeJson
namespace ProgressiveUnitProbe

def maxAtoms : Nat := 12
def maxSourceAtoms : Nat := 256
def maxTreeNodes : Nat := 127
def maxReceipts : Nat := 128
def maxOutputBytes : Nat := 16777216

def response (fields : List (String × Json)) : Json := Json.mkObj (
  [("law_id", toJson Nabt.LicensedDerivation.lawId),
   ("scope", toJson "conditional_on_supplied_interpretations"),
   ("conditional", toJson true), ("acquisition_measured", toJson false)] ++ fields)

def errorResponse (failure : Failure) : Json := response [
  ("status", toJson "ERROR"), ("error", toJson failure.code),
  ("search_complete", toJson false), ("message", toJson failure.message)]

def success (op : String) (fields : List (String × Json)) : Json :=
  response ([("status", toJson "OK"), ("op", toJson op)] ++ fields)

def limitedItems (limit : Nat) (parse : Json → ProbeM α) (value : Json) : ProbeM (List α) := do
  let values ← liftParse value.getArr?
  if values.size > limit then return ← limited "an array exceeds its declared resource bound"
  values.toList.mapM parse

def source (value : Json) : ProbeM (Nabt.UnitDiscovery.Source String) := do
  return {
    sourceId := ← nat (← field value "source_id")
    revision := ← nat (← field value "revision")
    scopeId := ← nat (← field value "scope_id")
    atomizationId := ← nat (← field value "atomization_id")
    atoms := ← limitedItems maxSourceAtoms atom (← field value "atoms") }

def span (value : Json) : ProbeM Nabt.UnitDiscovery.Span := do
  return {
    sourceId := ← nat (← field value "source_id")
    revision := ← nat (← field value "revision")
    scopeId := ← nat (← field value "scope_id")
    atomizationId := ← nat (← field value "atomization_id")
    start := ← nat (← field value "start")
    stop := ← nat (← field value "stop") }

def tag (value : Json) : ProbeM Nabt.LicensedDerivation.Tag := do
  return {
    ruleId := ← nat (← field value "rule_id")
    readingId := ← nat (← field value "reading_id")
    classId := ← nat (← field value "class_id")
    requirements := ← limitedItems 32 nat (← field value "requirements") }

def treeNodes : Nabt.LicensedDerivation.Tree α → Nat
  | .atom .. => 1
  | .join _ left right => 1 + treeNodes left + treeNodes right
  | .wrap _ child | .substitute _ _ child | .lift _ child => 1 + treeNodes child

def treeAt : Nat → Json → ProbeM (Nabt.LicensedDerivation.Tree String)
  | 0, _ => limited "derivation nesting exceeds its resource bound"
  | depth + 1, value => do
    let op ← str (← field value "op")
    let parsed ← match op with
      | "atom" => pure (Nabt.LicensedDerivation.Tree.atom
          (← source (← field value "source"))
          (← limitedItems maxSourceAtoms atom (← field value "before"))
          (← atom (← field value "value"))
          (← limitedItems maxSourceAtoms atom (← field value "after")))
      | "join" => pure (Nabt.LicensedDerivation.Tree.join (← tag (← field value "tag"))
          (← treeAt depth (← field value "left")) (← treeAt depth (← field value "right")))
      | "wrap" => pure (Nabt.LicensedDerivation.Tree.wrap (← tag (← field value "tag"))
          (← treeAt depth (← field value "child")))
      | "substitute" => pure (Nabt.LicensedDerivation.Tree.substitute (← tag (← field value "tag"))
          (← limitedItems maxSourceAtoms atom (← field value "replacement"))
          (← treeAt depth (← field value "child")))
      | "lift" => pure (Nabt.LicensedDerivation.Tree.lift (← tag (← field value "tag"))
          (← treeAt depth (← field value "child")))
      | _ => invalid "unknown derivation constructor"
    if treeNodes parsed > maxTreeNodes then
      return ← limited "derivation exceeds 127 nodes"
    return parsed

def tree (value : Json) : ProbeM (Nabt.LicensedDerivation.Tree String) := treeAt 32 value

def support (value : Json) : ProbeM (Nabt.UnitDiscovery.Support String) := do
  return ⟨← source (← field value "source"), ← span (← field value "span")⟩

def receipt (value : Json) : ProbeM (Nabt.LicensedDerivation.Receipt String) := do
  return {
    target := ← tree (← field value "target")
    requirement := ← nat (← field value "requirement")
    positive := ← boolean (← field value "positive")
    witnessId := ← nat (← field value "witness_id")
    supports := ← limitedItems 32 support (← field value "supports") }

def context (value : Json) : ProbeM (Nabt.LicensedDerivation.Context String) := do
  return {
    inventory := ← limitedItems 32 source (← field value "inventory")
    interpreted := ← limitedItems maxReceipts receipt (← field value "interpreted")
    offered := ← limitedItems maxReceipts receipt (← field value "offered") }

def sourceJson (source : Nabt.UnitDiscovery.Source String) : Json := Json.mkObj [
  ("source_id", toJson source.sourceId), ("revision", toJson source.revision),
  ("scope_id", toJson source.scopeId), ("atomization_id", toJson source.atomizationId),
  ("atoms", toJson source.atoms)]

def tagJson (tag : Nabt.LicensedDerivation.Tag) : Json := Json.mkObj [
  ("rule_id", toJson tag.ruleId), ("reading_id", toJson tag.readingId),
  ("class_id", toJson tag.classId), ("requirements", toJson tag.requirements)]

def treeJson : Nabt.LicensedDerivation.Tree String → Json
  | .atom source before value after => Json.mkObj [
      ("op", toJson "atom"), ("source", sourceJson source),
      ("before", toJson before), ("value", toJson value), ("after", toJson after)]
  | .join tag left right => Json.mkObj [
      ("op", toJson "join"), ("tag", tagJson tag),
      ("left", treeJson left), ("right", treeJson right)]
  | .wrap tag child => Json.mkObj [
      ("op", toJson "wrap"), ("tag", tagJson tag), ("child", treeJson child)]
  | .substitute tag replacement child => Json.mkObj [
      ("op", toJson "substitute"), ("tag", tagJson tag),
      ("replacement", toJson replacement), ("child", treeJson child)]
  | .lift tag child => Json.mkObj [
      ("op", toJson "lift"), ("tag", tagJson tag), ("child", treeJson child)]

def statusName : Nabt.LicensedDerivation.Status → String
  | .invalid => "INVALID_DERIVATION"
  | .pending => "UNKNOWN"
  | .conditionalLicensed => "LICENSED"
  | .rejected => "REJECTED"

def stepJson (ctx : Nabt.LicensedDerivation.Context String) (step : Nabt.LicensedDerivation.Tree String) : Json :=
  let admitted := Nabt.LicensedDerivation.admitted ctx step
  Json.mkObj [
    ("target", treeJson step), ("rank", toJson step.rank),
    ("raw", toJson step.raw), ("output", toJson step.output),
    ("displaced_output", match step with
      | .substitute _ _ child => toJson child.output
      | _ => Json.null),
    ("extent", toJson [step.start, step.stop]), ("requirements", toJson step.required),
    ("entry_valid", toJson (step.entry ctx.inventory)),
    ("positive_complete", toJson (Nabt.LicensedDerivation.localPositive ctx step)),
    ("negative", toJson (Nabt.LicensedDerivation.localNegative ctx step)),
    ("conflict", toJson (Nabt.LicensedDerivation.localConflict ctx step)),
    ("offered_admitted_ids", toJson (admitted.map Nabt.LicensedDerivation.Receipt.witnessId)),
    ("known_negative_ids", toJson ((ctx.interpreted.filter fun r =>
      Nabt.LicensedDerivation.acceptsReceipt ctx step r && !r.positive && step.required.contains r.requirement).map
        Nabt.LicensedDerivation.Receipt.witnessId))]

def derivationFields (ctx : Nabt.LicensedDerivation.Context String) (tree : Nabt.LicensedDerivation.Tree String)
    (seen : List String) : List (String × Json) :=
  let report := Nabt.LicensedDerivation.assess ctx tree
  let restored := tree.undo seen
  [("verdict", toJson (statusName report.status)),
   ("licensed", toJson (report.status == .conditionalLicensed)),
   ("conflict", toJson report.conflict),
   ("structural", toJson (tree.structural ctx.inventory)),
   ("rank", toJson tree.rank), ("tree_nodes", toJson (treeNodes tree)),
   ("rank_domain", toJson "derivation_height"),
   ("source", sourceJson tree.source), ("extent", toJson [tree.start, tree.stop]),
   ("raw", toJson tree.raw), ("output", toJson tree.output),
   ("before", toJson tree.before), ("after", toJson tree.after),
   ("reconstruction", toJson tree.reconstruct),
   ("reconstruction_matches", toJson (tree.reconstruct == tree.source.atoms)),
   ("seen", toJson seen), ("undo_raw", toJson restored),
   ("undo_source", toJson (restored.map fun raw => tree.before ++ raw ++ tree.after)),
   ("class_id", toJson tree.classId),
   ("premise_steps", toJson (tree.steps.map (stepJson ctx))),
   ("necessity", toJson "NOT_ESTABLISHED_BY_A_SINGLE_DERIVATION")]

def deriveOperation (request : Json) : ProbeM Json := do
  let target ← tree (← field request "tree")
  if (treeJson target).compress.toUTF8.size * (target.steps.length + 4) > maxOutputBytes then
    return ← limited "the estimated derivation report exceeds 16 MiB"
  let ctx ← context request
  let seen ← match ← optionalField request "seen" with
    | none => pure target.output
    | some value => limitedItems maxSourceAtoms atom value
  return success "derive" (derivationFields ctx target seen)

def shape (value : Json) : ProbeM Nabt.ProsodicUnits.Shape := do
  let text ← str value
  text.toList.mapM fun character => match character with
    | 'C' => pure Nabt.ProsodicUnits.Slot.c
    | 'V' => pure Nabt.ProsodicUnits.Slot.v
    | _ => invalid "a declared shape may contain only C and V"

def shapeText (shape : Nabt.ProsodicUnits.Shape) : String :=
  String.ofList (shape.map fun slot => match slot with | .c => 'C' | .v => 'V')

def budget (request : Json) : ProbeM Nat := do
  let value ← match ← optionalField request "max_atoms" with
    | none => pure maxAtoms
    | some value => nat value
  if value > maxAtoms then return ← limited "max_atoms exceeds the hard bound of 12"
  return value

def quotaOperation (request : Json) : ProbeM Json := do
  let c ← nat (← field request "consonants")
  let v ← nat (← field request "vowels")
  let bound ← budget request
  match Nabt.ProsodicUnits.boundedQuotaWords bound c v with
  | .exhausted required => return success "quota" [
      ("enumeration", toJson "EXHAUSTED"), ("search_complete", toJson false),
      ("required_atoms", toJson required), ("linguistic_rejection", toJson false)]
  | .complete shapes => return success "quota" [
      ("sub_law_id", toJson Nabt.ProsodicUnits.lawId), ("alphabet_id", toJson Nabt.ProsodicUnits.alphabetId),
      ("enumeration", toJson "COMPLETE"), ("search_complete", toJson true),
      ("consonants", toJson c), ("vowels", toJson v), ("count", toJson shapes.length),
      ("shapes", toJson (shapes.map shapeText)),
      ("shape_numbers", toJson (shapes.map Nabt.ProsodicUnits.shapeEncode)),
      ("linguistic_license_inferred", toJson false)]

def shapeOperation (request : Json) : ProbeM Json := do
  let value ← shape (← field request "shape")
  let bound ← budget request
  if value.length > bound then return ← limited "shape length exceeds max_atoms"
  let partitions := Nabt.ProsodicUnits.decompositions value
  return success "shape" [
    ("sub_law_id", toJson Nabt.ProsodicUnits.lawId), ("alphabet_id", toJson Nabt.ProsodicUnits.alphabetId),
    ("shape", toJson (shapeText value)), ("shape_n", toJson (Nabt.ProsodicUnits.shapeEncode value)),
    ("decoded", toJson (shapeText (Nabt.ProsodicUnits.shapeDecode (Nabt.ProsodicUnits.shapeEncode value)))),
    ("consonants", toJson (Nabt.ProsodicUnits.consonants value)), ("vowels", toJson (Nabt.ProsodicUnits.vowels value)),
    ("partition_count", toJson partitions.length),
    ("partitions", toJson (partitions.map fun parts => parts.map shapeText)),
    ("linguistic_license_inferred", toJson false)]

def composeShapesOperation (request : Json) : ProbeM Json := do
  let parts ← limitedItems 12 shape (← field request "parts")
  if parts.isEmpty || parts.any List.isEmpty then
    return ← invalid "compound units require a nonempty list of nonempty parts"
  let value := parts.flatten
  let bound ← budget request
  if value.length > bound then return ← limited "the compound shape exceeds max_atoms"
  return success "compose_shapes" [
    ("alphabet_id", toJson Nabt.ProsodicUnits.alphabetId),
    ("parts", toJson (parts.map shapeText)),
    ("part_numbers", toJson (parts.map Nabt.ProsodicUnits.shapeEncode)),
    ("shape", toJson (shapeText value)),
    ("shape_n", toJson (Nabt.ProsodicUnits.shapeEncode value)),
    ("consonants", toJson (Nabt.ProsodicUnits.consonants value)),
    ("vowels", toJson (Nabt.ProsodicUnits.vowels value)),
    ("linguistic_license_inferred", toJson false)]

def unitTreeJson : Nabt.ProsodicUnits.UnitTree → Json
  | .atom slot => toJson (shapeText [slot])
  | .join left right => toJson ([unitTreeJson left, unitTreeJson right] : List Json)

def forestOperation (request : Json) : ProbeM Json := do
  let value ← shape (← field request "shape")
  let bound ← match ← optionalField request "max_atoms" with
    | none => pure 8
    | some value => nat value
  if bound > 8 then return ← limited "binary forest max_atoms has a hard bound of 8"
  match Nabt.ProsodicUnits.boundedTrees bound value with
  | .exhausted required => return success "forest" [
      ("enumeration", toJson "EXHAUSTED"), ("required_atoms", toJson required),
      ("search_complete", toJson false), ("linguistic_rejection", toJson false)]
  | .complete trees => return success "forest" [
      ("sub_law_id", toJson Nabt.ProsodicUnits.lawId),
      ("alphabet_id", toJson Nabt.ProsodicUnits.alphabetId),
      ("enumeration", toJson "COMPLETE"), ("search_complete", toJson true),
      ("search_domain", toJson "all_order_preserving_binary_groupings_of_supplied_shape"),
      ("count", toJson trees.length), ("shape_n", toJson (Nabt.ProsodicUnits.shapeEncode value)),
      ("rank_domain", toJson "number_of_binary_joins"),
      ("trees", toJson (trees.map unitTreeJson)),
      ("ranks", toJson (trees.map Nabt.ProsodicUnits.UnitTree.rank)),
      ("linguistic_license_inferred", toJson false)]

/-- Only this explicitly generated atom/join grammar has a completeness
certificate. A caller's assertion that some other search is complete is not
an input to this operation. -/
def forestAssessOperation (request : Json) : ProbeM Json := do
  let rawSource ← source (← field request "source")
  let joinTag ← tag (← field request "tag")
  let start ← nat (← field request "start")
  let length ← nat (← field request "length")
  let bound ← match ← optionalField request "max_atoms" with
    | none => pure 8
    | some value => nat value
  if bound > 8 then return ← limited "binary source search has a hard bound of 8 atoms"
  if length == 0 || start + length > rawSource.atoms.length then
    return ← invalid "binary source search requires a nonempty valid source interval"
  if length > bound then return success "forest_assess" [
    ("enumeration", toJson "EXHAUSTED"), ("search_complete", toJson false),
    ("necessary_within_domain", toJson false), ("globally_unique", toJson false),
    ("linguistic_rejection", toJson false)]
  let ctx ← context request
  let skeletons := Nabt.ProsodicUnits.allTrees (List.replicate length Nabt.ProsodicUnits.Slot.c)
  -- Each leaf repeats the complete source and its context; each internal node
  -- repeats the complete tag, including every potentially large requirement.
  -- Reserve another tree for `chosen` plus envelope/row overhead. This early
  -- estimate protects allocation; dispatch also checks the actual JSONL bytes.
  let sourceBytes := (sourceJson rawSource).compress.toUTF8.size
  let tagBytes := (tagJson joinTag).compress.toUTF8.size
  let perTree := length * (4 * sourceBytes + 2 * tagBytes + 2048)
  let estimatedBytes := (skeletons.length + 2) * perTree +
    4 * sourceBytes + 4 * tagBytes + 4096
  if estimatedBytes > maxOutputBytes then
    return ← limited "the estimated source forest exceeds 16 MiB"
  let candidates := Nabt.BinaryUnitDomain.candidates rawSource joinTag start length
  let chosen := Nabt.BinaryUnitDomain.uniqueWithin ctx candidates
  let rows := candidates.map fun candidate =>
    let report := Nabt.LicensedDerivation.assess ctx candidate
    Json.mkObj [
      ("tree", treeJson candidate), ("verdict", toJson (statusName report.status)),
      ("conflict", toJson report.conflict), ("rank", toJson candidate.rank),
      ("output", toJson candidate.output)]
  let countStatus := fun status => (candidates.filter fun candidate =>
    decide ((Nabt.LicensedDerivation.assess ctx candidate).status = status)).length
  let licensed := countStatus .conditionalLicensed
  let pending := countStatus .pending
  let rejected := countStatus .rejected
  let invalid := countStatus .invalid
  let determination := if invalid > 0 then "INVALID_SOURCE_CONTEXT"
    else if chosen.isSome then "UNIQUE_WITHIN_BINARY_DOMAIN"
    else if licensed > 1 then "AMBIGUOUS"
    else if pending > 0 then "UNRESOLVED"
    else "ALL_REJECTED_WITHIN_BINARY_DOMAIN"
  return success "forest_assess" [
    ("sub_law_id", toJson Nabt.BinaryUnitDomain.lawId),
    ("search_domain", toJson "fixed_source_interval_and_tag_atomic_or_binary_join_only"),
    ("source", sourceJson rawSource), ("tag", tagJson joinTag),
    ("extent", toJson [start, start + length]),
    ("enumeration", toJson "COMPLETE"), ("search_complete", toJson true),
    ("candidate_count", toJson candidates.length), ("licensed_count", toJson licensed),
    ("pending_count", toJson pending), ("rejected_count", toJson rejected),
    ("invalid_count", toJson invalid), ("determination", toJson determination),
    ("rank_domain", toJson "derivation_height"), ("candidates", toJson rows),
    ("chosen", chosen.map treeJson |>.getD Json.null),
    ("necessary_within_domain", toJson chosen.isSome), ("globally_unique", toJson false)]

def segment (value : Json) : ProbeM Nabt.ProsodicUnits.Segment := do
  match ← str (← field value "kind") with
  | "consonant" => return .consonant (← nat (← field value "id"))
  | "vowel" =>
    let quality ← nat (← field value "quality")
    match ← str (← field value "quantity") with
    | "short" => return .vowel quality .short
    | "long" => return .vowel quality .long
    | _ => invalid "quantity must be short or long"
  | _ => invalid "unknown segment kind"

def quantityOperation (request : Json) : ProbeM Json := do
  let segments ← limitedItems 128 segment (← field request "segments")
  let value := Nabt.ProsodicUnits.segmentsShape segments
  return success "quantity" [
    ("sub_law_id", toJson Nabt.ProsodicUnits.lawId), ("shape", toJson (shapeText value)),
    ("shape_n", toJson (Nabt.ProsodicUnits.shapeEncode value)), ("segments", toJson segments.length),
    ("quantity_source", toJson "DECLARED_INPUT"),
    ("source_aligned_license", toJson false), ("long_vowel_inferred_from_vv", toJson false)]

def cell (value : Json) : ProbeM Nabt.Atom := do
  let n ← nat value
  if bounded : n < 116 then return ⟨n, bounded⟩
  else invalid "an A116 cell must be in [0,116); a compound number is not an atomic cell"

def effectOperation (request : Json) : ProbeM Json := do
  let cells ← limitedItems 128 cell (← field request "cells")
  let mode ← str (← field request "mode")
  let wasl ← match mode with
    | "wasl" => pure true
    | "waqf" => pure false
    | _ => invalid "mode must be wasl or waqf in the declared NABT law"
  let entry ← nat (← field request "entry")
  if entry ≥ 97 then return ← invalid "entry is outside the declared 97-state machine"
  match Nabt.UnitCarrier.make cells with
  | none => invalid "an empty payload is not a reified carrier"
  | some unit =>
    let effect := Nabt.UnitCarrier.effect wasl unit
    return success "cell_effect" [
      ("sub_law_id", toJson Nabt.UnitCarrier.lawId),
      ("alphabet_id", toJson Nabt.UnitCarrier.alphabetId),
      ("sound_law_id", toJson Nabt.Law.lawId), ("mode", toJson mode),
      ("unit_n", toJson (Nabt.UnitCarrier.number unit)),
      ("cells", toJson (cells.map Fin.val)), ("entry", toJson entry),
      ("exit", toJson (effect.transform entry)), ("weight", toJson (effect.weight entry)),
      ("sound_shape_accepted", toJson (Nabt.UnitCarrier.accepts wasl entry unit)),
      ("effect", toJson ((List.range 97).map fun q => Json.mkObj [
        ("entry", toJson q), ("exit", toJson (effect.transform q)),
        ("weight", toJson (effect.weight q))])),
      ("lexical_attestation_inferred", toJson false)]

def compareOperation (request : Json) : ProbeM Json := do
  let left ← tree (← field request "left")
  let right ← tree (← field request "right")
  return success "compare" [
    ("comparison_scope", toJson "proposal_identity_only"),
    ("licensed_comparison", toJson false),
    ("rank_domain", toJson "derivation_height"),
    ("left_structural_in_declared_source", toJson (left.structural [left.source])),
    ("right_structural_in_declared_source", toJson (right.structural [right.source])),
    ("same_derivation", toJson (left == right)),
    ("same_unit_key", toJson (Nabt.LicensedDerivation.unitKey left == Nabt.LicensedDerivation.unitKey right)),
    ("same_output", toJson (left.output == right.output)),
    ("same_occurrence", toJson (left.source == right.source && left.start == right.start &&
      left.raw == right.raw)),
    ("left_rank", toJson left.rank), ("right_rank", toJson right.rank),
    ("necessity", toJson "NOT_ESTABLISHED_BY_EQUAL_OUTPUT")]

def alphabetOperation : Json := success "alphabet" [
  ("alphabet_id", toJson Nabt.Law.alphabetId), ("carriers", toJson (29 : Nat)),
  ("cells", toJson Nabt.ProsodicUnits.cells.length), ("non_sukun_cells", toJson Nabt.ProsodicUnits.movingCells.length),
  ("sukun_cells", toJson Nabt.ProsodicUnits.stillCells.length),
  ("all_cells_are_phonetic_cv", toJson false), ("articulation_classes_acquired", toJson false)]

def dispatchOperation (request : Json) : ProbeM Json := do
  match ← str (← field request "op") with
  | "derive" => deriveOperation request
  | "quota" => quotaOperation request
  | "shape" => shapeOperation request
  | "compose_shapes" => composeShapesOperation request
  | "forest" => forestOperation request
  | "forest_assess" => forestAssessOperation request
  | "quantity" => quantityOperation request
  | "cell_effect" => effectOperation request
  | "compare" => compareOperation request
  | "alphabet" => pure alphabetOperation
  | _ => invalid "unknown operation"

/-- The transport emits compressed UTF-8 JSON followed by one newline. Keep
the actual response within the declared byte budget independently of every
operation's conservative allocation estimate. -/
def dispatch (request : Json) : ProbeM Json := do
  let result ← dispatchOperation request
  if result.compress.toUTF8.size + 1 > maxOutputBytes then
    return ← limited "the serialized response exceeds 16 MiB"
  return result

end ProgressiveUnitProbe

def main : IO Unit := do
  ProbeJson.readLoop ProgressiveUnitProbe.dispatch ProgressiveUnitProbe.errorResponse
    (← IO.getStdin) (← IO.getStdout)
