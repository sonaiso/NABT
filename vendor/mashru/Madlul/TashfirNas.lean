/-
  Madlul/TashfirNas.lean — جسرُ المعلومة المعمَّم: أداةٌ عامّةٌ لطيّ وفكّ `String` (نصّ)، تُفتح بها القطعتان
  المؤجَّلتان بالاسم اللتان تحملان حقولَ String: `Madlul.Hawass.Tasmiya`/`Khibra` و`Madlul.Shabaka`.

  السند: نفسُ تفويض المالك 2026-10-17 22:55 («alaqat/hawass/awwaليyyat/makan/isnad … ابني واكتشف كيف
  نقرا/تبني من الرياضيات»)؛ makan وawwaliyyat بُنيا (القطعتان 5، 6)؛ alaqat وhawass يحملان حقولَ String
  (Hawass.Tasmiya.ism/bud، Hawass.Khibra.jins/bud/ism، وAql.Maratib.ShahidWaqi.basma؛ Shabaka تُفحص بعدُ)
  فلا يكفيهما الترميزُ المبنيّ حتّى الآن (Nat/Int/تعداداتٌ محدودة) — هذه القطعةُ الأداةُ التي كانت مؤجَّلةً
  بالاسم في ترويسة Madlul/TashfirKhawass.lean («قابليّاتُها List QabHaraka تحتاج ترميزَ قوائم لم يُبنَ هنا»)
  مطبَّقةً على Char بدل Nat/Qima/QabHaraka مباشرةً.

  **البناءُ: تركيبٌ لا أداةٌ موازية.** String في Lean 4 (هذا الإصدار) ليست بنيةً `List Char` مباشرةً بل
  `ByteArray` UTF-8 مُغلَّف؛ لكنّ نواة Lean نفسَها تكفي الجسرَ كلَّه بلا برهانٍ جديدٍ تقريبًا:
  - **Char ↔ Nat**: `Char.toNat`/`Char.ofNat` أصلًا في النواة، والفكُّ يعيد الأصل بمبرهنة النواة نفسِها
    `Char.ofNat_toNat` حرفيًّا — لا برهانَ جديدًا هنا. وحدُّ الحرف (`charEnc c < 2^32`) لازمٌ من تعريف Char
    نفسِه (كلُّ Char قيمتُه UInt32) بمبرهنة النواة `UInt32.toNat_lt`، **لا حدٌّ مختارٌ** كـ`BOUND` في
    TashfirMadda/TashfirMirsat (ذاك تعيينٌ منّي كافٍ للشواهد، وهذا لازمٌ رياضيٌّ من تعريف النوع نفسِه — فرقٌ
    في جنس الدعوى بين القطعتين، لا تكرارٌ لاسم BOUND).
  - **List Char ↔ Nat**: `listEnc`/`listDec` نفسُهما من `Madlul/TashfirKhawass.lean` (مستوردةً لا مكرَّرة)
    مطبَّقةً على `charEnc`/`charDec` — نفسُ الآلة التي فتحتها تلك القطعةُ لهذا الاستعمال بعينه (نصُّ ترويستها:
    «الآلة هنا تُعيد استعمالها فورًا حين يُفوَّض أيٌّ منها»).
  - **String ↔ List Char**: `String.ofList`/`String.toList`، والفكُّ يعيد الأصل بمبرهنتَي النواة
    `String.ofList_toList`/`String.toList_ofList` حرفيًّا — لا برهانَ جديدًا هنا أيضًا.
  فالطيُّ كلُّه **غيرُ مشروطٍ** (كـKhawass لا كMadda/Mirsat/Izaha3): كلُّ Char من كلّ String دون 2^32 دائمًا
  بالتعريف، فلا شرط Sahih ولا Subtype ولا `Classical.propDecidable` في بنائي أنا هنا بتاتًا. **تصحيحٌ ضُبط
  بـ`#print axioms` نفسِه قبل أيّ ادّعاء (لا بالتخمين):** مسودةٌ أولى من هذا السطر زعمت أيضًا أنّ
  `Classical.choice` غائبٌ عن القطعة كلِّها، وهذا خطأ: `String.ofList_toList`/`String.toList_ofList` (نواةُ
  Lean نفسُها، لا بنائي) يعتمدان `Classical.choice` داخليًّا — فكلُّ مبرهنةٍ تستشهد بهما (`string_dec_enc`،
  `tayyString_la_yudi`، `string_shawahid_tudi`) تحمله تبعًا، بخلاف ما قبل تركيب String (`char_dec_enc`،
  `charEnc_lt`: بلا مسلّماتٍ أصلًا؛ `charList_dec_enc`: propext فقط؛ `charList_map_lt`: propext/Quot.sound
  بلا choice) — مؤكَّدٌ بفحص `#print axioms` لكلّ واحدةٍ على حدةٍ، لا من توقّعٍ عن غياب Subtype في بنائي.
  الفرقُ عن Madda/Mirsat حقيقيٌّ رغم ذلك: هناك Classical.choice من `Classical.propDecidable` في **بنائي
  أنا** (`fakkOf` على Subtype)؛ هنا من نواة Lean في **لازمةٍ مستوردة** لا من بنائي، وبنائي نفسُه غيرُ مشروطٍ
  تمامًا كما وُصف.

  ما يُبرهن هنا: `char_dec_enc`/`charEnc_lt` (نقلانِ مباشرانِ لمبرهنتَي نواة Lean، بلا برهانٍ جديد)،
  `charList_dec_enc`/`charList_map_lt` (بالاستقراء على القائمة، على نمط `qab_list_roundtrip` في
  TashfirKhawass)، `string_dec_enc` (تركيبُ الثلاث طبقاتٍ)، `tayyString_la_yudi` (`Tayy String Nat` مباشرةً
  — لا Unit/Subtype)؛ وعلى الشاهد `string_shawahid_tudi` (نصوصٌ عربيّةٌ حقيقيّةٌ مبنيّةٌ: «السمع»، «البصر» —
  تسميتا حاسّتين من `Madlul.Hawass.Hassa` تمهيدًا لجسرها التالي، لا شاهدًا من مودَعٍ لهذه القطعة بعينها —
  والفارغةُ "" حالةً حدّيّة).

  مؤجَّلٌ: جسرُ `Madlul.Hawass` نفسُه (يستعمل هذه الأداةَ لحقول `Tasmiya.ism/bud` وَ`Khibra.jins/bud/ism`؛
  يحتاج تصميمًا إضافيًّا لـ`Hassa`/`ShahidWaqi`/`Tasmiya`/`Khibra` نفسِها، لم يُبدأ)، وجسرُ `Madlul.Shabaka`
  (alaqat؛ لم تُقرأ بنيتُه التفصيليّة هذه الجلسةُ لتحديد ما يحتاج هذه الأداةَ بعينها)، وجسرُ `Aql.Isnad`
  (التكراريّةُ الحقيقيّةُ، مشكلةٌ مستقلّةٌ عن ترميز النصوص)، وجسورُ العوامل/Itar3.
-/
import Aql.Mawsua
import Madlul.TashfirKhawass

set_option autoImplicit false

namespace Madlul.TashfirNas

open Mawsua Madlul.TashfirKhawass

/-! ## ١. طيُّ Char — نقلٌ مباشرٌ لمبرهنتَي نواة Lean، بلا برهانٍ جديد -/

def charEnc : Char → Nat := Char.toNat
def charDec : Nat → Char := Char.ofNat

/-- **الفكُّ يعيد الأصل لكلّ حرف**: نقلٌ مباشرٌ لمبرهنة النواة `Char.ofNat_toNat`. -/
theorem char_dec_enc (c : Char) : charDec (charEnc c) = c := Char.ofNat_toNat c

/-- حدُّ الحرف: `2^32` — **لازمٌ من تعريف Char نفسِه** (قيمتُه UInt32)، لا حدٌّ مختارٌ كـ`BOUND` في
TashfirMadda/TashfirMirsat. -/
def charBound : Nat := 2 ^ 32

/-- نقلٌ مباشرٌ لمبرهنة النواة `UInt32.toNat_lt`. -/
theorem charEnc_lt (c : Char) : charEnc c < charBound := UInt32.toNat_lt c.val

/-! ## ٢. طيُّ List Char — تركيبٌ على listEnc/listDec من TashfirKhawass (مستوردةً لا مكرَّرة) -/

/-- نقلٌ مباشرٌ لمبرهنة النواة `String.ofList_toList`، بعد ردّ الحمولة بالاستقراء — على نمط
`qab_list_roundtrip` في TashfirKhawass. -/
theorem charList_dec_enc (l : List Char) : (l.map charEnc).map charDec = l := by
  induction l with
  | nil => rfl
  | cons c cs ih => simp only [List.map_cons, char_dec_enc, ih]

/-- على نمط `qabEnc_map_lt` في TashfirKhawass. -/
theorem charList_map_lt (l : List Char) : ∀ x ∈ l.map charEnc, x < charBound := by
  intro x hx
  obtain ⟨c, -, rfl⟩ := List.mem_map.1 hx
  exact charEnc_lt c

/-! ## ٣. طيُّ String — تركيبُ الطبقتين السابقتين مع `String.ofList`/`toList` -/

def stringEnc (s : String) : Nat := listEnc charBound (s.toList.map charEnc)
def stringDec (n : Nat) : String := String.ofList ((listDec charBound n).map charDec)

/-- **الفكُّ يعيد الأصل لكلّ نصٍّ — بلا شرط** (كـ`khawass_dec_enc`؛ كلُّ حرفٍ دون `charBound` دائمًا بالتعريف
فلا قيدَ على النصّ): `listDec` يردّ قائمةَ الرموز بعينها (`list_dec_enc`)، ثمّ `charDec` كلَّ رمزٍ إلى حرفه
(`charList_dec_enc`)، ثمّ `String.ofList_toList` يردّ النصَّ بعينه. -/
theorem string_dec_enc (s : String) : stringDec (stringEnc s) = s := by
  unfold stringDec stringEnc
  rw [list_dec_enc charBound (s.toList.map charEnc) (charList_map_lt s.toList)]
  rw [charList_dec_enc]
  exact String.ofList_toList

/-! ## ٤. الطيّ على String مباشرةً (بلا Unit/Subtype — لا شرط، كـKhawass) -/

def tayyString : Tayy String Nat where
  tawi := stringEnc
  fakk := fun n => some (stringDec n)
  fakk_tawi := fun s => by rw [string_dec_enc]

theorem tayyString_la_yudi (s : String) : tayyString.fakk (tayyString.tawi s) = some s :=
  tayyString.fakk_tawi s

/-! ## ٥. على الشاهد -/

/-- نصوصٌ عربيّةٌ حقيقيّةٌ (تسميتا حاسّتين من `Madlul.Hawass.Hassa`، تمهيدًا لجسرها التالي) والفارغةُ حالةً
حدّيّة — لا شاهدَ مودَعٍ لهذه الأداة العامّة بعينها. -/
theorem string_shawahid_tudi :
    stringDec (stringEnc "السمع") = "السمع" ∧
    stringDec (stringEnc "البصر") = "البصر" ∧
    stringDec (stringEnc "") = "" :=
  ⟨string_dec_enc _, string_dec_enc _, string_dec_enc _⟩

end Madlul.TashfirNas
