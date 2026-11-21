/-!
# SLGE من الصفر — الأدواتُ الرياضيّةُ الثلاث، بلا مكتبةٍ ولا مودَع

1. **القسمةُ إلى كتل** (`blockEnc`/`blockDec`): عددٌ في ‎[0, Σ sizes)‎ ⟷ (رقمُ الكتلة، الموضعُ فيها).
2. **العددُ مختلطُ الأساس** (`mixEnc`/`mixDec`): ثلاثيٌّ ‎(o, k₁, k₂)‎ ⟷ عددٌ في ‎[0, A·B·C)‎.
3. **العدُّ التقابليُّ للقوائم**: قائمةٌ من أعدادٍ دون ‎B‎ ⟷ ℕ (`encL`/`decL`)؛ وقائمةٌ من ℕ ⟷ ℕ
   باقترانٍ مبرهَنٍ هنا (`pair`/`unpair`، `encS`/`decS`).
-/

namespace SLGE

/-! ## 1. القسمةُ إلى كتل -/

def blockEnc : List Nat → Nat → Nat → Nat
  | _, 0, k => k
  | [], _ + 1, k => k
  | s :: ss, m + 1, k => s + blockEnc ss m k

def blockDec : List Nat → Nat → Nat × Nat
  | [], i => (0, i)
  | s :: ss, i => if i < s then (0, i) else let r := blockDec ss (i - s); (r.1 + 1, r.2)

theorem blockDec_enc : ∀ (ss : List Nat) (m k : Nat), m < ss.length → k < ss.getD m 0 →
    blockDec ss (blockEnc ss m k) = (m, k)
  | [], _, _, h, _ => by simp at h
  | s :: ss, 0, k, _, hk => by
    simp only [List.getD_cons_zero] at hk
    simp only [blockEnc, blockDec, hk, ↓reduceIte]
  | s :: ss, m + 1, k, hm, hk => by
    simp only [blockEnc, blockDec]
    have : ¬ (s + blockEnc ss m k < s) := by omega
    simp only [this, ↓reduceIte]
    simp only [List.length_cons, List.getD_cons_succ] at hm hk
    rw [show s + blockEnc ss m k - s = blockEnc ss m k by omega, blockDec_enc ss m k (by omega) hk]

theorem blockEnc_dec : ∀ (ss : List Nat) (i : Nat), i < ss.sum →
    (blockDec ss i).1 < ss.length ∧ (blockDec ss i).2 < ss.getD (blockDec ss i).1 0 ∧
      blockEnc ss (blockDec ss i).1 (blockDec ss i).2 = i
  | [], i, h => by simp at h
  | s :: ss, i, h => by
    simp only [blockDec]
    split
    · rename_i hi; simp [blockEnc, hi]
    · rename_i hi
      simp only [List.sum_cons] at h
      have := blockEnc_dec ss (i - s) (by omega)
      refine ⟨by simp; omega, by simpa using this.2.1, ?_⟩
      simp only [blockEnc]; rw [this.2.2]; omega

theorem blockEnc_lt : ∀ (ss : List Nat) (m k : Nat), m < ss.length → k < ss.getD m 0 →
    blockEnc ss m k < ss.sum
  | [], _, _, h, _ => by simp at h
  | s :: ss, 0, k, _, hk => by simp only [List.getD_cons_zero] at hk; simp [blockEnc]; omega
  | s :: ss, m + 1, k, hm, hk => by
    simp only [List.length_cons, List.getD_cons_succ] at hm hk
    have := blockEnc_lt ss m k (by omega) hk
    simp [blockEnc]; omega

/-! ## 2. العددُ مختلطُ الأساس -/

def mixEnc (B C o k₁ k₂ : Nat) : Nat := (o * B + k₁) * C + k₂
def mixDec (B C n : Nat) : Nat × Nat × Nat := (n / C / B, n / C % B, n % C)

theorem mixDec_enc (B C o k₁ k₂ : Nat) (h₁ : k₁ < B) (h₂ : k₂ < C) :
    mixDec B C (mixEnc B C o k₁ k₂) = (o, k₁, k₂) := by
  have hC : 0 < C := by omega
  have hB : 0 < B := by omega
  simp only [mixDec, mixEnc]
  have e1 : ((o * B + k₁) * C + k₂) / C = o * B + k₁ := by
    rw [Nat.add_comm, Nat.add_mul_div_right _ _ hC, Nat.div_eq_of_lt h₂, Nat.zero_add]
  have e2 : ((o * B + k₁) * C + k₂) % C = k₂ := by
    rw [Nat.add_comm, Nat.add_mul_mod_self_right, Nat.mod_eq_of_lt h₂]
  rw [e1, e2]
  have e3 : (o * B + k₁) / B = o := by
    rw [Nat.add_comm, Nat.add_mul_div_right _ _ hB, Nat.div_eq_of_lt h₁, Nat.zero_add]
  have e4 : (o * B + k₁) % B = k₁ := by
    rw [Nat.add_comm, Nat.add_mul_mod_self_right, Nat.mod_eq_of_lt h₁]
  rw [e3, e4]

theorem mixEnc_dec (B C n : Nat) (hB : 0 < B) (hC : 0 < C) :
    mixEnc B C (mixDec B C n).1 (mixDec B C n).2.1 (mixDec B C n).2.2 = n := by
  simp only [mixEnc, mixDec]
  rw [Nat.mul_comm (n / C / B) B, Nat.div_add_mod, Nat.mul_comm (n / C) C, Nat.div_add_mod]

theorem mixDec_lt (A B C n : Nat) (hB : 0 < B) (hC : 0 < C) (h : n < A * B * C) :
    (mixDec B C n).1 < A ∧ (mixDec B C n).2.1 < B ∧ (mixDec B C n).2.2 < C := by
  simp only [mixDec]
  refine ⟨?_, Nat.mod_lt _ hB, Nat.mod_lt _ hC⟩
  rw [Nat.div_div_eq_div_mul, Nat.div_lt_iff_lt_mul (Nat.mul_pos hC hB)]
  rw [Nat.mul_comm C B, ← Nat.mul_assoc]; exact h

/-! ## 3. العدُّ التقابليُّ للقوائم -/

/-- قائمةٌ من أرقامٍ دون ‎B‎، صغراها أوّلًا: ‎enc(a :: l) = 1 + a + B·enc(l)‎. -/
def encL (B : Nat) : List Nat → Nat
  | [] => 0
  | a :: l => 1 + a + B * encL B l

def decAux (B : Nat) : Nat → Nat → List Nat
  | 0, _ => []
  | f + 1, n => if n = 0 then [] else ((n - 1) % B) :: decAux B f ((n - 1) / B)

def decL (B n : Nat) : List Nat := decAux B n n

theorem decAux_enc (B : Nat) (hB : 0 < B) : ∀ (l : List Nat), (∀ x ∈ l, x < B) →
    ∀ f, encL B l ≤ f → decAux B f (encL B l) = l
  | [], _, f, _ => by cases f <;> simp [encL, decAux]
  | a :: l, h, f, hf => by
    have ha : a < B := h a (by simp)
    obtain ⟨f', rfl⟩ : ∃ f', f = f' + 1 := ⟨f - 1, by simp [encL] at hf; omega⟩
    simp only [decAux, encL]
    have hne : ¬ (1 + a + B * encL B l = 0) := by omega
    simp only [hne, ↓reduceIte]
    have e : 1 + a + B * encL B l - 1 = a + encL B l * B := by rw [Nat.mul_comm]; omega
    have h1 : (a + encL B l * B) % B = a := by rw [Nat.add_mul_mod_self_right, Nat.mod_eq_of_lt ha]
    have h2 : (a + encL B l * B) / B = encL B l := by
      rw [Nat.add_mul_div_right _ _ hB, Nat.div_eq_of_lt ha, Nat.zero_add]
    rw [e, h1, h2]
    congr 1
    apply decAux_enc B hB l (fun x hx => h x (by simp [hx]))
    simp [encL] at hf
    have : encL B l ≤ B * encL B l := Nat.le_mul_of_pos_left _ hB
    omega

theorem decL_encL (B : Nat) (hB : 0 < B) (l : List Nat) (h : ∀ x ∈ l, x < B) :
    decL B (encL B l) = l := decAux_enc B hB l h _ (Nat.le_refl _)

theorem encL_decAux (B : Nat) (hB : 0 < B) : ∀ f n, n ≤ f → encL B (decAux B f n) = n
  | 0, n, h => by simp [decAux, encL]; omega
  | f + 1, n, h => by
    simp only [decAux]
    split
    · rename_i h0; simp [encL, h0]
    · rename_i h0
      simp only [encL]
      rw [encL_decAux B hB f ((n - 1) / B) (by
        have := Nat.div_le_self (n - 1) B; omega)]
      have := Nat.mod_add_div (n - 1) B
      omega

theorem encL_decL (B : Nat) (hB : 0 < B) (n : Nat) : encL B (decL B n) = n :=
  encL_decAux B hB n n (Nat.le_refl _)

theorem decAux_lt (B : Nat) (hB : 0 < B) : ∀ f n, ∀ x ∈ decAux B f n, x < B
  | 0, _, x, hx => by simp [decAux] at hx
  | f + 1, n, x, hx => by
    simp only [decAux] at hx
    split at hx
    · simp at hx
    · simp only [List.mem_cons] at hx
      rcases hx with rfl | hx
      · exact Nat.mod_lt _ hB
      · exact decAux_lt B hB f _ x hx

/-! ### نطاقُ العدّ: القوائمُ بطول ‎j‎ تملأ ‎[geo j, geo (j+1))‎ بالضبط، وعددُها ‎Bʲ‎ -/

def geo (B : Nat) : Nat → Nat
  | 0 => 0
  | j + 1 => 1 + B * geo B j

theorem geo_succ_sub (B j : Nat) : geo B (j + 1) = geo B j + B ^ j := by
  induction j with
  | zero => simp [geo]
  | succ j ih =>
    simp only [geo] at ih ⊢
    rw [ih, Nat.mul_add, Nat.pow_succ, Nat.mul_comm (B ^ j) B]; omega

theorem encL_range (B : Nat) (hB : 0 < B) : ∀ (l : List Nat), (∀ x ∈ l, x < B) →
    geo B l.length ≤ encL B l ∧ encL B l < geo B (l.length + 1)
  | [], _ => by simp [geo, encL]
  | a :: l, h => by
    have ha := h a (by simp)
    have ih := encL_range B hB l (fun x hx => h x (by simp [hx]))
    simp only [List.length_cons, geo, encL] at ih ⊢
    constructor
    · have := Nat.mul_le_mul_left B ih.1; omega
    · have h1 : encL B l + 1 ≤ 1 + B * geo B l.length := by omega
      have := Nat.mul_le_mul_left B h1
      rw [Nat.mul_add, Nat.mul_one] at this; omega

/-- **طولُ الفكّ يعيّنه النطاق:** ‎|decL n| = j ⟺ geo j ≤ n < geo (j+1)‎. -/
theorem decL_length_iff (B : Nat) (hB : 0 < B) (n j : Nat) :
    (decL B n).length = j ↔ geo B j ≤ n ∧ n < geo B (j + 1) := by
  have hr := encL_range B hB (decL B n) (decAux_lt B hB n n)
  rw [encL_decL B hB] at hr
  have mono : ∀ a b, a ≤ b → geo B a ≤ geo B b := by
    intro a b hab
    induction hab with
    | refl => exact Nat.le_refl _
    | step _ ih => rw [geo_succ_sub]; omega
  constructor
  · rintro rfl; exact hr
  · rintro ⟨h1, h2⟩
    rcases Nat.lt_trichotomy (decL B n).length j with hl | he | hg
    · have := mono ((decL B n).length + 1) j (by omega); omega
    · exact he
    · have := mono (j + 1) (decL B n).length (by omega); omega

/-! ### الاقترانُ ‎ℕ × ℕ ⟷ ℕ‎ ثمّ قوائمُ ℕ -/

/-- ‎tri(s) = s(s+1)/2‎ بصيغته المغلقة (فيُحسب للأعداد الكبيرة)، ومعادلةُ عَوده مبرهَنة. -/
def tri (s : Nat) : Nat := s * (s + 1) / 2

theorem tri_zero : tri 0 = 0 := rfl

theorem tri_succ (s : Nat) : tri (s + 1) = tri s + s + 1 := by
  unfold tri
  have e : (s + 1) * (s + 1 + 1) = s * (s + 1) + (s + 1) * 2 := by
    simp only [Nat.mul_add, Nat.add_mul, Nat.mul_one, Nat.one_mul]; omega
  rw [e, Nat.add_mul_div_right _ _ (by decide)]; omega

def pair (u r : Nat) : Nat := tri (u + r) + r

def unpair : Nat → Nat × Nat
  | 0 => (0, 0)
  | z + 1 => let p := unpair z; if p.1 = 0 then (p.2 + 1, 0) else (p.1 - 1, p.2 + 1)

theorem pair_unpair : ∀ z, pair (unpair z).1 (unpair z).2 = z
  | 0 => rfl
  | z + 1 => by
    have ih := pair_unpair z
    simp only [unpair]
    split
    · rename_i h; simp only [pair, h, Nat.zero_add] at ih ⊢
      rw [Nat.add_zero, tri_succ]; omega
    · rename_i h; simp only [pair] at ih ⊢
      rw [show (unpair z).1 - 1 + ((unpair z).2 + 1) = (unpair z).1 + (unpair z).2 by omega]; omega

theorem tri_mono {s t : Nat} (h : s ≤ t) : tri s ≤ tri t := by
  induction h with
  | refl => exact Nat.le_refl _
  | step _ ih => rw [tri_succ]; omega

theorem pair_injective {u r u' r' : Nat} (h : pair u r = pair u' r') : u = u' ∧ r = r' := by
  unfold pair at h
  have hs : u + r = u' + r' := by
    rcases Nat.lt_trichotomy (u + r) (u' + r') with hl | he | hg
    · have := tri_mono (Nat.succ_le_of_lt hl); rw [tri_succ] at this; omega
    · exact he
    · have := tri_mono (Nat.succ_le_of_lt hg); rw [tri_succ] at this; omega
  rw [hs] at h; omega

theorem unpair_pair (u r : Nat) : unpair (pair u r) = (u, r) := by
  have h := pair_unpair (pair u r)
  obtain ⟨h1, h2⟩ := pair_injective h
  exact Prod.ext h1 h2

theorem unpair_le (z : Nat) : (unpair z).1 ≤ z ∧ (unpair z).2 ≤ z := by
  have h := pair_unpair z
  simp only [pair] at h
  have : (unpair z).1 + (unpair z).2 ≤ tri ((unpair z).1 + (unpair z).2) := by
    generalize (unpair z).1 + (unpair z).2 = s
    induction s with
    | zero => exact Nat.zero_le _
    | succ s ih => rw [tri_succ]; omega
  omega

/-- قائمةٌ من ℕ: ‎enc(a :: l) = 1 + pair(a, enc l)‎. -/
def encS : List Nat → Nat
  | [] => 0
  | a :: l => 1 + pair a (encS l)

def decSAux : Nat → Nat → List Nat
  | 0, _ => []
  | f + 1, n => if n = 0 then [] else (unpair (n - 1)).1 :: decSAux f (unpair (n - 1)).2

def decS (n : Nat) : List Nat := decSAux n n

theorem decSAux_enc : ∀ (l : List Nat) f, encS l ≤ f → decSAux f (encS l) = l
  | [], f, _ => by cases f <;> simp [encS, decSAux]
  | a :: l, f, hf => by
    obtain ⟨f', rfl⟩ : ∃ f', f = f' + 1 := ⟨f - 1, by simp [encS] at hf; omega⟩
    simp only [decSAux, encS]
    have hne : ¬ (1 + pair a (encS l) = 0) := by omega
    simp only [hne, ↓reduceIte]
    rw [show 1 + pair a (encS l) - 1 = pair a (encS l) by omega, unpair_pair]
    congr 1
    apply decSAux_enc l f'
    have := (unpair_le (pair a (encS l))).2
    rw [unpair_pair] at this
    simp [encS] at hf; omega

theorem decS_encS (l : List Nat) : decS (encS l) = l := decSAux_enc l _ (Nat.le_refl _)

theorem encS_decSAux : ∀ f n, n ≤ f → encS (decSAux f n) = n
  | 0, n, h => by simp [decSAux, encS]; omega
  | f + 1, n, h => by
    simp only [decSAux]
    split
    · rename_i h0; simp [encS, h0]
    · simp only [encS]
      rw [encS_decSAux f _ (by have := (unpair_le (n - 1)).2; omega), pair_unpair]; omega

theorem encS_decS (n : Nat) : encS (decS n) = n := encS_decSAux n n (Nat.le_refl _)

end SLGE
