/-
  Jisr/Ikhbar.lean — أساليب الإخبار: جردٌ مستنفَد على المودَعات، وما غطّته أطر المالك منها، بحدّ الأدنى المكتمل.

  الجرد: ستّةٌ وعشرون من أبواب «متن قطر الندى» (مودَع مختوم) بأسطر أبوابها أو فصولها: المبتدأ والخبر (L152)، النواسخ الثلاثة
  (L169–218)، الفاعل (L219)، النائب عن الفاعل (L240)، الاشتغال (L246)، التنازع (L258)، المفاعيل الخمسة (L267–306: به
  L268، المطلق L289، له L293، فيه L297، معه L301)، الحال (L307)، التمييز (L313)، المستثنى (L326)، الخفض بالحرف (L337)
  وبالإضافة (L339)، ما يعمل عمل فعله سبعة (L347–373)، التوابع الخمسة (L374–413)، العدد (L414–418)، والمضارع بين الرفع
  والنصب والجزم (L96–121)، والشرط (L115–121؛ والمغني L8729: الشرطية من قبيل الفعلية)، والنفي غلافًا بالحرف غير العامل
  («ما رجلٌ في الدار» L153؛ أمّا ما الحجازية ولا ولات العاملاتُ عملَ ليس L181–186 فمن النواسخ)؛ وواحدٌ من جدول العوامل
  (مودَع): كاد وأخواتها (الصنف 6، «المقاربة/الشروع/الرجاء») ولا بابَ له في القطر. وما في القطر من الإنشاء — النداء
  (L268–287)، التعجّب (L432–439) — خارجَ الإخبار، ومثله الاستفهام والطلب والتمنّي والترجّي في جدول العوامل
  (`Jisr/Nisab.ikhbar_82`): المالك أطّر النداء والاستفهام (`TarkibExt`)، وترخيصُهما في الإنشاء قرارُ نطاقٍ لاحق عنده.
  والجرد حاصرٌ على تعريفه (`kull_hasir`)، لا دعوى استنفاد أبواب القطر.

  التغطية (معيارٌ واحد معلَن): الأسلوب مغطًّى إن كان له دورٌ أو أداةٌ في أطر المالك (`Tarkib`: الأدوار 0–8 والأدوات 0–5 لا
  غير — `adwar_tisa`؛ `TarkibExt`: الشرط؛ `Muwahhad`: الغلاف والاستثناء المفرَّغ؛ `Kull`: الاستثناء التامّ)، أو معادلةٌ عنده
  على أدوار الأطر (`SLGE.Awamil.eqs`: كاد على الدورين 0 و2). فعطفُ النسق معادلةُ تساوٍ على دورين (9، 10) ليسا في الأطر —
  غير مغطًّى؛ وما سوى ذلك — النائب عن الفاعل، الاشتغال، التنازع، المفاعيل الأربعة الأخرى، الحال، التمييز، الإضافة، ما
  يعمل عمل فعله، التوابع الخمسة، العدد — ليس دورًا ولا أداةً ولا معادلة: ينتظر (`ghayr_mughatta`). ثمّ بُنيت السبعةَ عشرَ في
  `Jisr/Mulhaqat.lean` ملحقاتٍ على إطار المالك الموحَّد بأدوارٍ جديدة (`Mulhaqat.taghtiya_kamila`: 27/27)؛ و`mughatta` هنا يبقى
  على معياره: ما غطّته أطرُ المالك نفسُها.

  الحدّ الأدنى المكتمل: أقلُّ الأطر موضعان (`adna_itar`: عشرةُ أطرٍ بموضعين — ستّةٌ اسميةٌ من مبتدأ وخبر ظاهرين أو مقدَّرٍ
  أحدُهما، وأربعةٌ فعليةٌ من فعلٍ وفاعل: ظاهرين، أو الفاعلُ مقدَّرٌ بإحالة 14 أو 15، أو الفعلُ مقدَّر)، وهو قولُ القطر «من اسمين
  أو فعل واسم» (L73–74)؛ ومبرهنةُ المالك `Bridge.sent_min` تنفي الجملةَ من كلمةٍ واحدة. وعواملُ الإخبار الـ82 في الجدول
  كلُّها في أصنافٍ لها أسلوبٌ من الجرد (`awamil_ikhbar`).
  والعموم والخصوص والمطلق والمقيّد والسبب والشرط والمانع (دلالات الخبر، ج3) عند المالك في `SLGE/Madlul.lean`:
  `takhsis_sub`، `amal_bil_muqayyad`، `amal_bil_mutlaq_la_yafi`، `haml_iff`، `shart_adam`، `shart_la_yujib`،
  `sabab_la_yujib`، `mani_yamna`، `wujud_tamm` — مدقَّقةٌ في Audit.lean.
-/
import SLGE.Kull
import SLGE.Awamil
import Jisr.Awamil
import Jisr.Nisab

namespace Jisr
namespace Ikhbar
open SLGE.Tarkib

/-- أساليب الإخبار: ستّة وعشرون من أبواب القطر وفصوله، وكاد وأخواتها من جدول العوامل (بأسطرها في الرأس). -/
inductive Uslub
  | ibtida | nawasikh | muqaraba | fail | naib | ishtighal | tanazu
  | mafulBihi | mafulMutlaq | mafulLahu | mafulFihi | mafulMaahu
  | hal | tamyiz | istithna | jarr | idafa | amal
  | nat | tawkid | atfBayan | atfNasaq | badal | adad
  | mudari | shart | nafy
deriving DecidableEq, Repr

def kull : List Uslub :=
  [.ibtida, .nawasikh, .muqaraba, .fail, .naib, .ishtighal, .tanazu, .mafulBihi, .mafulMutlaq, .mafulLahu, .mafulFihi,
   .mafulMaahu, .hal, .tamyiz, .istithna, .jarr, .idafa, .amal, .nat, .tawkid, .atfBayan, .atfNasaq, .badal, .adad,
   .mudari, .shart, .nafy]

/-- **الجرد حاصر:** كلّ أسلوب في القائمة، والقائمة بلا تكرار — سبعةٌ وعشرون. -/
theorem kull_hasir : (∀ u : Uslub, u ∈ kull) ∧ kull.Nodup ∧ kull.length = 27 := by
  refine ⟨fun u => ?_, by decide, rfl⟩
  cases u <;> simp [kull]

/-- سطر القطر لكلّ أسلوب: أوّلُ سطر بابه، أو فصله/موضعه داخل الباب؛ والمقاربة 0 (لا باب لها في القطر؛ سندها الجدول). -/
def satr : Uslub → Nat
  | .ibtida => 152 | .nawasikh => 169 | .muqaraba => 0 | .fail => 219 | .naib => 240 | .ishtighal => 246 | .tanazu => 258
  | .mafulBihi => 268 | .mafulMutlaq => 289 | .mafulLahu => 293 | .mafulFihi => 297 | .mafulMaahu => 301
  | .hal => 307 | .tamyiz => 313 | .istithna => 326 | .jarr => 337 | .idafa => 339 | .amal => 347
  | .nat => 374 | .tawkid => 374 | .atfBayan => 374 | .atfNasaq => 374 | .badal => 374 | .adad => 414
  | .mudari => 96 | .shart => 115 | .nafy => 153

/-- المغطّى بالمعيار المعلَن في الرأس: المبتدأ والخبر (الدوران 0، 1)، النواسخ (الأدوات 1–3)، كاد (`Awamil.eqs 6` على
الدورين 0، 2)، الفاعل (3)، المفعول به (4)، الجارّ والمجرور (5، 6)، المضارع مرفوعًا بالتجرّد (الأداة 0) ومنصوبًا ومجزومًا
(4، 5)، الشرط (`TarkibExt`)، الاستثناء (`Muwahhad.istithna_mufarragh`، `Kull.istithna_tamm`)، النفي غلافًا (`Muwahhad`). -/
def mughatta : Uslub → Bool
  | .ibtida | .nawasikh | .muqaraba | .fail | .mafulBihi | .jarr | .mudari | .shart | .istithna | .nafy => true
  | _ => false

/-- **القسمة:** عشرةٌ مغطّاة بأسمائها، وسبعةَ عشرَ تنتظر بأسمائها. -/
theorem istinfad :
    kull.filter mughatta =
      [.ibtida, .nawasikh, .muqaraba, .fail, .mafulBihi, .istithna, .jarr, .mudari, .shart, .nafy] ∧
    kull.filter (fun u => !mughatta u) =
      [.naib, .ishtighal, .tanazu, .mafulMutlaq, .mafulLahu, .mafulFihi, .mafulMaahu, .hal, .tamyiz,
       .idafa, .amal, .nat, .tawkid, .atfBayan, .atfNasaq, .badal, .adad] := by decide

/-- **أدوار أطر المالك تسعة لا غير** (0–8)، **وأدواتها ستّ** (0–5): فما ليس منها ليس في الأطر. -/
theorem adwar_tisa :
    (framesL.flatMap fun f => f.2.2.map (·.1)).all (· ≤ 8) = true ∧
    (List.range 9).all (fun r => framesL.any fun f => f.2.2.any (·.1 == r)) = true ∧
    (framesL.map (·.2.1)).all (· ≤ 5) = true ∧
    (List.range 6).all (fun a => framesL.any fun f => f.2.1 == a) = true := by decide +kernel

/-- العدّ: عشرةٌ وسبعةَ عشرَ من سبعةٍ وعشرين؛ والمنتظرُ ليس له دورٌ في الأدوار التسعة (`adwar_tisa`) ولا أداةٌ في الستّ ولا
معادلةٌ على أدوارها (عطف النسق على 9 و10 خارجها: `SLGE.Awamil.links 8 = [(9, 10)]`). -/
theorem ghayr_mughatta : (kull.filter mughatta).length = 10 ∧ (kull.filter fun u => !mughatta u).length = 17 ∧
    SLGE.Awamil.links 8 = [(9, 10)] ∧ SLGE.Awamil.eqs 6 = [[(0, 1), (2, 1)]] := by decide

/-- **الحدّ الأدنى المكتمل:** أقلُّ الأطر موضعان، وهي عشرة: ستّةٌ اسمية (مبتدأ وخبر، ظاهرين أو مقدَّرًا أحدُهما) وأربعةٌ
فعلية (فعلٌ وفاعل: ظاهرين، أو الفاعلُ مقدَّرٌ بإحالة 14 أو 15، أو الفعلُ مقدَّر)؛ ولا إطارَ بموضعٍ واحد. -/
theorem adna_itar :
    (framesL.map (·.2.2.length)).all (· ≥ 2) = true ∧
    (framesL.filter fun f => f.2.2.length == 2).length = 10 ∧
    ((framesL.filter fun f => f.2.2.length == 2).filter fun f => f.1 == 0).length = 6 ∧
    ((framesL.filter fun f => f.2.2.length == 2).filter fun f => f.1 == 1).length = 4 ∧
    (framesL.filter fun f => f.2.2.length == 2).all (fun f =>
      (f.1 == 0 && f.2.2.map (·.1) == [0, 1] || f.2.2.map (·.1) == [1, 0]) ||
      (f.1 == 1 && f.2.2.map (·.1) == [2, 3])) = true := by decide +kernel

/-- أسلوب الإخبار لكلّ صنفٍ من أصناف جدول العوامل (تعيين معلَن): النواسخ 1–3 ← النواسخ؛ 4 و5 ← المضارع؛ 6 ← المقاربة؛
7 ← الجرّ؛ 8 ← عطف النسق؛ 9 ← الجرّ (أو المضارع)؛ 10 و11 ← الشرط؛ 12 و13 إنشاء (لا أسلوب إخبار). -/
def uslubSinf : Nat → Option Uslub
  | 1 | 2 | 3 => some .nawasikh
  | 4 | 5 => some .mudari
  | 6 => some .muqaraba
  | 7 => some .jarr
  | 8 => some .atfNasaq
  | 9 => some .jarr
  | 10 | 11 => some .shart
  | _ => none

/-- **عوامل الإخبار الـ82 كلُّها لها أسلوبٌ من الجرد**، والإنشائية الـ18 في أصنافٍ أربعة: إنّ (ليت ولعلّ)، الجوازم (لا الناهية
ولام الأمر)، الاستفهام، النداء. -/
theorem awamil_ikhbar :
    ((Jisr.Awamil.uslub.zip Jisr.Awamil.table).filter (fun p => p.1.2 == "الخبر")).all
      (fun p => (uslubSinf p.2.2.1).isSome) = true ∧
    ((Jisr.Awamil.uslub.zip Jisr.Awamil.table).filter (fun p => p.1.2 == "الخبر")).length = 82 ∧
    (((Jisr.Awamil.uslub.zip Jisr.Awamil.table).filter (fun p => p.1.2 != "الخبر")).map (·.2.2.1)).eraseDups = [2, 5, 12, 13] := by
  decide

end Ikhbar
end Jisr
