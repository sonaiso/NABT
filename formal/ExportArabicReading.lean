import Nabt.ArabicReading
import Nabt.Program
import Lean

/-! Small executable interoperability table. This exports definitions from
the checked modules; it does not prove the Python parser or its JSON codec. -/
open Lean Nabt.ArabicReading

def moods : List (String × Mood) :=
  [("ASSERT", .assertive), ("QUESTION", .question), ("COMMAND", .command),
   ("PROHIBITION", .prohibition), ("WISH", .wish), ("HOPE", .hope),
   ("VOCATIVE", .vocative), ("AMBIGUOUS", .ambiguous)]

def payloads : List (List Nabt.Atom) :=
  [[], [0], [115], [84, 8, 4], [85, 10, 4], [0, 115, 0]]

def main : IO Unit := do
  let table := Json.mkObj [
    ("schema_version", toJson (1 : Nat)),
    ("language_id", toJson Nabt.Program.TextProfile.arabicSyntax.languageId),
    ("moods", Json.arr ((moods.map fun (name, mood) => Json.mkObj [
      ("name", toJson name), ("code", toJson mood.code)]).toArray)),
    ("entry_profiles", Json.arr (([
      ("START_TEXT", Nabt.Program.TextProfile.controlledArabic),
      ("START_ARABIC", Nabt.Program.TextProfile.arabicSyntax)]).map (fun (name, profile) =>
        Json.mkObj [("name", toJson name),
          ("opcode", toJson (Nabt.Program.opcode profile.startOp)),
          ("language_id", toJson profile.languageId)])).toArray),
    ("envelope_domain", toJson "nabt.arabic-reading-envelope.b116.v1"),
    ("envelopes", Json.arr ((moods.flatMap fun (name, mood) => payloads.map fun payload =>
      Json.mkObj [("mood", toJson name), ("payload", toJson (payload.map Fin.val)),
        ("number", toJson (envelopeNumber ⟨mood, payload⟩))]).toArray))]
  IO.println table.compress
