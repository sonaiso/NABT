import Std

/-!
Completeness-transfer contracts for an independently specified source domain.
No Arabic source predicate or translation-fidelity premise is manufactured by
this module. The finite inventory is a parameter, not a definition of all rules
in a book. Byte partition success and selected-law success cannot supply the
`InventoryExhaustive` premise. Hash equality is a byte-identity check only after
the expected source identity has been fixed independently.
-/
namespace Nabt.BookCoverage

def lawId := "nabt.book-rule-coverage.v1"

variable {Rule Analysis : Type}

def InventoryExhaustive (inSource : Rule → Prop) (inventory : List Rule) : Prop :=
  ∀ rule, inSource rule → rule ∈ inventory

def InventoryFaithful (inSource : Rule → Prop) (inventory : List Rule) : Prop :=
  ∀ rule, rule ∈ inventory → inSource rule

def Covered (implemented : Rule → Prop) (inventory : List Rule) : Prop :=
  ∀ rule, rule ∈ inventory → implemented rule

def WholeSourceCovered (inSource implemented : Rule → Prop) : Prop :=
  ∀ rule, inSource rule → implemented rule

theorem whole_source_of_exhaustive_inventory
    (inSource implemented : Rule → Prop) (inventory : List Rule)
    (exhaustive : InventoryExhaustive inSource inventory)
    (covered : Covered implemented inventory) : WholeSourceCovered inSource implemented := by
  intro rule member
  exact covered rule (exhaustive rule member)

theorem whole_source_iff_inventory_coverage
    (inSource implemented : Rule → Prop) (inventory : List Rule)
    (exhaustive : InventoryExhaustive inSource inventory)
    (faithful : InventoryFaithful inSource inventory) :
    WholeSourceCovered inSource implemented ↔ Covered implemented inventory := by
  constructor
  · intro whole rule member
    exact whole rule (faithful rule member)
  · exact whole_source_of_exhaustive_inventory inSource implemented inventory exhaustive

theorem omitted_source_rule_refutes_exhaustiveness
    (inSource : Rule → Prop) (inventory : List Rule) (rule : Rule)
    (present : inSource rule) (missing : rule ∉ inventory) :
    ¬ InventoryExhaustive inSource inventory := by
  intro complete
  exact missing (complete rule present)

theorem unimplemented_source_rule_refutes_whole_source
    (inSource implemented : Rule → Prop) (rule : Rule)
    (present : inSource rule) (missing : ¬ implemented rule) :
    ¬ WholeSourceCovered inSource implemented := by
  intro complete
  exact missing (complete rule present)

def allChecked (check : Rule → Bool) (inventory : List Rule) : Bool := inventory.all check

theorem all_checked_exact (check : Rule → Bool) (inventory : List Rule) :
    allChecked check inventory = true ↔ Covered (fun rule => check rule = true) inventory := by
  simp [allChecked, Covered]

theorem checked_whole_source
    (inSource implemented : Rule → Prop) (check : Rule → Bool) (inventory : List Rule)
    (exhaustive : InventoryExhaustive inSource inventory)
    (checkSound : ∀ rule, check rule = true → implemented rule)
    (passed : allChecked check inventory = true) :
    WholeSourceCovered inSource implemented := by
  apply whole_source_of_exhaustive_inventory inSource implemented inventory exhaustive
  intro rule member
  exact checkSound rule ((all_checked_exact check inventory).mp passed rule member)

-- Runtime coverage must preserve BOTH directions of the source relation.
def Refines (source formal : Rule → Analysis → Prop) (inventory : List Rule) : Prop :=
  ∀ rule, rule ∈ inventory → ∀ analysis, source rule analysis ↔ formal rule analysis

def Enumerates (formal : Rule → Analysis → Prop) (run : Rule → List Analysis)
    (inventory : List Rule) : Prop :=
  ∀ rule, rule ∈ inventory → ∀ analysis, analysis ∈ run rule ↔ formal rule analysis

theorem complete_readings_transfer
    (inSource : Rule → Prop) (source formal : Rule → Analysis → Prop)
    (run : Rule → List Analysis) (inventory : List Rule)
    (exhaustive : InventoryExhaustive inSource inventory)
    (fidelity : Refines source formal inventory)
    (exactRun : Enumerates formal run inventory)
    (rule : Rule) (member : inSource rule) (analysis : Analysis) :
    analysis ∈ run rule ↔ source rule analysis := by
  have listed := exhaustive rule member
  exact (exactRun rule listed analysis).trans (fidelity rule listed analysis).symm

theorem source_reading_cannot_be_omitted
    (inSource : Rule → Prop) (source formal : Rule → Analysis → Prop)
    (run : Rule → List Analysis) (inventory : List Rule)
    (exhaustive : InventoryExhaustive inSource inventory)
    (fidelity : Refines source formal inventory)
    (exactRun : Enumerates formal run inventory)
    (rule : Rule) (member : inSource rule) (analysis : Analysis)
    (licensed : source rule analysis) : analysis ∈ run rule := by
  exact (complete_readings_transfer inSource source formal run inventory
    exhaustive fidelity exactRun rule member analysis).mpr licensed

theorem false_reading_cannot_be_added
    (inSource : Rule → Prop) (source formal : Rule → Analysis → Prop)
    (run : Rule → List Analysis) (inventory : List Rule)
    (exhaustive : InventoryExhaustive inSource inventory)
    (fidelity : Refines source formal inventory)
    (exactRun : Enumerates formal run inventory)
    (rule : Rule) (member : inSource rule) (analysis : Analysis)
    (unlicensed : ¬ source rule analysis) : analysis ∉ run rule := by
  intro included
  exact unlicensed ((complete_readings_transfer inSource source formal run inventory
    exhaustive fidelity exactRun rule member analysis).mp included)

-- Concrete countermodel: proving all listed rules covers only the selected set.
theorem selected_subset_is_covered :
    Covered (fun rule : Bool => rule = false) [false] := by
  intro rule member
  simpa using member

theorem selected_subset_is_not_exhaustive :
    ¬ InventoryExhaustive (fun _ : Bool => True) [false] := by
  apply omitted_source_rule_refutes_exhaustiveness _ _ true trivial
  simp

theorem selected_subset_is_not_whole_source :
    ¬ WholeSourceCovered (fun _ : Bool => True) (fun rule => rule = false) := by
  intro complete
  have impossible := complete true trivial
  cases impossible

-- A book-domain certificate needs a separate inclusion premise for Arabic.
theorem transfer_to_larger_claim_requires_inclusion
    (inBook inArabic implemented : Rule → Prop)
    (wholeBook : WholeSourceCovered inBook implemented)
    (scopeInclusion : ∀ rule, inArabic rule → inBook rule) :
    WholeSourceCovered inArabic implemented := by
  intro rule member
  exact wholeBook rule (scopeInclusion rule member)

-- List uniqueness is an evidence-accounting condition, not source completeness.
def uniqueIds [DecidableEq Rule] (inventory : List Rule) : Bool := decide inventory.Nodup

theorem unique_ids_exact [DecidableEq Rule] (inventory : List Rule) :
    uniqueIds inventory = true ↔ inventory.Nodup := by
  simp [uniqueIds]

theorem duplicate_id_rejected [DecidableEq Rule] (rule : Rule) (rest : List Rule) :
    uniqueIds (rule :: rule :: rest) = false := by
  simp [uniqueIds]

-- Exact complete certificates may not silently drop a known original rule.
theorem covered_sublist (implemented : Rule → Prop) (small large : List Rule)
    (included : ∀ rule, rule ∈ small → rule ∈ large)
    (covered : Covered implemented large) : Covered implemented small := by
  intro rule member
  exact covered rule (included rule member)

-- Contents are carried independently of source identity: an expected digest is
-- supplied by an installed policy, not chosen by a candidate certificate.
def identityMatches (expected candidate : String) : Bool := expected == candidate

theorem identity_matches_exact (expected candidate : String) :
    identityMatches expected candidate = true ↔ expected = candidate := by
  simp [identityMatches]

theorem changed_identity_rejected (expected candidate : String)
    (changed : expected ≠ candidate) : identityMatches expected candidate = false := by
  simp [identityMatches, changed]

end Nabt.BookCoverage
