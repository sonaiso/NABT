import Nabt.Words
import Lean

/-! Executable interoperability table for the conditional word algebra.
All 60 class/case outcomes and all 165 class/ending inverse images are emitted.
The export is not a source-attestation or parser-correctness certificate. -/

open Lean Nabt.Words

def wordsJson : Json := Json.mkObj [
  ("schema_version", toJson (1 : Nat)),
  ("law_id", toJson lawId),
  ("class_case_number_domain", toJson classCaseNumberDomain),
  ("case_codes", Json.mkObj [
    ("nasb", toJson Nabt.Governors.Case.nasb.code),
    ("raf", toJson Nabt.Governors.Case.raf.code),
    ("jarr", toJson Nabt.Governors.Case.jarr.code),
    ("jazm", toJson Nabt.Governors.Case.jazm.code)]),
  ("kinds", toJson (kinds.map fun kind => Json.mkObj [
    ("code", toJson kind.code), ("label", toJson kind.label),
    ("capacities", toJson [kind.capacities.1, kind.capacities.2])])),
  ("classes", toJson (declensionClasses.map fun cls => Json.mkObj [
    ("code", toJson cls.code), ("label", toJson cls.label), ("kind", toJson cls.kind.code)])),
  ("endings", toJson (endings.map fun observed => Json.mkObj [
    ("code", toJson observed.code), ("label", toJson observed.label)])),
  ("rows", toJson (declensionClasses.flatMap fun cls => allCases.map fun case => Json.mkObj [
    ("class", toJson cls.code), ("case", toJson case.code),
    ("number", toJson (classCaseNumber cls case)),
    ("ending", toJson ((ending cls case).map Ending.code))])),
  ("inverse", toJson (declensionClasses.flatMap fun cls => endings.map fun observed => Json.mkObj [
    ("class", toJson cls.code), ("ending", toJson observed.code),
    ("cases", toJson ((caseCandidates cls observed).map Nabt.Governors.Case.code))]))
]

def main : IO Unit := IO.println wordsJson.compress
