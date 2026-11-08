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


/-! Deterministic dispatch policy over owner-produced obligations. These facts
prove the control contract, not extraction of premises or linguistic truth. -/
namespace Nabt.RuleRouting.Dispatch

def lawId := "nabt.cognitive-dispatch.v1"
def layers : List String :=
  ["orthography", "morphology", "word_kind", "syntax", "mantuq", "concept"]
def profiles : List String := ["ordinary", "majaz", "analogy", "division"]
def flags : List String := ["condition", "retrieved_row", "source_local", "ceiling_preserved",
  "literal_excluded", "contextual_cue", "analogy_scoped_bundle", "division_typed_bundle"]

def stageAllowed (cursor target : Nat) : Bool := cursor == target && target < 6

def guard (profile mask : Nat) : Bool :=
  mask.testBit 0 && mask.testBit 1 && mask.testBit 2 && mask.testBit 3 &&
  (match profile with
   | 0 => true
   | 1 => mask.testBit 4 && mask.testBit 5
   | 2 => mask.testBit 6
   | 3 => mask.testBit 7
   | _ => false)

def allowed (cursor target profile mask : Nat) : Bool :=
  stageAllowed cursor target && guard profile mask

theorem allowed_requires_same_layer (c t p m : Nat) (h : allowed c t p m = true) : c = t := by
  simp only [allowed, stageAllowed, Bool.and_eq_true, beq_iff_eq] at h
  exact h.1.1

theorem allowed_requires_condition (c t p m : Nat) (h : allowed c t p m = true) :
    m.testBit 0 = true := by
  simp only [allowed, guard, Bool.and_eq_true] at h
  exact h.2.1.1.1.1

theorem majaz_requires_exclusion_and_cue (c t m : Nat) (h : allowed c t 1 m = true) :
    m.testBit 4 = true ∧ m.testBit 5 = true := by
  simp only [allowed, guard, Bool.and_eq_true] at h
  exact h.2.2

-- A dispatched step advances only with the gate owner's actual closure result.
def advance (cursor : Nat) (closed : Bool) : Nat := if closed then cursor + 1 else cursor

theorem stopped_does_not_advance (cursor : Nat) : advance cursor false = cursor := rfl

-- All 18 IDs refer to installed views; mappings are versioned navigation policy.
def viewLayers : List (String × Nat × List String) := [
  ("trace", 0, ["S"]), ("sound", 0, ["S"]), ("orthography", 0, ["S"]),
  ("cells", 0, ["S"]), ("graded", 1, ["S"]), ("lexicon", 5, ["C"]),
  ("morphology", 1, ["S"]), ("syntax", 3, ["S", "M"]),
  ("genera", 5, ["C", "G"]), ("quantity", 4, ["M"]),
  ("indications", 4, ["M"]), ("usage", 4, ["M"]),
  ("understanding", 4, ["M"]), ("restriction", 4, ["M"]),
  ("speech_act", 3, ["M"]), ("inference", 5, ["M", "G", "A"]),
  ("world", 5, ["C", "G", "A"]), ("revision", 5, ["S", "C", "M", "G", "A"])]

end Nabt.RuleRouting.Dispatch
