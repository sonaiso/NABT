import Nabt.Law
import Lean

/-! Export the executable table from the definitions checked in this project.
The JSON hash is recorded by packaging; hashing is not a Lean theorem. -/
open Lean Nabt

def atom (a : Fin 116) : Atom := a

def tableJson : Json := Json.mkObj [
  ("schema_version", toJson (1 : Nat)),
  ("alphabet_id", toJson Law.alphabetId),
  ("law_id", toJson Law.lawId),
  ("state_count", toJson (97 : Nat)),
  ("alphabet_size", toJson (116 : Nat)),
  ("start_state", toJson (0 : Nat)),
  ("dead_state", toJson (96 : Nat)),
  ("carriers", toJson canonicalCarriers),
  ("states", toJson (["fatha", "damma", "kasra", "sukun"] : List String)),
  ("pot", toJson ((List.range 97).map Law.pot)),
  ("final_wasl", toJson ((List.range 97).map Law.finalWasl)),
  ("final_waqf", toJson ((List.range 97).map Law.finalWaqf)),
  ("transitions", toJson ((List.range 97).map fun q =>
    (List.finRange 116).map fun a => [Law.step q a, Law.cost q a]))
]

def main : IO Unit := IO.println tableJson.compress
