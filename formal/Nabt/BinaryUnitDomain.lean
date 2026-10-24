import Nabt.ProsodicUnits
import Nabt.LicensedDerivation

/-!
# A provably exhaustive finite binary source domain

The grammar below has atomic source occurrences and binary joins only, with
one fixed tag and one fixed source interval. It excludes wrapping, lifting,
substitution, alternative atomizations and unbounded linguistic acquisition.
The executable candidate list is proved complete for this independently
declared grammar. No caller-supplied `complete` flag grants that property.
-/

namespace Nabt.BinaryUnitDomain


def lawId : String := "nabt.binary-unit-domain.v1"

/-- Exact positional contexts are built into every grammar production. -/
inductive BinaryFrame (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag) :
    List α → List α → List α → LicensedDerivation.Tree α → Prop where
  | atom (before : List α) (value : α) (after : List α) :
      BinaryFrame source tag before [value] after (.atom source before value after)
  | join (before leftRaw rightRaw after : List α) (left right : LicensedDerivation.Tree α)
      (leftFrame : BinaryFrame source tag before leftRaw (rightRaw ++ after) left)
      (rightFrame : BinaryFrame source tag (before ++ leftRaw) rightRaw after right) :
      BinaryFrame source tag before (leftRaw ++ rightRaw) after (.join tag left right)

theorem frame_fields (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag)
    (before raw after : List α) (tree : LicensedDerivation.Tree α)
    (frame : BinaryFrame source tag before raw after tree) :
    tree.source = source ∧ tree.before = before ∧ tree.raw = raw ∧
      tree.output = raw ∧ tree.after = after := by
  induction frame with
  | atom => exact ⟨rfl, rfl, rfl, rfl, rfl⟩
  | join before leftRaw rightRaw after left right _ _ leftIH rightIH =>
      simp only [LicensedDerivation.Tree.source, LicensedDerivation.Tree.before, LicensedDerivation.Tree.raw, LicensedDerivation.Tree.output, LicensedDerivation.Tree.after]
      exact ⟨leftIH.1, leftIH.2.1, by rw [leftIH.2.2.1, rightIH.2.2.1],
        by rw [leftIH.2.2.2.1, rightIH.2.2.2.1], rightIH.2.2.2.2⟩

theorem frame_nonempty (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag)
    (before raw after : List α) (tree : LicensedDerivation.Tree α)
    (frame : BinaryFrame source tag before raw after tree) : raw ≠ [] := by
  induction frame with
  | atom => simp
  | join before leftRaw rightRaw after left right _ _ leftIH _ => simp [leftIH]

/-- Slots indicate tree structure only. The actual leaf values are taken
from the complete raw interval, never copied from a pattern or gold label. -/
def instantiateFrame (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag)
    (before raw after : List α) : ProsodicUnits.UnitTree → Option (LicensedDerivation.Tree α)
  | .atom _ =>
      match raw with
      | [value] => some (.atom source before value after)
      | _ => none
  | .join left right => do
      let cut := left.flatten.length
      let l ← instantiateFrame source tag before (raw.take cut) (raw.drop cut ++ after) left
      let r ← instantiateFrame source tag (before ++ raw.take cut) (raw.drop cut) after right
      pure (.join tag l r)

theorem instantiateFrame_sound (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag)
    (before raw after : List α) (skeleton : ProsodicUnits.UnitTree) (tree : LicensedDerivation.Tree α)
    (built : instantiateFrame source tag before raw after skeleton = some tree) :
    BinaryFrame source tag before raw after tree := by
  induction skeleton generalizing before raw after tree with
  | atom slot =>
      cases raw with
      | nil => simp [instantiateFrame] at built
      | cons value rest =>
          cases rest with
          | nil =>
              simp only [instantiateFrame, Option.some.injEq] at built
              subst tree
              exact .atom before value after
          | cons next tail => simp [instantiateFrame] at built
  | join left right leftIH rightIH =>
      cases leftResult : instantiateFrame source tag before
        (raw.take left.flatten.length) (raw.drop left.flatten.length ++ after) left with
      | none => simp [instantiateFrame, leftResult] at built
      | some l =>
          cases rightResult : instantiateFrame source tag
            (before ++ raw.take left.flatten.length) (raw.drop left.flatten.length) after right with
          | none => simp [instantiateFrame, leftResult, rightResult] at built
          | some r =>
              have same : LicensedDerivation.Tree.join tag l r = tree := by
                simpa [instantiateFrame, leftResult, rightResult] using built
              subst tree
              have joined := BinaryFrame.join before (raw.take left.flatten.length)
                (raw.drop left.flatten.length) after l r
                (leftIH _ _ _ _ leftResult) (rightIH _ _ _ _ rightResult)
              simpa only [List.take_append_drop] using joined

theorem frame_has_skeleton (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag)
    (before raw after : List α) (tree : LicensedDerivation.Tree α)
    (frame : BinaryFrame source tag before raw after tree) :
    ∃ skeleton : ProsodicUnits.UnitTree,
      skeleton.flatten = List.replicate raw.length ProsodicUnits.Slot.c ∧
      instantiateFrame source tag before raw after skeleton = some tree := by
  induction frame with
  | atom before value after =>
      exact ⟨.atom .c, rfl, rfl⟩
  | join before leftRaw rightRaw after left right _ _ leftIH rightIH =>
      obtain ⟨leftSkeleton, leftShape, leftBuild⟩ := leftIH
      obtain ⟨rightSkeleton, rightShape, rightBuild⟩ := rightIH
      have cut : leftSkeleton.flatten.length = leftRaw.length := by simp [leftShape]
      refine ⟨.join leftSkeleton rightSkeleton, ?_, ?_⟩
      · simp [ProsodicUnits.UnitTree.flatten, leftShape, rightShape]
      · simp [instantiateFrame, cut, leftBuild, rightBuild]

theorem frame_structural [DecidableEq α] (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag)
    (before raw after : List α) (tree : LicensedDerivation.Tree α)
    (frame : BinaryFrame source tag before raw after tree)
    (replay : source.atoms = before ++ raw ++ after)
    (inventory : List (UnitDiscovery.Source α)) (present : source ∈ inventory) :
    tree.structural inventory = true := by
  induction frame with
  | atom before value after => simp [LicensedDerivation.Tree.structural, LicensedDerivation.Tree.entry, replay, present]
  | join before leftRaw rightRaw after left right leftFrame rightFrame leftIH rightIH =>
      have leftFields := frame_fields source tag _ _ _ left leftFrame
      have rightFields := frame_fields source tag _ _ _ right rightFrame
      have leftReplay : source.atoms = before ++ leftRaw ++ (rightRaw ++ after) := by
        simpa [List.append_assoc] using replay
      have rightReplay : source.atoms = (before ++ leftRaw) ++ rightRaw ++ after := by
        simpa [List.append_assoc] using replay
      simp [LicensedDerivation.Tree.structural, LicensedDerivation.Tree.entry, leftFields.1, rightFields.1,
        leftFields.2.1, rightFields.2.1, leftFields.2.2.1, rightFields.2.2.1,
        leftFields.2.2.2.2, rightFields.2.2.2.2, leftIH leftReplay, rightIH rightReplay]

/-- Value-based deduplication is independent of proof/receipt multiplicity. -/
def distinct [DecidableEq α] : List α → List α
  | [] => []
  | value :: rest => if value ∈ rest then distinct rest else value :: distinct rest

theorem mem_distinct [DecidableEq α] (value : α) (items : List α) :
    value ∈ distinct items ↔ value ∈ items := by
  induction items with
  | nil => simp [distinct]
  | cons head rest ih =>
      by_cases repeated : head ∈ rest
      · simp only [distinct, repeated, ↓reduceIte, ih, List.mem_cons]
        constructor
        · exact Or.inr
        · rintro (rfl | member)
          · exact repeated
          · exact member
      · simp [distinct, repeated, ih]

theorem distinct_nodup [DecidableEq α] (items : List α) : (distinct items).Nodup := by
  induction items with
  | nil => simp [distinct]
  | cons value rest ih =>
      by_cases repeated : value ∈ rest
      · simp [distinct, repeated, ih]
      · simp [distinct, repeated, List.nodup_cons, mem_distinct, ih]

def frameCandidates [DecidableEq α] (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag)
    (before raw after : List α) : List (LicensedDerivation.Tree α) :=
  distinct ((ProsodicUnits.allTrees (List.replicate raw.length ProsodicUnits.Slot.c)).filterMap
    (instantiateFrame source tag before raw after))

theorem mem_frameCandidates_iff [DecidableEq α] (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag)
    (before raw after : List α) (tree : LicensedDerivation.Tree α) :
    tree ∈ frameCandidates source tag before raw after ↔
      BinaryFrame source tag before raw after tree := by
  simp only [frameCandidates, mem_distinct, List.mem_filterMap]
  constructor
  · rintro ⟨skeleton, _, built⟩
    exact instantiateFrame_sound source tag before raw after skeleton tree built
  · intro frame
    obtain ⟨skeleton, shape, built⟩ := frame_has_skeleton source tag before raw after tree frame
    exact ⟨skeleton, (ProsodicUnits.allTrees_exact _ _).mpr shape, built⟩

def intervalRaw (source : UnitDiscovery.Source α) (start length : Nat) : List α :=
  (source.atoms.drop start).take length

def Within (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag)
    (start length : Nat) (tree : LicensedDerivation.Tree α) : Prop :=
  0 < length ∧ start + length ≤ source.atoms.length ∧
    BinaryFrame source tag (source.atoms.take start) (intervalRaw source start length)
      (source.atoms.drop (start + length)) tree

def candidates [DecidableEq α] (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag)
    (start length : Nat) : List (LicensedDerivation.Tree α) :=
  if 0 < length ∧ start + length ≤ source.atoms.length then
    frameCandidates source tag (source.atoms.take start) (intervalRaw source start length)
      (source.atoms.drop (start + length))
  else []

def instantiate (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag)
    (start : Nat) (skeleton : ProsodicUnits.UnitTree) : Option (LicensedDerivation.Tree α) :=
  let length := skeleton.flatten.length
  if start + length ≤ source.atoms.length then
    instantiateFrame source tag (source.atoms.take start) (intervalRaw source start length)
      (source.atoms.drop (start + length)) skeleton
  else none

theorem mem_candidates_iff [DecidableEq α] (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag)
    (start length : Nat) (tree : LicensedDerivation.Tree α) :
    tree ∈ candidates source tag start length ↔ Within source tag start length tree := by
  by_cases valid : 0 < length ∧ start + length ≤ source.atoms.length
  · simp [candidates, valid, mem_frameCandidates_iff, Within]
  · simp only [candidates, valid, ↓reduceIte, List.not_mem_nil, Within]
    constructor
    · exact False.elim
    · intro inside
      exact valid ⟨inside.1, inside.2.1⟩

theorem candidates_complete [DecidableEq α] (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag)
    (start length : Nat) :
    LicensedDerivation.CompleteWithin (Within source tag start length) (candidates source tag start length) :=
  fun tree inside => (mem_candidates_iff source tag start length tree).mpr inside

theorem candidates_nodup [DecidableEq α] (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag)
    (start length : Nat) : (candidates source tag start length).Nodup := by
  simp only [candidates]
  split
  · exact distinct_nodup _
  · simp

theorem interval_reconstructs (source : UnitDiscovery.Source α) (start length : Nat) :
    source.atoms.take start ++ intervalRaw source start length ++
      source.atoms.drop (start + length) = source.atoms := by
  rw [intervalRaw, List.append_assoc, ← List.drop_drop, List.take_append_drop,
    List.take_append_drop]

theorem candidate_structural [DecidableEq α] (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag)
    (start length : Nat) (tree : LicensedDerivation.Tree α)
    (member : tree ∈ candidates source tag start length)
    (inventory : List (UnitDiscovery.Source α)) (present : source ∈ inventory) :
    tree.structural inventory = true := by
  have frame := ((mem_candidates_iff source tag start length tree).mp member).2.2
  exact frame_structural source tag _ _ _ tree frame
    (interval_reconstructs source start length).symm inventory present

/-- A list-level certificate requires one licensed candidate and explicit
rejection of every distinct rival. Pending/invalid rivals prevent it. -/
def uniqueWithin [DecidableEq α] (ctx : LicensedDerivation.Context α) (trees : List (LicensedDerivation.Tree α)) :
    Option (LicensedDerivation.Tree α) :=
  let unique := distinct trees
  match unique.filter (fun tree => decide ((LicensedDerivation.assess ctx tree).status = .conditionalLicensed)) with
  | [chosen] =>
      if unique.all (fun other => decide (other = chosen ∨ (LicensedDerivation.assess ctx other).status = .rejected))
      then some chosen else none
  | _ => none

theorem uniqueWithin_sound [DecidableEq α] (ctx : LicensedDerivation.Context α) (trees : List (LicensedDerivation.Tree α))
    (chosen : LicensedDerivation.Tree α) (selected : uniqueWithin ctx trees = some chosen) :
    chosen ∈ trees ∧ LicensedDerivation.Licensed ctx chosen ∧
      ∀ other ∈ trees, other ≠ chosen → (LicensedDerivation.assess ctx other).status = .rejected := by
  dsimp only [uniqueWithin] at selected
  split at selected
  next found singleton =>
    split at selected
    next blocked =>
      have same : found = chosen := Option.some.inj selected
      subst chosen
      have member : found ∈ (distinct trees).filter
          (fun tree => decide ((LicensedDerivation.assess ctx tree).status = .conditionalLicensed)) := by
        rw [singleton]
        simp
      have supported := List.mem_filter.mp member
      refine ⟨(mem_distinct _ _).mp supported.1,
        (LicensedDerivation.assess_licensed_iff ctx found).mp (of_decide_eq_true supported.2), ?_⟩
      intro other inTrees different
      have either := (List.all_eq_true.mp blocked) other ((mem_distinct _ _).mpr inTrees)
      exact (of_decide_eq_true either).resolve_left different
    next => simp at selected
  next => simp at selected

private theorem singleton_of_unique_member (items : List α) (chosen : α)
    (present : chosen ∈ items) (unique : items.Nodup)
    (only : ∀ value ∈ items, value = chosen) : items = [chosen] := by
  cases items with
  | nil => simp at present
  | cons head rest =>
      have same := only head (by simp)
      subst head
      cases rest with
      | nil => rfl
      | cons next tail =>
          have nextSame := only next (by simp)
          subst next
          simp at unique

theorem uniqueWithin_complete [DecidableEq α] (ctx : LicensedDerivation.Context α)
    (trees : List (LicensedDerivation.Tree α)) (chosen : LicensedDerivation.Tree α)
    (member : chosen ∈ trees) (licensed : LicensedDerivation.Licensed ctx chosen)
    (blocked : ∀ other ∈ trees, other ≠ chosen →
      (LicensedDerivation.assess ctx other).status = .rejected) :
    uniqueWithin ctx trees = some chosen := by
  let accepted := (distinct trees).filter (fun tree =>
    decide ((LicensedDerivation.assess ctx tree).status = .conditionalLicensed))
  have chosenAccepted : chosen ∈ accepted := by
    apply List.mem_filter.mpr
    exact ⟨(mem_distinct chosen trees).mpr member,
      by simp [(LicensedDerivation.assess_licensed_iff ctx chosen).mpr licensed]⟩
  have only : ∀ other ∈ accepted, other = chosen := by
    intro other inAccepted
    have supported := List.mem_filter.mp inAccepted
    by_cases same : other = chosen
    · exact same
    · have otherLicensed := (LicensedDerivation.assess_licensed_iff ctx other).mp
        (of_decide_eq_true supported.2)
      exact False.elim (LicensedDerivation.rejected_not_licensed ctx other
        (blocked other ((mem_distinct _ _).mp supported.1) same) otherLicensed)
  have singleton : accepted = [chosen] :=
    singleton_of_unique_member accepted chosen chosenAccepted
      ((distinct_nodup trees).filter _) only
  have allBlocked : (distinct trees).all (fun other =>
      decide (other = chosen ∨ (LicensedDerivation.assess ctx other).status = .rejected)) = true := by
    apply List.all_eq_true.mpr
    intro other inside
    apply decide_eq_true
    by_cases same : other = chosen
    · exact Or.inl same
    · exact Or.inr (blocked other ((mem_distinct _ _).mp inside) same)
  dsimp only [accepted] at singleton
  simp only [uniqueWithin, singleton, allBlocked, ↓reduceIte]

theorem uniqueWithin_iff [DecidableEq α] (ctx : LicensedDerivation.Context α)
    (trees : List (LicensedDerivation.Tree α)) (chosen : LicensedDerivation.Tree α) :
    uniqueWithin ctx trees = some chosen ↔
      chosen ∈ trees ∧ LicensedDerivation.Licensed ctx chosen ∧
      ∀ other ∈ trees, other ≠ chosen → (LicensedDerivation.assess ctx other).status = .rejected :=
  ⟨uniqueWithin_sound ctx trees chosen,
    fun proof => uniqueWithin_complete ctx trees chosen proof.1 proof.2.1 proof.2.2⟩

theorem generated_necessity [DecidableEq α] (ctx : LicensedDerivation.Context α)
    (source : UnitDiscovery.Source α) (tag : LicensedDerivation.Tag) (start length : Nat)
    (chosen : LicensedDerivation.Tree α)
    (selected : uniqueWithin ctx (candidates source tag start length) = some chosen) :
    LicensedDerivation.NecessaryWithin ctx (Within source tag start length) chosen := by
  obtain ⟨member, licensed, blocked⟩ := uniqueWithin_sound ctx _ chosen selected
  exact LicensedDerivation.exhaustive_rejections_establish_necessity ctx _ _ chosen
    (candidates_complete source tag start length)
    ((mem_candidates_iff source tag start length chosen).mp member) licensed blocked

end Nabt.BinaryUnitDomain
