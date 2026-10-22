import Nabt.Count
import Nabt.Law

/-!
The potential theorem supplies an exhaustive, finite bound for the concrete
declared word machine, including zero-weight suffixes. This module connects
the generic counting specification to that bound. It does not identify an
accepted shape with an attested Arabic word, root, syntactic role, or meaning.
-/
namespace Nabt.Law

def alphabet : List Atom := List.finRange 116

def boundedWords (mode : Bool) (q w : Nat) : List (List Atom) :=
  Count.enumeration (machine mode) alphabet (3 * w + pot q) w q

def wordCount (mode : Bool) (q w : Nat) : Nat :=
  Count.count (machine mode) alphabet (3 * w + pot q) w q

theorem final_dead (mode : Bool) : (machine mode).final 96 = false := by
  cases mode <;> decide

theorem licensed_alive (mode : Bool) (q : Nat) (xs : List Atom)
    (h : (machine mode).Licensed q xs) : (machine mode).run q xs ≠ 96 := by
  intro hr
  have hf : (machine mode).final ((machine mode).run q xs) = true := h
  rw [hr, final_dead] at hf
  contradiction

theorem boundedWords_exact (mode : Bool) (q w : Nat) (hq : q < 96) (xs : List Atom) :
    xs ∈ boundedWords mode q w ↔
      (machine mode).weight q xs = w ∧ (machine mode).Licensed q xs := by
  constructor
  · intro h
    exact (Count.enumeration_sound (machine mode) alphabet (3 * w + pot q) w q xs h).2
  · rintro ⟨hw, hf⟩
    apply Count.enumeration_complete
    · have hb := suffix_fuel_bound mode xs q hq (licensed_alive mode q xs hf)
      simpa only [hw] using hb
    · intro a _
      simp [alphabet]
    · exact hw
    · exact hf

theorem boundedWords_nodup (mode : Bool) (q w : Nat) : (boundedWords mode q w).Nodup :=
  Count.enumeration_nodup (machine mode) alphabet (List.nodup_finRange 116) _ _ _

theorem wordCount_exact (mode : Bool) (q w : Nat) :
    wordCount mode q w = (boundedWords mode q w).length :=
  Count.count_eq_enumeration_length (machine mode) alphabet _ _ _

end Nabt.Law
