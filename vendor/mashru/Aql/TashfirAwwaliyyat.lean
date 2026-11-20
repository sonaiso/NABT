/-
  Aql/TashfirAwwaliyyat.lean — جسرُ المعلومة المعمَّم (السادس): طيُّ وفكُّ Aql.Awwaliyyat.Zaman5.

  السند: نفسُ تفويض المالك 2026-10-17 22:55؛ awwaliyyat من الأربعة الباقية (بعد makan، القطعة الخامسة)، وقُرئ
  Aql/Awwaliyyat.lean كاملًا (281 سطرًا) هذه الجلسةُ قبل التصميم.

  **البنيةُ الوحيدةُ القابلةُ للطيّ في هذا الملفّ:** `Zaman5` تعدادٌ من خمس قيمٍ بلا حمولة (الأزمنةُ الخمسةُ
  عند سيبويه بقراءة البنّاء: ماضٍ منقطع/متّصلٌ بالحال/حال/مستقبل/مستقبلٌ منفَّس). كلُّ ما عداه في الملفّ —
  `Tatabu E := Nat → E` (نوعُ دالّةٍ، لا بنيةُ بياناتٍ)، `muntazim`/`taaqub` (خاصّياتٌ على دالّةٍ)، ومبرهناتُ
  الأركان الأربعة والتعيين والتمييز والمرفوع الثالث والجزء/الكلّ — دوالٌّ ومبرهناتٌ عامّةٌ على أنواعٍ مجرَّدةٍ
  (`α`،`E`،`Prop`) لا بنى بياناتٍ محدَّدةٍ لها شاهدٌ يُطوى. فلا حاجةَ إلى `SLGE.mixEnc` أصلًا هنا (بخلاف كلّ
  القطع 1–5): تعدادٌ محدودٌ بلا حمولةٍ وبلا حقلٍ آخر يُركَّب معه — ترميزٌ مباشرٌ Nat كـ`Jiha`/`WahdaMakan` في
  TashfirMakan أو `Wahda` في TashfirAzmina، و`Tayy` عليه مباشرةً بلا طبقةِ mixEnc أصلًا (أبسط من كلّ ما سبق).

  ما يُبرهن هنا: `zaman5_dec_enc`/`zaman5Enc_lt` (الترميزُ المباشر)، `tayyZaman5_la_yudi` (`Tayy Zaman5 Nat`
  مباشرةً — لا Unit/Subtype، كـKhawass/Mawdi/Marja-tag لا كMadda/Mirsat/Izaha3)، وعلى الشاهد
  `zaman5_shawahid_tudi`: طيُّ وفكُّ الخمسةِ كلِّها بترتيبها — نفسُ القائمة المبنيّة في `Aql.Awwaliyyat.nafy_asma`
  حرفيًّا (`[.madiMunqati, .madiMuttasil, .hal, .mustaqbal, .mustaqbalMunaffas]`)، لا شاهدًا جديدًا منفصلًا.

  مؤجَّلٌ: alaqat/hawass/isnad (ثلاثةٌ من ثمانيةٍ فُوِّضت تبقى؛ Hawass/Shabaka(alaqat) تحتاجان أداةَ ترميز
  نصوصٍ String↔Nat لم تُبنَ بعد، وIsnad.Jumla تكراريّةٌ حقًّا)، وجسورُ العوامل/الإسناد/Itar3. لا جدولَ خارجيًّا
  مودَعًا لـZaman5 (`awwaliyyat.tsv` «مرشّحٌ» حتّى يأذن المالك بختمه، ومطابقتُه بالاسم لا بالقيمة) فلا مرآةَ
  بايثون — كالقطع 2–5.
-/
import Aql.Mawsua
import Aql.Awwaliyyat

set_option autoImplicit false

namespace Aql.TashfirAwwaliyyat

open Mawsua Aql.Awwaliyyat

/-! ## Zaman5 — تعدادٌ محدودٌ بلا حمولة؛ ترميزٌ مباشر بلا mixEnc -/

/-- ترميزُ الأزمنة الخمسة: ماضٍ منقطع 0، ماضٍ متّصل 1، حال 2، مستقبل 3، مستقبلٌ منفَّس 4. -/
def zaman5Enc : Zaman5 → Nat
  | .madiMunqati => 0 | .madiMuttasil => 1 | .hal => 2 | .mustaqbal => 3 | .mustaqbalMunaffas => 4

def zaman5Dec : Nat → Zaman5
  | 0 => .madiMunqati | 1 => .madiMuttasil | 2 => .hal | 3 => .mustaqbal | _ => .mustaqbalMunaffas

theorem zaman5_dec_enc (z : Zaman5) : zaman5Dec (zaman5Enc z) = z := by cases z <;> rfl
theorem zaman5Enc_lt (z : Zaman5) : zaman5Enc z < 5 := by cases z <;> decide

/-- **الطيُّ**: `Tayy Zaman5 Nat` مباشرةً، بلا شرطٍ وبلا Unit/Subtype — كـ`tayyKhawass`/`tayyMawdi`. -/
def tayyZaman5 : Tayy Zaman5 Nat where
  tawi := zaman5Enc
  fakk := fun n => some (zaman5Dec n)
  fakk_tawi := fun z => by rw [zaman5_dec_enc]

theorem tayyZaman5_la_yudi (z : Zaman5) : tayyZaman5.fakk (tayyZaman5.tawi z) = some z :=
  tayyZaman5.fakk_tawi z

/-! ## على الشاهد -/

/-- طيُّ وفكُّ الأزمنة الخمسة كلِّها بترتيبها — نفسُ قائمة `Aql.Awwaliyyat.nafy_asma` حرفيًّا، لا شاهدًا مبنيًّا
جديدًا. -/
theorem zaman5_shawahid_tudi :
    [Zaman5.madiMunqati, .madiMuttasil, .hal, .mustaqbal, .mustaqbalMunaffas].map
        (fun z => zaman5Dec (zaman5Enc z)) =
    [Zaman5.madiMunqati, .madiMuttasil, .hal, .mustaqbal, .mustaqbalMunaffas] := by
  simp [zaman5_dec_enc]

end Aql.TashfirAwwaliyyat
