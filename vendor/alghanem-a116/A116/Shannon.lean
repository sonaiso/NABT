import A116.Kraft

/-!
# اللوغاريتمُ مبنيًّا في النواة، وحدُّ شانون على شفرة hamil §١٧

قرارُ المالك (2026-10-12): «حدُّ شانون ‎H ≤ L‎ وقيمةُ ‎H = 2.3098‎ … قم ببنائه أنت» — بلا Mathlib، فلا حقيقيّات في المستودع.

## اللوغاريتمُ المبنيّ

`flog b n d := ⌊log₂((n/d)^b)⌋ = Nat.log2 (n^b / d^b)` — اللوغاريتمُ مضروبًا في b ومُقرَّبًا إلى أسفل، على الأعداد الطبيعيّة
وحدَها. وخاصّيّتُه المميِّزة مبرهَنةٌ **لكلّ** ‎n ≥ d > 0‎ (`flog_spec`): ‎2^a·d^b ≤ n^b < 2^(a+1)·d^b‎ — أي ‎a ≤ b·log₂(n/d) < a + 1‎
بقراءة الحقيقيّات؛ فهي تعريفُ اللوغاريتم بالقوى لا تقريبٌ له.

## حدُّ شانون بالأعداد الصحيحة

* `shannon_exact`: ‎N^N ≤ 2^bits · Π c^c‎ — وهي ‎H ≤ L‎ بعينها بعد أخذ ‎log₂‎ وقسمة N (H إنتروبيا الترددات، L الطولُ المتوسّط).
* `within_one_bit`: ‎2^bits · Π c^c < 2^N · N^N‎ — وهي ‎L < H + 1‎.
* `logCheck_spec`، `flog_eq`، `flog_values`: ‎aᵢ = ⌊b·log₂(N/cᵢ)⌋‎ بشهادة التربيع المتكرّر بدقّةٍ ثابتة لا بحساب ‎N^b‎.
* `entropy_bounds`: بـ‎b = 2¹⁸‎، ‎Σ cᵢ·aᵢ ≤ N·b·H < Σ cᵢ·(aᵢ + 1)‎ (من `flog_spec`)، والحسابُ يعطي
  ‎2.30975 ≤ H < 2.30977‎ — فـ«H = 2.3098» تقريبُ hamil إلى أربع منازل، والقيمةُ ‎2.30976…‎.

**الأعدادُ منقولة** (hamil `peeling_proof.md` §١٧، الإيداع ‎232821b‎) كما في `Kraft`؛ والمبرهَنُ الحسابُ. وقراءةُ الحدود قيمًا
لعددٍ حقيقيٍّ H رياضةٌ معلنة (رتابةُ log₂)، لا كائنٌ في Lean.
-/

set_option autoImplicit false
set_option exponentiation.threshold 1000000

namespace A116.Shannon

open A116.Kraft

/-- **اللوغاريتمُ المبنيّ**: ‎⌊b · log₂(n/d)⌋‎. -/
def flog (b n d : Nat) : Nat := Nat.log2 (n ^ b / d ^ b)

theorem pow_le_pow_left' {d n : Nat} (h : d ≤ n) : ∀ b : Nat, d ^ b ≤ n ^ b
  | 0 => Nat.le_refl _
  | b + 1 => by
    rw [Nat.pow_succ, Nat.pow_succ]
    exact Nat.mul_le_mul (pow_le_pow_left' h b) h

/-- **الخاصّيّةُ المميِّزة لكلّ ‎n ≥ d > 0‎**: ‎2^a·d^b ≤ n^b < 2^(a+1)·d^b‎. -/
theorem flog_spec (b n d : Nat) (hd : 0 < d) (hdn : d ≤ n) :
    2 ^ flog b n d * d ^ b ≤ n ^ b ∧ n ^ b < 2 ^ (flog b n d + 1) * d ^ b := by
  have hdb : 0 < d ^ b := Nat.pow_pos hd
  have hq : n ^ b / d ^ b ≠ 0 := by
    have : 1 ≤ n ^ b / d ^ b := (Nat.le_div_iff_mul_le hdb).2 (by simpa using pow_le_pow_left' hdn b)
    omega
  refine ⟨(Nat.le_div_iff_mul_le hdb).1 (Nat.log2_self_le hq), ?_⟩
  exact (Nat.div_lt_iff_lt_mul hdb).1 Nat.lt_log2_self

/-- حاصلُ ‎Π cᵢ^cᵢ‎. -/
def prodPow (l : List Nat) : Nat := l.foldl (fun p c => p * c ^ c) 1

/-- **‎H ≤ L‎** بالأعداد الصحيحة: ‎N^N ≤ 2^bits · Π c^c‎. -/
theorem shannon_exact : total ^ total ≤ 2 ^ bits * prodPow freqs := by decide +kernel

/-- **‎L < H + 1‎**: ‎2^bits · Π c^c < 2^N · N^N‎. -/
theorem within_one_bit : 2 ^ bits * prodPow freqs < 2 ^ total * total ^ total := by decide +kernel

/-- الدقّة: ‎b = 2¹⁸‎. -/
def prec : Nat := 2 ^ 18

/-! ## شهادةُ اللوغاريتم بالتربيع

حسابُ ‎n^(2¹⁸)‎ في النواة مباشرةً لا يتمّ (ملايينُ البتّات، يُقتل لنفاد الذاكرة). فيُشهَد بالتربيع المتكرّر بدقّةٍ ثابتة K بتًّا:
‎P/2^K‎ تقريبٌ سفليٌّ لـ‎(n/d)^(2^k)/2^e‎ و‎Q/2^K‎ علويٌّ، يُربَّع كلاهما ويُقطع (أرضًا للسفليّ وسقفًا للعلويّ) ويُنصَّف متى
جاوز 2. والثابتُ (`LowInv`، `UpInv`) مبرهَنٌ لكلّ خطوة، فإن انتهى السفليُّ ≥ 1 والعلويُّ < 2 بالأسّ نفسه a فذلك
‎2^a·d^b ≤ n^b < 2^(a+1)·d^b‎ (`logCheck_spec`) ولا يُحسب ‎n^b‎ قطّ. -/

/-- ثابتُ الدقّة الثابتة: P/2^K. -/
def normLow (K : Nat) : Nat → Nat × Nat → Nat × Nat
  | 0, x => x
  | f + 1, (P, e) => if 2 ^ (K + 1) ≤ P then normLow K f (P / 2, e + 1) else (P, e)

def normUp (K : Nat) : Nat → Nat × Nat → Nat × Nat
  | 0, x => x
  | f + 1, (Q, e) => if 2 ^ (K + 1) ≤ Q then normUp K f ((Q + 1) / 2, e + 1) else (Q, e)

def stepLow (K : Nat) (x : Nat × Nat) : Nat × Nat := normLow K 2 (x.1 * x.1 / 2 ^ K, 2 * x.2)
def stepUp (K : Nat) (x : Nat × Nat) : Nat × Nat :=
  normUp K 2 ((x.1 * x.1 + (2 ^ K - 1)) / 2 ^ K, 2 * x.2)

def runLow (K : Nat) : Nat → Nat × Nat → Nat × Nat
  | 0, x => x
  | s + 1, x => runLow K s (stepLow K x)
def runUp (K : Nat) : Nat → Nat × Nat → Nat × Nat
  | 0, x => x
  | s + 1, x => runUp K s (stepUp K x)

def initLow (K n d : Nat) : Nat × Nat := normLow K 64 (n * 2 ^ K / d, 0)
def initUp (K n d : Nat) : Nat × Nat := normUp K 64 ((n * 2 ^ K + (d - 1)) / d, 0)

/-- ‎P·D·2^e ≤ M·2^K‎ مع ‎D = d^(2^k)‎، ‎M = n^(2^k)‎. -/
def LowInv (K n d k : Nat) (x : Nat × Nat) : Prop := x.1 * d ^ (2 ^ k) * 2 ^ x.2 ≤ n ^ (2 ^ k) * 2 ^ K
def UpInv (K n d k : Nat) (x : Nat × Nat) : Prop := n ^ (2 ^ k) * 2 ^ K ≤ x.1 * d ^ (2 ^ k) * 2 ^ x.2

theorem normLow_inv (K n d k : Nat) : ∀ f x, LowInv K n d k x → LowInv K n d k (normLow K f x)
  | 0, _, h => h
  | f + 1, (P, e), h => by
    unfold normLow
    split
    · apply normLow_inv K n d k f
      unfold LowInv at *
      have h2 : P / 2 * 2 ≤ P := Nat.div_mul_le_self P 2
      calc P / 2 * d ^ 2 ^ k * 2 ^ (e + 1) = (P / 2 * 2) * d ^ 2 ^ k * 2 ^ e := by
              rw [Nat.pow_succ]; ac_rfl
        _ ≤ P * d ^ 2 ^ k * 2 ^ e := Nat.mul_le_mul (Nat.mul_le_mul h2 (Nat.le_refl _)) (Nat.le_refl _)
        _ ≤ _ := h
    · exact h

theorem normUp_inv (K n d k : Nat) : ∀ f x, UpInv K n d k x → UpInv K n d k (normUp K f x)
  | 0, _, h => h
  | f + 1, (Q, e), h => by
    unfold normUp
    split
    · apply normUp_inv K n d k f
      unfold UpInv at *
      have h2 : Q ≤ (Q + 1) / 2 * 2 := by omega
      calc _ ≤ Q * d ^ 2 ^ k * 2 ^ e := h
        _ ≤ ((Q + 1) / 2 * 2) * d ^ 2 ^ k * 2 ^ e :=
            Nat.mul_le_mul (Nat.mul_le_mul h2 (Nat.le_refl _)) (Nat.le_refl _)
        _ = _ := by rw [Nat.pow_succ]; ac_rfl
    · exact h

theorem pow_two_succ (a k : Nat) : a ^ 2 ^ (k + 1) = a ^ 2 ^ k * a ^ 2 ^ k := by
  rw [Nat.pow_succ, Nat.pow_mul, Nat.pow_two]

theorem ceil_mul {x t : Nat} (ht : 0 < t) : x ≤ (x + (t - 1)) / t * t := by
  have h1 := Nat.div_add_mod (x + (t - 1)) t
  have h2 := Nat.mod_lt (x + (t - 1)) ht
  rw [Nat.mul_comm]; omega

theorem sq_le {a b : Nat} (h : a ≤ b) : a * a ≤ b * b := Nat.mul_le_mul h h

theorem stepLow_inv (K n d k : Nat) (x : Nat × Nat) (h : LowInv K n d k x) :
    LowInv K n d (k + 1) (stepLow K x) := by
  apply normLow_inv
  unfold LowInv at *
  obtain ⟨P, e⟩ := x
  simp only at *
  have hpos : 0 < 2 ^ K := Nat.pow_pos (by decide)
  have hq : P * P / 2 ^ K * 2 ^ K ≤ P * P := Nat.div_mul_le_self _ _
  have hs := sq_le h
  rw [pow_two_succ, pow_two_succ, Nat.mul_comm 2 e, Nat.pow_mul, Nat.pow_two]
  apply Nat.le_of_mul_le_mul_right (c := 2 ^ K) _ hpos
  calc P * P / 2 ^ K * (d ^ 2 ^ k * d ^ 2 ^ k) * (2 ^ e * 2 ^ e) * 2 ^ K
        = (P * P / 2 ^ K * 2 ^ K) * (d ^ 2 ^ k * d ^ 2 ^ k) * (2 ^ e * 2 ^ e) := by
          ac_rfl
    _ ≤ (P * P) * (d ^ 2 ^ k * d ^ 2 ^ k) * (2 ^ e * 2 ^ e) :=
          Nat.mul_le_mul (Nat.mul_le_mul hq (Nat.le_refl _)) (Nat.le_refl _)
    _ = (P * d ^ 2 ^ k * 2 ^ e) * (P * d ^ 2 ^ k * 2 ^ e) := by
          ac_rfl
    _ ≤ (n ^ 2 ^ k * 2 ^ K) * (n ^ 2 ^ k * 2 ^ K) := hs
    _ = n ^ 2 ^ k * n ^ 2 ^ k * 2 ^ K * 2 ^ K := by
          ac_rfl

theorem stepUp_inv (K n d k : Nat) (x : Nat × Nat) (h : UpInv K n d k x) :
    UpInv K n d (k + 1) (stepUp K x) := by
  apply normUp_inv
  unfold UpInv at *
  obtain ⟨Q, e⟩ := x
  simp only at *
  have hpos : 0 < 2 ^ K := Nat.pow_pos (by decide)
  have hq : Q * Q ≤ (Q * Q + (2 ^ K - 1)) / 2 ^ K * 2 ^ K := ceil_mul hpos
  have hs := sq_le h
  rw [pow_two_succ, pow_two_succ, Nat.mul_comm 2 e, Nat.pow_mul, Nat.pow_two]
  apply Nat.le_of_mul_le_mul_right (c := 2 ^ K) _ hpos
  calc n ^ 2 ^ k * n ^ 2 ^ k * 2 ^ K * 2 ^ K = (n ^ 2 ^ k * 2 ^ K) * (n ^ 2 ^ k * 2 ^ K) := by
          ac_rfl
    _ ≤ (Q * d ^ 2 ^ k * 2 ^ e) * (Q * d ^ 2 ^ k * 2 ^ e) := hs
    _ = (Q * Q) * (d ^ 2 ^ k * d ^ 2 ^ k) * (2 ^ e * 2 ^ e) := by
          ac_rfl
    _ ≤ ((Q * Q + (2 ^ K - 1)) / 2 ^ K * 2 ^ K) * (d ^ 2 ^ k * d ^ 2 ^ k) * (2 ^ e * 2 ^ e) :=
          Nat.mul_le_mul (Nat.mul_le_mul hq (Nat.le_refl _)) (Nat.le_refl _)
    _ = _ := by ac_rfl

theorem runLow_inv (K n d : Nat) : ∀ s k x, LowInv K n d k x → LowInv K n d (k + s) (runLow K s x)
  | 0, _, _, h => h
  | s + 1, k, x, h => by
    have := runLow_inv K n d s (k + 1) _ (stepLow_inv K n d k x h)
    rw [show k + (s + 1) = k + 1 + s by omega]; exact this

theorem runUp_inv (K n d : Nat) : ∀ s k x, UpInv K n d k x → UpInv K n d (k + s) (runUp K s x)
  | 0, _, _, h => h
  | s + 1, k, x, h => by
    have := runUp_inv K n d s (k + 1) _ (stepUp_inv K n d k x h)
    rw [show k + (s + 1) = k + 1 + s by omega]; exact this

theorem initLow_inv (K n d : Nat) : LowInv K n d 0 (initLow K n d) := by
  apply normLow_inv
  unfold LowInv
  simp only [Nat.pow_zero, Nat.pow_one, Nat.mul_one]
  exact Nat.div_mul_le_self _ _

theorem initUp_inv (K n d : Nat) (hd : 0 < d) : UpInv K n d 0 (initUp K n d) := by
  apply normUp_inv
  unfold UpInv
  simp only [Nat.pow_zero, Nat.pow_one, Nat.mul_one]
  exact ceil_mul hd

/-- **شهادةُ اللوغاريتم بالتربيع**: مقطوعةٌ إلى K بتًّا، سفلى وعليا. -/
def logCheck (K s n d a : Nat) : Bool :=
  let l := runLow K s (initLow K n d)
  let u := runUp K s (initUp K n d)
  decide (2 ^ K ≤ l.1) && decide (l.2 = a) && decide (u.1 < 2 ^ (K + 1)) && decide (u.2 = a)

theorem logCheck_spec (K s n d a : Nat) (hd : 0 < d) (h : logCheck K s n d a = true) :
    2 ^ a * d ^ (2 ^ s) ≤ n ^ (2 ^ s) ∧ n ^ (2 ^ s) < 2 ^ (a + 1) * d ^ (2 ^ s) := by
  simp only [logCheck, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨hl, hla⟩, hu⟩, hua⟩ := h
  have L := runLow_inv K n d s 0 _ (initLow_inv K n d)
  have U := runUp_inv K n d s 0 _ (initUp_inv K n d hd)
  rw [Nat.zero_add] at L U
  unfold LowInv at L; unfold UpInv at U
  rw [hla] at L; rw [hua] at U
  have hpos : 0 < 2 ^ K := Nat.pow_pos (by decide)
  have hD : 0 < d ^ 2 ^ s := Nat.pow_pos hd
  constructor
  · apply Nat.le_of_mul_le_mul_right (c := 2 ^ K) _ hpos
    calc 2 ^ a * d ^ 2 ^ s * 2 ^ K = 2 ^ K * d ^ 2 ^ s * 2 ^ a := by
            ac_rfl
      _ ≤ _ * d ^ 2 ^ s * 2 ^ a := Nat.mul_le_mul (Nat.mul_le_mul hl (Nat.le_refl _)) (Nat.le_refl _)
      _ ≤ _ := L
  · apply Nat.lt_of_mul_lt_mul_right (a := 2 ^ K)
    calc n ^ 2 ^ s * 2 ^ K ≤ _ := U
      _ < 2 ^ (K + 1) * d ^ 2 ^ s * 2 ^ a :=
          Nat.mul_lt_mul_of_pos_right (Nat.mul_lt_mul_of_pos_right hu hD) (Nat.pow_pos (by decide))
      _ = 2 ^ (a + 1) * d ^ 2 ^ s * 2 ^ K := by
          rw [Nat.pow_succ, Nat.pow_succ]; ac_rfl

theorem flog_eq (b n d a : Nat) (hd : 0 < d)
    (h1 : 2 ^ a * d ^ b ≤ n ^ b) (h2 : n ^ b < 2 ^ (a + 1) * d ^ b) : flog b n d = a := by
  have hdb : 0 < d ^ b := Nat.pow_pos hd
  have q1 : 2 ^ a ≤ n ^ b / d ^ b := (Nat.le_div_iff_mul_le hdb).2 h1
  have q2 : n ^ b / d ^ b < 2 ^ (a + 1) := (Nat.div_lt_iff_lt_mul hdb).2 h2
  have hq : n ^ b / d ^ b ≠ 0 := by have := Nat.one_le_two_pow (n := a); omega
  have f1 := Nat.log2_self_le hq
  have f2 : n ^ b / d ^ b < 2 ^ (Nat.log2 (n ^ b / d ^ b) + 1) := Nat.lt_log2_self
  unfold flog
  apply Nat.le_antisymm
  · apply Nat.le_of_lt_succ
    apply (Nat.pow_lt_pow_iff_right (by decide : 1 < 2)).1
    exact Nat.lt_of_le_of_lt f1 q2
  · apply Nat.le_of_lt_succ
    apply (Nat.pow_lt_pow_iff_right (by decide : 1 < 2)).1
    exact Nat.lt_of_le_of_lt q1 f2

theorem map_flog (K s n : Nat) : ∀ (l as : List Nat), (∀ c ∈ l, 0 < c) →
    (l.zip as).all (fun p => logCheck K s n p.1 p.2) = true → l.length = as.length →
    l.map (flog (2 ^ s) n) = as
  | [], [], _, _, _ => rfl
  | [], _ :: _, _, _, h => by simp at h
  | _ :: _, [], _, _, h => by simp at h
  | c :: l, a :: as, hp, hc, hl => by
    simp only [List.zip_cons_cons, List.all_cons, Bool.and_eq_true] at hc
    have ⟨h1, h2⟩ := logCheck_spec K s n c a (hp c (by simp)) hc.1
    simp only [List.map_cons, List.cons.injEq]
    exact ⟨flog_eq _ _ _ _ (hp c (by simp)) h1 h2,
      map_flog K s n l as (fun x hx => hp x (by simp [hx])) hc.2 (by simpa using hl)⟩

/-- شهادةُ اللوغاريتم: ‎aᵢ = ⌊b · log₂(N/cᵢ)⌋‎ لكلّ خلية. -/
def aVals : List Nat := [372998, 546154, 746243, 825130, 826857, 1694942, 1827876, 1844615]

/-- الشهادةُ بالتربيع على الخلايا الثماني: ‎K = 64‎، ثماني عشرةَ تربيعة. -/
theorem cells_check : (freqs.zip aVals).all (fun p => logCheck 64 18 total p.1 p.2) = true := by
  decide +kernel

theorem flog_values : freqs.map (flog prec total) = aVals :=
  map_flog 64 18 total freqs aVals (by decide) cells_check rfl

theorem freqs_le_total : freqs.all (fun c => decide (0 < c) && decide (c ≤ total)) = true := by decide

/-- **‎2.30975 ≤ H < 2.30977‎**: ‎Σ cᵢaᵢ‎ و‎Σ cᵢ(aᵢ+1)‎ بين ‎2.30975·N·b‎ و‎2.30977·N·b‎. -/
theorem entropy_bounds :
    230975 * total * prec ≤ 100000 * ((freqs.zip aVals).foldl (fun s p => s + p.1 * p.2) 0) ∧
    100000 * ((freqs.zip aVals).foldl (fun s p => s + p.1 * (p.2 + 1)) 0) < 230977 * total * prec := by
  decide +kernel

end A116.Shannon
