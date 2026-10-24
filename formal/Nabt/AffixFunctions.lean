import Nabt.PersonEvidence
import Nabt.Derivation

set_option autoImplicit false

/-!
# Declared interpretations of Arabic units

This is an explicitly supplied grammatical vocabulary, NOT a discovered
partition of spellings. Examples are illustrations, not a surface classifier,
an exhaustive allomorph list, or authority to cut an unseen word. A unit may
have several correlated interpretations. The generic partition generator in
`UnitDiscovery` does not import this module or use its examples.

Every interpretation needs its own source, host and analysis evidence. Root
and template slots are a separate projection: their positions need not be a
contiguous substring. Pronoun features remain correlated in PersonEvidence.
Morphological number, syntactic case and a cardinal count are different axes.

Source windows and the ON/FOR comparison are recorded in
docs/UNIT_DISCOVERY_SOURCE_AUDIT.md. These declarations are new NABT knowledge
projections; their finite coverage checks do not prove linguistic acquisition.
-/

namespace Nabt.AffixFunctions

def inventoryId : String := "nabt.declared-unit-functions.v1"

inductive Layer where
  | clitic | inflection | derivation | lexical | orthographic
  deriving DecidableEq, Repr

inductive Position where
  | beforeStem | afterStem | templateSlot | wholeLexeme | realization
  deriving DecidableEq, Repr

inductive Function where
  | definiteArticle | relativeAl | conjunction | preposition | interrogative
  | futureParticle | attentionHa | deicticAddressKaf | deicticDistanceLam
  | imperfectPrefix | triliteralAugment | quadriliteralAugment
  | attachedSubjectPronoun | attachedObjectPronoun | attachedGenitivePronoun
  | femininePastTa | feminineNominalTa | feminineAlif
  | nominalDual | soundMasculinePlural | soundFemininePlural
  | fiveVerbNun | nominalDualPluralNun | femininePluralNun
  | emphaticNun | protectiveNun | tanwin
  | separatingAlif | pausalTaAsHa | radicalSlot
  | relativeLexeme | demonstrativeLexeme | dhuPossessiveLexeme
  | independentPronoun
  deriving DecidableEq, Repr

structure Declaration where
  function : Function
  key : String
  arabic : String
  layer : Layer
  positions : List Position
  examples : List String
  requirements : List String
  deriving DecidableEq, Repr

private def entry (function : Function) (key arabic : String) (layer : Layer)
    (positions : List Position) (examples requirements : List String) : Declaration :=
  ⟨function, key, arabic, layer, positions, examples,
    "independent_interpreted_source" :: requirements⟩

/-- A knowledge inventory. No declaration is a learned gate or a word analysis. -/
def declarations : List Declaration := [
  entry .definiteArticle "definite_article" "أل التعريف" .clitic [.beforeStem]
    ["ال"] ["nominal_host", "article_reading", "attachment", "orthographic_realization"],
  entry .relativeAl "relative_al" "أل الموصولة" .clitic [.beforeStem]
    ["الضارب", "المضروب"] ["explicit_adjectival_host", "non_elative_host", "relative_reading", "relative_clause"],
  entry .conjunction "conjunction" "حرف العطف المتصل" .clitic [.beforeStem]
    ["و", "ف"] ["particle_reading", "coordination_scope", "attachment"],
  entry .preposition "preposition" "حرف الجر المتصل" .clitic [.beforeStem]
    ["ب", "ل", "ك", "و", "ت"] ["particle_sense", "nominal_complement", "attachment"],
  entry .interrogative "interrogative" "همزة الاستفهام" .clitic [.beforeStem]
    ["أ"] ["question_reading", "speech_force", "attachment"],
  entry .futureParticle "future_particle" "سين الاستقبال" .clitic [.beforeStem]
    ["س"] ["imperfect_host", "future_reading", "attachment"],
  entry .attentionHa "attention_ha" "ها التنبيه" .clitic [.beforeStem]
    ["هذا", "هذه", "هؤلاء"] ["attention_reading", "deictic_host", "orthographic_realization"],
  entry .deicticAddressKaf "deictic_address_kaf" "كاف خطاب اسم الإشارة" .clitic [.afterStem]
    ["ذلك", "تلك"] ["demonstrative_host", "addressing_not_pronominal_case", "attachment"],
  entry .deicticDistanceLam "deictic_distance_lam" "لام البعد" .clitic [.afterStem]
    ["ذلك", "تلك"] ["demonstrative_host", "distance_reading", "attachment"],
  entry .imperfectPrefix "imperfect_prefix" "حرف المضارعة" .inflection [.beforeStem]
    ["أ", "ن", "ي", "ت"] ["imperfect_paradigm", "correlated_person_profile", "whole_form"],
  entry .triliteralAugment "triliteral_augment" "زيادة في قالب جذر ثلاثي" .derivation
    [.beforeStem, .templateSlot, .afterStem] ["أفعل", "انفعل", "افتعل", "استفعل"]
    ["root_arity_three", "complete_typed_pattern", "whole_form_replay", "lexical_family"],
  entry .quadriliteralAugment "quadriliteral_augment" "زيادة في قالب جذر رباعي" .derivation
    [.beforeStem, .templateSlot, .afterStem] ["تدحرج", "احرنجم", "اقشعرّ"]
    ["root_arity_four", "complete_typed_pattern", "whole_form_replay", "lexical_family"],
  entry .attachedSubjectPronoun "attached_subject_pronoun" "ضمير رفع متصل" .inflection [.afterStem]
    ["تُ", "تَ", "تِ", "نا", "تما", "تم", "تنّ", "ا", "و", "ي", "ن"]
    ["verbal_host", "subject_slot", "correlated_person_profile", "paradigm", "attachment"],
  entry .attachedObjectPronoun "attached_object_pronoun" "ضمير نصب متصل" .clitic [.afterStem]
    ["ي", "نا", "كَ", "كِ", "كما", "كم", "كنّ", "ه", "ها", "هما", "هم", "هنّ"]
    ["governing_host", "object_slot", "correlated_person_profile", "attachment", "reference"],
  entry .attachedGenitivePronoun "attached_genitive_pronoun" "ضمير جر متصل" .clitic [.afterStem]
    ["ي", "نا", "كَ", "كِ", "كما", "كم", "كنّ", "ه", "ها", "هما", "هم", "هنّ"]
    ["noun_or_preposition_host", "genitive_slot", "correlated_person_profile", "attachment", "reference"],
  entry .femininePastTa "feminine_past_ta" "تاء التأنيث الساكنة" .inflection [.afterStem]
    ["تْ"] ["perfect_host", "feminine_subject_agreement", "not_subject_pronoun", "whole_form"],
  entry .feminineNominalTa "feminine_nominal_ta" "تاء التأنيث الاسمية" .derivation [.afterStem]
    ["ة", "ت"] ["nominal_lexical_family", "morphological_marker", "lexical_gender_separate"],
  entry .feminineAlif "feminine_alif" "ألف التأنيث المقصورة أو الممدودة" .derivation [.afterStem]
    ["ى", "اء"] ["nominal_lexical_family", "nonradical_pattern", "feminine_alif_class"],
  entry .nominalDual "nominal_dual" "علامة تثنية الاسم" .inflection [.afterStem]
    ["ان", "ين", "ا", "ي"] ["nominal_dual_class", "case_frame", "nun_presence_or_idafa"],
  entry .soundMasculinePlural "sound_masculine_plural" "علامة جمع المذكر السالم" .inflection [.afterStem]
    ["ون", "ين", "و", "ي"] ["sound_masculine_class", "case_frame", "nun_presence_or_idafa"],
  entry .soundFemininePlural "sound_feminine_plural" "ألف وتاء الجمع" .inflection [.afterStem]
    ["ات"] ["sound_feminine_morphology", "nominal_paradigm", "lexical_gender_separate"],
  entry .fiveVerbNun "five_verb_nun" "نون رفع الأفعال الخمسة" .inflection [.afterStem]
    ["ان", "ون", "ين"] ["five_verb_family", "indicative_frame", "subject_pronoun", "nun_attachment"],
  entry .nominalDualPluralNun "nominal_dual_plural_nun" "نون المثنى والجمع" .inflection [.afterStem]
    ["ان", "ين", "ون"] ["nominal_dual_or_sound_masculine", "nun_attachment", "not_idafa_head"],
  entry .femininePluralNun "feminine_plural_nun" "نون النسوة" .inflection [.afterStem]
    ["نَ"] ["verbal_paradigm", "subject_pronoun", "feminine_plural_profile", "attachment"],
  entry .emphaticNun "emphatic_nun" "نون التوكيد الثقيلة أو الخفيفة" .inflection [.afterStem]
    ["نّ", "نْ"] ["verbal_host", "emphasis_reading", "direct_or_separated_attachment"],
  entry .protectiveNun "protective_nun" "نون الوقاية" .inflection [.afterStem]
    ["ني"] ["licensed_host_class", "first_person_ya", "host_nun_ya_segmentation"],
  entry .tanwin "tanwin" "التنوين الاسمي: التمكين والتنكير والمقابلة والعوض" .inflection [.afterStem]
    ["ٌ", "ٍ", "ً"] ["tanwin_kind", "nominal_class", "definiteness_separate", "orthographic_realization"],
  entry .separatingAlif "separating_alif" "الألف الفارقة المكتوبة" .orthographic [.realization]
    ["كتبوا"] ["plural_subject_waw", "orthographic_rule", "not_extra_pronoun"],
  entry .pausalTaAsHa "pausal_ta_as_ha" "تحقيق تاء التأنيث هاء في الوقف" .orthographic [.realization]
    ["رحمة"] ["lexical_ta_marbuta", "pause_mode", "written_source_preserved"],
  entry .radicalSlot "radical_slot" "خانة أصلية في الجذر" .derivation [.templateSlot]
    ["ن", "ت", "ه", "و", "ي"] ["typed_root_slot", "complete_pattern", "whole_form_replay", "lexical_family"],
  entry .relativeLexeme "relative_lexeme" "اسم موصول" .lexical [.wholeLexeme]
    ["الذي", "التي", "الذين", "اللاتي", "اللائي", "اللذان", "اللتان", "ذو", "ذا"]
    ["whole_lexeme_reading", "relative_clause", "dialect_or_construction", "no_automatic_article_strip"],
  entry .demonstrativeLexeme "demonstrative_lexeme" "اسم إشارة" .lexical [.wholeLexeme]
    ["ذا", "ذي", "ذه", "تي", "تا", "ذان", "تان", "أولاء"]
    ["whole_lexeme_reading", "deictic_reference", "number_and_gender_profile"],
  entry .dhuPossessiveLexeme "dhu_possessive_lexeme" "ذو بمعنى صاحب وصورها الإعرابية" .lexical [.wholeLexeme]
    ["ذو", "ذا", "ذي"] ["possessive_sense", "nominal_class", "case_frame", "idafa_complement"],
  entry .independentPronoun "independent_pronoun" "ضمير منفصل" .lexical [.wholeLexeme]
    ["أنا", "نحن", "أنت", "أنتما", "أنتم", "أنتن", "هو", "هي", "هما", "هم", "هن", "إياي", "إياك"]
    ["whole_pronoun_paradigm", "person_profile", "reference"]
]

/-- Existing correlated inventories are exposed as declared premises only. -/
def declaredPersonProfiles := PersonEvidence.profiles
def declaredAttachedAllomorphs := PersonEvidence.attachedForms
def declaredImperfectProfiles (family : PersonEvidence.Family) (pre : String) :=
  PersonEvidence.candidates family pre

theorem declaration_keys_unique : (declarations.map Declaration.key).Nodup := by decide
theorem each_function_declared (function : Function) :
    function ∈ declarations.map Declaration.function := by cases function <;> decide
theorem declarations_require_interpreted_source : declarations.all (fun d =>
    d.requirements.contains "independent_interpreted_source") = true := by decide
theorem declarations_have_positions : declarations.all (fun d => !d.positions.isEmpty) = true := by decide
theorem declarative_ta_preserves_person_ambiguity :
    (declaredImperfectProfiles .plain "ت").map PersonEvidence.Profile.qac = ["2MS", "3FS"] := by decide
theorem bare_alif_is_not_declared_imperfect_hamza :
    declaredImperfectProfiles .plain "ا" = [] := by decide

end Nabt.AffixFunctions
