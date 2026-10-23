import Nabt.PersonEvidence
import Lean

open Lean Nabt.PersonEvidence

def profileJson (p : Profile) : Json := Json.mkObj [
  ("qac", toJson p.qac), ("person", toJson p.person),
  ("gender", toJson p.gender), ("number", toJson p.number)]

def personEvidenceJson : Json := Json.mkObj [
  ("schema_version", toJson (1 : Nat)), ("law_id", toJson lawId),
  ("profiles", toJson (profiles.map profileJson)),
  ("families", toJson (families.map fun f => Json.mkObj [
    ("id", toJson f.label), ("five_verb", toJson f.fiveVerb), ("profiles", toJson f.codes)])),
  ("prefixes", toJson prefixes),
  ("prefix_rows", toJson (families.flatMap fun f => prefixes.map fun pre => Json.mkObj [
    ("family", toJson f.label), ("prefix", toJson pre),
    ("profiles", toJson ((candidates f pre).map Profile.qac))])),
  ("separate_pronouns", toJson (Nabt.NominalEvidence.pronounRows.map fun p => Json.mkObj [
    ("surface", toJson p.surface), ("person", toJson p.person),
    ("gender", toJson p.gender), ("number", toJson p.number)])),
  ("attached_forms", toJson (attachedForms.map fun p => Json.mkObj [
    ("surface", toJson p.surface), ("qac", toJson p.qac), ("host", toJson p.host)])),
  ("scope", toJson "CONDITIONAL_CORRELATED_PERSON_FAMILIES_NOT_PREFIX_CLASSIFICATION_OR_REFERENCE"),
  ("source_scope", toJson "NEW_UNICODE_PROJECTION_WITH_EXTERNAL_SOURCE_AND_PARSER_PREMISES"),
  ("nun_scope", toJson "FULL_PARADIGM_AND_SEGMENTATION_REQUIRED_NO_ROLE_CASE_OR_DIRECTNESS_FROM_ADJACENCY")]

def main : IO Unit := IO.println personEvidenceJson.compress
