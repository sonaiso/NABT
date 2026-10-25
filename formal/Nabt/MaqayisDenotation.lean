import Nabt.LexicalCatalog
import Nabt.MaqayisRules

/-! The author's proposed root origins are interpreted separately from a
lexical use. Neither a root number nor a shared root selects a token sense. -/
namespace Nabt.MaqayisDenotation
open LexicalDenotation LexicalCatalog

def lawId := "nabt.maqayis-selected-denotation.v1"

theorem bayt_origin_whole :
    check necessities sense13 .matching ["مجمع الشمل", "المأوى", "المآب"] = true := by decide

theorem sayf_origin_part :
    check necessities sense14 .inclusion ["طول"] = true := by decide

theorem root_cause_is_not_mental_necessity :
    check necessities sense14 .entailment ["طول"] = false := by decide

theorem cross_dictionary_gloss_not_automatically_equal :
    across necessities [some sense0, some sense12] .matching ["علم الشيء"] = false := by decide

theorem ilm_ambiguity_retained :
    MaqayisRules.Sense.flag ∈ MaqayisRules.senses ∧
    MaqayisRules.Sense.knowledge ∈ MaqayisRules.senses ∧
    MaqayisRules.Sense.flag ≠ MaqayisRules.Sense.knowledge :=
  MaqayisRules.root_does_not_determine_sense

end Nabt.MaqayisDenotation
