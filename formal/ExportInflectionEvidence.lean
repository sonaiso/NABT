import Nabt.InflectionEvidence
import Lean

/-! Conditional sign and relation tables; this exporter does not acquire a
declension class, segmentation, nun function or governing relation from text. -/

open Lean Nabt.InflectionEvidence

def bit (n i : Nat) : Bool := n / 2 ^ i % 2 == 1

def realizationJson (r : Realization) : Json := Json.mkObj [
  ("sign", toJson r.sign.code), ("mode", toJson r.mode.code),
  ("origin", toJson r.origin.code), ("surface", toJson r.surface.code)]

def inflectionEvidenceJson : Json := Json.mkObj [
  ("schema_version", toJson (1 : Nat)),
  ("law_id", toJson lawId),
  ("convention", toJson convention),
  ("surface_law_id", toJson Nabt.Words.lawId),
  ("signs", toJson (signs.map Sign.label)),
  ("modes", toJson (modes.map Mode.label)),
  ("origins", toJson (origins.map Origin.label)),
  ("case_domains", toJson (caseDomains.map CaseDomain.label)),
  ("rows", toJson (rows.map fun r => Json.mkObj [
    ("class", toJson r.cls.code), ("case", toJson r.grammaticalCase.code),
    ("sign", toJson r.realization.sign.code), ("mode", toJson r.realization.mode.code),
    ("origin", toJson r.realization.origin.code), ("surface", toJson r.realization.surface.code)])),
  ("diptote_rows", toJson (Nabt.Morphology.genitiveContexts.map fun c => Json.mkObj [
    ("code", toJson c.number), ("al", toJson c.al.code), ("idhafa", toJson c.idhafa.code),
    ("status", toJson (Nabt.Morphology.genitiveResult c).label),
    ("realizations", toJson ((diptoteRealizations c).map realizationJson))])),
  ("nun_rows", toJson (nunKinds.map fun n => Json.mkObj [
    ("code", toJson n.code), ("label", toJson n.label)])),
  ("relation_rows", toJson (relations.map fun r => Json.mkObj [
    ("code", toJson r.code), ("label", toJson r.label),
    ("kind", toJson r.kind.code), ("case", toJson r.requiredCase.code)])),
  ("receipt_bits", toJson ["identity_match", "rule_match", "active", "blocked",
    "support_present", "support_valid", "kind_match", "construction_known"]),
  ("receipt_rows", toJson ((List.range 256).map fun n => Json.mkObj [
    ("mask", toJson n), ("activated", toJson (activation (bit n 0) (bit n 1)
      (bit n 2) (bit n 3) (bit n 4) (bit n 5) (bit n 6) (bit n 7)))])),
  ("construction_rows", toJson (Nabt.Morphology.constructions.map fun c => Json.mkObj [
    ("construction", toJson c.code), ("domain", toJson (constructionDomain c).code)])),
  ("scope", toJson "CONDITIONAL_SIGNS_AND_SOURCE_BOUND_RELATIONS_NOT_FREE_TEXT_OR_CLASS_INFERENCE"),
  ("diptote_scope", toJson "GENITIVE_ROWS_REQUIRE_QUALIFIED_FOUR_STATE_CONTEXT_NOT_ASSUMED_ABSENCE"),
  ("nun_scope", toJson "TYPED_READING_ONLY_NO_CASE_OR_ROLE_FROM_NUN_KIND_ALONE"),
  ("segmentation_scope", toJson "EXACT_BYTE_PARTITION_REQUIRES_SEPARATE_GRAMMATICAL_LICENSE"),
  ("receipt_scope", toJson "IDENTITY_AND_SUPPORT_CHECK_IS_NOT_PROOF_OF_EXTERNAL_SOURCE_OR_PARSER_CORRECTNESS")
]

def main : IO Unit := IO.println inflectionEvidenceJson.compress
