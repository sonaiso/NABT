import A116.Alif
import A116.Ishtiqaq
import A116.Ilal

/-!
# الزوائدُ العشر من الـ116: حروفُ «سألتمونيها» حواملُ مرخَّصة، وكلُّ زائدٍ في القوالب منها

حروفُ الزيادة عشرة يجمعها «سألتمونيها»: س ء ل ت م و ن ي ه ا. وهي هنا **حواملُ من الـ29** لا أبجديّةٌ
ثانية: كلُّها في `carriers29` (`zawaid_are_carriers`)، وخاناتُها المرخَّصة 37 = ‎10 × 4 − 3‎ (الألفُ لا
تتحرّك، `Alif`) — `zawaid_cells_licensable`.

## ما يُبرهَن

* `template_lits_from_zawaid`: كلُّ رمزٍ زائدٍ (`lit`) في قوالب `SOUND_TEMPLATES` الإحدى والثلاثين إمّا
  حرفٌ من العشرة وإمّا علامةُ حالة (فتحة، ضمّة، كسرة، سكون، شدّة) — فالزائدُ في الاشتقاق مرخَّصٌ من الـ116
  بعينه. والطفرة: «ط» ليست زائدةً، وقالبٌ يزيدها يُرفض (`tafa_template_rejected`).
* **التقشير** (`peel_returns_root`): إسقاطُ الزوائد بالقالب يعيد الأصلَ الثلاثيّ بعينه، لكلّ أصلٍ ولكلّ
  قالبٍ سليم (من `Ishtiqaq.extract_fill_wf`) — وحدُّه مبرهَن: الصيغةُ وحدَها لا تعيّن الأصل
  (`Ishtiqaq.form_alone_does_not_determine_root`)، فالتقشيرُ مشروطٌ بالوزن.
* **الإبدالُ ترخيصٌ غيرُ الزيادة** (`ibdal_targets_outside_zawaid`): الطاءُ والدالُ اللتان يُبدَل إليهما
  تاءُ الافتعال (`Ilal` القاعدتان 8 و9) ليستا من العشرة؛ فالإبدالُ يُرخَّص بقاعدته المسمّاة في `Ilal`
  (ردٌّ بالسجلّ وحفظُ الترخيص: `ibdal_restore`، `admissible_replace_carrier`) لا بقائمة الزوائد.

## ما لم يُبرهَن (معلَّقٌ باسمه)

* «قانونُ ا و ا و ا»: الابتداءُ والوصلُ والوقف (`ExhaustPause.awa`، ADR ١٨)، وقانونُ الحاجة المتبادلة الذي يحكمه
  (`A116.Hajah`، ADR ٢٢).
* إعادةُ تدوير الزوائد «بالاستنفاد» درجةً درجة: يحتاج جدولَ الدرجات (`A116.Exhaust`) بحقل الاشتقاق، وهو
  معلَّقٌ في الدفتر الحاليّ (`JAMID_MUSHTAQ_PER_NUMBER_UNDEFINED`).
-/

set_option autoImplicit false

namespace A116.Zawaid

open A116 A116.Ladder A116.Field112 A116.Ishtiqaq

/-- حروفُ «سألتمونيها» بترتيب الكلمة، والهمزةُ حاملُها `ء`. -/
def zawaid : List Char := ['س', 'ء', 'ل', 'ت', 'م', 'و', 'ن', 'ي', 'ه', 'ا']

theorem zawaid_length : zawaid.length = 10 := rfl

theorem zawaid_nodup : zawaid.Nodup := by decide

/-- الزوائدُ حواملُ من الـ29. -/
theorem zawaid_are_carriers : zawaid.all (carriers29.contains ·) = true := by decide

/-- خاناتُ الزوائد المرخَّصة: كلُّ خانةٍ من `licensable` حاملُها من العشرة. -/
def zawaidCells : List Cell :=
  Alif.licensable.filter fun c => zawaid.contains (carrierChar c.carrier)

theorem zawaid_cells_licensable : zawaidCells.length = 37 := by decide

/-- علاماتُ الحالة في القوالب: فتحة، ضمّة، كسرة، سكون، شدّة. -/
def marks : List Char := ['َ', 'ُ', 'ِ', 'ْ', 'ّ']

def litOK : Sym Char → Bool
  | .lit c => zawaid.contains c || marks.contains c
  | .slot _ => true

/-- **كلُّ زائدٍ في القوالب الإحدى والثلاثين حرفٌ من «سألتمونيها» أو علامةُ حالة.** -/
theorem template_lits_from_zawaid : ∀ t ∈ soundTemplates, t.all litOK = true := by decide

/-- الطفرةُ المرفوضة: قالبٌ يزيد الطاء (ليست من العشرة) لا يمرّ. -/
theorem tafa_template_rejected :
    ([.lit 'ط', .lit 'َ', .slot 0, .lit 'َ', .slot 1, .lit 'َ', .slot 2] : Template Char).all litOK = false := by
  decide

/-- **التقشير**: إسقاطُ الزوائد بالقالب يعيد الأصلَ بعينه، لكلّ أصلٍ ولكلّ قالبٍ سليم. -/
theorem peel_returns_root {t : Template Char} (h : WF t) (r : Root Char) :
    extract t (fill t r) = [r 0, r 1, r 2] :=
  extract_fill_wf h r

/-- **التقشيرُ من القوالب كلِّها**: لكلّ قالبٍ من الإحدى والثلاثين ولكلّ أصل. -/
theorem peel_sound_templates : ∀ t ∈ soundTemplates, ∀ r : Root Char,
    extract t (fill t r) = [r 0, r 1, r 2] :=
  fun t ht r => extract_fill_wf (soundTemplates_wf t ht) r

/-- الإبدالُ غيرُ الزيادة: الطاءُ والدالُ ليستا من العشرة. -/
theorem ibdal_targets_outside_zawaid : zawaid.contains 'ط' = false ∧ zawaid.contains 'د' = false := by
  decide

end A116.Zawaid
