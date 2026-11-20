import A116.Qufl
import A116.NizamTree
import A116.Unicode
import A116.Certificate
import A116.Dal

/-!
# صيغةُ البرهان: من البتّ إلى الدالّ المقفول — ونقدُ «SlgeComplete.lean» صوريًّا (ADR ٦٤)

أرفق المالك (2026-10-15) ملفًّا يُدّعى فيه «برهانٌ كاملٌ لـSLGE، 100٪، Zero-Sorry» يحوّل المتتاليات الثنائية إلى لغةٍ
طبيعيّة. طلب النقدَ وصيغةَ برهانٍ وفق أفضل الممارسات الرياضيّة، مبنيّةً على ما في المستودع.

## الممارساتُ المتّبعة هنا

1. **الدعوى خاصّيّةٌ لا مُحقِّق.** لا تُكتب دالّةٌ بوليانيّة تعيد شروطَ النتيجة ثمّ «يُبرهَن» أنّها تعيدها؛ تُكتب الدعوى
   على تعريفاتٍ مستقلّةٍ عنها (الخانات، الترخيص، العدد).
2. **الجامعُ المانع بـ«⟺»** لا بالسلامة وحدَها: كلُّ صفٍّ في الجدول مرخَّص، وكلُّ مرخَّصٍ صفّ.
3. **«فريد» = تباين** (`injective`) مبرهَن، لا حقلٌ اسمُه `unique_n`.
4. **عدمُ الفراغ**: شاهدٌ يُقبل وشاهدٌ يُرفض لكلّ مُرخِّص، وإلّا فالقانونُ قد يكون «صادقًا» على لا شيء.
5. **الحدُّ مسمًّى**: ما لا يبلغه البرهانُ مبرهنةٌ سالبة (لا دالّة…)، لا سكوت.
6. **السندُ مرسًى**: كلُّ بندٍ في الصيغة الجامعة مبرهنةٌ قائمةٌ باسمها في وحدتها؛ هذه الوحدةُ تجمع ولا تعيد البرهان.

## الجزء أ — النقد (`A116.Sigha.Naqd`)

تعريفاتُ الملفّ المرفق بأعيانها، و`integrated_slge_safety` مبرهنةً بلا `aesop` (الأصلُ لا يُبنى: `aesop` غيرُ موجودٍ
في Lean الأساسيّ، و`simp` لا يتقدّم في السطر قبله — طُبع ذلك في الجلسة). ثمّ ما تقوله المبرهنةُ فعلًا: لا شيء عن اللغة.
-/

namespace A116.Sigha

namespace Naqd

/-! ### تعريفاتُ الملفّ المرفق كما كُتبت (أُضيف `DecidableEq` للفحص وحدَه) -/

structure PhoneticNode where
  id : Nat
  carrier : Nat
  state : Nat
  position : Nat
  deriving DecidableEq, Repr

inductive SyllablePattern
  | CV | CVV | CVC | CVVC
  deriving DecidableEq, Repr

structure SyllableUnit where
  pattern : SyllablePattern
  unique_id : Nat
  is_valid : Bool
  deriving DecidableEq, Repr

inductive RootGeometry
  | Tri (c1 c2 c3 : PhoneticNode)
  | Quad (c1 c2 c3 c4 : PhoneticNode)
  | Quint (c1 c2 c3 c4 c5 : PhoneticNode)
  deriving DecidableEq, Repr

structure VerbSystem where
  root : RootGeometry
  is_mudari : Bool
  is_amr : Bool
  is_majhool : Bool
  is_mutadi : Bool
  unique_n : Nat
  deriving DecidableEq, Repr

inductive SyntacticStructure
  | NominalSentence | VerbalSentence | SemiSentence
  deriving DecidableEq, Repr

structure SyntacticSlge where
  kind : SyntacticStructure
  unique_n : Nat
  lean_role : String
  deriving DecidableEq, Repr

def verify_integrated_slge (syl : SyllableUnit) (vs : VerbSystem) (syn : SyntacticSlge) : Bool :=
  if syl.unique_id == 0 || vs.unique_n == 0 || syn.unique_n == 0 then false
  else
    if syl.unique_id <= 116 then
      match vs.root with
      | RootGeometry.Tri _ _ _ => true
      | RootGeometry.Quad _ _ _ _ => true
      | RootGeometry.Quint _ _ _ _ _ => true
    else false

/-- **ن١ — المُحقِّقُ ثلاثةُ أعدادٍ لا غير.** فرعُ الجذر يعيد `true` في الحالات الثلاث، فالمُحقِّقُ يساوي حدودًا
عدديّةً على ثلاثة حقول، ولا يقرأ النمطَ ولا الجذرَ ولا الأعلامَ ولا نوعَ الجملة ولا الدور. -/
theorem verify_eq (syl : SyllableUnit) (vs : VerbSystem) (syn : SyntacticSlge) :
    verify_integrated_slge syl vs syn =
      (syl.unique_id != 0 && vs.unique_n != 0 && syn.unique_n != 0 && decide (syl.unique_id ≤ 116)) := by
  unfold verify_integrated_slge
  cases vs.root <;>
  by_cases h1 : syl.unique_id = 0 <;> by_cases h2 : vs.unique_n = 0 <;>
  by_cases h3 : syn.unique_n = 0 <;> by_cases h4 : syl.unique_id ≤ 116 <;> simp [*]

/-- **ن٢ — «مبرهنة الاستنفاد التوافقي الحتمي»** صادقة، ببرهانٍ يُبنى (بلا `aesop`). وهي إعادةُ تعريف المُحقِّق. -/
theorem integrated_slge_safety (syl : SyllableUnit) (vs : VerbSystem) (syn : SyntacticSlge) :
    verify_integrated_slge syl vs syn = true →
    (syl.unique_id > 0 ∧ syl.unique_id ≤ 116 ∧ vs.unique_n > 0 ∧ syn.unique_n > 0) := by
  rw [verify_eq]
  simp only [Bool.and_eq_true, bne_iff_ne, ne_eq, decide_eq_true_eq]
  omega

/-- **ن٣ — لا يقرأ المُحقِّقُ شيئًا غير الأعداد الثلاثة**: بنيتان تتّفقان فيها يتّفق حكمُهما، مهما اختلف الجذرُ
والنمطُ والأعلامُ ونوعُ الجملة. -/
theorem verify_ignores_structure (syl syl' : SyllableUnit) (vs vs' : VerbSystem) (syn syn' : SyntacticSlge)
    (h1 : syl.unique_id = syl'.unique_id) (h2 : vs.unique_n = vs'.unique_n) (h3 : syn.unique_n = syn'.unique_n) :
    verify_integrated_slge syl vs syn = verify_integrated_slge syl' vs' syn' := by
  rw [verify_eq, verify_eq, h1, h2, h3]

/-- بنيةٌ متناقضة: مضارعٌ وأمرٌ ومجهولٌ معًا، على جذرٍ خماسيٍّ من أصفار، في «جملةٍ» دورُها نصٌّ فارغ. -/
def zero : PhoneticNode := ⟨0, 0, 0, 0⟩
def garbageVerb : VerbSystem :=
  ⟨.Quint zero zero zero zero zero, true, true, true, true, 1⟩
def garbageSyl : SyllableUnit := ⟨.CV, 1, false⟩
def garbageSyn : SyntacticSlge := ⟨.SemiSentence, 1, ""⟩

/-- **ن٤ — يقبل المتناقض**: المُحقِّقُ يقبل البنيةَ أعلاه، و`is_valid = false` لا يُقرأ. -/
theorem accepts_garbage : verify_integrated_slge garbageSyl garbageVerb garbageSyn = true := by decide

/-- **ن٥ — يقبل فعلًا خماسيًّا**، والمستودعُ يبرهن أنّ الخماسيّ جامدٌ لا فعلَ له (`RootGrade.khumasi_jamid`،
الكتاب) وأنّ درجةَ الأصول المرخَّصة ثلاثٌ أو أربع (`RootGrade.only_tri_and_quad`). -/
theorem quint_verb_contradicts_repo :
    verify_integrated_slge garbageSyl garbageVerb garbageSyn = true ∧
    RootGrade.sinf 5 = .jamid ∧ RootGrade.hasFil 5 = false :=
  ⟨accepts_garbage, RootGrade.khumasi_jamid⟩

/-- **ن٦ — `unique_n` ليس فريدًا**: بنيتا فعلٍ مختلفتان بالعدد نفسِه، والمُحقِّقُ يقبلهما معًا. -/
theorem unique_n_not_injective :
    ∃ v w : VerbSystem, v ≠ w ∧ v.unique_n = w.unique_n ∧
      verify_integrated_slge garbageSyl v garbageSyn = true ∧
      verify_integrated_slge garbageSyl w garbageSyn = true :=
  ⟨garbageVerb, { garbageVerb with is_amr := false }, by decide, rfl, by decide, by decide⟩

/-- **ن٧ — أنماطُ المقاطع ناقصة**: الملفُّ يعرف أربعة (CV، CVV، CVC، CVVC)، والوقفُ في المستودع يرخّص CVCC (عَصْرْ)
وCVVCC (تَامّْ) — `Hadd.asr_tamm_pause` — وجدولُ الوقف يزيد على جدول الوصل بأطرافه (`ExhaustPause.pause_adds`). -/
theorem patterns_missing :
    (Hadd.strictPauseB Hadd.asrPause = true ∧ Hadd.strictPauseB Hadd.tammPause = true) ∧
    (∀ k, (ExhaustPause.pauseTable k).length = (Exhaust.table k).length + 3 * 4 ^ k) :=
  ⟨⟨Hadd.asr_tamm_pause.2.1, Hadd.asr_tamm_pause.2.2.2⟩, ExhaustPause.pause_adds⟩

end Naqd

/-! ## الجزء ب — الصيغة: كلُّ بندٍ في الملفّ المرفق بدعواه الصحيحة، مبرهنةً من المستودع

| بندُ المرفق | الدعوى الصحيحة | السند |
|---|---|---|
| «تدفّق الخلايا الثنائية» | UTF-8 يُقرأ بما كُتب بعينه لكلّ نقطةٍ في يونيكود | `Unicode.decode_encode` |
| «الـ116 الأساسية» | 116 خانة، منها 113 مرخَّصة | `cells_length`، `Alif.licensable_length` |
| «المقاطع CV…» | جدولُ كلّ درجةٍ وصلًا ووقفًا هو المرخَّصُ بقيد الحدّ لا غير (⟺) | `Exhaust.table_iff_licensed`، `ExhaustPause.pauseTable_iff_licensed` |
| «Unique N» | عددُ الشهادة متباينٌ على المجال ويُستردّ منه الكلمة؛ وعددُ الجذر متباين | `Certificate.certNumber_injective`، `certNumber_decode`، `RootGrade.num_inj` |
| «ثلاثي، رباعي، خماسي» | درجاتُ الأصول المرخَّصة ثلاثٌ وأربع؛ الخماسيُّ جامد | `RootGrade.only_tri_and_quad`، `khumasi_jamid` |
| «المضارع والأمر والزمن» | الاشتقاقُ والصرفُ مقفولان على كلّ جذرٍ بلا ألف وعلى الرباعيّ | `Qufl.dal_locked` |
| «الأواني النحوية» | ترخيصُ الشجرة ترخيصُ سطر أوراقها (`NizamLine.strictLineB`)، فلا يغيّره التجميع | `NizamTree.tree_eq_line`، `regroup_invariant` |
| «لغة طبيعية 100٪» | **حدٌّ مبرهَن**: لا دالّةَ في الخانات تردّ «قَالَ» إلى جذره (قول/قيل) — الدلالةُ وراء جسر | `Dal.no_cell_function_recovers_root` |
-/

open A116.Hadd in
/-- **الصيغةُ الجامعة.** كلُّ بندٍ دعوى مستقلّةٌ عن أيّ مُحقِّق، ومبرهنةٌ قائمةٌ باسمها في وحدتها. -/
theorem sigha :
    -- (١) البتّ ← يونيكود: قراءةٌ تعيد الكتابةَ وما بعدها
    (∀ c, c < 0x110000 → ∀ rest, Unicode.utf8Decode (Unicode.utf8Encode c ++ rest) = some (c, rest)) ∧
    -- (٢) الشبكة: 116 خانة، والمرخَّص 113
    (cells.length = 116 ∧ Alif.licensable.length = 113) ∧
    -- (٣) المقاطع: الجامعُ المانع لكلّ درجةٍ وصلًا ووقفًا
    (∀ k ss, ss ∈ Exhaust.table k ↔ ∃ w : List Cell, w ≠ [] ∧ isFarq w = false ∧ strictB w = true ∧
        Stages.parse (kindOf w) = some (.none, ss) ∧ ss.length = k + 1) ∧
    (∀ k ss, ss ∈ ExhaustPause.pauseTable k ↔ ∃ w : List Cell, w ≠ [] ∧ strictPauseB w = true ∧
        Stages.parse (kindOf w) = some (.none, ss) ∧ ss.length = k + 1) ∧
    -- (٤) العدد: فريدٌ على المجال ويُستردّ منه الشيء؛ وعددُ الجذر فريد
    (∀ {α : Type} [DecidableEq α] (D : List α) (A : α → List Cell) (x y : α), x ∈ D → y ∈ D →
        Certificate.certNumber D A x = Certificate.certNumber D A y → x = y) ∧
    (∀ {α : Type} [DecidableEq α] (D : List α) (A : α → List Cell) (x : α), x ∈ D →
        Fiber.decode D A (A x, Fiber.rank D A x) = some x) ∧
    (∀ r s : List (Fin 28), r.length = s.length → RootGrade.num r = RootGrade.num s → r = s) ∧
    -- (٥) الأصول: ثلاثةٌ أو أربعة؛ والخماسيُّ جامد
    (∀ L n, RootGrade.RootMurakhkhas L n → n ∈ [3, 4]) ∧
    (RootGrade.sinf 5 = .jamid ∧ RootGrade.hasFil 5 = false) ∧
    -- (٦) الدالُّ مقفول: الستُّ قائمة، والاشتقاقُ والصرفُ ممتدّان، والدلالةُ وراء الجسر
    ((∀ d w, w ≠ .dalala → (Qufl.locked d w).qaim = true) ∧
      (∀ d, Qufl.IshtiqaqLocked d ∧ Qufl.SarfLocked d) ∧
      (∀ d, Qufl.locked d .dalala = .muallaq "DALALA_AT_DAL_MADLUL_BRIDGE") ∧
      (∀ k, ¬ Exhaust.Murakhkhas Qufl.locked (k + 2))) ∧
    -- (٧) التركيب: الشجرةُ سطرُ أوراقها، والتجميعُ لا يغيّر الترخيص
    (∀ t : NizamTree.Tree (List Cell), NizamTree.strictTreeB t = NizamLine.strictLineB (NizamTree.yieldT t)) ∧
    -- (٨) الحدّ: الخاناتُ وحدَها لا تردّ قَالَ إلى جذره
    (¬ ∃ f : List Cell → Wazn.Root 3, f (Dal.qala Dal.qwl) = Dal.qwl ∧ f (Dal.qala Dal.qyl) = Dal.qyl) :=
  ⟨fun c hc rest => Unicode.decode_encode c hc rest,
   ⟨cells_length, Alif.licensable_length⟩,
   Exhaust.table_iff_licensed,
   ExhaustPause.pauseTable_iff_licensed,
   fun _ _ _ _ hx hy h => Certificate.certNumber_injective hx hy h,
   fun _ _ _ hx => Certificate.certNumber_decode hx,
   RootGrade.num_inj,
   RootGrade.only_tri_and_quad,
   RootGrade.khumasi_jamid,
   Qufl.dal_locked,
   NizamTree.tree_eq_line,
   Dal.no_cell_function_recovers_root⟩

/-! ## الجزء ج — عدمُ الفراغ: لكلّ مُرخِّصٍ في الصيغة شاهدٌ يُقبل وشاهدٌ يُرفض -/

open A116.Hadd in
/-- قيدُ الحدّ يقبل قُلْتُ وحَاجَّ ويرفض قَالْتُ (والثلاثيُّ وحدَه يقبلها)؛ والوقفُ يقبل عَصْرْ وتَامّْ والوصلُ يرفضهما؛
والقفلُ يبلغ «قَالَ» من قول — فلا بندَ في الصيغة صادقٌ على لا شيء. -/
theorem sigha_not_vacuous :
    (strictB qultu = true ∧ strictB hajjaCells = true) ∧
    (Ternary.continueB (kindOf qaaltu) = true ∧ strictB qaaltu = false) ∧
    (strictB asrPause = false ∧ strictPauseB asrPause = true ∧
      strictB tammPause = false ∧ strictPauseB tammPause = true) ∧
    (strictB (Wazn.fillC (Tasrif.madi (Tasrif.sifa (Tasrif.r3 'ق' 'و' 'ل')) .fatha .fatha) (Tasrif.r3 'ق' 'و' 'ل'))
      = true) :=
  ⟨⟨qultu_strict, hajja_strict⟩, hadd_debt_closed, asr_tamm_pause,
   (Qufl.locked_beyond_sahih (Tasrif.r3 'ق' 'و' 'ل') (by simp [Qufl.shawahid])).1⟩

end A116.Sigha
