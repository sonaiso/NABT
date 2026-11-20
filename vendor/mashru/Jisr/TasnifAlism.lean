/-
  Jisr/TasnifAlism.lean — المرحلة ٣: تحقّق قسم الاسم من مادّة مدلوله.

  القاعدة نفسها التي في Jisr/Tawafuq.lean: الأقسام (النوع) من الدال وحده، وما يُحكم به على الاسم
  أربعُ صفاتٍ في مدلوله (المادّة، المرحلة ٢)، والتحقّق هنا.

  الصفات الأربع، كلٌّ بسنده في ج3:
  * يمنع تصوّرُه الشركة؟           (745) — يفصل الكلّيّ عن الجزئيّ.
  * استوى معناه في أفراده؟          (745) — يفصل المتواطئ عن المشكّك، في الكلّيّ وحده.
  * دلّ على ذي صفة معيّنة؟           (747) — يفصل المشتقّ عن الجنس، في الكلّيّ وحده.
  * افتقر إلى ما يفسّره؟             (749) — يفصل الضمير عن العلم، في الجزئيّ وحده.

  هذه الصفات لا تُستخرج من اللفظ؛ تُودَع في جدول المعلومات السابقة بشهودها، وإلّا فلا حكم.
-/
import Dal.AqsamAlism

namespace Jisr

open Dal

/-- صفات مدلول الاسم التي يحكم بها ج3 745–749. -/
structure SifatMadlulIsm where
  yamnaShirka : Bool
  istiwa      : Bool
  dhuSifa     : Bool
  muftaqir    : Bool
deriving DecidableEq, Repr

def tasnifIsm (s : SifatMadlulIsm) : QismIsm :=
  if s.yamnaShirka then
    .juzi (if s.muftaqir then .damir else .alam)
  else
    .kulli (if s.istiwa then .mutawati else .mushakkik)
           (if s.dhuSifa then .mushtaq else .jinsJamid)

/-- الكلّيّ ما لا يمنع تصوّره الشركة (745). -/
theorem kulli_iff (s : SifatMadlulIsm) : (tasnifIsm s).isKulli = true ↔ s.yamnaShirka = false := by
  unfold tasnifIsm; cases s.yamnaShirka <;> simp [QismIsm.isKulli]

/-- في الكلّيّ: المشتقّ ما دلّ على ذي صفة، والجنس ما دلّ على الذات (747). -/
theorem mushtaq_iff (s : SifatMadlulIsm) (h : s.yamnaShirka = false) :
    (∃ t, tasnifIsm s = .kulli t .mushtaq) ↔ s.dhuSifa = true := by
  unfold tasnifIsm; rw [h]; cases s.dhuSifa <;> simp

/-- في الجزئيّ: العلم ما استقلّ، والضمير ما افتقر (749). -/
theorem alam_iff (s : SifatMadlulIsm) (h : s.yamnaShirka = true) :
    tasnifIsm s = .juzi .alam ↔ s.muftaqir = false := by
  unfold tasnifIsm; rw [h]; cases s.muftaqir <;> simp

/-- صفتا الكلّيّ لا تعملان في الجزئيّ: قسمه يحدّده الافتقار وحده. -/
theorem juzi_la_yaqra_sifat_kulli (s s' : SifatMadlulIsm)
    (h : s.yamnaShirka = true) (h' : s'.yamnaShirka = true) (hm : s.muftaqir = s'.muftaqir) :
    tasnifIsm s = tasnifIsm s' := by
  unfold tasnifIsm; rw [h, h', hm]; simp

/-- وصفة الجزئيّ لا تعمل في الكلّيّ. -/
theorem kulli_la_yaqra_iftiqar (s s' : SifatMadlulIsm)
    (h : s.yamnaShirka = false) (h' : s'.yamnaShirka = false)
    (hi : s.istiwa = s'.istiwa) (hd : s.dhuSifa = s'.dhuSifa) :
    tasnifIsm s = tasnifIsm s' := by
  unfold tasnifIsm; rw [h, h', hi, hd]; simp

/-- الاستيفاء: كلّ قسم من الستّة يتحقّق من صفاتٍ ما. -/
theorem tasnifIsm_mustawfa (q : QismIsm) : ∃ s, tasnifIsm s = q := by
  rcases q with ⟨t, j⟩ | a
  · refine ⟨⟨false, t = .mutawati, j = .mushtaq, false⟩, ?_⟩
    cases t <;> cases j <;> rfl
  · refine ⟨⟨true, false, false, a = .damir⟩, ?_⟩
    cases a <;> rfl

end Jisr
