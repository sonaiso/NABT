/-
  Madlul/Tayin.lean — المعلوماتُ السابقة التأسيسية للتعيين والتمييز: قواعدُ الإنشاء (induction FOR) وقواعدُ التفكيك
  (induction ON) — بتأويل البنّاء لهذين اللفظين (إنشاء/تفكيك)، **أمضاه المالك مع القواعد ت1–ت6 وم1–م5 وتعييناتها في الجلسة
  2026-10-16** («إمضاء تأويل FOR/ON والقواعد (ت1–ت6، م1–م5) والتعيينات أعلاه») — على أركان العقل الأربعة عند النبهاني
  وما نصّ عليه ابن سيده من منهجه في المخصّص (س252، 261–267) وما حكاه عن القائلين بالمواضعة (س103–125). قرار المالك (2026-10-16): «نحلّل ونوجد induction FOR and induction ON للمعلومات
  السابقة التأسيسية للتعيين والتمييز … حتّى نوجد قاعدةً للتصنيف». التحليلُ ومواضعُ النصوص بأسطرها في `Madlul/التعيين_والتمييز.md`؛
  وهنا الصورةُ الرياضيّة وحدها. الاقتباساتُ أدناه بلفظ المصدر وتشكيلُها مضاف.

  **السند** (نصوصٌ بأسطرها في النصّ المحوَّل المسجَّل في `mudaat/sijill.json`: ج1 = a1.txt، ج3 = a2.txt؛ والمخصّص مودَعٌ مختوم):
  - ج1 س317: العقل «نقل الواقع بواسطة الحس للدماغ ومعلومات سابقة تفسر هذا الواقع» — أربعةٌ: دماغ، حواسّ، واقع، معلوماتٌ سابقة؛
    وما فقد واحدًا «بحث منطقي … تخيل وتوهم».
  - ج3 س725: «علمه حقائق الأشياء وخواصها، أي أعطاه المعلومات التي يستعملها للحكم على الأشياء، فإن الإحساس بالواقع لا يكفي وحده
    للحكم عليه وإدراك حقيقته، بل لا بد من معلومات سابقة يفسر بواسطتها الواقع» — فالمعلوماتُ السابقة = حقائقُ الأشياء وخواصُّها.
  - ج3 س747: اسمُ الجنس «اللفظ الموضوع للحقيقة الذهنية من حيث هي هي»، والمشتقُّ ما دلّ «على ذي صفة معينة».
  - ج3 س737: المطابقةُ على تمام المسمّى «كدلالة الإنسان على الحيوان الناطق»، والتضمّنُ على جزئه، والالتزامُ على لازمه
    (وقراءتُها جنسًا وفصلًا تعيينُ البنّاء — لفظُ «الفصل» ليس في ج3، و«الجنس» فيه س747 لكنّ س737 لا يسمّيهما).
  - المخصّص س109–114 — **حكايةً عن القائلين بالمواضعة** (س103–104؛ وقولُه س125 «وجميع ما ذكرته من هذا الفصل إنما هو نقل عن هؤلاء
    قالوا»)، لا من منهجه: التسميةُ بالإشارة إلى الواقع «فكأنهم جاءوا إلى واحد من بني آدم فأومؤا إليه فقالوا إنسان … علم أن المراد
    به هذا النوع من الجنس المخلوق»، وتسميةُ الأجزاء «التي تتحلل جملته إليها وتتركب عنها»، واللفظُ «كالسمة المميزة للموسوم …
    وكالحد المميز لما تحته من المحدود».
  - المخصّص س252، 261–267: الفصلُ «الذي تتباين به الأنواع من تحت الجنس»؛ ومنهجُه: «تقديم الأعم فالأعم على الأخص فالأخص والإتيان
    بالكليات قبل الجزئيات والابتداء بالجواهر والتقفية بالأعراض … وتقديمنا كم على كيف وشدة المحافظة على التقييد والتحليل»؛
    ومثالُه خلقُ الإنسان: «فبدأت بتنقله وتكونه شيئا فشيئا ثم أردفت بكلية جوهره ثم بطوائفه … ثم ما يلحقه من العظم والصغر ثم
    الكيفيات كالألوان إلى ما يتبعها من الأعراض والخصال».

  **الصورة.** الخاصّةُ قيمةٌ ثلاثيّة (`Qima`: نعم/لا/لا حكم — على عبارة م13 «لا يُستنتج الامتناع من غياب الشاهد»؛ ومخرجُ التصنيف
  قسمٌ أو «لا حكم» ولا «ممتنع» فيه). الخواصُّ التأسيسية بقول المالك في الجلسة 2026-10-16، **وأُودعت بإذنه في الجلسة نفسها جدولًا
  مختومًا** («جدول الأجناس — القطعة الأولى»، `ajnas.tsv` في `MUDAA_DIR`، بصمته `f567d1ab…` في `mudaat/sijill.json`، نوعه «معلومات
  سابقة») — وجدولُ `fusul` و`ramzQism` هنا **مطابَقان** له بـ `tahaqquq/test_ajnas.py` (الخواصّ الخمس والحقائق وقابليّات الحركة): التغذّي
  والنموُّ («ويكبر» في قوله مدموجٌ فيه: تعيين) والموت، والانتقالُ الذاتيّ («الانتقالُ خاصّية» — والتحرّكُ والفعلُ الذاتيّان مدموجان فيه: تعيينُ البنّاء)، والعقلُ (العمليةُ العقلية؛
  وقراءةُ «الرجع الغريزيّ» عقلًا «لا»: تعيينُ البنّاء). **الحياةُ** `hayat` = التغذّي والنموُّ والموت: استنباطُ البنّاء من وصف المالك
  للنبات («ينمو ويكبر ويموت») والحيوان («يحيا ويتغذّى وينمو ويكبر ويموت»)؛ والجماديةُ `jamadiyya` بلفظه (لا يتغذّى ولا ينمو ولا
  يتحرّك ذاتيًّا — بلا «الموت»). **induction FOR** = المنشئات: الأقسامُ الأربعة `Qism` وفصولُها `fusul`، وقاعدةُ التصنيف `sannif` على
  تعيين البنّاء لترتيب ابن سيده الأعمَّ فالأخصّ (الحياةُ جوهرًا، ثمّ الانتقالُ، ثمّ العقل) — والعقلُ فصلٌ تحت الحيوان لا يُسأل عنه
  في الجماد والنبات (المالك: «هل يفعل فقط كرجع غريزيّ أو يعقل» — السؤالُ فيما يفعل؛ تعيينُ البنّاء)، فقيمتُه فيهما لا تغيّر
  التصنيف. **induction ON** = التفكيك: `sannif_iff` (كلُّ قسمٍ بشروطه `shurut` إذا وفقط إذا — وما لم يستوفِ شروطَ قسمٍ «لا حكم»، ولا
  قسمٌ خامس)، `sannif_fusul` (القسمُ يعيّن فصولَه)، `fusul_sannif` (الفصولُ
  تعيّن القسمَ — على الشاهد)، `fasl_wahid` (الأخوان يفترقان بواحدٍ من الثلاثيّ المشتقّ حياة/انتقال/عقل — على الشاهد)، `aql_la_yumayyiz`
  (الأعمُّ لا يميّزه الأخصّ). والقابليّةُ تتبع الخاصّة (المالك: «الحركةُ قابليّة والانتقالُ خاصّية»؛ وقابليّاتُ الحركة: السير والركض
  والجري والزحف والقفز): `mutasiq`، `qabiliyya_tabi_khassa`. ورتابةُ التحسين: تعيينُ قيمةٍ كانت «لا حكم» لا يغيّر تصنيفًا قائمًا
  (`tahsin_la_yughayyir` — خاصّةٌ للنموذج لا نصُّ م13)، وغيابُ قيمةٍ مطلوبة «لا حكم» (`ghiyab_la_hukm`). والربطُ بمدلول المالك
  `Awwalan.Madlul`: `ilaMadlul` بترميزٍ معلَن (الحقائق 1–4، الخواصّ 1–5، قابليّاتُ الحركة 11–15) — تعريفٌ بلا مبرهنةٍ سوى شاهد
  الترميز في `shawahid`.

  الوسم: مبرهن (لكلّ خواصّ): `sannif_iff`، `sannif_fusul` (مقارنةً بجدول `fusul` على الخواصّ الخمس دون `qab`)، `aql_la_yumayyiz`،
  `ghiyab_la_hukm`، `shawahid_khuruj`، `hayat_tahsin`، `tahsin_la_yughayyir`، `qabiliyya_tabi_khassa`؛ وبالحالات على القيم: `wa_naam`،
  `wa_la`، `hayat_naam`، `hayat_la`؛ ومبرهن على الشاهد (decide على جدول `fusul` المطابَق للمودَع المختوم `f567d1ab…` بـ
  `test_ajnas.py`): `fusul_sannif`، `fasl_wahid`، `shawahid`؛ وتعريفيّة: `sannif_ghayr_jamad`، `jamadiyya_hayat`، `yuhassinQ_naam`،
  `yuhassinQ_la`.
-/
import SLGE.MadlulAwwalan

set_option autoImplicit false

namespace Madlul
namespace Tayin
open SLGE.Awwalan

/-- قيمةُ الخاصّة ثلاثيًّا (على عبارة م13: لا يُستنتج الامتناع من غياب الشاهد): نعم، لا، لا حكم. -/
inductive Qima | naam | la | laHukm
deriving DecidableEq, Repr

/-- العطفُ الثلاثيّ: «لا» تغلب، ثمّ «لا حكم»، ثمّ «نعم». -/
def wa : Qima → Qima → Qima
  | .la, _ => .la
  | _, .la => .la
  | .laHukm, _ => .laHukm
  | _, .laHukm => .laHukm
  | .naam, .naam => .naam

theorem wa_naam (a b : Qima) : wa a b = .naam ↔ a = .naam ∧ b = .naam := by cases a <;> cases b <;> simp [wa]
theorem wa_la (a b : Qima) : wa a b = .la ↔ a = .la ∨ b = .la := by cases a <;> cases b <;> simp [wa]

/-- قابليّاتُ الحركة (المالك): السير، الركض، الجري، الزحف، القفز. -/
inductive QabHaraka | sayr | rakd | jary | zahf | qafz
deriving DecidableEq, Repr

/-- الخواصُّ التأسيسية (بقول المالك 2026-10-16، مودَعةً بإذنه: «جدول الأجناس — القطعة الأولى» `f567d1ab…`): التغذّي، النموّ، الموت،
الانتقالُ الذاتيّ، العقل؛ وقابليّاتُ الحركة المثبتة للجنس (`qab`). -/
structure Khawass where
  taghadhdhi : Qima := .laHukm
  numuw : Qima := .laHukm
  mawt : Qima := .laHukm
  intiqal : Qima := .laHukm
  aql : Qima := .laHukm
  qab : List QabHaraka := []
deriving DecidableEq, Repr

/-- **الحياة** (استنباطُ البنّاء من وصف المالك للنبات والحيوان): يتغذّى وينمو ويموت. -/
def hayat (k : Khawass) : Qima := wa k.taghadhdhi (wa k.numuw k.mawt)

theorem hayat_naam (k : Khawass) : hayat k = .naam ↔ k.taghadhdhi = .naam ∧ k.numuw = .naam ∧ k.mawt = .naam := by
  unfold hayat; rw [wa_naam, wa_naam]
theorem hayat_la (k : Khawass) : hayat k = .la ↔ k.taghadhdhi = .la ∨ k.numuw = .la ∨ k.mawt = .la := by
  unfold hayat; rw [wa_la, wa_la]

/-! ## induction FOR: المنشئات -/

/-- الأقسامُ التأسيسية الأربعة. -/
inductive Qism | jamad | nabat | hayawan | insan
deriving DecidableEq, Repr

/-- الجمادية (بلفظ المالك): لا يتغذّى ولا ينمو ولا يتحرّك ذاتيًّا — الثلاثُ «لا»؛ ولا شرطَ في الموت. -/
def jamadiyya (k : Khawass) : Prop := k.taghadhdhi = .la ∧ k.numuw = .la ∧ k.intiqal = .la

instance (k : Khawass) : Decidable (jamadiyya k) := by unfold jamadiyya; infer_instance

/-- **قاعدةُ التصنيف** على تعيين البنّاء لترتيب ابن سيده (الأعمّ فالأخصّ: الحياةُ جوهرًا، ثمّ الانتقالُ، ثمّ العقل). الجمادُ ما انتفت
عنه الثلاث؛ والحيُّ الذي لا ينتقل ذاتيًّا نبات؛ والحيُّ المنتقلُ ذاتيًّا بالرجع الغريزيّ (العقل «لا») حيوان، وبالعملية العقلية إنسان.
**العقلُ فصلٌ تحت الحيوان لا يُسأل عنه في الجماد والنبات** (المالك: «هل يفعل فقط كرجع غريزي أو يعقل» — السؤالُ فيما يفعل؛ وهذا
تعيينُ البنّاء). وما سواه (ما بعضُ حياته «لا» وبعضُها «نعم»، أو غيرُ الحيّ المنتقل، أو ما فيه «لا حكم» مطلوب) لا حكم. -/
def sannif (k : Khawass) : Option Qism :=
  if jamadiyya k then some .jamad
  else match hayat k, k.intiqal, k.aql with
  | .naam, .la, _ => some .nabat
  | .naam, .naam, .la => some .hayawan
  | .naam, .naam, .naam => some .insan
  | _, _, _ => none

/-- في غير الجمادية، التصنيفُ على الحياة والانتقال والعقل وحدها. -/
theorem sannif_ghayr_jamad (k : Khawass) (h : ¬ jamadiyya k) :
    sannif k = match hayat k, k.intiqal, k.aql with
      | .naam, .la, _ => some .nabat
      | .naam, .naam, .la => some .hayawan
      | .naam, .naam, .naam => some .insan
      | _, _, _ => none := by
  unfold sannif; simp only [h, ite_false]

theorem jamadiyya_hayat (k : Khawass) (h : jamadiyya k) : hayat k = .la :=
  (hayat_la k).2 (Or.inl h.1)

/-- **فصولُ الأقسام** (خواصُّ كلّ قسمٍ كما يُنشأ — صفوفُ المودَع `ajnas.tsv` الأربعة، مطابَقةً بـ `test_ajnas.py`): الجمادُ لا يتغذّى
ولا ينمو ولا ينتقل ذاتيًّا (وموتُه لا حكم)؛ والنباتُ حيٌّ
ثابت؛ والحيوانُ حيٌّ منتقلٌ ذاتيًّا بلا عقل وله قابليّاتُ الحركة؛ والإنسانُ حيٌّ منتقلٌ ذاتيًّا عاقلٌ وله قابليّاتُ الحركة. العقلُ في
الجماد والنبات «لا حكم» (لا يُسأل عنه فيهما). -/
def fusul : Qism → Khawass
  | .jamad => { taghadhdhi := .la, numuw := .la, intiqal := .la }
  | .nabat => { taghadhdhi := .naam, numuw := .naam, mawt := .naam, intiqal := .la }
  | .hayawan => { taghadhdhi := .naam, numuw := .naam, mawt := .naam, intiqal := .naam, aql := .la,
                  qab := [.sayr, .rakd, .jary, .zahf, .qafz] }
  | .insan => { taghadhdhi := .naam, numuw := .naam, mawt := .naam, intiqal := .naam, aql := .naam,
                qab := [.sayr, .rakd, .jary, .zahf, .qafz] }

/-! ## induction ON: التفكيك -/

/-- شروطُ كلّ قسم (ما يُنشأ به): الجمادُ جمادية؛ والنباتُ حيٌّ لا ينتقل؛ والحيوانُ حيٌّ ينتقل وعقلُه «لا»؛ والإنسانُ حيٌّ ينتقل وعقلُه
«نعم» — والعقلُ لا يُسأل عنه في الأوّلَين. -/
def shurut : Qism → Khawass → Prop
  | .jamad, k => jamadiyya k
  | .nabat, k => hayat k = .naam ∧ k.intiqal = .la
  | .hayawan, k => hayat k = .naam ∧ k.intiqal = .naam ∧ k.aql = .la
  | .insan, k => hayat k = .naam ∧ k.intiqal = .naam ∧ k.aql = .naam

/-- **التفكيك التامّ:** يُصنَّف قسمًا إذا وفقط إذا استوفى شروطَه — فما لم يستوفِ شروطَ قسمٍ فلا حكم، ولا قسمَ خامس. -/
theorem sannif_iff (k : Khawass) (q : Qism) : sannif k = some q ↔ shurut q k := by
  by_cases hj : jamadiyya k
  · have hs : sannif k = some .jamad := by
      unfold sannif; split
      · rfl
      · exact absurd hj ‹_›
    rw [hs]
    cases q
    · simp [shurut, hj]
    · simp only [Option.some.injEq, reduceCtorEq, false_iff, shurut]
      intro c; have := (hayat_naam k).1 c.1; rw [hj.1] at this; cases this.1
    · simp only [Option.some.injEq, reduceCtorEq, false_iff, shurut]
      intro c; have := (hayat_naam k).1 c.1; rw [hj.1] at this; cases this.1
    · simp only [Option.some.injEq, reduceCtorEq, false_iff, shurut]
      intro c; have := (hayat_naam k).1 c.1; rw [hj.1] at this; cases this.1
  · rw [sannif_ghayr_jamad k hj]
    cases q <;> simp only [shurut]
    · constructor
      · intro h; exfalso
        cases hh : hayat k <;> cases hr : k.intiqal <;> cases ha : k.aql <;> rw [hh, hr, ha] at h <;> simp at h
      · intro c; exact absurd c hj
    · cases hh : hayat k <;> cases hr : k.intiqal <;> cases ha : k.aql <;> simp
    · cases hh : hayat k <;> cases hr : k.intiqal <;> cases ha : k.aql <;> simp
    · cases hh : hayat k <;> cases hr : k.intiqal <;> cases ha : k.aql <;> simp

/-- **الفصولُ تعيّن القسم** (على الشاهد: جدول `fusul` بقول المالك): من فصول كلّ قسمٍ يعود القسمُ نفسُه. -/
theorem fusul_sannif : ∀ q : Qism, sannif (fusul q) = some q := by intro q; cases q <;> decide

/-- **القسمُ يعيّن فصولَه** (لكلّ خواصّ، مقارنةً بجدول `fusul` الذي كتبه البنّاء، على الخواصّ الخمس دون `qab`): ما صُنّف قسمًا فحياتُه
وانتقالُه على فصول قسمه، وعقلُه كذلك إن كان ممّا يميّزه العقل (الحيوان والإنسان)، والجمادُ منتفٍ عنه التغذّي والنموُّ والانتقال. -/
theorem sannif_fusul (k : Khawass) (q : Qism) (h : sannif k = some q) :
    hayat k = hayat (fusul q) ∧ k.intiqal = (fusul q).intiqal ∧
    ((q = .hayawan ∨ q = .insan) → k.aql = (fusul q).aql) ∧
    (q = .jamad → k.taghadhdhi = .la ∧ k.numuw = .la ∧ k.intiqal = .la) := by
  have hs := (sannif_iff k q).1 h
  cases q <;> simp only [shurut] at hs
  · exact ⟨by rw [jamadiyya_hayat k hs]; rfl, hs.2.2, (fun c => by rcases c with c | c <;> cases c), (fun _ => hs)⟩
  · exact ⟨by rw [hs.1]; rfl, hs.2, (fun c => by rcases c with c | c <;> cases c), (fun c => by cases c)⟩
  · exact ⟨by rw [hs.1]; rfl, hs.2.1, (fun _ => hs.2.2), (fun c => by cases c)⟩
  · exact ⟨by rw [hs.1]; rfl, hs.2.1, (fun _ => hs.2.2), (fun c => by cases c)⟩

/-- **التمييزُ بفصلٍ واحد من الثلاثيّ المشتقّ (حياة/انتقال/عقل)** — على الشاهد: الجمادُ والنباتُ يفترقان بالحياة (وهي ثلاثُ خواصّ) ويتّفقان
في الانتقال؛ والنباتُ والحيوانُ يفترقان بالانتقال ويتّفقان في الحياة؛ والحيوانُ والإنسانُ يفترقان بالعقل ويتّفقان في الحياة والانتقال. -/
theorem fasl_wahid :
    (hayat (fusul .jamad) ≠ hayat (fusul .nabat) ∧ (fusul .jamad).intiqal = (fusul .nabat).intiqal) ∧
    (hayat (fusul .nabat) = hayat (fusul .hayawan) ∧ (fusul .nabat).intiqal ≠ (fusul .hayawan).intiqal) ∧
    (hayat (fusul .hayawan) = hayat (fusul .insan) ∧ (fusul .hayawan).intiqal = (fusul .insan).intiqal ∧
      (fusul .hayawan).aql ≠ (fusul .insan).aql) := by decide

/-- **الأعمُّ قبل الأخصّ:** العقلُ لا يُسأل عنه في الجماد والنبات — قيمتُه فيهما لا تغيّر التصنيف (نعم، لا، لا حكم سواء). -/
theorem aql_la_yumayyiz (k : Khawass) (q : Qism) (hq : q = .jamad ∨ q = .nabat) (h : sannif k = some q) (a : Qima) :
    sannif { k with aql := a } = some q := by
  have hs := (sannif_iff k q).1 h
  apply (sannif_iff _ q).2
  rcases hq with rfl | rfl <;> simp only [shurut] at hs ⊢
  · exact ⟨hs.1, hs.2.1, hs.2.2⟩
  · exact ⟨hs.1, hs.2⟩

/-! ## لا حكم لا امتناع -/

/-- **غيابُ قيمةٍ مطلوبة «لا حكم»:** إن كانت الحياةُ أو الانتقالُ بلا حكم فلا تصنيف (م13: لا يُستنتج من غياب الشاهد). -/
theorem ghiyab_la_hukm (k : Khawass) (h : hayat k = .laHukm ∨ k.intiqal = .laHukm) : sannif k = none := by
  rcases hs : sannif k with _ | q
  · rfl
  · exfalso
    have := (sannif_iff k q).1 hs
    rcases h with h | h <;> cases q <;> simp only [shurut] at this
    · rw [jamadiyya_hayat k this] at h; cases h
    · rw [this.1] at h; cases h
    · rw [this.1] at h; cases h
    · rw [this.1] at h; cases h
    · rw [this.2.2] at h; cases h
    · rw [this.2] at h; cases h
    · rw [this.2.1] at h; cases h
    · rw [this.2.1] at h; cases h

/-- **شواهدُ الخروج عن الأقسام** (ثلاثُ حالاتٍ عامّة، والتامُّ في `sannif_iff`): غيرُ الحيّ المنتقلُ ذاتيًّا، وما بعضُ حياته «لا» وبعضُها
«نعم» (يتغذّى ولا ينمو)، والحيُّ المنتقلُ الذي لا حكمَ لعقله — كلُّها لا حكم. -/
theorem shawahid_khuruj (k : Khawass) :
    (hayat k = .la → k.intiqal = .naam → sannif k = none) ∧
    (k.taghadhdhi = .naam → k.numuw = .la → sannif k = none) ∧
    (hayat k = .naam → k.intiqal = .naam → k.aql = .laHukm → sannif k = none) := by
  refine ⟨fun hh hr => ?_, fun ht hn => ?_, fun hh hr ha => ?_⟩
  · rcases hs : sannif k with _ | q
    · rfl
    · exfalso
      have := (sannif_iff k q).1 hs
      cases q <;> simp only [shurut] at this
      · rw [this.2.2] at hr; cases hr
      · rw [hh] at this; cases this.1
      · rw [hh] at this; cases this.1
      · rw [hh] at this; cases this.1
  · rcases hs : sannif k with _ | q
    · rfl
    · exfalso
      have := (sannif_iff k q).1 hs
      cases q <;> simp only [shurut] at this
      · rw [this.1] at ht; cases ht
      · have := (hayat_naam k).1 this.1; rw [hn] at this; cases this.2.1
      · have := (hayat_naam k).1 this.1; rw [hn] at this; cases this.2.1
      · have := (hayat_naam k).1 this.1; rw [hn] at this; cases this.2.1
  · rcases hs : sannif k with _ | q
    · rfl
    · exfalso
      have := (sannif_iff k q).1 hs
      cases q <;> simp only [shurut] at this
      · rw [this.2.2] at hr; cases hr
      · rw [this.2] at hr; cases hr
      · rw [this.2.2] at ha; cases ha
      · rw [this.2.2] at ha; cases ha

/-- تحسينُ القيمة: ما كان «لا حكم» يُعيَّن، وما كان معيَّنًا يبقى (على الخواصّ الخمس). -/
def yuhassinQ : Qima → Qima → Prop
  | .laHukm, _ => True
  | a, b => a = b

def yuhassin (k k' : Khawass) : Prop :=
  yuhassinQ k.taghadhdhi k'.taghadhdhi ∧ yuhassinQ k.numuw k'.numuw ∧ yuhassinQ k.mawt k'.mawt ∧
  yuhassinQ k.intiqal k'.intiqal ∧ yuhassinQ k.aql k'.aql

theorem yuhassinQ_naam {a b : Qima} (h : yuhassinQ a b) (ha : a = .naam) : b = .naam := by
  subst ha; exact h.symm
theorem yuhassinQ_la {a b : Qima} (h : yuhassinQ a b) (ha : a = .la) : b = .la := by
  subst ha; exact h.symm

theorem hayat_tahsin (k k' : Khawass) (h : yuhassin k k') (hh : hayat k ≠ .laHukm) : hayat k' = hayat k := by
  obtain ⟨h1, h2, h3, -, -⟩ := h
  cases hk : hayat k with
  | naam =>
    obtain ⟨a, b, c⟩ := (hayat_naam k).1 hk
    exact (hayat_naam k').2 ⟨yuhassinQ_naam h1 a, yuhassinQ_naam h2 b, yuhassinQ_naam h3 c⟩
  | la =>
    rcases (hayat_la k).1 hk with a | b | c
    · exact (hayat_la k').2 (Or.inl (yuhassinQ_la h1 a))
    · exact (hayat_la k').2 (Or.inr (Or.inl (yuhassinQ_la h2 b)))
    · exact (hayat_la k').2 (Or.inr (Or.inr (yuhassinQ_la h3 c)))
  | laHukm => exact absurd hk hh

/-- **رتابةُ التحسين** (خاصّةٌ للنموذج): ما صُنّف قسمًا بقي قسمَه بعد تعيين ما كان «لا حكم» على الخواصّ الخمس. -/
theorem tahsin_la_yughayyir (k k' : Khawass) (q : Qism) (h : sannif k = some q) (hy : yuhassin k k') :
    sannif k' = some q := by
  have hs := (sannif_iff k q).1 h
  apply (sannif_iff k' q).2
  have hy' := hy
  obtain ⟨h1, h2, -, h4, h5⟩ := hy
  cases q <;> simp only [shurut] at hs ⊢
  · exact ⟨yuhassinQ_la h1 hs.1, yuhassinQ_la h2 hs.2.1, yuhassinQ_la h4 hs.2.2⟩
  · exact ⟨by rw [hayat_tahsin k k' hy' (by rw [hs.1]; decide)]; exact hs.1, yuhassinQ_la h4 hs.2⟩
  · exact ⟨by rw [hayat_tahsin k k' hy' (by rw [hs.1]; decide)]; exact hs.1,
      yuhassinQ_naam h4 hs.2.1, yuhassinQ_la h5 hs.2.2⟩
  · exact ⟨by rw [hayat_tahsin k k' hy' (by rw [hs.1]; decide)]; exact hs.1,
      yuhassinQ_naam h4 hs.2.1, yuhassinQ_naam h5 hs.2.2⟩

/-! ## القابليّة تتبع الخاصّة -/

/-- **الاتّساق** (المالك: «الحركةُ قابليّة والانتقالُ خاصّية»): لا تثبت قابليّةُ حركةٍ لجنسٍ إلّا وخاصّةُ الانتقال فيه «نعم». -/
def mutasiq (k : Khawass) : Prop := k.qab ≠ [] → k.intiqal = .naam

/-- **القابليّةُ تتبع الخاصّة:** في الخواصّ المتّسقة، ما صُنّف جمادًا أو نباتًا فلا قابليّةَ حركةٍ له؛ وما كان له قابليّةُ حركةٍ فمنتقلٌ ذاتيًّا
فهو حيوانٌ أو إنسان إن صُنّف. -/
theorem qabiliyya_tabi_khassa (k : Khawass) (hm : mutasiq k) (q : Qism) (h : sannif k = some q) :
    ((q = .jamad ∨ q = .nabat) → k.qab = []) ∧ (k.qab ≠ [] → (q = .hayawan ∨ q = .insan)) := by
  have hs := (sannif_iff k q).1 h
  have hla : (q = .jamad ∨ q = .nabat) → k.intiqal = .la := by
    intro hq; rcases hq with rfl | rfl <;> simp only [shurut] at hs
    · exact hs.2.2
    · exact hs.2
  constructor
  · intro hq
    cases hc : k.qab with
    | nil => rfl
    | cons x xs =>
      have hi := hm (by rw [hc]; exact List.cons_ne_nil x xs)
      rw [hla hq] at hi; cases hi
  · intro c
    have hi := hm c
    cases q <;> simp only [shurut] at hs
    · rw [hs.2.2] at hi; cases hi
    · rw [hs.2] at hi; cases hi
    · exact Or.inl rfl
    · exact Or.inr rfl

/-! ## الربط بمدلول المالك (تعريفٌ بترميزٍ معلَن، بلا مبرهنة) -/

/-- ترميزٌ معلَن: الحقائقُ جماد 1 نبات 2 حيوان 3 إنسان 4 (عمودُ `haqiqa` في المودَع، مطابَق)؛ الخواصُّ تغذٍّ 1 نموّ 2 موت 3 انتقال 4
عقل 5؛ قابليّاتُ الحركة 11–15 (ترميزُ البنّاء). -/
def ramzQism : Qism → Nat | .jamad => 1 | .nabat => 2 | .hayawan => 3 | .insan => 4
def ramzQab : QabHaraka → Nat | .sayr => 11 | .rakd => 12 | .jary => 13 | .zahf => 14 | .qafz => 15

def khawassNaam (k : Khawass) : List Nat :=
  (if k.taghadhdhi == .naam then [1] else []) ++ (if k.numuw == .naam then [2] else []) ++
  (if k.mawt == .naam then [3] else []) ++ (if k.intiqal == .naam then [4] else []) ++ (if k.aql == .naam then [5] else [])

/-- مدلولُ القسم عند المالك: حقيقتُه رمزُه، وخواصُّه ما ثبت «نعم» من فصوله، وقابليّاتُه قابليّاتُ الحركة المثبتة. -/
def ilaMadlul (q : Qism) : Madlul :=
  { haqiqa := ramzQism q, khawass := khawassNaam (fusul q), alaqat := [], qabiliyyat := (fusul q).qab.map ramzQab,
    afrad := [] }

/-- **شواهدُ المالك** (على الشاهد): خواصُّ الجماد والنبات والحيوان والإنسان بقوله تُصنَّف أقسامَها، والجمادُ بموتٍ «لا حكم» جماد؛ وغيرُ
الحيّ المنتقل لا حكم؛ وما لم يُعيَّن انتقالُه، أو عقلُه وهو منتقل، لا حكم؛ وما يتغذّى ولا ينمو لا حكم؛ والعقلُ لا يُسأل عنه في النبات
(بعقلٍ «نعم» نباتٌ بشروطه)؛ وترميزُ مدلول الإنسان خواصُّه الخمس وقابليّاتُه الخمس. -/
theorem shawahid :
    sannif { taghadhdhi := .la, numuw := .la, intiqal := .la } = some .jamad ∧
    sannif { taghadhdhi := .la, numuw := .la, mawt := .la, intiqal := .la } = some .jamad ∧
    sannif { taghadhdhi := .naam, numuw := .naam, mawt := .naam, intiqal := .la } = some .nabat ∧
    sannif { taghadhdhi := .naam, numuw := .naam, mawt := .naam, intiqal := .naam, aql := .la } = some .hayawan ∧
    sannif { taghadhdhi := .naam, numuw := .naam, mawt := .naam, intiqal := .naam, aql := .naam } = some .insan ∧
    sannif { taghadhdhi := .la, numuw := .la, mawt := .la, intiqal := .naam } = none ∧
    sannif { taghadhdhi := .naam, numuw := .naam, mawt := .naam } = none ∧
    sannif { taghadhdhi := .naam, numuw := .naam, mawt := .naam, intiqal := .naam } = none ∧
    sannif { taghadhdhi := .naam, numuw := .la, mawt := .naam, intiqal := .la } = none ∧
    sannif { taghadhdhi := .naam, numuw := .naam, mawt := .naam, intiqal := .la, aql := .naam } = some .nabat ∧
    (ilaMadlul .insan).khawass = [1, 2, 3, 4, 5] ∧ (ilaMadlul .insan).qabiliyyat = [11, 12, 13, 14, 15] ∧
    (ilaMadlul .nabat).qabiliyyat = [] ∧
    (ilaMadlul .jamad).haqiqa = 1 ∧ (ilaMadlul .nabat).haqiqa = 2 ∧ (ilaMadlul .hayawan).haqiqa = 3 ∧
    (ilaMadlul .insan).haqiqa = 4 := by decide

end Tayin
end Madlul
