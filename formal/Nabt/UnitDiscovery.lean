import Nabt.Derivation

/-!
# Contiguous proposals and conditional evidence licensing

The generator enumerates every contiguous partition of a supplied atom list.
The source declares the atomization: this is not a Unicode-grapheme algorithm.
Enumeration supplies neither unit classes nor linguistic functions. Those
remain opaque labels and separately interpreted, identity-bound evidence.

The licensing scope is **conditional on supplied interpreted evidence**.
An inventory below is a premise, not a claim that source bytes or their
linguistic interpretation have been independently replayed. No hash, caller
flag, spelling prefix, or repeated receipt acquires authority by itself.
-/

namespace Nabt.UnitDiscovery

def lawId : String := "nabt.unit-discovery.v1"
def evidenceScope : String := "conditional on supplied interpreted evidence"

abbrev Parts (α : Type) := List (List α)

def Exact (atoms : List α) (parts : Parts α) : Prop :=
  parts.flatten = atoms ∧ ∀ part ∈ parts, part ≠ []

instance [DecidableEq α] (atoms : List α) (parts : Parts α) :
    Decidable (Exact atoms parts) :=
  inferInstanceAs (Decidable
    (parts.flatten = atoms ∧ ∀ part ∈ parts, part ≠ []))

/-- At each original atom boundary, keep a cut or join the first part. -/
def extend (atom : α) : Parts α → List (Parts α)
  | [] => [[[atom]]]
  | part :: rest => [[atom] :: part :: rest, (atom :: part) :: rest]

/-- The empty source has one exact partition, containing no parts. -/
def allPartitions : List α → List (Parts α)
  | [] => [[]]
  | atom :: rest => (allPartitions rest).flatMap (extend atom)

private theorem extend_sound (atom : α) (atoms : List α) (parts result : Parts α)
    (exact : Exact atoms parts) (member : result ∈ extend atom parts) :
    Exact (atom :: atoms) result := by
  rcases exact with ⟨same, nonempty⟩
  cases parts with
  | nil =>
    simp only [extend, List.mem_singleton] at member
    subst result
    simp only [List.flatten_nil] at same
    subst atoms
    simp [Exact]
  | cons part rest =>
    simp only [extend, List.mem_cons, List.not_mem_nil, or_false] at member
    rcases member with rfl | rfl
    · constructor
      · simpa using congrArg (List.cons atom) same
      · intro p hp
        simp only [List.mem_cons] at hp
        rcases hp with rfl | hp
        · simp
        · exact nonempty p (List.mem_cons.mpr hp)
    · constructor
      · simpa using congrArg (List.cons atom) same
      · intro p hp
        simp only [List.mem_cons] at hp
        rcases hp with rfl | hp
        · simp
        · exact nonempty p (by simp [hp])

theorem allPartitions_sound (atoms : List α) (parts : Parts α)
    (member : parts ∈ allPartitions atoms) : Exact atoms parts := by
  induction atoms generalizing parts with
  | nil =>
    simp only [allPartitions, List.mem_singleton] at member
    subst parts
    simp [Exact]
  | cons atom atoms ih =>
    obtain ⟨previous, hp, he⟩ := List.mem_flatMap.mp member
    exact extend_sound atom atoms previous parts (ih previous hp) he

theorem allPartitions_complete (atoms : List α) (parts : Parts α)
    (exact : Exact atoms parts) : parts ∈ allPartitions atoms := by
  induction atoms generalizing parts with
  | nil =>
    cases parts with
    | nil => simp [allPartitions]
    | cons part rest =>
      have empty : part = [] := (List.append_eq_nil_iff.mp exact.1).1
      exact False.elim (exact.2 part (by simp) empty)
  | cons atom atoms ih =>
    cases parts with
    | nil => simp [Exact] at exact
    | cons part rest =>
      cases part with
      | nil => exact False.elim (exact.2 [] (by simp) rfl)
      | cons head tail =>
        have same : head = atom ∧ tail ++ rest.flatten = atoms := by
          simpa using exact.1
        rcases same with ⟨rfl, same⟩
        have restNonempty : ∀ p ∈ rest, p ≠ [] :=
          fun p hp => exact.2 p (by simp [hp])
        cases tail with
        | nil =>
          have previous : Exact atoms rest := ⟨by simpa using same, restNonempty⟩
          apply List.mem_flatMap.mpr
          refine ⟨rest, ih rest previous, ?_⟩
          cases rest <;> simp [extend]
        | cons next tail =>
          have previous : Exact atoms ((next :: tail) :: rest) := by
            refine ⟨same, ?_⟩
            intro p hp
            simp only [List.mem_cons] at hp
            rcases hp with rfl | hp
            · simp
            · exact restNonempty p hp
          apply List.mem_flatMap.mpr
          exact ⟨(next :: tail) :: rest, ih _ previous, by simp [extend]⟩

theorem mem_allPartitions_iff_exact (atoms : List α) (parts : Parts α) :
    parts ∈ allPartitions atoms ↔ Exact atoms parts :=
  ⟨allPartitions_sound atoms parts, allPartitions_complete atoms parts⟩

/-- Only used as the inverse of one enumeration step on nonempty parts. -/
private def eraseFirstAtom : Parts α → Parts α
  | [] => []
  | [] :: rest => rest
  | [_] :: rest => rest
  | (_ :: next :: tail) :: rest => (next :: tail) :: rest

private theorem eraseFirstAtom_extend (atom : α) (parts result : Parts α)
    (nonempty : ∀ p ∈ parts, p ≠ []) (member : result ∈ extend atom parts) :
    eraseFirstAtom result = parts := by
  cases parts with
  | nil =>
    simp only [extend, List.mem_singleton] at member
    subst result
    rfl
  | cons part rest =>
    cases part with
    | nil => exact False.elim (nonempty [] (by simp) rfl)
    | cons head tail =>
      simp only [extend, List.mem_cons, List.not_mem_nil, or_false] at member
      rcases member with rfl | rfl <;> rfl

private theorem extend_nodup (atom : α) (parts : Parts α)
    (nonempty : ∀ p ∈ parts, p ≠ []) : (extend atom parts).Nodup := by
  cases parts with
  | nil => simp [extend]
  | cons part rest =>
    cases part with
    | nil => exact False.elim (nonempty [] (by simp) rfl)
    | cons head tail => simp [extend]

theorem allPartitions_nodup (atoms : List α) : (allPartitions atoms).Nodup := by
  induction atoms with
  | nil => simp [allPartitions]
  | cons atom atoms ih =>
    apply List.pairwise_flatMap.mpr
    constructor
    · intro parts hp
      exact extend_nodup atom parts (allPartitions_sound atoms parts hp).2
    · apply List.Pairwise.imp_of_mem (p := ih)
      intro left right hl hr different x hx y hy same
      have leftInv := eraseFirstAtom_extend atom left x
        (allPartitions_sound atoms left hl).2 hx
      have rightInv := eraseFirstAtom_extend atom right y
        (allPartitions_sound atoms right hr).2 hy
      exact different (leftInv.symm.trans ((congrArg eraseFirstAtom same).trans rightInv))

private theorem length_flatMap_constant (f : α → List β) (items : List α) (k : Nat)
    (constant : ∀ item ∈ items, (f item).length = k) :
    (items.flatMap f).length = items.length * k := by
  induction items with
  | nil => simp
  | cons item items ih =>
    simp only [List.flatMap_cons, List.length_append, List.length_cons]
    rw [constant item (by simp), ih (fun x hx => constant x (by simp [hx]))]
    simp [Nat.add_mul, Nat.add_comm]

theorem allPartitions_count (atoms : List α) :
    (allPartitions atoms).length = 2 ^ (atoms.length - 1) := by
  induction atoms with
  | nil => simp [allPartitions]
  | cons atom atoms ih =>
    cases atoms with
    | nil => simp [allPartitions, extend]
    | cons next tail =>
      have constant : ∀ parts ∈ allPartitions (next :: tail),
          (extend atom parts).length = 2 := by
        intro parts hp
        have exact := allPartitions_sound (next :: tail) parts hp
        cases parts with
        | nil => simp [Exact] at exact
        | cons part rest => rfl
      rw [allPartitions, length_flatMap_constant _ _ 2 constant, ih]
      simp [Nat.pow_succ]

inductive Enumeration (α : Type) where
  | complete (partitions : List (Parts α))
  | exhausted
  deriving DecidableEq, Repr

/-- A budget bounds the declared atom count; exhaustion is not rejection. -/
def enumerateWithin (maxAtoms : Nat) (atoms : List α) : Enumeration α :=
  if atoms.length ≤ maxAtoms then .complete (allPartitions atoms) else .exhausted

theorem enumerateWithin_exhausted_iff (maxAtoms : Nat) (atoms : List α) :
    enumerateWithin maxAtoms atoms = .exhausted ↔ maxAtoms < atoms.length := by
  simp [enumerateWithin]

/-! ## Original source coordinates, independent of any filtered stream -/

structure Source (α : Type) where
  sourceId : Nat
  revision : Nat
  scopeId : Nat
  atomizationId : Nat
  atoms : List α
  deriving DecidableEq, Repr

structure Span where
  sourceId : Nat
  revision : Nat
  scopeId : Nat
  atomizationId : Nat
  start : Nat
  stop : Nat
  deriving DecidableEq, Repr

def ValidSpan (source : Source α) (span : Span) : Prop :=
  span.sourceId = source.sourceId ∧ span.revision = source.revision ∧
  span.scopeId = source.scopeId ∧ span.atomizationId = source.atomizationId ∧
  span.start < span.stop ∧ span.stop ≤ source.atoms.length

instance (source : Source α) (span : Span) : Decidable (ValidSpan source span) :=
  inferInstanceAs (Decidable (_ ∧ _ ∧ _ ∧ _ ∧ _ ∧ _))

def validSpan (source : Source α) (span : Span) : Bool := decide (ValidSpan source span)

def spanAtoms (source : Source α) (span : Span) : List α :=
  (source.atoms.drop span.start).take (span.stop - span.start)

/-- Coordinate adjacency requires the original boundary; removing an atom
from a filtered stream cannot make a positive gap adjacent here. -/
def adjacent (left right : Span) : Bool := decide (
  left.sourceId = right.sourceId ∧ left.revision = right.revision ∧
  left.scopeId = right.scopeId ∧ left.atomizationId = right.atomizationId ∧
  left.stop = right.start)

theorem validSpan_bounds (source : Source α) (span : Span)
    (valid : validSpan source span = true) :
    span.start < span.stop ∧ span.stop ≤ source.atoms.length :=
  (of_decide_eq_true valid).2.2.2.2

theorem adjacency_requires_original_boundary (left right : Span)
    (accepted : adjacent left right = true) : left.stop = right.start :=
  (of_decide_eq_true accepted).2.2.2.2

theorem positive_gap_not_adjacent (left right : Span) (gap : left.stop < right.start) :
    adjacent left right = false := by
  simp [adjacent, Nat.ne_of_lt gap]

theorem foreign_atomization_not_adjacent (left right : Span)
    (different : left.atomizationId ≠ right.atomizationId) :
    adjacent left right = false := by
  simp [adjacent, different]

/-- Offsets are computed from the complete unfiltered partition. -/
def partSpan (source : Source α) (parts : Parts α) (index : Nat) : Option Span :=
  (parts[index]?).map fun part =>
    let start := (parts.take index).flatten.length
    { sourceId := source.sourceId, revision := source.revision,
      scopeId := source.scopeId, atomizationId := source.atomizationId,
      start := start, stop := start + part.length }

/-! ## Correlated proposals and interpreted evidence

`UnitClass.id` and `Claim` name hypotheses supplied by a later learner or
declared vocabulary. This module does not discover their semantics.
Requirements are an open natural-number namespace; only zero is reserved.
-/

abbrev Requirement := Nat
def sourceRequirement : Requirement := 0

structure UnitClass where
  id : Nat
  deriving DecidableEq, Repr

structure Hypothesis (α Claim : Type) where
  source : Source α
  parts : Parts α
  partIndex : Nat
  host : Span
  unitClass : UnitClass
  claim : Claim
  ruleId : Nat
  occurrenceId : Nat
  readingId : Nat
  declaredRequirements : List Requirement
  deriving DecidableEq, Repr

def required (hypothesis : Hypothesis α Claim) : List Requirement :=
  sourceRequirement :: hypothesis.declaredRequirements

def wellFormed [DecidableEq α] (hypothesis : Hypothesis α Claim) : Bool :=
  decide (Exact hypothesis.source.atoms hypothesis.parts) &&
    validSpan hypothesis.source hypothesis.host &&
    match partSpan hypothesis.source hypothesis.parts hypothesis.partIndex with
    | none => false
    | some unit => validSpan hypothesis.source unit

/-- The complete source, not just its identifier, is a member of the supplied
inventory. Equal identifiers cannot silently substitute different atom bytes. -/
structure Support (α : Type) where
  source : Source α
  span : Span
  deriving DecidableEq, Repr

def validSupport [DecidableEq α] (inventory : List (Source α))
    (support : Support α) : Bool :=
  decide (support.source ∈ inventory) && validSpan support.source support.span

structure Receipt (α Claim : Type) where
  target : Hypothesis α Claim
  requirement : Requirement
  positive : Bool
  witnessId : Nat
  supports : List (Support α)
  deriving DecidableEq, Repr

/-- `interpreted` is an explicit input premise. Membership is not a proof of
the linguistic interpretation or of a real-world source replay. -/
def acceptsReceipt [DecidableEq α] [DecidableEq Claim]
    (inventory : List (Source α)) (interpreted : List (Receipt α Claim))
    (hypothesis : Hypothesis α Claim) (offered : Receipt α Claim) : Bool :=
  wellFormed hypothesis && decide (hypothesis.source ∈ inventory) &&
    decide (offered.target = hypothesis) && decide (offered ∈ interpreted) &&
    !offered.supports.isEmpty && offered.supports.all (validSupport inventory)

def admitted [DecidableEq α] [DecidableEq Claim]
    (inventory : List (Source α)) (interpreted : List (Receipt α Claim))
    (hypothesis : Hypothesis α Claim) (offered : List (Receipt α Claim)) :
    List (Receipt α Claim) :=
  offered.filter (acceptsReceipt inventory interpreted hypothesis)

/-- Logical support is set membership in requirement/polarity pairs.
Provenance rows remain intact, but repetition is not additional knowledge. -/
def supported (receipts : List (Receipt α Claim)) (requirement : Requirement)
    (positive : Bool) : Bool :=
  receipts.any fun receipt => decide (
    receipt.requirement = requirement ∧ receipt.positive = positive)

inductive Verdict where
  | pending
  | conditionalLicensed
  | rejected
  deriving DecidableEq, Repr

structure Assessment where
  verdict : Verdict
  conflict : Bool
  deriving DecidableEq, Repr

/-- The mandatory source requirement prevents vacuous licensing, even for
an empty caller-supplied requirements list. Negative evidence blocks; absent
evidence leaves a pending hypothesis. Conflict is reported separately. -/
def assessRequired (declaredRequirements : List Requirement)
    (receipts : List (Receipt α Claim)) : Assessment :=
  let needed := sourceRequirement :: declaredRequirements
  let conflict := needed.any fun r => supported receipts r true && supported receipts r false
  if needed.any (fun r => supported receipts r false) then ⟨.rejected, conflict⟩
  else if needed.all (fun r => supported receipts r true) then ⟨.conditionalLicensed, conflict⟩
  else ⟨.pending, conflict⟩

/-- `none` means malformed input, independently of the three conditional
evidence verdicts. Unknown requirements are never converted to rejection. -/
def assess [DecidableEq α] [DecidableEq Claim]
    (inventory : List (Source α)) (interpreted : List (Receipt α Claim))
    (hypothesis : Hypothesis α Claim) (offered : List (Receipt α Claim)) :
    Option Assessment :=
  if wellFormed hypothesis then
    some (assessRequired hypothesis.declaredRequirements
      (admitted inventory interpreted hypothesis offered))
  else none

def informationExtends (before after : List (Receipt α Claim)) : Bool :=
  before.all fun receipt => supported after receipt.requirement receipt.positive

/-- A new logical polarity for a relevant requirement is necessary for strict
progress. New negative evidence may turn licensing into conflict, so this is
information growth, not monotonic growth of the licensed set. -/
def strictProgress (declaredRequirements : List Requirement)
    (before after : List (Receipt α Claim)) : Bool :=
  informationExtends before after &&
    (sourceRequirement :: declaredRequirements).any (fun r =>
      (supported after r true && !supported before r true) ||
      (supported after r false && !supported before r false))

theorem wellFormed_preserves_source [DecidableEq α] (hypothesis : Hypothesis α Claim)
    (valid : wellFormed hypothesis = true) :
    Exact hypothesis.source.atoms hypothesis.parts := by
  simp only [wellFormed, Bool.and_eq_true, decide_eq_true_eq, and_assoc] at valid
  exact valid.1

theorem acceptsReceipt_iff [DecidableEq α] [DecidableEq Claim]
    (inventory : List (Source α)) (interpreted : List (Receipt α Claim))
    (hypothesis : Hypothesis α Claim) (offered : Receipt α Claim) :
    acceptsReceipt inventory interpreted hypothesis offered = true ↔
      wellFormed hypothesis = true ∧ hypothesis.source ∈ inventory ∧
      offered.target = hypothesis ∧ offered ∈ interpreted ∧ offered.supports ≠ [] ∧
      ∀ support ∈ offered.supports,
        support.source ∈ inventory ∧ ValidSpan support.source support.span := by
  simp [acceptsReceipt, validSupport, validSpan, List.all_eq_true, and_assoc]

/-- Exact equality binds source atoms, occurrence, partition, selected unit,
host, class, claim, rule, declared requirements and reading simultaneously. -/
theorem accepted_receipt_bound [DecidableEq α] [DecidableEq Claim]
    (inventory : List (Source α)) (interpreted : List (Receipt α Claim))
    (hypothesis : Hypothesis α Claim) (offered : Receipt α Claim)
    (accepted : acceptsReceipt inventory interpreted hypothesis offered = true) :
    offered.target = hypothesis ∧ offered ∈ interpreted ∧ offered.supports ≠ [] ∧
      ∀ support ∈ offered.supports,
        support.source ∈ inventory ∧ ValidSpan support.source support.span :=
  ((acceptsReceipt_iff inventory interpreted hypothesis offered).mp accepted).2.2

theorem foreign_target_not_accepted [DecidableEq α] [DecidableEq Claim]
    (inventory : List (Source α)) (interpreted : List (Receipt α Claim))
    (hypothesis : Hypothesis α Claim) (offered : Receipt α Claim)
    (foreign : offered.target ≠ hypothesis) :
    acceptsReceipt inventory interpreted hypothesis offered = false := by
  simp [acceptsReceipt, foreign]

theorem uninterpreted_not_accepted [DecidableEq α] [DecidableEq Claim]
    (inventory : List (Source α)) (interpreted : List (Receipt α Claim))
    (hypothesis : Hypothesis α Claim) (offered : Receipt α Claim)
    (absent : offered ∉ interpreted) :
    acceptsReceipt inventory interpreted hypothesis offered = false := by
  simp [acceptsReceipt, absent]

theorem no_support_not_accepted [DecidableEq α] [DecidableEq Claim]
    (inventory : List (Source α)) (interpreted : List (Receipt α Claim))
    (hypothesis : Hypothesis α Claim) (offered : Receipt α Claim)
    (empty : offered.supports = []) :
    acceptsReceipt inventory interpreted hypothesis offered = false := by
  simp [acceptsReceipt, empty]

theorem mem_admitted_iff [DecidableEq α] [DecidableEq Claim]
    (inventory : List (Source α)) (interpreted : List (Receipt α Claim))
    (hypothesis : Hypothesis α Claim) (offered : List (Receipt α Claim))
    (receipt : Receipt α Claim) :
    receipt ∈ admitted inventory interpreted hypothesis offered ↔
      receipt ∈ offered ∧ acceptsReceipt inventory interpreted hypothesis receipt = true := by
  simp [admitted]

theorem supported_iff (receipts : List (Receipt α Claim)) (requirement : Requirement)
    (positive : Bool) : supported receipts requirement positive = true ↔
      ∃ receipt ∈ receipts, receipt.requirement = requirement ∧ receipt.positive = positive := by
  simp [supported, List.any_eq_true]

theorem supported_append (before after : List (Receipt α Claim))
    (requirement : Requirement) (positive : Bool) :
    supported (before ++ after) requirement positive =
      (supported before requirement positive || supported after requirement positive) := by
  simp [supported]

/-- Different provenance for an already supported proposition is retained as
evidence, but cannot change any logical support bit. -/
theorem repeated_proposition_no_change (receipts : List (Receipt α Claim))
    (receipt : Receipt α Claim)
    (already : supported receipts receipt.requirement receipt.positive = true)
    (requirement : Requirement) (positive : Bool) :
    supported (receipt :: receipts) requirement positive = supported receipts requirement positive := by
  change (decide (receipt.requirement = requirement ∧ receipt.positive = positive) ||
    supported receipts requirement positive) = supported receipts requirement positive
  by_cases same : receipt.requirement = requirement ∧ receipt.positive = positive
  · rcases same with ⟨rfl, rfl⟩
    simp [already]
  · simp [same]

theorem assessRequired_ext (declaredRequirements : List Requirement)
    (before after : List (Receipt α Claim))
    (same : ∀ r positive, supported before r positive = supported after r positive) :
    assessRequired declaredRequirements before = assessRequired declaredRequirements after := by
  simp only [assessRequired, same]

theorem no_receipts_pending (declaredRequirements : List Requirement) :
    assessRequired declaredRequirements ([] : List (Receipt α Claim)) = ⟨.pending, false⟩ := by
  simp [assessRequired, supported]

theorem conditionalLicensed_iff (declaredRequirements : List Requirement)
    (receipts : List (Receipt α Claim)) :
    (assessRequired declaredRequirements receipts).verdict = .conditionalLicensed ↔
      ((sourceRequirement :: declaredRequirements).any
        (fun r => supported receipts r false) = false ∧
       (sourceRequirement :: declaredRequirements).all
        (fun r => supported receipts r true) = true) := by
  cases negative : (sourceRequirement :: declaredRequirements).any
      (fun r => supported receipts r false) <;>
    cases positive : (sourceRequirement :: declaredRequirements).all
      (fun r => supported receipts r true) <;>
    simp [assessRequired, negative, positive]

theorem licensed_requires_source (declaredRequirements : List Requirement)
    (receipts : List (Receipt α Claim))
    (licensed : (assessRequired declaredRequirements receipts).verdict = .conditionalLicensed) :
    supported receipts sourceRequirement true = true ∧
      supported receipts sourceRequirement false = false := by
  obtain ⟨noNegative, allPositive⟩ :=
    (conditionalLicensed_iff declaredRequirements receipts).mp licensed
  exact ⟨(List.all_eq_true.mp allPositive) sourceRequirement (by simp),
    by simpa using (List.any_eq_false.mp noNegative) sourceRequirement (by simp)⟩

theorem negative_rejects (declaredRequirements : List Requirement)
    (receipts : List (Receipt α Claim)) (requirement : Requirement)
    (needed : requirement ∈ sourceRequirement :: declaredRequirements)
    (negative : supported receipts requirement false = true) :
    (assessRequired declaredRequirements receipts).verdict = .rejected := by
  have found : (sourceRequirement :: declaredRequirements).any
      (fun r => supported receipts r false) = true :=
    List.any_eq_true.mpr ⟨requirement, needed, negative⟩
  simp [assessRequired, found]

theorem conflict_rejects (declaredRequirements : List Requirement)
    (receipts : List (Receipt α Claim))
    (conflict : (assessRequired declaredRequirements receipts).conflict = true) :
    (assessRequired declaredRequirements receipts).verdict = .rejected := by
  have flagged : (sourceRequirement :: declaredRequirements).any
      (fun r => supported receipts r true && supported receipts r false) = true := by
    dsimp only [assessRequired] at conflict
    split at conflict
    · exact conflict
    · split at conflict <;> exact conflict
  obtain ⟨r, needed, both⟩ := List.any_eq_true.mp flagged
  exact negative_rejects declaredRequirements receipts r needed (Bool.and_eq_true_iff.mp both).2

theorem repeated_proposition_same_assessment (declaredRequirements : List Requirement)
    (receipts : List (Receipt α Claim)) (receipt : Receipt α Claim)
    (already : supported receipts receipt.requirement receipt.positive = true) :
    assessRequired declaredRequirements (receipt :: receipts) =
      assessRequired declaredRequirements receipts :=
  assessRequired_ext declaredRequirements _ _
    (repeated_proposition_no_change receipts receipt already)

theorem no_offered_evidence_pending [DecidableEq α] [DecidableEq Claim]
    (inventory : List (Source α)) (interpreted : List (Receipt α Claim))
    (hypothesis : Hypothesis α Claim) :
    assess inventory interpreted hypothesis [] =
      if wellFormed hypothesis then some ⟨.pending, false⟩ else none := by
  simp [assess, admitted, no_receipts_pending]

theorem malformed_has_no_assessment [DecidableEq α] [DecidableEq Claim]
    (inventory : List (Source α)) (interpreted : List (Receipt α Claim))
    (hypothesis : Hypothesis α Claim) (offered : List (Receipt α Claim))
    (malformed : wellFormed hypothesis = false) :
    assess inventory interpreted hypothesis offered = none := by
  simp [assess, malformed]

theorem informationExtends_append (before after : List (Receipt α Claim)) :
    informationExtends before (before ++ after) = true := by
  apply List.all_eq_true.mpr
  intro receipt member
  apply (supported_iff _ _ _).mpr
  exact ⟨receipt, by simp [member], rfl, rfl⟩

theorem strictProgress_requires_new_fact (declaredRequirements : List Requirement)
    (before after : List (Receipt α Claim))
    (progress : strictProgress declaredRequirements before after = true) :
    informationExtends before after = true ∧
      ∃ r ∈ sourceRequirement :: declaredRequirements, ∃ positive : Bool,
        supported after r positive = true ∧ supported before r positive = false := by
  obtain ⟨grows, added⟩ := Bool.and_eq_true_iff.mp progress
  refine ⟨grows, ?_⟩
  obtain ⟨r, needed, change⟩ := List.any_eq_true.mp added
  refine ⟨r, needed, ?_⟩
  rcases Bool.or_eq_true_iff.mp change with yes | no
  · exact ⟨true, (Bool.and_eq_true_iff.mp yes).1, by simpa using (Bool.and_eq_true_iff.mp yes).2⟩
  · exact ⟨false, (Bool.and_eq_true_iff.mp no).1, by simpa using (Bool.and_eq_true_iff.mp no).2⟩

theorem repeated_proposition_not_progress (declaredRequirements : List Requirement)
    (receipts : List (Receipt α Claim)) (receipt : Receipt α Claim)
    (already : supported receipts receipt.requirement receipt.positive = true) :
    strictProgress declaredRequirements receipts (receipt :: receipts) = false := by
  simp only [strictProgress, repeated_proposition_no_change receipts receipt already]
  simp

/-! ## Interdigitated root/template shape readings

Only triliteral and quadriliteral candidates are represented in this initial
interface. This is not a claim that all Arabic nominal roots have those sizes.
Complete pattern replay checks the whole host, not a root-prefix substring.
-/

instance rootDecidableEq (n : Nat) : DecidableEq (Derivation.Root n) := fun left right =>
  if same : ∀ index : Fin n, left index = right index then
    isTrue (funext same)
  else isFalse (fun equality => same (fun index => congrFun equality index))

inductive RootPatternReading where
  | tri (pattern : Derivation.Pattern 3) (root : Derivation.Root 3)
  | quad (pattern : Derivation.Pattern 4) (root : Derivation.Root 4)
  deriving DecidableEq

namespace RootPatternReading

def render : RootPatternReading → List Char
  | .tri pattern root => Derivation.fill pattern root
  | .quad pattern root => Derivation.fill pattern root

def complete : RootPatternReading → Bool
  | .tri pattern _ => decide (Derivation.Complete pattern)
  | .quad pattern _ => decide (Derivation.Complete pattern)

def radicals : RootPatternReading → List Char
  | .tri _ root => (List.finRange 3).map root
  | .quad _ root => (List.finRange 4).map root

end RootPatternReading

def fitsHost (source : Source Char) (host : Span) (reading : RootPatternReading) : Bool :=
  validSpan source host && reading.complete && decide (reading.render = spanAtoms source host)

def recoverTri (pattern : Derivation.Pattern 3) (atoms : List Char) :
    Option RootPatternReading :=
  (Derivation.recover pattern atoms).map (RootPatternReading.tri pattern)

def recoverQuad (pattern : Derivation.Pattern 4) (atoms : List Char) :
    Option RootPatternReading :=
  (Derivation.recover pattern atoms).map (RootPatternReading.quad pattern)

theorem fitsHost_sound (source : Source Char) (host : Span) (reading : RootPatternReading)
    (fits : fitsHost source host reading = true) :
    ValidSpan source host ∧ reading.complete = true ∧ reading.render = spanAtoms source host := by
  simpa [fitsHost, validSpan, and_assoc] using fits

theorem fitsHost_tri_recovers (source : Source Char) (host : Span)
    (pattern : Derivation.Pattern 3) (root : Derivation.Root 3)
    (fits : fitsHost source host (.tri pattern root) = true) :
    recoverTri pattern (spanAtoms source host) = some (.tri pattern root) := by
  obtain ⟨_, complete, replay⟩ := fitsHost_sound source host (.tri pattern root) fits
  have recovered := (Derivation.recover_exact_iff pattern (spanAtoms source host) root).mpr
    ⟨of_decide_eq_true complete, replay⟩
  simp [recoverTri, recovered]

theorem fitsHost_quad_recovers (source : Source Char) (host : Span)
    (pattern : Derivation.Pattern 4) (root : Derivation.Root 4)
    (fits : fitsHost source host (.quad pattern root) = true) :
    recoverQuad pattern (spanAtoms source host) = some (.quad pattern root) := by
  obtain ⟨_, complete, replay⟩ := fitsHost_sound source host (.quad pattern root) fits
  have recovered := (Derivation.recover_exact_iff pattern (spanAtoms source host) root).mpr
    ⟨of_decide_eq_true complete, replay⟩
  simp [recoverQuad, recovered]

/-- Filters preserve whole correlated readings, with no first-reading choice. -/
def rootReadings (source : Source Char) (host : Span)
    (proposals : List RootPatternReading) : List RootPatternReading :=
  proposals.filter (fitsHost source host)

theorem rootReadings_preserve_ambiguity (source : Source Char) (host : Span)
    (proposals : List RootPatternReading) (left right : RootPatternReading)
    (leftMember : left ∈ proposals) (rightMember : right ∈ proposals)
    (leftFits : fitsHost source host left = true) (rightFits : fitsHost source host right = true)
    (different : left ≠ right) :
    left ∈ rootReadings source host proposals ∧ right ∈ rootReadings source host proposals ∧
      left ≠ right := by
  exact ⟨List.mem_filter.mpr ⟨leftMember, leftFits⟩,
    List.mem_filter.mpr ⟨rightMember, rightFits⟩, different⟩

end Nabt.UnitDiscovery
