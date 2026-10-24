import Nabt.Cell
import Nabt.Count
import Nabt.UnitDiscovery

/-!
# Ordered sound-shape proposals, reusable identities, and explicit quantity

The alphabet `C/V` is declared, not learned. Enumeration exhausts finite
ordered strings with given counts; it does not license an Arabic syllable.
An injective base-two address names the whole ordered shape, independently
of its derivation. Multiple partitions and binary groupings remain available.

The 116 A116 cells are carrier/mark pairs. The 29 sukun-marked cells have no
following short-vowel mark; a contextual reading can still assign a weak
carrier a vowel-extension role. No cell-to-phoneme reader is assumed here.
Long quantity is explicit, source-aligned interpreted evidence. `VV` alone
does not identify one long vowel rather than two short vowels.
-/

namespace Nabt.ProsodicUnits

def lawId : String := "nabt.prosodic-unit-proposals.v1"
def alphabetId : String := "nabt.ordered-cv.v1"
def quantityScope : String := "conditional on supplied source-aligned interpretations"

inductive Slot where
  | c
  | v
  deriving DecidableEq, Repr, BEq

abbrev Shape := List Slot

def slotValue : Slot → Nat
  | .c => 0
  | .v => 1

def bitSlot (n : Nat) : Slot := if n % 2 = 0 then .c else .v

theorem slotValue_lt_two (s : Slot) : slotValue s < 2 := by
  cases s <;> decide

theorem bitSlot_slotValue (s : Slot) : bitSlot (slotValue s) = s := by
  cases s <;> decide

theorem slotValue_bitSlot (n : Nat) : slotValue (bitSlot n) = n % 2 := by
  have bound := Nat.mod_lt n (by decide : 0 < 2)
  by_cases zero : n % 2 = 0
  · simp [bitSlot, zero, slotValue]
  · have one : n % 2 = 1 := by omega
    simp [bitSlot, one, slotValue]

def shapeLittle : Shape → Nat
  | [] => 0
  | s :: rest => 1 + slotValue s + 2 * shapeLittle rest

def shapeDecodeAux : Nat → Nat → Shape
  | 0, _ => []
  | fuel + 1, n =>
      if n = 0 then []
      else bitSlot (n - 1) :: shapeDecodeAux fuel ((n - 1) / 2)

def shapeEncode (shape : Shape) : Nat := shapeLittle shape.reverse
def shapeDecode (n : Nat) : Shape := (shapeDecodeAux n n).reverse

theorem shapeLittle_zero_iff (shape : Shape) : shapeLittle shape = 0 ↔ shape = [] := by
  cases shape <;> simp [shapeLittle]

theorem shapeEncode_zero_iff (shape : Shape) : shapeEncode shape = 0 ↔ shape = [] := by
  simp [shapeEncode, shapeLittle_zero_iff]

theorem shapeDecodeAux_little : ∀ (shape : Shape) (fuel : Nat),
    shapeLittle shape ≤ fuel → shapeDecodeAux fuel (shapeLittle shape) = shape
  | [], fuel, _ => by cases fuel <;> simp [shapeLittle, shapeDecodeAux]
  | s :: rest, fuel, bounded => by
      have slotBound := slotValue_lt_two s
      have positive : 0 < fuel := by simp only [shapeLittle] at bounded; omega
      obtain ⟨f, rfl⟩ : ∃ f, fuel = f + 1 := ⟨fuel - 1, by omega⟩
      have nonzero : shapeLittle (s :: rest) ≠ 0 := by simp [shapeLittle]
      have residue : (shapeLittle (s :: rest) - 1) % 2 = slotValue s := by
        simp only [shapeLittle]; omega
      have quotient : (shapeLittle (s :: rest) - 1) / 2 = shapeLittle rest := by
        simp only [shapeLittle]; omega
      have tailBound : shapeLittle rest ≤ f := by simp only [shapeLittle] at bounded; omega
      have bit : bitSlot (shapeLittle (s :: rest) - 1) = s := by
        cases s <;> simp_all [bitSlot, slotValue]
      simp only [shapeDecodeAux, nonzero, ↓reduceIte, quotient, bit,
        shapeDecodeAux_little rest f tailBound]

theorem shapeDecode_encode (shape : Shape) : shapeDecode (shapeEncode shape) = shape := by
  simp only [shapeDecode, shapeEncode,
    shapeDecodeAux_little _ _ (Nat.le_refl _), List.reverse_reverse]

theorem shapeEncode_injective : Function.Injective shapeEncode := by
  intro left right same
  have := congrArg shapeDecode same
  simpa only [shapeDecode_encode] using this

theorem shapeLittle_decodeAux : ∀ (fuel n : Nat),
    n ≤ fuel → shapeLittle (shapeDecodeAux fuel n) = n
  | 0, n, bounded => by
      have zero : n = 0 := by omega
      subst n
      rfl
  | fuel + 1, n, bounded => by
      by_cases zero : n = 0
      · simp [zero, shapeDecodeAux, shapeLittle]
      · have tailBound : (n - 1) / 2 ≤ fuel := by omega
        simp only [shapeDecodeAux, zero, ↓reduceIte, shapeLittle, slotValue_bitSlot]
        rw [shapeLittle_decodeAux fuel ((n - 1) / 2) tailBound]
        omega

theorem shapeEncode_decode (n : Nat) : shapeEncode (shapeDecode n) = n := by
  simp only [shapeEncode, shapeDecode, List.reverse_reverse,
    shapeLittle_decodeAux _ _ (Nat.le_refl _)]

theorem shapeKey_iff (left right : Shape) :
    shapeEncode left = shapeEncode right ↔ left = right :=
  ⟨fun same => shapeEncode_injective same, congrArg shapeEncode⟩

theorem shapeLittle_append (left right : Shape) :
    shapeLittle (left ++ right) = shapeLittle left + 2 ^ left.length * shapeLittle right := by
  induction left with
  | nil => simp [shapeLittle]
  | cons s rest ih =>
      simp only [List.cons_append, shapeLittle, ih, List.length_cons, Nat.pow_succ,
        Nat.mul_add, Nat.add_assoc]
      ac_rfl

theorem shapeEncode_append (left right : Shape) :
    shapeEncode (left ++ right) = 2 ^ right.length * shapeEncode left + shapeEncode right := by
  simp only [shapeEncode, List.reverse_append, shapeLittle_append, List.length_reverse]
  omega

def consonants : Shape → Nat
  | [] => 0
  | .c :: rest => consonants rest + 1
  | .v :: rest => consonants rest

def vowels : Shape → Nat
  | [] => 0
  | .c :: rest => vowels rest
  | .v :: rest => vowels rest + 1

theorem counts_length (shape : Shape) : consonants shape + vowels shape = shape.length := by
  induction shape with
  | nil => rfl
  | cons s rest ih => cases s <;> simp_all [consonants, vowels] <;> omega

theorem consonants_append (left right : Shape) :
    consonants (left ++ right) = consonants left + consonants right := by
  induction left with
  | nil => simp [consonants]
  | cons s rest ih => cases s <;> simp_all [consonants] <;> omega

theorem vowels_append (left right : Shape) :
    vowels (left ++ right) = vowels left + vowels right := by
  induction left with
  | nil => simp [vowels]
  | cons s rest ih => cases s <;> simp_all [vowels] <;> omega

/-- All orderings, including proposals that a linguistic law may reject. -/
def quotaWords (cCount vCount : Nat) : List Shape :=
  (Count.allWords [Slot.c, Slot.v] (cCount + vCount)).filter fun shape =>
    decide (consonants shape = cCount ∧ vowels shape = vCount)

theorem quotaWords_sound (cCount vCount : Nat) (shape : Shape)
    (member : shape ∈ quotaWords cCount vCount) :
    consonants shape = cCount ∧ vowels shape = vCount ∧ shape.length = cCount + vCount := by
  have counts := (List.mem_filter.mp member).2
  simp only [decide_eq_true_eq] at counts
  exact ⟨counts.1, counts.2, by rw [← counts.1, ← counts.2, counts_length]⟩

theorem quotaWords_complete (cCount vCount : Nat) (shape : Shape)
    (c : consonants shape = cCount) (v : vowels shape = vCount) :
    shape ∈ quotaWords cCount vCount := by
  apply List.mem_filter.mpr
  constructor
  · apply Count.allWords_complete
    · have := counts_length shape
      omega
    · intro slot _
      cases slot <;> simp
  · simp [c, v]

theorem mem_quotaWords_iff (cCount vCount : Nat) (shape : Shape) :
    shape ∈ quotaWords cCount vCount ↔ consonants shape = cCount ∧ vowels shape = vCount :=
  ⟨fun member => let proof := quotaWords_sound cCount vCount shape member; ⟨proof.1, proof.2.1⟩,
   fun counts => quotaWords_complete cCount vCount shape counts.1 counts.2⟩

theorem quotaWords_nodup (cCount vCount : Nat) : (quotaWords cCount vCount).Nodup :=
  (Count.allWords_nodup [Slot.c, Slot.v] (by decide) (cCount + vCount)).filter _

inductive SearchResult where
  | complete (shapes : List Shape)
  | exhausted (requiredAtoms : Nat)
  deriving DecidableEq, Repr

def boundedQuotaWords (maxAtoms cCount vCount : Nat) : SearchResult :=
  if cCount + vCount ≤ maxAtoms then .complete (quotaWords cCount vCount)
  else .exhausted (cCount + vCount)

theorem bounded_complete_iff (maxAtoms cCount vCount : Nat) :
    boundedQuotaWords maxAtoms cCount vCount = .complete (quotaWords cCount vCount) ↔
      cCount + vCount ≤ maxAtoms := by
  simp [boundedQuotaWords]

theorem bounded_exhausted_iff (maxAtoms cCount vCount : Nat) :
    boundedQuotaWords maxAtoms cCount vCount = .exhausted (cCount + vCount) ↔
      maxAtoms < cCount + vCount := by
  simp [boundedQuotaWords]

/-- Flat groupings are alternatives, not a quotient that erases boundaries. -/
def decompositions (shape : Shape) : List (List Shape) := UnitDiscovery.allPartitions shape

theorem decomposition_exact (shape : Shape) (parts : List Shape)
    (member : parts ∈ decompositions shape) :
    parts.flatten = shape ∧ ∀ part ∈ parts, part ≠ [] :=
  UnitDiscovery.allPartitions_sound shape parts member

theorem decomposition_complete (shape : Shape) (parts : List Shape)
    (same : parts.flatten = shape) (nonempty : ∀ part ∈ parts, part ≠ []) :
    parts ∈ decompositions shape :=
  UnitDiscovery.allPartitions_complete shape parts ⟨same, nonempty⟩

theorem decomposition_key (shape : Shape) (parts : List Shape)
    (member : parts ∈ decompositions shape) : shapeEncode parts.flatten = shapeEncode shape :=
  congrArg shapeEncode (decomposition_exact shape parts member).1

theorem decomposition_count (shape : Shape) :
    (decompositions shape).length = 2 ^ (shape.length - 1) :=
  UnitDiscovery.allPartitions_count shape

/-- Binary grouping preserves every supplied derivation; key equality is only
whole-content equality. It does not identify the grouping trees. -/
inductive UnitTree where
  | atom (slot : Slot)
  | join (left right : UnitTree)
  deriving DecidableEq, Repr

namespace UnitTree

def flatten : UnitTree → Shape
  | .atom slot => [slot]
  | .join left right => left.flatten ++ right.flatten

def key (tree : UnitTree) : Nat := shapeEncode tree.flatten

def rank : UnitTree → Nat
  | .atom _ => 0
  | .join left right => left.rank + right.rank + 1

theorem flatten_nonempty (tree : UnitTree) : tree.flatten ≠ [] := by
  induction tree with
  | atom slot => simp [flatten]
  | join left right ihLeft ihRight => simp [flatten, ihLeft]

theorem left_rank_lt (left right : UnitTree) : left.rank < (join left right).rank := by
  simp only [rank]; omega

theorem right_rank_lt (left right : UnitTree) : right.rank < (join left right).rank := by
  simp only [rank]; omega

theorem rank_length (tree : UnitTree) : tree.rank + 1 = tree.flatten.length := by
  induction tree with
  | atom slot => rfl
  | join left right ihLeft ihRight =>
      simp only [rank, flatten, List.length_append]
      omega

theorem key_iff (left right : UnitTree) : left.key = right.key ↔ left.flatten = right.flatten :=
  shapeKey_iff left.flatten right.flatten

theorem regroup_same_key (a b c : UnitTree) :
    (join (join a b) c).key = (join a (join b c)).key := by
  simp [key, flatten, List.append_assoc]

theorem regroup_different_tree :
    join (join (atom .c) (atom .v)) (atom .c) ≠
      join (atom .c) (join (atom .v) (atom .c)) := by decide

end UnitTree

def atomicTrees : Shape → List UnitTree
  | [slot] => [.atom slot]
  | _ => []

theorem mem_atomicTrees_iff (shape : Shape) (tree : UnitTree) :
    tree ∈ atomicTrees shape ↔ ∃ slot, shape = [slot] ∧ tree = .atom slot := by
  cases shape with
  | nil => simp [atomicTrees]
  | cons slot rest =>
      cases rest with
      | nil => simp [atomicTrees]
      | cons next tail => simp [atomicTrees]

def joinTrees (left right : List UnitTree) : List UnitTree :=
  left.flatMap fun l => right.map (UnitTree.join l)

theorem mem_joinTrees_iff (left right : List UnitTree) (tree : UnitTree) :
    tree ∈ joinTrees left right ↔
      ∃ l ∈ left, ∃ r ∈ right, tree = .join l r := by
  simp only [joinTrees, List.mem_flatMap, List.mem_map]
  constructor
  · rintro ⟨l, hl, r, hr, same⟩
    exact ⟨l, hl, r, hr, same.symm⟩
  · rintro ⟨l, hl, r, hr, same⟩
    exact ⟨l, hl, r, hr, same.symm⟩

theorem joinTrees_nodup (left right : List UnitTree)
    (leftUnique : left.Nodup) (rightUnique : right.Nodup) : (joinTrees left right).Nodup := by
  apply List.pairwise_flatMap.mpr
  constructor
  · intro l _
    exact rightUnique.map (UnitTree.join l)
      (fun _ _ different same => different (UnitTree.join.inj same).2)
  · apply leftUnique.imp
    intro l r different x hx y hy same
    obtain ⟨lx, _, rfl⟩ := List.mem_map.mp hx
    obtain ⟨ry, _, rfl⟩ := List.mem_map.mp hy
    exact different (UnitTree.join.inj same).1

/-- Fuel bounds recursion depth. Every join uses an original, proper split.
`shape.length` fuel is sufficient for all binary associations of that shape. -/
def allTreesAux : Nat → Shape → List UnitTree
  | 0, _ => []
  | fuel + 1, shape =>
      atomicTrees shape ++ (List.range shape.length).flatMap fun split =>
        if split = 0 then []
        else joinTrees (allTreesAux fuel (shape.take split))
          (allTreesAux fuel (shape.drop split))

theorem allTreesAux_sound (fuel : Nat) (shape : Shape) (tree : UnitTree)
    (member : tree ∈ allTreesAux fuel shape) : tree.flatten = shape := by
  induction fuel generalizing shape tree with
  | zero => simp [allTreesAux] at member
  | succ fuel ih =>
      rcases List.mem_append.mp member with atom | joins
      · obtain ⟨slot, rfl, rfl⟩ := (mem_atomicTrees_iff shape tree).mp atom
        rfl
      · obtain ⟨split, _, step⟩ := List.mem_flatMap.mp joins
        by_cases zero : split = 0
        · simp [zero] at step
        · simp only [zero, ↓reduceIte] at step
          obtain ⟨left, hl, right, hr, rfl⟩ := (mem_joinTrees_iff _ _ tree).mp step
          rw [UnitTree.flatten, ih _ _ hl, ih _ _ hr, List.take_append_drop]

theorem allTreesAux_complete (tree : UnitTree) (fuel : Nat)
    (bounded : tree.flatten.length ≤ fuel) : tree ∈ allTreesAux fuel tree.flatten := by
  induction tree generalizing fuel with
  | atom slot =>
      cases fuel with
      | zero => simp [UnitTree.flatten] at bounded
      | succ fuel => simp [allTreesAux, atomicTrees, UnitTree.flatten]
  | join left right ihLeft ihRight =>
      have leftPositive : 0 < left.flatten.length := by
        have := left.flatten_nonempty
        exact List.length_pos_iff.mpr this
      have rightPositive : 0 < right.flatten.length := by
        have := right.flatten_nonempty
        exact List.length_pos_iff.mpr this
      cases fuel with
      | zero => simp only [UnitTree.flatten, List.length_append] at bounded; omega
      | succ fuel =>
          have leftBound : left.flatten.length ≤ fuel := by
            simp only [UnitTree.flatten, List.length_append] at bounded; omega
          have rightBound : right.flatten.length ≤ fuel := by
            simp only [UnitTree.flatten, List.length_append] at bounded; omega
          apply List.mem_append.mpr
          right
          apply List.mem_flatMap.mpr
          refine ⟨left.flatten.length, ?_, ?_⟩
          · simp only [List.mem_range, UnitTree.flatten, List.length_append]
            omega
          · have nonzero : left.flatten.length ≠ 0 := by omega
            simp only [nonzero, ↓reduceIte, UnitTree.flatten,
              List.take_left, List.drop_left]
            exact (mem_joinTrees_iff _ _ _).mpr
              ⟨left, ihLeft fuel leftBound, right, ihRight fuel rightBound, rfl⟩

theorem allTreesAux_nodup (fuel : Nat) (shape : Shape) : (allTreesAux fuel shape).Nodup := by
  induction fuel generalizing shape with
  | zero => simp [allTreesAux]
  | succ fuel ih =>
      apply List.nodup_append.mpr
      refine ⟨?_, ?_, ?_⟩
      · cases shape with
        | nil => simp [atomicTrees]
        | cons slot rest => cases rest <;> simp [atomicTrees]
      · apply List.pairwise_flatMap.mpr
        constructor
        · intro split _
          split
          · simp
          · exact joinTrees_nodup _ _ (ih _) (ih _)
        · apply List.Pairwise.imp_of_mem (p := (List.nodup_range (n := shape.length)))
          intro i j hi hj different x hx y hy same
          by_cases izero : i = 0
          · simp [izero] at hx
          by_cases jzero : j = 0
          · simp [jzero] at hy
          simp only [izero, jzero, ↓reduceIte] at hx hy
          obtain ⟨left, hl, right, _, rfl⟩ := (mem_joinTrees_iff _ _ x).mp hx
          obtain ⟨otherLeft, hol, otherRight, _, rfl⟩ := (mem_joinTrees_iff _ _ y).mp hy
          have leftSame := (UnitTree.join.inj same).1
          have takeSame : shape.take i = shape.take j := by
            rw [← allTreesAux_sound fuel (shape.take i) left hl,
              ← allTreesAux_sound fuel (shape.take j) otherLeft hol, leftSame]
          have lengths := congrArg List.length takeSame
          have ibound := List.mem_range.mp hi
          have jbound := List.mem_range.mp hj
          simp only [List.length_take] at lengths
          apply different
          omega
      · intro atom atomMember tree treeMember same
        obtain ⟨slot, _, rfl⟩ := (mem_atomicTrees_iff shape atom).mp atomMember
        obtain ⟨split, _, step⟩ := List.mem_flatMap.mp treeMember
        by_cases zero : split = 0
        · simp [zero] at step
        · simp only [zero, ↓reduceIte] at step
          obtain ⟨left, _, right, _, rfl⟩ := (mem_joinTrees_iff _ _ tree).mp step
          cases same

def allTrees (shape : Shape) : List UnitTree := allTreesAux shape.length shape

theorem allTrees_exact (shape : Shape) (tree : UnitTree) :
    tree ∈ allTrees shape ↔ tree.flatten = shape := by
  constructor
  · exact allTreesAux_sound shape.length shape tree
  · intro same
    rw [allTrees, ← same]
    exact allTreesAux_complete tree tree.flatten.length (Nat.le_refl _)

theorem allTrees_nodup (shape : Shape) : (allTrees shape).Nodup :=
  allTreesAux_nodup shape.length shape

inductive ForestResult where
  | complete (trees : List UnitTree)
  | exhausted (requiredAtoms : Nat)
  deriving DecidableEq, Repr

def boundedTrees (maxAtoms : Nat) (shape : Shape) : ForestResult :=
  if shape.length ≤ maxAtoms then .complete (allTrees shape)
  else .exhausted shape.length

theorem boundedTrees_exhausted_iff (maxAtoms : Nat) (shape : Shape) :
    boundedTrees maxAtoms shape = .exhausted shape.length ↔ maxAtoms < shape.length := by
  simp [boundedTrees]

theorem equal_counts_distinct_order :
    consonants [.c, .v, .c, .v] = consonants [.c, .v, .v, .c] ∧
    vowels [.c, .v, .c, .v] = vowels [.c, .v, .v, .c] ∧
    shapeEncode [.c, .v, .c, .v] ≠ shapeEncode [.c, .v, .v, .c] := by decide

theorem cv_composition : [Slot.c, .v] ++ [.c, .v] = [.c, .v, .c, .v] := rfl

theorem small_quota_counts :
    (quotaWords 2 1).length = 3 ∧ (quotaWords 2 2).length = 6 ∧
    (quotaWords 3 1).length = 4 ∧ (quotaWords 3 2).length = 10 ∧
    (quotaWords 3 3).length = 20 := by decide

/-! ## The A116 carrier/mark domain is not a discovered phoneme inventory. -/

def cells : List Cell := (List.finRange 116).map Cell.decode
def movingCells : List Cell := cells.filter fun cell => decide (cell.mark.val < 3)
def stillCells : List Cell := cells.filter fun cell => decide (cell.mark.val = 3)

def followingShortMark (cell : Cell) : Option (Fin 3) :=
  if h : cell.mark.val < 3 then some ⟨cell.mark.val, h⟩ else none

theorem carrier_mark_counts :
    cells.length = 116 ∧ movingCells.length = 87 ∧ stillCells.length = 29 := by decide

theorem no_short_mark_iff_sukun (cell : Cell) :
    followingShortMark cell = none ↔ cell.mark.val = 3 := by
  have bound := cell.mark.isLt
  simp only [followingShortMark]
  split <;> simp_all <;> omega

/-! ## Quantity is an explicitly aligned interpretation, never read from VV alone. -/

inductive Quantity where
  | short
  | long
  deriving DecidableEq, Repr

inductive Segment where
  | consonant (identity : Nat)
  | vowel (quality : Nat) (quantity : Quantity)
  deriving DecidableEq, Repr

def segmentShape : Segment → Shape
  | .consonant _ => [.c]
  | .vowel _ .short => [.v]
  | .vowel _ .long => [.v, .v]

def segmentsShape (segments : List Segment) : Shape := segments.flatMap segmentShape

theorem segmentsShape_append (left right : List Segment) :
    segmentsShape (left ++ right) = segmentsShape left ++ segmentsShape right := by
  simp [segmentsShape]

theorem vv_does_not_determine_quantity :
    segmentsShape [.vowel 0 .long] = segmentsShape [.vowel 0 .short, .vowel 0 .short] ∧
      ([Segment.vowel 0 .long] : List Segment) ≠ [.vowel 0 .short, .vowel 0 .short] := by decide

structure AlignmentPiece where
  raw : List Atom
  segments : List Segment
  deriving DecidableEq, Repr

structure Reading where
  source : UnitDiscovery.Source Atom
  host : UnitDiscovery.Span
  pieces : List AlignmentPiece
  ruleId : Nat
  readingId : Nat
  deriving DecidableEq, Repr

def Reading.raw (reading : Reading) : List Atom := reading.pieces.flatMap AlignmentPiece.raw
def Reading.segments (reading : Reading) : List Segment := reading.pieces.flatMap AlignmentPiece.segments
def Reading.shape (reading : Reading) : Shape := segmentsShape reading.segments

def Reading.WellFormed (reading : Reading) : Prop :=
  UnitDiscovery.ValidSpan reading.source reading.host ∧
  reading.raw = UnitDiscovery.spanAtoms reading.source reading.host ∧
  ∀ piece ∈ reading.pieces, piece.raw ≠ [] ∧ piece.segments ≠ []

instance (reading : Reading) : Decidable reading.WellFormed :=
  inferInstanceAs (Decidable (_ ∧ _ ∧ _))

structure ReadingReceipt where
  target : Reading
  witnessId : Nat
  supports : List (UnitDiscovery.Support Atom)
  deriving DecidableEq, Repr

/-- Structural validation plus exact membership in a supplied interpreted
inventory. This checks a declared quantity reading, not its acquisition. -/
def acceptsReading (sources : List (UnitDiscovery.Source Atom))
    (interpreted : List ReadingReceipt) (reading : Reading) (receipt : ReadingReceipt) : Bool :=
  decide reading.WellFormed && decide (reading.source ∈ sources) &&
  decide (receipt.target = reading) && decide (receipt ∈ interpreted) &&
  !receipt.supports.isEmpty && receipt.supports.all (UnitDiscovery.validSupport sources)

theorem acceptsReading_iff (sources : List (UnitDiscovery.Source Atom))
    (interpreted : List ReadingReceipt) (reading : Reading) (receipt : ReadingReceipt) :
    acceptsReading sources interpreted reading receipt = true ↔
      reading.WellFormed ∧ reading.source ∈ sources ∧ receipt.target = reading ∧
      receipt ∈ interpreted ∧ receipt.supports ≠ [] ∧
      ∀ support ∈ receipt.supports,
        support.source ∈ sources ∧ UnitDiscovery.ValidSpan support.source support.span := by
  simp [acceptsReading, UnitDiscovery.validSupport, UnitDiscovery.validSpan,
    List.all_eq_true, and_assoc]

theorem accepted_quantity_mapping_bound (sources : List (UnitDiscovery.Source Atom))
    (interpreted : List ReadingReceipt) (reading : Reading) (receipt : ReadingReceipt)
    (accepted : acceptsReading sources interpreted reading receipt = true) :
    reading.raw = UnitDiscovery.spanAtoms reading.source reading.host ∧
      receipt.target = reading ∧ receipt ∈ interpreted := by
  have valid := (acceptsReading_iff sources interpreted reading receipt).mp accepted
  exact ⟨valid.1.2.1, valid.2.2.1, valid.2.2.2.1⟩

theorem foreign_quantity_mapping_not_accepted (sources : List (UnitDiscovery.Source Atom))
    (interpreted : List ReadingReceipt) (reading : Reading) (receipt : ReadingReceipt)
    (different : receipt.target ≠ reading) :
    acceptsReading sources interpreted reading receipt = false := by
  simp [acceptsReading, different]

theorem no_interpreted_quantity_not_accepted (sources : List (UnitDiscovery.Source Atom))
    (reading : Reading) (receipt : ReadingReceipt) :
    acceptsReading sources [] reading receipt = false := by
  simp [acceptsReading]

end Nabt.ProsodicUnits
