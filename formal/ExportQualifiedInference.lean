import Nabt.QualifiedInference
import Lean

open Lean Nabt.SemanticInference Nabt.QualifiedInference

private def roleLabel : Role → String
  | .premise => "premise"
  | .cause => "cause"
  | .condition => "condition"
  | .blockerAbsence => "blocker_absence"
  | .necessaryBridge => "necessary_bridge"
  | .originRuling => "origin_ruling"
  | .sharedCause => "shared_cause"
  | .transferBridge => "transfer_bridge"

private def kindLabel : Kind → String
  | .direct => "direct"
  | .causal => "causal"
  | .opposition => "opposition"
  | .analogy => "analogy"

private def atomJson (atom : Atom Nat) : Json := Json.mkObj [
  ("value", toJson atom.value), ("positive", toJson atom.positive), ("scope", toJson atom.scope)]

private def requirementJson (requirement : Requirement Nat) : Json := Json.mkObj [
  ("role", toJson (roleLabel requirement.role)), ("atom", atomJson requirement.atom)]

private def profiles : List (String × Kind × List Role × Bool) := [
  ("direct", .direct, [.premise], false),
  ("transfer", .direct, [.premise, .transferBridge], false),
  ("causal", .causal, [.cause, .condition, .blockerAbsence], false),
  ("opposition", .opposition, [.premise, .necessaryBridge, .condition, .blockerAbsence], false),
  ("analogy", .analogy, [.originRuling, .sharedCause, .transferBridge, .condition, .blockerAbsence], false),
  ("empty", .direct, [], false),
  ("causal_missing_cause", .causal, [.condition], false),
  ("opposition_missing_bridge", .opposition, [.premise], false),
  ("analogy_missing_transfer", .analogy, [.originRuling, .sharedCause], false),
  ("blocker_wrong_sign", .causal, [.cause, .condition, .blockerAbsence], true)]

private def requirements (roles : List Role) (badBlocker : Bool) : List (Requirement Nat) :=
  roles.zipIdx |>.map fun (role, index) =>
    ⟨role, ⟨index, if role == .blockerAbsence then badBlocker else true, "fixture"⟩⟩

private def knownFor (requirements : List (Requirement Nat)) (mask : Nat)
    (wrongScope : Bool) : List (Atom Nat) :=
  requirements.zipIdx.flatMap fun (requirement, index) =>
    let atom := if wrongScope then { requirement.atom with scope := "other" } else requirement.atom
    let state := mask / 4 ^ index % 4
    (if state == 1 || state == 3 then [atom] else []) ++
      (if state == 2 || state == 3 then [atom.opposite] else [])

private def variant (atom : Atom Nat) (index : Nat) : Atom Nat :=
  match index with
  | 0 => atom
  | 1 => atom.opposite
  | 2 => { atom with value := atom.value + 10 }
  | _ => { atom with scope := "other" }

def main : IO Unit := do
  for (name, kind, roles, badBlocker) in profiles do
    let obligations := requirements roles badBlocker
    for mask in List.range (4 ^ obligations.length) do
      for wrongScope in [false, true] do
        let known := knownFor obligations mask wrongScope
        IO.println (Json.mkObj [
          ("law_id", toJson lawId), ("row_kind", toJson "guard"),
          ("profile", toJson name), ("kind", toJson (kindLabel kind)),
          ("mask", toJson mask), ("wrong_scope", toJson wrongScope),
          ("requirements", toJson (obligations.map requirementJson)),
          ("known", toJson (known.map atomJson)),
          ("profile_valid", toJson (profileValid kind obligations)),
          ("verdict", toJson ((assess kind obligations known).label))]).compress
  for antecedentPositive in [false, true] do
    for consequentPositive in [false, true] do
      for sameScope in [false, true] do
        for absentVariant in List.range 4 do
          for conclusionVariant in List.range 4 do
            let antecedent : Atom Nat := ⟨0, antecedentPositive, "fixture"⟩
            let consequent : Atom Nat := ⟨1, consequentPositive, if sameScope then "fixture" else "different"⟩
            let absent := variant consequent.opposite absentVariant
            let conclusion := variant antecedent.opposite conclusionVariant
            IO.println (Json.mkObj [
              ("law_id", toJson lawId), ("row_kind", toJson "opposition_shape"),
              ("antecedent", atomJson antecedent), ("consequent", atomJson consequent),
              ("absent", atomJson absent), ("conclusion", atomJson conclusion),
              ("accepted", toJson (oppositionShape antecedent consequent absent conclusion))]).compress
