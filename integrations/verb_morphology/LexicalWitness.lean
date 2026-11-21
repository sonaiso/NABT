import A116.QiraaMadlul

namespace PortCheck.Lexical
open A116 A116.QiraaMadlul

/-- These are the formal connected-speech cells. POS and the usage relation are supplied. -/
def wording : A116.Tarkib.Tarkib := [kw "نَطَقَ" .fil, kw "لْحَجَرُ" .ism]

theorem withdrawRelation :
    hQ wording = ⟨true, some .majaz⟩ ∧ hQbila wording = ⟨true, some .laHukm⟩ := by
  decide +kernel

theorem withdrawGenusMapping :
    (qiraa mujamShahid HukmMuwahhad.tashbih wording).isSome = true ∧
    (qiraa { mujamShahid with ajnas := [] } HukmMuwahhad.tashbih wording).isSome = false := by
  decide +kernel

#print axioms withdrawRelation
#print axioms withdrawGenusMapping
end PortCheck.Lexical
