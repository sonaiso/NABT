/-
  Jisr/JisrDalUtur.lean — الجسرُ إلى الدالّ وقارئُ الطبقة الثالثة: موافقةُ `JisrDal.hukm` لـ`Utur.halaIrab` في المفرد المنصرف.
  فوق `Jisr/JisrDal.lean` و`Jisr/Utur.lean` معًا (الاتّجاه: الدالُّ ← الطبقةُ الثالثة ← هذا الملفّ؛ لا دورَ في الاستيراد).

  **المبرهنتان (في `Audit.lean`):** `mufrad_halaIrab` — اتّساقٌ بين تعريفين مستقلّين: في المفرد المنصرف غير المنوَّن، الحكمُ من الدالّ معيَّنٌ
  بإعرابٍ إذا وفقط إذا كانت حالتُه عند المالك (`Bridge.irabState`) هي ما يقرؤه `Utur.halaIrab` آخرَ الكلمة — لكلّ كلمةٍ وخليةٍ أخيرةٍ متحرّكة
  دون 116 وإعراب (بالتقسيم على الحالة)؛ `mufrad_tanwin` — التنوينُ (نونٌ ساكنة 59 آخرًا) لا يقرؤه الجسرُ فلا حكم (وقارئُ الطبقة الثالثة — تعريفُ البنّاء في
  `Jisr/Utur.lean` — يقرأ ما قبلَه: التنوينُ في القارئ) — بفكّ التعريف.
-/
import Jisr.JisrDal
import Jisr.Utur

set_option autoImplicit false

namespace Jisr
namespace JisrDalUtur
open SLGE SLGE.Wad JisrDal

/-- **الجسرُ يوافق قارئَ الطبقة الثالثة**: في المفرد المنصرف غير المنوَّن الحكمُ معيَّنٌ بإعرابٍ حالتُه عند المالك (`Bridge.irabState`) هي ما يقرؤه
`Utur.halaIrab` آخرَ الكلمة — لكلّ كلمةٍ وخليةٍ أخيرةٍ متحرّكةٍ دون 116 وإعراب. -/
theorem mufrad_halaIrab (l : List Nat) (c : Nat) (hc : hala c < 3) (h116 : c < 116) (i : Irab) :
    hukm .mufrad (l ++ [c]) = .muayyan i ↔ Bridge.irabState i = Utur.halaIrab true (l ++ [c]) := by
  have h59 : c ≠ 59 := by unfold hala at hc; omega
  have hh : Utur.halaIrab true (l ++ [c]) = c % 4 := by
    unfold Utur.halaIrab
    split
    · rename_i a rest heq; simp at heq; omega
    · rename_i a rest heq; simp at heq; omega
    · rename_i heq; simp at heq
  rw [hh]
  have h3 : c % 4 = 0 ∨ c % 4 = 1 ∨ c % 4 = 2 := by unfold hala at hc; omega
  rcases h3 with h | h | h <;> simp [hukm_append _ _ _ h116, hukmKhaliya, hala, h] <;> cases i <;> simp [Bridge.irabState]

/-- **التنوينُ لا يقرؤه الجسر** (نونٌ ساكنة 59 آخرًا: في القارئ) — بفكّ التعريف. -/
theorem mufrad_tanwin (l : List Nat) (c : Nat) : hukm .mufrad (l ++ [c, 59]) = .laHukm := by
  simp [hukm_append2, hukmKhaliya, hala]

end JisrDalUtur
end Jisr
