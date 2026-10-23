import Nabt.Derivation

/-!
# Bounded nominal shapes transcribed from primary grammar passages

This is NEW_GRAMMAR_PROJECTION, not a copied upstream Lean inventory.
The exact source windows, UTF-8 hashes, conditions, and token lists are in
`evidence/derivation/nominal_pattern_sources.json` at the pinned Alghanem
corpus commit 9d8fa03a51f894416e0abaf3b6821c5ae6441dcd.

The following proofs concern complete formal templates and exact recovery.
A pattern label is a source-associated reading proposal. It does not prove
a word is a masdar, instrument, place, adjective, diminutive or comparative;
it does not prove an attested root, nominal base, productive derivation,
voice, tense, case or syntactic role. The grammar states further premises.

Arity counts independent consonant slots. The four-slot diminutives do not
recover the length or original radicals of the larger nominal base. The
quadriliteral masdar keeps its third and fourth slots independent, even
though the traditional display repeats the letter lam.

The final inflection is omitted from each stem. Ta marbuta is a literal
inside the stem. Listed endings only describe a separate one-character
boundary profile; they confer no declension or grammatical license.

Jamid has no unique shape/default rule. Future has no additional template.
Weak/hamza transformations, deletion of longer bases and lexical choices
remain outside this finite shape inventory.
-/

namespace Nabt.NominalPatterns

open Nabt.Derivation

/-- فَعْل; AQ-MASDAR-BARE. Shape only. -/
def t_masdar_bare_fa3l : Pattern 3 :=
  [.slot 0, .literal 'َ', .slot 1, .literal 'ْ', .slot 2]

/-- فَعَل; AQ-MASDAR-BARE. Shape only. -/
def t_masdar_bare_fa3al : Pattern 3 :=
  [.slot 0, .literal 'َ', .slot 1, .literal 'َ', .slot 2]

/-- فُعُول; AQ-MASDAR-BARE. Shape only. -/
def t_masdar_bare_fu3ul : Pattern 3 :=
  [.slot 0, .literal 'ُ', .slot 1, .literal 'ُ', .literal 'و', .slot 2]

/-- فَعَالَة; AQ-MASDAR-BARE. Shape only. -/
def t_masdar_bare_fa3ala : Pattern 3 :=
  [.slot 0, .literal 'َ', .slot 1, .literal 'َ', .literal 'ا', .slot 2, .literal 'َ', .literal 'ة']

/-- فُعُولَة; AQ-MASDAR-BARE. Shape only. -/
def t_masdar_bare_fu3ula : Pattern 3 :=
  [.slot 0, .literal 'ُ', .slot 1, .literal 'ُ', .literal 'و', .slot 2, .literal 'َ', .literal 'ة']

/-- تَفْعِيل; AQ-MASDAR-II. Shape only. -/
def t_masdar_II_taf3il : Pattern 3 :=
  [.literal 'ت', .literal 'َ', .slot 0, .literal 'ْ', .slot 1, .literal 'ِ', .literal 'ي', .slot 2]

/-- مُفَاعَلَة; AQ-MASDAR-III. Shape only. -/
def t_masdar_III_mufa3ala : Pattern 3 :=
  [.literal 'م', .literal 'ُ', .slot 0, .literal 'َ', .literal 'ا', .slot 1, .literal 'َ', .slot 2, .literal 'َ', .literal 'ة']

/-- فِعَال; AQ-MASDAR-III. Shape only. -/
def t_masdar_III_fi3al : Pattern 3 :=
  [.slot 0, .literal 'ِ', .slot 1, .literal 'َ', .literal 'ا', .slot 2]

/-- إِفْعَال; AQ-MASDAR-IV. Shape only. -/
def t_masdar_IV_if3al : Pattern 3 :=
  [.literal 'إ', .literal 'ِ', .slot 0, .literal 'ْ', .slot 1, .literal 'َ', .literal 'ا', .slot 2]

/-- تَفَعُّل; AQ-MASDAR-V. Shape only. -/
def t_masdar_V_tafa33ul : Pattern 3 :=
  [.literal 'ت', .literal 'َ', .slot 0, .literal 'َ', .slot 1, .literal 'ّ', .literal 'ُ', .slot 2]

/-- تَفَاعُل; KI-MASDAR-VI. Shape only. -/
def t_masdar_VI_tafa3ul : Pattern 3 :=
  [.literal 'ت', .literal 'َ', .slot 0, .literal 'َ', .literal 'ا', .slot 1, .literal 'ُ', .slot 2]

/-- اِنْفِعَال; AQ-MASDAR-WASL. Shape only. -/
def t_masdar_VII_infi3al : Pattern 3 :=
  [.literal 'ا', .literal 'ِ', .literal 'ن', .literal 'ْ', .slot 0, .literal 'ِ', .slot 1, .literal 'َ', .literal 'ا', .slot 2]

/-- اِفْتِعَال; AQ-MASDAR-WASL. Shape only. -/
def t_masdar_VIII_ifti3al : Pattern 3 :=
  [.literal 'ا', .literal 'ِ', .slot 0, .literal 'ْ', .literal 'ت', .literal 'ِ', .slot 1, .literal 'َ', .literal 'ا', .slot 2]

/-- اِسْتِفْعَال; AQ-MASDAR-WASL. Shape only. -/
def t_masdar_X_istif3al : Pattern 3 :=
  [.literal 'ا', .literal 'ِ', .literal 'س', .literal 'ْ', .literal 'ت', .literal 'ِ', .slot 0, .literal 'ْ', .slot 1, .literal 'َ', .literal 'ا', .slot 2]

/-- فَعْلَلَة; AQ-MASDAR-QUAD. Shape only. -/
def t_masdar_quad_fa3lala : Pattern 4 :=
  [.slot 0, .literal 'َ', .slot 1, .literal 'ْ', .slot 2, .literal 'َ', .slot 3, .literal 'َ', .literal 'ة']

/-- مِفْعَل; KI-INSTRUMENT. Shape only. -/
def t_instrument_mif3al : Pattern 3 :=
  [.literal 'م', .literal 'ِ', .slot 0, .literal 'ْ', .slot 1, .literal 'َ', .slot 2]

/-- مِفْعَلَة; KI-INSTRUMENT. Shape only. -/
def t_instrument_mif3ala : Pattern 3 :=
  [.literal 'م', .literal 'ِ', .slot 0, .literal 'ْ', .slot 1, .literal 'َ', .slot 2, .literal 'َ', .literal 'ة']

/-- مِفْعَال; KI-INSTRUMENT. Shape only. -/
def t_instrument_mif3aal : Pattern 3 :=
  [.literal 'م', .literal 'ِ', .slot 0, .literal 'ْ', .slot 1, .literal 'َ', .literal 'ا', .slot 2]

/-- مَفْعَل; KI-PLACE. Shape only. -/
def t_place_maf3al : Pattern 3 :=
  [.literal 'م', .literal 'َ', .slot 0, .literal 'ْ', .slot 1, .literal 'َ', .slot 2]

/-- مَفْعِل; KI-PLACE. Shape only. -/
def t_place_maf3il : Pattern 3 :=
  [.literal 'م', .literal 'َ', .slot 0, .literal 'ْ', .slot 1, .literal 'ِ', .slot 2]

/-- فَعَل; AQ-SIFA. Shape only. -/
def t_sifa_fa3al : Pattern 3 :=
  [.slot 0, .literal 'َ', .slot 1, .literal 'َ', .slot 2]

/-- فَعِيل; AQ-SIFA, AQ-FAIIL-OVERLAP. Shape only. -/
def t_sifa_fa3il : Pattern 3 :=
  [.slot 0, .literal 'َ', .slot 1, .literal 'ِ', .literal 'ي', .slot 2]

/-- فَاعِل; AQ-SIFA, AQ-FAAIL. Shape only. -/
def t_sifa_faa3il : Pattern 3 :=
  [.slot 0, .literal 'َ', .literal 'ا', .slot 1, .literal 'ِ', .slot 2]

/-- فُعَيْل; AQ-DIMINUTIVE. Shape only. -/
def t_diminutive_fu3ayl : Pattern 3 :=
  [.slot 0, .literal 'ُ', .slot 1, .literal 'َ', .literal 'ي', .literal 'ْ', .slot 2]

/-- فُعَيْعِل; AQ-DIMINUTIVE. Shape only. -/
def t_diminutive_fu3ay3il : Pattern 4 :=
  [.slot 0, .literal 'ُ', .slot 1, .literal 'َ', .literal 'ي', .literal 'ْ', .slot 2, .literal 'ِ', .slot 3]

/-- فُعَيْعِيل; AQ-DIMINUTIVE. Shape only. -/
def t_diminutive_fu3ay3iil : Pattern 4 :=
  [.slot 0, .literal 'ُ', .slot 1, .literal 'َ', .literal 'ي', .literal 'ْ', .slot 2, .literal 'ِ', .literal 'ي', .slot 3]

/-- أَفْعَل; AQ-TAFDIL. Shape only. -/
def t_comparative_af3al : Pattern 3 :=
  [.literal 'أ', .literal 'َ', .slot 0, .literal 'ْ', .slot 1, .literal 'َ', .slot 2]

def patterns : List CatalogPattern := [
  { id := "grammar.masdar.bare.fa3l", label := "مصدر ثلاثي: فَعْل", arity := 3,
    tokens := t_masdar_bare_fa3l, family := "masdar",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:AQ-MASDAR-BARE",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.masdar.bare.fa3al", label := "مصدر ثلاثي: فَعَل", arity := 3,
    tokens := t_masdar_bare_fa3al, family := "masdar",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:AQ-MASDAR-BARE",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.masdar.bare.fu3ul", label := "مصدر ثلاثي: فُعُول", arity := 3,
    tokens := t_masdar_bare_fu3ul, family := "masdar",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:AQ-MASDAR-BARE",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.masdar.bare.fa3ala", label := "مصدر ثلاثي: فَعَالَة", arity := 3,
    tokens := t_masdar_bare_fa3ala, family := "masdar",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:AQ-MASDAR-BARE",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.masdar.bare.fu3ula", label := "مصدر ثلاثي: فُعُولَة", arity := 3,
    tokens := t_masdar_bare_fu3ula, family := "masdar",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:AQ-MASDAR-BARE",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.masdar.II.taf3il", label := "مصدر فعّل: تَفْعِيل", arity := 3,
    tokens := t_masdar_II_taf3il, family := "masdar",
    form := "nominal", voice := "none",
    augmentation := "augmented",
    sourceContract := "grammar:AQ-MASDAR-II",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.masdar.III.mufa3ala", label := "مصدر فاعل: مُفَاعَلَة", arity := 3,
    tokens := t_masdar_III_mufa3ala, family := "masdar",
    form := "nominal", voice := "none",
    augmentation := "augmented",
    sourceContract := "grammar:AQ-MASDAR-III",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.masdar.III.fi3al", label := "مصدر فاعل: فِعَال", arity := 3,
    tokens := t_masdar_III_fi3al, family := "masdar",
    form := "nominal", voice := "none",
    augmentation := "augmented",
    sourceContract := "grammar:AQ-MASDAR-III",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.masdar.IV.if3al", label := "مصدر أفعل: إِفْعَال", arity := 3,
    tokens := t_masdar_IV_if3al, family := "masdar",
    form := "nominal", voice := "none",
    augmentation := "augmented",
    sourceContract := "grammar:AQ-MASDAR-IV",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.masdar.V.tafa33ul", label := "مصدر تفعّل: تَفَعُّل", arity := 3,
    tokens := t_masdar_V_tafa33ul, family := "masdar",
    form := "nominal", voice := "none",
    augmentation := "augmented",
    sourceContract := "grammar:AQ-MASDAR-V",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.masdar.VI.tafa3ul", label := "مصدر تفاعل: تَفَاعُل", arity := 3,
    tokens := t_masdar_VI_tafa3ul, family := "masdar",
    form := "nominal", voice := "none",
    augmentation := "augmented",
    sourceContract := "grammar:KI-MASDAR-VI",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.masdar.VII.infi3al", label := "مصدر انفعل: اِنْفِعَال", arity := 3,
    tokens := t_masdar_VII_infi3al, family := "masdar",
    form := "nominal", voice := "none",
    augmentation := "augmented",
    sourceContract := "grammar:AQ-MASDAR-WASL",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.masdar.VIII.ifti3al", label := "مصدر افتعل: اِفْتِعَال", arity := 3,
    tokens := t_masdar_VIII_ifti3al, family := "masdar",
    form := "nominal", voice := "none",
    augmentation := "augmented",
    sourceContract := "grammar:AQ-MASDAR-WASL",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.masdar.X.istif3al", label := "مصدر استفعل: اِسْتِفْعَال", arity := 3,
    tokens := t_masdar_X_istif3al, family := "masdar",
    form := "nominal", voice := "none",
    augmentation := "augmented",
    sourceContract := "grammar:AQ-MASDAR-WASL",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.masdar.quad.fa3lala", label := "مصدر رباعي: فَعْلَلَة", arity := 4,
    tokens := t_masdar_quad_fa3lala, family := "masdar",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:AQ-MASDAR-QUAD",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.instrument.mif3al", label := "آلة محتملة: مِفْعَل", arity := 3,
    tokens := t_instrument_mif3al, family := "instrument",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:KI-INSTRUMENT",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.instrument.mif3ala", label := "آلة محتملة: مِفْعَلَة", arity := 3,
    tokens := t_instrument_mif3ala, family := "instrument",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:KI-INSTRUMENT",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.instrument.mif3aal", label := "آلة محتملة: مِفْعَال", arity := 3,
    tokens := t_instrument_mif3aal, family := "instrument",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:KI-INSTRUMENT",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.place.maf3al", label := "مكان محتمل: مَفْعَل", arity := 3,
    tokens := t_place_maf3al, family := "place",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:KI-PLACE",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.place.maf3il", label := "مكان محتمل: مَفْعِل", arity := 3,
    tokens := t_place_maf3il, family := "place",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:KI-PLACE",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.sifa.fa3al", label := "صفة مشبهة محتملة: فَعَل", arity := 3,
    tokens := t_sifa_fa3al, family := "sifa_mushabbaha",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:AQ-SIFA",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.sifa.fa3il", label := "صفة مشبهة محتملة: فَعِيل", arity := 3,
    tokens := t_sifa_fa3il, family := "sifa_mushabbaha",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:AQ-SIFA+AQ-FAIIL-OVERLAP",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.sifa.faa3il", label := "صفة مشبهة محتملة: فَاعِل", arity := 3,
    tokens := t_sifa_faa3il, family := "sifa_mushabbaha",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:AQ-SIFA+AQ-FAAIL",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.diminutive.fu3ayl", label := "تصغير محتمل: فُعَيْل", arity := 3,
    tokens := t_diminutive_fu3ayl, family := "diminutive",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:AQ-DIMINUTIVE",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.diminutive.fu3ay3il", label := "تصغير محتمل: فُعَيْعِل", arity := 4,
    tokens := t_diminutive_fu3ay3il, family := "diminutive",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:AQ-DIMINUTIVE",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.diminutive.fu3ay3iil", label := "تصغير محتمل: فُعَيْعِيل", arity := 4,
    tokens := t_diminutive_fu3ay3iil, family := "diminutive",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:AQ-DIMINUTIVE",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] },
  { id := "grammar.comparative.af3al", label := "تفضيل محتمل: أَفْعَل", arity := 3,
    tokens := t_comparative_af3al, family := "comparative",
    form := "nominal", voice := "none",
    augmentation := "none",
    sourceContract := "grammar:AQ-TAFDIL",
    sourceKind := "NEW_GRAMMAR_PROJECTION",
    rootDomain := "radicals28_shape_only",
    endings := ['َ', 'ُ', 'ِ', 'ٌ', 'ٍ', 'ْ'] }
]

theorem pattern_count : patterns.length = 27 := by decide

theorem pattern_ids_unique : (patterns.map CatalogPattern.id).Nodup := by decide

theorem patterns_complete :
    ∀ pattern ∈ patterns, Complete pattern.tokens := by decide

/-- Every supplied formal root returns exactly through its complete template. -/
theorem pattern_recovery (pattern : CatalogPattern) (member : pattern ∈ patterns)
    (root : Root pattern.arity) :
    recover pattern.tokens (fill pattern.tokens root) = some root := by
  exact recover_fill pattern.tokens root (patterns_complete pattern member)

theorem combined_pattern_count : (corePatterns ++ patterns).length = 71 := by decide

theorem combined_pattern_ids_unique :
    ((corePatterns ++ patterns).map CatalogPattern.id).Nodup := by decide

/-- The source permits different class readings with the identical shape. -/
theorem sifa_faail_same_shape : t_sifa_faa3il = t_nominal_faail := by rfl

theorem sifa_faail_same_fill (root : Root 3) :
    fill t_sifa_faa3il root = fill t_nominal_faail root := by rfl

/-- Semantic alternatives retain distinct catalog identities. -/
theorem sifa_faail_ids_distinct :
    "grammar.sifa.faa3il" ≠ "nominal.faail" := by decide

/-- Hasan-like and masdar-like readings can also have the same interior. -/
theorem sifa_masdar_same_shape : t_sifa_fa3al = t_masdar_bare_fa3al := by rfl

theorem sifa_masdar_ids_distinct :
    "grammar.sifa.fa3al" ≠ "grammar.masdar.bare.fa3al" := by decide

/-- Distinct fourth consonants cannot be conflated in the quad masdar. -/
theorem quad_fourth_slot_distinguishes (left right : Root 4)
    (different : left 3 ≠ right 3) :
    fill t_masdar_quad_fa3lala left ≠ fill t_masdar_quad_fa3lala right := by
  intro same
  have roots : left = right :=
    fill_injective_complete t_masdar_quad_fa3lala (by decide) left right same
  exact different (congrFun roots 3)

end Nabt.NominalPatterns
