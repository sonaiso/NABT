/-
  Aql/TashfirMirsat.lean — جسرُ المعلومة المعمَّم (الثالث): طيُّ وفكُّ Aql.Mirsat.Mirsat (المرساة: الآنُ
  زمنًا وهنا مكانًا) بإعادة استعمال `zigzag`/`BOUND` من Madlul/TashfirMadda.lean بعينها — لا قناةً موازية.

  السند: طلب المالك 2026-10-17 22:55: «Khawass/alaqat/hawass/awwaliyyat/azmina/makan/mirsat/isnad: مؤجَّلة
  بالاسم. ايضا نفذ انت مفوض مني». Mirsat من هذا الاسم، واختيرت ثانيةً (بعد Khawass) لأنّها أقربُ القطعة
  بنيةً لِما طُوي فعلًا في TashfirMadda: حقولُها الأربعة (`an`، و`huna.amudi/ufuqi/tuli`) كلُّها Int طليقةٌ —
  لا قوائمَ ولا أنواعًا محدودة (بخلاف Khawass) — فالأداةُ الموجودةُ بعينها (`zigzag`/`unzigzag`/`BOUND`) تكفي
  بلا أداةٍ جديدة؛ هذا استثمارٌ مباشرٌ لِما بُني، لا تكرارٌ.

  **الصورة.** `Aql.Makan.Izaha3` ثلاثةُ حقولٍ Int (amudi, ufuqi, tuli)، و`Aql.Mirsat.Mirsat` حقلان: `an : Int`
  و`huna : Izaha3` — أربعةُ Int إجمالًا. الطيُّ طبقتان من `SLGE.mixEnc` على زِكزاك الأربعة (لا ثلاثًا كـMadda،
  لأنّ لا Option هنا، كلُّ حقلٍ Int مباشرةً فلا حاجةَ لِـ`optIntEnc`): طبقةٌ تطوي الثلاثةَ المكانيّة، وطبقةٌ
  تضمّ نتيجتَها إلى الزمن. **الشرطُ** (`Sahih`) هنا كـMadda تمامًا — غيرُ مشروطٍ على شكل Mirsat بل على بقاء
  زِكزاك الأربعة دون BOUND؛ وخلافًا لـKhawass (غيرُ مشروطةٍ أصلًا) فهذه مشروطةٌ حقًّا لأنّ Int طليقٌ لا محدود.

  ما يُبرهن هنا: `mirsat_dec_enc` (نقلٌ مباشرٌ لـ`SLGE.mixDec_enc` مرّتين و`zigzag_unzigzag` أربعَ مرّات)؛
  `fakkOf_tawiOf`/`tayyMirsat_la_yudi` (Tayy MirsatUnit Nat، Subtype على Sahih كـTashfirMadda.MaddaUnit
  بعينه)؛ وعلى الشاهد `shawahid_sahih`/`mirsat_shawahid_tudi` (ثلاثةُ مراسٍ مبنيّةٍ: الأصلُ `⟨0, Makan.sifr⟩`
  الذي يَرِد بلفظه في Aql/Isnad.lean شاهدَي «ههنا عمرو» و«فيها عبد الله»، ومرساتان بقيمٍ سالبةٍ وموجبةٍ على
  المحاور الأربعة معًا — لا مودَعَ لهذه القطعة فلا جدول خارجيّ، كالمدلولات المبنيّة في Jisr/Utur.lean).

  مؤجَّلٌ: alaqat (Shabaka)، hawass (Hawass)، awwaliyyat (Awwaliyyat)، azmina (Azmina.Izaha نفسُها — أقربُ
  القطعة التالية بنيةً، حقلان Int/Wahda فقط)، makan (Makan.Izaha3 المجرَّدة، وMawdi/Jar)، isnad
  (Aql.Isnad.Jumla التكراريّة حقًّا — تحتاج ترميز شجرةٍ لا طبقاتِ mixEnc المسطَّحة). وجسرا العوامل وItar3 على
  هذه الآلة نفسِها.
-/
import Madlul.TashfirMadda
import Aql.Mirsat

set_option autoImplicit false

namespace Aql.TashfirMirsat

open Mawsua Madlul.TashfirMadda Aql.Makan Aql.Mirsat

/-- شرطُ الصحّة: زِكزاكُ الأربعة (الزمن والمحاور الثلاثة) دون BOUND — لا شرطَ على شكل Mirsat. -/
def Sahih (r : Mirsat) : Prop :=
  zigzag r.an < BOUND ∧ zigzag r.huna.amudi < BOUND ∧ zigzag r.huna.ufuqi < BOUND ∧ zigzag r.huna.tuli < BOUND

/-- **الطيّ**: طبقةٌ للمحاور الثلاثة، ثمّ طبقةٌ تضمّ الزمن. -/
def mirsatEnc (r : Mirsat) : Nat :=
  let l1 := SLGE.mixEnc BOUND BOUND (zigzag r.huna.amudi) (zigzag r.huna.ufuqi) (zigzag r.huna.tuli)
  SLGE.mixEnc BOUND BOUND l1 (zigzag r.an) 0

/-- **الفكّ**: عكسُ الطيّ طبقةً طبقة. -/
def mirsatDec (n : Nat) : Mirsat :=
  match SLGE.mixDec BOUND BOUND n with
  | (l1, anC, _) =>
    match SLGE.mixDec BOUND BOUND l1 with
    | (amudiC, ufuqiC, tuliC) =>
      { an := unzigzag anC, huna := { amudi := unzigzag amudiC, ufuqi := unzigzag ufuqiC, tuli := unzigzag tuliC } }

/-- **الفكُّ يعيد الأصل تحت شرط الصحّة** — نقلٌ مباشرٌ لـ `SLGE.mixDec_enc` مرّتين و`zigzag_unzigzag` أربعَ مرّات. -/
theorem mirsat_dec_enc (r : Mirsat) (h : Sahih r) : mirsatDec (mirsatEnc r) = r := by
  obtain ⟨h1, h2, h3, h4⟩ := h
  simp only [mirsatDec, mirsatEnc,
    SLGE.mixDec_enc BOUND BOUND _ (zigzag r.an) 0 h1 bound_pos,
    SLGE.mixDec_enc BOUND BOUND (zigzag r.huna.amudi) (zigzag r.huna.ufuqi) (zigzag r.huna.tuli) h3 h4,
    zigzag_unzigzag]

/-! ## الطيّ على الحامل المقيَّد بـ Sahih (Subtype)، على نمط TashfirMadda.MaddaUnit بعينه -/

def MirsatUnit : Type := {r : Mirsat // Sahih r}

noncomputable def fakkOf (code : Nat) : Option MirsatUnit :=
  @dite (Option MirsatUnit) (Sahih (mirsatDec code)) (Classical.propDecidable _)
    (fun h => some ⟨mirsatDec code, h⟩) (fun _ => none)

theorem fakkOf_tawiOf (u : MirsatUnit) : fakkOf (mirsatEnc u.1) = some u := by
  obtain ⟨r, hr⟩ := u
  show fakkOf (mirsatEnc r) = some ⟨r, hr⟩
  have heq : mirsatDec (mirsatEnc r) = r := mirsat_dec_enc r hr
  unfold fakkOf
  rw [heq, dite_eq_left hr]

noncomputable def tayyMirsat : Tayy MirsatUnit Nat where
  tawi := fun u => mirsatEnc u.1
  fakk := fakkOf
  fakk_tawi := fakkOf_tawiOf

theorem tayyMirsat_la_yudi (u : MirsatUnit) : tayyMirsat.fakk (tayyMirsat.tawi u) = some u :=
  tayyMirsat.fakk_tawi u

/-! ## على الشاهد: ثلاثُ مراسٍ مبنيّة (لا مودَع لهذه القطعة) -/

/-- الأصل: الآن صفرٌ وهنا السفرُ المطلق — بلفظه في Aql/Isnad.lean («ههنا عمرو»، «فيها عبد الله»). -/
def mirsatAsl : Mirsat := ⟨0, Makan.sifr⟩
/-- مرساةٌ بقيمٍ سالبةٍ وموجبةٍ معًا على الزمن والمحاور الثلاثة. -/
def mirsatThani : Mirsat := ⟨-5, ⟨3, -7, 12⟩⟩
def mirsatThalith : Mirsat := ⟨1000, ⟨-1, -1, -1⟩⟩

theorem shawahid_sahih : Sahih mirsatAsl ∧ Sahih mirsatThani ∧ Sahih mirsatThalith := by
  unfold Sahih mirsatAsl mirsatThani mirsatThalith Makan.sifr zigzag BOUND
  decide

theorem mirsat_shawahid_tudi :
    mirsatDec (mirsatEnc mirsatAsl) = mirsatAsl ∧ mirsatDec (mirsatEnc mirsatThani) = mirsatThani ∧
    mirsatDec (mirsatEnc mirsatThalith) = mirsatThalith := by
  obtain ⟨s1, s2, s3⟩ := shawahid_sahih
  exact ⟨mirsat_dec_enc mirsatAsl s1, mirsat_dec_enc mirsatThani s2, mirsat_dec_enc mirsatThalith s3⟩

end Aql.TashfirMirsat
