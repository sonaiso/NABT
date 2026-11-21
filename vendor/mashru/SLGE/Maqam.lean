import SLGE.Ladder2

/-!
# SLGE المقام: المتكلّم والمخاطب والغائب — ونظامُ الإحالة

**السِّمة:** ‎(شخص، جنس، عدد)‎ — الشخص ‎1‎ متكلّم، ‎2‎ مخاطب، ‎3‎ غائب؛ الجنس ‎0‎ مذكّر، ‎1‎ مؤنّث، ‎2‎ مشترك؛
العدد ‎0‎ مفرد، ‎1‎ مثنّى، ‎2‎ جمع. الاسمُ الظاهر غائبٌ أبدًا.

**الإحالة (قيمٌ في ‎n‎):** ‎0‎ لا إحالة، ‎i+1‎ إلى الخانة ‎i‎ (سابقة)، ‎14‎ إلى المقام (حضور المتكلّم/المخاطب، أو إشارةٌ حسّيّة)،
‎15‎ إلى سابقٍ خارج الجملة، ‎16‎ ضمير الشأن (يحيل إلى الجملة بعده).

**قانونُ الإحالة (الابتداء/الوصل/الوقف):**
* المتكلّمُ والمخاطب حاضران في المقام: إحالتُهما إليه، فيُبتدأ بهما بلا مرجع.
* الغائبُ لا يُبتدأ به: مرجعُه سابقٌ مطابقٌ له في الجنس والعدد — إلّا ضمير الشأن، مفردًا، في صدر الاسميّة.
* الإشارةُ تحيل إلى المقام حسًّا أو إلى سابقٍ مطابق؛ والموصولُ لا يتمّ إلّا بصلةٍ فيها عائدٌ مطابق.
-/

namespace SLGE
namespace Maqam

abbrev Feat := Nat × Nat × Nat

def hudur : Nat := 14
def sabiq : Nat := 15
def shaan : Nat := 16

/-- الضمائرُ المنفصلة الأربعة عشر: (الصورة، حواملُها، السِّمة). ‎ه=1 و=28 م=27 ا=2 ي=11 ن=14 ء=0 ت=18 ح=4‎. -/
def damair : List (String × List Nat × Feat) :=
  [("هو", [1, 28], (3, 0, 0)), ("هما", [1, 27, 2], (3, 0, 1)), ("هم", [1, 27], (3, 0, 2)),
   ("هي", [1, 11], (3, 1, 0)), ("هما", [1, 27, 2], (3, 1, 1)), ("هنّ", [1, 14, 14], (3, 1, 2)),
   ("أنتَ", [0, 14, 18], (2, 0, 0)), ("أنتما", [0, 14, 18, 27, 2], (2, 0, 1)), ("أنتم", [0, 14, 18, 27], (2, 0, 2)),
   ("أنتِ", [0, 14, 18], (2, 1, 0)), ("أنتما", [0, 14, 18, 27, 2], (2, 1, 1)), ("أنتنّ", [0, 14, 18, 14, 14], (2, 1, 2)),
   ("أنا", [0, 14, 2], (1, 2, 0)), ("نحن", [14, 4, 14], (1, 2, 2))]

/-- **المقامُ ثلاثة لا رابع:** متكلّمٌ (2)، مخاطبٌ (6)، غائبٌ (6)؛ والسِّماتُ الأربع عشرة متمايزة. -/
theorem maqam_three :
    damair.all (fun d => 1 ≤ d.2.2.1 && d.2.2.1 ≤ 3) = true ∧
    ([1, 2, 3].map fun p => (damair.filter (·.2.2.1 == p)).length) = [2, 6, 6] ∧
    (damair.map (·.2.2)).Nodup := by decide

/-- **السِّمةُ قيمةٌ فوق الدالّ:** أربعَ عشرةَ سمةً على اثنتي عشرة صورة، وإحدى عشرة سلسلةَ حوامل — ‎هما/أنتما‎ لجنسين،
و‎أنتَ/أنتِ‎ سلسلةٌ واحدة لا تفرّقها إلّا الحالة؛ فالموضعُ في المقام يميّز ما لا يميّزه الحاملُ وحده. -/
theorem dal_underdetermines_maqam :
    (damair.map (·.1)).eraseDups.length = 12 ∧ (damair.map (·.2.1)).eraseDups.length = 11 ∧
    (damair.map (·.2.2)).eraseDups.length = 14 := by decide

/-- **شاهدُ المرادي:** حواملُ الضمائر كلُّها في جدول الجنى الداني (الأحاديّ إلى الخماسيّ). -/
theorem damair_in_muradi :
    damair.all (fun d => (Law.harf1 ++ Law.harf2 ++ Law.harf3 ++ Law.harf4 ++ Law.harf5).contains d.2.1) = true := by
  decide

/-! ## قانونُ الإحالة -/

/-- **الإحالةُ المرخَّصة** لكلمةٍ سمتُها ‎f‎ وإحالتُها ‎ref‎، وأمامها سماتُ السوابق ‎ante‎ (الخانات قبلها في الجملة)،
و‎prev‎: أفي الكلام جملةٌ سابقة؟ و‎sadr‎: أهي في صدر الاسميّة؟ و‎deictic‎: أتقبل الإحالةَ الحسّيّة (الإشارة)؟ -/
def refOK (f : Feat) (ref : Nat) (ante : List Feat) (prev sadr deictic : Bool) : Bool :=
  if f.1 ≤ 2 then
    ref == hudur || (1 ≤ ref && ref ≤ ante.length && (ante.getD (ref - 1) (0, 0, 0)).1 == f.1)
  else if ref == shaan then sadr && f.2.2 == 0 && f.2.1 ≤ 1
  else if ref == hudur then deictic
  else if ref == sabiq then prev
  else 1 ≤ ref && ref ≤ ante.length &&
    (let a := ante.getD (ref - 1) (0, 0, 0); a.1 == 3 && (a.2.1 == f.2.1 || a.2.1 == 2 || f.2.1 == 2) && a.2.2 == f.2.2)

/-- **المتكلّمُ والمخاطبُ يُبتدأ بهما:** إحالتُهما إلى المقام، بلا سابقٍ ولا كلامٍ قبلهما. -/
theorem participants_free : damair.all (fun d => d.2.2.1 ≤ 2 → refOK d.2.2 hudur [] false false false) = true := by
  decide

/-- **الغائبُ لا يُبتدأ به:** بلا سابقٍ في الجملة ولا قبلها، لا إحالةَ له إلّا ضمير الشأن في الصدر مفردًا. -/
theorem ghaib_needs_ante :
    damair.all (fun d => d.2.2.1 == 3 → ([0, 1, 2, 3, hudur, sabiq].all fun r => !refOK d.2.2 r [] false false false)) = true ∧
    refOK (3, 0, 0) shaan [] false true false = true ∧ refOK (3, 1, 0) shaan [] false true false = true ∧
    refOK (3, 0, 2) shaan [] false true false = false ∧ refOK (3, 0, 0) shaan [] false false false = false := by decide

/-- **المطابقة:** ‎هي‎ لا تحيل إلى مذكّر، ولا ‎هم‎ إلى مفرد؛ وتحيل إلى مطابقها؛ والجملةُ السابقة مرجعٌ إن وُجدت. -/
theorem mutabaqa :
    refOK (3, 1, 0) 1 [(3, 0, 0)] false false false = false ∧ refOK (3, 1, 0) 1 [(3, 1, 0)] false false false = true ∧
    refOK (3, 0, 2) 1 [(3, 0, 0)] false false false = false ∧ refOK (3, 0, 2) 1 [(3, 0, 2)] false false false = true ∧
    refOK (3, 0, 0) sabiq [] true false false = true ∧ refOK (3, 0, 0) sabiq [] false false false = false := by decide

/-! ## الأسماءُ المبنيّة المحيلة: الإشارةُ والموصول (شاهدُها قطر الندى L132–140) -/

/-- أسماءُ الإشارة بسماتها (غائبٌ دائمًا). -/
def ishara : List (String × Feat) :=
  [("ذا", (3, 0, 0)), ("ذي", (3, 1, 0)), ("ذه", (3, 1, 0)), ("تي", (3, 1, 0)), ("ته", (3, 1, 0)), ("تا", (3, 1, 0)),
   ("ذان", (3, 0, 1)), ("تان", (3, 1, 1)), ("أولاء", (3, 2, 2))]

/-- الموصولاتُ الخاصّة بسماتها، والمشتركةُ سمتُها ‎(3,2,·)‎ تُعيَّن بالعائد. -/
def mawsulKhass : List (String × Feat) :=
  [("الذي", (3, 0, 0)), ("التي", (3, 1, 0)), ("اللذان", (3, 0, 1)), ("اللتان", (3, 1, 1)),
   ("الذين", (3, 0, 2)), ("الألى", (3, 0, 2)), ("اللائي", (3, 1, 2)), ("اللاتي", (3, 1, 2))]

def mawsulMushtarak : List String := ["من", "ما", "أي", "أل", "ذو", "ذا"]

/-- **الإشارةُ تحيل حسًّا إلى المقام أو إلى سابقٍ مطابق:** ‎ذا‎ حسّيًّا تُرخَّص بلا سابق، و‎تان‎ لا تحيل إلى مفرد. -/
theorem ishara_ref :
    ishara.length = 9 ∧ ishara.all (fun x => refOK x.2 hudur [] false false true) = true ∧
    refOK (3, 1, 1) 1 [(3, 1, 0)] false false true = false ∧ refOK (3, 1, 1) 1 [(3, 1, 1)] false false true = true := by
  decide

/-- العائد: ‎0‎ فاعلٌ مستتر في الصلة، ‎1‎ ضميرٌ ظاهرٌ متّصل، ‎2‎ ضميرٌ محذوف («وقد يحذف»، القطر L141). -/
def silaOK (mawsulFeat aidFeat : Feat) (aidKind : Nat) : Bool :=
  aidKind ≤ 2 && aidFeat.1 == 3 &&
  (mawsulFeat.2.1 == 2 || (aidFeat.2.1 == mawsulFeat.2.1 && aidFeat.2.2 == mawsulFeat.2.2))

/-- **لا صلةَ بلا عائدٍ مطابق:** ‎الذي قامَ‎ (عائدٌ مستتر مذكّر مفرد) تُرخَّص، و‎التي قامَ‎ لا،
و‎من‎ المشتركة تقبل أيَّ عائدٍ غائب؛ والعائدُ المحذوف موضعٌ قائم. -/
theorem sila_aid :
    silaOK (3, 0, 0) (3, 0, 0) 0 = true ∧ silaOK (3, 1, 0) (3, 0, 0) 0 = false ∧
    silaOK (3, 2, 0) (3, 1, 2) 0 = true ∧ silaOK (3, 0, 0) (3, 0, 0) 2 = true ∧ silaOK (3, 0, 0) (3, 0, 0) 3 = false ∧
    mawsulKhass.length = 8 ∧ mawsulMushtarak.length = 6 := by decide

/-! ## الرقم: السِّمةُ والإحالةُ في ‎n‎ -/

def featCode (f : Feat) : Nat := (f.1 * 3 + f.2.1) * 3 + f.2.2

/-- رقمُ الكلمة المحيلة: (رقمُ دالّها، سمتُها، إحالتُها). -/
def refEnc (dal : Nat) (f : Feat) (ref : Nat) : Nat := pair dal (pair (featCode f) ref)

theorem featCode_inj : ∀ f ∈ damair.map (·.2.2) ++ ishara.map (·.2) ++ mawsulKhass.map (·.2),
    ∀ g ∈ damair.map (·.2.2) ++ ishara.map (·.2) ++ mawsulKhass.map (·.2), featCode f = featCode g → f = g := by
  decide

/-- **السِّمةُ والإحالةُ تغيّران ‎n‎ والدالُّ واحد:** ‎هما‎ للمذكّرين وللمؤنّثتين، و‎هو‎ بمرجعٍ سابقٍ وبالشأن. -/
theorem maqam_value (dal : Nat) :
    refEnc dal (3, 0, 1) 1 ≠ refEnc dal (3, 1, 1) 1 ∧ refEnc dal (3, 0, 0) 1 ≠ refEnc dal (3, 0, 0) shaan := by
  constructor
  · intro h; have := (pair_injective (pair_injective h).2).1; simp [featCode] at this
  · intro h; have := (pair_injective (pair_injective h).2).2; simp [shaan] at this

end Maqam
end SLGE
