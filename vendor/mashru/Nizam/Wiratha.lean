import Aql.Qaida
import Nizam.WahdatJadwal
import SLGE.Root
import SLGE.Syllable

/-!
# الترخيصُ المتدرّج لكلّ ملفّ Lean، ووراثةُ جيناته الحسابيّة

قولُ المالك في الجلسة (2026-11-01، 19:11 بتوقيت عمّان):
«الخل ان كل module يجب ان يكون بالترخيص الجبري المتدرج فكل module يخضع لقانون الوراثة والتوريث ويدخل في ال slot machine  وهو حامل جيناته الحسابية»
ثمّ اختار من سؤالين متعدّدَي الخيارات نصُّ خياراتهما من البنّاء «كلُّ ملفّ Lean في المشروع» معنًى لـ module،
و«بعد الفرع الحاليّ في طلبٍ مستقلّ (موصى به)» ترتيبًا. ووصفُ الخيار الأوّل:
«لكلّ ملفٍّ رتبة، ولا يستورد إلّا ما دونها، وجيناتُه أعدادُه؛ وأكثرُ الملفّات ليس فيها آلة»
والخيارُ الموصى به كان «كلُّ آلةٍ في السلّم (موصى به)». ثمّ رسالتُه 20:05 (في `hawkama/الوراثة_الصنفية.md`
§١ بنصّها): «… يجب ان يرث كل lean ما ترخص قبله وكل اختبار ما قبله»؛ ووراثةُ الاختبارات منها لم تُبنَ (§٥ أ(5)).
ثمّ ردُّه 20:25 على مسوّدة التصميم: «Option a»، وقراءتُه §٥ أ من التصميم (الملفّات أوّلًا) قراءةُ البنّاء.

**البناء** (تعيينُ البنّاء، ينتظر إمضاءك):
- الملفّاتُ وحداتُ حزمة lake: مكتباتُ `lakefile.toml` الثماني بأنماطها، وجذورُ تنفيذيّاته التسعة؛ وملفّاتُها في تسع مجلّدات و`Nabt.lean`. وخارجها
  `Audit.lean` و`AuditNabt.lean` وملفّاتُ `tahaqquq` الأربعة. وتضييقُ «كلُّ ملفّ Lean في المشروع» إلى وحدات الحزمة قراءةُ البنّاء. والجدولُ مولَّدٌ من رؤوسها (`Nizam/WahdatJadwal.lean`)، ويطابقه محلّلُ رؤوس Lean نفسُه (`tahaqquq/test_wiratha.py`).
- كلُّ ملفٍّ يستورد من المشروع شيئًا قانونٌ في قاعدةٍ من `Aql/Qaida.lean`: مقدّماتُه ما يستورده من المشروع، ونتيجتُه هو. وما لا يستورد من المشروع
  شيئًا أصلٌ بالتعريف (`aslB`)، وليس قانونًا.
- رتبةُ الملفّ درجةُ اشتقاقه (`rutba_daraja`)، فالقاعدةُ متدرّجة (`mutadarrija`)، وما رتبتُه صفرٌ لا يُرخَّص إلّا أصلًا (`rutba_sifr_asl` من `Aql/Qaida.lean`).
- ترتيبُ البناء سلسلةٌ يقبلها فاحصُ القاعدة نفسُه (`Qaida.fahs`) فيُثبت كلَّ ملفّ (`bina_maqbul`)، فكلُّ ملفٍّ مرخَّص على أصولها
  (`kull_wahda_murakhkhasa`) — على هذا الجدول، ويصدق على كلّ جدولِ استيرادٍ بلا دَور.
- وما لا يرث شيئًا قائمةٌ مسمّاة (`bilaWirth`، 78: 53 ومعها جذورُ A116 الخمسةُ والعشرون، 2026-11-20)، تطابقها رتبةُ الصفر على هذا الجدول (`bilaWirth_iff`). وملفٌّ جديدٌ يُعاد له توليدُ الجدول (يفحصه ١ و٢
  في الاختبار)، ثمّ لا يُبنى `bilaWirth_iff` إن لم يستورد من المشروع شيئًا حتى يُضاف اسمُه.
- **الأصلُ قرارُ المالك، ولم يُبنَ:** الأصلُ في `bina_maqbul` و`kull_wahda_murakhkhasa` ما رتبتُه صفرٌ كلُّه (`aslB`، بالتعريف)، ومنه ما تعدّه الوثيقةُ
  غيرَ أصل (`Jisr.BabFa` …). والمبنيُّ لقراره `rutba_sifr` (على هذا الجدول، لأنّ فرضَها `mutadarrija`): أيًّا كانت الأصولُ ‎`a`‎، ما رتبتُه صفرٌ لا يُرخَّص إلّا منها؛ فما يعدّه يتيمًا لا يُرخَّص حتى
  يُوصل بأبيه.
- **الجيناتُ الحسابيّة** (قراءةُ البنّاء): لكلّ ملفٍّ حساباتُه الصنفيّة (`SLGE.Hisab`): اسمُ كلٍّ، وعددُ أصنافه، وثابتُه (`jinatKhassa`). وجيناتُه كلُّها
  الخاصّةُ مع جينات ما يستورده (`jinat`)، فكلُّ ملفٍّ يحمل جيناتِ ما يستورده (`jinat_tuwarrath`، و`jinatKull_tuwarrath` على هذا الجدول). والاسمُ نصُّ
  المعرِّف كما كُتب، والأعدادُ من الثابت الذي يُحلّ إليه (`jin!`)؛ وأنّ `jinatKhassa` هي حساباتُ كلّ وحدةٍ في البيئة بعينها، بأسمائها الكاملة، يفحصه
  `tahaqquq/test_wiratha.py` (٣) على الوحدات التي يستوردها (273، بلا جذور التنفيذيّات).

**حدُّه:** «يدخل في ال slot machine» هنا أنّ ترتيبَ البناء سلسلةٌ يقبلها فاحصُ المحرّك (`Qaida.fahs`)، لا آلةً من `SLGE.Machine`. والترخيصُ صياغةُ ترتيب
البناء في قاعدة المحرّك: يصدق على كلّ جدولِ استيرادٍ بلا دَور مع هذه الأصول، وLean يمنع الدَّور؛ فليس شاهدًا على محتوى الملفّات. والوراثةُ هنا
وراثةُ الاستيراد والجينات، لا اشتقاقُ حساب آلةٍ من حساب أبيها (§٥ ب من التصميم، لم يُبنَ). والجدولُ استيرادُ الرؤوس، لا ما يستعمله الملفّ فعلًا.
-/

namespace Nizam
namespace Wiratha
open Qaida WahdatJadwal

/-- عددُ الملفّات. -/
def N : Nat := wahdat.length

/-- اسمُ وحدة الملفّ بموضعه. -/
def ism (i : Nat) : String := (wahdat.getD i ("", [])).1

/-- ما يستورده الملفّ من المشروع، بمواضعه. -/
def istirad (i : Nat) : List Nat := (wahdat.getD i ("", [])).2

/-- رتبةُ الملفّ. -/
def rutba (i : Nat) : Nat := rutbaJadwal.getD i 0

/-- قانونُ كلّ ملفٍّ يستورد من المشروع: مقدّماتُه ما يستورده، ونتيجتُه هو. -/
def qawanin : List (Qanun Nat) :=
  (List.range N).filterMap fun i => if istirad i = [] then none else some ⟨ism i, istirad i, i⟩

/-- قاعدةُ الملفّات. -/
def qaida : Qaida Nat := ⟨"WahdatJadwal", qawanin⟩

/-- الأصلُ: ملفٌّ في الجدول لا يستورد من المشروع شيئًا. -/
def aslB (i : Nat) : Bool := decide (i < N) && (istirad i).isEmpty

/-- سلسلةُ البناء: لكلّ ملفٍّ بترتيبه خطوةٌ — أصلٌ، أو قانونُه برقمه في القاعدة. -/
def silsila : List (Khatwa Nat) :=
  tartib.map fun i => if istirad i = [] then .asl i else .qanun ((List.range i).countP fun j => istirad j ≠ [])

/-- **الرتبةُ درجةُ الاشتقاق:** 0 لما لا يستورد من المشروع شيئًا، وإلّا واحدٌ فوق أعلى ما يستورده — على الجدول. -/
theorem rutba_daraja : ∀ i < N, rutba i = (istirad i).foldr (fun j a => max a (rutba j + 1)) 0 := by
  decide +kernel

/-- **القاعدةُ متدرّجة:** لكلّ قانونٍ مقدّماتٌ، وكلُّ مقدّمةٍ أدنى رتبةً من نتيجته — على الجدول. -/
theorem mutadarrija : Mutadarrija qaida rutba := by
  unfold Mutadarrija; decide +kernel

/-! ### الفحصُ قطعةً قطعة

لمّا دخلت وحداتُ A116 الجدولَ (2026-11-20) صار فحصُ السلسلة كلِّها بقرارٍ واحدٍ في النواة يجاوز ذاكرةَ البيئة (قُتل عند 6 غ.ب). فالسلسلةُ تُفحص
قطعًا من `QITAA` خطوةً، كلُّ قطعةٍ بقرارٍ مستقلّ يبدأ من ثابت ما قبلها؛ و`fahs_qitaa` يجمعها فحصًا واحدًا (مبرهنٌ لكلّ قاعدةٍ وسلسلة). -/

/-- الفاحصُ على سلسلتين متتاليتين هو الفاحصُ على الأولى ثمّ على الثانية من ثابتها. -/
theorem fahs_append {P : Type} [DecidableEq P] (q : Qaida P) (a : P → Bool) :
    ∀ (xs ys : List (Khatwa P)) (t : List P), fahs q a t (xs ++ ys) = (fahs q a t xs).bind (fun t' => fahs q a t' ys) := by
  intro xs
  induction xs with
  | nil => intro ys t; rfl
  | cons x xs ih =>
    intro ys t
    simp only [List.cons_append, fahs]
    cases tatbiq q a t x with
    | none => rfl
    | some t' => exact ih ys t'

/-- **القطعُ تجمع:** إن قبل الفاحصُ كلَّ قطعةٍ من ثابت ما قبلها فقد قبل السلسلةَ كلَّها. -/
theorem fahs_qitaa {P : Type} [DecidableEq P] (q : Qaida P) (a : P → Bool) (S : List (Khatwa P)) (T : List P) (n K : Nat)
    (h : ∀ k < K, fahs q a (T.take (k * n)) ((S.drop (k * n)).take n) = some (T.take ((k + 1) * n)))
    (hS : S.length ≤ K * n) (hT : T.length ≤ K * n) : fahs q a [] S = some T := by
  have key : ∀ k ≤ K, fahs q a [] (S.take (k * n)) = some (T.take (k * n)) := by
    intro k
    induction k with
    | zero => intro _; simp [fahs]
    | succ k ih =>
      intro hk
      have e : (k + 1) * n = k * n + n := Nat.succ_mul k n
      rw [e, List.take_add, fahs_append, ih (by omega)]
      simp only [Option.bind_some]
      rw [← e]; exact h k (by omega)
  have := key K (Nat.le_refl K)
  rwa [List.take_of_length_le hS, List.take_of_length_le hT] at this

/-- طولُ القطعة، وعددُ القطع (يسع 640 ملفًّا؛ وما زاد يردّه `bina_maqbul` بفرض الطول). -/
def QITAA : Nat := 40

/-- القطعةُ ‎`k`‎ مقبولةٌ من ثابت ما قبلها. -/
def qitaa (k : Nat) : Prop :=
  fahs qaida aslB (tartib.take (k * QITAA)) ((silsila.drop (k * QITAA)).take QITAA) = some (tartib.take ((k + 1) * QITAA))

theorem qitaa_0 : qitaa 0 := by unfold qitaa; decide +kernel
theorem qitaa_1 : qitaa 1 := by unfold qitaa; decide +kernel
theorem qitaa_2 : qitaa 2 := by unfold qitaa; decide +kernel
theorem qitaa_3 : qitaa 3 := by unfold qitaa; decide +kernel
theorem qitaa_4 : qitaa 4 := by unfold qitaa; decide +kernel
theorem qitaa_5 : qitaa 5 := by unfold qitaa; decide +kernel
theorem qitaa_6 : qitaa 6 := by unfold qitaa; decide +kernel
theorem qitaa_7 : qitaa 7 := by unfold qitaa; decide +kernel
theorem qitaa_8 : qitaa 8 := by unfold qitaa; decide +kernel
theorem qitaa_9 : qitaa 9 := by unfold qitaa; decide +kernel
theorem qitaa_10 : qitaa 10 := by unfold qitaa; decide +kernel
theorem qitaa_11 : qitaa 11 := by unfold qitaa; decide +kernel
theorem qitaa_12 : qitaa 12 := by unfold qitaa; decide +kernel
theorem qitaa_13 : qitaa 13 := by unfold qitaa; decide +kernel
theorem qitaa_14 : qitaa 14 := by unfold qitaa; decide +kernel
theorem qitaa_15 : qitaa 15 := by unfold qitaa; decide +kernel

/-- **البناءُ سلسلةٌ مقبولة:** فاحصُ القاعدة يقبل ترتيبَ البناء خطوةً خطوة، ويُثبت به الملفّاتِ كلَّها — على الجدول. -/
theorem bina_maqbul : fahs qaida aslB [] silsila = some tartib ∧ ∀ i < N, i ∈ tartib := by
  refine ⟨fahs_qitaa qaida aslB silsila tartib QITAA 16 (fun k hk => ?_) (by decide +kernel) (by decide +kernel), by decide +kernel⟩
  match k, hk with
    | 0, _ => exact qitaa_0
    | 1, _ => exact qitaa_1
    | 2, _ => exact qitaa_2
    | 3, _ => exact qitaa_3
    | 4, _ => exact qitaa_4
    | 5, _ => exact qitaa_5
    | 6, _ => exact qitaa_6
    | 7, _ => exact qitaa_7
    | 8, _ => exact qitaa_8
    | 9, _ => exact qitaa_9
    | 10, _ => exact qitaa_10
    | 11, _ => exact qitaa_11
    | 12, _ => exact qitaa_12
    | 13, _ => exact qitaa_13
    | 14, _ => exact qitaa_14
    | 15, _ => exact qitaa_15
    | _ + 16, h => exact absurd h (by omega)

/-- **كلُّ ملفٍّ مرخَّص** في القاعدة على أصولها (`aslB`: ما رتبتُه صفر) — على هذا الجدول. -/
theorem kull_wahda_murakhkhasa : ∀ i < N, Murakhkhas qaida (fun p => aslB p = true) i := by
  intro i hi
  exact fahs_sahih qaida aslB silsila [] tartib (by simp) bina_maqbul.1 i (bina_maqbul.2 i hi)

/-- **ما رتبتُه صفرٌ لا يُرخَّص إلّا أصلًا:** أيًّا كانت الأصولُ ‎`a`‎ (قرارُ المالك)، كلُّ ملفٍّ مرخَّصٍ عليها رتبتُه صفرٌ منها — على هذا الجدول
(فرضُها `mutadarrija`). -/
theorem rutba_sifr (a : Nat → Bool) (i : Nat) (h : Murakhkhas qaida (fun p => a p = true) i) (h0 : rutba i = 0) :
    a i = true :=
  rutba_sifr_asl qaida rutba _ mutadarrija h h0

/-- ما لا يرث من المشروع شيئًا: كلُّ ملفٍّ رتبتُه صفر. أيُّها أصلٌ وأيُّها يتيمٌ يُوصل بأبيه قرارُ المالك (`hawkama/الوراثة_الصنفية.md`). -/
def bilaWirth : List String := [
  "A116.Cells", "A116.Derivation", "A116.Fiber", "A116.Fold", "A116.FractalMushafDef", "A116.FractalTarkibData",
  "A116.Harf.Khana", "A116.Hasr", "A116.Ishtiqaq", "A116.Kraft", "A116.LazimData", "A116.Malumat",
  "A116.MaqayisData", "A116.NaqlData", "A116.Qarar", "A116.QarinaData", "A116.Qism", "A116.Recovery",
  "A116.Silsila", "A116.Stages", "A116.Tadwir", "A116.Tanith", "A116.TashkilData", "A116.TawafiqMasfufaData",
  "A116.WadData",
  "Aql.Qaida", "Aql.WaqiRibtJadwal",
  "Dal.Adad", "Dal.AqsamAlism", "Dal.AqsamAllafz", "Dal.Khaliya", "Dal.WaqfSibawayhi",
  "Faahis.SijillMakhtum",
  "Jisr.AqsamDalMadlul", "Jisr.AwamilJadwal", "Jisr.AwamilUslub", "Jisr.BabFa", "Jisr.BaqiJaza", "Jisr.MajariKalim",
  "Jisr.QawaidJadwal", "Jisr.TartibMamul",
  "Madlul.AqsamAlmadlul", "Madlul.Dalala", "Madlul.Fard116Data", "Madlul.IshtirakData", "Madlul.JadwalLuzumNaw", "Madlul.NahtData",
  "Nabt.ArabicCoverage", "Nabt.BookCoverage", "Nabt.Cell", "Nabt.ClassicalBoundaryAffixes", "Nabt.ClassicalGemination",
  "Nabt.ClassicalHamza", "Nabt.ClassicalLanguageEvidence", "Nabt.ClassicalReferenceReadings", "Nabt.ClassicalWeak",
  "Nabt.Derivation", "Nabt.LearnedModelData", "Nabt.MaqayisRules", "Nabt.Obligations", "Nabt.PhonologicalModes",
  "Nabt.ProductiveForms", "Nabt.Program", "Nabt.PropertyEvidence", "Nabt.RationalInquiry", "Nabt.RecursiveLicensedAlgebra",
  "Nabt.RuleLearning", "Nabt.SemanticInference", "Nabt.Shakhsiyya3Rules", "Nabt.Transition",
  "Nizam.Asas", "Nizam.Damj", "Nizam.Qiyas", "Nizam.WahdatJadwal",
  "SLGE.AwamilTable", "SLGE.Core", "SLGE.MadlulAwwalan", "SLGE.TarkibLit"]

/-! ### فحصُ `bilaWirth` قطعًا

قرارُه الواحد في النواة بلغ 5.7 غ.ب بعد دخول A116 (قيسَ بـ`scripts/qiyas_dhakira.py`، 2026-11-20): مقارنةُ أسماء الملفّات الـ453 نصوصًا بالقائمة.
فالشطرُ الأوّل قطعٌ من 40 ملفًّا، والثاني قطعٌ من 20 اسمًا، كلُّ قطعةٍ بقرارٍ مستقلّ؛ ويجمعهما `bilaWirth_iff` بنصّه السابق. -/

theorem wirth_0 : ∀ r < 40, 40 * 0 + r < N → (rutba (40 * 0 + r) = 0 ↔ ism (40 * 0 + r) ∈ bilaWirth) := by
  decide +kernel
theorem wirth_1 : ∀ r < 40, 40 * 1 + r < N → (rutba (40 * 1 + r) = 0 ↔ ism (40 * 1 + r) ∈ bilaWirth) := by
  decide +kernel
theorem wirth_2 : ∀ r < 40, 40 * 2 + r < N → (rutba (40 * 2 + r) = 0 ↔ ism (40 * 2 + r) ∈ bilaWirth) := by
  decide +kernel
theorem wirth_3 : ∀ r < 40, 40 * 3 + r < N → (rutba (40 * 3 + r) = 0 ↔ ism (40 * 3 + r) ∈ bilaWirth) := by
  decide +kernel
theorem wirth_4 : ∀ r < 40, 40 * 4 + r < N → (rutba (40 * 4 + r) = 0 ↔ ism (40 * 4 + r) ∈ bilaWirth) := by
  decide +kernel
theorem wirth_5 : ∀ r < 40, 40 * 5 + r < N → (rutba (40 * 5 + r) = 0 ↔ ism (40 * 5 + r) ∈ bilaWirth) := by
  decide +kernel
theorem wirth_6 : ∀ r < 40, 40 * 6 + r < N → (rutba (40 * 6 + r) = 0 ↔ ism (40 * 6 + r) ∈ bilaWirth) := by
  decide +kernel
theorem wirth_7 : ∀ r < 40, 40 * 7 + r < N → (rutba (40 * 7 + r) = 0 ↔ ism (40 * 7 + r) ∈ bilaWirth) := by
  decide +kernel
theorem wirth_8 : ∀ r < 40, 40 * 8 + r < N → (rutba (40 * 8 + r) = 0 ↔ ism (40 * 8 + r) ∈ bilaWirth) := by
  decide +kernel
theorem wirth_9 : ∀ r < 40, 40 * 9 + r < N → (rutba (40 * 9 + r) = 0 ↔ ism (40 * 9 + r) ∈ bilaWirth) := by
  decide +kernel
theorem wirth_10 : ∀ r < 40, 40 * 10 + r < N → (rutba (40 * 10 + r) = 0 ↔ ism (40 * 10 + r) ∈ bilaWirth) := by
  decide +kernel
theorem wirth_11 : ∀ r < 40, 40 * 11 + r < N → (rutba (40 * 11 + r) = 0 ↔ ism (40 * 11 + r) ∈ bilaWirth) := by
  decide +kernel
theorem wirth_12 : ∀ r < 40, 40 * 12 + r < N → (rutba (40 * 12 + r) = 0 ↔ ism (40 * 12 + r) ∈ bilaWirth) := by
  decide +kernel
theorem wirth_13 : ∀ r < 40, 40 * 13 + r < N → (rutba (40 * 13 + r) = 0 ↔ ism (40 * 13 + r) ∈ bilaWirth) := by
  decide +kernel
theorem wirth_14 : ∀ r < 40, 40 * 14 + r < N → (rutba (40 * 14 + r) = 0 ↔ ism (40 * 14 + r) ∈ bilaWirth) := by
  decide +kernel
theorem wirth_15 : ∀ r < 40, 40 * 15 + r < N → (rutba (40 * 15 + r) = 0 ↔ ism (40 * 15 + r) ∈ bilaWirth) := by
  decide +kernel

theorem aslIsm_0 : ∀ r < 20, 20 * 0 + r < bilaWirth.length → ∃ i < N, ism i = bilaWirth.getD (20 * 0 + r) "" := by
  decide +kernel
theorem aslIsm_1 : ∀ r < 20, 20 * 1 + r < bilaWirth.length → ∃ i < N, ism i = bilaWirth.getD (20 * 1 + r) "" := by
  decide +kernel
theorem aslIsm_2 : ∀ r < 20, 20 * 2 + r < bilaWirth.length → ∃ i < N, ism i = bilaWirth.getD (20 * 2 + r) "" := by
  decide +kernel
theorem aslIsm_3 : ∀ r < 20, 20 * 3 + r < bilaWirth.length → ∃ i < N, ism i = bilaWirth.getD (20 * 3 + r) "" := by
  decide +kernel
theorem aslIsm_4 : ∀ r < 20, 20 * 4 + r < bilaWirth.length → ∃ i < N, ism i = bilaWirth.getD (20 * 4 + r) "" := by
  decide +kernel
theorem aslIsm_5 : ∀ r < 20, 20 * 5 + r < bilaWirth.length → ∃ i < N, ism i = bilaWirth.getD (20 * 5 + r) "" := by
  decide +kernel
theorem aslIsm_6 : ∀ r < 20, 20 * 6 + r < bilaWirth.length → ∃ i < N, ism i = bilaWirth.getD (20 * 6 + r) "" := by
  decide +kernel
theorem aslIsm_7 : ∀ r < 20, 20 * 7 + r < bilaWirth.length → ∃ i < N, ism i = bilaWirth.getD (20 * 7 + r) "" := by
  decide +kernel

/-- **ما لا يرث مسمًّى:** رتبةُ الملفّ صفرٌ إذا وفقط إذا كان اسمُه في `bilaWirth` — على هذا الجدول. فملفٌّ جديدٌ لا يستورد من المشروع
شيئًا، بعد إعادة توليد الجدول (يفحصها الاختبار)، لا يُبنى معه هذا حتى يُضاف اسمُه. -/
theorem bilaWirth_iff : (∀ i < N, (rutba i = 0 ↔ ism i ∈ bilaWirth)) ∧ ∀ m ∈ bilaWirth, ∃ i < N, ism i = m := by
  have hN : N ≤ 40 * 16 := by decide +kernel
  have hB : bilaWirth.length ≤ 20 * 8 := by decide
  refine ⟨fun i hi => ?_, fun m hm => ?_⟩
  · have e : i = 40 * (i / 40) + i % 40 := (Nat.div_add_mod i 40).symm
    have hk : i / 40 < 16 := by omega
    have hr : i % 40 < 40 := Nat.mod_lt _ (by decide)
    rw [e]
    have key : ∀ k < 16, ∀ r < 40, 40 * k + r < N → (rutba (40 * k + r) = 0 ↔ ism (40 * k + r) ∈ bilaWirth) := by
      intro k hk
      match k, hk with
    | 0, _ => exact wirth_0
    | 1, _ => exact wirth_1
    | 2, _ => exact wirth_2
    | 3, _ => exact wirth_3
    | 4, _ => exact wirth_4
    | 5, _ => exact wirth_5
    | 6, _ => exact wirth_6
    | 7, _ => exact wirth_7
    | 8, _ => exact wirth_8
    | 9, _ => exact wirth_9
    | 10, _ => exact wirth_10
    | 11, _ => exact wirth_11
    | 12, _ => exact wirth_12
    | 13, _ => exact wirth_13
    | 14, _ => exact wirth_14
    | 15, _ => exact wirth_15
      | _ + 16, h => exact absurd h (by omega)
    exact key (i / 40) hk (i % 40) hr (by omega)
  · obtain ⟨j, hj, rfl⟩ := List.getElem_of_mem hm
    have e : j = 20 * (j / 20) + j % 20 := (Nat.div_add_mod j 20).symm
    have key : ∀ k < 8, ∀ r < 20, 20 * k + r < bilaWirth.length → ∃ i < N, ism i = bilaWirth.getD (20 * k + r) "" := by
      intro k hk
      match k, hk with
    | 0, _ => exact aslIsm_0
    | 1, _ => exact aslIsm_1
    | 2, _ => exact aslIsm_2
    | 3, _ => exact aslIsm_3
    | 4, _ => exact aslIsm_4
    | 5, _ => exact aslIsm_5
    | 6, _ => exact aslIsm_6
    | 7, _ => exact aslIsm_7
      | _ + 8, h => exact absurd h (by omega)
    have := key (j / 20) (by omega) (j % 20) (Nat.mod_lt _ (by decide)) (by omega)
    rw [← e] at this
    simpa [List.getD_eq_getElem?_getD, List.getElem?_eq_getElem hj] using this

/-! ## الجيناتُ الحسابيّة -/

/-- جينٌ حسابيّ: اسمُ الحساب الصنفيّ، وعددُ أصنافه، وثابتُ طوله. -/
abbrev Jin := String × Nat × Nat

/-- جينُ الحساب الصنفيّ ‎`x`‎: اسمُه نصُّ المعرِّف كما كُتب، وعددُ أصنافه وثابتُه من الثابت الذي يُحلّ إليه؛ فلا تُبدَّل أعدادُ حسابٍ بأعداد غيره،
ومطابقةُ الاسم للاسم الكامل يفحصها `tahaqquq/test_wiratha.py` (٣). -/
macro "jin!" x:ident : term => `(($(Lean.quote x.getId.toString), ($x).Q.m, ($x).K))

/-- جيناتُ الملفّ الخاصّة: حساباتُه الصنفيّة. -/
def jinatKhassa (m : String) : List Jin :=
  if m = "SLGE.Root" then
    [jin! SLGE.Law.HisabJadhr.hisabJadhr, jin! SLGE.Law.HisabZaid.hisabZaid]
  else if m = "SLGE.Law" then
    [jin! SLGE.Law.HisabKalima.hisabWaqf, jin! SLGE.Law.HisabKalima.hisabWasl, jin! SLGE.Law.HisabJumla.hisabJumla]
  else if m = "SLGE.Syllable" then
    [jin! SLGE.Law.HisabMaqta.hisabWaqf, jin! SLGE.Law.HisabMaqta.hisabWasl]
  else []

/-- جيناتُ الملفّ بالوراثة بوقود ‎`k`‎: الخاصّةُ، ثمّ جيناتُ ما يستورده بوقود ‎`k − 1`‎. -/
def jinat : Nat → Nat → List Jin
  | 0, i => jinatKhassa (ism i)
  | k + 1, i => jinatKhassa (ism i) ++ (istirad i).flatMap (jinat k)

/-- جيناتُ الملفّ كلُّها: بوقودٍ رتبتُه. -/
def jinatKull (i : Nat) : List Jin := jinat (rutba i) i

/-- **الخاصّةُ تبقى:** جيناتُ الملفّ الخاصّة في جيناته بأيّ وقود. -/
theorem jinat_khassa (k i : Nat) : ∀ g ∈ jinatKhassa (ism i), g ∈ jinat k i := by
  intro g hg
  cases k with
  | zero => exact hg
  | succ k => exact List.mem_append_left _ hg

/-- **التوريث:** جيناتُ ما يستورده الملفّ بوقود ‎`k`‎ في جيناته بوقود ‎`k + 1`‎. -/
theorem jinat_tuwarrath (k i j : Nat) (hj : j ∈ istirad i) : ∀ g ∈ jinat k j, g ∈ jinat (k + 1) i := by
  intro g hg
  exact List.mem_append_right _ (List.mem_flatMap.mpr ⟨j, hj, hg⟩)

/-- **الوقودُ لا يُسقط:** ما في الجينات بوقود ‎`k`‎ فيها بوقود ‎`k + 1`‎. -/
theorem jinat_ratib : ∀ k i, ∀ g ∈ jinat k i, g ∈ jinat (k + 1) i := by
  intro k
  induction k with
  | zero =>
    intro i g hg
    exact List.mem_append_left _ hg
  | succ k ih =>
    intro i g hg
    show g ∈ jinatKhassa (ism i) ++ (istirad i).flatMap (jinat (k + 1))
    have hg' : g ∈ jinatKhassa (ism i) ++ (istirad i).flatMap (jinat k) := hg
    rcases List.mem_append.mp hg' with h | h
    · exact List.mem_append_left _ h
    · obtain ⟨j, hj, hg2⟩ := List.mem_flatMap.mp h
      exact List.mem_append_right _ (List.mem_flatMap.mpr ⟨j, hj, ih j g hg2⟩)

theorem jinat_ratib_le (i : Nat) {k k' : Nat} (h : k ≤ k') : ∀ g ∈ jinat k i, g ∈ jinat k' i := by
  induction h with
  | refl => exact fun g hg => hg
  | step _ ih => exact fun g hg => jinat_ratib _ i g (ih g hg)

/-- كلُّ ما يستورده الملفّ أدنى منه رتبةً — على الجدول. -/
theorem istirad_adna : ∀ i < N, ∀ j ∈ istirad i, rutba j < rutba i := by
  decide +kernel

/-- **كلُّ ملفٍّ يحمل جيناتِ ما يستورده كلَّها:** على الجدول، بالتدرّج. -/
theorem jinatKull_tuwarrath (i : Nat) (hi : i < N) (j : Nat) (hj : j ∈ istirad i) :
    ∀ g ∈ jinatKull j, g ∈ jinatKull i := by
  intro g hg
  have hlt := istirad_adna i hi j hj
  obtain ⟨k, hk⟩ : ∃ k, rutba i = k + 1 := ⟨rutba i - 1, by omega⟩
  unfold jinatKull at hg ⊢
  rw [hk]
  exact jinat_tuwarrath k i j hj g (jinat_ratib_le j (by omega) g hg)

/-- **الشاهد:** آلاتُ المالك السبع في ثلاثة ملفّات بحساباتها، وأصنافُها وثوابتُها مقروءةٌ منها. -/
theorem shahid_jinat :
    jinatKhassa "SLGE.Root" = [("SLGE.Law.HisabJadhr.hisabJadhr", 5, 1), ("SLGE.Law.HisabZaid.hisabZaid", 10, 2)] ∧
    jinatKhassa "SLGE.Law" = [("SLGE.Law.HisabKalima.hisabWaqf", 13, 2), ("SLGE.Law.HisabKalima.hisabWasl", 13, 2),
      ("SLGE.Law.HisabJumla.hisabJumla", 13, 3)] ∧
    jinatKhassa "SLGE.Syllable" = [("SLGE.Law.HisabMaqta.hisabWaqf", 8, 2), ("SLGE.Law.HisabMaqta.hisabWasl", 8, 2)] := by
  decide +kernel

end Wiratha
end Nizam
