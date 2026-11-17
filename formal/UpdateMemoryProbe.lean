import Nabt.UpdateMemory
import Lean

open Nabt.UpdateMemory Lean

def bit (b : Bool) : Json := toJson (if b then (1 : Nat) else 0)
def memoryJson (m : Memory) : Json :=
  Json.arr #[bit m.1, bit m.2.1, bit m.2.2.1, bit m.2.2.2.1, bit m.2.2.2.2]
def answerJson (a : Answer) : Json :=
  Json.arr #[bit a.1, bit a.2.1, bit a.2.2.1, bit a.2.2.2]

def main : IO Unit :=
  IO.println (Json.mkObj [("law", toJson lawId), ("rows", toJson (memories.map fun m =>
    Json.mkObj [("memory", memoryJson m), ("answer", answerJson (observe m)),
      ("signature", Json.arr #[answerJson (observe m), answerJson (observe (addProperty m)),
        answerJson (observe (addLaw m))])]))]).compress
