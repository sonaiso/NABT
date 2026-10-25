import Nabt.BookCoverage

/-!
# Retrieval-independent routing over an installed inventory

Ranks are proposals only. Unknown IDs are removed, every installed ID is then
appended, and duplicate IDs are removed. These theorems concern this finite
inventory, not all Arabic rules or correctness of caller-supplied premises.
Source completeness still requires `BookCoverage.InventoryExhaustive` and
translation fidelity; the existing `BookCoverage.complete_readings_transfer`
is the sole transfer theorem, rather than a second copy here.
-/
namespace Nabt.RuleRouting

def lawId := "nabt.rule-routing.v1"

variable {Rule : Type} [DecidableEq Rule]

/-- Keep the ranker's order when possible, with complete installed fallback. -/
def schedule (inventory ranked : List Rule) : List Rule :=
  ((ranked.filter fun rule => decide (rule ∈ inventory)) ++ inventory).eraseDups

theorem schedule_exact (inventory ranked : List Rule) (rule : Rule) :
    rule ∈ schedule inventory ranked ↔ rule ∈ inventory := by
  simp only [schedule, List.mem_eraseDups, List.mem_append, List.mem_filter,
    decide_eq_true_eq]
  exact ⟨fun h => h.elim And.right id, fun h => Or.inr h⟩

/-- The ranker cannot add or remove accepted IDs once the fallback is scanned. -/
theorem checked_schedule_exact (inventory ranked : List Rule)
    (check : Rule → Bool) (rule : Rule) :
    rule ∈ (schedule inventory ranked).filter check ↔
      rule ∈ inventory.filter check := by
  simp only [List.mem_filter, schedule_exact]

/-- Completion is certified only after the whole deduplicated schedule fits. -/
def scanComplete (inventory ranked : List Rule) (budget : Nat) : Bool :=
  decide ((schedule inventory ranked).length ≤ budget)

theorem exhausted_budget_not_complete (inventory ranked : List Rule)
    (budget : Nat) (exhausted : budget < (schedule inventory ranked).length) :
    scanComplete inventory ranked budget = false := by
  simp [scanComplete, Nat.not_le_of_gt exhausted]

end Nabt.RuleRouting
