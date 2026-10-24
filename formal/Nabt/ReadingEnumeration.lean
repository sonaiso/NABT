import Nabt.MantuqMafhum

/-!
Exhaustive composition of finite candidate pools, not exhaustive Arabic parsing.
`Selects` is the declarative grammar: one alternative from each ordered pool.
Lean enumerates that relation, keeps incomplete alternatives and exact bindings,
and checks one proof per combination. No caller-supplied coverage flag is used.
The linguistic adequacy and completeness of the pools remain explicit premises.
-/
namespace Nabt.ReadingEnumeration
open SourceSemantics MantuqMafhum

def lawId : String := "nabt.reading-enumeration.v1"

structure Alternative where
  identity : String
  binding : Binding
  premises : Option (List Formula)
  deriving DecidableEq, Repr

inductive Selects : List (List Alternative) → List Alternative → Prop
  | nil : Selects [] []
  | cons {pool pools a rest} : a ∈ pool → Selects pools rest →
      Selects (pool :: pools) (a :: rest)

def enumerate : List (List Alternative) → List (List Alternative)
  | [] => [[]]
  | pool :: pools => pool.flatMap fun a => (enumerate pools).map (a :: ·)

theorem enumeration_exact (pools : List (List Alternative)) (selection : List Alternative) :
    selection ∈ enumerate pools ↔ Selects pools selection := by
  induction pools generalizing selection with
  | nil =>
    constructor
    · intro h
      have : selection = [] := by simpa [enumerate] using h
      subst selection
      exact .nil
    · intro h
      cases h
      simp [enumerate]
  | cons pool pools ih =>
    constructor
    · intro h
      obtain ⟨a, ha, mapped⟩ := List.mem_flatMap.mp h
      obtain ⟨rest, hr, same⟩ := List.mem_map.mp mapped
      subst selection
      exact .cons ha ((ih rest).mp hr)
    · intro h
      cases h with
      | cons ha hr =>
        exact List.mem_flatMap.mpr ⟨_, ha, List.mem_map.mpr ⟨_, (ih _).mpr hr, rfl⟩⟩

def count : List (List Alternative) → Nat
  | [] => 1
  | pool :: pools => pool.length * count pools

theorem enumeration_count (pools : List (List Alternative)) :
    (enumerate pools).length = count pools := by
  induction pools with
  | nil => rfl
  | cons pool pools ih =>
    simp only [enumerate, count]
    induction pool with
    | nil => simp
    | cons a rest ihr =>
      simp [List.flatMap_cons, ih, ihr, Nat.add_mul, Nat.add_comm]

def combine : List Alternative → Option (List Formula)
  | [] => some []
  | a :: rest => do return (← a.premises) ++ (← combine rest)

theorem incomplete_preserved (selection : List Alternative) (a : Alternative)
    (member : a ∈ selection) (missing : a.premises = none) : combine selection = none := by
  induction selection with
  | nil => simp at member
  | cons head rest ih =>
    rcases List.mem_cons.mp member with same | tail
    · subst head
      simp [combine, missing]
    · simp [combine, ih tail]

theorem combined_premises_hold (selection : List Alternative) (ps : List Formula)
    (model : String → List String → Prop) (env : Nat → String)
    (truth : ∀ a ∈ selection, ∀ qs, a.premises = some qs → PremisesHold qs model env)
    (complete : combine selection = some ps) : PremisesHold ps model env := by
  induction selection generalizing ps with
  | nil =>
    have : ps = [] := by simpa [combine] using complete.symm
    subst ps
    simp [PremisesHold]
  | cons a rest ih =>
    cases hp : a.premises with
    | none => simp [combine, hp] at complete
    | some qs =>
      cases hr : combine rest with
      | none => simp [combine, hp, hr] at complete
      | some rs =>
        have same : qs ++ rs = ps := by simpa [combine, hp, hr] using complete
        subst ps
        intro f member
        rcases List.mem_append.mp member with left | right
        · exact truth a (by simp) qs hp f left
        · exact ih rs (fun b hb => truth b (by simp [hb])) hr f right

def bound (expected : Binding) (selection : List Alternative) : Bool :=
  selection.all fun a => decide (a.binding = expected)

def result (selection : List Alternative) (proof : Proof) : Option Formula := do
  infer (← combine selection) proof

def verifyRows (expected : Binding) (target : Formula) :
    List (List Alternative) → List Proof → Bool
  | [], [] => true
  | row :: rows, proof :: proofs =>
      bound expected row && decide (result row proof = some target) &&
        verifyRows expected target rows proofs
  | _, _ => false

theorem verified_rows_length (expected : Binding) (target : Formula)
    (rows : List (List Alternative)) (proofs : List Proof)
    (checked : verifyRows expected target rows proofs = true) : rows.length = proofs.length := by
  induction rows generalizing proofs with
  | nil => cases proofs <;> simp_all [verifyRows]
  | cons row rows ih =>
    cases proofs with
    | nil => simp [verifyRows] at checked
    | cons proof proofs =>
      simp only [verifyRows, Bool.and_eq_true_iff] at checked
      simp [ih proofs checked.2]

theorem verified_rows_each (expected : Binding) (target : Formula)
    (rows : List (List Alternative)) (proofs : List Proof)
    (checked : verifyRows expected target rows proofs = true)
    (row : List Alternative) (member : row ∈ rows) :
    (∀ a ∈ row, a.binding = expected) ∧ ∃ proof, result row proof = some target := by
  induction rows generalizing proofs with
  | nil => simp at member
  | cons head rows ih =>
    cases proofs with
    | nil => simp [verifyRows] at checked
    | cons proof proofs =>
      simp only [verifyRows, Bool.and_eq_true_iff, decide_eq_true_eq] at checked
      rcases List.mem_cons.mp member with same | tail
      · subst head
        exact ⟨by simpa [bound, List.all_eq_true] using checked.1.1, ⟨proof, checked.1.2⟩⟩
      · exact ih proofs checked.2 tail

/-- Neither an empty document nor an empty pool can yield a vacuous verdict. -/
def check (expected : Binding) (pools : List (List Alternative))
    (target : Formula) (proofs : List Proof) : Bool :=
  !pools.isEmpty && (count pools != 0) &&
    verifyRows expected target (enumerate pools) proofs

theorem checked_selection (expected : Binding) (pools : List (List Alternative))
    (target : Formula) (proofs : List Proof) (checked : check expected pools target proofs = true)
    (selection : List Alternative) (licensed : Selects pools selection) :
    (∀ a ∈ selection, a.binding = expected) ∧ ∃ proof, result selection proof = some target := by
  simp only [check, Bool.and_eq_true_iff] at checked
  exact verified_rows_each expected target _ proofs checked.2 selection
    ((enumeration_exact pools selection).mpr licensed)

theorem checked_certificate_count (expected : Binding) (pools : List (List Alternative))
    (target : Formula) (proofs : List Proof) (checked : check expected pools target proofs = true) :
    proofs.length = count pools := by
  simp only [check, Bool.and_eq_true_iff] at checked
  exact (verified_rows_length expected target _ proofs checked.2).symm.trans (enumeration_count pools)

theorem omitted_combination_rejected (expected : Binding) (pools : List (List Alternative))
    (target : Formula) (proofs : List Proof) (different : proofs.length ≠ count pools) :
    check expected pools target proofs = false := by
  cases h : check expected pools target proofs with
  | false => rfl
  | true => exact False.elim (different (checked_certificate_count expected pools target proofs h))

theorem every_selection_entails (expected : Binding) (pools : List (List Alternative))
    (target : Formula) (proofs : List Proof) (checked : check expected pools target proofs = true)
    (selection : List Alternative) (licensed : Selects pools selection)
    (model : String → List String → Prop) (env : Nat → String)
    (truth : ∀ a ∈ selection, ∀ ps, a.premises = some ps → PremisesHold ps model env) :
    target.meaning model env := by
  obtain ⟨_, proof, accepted⟩ := checked_selection expected pools target proofs checked selection licensed
  cases complete : combine selection with
  | none => simp [result, complete] at accepted
  | some ps =>
    have inferred : infer ps proof = some target := by simpa [result, complete] using accepted
    exact infer_sound ps proof target model env
      (combined_premises_hold selection ps model env truth complete) inferred

theorem incomplete_selection_blocks (expected : Binding) (pools : List (List Alternative))
    (target : Formula) (proofs : List Proof) (selection : List Alternative)
    (licensed : Selects pools selection) (a : Alternative) (member : a ∈ selection)
    (missing : a.premises = none) : check expected pools target proofs = false := by
  cases h : check expected pools target proofs with
  | false => rfl
  | true =>
    obtain ⟨_, proof, accepted⟩ := checked_selection expected pools target proofs h selection licensed
    simp [result, incomplete_preserved selection a member missing] at accepted

theorem changed_binding_blocks (expected : Binding) (pools : List (List Alternative))
    (target : Formula) (proofs : List Proof) (selection : List Alternative)
    (licensed : Selects pools selection) (a : Alternative) (member : a ∈ selection)
    (changed : a.binding ≠ expected) : check expected pools target proofs = false := by
  cases h : check expected pools target proofs with
  | false => rfl
  | true => exact False.elim (changed ((checked_selection expected pools target proofs h selection licensed).1 a member))

theorem empty_document_blocks (expected : Binding) (target : Formula) (proofs : List Proof) :
    check expected [] target proofs = false := by simp [check]

/-- A late empty pool is rejected before evaluating even a huge empty product. -/
theorem zero_count_blocks (expected : Binding) (pools : List (List Alternative))
    (target : Formula) (proofs : List Proof) (empty : count pools = 0) :
    check expected pools target proofs = false := by simp [check, empty]

/-- Resource exhaustion has no Boolean verdict; no prefix is checked. -/
def boundedCheck (limit : Nat) (expected : Binding) (pools : List (List Alternative))
    (target : Formula) (proofs : List Proof) : Option Bool :=
  if count pools > limit then none else some (check expected pools target proofs)

theorem bounded_check_exact (limit : Nat) (expected : Binding) (pools : List (List Alternative))
    (target : Formula) (proofs : List Proof) :
    boundedCheck limit expected pools target proofs = some true ↔
      count pools ≤ limit ∧ check expected pools target proofs = true := by
  simp [boundedCheck]

theorem resource_exhaustion_no_verdict (limit : Nat) (expected : Binding)
    (pools : List (List Alternative)) (target : Formula) (proofs : List Proof)
    (exhausted : count pools > limit) :
    boundedCheck limit expected pools target proofs = none := by simp [boundedCheck, exhausted]

end Nabt.ReadingEnumeration
