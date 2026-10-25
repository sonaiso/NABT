import Nabt.ClassicalHamza
import Lean

open Lean Nabt.ClassicalHamza

def boundaryName : Boundary → String
  | .ibtida => "ibtida" | .wasl => "wasl" | .waqf => "waqf"
def originName : Origin → String
  | .added => "added" | .radical => "radical" | .unknown => "unknown"
def verbName : VerbMedial → String
  | .changedToAlif => "changed_to_alif" | .retained => "retained" | .unknown => "unknown"
def singularOriginName : SingularOrigin → String
  | .addedLong => "added_long" | .radicalLong => "radical_long"
  | .nonlong => "nonlong" | .unknown => "unknown"
def templateName : Template → String
  | .mafail => "mafail" | .mafailLong => "mafail_long"
  | .other => "other" | .unknown => "unknown"
def profileName : Profile → String
  | .namedCommon => "named_common" | .allAttested => "all_attested"
def glideName : Glide → String
  | .waw => "waw" | .ya => "ya"
def operationName : Operation → String
  | .interrogativeIbdal => "interrogative_ibdal"
  | .interrogativeTashil => "interrogative_tashil"
  | .hamzateFinal => "hamzate_final" | .hamzateMedial => "hamzate_medial"
  | .hamzatePlural => "hamzate_plural" | .hamzateSecondGlide => "hamzate_second_glide"
  | .shortCommand => "short_command" | .fullDialectCommand => "full_dialect_command"

def ruleId : Frame → String
  | .interrogative .. => "HAMZA-INTERROGATIVE-AL"
  | .finalLong .. => "HAMZA-FINAL-LONG"
  | .active .. => "HAMZA-ACTIVE-PARTICIPLE"
  | .broken .. => "HAMZA-BROKEN-PLURAL"
  | .twoGlides .. => "HAMZA-TWO-GLIDES"
  | .lexical .. => "HAMZA-LEXICAL-COMMAND"

def frameJson : Frame → Json
  | .interrogative tail b => Json.mkObj [
      ("tail", toJson tail), ("boundary", toJson (boundaryName b))]
  | .finalLong pre g o suffix => Json.mkObj [
      ("prefix", toJson pre), ("glide", toJson (glideName g)),
      ("alif_origin", toJson (originName o)), ("suffix", toJson suffix)]
  | .active a z g v => Json.mkObj [
      ("first", toJson a), ("last", toJson z), ("glide", toJson (glideName g)),
      ("verb_medial", toJson (verbName v))]
  | .broken a b l z feminine o t => Json.mkObj [
      ("singular", toJson ([a, b, l, z] ++ if feminine then ["ة"] else [])),
      ("singular_long_origin", toJson (singularOriginName o)),
      ("plural_template", toJson (templateName t))]
  | .twoGlides underlying t => Json.mkObj [
      ("underlying_plural", toJson underlying), ("plural_template", toJson (templateName t))]
  | .lexical root p => Json.mkObj [
      ("root", toJson root), ("profile", toJson (profileName p))]

def frames : List Frame :=
  ([Boundary.ibtida, .wasl, .waqf].map fun b => .interrogative ["ر", "ج", "ل"] b) ++
  ([Origin.added, .radical, .unknown].flatMap fun o =>
    [[], ["ن"]].map fun suffix => .finalLong ["د", "ع"] .waw o suffix) ++
  ([VerbMedial.changedToAlif, .retained, .unknown].map fun v => .active "ق" "ل" .waw v) ++
  ([SingularOrigin.addedLong, .radicalLong, .nonlong, .unknown].flatMap fun o =>
    [Template.mafail, .mafailLong, .other, .unknown].map fun t =>
      .broken "ص" "ح" "ي" "ف" true o t) ++
  ([Template.mafail, .mafailLong, .other, .unknown].map fun t =>
    .twoGlides ["ء", "و", "ا", "و", "ل"] t) ++
  ([["ء", "خ", "ذ"], ["ء", "ك", "ل"], ["ء", "م", "ر"], ["ء", "س", "ر"]].flatMap fun root =>
    [Profile.namedCommon, .allAttested].map fun p => .lexical root p)

def main : IO Unit := do
  let rows := frames.map fun f => Json.mkObj [
    ("rule_id", toJson (ruleId f)), ("frame", frameJson f),
    ("input", toJson (input f)), ("operations", toJson ((enumerate f).map operationName)),
    ("outputs", toJson (outputs f))]
  IO.println (Json.mkObj [("law_id", toJson lawId), ("rows", toJson rows)]).compress
