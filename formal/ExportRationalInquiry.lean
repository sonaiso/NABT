import Nabt.RationalInquiry
import Lean

/-!
Exhaustive finite conformance view of the rational-inquiry decision gate.
All nine Boolean checks and rank pairs in 0..3 are exported. This is not an
external-truth oracle or a proof of the adapter deriving the input checks.
-/

open Lean Nabt.RationalInquiry

private def flag (mask bit : Nat) : Bool := (mask / 2 ^ bit) % 2 == 1

private def checksFromMask (mask requestedRank evidenceRank : Nat) : Checks :=
  { formed := flag mask 0
    reviewed := flag mask 1
    provenance := flag mask 2
    scopeCovered := flag mask 3
    supported := flag mask 4
    counterevidence := flag mask 5
    requiresWorldBridge := flag mask 6
    worldBridge := flag mask 7
    exhausted := flag mask 8
    requestedRank := requestedRank
    evidenceRank := evidenceRank }

def main : IO Unit := do
  for mask in List.range 512 do
    for requestedRank in List.range 4 do
      for evidenceRank in List.range 4 do
        let result := assess (checksFromMask mask requestedRank evidenceRank)
        let row := Json.mkObj [
          ("law_id", toJson lawId),
          ("mask", toJson mask),
          ("requested_rank", toJson requestedRank),
          ("evidence_rank", toJson evidenceRank),
          ("verdict", toJson result.verdict.label),
          ("authorized_rank", toJson result.authorizedRank)]
        IO.println row.compress
