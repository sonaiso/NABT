import Nabt.LexicalCatalog

/-! Selected Lisan readings, not a complete formalization of the dictionary.
Exact source spans are replayed by build_lexical_catalog.py. A gloss is kept
atomic unless the explicit interpretation separately licenses decomposition. -/
namespace Nabt.LisanRules
open LexicalDenotation LexicalCatalog

def lawId := "nabt.lisan-selected-denotation.v1"

theorem qalam_ambiguity_blocks_single_gloss :
    across necessities ((forRoot "قلم").map some) .matching ["الذي يكتب به"] = false := by decide

theorem ear_word_not_automatically_part_of_hearing :
    check necessities sense5 .inclusion ["الأذن"] = false := by decide

theorem mental_association_needs_other_source :
    check [] sense10 .entailment ["الشجاعة"] = false ∧
    check necessities sense10 .entailment ["الشجاعة"] = true := by decide

theorem naming_reason_cannot_replace_mental_rule :
    check [⟨sense10, "الشجاعة", .namingReason, sense10.citation⟩]
      sense10 .entailment ["الشجاعة"] = false := by decide

theorem external_only_cannot_replace_mental_rule :
    check [⟨sense10, "الشجاعة", .externalOnly, sense10.citation⟩]
      sense10 .entailment ["الشجاعة"] = false := by decide

end Nabt.LisanRules
