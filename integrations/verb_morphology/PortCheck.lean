import A116.Numbering
import A116.Alif
import A116.Ishtiqaq
import A116.Sawabiq
import Nabt.Bridges
import Nabt.Derivation
import Nabt.Law
import Lean.Data.Json

namespace PortCheck

def mark : A116.Haraka → Nabt.Mark
  | .fatha => 0 | .damma => 1 | .kasra => 2 | .sukun => 3

def toNabt (c : A116.Cell) : Nabt.Cell := ⟨c.carrier, mark c.haraka⟩
def toExternal (c : Nabt.Cell) : A116.Cell := ⟨c.carrier, A116.Numbering.harakaOf c.mark.val⟩

theorem roundTripUp (c : A116.Cell) : toExternal (toNabt c) = c := by
  rcases c with ⟨l, h⟩; cases h <;> rfl

theorem roundTripDown (c : Nabt.Cell) : toNabt (toExternal c) = c := by
  rcases c with ⟨l, h⟩
  suffices hm : mark (A116.Numbering.harakaOf h.val) = h by
    exact congrArg (Nabt.Cell.mk l) hm
  revert h; decide +kernel

theorem bridgeIndexAgrees (c : A116.Cell) :
    A116.Numbering.bridgeIndex c = (Nabt.Bridges.encodeCell .alghanemBridge (toNabt c)).val := by
  rcases c with ⟨l, h⟩; cases h <;> revert l <;> decide +kernel

def token : A116.Ishtiqaq.Sym Char → Nabt.Derivation.Token 3
  | .lit c => .literal c
  | .slot i => .slot i

theorem fillAgrees (t : A116.Ishtiqaq.Template Char) (r : Nabt.Derivation.Root 3) :
    Nabt.Derivation.fill (t.map token) r = A116.Ishtiqaq.fill t r := by
  induction t with
  | nil => rfl
  | cons s t ih => cases s <;> simp [Nabt.Derivation.fill, A116.Ishtiqaq.fill, token,
      Nabt.Derivation.evaluate, A116.Ishtiqaq.fillSym] at ih ⊢ <;> exact ih

theorem acceptIff (t : A116.Ishtiqaq.Template Char) (w : List Char) (r : Nabt.Derivation.Root 3) :
    Nabt.Derivation.recover (t.map token) w = some r ↔
    Nabt.Derivation.Complete (t.map token) ∧ A116.Ishtiqaq.fill t r = w := by
  rw [Nabt.Derivation.recover_exact_iff, fillAgrees]

def cellNumbers (s : List A116.Cell) := s.map fun c => (toNabt c).encode.val
theorem transitionDifferent :
    A116.run .awaiting [⟨⟨0, by decide⟩, .fatha⟩] = .afterSeed ∧
    Nabt.Law.step 0 (toNabt ⟨⟨0, by decide⟩, .fatha⟩).encode = 96 := by decide +kernel

theorem strongerAlifFilter :
    A116.Alif.licensable.contains ⟨⟨0, by decide⟩, .fatha⟩ = false := by decide +kernel

open A116.Ishtiqaq in
theorem changedVowel :
    extract t_past_I_a "كُتِب".toList = "كتب".toList ∧
    Nabt.Derivation.recover (t_past_I_a.map token) "كُتِب".toList = none := by decide +kernel

#print axioms roundTripUp
#print axioms roundTripDown
#print axioms bridgeIndexAgrees
#print axioms fillAgrees
#print axioms acceptIff
#print axioms transitionDifferent
#print axioms strongerAlifFilter
#print axioms changedVowel

end PortCheck
