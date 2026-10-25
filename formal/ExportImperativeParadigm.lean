import Nabt.ImperativeParadigm
import Lean

open Lean Nabt.ImperativeParadigm

def spelling : Nabt.ProductiveForms.Mark → String
  | .a => "َ" | .i => "ِ" | .u => "ُ" | .sukun => "ْ"

def suffixText (p : Subject) : String :=
  String.join ((suffix p).map fun c => String.singleton c.1 ++ c.2.elim "" spelling)

def main : IO Unit := do
  let rows := subjects.map fun p => Json.mkObj [
    ("profile", toJson (code p)), ("gender", toJson (gender p)),
    ("number", toJson (number p)), ("final", toJson (spelling (finalMark p))),
    ("suffix", toJson (suffixText p)),
    ("kind", toJson (if p = .fp then "feminine_subject" else "subject_pronoun"))]
  IO.println (Json.mkObj [("law_id", toJson lawId), ("rows", toJson rows),
    ("nun_final_2FP_deferred", toJson (decide (qualified ⟨'س', 'ك', 'ن', .u⟩ .fp = none)))]).compress
