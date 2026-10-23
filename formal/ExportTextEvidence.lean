import Nabt.TextEvidence
import Lean

/-! Complete finite tables for the conditional cue-intersection and receipt
activation functions. Neither table is a lexical answer dictionary. -/

open Lean Nabt.TextEvidence

def bit (number index : Nat) : Bool := number / 2 ^ index % 2 == 1

def textEvidenceJson : Json := Json.mkObj [
  ("schema_version", toJson (1 : Nat)),
  ("law_id", toJson lawId),
  ("number_domains", Json.mkObj [
    ("kind_mask", toJson maskNumberDomain),
    ("activation_mask", toJson activationNumberDomain)]),
  ("kinds", toJson (Nabt.Words.kinds.map fun kind => Json.mkObj [
    ("code", toJson kind.code), ("label", toJson kind.label)])),
  ("cues", toJson (cues.map fun cue => Json.mkObj [
    ("bit", toJson cue.code), ("label", toJson cue.label),
    ("kind", toJson cue.kind.code)])),
  ("kind_rows", toJson ((List.range 8).map fun number =>
    let mask : CueMask := ⟨bit number 0, bit number 1, bit number 2⟩
    Json.mkObj [
      ("mask", toJson mask.code),
      ("candidates", toJson (mask.candidates.map Nabt.Words.Kind.code)),
      ("selected", toJson ((select mask.candidates).map Nabt.Words.Kind.code))])),
  ("activation_bits", toJson ["identity_match", "rule_match", "active", "blocked",
    "support_present", "support_valid"]),
  ("receipt_rows", toJson ((List.range 64).map fun number => Json.mkObj [
    ("mask", toJson number),
    ("activated", toJson (activation (bit number 0) (bit number 1)
      (bit number 2) (bit number 3) (bit number 4) (bit number 5)))])),
  ("scope", toJson "CONDITIONAL_CUE_ALGEBRA_NOT_LINGUISTIC_ACTIVATION_OR_PARSER_REFINEMENT")
]

def main : IO Unit := IO.println textEvidenceJson.compress
