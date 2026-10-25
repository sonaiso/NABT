import Nabt.LinguisticTruth
import ProbeJson

open Lean ProbeJson Nabt.LinguisticTruth Nabt.SemanticInference
namespace LinguisticTruthMain

def exactKeys (j : Json) (keys : List String) : ProbeM Unit := do
  let obj ← liftParse j.getObj?
  if obj.size != keys.length || keys.any (fun k => (obj.get? k).isNone) then
    invalid ("expected exactly: " ++ String.intercalate ", " keys)
  else pure ()

def textValue (j : Json) : ProbeM String := do
  let s ← str j
  if s.utf8ByteSize > 16384 then limited "text field exceeds 16384 UTF8 bytes" else pure s

def boundedItems (limit : Nat) (parse : Json → ProbeM α) (j : Json) : ProbeM (List α) := do
  let xs ← liftParse j.getArr?
  if xs.size > limit then return ← limited "array exceeds native limit"
  xs.toList.mapM parse

def parseCitation (j : Json) : ProbeM Nabt.LexicalDenotation.Citation := do
  exactKeys j ["work", "revision", "source_sha256", "start_byte", "end_byte", "quotation"]
  return ⟨← textValue (← field j "work"), ← textValue (← field j "revision"),
    ← textValue (← field j "source_sha256"), ← nat (← field j "start_byte"),
    ← nat (← field j "end_byte"), ← textValue (← field j "quotation")⟩

def parseOccurrence (j : Json) : ProbeM Nabt.LexicalDenotation.Occurrence := do
  exactKeys j ["source", "revision", "raw", "start_byte", "end_byte", "referent", "time", "context"]
  return ⟨← textValue (← field j "source"), ← textValue (← field j "revision"),
    ← textValue (← field j "raw"), ← nat (← field j "start_byte"), ← nat (← field j "end_byte"),
    ← textValue (← field j "referent"), ← textValue (← field j "time"), ← textValue (← field j "context")⟩

def parseFrame (j : Json) : ProbeM Frame := do
  exactKeys j ["occurrence", "expression", "convention"]
  return ⟨← parseOccurrence (← field j "occurrence"), ← textValue (← field j "expression"),
    ← textValue (← field j "convention")⟩

def parseOrigin (j : Json) : ProbeM Origin := do
  match ← str j with
  | "original" => pure .original | "transferred" => pure .transferred
  | _ => invalid "origin must be original or transferred"

def parseDesignation (j : Json) : ProbeM Designation := do
  exactKeys j ["id", "expression", "sense", "convention", "origin", "citation"]
  return ⟨← textValue (← field j "id"), ← textValue (← field j "expression"),
    ← textValue (← field j "sense"), ← textValue (← field j "convention"),
    ← parseOrigin (← field j "origin"), ← parseCitation (← field j "citation")⟩

def parseRelation (j : Json) : ProbeM Relation := do
  exactKeys j ["designation", "target_sense", "kind", "citation"]
  return ⟨← parseDesignation (← field j "designation"), ← textValue (← field j "target_sense"),
    ← textValue (← field j "kind"), ← parseCitation (← field j "citation")⟩

def parseCandidate (j : Json) : ProbeM Candidate := do
  exactKeys j ["designation", "intended_sense", "relation"]
  let r ← field j "relation"
  return ⟨← parseDesignation (← field j "designation"), ← textValue (← field j "intended_sense"),
    ← if r == Json.null then pure none else some <$> parseRelation r⟩

def parseJudgment (j : Json) : ProbeM Judgment := do
  match ← str (← field j "kind") with
  | "established" =>
    exactKeys j ["kind", "designation"]
    return .established (← parseDesignation (← field j "designation"))
  | "used" =>
    exactKeys j ["kind", "frame", "sense"]
    return .used (← parseFrame (← field j "frame")) (← textValue (← field j "sense"))
  | "related" =>
    exactKeys j ["kind", "relation"]
    return .related (← parseRelation (← field j "relation"))
  | "excludes" =>
    exactKeys j ["kind", "frame", "designation"]
    return .excludes (← parseFrame (← field j "frame")) (← parseDesignation (← field j "designation"))
  | _ => invalid "unknown judgment kind"

def parseAtom (j : Json) : ProbeM (Atom Judgment) := do
  exactKeys j ["value", "positive", "scope"]
  return ⟨← parseJudgment (← field j "value"), ← boolean (← field j "positive"),
    ← textValue (← field j "scope")⟩

def citationJson (c : Nabt.LexicalDenotation.Citation) : Json := Json.mkObj [
  ("work", toJson c.work), ("revision", toJson c.revision), ("source_sha256", toJson c.sourceSha256),
  ("start_byte", toJson c.startByte), ("end_byte", toJson c.endByte), ("quotation", toJson c.quotation)]
def occurrenceJson (o : Nabt.LexicalDenotation.Occurrence) : Json := Json.mkObj [
  ("source", toJson o.source), ("revision", toJson o.revision), ("raw", toJson o.raw),
  ("start_byte", toJson o.startByte), ("end_byte", toJson o.endByte), ("referent", toJson o.referent),
  ("time", toJson o.time), ("context", toJson o.context)]
def frameJson (f : Frame) : Json := Json.mkObj [("occurrence", occurrenceJson f.occurrence),
  ("expression", toJson f.expression), ("convention", toJson f.convention)]
def designationJson (d : Designation) : Json := Json.mkObj [("id", toJson d.id),
  ("expression", toJson d.expression), ("sense", toJson d.sense), ("convention", toJson d.convention),
  ("origin", toJson d.origin.label), ("citation", citationJson d.citation)]
def relationJson (r : Relation) : Json := Json.mkObj [("designation", designationJson r.designation),
  ("target_sense", toJson r.targetSense), ("kind", toJson r.kind), ("citation", citationJson r.citation)]
def candidateJson (c : Candidate) : Json := Json.mkObj [("designation", designationJson c.designation),
  ("intended_sense", toJson c.intendedSense),
  ("relation", match c.relation with | none => Json.null | some r => relationJson r)]
def judgmentJson : Judgment → Json
  | .established d => Json.mkObj [("kind", toJson "established"), ("designation", designationJson d)]
  | .used f s => Json.mkObj [("kind", toJson "used"), ("frame", frameJson f), ("sense", toJson s)]
  | .related r => Json.mkObj [("kind", toJson "related"), ("relation", relationJson r)]
  | .excludes f d => Json.mkObj [("kind", toJson "excludes"), ("frame", frameJson f),
      ("designation", designationJson d)]
def atomJson (a : Atom Judgment) : Json := Json.mkObj [("value", judgmentJson a.value),
  ("positive", toJson a.positive), ("scope", toJson a.scope)]

def response (f : Frame) (ds : List Designation) (rs : List Relation)
    (known : List (Atom Judgment)) (proposed : Option (List Candidate)) (budget : Nat) : Json :=
  let candidates := boundedEnumerate budget f ds rs
  Json.mkObj [
    ("status", toJson (if candidates.isSome then "CHECKED" else "RESOURCE_EXHAUSTED")),
    ("law_id", toJson lawId), ("authority", toJson "CONDITIONAL_SUPPLIED_LEDGER"),
    ("all_arabic_senses_enumerated", toJson false), ("world_truth_asserted", toJson false),
    ("complete_proposal", toJson (do let _ ← candidates; let cs ← proposed; return completeProposal f ds rs cs)),
    ("rows", Json.arr ((candidates.getD []).map fun c => Json.mkObj [
      ("candidate", candidateJson c), ("kind", toJson ((shape f c).map UsageKind.label)),
      ("verdict", toJson (assess f c known).label)]).toArray)]

def dispatch (j : Json) : ProbeM Json := do
  exactKeys j ["frame", "designations", "relations", "known", "proposed", "budget"]
  let f ← parseFrame (← field j "frame")
  let ds ← boundedItems 128 parseDesignation (← field j "designations")
  let rs ← boundedItems 128 parseRelation (← field j "relations")
  let known ← boundedItems 1024 parseAtom (← field j "known")
  let proposed ← field j "proposed"
  let ps ← if proposed == Json.null then pure none else some <$> boundedItems 256 parseCandidate proposed
  let budget ← nat (← field j "budget")
  if budget > 4096 then return ← limited "ledger budget exceeds 4096"
  return response f ds rs known ps budget

def errorJson (e : Failure) : Json := Json.mkObj [("status", toJson e.code), ("message", toJson e.message)]

def fixtureCitation : Nabt.LexicalDenotation.Citation :=
  ⟨"synthetic-conformance-only", "fixture-v1", "fixture-digest", 0, 7, "fixture"⟩
def fixtureFrame : Frame := ⟨⟨"fixture", "v1", "word", 0, 4, "unspecified", "unspecified", "fixture"⟩,
  "word", "linguistic"⟩
def fixtureDesignation : Designation := ⟨"first", "word", "animal", "linguistic", .original, fixtureCitation⟩
def fixtureRelation : Relation := ⟨fixtureDesignation, "brave", "similarity", fixtureCitation⟩

def requestJson (f : Frame) (ds : List Designation) (rs : List Relation)
    (known : List (Atom Judgment)) (proposed : Option (List Candidate)) (budget : Nat) : Json :=
  Json.mkObj [("frame", frameJson f), ("designations", toJson (ds.map designationJson)),
    ("relations", toJson (rs.map relationJson)), ("known", toJson (known.map atomJson)),
    ("proposed", match proposed with | none => Json.null | some cs => toJson (cs.map candidateJson)),
    ("budget", toJson budget)]

def fixtureRow (f : Frame) (ds : List Designation) (rs : List Relation)
    (known : List (Atom Judgment)) (ps : Option (List Candidate)) (budget : Nat) : Json :=
  Json.mkObj [("law_id", toJson lawId), ("row_kind", toJson "request"),
    ("request", requestJson f ds rs known ps budget), ("response", response f ds rs known ps budget)]

def knownFor (f : Frame) (c : Candidate) (mask : Nat) (wrongScope : Bool) : List (Atom Judgment) :=
  (requirements f c).zipIdx.flatMap fun (req, index) =>
    let atom := if wrongScope then { req.atom with scope := "other" } else req.atom
    let state := mask / 4 ^ index % 4
    (if state == 1 || state == 3 then [atom] else []) ++
      (if state == 2 || state == 3 then [atom.opposite] else [])

def exportFixtures : IO Unit := do
  let f := fixtureFrame
  let original := fixtureDesignation
  let transferred := { original with id := "transferred", origin := .transferred }
  for d in [original, transferred] do
    let c := Candidate.literal d
    for mask in List.range 16 do
      for wrongScope in [false, true] do
        IO.println (fixtureRow f [d] [] (knownFor f c mask wrongScope) (some [c]) 1).compress
  let r := fixtureRelation
  let c := Candidate.figurative r
  for mask in List.range 256 do
    for wrongScope in [false, true] do
      IO.println (fixtureRow f [original] [r] (knownFor f c mask wrongScope)
        (some [Candidate.literal original, c]) 2).compress
  let rival := { original with id := "second", sense := "other-sense" }
  for ds in [[], [original], [original, rival], [transferred],
      [{ original with convention := "custom" }]] do
    for rs in [[], [r], [{ r with kind := "" }], [{ r with targetSense := original.sense }]] do
      let cs := enumerate f ds rs
      for ps in [none, some cs, some [], some (cs.drop 1), some (cs.reverse)] do
        for budget in [0, ds.length + rs.length] do
          IO.println (fixtureRow f ds rs [] ps budget).compress
  -- Every occurrence coordinate is evidence identity, even with the same scope.
  let base := Candidate.literal original
  let supported := (requirements f base).map (·.atom)
  for changed in [
      { f with occurrence := { f.occurrence with source := "changed" } },
      { f with occurrence := { f.occurrence with revision := "changed" } },
      { f with occurrence := { f.occurrence with raw := "changed" } },
      { f with occurrence := { f.occurrence with startByte := 1 } },
      { f with occurrence := { f.occurrence with endByte := 5 } },
      { f with occurrence := { f.occurrence with referent := "changed" } },
      { f with occurrence := { f.occurrence with time := "changed" } },
      { f with occurrence := { f.occurrence with context := "changed" } },
      { f with expression := "changed" }, { f with convention := "custom" }] do
    IO.println (fixtureRow changed [original] [] supported none 1).compress

end LinguisticTruthMain

def main (args : List String) : IO Unit := do
  let output ← IO.getStdout
  if args == ["--export"] then LinguisticTruthMain.exportFixtures
  else if args.isEmpty then
    ProbeJson.readLoop LinguisticTruthMain.dispatch LinguisticTruthMain.errorJson
      (← IO.getStdin) output (ByteArray.emptyWithCapacity 0) false
  else throw (IO.userError "usage: linguisticTruth [--export]")
