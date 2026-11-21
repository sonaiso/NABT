/-!
# الطيُّ والفكّ — تقابلٌ مبرهَن بين الكلمات الجائزة والأعداد

منقولٌ من مستودع Algebra: `src/algebra/folding.py` (المبرهنات ١ و٣ و٤)،
بتعريفاته نفسِها حرفًا: `completions` هي `S`، و`admissible_count` هي `T`، و`fold`
و`unfold` و`offset` و`fold_any` بأسمائها. والفرقُ أنّ البرهانَ هناك نثرٌ في
وثيقةٍ ومفحوصٌ بالعدّ إلى طولٍ مُعلَن، وهنا تفحصه نواةُ Lean **لكلّ طول**.

## الإطار

أبجديّةٌ `{0, …, f+b−1}`: الرموزُ `0 … f−1` **أحرار**، و`f … f+b−1` **محجورون**.
والكلمةُ **جائزة** إن لم يقع محجوران متجاوران. ومعلَمةُ البدء `open` تقول أيجوز أن
يكون الرمزُ الأوّلُ محجورًا (`true`: نعم، وهي حالُ `T`؛ `false`: لا).

## المبرهنات

* `fold_lt`، `unfold_fold`، `unfold_spec`: **التقابل.** `fold open` يرسل الجائزاتِ
  الطولِ `n` إلى `{0, …, S n open − 1}`، و`unfold` معكوسُه من الجهتين.
  فـ`S n open` هو عددُ الجائزات **بالتقابل لا بالتعداد**.
* `T_succ_succ`: **العدّ.** ‎T(n+2) = f·T(n+1) + f·b·T(n)‎ (المبرهنة ١).
* `foldAny_injective`، `foldAny_surjective`: **الطيُّ بلا طول.** ‎off(|w|) + fold(w)‎
  تقابلٌ من الجائزات بكلّ أطوالها إلى ℕ كلِّها: التباينُ بلا شرط، والشمولُ بشرط ‎f ≥ 1‎
  (المبرهنة ٤).

## ما لم يُنقَل

الرتابةُ بالترتيب المعجميّ (من المبرهنة ٣) والمعدَّلُ ‎ρ‎ (المبرهنة ٢)؛ فالأولى
لا يحتاجها التقابل، والثانية وصفٌ عائمٌ لا جزءٌ منه.
-/

namespace A116.Fold

variable (f b : Nat)

/-- ‎S(m, open)‎: عددُ الجائزات الطولِ `m`، و`open` جوازُ أن يبدأ بمحجور. -/
def S : Nat → Bool → Nat
  | 0, _ => 1
  | m + 1, true => f * S m true + b * S m false
  | m + 1, false => f * S m true

/-- ‎T(n) = S(n, true)‎. -/
def T (n : Nat) : Nat := S f b n true

/-- الجوازُ: كلُّ رمزٍ في الأبجديّة، والمحجورُ لا يقع إلّا حيث يجوز، وبعده لا يجوز. -/
def Valid : Bool → List Nat → Prop
  | _, [] => True
  | o, x :: xs => x < f + b ∧ (f ≤ x → o = true) ∧ Valid (decide (x < f)) xs

/-- الطيّ: مجموعُ أحجام الأقسام التي تسبق الرمزَ في موضعه، ثمّ الباقي. -/
def fold : Bool → List Nat → Nat
  | _, [] => 0
  | o, x :: xs =>
    min x f * S f b xs.length true + (if o then (x - f) * S f b xs.length false else 0) +
      fold (decide (x < f)) xs

/-- الفكّ: يُعيَّن القسمُ بالقسمة، ثمّ يُنزَل في الباقي. -/
def unfold : Nat → Bool → Nat → List Nat
  | 0, _, _ => []
  | n + 1, _, k =>
    if k < f * S f b n true then
      k / S f b n true :: unfold n true (k % S f b n true)
    else
      (f + (k - f * S f b n true) / S f b n false) ::
        unfold n false ((k - f * S f b n true) % S f b n false)

/-! ## العدّ -/

/-- **المبرهنة ١:** ‎T(n+2) = f·T(n+1) + f·b·T(n)‎. -/
theorem T_succ_succ (n : Nat) : T f b (n + 2) = f * T f b (n + 1) + f * b * T f b n := by
  simp only [T, S]
  rw [Nat.mul_left_comm b f, Nat.mul_assoc]

theorem S_false_le_S_true (m : Nat) : S f b m false ≤ S f b m true := by
  cases m with
  | zero => simp [S]
  | succ m => simp only [S]; exact Nat.le_add_right _ _

/-! ## التقابل -/

private theorem lt_mul_of_lt_succ_mul {x A r c : Nat} (hr : r < A) (hx : x + 1 ≤ c) :
    x * A + r < c * A := by
  have h1 : x * A + r < x * A + A := Nat.add_lt_add_left hr _
  have h2 : x * A + A = (x + 1) * A := (Nat.succ_mul x A).symm
  have h3 : (x + 1) * A ≤ c * A := Nat.mul_le_mul_right A hx
  omega

/-- الطيُّ على رمزٍ حرٍّ في الصدر. -/
theorem fold_cons_free {o : Bool} {x : Nat} {xs : List Nat} (hx : x < f) :
    fold f b o (x :: xs) = x * S f b xs.length true + fold f b true xs := by
  rw [fold, Nat.min_eq_left (Nat.le_of_lt hx), Nat.sub_eq_zero_of_le (Nat.le_of_lt hx),
    decide_eq_true hx]
  cases o <;> simp

/-- الطيُّ على رمزٍ محجورٍ في الصدر (ولا يقع إلّا حيث يجوز). -/
theorem fold_cons_blocked {x : Nat} {xs : List Nat} (hx : f ≤ x) :
    fold f b true (x :: xs) =
      f * S f b xs.length true + ((x - f) * S f b xs.length false + fold f b false xs) := by
  rw [fold, Nat.min_eq_right hx, decide_eq_false (Nat.not_lt.2 hx)]
  simp [Nat.add_assoc]

/-- **الطيُّ داخلَ مداه:** صورةُ كلّ جائزةٍ أصغرُ من عدد الجائزات. -/
theorem fold_lt : ∀ (w : List Nat) (o : Bool), Valid f b o w → fold f b o w < S f b w.length o
  | [], _, _ => by simp [fold, S]
  | x :: xs, o, ⟨_, hblk, hv⟩ => by
    have ih := fold_lt xs _ hv
    by_cases hx : x < f
    · rw [decide_eq_true hx] at ih
      have key : x * S f b xs.length true + fold f b true xs < f * S f b xs.length true :=
        lt_mul_of_lt_succ_mul ih hx
      rw [fold_cons_free f b hx, List.length_cons]
      cases o <;> simp only [S] <;> omega
    · have hfx : f ≤ x := Nat.le_of_not_lt hx
      have ho : o = true := hblk hfx
      subst ho
      rw [decide_eq_false hx] at ih
      have key : (x - f) * S f b xs.length false + fold f b false xs < b * S f b xs.length false :=
        lt_mul_of_lt_succ_mul ih (by omega)
      rw [fold_cons_blocked f b hfx, List.length_cons]
      simp only [S]
      omega

/-- الفكُّ حين يقع العددُ في كتلة الأحرار. -/
theorem unfold_lo {n : Nat} {o : Bool} {k : Nat} (h : k < f * S f b n true) :
    unfold f b (n + 1) o k = k / S f b n true :: unfold f b n true (k % S f b n true) := by
  simp only [unfold, h, ↓reduceIte]

/-- الفكُّ حين يقع العددُ فوق كتلة الأحرار. -/
theorem unfold_hi {n : Nat} {o : Bool} {k : Nat} (h : ¬ k < f * S f b n true) :
    unfold f b (n + 1) o k =
      (f + (k - f * S f b n true) / S f b n false) ::
        unfold f b n false ((k - f * S f b n true) % S f b n false) := by
  simp only [unfold, h, ↓reduceIte]

/-- قسمةُ ‎(q·A + r)‎ على ‎A‎ حين ‎r < A‎: الخارجُ ‎q‎ والباقي ‎r‎. -/
private theorem divmod_of_lt {q A r : Nat} (hr : r < A) :
    (q * A + r) / A = q ∧ (q * A + r) % A = r := by
  have hA : 0 < A := Nat.lt_of_le_of_lt (Nat.zero_le _) hr
  constructor
  · rw [Nat.mul_comm, Nat.mul_add_div hA, Nat.div_eq_of_lt hr, Nat.add_zero]
  · rw [Nat.mul_comm, Nat.mul_add_mod, Nat.mod_eq_of_lt hr]

/-- **الفكُّ معكوسُ الطيّ من اليسار:** كلُّ جائزةٍ تعود بعينها. -/
theorem unfold_fold : ∀ (w : List Nat) (o : Bool), Valid f b o w →
    unfold f b w.length o (fold f b o w) = w
  | [], _, _ => by simp [unfold]
  | x :: xs, o, ⟨_, hblk, hv⟩ => by
    have ih := unfold_fold xs _ hv
    have hlt := fold_lt f b xs _ hv
    by_cases hx : x < f
    · rw [decide_eq_true hx] at ih hlt
      have hk : x * S f b xs.length true + fold f b true xs < f * S f b xs.length true :=
        lt_mul_of_lt_succ_mul hlt hx
      obtain ⟨hdiv, hmod⟩ := divmod_of_lt (q := x) hlt
      rw [List.length_cons, fold_cons_free f b hx, unfold_lo f b hk, hdiv, hmod, ih]
    · have hfx : f ≤ x := Nat.le_of_not_lt hx
      have ho : o = true := hblk hfx
      subst ho
      rw [decide_eq_false hx] at ih hlt
      have hk : ¬ (f * S f b xs.length true +
          ((x - f) * S f b xs.length false + fold f b false xs) < f * S f b xs.length true) := by
        omega
      obtain ⟨hdiv, hmod⟩ := divmod_of_lt (q := x - f) hlt
      rw [List.length_cons, fold_cons_blocked f b hfx, unfold_hi f b hk,
        Nat.add_sub_cancel_left, hdiv, hmod, ih, Nat.add_sub_cancel' hfx]

/-- **الفكُّ معكوسُ الطيّ من اليمين:** كلُّ عددٍ في المدى صورةُ جائزةٍ بالطول المطلوب. -/
theorem unfold_spec : ∀ (n : Nat) (o : Bool) (k : Nat), k < S f b n o →
    Valid f b o (unfold f b n o k) ∧ (unfold f b n o k).length = n ∧
      fold f b o (unfold f b n o k) = k
  | 0, _, k, hk => by
    simp only [S] at hk
    have : k = 0 := by omega
    subst this
    simp [unfold, Valid, fold]
  | n + 1, o, k, hk => by
    by_cases hlt : k < f * S f b n true
    · have hA : 0 < S f b n true := by
        rcases Nat.eq_zero_or_pos (S f b n true) with h | h
        · rw [h, Nat.mul_zero] at hlt; exact absurd hlt (Nat.not_lt_zero _)
        · exact h
      have hc : k / S f b n true < f := (Nat.div_lt_iff_lt_mul hA).2 hlt
      have hr : k % S f b n true < S f b n true := Nat.mod_lt _ hA
      obtain ⟨hv, hlen, hfold⟩ := unfold_spec n true _ hr
      have hdm : S f b n true * (k / S f b n true) + k % S f b n true = k := Nat.div_add_mod k _
      rw [unfold_lo f b hlt]
      refine ⟨⟨by omega, fun h => absurd h (Nat.not_le_of_lt hc), ?_⟩, ?_, ?_⟩
      · rw [decide_eq_true hc]; exact hv
      · rw [List.length_cons, hlen]
      · rw [fold_cons_free f b hc, hlen, hfold, Nat.mul_comm]; exact hdm
    · have ho : o = true := by
        cases o with
        | true => rfl
        | false => simp only [S] at hk; exact absurd hk hlt
      subst ho
      simp only [S] at hk
      have hk' : k - f * S f b n true < b * S f b n false := by omega
      have hB : 0 < S f b n false := by
        rcases Nat.eq_zero_or_pos (S f b n false) with h | h
        · rw [h, Nat.mul_zero] at hk'; exact absurd hk' (Nat.not_lt_zero _)
        · exact h
      have hq : (k - f * S f b n true) / S f b n false < b := (Nat.div_lt_iff_lt_mul hB).2 hk'
      have hr : (k - f * S f b n true) % S f b n false < S f b n false := Nat.mod_lt _ hB
      obtain ⟨hv, hlen, hfold⟩ := unfold_spec n false _ hr
      have hnot : ¬ (f + (k - f * S f b n true) / S f b n false < f) :=
        Nat.not_lt.2 (Nat.le_add_right _ _)
      have hdm : S f b n false * ((k - f * S f b n true) / S f b n false) +
          (k - f * S f b n true) % S f b n false = k - f * S f b n true := Nat.div_add_mod _ _
      rw [unfold_hi f b hlt]
      refine ⟨⟨Nat.add_lt_add_left hq f, fun _ => rfl, ?_⟩, ?_, ?_⟩
      · rw [decide_eq_false hnot]; exact hv
      · rw [List.length_cons, hlen]
      · rw [fold_cons_blocked f b (Nat.le_add_right _ _), hlen, hfold, Nat.add_sub_cancel_left,
          Nat.mul_comm ((k - f * S f b n true) / S f b n false)]
        omega

/-- **التقابلُ مجموعًا:** جائزتان بطولٍ واحدٍ لهما طيٌّ واحدٌ فهما واحدة. -/
theorem fold_injective {o : Bool} {w w' : List Nat} (hv : Valid f b o w) (hv' : Valid f b o w')
    (hlen : w.length = w'.length) (h : fold f b o w = fold f b o w') : w = w' := by
  rw [← unfold_fold f b w o hv, ← unfold_fold f b w' o hv', hlen, h]

/-! ## الطيُّ بلا طول (المبرهنة ٤) -/

/-- ‎off(n) = Σ_{m<n} T(m)‎: بدايةُ فترةِ الطول `n` في ℕ. -/
def off : Nat → Nat
  | 0 => 0
  | n + 1 => off n + T f b n

/-- الطيُّ بلا طول: ‎off(|w|) + fold(w)‎. -/
def foldAny (w : List Nat) : Nat := off f b w.length + fold f b true w

theorem T_pos (hf : 0 < f) : ∀ n, 0 < T f b n
  | 0 => by simp [T, S]
  | n + 1 => by
    have ih := T_pos hf n
    simp only [T, S] at ih ⊢
    have : 0 < f * S f b n true := Nat.mul_pos hf ih
    omega

theorem le_off (hf : 0 < f) : ∀ n, n ≤ off f b n
  | 0 => Nat.le_refl _
  | n + 1 => by
    have := le_off hf n; have := T_pos f b hf n; simp only [off]; omega

/-- كلُّ عددٍ يقع في فترة طولٍ واحدة. -/
theorem exists_interval (hf : 0 < f) (k : Nat) : ∃ n, off f b n ≤ k ∧ k < off f b (n + 1) := by
  have key : ∀ N, k < off f b N → ∃ n, off f b n ≤ k ∧ k < off f b (n + 1) := by
    intro N
    induction N with
    | zero => intro h; exact absurd h (Nat.not_lt_zero _)
    | succ N ih =>
      intro h
      by_cases hN : k < off f b N
      · exact ih hN
      · exact ⟨N, Nat.le_of_not_lt hN, h⟩
  have hk : k < off f b (k + 1) := Nat.lt_of_lt_of_le (Nat.lt_succ_self k) (le_off f b hf _)
  exact key _ hk

theorem off_mono {m n : Nat} (h : m ≤ n) : off f b m ≤ off f b n := by
  induction h with
  | refl => exact Nat.le_refl _
  | step _ ih => simp only [off]; omega

/-- **الطيُّ بلا طول متباين:** لا يُستعار الطولُ من خارج. -/
theorem foldAny_injective {w w' : List Nat} (hv : Valid f b true w)
    (hv' : Valid f b true w') (h : foldAny f b w = foldAny f b w') : w = w' := by
  have h1 := fold_lt f b w true hv
  have h2 := fold_lt f b w' true hv'
  unfold foldAny at h
  have hlen : w.length = w'.length := by
    rcases Nat.lt_trichotomy w.length w'.length with hl | hl | hl
    · have := off_mono f b (Nat.succ_le_of_lt hl)
      simp only [off, T] at this; omega
    · exact hl
    · have := off_mono f b (Nat.succ_le_of_lt hl)
      simp only [off, T] at this; omega
  rw [hlen] at h
  exact fold_injective f b hv hv' hlen (by omega)

/-- **الطيُّ بلا طول شامل:** كلُّ عددٍ طبيعيٍّ صورةُ جائزة. -/
theorem foldAny_surjective (hf : 0 < f) (k : Nat) : ∃ w, Valid f b true w ∧ foldAny f b w = k := by
  obtain ⟨n, hlo, hhi⟩ := exists_interval f b hf k
  have hin : k - off f b n < S f b n true := by simp only [off, T] at hhi; omega
  obtain ⟨hv, hlen, hfold⟩ := unfold_spec f b n true _ hin
  exact ⟨_, hv, by unfold foldAny; rw [hlen, hfold]; omega⟩

end A116.Fold
