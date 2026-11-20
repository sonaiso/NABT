import A116.NizamLine

/-!
# السطرُ وأزواجُه، والكلمةُ الفارغة (ADR ٣٢)

شاهدان على تعريف `NizamLine.strictLineB` نفسِه، وحلّ:

* `empty_word_smuggles_straddle`: كلمةٌ فارغةٌ بين «يَا» و«الشَّافِعِينَ» تجعل `crossStr` كاذبًا على جانبيها فيسقط فحصُ
  الحدّ بين جارتيها — `strictLineB [يَا، []، شْشَافِعِينَ] = true` و`strictLineB [يَا، شْشَافِعِينَ] = false`
  (`EMPTY_WORD_SMUGGLES_STRADDLE`).
* الحلّ: الكلمةُ الفارغةُ محايدُ السطر فتُحذف قبل الحكم — `strictLineN`؛ لا يتغيّر بكلمةٍ فارغةٍ في أيّ موضع
  (`strictLineN_erase_empty`)، وهو `strictLineB` بعينه على السطور بلا كلمةٍ فارغة (`strictLineN_nonempty`).
* `pairwise_needs_vowel_start`: قرانُ الأزواج (`pairA`: `strictJoinB` لكلّ متجاورتين) يفترق عن السطر حين تبتدئ
  كلمةٌ داخليّةٌ بساكن («قُلِ لْحَمْدُ لِلَّهِ»). وأنّ هذا هو الافتراقُ الوحيد — السطرُ قرانُ أزواجه إن بدأت كلُّ كلمةٍ
  بعد الأولى بمتحرّك — مبرهَنٌ في Algebra على هذه التعريفات بأعيانها (`HarfBridge.line_eq_pairwise`، ADR ٥ هناك،
  بتثبيت الغانم عند `df76f39`)؛ ولا يُعاد هنا.
-/

set_option autoImplicit false

namespace A116.LineEmpty

open A116 A116.Hadd A116.NizamLine A116.Ladder Haraka

/-- **العيب**: الكلمةُ الفارغةُ تُسقط فحصَ الحدّ بين جارتيها. -/
theorem empty_word_smuggles_straddle :
    strictLineB [ya, [], shshafiina] = true ∧ strictLineB [ya, shshafiina] = false := by
  decide +kernel

def nonEmpty {β : Type} (ws : List (List β)) : List (List β) := ws.filter fun w => !w.isEmpty

/-- السطرُ بعد حذف محايده. -/
def strictLineN (ws : List (List Cell)) : Bool := strictLineB (nonEmpty ws)

theorem strictLineN_erase_empty (u v : List (List Cell)) :
    strictLineN (u ++ [] :: v) = strictLineN (u ++ v) := by
  simp [strictLineN, nonEmpty, List.filter_append]

theorem strictLineN_nonempty (ws : List (List Cell)) (hne : ∀ w ∈ ws, w ≠ []) :
    strictLineN ws = strictLineB ws := by
  unfold strictLineN nonEmpty
  rw [List.filter_eq_self.mpr]
  intro w hw
  cases w with
  | nil => exact absurd rfl (hne [] hw)
  | cons _ _ => rfl

theorem strictLineN_fixes_smuggling : strictLineN [ya, [], shshafiina] = false := by
  rw [show [ya, [], shshafiina] = [ya] ++ [] :: [shshafiina] from rfl, strictLineN_erase_empty]
  rw [strictLineN_nonempty _ (by decide)]
  exact empty_word_smuggles_straddle.2

/-- قرانُ الأزواج. -/
def pairTailA : List Cell → List (List Cell) → Bool
  | _, [] => true
  | v, u :: r => strictJoinB v u && pairTailA u r

def pairA : List (List Cell) → Bool
  | [] => true
  | [w] => strictB w
  | w :: v :: rest => strictJoinB w v && pairTailA v rest

def lillahi : List Cell := [atom 'ل' kasra, atom 'ل' sukun, atom 'ل' fatha, atom 'ه' kasra]

/-- **الشرطُ لازم**: كلمةٌ داخليّةٌ تبتدئ بساكن تفرّق السطرَ عن أزواجه. -/
theorem pairwise_needs_vowel_start :
    strictLineB [quli, lhamdu, lillahi] = true ∧ pairA [quli, lhamdu, lillahi] = false := by
  decide +kernel

end A116.LineEmpty
