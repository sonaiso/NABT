import Nabt.UnitDiscovery
import Nabt.AffixFunctions
import Nabt.PersonEvidence
import Nabt.NominalEvidence
import Lean

/-!
Bounded JSONL adapter for the executable conditional specifications.
No operation interprets Arabic evidence, authenticates supplied source bytes,
discovers linguistic classes, or establishes lexical attestation. The person
and nominal operations expose their existing conditional laws unchanged.

Atoms are nonempty caller-declared strings. Their UTF-8 boundaries are not a
Unicode grapheme-segmentation result. Integer fields use canonical unsigned
decimal JSON tokens (booleans, signs, decimals and exponents are rejected).
The streaming reader retains at most 1 MiB per line before rejecting it.
-/

open Lean
open Nabt.UnitDiscovery

namespace UnitDiscoveryProbe

def maxLineBytes : Nat := 1048576
def maxAtoms : Nat := 12
def maxDepth : Nat := 64
def maxNumberDigits : Nat := 256
def maxPartitionOutputBytes : Nat := 16777216

structure Failure where
  code : String
  message : String

abbrev ProbeM := Except Failure

def invalid (message : String) : ProbeM α := .error ⟨"INVALID_INPUT", message⟩
def limited (message : String) : ProbeM α := .error ⟨"RESOURCE_LIMIT", message⟩

def liftParse (result : Except String α) : ProbeM α :=
  result.mapError (fun message => ⟨"INVALID_INPUT", message⟩)

def field (object : Json) (name : String) : ProbeM Json :=
  liftParse (object.getObjVal? name)

def optionalField (object : Json) (name : String) : ProbeM (Option Json) := do
  let entries ← liftParse object.getObj?
  return entries.get? name

def nat (value : Json) : ProbeM Nat := liftParse value.getNat?
def str (value : Json) : ProbeM String := liftParse value.getStr?
def boolean (value : Json) : ProbeM Bool := liftParse value.getBool?

def items (parse : Json → ProbeM α) (value : Json) : ProbeM (List α) := do
  let values ← liftParse value.getArr?
  values.toList.mapM parse

def atom (value : Json) : ProbeM String := do
  let value ← str value
  if value.isEmpty then invalid "an atom must be a nonempty declared string"
  else return value

def source (value : Json) : ProbeM (Source String) := do
  return {
    sourceId := ← nat (← field value "source_id")
    revision := ← nat (← field value "revision")
    scopeId := ← nat (← field value "scope_id")
    atomizationId := ← nat (← field value "atomization_id")
    atoms := ← items atom (← field value "atoms") }

def span (value : Json) : ProbeM Span := do
  return {
    sourceId := ← nat (← field value "source_id")
    revision := ← nat (← field value "revision")
    scopeId := ← nat (← field value "scope_id")
    atomizationId := ← nat (← field value "atomization_id")
    start := ← nat (← field value "start")
    stop := ← nat (← field value "stop") }

def hypothesis (value : Json) : ProbeM (Hypothesis String String) := do
  return {
    source := ← source (← field value "source")
    parts := ← items (items str) (← field value "parts")
    partIndex := ← nat (← field value "part_index")
    host := ← span (← field value "host")
    unitClass := ⟨← nat (← field value "unit_class")⟩
    claim := ← str (← field value "claim")
    ruleId := ← nat (← field value "rule_id")
    readingId := ← nat (← field value "reading_id")
    occurrenceId := ← nat (← field value "occurrence_id")
    declaredRequirements := ← items nat (← field value "requirements") }

def support (value : Json) : ProbeM (Support String) := do
  return ⟨← source (← field value "source"), ← span (← field value "span")⟩

def receipt (value : Json) : ProbeM (Receipt String String) := do
  return {
    target := ← hypothesis (← field value "target")
    requirement := ← nat (← field value "requirement")
    positive := ← boolean (← field value "positive")
    witnessId := ← nat (← field value "witness_id")
    supports := ← items support (← field value "supports") }

def response (fields : List (String × Json)) : Json := Json.mkObj (
  [("law_id", toJson Nabt.UnitDiscovery.lawId),
   ("scope", toJson "conditional_on_supplied_interpretations"),
   ("conditional", toJson true)] ++ fields)

def errorResponse (failure : Failure) : Json := response [
  ("status", toJson "ERROR"), ("error", toJson failure.code),
  ("message", toJson failure.message)]

def success (op : String) (fields : List (String × Json)) : Json :=
  response ([("status", toJson "OK"), ("op", toJson op)] ++ fields)

def atomsAt (atoms : List String) (groups : Parts Nat) : Parts String :=
  groups.map (fun group => group.map (fun index => atoms[index]?.getD ""))

def cutSet (groups : Parts Nat) : List Nat :=
  groups.drop 1 |>.filterMap List.head?

def byteBoundaries (atoms : List String) : List Nat :=
  (atoms.foldl (fun (state : Nat × List Nat) value =>
    let next := state.1 + value.toUTF8.size
    (next, next :: state.2)) (0, [0])).2.reverse

def partitionOperation (request : Json) : ProbeM Json := do
  let atoms ← items atom (← field request "atoms")
  let budget ← match ← optionalField request "max_atoms" with
    | none => pure maxAtoms
    | some value => nat value
  if budget > maxAtoms then
    return ← limited "max_atoms exceeds the hard limit of 12 declared atoms"
  if atoms.length > budget then
    return ← limited "the atom count exceeds max_atoms"
  let count := 2 ^ (atoms.length - 1)
  let atomBytes := (atoms.map (fun value => value.toUTF8.size)).sum
  -- Conservative output bound, checked before generating exponential output.
  if count * (6 * atomBytes + 128 * atoms.length + 256) > maxPartitionOutputBytes then
    return ← limited "the estimated partition JSON output exceeds 16 MiB"
  let offsets ← match ← optionalField request "byte_offsets" with
    | none => pure []
    | some value => items nat value
  match enumerateWithin budget (List.range atoms.length) with
  | .exhausted => limited "the atom count exceeds max_atoms"
  | .complete groups =>
    let boundaries := byteBoundaries atoms
    return success "partitions" [
      ("count", toJson groups.length),
      ("position_groups", toJson groups),
      ("parts", toJson (groups.map (atomsAt atoms))),
      ("cut_sets", toJson (groups.map cutSet)),
      ("atom_byte_boundaries", toJson boundaries),
      ("byte_boundary_scope", toJson "supplied_atom_boundaries_not_unicode_segmentation"),
      ("byte_cut_checks", toJson (offsets.map fun offset => Json.mkObj [
        ("offset", toJson offset), ("allowed", toJson (boundaries.contains offset))]))]

def inspectOperation (request : Json) : ProbeM Json := do
  let atoms ← items atom (← field request "atoms")
  let groups ← items (items nat) (← field request "position_groups")
  let valid := decide (Exact (List.range atoms.length) groups)
  return success "inspect_partition" [
    ("valid", toJson valid),
    ("parts", if valid then toJson (atomsAt atoms groups) else Json.null)]

def adjacencyOperation (request : Json) : ProbeM Json := do
  let left ← span (← field request "left")
  let right ← span (← field request "right")
  return success "adjacency" [("adjacent", toJson (adjacent left right))]

def verdictName : Verdict → String
  | .pending => "UNKNOWN"
  | .conditionalLicensed => "LICENSED"
  | .rejected => "REJECTED"

def stateName (positive negative : Bool) : String :=
  if positive && negative then "CONFLICT"
  else if positive then "POSITIVE"
  else if negative then "NEGATIVE" else "UNKNOWN"

def receiptReason (inventory : List (Source String))
    (interpreted : List (Receipt String String))
    (target : Hypothesis String String) (offered : Receipt String String) : String :=
  if !wellFormed target then "MALFORMED_TARGET"
  else if target.source ∉ inventory then "SOURCE_NOT_IN_INVENTORY"
  else if offered.target ≠ target then "FOREIGN_TARGET"
  else if offered ∉ interpreted then "UNINTERPRETED"
  else if offered.supports.isEmpty then "EMPTY_SUPPORT"
  else if !offered.supports.all (validSupport inventory) then "INVALID_SUPPORT"
  else "ACCEPTED"

def ledgerOperation (request : Json) : ProbeM Json := do
  let target ← hypothesis (← field request "target")
  let inventory ← items source (← field request "inventory")
  let interpreted ← items receipt (← field request "interpreted")
  let offered ← items receipt (← field request "offered")
  let stages ← match ← optionalField request "stage_requirements" with
    | none => pure []
    | some value => items (items nat) value
  let checked := admitted inventory interpreted target offered
  let result := assess inventory interpreted target offered
  let valid := wellFormed target
  let logicalAtoms := (checked.map fun r => (r.requirement, r.positive)).eraseDups
  return success "ledger" [
    ("well_formed", toJson valid),
    ("verdict", toJson (result.map (fun a => verdictName a.verdict) |>.getD "INVALID_HYPOTHESIS")),
    ("conflict", toJson (result.map Assessment.conflict |>.getD false)),
    ("admitted_ids", toJson (checked.map Receipt.witnessId)),
    ("requirements", toJson (required target)),
    ("supported_atoms", toJson (logicalAtoms.map fun (r, polarity) => Json.mkObj [
      ("requirement", toJson r), ("positive", toJson polarity)])),
    ("per_requirement", toJson ((required target).eraseDups.map fun r =>
      let positive := supported checked r true
      let negative := supported checked r false
      Json.mkObj [("requirement", toJson r), ("positive", toJson positive),
        ("negative", toJson negative), ("state", toJson (stateName positive negative))])),
    ("receipt_checks", toJson (offered.map fun r => Json.mkObj [
      ("witness_id", toJson r.witnessId),
      ("accepted", toJson (acceptsReceipt inventory interpreted target r)),
      ("reason", toJson (receiptReason inventory interpreted target r))])),
    ("stages", toJson (stages.map fun requirements =>
      let stage := assessRequired requirements checked
      Json.mkObj [("requirements", toJson (sourceRequirement :: requirements)),
        ("verdict", toJson (if valid then verdictName stage.verdict else "INVALID_HYPOTHESIS")),
        ("conflict", toJson (valid && stage.conflict))]))]

def singleChar (value : Json) : ProbeM Char := do
  let text ← str value
  match text.toList with
  | [character] => return character
  | _ => invalid "root radicals and pattern literals must be single Unicode scalar values"

def patternToken (arity : Nat) (value : Json) : ProbeM (Nabt.Derivation.Token arity) := do
  let entries ← liftParse value.getObj?
  if entries.size != 1 then
    return ← invalid "a pattern token must contain exactly one literal or slot field"
  match entries.get? "literal", entries.get? "slot" with
  | some literal, none => return .literal (← singleChar literal)
  | none, some slot =>
    let index ← nat slot
    if bounded : index < arity then return .slot ⟨index, bounded⟩
    else invalid "a pattern slot is outside its declared root arity"
  | _, _ => invalid "a pattern token must contain exactly one literal or slot field"

def rootReplayAt (arity : Nat) (request : Json) : ProbeM Json := do
  let radicals ← items singleChar (← field request "root")
  if radicals.length != arity then
    return ← invalid "root length does not equal the declared arity"
  let root : Nabt.Derivation.Root arity := fun index => radicals[index.val]?.getD '\x00'
  let pattern ← items (patternToken arity) (← field request "pattern")
  let surface ← str (← field request "surface")
  let generated := Nabt.Derivation.fill pattern root
  let complete := decide (Nabt.Derivation.Complete pattern)
  let recovered := Nabt.Derivation.recover pattern surface.toList
  let recoveredJson := match recovered with
    | none => Json.null
    | some value => toJson ((List.finRange arity).map fun index => String.singleton (value index))
  return success "root_replay" [
    ("sub_law_id", toJson Nabt.Derivation.lawId),
    ("arity", toJson arity), ("complete", toJson complete),
    ("shape_matches", toJson (complete && decide (generated = surface.toList))),
    ("generated_surface", toJson (String.ofList generated)),
    ("recovered_root", recoveredJson),
    ("lexical_attestation", Json.null)]

def rootReplayOperation (request : Json) : ProbeM Json := do
  let arity ← nat (← field request "arity")
  match arity with
  | 3 => rootReplayAt 3 request
  | 4 => rootReplayAt 4 request
  | _ => invalid "root_replay supports only arity 3 or 4 in this interface"

def personFamily (value : String) : ProbeM Nabt.PersonEvidence.Family :=
  match value with
  | "plain" => pure .plain
  | "dual" => pure .dual
  | "masculine_plural" => pure .masculinePlural
  | "feminine_singular" => pure .feminineSingular
  | "feminine_plural" => pure .femininePlural
  | _ => invalid "unknown person family"

def personOperation (request : Json) : ProbeM Json := do
  let family ← personFamily (← str (← field request "family"))
  let pre ← str (← field request "pre")
  let qualified ← boolean (← field request "qualified")
  let profiles := Nabt.PersonEvidence.qualifiedCandidates qualified family pre
  return success "person_profiles" [
    ("sub_law_id", toJson Nabt.PersonEvidence.lawId),
    ("profiles", toJson (profiles.map fun p => Json.mkObj [
      ("qac", toJson p.qac), ("person", toJson p.person),
      ("gender", toJson p.gender), ("number", toJson p.number)]))]

def nominalConstraint (value : String) : ProbeM Nabt.NominalEvidence.Constraint :=
  match value with
  | "masculine" => pure .masculine
  | "feminine" => pure .feminine
  | "singular" => pure .singular
  | "dual" => pure .dual
  | "plural" => pure .plural
  | "soundMasculine" => pure .soundMasculine
  | "soundFeminine" => pure .soundFeminine
  | "broken" => pure .broken
  | "otherPlural" => pure .otherPlural
  | "definite" => pure .definite
  | "indefinite" => pure .indefinite
  | _ => invalid "unknown nominal constraint; no lexical labels are converted into constraints"

def nominalOperation (request : Json) : ProbeM Json := do
  let constraints ← items (fun value => str value >>= nominalConstraint)
    (← field request "constraints")
  let profiles := Nabt.NominalEvidence.refine constraints
  return success "nominal_profiles" [
    ("sub_law_id", toJson Nabt.NominalEvidence.lawId),
    ("profiles", toJson (profiles.map fun p => Json.mkObj [
      ("code", toJson p.code), ("gender", toJson p.gender.val),
      ("form", toJson p.form.val), ("definiteness", toJson p.definiteness.val),
      ("number", toJson p.number)]))]

def layerName : Nabt.AffixFunctions.Layer → String
  | .clitic => "clitic" | .inflection => "inflection" | .derivation => "derivation"
  | .lexical => "lexical" | .orthographic => "orthographic"

def positionName : Nabt.AffixFunctions.Position → String
  | .beforeStem => "before_stem" | .afterStem => "after_stem"
  | .templateSlot => "template_slot" | .wholeLexeme => "whole_lexeme"
  | .realization => "realization"

def inventoryOperation : Json := success "inventory" [
  ("inventory_id", toJson Nabt.AffixFunctions.inventoryId),
  ("declared", toJson true), ("classifier", toJson false),
  ("declarations", toJson (Nabt.AffixFunctions.declarations.map fun d => Json.mkObj [
    ("key", toJson d.key), ("label", toJson d.arabic), ("layer", toJson (layerName d.layer)),
    ("positions", toJson (d.positions.map positionName)),
    ("examples", toJson d.examples), ("requirements", toJson d.requirements)]))]

def dispatch (request : Json) : ProbeM Json := do
  match ← str (← field request "op") with
  | "partitions" => partitionOperation request
  | "inspect_partition" => inspectOperation request
  | "adjacency" => adjacencyOperation request
  | "ledger" => ledgerOperation request
  | "root_replay" => rootReplayOperation request
  | "person_profiles" => personOperation request
  | "nominal_profiles" => nominalOperation request
  | "inventory" => pure inventoryOperation
  | _ => invalid "unknown operation"

/-- A small lexical boundary check before the general JSON parser prevents
unbounded numeric exponents and deeply nested malformed input. Strings and
escapes are preserved; interpretation still belongs to Lean's JSON parser. -/
def preflight (line : String) : ProbeM Unit := do
  let mut quoted := false
  let mut escaped := false
  let mut depth := 0
  let mut digits := 0
  for character in line.toList do
    if quoted then
      if escaped then escaped := false
      else if character == '\\' then escaped := true
      else if character == '"' then quoted := false
    else
      if character == '"' then
        quoted := true
        digits := 0
      else if '0' ≤ character && character ≤ '9' then
        digits := digits + 1
        if digits > maxNumberDigits then
          return ← limited "a JSON numeric token exceeds 256 decimal digits"
      else
        if (digits > 0 && (character == '.' || character == 'e' || character == 'E')) ||
            character == '-' || character == '+' then
          return ← invalid "numeric fields require unsigned decimal integer tokens"
        digits := 0
        if character == '[' || character == '{' then
          depth := depth + 1
          if depth > maxDepth then return ← limited "JSON nesting exceeds 64 levels"
        else if character == ']' || character == '}' then
          depth := depth - 1

def processLine (bytes : ByteArray) (oversized : Bool) : Json :=
  if oversized then errorResponse ⟨"RESOURCE_LIMIT", "input line exceeds 1 MiB"⟩
  else match String.fromUTF8? bytes with
    | none => errorResponse ⟨"INVALID_INPUT", "input line is not valid UTF-8"⟩
    | some line =>
      match (do
        preflight line
        let request ← liftParse (Json.parse line)
        dispatch request : ProbeM Json) with
      | .ok result => result
      | .error failure => errorResponse failure

def emit (output : IO.FS.Stream) (bytes : ByteArray) (oversized : Bool) : IO Unit := do
  output.putStr ((processLine bytes oversized).compress ++ "\n")
  output.flush

/-- Bounded streaming, including discard-to-newline after an oversized line.
The following JSONL request is still processed independently. -/
partial def readLoop (input output : IO.FS.Stream)
    (pending : ByteArray := ByteArray.empty) (overflow : Bool := false) : IO Unit := do
  -- `Stream.read n` may wait for n bytes through buffered stdio. A one-byte
  -- request lets a complete line receive its response before stdin reaches EOF.
  let chunk ← input.read 1
  if chunk.isEmpty then
    if !pending.isEmpty || overflow then emit output pending overflow
  else
    let mut pending := pending
    let mut overflow := overflow
    for byte in chunk do
      if byte == 10 then
        emit output pending overflow
        pending := ByteArray.empty
        overflow := false
      else if !overflow then
        if pending.size < maxLineBytes then pending := pending.push byte
        else
          pending := ByteArray.empty
          overflow := true
    readLoop input output pending overflow

end UnitDiscoveryProbe

def main : IO Unit := do
  UnitDiscoveryProbe.readLoop (← IO.getStdin) (← IO.getStdout)
