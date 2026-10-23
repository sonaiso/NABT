import Nabt.Morphology
import Lean

/-! Complete operation tables for the finite conditional morphology law.
Source extraction, word identity validation, and evidence replay remain outside
this exporter. No table row is a source attestation or a lexical dictionary. -/

open Lean Nabt.Morphology

def morphologyJson : Json := Json.mkObj [
  ("schema_version", toJson (1 : Nat)),
  ("law_id", toJson lawId),
  ("number_domains", Json.mkObj [
    ("verb_input", toJson verbStateNumberDomain),
    ("qualified_causes", toJson causeInputNumberDomain),
    ("diptote_context", toJson genitiveStateNumberDomain),
    ("diptote_residual", toJson genitiveResidualNumberDomain)]),
  ("evidence", toJson (evidenceStates.map fun evidence => Json.mkObj [
    ("code", toJson evidence.code), ("label", toJson evidence.label),
    ("positive", toJson evidence.positive), ("negative", toJson evidence.negative),
    ("values", toJson evidence.values)])),
  ("constructions", toJson (constructions.map fun construction => Json.mkObj [
    ("code", toJson construction.code), ("label", toJson construction.label)])),
  ("tenses", toJson (tenses.map fun tense => Json.mkObj [
    ("code", toJson tense.code), ("label", toJson tense.label)])),
  ("nuns", toJson (nunConnections.map fun nun => Json.mkObj [
    ("code", toJson nun.code), ("label", toJson nun.label)])),
  ("verb_rows", toJson (verbInputs.map fun input => Json.mkObj [
    ("tense", toJson input.1.code), ("nun", toJson input.2.code),
    ("number", toJson (verbStateNumber input.1 input.2)),
    ("construction", toJson (verbConstruction input.1 input.2).code)])),
  ("verb_partial", toJson ((none :: tenses.map some).flatMap fun tense =>
    (none :: nunConnections.map some).map fun nun =>
      let query : VerbQuery := ⟨tense, nun⟩
      Json.mkObj [
        ("tense", toJson (tense.map Tense.code)),
        ("nun", toJson (nun.map NunConnection.code)),
        ("input_numbers", toJson ((verbReadings query).map fun input =>
          verbStateNumber input.1 input.2)),
        ("constructions", toJson ((verbCandidates query).map Construction.code))])),
  ("noun_rows", toJson ([false, true].map fun resemblance => Json.mkObj [
    ("particle_resemblance", toJson resemblance),
    ("construction", toJson (nounConstruction resemblance).code)])),
  ("noun_partial", toJson (evidenceStates.map fun evidence => Json.mkObj [
    ("particle_resemblance", toJson evidence.code),
    ("constructions", toJson ((nounCandidates evidence).map Construction.code))])),
  ("particle", Json.mkObj [
    ("kind", toJson Nabt.Words.Kind.particle.code),
    ("construction", toJson particleConstruction.code)]),
  ("nominal_denotations", toJson (nominalDenotations.map fun denotation => Json.mkObj [
    ("code", toJson denotation.code), ("label", toJson denotation.label)])),
  ("nominal_rows", toJson ([false, true].flatMap fun universal =>
    [false, true].map fun qualityBearer => Json.mkObj [
      ("universal", toJson universal), ("quality_bearer", toJson qualityBearer),
      ("denotation", toJson (nominalDenotation universal qualityBearer).code)])),
  ("nominal_partial", toJson (evidenceStates.flatMap fun universal =>
    evidenceStates.map fun qualityBearer => Json.mkObj [
      ("universal", toJson universal.code), ("quality_bearer", toJson qualityBearer.code),
      ("denotations", toJson ((nominalDenotationCandidates universal qualityBearer).map
        NominalDenotation.code))])),
  ("cause_traits", toJson (causeTraits.map fun trait => Json.mkObj [
    ("bit", toJson trait.code), ("label", toJson trait.label)])),
  ("cause_rows", toJson (causeInputs.map fun input => Json.mkObj [
    ("mask", toJson input.val), ("diptote", toJson input.diptote)])),
  ("genitive_results", toJson ([GenitiveResult.pending, .fatha, .kasra, .conflict].map
    fun result => Json.mkObj [
      ("code", toJson result.code), ("label", toJson result.label),
      ("ending", toJson (result.ending.map Nabt.Words.Ending.code))])),
  ("genitive_residual_bits", Json.mkObj [("al", toJson (0 : Nat)), ("idhafa", toJson (1 : Nat))]),
  ("genitive_rows", toJson (genitiveContexts.map fun context => Json.mkObj [
    ("number", toJson context.number),
    ("al", toJson context.al.code), ("idhafa", toJson context.idhafa.code),
    ("positive", toJson context.positive), ("negative", toJson context.negative),
    ("plans", toJson context.plans),
    ("result", toJson (genitiveResult context).code),
    ("ending", toJson ((genitiveResult context).ending.map Nabt.Words.Ending.code)),
    ("candidates", toJson ((genitiveCandidates context).map Nabt.Words.Ending.code))]))
]

def main : IO Unit := IO.println morphologyJson.compress
