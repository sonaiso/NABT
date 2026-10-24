import Nabt.UnitDiscovery
import Nabt.Transition

/-!
# Finite, source-preserving licensed constructions

`Tree` proposes an atomic occurrence or a join, enclosure, substitution,
or lift. It is not a license. `Licensed` has one constructor per operation;
every composite node needs its own exact-target interpreted premises and all
of its children must already be licensed. The interpretation inventory is an
explicit premise, not a source reader or an acquired linguistic classifier.

Raw source, current output, remaining source and derivation identity are
separate. A substitution retains its complete child (including the displaced
output), so deletion is reversible rather than an empty source occurrence.
`undo` checks the current output and replays that retained derivation.
An enclosure is inert on output and source, not on classification: its tag
may classify the enclosing unit under its own exact-target evidence. A lift
additionally requires a class change. Neither operation inserts raw atoms.

General preservation follows by induction on a finite licensed derivation.
Necessity is stronger: it is proved only relative to an explicitly exhaustive
domain in which every competing derivation has a rejection. Pending and an
exhausted search cannot supply those rejections.
There is no finite global closure claim: unbounded tags, replacements and
successive enclosures give an infinite proposal language. A finite search
must declare bounds for its complete candidate domain separately.
-/

namespace Nabt.LicensedDerivation

def lawId : String := "nabt.licensed-derivation.v1"
def evidenceScope : String := "conditional_on_supplied_interpretations"

/-- These identifiers have no built-in linguistic meanings. Requirement zero
is mandatory construction applicability, not a caller-supplied acceptance bit. -/
structure Tag where
  ruleId : Nat
  readingId : Nat
  classId : Nat
  requirements : List Nat
  deriving DecidableEq, Repr

inductive Tree (α : Type) where
  | atom (source : UnitDiscovery.Source α) (before : List α)
      (value : α) (after : List α)
  | join (tag : Tag) (left right : Tree α)
  | wrap (tag : Tag) (child : Tree α)
  | substitute (tag : Tag) (replacement : List α) (child : Tree α)
  | lift (tag : Tag) (child : Tree α)
  deriving DecidableEq, Repr

namespace Tree

def source : Tree α → UnitDiscovery.Source α
  | .atom source _ _ _ => source
  | .join _ left _ => left.source
  | .wrap _ child | .substitute _ _ child | .lift _ child => child.source

def before : Tree α → List α
  | .atom _ before _ _ => before
  | .join _ left _ => left.before
  | .wrap _ child | .substitute _ _ child | .lift _ child => child.before

def raw : Tree α → List α
  | .atom _ _ value _ => [value]
  | .join _ left right => left.raw ++ right.raw
  | .wrap _ child | .substitute _ _ child | .lift _ child => child.raw

def after : Tree α → List α
  | .atom _ _ _ after => after
  | .join _ _ right => right.after
  | .wrap _ child | .substitute _ _ child | .lift _ child => child.after

def output : Tree α → List α
  | .atom _ _ value _ => [value]
  | .join _ left right => left.output ++ right.output
  | .substitute _ replacement _ => replacement
  | .wrap _ child | .lift _ child => child.output

def classId : Tree α → Option Nat
  | .atom .. => none
  | .join tag .. | .wrap tag .. | .substitute tag .. | .lift tag .. => some tag.classId

def rank : Tree α → Nat
  | .atom .. => 0
  | .join _ left right => max left.rank right.rank + 1
  | .wrap _ child | .substitute _ _ child | .lift _ child => child.rank + 1

def required : Tree α → List Nat
  | .atom .. => []
  | .join tag .. | .wrap tag .. | .substitute tag .. | .lift tag .. =>
      0 :: tag.requirements

/-- Each proposal stays in the trace, even if multiple proposals share a unit
key. Repeated source occurrences are not collapsed by equality of spelling. -/
def steps : Tree α → List (Tree α)
  | .atom .. => []
  | tree@(.join _ left right) => tree :: (left.steps ++ right.steps)
  | tree@(.wrap _ child) | tree@(.substitute _ _ child) | tree@(.lift _ child) =>
      tree :: child.steps

def start (tree : Tree α) : Nat := tree.before.length
def stop (tree : Tree α) : Nat := tree.start + tree.raw.length
def remainder (tree : Tree α) : List α × List α := (tree.before, tree.after)
def reconstruct (tree : Tree α) : List α := tree.before ++ tree.raw ++ tree.after

/-- These are operation-specific structural entry conditions. Neither a tag
nor an equality of flattened source grants an interpreted license. -/
def entry [DecidableEq α] (inventory : List (UnitDiscovery.Source α)) : Tree α → Bool
  | .atom source before value after =>
      decide (source ∈ inventory ∧ source.atoms = before ++ [value] ++ after)
  | .join _ left right => decide (
      left.source = right.source ∧
      right.before = left.before ++ left.raw ∧
      left.after = right.raw ++ right.after)
  | .wrap .. => true
  | .substitute _ replacement child => decide (replacement ≠ child.output)
  | .lift tag child => decide (some tag.classId ≠ child.classId)

def structural [DecidableEq α] (inventory : List (UnitDiscovery.Source α)) :
    Tree α → Bool
  | tree@(.atom ..) => tree.entry inventory
  | tree@(.join _ left right) =>
      tree.entry inventory && left.structural inventory && right.structural inventory
  | tree@(.wrap _ child) | tree@(.substitute _ _ child) | tree@(.lift _ child) =>
      tree.entry inventory && child.structural inventory

/-- `undo` consumes the claimed current output. At substitution it verifies
the full replacement then replays the displaced child output retained in the
tree. No removed atom is reconstructed from a default value. -/
def undo [DecidableEq α] : Tree α → List α → Option (List α)
  | .atom _ _ value _, seen => if seen = [value] then some [value] else none
  | .join _ left right, seen =>
      if seen.length = left.output.length + right.output.length then do
        let restoredLeft ← left.undo (seen.take left.output.length)
        let restoredRight ← right.undo (seen.drop left.output.length)
        pure (restoredLeft ++ restoredRight)
      else none
  | .wrap _ child, seen | .lift _ child, seen => child.undo seen
  | .substitute _ replacement child, seen =>
      if seen = replacement then child.undo child.output else none

end Tree

/-- Unit identity is source-bound content plus its interpreted class. It does
not identify the derivation: different trees may produce the same unit key. -/
structure UnitKey (α : Type) where
  source : UnitDiscovery.Source α
  start : Nat
  raw : List α
  output : List α
  classId : Option Nat
  deriving DecidableEq, Repr

def unitKey (tree : Tree α) : UnitKey α :=
  ⟨tree.source, tree.start, tree.raw, tree.output, tree.classId⟩

structure Receipt (α : Type) where
  target : Tree α
  requirement : Nat
  positive : Bool
  witnessId : Nat
  supports : List (UnitDiscovery.Support α)
  deriving DecidableEq, Repr

structure Context (α : Type) where
  inventory : List (UnitDiscovery.Source α)
  interpreted : List (Receipt α)
  offered : List (Receipt α)
  deriving DecidableEq, Repr

def acceptsReceipt [DecidableEq α] (ctx : Context α) (target : Tree α)
    (receipt : Receipt α) : Bool :=
  decide (receipt.target = target) && decide (receipt ∈ ctx.interpreted) &&
    !receipt.supports.isEmpty && receipt.supports.all (UnitDiscovery.validSupport ctx.inventory)

def admitted [DecidableEq α] (ctx : Context α) (target : Tree α) : List (Receipt α) :=
  ctx.offered.filter (acceptsReceipt ctx target)

/-- A known, valid negative interpretation is not hideable by removing it
from the offered positive ledger. This is an explicit closed negative ledger
within the supplied interpretation context, not a claim of world knowledge. -/
def negativeAdmitted [DecidableEq α] (ctx : Context α) (target : Tree α) : List (Receipt α) :=
  ctx.interpreted.filter fun receipt => acceptsReceipt ctx target receipt && !receipt.positive

def supported (receipts : List (Receipt α)) (requirement : Nat) (positive : Bool) : Bool :=
  receipts.any fun receipt => decide (
    receipt.requirement = requirement ∧ receipt.positive = positive)

def localNegative [DecidableEq α] (ctx : Context α) (tree : Tree α) : Bool :=
  tree.required.any fun requirement => supported (negativeAdmitted ctx tree) requirement false

def localPositive [DecidableEq α] (ctx : Context α) (tree : Tree α) : Bool :=
  tree.required.all fun requirement => supported (admitted ctx tree) requirement true

def localConflict [DecidableEq α] (ctx : Context α) (tree : Tree α) : Bool :=
  tree.required.any fun requirement =>
    supported (admitted ctx tree) requirement true &&
      supported (negativeAdmitted ctx tree) requirement false

def localLicensed [DecidableEq α] (ctx : Context α) (tree : Tree α) : Bool :=
  !localNegative ctx tree && localPositive ctx tree

def allLicensed [DecidableEq α] (ctx : Context α) (tree : Tree α) : Bool :=
  tree.steps.all (localLicensed ctx)

def anyNegative [DecidableEq α] (ctx : Context α) (tree : Tree α) : Bool :=
  tree.steps.any (localNegative ctx)

def anyConflict [DecidableEq α] (ctx : Context α) (tree : Tree α) : Bool :=
  tree.steps.any (localConflict ctx)

inductive Status where
  | invalid
  | pending
  | conditionalLicensed
  | rejected
  deriving DecidableEq, Repr

structure Report where
  status : Status
  conflict : Bool
  deriving DecidableEq, Repr

/-- Invalid structure is distinct from missing premises and from negative
evidence. Every child contributes to rejection, conflict and pending status. -/
def assess [DecidableEq α] (ctx : Context α) (tree : Tree α) : Report :=
  if tree.structural ctx.inventory then
    let conflict := anyConflict ctx tree
    if anyNegative ctx tree then ⟨.rejected, conflict⟩
    else if allLicensed ctx tree then ⟨.conditionalLicensed, conflict⟩
    else ⟨.pending, conflict⟩
  else ⟨.invalid, false⟩

/-- The proof object has a base case and a distinct step for every operation.
Local structural conditions are used to *derive* the global source invariant.
They do not assume that invariant at every composite node. -/
inductive Licensed [DecidableEq α] (ctx : Context α) : Tree α → Prop where
  | atom (source : UnitDiscovery.Source α) (before : List α) (value : α) (after : List α)
      (entry : (Tree.atom source before value after).entry ctx.inventory = true) :
      Licensed ctx (.atom source before value after)
  | join (tag : Tag) (left right : Tree α)
      (leftLicensed : Licensed ctx left) (rightLicensed : Licensed ctx right)
      (entry : (Tree.join tag left right).entry ctx.inventory = true)
      (premises : localLicensed ctx (.join tag left right) = true) :
      Licensed ctx (.join tag left right)
  | wrap (tag : Tag) (child : Tree α) (childLicensed : Licensed ctx child)
      (premises : localLicensed ctx (.wrap tag child) = true) :
      Licensed ctx (.wrap tag child)
  | substitute (tag : Tag) (replacement : List α) (child : Tree α)
      (childLicensed : Licensed ctx child)
      (entry : (Tree.substitute tag replacement child).entry ctx.inventory = true)
      (premises : localLicensed ctx (.substitute tag replacement child) = true) :
      Licensed ctx (.substitute tag replacement child)
  | lift (tag : Tag) (child : Tree α) (childLicensed : Licensed ctx child)
      (entry : (Tree.lift tag child).entry ctx.inventory = true)
      (premises : localLicensed ctx (.lift tag child) = true) :
      Licensed ctx (.lift tag child)

theorem acceptsReceipt_iff [DecidableEq α] (ctx : Context α) (target : Tree α)
    (receipt : Receipt α) : acceptsReceipt ctx target receipt = true ↔
      receipt.target = target ∧ receipt ∈ ctx.interpreted ∧ receipt.supports ≠ [] ∧
        ∀ support ∈ receipt.supports,
          support.source ∈ ctx.inventory ∧ UnitDiscovery.ValidSpan support.source support.span := by
  simp [acceptsReceipt, UnitDiscovery.validSupport, UnitDiscovery.validSpan,
    List.all_eq_true, and_assoc]

theorem foreign_target_not_accepted [DecidableEq α] (ctx : Context α)
    (target : Tree α) (receipt : Receipt α) (foreign : receipt.target ≠ target) :
    acceptsReceipt ctx target receipt = false := by
  simp [acceptsReceipt, foreign]

theorem uninterpreted_not_accepted [DecidableEq α] (ctx : Context α)
    (target : Tree α) (receipt : Receipt α) (absent : receipt ∉ ctx.interpreted) :
    acceptsReceipt ctx target receipt = false := by
  simp [acceptsReceipt, absent]

theorem mem_admitted_iff [DecidableEq α] (ctx : Context α)
    (target : Tree α) (receipt : Receipt α) : receipt ∈ admitted ctx target ↔
      receipt ∈ ctx.offered ∧ acceptsReceipt ctx target receipt = true := by
  simp [admitted]

theorem mem_negativeAdmitted_iff [DecidableEq α] (ctx : Context α)
    (target : Tree α) (receipt : Receipt α) : receipt ∈ negativeAdmitted ctx target ↔
      receipt ∈ ctx.interpreted ∧ acceptsReceipt ctx target receipt = true ∧
        receipt.positive = false := by
  simp [negativeAdmitted]

theorem negative_ledger_independent_of_offered [DecidableEq α] (ctx : Context α)
    (offered : List (Receipt α)) (target : Tree α) :
    negativeAdmitted { ctx with offered := offered } target = negativeAdmitted ctx target := by
  rfl

theorem supported_iff (receipts : List (Receipt α)) (requirement : Nat)
    (positive : Bool) : supported receipts requirement positive = true ↔
      ∃ receipt ∈ receipts, receipt.requirement = requirement ∧ receipt.positive = positive := by
  simp [supported, List.any_eq_true]

theorem localLicensed_iff [DecidableEq α] (ctx : Context α) (tree : Tree α) :
    localLicensed ctx tree = true ↔
      localNegative ctx tree = false ∧ localPositive ctx tree = true := by
  simp [localLicensed]

theorem allLicensed_no_negative [DecidableEq α] (ctx : Context α) (tree : Tree α)
    (all : allLicensed ctx tree = true) : anyNegative ctx tree = false := by
  apply List.any_eq_false.mpr
  intro step member
  have locally :=  List.all_eq_true.mp all step member
  simpa using ((localLicensed_iff ctx step).mp locally).1

theorem licensed_iff_structure_and_premises [DecidableEq α] (ctx : Context α)
    (tree : Tree α) : Licensed ctx tree ↔
      tree.structural ctx.inventory = true ∧ allLicensed ctx tree = true := by
  induction tree with
  | atom source before value after =>
    constructor
    · intro licensed
      cases licensed with
      | atom _ _ _ _ entry => simpa [Tree.structural, allLicensed, Tree.steps] using entry
    · intro valid
      exact .atom source before value after valid.1
  | join tag left right leftIH rightIH =>
    constructor
    · intro licensed
      cases licensed with
      | join _ _ _ leftLicensed rightLicensed entry premises =>
        obtain ⟨leftStructure, leftPremises⟩ := leftIH.mp leftLicensed
        obtain ⟨rightStructure, rightPremises⟩ := rightIH.mp rightLicensed
        simp [Tree.structural, allLicensed, Tree.steps] at *
        exact ⟨⟨⟨entry, leftStructure⟩, rightStructure⟩, ⟨premises, leftPremises, rightPremises⟩⟩
    · intro valid
      simp only [Tree.structural, Bool.and_eq_true, allLicensed, Tree.steps,
        List.all_cons, List.all_append] at valid
      exact .join tag left right (leftIH.mpr ⟨valid.1.1.2, valid.2.2.1⟩)
        (rightIH.mpr ⟨valid.1.2, valid.2.2.2⟩) valid.1.1.1 valid.2.1
  | wrap tag child childIH =>
    constructor
    · intro licensed
      cases licensed with
      | wrap _ _ childLicensed premises =>
        obtain ⟨structuralOk, all⟩ := childIH.mp childLicensed
        simpa [Tree.structural, Tree.entry, allLicensed, Tree.steps, structuralOk, premises] using all
    · intro valid
      simp only [Tree.structural, Tree.entry, Bool.true_and, allLicensed, Tree.steps,
        List.all_cons, Bool.and_eq_true] at valid
      exact .wrap tag child (childIH.mpr ⟨valid.1, valid.2.2⟩) valid.2.1
  | substitute tag replacement child childIH =>
    constructor
    · intro licensed
      cases licensed with
      | substitute _ _ _ childLicensed entry premises =>
        obtain ⟨structuralOk, all⟩ := childIH.mp childLicensed
        simp [Tree.structural, allLicensed, Tree.steps, structuralOk, entry, premises] at *
        exact all
    · intro valid
      simp only [Tree.structural, allLicensed, Tree.steps, List.all_cons,
        Bool.and_eq_true] at valid
      exact .substitute tag replacement child (childIH.mpr ⟨valid.1.2, valid.2.2⟩)
        valid.1.1 valid.2.1
  | lift tag child childIH =>
    constructor
    · intro licensed
      cases licensed with
      | lift _ _ childLicensed entry premises =>
        obtain ⟨structuralOk, all⟩ := childIH.mp childLicensed
        simp [Tree.structural, allLicensed, Tree.steps, structuralOk, entry, premises] at *
        exact all
    · intro valid
      simp only [Tree.structural, allLicensed, Tree.steps, List.all_cons,
        Bool.and_eq_true] at valid
      exact .lift tag child (childIH.mpr ⟨valid.1.2, valid.2.2⟩) valid.1.1 valid.2.1

theorem assess_licensed_iff [DecidableEq α] (ctx : Context α) (tree : Tree α) :
    (assess ctx tree).status = .conditionalLicensed ↔ Licensed ctx tree := by
  rw [licensed_iff_structure_and_premises]
  by_cases structuralOk : tree.structural ctx.inventory = true
  · by_cases all : allLicensed ctx tree = true
    · have negative := allLicensed_no_negative ctx tree all
      simp [assess, structuralOk, negative, all]
    · simp [assess, structuralOk, all]
      split <;> simp
  · simp [assess, structuralOk]

theorem rejected_not_licensed [DecidableEq α] (ctx : Context α) (tree : Tree α)
    (rejected : (assess ctx tree).status = .rejected) : ¬ Licensed ctx tree := by
  intro licensed
  have accepted := (assess_licensed_iff ctx tree).mpr licensed
  rw [rejected] at accepted
  cases accepted

theorem known_negative_cannot_be_hidden_by_offered [DecidableEq α]
    (ctx : Context α) (tree step : Tree α) (receipt : Receipt α)
    (structureOk : tree.structural ctx.inventory = true) (member : step ∈ tree.steps)
    (accepted : acceptsReceipt ctx step receipt = true)
    (needed : receipt.requirement ∈ step.required) (negative : receipt.positive = false) :
    (assess ctx tree).status = .rejected := by
  have interpreted := ((acceptsReceipt_iff ctx step receipt).mp accepted).2.1
  have admittedNegative := (mem_negativeAdmitted_iff ctx step receipt).mpr
    ⟨interpreted, accepted, negative⟩
  have supportedNegative := (supported_iff (negativeAdmitted ctx step) receipt.requirement false).mpr
    ⟨receipt, admittedNegative, rfl, negative⟩
  have stepNegative : localNegative ctx step = true :=
    List.any_eq_true.mpr ⟨receipt.requirement, needed, supportedNegative⟩
  have treeNegative : anyNegative ctx tree = true :=
    List.any_eq_true.mpr ⟨step, member, stepNegative⟩
  simp [assess, structureOk, treeNegative]

theorem invalid_iff_structure [DecidableEq α] (ctx : Context α) (tree : Tree α) :
    (assess ctx tree).status = .invalid ↔ tree.structural ctx.inventory = false := by
  cases structuralOk : tree.structural ctx.inventory <;>
    cases negative : anyNegative ctx tree <;>
      cases all : allLicensed ctx tree <;> simp [assess, structuralOk, negative, all]

theorem rejected_iff_negative [DecidableEq α] (ctx : Context α) (tree : Tree α) :
    (assess ctx tree).status = .rejected ↔
      tree.structural ctx.inventory = true ∧ anyNegative ctx tree = true := by
  cases structuralOk : tree.structural ctx.inventory <;>
    cases negative : anyNegative ctx tree <;>
      cases all : allLicensed ctx tree <;> simp [assess, structuralOk, negative, all]

theorem pending_iff_missing [DecidableEq α] (ctx : Context α) (tree : Tree α) :
    (assess ctx tree).status = .pending ↔
      tree.structural ctx.inventory = true ∧ anyNegative ctx tree = false ∧
        allLicensed ctx tree = false := by
  cases structuralOk : tree.structural ctx.inventory <;>
    cases negative : anyNegative ctx tree <;>
      cases all : allLicensed ctx tree <;> simp [assess, structuralOk, negative, all]

theorem conflict_rejects [DecidableEq α] (ctx : Context α) (tree : Tree α)
    (conflict : (assess ctx tree).conflict = true) : (assess ctx tree).status = .rejected := by
  have structureOk : tree.structural ctx.inventory = true := by
    cases structuralResult : tree.structural ctx.inventory with
    | false => simp [assess, structuralResult] at conflict
    | true => rfl
  have knownConflict : anyConflict ctx tree = true := by
    cases negative : anyNegative ctx tree <;>
      cases all : allLicensed ctx tree <;> simpa [assess, structureOk, negative, all] using conflict
  obtain ⟨step, member, conflicted⟩ := List.any_eq_true.mp knownConflict
  obtain ⟨requirement, needed, both⟩ := List.any_eq_true.mp conflicted
  have stepNegative : localNegative ctx step = true :=
    List.any_eq_true.mpr ⟨requirement, needed, (Bool.and_eq_true_iff.mp both).2⟩
  have negative : anyNegative ctx tree = true := List.any_eq_true.mpr ⟨step, member, stepNegative⟩
  exact (rejected_iff_negative ctx tree).mpr ⟨structureOk, negative⟩

theorem licensed_source_member [DecidableEq α] (ctx : Context α) (tree : Tree α)
    (licensed : Licensed ctx tree) : tree.source ∈ ctx.inventory := by
  induction licensed with
  | atom source before value after entry =>
    exact (of_decide_eq_true entry).1
  | join _ _ _ _ _ _ _ leftIH _ => exact leftIH
  | wrap _ _ _ _ childIH => exact childIH
  | substitute _ _ _ _ _ _ childIH => exact childIH
  | lift _ _ _ _ _ childIH => exact childIH

theorem licensed_reconstruct [DecidableEq α] (ctx : Context α) (tree : Tree α)
    (licensed : Licensed ctx tree) : tree.reconstruct = tree.source.atoms := by
  induction licensed with
  | atom source before value after entry =>
    exact (of_decide_eq_true entry).2.symm
  | join tag left right _ _ entry _ leftIH _ =>
    have boundary : left.after = right.raw ++ right.after := (of_decide_eq_true entry).2.2
    simpa [Tree.reconstruct, Tree.before, Tree.raw, Tree.after, Tree.source,
      boundary, List.append_assoc] using leftIH
  | wrap _ _ _ _ childIH => exact childIH
  | substitute _ _ _ _ _ _ childIH => exact childIH
  | lift _ _ _ _ _ childIH => exact childIH

theorem licensed_raw_nonempty [DecidableEq α] (ctx : Context α) (tree : Tree α)
    (licensed : Licensed ctx tree) : tree.raw ≠ [] := by
  induction licensed with
  | atom => simp [Tree.raw]
  | join _ _ _ _ _ _ _ leftIH _ =>
    intro impossible
    exact leftIH (List.append_eq_nil_iff.mp impossible).1
  | wrap _ _ _ _ childIH => exact childIH
  | substitute _ _ _ _ _ _ childIH => exact childIH
  | lift _ _ _ _ _ childIH => exact childIH

theorem licensed_bounds [DecidableEq α] (ctx : Context α) (tree : Tree α)
    (licensed : Licensed ctx tree) :
    tree.start < tree.stop ∧ tree.stop ≤ tree.source.atoms.length := by
  have lengths := congrArg List.length (licensed_reconstruct ctx tree licensed)
  have nonempty := List.length_pos_iff.mpr (licensed_raw_nonempty ctx tree licensed)
  simp only [Tree.reconstruct, List.length_append] at lengths
  dsimp [Tree.start, Tree.stop]
  omega

theorem licensed_join_original_adjacency [DecidableEq α] (ctx : Context α)
    (tag : Tag) (left right : Tree α) (licensed : Licensed ctx (.join tag left right)) :
    left.source = right.source ∧ left.stop = right.start := by
  cases licensed with
  | join _ _ _ _ _ entry _ =>
    obtain ⟨same, boundary, _⟩ := of_decide_eq_true entry
    refine ⟨same, ?_⟩
    simp [Tree.stop, Tree.start, boundary]

theorem licensed_premises_retained [DecidableEq α] (ctx : Context α) (tree : Tree α)
    (licensed : Licensed ctx tree) (step : Tree α) (member : step ∈ tree.steps)
    (requirement : Nat) (needed : requirement ∈ step.required) :
    ∃ receipt ∈ ctx.offered, receipt ∈ ctx.interpreted ∧ receipt.target = step ∧
      receipt.requirement = requirement ∧ receipt.positive = true ∧ receipt.supports ≠ [] ∧
      ∀ support ∈ receipt.supports,
        support.source ∈ ctx.inventory ∧ UnitDiscovery.ValidSpan support.source support.span := by
  have all := (licensed_iff_structure_and_premises ctx tree).mp licensed |>.2
  have locally :=  List.all_eq_true.mp all step member
  have positive := ((localLicensed_iff ctx step).mp locally).2
  have support := List.all_eq_true.mp positive requirement needed
  obtain ⟨receipt, admitted, requirementEq, polarity⟩ := (supported_iff _ _ _).mp support
  obtain ⟨offered, accepted⟩ := (mem_admitted_iff ctx step receipt).mp admitted
  obtain ⟨target, interpreted, nonempty, valid⟩ := (acceptsReceipt_iff ctx step receipt).mp accepted
  exact ⟨receipt, offered, interpreted, target, requirementEq, polarity, nonempty, valid⟩

theorem no_offered_composite_license [DecidableEq α] (ctx : Context α) (tree : Tree α)
    (empty : ctx.offered = []) (composite : tree ∈ tree.steps) (mandatory : 0 ∈ tree.required) :
    ¬ Licensed ctx tree := by
  intro licensed
  obtain ⟨receipt, member, _⟩ :=
    licensed_premises_retained ctx tree licensed tree composite 0 mandatory
  simp [empty] at member

theorem join_rank_left (tag : Tag) (left right : Tree α) :
    left.rank < (Tree.join tag left right).rank := by
  have := Nat.le_max_left left.rank right.rank
  simp only [Tree.rank]
  omega

theorem join_rank_right (tag : Tag) (left right : Tree α) :
    right.rank < (Tree.join tag left right).rank := by
  have := Nat.le_max_right left.rank right.rank
  simp only [Tree.rank]
  omega

theorem wrap_rank (tag : Tag) (child : Tree α) : child.rank < (Tree.wrap tag child).rank := by
  simp [Tree.rank]

theorem substitute_rank (tag : Tag) (replacement : List α) (child : Tree α) :
    child.rank < (Tree.substitute tag replacement child).rank := by
  simp [Tree.rank]

theorem lift_rank (tag : Tag) (child : Tree α) : child.rank < (Tree.lift tag child).rank := by
  simp [Tree.rank]

theorem trace_rank_bounded (tree : Tree α) (step : Tree α) (member : step ∈ tree.steps) :
    step.rank ≤ tree.rank := by
  induction tree with
  | atom => simp [Tree.steps] at member
  | join tag left right leftIH rightIH =>
    simp only [Tree.steps, List.mem_cons, List.mem_append] at member
    rcases member with rfl | member | member
    · exact Nat.le_refl _
    · exact Nat.le_trans (leftIH member) (Nat.le_of_lt (join_rank_left tag left right))
    · exact Nat.le_trans (rightIH member) (Nat.le_of_lt (join_rank_right tag left right))
  | wrap tag child childIH =>
    simp only [Tree.steps, List.mem_cons] at member
    rcases member with rfl | member
    · exact Nat.le_refl _
    · exact Nat.le_trans (childIH member) (Nat.le_of_lt (wrap_rank tag child))
  | substitute tag replacement child childIH =>
    simp only [Tree.steps, List.mem_cons] at member
    rcases member with rfl | member
    · exact Nat.le_refl _
    · exact Nat.le_trans (childIH member) (Nat.le_of_lt (substitute_rank tag replacement child))
  | lift tag child childIH =>
    simp only [Tree.steps, List.mem_cons] at member
    rcases member with rfl | member
    · exact Nat.le_refl _
    · exact Nat.le_trans (childIH member) (Nat.le_of_lt (lift_rank tag child))

theorem undo_output [DecidableEq α] (tree : Tree α) :
    tree.undo tree.output = some tree.raw := by
  induction tree with
  | atom => simp [Tree.undo, Tree.output, Tree.raw]
  | join tag left right leftIH rightIH =>
    simp [Tree.undo, Tree.output, Tree.raw, leftIH, rightIH]
  | wrap tag child childIH => exact childIH
  | substitute tag replacement child childIH =>
    simpa [Tree.undo, Tree.output, Tree.raw] using childIH
  | lift tag child childIH => exact childIH

theorem undo_exact [DecidableEq α] (tree : Tree α) (seen restored : List α) :
    tree.undo seen = some restored ↔ seen = tree.output ∧ restored = tree.raw := by
  induction tree generalizing seen restored with
  | atom source before value after =>
    by_cases same : seen = [value]
    · simp [Tree.undo, Tree.output, Tree.raw, same, eq_comm]
    · simp [Tree.undo, Tree.output, Tree.raw, same]
  | join tag left right leftIH rightIH =>
    constructor
    · intro accepted
      simp only [Tree.undo] at accepted
      split at accepted
      next _ =>
        cases leftResult : left.undo (seen.take left.output.length) with
        | none => simp [leftResult] at accepted
        | some leftRestored =>
          cases rightResult : right.undo (seen.drop left.output.length) with
          | none => simp [leftResult, rightResult] at accepted
          | some rightRestored =>
            have leftExact := (leftIH _ _).mp leftResult
            have rightExact := (rightIH _ _).mp rightResult
            have restoredExact : leftRestored ++ rightRestored = restored := by
              simpa [leftResult, rightResult] using accepted
            constructor
            · show seen = left.output ++ right.output
              calc
                seen = seen.take left.output.length ++ seen.drop left.output.length :=
                  (List.take_append_drop left.output.length seen).symm
                _ = left.output ++ right.output := by rw [leftExact.1, rightExact.1]
            · exact restoredExact.symm.trans (by rw [leftExact.2, rightExact.2]; rfl)
      next _ => simp at accepted
    · rintro ⟨rfl, rfl⟩
      exact undo_output (.join tag left right)
  | wrap tag child childIH => exact childIH seen restored
  | substitute tag replacement child childIH =>
    by_cases same : seen = replacement
    · simp [Tree.undo, Tree.output, Tree.raw, same, undo_output, eq_comm]
    · simp [Tree.undo, Tree.output, Tree.raw, same]
  | lift tag child childIH => exact childIH seen restored

theorem altered_output_not_restored [DecidableEq α] (tree : Tree α) (seen : List α)
    (different : seen ≠ tree.output) : tree.undo seen = none := by
  cases result : tree.undo seen with
  | none => rfl
  | some restored => exact False.elim (different ((undo_exact tree seen restored).mp result).1)

theorem licensed_undo_reconstructs_source [DecidableEq α] (ctx : Context α) (tree : Tree α)
    (licensed : Licensed ctx tree) :
    (tree.undo tree.output).map (fun restored => tree.before ++ restored ++ tree.after) =
      some tree.source.atoms := by
  rw [undo_output]
  exact congrArg some (licensed_reconstruct ctx tree licensed)

theorem substitute_retains_raw (tag : Tag) (replacement : List α) (child : Tree α) :
    (Tree.substitute tag replacement child).raw = child.raw ∧
      (Tree.substitute tag replacement child).remainder = child.remainder := by
  exact ⟨rfl, rfl⟩

theorem unit_key_retains_source (left right : Tree α) (same : unitKey left = unitKey right) :
    left.source = right.source ∧ left.start = right.start ∧ left.raw = right.raw := by
  exact ⟨congrArg UnitKey.source same, congrArg UnitKey.start same, congrArg UnitKey.raw same⟩

theorem same_unit_distinct_derivations (tag : Tag) (child : Tree α) :
    unitKey (.wrap tag child) = unitKey (.lift tag child) ∧
      Tree.wrap tag child ≠ Tree.lift tag child := by
  constructor
  · rfl
  · intro impossible
    cases impossible

/-- A proof of necessity must quantify over the declared domain. The list
alone is not evidence of exhaustive search; `complete` is a proposition. -/
def CompleteWithin (domain : Tree α → Prop) (candidates : List (Tree α)) : Prop :=
  ∀ tree, domain tree → tree ∈ candidates

def NecessaryWithin [DecidableEq α] (ctx : Context α) (domain : Tree α → Prop)
    (chosen : Tree α) : Prop :=
  domain chosen ∧ Licensed ctx chosen ∧
    ∀ other, domain other → Licensed ctx other → other = chosen

theorem exhaustive_rejections_establish_necessity [DecidableEq α] (ctx : Context α)
    (domain : Tree α → Prop) (candidates : List (Tree α)) (chosen : Tree α)
    (complete : CompleteWithin domain candidates) (inside : domain chosen)
    (licensed : Licensed ctx chosen)
    (blocked : ∀ other ∈ candidates, other ≠ chosen → (assess ctx other).status = .rejected) :
    NecessaryWithin ctx domain chosen := by
  refine ⟨inside, licensed, ?_⟩
  intro other inDomain otherLicensed
  by_cases same : other = chosen
  · exact same
  · exact False.elim (rejected_not_licensed ctx other
      (blocked other (complete other inDomain) same) otherLicensed)

/-- If another candidate is merely pending, this stronger rejection
certificate is unavailable. Absence of a license is not its rejection. -/
theorem pending_blocks_rejection_certificate [DecidableEq α] (ctx : Context α)
    (candidates : List (Tree α)) (chosen other : Tree α) (member : other ∈ candidates)
    (different : other ≠ chosen) (pending : (assess ctx other).status = .pending) :
    ¬ (∀ candidate ∈ candidates, candidate ≠ chosen →
      (assess ctx candidate).status = .rejected) := by
  intro blocked
  have rejection := blocked other member different
  rw [pending] at rejection
  cases rejection

end Nabt.LicensedDerivation
