import Nabt.ClassicalLanguageEvidence

/-! Complete numbered INVENTORY of the reviewed 2009 Awamil body, pp. 41–64.
The family labels do not activate a grammatical use or assert full coverage
of conditions/variants. See evidence/mantuq_mafhum/awamil_inventory.json.
The manuscript/editorial attribution is not authenticated by counting. -/
namespace Nabt.AwamilInventory

def lawId := "nabt.awamil-numbered-inventory.v1"
structure Entry where
  number : Nat
  name : String
  page : Nat
  group : Nat
  family : String
  deriving DecidableEq, Repr

def entries : List Entry := [
  ⟨1, "الباء", 41, 1, "jarr"⟩,
  ⟨2, "من", 43, 1, "jarr"⟩,
  ⟨3, "إلى", 44, 1, "jarr"⟩,
  ⟨4, "في", 44, 1, "jarr"⟩,
  ⟨5, "اللام", 45, 1, "jarr"⟩,
  ⟨6, "رب", 46, 1, "jarr"⟩,
  ⟨7, "على", 46, 1, "jarr"⟩,
  ⟨8, "عن", 46, 1, "jarr"⟩,
  ⟨9, "الكاف", 46, 1, "jarr"⟩,
  ⟨10, "مذ", 47, 1, "jarr"⟩,
  ⟨11, "منذ", 47, 1, "jarr"⟩,
  ⟨12, "حتى", 47, 1, "jarr"⟩,
  ⟨13, "واو القسم", 48, 1, "jarr"⟩,
  ⟨14, "تاء القسم", 48, 1, "jarr"⟩,
  ⟨15, "حاشا", 48, 1, "jarr"⟩,
  ⟨16, "خلا", 48, 1, "jarr"⟩,
  ⟨17, "عدا", 48, 1, "jarr"⟩,
  ⟨18, "إن", 49, 2, "inna"⟩,
  ⟨19, "أن", 49, 2, "inna"⟩,
  ⟨20, "كأن", 49, 2, "inna"⟩,
  ⟨21, "لكن", 49, 2, "inna"⟩,
  ⟨22, "ليت", 49, 2, "inna"⟩,
  ⟨23, "لعل", 49, 2, "inna"⟩,
  ⟨24, "ما", 50, 3, "laysaParticle"⟩,
  ⟨25, "لا", 50, 3, "laysaParticle"⟩,
  ⟨26, "واو المعية", 51, 4, "singleNasb"⟩,
  ⟨27, "إلا", 52, 4, "singleNasb"⟩,
  ⟨28, "يا", 52, 4, "singleNasb"⟩,
  ⟨29, "أيا", 52, 4, "singleNasb"⟩,
  ⟨30, "هيا", 52, 4, "singleNasb"⟩,
  ⟨31, "أي", 52, 4, "singleNasb"⟩,
  ⟨32, "الهمزة", 52, 4, "singleNasb"⟩,
  ⟨33, "أن", 53, 5, "presentNasb"⟩,
  ⟨34, "لن", 53, 5, "presentNasb"⟩,
  ⟨35, "كي", 53, 5, "presentNasb"⟩,
  ⟨36, "إذن", 53, 5, "presentNasb"⟩,
  ⟨37, "إن", 54, 6, "presentJazm"⟩,
  ⟨38, "لم", 54, 6, "presentJazm"⟩,
  ⟨39, "لما", 54, 6, "presentJazm"⟩,
  ⟨40, "لام الأمر", 54, 6, "presentJazm"⟩,
  ⟨41, "لا الناهية", 54, 6, "presentJazm"⟩,
  ⟨42, "من", 55, 7, "conditionalName"⟩,
  ⟨43, "أي", 55, 7, "conditionalName"⟩,
  ⟨44, "ما", 55, 7, "conditionalName"⟩,
  ⟨45, "متى", 55, 7, "conditionalName"⟩,
  ⟨46, "مهما", 55, 7, "conditionalName"⟩,
  ⟨47, "أين", 55, 7, "conditionalName"⟩,
  ⟨48, "أنى", 55, 7, "conditionalName"⟩,
  ⟨49, "حيثما", 55, 7, "conditionalName"⟩,
  ⟨50, "إذما", 55, 7, "conditionalName"⟩,
  ⟨51, "عشرة المركبة", 55, 8, "distinction"⟩,
  ⟨52, "كم الاستفهامية", 57, 8, "distinction"⟩,
  ⟨53, "كأين", 57, 8, "distinction"⟩,
  ⟨54, "كذا", 57, 8, "distinction"⟩,
  ⟨55, "رويد", 58, 9, "verbName"⟩,
  ⟨56, "بله", 58, 9, "verbName"⟩,
  ⟨57, "دونك", 58, 9, "verbName"⟩,
  ⟨58, "عليك", 58, 9, "verbName"⟩,
  ⟨59, "ها", 58, 9, "verbName"⟩,
  ⟨60, "حيهل", 58, 9, "verbName"⟩,
  ⟨61, "هيهات", 58, 9, "verbName"⟩,
  ⟨62, "شتان", 58, 9, "verbName"⟩,
  ⟨63, "سرعان", 58, 9, "verbName"⟩,
  ⟨64, "كان", 59, 10, "kana"⟩,
  ⟨65, "صار", 60, 10, "kana"⟩,
  ⟨66, "أصبح", 60, 10, "kana"⟩,
  ⟨67, "أمسى", 60, 10, "kana"⟩,
  ⟨68, "أضحى", 60, 10, "kana"⟩,
  ⟨69, "ظل", 60, 10, "kana"⟩,
  ⟨70, "بات", 60, 10, "kana"⟩,
  ⟨71, "ما زال", 60, 10, "kana"⟩,
  ⟨72, "ما برح", 60, 10, "kana"⟩,
  ⟨73, "ما فتئ", 60, 10, "kana"⟩,
  ⟨74, "ما انفك", 60, 10, "kana"⟩,
  ⟨75, "ما دام", 60, 10, "kana"⟩,
  ⟨76, "ليس", 60, 10, "kana"⟩,
  ⟨77, "عسى", 61, 11, "approximation"⟩,
  ⟨78, "كاد", 61, 11, "approximation"⟩,
  ⟨79, "كرب", 61, 11, "approximation"⟩,
  ⟨80, "أوشك", 61, 11, "approximation"⟩,
  ⟨81, "نعم", 61, 12, "praise"⟩,
  ⟨82, "بئس", 61, 12, "praise"⟩,
  ⟨83, "حبذا", 61, 12, "praise"⟩,
  ⟨84, "ساء", 61, 12, "praise"⟩,
  ⟨85, "علمت", 62, 13, "cognition"⟩,
  ⟨86, "وجدت", 62, 13, "cognition"⟩,
  ⟨87, "رأيت", 62, 13, "cognition"⟩,
  ⟨88, "ظننت", 62, 13, "cognition"⟩,
  ⟨89, "حسبت", 62, 13, "cognition"⟩,
  ⟨90, "خلت", 62, 13, "cognition"⟩,
  ⟨91, "زعمت", 62, 13, "cognition"⟩,
  ⟨92, "الفعل على الإطلاق", 63, 14, "analogical"⟩,
  ⟨93, "اسم الفاعل", 63, 14, "analogical"⟩,
  ⟨94, "اسم المفعول", 63, 14, "analogical"⟩,
  ⟨95, "الصفة المشبهة", 63, 14, "analogical"⟩,
  ⟨96, "المصدر", 63, 14, "analogical"⟩,
  ⟨97, "المضاف", 63, 14, "analogical"⟩,
  ⟨98, "الاسم التام", 63, 14, "analogical"⟩,
  ⟨99, "رافع المبتدأ والخبر", 64, 15, "semantic"⟩,
  ⟨100, "رافع الفعل المضارع", 64, 15, "semantic"⟩
]

theorem complete_numbered_inventory : entries.map Entry.number = (List.range 100).map (· + 1) := by decide
theorem inventory_count : entries.length = 100 := by decide
theorem numbered_identities_unique : (entries.map Entry.number).Nodup := by decide
theorem partition_counts :
    (entries.filter (·.group ≤ 13)).length = 91 ∧
    (entries.filter (·.group == 14)).length = 7 ∧
    (entries.filter (·.group == 15)).length = 2 := by decide

def lookup (number : Nat) : Option Entry := entries.find? (·.number == number)
def boundLookup (work : ClassicalLanguageEvidence.Work) (number : Nat) : Option Entry :=
  if work = .jurjaniAwamil then lookup number else none

theorem wrong_work_has_no_entry (work : ClassicalLanguageEvidence.Work)
    (wrong : work ≠ .jurjaniAwamil) (n : Nat) : boundLookup work n = none := by
  simp [boundLookup, wrong]

theorem repeated_spelling_distinct_identity :
    lookup 24 ≠ lookup 44 ∧ lookup 19 ≠ lookup 33 := by decide

theorem outside_inventory : lookup 0 = none ∧ lookup 101 = none := by decide

end Nabt.AwamilInventory
