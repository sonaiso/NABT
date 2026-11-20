import A116.Tawafiq
import A116.Mizan
import A116.TawafiqMasfufaData

/-!
# عددُ المرخَّص لكلّ طول: مصفوفةُ انتقال الميزان (STEP-0010، يسدّ `TAWAFIQ_CLOSED_FORM_NOT_PROVEN`)

`Tawafiq.wasl n` و`Tawafiq.waqf n` عدّان على ‎113^n‎ سلسلة، مبرهَنان بـ`decide` للطولين 1 و2 وحدَهما، والثالثُ
مطابَقٌ لا مبرهَن (ADR ٦٣). وهنا **صيغةٌ لكلّ n**:

‎wasl n = uᵀ · Mⁿ · a‎

حيث M مصفوفةُ انتقال آلة الحرف (`Harf.wasl`، 42 حالًا، ADR ٤٢): ‎M[s][t]‎ عددُ الخانات المرخَّصة (113) التي تنقل
الحالَ s إلى t؛ و`a` متّجهُ القبول (‎a[t] = 1‎ إن قبلت `Harf.qabilWasl` الحالَ t)؛ و`u` متّجهُ الابتداء (حالُ `bad'`).
ووقفًا كذلك بـ`Harf.waqf` و`Harf.qabilWaqf`.

* `count_eq`: لكلّ آلةٍ منتهية ولكلّ أبجديّة، عددُ الكلمات المقبولة بطول n هو العدُّ التراجعيّ `cnt` — بالاستقراء.
* `cnt_succ_mat`: العدُّ التراجعيُّ ضربُ مصفوفةٍ في متّجه، على أيّ قائمة حالاتٍ بلا تكرارٍ تحوي كلَّ انتقال.
* `cnt_pow`: ‎cnt n = Mⁿ a‎ (`pow`).
* `wasl_mat`، `waqf_mat`: **الصيغةُ لكلّ n** على خانات الغانم، من `HarfBridge.wasl_eq_strictB` و`waqf_eq_strictPauseB`.
* `wasl_list`، `waqf_list`: المتّجهُ مقصورًا على قائمة الحالات (`Mizan.hal_nodup`)، فيُحسب بضرب مصفوفةٍ 42 × 42 لا بعدّ
  ‎113^n‎ سلسلة؛ ومنه القيمُ الأولى (`wasl_qiyam`، `waqf_qiyam`؛ مبرهنٌ على الشاهد).
* `row_sum`، `rows_113`: كلُّ صفٍّ مجموعُه حجمُ الأبجديّة.
* `wasl_rec`، `waqf_rec`: تكرارٌ ثلاثيٌّ لكلّ n؛ و`wasl_eq_seq`، `waqf_eq_seq`: العددُ لكلّ n هو المتتاليةُ المعرَّفة بالقيم الأولى والتكرار.

الحدُّ (معلن): هذه صيغةٌ بالمصفوفة لكلّ n لا صيغةٌ جبريّةٌ بالقوى المميّزة (`TAWAFIQ_EIGEN_FORM_NOT_WRITTEN`)؛ والأبجديّةُ
113 خانةً بقيد `Alif.licensable`، فثغرةُ `ALIF_CLOSER_NOT_REFUSED` داخلَ الأعداد كما هي في `Tawafiq`.
-/

set_option autoImplicit false

namespace A116.TawafiqMasfufa

open A116 A116.Hadd HarfBridge

section Amm

variable {α S : Type}

/-- طيُّ الآلة على الكلمة. -/
def runA (f : S → α → S) : S → List α → S
  | s, [] => s
  | s, x :: t => runA f (f s x) t

/-- كلُّ الكلمات بطول n من الأبجديّة. -/
def words (A : List α) : Nat → List (List α)
  | 0 => [[]]
  | n + 1 => A.flatMap fun c => (words A n).map (c :: ·)

/-- العدُّ التراجعيّ: كم كلمةً بطول n تقبلها الآلةُ من الحال s. -/
def cnt (A : List α) (f : S → α → S) (acc : S → Bool) : Nat → S → Nat
  | 0, s => if acc s then 1 else 0
  | n + 1, s => (A.map fun x => cnt A f acc n (f s x)).sum

theorem count_aux (A : List α) (f : S → α → S) (acc : S → Bool) (n : Nat)
    (ih : ∀ s, ((words A n).filter fun w => acc (runA f s w)).length = cnt A f acc n s)
    (s : S) : ∀ B : List α,
    ((B.flatMap fun c => (words A n).map (c :: ·)).filter fun w => acc (runA f s w)).length =
      (B.map fun x => cnt A f acc n (f s x)).sum
  | [] => rfl
  | c :: B => by
    rw [List.flatMap_cons, List.filter_append, List.length_append, count_aux A f acc n ih s B,
      List.map_cons, List.sum_cons, List.filter_map, List.length_map]
    congr 1
    exact ih (f s c)

/-- **العدُّ صحيحٌ لكلّ طول**: عددُ الكلمات المقبولة بطول n هو `cnt n`. -/
theorem count_eq (A : List α) (f : S → α → S) (acc : S → Bool) :
    ∀ n s, ((words A n).filter fun w => acc (runA f s w)).length = cnt A f acc n s
  | 0, s => by
    simp only [words, cnt]
    cases h : acc s <;> simp [runA, h]
  | n + 1, s => count_aux A f acc n (count_eq A f acc n) s A

variable [DecidableEq S]

/-- مدخلُ المصفوفة: كم حرفًا ينقل s إلى t. -/
def mat (A : List α) (f : S → α → S) (s t : S) : Nat := (A.filter fun x => f s x = t).length

/-- ضربُ المصفوفة في المتّجه على قائمة الحالات L. -/
def mul (L : List S) (A : List α) (f : S → α → S) (v : S → Nat) (s : S) : Nat :=
  (L.map fun t => mat A f s t * v t).sum

omit [DecidableEq S] in
theorem sum_zero : ∀ L : List S, (L.map fun _ => (0 : Nat)).sum = 0
  | [] => rfl
  | _ :: L => by rw [List.map_cons, List.sum_cons, sum_zero L]

theorem sum_ite (v : S → Nat) (y : S) : ∀ L : List S, L.Nodup → y ∈ L →
    (L.map fun t => (if y = t then 1 else 0) * v t).sum = v y
  | [], _, h => absurd h (List.not_mem_nil)
  | t :: L, hn, hy => by
    rw [List.map_cons, List.sum_cons]
    rcases List.nodup_cons.mp hn with ⟨htL, hL⟩
    by_cases e : y = t
    · subst e
      have : (L.map fun t => (if y = t then 1 else 0) * v t).sum = 0 := by
        have z : ∀ t ∈ L, (if y = t then 1 else 0) * v t = 0 := by
          intro t ht
          have : y ≠ t := fun h => htL (h ▸ ht)
          simp [this]
        rw [List.map_congr_left z, sum_zero]
      rw [this]; simp
    · have hy' : y ∈ L := by
        rcases List.mem_cons.mp hy with h | h
        · exact absurd h e
        · exact h
      rw [sum_ite v y L hL hy']; simp [e]

omit [DecidableEq S] in
theorem sum_add (L : List S) (g h : S → Nat) :
    (L.map fun t => g t + h t).sum = (L.map g).sum + (L.map h).sum := by
  induction L with
  | nil => rfl
  | cons t L ih => simp only [List.map_cons, List.sum_cons, ih]; omega

theorem mat_cons (A : List α) (f : S → α → S) (x : α) (s t : S) :
    mat (x :: A) f s t = (if f s x = t then 1 else 0) + mat A f s t := by
  unfold mat
  by_cases h : f s x = t <;> simp [h, Nat.add_comm]

theorem sum_mat (L : List S) (hL : L.Nodup) (f : S → α → S) (s : S) (v : S → Nat)
    (hm : ∀ x, f s x ∈ L) : ∀ A : List α,
    (A.map fun x => v (f s x)).sum = mul L A f v s
  | [] => by
    simp only [List.map_nil, List.sum_nil, mul, mat, List.filter_nil, List.length_nil, Nat.zero_mul]
    exact (sum_zero L).symm
  | x :: A => by
    rw [List.map_cons, List.sum_cons, sum_mat L hL f s v hm A, ← sum_ite v (f s x) L hL (hm x)]
    unfold mul
    rw [← sum_add]
    congr 1
    apply List.map_congr_left
    intro t _
    rw [mat_cons, Nat.add_mul]

/-- **العدُّ ضربُ مصفوفة**: الطولُ ‎n+1‎ من الطول n بضربه في M. -/
theorem cnt_succ_mat (L : List S) (hL : L.Nodup) (A : List α) (f : S → α → S) (acc : S → Bool)
    (hm : ∀ s x, f s x ∈ L) (n : Nat) (s : S) :
    cnt A f acc (n + 1) s = mul L A f (cnt A f acc n) s := by
  rw [cnt]
  exact sum_mat L hL f s (cnt A f acc n) (hm s) A

/-- **كلُّ صفٍّ مجموعُه حجمُ الأبجديّة**: كلُّ حرفٍ ينقل كلَّ حالٍ إلى حالٍ واحدٍ من L. -/
theorem row_sum (L : List S) (hL : L.Nodup) (A : List α) (f : S → α → S) (hm : ∀ s x, f s x ∈ L) (s : S) :
    (L.map fun t => mat A f s t).sum = A.length := by
  have e : (A.map fun _ => (1 : Nat)).sum = A.length := by
    induction A with
    | nil => rfl
    | cons _ A ih => rw [List.map_cons, List.sum_cons, ih, List.length_cons, Nat.add_comm]
  have h := sum_mat L hL f s (fun _ => 1) (hm s) A
  rw [e] at h
  rw [h, mul]
  congr 1
  apply List.map_congr_left
  intro t _
  rw [Nat.mul_one]

/-- متّجهُ القبول. -/
def accV (acc : S → Bool) (s : S) : Nat := if acc s then 1 else 0

/-- ‎Mⁿ a‎: القوّةُ n للمصفوفة مضروبةً في متّجه القبول. -/
def pow (L : List S) (A : List α) (f : S → α → S) (acc : S → Bool) : Nat → S → Nat
  | 0 => accV acc
  | n + 1 => mul L A f (pow L A f acc n)

/-- **‎cnt n = Mⁿ a‎** لكلّ n. -/
theorem cnt_pow (L : List S) (hL : L.Nodup) (A : List α) (f : S → α → S) (acc : S → Bool)
    (hm : ∀ s x, f s x ∈ L) : ∀ n, cnt A f acc n = pow L A f acc n
  | 0 => by funext s; rfl
  | n + 1 => by
    funext s
    rw [cnt_succ_mat L hL A f acc hm n s, cnt_pow L hL A f acc hm n]; rfl

/-! ### المتّجهُ قائمةً على L: ما يُحسب -/

/-- صفوفُ المصفوفة على L. -/
def matL (L : List S) (A : List α) (f : S → α → S) : List (List Nat) :=
  L.map fun s => L.map fun t => mat A f s t

def dot (r v : List Nat) : Nat := (List.zipWith (· * ·) r v).sum

def stepL (M : List (List Nat)) (v : List Nat) : List Nat := M.map fun r => dot r v

def iterL (M : List (List Nat)) (v0 : List Nat) : Nat → List Nat
  | 0 => v0
  | n + 1 => stepL M (iterL M v0 n)

omit [DecidableEq S] in
theorem dot_map (L : List S) (g h : S → Nat) :
    dot (L.map g) (L.map h) = (L.map fun t => g t * h t).sum := by
  induction L with
  | nil => rfl
  | cons t L ih =>
    simp only [dot, List.map_cons, List.zipWith_cons_cons, List.sum_cons] at ih ⊢
    rw [ih]

theorem iterL_eq (L : List S) (hL : L.Nodup) (A : List α) (f : S → α → S) (acc : S → Bool)
    (hm : ∀ s x, f s x ∈ L) : ∀ n,
    iterL (matL L A f) (L.map (accV acc)) n = L.map (cnt A f acc n)
  | 0 => by simp [iterL, cnt, accV]
  | n + 1 => by
    rw [iterL, iterL_eq L hL A f acc hm n, stepL, matL, List.map_map]
    apply List.map_congr_left
    intro s _
    simp only [Function.comp, dot_map]
    rw [cnt_succ_mat L hL A f acc hm n s]; rfl

end Amm

/-! ## على خانات الغانم -/

/-- خطوتا الآلة على خانة الغانم. -/
def fW (s : Harf.Hal) (c : Cell) : Harf.Hal := Harf.wasl s (unproj c)
def fQ (s : Harf.Hal) (c : Cell) : Harf.Hal := Harf.waqf s (unproj c)

theorem run_toH (g : Harf.Hal → Harf.Khana → Harf.Hal) : ∀ (s : Harf.Hal) (w : List Cell),
    Harf.run g s (Mizan.toH w) = runA (fun s c => g s (unproj c)) s w
  | _, [] => rfl
  | s, c :: w => run_toH g (g s (unproj c)) w

theorem seqs_words : ∀ n, Tawafiq.seqs n = words Alif.licensable n
  | 0 => rfl
  | n + 1 => by rw [Tawafiq.seqs, words, seqs_words n]

theorem strictB_run (w : List Cell) : strictB w = Harf.qabilWasl (runA fW .bad' w) := by
  have h := wasl_eq_strictB (Mizan.toH w)
  rw [Mizan.projW_toH] at h
  rw [← h, Harf.waslB, run_toH]; rfl

theorem strictPauseB_run (w : List Cell) : strictPauseB w = Harf.qabilWaqf (runA fQ .bad' w) := by
  have h := waqf_eq_strictPauseB (Mizan.toH w)
  rw [Mizan.projW_toH] at h
  rw [← h, Harf.waqfB, run_toH]; rfl

/-- **الوصلُ لكلّ طول عدٌّ تراجعيّ على الآلة.** -/
theorem wasl_cnt (n : Nat) : Tawafiq.wasl n = cnt Alif.licensable fW Harf.qabilWasl n .bad' := by
  rw [← count_eq, ← seqs_words, Tawafiq.wasl]
  congr 1
  apply List.filter_congr
  intro w _
  exact strictB_run w

theorem waqf_cnt (n : Nat) : Tawafiq.waqf n = cnt Alif.licensable fQ Harf.qabilWaqf n .bad' := by
  rw [← count_eq, ← seqs_words, Tawafiq.waqf]
  congr 1
  apply List.filter_congr
  intro w _
  exact strictPauseB_run w

theorem hm (f : Harf.Hal → Cell → Harf.Hal) : ∀ s x, f s x ∈ Harf.Hal.all :=
  fun _ _ => Harf.Hal.mem_all _

/-- **‎wasl n = uᵀ Mⁿ a‎ لكلّ n**: الطولُ n قيمةُ القوّة n لمصفوفة انتقال الوصل عند حال الابتداء. -/
theorem wasl_mat (n : Nat) :
    Tawafiq.wasl n = pow Harf.Hal.all Alif.licensable fW Harf.qabilWasl n .bad' := by
  rw [wasl_cnt, cnt_pow Harf.Hal.all Mizan.hal_nodup Alif.licensable fW _ (hm fW)]

/-- **ووقفًا ‎waqf n = uᵀ Qⁿ a′‎ لكلّ n.** -/
theorem waqf_mat (n : Nat) :
    Tawafiq.waqf n = pow Harf.Hal.all Alif.licensable fQ Harf.qabilWaqf n .bad' := by
  rw [waqf_cnt, cnt_pow Harf.Hal.all Mizan.hal_nodup Alif.licensable fQ _ (hm fQ)]

/-- مصفوفتا الانتقال صفوفًا (42 × 42)، ومتّجها القبول. -/
def MW : List (List Nat) := matL Harf.Hal.all Alif.licensable fW
def MQ : List (List Nat) := matL Harf.Hal.all Alif.licensable fQ
def aW : List Nat := Harf.Hal.all.map (accV Harf.qabilWasl)
def aQ : List Nat := Harf.Hal.all.map (accV Harf.qabilWaqf)

/-- **المحسوبُ هو العدد**: رأسُ ‎Mⁿ a‎ على القائمة هو `wasl n`، لكلّ n (`bad'` أوّلُ الحالات، `Mizan.bad_first`). -/
theorem wasl_list (n : Nat) : (iterL MW aW n).head? = some (Tawafiq.wasl n) := by
  rw [MW, aW, iterL_eq Harf.Hal.all Mizan.hal_nodup Alif.licensable fW _ (hm fW), wasl_cnt]; rfl

theorem waqf_list (n : Nat) : (iterL MQ aQ n).head? = some (Tawafiq.waqf n) := by
  rw [MQ, aQ, iterL_eq Harf.Hal.all Mizan.hal_nodup Alif.licensable fQ _ (hm fQ), waqf_cnt]; rfl

/-- كلُّ صفٍّ في مصفوفتَي الوصل والوقف مجموعُه 113 (`Alif.licensable_length`). -/
theorem rows_113 (f : Harf.Hal → Cell → Harf.Hal) (s : Harf.Hal) :
    (Harf.Hal.all.map fun t => mat Alif.licensable f s t).sum = 113 := by
  rw [row_sum Harf.Hal.all Mizan.hal_nodup Alif.licensable f (hm f) s, Alif.licensable_length]

/-! ## المصفوفتان حرفيّتين: الجدولُ المولَّد هو المصفوفةُ بعينها

`TawafiqMasfufaData` يطبعه Lean المترجَم (`lake exe a116-table masfufa-lean`) ويُطابَق في CI، والنواةُ تفحص هنا أنّه
`MW` و`MQ` بعينهما؛ فالحسابُ بعدُ على أعدادٍ لا على آلة. -/

theorem MW_eq : MW = TawafiqMasfufaData.wL := by decide +kernel
theorem MQ_eq : MQ = TawafiqMasfufaData.qL := by decide +kernel
theorem aW_eq : aW = TawafiqMasfufaData.aWL := by decide +kernel
theorem aQ_eq : aQ = TawafiqMasfufaData.aQL := by decide +kernel

theorem wasl_of (n v : Nat) (h : (iterL TawafiqMasfufaData.wL TawafiqMasfufaData.aWL n).head? = some v) :
    Tawafiq.wasl n = v := by
  rw [← MW_eq, ← aW_eq, wasl_list] at h; exact Option.some.inj h

theorem waqf_of (n v : Nat) (h : (iterL TawafiqMasfufaData.qL TawafiqMasfufaData.aQL n).head? = some v) :
    Tawafiq.waqf n = v := by
  rw [← MQ_eq, ← aQ_eq, waqf_list] at h; exact Option.some.inj h

/-- القيمُ الأولى وصلًا (الأطوالُ 0–6): الثالثُ كان مطابَقًا لا مبرهَنًا (ADR ٦٣). -/
theorem wasl_qiyam :
    Tawafiq.wasl 0 = 1 ∧ Tawafiq.wasl 1 = 84 ∧ Tawafiq.wasl 2 = 9492 ∧ Tawafiq.wasl 3 = 1001953 ∧
    Tawafiq.wasl 4 = 107293617 ∧ Tawafiq.wasl 5 = 11454218577 ∧ Tawafiq.wasl 6 = 1223605775448 :=
  ⟨wasl_of 0 1 (by decide +kernel), wasl_of 1 84 (by decide +kernel), wasl_of 2 9492 (by decide +kernel),
   wasl_of 3 1001953 (by decide +kernel), wasl_of 4 107293617 (by decide +kernel),
   wasl_of 5 11454218577 (by decide +kernel), wasl_of 6 1223605775448 (by decide +kernel)⟩

/-- والقيمُ الأولى وقفًا (الأطوالُ 0–7). -/
theorem waqf_qiyam :
    Tawafiq.waqf 0 = 1 ∧ Tawafiq.waqf 1 = 84 ∧ Tawafiq.waqf 2 = 9492 ∧ Tawafiq.waqf 3 = 1072596 ∧
    Tawafiq.waqf 4 = 113230177 ∧ Tawafiq.waqf 5 = 12124976049 ∧ Tawafiq.waqf 6 = 1294416797265 ∧
    Tawafiq.waqf 7 = 138276963960489 :=
  ⟨waqf_of 0 1 (by decide +kernel), waqf_of 1 84 (by decide +kernel), waqf_of 2 9492 (by decide +kernel),
   waqf_of 3 1072596 (by decide +kernel), waqf_of 4 113230177 (by decide +kernel),
   waqf_of 5 12124976049 (by decide +kernel), waqf_of 6 1294416797265 (by decide +kernel),
   waqf_of 7 138276963960489 (by decide +kernel)⟩

/-! ## التكرارُ لكلّ n: ‎x³ = 84x² + 2436x + 84‎

يكفي أن يصدق التكرارُ على المتّجه مرّةً واحدة (‎M⁷a = 84M⁶a + 2436M⁵a + 84M⁴a‎، يُفحص بالنواة)، ثمّ يسري إلى كلّ n
لأنّ الضربَ في M خطّيّ (`mul_lin`، `pow_rec`). -/

section Rec

variable {α S : Type} [DecidableEq S]

omit [DecidableEq S] in
theorem sum_smul (L : List S) (c : Nat) (g : S → Nat) :
    (L.map fun t => c * g t).sum = c * (L.map g).sum := by
  induction L with
  | nil => simp
  | cons t L ih => simp only [List.map_cons, List.sum_cons, ih, Nat.mul_add]

theorem mul_lin (L : List S) (A : List α) (f : S → α → S) (a b c : Nat) (u v w : S → Nat) (s : S) :
    mul L A f (fun t => a * u t + b * v t + c * w t) s
      = a * mul L A f u s + b * mul L A f v s + c * mul L A f w s := by
  unfold mul
  rw [← sum_smul, ← sum_smul, ← sum_smul, ← sum_add, ← sum_add]
  congr 1
  apply List.map_congr_left
  intro t _
  rw [Nat.mul_add, Nat.mul_add, Nat.mul_left_comm, Nat.mul_left_comm (mat A f s t) b,
    Nat.mul_left_comm (mat A f s t) c]

/-- **التكرارُ يسري**: إن صدق عند k صدق عند كلّ ‎n + k‎. -/
theorem pow_rec (L : List S) (A : List α) (f : S → α → S) (acc : S → Bool) (a b c k : Nat)
    (h0 : ∀ s, pow L A f acc (k + 3) s =
      a * pow L A f acc (k + 2) s + b * pow L A f acc (k + 1) s + c * pow L A f acc k s) :
    ∀ n s, pow L A f acc (n + k + 3) s =
      a * pow L A f acc (n + k + 2) s + b * pow L A f acc (n + k + 1) s + c * pow L A f acc (n + k) s
  | 0, s => by simpa using h0 s
  | n + 1, s => by
    have ih : pow L A f acc (n + k + 3) = fun t =>
        a * pow L A f acc (n + k + 2) t + b * pow L A f acc (n + k + 1) t + c * pow L A f acc (n + k) t :=
      funext (pow_rec L A f acc a b c k h0 n)
    rw [show n + 1 + k + 3 = (n + k + 3) + 1 by omega, show n + 1 + k + 2 = (n + k + 2) + 1 by omega,
      show n + 1 + k + 1 = (n + k + 1) + 1 by omega, show n + 1 + k = (n + k) + 1 by omega,
]
    have e := mul_lin L A f a b c (pow L A f acc (n + k + 2)) (pow L A f acc (n + k + 1)) (pow L A f acc (n + k)) s
    rw [← ih] at e
    exact e

/-- التركيبُ الخطّيُّ على القوائم. -/
def lin3 (a b c : Nat) : List Nat → List Nat → List Nat → List Nat
  | x :: xs, y :: ys, z :: zs => (a * x + b * y + c * z) :: lin3 a b c xs ys zs
  | _, _, _ => []

omit [DecidableEq S] in
theorem lin3_map (a b c : Nat) (g h k : S → Nat) : ∀ L : List S,
    lin3 a b c (L.map g) (L.map h) (L.map k) = L.map fun s => a * g s + b * h s + c * k s
  | [] => rfl
  | t :: L => by simp only [List.map_cons, lin3, lin3_map a b c g h k L]

end Rec

theorem pow_list (f : Harf.Hal → Cell → Harf.Hal) (acc : Harf.Hal → Bool) (n : Nat) :
    iterL (matL Harf.Hal.all Alif.licensable f) (Harf.Hal.all.map (accV acc)) n =
      Harf.Hal.all.map (pow Harf.Hal.all Alif.licensable f acc n) := by
  rw [iterL_eq Harf.Hal.all Mizan.hal_nodup Alif.licensable f acc (hm f),
    cnt_pow Harf.Hal.all Mizan.hal_nodup Alif.licensable f acc (hm f)]

theorem base_of (f : Harf.Hal → Cell → Harf.Hal) (acc : Harf.Hal → Bool) (k : Nat)
    (h : iterL (matL Harf.Hal.all Alif.licensable f) (Harf.Hal.all.map (accV acc)) (k + 3) =
      lin3 84 2436 84 (iterL (matL Harf.Hal.all Alif.licensable f) (Harf.Hal.all.map (accV acc)) (k + 2))
        (iterL (matL Harf.Hal.all Alif.licensable f) (Harf.Hal.all.map (accV acc)) (k + 1))
        (iterL (matL Harf.Hal.all Alif.licensable f) (Harf.Hal.all.map (accV acc)) k)) :
    ∀ s, pow Harf.Hal.all Alif.licensable f acc (k + 3) s =
      84 * pow Harf.Hal.all Alif.licensable f acc (k + 2) s +
        2436 * pow Harf.Hal.all Alif.licensable f acc (k + 1) s +
          84 * pow Harf.Hal.all Alif.licensable f acc k s := by
  rw [pow_list, pow_list, pow_list, pow_list, lin3_map] at h
  intro s
  exact List.map_inj_left.mp h s (Harf.Hal.mem_all s)

/-- الأساسُ وصلًا: ‎M⁷a = 84M⁶a + 2436M⁵a + 84M⁴a‎ على كلّ الحالات (على الشاهد، بالنواة). -/
theorem base_wasl : ∀ s, pow Harf.Hal.all Alif.licensable fW Harf.qabilWasl 7 s =
    84 * pow Harf.Hal.all Alif.licensable fW Harf.qabilWasl 6 s +
      2436 * pow Harf.Hal.all Alif.licensable fW Harf.qabilWasl 5 s +
        84 * pow Harf.Hal.all Alif.licensable fW Harf.qabilWasl 4 s := by
  apply base_of fW Harf.qabilWasl 4
  show iterL MW aW 7 = lin3 84 2436 84 (iterL MW aW 6) (iterL MW aW 5) (iterL MW aW 4)
  rw [MW_eq, aW_eq]; decide +kernel

/-- والأساسُ وقفًا: ‎Q⁸a′ = 84Q⁷a′ + 2436Q⁶a′ + 84Q⁵a′‎. -/
theorem base_waqf : ∀ s, pow Harf.Hal.all Alif.licensable fQ Harf.qabilWaqf 8 s =
    84 * pow Harf.Hal.all Alif.licensable fQ Harf.qabilWaqf 7 s +
      2436 * pow Harf.Hal.all Alif.licensable fQ Harf.qabilWaqf 6 s +
        84 * pow Harf.Hal.all Alif.licensable fQ Harf.qabilWaqf 5 s := by
  apply base_of fQ Harf.qabilWaqf 5
  show iterL MQ aQ 8 = lin3 84 2436 84 (iterL MQ aQ 7) (iterL MQ aQ 6) (iterL MQ aQ 5)
  rw [MQ_eq, aQ_eq]; decide +kernel

/-- **عددُ المرخَّص وصلًا لكلّ طول**: ‎wasl(n+7) = 84·wasl(n+6) + 2436·wasl(n+5) + 84·wasl(n+4)‎، ومع
`wasl_qiyam` يتعيّن العددُ لكلّ n. -/
theorem wasl_rec (n : Nat) :
    Tawafiq.wasl (n + 7) = 84 * Tawafiq.wasl (n + 6) + 2436 * Tawafiq.wasl (n + 5) + 84 * Tawafiq.wasl (n + 4) := by
  have h := pow_rec Harf.Hal.all Alif.licensable fW Harf.qabilWasl 84 2436 84 4 base_wasl n .bad'
  rw [wasl_mat, wasl_mat, wasl_mat, wasl_mat]
  exact h

/-- **وعددُ المرخَّص وقفًا لكلّ طول**: ‎waqf(n+8) = 84·waqf(n+7) + 2436·waqf(n+6) + 84·waqf(n+5)‎. -/
theorem waqf_rec (n : Nat) :
    Tawafiq.waqf (n + 8) = 84 * Tawafiq.waqf (n + 7) + 2436 * Tawafiq.waqf (n + 6) + 84 * Tawafiq.waqf (n + 5) := by
  have h := pow_rec Harf.Hal.all Alif.licensable fQ Harf.qabilWaqf 84 2436 84 5 base_waqf n .bad'
  rw [waqf_mat, waqf_mat, waqf_mat, waqf_mat]
  exact h

/-- المتتاليةُ المعرَّفة بالقيم الأولى والتكرار، وصلًا. -/
def seqW : Nat → Nat
  | 0 => 1 | 1 => 84 | 2 => 9492 | 3 => 1001953 | 4 => 107293617 | 5 => 11454218577 | 6 => 1223605775448
  | n + 7 => 84 * seqW (n + 6) + 2436 * seqW (n + 5) + 84 * seqW (n + 4)

/-- ووقفًا. -/
def seqQ : Nat → Nat
  | 0 => 1 | 1 => 84 | 2 => 9492 | 3 => 1072596 | 4 => 113230177 | 5 => 12124976049 | 6 => 1294416797265
  | 7 => 138276963960489
  | n + 8 => 84 * seqQ (n + 7) + 2436 * seqQ (n + 6) + 84 * seqQ (n + 5)

/-- **العددُ وصلًا لكلّ طول هو `seqW`.** -/
theorem wasl_eq_seq : ∀ n, Tawafiq.wasl n = seqW n
  | 0 => wasl_qiyam.1
  | 1 => wasl_qiyam.2.1
  | 2 => wasl_qiyam.2.2.1
  | 3 => wasl_qiyam.2.2.2.1
  | 4 => wasl_qiyam.2.2.2.2.1
  | 5 => wasl_qiyam.2.2.2.2.2.1
  | 6 => wasl_qiyam.2.2.2.2.2.2
  | n + 7 => by
    rw [wasl_rec, wasl_eq_seq (n + 6), wasl_eq_seq (n + 5), wasl_eq_seq (n + 4)]; rfl

/-- **والعددُ وقفًا لكلّ طول هو `seqQ`.** -/
theorem waqf_eq_seq : ∀ n, Tawafiq.waqf n = seqQ n
  | 0 => waqf_qiyam.1
  | 1 => waqf_qiyam.2.1
  | 2 => waqf_qiyam.2.2.1
  | 3 => waqf_qiyam.2.2.2.1
  | 4 => waqf_qiyam.2.2.2.2.1
  | 5 => waqf_qiyam.2.2.2.2.2.1
  | 6 => waqf_qiyam.2.2.2.2.2.2.1
  | 7 => waqf_qiyam.2.2.2.2.2.2.2
  | n + 8 => by
    rw [waqf_rec, waqf_eq_seq (n + 7), waqf_eq_seq (n + 6), waqf_eq_seq (n + 5)]; rfl

end A116.TawafiqMasfufa
