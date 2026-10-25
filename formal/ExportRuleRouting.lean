import Nabt.RuleRouting
import Lean

open Lean Nabt.RuleRouting

def installed : List String := ["qatr", "mughni", "sibawayhi"]
def alphabet : List String := installed ++ ["unknown"]

def rankedWords : Nat → List (List String)
  | 0 => [[]]
  | n + 1 => alphabet.flatMap fun token => (rankedWords n).map (token :: ·)

def main : IO Unit := do
  let rankings := (List.range 5).flatMap rankedWords
  let rows := rankings.map fun ranked => Json.mkObj [
    ("inventory", toJson installed), ("ranked", toJson ranked),
    ("schedule", toJson (schedule installed ranked)),
    ("budget_complete", toJson ((List.range 5).map (scanComplete installed ranked))),
    ("accepted", toJson ((List.range 8).map fun mask =>
      (schedule installed ranked).filter fun name => mask.testBit (installed.idxOf name)))]
  IO.println (Json.mkObj [("law_id", toJson lawId), ("rows", toJson rows)]).compress
