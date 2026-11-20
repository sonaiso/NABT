/-
  Nizam/Aqd.lean — العقدُ الواحد: البرهانُ المغلق لا يتجزّأ.

  قولُ المالك (2026-10-19، 20:08 بتوقيت عمّان): «البرهان المغلق لا يتجزأ يجب ان يعمل ككل واحد لا يتجزأ يعمل الكل مع الكل حتى
  لا نفطر للترقيع فكر بحل»؛ ثمّ (20:18): «حلل وقارن ثم  يُبنى طلبُ الدمج الواحد بهذا العقد موافق».

  البناءُ (تصميمُ البنّاء الذي وافق عليه المالك):
  * **العقدُ بنيةٌ واحدة** (`Aqd`): كلُّ طبقةٍ فيه حقلٌ بثلاثة أجزاء — مواصفةٌ، ومنفّذٌ بالبتّات، ومساواتُهما شرطًا في البنية
    نفسها. فلا يُنشأ عقدٌ إلّا ومنفّذُ كلّ حقلٍ مساوٍ لمواصفته التي تُقدَّم معه. والمساواةُ لا تجعل المواصفةَ صحيحةً لغةً، ولا
    يُبرهَن ذلك هنا: العقدُ المعيَّن يأخذ مواصفاتِه من تعريفات المشروع (`Mashru` أدناه)؛ وعقدٌ بمواصفاتٍ تافهةٍ يُبنى ويصدق عليه البرهان.
  * **مبرهنةٌ واحدة لكلّ عقد** (`kull_ma_kull`): حكمُ المنفّذ البتّيّ هو حكمُ المواصفة بمراتبه الثلاث (`Nizam.Hukm`):
    مرخَّص ⟺ القانونُ يقبل الدالّ، ولا مانع، وله جذرٌ يشهد له صفٌّ بالمدلول، واستوفى القيود؛ ممتنعٌ ⟺ القانونُ يردّ الدالّ أو
    قناعُ الموانع يردّ المدلول، والسببُ باسمه (`mumtani_asbab`)؛ وما سواهما «لا حكم» (غيابُ الشاهد لا يصير امتناعًا). ومعها:
    القراءةُ التي يحملها المرخَّص (الجذر، وحالُ الآخر، وقناعُ الصيغة) مطابقةٌ للمواصفة (`QiraaSahiha`).
  * **ما يشترك في الحكم وما لا يشترك**: القانونُ والجذرُ والشواهدُ والقيودُ والموانعُ تشترك في الحكم الواحد؛ وحالُ الآخر والصيغةُ
    قراءةٌ يحملها الحكمُ ولا تقيّده — لا قيدَ بين الطبقات مبنيٌّ بعد.
  * **البياناتُ قيمٌ لا مبرهنات**: صفوفُ الشواهد ومستوياتُ القيود والموانع حقولٌ بلا برهان؛ فإضافتُها لا تمسّ المبرهنة.
    وإضافةُ طبقةٍ توسيعٌ للبنية بحقلٍ وقانونه، ثمّ تُبرهن المبرهنةُ الواحدةُ مرّةً أخرى.

  العقدُ على Mashru (`Mashru n`، لكلّ نوع علاقةٍ n من `JadwalLuzum`: خمسةُ عقودٍ بمبرهنةٍ واحدة):
  * القانون (المرحلة «أ» من قانون المواصفة): مواصفتُه إطارُ الدالّ `Jisr.Utur.dalOK` (الابتداء، والوصل كما يُقرأ، والوقف «المكتمل»)
    — بناه البنّاء 2026-10-16 في `Jisr/Utur.lean` قراءةً لـ`SLGE/Necessity.lean` س25 بقرار المالك بناءَ الأطر، ودخل main بـ #12 (و#10 دمجٌ
    في الفرع `jisr/aqsam-55`)، وليس من تعييناته التي أمضاها يومئذٍ؛ وقرّر المالك 2026-10-20 00:23 اتّخاذَه مواصفةً، على مقدّمةٍ خاطئةٍ منّي
    (أنّه أمضاه) أُبلغ بها في الجلسة نفسها، فالقرارُ ينتظر تثبيتَه. وهو القانونان معًا لكلّ سلسلة
    (`dalOK_taqatu`): `Fwaqf (run 0 x)`
    على الخلايا المعطاة (صورةُ شواهد المالك `qaltu`/`hajja`/`bint`) و`complete'` بعد التسكين (`SLGE.Bridge.DalLic`). ولا واحدَ منهما
    يكفي وحده (`wahid_la_yakfi`: «قَالْتُ» يقبلها الثاني وحده، و«بَ» يقبلها الأوّل وحده)، ومقدارُ الفرق على الخانة والخانتين
    `farq_dalLic` (84 و84، والعقدُ يقبل 0 و9,436). ومنفّذُه الجدولُ نفسُه على الصورتين — فهرسُه [حالة:7][رمز:7] ومدخلُه [وزن:1][حالة:7]
    (`runB_run`)، والرمزُ فوق 116 يميت السلسلة (`run_kabir`). والمنفّذُ `qanunB` هو المكوّنان بجدول البتّات بحارسهما `kamaB && baadB`،
    وهما مساويان لـ`Fwaqf ∘ run 0` ولـ`complete'` لكلّ سلسلة (`kama_sawa`، `baad_sawa`)، فـ`qanun_sawa` منهما ومن `dalOK_taqatu`؛ والقارئ
    يستدعي `kamaB`/`baadB` بأعيانهما في سطر العقد.
  * الجذر: إسقاطُ ثلاث خاناتٍ حواملُها سالمة (لا ا ي و: `SLGE.Law.weak`) بحرفها `Jisr.JisrDal.harf`؛ منفّذُه الإزاحةُ وقناعُ العلّة
    (`qina_illa`)، ورمزُه حقولُ خمسة بتّات (`fakk_ramz`)؛ وحواملُ المسقَط سالمةٌ بشرط المالك `SLGE.Law.SoundR` (`jidhr_salim` —
    خلوُّها من ا ي و، لا أنّ المسقَطَ جذرٌ). والمعتلُّ يُردّ «لا حكم» (`qala_la_hukm`). أمّا المزيدُ والأدواتُ والضمائرُ فالإسقاطُ
    يأخذ خاناتها الثلاث كما هي فيُعطي مرشَّحًا ليس جذرًا («اسْمٌ» بهمزة الوصل المُصلَحة → «ءسم»، «أَنْتَ» → «ءنت»): مرشَّحُ جذرٍ
    لا هويّة، والمسارُ غيرُ الجذريّ لم يُبنَ.
  * حالُ الآخر: `Jisr.JisrDal.hala` للخانة الأخيرة، ومنفّذُه القناع 3. وقراءتُه إعرابًا مرشَّحٌ بتقابل المالك
    `SLGE.Bridge.irabState` (قطر الندى L77–78) للحركة وحدها؛ والسكونُ في الآخر «لا حكم» (`irabMurashshah_la_jazm`).
  * الصيغة: مرشَّحو صيغة الفعل من `Jisr.Iqtiran` (ماضٍ/أمر/مضارع) بقيد افتتاح نأيت (قطر L65)، منفّذُها قناعُ ثلاثة بتّات
    وحاملُ نأيت قناعٌ على الحوامل — إن كان الدالُّ فعلًا؛ والفعليّةُ نفسُها لا تُعيَّن هنا.
  * الشواهد: صفوفُ `Madlul.JadwalLuzum.jadwal` من نوع n بأسطرها، مفتاحُها جذرُ المادّة ومدلولُها الجذرُ الآخر (كما في الجدول).
    فالحكمُ على مستوى المادّة: «في مادّة جذر هذا الدالّ صفٌّ من نوع n إلى الجذر b، بلفظه W وسطره» — لا أنّ صيغةَ الدالّ هي W
    بعينها؛ مطابقةُ الصيغة (الوزن) حقلٌ لم يُبنَ. شاهدُه «كَتَبَ»: سطرُ اللسان س24030 فيه «وكتب الرجل وأكتبه إكتابا: علمه
    الكتاب»، ولفظُ الصفّ W فيه «وءكتبه».
  * القيودُ والموانعُ على المدلول: فارغةٌ في هذا العقد (لا قيدَ مودَعًا على رموز المدلول بعد) — معلَن.

  العدّ بالمعيار الموحَّد في `Nizam/Asas.lean` (جدولُ توجيهٍ رفعه المالك 2026-10-19 18:02): 30 مبرهنة —
  16 لكلّ (`iqtiranB_iff`، `tarkib_iff`، `bit_wahid`، `mustawa_iff`، `kull_ma_kull`، `la_shahid_la_hukm`، `khatwa_qanun`، `runB_run`،
  `run_kabir`، `kama_sawa`، `baad_sawa`، `dalOK_taqatu`، `fakk_ramz`، `siyagh_sawa`، `jidhr_salim`، `irabMurashshah_la_jazm`)،
  و2 تعريفيّة (`mumtani_asbab`، `irabMin_irabState`)، و12 على الشاهد: ثمانٍ برهانُها decide (`fahras`، `madkhal_fakk`، `qina_illa`،
  `nayta_qina`، `farq_dalLic`، `wahid_la_yakfi`،
  `shawahid_sigha`، `kataba_haal`)، وأربعٌ على كلمةٍ معيّنة (ثلاثٌ منها كمّيّةٌ في المدلول) برهانُها decide على المواصفة ثمّ نقلٌ بـ
  `kull_ma_kull` أو `mumtani_asbab` — خارجَ حرف المعيار («برهانُها decide»)، ووسمُها هنا أدنى من «لكلّ» الذي يبلغه حرفُه، معلَن (`kataba_ilm_taraduf`، `kataba_luzum_la_hukm`، `qaltu_mumtani`،
  `qala_la_hukm`): الحكمُ على كلمةٍ بعينها لا يُحسب بـ decide مباشرةً لأنّ جدول القانون (`Array.ofFn`) يُعمِّق ردَّ النواة.
  القارئ يطبع سطورَ العقد (`Qari/Main.lean`، `iqraAqd`) ويطابقه `tahaqquq/test_qari.py` §١٨؛ الطفرات P255–P268، وP269–P271 (المرحلة «أ»).
  لم يُبنَ: مطابقةُ صيغة الكلمة للفظ الصفّ (الوزن)، والمسارُ غيرُ الجذريّ، وحقولُ الموضع والعامل وتعدّدِ التقدير.
  بلا sorry ولا axiom ولا native_decide.
-/
import Nizam.Asas
import SLGE.Law
import SLGE.Bridge
import Jisr.Iqtiran
import Madlul.JadwalLuzumData
import Dal.Makharij
import Jisr.Utur

namespace Nizam
namespace Aqd

open SLGE.Law

/-! ## ١. نواةُ البتّات: ثلاثُ مبرهناتٍ عامّة -/

/-- الاقترانُ قناعًا: AND للقيود. -/
def iqtiranB (c : Nat) (qs : List Nat) : Nat := qs.foldl (· &&& ·) c

theorem iqtiranB_iff (m : Nat) : ∀ (qs : List Nat) (c : Nat),
    (iqtiranB c qs).testBit m = true ↔ c.testBit m = true ∧ ∀ q ∈ qs, q.testBit m = true
  | [], c => by simp [iqtiranB]
  | q :: qs, c => by
    simp only [iqtiranB, List.foldl_cons] at *
    rw [show qs.foldl (· &&& ·) (c &&& q) = iqtiranB (c &&& q) qs from rfl, iqtiranB_iff m qs, Nat.testBit_and,
      Bool.and_eq_true]
    simp only [List.mem_cons, forall_eq_or_imp]
    exact ⟨fun ⟨⟨a, b⟩, d⟩ => ⟨a, b, d⟩, fun ⟨a, b, d⟩ => ⟨⟨a, b⟩, d⟩⟩

/-- صفُّ شاهد: رمزُ الجذر، ومستوى ما يشهد له، وسطرُه في المودَع — فالشاهدُ لا يضيع في الناتج. -/
structure Shahid where
  jidhr : Nat
  madlul : Nat
  satr : Nat
  deriving DecidableEq, Repr

/-- تركيبُ الشواهد: OR لمستويات الصفوف التي جذرُها مرفوعٌ في F. -/
def tarkibShawahid (F : Nat) : List Shahid → Nat
  | [] => 0
  | e :: es => (if F.testBit e.jidhr then e.madlul else 0) ||| tarkibShawahid F es

theorem tarkib_iff (F m : Nat) : ∀ es : List Shahid,
    (tarkibShawahid F es).testBit m = true ↔ ∃ e ∈ es, F.testBit e.jidhr = true ∧ e.madlul.testBit m = true
  | [] => by simp [tarkibShawahid]
  | e :: es => by
    simp only [tarkibShawahid, Nat.testBit_or, Bool.or_eq_true, tarkib_iff F m es, List.mem_cons]
    by_cases hj : F.testBit e.jidhr = true
    · simp only [hj, ite_true]
      constructor
      · rintro (h | ⟨e', hm, h1, h2⟩)
        · exact ⟨e, Or.inl rfl, hj, h⟩
        · exact ⟨e', Or.inr hm, h1, h2⟩
      · rintro ⟨e', he | he, h1, h2⟩
        · subst he; exact Or.inl h2
        · exact Or.inr ⟨e', he, h1, h2⟩
    · simp only [hj, Bool.false_eq_true, ite_false, Nat.zero_testBit, false_or]
      constructor
      · rintro ⟨e', hm, h1, h2⟩; exact ⟨e', Or.inr hm, h1, h2⟩
      · rintro ⟨e', he | he, h1, h2⟩
        · subst he; exact absurd h1 hj
        · exact ⟨e', he, h1, h2⟩

theorem bit_wahid (r j : Nat) : (1 <<< r).testBit j = true ↔ j = r := by
  rw [Nat.shiftLeft_eq, Nat.one_mul, Nat.testBit_two_pow]; simp [eq_comm]

/-- رتبةُ الصيغة في قناعها: ماضٍ 0، أمر 1، مضارع 2. -/
def rutbaSigha : Jisr.Iqtiran.SighaFil → Nat
  | .madin => 0 | .amr => 1 | .mudari => 2

/-! ## ٢. العقد -/

/-- **العقدُ الواحد**: كلُّ طبقةٍ مواصفةٌ ومنفّذٌ ومساواتُهما. -/
structure Aqd where
  /-- قانونُ الدالّ (ابتداء/وصل/وقف). -/
  qanun : List Nat → Bool
  qanunB : List Nat → Bool
  qanun_sawa : ∀ x, qanunB x = qanun x
  /-- إسقاطُ الدالّ إلى رمز جذره. -/
  jidhr : List Nat → Option Nat
  jidhrB : List Nat → Option Nat
  jidhr_sawa : ∀ x, jidhrB x = jidhr x
  /-- حالُ الآخر (0..3). -/
  haal : List Nat → Option Nat
  haalB : List Nat → Option Nat
  haal_sawa : ∀ x, haalB x = haal x
  /-- مرشَّحو صيغة الفعل، ومنفّذُهم قناع. -/
  sigha : List Nat → List Jisr.Iqtiran.SighaFil
  sighaB : List Nat → Nat
  sigha_sawa : ∀ x s, (sighaB x).testBit (rutbaSigha s) = true ↔ s ∈ sigha x
  /-- شواهدُ الوضع بأسطرها، وقيودُ المدلول، وموانعُه (بيانات). -/
  shawahid : List Shahid
  quyud : List Nat → List Nat
  mani : List Nat → Nat

/-- **المواصفة**: الجذرُ r يشهد له بالمدلول m صفٌّ من الشواهد، واستوفى m قيودَ الدالّ كلَّها. -/
def Mashhud (A : Aqd) (x : List Nat) (r m : Nat) : Prop :=
  (∃ e ∈ A.shawahid, e.jidhr = r ∧ e.madlul.testBit m = true) ∧ ∀ q ∈ A.quyud x, q.testBit m = true

/-- **المواصفة**: مرخَّص — القانونُ يقبل الدالّ، ولا مانع، وله جذرٌ مشهودٌ له بالمدلول. -/
def Murakhkhas (A : Aqd) (x : List Nat) (m : Nat) : Prop :=
  A.qanun x = true ∧ (A.mani x).testBit m = false ∧ ∃ r, A.jidhr x = some r ∧ Mashhud A x r m

/-- **المواصفة**: ممتنع — القانونُ يردّ الدالّ، أو قناعُ الموانع يردّ المدلول. -/
def Mumtani (A : Aqd) (x : List Nat) (m : Nat) : Prop :=
  A.qanun x = false ∨ (A.mani x).testBit m = true

/-- **القراءةُ** التي يحملها الحكمُ المرخَّص: رمزُ الجذر، وحالُ الآخر، وقناعُ مرشَّحي الصيغة — كلُّها من المنفّذ البتّيّ.
    والحالُ والصيغةُ قراءةٌ محمولةٌ لا قيدٌ على الحكم: لا قيدَ بين الطبقات مبنيٌّ بعد. -/
structure Qiraa where
  jidhr : Nat
  haal : Option Nat
  sigha : Nat
  deriving DecidableEq, Repr

/-- **المواصفة**: القراءةُ مطابقةٌ للمواصفة — جذرُها جذرُ المواصفة، وحالُها حالُها، وقناعُ صيغتها مرشَّحوها بأعيانهم.
    (مطابقةُ المنفّذ للمواصفة، لا صحّةُ المواصفة لغةً: هذه في تعريفات العقد المعيَّن، كـ`Mashru`.) -/
def QiraaSahiha (A : Aqd) (x : List Nat) (q : Qiraa) : Prop :=
  A.jidhr x = some q.jidhr ∧ q.haal = A.haal x ∧ ∀ s, q.sigha.testBit (rutbaSigha s) = true ↔ s ∈ A.sigha x

/-- **المنفّذ**: مستوى المرخَّص من جذرٍ r بالبتّات وحدها — OR الشواهد ثمّ AND القيود. -/
def mustawa (A : Aqd) (x : List Nat) (r : Nat) : Nat :=
  iqtiranB (tarkibShawahid (1 <<< r) A.shawahid) (A.quyud x)

def sababQanun : String := "القانون يردّ الدالّ (ابتداء/وصل/وقف)"
def sababMani : String := "قناعُ الموانع يردّ المدلول"

/-- **المنفّذ**: الحكمُ الثلاثيّ؛ المرخَّصُ بقراءته، والممتنعُ باسم سببه. -/
def hukmB (A : Aqd) (x : List Nat) (m : Nat) : Hukm Qiraa :=
  if A.qanunB x = false then .mumtani sababQanun
  else if (A.mani x).testBit m then .mumtani sababMani
  else match A.jidhrB x with
    | some r => if (mustawa A x r).testBit m then .murakhkhas ⟨r, A.haalB x, A.sighaB x⟩ else .laHukm
    | none => .laHukm

theorem mustawa_iff (A : Aqd) (x : List Nat) (r m : Nat) : (mustawa A x r).testBit m = true ↔ Mashhud A x r m := by
  unfold mustawa Mashhud
  rw [iqtiranB_iff, tarkib_iff]
  simp only [bit_wahid]

/-- **المبرهنةُ الواحدة: الكلُّ مع الكلّ.** لكلّ عقدٍ ولكلّ دالٍّ ولكلّ مدلول: حكمُ المنفّذ البتّيّ هو حكمُ المواصفة بمراتبه
    الثلاث (سلامةً واكتمالًا معًا)، والقراءةُ التي يحملها المرخَّصُ مطابقةٌ للمواصفة في كلّ حقولها. -/
theorem kull_ma_kull (A : Aqd) (x : List Nat) (m : Nat) :
    ((∃ q, hukmB A x m = .murakhkhas q) ↔ Murakhkhas A x m) ∧
    ((∃ s, hukmB A x m = .mumtani s) ↔ Mumtani A x m) ∧
    (hukmB A x m = .laHukm ↔ ¬ Murakhkhas A x m ∧ ¬ Mumtani A x m) ∧
    (∀ q, hukmB A x m = .murakhkhas q → QiraaSahiha A x q) := by
  unfold hukmB Murakhkhas Mumtani QiraaSahiha
  rw [A.qanun_sawa x, A.jidhr_sawa x, A.haal_sawa x]
  cases hq : A.qanun x
  · simp
  · cases hn : (A.mani x).testBit m
    · cases hj : A.jidhr x with
      | none => simp
      | some r =>
        cases hp : (mustawa A x r).testBit m
        · have hs : ¬ Mashhud A x r m := fun h => by rw [(mustawa_iff A x r m).mpr h] at hp; cases hp
          simp [hs, hp]
        · have hs : Mashhud A x r m := (mustawa_iff A x r m).mp hp
          simp [hs, hp, A.sigha_sawa x]
    · simp

/-- **لا شاهدَ فلا حكم** (لكلّ عقد): دالٌّ يقبله القانونُ بلا مانعٍ، وجذرُه لا صفَّ له في الشواهد — حكمُه «لا حكم» في كلّ مدلول؛
    الغيابُ لا يصير امتناعًا. (من `kull_ma_kull` وحدها.) -/
theorem la_shahid_la_hukm (A : Aqd) (x : List Nat) (r : Nat) (hj : A.jidhr x = some r)
    (hs : ∀ e ∈ A.shawahid, e.jidhr ≠ r) (hq : A.qanun x = true) (m : Nat) (hn : (A.mani x).testBit m = false) :
    hukmB A x m = .laHukm := by
  apply (kull_ma_kull A x m).2.2.1.mpr
  refine ⟨?_, ?_⟩
  · rintro ⟨_, _, r', hr', ⟨e, he, h1, _⟩, _⟩
    rw [hj] at hr'
    cases hr'
    exact hs e he h1
  · rintro (h | h)
    · rw [hq] at h; cases h
    · rw [hn] at h; cases h

/-- **الممتنعُ باسم سببه** (لكلّ عقد): «القانون يردّ الدالّ» ⟺ القانونُ يردّه؛ و«قناعُ الموانع يردّ المدلول» ⟺ القانونُ يقبله
    والقناعُ يردّ المدلول. فالاسمُ المطبوع شاهدٌ على سببه لا سلسلةٌ حرّة. -/
theorem mumtani_asbab (A : Aqd) (x : List Nat) (m : Nat) :
    (hukmB A x m = .mumtani sababQanun ↔ A.qanun x = false) ∧
    (hukmB A x m = .mumtani sababMani ↔ A.qanun x = true ∧ (A.mani x).testBit m = true) := by
  have hne : sababMani ≠ sababQanun := by simp [sababMani, sababQanun]
  unfold hukmB
  rw [A.qanun_sawa x]
  cases hq : A.qanun x
  · simp [hne.symm]
  · cases hn : (A.mani x).testBit m
    · simp
      split
      · split <;> simp
      · simp
    · simp [hne]

/-! ## ٣. العقدُ على Mashru -/

/-- مدخلُ جدول القانون: [وزن:1][حالة تالية:7]. -/
def madkhal (q a : Nat) : Nat := (ω q a <<< 7) ||| δ q a

/-- جدولُ القانون: فهرسُه [حالة:7][رمز:7] (16384 مدخلًا). -/
def jadwalQanun : Array Nat := Array.ofFn (n := 128 * 128) fun i =>
  if i.val >>> 7 < 97 ∧ i.val &&& 127 < 117 then madkhal (i.val >>> 7) (i.val &&& 127) else 96

def khatwa (q a : Nat) : Nat := jadwalQanun[(q <<< 7) ||| a]!

/-- الفهرسُ ضمُّ حقلين يُفكّ بالإزاحة والقناع. -/
theorem fahras : ∀ q < 97, ∀ a < 117,
    (q <<< 7 ||| a) < 128 * 128 ∧ (q <<< 7 ||| a) >>> 7 = q ∧ (q <<< 7 ||| a) &&& 127 = a := by decide +kernel

/-- المدخلُ بايتٌ: الحالةُ التالية في البتّات السبعة الدنيا، والوزنُ في الثامن. -/
theorem madkhal_fakk : ∀ q < 97, ∀ a < 117,
    madkhal q a &&& 127 = δ q a ∧ madkhal q a >>> 7 = ω q a ∧ madkhal q a < 256 := by decide +kernel

theorem khatwa_qanun (q a : Nat) (hq : q < 97) (ha : a < 117) : khatwa q a &&& 127 = δ q a := by
  obtain ⟨hlt, h1, h2⟩ := fahras q hq a ha
  unfold khatwa jadwalQanun
  rw [getElem!_pos (Array.ofFn _) _ (by simpa using hlt), Array.getElem_ofFn]
  simp only [h1, h2, hq, ha, and_self, ite_true]
  exact (madkhal_fakk q hq a ha).1

def runB : Nat → List Nat → Nat
  | q, [] => q
  | q, a :: l => runB (khatwa q a &&& 127) l

/-- **التشغيلُ بالجدول هو القانونُ نفسُه** على كلّ سلسلةٍ من الرموز الـ117 تبدأ من حالةٍ حيّة. -/
theorem runB_run : ∀ (l : List Nat) (q : Nat), q < 97 → (∀ a ∈ l, a < 117) → runB q l = run q l := by
  intro l
  induction l with
  | nil => intro q _ _; rfl
  | cons a l ih =>
    intro q hq hl
    have ha := hl a (List.mem_cons_self ..)
    simp only [runB, run]
    rw [khatwa_qanun q a hq ha]
    exact ih _ (fin_close q hq a ha) (fun b hb => hl b (List.mem_cons_of_mem _ hb))

/-- رمزُ الجذر بحقولٍ من خمسة بتّات (السعةُ 32 ≥ 29). -/
def ramz32 (r : List Nat) : Nat := r.foldl (fun n c => n * 32 + c) 0

/-- رمزُ جذرٍ مكتوبٍ حروفًا، بفهارس `Dal.hawamil`. -/
def ramzNass (s : String) : Nat := ramz32 (s.toList.map fun ch => Dal.hawamil.idxOf ch)

/-- فكُّ رمز الجذر حقولًا: الإزاحةُ والقناع. -/
def fakkRamz (r : Nat) : List Nat := [r >>> 10, (r >>> 5) &&& 31, r &&& 31]

/-- **الرمزُ يُفكّ إلى أصله**: حقلا الخمسة البتّات الدنيان لا يتداخلان ما داما دون 32 (والحواملُ 29)، والأعلى بلا حدّ. -/
theorem fakk_ramz (a b c : Nat) (hb : b < 32) (hc : c < 32) : fakkRamz (ramz32 [a, b, c]) = [a, b, c] := by
  have h31 : ∀ n : Nat, n &&& 31 = n % 32 := fun n => Nat.and_two_pow_sub_one_eq_mod n 5
  simp only [fakkRamz, ramz32, List.foldl, h31, Nat.shiftRight_eq_div_pow, List.cons.injEq, and_true]
  omega

/-- حروفُ العلّة (`SLGE.Law.weak`: ا ي و) قناعًا على الحوامل. -/
def qinaIlla : Nat := (1 <<< 2) ||| (1 <<< 11) ||| (1 <<< 28)

theorem qina_illa : ∀ c < 116, qinaIlla.testBit (c >>> 2) = weak (c / 4) := by decide +kernel

/-- حواملُ نأيت (`SLGE.Wad.nayta`) قناعًا على الحوامل. -/
def naytaQina : Nat := SLGE.Wad.nayta.foldl (fun b c => b ||| (1 <<< c)) 0

theorem nayta_qina : ∀ c0 < 116, (naytaQina >>> (c0 >>> 2)) &&& 1 = (if SLGE.Wad.nayta.contains (c0 / 4) then 1 else 0) := by
  decide +kernel

/-- مواصفةُ الصيغة: مرشَّحو `Jisr.Iqtiran` بقيد افتتاح نأيت على الخانة الأولى. -/
def siyagh (x : List Nat) : List Jisr.Iqtiran.SighaFil :=
  match x with
  | c0 :: _ => if c0 < 116 then Jisr.Iqtiran.iqtiran Jisr.Iqtiran.sighaMurashshaha [Jisr.Iqtiran.qaydNaytaIftitah c0] else []
  | [] => []

/-- منفّذُ الصيغة: الماضي والأمرُ مرفوعان أبدًا، والمضارعُ ببتّ نأيت. -/
def siyaghB (x : List Nat) : Nat :=
  match x with
  | c0 :: _ => if c0 < 116 then 3 ||| (((naytaQina >>> (c0 >>> 2)) &&& 1) <<< 2) else 0
  | [] => 0

theorem siyagh_sawa (x : List Nat) (s : Jisr.Iqtiran.SighaFil) :
    (siyaghB x).testBit (rutbaSigha s) = true ↔ s ∈ siyagh x := by
  match x with
  | [] => simp [siyaghB, siyagh]
  | c0 :: _ =>
    unfold siyaghB siyagh
    by_cases hc : c0 < 116
    · simp only [hc, ite_true]
      rw [nayta_qina c0 hc]
      have key : ∀ b : Bool, ∀ s : Jisr.Iqtiran.SighaFil,
          (3 ||| ((if b then 1 else 0) <<< 2)).testBit (rutbaSigha s) = true ↔
            (match s with | .mudari => b | _ => true) = true := by
        intro b s; cases b <;> cases s <;> decide
      rw [key, Jisr.Iqtiran.iqtiran_iff]
      cases s <;> simp [Jisr.Iqtiran.sighaMurashshaha, Jisr.Iqtiran.qaydNaytaIftitah, Jisr.JisrDal.harf]
    · simp [hc]

/-- رمزٌ فوق الـ116 والحدّ يميت السلسلة أينما وقع. -/
theorem run_kabir : ∀ (l : List Nat) (q a : Nat), a ∈ l → 117 ≤ a → run q l = 96
  | [], _, _, h, _ => by simp at h
  | b :: l, q, a, h, ha => by
    simp only [run]
    rcases List.mem_cons.mp h with rfl | h
    · rw [show δ q a = 96 by simp [δ, ha]]; exact run_dead l
    · exact run_kabir l _ a h ha

/-- **المكوّنُ على الخلايا كما هي بجدول البتّات**: الحارسُ (كلُّ رمزٍ دون 117) ثمّ الجدول. -/
def kamaB (x : List Nat) : Bool := x.all (· < 117) && Fwaqf (runB 0 x)

/-- **والمكوّنُ بعد تسكين الآخر**: هو نفسُه على صورة الوقف. -/
def baadB (x : List Nat) : Bool := kamaB (waqfForm x)

/-- **`kamaB` مساوٍ لمواصفته لكلّ سلسلة** (`Fwaqf ∘ run 0`)؛ والقارئ يستدعيه في سطر العقد. -/
theorem kama_sawa (x : List Nat) : kamaB x = Fwaqf (run 0 x) := by
  unfold kamaB
  by_cases h : x.all (· < 117) = true
  · have hl : ∀ a ∈ x, a < 117 := fun a ha => by have := List.all_eq_true.mp h a ha; simpa using this
    simp only [h, Bool.true_and]
    rw [runB_run x 0 (by decide) hl]
  · obtain ⟨a, ha, hb⟩ : ∃ a ∈ x, ¬ a < 117 := by simpa [List.all_eq_true] using h
    simp only [Bool.not_eq_true] at h
    have h96 : Fwaqf (run 0 x) = false := by rw [run_kabir x 0 a ha (by omega)]; decide
    simp only [h, h96, Bool.false_and]

/-- **`baadB` مساوٍ لمواصفته لكلّ سلسلة** (`complete'`)؛ والقارئ يستدعيه في سطر العقد. -/
theorem baad_sawa (x : List Nat) : baadB x = complete' x := by
  unfold baadB
  rw [kama_sawa]
  unfold complete'
  rfl

/-- **إطارُ الدالّ هو تقاطعُ القانونين بعينه** (لكلّ سلسلة): `Jisr.Utur.dalOK` (الابتداء والوصل كما يُقرأ والوقف «المكتمل» —
    قراءةُ البنّاء لـ`SLGE/Necessity.lean` س25 في `Jisr/Utur.lean`) = ما يُقبل كما يُقرأ موقوفًا عليه (`Fwaqf ∘ run 0`) ∧ ما يكتمل
    بعد التسكين (`complete'`). -/
theorem dalOK_taqatu (x : List Nat) : Jisr.Utur.dalOK x = (Fwaqf (run 0 x) && complete' x) := by
  cases hc : (Fwaqf (run 0 x) && complete' x)
  · cases h : Jisr.Utur.dalOK x
    · rfl
    · have h1 := Jisr.Utur.dal_waqf_kama_yuqra x h
      have h2 := Jisr.Utur.dal_yastalzim_complete x h
      rw [h1, h2] at hc; cases hc
  · simp only [Bool.and_eq_true] at hc
    obtain ⟨hl, hcmp⟩ := hc
    have hr : run 0 x ≠ 96 := fun e => by rw [e] at hl; exact absurd hl (by decide)
    have hne : x ≠ [] := fun e => by subst e; exact absurd hl (by decide)
    have hib : Jisr.Utur.ibtidaDal x = true := by
      match x, hne, hr with
      | a :: l, _, hr' =>
        simp only [Jisr.Utur.ibtidaDal, bne_iff_ne, ne_eq]
        intro h0
        apply hr'
        simp only [run, h0]
        exact run_dead l
    simp only [Jisr.Utur.dalOK, Jisr.Utur.waslDal, Jisr.Utur.waqfDal, hib, hcmp, Bool.and_true, Bool.true_and,
      Bool.and_eq_true, Bool.not_eq_true', List.isEmpty_eq_false_iff, bne_iff_ne, ne_eq]
    exact ⟨hne, hr⟩

/-- **عقدُ Mashru** لنوع علاقةٍ n من `JadwalLuzum`. مواصفاتُه تعريفاتُ المشروع: القانونُ إطارُ الدالّ `Jisr.Utur.dalOK` (الابتداء والوصل
    كما يُقرأ والوقف «المكتمل»؛ قراءةُ البنّاء لـ Necessity س25، ومواصفةٌ هنا بقرار المالك 2026-10-20 00:23 الذي ينتظر تثبيتَه)، وهو بـ `dalOK_taqatu`
    القانونان معًا: `Fwaqf (run 0 x)` على الخلايا المعطاة و`complete'` (`SLGE.Bridge.DalLic`) بعد التسكين — ولا واحدَ منهما يكفي وحده
    (`wahid_la_yakfi`؛ وقولُ المالك في الجلسة: «ولا واحد يصلح وحده …»)؛
    والحرفُ والحالُ `Jisr.JisrDal.harf`/`hala`، وحروفُ العلّة `SLGE.Law.weak`، والصيغةُ `Jisr.Iqtiran`. -/
def Mashru (n : JadwalLuzum.Naw) : Aqd where
  qanun x := Jisr.Utur.dalOK x
  qanunB x := kamaB x && baadB x
  qanun_sawa x := by
    show (kamaB x && baadB x) = Jisr.Utur.dalOK x
    rw [kama_sawa, baad_sawa, dalOK_taqatu]
  jidhr x := if x.length = 3 ∧ x.all (fun c => c < 116 && !weak (Jisr.JisrDal.harf c)) then
    some (ramz32 (x.map Jisr.JisrDal.harf)) else none
  jidhrB x := if x.length = 3 ∧ x.all (fun c => c < 116 && !qinaIlla.testBit (c >>> 2)) then
    some (ramz32 (x.map (· >>> 2))) else none
  jidhr_sawa x := by
    have h1 : (fun c => decide (c < 116) && !qinaIlla.testBit (c >>> 2)) =
        (fun c => decide (c < 116) && !weak (Jisr.JisrDal.harf c)) := by
      funext c
      by_cases hc : c < 116
      · simp only [hc, decide_true, Bool.true_and, qina_illa c hc, Jisr.JisrDal.harf]
      · simp [hc]
    have h2 : (fun a : Nat => a >>> 2) = Jisr.JisrDal.harf := by
      funext a; rw [Nat.shiftRight_eq_div_pow]; rfl
    simp only [h1, h2]
  haal x := match x.getLast? with | some a => if a < 116 then some (Jisr.JisrDal.hala a) else none | none => none
  haalB x := match x.getLast? with | some a => if a < 116 then some (a &&& 3) else none | none => none
  haal_sawa x := by
    have : ∀ a : Nat, a &&& 3 = Jisr.JisrDal.hala a := fun a => Nat.and_two_pow_sub_one_eq_mod a 2
    simp only [this]
  sigha := siyagh
  sighaB := siyaghB
  sigha_sawa := siyagh_sawa
  shawahid := (JadwalLuzum.jadwal.filter (·.naw == n)).map fun s => ⟨ramzNass s.a, 1 <<< ramzNass s.b, s.satr⟩
  quyud _ := []
  mani _ := 0

/-- **حواملُ المسقَط سالمةٌ بشرط المالك**: ما أُسقط فحواملُه سالمةٌ بـ `SLGE.Law.SoundR` (دون 29، لا ا ي و)، ورمزُه رمزُ حروفه
    (`Jisr.JisrDal.harf`). لا يثبت أنّ المسقَطَ جذرٌ: المزيدُ والأدواتُ والضمائرُ تُسقَط كما هي. -/
theorem jidhr_salim (n : JadwalLuzum.Naw) (x : List Nat) (r : Nat) (h : (Mashru n).jidhr x = some r) :
    SoundR (x.map Jisr.JisrDal.harf) ∧ r = ramz32 (x.map Jisr.JisrDal.harf) := by
  simp only [Mashru] at h
  split at h
  · rename_i hc
    obtain ⟨_, hall⟩ := hc
    refine ⟨fun c hc' => ?_, (Option.some.inj h).symm⟩
    obtain ⟨a, ha, rfl⟩ := List.mem_map.mp hc'
    have := List.all_eq_true.mp hall a ha
    simp only [Bool.and_eq_true, decide_eq_true_eq, Bool.not_eq_true', weak, Jisr.JisrDal.harf,
      Bool.or_eq_false_iff, beq_eq_false_iff_ne] at this
    obtain ⟨h1, ⟨h2, h3⟩, h4⟩ := this
    exact ⟨by unfold Jisr.JisrDal.harf; omega, h2, h3, h4⟩
  · cases h

/-- **لا واحدَ من القانونين يكفي وحده** (شاهدان): «قَالْتُ» بخلاياها يردّها القانونُ على الخلايا (شاهدُ المالك
    `SLGE.Law.qaltu`) ويقبلها `complete'` بعد تسكين آخرها («قالْتْ»)؛ و«بَ» خانةً واحدة يقبلها الأوّل ويردّها `complete'`
    (`SLGE.Law.nec_second`)؛ والعقدُ بهما معًا (`dalOK`) يردّ الاثنتين. -/
theorem wahid_la_yakfi (n : JadwalLuzum.Naw) :
    (Fwaqf (run 0 [4*7+0, 4*2+3, 4*13+3, 4*18+1]) = false ∧ complete' [4*7+0, 4*2+3, 4*13+3, 4*18+1] = true ∧
      (Mashru n).qanun [4*7+0, 4*2+3, 4*13+3, 4*18+1] = false) ∧
    (Fwaqf (run 0 [4*26+0]) = true ∧ complete' [4*26+0] = false ∧ (Mashru n).qanun [4*26+0] = false) := by
  cases n <;> decide +kernel

/-- **مقدارُ الفرق على الخانة والخانتين** (على الشاهد، بـ decide على النطاق كلّه): من 116 خانةً 84 يقبلها القانونُ على الخلايا
    ويردّها `complete'`، ولا عكس؛ ومن 13,456 زوجًا 84 يقبلها `complete'` ويردّها الأوّل، ولا عكس. والعقدُ بهما معًا يقبل من الخانة
    الواحدة صفرًا ومن الأزواج 9,436 (= ما يقبله الأوّل؛ وهو عددُ `Jisr.Utur.itar_dal_anmat_2`). -/
theorem farq_dalLic :
    ((List.range 116).filter fun a => Fwaqf (run 0 [a]) && !complete' [a]).length = 84 ∧
    ((List.range 116).filter fun a => complete' [a] && !Fwaqf (run 0 [a])).length = 0 ∧
    (((List.range 116).flatMap fun a => (List.range 116).map fun b => [a, b]).filter
      fun l => complete' l && !Fwaqf (run 0 l)).length = 84 ∧
    (((List.range 116).flatMap fun a => (List.range 116).map fun b => [a, b]).filter
      fun l => Fwaqf (run 0 l) && !complete' l).length = 0 ∧
    ((List.range 116).filter fun a => Jisr.Utur.dalOK [a]).length = 0 ∧
    (((List.range 116).flatMap fun a => (List.range 116).map fun b => [a, b]).filter Jisr.Utur.dalOK).length = 9436 := by
  decide +kernel

/-- قراءةُ حالٍ إعرابًا بتقابل المالك `SLGE.Bridge.irabState` (قطر الندى L77–78). -/
def irabMin (h : Nat) : Option SLGE.Wad.Irab := SLGE.Wad.allIrab.find? fun r => SLGE.Bridge.irabState r == h

theorem irabMin_irabState : ∀ r : SLGE.Wad.Irab, irabMin (SLGE.Bridge.irabState r) = some r := by
  intro r; cases r <;> rfl

/-- **مرشَّحُ إعراب الآخر**: الحركةُ وحدها (فتحة/ضمّة/كسرة) تُقرأ إعرابًا مرشَّحًا؛ والسكونُ في الآخر «لا حكم» — قد يكون وقفًا أو
    جزمًا أو بناءً، أو حرفَ مدٍّ أو نونَ تنوينٍ أو هاءَ وقف؛ والجزمُ للفعل وحده (`SLGE/Wad.lean`). -/
def irabMurashshah (h : Nat) : Option SLGE.Wad.Irab := if h < 3 then irabMin h else none

/-- السكونُ لا يُقرأ إعرابًا، ولا يُرشَّح الجزمُ أبدًا. -/
theorem irabMurashshah_la_jazm : irabMurashshah 3 = none ∧ ∀ h, irabMurashshah h ≠ some .jazm := by
  refine ⟨rfl, fun h => ?_⟩
  unfold irabMurashshah
  split
  · rename_i hh
    rcases (by omega : h = 0 ∨ h = 1 ∨ h = 2) with rfl | rfl | rfl <;> decide
  · simp

/-! ## ٤. شواهدُ على المودَع: تُبرهن على المواصفة وحدها، و`kull_ma_kull` تنقلها إلى المنفّذ بلا برهانٍ جديد -/

/-- كَتَبَ: ك/فتحة(32) ت/فتحة(72) ب/فتحة(104). -/
def kataba : List Nat := [32, 72, 104]

/-- **كَتَبَ ← «علم» ترادفًا مرخَّص** على مستوى المادّة (لسان العرب س24030، لفظُ الصفّ «وءكتبه»)، والحكمُ يحمل قراءتَها:
    جذرُها «كتب»، وحالُ آخرها فتحة، ومرشَّحو صيغتها الماضي والأمر. -/
theorem kataba_ilm_taraduf :
    ∃ q, hukmB (Mashru .taraduf) kataba (ramzNass "علم") = .murakhkhas q ∧ q.jidhr = ramzNass "كتب" ∧
      q.haal = some 0 ∧ ∀ s, q.sigha.testBit (rutbaSigha s) = true ↔ s ∈ [.madin, .amr] := by
  have K := kull_ma_kull (Mashru .taraduf) kataba (ramzNass "علم")
  have spec : Murakhkhas (Mashru .taraduf) kataba (ramzNass "علم") :=
    ⟨by decide +kernel, by decide, ramzNass "كتب", by decide +kernel,
      ⟨⟨ramzNass "كتب", 1 <<< ramzNass "علم", 24030⟩, by decide +kernel, rfl, by decide +kernel⟩,
      by simp [Mashru]⟩
  obtain ⟨q, hq⟩ := K.1.mpr spec
  obtain ⟨hj, hh, hs⟩ := K.2.2.2 q hq
  refine ⟨q, hq, ?_, ?_, fun s => ?_⟩
  · have : (Mashru .taraduf).jidhr kataba = some (ramzNass "كتب") := by decide +kernel
    rw [this] at hj; exact (Option.some.inj hj).symm
  · rw [hh]; decide +kernel
  · rw [hs s]
    have : (Mashru .taraduf).sigha kataba = [.madin, .amr] := by decide +kernel
    rw [this]

/-- **كَتَبَ لزومًا «لا حكم» في كلّ مدلول**: لا صفَّ لزومٍ في مادّة جذرها، فالغيابُ لا يصير امتناعًا (`la_shahid_la_hukm`). -/
theorem kataba_luzum_la_hukm (m : Nat) : hukmB (Mashru .luzum) kataba m = .laHukm :=
  la_shahid_la_hukm _ _ (ramzNass "كتب") (by decide +kernel) (by decide +kernel) (by decide +kernel) m
    (Nat.zero_testBit m)

/-- **«قَالْتُ» يردّها القانون**: ممتنعةٌ بسببها المسمّى («القانون يردّ الدالّ») بأيّ مدلولٍ في كلّ عقدٍ `Mashru n`. -/
theorem qaltu_mumtani (n : JadwalLuzum.Naw) (m : Nat) :
    hukmB (Mashru n) [4*7+0, 4*2+3, 4*13+3, 4*18+1] m = .mumtani sababQanun :=
  (mumtani_asbab (Mashru n) _ m).1.mpr (wahid_la_yakfi n).1.2.2

/-- **«قَالَ» لا جذرَ له في العقد**: حاملُه الثاني ألفٌ (حرفُ علّة) فلا إسقاطَ، والقانونُ يقبله — فحكمُه «لا حكم» بأيّ مدلولٍ في
    كلّ عقدٍ `Mashru n`، لا جذرٌ خاطئ ولا امتناع. -/
theorem qala_la_hukm (n : JadwalLuzum.Naw) (m : Nat) : hukmB (Mashru n) [4*7+0, 4*2+3, 4*13+0] m = .laHukm := by
  apply (kull_ma_kull (Mashru n) _ m).2.2.1.mpr
  have hj : (Mashru n).jidhr [4*7+0, 4*2+3, 4*13+0] = none := by cases n <;> decide +kernel
  refine ⟨?_, ?_⟩
  · rintro ⟨_, _, r, hr, _⟩; rw [hj] at hr; cases hr
  · rintro (h | h)
    · revert h; cases n <;> decide +kernel
    · simp [Mashru] at h

/-- **الصيغة**: كَتَبَ (أوّلُها ك، خارجَ نأيت) ماضٍ أو أمر؛ يَكْتُبُ (أوّلُها ي) الثلاثة — كشاهدَي `Jisr.Iqtiran.shahid_sigha`. -/
theorem shawahid_sigha :
    (Mashru .taraduf).sigha kataba = [.madin, .amr] ∧
    (Mashru .taraduf).sigha [4*11+0, 4*8+3, 4*18+1, 4*26+1] = [.madin, .amr, .mudari] := by
  decide +kernel

/-- **حالُ الآخر** في كَتَبَ فتحة (0)، ومرشَّحُها إعرابًا النصب إن كان معربًا — والإعرابُ والبناءُ من الباب: لا حكم هنا. -/
theorem kataba_haal : (Mashru .taraduf).haal kataba = some 0 ∧ irabMurashshah 0 = some .nasb := by decide +kernel

end Aqd
end Nizam
