import Nabt.PropertyEvidence

open Nabt.PropertyEvidence

def verdictName : Verdict → String
  | .conflict => "conflict"
  | .rejected => "rejected"
  | .pending => "pending"
  | .licensed => "licensed"

/-- All 4-bit R/P/N states; outputs follow the predicate specification. -/
def main : IO Unit := do
  IO.println "required\tpositive\tnegative\tstatus\tmissing\tconflicts\trefutations"
  for r in List.range 16 do
    for p in List.range 16 do
      for n in List.range 16 do
        let required := bits 4 r
        let ledger := ledgerOfMasks 4 p n
        let status := verdictName (judge required ledger)
        IO.println s!"{r}\t{p}\t{n}\t{status}\t{missingMask required ledger}\t{conflictMask required ledger}\t{negativeMask required ledger}"
