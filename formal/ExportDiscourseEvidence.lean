import Nabt.DiscourseEvidence
import Lean

open Lean Nabt.DiscourseEvidence

def bit (mask position : Nat) : Bool := mask / 2 ^ position % 2 == 1
def featureValues : List (Option Nat) := [none, some 0, some 1, some 2, some 3]
def featureJson : Option Nat → Json | none => Json.null | some n => toJson n
def refWitness (mask : Nat) : ReferenceWitness :=
  ⟨bit mask 0, bit mask 1, bit mask 2, bit mask 3, bit mask 4, bit mask 5, bit mask 6⟩
def assertionWitness (mask : Nat) : AssertionWitness :=
  ⟨bit mask 0, bit mask 1, bit mask 2, bit mask 3, bit mask 4, bit mask 5⟩

def discourseEvidenceJson : Json := Json.mkObj [
  ("schema_version", toJson (1 : Nat)),
  ("law_id", toJson lawId),
  ("role_rows", toJson (discourseRoles.map fun role => Json.mkObj [
    ("label", toJson role.label), ("case", toJson role.requiredCase.code)])),
  ("scope", toJson "CONDITIONAL_REFERENCE_AND_QUALIFIED_SOURCE_COMMITMENTS_NOT_EXTERNAL_TRUTH_OR_FREE_TEXT_PARSER"),
  ("feature_values", toJson (featureValues.map featureJson)),
  ("compatibilities", toJson (compatibilities.map Compatibility.label)),
  ("feature_rows", toJson (featureValues.flatMap fun left => featureValues.map fun right => Json.mkObj [
    ("left", featureJson left), ("right", featureJson right),
    ("status", toJson (featureCompatibility left right).label)])),
  ("combine_rows", toJson (compatibilities.flatMap fun left => compatibilities.map fun right => Json.mkObj [
    ("left", toJson left.label), ("right", toJson right.label),
    ("status", toJson (combineCompatibility left right).label)])),
  ("reference_origins", toJson (referenceOrigins.map ReferenceOrigin.label)),
  ("reference_bits", toJson ["origin_licensed", "identity_bound", "source_supported",
    "scope_allowed", "quote_allowed", "order_licensed", "return_licensed"]),
  ("reference_rows", toJson (referenceOrigins.flatMap fun origin => compatibilities.flatMap fun status =>
    (List.range 128).map fun mask => Json.mkObj [
      ("origin", toJson origin.label), ("compatibility", toJson status.label),
      ("mask", toJson mask), ("allowed", toJson (referenceAllowed origin status (refWitness mask)))])),
  ("selection_rows", toJson ((List.range 3).flatMap fun count => [false, true].flatMap fun closed =>
    [false, true].map fun confirmed => Json.mkObj [
      ("count_class", toJson count), ("closed_scope", toJson closed), ("all_confirmed", toJson confirmed),
      ("status", toJson (selectionStatus count closed confirmed).label)])),
  ("selection_scope", toJson "DISTINCT_SURVIVING_IDENTITIES_WITHIN_DECLARED_COMPLETE_UNIVERSE;COUNT_CLASS_2_MEANS_MULTIPLE"),
  ("forces", toJson (forces.map Force.label)),
  ("assertion_bits", toJson ["licensed_syntax", "scope_complete", "references_complete",
    "qualifiers_preserved", "nonquoted", "source_supported"]),
  ("assertion_rows", toJson (forces.flatMap fun force => (List.range 64).map fun mask => Json.mkObj [
    ("force", toJson force.label), ("mask", toJson mask),
    ("allowed", toJson (assertionAllowed force (assertionWitness mask)))])),
  ("polarities", toJson (polarities.map Polarity.label)),
  ("negation_rows", toJson (polarities.map fun p => Json.mkObj [
    ("input", toJson p.label), ("output", toJson (negate p).label)])),
  ("connectors", toJson (connectors.map Connector.label)),
  ("truth_rows", toJson (connectors.flatMap fun connector => [false, true].flatMap fun left =>
    [false, true].map fun right => Json.mkObj [
      ("operator", toJson connector.label), ("left", toJson left), ("right", toJson right),
      ("value", toJson (truthValue connector left right))])),
  ("coordination_rows", toJson (connectors.flatMap fun connector => polarities.map fun polarity => Json.mkObj [
    ("operator", toJson connector.label), ("polarity", toJson polarity.label),
    ("project_branches", toJson (projectBranches connector polarity))])),
  ("claim_fields", toJson ["predicate", "arguments", "polarity", "tense", "time", "place", "restriction"]),
  ("claim_projection_rows", toJson ((List.range 128).map fun mask => Json.mkObj [
    ("mask", toJson mask), ("allowed", toJson (claimProjectionAllowed
      (bit mask 0) (bit mask 1) (bit mask 2) (bit mask 3) (bit mask 4) (bit mask 5) (bit mask 6)))])),
  ("causal_bits", toJson ["relation_licensed", "source_supported", "scope_complete", "endpoints_resolved"]),
  ("causal_rows", toJson ((List.range 16).map fun mask => Json.mkObj [
    ("mask", toJson mask), ("allowed", toJson (causalAllowed
      (bit mask 0) (bit mask 1) (bit mask 2) (bit mask 3)))]))
]

def main : IO Unit := IO.println discourseEvidenceJson.compress
