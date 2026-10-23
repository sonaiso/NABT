import Nabt.Derivation
import Nabt.NominalPatterns
import Lean

/-! The installed finite shape catalog and a separately named conditional
paradigm law. Neither export is a dictionary of words, roots or meanings. -/

open Lean Nabt.Derivation

def tokenJson : Token n → Json
  | .literal value => toJson (String.singleton value)
  | .slot index => toJson index.val

def patternJson (pattern : CatalogPattern) : Json := Json.mkObj [
  ("id", toJson pattern.id),
  ("label", toJson pattern.label),
  ("arity", toJson pattern.arity),
  ("tokens", toJson (pattern.tokens.map tokenJson)),
  ("family", toJson pattern.family),
  ("form", toJson pattern.form),
  ("voice", toJson pattern.voice),
  ("augmentation", toJson pattern.augmentation),
  ("source_contract", toJson pattern.sourceContract),
  ("source_kind", toJson pattern.sourceKind),
  ("root_domain", toJson pattern.rootDomain),
  ("endings", toJson (pattern.endings.map String.singleton))
]

def paradigmRows : List Json := (List.range 8).flatMap fun positiveNumber =>
  (List.range 8).map fun negativeNumber =>
    let positive := Paradigm.Mask.ofCode positiveNumber
    let negative := Paradigm.Mask.ofCode negativeNumber
    Json.mkObj [
      ("positive_mask", toJson positiveNumber),
      ("negative_mask", toJson negativeNumber),
      ("models", toJson ((Paradigm.models positive negative).map Paradigm.Mask.code)),
      ("categories", toJson ((Paradigm.categories positive negative).map Paradigm.Category.label))
    ]

def derivationJson : Json := Json.mkObj [
  ("schema_version", toJson (1 : Nat)),
  ("law_id", toJson lawId),
  ("alphabet_id", toJson alphabetId),
  ("profile", toJson profile),
  ("patterns", toJson ((corePatterns ++ Nabt.NominalPatterns.patterns).map patternJson)),
  ("paradigm_law_id", toJson Paradigm.lawId),
  ("paradigm_rows", toJson paradigmRows),
  ("scope", toJson "EXACT_SHAPE_CANDIDATES_NOT_LEXICAL_ROOTS_OR_SEMANTIC_CLASSES"),
  ("paradigm_scope", toJson "CONDITIONAL_SAME_VERB_AVAILABILITY_NOT_NOMINAL_JAMID_MUSHTAQ")
]

def main : IO Unit := IO.println derivationJson.compress
