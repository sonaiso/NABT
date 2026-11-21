/-
  Madlul/Shabaka.lean — شبكةُ العلاقات بين الأجناس والأفعال والصفات، وأساليبُ الإخبار تحويلاتٍ على الأدوار، وسلسلةُ القرار
  المرخَّصة جبريًّا (على `Aql/Qaida.lean`) في تسلسلٍ هرميٍّ متدرّج.

  قرارُ المالك (2026-10-16، 14:02 و14:34): «العلاقات بين الصفات والخواص والأجناس عمل lean وتسلسل هرمي تدريجي مرخص جبريا … الحيوان يشرب
  الماء والماء يحقق الارواء الماء سائل فاذا السائل شراب والشراب يشرب شبكة علاقات راجع النبهاني لبناء سلسلة القرار لاساليب الإخبار عن
  الفعالية والفاعلية والمفعولية والانفعالية والتفاعلية والاستفعالية واللازم والمتعدي وتحول المتعدي الى لازم وتحول اللازم لمتعدي
  بالمشاركة والمطاوعة والطلب وكذلك السببية والمسببية»؛ وإمضاؤه (14:39) لقراءة البنّاء: «موافق».

  **السند** (بأسطره؛ الاقتباساتُ بلفظ المصدر وتشكيلُها مضاف):
  - ج3 (a2.txt، مرشّح) س721: «وضعت ليفيد الوضع النسب الإسنادية، أو التقييدية، أو الإضافية، بين المفردات، بضم بعضها إلى بعض،
    كالفاعلية، والمفعولية، وغيرهما» — الفاعليةُ والمفعوليةُ نِسَبٌ (وعلى `SLGE.Simat.semOf`: 3 فاعلية، 4 مفعولية؛ `Jisr/Nisab.lean`).
  - ج3 س796: «النوع الأول: السببية - وهي إطلاق اسم السبب على المسبب. والعلاقة السببية أربعة أقسام: أحدها: السببية القابلية …
    مثل قولهم سال الوادي، أي الماء الذي في الوادي … والثالث: السببية الفاعلية مثل نـزل السحاب أي المطر، بإطلاق اسم فاعل الشيء عليه»؛
    س798: «النوع الثاني: المسببية - وهي إطلاق اسم المسبب على السبب» — السببيةُ والمسببيةُ علاقتا تسميةٍ (مجازٌ برخصة فوق هذه الطبقة).
  - الكتاب (مختوم) س324: «باب الفاعل الذي لم يتعده فعله إلى مفعول»؛ س332–334: «باب الفاعل الذي يتعداه فعله إلى مفعول … وانتصب زيد
    لأنه مفعول تعدى إليه فعل الفاعل»؛ س16543–16546: «باب ما طاوع الذي فعله على فعل وهو يكون على انفعل وافتعل … كسرته فانكسر …
    ونظير فعلته فانفعل أفعلته ففعل نحو أدخلته فدخل» — لفظُه «نظير»؛ وقراءةُ البنّاء لهذا النظير: المطاوعةُ عكسُ التعدية على
    اللازم المجرّد (`tawi_addi`، على تعريفَي `addi`/`tawi` اللذين كتبهما البنّاء).
  - الألفية (مختوم) س334 (تاء المطاوعة)، س1193: «ونحو الاستفعال والمطاوعه».
  - لسان العرب (مختوم): س16528: «الشرب: مصدر شربت أشرب شربا وشربا. ابن سيده: شرب الماء وغيره شربا» (شربٌ متعدٍّ ومفعولُه الماء)؛
    س16550: «والشراب: ما شرب من أي نوع كان» (التسميةُ بالمفعولية)؛ س16599: «والشراب: اسم لما يشرب. وكل شيء لا يمضغ، فإنه يقال
    فيه: يشرب» (قانونٌ معجميّ: ما لا يُمضغ يُشرب)؛ س205864: «سال الماء والشيء سيلا وسيلانا: جرى، وأساله غيره» (لازمٌ وتعديتُه)؛
    س100934: «كسر الشيء يكسره كسرا فانكسر وتكسر» (المطاوعة)؛ س18424: «وضاربه أي جالده. وتضاربا» (المشاركة)؛ س281482–281484:
    «الاستسقاء … استفعال من طلب السقيا … واستسقيت فلانا إذا طلبت منه أن يسقيك» (الطلب)؛ س231914: «فأمت وصأبت إذا رويت من الماء»
    وس251637: «يروي، فهو ريان … فالريان فعلان من الري» (الريُّ من الماء: سببٌ ومسبَّب — و«الإرواء» في قول المالك سُمّي هنا «الريّ»:
    تعيينُ البنّاء).

  **الصورة.** (١) **الإخبار** `Ikhbar A`: فعلٌ `Fil` (بلزومه/تعدّيه `Luzum`) وأسلوبٌ `Uslub` وأدوارٌ (فاعل، مفعول، سبب/طالب) مشغولةٌ
  بأعيانٍ من `A` أو فارغة (لا حكم). **الأساليبُ تحويلاتٌ على الأدوار**: `jahhil` (المجهول: يحذف الفاعلَ ويبقي المفعولَ نائبًا)، `tawi`
  (المطاوعة: المفعولُ يصير فاعلَ اللازم)، `addi` (التعدية/السببية: فاعلٌ جديد سببًا والفاعلُ القديم مفعولًا)، `sharik` (المشاركة: فاعلان
  متبادلان)، `utlub` (الطلب: طالبٌ والفاعلُ مطلوبٌ منه). (٢) **الشبكة** `Shabaka`: قوائمُ أصولٍ مودَعة بأسمائها — قابليّات (جنس، فعل)،
  مفعوليّات (فعل، جنس)، سببيّات (سبب، مسبَّب)، حالات (جنس، حالة)، تسميات (صفة، فعل)، وقوانينُ معجميّة (حالة، فعل). (٣) **سلسلةُ
  القرار**: أقوالٌ `Qawl` بأربع رتب (`rutba`: الأصولُ 0، النسبةُ 1، الصفةُ/المفعولُ/النتيجةُ 2، ذو الحالة 3)، وقاعدةٌ `qaidaOf sh`
  قوانينُها مولَّدةٌ من أصول الشبكة: ش1 الفاعليةُ والمفعولية → النسبة («الحيوان يشرب الماء»)، ش2 التسميةُ بالمفعولية → الصفة
  («الماء شراب»)، ش3 المسمّى يُفعل («الشراب يُشرب»)، ش4 النسبةُ والسببية → النتيجة («الحيوان يُروى» — تعيينُ البنّاء من قول المالك
  «الحيوان يشرب الماء والماء يحقق الارواء»، أمضاه 14:39)، ش5 القانونُ المعجميّ والتسمية → ذو الحالة موصوف («السائل شراب»). **ولا قانونَ
  يرفع صفةَ النوع إلى ذي حالته.** القاعدةُ متدرّجة (`Mutadarrija`: ما رتبته صفر لا يُرخَّص إلّا أصلًا مودَعًا) وسليمةٌ على **نموذج
  البنّاء** `semB` («ما يثبت في الشبكة» — تعيينٌ: الأصولُ بقوائمها والمشتقّاتُ بمعانيها؛ وذو الحالة لا يثبت إلّا بقانونٍ معجميّ مودَع —
  لا إغلاقَ للعالم: الغيابُ ليس امتناعًا، م13): كلُّ مرخَّصٍ ثابتٌ فيه، وما لا يثبت فلا سلسلةَ له — **«لا حكم» لا «ممتنع»**. وعامًّا: بلا
  قانونٍ معجميّ مودَع لا يُرخَّص «ذو الحالة موصوف» بأيّ سلسلة (`jinsSifa_la_yurakhkhas`) — فـ«السائل شراب» لا حكم في `qaida`، ويصير
  مرخَّصًا في `qaida'` حين يُودَع قانونُ اللسان س16599: **القرارُ تابعٌ لما أُودع** (بالتعريف: `Murakhkhas` لا يأخذ إلّا الأصولَ
  والقوانين، وعلى الشاهد).

  **المبرهنات (لكلّ):** `tawi_addi` (المطاوعةُ عكسُ التعدية على اللازم المجرّد: أفعلته ففعل — قراءةً لنظير الكتاب س16546)،
  `tawi_lazim` (المطاوَعُ لازم: فعلته فانفعل)، `tawi_fail` (فاعلُ المطاوَع مفعولُ المتعدّي: كسرته فانكسر)، `tawi_lazim_la_hukm` (لا مطاوعةَ
  للازم)، `jahhil_naib` (نائبُ الفاعل مفعولُ المعلوم)، `jahhil_lazim_la_hukm`، `sharik_tabadul` (المشاركةُ متبادلة)، `utlub_yahfaz` (الطلبُ
  يحفظ الفعلَ والمطلوبَ منه)، `uslub_la_yakhtari` (لا أسلوبَ يخترع عينًا)؛ `murakhkhas_salim` (سلامةُ الترخيص على كلّ قاعدةٍ ونموذج)،
  `asl_sadiq`، `qaida_mutadarrija` (لكلّ شبكة: القاعدةُ المولَّدة متدرّجة بالرتبة)، `asl_la_yurakhkhas_illa_mudaan`، `s1`–`s5` وحفظُ
  الثبوت `qawanin_salima` (لكلّ شبكة)، `shabaka_salima` (كلُّ مرخَّصٍ ثابتٌ في النموذج)، `ghayr_thabit_la_yurakhkhas` و`marfud` (ما لا
  يثبت لا سلسلةَ له)، `jinsSifa_la_yurakhkhas` (بلا قانونٍ معجميّ لا يُرخَّص ذو الحالة موصوفًا — لكلّ شبكة). **على الشاهد** (شبكةُ مثال
  المالك `shabaka` بشواهدها): `shawahid_maqbula` (سلاسلُ «الحيوان يشرب الماء»، «الحيوان يُروى» عبر «الماء يحقّق الريّ»، «الماء سائل»،
  «الماء شراب»، «الشراب يُشرب» يقبلها الفاحص)، `sail_sharab_marfud` (لا ترخيصَ لـ«السائل شراب» في `qaida` بأيّ سلسلة — من العامّ)،
  `sail_sharab_bil_mujam` (ويُقبل في `qaida'` بسلسلةٍ تمرّ بقانون اللسان س16599)، `salasil_marfuda` (سلسلةٌ مقلوبة وأصلٌ غيرُ مودَع
  يُرفضان)، `qaida_shahid_mutadarrija`، `adad_qawanin` (6 قوانين منسَّخة: ش1 اثنان، ش2 واحد، ش3 واحد، ش4 اثنان؛ ومع المعجميّ 7).

  الوسم: مبرهن (لكلّ) ما سُمّي كذلك (والمرايا `semB_*` تعريفيّة rfl)؛ مبرهن على الشاهد (decide على الشبكة `shabaka` التي كتبها
  البنّاء من الشواهد أعلاه) ما سُمّي كذلك. `semB` تعيينُ البنّاء للنموذج لا نصٌّ. الشبكةُ مودَعةٌ جدولًا («جدول العلاقات»، معلومات
  سابقة، `alaqat.tsv`، `0269d2ce…`) بإذن المالك («أُعدّه وتختمه بإذنك كالسابق. موافق» 14:39 — الإذنُ كلمةُ «موافق» على مقترحٍ يصف
  الجدول ولا يسمّي الملفّ؛ تثبيتُه بالاسم باسمه) ومطابَقةٌ بـ `tahaqquq/test_shabaka.py`. في الجدول المختوم خللٌ معلَن: صفُّ ش4 يسمّي
  «قول المالك» سندًا للقانون والصوابُ «تعيينُ البنّاء أمضاه المالك»، وشاهدُه ج3 س796/798 لعلاقة السببية اسمًا (مجازًا) لا للقانون؛
  وصفُّ ش0 «لا قانون» موسومٌ `qanun`؛ وعمودُ `luzum` في صفوف الأصول لا مرآةَ له (أزواجٌ بأسمائها). المجازُ (السببية/المسببية تسميةً)
  فوق هذه الطبقة برخصةٍ مسمّاة — لم يُبنَ هنا.
-/
import Madlul.Jamad
import Aql.Qaida

set_option autoImplicit false

namespace Madlul
namespace Shabaka
open Tayin Wiratha Jamad Qaida

/-! ## ١. الأدوار والأساليب تحويلاتٍ -/

/-- اللزومُ والتعدّي (الكتاب س324، س332). -/
inductive Luzum | lazim | mutaaddi
deriving DecidableEq, Repr

/-- أساليبُ الإخبار عن الفعل: المجرّد (المعلوم)، المجهول، المطاوعة (انفعل)، التعدية/السببية (أفعل)، المشاركة (فاعَل/تفاعَل)،
الطلب (استفعل). -/
inductive Uslub | mujarrad | majhul | mutawaa | tadiya | musharaka | talab
deriving DecidableEq, Repr

/-- فعلٌ بلزومه. -/
structure Fil where
  ism : String
  luzum : Luzum
deriving DecidableEq, Repr

/-- إخبارٌ: فعلٌ وأسلوبٌ وأدوارٌ مشغولة (الفاعل، المفعول، السبب/الطالب) بأعيانٍ من `A`؛ الدورُ الفارغ «لا حكم». -/
structure Ikhbar (A : Type) where
  fil : Fil
  uslub : Uslub := .mujarrad
  fail : Option A := none
  mafool : Option A := none
  sabab : Option A := none
deriving DecidableEq, Repr

variable {A : Type}

/-- **المجهول:** يُحذف الفاعلُ ويبقى المفعولُ نائبًا عنه؛ ولا مجهولَ لما لا مفعولَ له (لا حكم). -/
def jahhil (i : Ikhbar A) : Option (Ikhbar A) :=
  match i.uslub, i.mafool with
  | .mujarrad, some m => some { i with uslub := .majhul, fail := none, mafool := some m }
  | _, _ => none

/-- **المطاوعة** (الكتاب س16543: كسرته فانكسر): المفعولُ يصير فاعلَ اللازم؛ ولا مطاوعةَ للازم ولا لغير المجرّد. -/
def tawi (i : Ikhbar A) : Option (Ikhbar A) :=
  match i.uslub, i.fil.luzum, i.mafool with
  | .mujarrad, .mutaaddi, some m => some { fil := { i.fil with luzum := .lazim }, uslub := .mutawaa, fail := some m }
  | .tadiya, _, some m => some { fil := i.fil, uslub := .mujarrad, fail := some m }
  | _, _, _ => none

/-- **التعدية/السببية** (الكتاب س16546: أدخلته فدخل؛ لسان س205864: سال … وأساله غيره): فاعلٌ جديد `s` سببًا، والفاعلُ القديم
مفعولًا؛ على المجرّد اللازم ذي الفاعل. -/
def addi (i : Ikhbar A) (s : A) : Option (Ikhbar A) :=
  match i.uslub, i.fil.luzum, i.fail with
  | .mujarrad, .lazim, some f => some { fil := i.fil, uslub := .tadiya, fail := some s, mafool := some f, sabab := some s }
  | _, _, _ => none

/-- **المشاركة** (لسان س18424: ضاربه، تضاربا): فاعلان كلٌّ فاعلٌ ومفعول؛ على المجرّد المتعدّي ذي الفاعل والمفعول. -/
def sharik (i : Ikhbar A) : Option (Ikhbar A) :=
  match i.uslub, i.fil.luzum, i.fail, i.mafool with
  | .mujarrad, .mutaaddi, some f, some m => some { fil := i.fil, uslub := .musharaka, fail := some f, mafool := some m }
  | _, _, _, _ => none

/-- **الطلب** (لسان س281484: استسقيت فلانا إذا طلبت منه أن يسقيك): طالبٌ `t` فاعلًا للاستفعال، والفاعلُ المطلوبُ منه مفعولًا،
والفعلُ هو هو. -/
def utlub (i : Ikhbar A) (t : A) : Option (Ikhbar A) :=
  match i.uslub, i.fail with
  | .mujarrad, some f => some { fil := i.fil, uslub := .talab, fail := some t, mafool := some f, sabab := some t }
  | _, _ => none

/-- **المطاوعةُ عكسُ التعدية:** أفعلته ففعل — تعديةُ اللازم ثمّ مطاوعتُها تعيد الإخبارَ الأصليّ (مجرّدًا بفاعله، بلا مفعولٍ ولا سبب). -/
theorem tawi_addi (i : Ikhbar A) (s : A) (i' : Ikhbar A) (h : addi i s = some i') :
    tawi i' = some { fil := i.fil, uslub := .mujarrad, fail := i.fail } := by
  obtain ⟨⟨ism, luzum⟩, uslub, fail, mafool, sabab⟩ := i
  cases uslub <;> cases luzum <;> cases fail <;> simp [addi] at h
  subst h
  rfl

/-- **المطاوَعُ لازم:** مطاوعةُ المتعدّي المجرّد تعطي إخبارًا لازمًا (الكتاب س16543: فعلته فانفعل). -/
theorem tawi_lazim (i i' : Ikhbar A) (hu : i.uslub = .mujarrad) (h : tawi i = some i') :
    i'.fil.luzum = .lazim ∧ i'.mafool = none := by
  obtain ⟨⟨ism, luzum⟩, uslub, fail, mafool, sabab⟩ := i
  simp at hu; subst hu
  cases luzum <;> cases mafool <;> simp [tawi] at h <;> subst h <;> exact ⟨rfl, rfl⟩

/-- **فاعلُ المطاوَع مفعولُ المتعدّي:** كسرتُه فانكسر — ما انكسر هو ما كُسر. -/
theorem tawi_fail (i i' : Ikhbar A) (h : tawi i = some i') : i'.fail = i.mafool := by
  obtain ⟨⟨ism, luzum⟩, uslub, fail, mafool, sabab⟩ := i
  cases uslub <;> cases luzum <;> cases mafool <;> simp [tawi] at h <;> subst h <;> rfl

/-- **لا مطاوعةَ للازم المجرّد:** لا مفعولَ يصير فاعلًا (لا حكم). -/
theorem tawi_lazim_la_hukm (i : Ikhbar A) (hu : i.uslub = .mujarrad) (hl : i.fil.luzum = .lazim) : tawi i = none := by
  obtain ⟨⟨ism, luzum⟩, uslub, fail, mafool, sabab⟩ := i
  simp at hu hl; subst hu; subst hl
  cases mafool <;> rfl

/-- **نائبُ الفاعل مفعولُ المعلوم:** في المجهول يبقى المفعولُ ويُحذف الفاعل. -/
theorem jahhil_naib (i i' : Ikhbar A) (h : jahhil i = some i') : i'.mafool = i.mafool ∧ i'.fail = none ∧ i'.uslub = .majhul := by
  obtain ⟨fil, uslub, fail, mafool, sabab⟩ := i
  cases uslub <;> cases mafool <;> simp [jahhil] at h <;> subst h <;> exact ⟨rfl, rfl, rfl⟩

/-- **لا مجهولَ لما لا مفعولَ له** (لا حكم). -/
theorem jahhil_lazim_la_hukm (i : Ikhbar A) (h : i.mafool = none) : jahhil i = none := by
  obtain ⟨fil, uslub, fail, mafool, sabab⟩ := i
  simp at h; subst h
  cases uslub <;> rfl

/-- تبادلُ الفاعل والمفعول. -/
def tabadul (i : Ikhbar A) : Ikhbar A := { i with fail := i.mafool, mafool := i.fail }

/-- **المشاركةُ متبادلة:** ضاربه وضاربَه الآخر سواءٌ في الأسلوب والفعل والمشاركين (مجموعةً لا ترتيبًا): مشاركةُ المتبادَل هي
متبادَلُ المشاركة. -/
theorem sharik_tabadul (i : Ikhbar A) : sharik (tabadul i) = (sharik i).map tabadul := by
  obtain ⟨⟨ism, luzum⟩, uslub, fail, mafool, sabab⟩ := i
  cases uslub <;> cases luzum <;> cases fail <;> cases mafool <;> rfl

/-- **الطلبُ يحفظ الفعلَ والمطلوبَ منه:** استسقيتُه — الفعلُ السقي بعينه، والمسقي المطلوبُ منه مفعولُ الاستفعال، والطالبُ فاعلُه. -/
theorem utlub_yahfaz (i i' : Ikhbar A) (t : A) (h : utlub i t = some i') :
    i'.fil = i.fil ∧ i'.mafool = i.fail ∧ i'.fail = some t ∧ i'.uslub = .talab := by
  obtain ⟨fil, uslub, fail, mafool, sabab⟩ := i
  cases uslub <;> cases fail <;> simp [utlub] at h <;> subst h <;> exact ⟨rfl, rfl, rfl, rfl⟩

/-- أعيانُ الإخبار: ما شغل الأدوار. -/
def ayan (i : Ikhbar A) : List A := [i.fail, i.mafool, i.sabab].filterMap id

/-- **لا أسلوبَ يخترع عينًا:** أعيانُ ناتج كلّ تحويلٍ من أعيان أصله ومن العين المزيدة المعلَنة (في التعدية والطلب) لا غير. -/
theorem uslub_la_yakhtari (i i' : Ikhbar A) :
    (jahhil i = some i' → ∀ a ∈ ayan i', a ∈ ayan i) ∧
    (tawi i = some i' → ∀ a ∈ ayan i', a ∈ ayan i) ∧
    (sharik i = some i' → ∀ a ∈ ayan i', a ∈ ayan i) ∧
    (∀ s, addi i s = some i' → ∀ a ∈ ayan i', a ∈ ayan i ∨ a = s) ∧
    (∀ t, utlub i t = some i' → ∀ a ∈ ayan i', a ∈ ayan i ∨ a = t) := by
  obtain ⟨⟨ism, luzum⟩, uslub, fail, mafool, sabab⟩ := i
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · intro h; cases uslub <;> cases mafool <;> simp [jahhil] at h <;> subst h <;> simp_all [ayan]
  · intro h; cases uslub <;> cases luzum <;> cases mafool <;> simp [tawi] at h <;> subst h <;> simp_all [ayan]
  · intro h; cases uslub <;> cases luzum <;> cases fail <;> cases mafool <;> simp [sharik] at h <;> subst h <;> simp_all [ayan]
  · intro s h; cases uslub <;> cases luzum <;> cases fail <;> simp [addi] at h <;> subst h <;> simp_all [ayan]
  · intro t h; cases uslub <;> cases fail <;> simp [utlub] at h <;> subst h <;> simp_all [ayan]

/-! ## ٢. الشبكة وسلسلةُ القرار -/

/-- الأقوالُ في الشبكة (الأعيانُ أسماءٌ بالعربيّة): أصولٌ مودَعة (رتبة 0) وأقوالٌ مشتقّة (رتب 1–3). -/
inductive Qawl
  | qabiliyya (jins fil : String)        -- «الجنسُ يفعل» — قابليّةٌ مودَعة (القطعة الأولى: شرب)
  | mafooliyya (fil jins : String)       -- «الجنسُ مفعولُ الفعل» — المعجم (لسان س16528: شرب الماء)
  | sababiyya (sabab musabbab : String)  -- «السببُ يحقّق المسبَّب» — المعجم (س231914: رويت من الماء)
  | hala (jins h : String)               -- «الجنسُ في حالة» — القطعة الثانية (الماء سائل)
  | tasmiya (sifa fil : String)          -- «الصفةُ اسمٌ لمفعول الفعل» — المعجم (س16550: الشراب ما شُرب)
  | qanunMujam (h fil : String)          -- «ما في الحالة يُفعل» — قانونٌ معجميّ (س16599: ما لا يُمضغ يُشرب)
  | nisba (fail fil mafool : String)     -- رتبة 1: «الفاعلُ يفعل المفعول» (الحيوان يشرب الماء)
  | sifa (jins sifa : String)            -- رتبة 2: «الجنسُ موصوف» (الماء شراب)
  | yufal (sifa fil : String)            -- رتبة 2: «الموصوفُ يُفعل» (الشراب يُشرب)
  | natija (jins musabbab : String)      -- رتبة 2: «الجنسُ يناله المسبَّب» (الحيوان يُروى)
  | jinsSifa (h sifa : String)           -- رتبة 3: «ذو الحالة موصوف» (السائل شراب)
deriving DecidableEq, Repr

/-- **الرتبة = درجةُ الاشتقاق:** الأصولُ المودَعة صفر، والنسبةُ 1، والتسميةُ والنتيجة 2، والحكمُ على ذي الحالة 3. -/
def rutba : Qawl → Nat
  | .qabiliyya .. | .mafooliyya .. | .sababiyya .. | .hala .. | .tasmiya .. | .qanunMujam .. => 0
  | .nisba .. => 1
  | .sifa .. | .yufal .. | .natija .. => 2
  | .jinsSifa .. => 3

/-- الشبكةُ المودَعة: قوائمُ الأصول (أزواجٌ بأسمائها) — تُولَّد منها القوانين. -/
structure Shabaka where
  qabiliyyat : List (String × String)
  mafooliyyat : List (String × String)
  sababiyyat : List (String × String)
  halat : List (String × String)
  tasmiyat : List (String × String)
  qawaninMujam : List (String × String) := []

/-- أصولُ الشبكة قولًا: ما كان في قوائمها. -/
def Shabaka.aslB (sh : Shabaka) : Qawl → Bool
  | .qabiliyya j f => sh.qabiliyyat.contains (j, f)
  | .mafooliyya f m => sh.mafooliyyat.contains (f, m)
  | .sababiyya a b => sh.sababiyyat.contains (a, b)
  | .hala m h => sh.halat.contains (m, h)
  | .tasmiya s f => sh.tasmiyat.contains (s, f)
  | .qanunMujam h f => sh.qawaninMujam.contains (h, f)
  | _ => false

/-- الصفةُ ثابتةٌ لجنسٍ: تسميةٌ لمفعول فعلٍ هو مفعولُه. -/
def Shabaka.sifaB (sh : Shabaka) (m s : String) : Bool :=
  sh.tasmiyat.any fun (s', f) => s' == s && sh.aslB (.mafooliyya f m)

/-- **ما يثبت في الشبكة** — نموذجُ البنّاء (تعيين): الأصولُ بقوائمها، والمشتقّاتُ بمعانيها: النسبةُ قابليّةٌ ومفعوليّة؛ والصفةُ تسميةٌ
لمفعولٍ؛ والموصوفُ يُفعل؛ والنتيجةُ نسبةٌ وسببيّةٌ؛ وذو الحالة موصوفٌ بقانونٍ معجميّ مودَع لا غير — فلا إغلاقَ للعالم: ما لا يثبت
«لا حكم» لا «ممتنع» (م13). -/
def Shabaka.semB (sh : Shabaka) : Qawl → Bool
  | .nisba j f m => sh.aslB (.qabiliyya j f) && sh.aslB (.mafooliyya f m)
  | .sifa m s => sh.sifaB m s
  | .yufal s f => sh.aslB (.tasmiya s f)
  | .natija j b => sh.mafooliyyat.any fun (f, m) => sh.aslB (.qabiliyya j f) && sh.aslB (.mafooliyya f m) && sh.aslB (.sababiyya m b)
  | .jinsSifa h s => sh.tasmiyat.any fun (s', f) => s' == s && sh.aslB (.qanunMujam h f)
  | q => sh.aslB q

/-- القوانين (قاعدةٌ واحدة، إصدار «شبكة-1»)، مولَّدةً من أصول الشبكة:
ش1 الفاعليةُ والمفعولية → النسبة؛ ش2 التسميةُ بالمفعولية → الصفة؛ ش3 المسمّى يُفعل؛ ش4 النسبةُ والسببية → النتيجة؛
ش5 القانونُ المعجميّ والتسمية → ذو الحالة موصوف. **ولا قانونَ يرفع صفةَ النوع إلى ذي حالته.** -/
def qaidaOf (sh : Shabaka) : Qaida Qawl :=
  { isdar := "شبكة-1"
    qawanin :=
      (sh.qabiliyyat.flatMap fun (j, f) => sh.mafooliyyat.filterMap fun (f', m) =>
        if f' == f then some ⟨"ش1", [.qabiliyya j f, .mafooliyya f m], .nisba j f m⟩ else none) ++
      (sh.mafooliyyat.flatMap fun (f, m) => sh.tasmiyat.filterMap fun (s, f') =>
        if f' == f then some ⟨"ش2", [.mafooliyya f m, .tasmiya s f], .sifa m s⟩ else none) ++
      (sh.tasmiyat.map fun (s, f) => ⟨"ش3", [.tasmiya s f], .yufal s f⟩) ++
      (sh.qabiliyyat.flatMap fun (j, f) => sh.mafooliyyat.flatMap fun (f', m) => sh.sababiyyat.filterMap fun (m', b) =>
        if f' == f && m' == m then some ⟨"ش4", [.nisba j f m, .sababiyya m b], .natija j b⟩ else none) ++
      (sh.qawaninMujam.flatMap fun (h, f) => sh.tasmiyat.filterMap fun (s, f') =>
        if f' == f then some ⟨"ش5", [.qanunMujam h f, .tasmiya s f], .jinsSifa h s⟩ else none) }

/-- **سلامةُ الترخيص** (لكلّ قاعدةٍ ونموذج): إن صدقت الأصولُ في النموذج وحفظت كلُّ قوانين القاعدة الصدقَ، فكلُّ قولٍ مرخَّص صادق. -/
theorem murakhkhas_salim {P : Type} (q : Qaida P) (A : P → Prop) (sem : P → Prop)
    (hA : ∀ p, A p → sem p) (hq : ∀ r ∈ q.qawanin, (∀ m ∈ r.muqaddimat, sem m) → sem r.natija) :
    ∀ p, Murakhkhas q A p → sem p := by
  intro p h
  induction h with
  | asl ha => exact hA _ ha
  | qanun r hr _ ih => exact hq r hr ih

/-- أصولُ الشبكة ثابتةٌ في نموذجها (لكلّ شبكة). -/
theorem asl_sadiq (sh : Shabaka) (p : Qawl) (h : sh.aslB p = true) : sh.semB p = true := by
  cases p <;> first | exact h | simp [Shabaka.aslB] at h

/-- **القاعدةُ المولَّدة متدرّجة** (لكلّ شبكة): مقدّماتُ كلّ قانونٍ أدنى رتبةً من نتيجته ولا قانونَ بلا مقدّمة — فما رتبته صفر
(الأصول) لا يُرخَّص إلّا مودَعًا (`rutba_sifr_asl`). -/
theorem qaida_mutadarrija (sh : Shabaka) : Mutadarrija (qaidaOf sh) rutba := by
  intro r hr
  simp only [qaidaOf, List.mem_append, List.mem_flatMap, List.mem_filterMap, List.mem_map] at hr
  rcases hr with (((⟨⟨j, f⟩, _, ⟨f', m⟩, _, hr⟩ | ⟨⟨f, m⟩, _, ⟨s, f'⟩, _, hr⟩) | ⟨⟨s, f⟩, _, hr⟩) |
      ⟨⟨j, f⟩, _, ⟨f', m⟩, _, ⟨m', b⟩, _, hr⟩) | ⟨⟨h, f⟩, _, ⟨s, f'⟩, _, hr⟩ <;>
    (try split at hr) <;> (try simp only [Option.some.injEq, reduceCtorEq] at hr) <;> subst hr <;> simp [rutba]

/-- ما رتبته صفر لا يُرخَّص إلّا أصلًا مودَعًا — على كلّ شبكة. -/
theorem asl_la_yurakhkhas_illa_mudaan (sh : Shabaka) (p : Qawl) (h0 : rutba p = 0)
    (h : Murakhkhas (qaidaOf sh) (fun y => sh.aslB y = true) p) : sh.aslB p = true :=
  rutba_sifr_asl (qaidaOf sh) rutba _ (qaida_mutadarrija sh) h h0

@[simp] theorem semB_qabiliyya (sh : Shabaka) (j f : String) : sh.semB (.qabiliyya j f) = sh.aslB (.qabiliyya j f) := rfl
@[simp] theorem semB_mafooliyya (sh : Shabaka) (f m : String) : sh.semB (.mafooliyya f m) = sh.aslB (.mafooliyya f m) := rfl
@[simp] theorem semB_sababiyya (sh : Shabaka) (a b : String) : sh.semB (.sababiyya a b) = sh.aslB (.sababiyya a b) := rfl
@[simp] theorem semB_tasmiya (sh : Shabaka) (s f : String) : sh.semB (.tasmiya s f) = sh.aslB (.tasmiya s f) := rfl
@[simp] theorem semB_qanunMujam (sh : Shabaka) (h f : String) : sh.semB (.qanunMujam h f) = sh.aslB (.qanunMujam h f) := rfl
@[simp] theorem semB_nisba (sh : Shabaka) (j f m : String) :
    sh.semB (.nisba j f m) = (sh.aslB (.qabiliyya j f) && sh.aslB (.mafooliyya f m)) := rfl

theorem s1 (sh : Shabaka) (j f m : String) (h1 : sh.aslB (.qabiliyya j f) = true) (h2 : sh.aslB (.mafooliyya f m) = true) :
    sh.semB (.nisba j f m) = true := by simp [h1, h2]
theorem s2 (sh : Shabaka) (f m s : String) (hs : (s, f) ∈ sh.tasmiyat) (h2 : sh.aslB (.mafooliyya f m) = true) :
    sh.semB (.sifa m s) = true := by
  simp only [Shabaka.semB, Shabaka.sifaB, List.any_eq_true]
  exact ⟨(s, f), hs, by simp [h2]⟩
theorem s3 (sh : Shabaka) (s f : String) (h : sh.aslB (.tasmiya s f) = true) : sh.semB (.yufal s f) = true := h
theorem s4 (sh : Shabaka) (j f m b : String) (hf : (f, m) ∈ sh.mafooliyyat) (h1 : sh.aslB (.qabiliyya j f) = true)
    (h2 : sh.aslB (.mafooliyya f m) = true) (h3 : sh.aslB (.sababiyya m b) = true) : sh.semB (.natija j b) = true := by
  simp only [Shabaka.semB, List.any_eq_true]
  exact ⟨(f, m), hf, by simp [h1, h2, h3]⟩
theorem s5 (sh : Shabaka) (h f s : String) (hs : (s, f) ∈ sh.tasmiyat) (hq : sh.aslB (.qanunMujam h f) = true) :
    sh.semB (.jinsSifa h s) = true := by
  simp only [Shabaka.semB, List.any_eq_true]
  exact ⟨(s, f), hs, by simp [hq]⟩

/-- **قوانينُ الشبكة تحفظ الثبوت** (لكلّ شبكة): كلُّ قانونٍ مولَّد إن ثبتت مقدّماتُه في النموذج ثبتت نتيجتُه. -/
theorem qawanin_salima (sh : Shabaka) :
    ∀ r ∈ (qaidaOf sh).qawanin, (∀ m ∈ r.muqaddimat, sh.semB m = true) → sh.semB r.natija = true := by
  intro r hr hm
  simp only [qaidaOf, List.mem_append, List.mem_flatMap, List.mem_filterMap, List.mem_map] at hr
  rcases hr with (((⟨⟨j, f⟩, hj, ⟨f', m⟩, hf, hr⟩ | ⟨⟨f, m⟩, hf, ⟨s, f'⟩, hs, hr⟩) | ⟨⟨s, f⟩, hs, hr⟩) |
      ⟨⟨j, f⟩, hj, ⟨f', m⟩, hf, ⟨m', b⟩, hb, hr⟩) | ⟨⟨h, f⟩, hh, ⟨s, f'⟩, hs, hr⟩
  · split at hr
    · rename_i hff; simp only [beq_iff_eq] at hff; subst hff
      simp only [Option.some.injEq] at hr; subst hr
      simp only [List.mem_cons, List.not_mem_nil, or_false, forall_eq_or_imp, forall_eq, semB_qabiliyya,
        semB_mafooliyya] at hm
      exact s1 sh _ _ _ hm.1 hm.2
    · simp at hr
  · split at hr
    · rename_i hff; simp only [beq_iff_eq] at hff; subst hff
      simp only [Option.some.injEq] at hr; subst hr
      simp only [List.mem_cons, List.not_mem_nil, or_false, forall_eq_or_imp, forall_eq, semB_mafooliyya,
        semB_tasmiya] at hm
      exact s2 sh _ _ _ hs hm.1
    · simp at hr
  · subst hr
    simp only [List.mem_cons, List.not_mem_nil, or_false, forall_eq, semB_tasmiya] at hm
    exact s3 sh _ _ hm
  · split at hr
    · rename_i hff; simp only [Bool.and_eq_true, beq_iff_eq] at hff; obtain ⟨rfl, rfl⟩ := hff
      simp only [Option.some.injEq] at hr; subst hr
      simp only [List.mem_cons, List.not_mem_nil, or_false, forall_eq_or_imp, forall_eq, semB_nisba,
        semB_sababiyya, Bool.and_eq_true] at hm
      exact s4 sh _ _ _ _ hf hm.1.1 hm.1.2 hm.2
    · simp at hr
  · split at hr
    · rename_i hff; simp only [beq_iff_eq] at hff; subst hff
      simp only [Option.some.injEq] at hr; subst hr
      simp only [List.mem_cons, List.not_mem_nil, or_false, forall_eq_or_imp, forall_eq, semB_qanunMujam,
        semB_tasmiya] at hm
      exact s5 sh _ _ _ hs hm.1
    · simp at hr

/-- **سلامةُ الشبكة** (لكلّ شبكة): كلُّ قولٍ مرخَّص في قاعدتها على أصولها ثابتٌ في نموذجها. -/
theorem shabaka_salima (sh : Shabaka) (p : Qawl) (h : Murakhkhas (qaidaOf sh) (fun y => sh.aslB y = true) p) :
    sh.semB p = true :=
  murakhkhas_salim (qaidaOf sh) _ (fun q => sh.semB q = true) (asl_sadiq sh) (qawanin_salima sh) p h

/-- ومنه: **ما لا يثبت في النموذج لا يُرخَّص** — لا سلسلةَ تمرّ بالفاحص لقولٍ لا يثبت (وهو «لا حكم» لا «ممتنع»). -/
theorem ghayr_thabit_la_yurakhkhas (sh : Shabaka) (p : Qawl) (h : sh.semB p = false) :
    ¬ Murakhkhas (qaidaOf sh) (fun y => sh.aslB y = true) p := fun hm => by
  have := shabaka_salima sh p hm
  simp [h] at this

theorem marfud (sh : Shabaka) (c : Iddia Qawl) (h : sh.semB c.qawl = false) : maqbul (qaidaOf sh) sh.aslB c = false := by
  cases hm : maqbul (qaidaOf sh) sh.aslB c
  · rfl
  · exact absurd (maqbul_murakhkhas _ _ c hm) (ghayr_thabit_la_yurakhkhas sh c.qawl h)

/-- **بلا قانونٍ معجميّ مودَع لا يُرخَّص «ذو الحالة موصوف» بأيّ سلسلة** (لكلّ شبكة): ليس أصلًا، ولا قانونَ نتيجتُه ذو الحالة إلّا ش5
وهو لا يُولَّد إلّا من قانونٍ معجميّ — فالقرارُ «لا حكم» من بنية القاعدة لا من شاهدٍ مضادّ (م13: الغيابُ ليس امتناعًا). -/
theorem jinsSifa_la_yurakhkhas (sh : Shabaka) (hq : sh.qawaninMujam = []) (h s : String) :
    ¬ Murakhkhas (qaidaOf sh) (fun y => sh.aslB y = true) (.jinsSifa h s) := by
  intro hm
  generalize hp : Qawl.jinsSifa h s = p at hm
  cases hm with
  | asl ha => subst hp; simp [Shabaka.aslB] at ha
  | qanun r hr _ =>
    simp only [qaidaOf, hq, List.mem_append, List.mem_flatMap, List.mem_filterMap, List.mem_map, List.flatMap_nil,
      List.not_mem_nil, or_false] at hr
    rcases hr with ((⟨⟨j, f⟩, _, ⟨f', m⟩, _, hr⟩ | ⟨⟨f, m⟩, _, ⟨s', f'⟩, _, hr⟩) | ⟨⟨s', f⟩, _, hr⟩) |
        ⟨⟨j, f⟩, _, ⟨f', m⟩, _, ⟨m', b⟩, _, hr⟩ <;>
      (try split at hr) <;> (try simp only [Option.some.injEq, reduceCtorEq] at hr) <;> subst hr <;> simp at hp

/-! ## ٣. الشاهد: شبكةُ مثال المالك -/

/-- شبكةُ المثال (أصولُها بشواهدها): القابليّات من القطعة الأولى (الحيوان والإنسان: شرب)؛ المفعولية من لسان س16528 (شرب الماء)؛
السببية من لسان س231914 وس251637 (الريُّ من الماء)؛ الحالاتُ من القطعة الثانية (الماء والزئبق سائلان، الحديد جامد)؛ التسمية من
لسان س16550 (الشراب ما شُرب). -/
def shabaka : Shabaka :=
  { qabiliyyat := [("الحيوان", "شرب"), ("الإنسان", "شرب")]
    mafooliyyat := [("شرب", "الماء")]
    sababiyyat := [("الماء", "الريّ")]
    halat := [("الماء", "سائل"), ("الزئبق", "سائل"), ("الحديد", "جامد")]
    tasmiyat := [("شراب", "شرب")] }

/-- الشبكةُ نفسها مع القانون المعجميّ (لسان س16599: «وكل شيء لا يمضغ، فإنه يقال فيه: يشرب» — وأنّ السائل لا يُمضغ: تعيين). -/
def shabaka' : Shabaka := { shabaka with qawaninMujam := [("سائل", "شرب")] }

def qaida : Qaida Qawl := qaidaOf shabaka
def qaida' : Qaida Qawl := qaidaOf shabaka'

/-- خطوةُ قانونٍ في السلسلة: بموضعه في القاعدة المولَّدة (بمقدّماته ونتيجته). -/
def khatwa (sh : Shabaka) (muq : List Qawl) (nat : Qawl) : Khatwa Qawl :=
  .qanun ((qaidaOf sh).qawanin.findIdx fun r => r.muqaddimat == muq && r.natija == nat)

/-- **سلاسلُ مثال المالك يقبلها الفاحص:** «الحيوان يشرب الماء» (ش1)، «الحيوان يُروى» (الماء يحقّق الريّ: ش4)، «الماء سائل» (أصل)،
«الماء شراب» (ش2)، «الشراب يُشرب» (ش3). -/
theorem shawahid_maqbula :
    maqbul qaida shabaka.aslB ⟨.nisba "الحيوان" "شرب" "الماء",
      [.asl (.qabiliyya "الحيوان" "شرب"), .asl (.mafooliyya "شرب" "الماء"),
       khatwa shabaka [.qabiliyya "الحيوان" "شرب", .mafooliyya "شرب" "الماء"] (.nisba "الحيوان" "شرب" "الماء")]⟩ = true ∧
    maqbul qaida shabaka.aslB ⟨.natija "الحيوان" "الريّ",
      [.asl (.qabiliyya "الحيوان" "شرب"), .asl (.mafooliyya "شرب" "الماء"),
       khatwa shabaka [.qabiliyya "الحيوان" "شرب", .mafooliyya "شرب" "الماء"] (.nisba "الحيوان" "شرب" "الماء"),
       .asl (.sababiyya "الماء" "الريّ"),
       khatwa shabaka [.nisba "الحيوان" "شرب" "الماء", .sababiyya "الماء" "الريّ"] (.natija "الحيوان" "الريّ")]⟩ = true ∧
    maqbul qaida shabaka.aslB ⟨.hala "الماء" "سائل", [.asl (.hala "الماء" "سائل")]⟩ = true ∧
    maqbul qaida shabaka.aslB ⟨.sifa "الماء" "شراب",
      [.asl (.mafooliyya "شرب" "الماء"), .asl (.tasmiya "شراب" "شرب"),
       khatwa shabaka [.mafooliyya "شرب" "الماء", .tasmiya "شراب" "شرب"] (.sifa "الماء" "شراب")]⟩ = true ∧
    maqbul qaida shabaka.aslB ⟨.yufal "شراب" "شرب",
      [.asl (.tasmiya "شراب" "شرب"), khatwa shabaka [.tasmiya "شراب" "شرب"] (.yufal "شراب" "شرب")]⟩ = true := by
  decide

/-- **«السائل شراب» لا سلسلةَ له** في `qaida` — من العامّ `jinsSifa_la_yurakhkhas`: لا قانونَ معجميّ مودَع، فلا يقبله الفاحص بأيّ
سلسلة؛ والحكمُ «لا حكم» لا «ممتنع» (ولا يُستنتج من كون الزئبق سائلًا بلا شاهدِ شربٍ شيءٌ: م13). -/
theorem sail_sharab_marfud (c : Iddia Qawl) (hc : c.qawl = .jinsSifa "سائل" "شراب") :
    maqbul qaida shabaka.aslB c = false := by
  cases hm : maqbul qaida shabaka.aslB c
  · rfl
  · have := maqbul_murakhkhas _ _ c hm
    rw [hc] at this
    exact absurd this (jinsSifa_la_yurakhkhas shabaka rfl _ _)

/-- **ويُقبل في `qaida'`** حين يُودَع القانونُ المعجميّ (لسان س16599) — القرارُ تابعٌ لما أُودع. -/
theorem sail_sharab_bil_mujam :
    maqbul qaida' shabaka'.aslB ⟨.jinsSifa "سائل" "شراب",
      [.asl (.qanunMujam "سائل" "شرب"), .asl (.tasmiya "شراب" "شرب"),
       khatwa shabaka' [.qanunMujam "سائل" "شرب", .tasmiya "شراب" "شرب"] (.jinsSifa "سائل" "شراب")]⟩ = true := by
  decide

/-- سلسلةٌ مقلوبة (القانونُ قبل أصوله) تُرفض، وأصلٌ غيرُ مودَع (الزئبق مفعول الشرب) يُرفض. -/
theorem salasil_marfuda :
    maqbul qaida shabaka.aslB ⟨.nisba "الحيوان" "شرب" "الماء",
      [khatwa shabaka [.qabiliyya "الحيوان" "شرب", .mafooliyya "شرب" "الماء"] (.nisba "الحيوان" "شرب" "الماء"),
       .asl (.qabiliyya "الحيوان" "شرب"), .asl (.mafooliyya "شرب" "الماء")]⟩ = false ∧
    maqbul qaida shabaka.aslB ⟨.mafooliyya "شرب" "الزئبق", [.asl (.mafooliyya "شرب" "الزئبق")]⟩ = false := by
  decide

/-- قاعدةُ الشاهد متدرّجة (من العامّ). -/
theorem qaida_shahid_mutadarrija : Mutadarrija qaida rutba := qaida_mutadarrija shabaka

/-- عددُ قوانين الشاهد: 2 (ش1) + 1 (ش2) + 1 (ش3) + 2 (ش4) = 6، ومع القانون المعجميّ 7. -/
theorem adad_qawanin : qaida.qawanin.length = 6 ∧ qaida'.qawanin.length = 7 := by decide

end Shabaka
end Madlul
