import Std

/-!
# Recursive licensed algebra: roots, morphology, and syntax

Independent formal kernel, 2026-10-24. This file imports only Std.

The roots, lexical entries, rule inventory, interfaces, realizations, and
linguistic gates are explicit parameters. Their linguistic adequacy is not
inferred from numbering or induction. A root is an ordered triple/quadruple;
fixed lexical entries provide an independent inlet, including particles.

`Tree.n` is injective on structural derivation trees. It includes constructor
tags, rule identifiers, and ordered children. It is relative to a fixed rule
registry/version, NOT an identifier for surface strings, meanings, proof terms,
or source occurrences. Repeated identical constructions receive the same n.

The carrier is the whole Tree. A Face supplies its category, state, position
interface, and residual requirements. Unary morphology can rewrite a surface;
there is no false assumption that root radicals form a contiguous substring.
The complete old tree is retained independently of that realization.

Every node requires its own typing and gate certificates. Derived units remain
eligible as inputs to further rules without losing their inner structure.
Finite exhaustive search is relative to finite seed/rule lists and a height
bound. Filtering additionally requires a decision procedure for certification.
-/

namespace RecursiveLicensedAlgebra

set_option autoImplicit false

inductive Seed where
  | root3 (a b c : Nat)
  | root4 (a b c d : Nat)
  | lexical (entry : Nat)
  deriving DecidableEq, Repr

inductive Tree where
  | leaf (seed : Seed)
  | unary (rule : Nat) (child : Tree)
  | binary (rule : Nat) (left right : Tree)
  deriving DecidableEq, Repr

inductive Category where
  | root3 | root4 | noun | verb | particle
  | nounPhrase | verbPhrase | semiClause | nominalClause | verbalClause | clause | pending
  deriving DecidableEq, Repr

/-- Position is an interface tag; source coordinates need separate provenance. -/
structure Face where
  category : Category
  state : Nat := 0
  position : Nat := 0
  residual : List Nat := []
  deriving DecidableEq, Repr

abbrev Surface := List Nat

structure UnaryRule where
  input : Face
  output : Face
  realize : Surface → Surface
  gate : Tree → Prop

structure BinaryRule where
  left : Face
  right : Face
  output : Face
  realize : Surface → Surface → Surface
  gate : Tree → Tree → Prop

structure Grammar where
  root3Allowed : Nat → Nat → Nat → Prop
  root4Allowed : Nat → Nat → Nat → Nat → Prop
  lexicalAllowed : Nat → Prop
  lexicalFace : Nat → Face
  lexicalSurface : Nat → Surface
  unaryRule : Nat → UnaryRule
  binaryRule : Nat → BinaryRule

def Seed.face (g : Grammar) : Seed → Face
  | .root3 _ _ _ => { category := .root3 }
  | .root4 _ _ _ _ => { category := .root4 }
  | .lexical entry => g.lexicalFace entry

def Seed.allowed (g : Grammar) : Seed → Prop
  | .root3 a b c => g.root3Allowed a b c
  | .root4 a b c d => g.root4Allowed a b c d
  | .lexical entry => g.lexicalAllowed entry

def Seed.surface (g : Grammar) : Seed → Surface
  | .root3 a b c => [a, b, c]
  | .root4 a b c d => [a, b, c, d]
  | .lexical entry => g.lexicalSurface entry

def Tree.face (g : Grammar) : Tree → Face
  | .leaf seed => seed.face g
  | .unary r _ => (g.unaryRule r).output
  | .binary r _ _ => (g.binaryRule r).output

def Tree.surface (g : Grammar) : Tree → Surface
  | .leaf seed => seed.surface g
  | .unary r child => (g.unaryRule r).realize (child.surface g)
  | .binary r left right =>
      (g.binaryRule r).realize (left.surface g) (right.surface g)

/-- Ordered seed provenance survives every surface rewriting operation. -/
def Tree.origins : Tree → List Seed
  | .leaf seed => [seed]
  | .unary _ child => child.origins
  | .binary _ left right => left.origins ++ right.origins

def Tree.height : Tree → Nat
  | .leaf _ => 0
  | .unary _ child => child.height + 1
  | .binary _ left right => max left.height right.height + 1

inductive Certified (g : Grammar) : Tree → Prop where
  | leaf (seed : Seed) (allowed : seed.allowed g) : Certified g (.leaf seed)
  | unary {r : Nat} {child : Tree}
      (inner : Certified g child)
      (fits : child.face g = (g.unaryRule r).input)
      (allowed : (g.unaryRule r).gate child) :
      Certified g (.unary r child)
  | binary {r : Nat} {left right : Tree}
      (leftProof : Certified g left) (rightProof : Certified g right)
      (leftFits : left.face g = (g.binaryRule r).left)
      (rightFits : right.face g = (g.binaryRule r).right)
      (allowed : (g.binaryRule r).gate left right) :
      Certified g (.binary r left right)

def AllNodeConditions (g : Grammar) : Tree → Prop
  | .leaf seed => seed.allowed g
  | .unary r child =>
      AllNodeConditions g child ∧ child.face g = (g.unaryRule r).input ∧
        (g.unaryRule r).gate child
  | .binary r left right =>
      AllNodeConditions g left ∧ AllNodeConditions g right ∧
        left.face g = (g.binaryRule r).left ∧
        right.face g = (g.binaryRule r).right ∧
        (g.binaryRule r).gate left right

/-- The induction principle needed to preserve any constructor-local invariant. -/
theorem licensed_induction (g : Grammar) (P : Tree → Prop)
    (seedCase : ∀ s, s.allowed g → P (.leaf s))
    (unaryCase : ∀ r t, Certified g t →
      t.face g = (g.unaryRule r).input → (g.unaryRule r).gate t →
      P t → P (.unary r t))
    (binaryCase : ∀ r l t, Certified g l → Certified g t →
      l.face g = (g.binaryRule r).left → t.face g = (g.binaryRule r).right →
      (g.binaryRule r).gate l t → P l → P t → P (.binary r l t))
    {t : Tree} (h : Certified g t) : P t := by
  induction h with
  | leaf s allowed => exact seedCase s allowed
  | @unary r t inner fits allowed ih => exact unaryCase r t inner fits allowed ih
  | @binary r l t hl ht fl ft allowed ihl iht =>
      exact binaryCase r l t hl ht fl ft allowed ihl iht

/--
An independently supplied contract connects a realization to its claimed face.
It can express a phonotactic law or another invariant of faces and surfaces.
No Arabic instance of these contracts is silently assumed by `Certified`.
-/
structure RealizationContracts (g : Grammar) (P : Face → Surface → Prop) : Prop where
  seed : ∀ (s : Seed), s.allowed g → P (s.face g) (s.surface g)
  unary : ∀ (r : Nat) (t : Tree), t.face g = (g.unaryRule r).input → (g.unaryRule r).gate t →
    P (t.face g) (t.surface g) →
    P (g.unaryRule r).output ((g.unaryRule r).realize (t.surface g))
  binary : ∀ (r : Nat) (l t : Tree), l.face g = (g.binaryRule r).left →
    t.face g = (g.binaryRule r).right → (g.binaryRule r).gate l t →
    P (l.face g) (l.surface g) → P (t.face g) (t.surface g) →
    P (g.binaryRule r).output ((g.binaryRule r).realize (l.surface g) (t.surface g))

theorem certified_realization_sound (g : Grammar) (P : Face → Surface → Prop)
    (contracts : RealizationContracts g P) {t : Tree} (h : Certified g t) :
    P (t.face g) (t.surface g) := by
  induction h with
  | leaf s allowed => exact contracts.seed s allowed
  | @unary r child _ fits allowed ih => exact contracts.unary r child fits allowed ih
  | @binary r l t _ _ fl ft allowed ihl iht =>
      exact contracts.binary r l t fl ft allowed ihl iht

theorem certified_iff_all_node_conditions (g : Grammar) (t : Tree) :
    Certified g t ↔ AllNodeConditions g t := by
  constructor
  · intro h
    induction h with
    | leaf s allowed => exact allowed
    | unary _ fits allowed ih => exact ⟨ih, fits, allowed⟩
    | binary _ _ fl fr allowed ihl ihr => exact ⟨ihl, ihr, fl, fr, allowed⟩
  · induction t with
    | leaf s => exact Certified.leaf s
    | unary r t ih =>
        rintro ⟨ht, fits, allowed⟩
        exact .unary (ih ht) fits allowed
    | binary r l t ihl iht =>
        rintro ⟨hl, ht, fl, ft, allowed⟩
        exact .binary (ihl hl) (iht ht) fl ft allowed

theorem unary_rejected_on_interface_mismatch (g : Grammar) (r : Nat) (t : Tree)
    (mismatch : t.face g ≠ (g.unaryRule r).input) : ¬ Certified g (.unary r t) := by
  intro h
  exact mismatch ((certified_iff_all_node_conditions g _).1 h).2.1

theorem binary_rejected_on_gate_failure (g : Grammar) (r : Nat) (l t : Tree)
    (blocked : ¬ (g.binaryRule r).gate l t) : ¬ Certified g (.binary r l t) := by
  intro h
  exact blocked ((certified_iff_all_node_conditions g _).1 h).2.2.2.2

/-- A fully checked result is again a carrier for any subsequent rule. -/
structure Unit (g : Grammar) where
  tree : Tree
  certified : Certified g tree

def seedUnit (g : Grammar) (s : Seed) (h : s.allowed g) : Unit g :=
  ⟨.leaf s, .leaf s h⟩

def unaryUnit {g : Grammar} (r : Nat) (u : Unit g)
    (fits : u.tree.face g = (g.unaryRule r).input)
    (allowed : (g.unaryRule r).gate u.tree) : Unit g :=
  ⟨.unary r u.tree, .unary u.certified fits allowed⟩

def binaryUnit {g : Grammar} (r : Nat) (u v : Unit g)
    (fu : u.tree.face g = (g.binaryRule r).left)
    (fv : v.tree.face g = (g.binaryRule r).right)
    (allowed : (g.binaryRule r).gate u.tree v.tree) : Unit g :=
  ⟨.binary r u.tree v.tree, .binary u.certified v.certified fu fv allowed⟩

theorem unary_origins_preserved (r : Nat) (t : Tree) :
    (Tree.unary r t).origins = t.origins := rfl

theorem binary_origins_preserved (r : Nat) (l t : Tree) :
    (Tree.binary r l t).origins = l.origins ++ t.origins := rfl

theorem unary_rank_increases (r : Nat) (t : Tree) :
    t.height < (Tree.unary r t).height := Nat.lt_succ_self _

theorem binary_rank_increases (r : Nat) (l t : Tree) :
    l.height < (Tree.binary r l t).height ∧ t.height < (Tree.binary r l t).height := by
  simp only [Tree.height]
  exact ⟨Nat.lt_succ_of_le (Nat.le_max_left _ _), Nat.lt_succ_of_le (Nat.le_max_right _ _)⟩

theorem unary_retains_child (r : Nat) (t : Tree) :
    (match Tree.unary r t with | .unary _ inner => some inner | _ => none) = some t := rfl

theorem binary_retains_children (r : Nat) (l t : Tree) :
    (match Tree.binary r l t with | .binary _ x y => some (x,y) | _ => none) = some (l,t) := rfl

theorem new_carrier_is_one_outer_unit {g : Grammar} (u : Unit g) : [u].length = 1 := rfl

/-! ## Exact structural numbering into Nat -/

def triangle : Nat → Nat
  | 0 => 0
  | n + 1 => triangle n + n + 1

def pair (a b : Nat) : Nat := triangle (a + b) + b

theorem triangle_mono {a b : Nat} (h : a ≤ b) : triangle a ≤ triangle b := by
  induction h with
  | refl => exact Nat.le_refl _
  | step _ ih => simp only [triangle]; omega

theorem pair_injective {a b c d : Nat} (h : pair a b = pair c d) : a = c ∧ b = d := by
  unfold pair at h
  have sameDiagonal : a + b = c + d := by
    rcases Nat.lt_trichotomy (a + b) (c + d) with hl | he | hr
    · have hm := triangle_mono (Nat.succ_le_of_lt hl)
      simp only [triangle] at hm
      omega
    · exact he
    · have hm := triangle_mono (Nat.succ_le_of_lt hr)
      simp only [triangle] at hm
      omega
  rw [sameDiagonal] at h
  omega

def Seed.n : Seed → Nat
  | .root3 a b c => 3 * pair a (pair b c)
  | .root4 a b c d => 3 * pair a (pair b (pair c d)) + 1
  | .lexical entry => 3 * entry + 2

theorem seed_number_injective (s t : Seed) (h : s.n = t.n) : s = t := by
  cases s with
  | root3 a b c =>
      cases t with
      | root3 x y z =>
          simp only [Seed.n] at h
          have hp := pair_injective (by omega : pair a (pair b c) = pair x (pair y z))
          have hq := pair_injective hp.2
          simp_all
      | root4 x y z w => simp only [Seed.n] at h; omega
      | lexical entry => simp only [Seed.n] at h; omega
  | root4 a b c d =>
      cases t with
      | root3 x y z => simp only [Seed.n] at h; omega
      | root4 x y z w =>
          simp only [Seed.n] at h
          have hp := pair_injective (by omega : pair a (pair b (pair c d)) = pair x (pair y (pair z w)))
          have hq := pair_injective hp.2
          have hr := pair_injective hq.2
          simp_all
      | lexical entry => simp only [Seed.n] at h; omega
  | lexical entry =>
      cases t with
      | root3 x y z => simp only [Seed.n] at h; omega
      | root4 x y z w => simp only [Seed.n] at h; omega
      | lexical other => simp only [Seed.n] at h; congr 1; omega

def Tree.n : Tree → Nat
  | .leaf seed => 3 * seed.n
  | .unary r child => 3 * pair r child.n + 1
  | .binary r left right => 3 * pair r (pair left.n right.n) + 2

theorem tree_number_injective (t u : Tree) (h : t.n = u.n) : t = u := by
  induction t generalizing u with
  | leaf seed =>
      cases u with
      | leaf other =>
          simp only [Tree.n] at h
          exact congrArg Tree.leaf (seed_number_injective seed other (by omega))
      | unary r child => simp only [Tree.n] at h; omega
      | binary r l t => simp only [Tree.n] at h; omega
  | unary r child ih =>
      cases u with
      | leaf seed => simp only [Tree.n] at h; omega
      | unary s other =>
          simp only [Tree.n] at h
          have hp := pair_injective (by omega : pair r child.n = pair s other.n)
          rw [hp.1, ih other hp.2]
      | binary s l t => simp only [Tree.n] at h; omega
  | binary r left right ihl ihr =>
      cases u with
      | leaf seed => simp only [Tree.n] at h; omega
      | unary s other => simp only [Tree.n] at h; omega
      | binary s l t =>
          simp only [Tree.n] at h
          have hp := pair_injective (by omega : pair r (pair left.n right.n) = pair s (pair l.n t.n))
          have hq := pair_injective hp.2
          rw [hp.1, ihl l hq.1, ihr t hq.2]

def Unit.n {g : Grammar} (u : Unit g) : Nat := u.tree.n

theorem unit_number_injective {g : Grammar} (u v : Unit g) (h : u.n = v.n) : u = v := by
  have same := tree_number_injective u.tree v.tree h
  cases u; cases v
  simp_all

theorem roots_of_different_lengths_have_different_ids (a b c d e f z : Nat) :
    (Tree.leaf (.root3 a b c)).n ≠ (Tree.leaf (.root4 d e f z)).n := by
  intro h
  have := tree_number_injective _ _ h
  cases this

theorem unary_result_has_new_id (r : Nat) (t : Tree) : (Tree.unary r t).n ≠ t.n := by
  intro h
  have same := tree_number_injective _ _ h
  have ranks := congrArg Tree.height same
  simp only [Tree.height] at ranks
  omega

theorem binary_rule_tags_are_recovered (r s : Nat) (l t x y : Tree)
    (h : (Tree.binary r l t).n = (Tree.binary s x y).n) : r = s ∧ l = x ∧ t = y := by
  have := tree_number_injective _ _ h
  exact Tree.binary.inj this

/-! ## Gate logic concerns evidence, independently of ordered construction -/

def XorGate (p q : Prop) : Prop := (p ∧ ¬q) ∨ (q ∧ ¬p)
def NorGate (p q : Prop) : Prop := ¬(p ∨ q)

theorem and_gate {p q : Prop} (hp : p) (hq : q) : p ∧ q := ⟨hp,hq⟩
theorem or_gate_left {p q : Prop} (hp : p) : p ∨ q := Or.inl hp
theorem nor_gate_iff {p q : Prop} : NorGate p q ↔ ¬p ∧ ¬q := by
  constructor
  · intro h; exact ⟨fun hp => h (.inl hp), fun hq => h (.inr hq)⟩
  · rintro ⟨hnp,hnq⟩ (hp | hq)
    · exact hnp hp
    · exact hnq hq

theorem xor_requires_exclusion {p q : Prop} (h : XorGate p q) : ¬(p ∧ q) := by
  rintro ⟨hp,hq⟩
  rcases h with ⟨_,hnq⟩ | ⟨_,hnp⟩
  · exact hnq hq
  · exact hnp hp

theorem implication_requires_antecedent {p q : Prop} (hp : p) (rule : p → q) : q := rule hp

/-- A true implication alone does not prove its conclusion. -/
theorem implication_alone_insufficient : ¬ (∀ p q : Prop, (p → q) → q) := by
  intro h
  exact h False False (fun x => x)

theorem ordered_children_are_not_exchangeable (r : Nat) (l t : Tree) (hne : l ≠ t) :
    (Tree.binary r l t).n ≠ (Tree.binary r t l).n := by
  intro h
  exact hne (binary_rule_tags_are_recovered r r l t t l h).2.1

/-! ## All combinations, exhaustively, within finite explicit bounds -/

structure Inventory where
  seeds : List Seed
  unaryRules : List Nat
  binaryRules : List Nat

def Supported (i : Inventory) : Tree → Prop
  | .leaf s => s ∈ i.seeds
  | .unary r t => r ∈ i.unaryRules ∧ Supported i t
  | .binary r l t => r ∈ i.binaryRules ∧ Supported i l ∧ Supported i t

def candidates (i : Inventory) : Nat → List Tree
  | 0 => i.seeds.map Tree.leaf
  | h + 1 =>
      let prev := candidates i h
      i.seeds.map Tree.leaf ++
      i.unaryRules.flatMap (fun r => prev.map (Tree.unary r)) ++
      i.binaryRules.flatMap (fun r => prev.flatMap (fun l => prev.map (Tree.binary r l)))

theorem candidates_iff (i : Inventory) (h : Nat) (t : Tree) :
    t ∈ candidates i h ↔ Supported i t ∧ t.height ≤ h := by
  induction h generalizing t with
  | zero =>
      cases t <;> simp [candidates, Supported, Tree.height]
  | succ h ih =>
      cases t with
      | leaf s => simp [candidates, Supported, Tree.height]
      | unary r t =>
          simp [candidates, Supported, Tree.height, ih, Nat.succ_le_succ_iff,
            and_assoc, and_left_comm, and_comm]
      | binary r l t =>
          simp [candidates, Supported, Tree.height, ih, Nat.succ_le_succ_iff,
            Nat.max_le, and_assoc, and_left_comm, and_comm]

/-- Increasing the height budget retains every previously generated tree. -/
theorem candidates_monotone (i : Inventory) {h k : Nat} (increase : h ≤ k)
    (t : Tree) (old : t ∈ candidates i h) : t ∈ candidates i k := by
  obtain ⟨supported, bounded⟩ := (candidates_iff i h t).1 old
  exact (candidates_iff i k t).2 ⟨supported, Nat.le_trans bounded increase⟩

def licensedCandidates (g : Grammar) (i : Inventory) (h : Nat)
    [DecidablePred (Certified g)] : List Tree :=
  (candidates i h).filter fun t => decide (Certified g t)

theorem licensed_candidates_iff (g : Grammar) (i : Inventory) (h : Nat)
    [DecidablePred (Certified g)] (t : Tree) :
    t ∈ licensedCandidates g i h ↔ Supported i t ∧ t.height ≤ h ∧ Certified g t := by
  simp [licensedCandidates, candidates_iff, and_assoc]

/-- Every finite licensed derivation in the inventory is reached at some stage. -/
theorem every_finite_licensed_tree_eventually_generated (g : Grammar) (i : Inventory)
    [DecidablePred (Certified g)] (t : Tree) (supported : Supported i t)
    (licensed : Certified g t) : ∃ h, t ∈ licensedCandidates g i h := by
  exact ⟨t.height, (licensed_candidates_iff g i t.height t).2
    ⟨supported, Nat.le_refl _, licensed⟩⟩

/-! A numerical check of candidate counts, not of any Arabic grammar. -/
def demoInventory : Inventory := ⟨[.root3 1 2 3, .root4 1 2 3 4, .lexical 0], [0,1], [0,1]⟩

set_option maxRecDepth 100000 in
theorem demo_candidate_counts :
    (candidates demoInventory 0).length = 3 ∧
    (candidates demoInventory 1).length = 27 ∧
    (candidates demoInventory 2).length = 1515 := by decide

end RecursiveLicensedAlgebra

-- Independent axiom inspection; original source bytes above are unchanged.
#print axioms RecursiveLicensedAlgebra.licensed_induction
#print axioms RecursiveLicensedAlgebra.certified_realization_sound
#print axioms RecursiveLicensedAlgebra.certified_iff_all_node_conditions
#print axioms RecursiveLicensedAlgebra.unary_rejected_on_interface_mismatch
#print axioms RecursiveLicensedAlgebra.binary_rejected_on_gate_failure
#print axioms RecursiveLicensedAlgebra.unary_origins_preserved
#print axioms RecursiveLicensedAlgebra.binary_origins_preserved
#print axioms RecursiveLicensedAlgebra.unary_rank_increases
#print axioms RecursiveLicensedAlgebra.binary_rank_increases
#print axioms RecursiveLicensedAlgebra.unary_retains_child
#print axioms RecursiveLicensedAlgebra.binary_retains_children
#print axioms RecursiveLicensedAlgebra.new_carrier_is_one_outer_unit
#print axioms RecursiveLicensedAlgebra.triangle_mono
#print axioms RecursiveLicensedAlgebra.pair_injective
#print axioms RecursiveLicensedAlgebra.seed_number_injective
#print axioms RecursiveLicensedAlgebra.tree_number_injective
#print axioms RecursiveLicensedAlgebra.unit_number_injective
#print axioms RecursiveLicensedAlgebra.roots_of_different_lengths_have_different_ids
#print axioms RecursiveLicensedAlgebra.unary_result_has_new_id
#print axioms RecursiveLicensedAlgebra.binary_rule_tags_are_recovered
#print axioms RecursiveLicensedAlgebra.and_gate
#print axioms RecursiveLicensedAlgebra.or_gate_left
#print axioms RecursiveLicensedAlgebra.nor_gate_iff
#print axioms RecursiveLicensedAlgebra.xor_requires_exclusion
#print axioms RecursiveLicensedAlgebra.implication_requires_antecedent
#print axioms RecursiveLicensedAlgebra.implication_alone_insufficient
#print axioms RecursiveLicensedAlgebra.ordered_children_are_not_exchangeable
#print axioms RecursiveLicensedAlgebra.candidates_iff
#print axioms RecursiveLicensedAlgebra.candidates_monotone
#print axioms RecursiveLicensedAlgebra.licensed_candidates_iff
#print axioms RecursiveLicensedAlgebra.every_finite_licensed_tree_eventually_generated
#print axioms RecursiveLicensedAlgebra.demo_candidate_counts
