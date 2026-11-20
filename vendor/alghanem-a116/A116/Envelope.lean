import A116.PauseCount

/-!
# «الغلاف» الثنائيّ والترخيصُ الثلاثيّ: العددُ واحدٌ والأعيانُ لا (ADR ١١)

الغلافُ كما ورد في النقاش (مقترَحٌ خارجيّ، لا مودَع): سلاسلُ على ‎{C، V}‎ بطول 2..12، تبدأ بـC وتنتهي بـC ولا
تتجاور فيها V وV. وقراءتُها على الأصناف الثلاثة: ‎C‎ تليها ‎V‎ متحرّكٌ (`cv`)، و‎C‎ لا تليها ‎V‎ مدٌّ (`v`) أو
ساكنٌ (`c`) — فالغلافُ أعمى عن الفرق بينهما كما الثنائيُّ أعمى عن المدّ (`binary_is_blind_to_madd`).

* `envelope_375`: عددُ الغلاف 375 — وهو مجموعُ المرخَّص وقفًا بالأوزان نفسها (`pause_count_375`)؛
* `envelope_licensed_75`: ومنه **75** فقط لها قراءةٌ مرخَّصةٌ وقفًا، و59 وصلًا (`envelope_licensed_continue_59`).

فالتوافقُ في العدد لا في الأعيان. البرهانُ حسابٌ على تعريف الغلاف المذكور بعينه (`decide +kernel`)،
مبرهنٌ على هذه الأطوال لا لكلّ طول. وهو عن تعريفٍ لا عن اللغة: الغلافُ اقتراحٌ يُقاس، لا معلومةٌ سابقة.
-/

namespace A116.Ternary

open A116.Stages K

/-- كلُّ السلاسل بطول `n` (‎true = C‎، ‎false = V‎). -/
def strs : Nat → List (List Bool)
  | 0 => [[]]
  | n + 1 => (strs n).map (true :: ·) ++ (strs n).map (false :: ·)

def noVV : List Bool → Bool
  | false :: false :: _ => false
  | _ :: t => noVV t
  | [] => true

/-- شرطُ الغلاف: يبدأ بـC، وينتهي بـC، ولا ‎VV‎. -/
def envOk (s : List Bool) : Bool := s.head? == some true && s.getLast? == some true && noVV s

def envelope (n : Nat) : List (List Bool) := (strs n).filter envOk

/-- خياراتُ كلّ موضع: ‎CV‎ متحرّك، و‎C‎ وحدَها مدٌّ أو ساكن، و‎V‎ بلا حاملٍ لا قراءةَ لها. -/
def choices : List Bool → List (List K)
  | true :: false :: t => [cv] :: choices t
  | true :: t => [v, c] :: choices t
  | false :: t => [] :: choices t
  | [] => []

def readings : List (List K) → List (List K)
  | [] => [[]]
  | o :: t => o.flatMap fun x => (readings t).map (x :: ·)

def pauseSome (s : List Bool) : Bool := (readings (choices s)).any pauseB
def continueSome (s : List Bool) : Bool := (readings (choices s)).any continueB

def total (f : List Bool → Bool) : Nat :=
  ((List.range 11).map fun i => ((envelope (i + 2)).filter f).length).sum

set_option maxRecDepth 100000 in
theorem envelope_375 : total (fun _ => true) = 375 := by decide +kernel

set_option maxRecDepth 100000 in
theorem envelope_licensed_75 : total pauseSome = 75 := by decide +kernel

set_option maxRecDepth 100000 in
theorem envelope_licensed_continue_59 : total continueSome = 59 := by decide +kernel

/-! ## لكلّ طولٍ من 2 إلى 12 (ADR ١٢)

الأعدادُ لكلّ طول، والتكراران عليها: الوصلُ ‎C(n) = C(n−1) + C(n−3)‎ (أبقارُ نارايانا، OEIS A000930)، والوقفُ
‎P(n) = P(n−2) + P(n−3) + P(n−4)‎ و‎3·P(n) = C(n+1) + C(n) + 2·C(n−1) − (−1)ⁿ‎. مبرهنٌ **على هذه الأطوال**
بالحساب؛ والبرهانُ لكلّ طول (آلةٌ على C/V حالاتُها مجموعاتُ حالات `δ`) دَينٌ مسمًّى. والوحدة: سلاسلُ غلافٍ
بالطول. -/

def perLength (f : List Bool → Bool) : List Nat :=
  (List.range 11).map fun i => ((envelope (i + 2)).filter f).length

set_option maxRecDepth 100000 in
theorem envelope_pause_per_length :
    perLength pauseSome = [0, 1, 1, 2, 2, 4, 5, 8, 11, 17, 24] := by decide +kernel

set_option maxRecDepth 100000 in
theorem envelope_continue_per_length :
    perLength continueSome = [0, 1, 1, 1, 2, 3, 4, 6, 9, 13, 19] := by decide +kernel

/-- التكراران على الأطوال المحسوبة (الفهرسُ ‎i‎ للطول ‎i+2‎). -/
theorem envelope_recurrences_upto_12 :
    (let c := [0, 1, 1, 1, 2, 3, 4, 6, 9, 13, 19]
     let p := [0, 1, 1, 2, 2, 4, 5, 8, 11, 17, 24]
     ((List.range 8).all fun i => c[i + 3]! == c[i + 2]! + c[i]!) &&
     ((List.range 7).all fun i => p[i + 4]! == p[i + 2]! + p[i + 1]! + p[i]!)) = true := by
  decide

end A116.Ternary
