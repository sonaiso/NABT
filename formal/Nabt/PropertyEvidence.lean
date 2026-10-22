import Std

/-!
# Source-property admission and a finite evidence ledger

The source reader supplies an expected record after replaying its pinned bytes.
This file proves the exact-record admission boundary, NOT authenticity of that
reader, SHA-256 collision freedom, Arabic interpretation, or Python refinement.
The ledger is independently specified by predicates on `Fin width`. Its table
is compared exhaustively with Python's bit-mask implementation for width four.
-/

namespace Nabt.PropertyEvidence

structure EvidenceBinding where
  occurrenceId : String
  readingId : String
  sourceSha256 : String
  contextSha256 : String
  definitionId : String
  policyId : String
  schemaId : String
  checkerVersion : String
  deriving DecidableEq, Repr

structure EvidenceProposal where
  recordId : String
  binding : EvidenceBinding
  known : Nat
  value : Nat
  label : Option Bool
  deriving DecidableEq, Repr

/-- No receipt or caller assertion substitutes for the replayed expected record. -/
def admits (expected : Option EvidenceProposal) (proposed : EvidenceProposal) : Bool :=
  decide (expected = some proposed)

@[simp] theorem admits_iff (expected : Option EvidenceProposal)
    (proposed : EvidenceProposal) :
    admits expected proposed = true ↔ expected = some proposed := by
  simp [admits]

@[simp] theorem absent_replay_refused (proposed : EvidenceProposal) :
    admits none proposed = false := by
  simp [admits]

theorem admitted_record_is_exact (expected proposed : EvidenceProposal)
    (accepted : admits (some expected) proposed = true) : proposed = expected := by
  have same := (admits_iff (some expected) proposed).mp accepted
  exact (Option.some.inj same).symm

theorem binding_cannot_transfer (expected proposed : EvidenceProposal)
    (different : proposed.binding ≠ expected.binding) :
    admits (some expected) proposed = false := by
  simp only [admits, decide_eq_false_iff_not, Option.some.injEq]
  intro same
  exact different (congrArg EvidenceProposal.binding same.symm)

theorem labels_cannot_transfer (expected proposed : EvidenceProposal)
    (different : proposed.label ≠ expected.label) :
    admits (some expected) proposed = false := by
  simp only [admits, decide_eq_false_iff_not, Option.some.injEq]
  intro same
  exact different (congrArg EvidenceProposal.label same.symm)

theorem changed_replay_refuses_stale_record (old revised : EvidenceProposal)
    (changed : revised ≠ old) : admits (some revised) old = false := by
  simp [admits, changed]

/-- Unknown is not an explicit negative observation. -/
theorem unknown_label_is_not_false (record : EvidenceProposal) :
    { record with label := none } ≠ { record with label := some false } := by
  intro same
  have labels := congrArg EvidenceProposal.label same
  contradiction

/-- Equality alone may match a partial record; ready admission is stronger. -/
def ready (width : Nat) (record : EvidenceProposal) : Bool :=
  decide (0 < width ∧ width ≤ 32 ∧ record.known = 2 ^ width - 1 ∧
    record.value < 2 ^ width ∧ record.label.isSome = true)

def acceptsReady (width : Nat) (expected : Option EvidenceProposal)
    (proposed : EvidenceProposal) : Bool :=
  admits expected proposed && ready width proposed

theorem accepts_ready_iff (width : Nat) (expected : Option EvidenceProposal)
    (proposed : EvidenceProposal) :
    acceptsReady width expected proposed = true ↔
      expected = some proposed ∧ ready width proposed = true := by
  simp [acceptsReady]

theorem unknown_cannot_be_ready (width : Nat) (record : EvidenceProposal) :
    ready width {record with label := none} = false := by
  simp [ready]

theorem ready_requires_full_mask (width : Nat) (record : EvidenceProposal)
    (isReady : ready width record = true) : record.known = 2 ^ width - 1 := by
  have checked := of_decide_eq_true isReady
  exact checked.2.2.1

theorem ready_admission_binds_record (width : Nat) (expected proposed : EvidenceProposal)
    (accepted : acceptsReady width (some expected) proposed = true) :
    proposed = expected ∧ ready width proposed = true := by
  have checked := (accepts_ready_iff width (some expected) proposed).mp accepted
  exact ⟨(Option.some.inj checked.1).symm, checked.2⟩

structure Ledger (width : Nat) where
  positive : Fin width → Bool
  negative : Fin width → Bool

abbrev Required (width : Nat) := Fin width → Bool

def Conflict {width : Nat} (required : Required width) (ledger : Ledger width) : Prop :=
  ∃ i, required i = true ∧ ledger.positive i = true ∧ ledger.negative i = true

def Negative {width : Nat} (required : Required width) (ledger : Ledger width) : Prop :=
  ∃ i, required i = true ∧ ledger.positive i = false ∧ ledger.negative i = true

def Missing {width : Nat} (required : Required width) (ledger : Ledger width) : Prop :=
  ∃ i, required i = true ∧ ledger.positive i = false ∧ ledger.negative i = false

instance {width : Nat} (required : Required width) (ledger : Ledger width) :
    Decidable (Conflict required ledger) := by
  unfold Conflict
  infer_instance

instance {width : Nat} (required : Required width) (ledger : Ledger width) :
    Decidable (Negative required ledger) := by
  unfold Negative
  infer_instance

instance {width : Nat} (required : Required width) (ledger : Ledger width) :
    Decidable (Missing required ledger) := by
  unfold Missing
  infer_instance

inductive Verdict where
  | conflict | rejected | pending | licensed
  deriving DecidableEq, Repr

def judge {width : Nat} (required : Required width) (ledger : Ledger width) : Verdict :=
  if Conflict required ledger then .conflict
  else if Negative required ledger then .rejected
  else if Missing required ledger then .pending
  else .licensed

theorem conflict_has_priority {width : Nat} (required : Required width)
    (ledger : Ledger width) (conflict : Conflict required ledger) :
    judge required ledger = .conflict := by
  simp [judge, conflict]

theorem rejected_iff {width : Nat} (required : Required width) (ledger : Ledger width) :
    judge required ledger = .rejected ↔
      ¬ Conflict required ledger ∧ Negative required ledger := by
  by_cases c : Conflict required ledger <;>
    by_cases n : Negative required ledger <;>
    by_cases m : Missing required ledger <;> simp [judge, c, n, m]

theorem pending_iff {width : Nat} (required : Required width) (ledger : Ledger width) :
    judge required ledger = .pending ↔
      ¬ Conflict required ledger ∧ ¬ Negative required ledger ∧ Missing required ledger := by
  by_cases c : Conflict required ledger <;>
    by_cases n : Negative required ledger <;>
    by_cases m : Missing required ledger <;> simp [judge, c, n, m]

theorem licensed_iff {width : Nat} (required : Required width) (ledger : Ledger width) :
    judge required ledger = .licensed ↔
      ∀ i, required i = true → ledger.positive i = true ∧ ledger.negative i = false := by
  constructor
  · intro licensed i needed
    have noConflict : ¬ Conflict required ledger := by
      intro conflict
      have other := conflict_has_priority required ledger conflict
      rw [licensed] at other
      contradiction
    have noNegative : ¬ Negative required ledger := by
      intro negative
      have other : judge required ledger = .rejected :=
        (rejected_iff required ledger).mpr ⟨noConflict, negative⟩
      rw [licensed] at other
      contradiction
    have noMissing : ¬ Missing required ledger := by
      intro missing
      have other : judge required ledger = .pending :=
        (pending_iff required ledger).mpr ⟨noConflict, noNegative, missing⟩
      rw [licensed] at other
      contradiction
    cases hp : ledger.positive i <;> cases hn : ledger.negative i
    · exact False.elim (noMissing ⟨i, needed, hp, hn⟩)
    · exact False.elim (noNegative ⟨i, needed, hp, hn⟩)
    · exact ⟨rfl, rfl⟩
    · exact False.elim (noConflict ⟨i, needed, hp, hn⟩)
  · intro complete
    have noConflict : ¬ Conflict required ledger := by
      rintro ⟨i, needed, _, hn⟩
      have noNeg := (complete i needed).2
      rw [hn] at noNeg
      contradiction
    have noNegative : ¬ Negative required ledger := by
      rintro ⟨i, needed, hp, _⟩
      have pos := (complete i needed).1
      rw [hp] at pos
      contradiction
    have noMissing : ¬ Missing required ledger := by
      rintro ⟨i, needed, hp, _⟩
      have pos := (complete i needed).1
      rw [hp] at pos
      contradiction
    simp [judge, noConflict, noNegative, noMissing]

theorem empty_requirements_licensed {width : Nat} (ledger : Ledger width) :
    judge (fun _ => false) ledger = .licensed := by
  apply (licensed_iff _ _).mpr
  intro _ impossible
  contradiction

/-- Application must first find a rule; the empty arithmetic mask is not lookup success. -/
def judgeRule {width : Nat} (required : Option (Required width))
    (ledger : Ledger width) : Option Verdict :=
  required.map (fun r => judge r ledger)

@[simp] theorem absent_rule_not_licensed {width : Nat} (ledger : Ledger width) :
    judgeRule none ledger = none := by
  rfl

/-- A read mask is interpreted independently as finite Boolean predicates. -/
def bits (width mask : Nat) : Fin width → Bool :=
  fun i => decide (mask / 2 ^ i.val % 2 = 1)

/-- Natural-number operations avoid an unbounded signed complement. -/
def numericConflicts (required positive negative : Nat) : Nat :=
  required &&& positive &&& negative

def numericNegatives (required positive negative : Nat) : Nat :=
  (required &&& negative) ^^^ ((required &&& negative) &&& positive)

def numericMissing (required positive negative : Nat) : Nat :=
  required ^^^ (required &&& (positive ||| negative))

theorem numeric_conflicts_bit {width : Nat} (r p n : Nat) (i : Fin width) :
    bits width (numericConflicts r p n) i =
      (bits width r i && bits width p i && bits width n i) := by
  simp only [bits, ← Nat.testBit_eq_decide_div_mod_eq]
  simp [numericConflicts]

theorem numeric_negatives_bit {width : Nat} (r p n : Nat) (i : Fin width) :
    bits width (numericNegatives r p n) i =
      (bits width r i && !bits width p i && bits width n i) := by
  simp only [bits, ← Nat.testBit_eq_decide_div_mod_eq]
  simp only [numericNegatives, Nat.testBit_xor, Nat.testBit_and]
  cases hr : r.testBit i.val <;> cases hp : p.testBit i.val <;>
    cases hn : n.testBit i.val <;>
    simp

theorem numeric_missing_bit {width : Nat} (r p n : Nat) (i : Fin width) :
    bits width (numericMissing r p n) i =
      (bits width r i && !bits width p i && !bits width n i) := by
  simp only [bits, ← Nat.testBit_eq_decide_div_mod_eq]
  simp only [numericMissing, Nat.testBit_xor, Nat.testBit_and, Nat.testBit_or]
  cases hr : r.testBit i.val <;> cases hp : p.testBit i.val <;>
    cases hn : n.testBit i.val <;>
    simp

def ledgerOfMasks (width positive negative : Nat) : Ledger width :=
  ⟨bits width positive, bits width negative⟩

def predicateMask {width : Nat} (predicate : Fin width → Bool) : Nat :=
  ((List.finRange width).map (fun i => if predicate i then 2 ^ i.val else 0)).sum

def conflictMask {width : Nat} (required : Required width) (ledger : Ledger width) : Nat :=
  predicateMask (fun i => required i && ledger.positive i && ledger.negative i)

def negativeMask {width : Nat} (required : Required width) (ledger : Ledger width) : Nat :=
  predicateMask (fun i => required i && !ledger.positive i && ledger.negative i)

def missingMask {width : Nat} (required : Required width) (ledger : Ledger width) : Nat :=
  predicateMask (fun i => required i && !ledger.positive i && !ledger.negative i)

end Nabt.PropertyEvidence
