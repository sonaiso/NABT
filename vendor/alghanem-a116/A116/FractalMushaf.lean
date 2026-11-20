import A116.FractalData
import A116.FractalHadd

/-!
# الفراكتالُ على المصحف كلِّه: من التشغيل إلى النواة (ADR ٧٨)

`A116.FractalData` صفٌّ لكلّ آية من تشغيل البوّابة على المصحف المختوم (`tools/gen_fractal.py`، يُطابَق في CI).
والنواةُ هنا تحسب على المودَع، لا تقرأ أرقامًا مكتوبة:

* **المرحلةُ الأولى على الأصناف** (`athar_mushaf`): أثرُ المصحف طيُّ آثار آياته من الصفر (`comp`، `sifr`) — وهو
  بـ`Fractal.fractal_append` أثرُ المصحف مسطَّحًا — فيُرسل كلَّ حالةٍ ابتدائيّة إلى `cv`: تسلسلُ الأصناف لا ينقطع.
* **العدّ** (`kalimat_count`): الكلماتُ الجاهزة بلا سياق، والمرفوضة، والآيات.
* **المرحلةُ الثانية بالحدّ والإصلاح** (`mawsul_sahih`): كلُّ آيةٍ جهزت كلماتُها في سياقها قبلتها آلةُ الحرف وقفًا
  بحدّها بين الكلمات بعد الإصلاح (`Harf.lineWaqfB` = `strictLinePauseB`) — والنصُّ عطفُ آياته (`FractalHadd.text_for`).
* **الإصلاحُ صفر** (`islah_sifr`): ما حرّكه الحدُّ بعد حدٍّ مُصلَح صفر على المصحف كلِّه — مثولُ `FractalHadd.repair_seam_zero`.
-/

namespace A116.FractalMushaf

set_option maxRecDepth 200000

/-- أثرُ المصحف: طيُّ آثار الآيات من الصفر. -/
def atharMushaf : List Nat := ayat.foldl (fun acc a => comp acc a.athar) sifr

/-- **المرحلةُ الأولى**: كلُّ حالةٍ ابتدائيّة تنتهي بـ`cv` (الرقم 1). -/
theorem athar_mushaf : atharMushaf = [1, 1, 1, 1] := by decide +kernel

/-- **العدّ**: الآيات. -/
theorem ayat_count : ayat.length = 6236 := by decide +kernel

/-- **والكلماتُ** الجاهزة بلا سياق، والمرفوضة. -/
theorem kalimat_count : (ayat.map Aya.ready).sum = 78207 ∧ (ayat.map Aya.refused).sum = 38 := by
  decide +kernel

/-- **المرحلةُ الثانية**: كلُّ آيةٍ جاهزةٍ في سياقها موصولةٌ صحيحًا بقيد الحدّ بعد الإصلاح. -/
theorem mawsul_sahih : ayat.all (fun a => !a.ctx || a.accepted) = true := by decide +kernel

/-- الآياتُ الجاهزة في سياقها. -/
theorem ayat_ctx_count : (ayat.filter Aya.ctx).length = 6198 := by decide +kernel

/-- حدودُها، والمُصلَحُ منها، وما حرّكه الحدّ. -/
theorem hadd_counts :
    ((ayat.filter Aya.ctx).map Aya.seams).sum = 71651 ∧
    (ayat.map Aya.repairs).sum = 2752 ∧
    (ayat.map Aya.moved).sum = 16188 := by
  decide +kernel

/-- **الإصلاحُ صفر على المصحف**: لا حدَّ مُصلَحًا حرّكه الحدّ. -/
theorem islah_sifr : (ayat.map Aya.movedRepaired).sum = 0 := by decide +kernel

/-- **النصُّ عطفُ آياته**: طيُّ العطف من الصحيح على الآيات الجاهزة صحيح. -/
theorem nass_atf : (ayat.filter Aya.ctx).foldl (fun acc a => acc && a.accepted) true = true := by
  decide +kernel

end A116.FractalMushaf
