/-
  Dal/Makharij.lean — تسمية الحالات الأربع، وجدول المخارج المعلَن (قرار المالك، 15 أكتوبر 2026).

  السند: مرفق المالك slge-closed.zip (بصمته b773980b…)، SLGE/Ladder.lean الأسطر 5–10 و36 و121،
  وSLGE/Law.lean السطر 8، وSLGE/Bridge.lean السطر 78:
  * الحالات: «فتحة 0، ضمّة 1، كسرة 2، سكون 3».
  * «مخارجُ الحوامل بترتيب وصف سيبويه في «الكتاب» (الجزء 4، ص431)، واللامُ مخرجًا مستقلًّا … فتصير
    خمسةَ عشرَ مخرجًا للحوامل، ومعها الخيشومُ ستّةَ عشر كما نصّ. الحواملُ بهذا الترتيب:
    ء ه ا | ع ح | غ خ | ق | ك | ج ش ي | ض | ل | ن | ر | ط د ت | ز س ص | ظ ذ ث | ف | ب م و
    فالألفُ 2، والياءُ 11، والواوُ 28.»
  * «المدُّ بعد الفتحة ألف، وبعد الضمّة واو، وبعد الكسرة ياء» (maddOf).
  * المودَع الشاهد كما أعلنه المالك هناك (SLGE/BridgeWitness.lean السطر 2):
    سيبويه 0180Sibawayhi.KitabSibawayhi.JK006989-ara1، sha256 a160f940bb194e6fe7e6655d2c7f28e41f1fc648c4c5e340cc4e42306d5cb625.

  الجدول **شاهدٌ معلَن لا نتيجة** (مطابَق لمرفق المالك)؛ وما يُبرهن هنا خواصُّ الجدول: عدده، وتفرّده،
  وتطابق مجموع المخارج مع الحوامل، ومواضع الألف والياء والواو، وتقابل (مخرج، موضع) ↔ حامل.
  بلا sorry ولا axiom ولا native_decide.
-/
import Dal.Khaliya

namespace Dal

/-! ## ١. الحالات الأربع بأسمائها -/

inductive HalaIsm | fatha | damma | kasra | sukun
deriving DecidableEq, Repr

def HalaIsm.ila : HalaIsm → Hala
  | .fatha => 0 | .damma => 1 | .kasra => 2 | .sukun => 3

def HalaIsm.min (h : Hala) : HalaIsm :=
  match h with
  | ⟨0, _⟩ => .fatha | ⟨1, _⟩ => .damma | ⟨2, _⟩ => .kasra | _ => .sukun

theorem hala_min_ila (h : HalaIsm) : HalaIsm.min h.ila = h := by cases h <;> rfl

theorem hala_ila_min (h : Hala) : (HalaIsm.min h).ila = h := by
  obtain ⟨v, hv⟩ := h
  match v, hv with
  | 0, _ => rfl | 1, _ => rfl | 2, _ => rfl | 3, _ => rfl

/-- الحركات ثلاث والسكون رابع: المتحرّك ما ليس ساكنًا. -/
def HalaIsm.mutaharrik : HalaIsm → Bool
  | .sukun => false
  | _ => true

theorem thalath_harakat : (([.fatha, .damma, .kasra, .sukun] : List HalaIsm).filter HalaIsm.mutaharrik).length = 3 := by
  decide

/-! ## ٢. جدول المخارج المعلَن -/

/-- الحوامل التسعة والعشرون بترتيب المخارج (الهمزة أوّلًا). -/
def hawamil : List Char :=
  ['ء', 'ه', 'ا', 'ع', 'ح', 'غ', 'خ', 'ق', 'ك', 'ج', 'ش', 'ي', 'ض', 'ل', 'ن', 'ر',
   'ط', 'د', 'ت', 'ز', 'س', 'ص', 'ظ', 'ذ', 'ث', 'ف', 'ب', 'م', 'و']

/-- أحجام المخارج الخمسة عشر بترتيبها. -/
def ahjam : List Nat := [3, 2, 2, 1, 1, 3, 1, 1, 1, 1, 3, 3, 3, 1, 3]

theorem hawamil_29 : hawamil.length = 29 := by decide
theorem hawamil_nodup : hawamil.Nodup := by decide
theorem makharij_15 : ahjam.length = 15 := by decide
theorem ahjam_sum : ahjam.sum = 29 := by decide
theorem ahjam_mawjaba : ahjam.all (0 < ·) = true := by decide

/-- مواضع حروف العلّة كما أعلنها المالك: الألف 2، الياء 11، الواو 28. -/
theorem alif_2 : hawamil[2]? = some 'ا' := by decide
theorem ya_11 : hawamil[11]? = some 'ي' := by decide
theorem waw_28 : hawamil[28]? = some 'و' := by decide

/-- حرف الحامل بموضعه. -/
def harf (c : Hamil) : Char := hawamil.getD c.val ' '

/-- المخرج ورتبة الحامل فيه: نجمع الأحجام حتّى نبلغ الموضع. -/
def makhrajMin : List Nat → Nat → Nat → Nat × Nat
  | [], _, c => (0, c)
  | s :: ss, i, c => if c < s then (i, c) else makhrajMin ss (i + 1) (c - s)

def makhraj (c : Hamil) : Nat × Nat := makhrajMin ahjam 0 c.val

/-- الحامل من (المخرج، الرتبة): مجموع أحجام ما قبله زائد الرتبة. -/
def hamilMin (m k : Nat) : Nat := (ahjam.take m).sum + k

/-- التقابل على الجدول كلّه: لكلّ حاملٍ مخرجٌ ورتبةٌ يعيدانه، والمخرج دون 15 والرتبة دون حجمه. -/
theorem makhraj_hamil : ∀ c : Fin 29,
    hamilMin (makhraj c).1 (makhraj c).2 = c.val ∧ (makhraj c).1 < 15 ∧
    (makhraj c).2 < ahjam.getD (makhraj c).1 0 := by decide

/-- ولكلّ (مخرج، رتبة) صحيحين حاملٌ دون 29 يعيدهما. -/
theorem hamil_makhraj : ∀ m : Fin 15, ∀ k : Fin 3, k.val < ahjam.getD m.val 0 →
    hamilMin m.val k.val < 29 ∧ makhrajMin ahjam 0 (hamilMin m.val k.val) = (m.val, k.val) := by
  decide

/-- الألف والياء والواو في ثلاثة مخارج مختلفة (الألف في الأوّل مع الهمزة والهاء). -/
theorem illa_mukhtalifa : (makhraj 2).1 = 0 ∧ (makhraj 11).1 = 5 ∧ (makhraj 28).1 = 14 := by decide

/-! ## ٣. المدّ: جدولٌ معلَن -/

/-- حامل المدّ لكلّ حركة: الفتحة ألف، الضمّة واو، الكسرة ياء. -/
def maddOf : HalaIsm → Option Hamil
  | .fatha => some 2
  | .damma => some 28
  | .kasra => some 11
  | .sukun => none

theorem madd_huruf_illa : (maddOf .fatha).map harf = some 'ا' ∧ (maddOf .damma).map harf = some 'و' ∧
    (maddOf .kasra).map harf = some 'ي' := by decide

theorem la_madd_lissukun : maddOf .sukun = none := rfl

end Dal
