import Nabt.Derivation

namespace MasdarReference
open Nabt.Derivation

structure Row (n : Nat) where
  pattern : Pattern n
  root : Root n
  sense : String
  role : String

/-- Natural join of an adopted dictionary row with the exact-pattern reference and
a separately supplied admissibility check for that reading's sense and role. -/
def select (ps : List (Pattern n)) (text : List Char) (rows : List (Row n))
    (allowed : String → String → Bool) : List (Row n) :=
  rows.filter fun r =>
    decide (r.pattern ∈ ps) && decide (Complete r.pattern) &&
    (fill r.pattern r.root == text) && allowed r.sense r.role

theorem select_exact (ps : List (Pattern n)) (text : List Char)
    (rows : List (Row n)) (allowed : String → String → Bool) (r : Row n) :
    r ∈ select ps text rows allowed ↔ r ∈ rows ∧
      (r.pattern,r.root) ∈ readings ps text ∧ allowed r.sense r.role = true := by
  simp only [select, List.mem_filter, Bool.and_eq_true, decide_eq_true_eq,
             beq_iff_eq, mem_readings_iff, recover_exact_iff]
  constructor
  · rintro ⟨hr,⟨⟨hp,hc⟩,hf⟩,ha⟩
    exact ⟨hr,⟨hp,hc,hf⟩,ha⟩
  · rintro ⟨hr,⟨hp,hc,hf⟩,ha⟩
    exact ⟨hr,⟨⟨hp,hc⟩,hf⟩,ha⟩

def ziRaaAh : Pattern 3 :=
 [.slot 0,.literal 'ِ',.slot 1,.literal 'َ',.literal 'ا',.slot 2,.literal 'َ',.literal 'ة']

def zra : Root 3 := fun i => #['ز','ر','ع'][i.val]!

theorem ziraa_shape : recover ziRaaAh "زِرَاعَة".toList = some zra := by
  apply (recover_exact_iff ..).2
  exact ⟨by decide, by decide⟩

end MasdarReference
#print axioms MasdarReference.select_exact
#print axioms MasdarReference.ziraa_shape
