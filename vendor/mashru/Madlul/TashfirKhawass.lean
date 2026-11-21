/-
  Madlul/TashfirKhawass.lean — جسرُ المعلومة المعمَّم: طيُّ وفكُّ Madlul.Tayin.Khawass (الخواصُّ التأسيسية
  الخمس وقابليّاتُ الحركة)، بإغلاق الفجوة التي أجّلها Madlul/TashfirMadda.lean بالاسم: «قابليّاتُها
  qab : List QabHaraka تحتاج ترميزَ قوائم لم يُبنَ هنا».

  السند: طلب المالك 2026-10-17 22:55 (ردًّا على قائمتي «ما بقي باسمه» بعد PR #32): «Khawass/alaqat/hawass/
  awwaliyyat/azmina/makan/mirsat/isnad: مؤجَّلة بالاسم. ايضا نفذ انت مفوض مني». هذه القطعةُ أوّلُ المؤجَّلات
  تنفيذًا، ومختارةٌ عمدًا أوّلًا: Khawass مذكورةٌ بالاسم في طلب المالك، وفجوتُها الوحيدة (ترميزُ القوائم) أداةٌ
  عامّةٌ تُفتح بها بقيّةُ القطعة (ItarMadlul وغيرها تحمل حقول Madlul ذاتَ قوائم مماثلة) — فبناؤها هنا استثمارٌ
  يُستعمَل لا حلٌّ مفردٌ.

  **الفجوة المغلَقة: ترميزُ القوائم.** `Madlul.Jamad.Madda` (في TashfirMadda) حقولُها قيمٌ مفردة (Nat، Option Nat،
  Option Int) فلم تحتجْ قائمة. `Khawass.qab : List QabHaraka` طولُها غيرُ محدود، فلا يكفيها `SLGE.mixEnc`/
  `mixDec` مباشرةً (يطويان قيمتين محدودتين مع ثالثةٍ طليقة، لا قائمةً). البناءُ هنا عمومٌ بسيط: يُفكَّك فعليًّا
  إلى `SLGE.mixEnc`/`mixDec` نفسِهما (لا قناةٌ موازية) بحيلة «نيل‌/كونْس» المعتادة (كما في Lisp/Prolog: القائمةُ
  الفارغة صفرٌ، والكونْس رأسٌ محدودٌ مع ذنبٍ مطويّ زائد واحد — توسيعٌ لحيلة `optNatEnc` في TashfirMadda من
  غيابٍ/حضورٍ واحد إلى عددٍ غيرِ محدودٍ من الحضورات): `listEnc B [] = 0`، `listEnc B (x::xs) = mixEnc B 1
  (listEnc B xs) x 0 + 1` (مع `x < B`). الفكُّ `listDec` كُلّيٌّ على كلّ عددٍ (كما تتطلّب دالّةُ Lean)، بالقسمة
  على نفس النمط الذي يُنهي زِكزاكَ Int في TashfirMadda — ولا شرطَ صحّةٍ يُحمَل في Tayy لأنّ كلَّ عددٍ يُفكَّك إلى
  قائمةٍ ما (قد تكون غيرَ الأصل لو لم يُحترَم الحدّ)؛ الصحّةُ شرطٌ على الطيّ لا الفكّ: ما طُوي بعناصر دون B يُفكُّ
  بعينه (`list_dec_enc`).

  **سببٌ آخرُ لاختيار Khawass أوّلًا — واكتشافٌ بنائيّ:** حقولُها الخمسُ من `Qima` (ثلاثُ قيمٍ) وقائمتُها من
  `QabHaraka` (خمسُ قيم) — نوعانِ **محدودانِ** فعلًا، لا قيمًا طليقةً كحقول Madda (كثافةٌ، حرارة). فترميزُ Qima/
  QabHaraka نفسِهما لا يحتاج شرط صحّةٍ (كلُّ قيمةٍ من نوعٍ محدودٍ كلِّه دون حدّها بالتعريف)، وقائمةٌ من نوعٍ محدودٍ
  تُطوى بعناصر دون حدّه دائمًا. فطيُّ Khawass كلِّه **غيرُ مشروطٍ** — لا Subtype ولا `Classical.propDecidable` ولا
  `noncomputable` كما احتاجت TashfirSullam (شرطُ صحّة السلّم) وTashfirMadda (شرطُ البقاء دون BOUND): هذا أوّلُ
  مثالٍ في هذه السلسلة طيُّه وفكُّه **حسابيّان تمامًا** (بلا مسلّمةٍ كلاسيكيّة في بنائه، لا في برهانه فقط).

  ما يُبرهن هنا: تمامُ الطيّ والفكّ لكلّ قيمةٍ من Qima وQabHaraka (3 منشِئاتٍ و5، بالاستقراء البنائيّ على الحالات
  كلِّها لا شاهدًا)؛ تمامُ `listEnc`/`listDec` العموميّ لكلّ قائمة Nat بعناصر دون حدّها (بالاستقراء على القائمة)؛
  تمامُ `khawassEnc`/`khawassDec` لكلّ Khawass بلا شرط (مركَّبٌ من الثلاثة السابقة عبر `SLGE.mixDec_enc` ثلاثَ
  مرّات)؛ وTayy محسوبةٌ على Khawass مباشرةً (بلا Unit/Subtype)؛ وعلى الشاهد: فصولُ الأقسام الأربعة من
  `Tayin.fusul` (الجمادُ والنباتُ والحيوانُ والإنسان — نفسُ شواهد المودَع المختوم `ajnas.tsv`).

  مؤجَّلٌ: جداولُ alaqat/hawass/awwaliyyat/azmina/makan/mirsat/isnad (الآلة هنا تُعيد استعمالها فورًا حين يُفوَّض
  أيٌّ منها)؛ وجسرا العوامل والإسناد وItar3 على آلة Tayy (أثقلُ بنيةً: `Aql.Isnad.Jumla` تكراريّةٌ حقًّا، و
  `Jisr.Utur.ItarMadlul`/`Itar3` تحملان `SLGE.Awwalan.Madlul` بأربع قوائم — `listEnc`/`listDec` هنا تفتحهما لكنّها
  لم تُركَّب عليهما بعد: مهمّةٌ تالية مستقلّة)؛ وجدولُ اللزوم من شبكة المعاجم (مقاييسُ اللغة ولسانُ العرب مختومانِ
  فعلًا في mudaat/sijill.json بإذنٍ سابقٍ صحيح — تحقَّق في هذه الجلسة، فلا ختمَ جديدًا يلزمها؛ العائقُ وحدَه عدمُ
  حضور نصّهما المحوَّل في MUDAA_DIR هذه الجلسة — بيانٌ لا إذن).
-/
import SLGE.Core
import Aql.Mawsua
import Madlul.Tayin

set_option autoImplicit false

namespace Madlul.TashfirKhawass

open Mawsua Madlul.Tayin

/-! ## ١. طيُّ Qima وQabHaraka (نوعانِ محدودان، بلا شرط) -/

def qimaEnc : Qima → Nat
  | .naam => 0 | .la => 1 | .laHukm => 2

def qimaDec : Nat → Qima
  | 0 => .naam | 1 => .la | _ => .laHukm

theorem qima_dec_enc (q : Qima) : qimaDec (qimaEnc q) = q := by cases q <;> rfl
theorem qimaEnc_lt (q : Qima) : qimaEnc q < 3 := by cases q <;> decide

def qabEnc : QabHaraka → Nat
  | .sayr => 0 | .rakd => 1 | .jary => 2 | .zahf => 3 | .qafz => 4

def qabDec : Nat → QabHaraka
  | 0 => .sayr | 1 => .rakd | 2 => .jary | 3 => .zahf | _ => .qafz

theorem qab_dec_enc (q : QabHaraka) : qabDec (qabEnc q) = q := by cases q <;> rfl
theorem qabEnc_lt (q : QabHaraka) : qabEnc q < 5 := by cases q <;> decide

/-! ## ٢. طيُّ القوائم المعمَّم: nil↦0، cons x xs↦ mixEnc B 1 (طيّ xs) x 0 + 1 -/

/-- طيُّ `List Nat` (عناصرُها دون B) إلى عددٍ واحد، بتركيب `SLGE.mixEnc` لا بقناةٍ موازية: توسيعُ حيلة
`optNatEnc` (غيابٌ/حضورٌ واحد) إلى عددٍ غيرِ محدودٍ من «الحضورات». -/
def listEnc (B : Nat) : List Nat → Nat
  | [] => 0
  | x :: xs => SLGE.mixEnc B 1 (listEnc B xs) x 0 + 1

/-- فكُّ العدد إلى `List Nat` — كُلّيٌّ على كلّ عدد (ما لم يُطوَ بعناصر دون B يُفكَّك إلى قائمةٍ ما، لا يهمّ أيّة). -/
def listDec (B : Nat) : Nat → List Nat
  | 0 => []
  | n + 1 => (SLGE.mixDec B 1 n).2.1 :: listDec B (SLGE.mixDec B 1 n).1
termination_by n => n
decreasing_by
  have heq : (SLGE.mixDec B 1 n).1 = n / B := by simp [SLGE.mixDec]
  rw [heq]
  exact Nat.lt_succ_of_le (Nat.div_le_self n B)

/-- **الفكُّ يعيد الأصل لكلّ قائمةٍ بعناصر دون B** — بالاستقراء على القائمة، نقلًا مباشرًا لـ `SLGE.mixDec_enc`. -/
theorem list_dec_enc (B : Nat) (l : List Nat) (h : ∀ x ∈ l, x < B) : listDec B (listEnc B l) = l := by
  induction l with
  | nil => simp [listEnc, listDec]
  | cons x xs ih =>
    have hx : x < B := h x List.mem_cons_self
    have hxs : ∀ y ∈ xs, y < B := fun y hy => h y (List.mem_cons_of_mem x hy)
    show listDec B (SLGE.mixEnc B 1 (listEnc B xs) x 0 + 1) = x :: xs
    unfold listDec
    rw [SLGE.mixDec_enc B 1 (listEnc B xs) x 0 hx (Nat.zero_lt_one)]
    simp only
    rw [ih hxs]

/-! ## ٣. طيُّ Khawass كلِّها (غيرُ مشروط) -/

/-- حدُّ الطبقة الوسيطة (الخواصُّ الخمس): كلُّ قيمةٍ دون 3 فالخمسُ معًا دون 3^5 = 243. -/
theorem khawass_l2_lt (k : Khawass) :
    SLGE.mixEnc 3 3 (SLGE.mixEnc 3 3 (qimaEnc k.taghadhdhi) (qimaEnc k.numuw) (qimaEnc k.mawt))
      (qimaEnc k.intiqal) (qimaEnc k.aql) < 243 := by
  simp only [SLGE.mixEnc]
  have h1 := qimaEnc_lt k.taghadhdhi
  have h2 := qimaEnc_lt k.numuw
  have h3 := qimaEnc_lt k.mawt
  have h4 := qimaEnc_lt k.intiqal
  have h5 := qimaEnc_lt k.aql
  omega

/-- **الطيّ**: ثلاثُ طبقاتٍ من `SLGE.mixEnc` للخواصّ الخمس (دون شرط، كلُّها من Qima)، زائدًا `listEnc` للقابليّات. -/
def khawassEnc (k : Khawass) : Nat :=
  let l1 := SLGE.mixEnc 3 3 (qimaEnc k.taghadhdhi) (qimaEnc k.numuw) (qimaEnc k.mawt)
  let l2 := SLGE.mixEnc 3 3 l1 (qimaEnc k.intiqal) (qimaEnc k.aql)
  SLGE.mixEnc 243 1 (listEnc 5 (k.qab.map qabEnc)) l2 0

/-- **الفكّ**: عكسُ الطيّ طبقةً طبقة. -/
def khawassDec (n : Nat) : Khawass :=
  match SLGE.mixDec 243 1 n with
  | (qabCode, l2, _) =>
    match SLGE.mixDec 3 3 l2 with
    | (l1, intiqalC, aqlC) =>
      match SLGE.mixDec 3 3 l1 with
      | (taghadhdhiC, numuwC, mawtC) =>
        { taghadhdhi := qimaDec taghadhdhiC, numuw := qimaDec numuwC, mawt := qimaDec mawtC,
          intiqal := qimaDec intiqalC, aql := qimaDec aqlC,
          qab := (listDec 5 qabCode).map qabDec }

theorem qabEnc_map_lt (l : List QabHaraka) : ∀ x ∈ l.map qabEnc, x < 5 := by
  intro x hx
  obtain ⟨y, -, rfl⟩ := List.mem_map.1 hx
  exact qabEnc_lt y

theorem qab_list_roundtrip (l : List QabHaraka) : (l.map qabEnc).map qabDec = l := by
  induction l with
  | nil => rfl
  | cons x xs ih => simp only [List.map_cons, qab_dec_enc, ih]

/-- **الفكُّ يعيد الأصل لكلّ Khawass — بلا شرط.** مركَّبةٌ من ثلاث نقلاتٍ لـ `SLGE.mixDec_enc` ونقلةٍ لـ
`list_dec_enc`؛ لا Subtype هنا لأنّ لا شرط. -/
theorem khawass_dec_enc (k : Khawass) : khawassDec (khawassEnc k) = k := by
  have h2 := qimaEnc_lt k.intiqal
  have h3 := qimaEnc_lt k.aql
  have h4 := qimaEnc_lt k.numuw
  have h5 := qimaEnc_lt k.mawt
  have hlist : ∀ x ∈ k.qab.map qabEnc, x < 5 := qabEnc_map_lt k.qab
  simp only [khawassDec, khawassEnc]
  rw [SLGE.mixDec_enc 243 1 _ _ 0 (khawass_l2_lt k) (Nat.zero_lt_one)]
  rw [SLGE.mixDec_enc 3 3 _ (qimaEnc k.intiqal) (qimaEnc k.aql) h2 h3]
  rw [SLGE.mixDec_enc 3 3 (qimaEnc k.taghadhdhi) (qimaEnc k.numuw) (qimaEnc k.mawt) h4 h5]
  rw [list_dec_enc 5 (k.qab.map qabEnc) hlist]
  simp only [qima_dec_enc, qab_list_roundtrip]

/-! ## ٤. الطيّ على Khawass مباشرةً (بلا Unit/Subtype — لا شرط) -/

def tayyKhawass : Tayy Khawass Nat where
  tawi := khawassEnc
  fakk := fun n => some (khawassDec n)
  fakk_tawi := fun k => by rw [khawass_dec_enc]

theorem tayyKhawass_la_yudi (k : Khawass) : tayyKhawass.fakk (tayyKhawass.tawi k) = some k :=
  tayyKhawass.fakk_tawi k

/-! ## ٥. على الشاهد: فصولُ الأقسام الأربعة (مودَع ajnas.tsv، f567d1ab…) -/

theorem khawass_shawahid_tudi :
    khawassDec (khawassEnc (fusul .jamad)) = fusul .jamad ∧
    khawassDec (khawassEnc (fusul .nabat)) = fusul .nabat ∧
    khawassDec (khawassEnc (fusul .hayawan)) = fusul .hayawan ∧
    khawassDec (khawassEnc (fusul .insan)) = fusul .insan :=
  ⟨khawass_dec_enc _, khawass_dec_enc _, khawass_dec_enc _, khawass_dec_enc _⟩

end Madlul.TashfirKhawass
