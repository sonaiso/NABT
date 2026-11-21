import SLGE.Core

/-!
# العدُّ التقابليُّ لِما يرخّصه قانونٌ منتهٍ، مرتَّبًا بالدرجات

آلةٌ: رموزٌ ‎0 … A-1‎، وانتقالٌ ‎δ‎، ووزنٌ ‎ω‎ لكلّ انتقال، وقبولٌ ‎F‎.
السلسلةُ **مرخَّصة** إذا كانت رموزُها في الأبجدية وانتهى سيرُها إلى حالةٍ مقبولة.
ووزنُها مجموعُ أوزان انتقالاتها (عند القانون: عددُ الصوامت ‎c‎).

يُبرهَن هنا لكلّ آلةٍ كانت:
* ‎C f w q‎ هو **عددُ** المرخَّصات بوزنٍ ‎w‎ وطولٍ لا يتجاوز ‎f‎، والرتبةُ ‎rank‎ تقابلٌ بينها وبين ‎[0, C)‎؛
* الترقيمُ المتدرّج ‎gEnc‎: تقابلٌ بين المرخَّصات كلّها وبين ‎ℕ‎، يملأ كلَّ درجةٍ قبل التي تليها
  (**الاستنفادُ قبل الترخيص**)؛
* وأعدادُ ‎C‎ لآلاتٍ بعينها لا تُحسب هنا: تُحسب بالحساب الصنفيّ (`SLGE/HisabSinfi.lean`)؛ وكان هنا جدولٌ ‎tab‎ يحسبها
  (‎row‎، ‎tab‎، ‎tab_eq‎) حُذف بإذن المالك في الجلسة (2026-11-01؛ انظر رأس `SLGE/HisabSinfi.lean`).
-/

namespace SLGE

structure Machine where
  A : Nat
  δ : Nat → Nat → Nat
  ω : Nat → Nat → Nat
  F : Nat → Bool

namespace Machine
variable (M : Machine)

def runL (q : Nat) : List Nat → Nat
  | [] => q
  | a :: l => runL (M.δ q a) l

def wtL (q : Nat) : List Nat → Nat
  | [] => 0
  | a :: l => M.ω q a + wtL (M.δ q a) l

theorem runL_append (q : Nat) (l r : List Nat) : M.runL q (l ++ r) = M.runL (M.runL q l) r := by
  induction l generalizing q with
  | nil => rfl
  | cons a l ih => exact ih (M.δ q a)

theorem wtL_append (q : Nat) (l r : List Nat) :
    M.wtL q (l ++ r) = M.wtL q l + M.wtL (M.runL q l) r := by
  induction l generalizing q with
  | nil => simp [wtL, runL]
  | cons a l ih => simp only [List.cons_append, wtL, runL, ih]; omega

def base (w q : Nat) : Nat := if w = 0 ∧ M.F q = true then 1 else 0

def C : Nat → Nat → Nat → Nat
  | 0, w, q => M.base w q
  | f + 1, w, q => M.base w q + ((List.range M.A).map fun b =>
      if M.ω q b ≤ w then C f (w - M.ω q b) (M.δ q b) else 0).sum

def sizes (f w q : Nat) : List Nat :=
  (List.range M.A).map fun b => if M.ω q b ≤ w then M.C f (w - M.ω q b) (M.δ q b) else 0

theorem C_succ (f w q : Nat) : M.C (f + 1) w q = M.base w q + (M.sizes f w q).sum := by
  simp only [C, sizes]

theorem sizes_length (f w q : Nat) : (M.sizes f w q).length = M.A := by simp [sizes]

theorem sizes_getD (f w q b : Nat) (h : b < M.A) :
    (M.sizes f w q).getD b 0 = if M.ω q b ≤ w then M.C f (w - M.ω q b) (M.δ q b) else 0 := by
  simp [sizes, h]

theorem base_le_C (w q : Nat) : ∀ f, M.base w q ≤ M.C f w q
  | 0 => Nat.le_refl _
  | f + 1 => by rw [C_succ]; omega

theorem base_eq_one {w q : Nat} (h : w = 0 ∧ M.F q = true) : M.base w q = 1 := by
  simp [base, h]

theorem base_lt_iff {i w q : Nat} : i < M.base w q ↔ i = 0 ∧ w = 0 ∧ M.F q = true := by
  unfold base
  by_cases h : w = 0 ∧ M.F q = true
  · rw [if_pos h]; constructor
    · intro hi; exact ⟨by omega, h⟩
    · intro hi; omega
  · rw [if_neg h]; constructor
    · intro hi; omega
    · intro hi; exact absurd hi.2 h

/-- المرخَّصُ بوزنٍ ‎w‎ وطولٍ لا يتجاوز ‎f‎ من الحالة ‎q‎. -/
def Acc : Nat → Nat → Nat → List Nat → Prop
  | _, w, q, [] => w = 0 ∧ M.F q = true
  | 0, _, _, _ :: _ => False
  | f + 1, w, q, a :: l => a < M.A ∧ M.ω q a ≤ w ∧ Acc f (w - M.ω q a) (M.δ q a) l

theorem acc_nil (f w q : Nat) : M.Acc f w q [] ↔ (w = 0 ∧ M.F q = true) := by
  cases f <;> simp only [Acc]

theorem acc_iff : ∀ (l : List Nat) (f w q : Nat), M.Acc f w q l ↔
    ((∀ a ∈ l, a < M.A) ∧ l.length ≤ f ∧ M.wtL q l = w ∧ M.F (M.runL q l) = true)
  | [], f, w, q => by
    rw [acc_nil]; simp only [wtL, runL, List.length_nil]
    constructor
    · rintro ⟨h1, h2⟩; exact ⟨by simp, Nat.zero_le _, h1.symm, h2⟩
    · rintro ⟨_, _, h3, h4⟩; exact ⟨h3.symm, h4⟩
  | a :: l, 0, w, q => by simp [Acc]
  | a :: l, f + 1, w, q => by
    simp only [Acc, acc_iff l f, wtL, runL, List.mem_cons, List.length_cons, forall_eq_or_imp]
    constructor
    · rintro ⟨ha, hω, h1, h2, h3, h4⟩; exact ⟨⟨ha, h1⟩, by omega, by omega, h4⟩
    · rintro ⟨⟨ha, h1⟩, h2, h3, h4⟩; exact ⟨ha, by omega, h1, by omega, by omega, h4⟩

/-- الرتبة: ترتيبٌ معجميٌّ، والسلسلةُ المنتهيةُ قبل امتداداتها. -/
def rank : Nat → Nat → Nat → List Nat → Nat
  | _, _, _, [] => 0
  | f, w, q, a :: l =>
    M.base w q + blockEnc (M.sizes (f - 1) w q) a (rank (f - 1) (w - M.ω q a) (M.δ q a) l)

def unrank : Nat → Nat → Nat → Nat → List Nat
  | 0, _, _, _ => []
  | f + 1, w, q, i =>
    if i < M.base w q then [] else
      (blockDec (M.sizes f w q) (i - M.base w q)).1 ::
        unrank f (w - M.ω q (blockDec (M.sizes f w q) (i - M.base w q)).1)
          (M.δ q (blockDec (M.sizes f w q) (i - M.base w q)).1)
          (blockDec (M.sizes f w q) (i - M.base w q)).2

theorem rank_lt : ∀ (l : List Nat) (f w q : Nat), M.Acc f w q l → M.rank f w q l < M.C f w q
  | [], f, w, q, h => by
    simp only [rank]; have := M.base_le_C w q f; have h1 := M.base_eq_one ((M.acc_nil f w q).1 h); omega
  | a :: l, 0, w, q, h => by simp [Acc] at h
  | a :: l, f + 1, w, q, h => by
    obtain ⟨ha, hω, hl⟩ := h
    have ih := rank_lt l f _ _ hl
    simp only [rank, Nat.add_sub_cancel]
    rw [C_succ]
    have := blockEnc_lt (M.sizes f w q) a _ (by rw [sizes_length]; exact ha)
      (by rw [sizes_getD _ _ _ _ _ ha, if_pos hω]; exact ih)
    omega

theorem unrank_rank : ∀ (l : List Nat) (f w q : Nat), M.Acc f w q l →
    M.unrank f w q (M.rank f w q l) = l
  | [], 0, w, q, _ => rfl
  | [], f + 1, w, q, h => by
    simp only [rank, unrank]; rw [M.base_eq_one ((M.acc_nil _ w q).1 h)]; simp
  | a :: l, 0, _, _, h => by simp [Acc] at h
  | a :: l, f + 1, w, q, h => by
    obtain ⟨ha, hω, hl⟩ := h
    have hlt := M.rank_lt l f _ _ hl
    have hd := blockDec_enc (M.sizes f w q) a (M.rank f (w - M.ω q a) (M.δ q a) l)
      (by rw [sizes_length]; exact ha) (by rw [sizes_getD _ _ _ _ _ ha, if_pos hω]; exact hlt)
    simp only [rank, unrank, Nat.add_sub_cancel]
    rw [if_neg (by omega), Nat.add_sub_cancel_left, hd]
    simp only
    rw [unrank_rank l f _ _ hl]

theorem unrank_spec : ∀ (f w q i : Nat), i < M.C f w q →
    M.Acc f w q (M.unrank f w q i) ∧ M.rank f w q (M.unrank f w q i) = i
  | 0, w, q, i, h => by
    simp only [C] at h
    have := M.base_lt_iff.1 h
    simp only [unrank, acc_nil, rank]; exact ⟨this.2, this.1.symm⟩
  | f + 1, w, q, i, h => by
    rw [C_succ] at h
    by_cases hb : i < M.base w q
    · have := M.base_lt_iff.1 hb
      simp only [unrank, if_pos hb, acc_nil, rank]; exact ⟨this.2, this.1.symm⟩
    · simp only [unrank, if_neg hb]
      have hj : i - M.base w q < (M.sizes f w q).sum := by omega
      obtain ⟨h1, h2, h3⟩ := blockEnc_dec _ _ hj
      generalize blockDec (M.sizes f w q) (i - M.base w q) = p at h1 h2 h3 ⊢
      rw [sizes_length] at h1
      rw [sizes_getD _ _ _ _ _ h1] at h2
      by_cases hω : M.ω q p.1 ≤ w
      · rw [if_pos hω] at h2
        obtain ⟨ihA, ihR⟩ := unrank_spec f _ _ p.2 h2
        refine ⟨⟨h1, hω, ihA⟩, ?_⟩
        simp only [rank, Nat.add_sub_cancel, ihR, h3]; omega
      · rw [if_neg hω] at h2; omega

/-! ### الترقيمُ المتدرّج: الدرجةُ ‎W‎ لا تُرقَّم إلّا بعد استنفاد ما دونها -/

def levels (L : Nat → Nat) : Nat → Nat → List Nat
  | _, 0 => []
  | s, N + 1 => L s :: levels L (s + 1) N

def offFrom (L : Nat → Nat) : Nat → Nat → Nat
  | _, 0 => 0
  | s, m + 1 => L s + offFrom L (s + 1) m

theorem blockEnc_levels (L : Nat → Nat) : ∀ s N m k, m ≤ N →
    blockEnc (levels L s N) m k = offFrom L s m + k
  | s, N, 0, k, _ => by cases N <;> simp [blockEnc, offFrom, levels]
  | _, 0, _ + 1, _, h => by omega
  | s, N + 1, m + 1, k, h => by
    simp only [levels, blockEnc, offFrom]; rw [blockEnc_levels L (s + 1) N m k (by omega)]; omega

theorem levels_length (L : Nat → Nat) : ∀ s N, (levels L s N).length = N
  | _, 0 => rfl
  | s, N + 1 => by simp [levels, levels_length L (s + 1) N]

theorem levels_getD (L : Nat → Nat) : ∀ s N m, m < N → (levels L s N).getD m 0 = L (s + m)
  | _, 0, _, h => by omega
  | s, N + 1, 0, _ => by simp [levels]
  | s, N + 1, m + 1, h => by
    simp only [levels, List.getD_cons_succ]
    rw [levels_getD L (s + 1) N m (by omega)]; congr 1; omega

theorem levels_sum (L : Nat → Nat) : ∀ s N, (levels L s N).sum = offFrom L s N
  | _, 0 => rfl
  | s, N + 1 => by simp [levels, offFrom, levels_sum L (s + 1) N]

theorem offFrom_snoc (L : Nat → Nat) : ∀ s m, offFrom L s (m + 1) = offFrom L s m + L (s + m)
  | s, 0 => by simp [offFrom]
  | s, m + 1 => by
    rw [offFrom, offFrom_snoc L (s + 1) m, offFrom]
    have : s + 1 + m = s + (m + 1) := by omega
    rw [this]; omega

theorem offFrom_ge (L : Nat → Nat) (hpos : ∀ j, 0 < L (j + 1)) :
    ∀ s m, 0 < s → m ≤ offFrom L s m
  | _, 0, _ => Nat.zero_le _
  | s, m + 1, hs => by
    rw [offFrom]
    have := offFrom_ge L hpos (s + 1) m (by omega)
    have : 0 < L s := by obtain ⟨j, rfl⟩ : ∃ j, s = j + 1 := ⟨s - 1, by omega⟩; exact hpos j
    omega

theorem offFrom_ge0 (L : Nat → Nat) (hpos : ∀ j, 0 < L (j + 1)) (m : Nat) : m ≤ offFrom L 0 (m + 1) := by
  have := offFrom_ge L hpos 1 m (by omega); simp only [offFrom, Nat.zero_add]; omega

def lev (K q0 j : Nat) : Nat := M.C (K * j) j q0

def Lic (q0 : Nat) (l : List Nat) : Prop := (∀ a ∈ l, a < M.A) ∧ M.F (M.runL q0 l) = true

def gEnc (K q0 : Nat) (l : List Nat) : Nat :=
  offFrom (M.lev K q0) 0 (M.wtL q0 l) + M.rank (K * M.wtL q0 l) (M.wtL q0 l) q0 l

def gDec (K q0 n : Nat) : List Nat :=
  M.unrank (K * (blockDec (levels (M.lev K q0) 0 (n + 2)) n).1)
    (blockDec (levels (M.lev K q0) 0 (n + 2)) n).1 q0 (blockDec (levels (M.lev K q0) 0 (n + 2)) n).2

/-- **الترقيمُ المتدرّج مبرهَن:** كلُّ مرخَّصٍ له رقمٌ واحد يُفكّ إليه، وكلُّ عددٍ رقمُ مرخَّصٍ واحد،
ورقمُ ما وزنُه ‎W‎ يقع بين ‎off W‎ و‎off (W+1)‎: الدرجاتُ تُستنفَد على الترتيب. -/
theorem graded (K q0 : Nat) (hK : ∀ l, M.Lic q0 l → l.length ≤ K * M.wtL q0 l)
    (hpos : ∀ j, 0 < M.lev K q0 (j + 1)) :
    (∀ l, M.Lic q0 l → M.gDec K q0 (M.gEnc K q0 l) = l) ∧
    (∀ n, M.Lic q0 (M.gDec K q0 n) ∧ M.gEnc K q0 (M.gDec K q0 n) = n) ∧
    (∀ l, M.Lic q0 l → offFrom (M.lev K q0) 0 (M.wtL q0 l) ≤ M.gEnc K q0 l ∧
      M.gEnc K q0 l < offFrom (M.lev K q0) 0 (M.wtL q0 l + 1)) := by
  have accOf : ∀ l, M.Lic q0 l → M.Acc (K * M.wtL q0 l) (M.wtL q0 l) q0 l := fun l hl =>
    (M.acc_iff l _ _ _).2 ⟨hl.1, hK l hl, rfl, hl.2⟩
  refine ⟨fun l hl => ?_, fun n => ?_, fun l hl => ?_⟩
  · have ha := accOf l hl
    have hr := M.rank_lt l _ _ _ ha
    have hge := offFrom_ge0 (M.lev K q0) hpos (M.wtL q0 l - 1)
    have hW : M.wtL q0 l < M.gEnc K q0 l + 2 := by
      unfold gEnc
      have : offFrom (M.lev K q0) 0 (M.wtL q0 l) ≥ M.wtL q0 l - 1 := by
        rcases Nat.eq_zero_or_pos (M.wtL q0 l) with h0 | h0
        · rw [h0]; exact Nat.zero_le _
        · have e : M.wtL q0 l - 1 + 1 = M.wtL q0 l := by omega
          rw [e] at hge; exact hge
      omega
    have he : blockEnc (levels (M.lev K q0) 0 (M.gEnc K q0 l + 2)) (M.wtL q0 l)
        (M.rank (K * M.wtL q0 l) (M.wtL q0 l) q0 l) = M.gEnc K q0 l := by
      rw [blockEnc_levels _ _ _ _ _ (by omega)]; rfl
    have hd := blockDec_enc (levels (M.lev K q0) 0 (M.gEnc K q0 l + 2)) (M.wtL q0 l)
      (M.rank (K * M.wtL q0 l) (M.wtL q0 l) q0 l) (by rw [levels_length]; exact hW)
      (by rw [levels_getD _ _ _ _ hW, Nat.zero_add]; exact hr)
    rw [he] at hd
    unfold gDec; rw [hd]; exact M.unrank_rank l _ _ _ ha
  · have hs : n < (levels (M.lev K q0) 0 (n + 2)).sum := by
      rw [levels_sum, show n + 2 = n + 1 + 1 from rfl]; have := offFrom_ge0 (M.lev K q0) hpos (n + 1); omega
    obtain ⟨h1, h2, h3⟩ := blockEnc_dec _ _ hs
    rw [levels_length] at h1
    rw [levels_getD _ _ _ _ h1, Nat.zero_add] at h2
    obtain ⟨hA, hR⟩ := M.unrank_spec _ _ _ _ h2
    have hl := (M.acc_iff _ _ _ _).1 hA
    unfold gDec
    refine ⟨⟨hl.1, hl.2.2.2⟩, ?_⟩
    unfold gEnc; rw [hl.2.2.1, hR]
    rw [blockEnc_levels _ _ _ _ _ (by omega)] at h3; exact h3
  · have hr := M.rank_lt l _ _ _ (accOf l hl)
    unfold gEnc; rw [offFrom_snoc, Nat.zero_add]
    exact ⟨Nat.le_add_right _ _, by unfold lev at *; omega⟩

/-- **العدُّ في الدرجة ‎W‎:** المرخَّصاتُ بوزن ‎W‎ تقابلُ ‎[0, lev W)‎ بالرتبة — فعددُها ‎lev W‎ بالضبط. -/
theorem level_count (K q0 W : Nat) (hK : ∀ l, M.Lic q0 l → l.length ≤ K * M.wtL q0 l) :
    (∀ l, M.Lic q0 l → M.wtL q0 l = W → M.rank (K * W) W q0 l < M.lev K q0 W) ∧
    (∀ l l', M.Lic q0 l → M.Lic q0 l' → M.wtL q0 l = W → M.wtL q0 l' = W →
      M.rank (K * W) W q0 l = M.rank (K * W) W q0 l' → l = l') ∧
    (∀ i, i < M.lev K q0 W → ∃ l, M.Lic q0 l ∧ M.wtL q0 l = W ∧ M.rank (K * W) W q0 l = i) := by
  have accOf : ∀ l, M.Lic q0 l → M.wtL q0 l = W → M.Acc (K * W) W q0 l := fun l hl hw =>
    (M.acc_iff l _ _ _).2 ⟨hl.1, hw ▸ hK l hl, hw, hl.2⟩
  refine ⟨fun l hl hw => M.rank_lt l _ _ _ (accOf l hl hw), fun l l' hl hl' hw hw' he => ?_,
    fun i hi => ?_⟩
  · rw [← M.unrank_rank l _ _ _ (accOf l hl hw), he, M.unrank_rank l' _ _ _ (accOf l' hl' hw')]
  · obtain ⟨hA, hR⟩ := M.unrank_spec _ _ _ _ hi
    have h := (M.acc_iff _ _ _ _).1 hA
    exact ⟨_, ⟨h.1, h.2.2.2⟩, h.2.2.1, hR⟩

def gDecF (K q0 Wm n : Nat) : List Nat :=
  M.unrank (K * (blockDec (levels (M.lev K q0) 0 (Wm + 1)) n).1)
    (blockDec (levels (M.lev K q0) 0 (Wm + 1)) n).1 q0 (blockDec (levels (M.lev K q0) 0 (Wm + 1)) n).2

/-- **الترقيمُ المتدرّج حين تنتهي الدرجات** (أعلاها ‎Wm‎): تقابلٌ بين المرخَّصات و‎[0, off (Wm+1))‎. -/
theorem gradedFin (K q0 Wm : Nat) (hK : ∀ l, M.Lic q0 l → l.length ≤ K * M.wtL q0 l)
    (hW : ∀ l, M.Lic q0 l → M.wtL q0 l ≤ Wm) :
    (∀ l, M.Lic q0 l → M.gDecF K q0 Wm (M.gEnc K q0 l) = l) ∧
    (∀ n, n < offFrom (M.lev K q0) 0 (Wm + 1) →
      M.Lic q0 (M.gDecF K q0 Wm n) ∧ M.gEnc K q0 (M.gDecF K q0 Wm n) = n) ∧
    (∀ l, M.Lic q0 l → offFrom (M.lev K q0) 0 (M.wtL q0 l) ≤ M.gEnc K q0 l ∧
      M.gEnc K q0 l < offFrom (M.lev K q0) 0 (M.wtL q0 l + 1)) := by
  have accOf : ∀ l, M.Lic q0 l → M.Acc (K * M.wtL q0 l) (M.wtL q0 l) q0 l := fun l hl =>
    (M.acc_iff l _ _ _).2 ⟨hl.1, hK l hl, rfl, hl.2⟩
  refine ⟨fun l hl => ?_, fun n hn => ?_, fun l hl => ?_⟩
  · have ha := accOf l hl
    have hr := M.rank_lt l _ _ _ ha
    have hW' := hW l hl
    have he : blockEnc (levels (M.lev K q0) 0 (Wm + 1)) (M.wtL q0 l)
        (M.rank (K * M.wtL q0 l) (M.wtL q0 l) q0 l) = M.gEnc K q0 l := by
      rw [blockEnc_levels _ _ _ _ _ (by omega)]; rfl
    have hd := blockDec_enc (levels (M.lev K q0) 0 (Wm + 1)) (M.wtL q0 l)
      (M.rank (K * M.wtL q0 l) (M.wtL q0 l) q0 l) (by rw [levels_length]; omega)
      (by rw [levels_getD _ _ _ _ (by omega), Nat.zero_add]; exact hr)
    rw [he] at hd
    unfold gDecF; rw [hd]; exact M.unrank_rank l _ _ _ ha
  · have hs : n < (levels (M.lev K q0) 0 (Wm + 1)).sum := by rw [levels_sum]; exact hn
    obtain ⟨h1, h2, h3⟩ := blockEnc_dec _ _ hs
    rw [levels_length] at h1
    rw [levels_getD _ _ _ _ h1, Nat.zero_add] at h2
    obtain ⟨hA, hR⟩ := M.unrank_spec _ _ _ _ h2
    have hl := (M.acc_iff _ _ _ _).1 hA
    unfold gDecF
    refine ⟨⟨hl.1, hl.2.2.2⟩, ?_⟩
    unfold gEnc; rw [hl.2.2.1, hR]
    rw [blockEnc_levels _ _ _ _ _ (by omega)] at h3; exact h3
  · have hr := M.rank_lt l _ _ _ (accOf l hl)
    unfold gEnc; rw [offFrom_snoc, Nat.zero_add]
    exact ⟨Nat.le_add_right _ _, by unfold lev at *; omega⟩

/-! ## ترقيمُ التوافيق: كتلةٌ لكلّ مفتاحٍ صريح، وفي الكتلة رتبتان من آلتين

يُستعمل للمزيد: المفتاحُ الوزنُ (أو الوزنُ وحالةُ الوصل)، والآلتان آلةُ السابقة وآلةُ اللاحقة.
فعددُ التوافيق مجموعُ جداءِ العددين في كلّ كتلة، والترقيمُ تقابلٌ مع ‎[0, المجموع)‎. -/

section Blocks
variable {α : Type} [BEq α] [LawfulBEq α] (E : List α) (d : α) (ML MR : α → Machine)
  (sL sR : α → Nat) (K wL wR : Nat)

def bsize (e : α) : Nat := (ML e).lev K (sL e) wL * (MR e).lev K (sR e) wR

def bsizes : List Nat := E.map (bsize ML MR sL sR K wL wR)

def bEnc (e : α) (l r : List Nat) : Nat :=
  blockEnc (bsizes E ML MR sL sR K wL wR) (E.idxOf e)
    ((ML e).rank (K * wL) wL (sL e) l * (MR e).lev K (sR e) wR + (MR e).rank (K * wR) wR (sR e) r)

def bDec (n : Nat) : α × List Nat × List Nat :=
  let p := blockDec (bsizes E ML MR sL sR K wL wR) n
  let e := E.getD p.1 d
  (e, (ML e).unrank (K * wL) wL (sL e) (p.2 / (MR e).lev K (sR e) wR),
    (MR e).unrank (K * wR) wR (sR e) (p.2 % (MR e).lev K (sR e) wR))

def BValid (x : α × List Nat × List Nat) : Prop :=
  x.1 ∈ E ∧ (ML x.1).Acc (K * wL) wL (sL x.1) x.2.1 ∧ (MR x.1).Acc (K * wR) wR (sR x.1) x.2.2

theorem mix2_lt {a b A B : Nat} (ha : a < A) (hb : b < B) : a * B + b < A * B := by
  have := Nat.mul_le_mul_right B (Nat.succ_le_of_lt ha)
  rw [Nat.succ_mul] at this; omega

theorem bsizes_getD (i : Nat) (hi : i < E.length) :
    (bsizes E ML MR sL sR K wL wR).getD i 0 = bsize ML MR sL sR K wL wR (E.getD i d) := by
  simp [bsizes, List.getD_eq_getElem?_getD, hi]

theorem getD_eq (i : Nat) (hi : i < E.length) : E.getD i d = E[i] := by
  simp [List.getD_eq_getElem?_getD, hi]

/-- **ترقيمُ التوافيق تقابل.** -/
theorem bNum (hE : E.Nodup) :
    (∀ x, BValid E ML MR sL sR K wL wR x →
      bDec E d ML MR sL sR K wL wR (bEnc E ML MR sL sR K wL wR x.1 x.2.1 x.2.2) = x) ∧
    (∀ n, n < (bsizes E ML MR sL sR K wL wR).sum →
      BValid E ML MR sL sR K wL wR (bDec E d ML MR sL sR K wL wR n) ∧
      bEnc E ML MR sL sR K wL wR (bDec E d ML MR sL sR K wL wR n).1
        (bDec E d ML MR sL sR K wL wR n).2.1 (bDec E d ML MR sL sR K wL wR n).2.2 = n) := by
  constructor
  · rintro ⟨e, l, r⟩ ⟨he, hl, hr⟩
    have hi := List.idxOf_lt_length_of_mem he
    have hge : E.getD (E.idxOf e) d = e := by rw [getD_eq E d _ hi]; exact List.getElem_idxOf hi
    have rl : (ML e).rank (K * wL) wL (sL e) l < (ML e).lev K (sL e) wL := (ML e).rank_lt l _ _ _ hl
    have rr : (MR e).rank (K * wR) wR (sR e) r < (MR e).lev K (sR e) wR := (MR e).rank_lt r _ _ _ hr
    have hin := mix2_lt rl rr
    have hd := blockDec_enc (bsizes E ML MR sL sR K wL wR) (E.idxOf e)
      ((ML e).rank (K * wL) wL (sL e) l * (MR e).lev K (sR e) wR + (MR e).rank (K * wR) wR (sR e) r)
      (by simp [bsizes]; exact hi)
      (by rw [bsizes_getD E d ML MR sL sR K wL wR _ (by simpa using hi), hge]; exact hin)
    have hpos : 0 < (MR e).lev K (sR e) wR := Nat.lt_of_le_of_lt (Nat.zero_le _) rr
    unfold bDec bEnc
    simp only [hd, hge]
    have e1 : ((ML e).rank (K * wL) wL (sL e) l * (MR e).lev K (sR e) wR +
        (MR e).rank (K * wR) wR (sR e) r) / (MR e).lev K (sR e) wR = (ML e).rank (K * wL) wL (sL e) l := by
      rw [Nat.add_comm, Nat.add_mul_div_right _ _ hpos, Nat.div_eq_of_lt rr]
      omega
    have e2 : ((ML e).rank (K * wL) wL (sL e) l * (MR e).lev K (sR e) wR +
        (MR e).rank (K * wR) wR (sR e) r) % (MR e).lev K (sR e) wR = (MR e).rank (K * wR) wR (sR e) r := by
      rw [Nat.add_comm, Nat.add_mul_mod_self_right, Nat.mod_eq_of_lt rr]
    rw [e1, e2, (ML e).unrank_rank l _ _ _ hl, (MR e).unrank_rank r _ _ _ hr]
  · intro n hn
    obtain ⟨h1, h2, h3⟩ := blockEnc_dec _ _ hn
    generalize hp : blockDec (bsizes E ML MR sL sR K wL wR) n = p at h1 h2 h3
    have hlen : p.1 < E.length := by simpa [bsizes] using h1
    rw [bsizes_getD E d ML MR sL sR K wL wR _ hlen] at h2
    generalize he : E.getD p.1 d = e at h2
    unfold bsize at h2
    have hR : 0 < (MR e).lev K (sR e) wR := by
      rcases Nat.eq_zero_or_pos ((MR e).lev K (sR e) wR) with h | h
      · rw [h, Nat.mul_zero] at h2; omega
      · exact h
    have hq : p.2 / (MR e).lev K (sR e) wR < (ML e).lev K (sL e) wL := by
      rw [Nat.div_lt_iff_lt_mul hR]; exact h2
    have hm : p.2 % (MR e).lev K (sR e) wR < (MR e).lev K (sR e) wR := Nat.mod_lt _ hR
    obtain ⟨aL, rL⟩ := (ML e).unrank_spec _ _ _ _ hq
    obtain ⟨aR, rR⟩ := (MR e).unrank_spec _ _ _ _ hm
    have hmem : e ∈ E := by rw [← he, getD_eq E d _ hlen]; exact List.getElem_mem hlen
    have hidx : E.idxOf e = p.1 := by rw [← he, getD_eq E d _ hlen]; exact hE.idxOf_getElem _ hlen
    unfold bDec bEnc BValid
    simp only [hp, he]
    refine ⟨⟨hmem, aL, aR⟩, ?_⟩
    rw [rL, rR, hidx, Nat.div_add_mod']
    exact h3

end Blocks

end Machine
end SLGE
