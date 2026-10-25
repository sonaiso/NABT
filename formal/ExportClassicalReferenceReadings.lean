import Nabt.ClassicalReferenceReadings
import Lean

open Lean Nabt.ClassicalReferenceReadings

def endingName : Ending → String
  | .nominative => "nominative" | .accusative => "accusative"
  | .genitive => "genitive" | .jussive => "jussive"

def numberName : Number → String
  | .singular => "singular" | .dual => "dual" | .plural => "plural"

def readingName : Reading → String
  | .topic => "topic" | .omittedVerb => "omitted_verb"
  | .descriptionSubject => "description_subject" | .frontedPredicate => "fronted_predicate"
  | .anInterpretiveIndicative => "an_interpretive_indicative"
  | .anInterpretiveJussive => "an_interpretive_jussive"
  | .anMasdariyyaSubjunctive => "an_masdariyya_subjunctive"

def frameJson (f : Frame) : Json :=
  let obs := match observed f with | none => Json.null | some e => toJson (endingName e)
  match f with
  | .freeIshtighal _ => Json.mkObj [("family",toJson "free_ishtighal"),("observed_ending",obs)]
  | .matchedDescription n _ => Json.mkObj [("family",toJson "matched_description"),
      ("number",toJson (numberName n)),("observed_ending",obs)]
  | .interpretiveAn b _ => Json.mkObj [("family",toJson "interpretive_an"),
      ("has_la",toJson b),("observed_ending",obs)]

def frames : List Frame :=
  let endings : List (Option Ending) :=
    [none, some .nominative, some .accusative, some .genitive, some .jussive]
  endings.flatMap fun e =>
    [.freeIshtighal e, .matchedDescription .singular e,
     .matchedDescription .dual e, .matchedDescription .plural e,
     .interpretiveAn true e, .interpretiveAn false e]

def main : IO Unit := do
  let rows := frames.map fun f => Json.mkObj [
    ("frame", frameJson f),
    ("readings",toJson ((enumerate f).map readingName)),
    ("ranks",toJson ((enumerate f).map rank)),
    ("endings",toJson ((enumerate f).map (endingName ∘ ending)))]
  IO.println (Json.mkObj [("law_id",toJson lawId),("rows",toJson rows)]).compress
