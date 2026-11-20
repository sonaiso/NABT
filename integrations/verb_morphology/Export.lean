import A116.Tasrif
import A116.Rubai
import A116.Sawabiq
import Nabt.NominalPatterns
import Lean.Data.Json

open Lean A116 A116.Wazn A116.Tasrif
namespace VerbExport

def mark : Haraka → Char
  | .fatha => 'َ' | .kasra => 'ِ' | .damma => 'ُ' | .sukun => 'ْ'

def clsChar : Cls → Char
  | .waw => 'و' | .ya => 'ي' | .hamz => 'ء' | .lam => 'ل' | .sahih => '*'

def tokens {n : Nat} (t : List (CSym n)) : String := String.ofList (t.flatMap fun
  | .lit c => [Field112.carrierChar c.carrier, mark c.haraka]
  | .slot i h => [Char.ofNat (49 + i.val), mark h])

def record (domain key body : String) := Json.arr #[toJson domain, toJson key, toJson body]

def rows (s : Sifa) : List Json := Id.run do
  let d := String.ofList [clsChar s.c0, clsChar s.c1, clsChar s.c2, if s.e12 then '=' else '!']
  let mut result := []
  for v in harakat3 do
    result := record d ("past.I." ++ String.singleton (mark v)) (tokens (madi s v .fatha)) :: result
    for b in babs do
      if b == .afala && v != .kasra then continue
      let family := if b == .mujarrad then "I" else "IV"
      result := record d ("imperative." ++ family ++ "." ++ String.singleton (mark v))
        (tokens (amr s b v)) :: result
      for p in prefixes do
        for m in moods do
          result := record d (String.intercalate "." ["imperfect", family, String.singleton (mark v),
            String.singleton p, String.singleton (mark m)]) (tokens (mudari s b p v m)) :: result
  return result

-- The owner's wasl vowel depends on whether the first radical is lam.
def quad (b : Rubai.Bina) : List Json :=
  if b.w.wasl then ['ل', 'ك'].map fun c =>
    record (if c == 'ل' then "ل***" else "!***") b.name
      (tokens (.lit (Ladder.atom 'ء' (waslH b.w (fun _ => Ladder.carrierOf c))) ::
        b.w.body ++ [.slot b.w.last b.h]))
  else [record "****" b.name (tokens (b.w.body ++ [.slot b.w.last b.h]))]

def charTemplate (t : Ishtiqaq.Template Char) := String.ofList (t.map fun
  | .lit c => c | .slot i => Char.ofNat (49 + i.val))

end VerbExport
open VerbExport in
def main : IO Unit := do
  IO.println ((Json.mkObj [
    ("sources", toJson (Ishtiqaq.soundTemplates.map charTemplate)),
    ("prefix_slots", toJson ([Sawabiq.slot1, Sawabiq.slot2, Sawabiq.slot3].map (·.map String.ofList))),
    ("paradigms", Json.arr ((allSifa.flatMap rows ++ Rubai.abniya.flatMap quad).toArray))
  ]).compress)
