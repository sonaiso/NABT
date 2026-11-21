/-
  Madlul/Jamad.lean — تصنيفُ الجماد: الكمُّ (الكتلة والحجم والكثافة والحرارة)، والحالاتُ الثلاث وقابليّاتُ التحوّل بعتباتها،
  وقانونُ التعيين في التحوّل (الشيءُ هو هو)، وشروطُ نظام الفيزياء ونظام الرياضيات، والوحدةُ والكثرة بوجهيها.

  قرارُ المالك (2026-10-16، 13:19): «الجماد يصنف وفق الكثافة والكتلة والخواص والقابليات والعلاقات والتحول على سبيل سائل أو غاز أو
  صلب وقانون التوريث والوراثة وفق نظام التعيين والتمييز وشروط نظام الفيزياء والوحدة والكثرة وشروط نظام الرياضات»؛ وإمضاؤه (13:26):
  أعمدةُ الكمّ الكتلةُ والحجمُ والكثافةُ ومعها الحرارةُ وعتباتُ التحوّل؛ والوحدةُ والكثرةُ بوجهيها (الدالّ والمدلول)؛ «ابني مبرهنات».
  قانونُ التوريث في `Madlul/Wiratha.lean`.

  **السند من المودَعات المختومة** (بأسطرها؛ الاقتباساتُ بلفظ المصدر وتشكيلُها مضاف):
  - المخصّص س32363 (باب الثلج والبرد ونحوهما): «الثلج ما جمد من الماء بالنهار والليل» — الثلجُ ماءٌ في حالةٍ (الجمود): الحقيقةُ
    واحدةٌ والحالةُ مختلفة.
  - لسان العرب س56094: «الجمد، بالتحريك: الماء الجامد»؛ س13356: «الذوب: ضد الجمود. ذاب يذوب ذوبا وذوبانا: نقيض جمد» — التحوّلان
    متقابلان؛ س205864: «سال الماء والشيء سيلا وسيلانا: جرى»؛ س73042: «وبخار القدر: ما ارتفع منها» — فألفاظُ المعجم للحالات:
    الجامد والسائل والبخار (وبلفظ المالك: صلب/سائل/غاز).
  - لسان س77655: «الحجر: الصخرة، والجمع في القلة أحجار، وفي الكثرة حجار وحجارة» — الوحدةُ والكثرةُ في الدالّ (جمعُ القلّة والكثرة)؛
    س203789: «نوع معروف من التراب، وجمعه الرمال، والقطعة منها رملة» (الرمل) — تاءُ الوحدة تُفرد قطعةً من المقيس (الرملُ نوعٌ من
    التراب: جنسٌ أعلى بلفظ المعجم)؛ س88481: «الصخرة: الحجر العظيم الصلب» — الكمُّ (العظم) قبل الكيف (الصلابة).
  - لسان س56549: «والحديد: هذا الجوهر المعروف»؛ س127388: «والرصاص: معروف من المعدنيات»؛ س13283: «والذهب: معروف»؛ س178415:
    «والزئبق: الزاووق؛ فارسي معرب»؛ س49808: «الملح: ما يطيب به الطعام»؛ س265253: «الماء والماه والماءة: معروف».
  - المخصّص س35587: «باب نعوت الصخر من قبل عظمها» — ترتيبُ ابن سيده في الجماد يبدأ بالكمّ (س261–263: كمٌّ قبل كيف).
  - مدلولُ المالك `SLGE.Awwalan.Madlul` (س24–47): `afrad` و`kulli` و`tawatu` (متواطئ/مشكّك على الأفراد).

  **الصورة.** `Hala` الحالاتُ الثلاث مرتّبةً بالحرارة (`daraja`)؛ `Tahawwul` التحوّلاتُ الأربعة؛ `tahawwul` آلةُ الحالات؛ `Madda`
  مادّةٌ (جنسٌ من الجماد مقيس): حقيقتُها، وكثافتُها لكلّ حالة (غ/م³؛ `none` لا حكم)، وعتبتا الذوب والغليان (°م عند ضغطٍ مرجعيّ؛
  `none` لا حكم); `halaInda m t` الحالةُ عند حرارةٍ (ف4)؛ `Fard` فردٌ من مادّة بحالةٍ وكتلة (ميكروغرام) — `tahawwal` يغيّر الحالةَ
  وحدَها؛ `Jism` جسمٌ معدود (مادّة، حالة، حجم سم³) وكتلتُه من الكثافة (ف1)؛ `Wahda` معدود/مقيس و`ifrad` (تاءُ الوحدة تُفرد واحدًا).
  الوحداتُ صحيحةٌ كلُّها (ر2): الكثافةُ غ/م³ = ميكروغرام/سم³، فكتلةُ الجسم (ميكروغرام) = كثافة × حجم بلا قسمة (ر3).

  **شروطُ نظام الفيزياء** (جدولُ «نظام الفيزياء» المودَع `nizam_fizya.tsv`؛ مرآتُها هنا): ف1 الكتلةُ من الكثافة والحجم (`Jism.kutla`)؛
  ف2 حفظُ الكتلة في التحوّل (`tahawwul_yahfaz_kutla`) وجمعُها على الأجزاء (`kutla_majmu`)؛ ف3 عتبةُ الذوب دون عتبة الغليان
  (`muttasiq`)؛ ف4 الحالةُ بالحرارة بين العتبتين (`halaInda`، `hala_ratiba`)؛ ف5 التحوّلاتُ بين الحالات المتجاورة وتقابلُها
  (`dhawb_jumud`، `tabakhkhur_takathuf`، `tahawwul_daraja`)؛ ف6 الطفو: الأقلُّ كثافةً يطفو على الأكثر (`yatfu`).
  **شروطُ نظام الرياضيات** (`nizam_riyadiyyat.tsv`): ر1 الكمُّ منفصلٌ للمعدود ومتّصلٌ للمقيس (`Wahda`)؛ ر2 الوحداتُ الصغرى والأعدادُ
  الصحيحة؛ ر3 النسبةُ بالضرب التبادليّ بلا قسمة؛ ر4 الوسيط: كثافةُ المركّب بين كثافتي جزأيه — الكثافةُ لا تُجمع (`kathafa_la_tujma`)؛
  ر5 الترتيبُ الكلّيّ على الأعداد فالتصنيفُ بالكثافة والكتلة ترتيب (`tartib_kathafa`)؛ ر6 الواحدُ والأفراد (`ifrad`، `tawatu`).

  **المبرهنات (لكلّ):** `hala_ratiba` (الحالةُ رتيبةٌ في الحرارة)، `sail_bayn` (السائلُ بين العتبتين)، `dhawb_jumud`/`tabakhkhur_takathuf`
  (التحوّلان المتقابلان يتعاكسان)، `tahawwul_yughayyir` (كلُّ تحوّلٍ ناجح يغيّر الحالة)، `tahawwul_daraja` (التسخينُ يرفع درجةً والتبريدُ
  ينزلها)، `tahawwul_la_yughayyir_haqiqa` (**قانونُ التعيين: التحوّلُ لا يغيّر الحقيقة**)، `tahawwul_yahfaz_kutla` (ف2)،
  `kutla_majmu` (كتلةُ الكلّ مجموعُ أجزائه)، `kathafa_la_tujma` (ر4)، `tartib_kathafa` (ر5)، `ifrad_madud` (ر6)،
  `jism_kutla_la_hukm` (لا كثافةَ فلا كتلةَ محسوبة — لا حكم). **على الشاهد** (المواد الستّ ببصمة مرجعها في الجدول المودَع):
  `shawahid_hala` (الحالةُ المرجعية عند 25°م من العتبات: الماءُ والزئبقُ سائلان والباقي جامد)، `shawahid_muttasiq` (ف3 على الستّ)،
  `thalj_ma` (الثلجُ ماءٌ: التجمّدُ يحفظ الحقيقةَ والكتلة ويزيد الحجم: 100 غ ماءً 100 سم³ وثلجًا 109)، `thalj_yatfu` (الثلجُ يطفو على
  الماء: 916,700 < 997,047)، `kathafa_mushakkika` (الكثافةُ مشكّكةٌ على أفراد الماء بحالاته — على `tawatu` المالك)؛ وتعريفيّة (تمثيلٌ
  معلَن لا شاهد): `haqiqa_mutawatia` (أفرادٌ بحقيقةٍ واحدة متواطئون بالبناء).

  الوسم: مبرهن (لكلّ): ما سُمّي لكلّ أعلاه؛ مبرهن على الشاهد (decide على جدول `mawadd`، وهو مطابَقٌ قيمةً قيمة لصفوف «ثابت» في
  المودَع المختوم «نظام الفيزياء» `nizam_fizya.tsv` (`eb761b85…`) بـ `test_jamad.py`): `shawahid_hala`، `shawahid_muttasiq`،
  `thalj_ma`، `thalj_yatfu`، `kathafa_mushakkika`. قيمُ الكمّ نقلَها البنّاء من صفحات Wikipedia (Iron, Gold, Lead, Mercury (element),
  Sodium chloride, Properties of water — قُرئت بأداةٍ في الجلسة 2026-10-16) مقرَّبةً إلى الصحيح: غ/م³ من g/cm³ ×1,000,000 (7.874 →
  7,874,000)، و°م إلى أقرب صحيح (99.98 → 100؛ −38.829 → −39؛ 327.46 → 327؛ 800.7 → 801؛ 1064.18 → 1064) — فالقيمُ في مودَعٍ مختوم من
  نقل البنّاء، ومرجعُها الأصليّ غيرُ مودَع: فهي «علمي» لا «مقيس» حتّى يُودَع مرجعٌ محجوب ويُقاس عليه.
-/
import Madlul.Wiratha

set_option autoImplicit false

namespace Madlul
namespace Jamad
open Tayin Wiratha SLGE.Awwalan

/-- الحالاتُ الثلاث بألفاظ المعجم (الجامد س56094، السائل س205864، البخار س73042؛ وبلفظ المالك صلب/سائل/غاز)، مرتّبةً بالحرارة. -/
inductive Hala | jamid | sail | bukhar
deriving DecidableEq, Repr

/-- درجةُ الحالة في سلّم الحرارة. -/
def Hala.daraja : Hala → Nat
  | .jamid => 0
  | .sail => 1
  | .bukhar => 2

/-- التحوّلاتُ الأربعة: الذوبُ والجمودُ (متقابلان: لسان س13356)، والتبخّرُ والتكثّف. -/
inductive Tahawwul | dhawb | jumud | tabakhkhur | takathuf
deriving DecidableEq, Repr

/-- آلةُ الحالات (ف5): التسخينُ يرفع إلى الحالة المجاورة، والتبريدُ ينزل؛ وما سواه لا تحوّل. -/
def tahawwul : Tahawwul → Hala → Option Hala
  | .dhawb, .jamid => some .sail
  | .tabakhkhur, .sail => some .bukhar
  | .takathuf, .bukhar => some .sail
  | .jumud, .sail => some .jamid
  | _, _ => none

/-- **التحوّلان المتقابلان يتعاكسان** (الذوبُ ضدّ الجمود: لسان س13356): جمودٌ بعد ذوبٍ يعيد الحالة. -/
theorem dhawb_jumud (h h' : Hala) (e : tahawwul .dhawb h = some h') : tahawwul .jumud h' = some h := by
  cases h <;> cases h' <;> simp_all [tahawwul]

theorem tabakhkhur_takathuf (h h' : Hala) (e : tahawwul .tabakhkhur h = some h') :
    tahawwul .takathuf h' = some h := by
  cases h <;> cases h' <;> simp_all [tahawwul]

/-- **كلُّ تحوّلٍ ناجح يغيّر الحالة.** -/
theorem tahawwul_yughayyir (c : Tahawwul) (h h' : Hala) (e : tahawwul c h = some h') : h' ≠ h := by
  cases c <;> cases h <;> cases h' <;> simp_all [tahawwul]

/-- **التسخينُ يرفع درجةً واحدة والتبريدُ ينزلها** (ف5). -/
theorem tahawwul_daraja (c : Tahawwul) (h h' : Hala) (e : tahawwul c h = some h') :
    h'.daraja = h.daraja + 1 ∨ h'.daraja + 1 = h.daraja := by
  cases c <;> cases h <;> cases h' <;> simp_all [tahawwul, Hala.daraja]

/-- مادّةٌ (جنسٌ من الجماد، مقيس): حقيقتُها، وكثافتُها لكلّ حالة (غ/م³؛ `none` لا حكم)، وعتبتا الذوب والغليان (°م؛ `none` لا حكم). -/
structure Madda where
  haqiqa : Nat
  kJamid : Option Nat := none
  kSail : Option Nat := none
  kBukhar : Option Nat := none
  dhawb : Option Int := none
  ghalayan : Option Int := none
deriving DecidableEq, Repr

/-- الكثافةُ بحسب الحالة. -/
def Madda.kathafa (m : Madda) : Hala → Option Nat
  | .jamid => m.kJamid
  | .sail => m.kSail
  | .bukhar => m.kBukhar

/-- **ف3:** عتبةُ الذوب دون عتبة الغليان — حيث حضرتا. -/
def muttasiq (m : Madda) : Prop := ∀ d g : Int, m.dhawb = some d → m.ghalayan = some g → d < g

/-- فاحصُ ف3 المحسوب: صادقٌ حيث غابت عتبة (لا حكم)، وحيث حضرتا فبالمقارنة. -/
def muttasiqB (m : Madda) : Bool :=
  match m.dhawb, m.ghalayan with
  | some d, some g => decide (d < g)
  | _, _ => true

/-- الفاحصُ سليم: ما قبله فمتّسق. -/
theorem muttasiqB_salim (m : Madda) (h : muttasiqB m = true) : muttasiq m := by
  intro d g hd hg
  unfold muttasiqB at h
  simp only [hd, hg] at h
  exact of_decide_eq_true h

/-- **ف4:** الحالةُ عند حرارةٍ `t`: دون الذوب جامد، ودون الغليان سائل، وإلّا بخار؛ وبغياب عتبةٍ «لا حكم». -/
def halaInda (m : Madda) (t : Int) : Option Hala :=
  match m.dhawb, m.ghalayan with
  | some d, some g => some (if t < d then .jamid else if t < g then .sail else .bukhar)
  | _, _ => none

/-- الحالةُ المرجعية: عند 25°م. -/
def halaMarjiiyya (m : Madda) : Option Hala := halaInda m 25

/-- **الحالةُ رتيبةٌ في الحرارة** (ف4): ما ارتفعت الحرارةُ لم تنزل الحالة. -/
theorem hala_ratiba (m : Madda) (t t' : Int) (h h' : Hala) (ht : t ≤ t')
    (e : halaInda m t = some h) (e' : halaInda m t' = some h') : h.daraja ≤ h'.daraja := by
  unfold halaInda at e e'
  cases hd : m.dhawb with
  | none => simp [hd] at e
  | some d =>
    cases hg : m.ghalayan with
    | none => simp [hd, hg] at e
    | some g =>
      simp only [hd, hg, Option.some.injEq] at e e'
      subst e; subst e'
      by_cases h1 : t < d <;> by_cases h2 : t < g <;> by_cases h3 : t' < d <;> by_cases h4 : t' < g <;>
        simp [h1, h2, h3, h4, Hala.daraja] <;> omega

/-- **السائلُ بين العتبتين:** إن كانت الحالةُ سائلةً عند `t` فعتبةُ الذوب ≤ t < عتبةُ الغليان. -/
theorem sail_bayn (m : Madda) (t : Int) (d g : Int) (hd : m.dhawb = some d) (hg : m.ghalayan = some g)
    (e : halaInda m t = some .sail) : d ≤ t ∧ t < g := by
  unfold halaInda at e
  simp only [hd, hg, Option.some.injEq] at e
  by_cases h1 : t < d <;> by_cases h2 : t < g <;> simp [h1, h2] at e <;> omega

/-- فردٌ من مادّة: المادّةُ (الحقيقة) وحالتُه الراهنة وكتلتُه (ميكروغرام). -/
structure Fard where
  madda : Madda
  hala : Hala
  kutla : Nat
deriving DecidableEq, Repr

/-- التحوّلُ على الفرد: يغيّر الحالةَ وحدَها. -/
def Fard.tahawwal (f : Fard) (c : Tahawwul) : Option Fard :=
  (tahawwul c f.hala).map fun h => { f with hala := h }

/-- **قانونُ التعيين: التحوّلُ لا يغيّر الحقيقة** (الثلجُ ماءٌ جمد — المخصّص س32363؛ الجمدُ الماءُ الجامد — لسان س56094):
لكلّ فردٍ وتحوّلٍ ناجح، المادّةُ هي هي. -/
theorem tahawwul_la_yughayyir_haqiqa (f f' : Fard) (c : Tahawwul) (e : f.tahawwal c = some f') :
    f'.madda = f.madda := by
  unfold Fard.tahawwal at e
  cases hc : tahawwul c f.hala <;> simp [hc] at e
  subst e; rfl

/-- **ف2: حفظُ الكتلة في التحوّل.** -/
theorem tahawwul_yahfaz_kutla (f f' : Fard) (c : Tahawwul) (e : f.tahawwal c = some f') : f'.kutla = f.kutla := by
  unfold Fard.tahawwal at e
  cases hc : tahawwul c f.hala <;> simp [hc] at e
  subst e; rfl

/-- حجمُ الفرد من كتلته وكثافة حالته (سم³ = ميكروغرام ÷ (غ/م³))؛ بلا كثافةٍ لا حكم. -/
def Fard.hajm (f : Fard) : Option Nat := (f.madda.kathafa f.hala).map fun ρ => f.kutla / ρ

/-- **ف2: كتلةُ الكلّ مجموعُ كتل أجزائه** (علاقةُ الجزء). -/
def kutlaMajmu (ajza : List Fard) : Nat := (ajza.map Fard.kutla).sum

theorem kutla_majmu (a : Fard) (rest : List Fard) : kutlaMajmu (a :: rest) = a.kutla + kutlaMajmu rest := by
  simp [kutlaMajmu]

/-- **ر4 الوسيط — الكثافةُ لا تُجمع:** جزآن بكثافتين ρ₁ ≤ ρ₂ وحجمين v₁ وv₂: كثافةُ المركّب (كتلتُه على حجمه) بين الكثافتين —
بالضرب التبادليّ بلا قسمة: ρ₁(v₁+v₂) ≤ ρ₁v₁+ρ₂v₂ ≤ ρ₂(v₁+v₂). -/
theorem kathafa_la_tujma (ρ₁ ρ₂ v₁ v₂ : Nat) (h : ρ₁ ≤ ρ₂) :
    ρ₁ * (v₁ + v₂) ≤ ρ₁ * v₁ + ρ₂ * v₂ ∧ ρ₁ * v₁ + ρ₂ * v₂ ≤ ρ₂ * (v₁ + v₂) := by
  have a := Nat.mul_le_mul_right v₂ h
  have b := Nat.mul_le_mul_right v₁ h
  rw [Nat.mul_add, Nat.mul_add]
  exact ⟨Nat.add_le_add_left a _, Nat.add_le_add_right b _⟩

/-- جسمٌ (معدود): مادّةٌ بحالةٍ وحجم (سم³). -/
structure Jism where
  madda : Madda
  hala : Hala
  hajm : Nat
deriving DecidableEq, Repr

/-- **ف1: الكتلةُ من الكثافة والحجم** (ميكروغرام = غ/م³ × سم³)؛ بلا كثافةٍ لا حكم. -/
def Jism.kutla (j : Jism) : Option Nat := (j.madda.kathafa j.hala).map fun ρ => ρ * j.hajm

/-- لا كثافةَ للحالة فلا كتلةَ محسوبة — «لا حكم» لا صفر. -/
theorem jism_kutla_la_hukm (j : Jism) (h : j.madda.kathafa j.hala = none) : j.kutla = none := by
  simp [Jism.kutla, h]

/-- **ف6 الطفو:** يطفو جسمٌ على سائلٍ إذا كانت كثافتُه دون كثافة السائل؛ وبغياب إحداهما لا حكم. -/
def yatfu (j : Jism) (sail : Madda) : Option Bool :=
  match j.madda.kathafa j.hala, sail.kSail with
  | some a, some b => some (decide (a < b))
  | _, _ => none

/-- **ر5 — التصنيفُ بالكثافة ترتيب:** مقارنةُ مادّتين عند حالةٍ: أخفّ/سواء/أثقل حيث حضرت الكثافتان، ولا حكم حيث غابت إحداهما. -/
def qarin (m₁ m₂ : Madda) (h : Hala) : Option Ordering :=
  match m₁.kathafa h, m₂.kathafa h with
  | some a, some b => some (compare a b)
  | _, _ => none

/-- الترتيبُ كلّيّ: المقارنةُ إمّا لا حكم وإمّا واحدةٌ من الثلاث — لا رابع. -/
theorem tartib_kathafa (m₁ m₂ : Madda) (h : Hala) :
    qarin m₁ m₂ h = none ∨ qarin m₁ m₂ h = some .lt ∨ qarin m₁ m₂ h = some .eq ∨ qarin m₁ m₂ h = some .gt := by
  unfold qarin
  cases m₁.kathafa h with
  | none => simp
  | some a =>
    cases m₂.kathafa h with
    | none => simp
    | some b =>
      show some (compare a b) = none ∨ some (compare a b) = some .lt ∨ some (compare a b) = some .eq ∨
        some (compare a b) = some .gt
      generalize compare a b = c
      cases c <;> simp

/-- **ر1/ر6 — الوحدةُ والكثرة في المدلول:** معدودٌ (كمٌّ منفصل: الحجر، أحجار/حجارة) أو مقيس (كمٌّ متّصل: الماء، التراب). -/
inductive Wahda | madud | maqis
deriving DecidableEq, Repr

/-- **وجهُ الدالّ:** تاءُ الوحدة تُفرد واحدًا من الجنس — من المقيس قطعةً معدودة (الرمل/رملة: لسان س203789). -/
def ifrad (w : Wahda) (taWahda : Bool) : Wahda := if taWahda then .madud else w

theorem ifrad_madud (w : Wahda) : ifrad w true = .madud := rfl
theorem ifrad_bila_ta (w : Wahda) : ifrad w false = w := rfl

/-! ## الشاهد: المواد الستّ -/

/-- الماء: لسان س265253؛ ثلجُه المخصّص س32363 ولسان س56094. الكثافة غ/م³: الجامد 916,700 (0.9167 عند 0°م)، السائل 997,047 (عند 25°م)،
البخار لا حكم؛ الذوب 0، الغليان 100 (99.98). -/
def ma : Madda := { haqiqa := 11, kJamid := some 916700, kSail := some 997047, dhawb := some 0, ghalayan := some 100 }
/-- الحديد: لسان س56549. 7,874,000؛ 1538؛ 2861. -/
def hadid : Madda := { haqiqa := 12, kJamid := some 7874000, dhawb := some 1538, ghalayan := some 2861 }
/-- الذهب: لسان س13283. 19,283,000؛ 1064؛ 2970. -/
def dhahab : Madda := { haqiqa := 13, kJamid := some 19283000, dhawb := some 1064, ghalayan := some 2970 }
/-- الرصاص: لسان س127388. 11,348,000؛ 327؛ 1749. -/
def rasas : Madda := { haqiqa := 14, kJamid := some 11348000, dhawb := some 327, ghalayan := some 1749 }
/-- الزئبق: لسان س178415. السائل 13,546,000؛ −39؛ 357. -/
def zibaq : Madda := { haqiqa := 15, kSail := some 13546000, dhawb := some (-39), ghalayan := some 357 }
/-- الملح: لسان س49808. 2,170,000؛ 801؛ 1413 (وفي متن الصفحة 1465 — تعدّدٌ معلَن). -/
def milh : Madda := { haqiqa := 16, kJamid := some 2170000, dhawb := some 801, ghalayan := some 1413 }

def mawadd : List Madda := [ma, hadid, dhahab, rasas, zibaq, milh]

/-- **الحالةُ المرجعية من العتبات** (ف4 على الشاهد): الماءُ والزئبقُ سائلان عند 25°م والأربعةُ الباقية جامدة. -/
theorem shawahid_hala :
    halaMarjiiyya ma = some .sail ∧ halaMarjiiyya zibaq = some .sail ∧ halaMarjiiyya hadid = some .jamid ∧
    halaMarjiiyya dhahab = some .jamid ∧ halaMarjiiyya rasas = some .jamid ∧ halaMarjiiyya milh = some .jamid := by
  decide

/-- **ف3 على الشاهد:** الستُّ متّسقةُ العتبات (بالفاحص السليم `muttasiqB_salim`). -/
theorem shawahid_muttasiq : mawadd.all muttasiqB = true := by decide

theorem shawahid_muttasiq' : ∀ m ∈ mawadd, muttasiq m := by
  intro m hm
  exact muttasiqB_salim m (List.all_eq_true.1 shawahid_muttasiq m hm)

/-- فردٌ من الماء سائلًا بكتلة 100 غرام (100 مليون ميكروغرام). -/
def qatra : Fard := { madda := ma, hala := .sail, kutla := 100000000 }

/-- **الثلجُ ماءٌ** (المخصّص س32363): تجمّدُ القطرة يعطي فردًا جامدًا حقيقتُه حقيقةُ الماء وكتلتُه كتلتُها، وحجمُه أكبر (ر3: 100 سم³
سائلًا — 100,000,000 ÷ 997,047 — و109 جامدًا — ÷ 916,700 — قسمةً صحيحة). -/
theorem thalj_ma :
    ∃ th : Fard, qatra.tahawwal .jumud = some th ∧ th.madda.haqiqa = ma.haqiqa ∧ th.kutla = qatra.kutla ∧
      th.hala = .jamid ∧ th.hajm = some 109 ∧ qatra.hajm = some 100 := by
  refine ⟨{ qatra with hala := .jamid }, ?_, rfl, rfl, rfl, ?_, ?_⟩ <;> decide

/-- **الثلجُ يطفو على الماء** (ف6 على الشاهد): 916,700 < 997,047. -/
theorem thalj_yatfu : yatfu { madda := ma, hala := .jamid, hajm := 1 } ma = some true := by decide

/-- مدلولُ الماء على مدلول المالك: أفرادُه بحالاته، وقيمُ المعنى فيهم كثافاتُهم (مشكّكة) أو حقيقتُهم (متواطئة). -/
def madlulKathafa (m : Madda) : Madlul :=
  { haqiqa := m.haqiqa, khawass := [], alaqat := [], qabiliyyat := [],
    afrad := [m.kJamid, m.kSail].filterMap id }
def madlulHaqiqa (m : Madda) : Madlul :=
  { haqiqa := m.haqiqa, khawass := [], alaqat := [], qabiliyyat := [], afrad := [m.haqiqa, m.haqiqa] }

/-- **الكثافةُ مشكّكة** (على `tawatu` المالك س44، على الشاهد): معنى «الكثافة» يختلف بالدرجة بين أفراد الماء (جامده 916,700 وسائله
997,047). -/
theorem kathafa_mushakkika : tawatu (madlulKathafa ma) = .mushakkik := by decide

/-- **الحقيقةُ متواطئة — تعريفيّة:** أفرادٌ مثَّلهم البنّاءُ بحقيقةٍ واحدة متواطئون بالبناء (`tawatu` على قائمةٍ متساوية)؛ تمثيلٌ معلَن
لا شاهدَ فيه على الماء. -/
theorem haqiqa_mutawatia (m : Madda) : tawatu (madlulHaqiqa m) = .mutawati := by
  simp [tawatu, madlulHaqiqa]

end Jamad
end Madlul
