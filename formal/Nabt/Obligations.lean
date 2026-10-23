import Std

/-!
Named positive obligations: a native NABT specification, inspired by the
positive-formula residual laws in Mashru and Alghanem. No other repository
is imported. The algebra is conditional on supplied assignments, not a
proof that a source, definition, policy, or linguistic assertion is true.

The structural results quantify over every finite formula. The mask
results quantify over natural-number masks. Runtime registry validation,
resource budgets, serialization, and Python execution are separately tested.
-/

namespace Nabt.Obligations

structure PropositionIdentity where
  name : String
  source : String
  occurrence : String
  reading : String
  context : String
  definition : String
  policy : String
deriving DecidableEq, Repr

/-- Equal display names do not erase a different context. -/
theorem identity_context_isolation {a b : PropositionIdentity}
    (different : a.context ≠ b.context) : a ≠ b := by
  intro same
  exact different (congrArg PropositionIdentity.context same)

/-- A proposition cannot be transferred to another source by retaining its name. -/
theorem identity_source_isolation {a b : PropositionIdentity}
    (different : a.source ≠ b.source) : a ≠ b := by
  intro same
  exact different (congrArg PropositionIdentity.source same)

inductive Formula (α : Type) where
  | yes
  | no
  | atom (a : α)
  | conj (left right : Formula α)
  | disj (left right : Formula α)
deriving DecidableEq, Repr

namespace Formula

def eval (assignment : α → Bool) : Formula α → Bool
  | .yes => true
  | .no => false
  | .atom a => assignment a
  | .conj l r => eval assignment l && eval assignment r
  | .disj l r => eval assignment l || eval assignment r

def atoms : Formula α → List α
  | .yes | .no => []
  | .atom a => [a]
  | .conj l r | .disj l r => atoms l ++ atoms r

/-- Positive formulas are monotone in positive support. -/
theorem eval_monotone (p q : α → Bool)
    (grows : ∀ a, p a = true → q a = true) (f : Formula α) :
    eval p f = true → eval q f = true := by
  induction f with
  | yes => simp [eval]
  | no => simp [eval]
  | atom a => exact grows a
  | conj l r il ir =>
    simpa only [eval, Bool.and_eq_true] using And.imp il ir
  | disj l r il ir =>
    simpa only [eval, Bool.or_eq_true] using Or.imp il ir

/-- An assignment outside the formula's atoms has no effect on its value. -/
theorem eval_ext_on_atoms (p q : α → Bool) (f : Formula α)
    (same : ∀ a ∈ atoms f, p a = q a) : eval p f = eval q f := by
  induction f with
  | yes => rfl
  | no => rfl
  | atom a => exact same a (by simp [atoms])
  | conj l r il ir =>
    simp only [eval]
    rw [il (fun a ha => same a (by simp [atoms, ha])),
        ir (fun a ha => same a (by simp [atoms, ha]))]
  | disj l r il ir =>
    simp only [eval]
    rw [il (fun a ha => same a (by simp [atoms, ha])),
        ir (fun a ha => same a (by simp [atoms, ha]))]

end Formula

/-- Inclusion of the finite sets represented by two masks. -/
def Submask (x y : Nat) : Prop := x &&& y = x

instance (x y : Nat) : Decidable (Submask x y) :=
  inferInstanceAs (Decidable (x &&& y = x))

theorem submask_iff_bits (x y : Nat) :
    Submask x y ↔ ∀ i, x.testBit i = true → y.testBit i = true := by
  constructor
  · intro h i hx
    have bit := congrArg (fun n => n.testBit i) h
    simpa [Nat.testBit_and, hx] using bit
  · intro h
    apply Nat.eq_of_testBit_eq
    intro i
    simp only [Nat.testBit_and]
    cases hx : x.testBit i
    · simp
    · simp [h i hx]

theorem submask_refl (x : Nat) : Submask x x := by simp [Submask]

theorem submask_trans {x y z : Nat} (xy : Submask x y) (yz : Submask y z) :
    Submask x z :=
  (submask_iff_bits x z).2 (fun i hi =>
    (submask_iff_bits y z).1 yz i ((submask_iff_bits x y).1 xy i hi))

theorem submask_strict_lt {x y : Nat} (xy : Submask x y) (different : x ≠ y) : x < y := by
  have le : x ≤ y := xy ▸ Nat.and_le_right
  omega

/-- A completion covers a conjunction plan iff it covers both components. -/
theorem union_submask_iff (x y s : Nat) :
    Submask (x ||| y) s ↔ Submask x s ∧ Submask y s := by
  simp only [submask_iff_bits, Nat.testBit_or, Bool.or_eq_true]
  constructor
  · intro h
    exact ⟨fun i hx => h i (Or.inl hx), fun i hy => h i (Or.inr hy)⟩
  · intro h i hi
    exact hi.elim (h.1 i) (h.2 i)

/-- Equality duplicates are erased; only inclusion-minimal elements remain. -/
def minimal (plans : List Nat) : List Nat :=
  plans.eraseDups.filter fun x => plans.all fun y => decide (Submask y x → y = x)

theorem mem_minimal_iff (plans : List Nat) (x : Nat) :
    x ∈ minimal plans ↔ x ∈ plans ∧ ∀ y ∈ plans, Submask y x → y = x := by
  unfold minimal
  rw [List.mem_filter, List.mem_eraseDups]
  constructor
  · rintro ⟨hx, hall⟩
    exact ⟨hx, fun y hy => of_decide_eq_true ((List.all_eq_true.1 hall) y hy)⟩
  · rintro ⟨hx, hall⟩
    exact ⟨hx, List.all_eq_true.2 (fun y hy => decide_eq_true (hall y hy))⟩

/-- Every original plan contains an inclusion-minimal plan. -/
theorem minimal_contains_subset (plans : List Nat) (x : Nat) (hx : x ∈ plans) :
    ∃ y ∈ minimal plans, Submask y x := by
  classical
  induction x using Nat.strongRecOn with
  | ind x ih =>
    by_cases h : ∀ y ∈ plans, Submask y x → y = x
    · exact ⟨x, (mem_minimal_iff plans x).2 ⟨hx, h⟩, submask_refl x⟩
    · have smaller : ∃ y, y ∈ plans ∧ Submask y x ∧ y ≠ x := by
        apply Classical.byContradiction
        intro none
        apply h
        intro y hy hsub
        apply Classical.byContradiction
        intro hne
        exact none ⟨y, hy, hsub, hne⟩
      obtain ⟨y, hy, hsub, hne⟩ := smaller
      obtain ⟨z, hz, hzy⟩ := ih y (submask_strict_lt hsub hne) hy
      exact ⟨z, hz, submask_trans hzy hsub⟩

theorem minimal_antichain {plans : List Nat} {x y : Nat}
    (hx : x ∈ minimal plans) (hy : y ∈ minimal plans) (xy : Submask x y) : x = y :=
  ((mem_minimal_iff plans y).1 hy).2 x ((mem_minimal_iff plans x).1 hx).1 xy

/-- A family covers a completion when some family member is included in it. -/
def Covers (plans : List Nat) (completion : Nat) : Prop :=
  ∃ p ∈ plans, Submask p completion

/-- Equality deduplication preserves the represented completion set. -/
theorem covers_eraseDups (plans : List Nat) (s : Nat) :
    Covers plans.eraseDups s ↔ Covers plans s := by
  simp [Covers]

/-- Minimization preserves exactly the represented completion set. -/
theorem covers_minimal (plans : List Nat) (s : Nat) :
    Covers (minimal plans) s ↔ Covers plans s := by
  constructor
  · rintro ⟨p, hp, hps⟩
    exact ⟨p, ((mem_minimal_iff plans p).1 hp).1, hps⟩
  · rintro ⟨p, hp, hps⟩
    obtain ⟨q, hq, hqp⟩ := minimal_contains_subset plans p hp
    exact ⟨q, hq, submask_trans hqp hps⟩

def conjoin (left right : List Nat) : List Nat :=
  left.flatMap fun x => right.map fun y => x ||| y

theorem covers_conjoin (left right : List Nat) (s : Nat) :
    Covers (conjoin left right) s ↔ Covers left s ∧ Covers right s := by
  constructor
  · rintro ⟨p, hp, hps⟩
    obtain ⟨x, hx, hpmap⟩ := List.mem_flatMap.1 hp
    obtain ⟨y, hy, rfl⟩ := List.mem_map.1 hpmap
    have parts := (union_submask_iff x y s).1 hps
    exact ⟨⟨x, hx, parts.1⟩, ⟨y, hy, parts.2⟩⟩
  · rintro ⟨⟨x, hx, hxs⟩, ⟨y, hy, hys⟩⟩
    exact ⟨x ||| y, List.mem_flatMap.2 ⟨x, hx, List.mem_map.2 ⟨y, hy, rfl⟩⟩,
           (union_submask_iff x y s).2 ⟨hxs, hys⟩⟩

theorem covers_append (left right : List Nat) (s : Nat) :
    Covers (left ++ right) s ↔ Covers left s ∨ Covers right s := by
  simp only [Covers, List.mem_append, or_and_right, exists_or]

private theorem singleton_bit (i j : Nat) :
    (1 <<< i).testBit j = decide (i = j) := by
  rw [Nat.shiftLeft_eq, Nat.one_mul]
  exact Nat.testBit_two_pow

theorem singleton_submask_iff (i s : Nat) : Submask (1 <<< i) s ↔ s.testBit i = true := by
  rw [submask_iff_bits]
  constructor
  · intro h
    exact h i (by rw [singleton_bit]; simp)
  · intro h j hj
    have same : i = j := by simpa only [singleton_bit, decide_eq_true_eq] using hj
    simpa [← same] using h

/-- Recurrence on finite positive syntax; a negative atom has no completion. -/
def plans (positive negative : Nat) : Formula Nat → List Nat
  | .yes => [0]
  | .no => []
  | .atom i => if positive.testBit i then [0]
      else if negative.testBit i then [] else [1 <<< i]
  | .conj l r => minimal (conjoin (plans positive negative l) (plans positive negative r))
  | .disj l r => minimal (plans positive negative l ++ plans positive negative r)

/--
Soundness and completeness for positive completion: every admissible successful
completion contains a returned plan, and a contained returned plan suffices.
The completion must avoid negative support. Relevant conflicts are handled by
`assess` before this internal recurrence is projected to a verdict.
-/
theorem plans_cover_iff (positive negative s : Nat) (f : Formula Nat)
    (avoids : s &&& negative = 0) :
    Covers (plans positive negative f) s ↔
      f.eval (fun i => (positive ||| s).testBit i) = true := by
  induction f with
  | yes => simp [plans, Covers, Submask, Formula.eval]
  | no => simp [plans, Covers, Formula.eval]
  | atom i =>
    by_cases hp : positive.testBit i = true
    · simp [plans, hp, Covers, Submask, Formula.eval]
    · by_cases hn : negative.testBit i = true
      · have hs : s.testBit i = false := by
          have h := congrArg (fun n => n.testBit i) avoids
          simpa [Nat.testBit_and, hn] using h
        simp [plans, hp, hn, hs, Covers, Formula.eval]
      · simpa [plans, hp, hn, Covers, Formula.eval] using singleton_submask_iff i s
  | conj l r il ir =>
    simp only [plans, covers_minimal, covers_conjoin, Formula.eval, Bool.and_eq_true]
    exact and_congr il ir
  | disj l r il ir =>
    simp only [plans, covers_minimal, covers_append, Formula.eval, Bool.or_eq_true]
    exact or_congr il ir

/-- Every produced plan avoids negative support. -/
theorem plans_avoid_negative (positive negative : Nat) (f : Formula Nat)
    (p : Nat) (member : p ∈ plans positive negative f) : p &&& negative = 0 := by
  induction f generalizing p with
  | yes =>
    have zero : p = 0 := by simpa [plans] using member
    simp [zero]
  | no => simp [plans] at member
  | atom i =>
    by_cases hp : positive.testBit i = true
    · have zero : p = 0 := by simpa [plans, hp] using member
      simp [zero]
    · by_cases hn : negative.testBit i = true
      · simp [plans, hp, hn] at member
      · have singleton : p = 1 <<< i := by simpa [plans, hp, hn] using member
        subst p
        apply Nat.eq_of_testBit_eq
        intro j
        rw [Nat.testBit_and, singleton_bit, Nat.zero_testBit]
        by_cases same : i = j
        · subst j
          simp [hn]
        · simp [same]
  | conj l r il ir =>
    have original := ((mem_minimal_iff _ p).1 member).1
    obtain ⟨x, hx, hpmap⟩ := List.mem_flatMap.1 original
    obtain ⟨y, hy, rfl⟩ := List.mem_map.1 hpmap
    rw [Nat.and_or_distrib_right, il x hx, ir y hy]
    rfl
  | disj l r il ir =>
    have original := ((mem_minimal_iff _ p).1 member).1
    exact (List.mem_append.1 original).elim (il p) (ir p)

/-- Every produced plan is sufficient under the supplied positive support. -/
theorem plans_sound (positive negative : Nat) (f : Formula Nat)
    (p : Nat) (member : p ∈ plans positive negative f) :
    f.eval (fun i => (positive ||| p).testBit i) = true :=
  (plans_cover_iff positive negative p f (plans_avoid_negative positive negative f p member)).1
    ⟨p, member, submask_refl p⟩

/-- Every admissible successful completion contains a produced plan. -/
theorem plans_complete (positive negative s : Nat) (f : Formula Nat)
    (avoids : s &&& negative = 0)
    (success : f.eval (fun i => (positive ||| s).testBit i) = true) :
    ∃ p ∈ plans positive negative f, Submask p s :=
  (plans_cover_iff positive negative s f avoids).2 success

/-- Produced plans form an inclusion antichain for every finite formula. -/
theorem plans_antichain (positive negative : Nat) (f : Formula Nat)
    {x y : Nat} (hx : x ∈ plans positive negative f)
    (hy : y ∈ plans positive negative f) (subset : Submask x y) : x = y := by
  cases f with
  | yes => simp only [plans, List.mem_singleton] at hx hy; exact hx.trans hy.symm
  | no => simp [plans] at hx
  | atom i =>
    cases hp : positive.testBit i <;> cases hn : negative.testBit i <;>
      simp [plans, hp, hn] at hx hy <;> simp_all
  | conj l r => exact minimal_antichain hx hy subset
  | disj l r => exact minimal_antichain hx hy subset

/-- No strictly smaller admissible positive completion suffices for a returned plan. -/
theorem plans_minimal_success (positive negative : Nat) (f : Formula Nat)
    {p s : Nat} (hp : p ∈ plans positive negative f) (subset : Submask s p)
    (avoids : s &&& negative = 0)
    (success : f.eval (fun i => (positive ||| s).testBit i) = true) : s = p := by
  obtain ⟨q, hq, hqs⟩ := plans_complete positive negative s f avoids success
  have same : q = p := plans_antichain positive negative f hq hp (submask_trans hqs subset)
  rw [same] at hqs
  have sp : s ≤ p := subset ▸ Nat.and_le_right
  have ps : p ≤ s := hqs ▸ Nat.and_le_right
  exact Nat.le_antisymm sp ps

theorem plans_empty_iff_no_completion (positive negative : Nat) (f : Formula Nat) :
    plans positive negative f = [] ↔
      ∀ s, s &&& negative = 0 → f.eval (fun i => (positive ||| s).testBit i) = false := by
  constructor
  · intro empty s avoids
    have no_cover : ¬ Covers (plans positive negative f) s := by simp [empty, Covers]
    have not_true := mt (plans_cover_iff positive negative s f avoids).2 no_cover
    simpa using not_true
  · intro impossible
    apply List.eq_nil_iff_forall_not_mem.2
    intro p hp
    have success := plans_sound positive negative f p hp
    have failure := impossible p (plans_avoid_negative positive negative f p hp)
    rw [success] at failure
    contradiction

inductive Verdict where
  | licensed
  | rejected
  | pending
  | conflict
deriving DecidableEq, Repr

def project (family : List Nat) : Verdict :=
  if 0 ∈ family then .licensed else if family = [] then .rejected else .pending

def hasConflict (positive negative : Nat) (f : Formula Nat) : Bool :=
  f.atoms.any fun i => positive.testBit i && negative.testBit i

def assess (positive negative : Nat) (f : Formula Nat) : Verdict :=
  if hasConflict positive negative f then .conflict else project (plans positive negative f)

/-- Empty obligations license precisely when the supplied positive support suffices. -/
theorem projection_licensed_iff (positive negative : Nat) (f : Formula Nat) :
    project (plans positive negative f) = .licensed ↔ f.eval positive.testBit = true := by
  have zero_cover : Covers (plans positive negative f) 0 ↔ 0 ∈ plans positive negative f := by
    simp [Covers, Submask]
  have cover := plans_cover_iff positive negative 0 f (by simp)
  simp only [Nat.or_zero] at cover
  rw [zero_cover] at cover
  have projected : project (plans positive negative f) = .licensed ↔
      0 ∈ plans positive negative f := by
    by_cases empty : plans positive negative f = []
    · simp [project, empty]
    · by_cases zero : 0 ∈ plans positive negative f <;> simp [project, empty, zero]
  exact projected.trans cover

/-- Rejection concerns this finite positive formula and its admissible completions. -/
theorem projection_rejected_iff (positive negative : Nat) (f : Formula Nat) :
    project (plans positive negative f) = .rejected ↔
      ∀ s, s &&& negative = 0 → f.eval (fun i => (positive ||| s).testBit i) = false := by
  rw [← plans_empty_iff_no_completion]
  unfold project
  by_cases zero : 0 ∈ plans positive negative f
  · have nonempty : plans positive negative f ≠ [] := by
      intro empty
      simp [empty] at zero
    simp [zero, nonempty]
  · simp [zero]

theorem conflict_precedes_projection (positive negative : Nat) (f : Formula Nat)
    (conflict : hasConflict positive negative f = true) :
    assess positive negative f = .conflict := by
  simp [assess, conflict]

theorem conflict_free_projection (positive negative : Nat) (f : Formula Nat)
    (consistent : hasConflict positive negative f = false) :
    assess positive negative f = project (plans positive negative f) := by
  simp [assess, consistent]

/-- Unknown is pending, not a negative judgment (a witness at any bit). -/
theorem unknown_atom_pending (i : Nat) : assess 0 0 (.atom i) = .pending := by
  have nonzero : 1 <<< i ≠ 0 := by simp [Nat.shiftLeft_eq]
  simp [assess, hasConflict, Formula.atoms, plans, project, Ne.symm nonzero]

end Nabt.Obligations
