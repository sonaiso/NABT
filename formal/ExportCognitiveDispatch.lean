import Nabt.RuleRouting
import Nabt.AwamilInventory
import Lean
open Lean Nabt.RuleRouting.Dispatch

def main : IO Unit := do
  let views := viewLayers.map fun (id, layer, networks) => Json.mkObj [
    ("id", toJson id), ("layer", toJson layer), ("networks", toJson networks)]
  IO.println (Json.mkObj [
    ("law_id", toJson lawId), ("layers", toJson layers),
    ("profiles", toJson profiles), ("flags", toJson flags), ("views", toJson views),
    ("stage_gate", toJson ((List.range 6).map fun c => (List.range 6).map (stageAllowed c))),
    ("condition_gate", toJson ((List.range 4).map fun p => (List.range 256).map (guard p))),
    ("awamil_count", toJson Nabt.AwamilInventory.entries.length),
    ("awamil_partition", toJson ([
      (Nabt.AwamilInventory.entries.filter (·.group ≤ 13)).length,
      (Nabt.AwamilInventory.entries.filter (·.group == 14)).length,
      (Nabt.AwamilInventory.entries.filter (·.group == 15)).length]))]).compress
