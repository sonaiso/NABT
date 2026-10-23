import Nabt.Governors
import Lean

/-! Executable fields of the finite governor inventory. The checked-in JSON
also records source provenance; hashing and Git provenance are not theorems.
Compare this export structurally with `src/nabt/data/governors.json`.
-/

open Lean Nabt.Governors

def roleJson (r : Role) : Json := Json.mkObj [
  ("code", toJson r.code),
  ("name", toJson r.name),
  ("category", toJson (match r.category with | .noun => "noun" | .verb => "verb"))
]

def classJson (c : GovernorClass) : Json := Json.mkObj [
  ("code", toJson c.code),
  ("name", toJson c.name),
  ("alternatives", toJson (c.equations.map fun alt => alt.map fun e => [e.1.code, e.2.code])),
  ("links", toJson (c.links.map fun link => [link.1.code, link.2.code]))
]

def entryJson (row : Row) (index : Nat) : Json := Json.mkObj [
  ("row_id", toJson (index + 1)),
  ("label", toJson row.label),
  ("class_code", toJson row.governorClass.code),
  ("implicit", toJson row.implicit)
]

def allCases : List Case := [.nasb, .raf, .jarr, .jazm]

def roleMarkJson : List Json := roles.flatMap fun r => allCases.map fun c => Json.mkObj [
  ("role", toJson r.code), ("mark", toJson c.code),
  ("number", toJson (roleMarkNumber r c)), ("allowed", toJson (r.category.accepts c))]

def requiredRoles (c : GovernorClass) : List Role :=
  ((c.equations.flatten.map Prod.fst) ++
    (c.links.flatMap fun link => [link.1, link.2])).eraseDups

def assignmentsFor : List Role → List (List (Role × Option Case))
  | [] => [[]]
  | r :: rest => ([none, some .nasb, some .raf, some .jarr, some .jazm] : List (Option Case)).flatMap
      fun value => (assignmentsFor rest).map fun tail => (r, value) :: tail

def assignmentOf (pairs : List (Role × Option Case)) : Assignment := fun role =>
  ((pairs.find? fun p => p.1 == role).map Prod.snd).getD none

def alternativeCodes (alternatives : List Alternative) : List (List (List Nat)) :=
  alternatives.map fun alt => alt.map fun e => [e.1.code, e.2.code]

def assignmentProbes : List Json := classes.flatMap fun c =>
  (assignmentsFor (requiredRoles c)).map fun pairs => Json.mkObj [
    ("class_code", toJson c.code),
    ("assignments", toJson (pairs.map fun (r, value) => Json.mkObj [
      ("role", toJson r.code), ("mark", toJson (value.map Case.code))])),
    ("complete", toJson (alternativeCodes (completeAlternatives c (assignmentOf pairs)))),
    ("viable", toJson (alternativeCodes (viableAlternatives c (assignmentOf pairs))))]

def governorsJson : Json := Json.mkObj [
  ("schema_version", toJson (1 : Nat)),
  ("law_id", toJson lawId),
  ("role_mark_number_domain", toJson roleMarkNumberDomain),
  ("role_mark_codes", toJson roleMarkJson),
  ("mark_codes", Json.mkObj [
    ("nasb", toJson Case.nasb.code), ("raf", toJson Case.raf.code),
    ("jarr", toJson Case.jarr.code), ("jazm", toJson Case.jazm.code)]),
  ("roles", toJson (roles.map roleJson)),
  ("classes", toJson (classes.map classJson)),
  ("entries", toJson (table.zipIdx.map fun (row, index) => entryJson row index)),
  ("assignment_probes", toJson assignmentProbes)
]

def main : IO Unit := IO.println governorsJson.compress
