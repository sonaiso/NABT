import Nabt.RecursiveSourceBridge
import ProbeJson
import Std.Data.TreeSet

/-!
Bounded executable transport for the imported root-to-sentence structural
algebra and the exact typed source bridge. Structural numbering and finite
proposal enumeration are not grammatical licenses. The source assessment is
conditional on the explicitly supplied interpretation ledger. It cannot
produce a `CertifiedBridge` for an unspecified semantic Grammar.
-/

open Lean ProbeJson
namespace RecursiveBridgeProbe


def maxSourceAtoms : Nat := 256
def maxNodes : Nat := 127
def maxReceipts : Nat := 128
def maxOutputBytes : Nat := 16777216
def maxNumberBits : Nat := 4096
def maxCandidates : Nat := 4096
def maxHeight : Nat := 8

def response (fields : List (String × Json)) : Json := Json.mkObj (
  [("law_id", toJson Nabt.RecursiveSourceBridge.lawId),
   ("scope", toJson "structural_source_binding_and_conditional_interpretations"),
   ("conditional", toJson true), ("acquisition_measured", toJson false),
   ("grammar_certified", toJson false)] ++ fields)

def errorResponse (failure : Failure) : Json := response [
  ("status", toJson "ERROR"), ("error", toJson failure.code),
  ("search_complete", toJson false), ("linguistic_rejection", toJson false),
  ("message", toJson failure.message)]

def success (op : String) (fields : List (String × Json)) : Json :=
  response ([("status", toJson "OK"), ("op", toJson op)] ++ fields)

def keysWithin (value : Json) (allowed : List String) : ProbeM Unit := do
  let entries ← liftParse value.getObj?
  if (allowed.filter fun key => (entries.get? key).isSome).length != entries.size then
    return ← invalid "an object contains an undeclared field"

def text (value : Json) : ProbeM String := do
  let value ← str value
  if value.toUTF8.size > 1024 then return ← limited "text field exceeds 1024 UTF-8 bytes"
  return value

def identifier (value : Json) : ProbeM String := do
  let value ← text value
  if value.isEmpty then return ← invalid "an identifier must be nonempty"
  return value

def limitedItems (limit : Nat) (parse : Json → ProbeM α) (value : Json) : ProbeM (List α) := do
  let values ← liftParse value.getArr?
  if values.size > limit then return ← limited "an array exceeds its declared resource bound"
  values.toList.mapM parse

def nullable (parse : Json → ProbeM α) (value : Json) : ProbeM (Option α) :=
  if value == Json.null then pure none else some <$> parse value

def singleChar (value : Json) : ProbeM Char := do
  let value ← str value
  match value.toList with
  | [character] => return character
  | _ => invalid "an atom, radical or literal must be exactly one Unicode scalar value"

def charsJson (values : List Char) : Json := toJson (values.map fun value => String.singleton value)

def source (value : Json) : ProbeM (Nabt.UnitDiscovery.Source Char) := do
  keysWithin value ["source_id", "revision", "scope_id", "atomization_id", "atoms"]
  let atomization ← nat (← field value "atomization_id")
  if atomization != 1 then return ← invalid "this probe requires Unicode scalar atomization_id 1"
  return {
    sourceId := ← nat (← field value "source_id")
    revision := ← nat (← field value "revision")
    scopeId := ← nat (← field value "scope_id")
    atomizationId := atomization
    atoms := ← limitedItems maxSourceAtoms singleChar (← field value "atoms") }

def span (value : Json) : ProbeM Nabt.UnitDiscovery.Span := do
  keysWithin value ["source_id", "revision", "scope_id", "atomization_id", "start", "stop"]
  return {
    sourceId := ← nat (← field value "source_id")
    revision := ← nat (← field value "revision")
    scopeId := ← nat (← field value "scope_id")
    atomizationId := ← nat (← field value "atomization_id")
    start := ← nat (← field value "start")
    stop := ← nat (← field value "stop") }

def tag (value : Json) : ProbeM Nabt.LicensedDerivation.Tag := do
  keysWithin value ["rule_id", "reading_id", "class_id", "requirements"]
  return {
    ruleId := ← nat (← field value "rule_id")
    readingId := ← nat (← field value "reading_id")
    classId := ← nat (← field value "class_id")
    requirements := ← limitedItems 32 nat (← field value "requirements") }

def hostNodes : Nabt.LicensedDerivation.Tree Char → Nat
  | .atom .. => 1
  | .join _ left right => 1 + hostNodes left + hostNodes right
  | .wrap _ child | .substitute _ _ child | .lift _ child => 1 + hostNodes child

def hostTreeAt : Nat → Json → ProbeM (Nabt.LicensedDerivation.Tree Char)
  | 0, _ => limited "source host tree nesting exceeds 32 levels"
  | depth + 1, value => do
    let op ← str (← field value "op")
    let parsed ← match op with
      | "atom" => do
          keysWithin value ["op", "source", "before", "value", "after"]
          return Nabt.LicensedDerivation.Tree.atom
            (← source (← field value "source"))
            (← limitedItems maxSourceAtoms singleChar (← field value "before"))
            (← singleChar (← field value "value"))
            (← limitedItems maxSourceAtoms singleChar (← field value "after"))
      | "join" => do
          keysWithin value ["op", "tag", "left", "right"]
          return Nabt.LicensedDerivation.Tree.join (← tag (← field value "tag"))
            (← hostTreeAt depth (← field value "left")) (← hostTreeAt depth (← field value "right"))
      | "wrap" => do
          keysWithin value ["op", "tag", "child"]
          return Nabt.LicensedDerivation.Tree.wrap (← tag (← field value "tag"))
            (← hostTreeAt depth (← field value "child"))
      | "substitute" => do
          keysWithin value ["op", "tag", "replacement", "child"]
          return Nabt.LicensedDerivation.Tree.substitute (← tag (← field value "tag"))
            (← limitedItems maxSourceAtoms singleChar (← field value "replacement"))
            (← hostTreeAt depth (← field value "child"))
      | "lift" => do
          keysWithin value ["op", "tag", "child"]
          return Nabt.LicensedDerivation.Tree.lift (← tag (← field value "tag"))
            (← hostTreeAt depth (← field value "child"))
      | _ => invalid "unknown source host constructor"
    if hostNodes parsed > maxNodes then return ← limited "a source host tree exceeds 127 nodes"
    return parsed

def seed (value : Json) : ProbeM Nabt.RecursiveLicensedAlgebra.Seed := do
  let kind ← str (← field value "kind")
  match kind with
  | "lexical" => do
      keysWithin value ["kind", "entry"]
      return .lexical (← nat (← field value "entry"))
  | "root3" | "root4" => do
      keysWithin value ["kind", "radicals"]
      let radicals ← limitedItems 4 nat (← field value "radicals")
      match kind, radicals with
      | "root3", [a,b,c] => return .root3 a b c
      | "root4", [a,b,c,d] => return .root4 a b c d
      | _, _ => invalid "root seed length differs from its declared arity"
  | _ => invalid "unknown structural seed kind"

def coreNodes : Nabt.RecursiveLicensedAlgebra.Tree → Nat
  | .leaf .. => 1
  | .unary _ child => 1 + coreNodes child
  | .binary _ left right => 1 + coreNodes left + coreNodes right

def coreTreeAt : Nat → Json → ProbeM Nabt.RecursiveLicensedAlgebra.Tree
  | 0, _ => limited "structural tree nesting exceeds 32 levels"
  | depth + 1, value => do
    let op ← str (← field value "op")
    let parsed ← match op with
      | "leaf" => do
          keysWithin value ["op", "seed"]
          return Nabt.RecursiveLicensedAlgebra.Tree.leaf (← seed (← field value "seed"))
      | "unary" => do
          keysWithin value ["op", "rule", "child"]
          return Nabt.RecursiveLicensedAlgebra.Tree.unary (← nat (← field value "rule"))
            (← coreTreeAt depth (← field value "child"))
      | "binary" => do
          keysWithin value ["op", "rule", "left", "right"]
          return Nabt.RecursiveLicensedAlgebra.Tree.binary (← nat (← field value "rule"))
            (← coreTreeAt depth (← field value "left")) (← coreTreeAt depth (← field value "right"))
      | _ => invalid "unknown structural tree constructor"
    if coreNodes parsed > maxNodes then return ← limited "a structural tree exceeds 127 nodes"
    return parsed

def category (value : Json) : ProbeM Nabt.RecursiveLicensedAlgebra.Category := do
  match ← str value with
  | "root3" => return .root3
  | "root4" => return .root4
  | "noun" => return .noun
  | "verb" => return .verb
  | "particle" => return .particle
  | "nounPhrase" => return .nounPhrase
  | "verbPhrase" => return .verbPhrase
  | "semiClause" => return .semiClause
  | "nominalClause" => return .nominalClause
  | "verbalClause" => return .verbalClause
  | "clause" => return .clause
  | "pending" => return .pending
  | _ => invalid "unknown section category"

def provenance (value : Json) : ProbeM Nabt.RecursiveSourceBridge.Provenance := do
  match ← str value with
  | "native_tree" => return .nativeTree
  | "source_reconstruction" => return .sourceReconstruction
  | _ => invalid "unknown child tree provenance"

def patternToken (arity : Nat) (value : Json) : ProbeM (Nabt.Derivation.Token arity) := do
  let entries ← liftParse value.getObj?
  if entries.size != 1 then return ← invalid "a pattern token must have exactly one slot or literal"
  match entries.get? "literal", entries.get? "slot" with
  | some literal, none => return .literal (← singleChar literal)
  | none, some slot =>
      let index ← nat slot
      if bounded : index < arity then return .slot ⟨index, bounded⟩
      else invalid "a pattern slot is outside its root arity"
  | _, _ => invalid "a pattern token must have exactly one slot or literal"

def readingAt (arity : Nat) (value : Json) :
    ProbeM (Nabt.Derivation.Pattern arity × Nabt.Derivation.Root arity) := do
  let radicals ← limitedItems 4 singleChar (← field value "root")
  if radicals.length != arity then return ← invalid "root length differs from reading arity"
  let root : Nabt.Derivation.Root arity := fun index => radicals[index.val]?.getD '\x00'
  let pattern ← limitedItems maxSourceAtoms (patternToken arity) (← field value "pattern")
  return (pattern, root)

def reading (value : Json) : ProbeM Nabt.UnitDiscovery.RootPatternReading := do
  keysWithin value ["arity", "root", "pattern"]
  match ← nat (← field value "arity") with
  | 3 =>
      let (pattern, root) ← readingAt 3 value
      return .tri pattern root
  | 4 =>
      let (pattern, root) ← readingAt 4 value
      return .quad pattern root
  | _ => invalid "a root reading must have arity three or four"

def origin (value : Json) : ProbeM Nabt.RecursiveSourceBridge.Origin := do
  match ← str (← field value "kind") with
  | "literal" =>
      keysWithin value ["kind", "value"]
      return .literal (← singleChar (← field value "value"))
  | "radical" =>
      keysWithin value ["kind", "index"]
      return .radical (← nat (← field value "index"))
  | _ => invalid "unknown alignment origin"

def alignment (value : Json) : ProbeM Nabt.RecursiveSourceBridge.AlignmentPoint := do
  keysWithin value ["pattern_position", "source_position", "origin"]
  return ⟨← nat (← field value "pattern_position"),
    ← nat (← field value "source_position"), ← origin (← field value "origin")⟩

def morphology (value : Json) : ProbeM Nabt.RecursiveSourceBridge.Morphology := do
  keysWithin value ["catalog_id", "registry_id", "reading_id", "reading", "alignment"]
  return {
    catalogId := ← identifier (← field value "catalog_id")
    registryId := ← identifier (← field value "registry_id")
    readingId := ← identifier (← field value "reading_id")
    reading := ← reading (← field value "reading")
    alignment := ← limitedItems maxSourceAtoms alignment (← field value "alignment") }

def role (value : Json) : ProbeM Nabt.RecursiveSourceBridge.Role := do
  keysWithin value ["role", "reading_id", "target", "head", "case", "case_domain"]
  return {
    role := ← identifier (← field value "role")
    readingId := ← identifier (← field value "reading_id")
    target := ← span (← field value "target")
    head := ← nullable span (← field value "head")
    grammaticalCase := ← nullable identifier (← field value "case")
    caseDomain := ← nullable identifier (← field value "case_domain") }

def metadata (value : Json) : ProbeM Nabt.RecursiveSourceBridge.Metadata := do
  keysWithin value ["registry_id", "reading_id", "source", "host", "host_tree", "morphology",
    "section", "roles", "evidence_ids", "required", "provenance", "unresolved"]
  return {
    registryId := ← identifier (← field value "registry_id")
    readingId := ← identifier (← field value "reading_id")
    source := ← source (← field value "source")
    host := ← span (← field value "host")
    hostTree := ← hostTreeAt 32 (← field value "host_tree")
    morphology := ← nullable morphology (← field value "morphology")
    wordSection := ← nullable category (← field value "section")
    roles := ← limitedItems 32 role (← field value "roles")
    evidenceIds := ← limitedItems 128 nat (← field value "evidence_ids")
    required := ← limitedItems 32 nat (← field value "required")
    provenance := ← provenance (← field value "provenance")
    unresolved := ← limitedItems 32 text (← field value "unresolved") }

def nodeAt : Nat → Json → ProbeM Nabt.RecursiveSourceBridge.Node
  | 0, _ => limited "annotated node nesting exceeds 32 levels"
  | depth + 1, value => do
    let op ← str (← field value "op")
    let parsed ← match op with
      | "leaf" => do
          keysWithin value ["op", "seed", "metadata"]
          return Nabt.RecursiveSourceBridge.Node.leaf (← seed (← field value "seed"))
            (← metadata (← field value "metadata"))
      | "unary" => do
          keysWithin value ["op", "rule", "metadata", "child"]
          return Nabt.RecursiveSourceBridge.Node.unary (← nat (← field value "rule"))
            (← metadata (← field value "metadata")) (← nodeAt depth (← field value "child"))
      | "binary" => do
          keysWithin value ["op", "rule", "metadata", "left", "right"]
          return Nabt.RecursiveSourceBridge.Node.binary (← nat (← field value "rule"))
            (← metadata (← field value "metadata"))
            (← nodeAt depth (← field value "left")) (← nodeAt depth (← field value "right"))
      | _ => invalid "unknown annotated node constructor"
    if parsed.nodes.length > maxNodes then return ← limited "an annotated tree exceeds 127 nodes"
    return parsed

def support (value : Json) : ProbeM (Nabt.UnitDiscovery.Support Char) := do
  keysWithin value ["source", "span"]
  return ⟨← source (← field value "source"), ← span (← field value "span")⟩

def receipt (value : Json) : ProbeM Nabt.RecursiveSourceBridge.Receipt := do
  keysWithin value ["target", "requirement", "positive", "witness_id", "supports"]
  return {
    target := ← nodeAt 32 (← field value "target")
    requirement := ← nat (← field value "requirement")
    positive := ← boolean (← field value "positive")
    witnessId := ← nat (← field value "witness_id")
    supports := ← limitedItems 32 support (← field value "supports") }

def context (value : Json) : ProbeM Nabt.RecursiveSourceBridge.Context := do
  return {
    inventory := ← limitedItems 32 source (← field value "inventory")
    interpreted := ← limitedItems maxReceipts receipt (← field value "interpreted")
    offered := ← limitedItems maxReceipts receipt (← field value "offered") }

def sourceJson (source : Nabt.UnitDiscovery.Source Char) : Json := Json.mkObj [
  ("source_id", toJson source.sourceId), ("revision", toJson source.revision),
  ("scope_id", toJson source.scopeId), ("atomization_id", toJson source.atomizationId),
  ("atoms", charsJson source.atoms)]

def spanJson (span : Nabt.UnitDiscovery.Span) : Json := Json.mkObj [
  ("source_id", toJson span.sourceId), ("revision", toJson span.revision),
  ("scope_id", toJson span.scopeId), ("atomization_id", toJson span.atomizationId),
  ("start", toJson span.start), ("stop", toJson span.stop)]

def tagJson (tag : Nabt.LicensedDerivation.Tag) : Json := Json.mkObj [
  ("rule_id", toJson tag.ruleId), ("reading_id", toJson tag.readingId),
  ("class_id", toJson tag.classId), ("requirements", toJson tag.requirements)]

def hostTreeJson : Nabt.LicensedDerivation.Tree Char → Json
  | .atom source before value after => Json.mkObj [
      ("op", toJson "atom"), ("source", sourceJson source),
      ("before", charsJson before), ("value", toJson (String.singleton value)), ("after", charsJson after)]
  | .join tag left right => Json.mkObj [
      ("op", toJson "join"), ("tag", tagJson tag), ("left", hostTreeJson left), ("right", hostTreeJson right)]
  | .wrap tag child => Json.mkObj [
      ("op", toJson "wrap"), ("tag", tagJson tag), ("child", hostTreeJson child)]
  | .substitute tag replacement child => Json.mkObj [
      ("op", toJson "substitute"), ("tag", tagJson tag),
      ("replacement", charsJson replacement), ("child", hostTreeJson child)]
  | .lift tag child => Json.mkObj [
      ("op", toJson "lift"), ("tag", tagJson tag), ("child", hostTreeJson child)]

def seedJson : Nabt.RecursiveLicensedAlgebra.Seed → Json
  | .root3 a b c => Json.mkObj [("kind", toJson "root3"), ("radicals", toJson [a,b,c])]
  | .root4 a b c d => Json.mkObj [("kind", toJson "root4"), ("radicals", toJson [a,b,c,d])]
  | .lexical entry => Json.mkObj [("kind", toJson "lexical"), ("entry", toJson entry)]

def coreTreeJson : Nabt.RecursiveLicensedAlgebra.Tree → Json
  | .leaf seed => Json.mkObj [("op", toJson "leaf"), ("seed", seedJson seed)]
  | .unary rule child => Json.mkObj [
      ("op", toJson "unary"), ("rule", toJson rule), ("child", coreTreeJson child)]
  | .binary rule left right => Json.mkObj [
      ("op", toJson "binary"), ("rule", toJson rule),
      ("left", coreTreeJson left), ("right", coreTreeJson right)]

def categoryName : Nabt.RecursiveLicensedAlgebra.Category → String
  | .root3 => "root3"
  | .root4 => "root4"
  | .noun => "noun"
  | .verb => "verb"
  | .particle => "particle"
  | .nounPhrase => "nounPhrase"
  | .verbPhrase => "verbPhrase"
  | .semiClause => "semiClause"
  | .nominalClause => "nominalClause"
  | .verbalClause => "verbalClause"
  | .clause => "clause"
  | .pending => "pending"

def provenanceName : Nabt.RecursiveSourceBridge.Provenance → String
  | .nativeTree => "native_tree"
  | .sourceReconstruction => "source_reconstruction"

def tokenJson {arity : Nat} : Nabt.Derivation.Token arity → Json
  | .slot index => Json.mkObj [("slot", toJson index.val)]
  | .literal value => Json.mkObj [("literal", toJson (String.singleton value))]

def readingJson : Nabt.UnitDiscovery.RootPatternReading → Json
  | .tri pattern root => Json.mkObj [
      ("arity", toJson (3 : Nat)), ("root", charsJson (List.ofFn root)),
      ("pattern", toJson (pattern.map tokenJson))]
  | .quad pattern root => Json.mkObj [
      ("arity", toJson (4 : Nat)), ("root", charsJson (List.ofFn root)),
      ("pattern", toJson (pattern.map tokenJson))]

def originJson : Nabt.RecursiveSourceBridge.Origin → Json
  | .literal value => Json.mkObj [("kind", toJson "literal"), ("value", toJson (String.singleton value))]
  | .radical index => Json.mkObj [("kind", toJson "radical"), ("index", toJson index)]

def alignmentJson (point : Nabt.RecursiveSourceBridge.AlignmentPoint) : Json := Json.mkObj [
  ("pattern_position", toJson point.patternPosition), ("source_position", toJson point.sourcePosition),
  ("origin", originJson point.origin)]

def morphologyJson (morphology : Nabt.RecursiveSourceBridge.Morphology) : Json := Json.mkObj [
  ("catalog_id", toJson morphology.catalogId), ("registry_id", toJson morphology.registryId),
  ("reading_id", toJson morphology.readingId), ("reading", readingJson morphology.reading),
  ("alignment", toJson (morphology.alignment.map alignmentJson))]

def roleJson (role : Nabt.RecursiveSourceBridge.Role) : Json := Json.mkObj [
  ("role", toJson role.role), ("reading_id", toJson role.readingId), ("target", spanJson role.target),
  ("head", role.head.map spanJson |>.getD Json.null),
  ("case", role.grammaticalCase.map toJson |>.getD Json.null),
  ("case_domain", role.caseDomain.map toJson |>.getD Json.null)]

def metadataJson (metadata : Nabt.RecursiveSourceBridge.Metadata) : Json := Json.mkObj [
  ("registry_id", toJson metadata.registryId), ("reading_id", toJson metadata.readingId),
  ("source", sourceJson metadata.source), ("host", spanJson metadata.host),
  ("host_tree", hostTreeJson metadata.hostTree),
  ("morphology", metadata.morphology.map morphologyJson |>.getD Json.null),
  ("section", metadata.wordSection.map (toJson ∘ categoryName) |>.getD Json.null),
  ("roles", toJson (metadata.roles.map roleJson)), ("evidence_ids", toJson metadata.evidenceIds),
  ("required", toJson metadata.required), ("provenance", toJson (provenanceName metadata.provenance)),
  ("unresolved", toJson metadata.unresolved)]

def nodeJson : Nabt.RecursiveSourceBridge.Node → Json
  | .leaf seed metadata => Json.mkObj [
      ("op", toJson "leaf"), ("seed", seedJson seed), ("metadata", metadataJson metadata)]
  | .unary rule metadata child => Json.mkObj [
      ("op", toJson "unary"), ("rule", toJson rule),
      ("metadata", metadataJson metadata), ("child", nodeJson child)]
  | .binary rule metadata left right => Json.mkObj [
      ("op", toJson "binary"), ("rule", toJson rule),
      ("metadata", metadataJson metadata), ("left", nodeJson left), ("right", nodeJson right)]

def statusName : Nabt.RecursiveSourceBridge.Status → String
  | .invalid => "INVALID_SOURCE_BINDING"
  | .sourceOnly => "SOURCE_ONLY"
  | .pending => "UNKNOWN"
  | .conditionalLicensed => "CONDITIONALLY_LICENSED"
  | .rejected => "REJECTED"

def numberBudget (request : Json) : ProbeM Nat := do
  let budget ← match ← optionalField request "max_number_bits" with
    | none => pure maxNumberBits
    | some value => nat value
  if budget > maxNumberBits then return ← limited "max_number_bits exceeds hard bound 4096"
  return budget

def numberOperation (request : Json) : ProbeM Json := do
  keysWithin request ["op", "registry_id", "tree", "max_number_bits"]
  let registry ← identifier (← field request "registry_id")
  let tree ← coreTreeAt 32 (← field request "tree")
  let budget ← numberBudget request
  let estimatedBits := Nabt.RecursiveSourceBridge.numberBits tree
  if estimatedBits > budget then return ← limited "structural number bit-cost estimate exceeds the budget before evaluation"
  let number := Nabt.RecursiveSourceBridge.structuralNumber tree
  return success "core_number" [
    ("number_domain", toJson Nabt.RecursiveSourceBridge.numberDomain), ("registry_id", toJson registry),
    ("number", toJson (toString number)), ("tree", coreTreeJson tree),
    ("estimated_max_number_bits", toJson estimatedBits), ("number_bit_budget", toJson budget),
    ("structural_only", toJson true), ("linguistically_licensed", toJson false),
    ("height", toJson tree.height), ("nodes", toJson (coreNodes tree))]

def coreInventory (value : Json) : ProbeM Nabt.RecursiveLicensedAlgebra.Inventory := do
  keysWithin value ["seeds", "unary_rules", "binary_rules"]
  return ⟨← limitedItems 64 seed (← field value "seeds"),
    ← limitedItems 16 nat (← field value "unary_rules"),
    ← limitedItems 16 nat (← field value "binary_rules")⟩

def inventoryJson (inventory : Nabt.RecursiveLicensedAlgebra.Inventory) : Json := Json.mkObj [
  ("seeds", toJson (inventory.seeds.map seedJson)),
  ("unary_rules", toJson inventory.unaryRules), ("binary_rules", toJson inventory.binaryRules)]

/-- Saturate before multiplication in each later stage; no candidate tree is
allocated until this recurrence has established the permitted result count. -/
def countWithin (inventory : Nabt.RecursiveLicensedAlgebra.Inventory) (cap : Nat) : Nat → Nat
  | 0 => min (cap + 1) inventory.seeds.length
  | height + 1 =>
      let previous := countWithin inventory cap height
      min (cap + 1) (inventory.seeds.length + inventory.unaryRules.length * previous +
        inventory.binaryRules.length * previous * previous)

def enumerationOperation (request : Json) : ProbeM Json := do
  keysWithin request ["op", "registry_id", "inventory", "height", "max_candidates", "max_number_bits"]
  let registry ← identifier (← field request "registry_id")
  let inventory ← coreInventory (← field request "inventory")
  let height ← nat (← field request "height")
  if height > maxHeight then return ← limited "enumeration height exceeds hard bound eight"
  let budget ← match ← optionalField request "max_candidates" with
    | none => pure maxCandidates
    | some value => nat value
  if budget > maxCandidates then return ← limited "max_candidates exceeds hard bound 4096"
  let numberBudget ← numberBudget request
  let normalized := Nabt.RecursiveSourceBridge.normalizeInventory inventory
  let predicted := countWithin normalized budget height
  if predicted > budget then
    return success "core_enumerate" [
      ("enumeration", toJson "EXHAUSTED"), ("search_complete", toJson false),
      ("linguistic_rejection", toJson false), ("registry_id", toJson registry),
      ("height", toJson height), ("candidate_budget", toJson budget),
      ("required_candidates_at_least", toJson predicted), ("candidates", toJson ([] : List Json))]
  let candidates := Nabt.RecursiveSourceBridge.uniqueCandidates inventory height
  let maximumBits := candidates.foldl (fun bound tree => max bound (Nabt.RecursiveSourceBridge.numberBits tree)) 0
  if maximumBits > numberBudget then
    return success "core_enumerate" [
      ("enumeration", toJson "EXHAUSTED"), ("search_complete", toJson false),
      ("linguistic_rejection", toJson false), ("registry_id", toJson registry),
      ("height", toJson height), ("reason", toJson "number_bit_budget"),
      ("estimated_max_number_bits", toJson maximumBits), ("number_bit_budget", toJson numberBudget),
      ("candidates", toJson ([] : List Json))]
  let entries := candidates.map fun tree => Json.mkObj [
    ("tree", coreTreeJson tree), ("number", toJson (toString (Nabt.RecursiveSourceBridge.structuralNumber tree)))]
  return success "core_enumerate" [
    ("enumeration", toJson "COMPLETE"), ("search_complete", toJson true),
    ("linguistic_rejection", toJson false), ("structural_only", toJson true),
    ("number_domain", toJson Nabt.RecursiveSourceBridge.numberDomain), ("registry_id", toJson registry),
    ("height", toJson height), ("candidate_count", toJson candidates.length),
    ("inventory", inventoryJson normalized),
    ("removed_duplicate_seeds", toJson (inventory.seeds.length - normalized.seeds.length)),
    ("removed_duplicate_unary_rules", toJson (inventory.unaryRules.length - normalized.unaryRules.length)),
    ("removed_duplicate_binary_rules", toJson (inventory.binaryRules.length - normalized.binaryRules.length)),
    ("estimated_max_number_bits", toJson maximumBits), ("number_bit_budget", toJson numberBudget),
    ("candidates", toJson entries)]

def nodeStepJson (context : Nabt.RecursiveSourceBridge.Context) (node : Nabt.RecursiveSourceBridge.Node) (index : Nat) : Json :=
  let positive := Nabt.RecursiveSourceBridge.positives context node
  let negative := Nabt.RecursiveSourceBridge.negatives context node
  Json.mkObj [
    ("preorder_index", toJson index), ("registry_id", toJson node.metadata.registryId),
    ("reading_id", toJson node.metadata.readingId), ("host", spanJson node.metadata.host),
    ("source_bound", toJson (node.localSourceValid context.inventory)),
    ("requirements", toJson node.requirements),
    ("missing_requirements", toJson (node.requirements.filter fun requirement =>
      !Nabt.RecursiveSourceBridge.hasRequirement positive requirement)),
    ("positive_complete", toJson (Nabt.RecursiveSourceBridge.localPositive context node)),
    ("negative", toJson (Nabt.RecursiveSourceBridge.localNegative context node)),
    ("admitted_positive_witness_ids", toJson (positive.map Nabt.RecursiveSourceBridge.Receipt.witnessId)),
    ("known_negative_witness_ids", toJson (negative.map Nabt.RecursiveSourceBridge.Receipt.witnessId)),
    ("provenance", toJson (provenanceName node.metadata.provenance)),
    ("unresolved", toJson node.metadata.unresolved),
    ("reconstruction_matches", toJson (node.metadata.hostTree.reconstruct == node.metadata.source.atoms))]

def bridgeOperation (request : Json) : ProbeM Json := do
  keysWithin request ["op", "node", "inventory", "interpreted", "offered"]
  let node ← nodeAt 32 (← field request "node")
  let context ← context request
  let report := Nabt.RecursiveSourceBridge.assess context node
  return success "bridge_assess" [
    ("verdict", toJson (statusName report.status)),
    ("source_bound", toJson report.sourceBound),
    ("conditional_licensed", toJson (report.status == .conditionalLicensed)),
    ("all_premises", toJson report.allPremises), ("negative", toJson report.negative),
    ("linguistic_ready", toJson report.linguisticReady),
    ("atomization_domain", toJson Nabt.RecursiveSourceBridge.atomizationDomain),
    ("node", nodeJson node), ("erased_tree", coreTreeJson node.erase),
    ("nodes", toJson node.nodes.length),
    ("steps", toJson (node.nodes.zipIdx.map fun (step, index) => nodeStepJson context step index)),
    ("semantic_obligation", toJson "explicit_PR14_host_Licensed_and_Grammar_Certified_and_RealizationAligned_contracts_required")]

def dispatch (request : Json) : ProbeM Json := do
  let op ← str (← field request "op")
  let result ← match op with
    | "core_number" => numberOperation request
    | "core_enumerate" => enumerationOperation request
    | "bridge_assess" => bridgeOperation request
    | _ => invalid "unknown recursive bridge operation"
  if result.compress.toUTF8.size + 1 > maxOutputBytes then
    return ← limited "the complete JSONL output exceeds 16 MiB"
  return result

/-! The general Lean JSON parser stores object members in a map and therefore
forgets duplicate keys. This raw guard is local to this new probe: existing
ProbeJson consumers retain their frozen transport. Decode each object key as
a JSON string before comparing, so literal and escaped spellings cannot hide
a duplicate. String values are skipped without interpreting their contents. -/

structure KeyFrame where
  isObject : Bool
  expectingKey : Bool
  keys : Std.TreeSet String := {}

def jsonQuote : Char := Char.ofNat 34

def rejectDuplicateKeys (line : String) : ProbeM Unit := do
  let mut stack : List KeyFrame := []
  let mut quoted := false
  let mut escaped := false
  let mut captureKey := false
  let mut keyText : List Char := []
  for character in line.toList do
    if quoted then
      if captureKey then keyText := character :: keyText
      if escaped then
        escaped := false
      else if character == '\\' then
        escaped := true
      else if character == jsonQuote then
        quoted := false
        if captureKey then
          let keyJson ← liftParse (Json.parse (String.ofList keyText.reverse))
          let key ← str keyJson
          match stack with
          | frame :: rest =>
              if frame.keys.contains key then return ← invalid "duplicate JSON object key"
              stack := { frame with expectingKey := false, keys := frame.keys.insert key } :: rest
          | [] => return ← invalid "object key has no enclosing object"
          keyText := []
        captureKey := false
    else if character == jsonQuote then
      quoted := true
      escaped := false
      captureKey := match stack with
        | frame :: _ => frame.isObject && frame.expectingKey
        | [] => false
      keyText := if captureKey then [jsonQuote] else []
    else if character == '{' then
      stack := ⟨true, true, {}⟩ :: stack
    else if character == '[' then
      stack := ⟨false, false, {}⟩ :: stack
    else if character == '}' || character == ']' then
      stack := stack.drop 1
    else if character == ':' then
      match stack with
      | frame :: rest => stack := { frame with expectingKey := false } :: rest
      | [] => pure ()
    else if character == ',' then
      match stack with
      | frame :: rest =>
          if frame.isObject then stack := { frame with expectingKey := true } :: rest
      | [] => pure ()

def processRecursiveLine (bytes : ByteArray) (oversized : Bool) : Json :=
  if oversized then errorResponse ⟨"RESOURCE_LIMIT", "input line exceeds 1 MiB"⟩
  else match String.fromUTF8? bytes with
    | none => errorResponse ⟨"INVALID_INPUT", "input line is not valid UTF-8"⟩
    | some line =>
      match (do
        ProbeJson.preflight line "duplicate JSON object key"
        rejectDuplicateKeys line
        let request ← liftParse (Json.parse line)
        dispatch request : ProbeM Json) with
      | .ok result => result
      | .error failure => errorResponse failure

def emitRecursive (output : IO.FS.Stream) (bytes : ByteArray) (oversized : Bool) : IO Unit := do
  output.putStr ((processRecursiveLine bytes oversized).compress ++ "\n")
  output.flush

/-- Same bounded streaming and discard-to-newline contract as ProbeJson, with
the additional raw-key check before the lossy generic JSON object parser. -/
partial def readRecursiveLoop (input output : IO.FS.Stream)
    (pending : ByteArray := ByteArray.empty) (overflow : Bool := false) : IO Unit := do
  let chunk ← input.read 1
  if chunk.isEmpty then
    if !pending.isEmpty || overflow then emitRecursive output pending overflow
  else
    let mut pending := pending
    let mut overflow := overflow
    for byte in chunk do
      if byte == 10 then
        emitRecursive output pending overflow
        pending := ByteArray.empty
        overflow := false
      else if !overflow then
        if pending.size < ProbeJson.maxLineBytes then pending := pending.push byte
        else
          pending := ByteArray.empty
          overflow := true
    readRecursiveLoop input output pending overflow

end RecursiveBridgeProbe

def main : IO Unit := do
  let input ← IO.getStdin
  let output ← IO.getStdout
  RecursiveBridgeProbe.readRecursiveLoop input output
