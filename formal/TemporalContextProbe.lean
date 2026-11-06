import Nabt.TemporalContext
import ProbeJson

open Lean ProbeJson Nabt.TemporalContext
namespace TemporalContextProbe

-- Same canonical signed-string convention as the evidence/time owners.
-- ProbeJson continues to reject signed numeric tokens for other consumers.
def signed (v : Json) : ProbeM Int := do
  let raw ← str v
  if raw.length > 256 then return ← limited "signed temporal integer exceeds 256 characters"
  let some n := raw.toInt? | return ← invalid "canonical signed decimal string required"
  if toString n != raw then return ← invalid "noncanonical signed decimal string"
  return n

def interval (v : Json) : ProbeM Interval := do
  let a ← signed (← field v "first")
  let b ← signed (← field v "last")
  return ⟨a,b⟩

def optionalInterval (v : Json) : ProbeM (Option Interval) := do
  if v == Json.null then return none
  return some (← interval v)

def relation (v : String) : ProbeM Relation := match v with
  | "before" => pure .before | "after" => pure .after | "equals" => pure .equals
  | "intersects" => pure .intersects | "contains" => pure .contains | "within" => pure .within
  | _ => invalid "unknown temporal relation"

def label : Verdict → String
  | .confirmed => "CONFIRMED" | .conflict => "CONFLICT" | .unknown => "UNKNOWN"

def dispatch (v : Json) : ProbeM Json := do
  let op ← str (← field v "op")
  let fields ← match op with
    | "check" => do
      let r ← relation (← str (← field v "relation"))
      let a ← optionalInterval (← field v "left")
      let b ← optionalInterval (← field v "right")
      pure [("verdict",toJson (label (check r a b)))]
    | "shift" => do
      let a ← interval (← field v "interval")
      let days ← signed (← field v "days")
      let result := shift a days
      pure [("interval",Json.mkObj [("first",toJson result.first),("last",toJson result.last)]),
            ("valid",toJson (decide result.valid))]
    | _ => invalid "unknown temporal operation"
  return Json.mkObj ([("law_id",toJson lawId),("status",toJson "OK"),
    ("request",v),("scope",toJson "SUPPLIED_INTEGER_DAY_INTERVALS"),
    ("world_truth_established",toJson false)] ++ fields)

def errorResponse (f : Failure) : Json := Json.mkObj [
  ("law_id",toJson lawId),("status",toJson "ERROR"),("code",toJson f.code),("message",toJson f.message)]
end TemporalContextProbe

def main : IO Unit := do
  ProbeJson.readLoop TemporalContextProbe.dispatch TemporalContextProbe.errorResponse
    (← IO.getStdin) (← IO.getStdout)
