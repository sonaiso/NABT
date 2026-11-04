import Nabt.GroundedPassage
import ProbeJson

open Lean ProbeJson Nabt.SemanticInference
namespace Nabt.GroundedPassage

deriving instance FromJson, ToJson for Sample
deriving instance FromJson, ToJson for Measurement
deriving instance FromJson, ToJson for MapRecord
deriving instance FromJson, ToJson for Permission
deriving instance FromJson, ToJson for Input

def Claim.describe : Claim → String × Json
  | .input id => ("input", toJson id)
  | .position t x => ("position", Json.mkObj [("minute", toJson t), ("x_cm", toJson x)])
  | .side t s => ("direction", Json.mkObj [("minute", toJson t), ("side", toJson s)])
  | .distance t d => ("distance", Json.mkObj [("minute", toJson t), ("cm", toJson d)])
  | .crossing t => ("crossing", toJson t)
  | .deadline t e => ("permission_endpoint", Json.mkObj [("minute", toJson t), ("boundary", toJson e)])
  | .within t lim => ("crossing_before_deadline", Json.mkObj [("minute", toJson t), ("limit", toJson lim)])

def validScale (k : Nat) : Bool := k == 1 || k == 100
def validMeasure (m : Measurement) : Bool :=
  validScale m.cmPerUnit && m.samples.length ≤ 48 &&
  m.samples.all (fun s => s.minute < 1440 && s.x.natAbs ≤ 10000000) &&
  decide ((m.samples.map Sample.minute).Pairwise (· < ·))

def dispatch (envelope : Json) : ProbeM Json := do
  -- A canonical inner wire preserves duplicate-key and numeric-token rejection.
  let raw ← str envelope
  -- ProbeJson bounds unsigned tokens. Omit minus signs for this lexical
  -- depth/digit budget only; parse and require canonicality on the original.
  preflight (raw.replace "-" " ")
  let j ← liftParse (Json.parse raw)
  if j.compress != raw then return ← invalid "noncanonical passage wire"
  let i : Input ← liftParse (fromJson? j)
  if toJson i != j then return ← invalid "unexpected fields or noncanonical projection"
  let ids := i.maps.map MapRecord.id ++ i.fixes.map Measurement.id ++
             i.tracks.map Measurement.id ++ i.permits.map Permission.id
  if i.maps.length > 1 || i.fixes.length > 1 || i.permits.length > 1 || i.tracks.length > 4 then
    return ← limited "passage source bound"
  if i.scope.isEmpty || ids.any (fun id => id.isEmpty || id == lawId) ||
      ids.eraseDups != ids || i.active.eraseDups != i.active ||
      !i.active.all ids.contains || !["forward","backward"].contains i.facing ||
      !i.maps.all (fun m => validScale m.cmPerUnit && m.gateX.natAbs ≤ 10000000) ||
      !i.fixes.all (fun m => validMeasure m && m.samples.length == 1) ||
      !i.tracks.all validMeasure ||
      !i.permits.all (fun p => p.minute < 1440 && ["exclusive","unspecified"].contains p.endpoint) then
    return ← invalid "invalid passage premises"
  let paths := candidates i
  let rules := (paths.flatMap Path.steps).filterMap fun
    | .rule r => some r | _ => none
  let program : Program Claim := {
    sources := law i.scope :: i.active.map (record i.scope)
    facts := i.active.map fun id => ⟨record i.scope id, ⟨.input id, true, i.scope⟩⟩
    rules := rules.eraseDups }
  let accepted := minimalChecked program paths
  let rows := accepted.map fun p =>
    let (kind,value) := p.goal.value.describe
    let trace := p.steps.map fun (step : Step Claim) => match step with
      | Step.fact f => Json.mkObj [("fact",toJson f.source.identity)]
      | .rule r => Json.mkObj [("rule",toJson r.name),("claim",toJson r.head.value.describe)]
    Json.mkObj [("kind",toJson kind),("value",value),("support",toJson p.support),("steps",toJson trace)]
  return Json.mkObj [("law",toJson lawId),("status",toJson "CHECKED"),("paths",toJson rows)]

end Nabt.GroundedPassage

def main : IO Unit := do
  let errorJson := fun (e : Failure) => Json.mkObj [("status",toJson e.code),("reason",toJson e.message)]
  ProbeJson.readLoop Nabt.GroundedPassage.dispatch errorJson (← IO.getStdin) (← IO.getStdout)
