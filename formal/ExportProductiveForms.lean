import Nabt.ProductiveForms
import Lean

open Lean Nabt.ProductiveForms

def spelling : Mark → String
  | .a => "َ" | .i => "ِ" | .u => "ُ" | .sukun => "ْ"

def main : IO Unit := do
  let rows := [Vowel.a, .i, .u] |>.map fun v =>
    Json.mkObj [("medial", toJson (spelling (medial v))),
                ("initial", toJson (spelling (initial v))),
                ("final", toJson (spelling Mark.sukun))]
  IO.println (Json.mkObj [("law_id", toJson lawId), ("imperative", toJson rows)]).compress
