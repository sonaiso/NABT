import Nabt.PhonologicalModes
import Lean

open Lean Nabt.PhonologicalModes

def vowelLabel : Vowel → String
  | .a => "a" | .i => "i" | .u => "u"

def segmentLabel : Segment → String
  | .consonant s => s
  | .short v => vowelLabel v
  | .long v => vowelLabel v ++ ":"

def endingLabel : Ending → String
  | .stable => "stable" | .short _ => "short" | .tanwin _ => "tanwin"
  | .feminine _ => "feminine" | .weak _ => "weak" | .single _ => "single"

def endingVowel : Ending → Option String
  | .stable => none
  | .short v | .tanwin v | .feminine v | .weak v | .single v => some (vowelLabel v)

def endings : List Ending := [.stable] ++ [Vowel.a, .i, .u].flatMap
  (fun v => [.short v, .tanwin v, .feminine v, .weak v, .single v])

def main : IO Unit := do
  let onsets := [Start.ibtida, .wasl].flatMap fun s =>
    ([none, some Vowel.a, some Vowel.i, some Vowel.u] : List (Option Vowel)).map fun v =>
      Json.mkObj [("start", toJson (if s == .ibtida then "ibtida" else "wasl")),
        ("vowel", toJson (v.map vowelLabel)),
        ("segments", toJson ((onset s v).map segmentLabel))]
  let rows := [End.wasl, .waqf].flatMap fun e =>
    [Profile.standardCore, .sibawayhiOptions].flatMap fun p => endings.map fun k =>
      Json.mkObj [("end", toJson (if e == .wasl then "wasl" else "waqf")),
        ("profile", toJson (if p == .standardCore then "standard_core" else "sibawayhi_attested_options")),
        ("ending", toJson (endingLabel k)), ("vowel", toJson (endingVowel k)),
        ("suffixes", toJson ((suffixes e p k).map (List.map segmentLabel)))]
  IO.println (Json.mkObj [("law_id", toJson lawId), ("onsets", toJson onsets),
    ("endings", toJson rows)]).compress
