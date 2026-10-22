import Nabt.Cell
import Nabt.Transition

/-!
Versioned sound-shape law, adapted from Saleh1967/Mashru SLGE/Law.lean
at df6bcc9eb9b536db3684cc8a2eb773c2c9f01136. NABT uses its own canonical
carrier order, connected by an exhaustively checked permutation.

The finite declarations below are a model. Their formal verification does not
establish completeness of the Arabic lexicon, syntax, or source attestation.
In this release alphabet size is 116: word boundary token 116 is excluded.
-/
namespace Nabt.Law

set_option maxRecDepth 100000
set_option maxHeartbeats 10000000

def sourceCommit := "df6bcc9eb9b536db3684cc8a2eb773c2c9f01136"
def lawId := "nabt-sound-shape-v1"
def alphabetId := "nabt.a116.v1"

def toSlgeCarrier : List Nat :=
  [2,26,18,24,9,4,6,17,23,15,19,20,10,21,12,16,22,3,5,25,7,8,13,27,14,1,28,11,0]
def fromSlgeCarrier : List Nat :=
  [28,25,0,17,5,18,6,20,21,4,12,27,14,22,24,9,15,7,2,10,11,13,16,8,3,19,1,23,26]

def toSlge (a : Nat) : Nat := 4 * toSlgeCarrier.getD (a / 4) 0 + a % 4
def fromSlge (a : Nat) : Nat := 4 * fromSlgeCarrier.getD (a / 4) 0 + a % 4

theorem permutation_bound : ∀ a : Atom, toSlge a.val < 116 := by decide +kernel
theorem permutation_inverse : ∀ a : Atom, fromSlge (toSlge a.val) = a.val := by decide +kernel
theorem permutation_inverse_other : ∀ a : Atom, toSlge (fromSlge a.val) = a.val := by decide +kernel
theorem permutation_mark : ∀ a : Atom, toSlge a.val % 4 = a.val % 4 := by decide +kernel

def groups : List Nat :=
  [0,0,0,1,1,2,2,3,4,5,5,5,6,7,8,9,10,10,10,11,11,11,12,12,12,13,14,14,14]
def group (c : Nat) : Nat := groups.getD c 15
def weak (c : Nat) : Bool := c == 2 || c == 11 || c == 28
def conflict (k m : Nat) : Bool := group k == group m && k != m && !weak k && !weak m
def maddOf (h : Nat) : Nat := [2,28,11].getD h 2

/-- Internal SLGE-order transition, including its declared boundary symbol. -/
def rawStep (q a : Nat) : Nat :=
  if 96 ≤ q ∨ 117 ≤ a then 96
  else if a = 116 then (if (1 ≤ q ∧ q ≤ 4) ∨ 67 ≤ q then 37 else if 6 ≤ q ∧ q < 35 then q + 32 else 96)
  else if a / 4 = 2 ∧ (a % 4 < 3 ∨ q ≠ 1) then 96
  else if a % 4 < 3 then
    (if q ≤ 4 ∨ q = 37 then 1 + a % 4
     else if 6 ≤ q ∧ q < 35 then (if a / 4 = q - 6 then 1 + a % 4 else 96)
     else if 38 ≤ q ∧ q < 67 then (if a / 4 = q - 38 then 1 + a % 4 else 96)
     else if 67 ≤ q then (if conflict (q - 67) (a / 4) then 96 else 1 + a % 4)
     else 96)
  else
    (if 1 ≤ q ∧ q ≤ 3 then (if a / 4 = maddOf (q - 1) then 4 else 67 + a / 4)
     else if q = 4 then 6 + a / 4 else if 67 ≤ q then 35
     else if 6 ≤ q ∧ q < 35 then 36 else 96)

def rawCost (q a : Nat) : Nat :=
  if a < 116 ∧ a % 4 = 3 ∧ 1 ≤ q ∧ q ≤ 3 ∧ a / 4 = maddOf (q - 1) then 0
  else if a = 116 then 0 else 1

def step (q : Nat) (a : Atom) : Nat := rawStep q (toSlge a.val)
def cost (q : Nat) (a : Atom) : Nat := rawCost q (toSlge a.val)
def finalWaqf (q : Nat) : Bool := decide ((1 ≤ q ∧ q ≤ 36) ∨ (67 ≤ q ∧ q < 96))
def finalWasl (q : Nat) : Bool := decide ((1 ≤ q ∧ q ≤ 34) ∨ (67 ≤ q ∧ q < 96))

def machine (wasl : Bool) : Machine Nat Atom :=
  ⟨step, cost, if wasl then finalWasl else finalWaqf⟩

def pot (q : Nat) : Nat :=
  if q = 0 then 0 else if q ≤ 3 then 2 else if q = 4 then 1
  else if q < 35 then 1 else if q = 35 then 2 else if q = 36 then 1
  else if 67 ≤ q ∧ q < 96 then 2 else 0

theorem state_closed : ∀ q : Fin 97, ∀ a : Atom, step q.val a < 97 := by decide +kernel
theorem step_potential : ∀ q : Fin 96, ∀ a : Atom, step q.val a ≠ 96 →
    1 + pot (step q.val a) ≤ 3 * cost q.val a + pot q.val := by decide +kernel
theorem dead_absorbing (a : Atom) : step 96 a = 96 := by simp [step, rawStep]

theorem run_dead (mode : Bool) (xs : List Atom) : (machine mode).run 96 xs = 96 := by
  induction xs with
  | nil => rfl
  | cons a xs ih => simpa only [Machine.run, machine, dead_absorbing] using ih

theorem bound_aux (mode : Bool) : ∀ (xs : List Atom) (q : Nat), q < 96 →
    (machine mode).run q xs ≠ 96 →
    xs.length + pot ((machine mode).run q xs) ≤ 3 * (machine mode).weight q xs + pot q
  | [], q, _, _ => by simp [Machine.run, Machine.weight]
  | a :: xs, q, hq, halive => by
    have hn : step q a ≠ 96 := by
      intro he
      apply halive
      show (machine mode).run (step q a) xs = 96
      rw [he, run_dead]
    have hclose : step q a < 97 := state_closed ⟨q, by omega⟩ a
    have hnext : step q a < 96 := by omega
    have hs : 1 + pot (step q a) ≤ 3 * cost q a + pot q := step_potential ⟨q, hq⟩ a hn
    have ht := bound_aux mode xs (step q a) hnext halive
    simp only [List.length_cons, Machine.run, Machine.weight, machine] at *
    omega

theorem suffix_fuel_bound (mode : Bool) (xs : List Atom) (q : Nat) (hq : q < 96)
    (halive : (machine mode).run q xs ≠ 96) :
    xs.length ≤ 3 * (machine mode).weight q xs + pot q := by
  have := bound_aux mode xs q hq halive
  omega

theorem word_fuel_bound (mode : Bool) (xs : List Atom)
    (halive : (machine mode).run 0 xs ≠ 96) :
    xs.length ≤ 3 * (machine mode).weight 0 xs := by
  simpa only [pot, ↓reduceIte, Nat.add_zero] using suffix_fuel_bound mode xs 0 (by decide) halive

/-- Regression witnesses: canonical kaf=21, alif=0. -/
theorem incorrect_alif_rejected :
    (machine false).run 0 [⟨85, by decide⟩, ⟨3, by decide⟩] = 96 := by decide
theorem matching_alif_accepted :
    (machine false).Licensed 0 [⟨84, by decide⟩, ⟨3, by decide⟩] := by decide
theorem repeated_alif_rejected :
    (machine false).run 0 [⟨84, by decide⟩, ⟨3, by decide⟩, ⟨3, by decide⟩] = 96 := by decide
theorem zero_weight_suffix :
    (machine false).weight 1 [⟨3, by decide⟩] = 0 ∧
    (machine false).Licensed 1 [⟨3, by decide⟩] := by decide

end Nabt.Law
