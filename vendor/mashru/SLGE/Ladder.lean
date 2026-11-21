import SLGE.Core

/-!
# السلّم: مخرج ← خانة ← مقطع ← كلمة ← جملة — رقمٌ فريدٌ وفكٌّ مبرهَنان في كلّ درجة

**المعلَن (شاهدٌ لا قانون):** مخارجُ الحوامل بترتيب وصف سيبويه في «الكتاب» (الجزء 4، ص431)،
واللامُ مخرجًا مستقلًّا (جملتُها ساقطةٌ من النسختين المودَعتين) — فتصير خمسةَ عشرَ مخرجًا للحوامل،
ومعها الخيشومُ ستّةَ عشر كما نصّ. الحواملُ بهذا الترتيب:
ء ه ا | ع ح | غ خ | ق | ك | ج ش ي | ض | ل | ن | ر | ط د ت | ز س ص | ظ ذ ث | ف | ب م و
فالألفُ 2، والياءُ 11، والواوُ 28.

**القانونُ في المقطع:** المتحرّكُ يفتح (‎29 × 3 = 87‎)؛ والمدُّ بعد الفتحة ألف، وبعد الضمّة واو، وبعد
الكسرة ياء (فلا يحمل المدُّ معلومةً)؛ والمُغلِقُ بعد متحرّكٍ أيُّ ساكنٍ إلّا حرفَ مدّ حركته (28)؛ وبعد المدّ
أو المُغلِق أيُّ ساكن (29). ستّةُ أنواع: CV، CVV، CVC، CVVC، CVCC، CVVCC.
-/

namespace SLGE

/-! ## الدرجة 0: المخرج ← الحامل -/

def makharijSizes : List Nat := [3, 2, 2, 1, 1, 3, 1, 1, 1, 1, 3, 3, 3, 1, 3]

theorem makharij_count : makharijSizes.length = 15 ∧ makharijSizes.sum = 29 := by decide

def carrierEnc (m k : Nat) : Nat := blockEnc makharijSizes m k
def carrierDec (c : Nat) : Nat × Nat := blockDec makharijSizes c

theorem carrier_dec_enc (m k : Nat) (hm : m < 15) (hk : k < makharijSizes.getD m 0) :
    carrierDec (carrierEnc m k) = (m, k) :=
  blockDec_enc _ m k (by simpa [makharijSizes] using hm) hk

theorem carrier_enc_dec (c : Nat) (hc : c < 29) :
    carrierEnc (carrierDec c).1 (carrierDec c).2 = c :=
  (blockEnc_dec makharijSizes c (by simpa [makharijSizes] using hc)).2.2

/-! ## الدرجة 1: الحامل والحالة ← الخانة (‎4c + s‎؛ الحالات: فتحة 0، ضمّة 1، كسرة 2، سكون 3) -/

def cellEnc (c s : Nat) : Nat := mixEnc 1 4 c 0 s
def cellDec (n : Nat) : Nat × Nat := ((mixDec 1 4 n).1, (mixDec 1 4 n).2.2)

theorem cell_dec_enc (c s : Nat) (hs : s < 4) : cellDec (cellEnc c s) = (c, s) := by
  simp [cellDec, cellEnc, mixDec_enc 1 4 c 0 s (by decide) hs]

theorem cell_enc_dec (n : Nat) : cellEnc (cellDec n).1 (cellDec n).2 = n := by
  have := mixEnc_dec 1 4 n (by decide) (by decide)
  simp only [mixDec, Nat.mod_one] at this
  simpa [cellEnc, cellDec, mixDec] using this

theorem cell_range (c s : Nat) (hc : c < 29) (hs : s < 4) : cellEnc c s < 116 := by
  simp [cellEnc, mixEnc]; omega

/-! ## الدرجة 2: الخانات ← المقطع -/

/-- المقطع: (النوع، الفاتح، المُغلِقُ الأوّل، المُغلِقُ الثاني). -/
abbrev Syl := Nat × Nat × Nat × Nat

/-- ‎(A₁, A₂)‎ لكلّ نوع: عددُ خيارات المُغلِقَين (1 = لا مُغلِق). -/
def radix : Nat → Nat × Nat
  | 0 => (1, 1)     -- CV
  | 1 => (1, 1)     -- CVV
  | 2 => (28, 1)    -- CVC
  | 3 => (29, 1)    -- CVVC
  | 4 => (28, 29)   -- CVCC
  | _ => (29, 29)   -- CVVCC

def sylSizes : List Nat := (List.range 6).map fun t => 87 * (radix t).1 * (radix t).2

theorem syl_sizes : sylSizes = [87, 87, 2436, 2523, 70644, 73167] ∧ sylSizes.sum = 148944 := by
  decide

def Valid (x : Syl) : Prop :=
  x.1 < 6 ∧ x.2.1 < 87 ∧ x.2.2.1 < (radix x.1).1 ∧ x.2.2.2 < (radix x.1).2

def sylEnc (x : Syl) : Nat :=
  blockEnc sylSizes x.1 (mixEnc (radix x.1).1 (radix x.1).2 x.2.1 x.2.2.1 x.2.2.2)

def sylDec (n : Nat) : Syl :=
  let b := blockDec sylSizes n
  let r := radix b.1
  let m := mixDec r.1 r.2 b.2
  (b.1, m.1, m.2.1, m.2.2)

theorem radix_pos (t : Nat) : 0 < (radix t).1 ∧ 0 < (radix t).2 := by
  unfold radix; split <;> decide

theorem sylSizes_getD (t : Nat) (ht : t < 6) : sylSizes.getD t 0 = 87 * (radix t).1 * (radix t).2 := by
  match t, ht with
  | 0, _ | 1, _ | 2, _ | 3, _ | 4, _ | 5, _ => rfl

theorem mix_lt (A B C o k₁ k₂ : Nat) (ho : o < A) (h₁ : k₁ < B) (h₂ : k₂ < C) :
    mixEnc B C o k₁ k₂ < A * B * C := by
  simp only [mixEnc]
  have : o * B + k₁ < A * B := by
    have := Nat.mul_le_mul_right B (Nat.succ_le_of_lt ho); rw [Nat.succ_mul] at this; omega
  have := Nat.mul_le_mul_right C (Nat.succ_le_of_lt this); rw [Nat.succ_mul] at this; omega

/-- **فكُّ المقطع:** رقمُه يعيده بعينه. -/
theorem syl_dec_enc (x : Syl) (h : Valid x) : sylDec (sylEnc x) = x := by
  obtain ⟨t, o, k₁, k₂⟩ := x
  obtain ⟨ht, ho, h₁, h₂⟩ := h
  simp only [sylDec, sylEnc]
  rw [blockDec_enc sylSizes t _ (by simpa [sylSizes] using ht)
    (by rw [sylSizes_getD t ht]; exact mix_lt 87 _ _ o k₁ k₂ ho h₁ h₂)]
  simp only [mixDec_enc _ _ o k₁ k₂ h₁ h₂]

/-- **الشمول:** كلُّ عددٍ دون ‎148,944‎ رقمُ مقطعٍ صحيحٍ واحد. -/
theorem syl_enc_dec (n : Nat) (hn : n < 148944) : Valid (sylDec n) ∧ sylEnc (sylDec n) = n := by
  have hb := blockEnc_dec sylSizes n (by rw [syl_sizes.2]; exact hn)
  have ht : (blockDec sylSizes n).1 < 6 := by simpa [sylSizes] using hb.1
  have hp := radix_pos (blockDec sylSizes n).1
  have hin := hb.2.1
  rw [sylSizes_getD _ ht] at hin
  have hl := mixDec_lt 87 _ _ _ hp.1 hp.2 hin
  refine ⟨⟨ht, hl.1, hl.2.1, hl.2.2⟩, ?_⟩
  simp only [sylEnc, sylDec]
  rw [mixEnc_dec _ _ _ hp.1 hp.2]
  exact hb.2.2

/-! ### المقطع ← خاناته (الحاملُ بترتيب المخارج، والحالة) -/

def maddOf (h : Nat) : Nat := if h = 0 then 2 else if h = 1 then 28 else 11

def skip (m k : Nat) : Nat := if k < m then k else k + 1
def unskip (m c : Nat) : Nat := if c < m then c else c - 1

def cellsOf (x : Syl) : List (Nat × Nat) :=
  let c0 := x.2.1 / 3; let h := x.2.1 % 3; let k₁ := x.2.2.1; let k₂ := x.2.2.2
  match x.1 with
  | 0 => [(c0, h)]
  | 1 => [(c0, h), (maddOf h, 3)]
  | 2 => [(c0, h), (skip (maddOf h) k₁, 3)]
  | 3 => [(c0, h), (maddOf h, 3), (k₁, 3)]
  | 4 => [(c0, h), (skip (maddOf h) k₁, 3), (k₂, 3)]
  | _ => [(c0, h), (maddOf h, 3), (k₁, 3), (k₂, 3)]

/-- المقطعُ من خاناته: النوعُ يُقرأ من الطول ومن كون الثانية مدَّ الحركة. -/
def sylOfCells : List (Nat × Nat) → Option Syl
  | [(c0, h)] => some (0, 3 * c0 + h, 0, 0)
  | [(c0, h), (a, _)] =>
    if a = maddOf h then some (1, 3 * c0 + h, 0, 0) else some (2, 3 * c0 + h, unskip (maddOf h) a, 0)
  | [(c0, h), (a, _), (b, _)] =>
    if a = maddOf h then some (3, 3 * c0 + h, b, 0) else some (4, 3 * c0 + h, unskip (maddOf h) a, b)
  | [(c0, h), _, (b, _), (d, _)] => some (5, 3 * c0 + h, b, d)
  | _ => none

theorem skip_ne (m k : Nat) : skip m k ≠ m := by unfold skip; split <;> omega
theorem unskip_skip (m k : Nat) : unskip m (skip m k) = k := by
  unfold skip unskip
  by_cases hk : k < m
  · simp [hk]
  · have : ¬ (k + 1 < m) := by omega
    simp [hk, this]
theorem skip_lt (m k : Nat) (hm : m < 29) (hk : k < 28) : skip m k < 29 := by unfold skip; split <;> omega

theorem onset (o : Nat) : 3 * (o / 3) + o % 3 = o := by omega

/-- **فكُّ المقطع من خاناته:** الخاناتُ تعيد المقطعَ بعينه. -/
theorem syl_of_cells (x : Syl) (h : Valid x) : sylOfCells (cellsOf x) = some x := by
  obtain ⟨t, o, k₁, k₂⟩ := x
  obtain ⟨ht, ho, h₁, h₂⟩ := h
  have hO := onset o
  match t, ht with
  | 0, _ => simp only [radix] at h₁ h₂; simp [cellsOf, sylOfCells, hO]; omega
  | 1, _ => simp only [radix] at h₁ h₂; simp [cellsOf, sylOfCells, hO]; omega
  | 2, _ =>
    simp only [radix] at h₁ h₂
    simp [cellsOf, sylOfCells, skip_ne, unskip_skip, hO]; omega
  | 3, _ => simp only [radix] at h₁ h₂; simp [cellsOf, sylOfCells, hO]; omega
  | 4, _ => simp [cellsOf, sylOfCells, skip_ne, unskip_skip, hO]
  | 5, _ => simp [cellsOf, sylOfCells, hO]

theorem sylEnc_lt (x : Syl) (h : Valid x) : sylEnc x < 148944 := by
  obtain ⟨t, o, k₁, k₂⟩ := x
  obtain ⟨ht, ho, h₁, h₂⟩ := h
  rw [← syl_sizes.2]
  exact blockEnc_lt _ _ _ (by simpa [sylSizes] using ht)
    (by rw [sylSizes_getD t ht]; exact mix_lt 87 _ _ o k₁ k₂ ho h₁ h₂)

/-! ## الدرجة 3: المقاطع ← الكلمة (عدٌّ تقابليٌّ بالأساس ‎148,944‎) -/

def wordEnc (w : List Syl) : Nat := encL 148944 (w.map sylEnc)
def wordDec (n : Nat) : List Syl := (decL 148944 n).map sylDec

/-- **فكُّ الكلمة.** -/
theorem word_dec_enc (w : List Syl) (h : ∀ x ∈ w, Valid x) : wordDec (wordEnc w) = w := by
  simp only [wordDec, wordEnc]
  rw [decL_encL 148944 (by decide) _ (by
    intro y hy; obtain ⟨x, hx, rfl⟩ := List.mem_map.1 hy; exact sylEnc_lt x (h x hx))]
  rw [List.map_map]
  conv => rhs; rw [← List.map_id w]
  exact List.map_congr_left fun x hx => syl_dec_enc x (h x hx)

/-- **الشمول:** كلُّ عددٍ رقمُ كلمةٍ واحدةٍ مقاطعُها صحيحة. -/
theorem word_enc_dec (n : Nat) : (∀ x ∈ wordDec n, Valid x) ∧ wordEnc (wordDec n) = n := by
  have hd : ∀ y ∈ decL 148944 n, y < 148944 := decAux_lt 148944 (by decide) n n
  refine ⟨fun x hx => ?_, ?_⟩
  · obtain ⟨y, hy, rfl⟩ := List.mem_map.1 hx; exact (syl_enc_dec y (hd y hy)).1
  · simp only [wordEnc, wordDec, List.map_map]
    have : (decL 148944 n).map (sylEnc ∘ sylDec) = decL 148944 n := by
      conv => rhs; rw [← List.map_id (decL 148944 n)]
      exact List.map_congr_left fun y hy => (syl_enc_dec y (hd y hy)).2
    rw [this, encL_decL 148944 (by decide)]

/-! ## الدرجة 4: الكلمات ← الجملة (قائمةٌ من ℕ بالاقتران) -/

def sentEnc (S : List (List Syl)) : Nat := encS (S.map wordEnc)
def sentDec (n : Nat) : List (List Syl) := (decS n).map wordDec

/-- **فكُّ الجملة.** -/
theorem sent_dec_enc (S : List (List Syl)) (h : ∀ w ∈ S, ∀ x ∈ w, Valid x) :
    sentDec (sentEnc S) = S := by
  simp only [sentDec, sentEnc, decS_encS, List.map_map]
  conv => rhs; rw [← List.map_id S]
  exact List.map_congr_left fun w hw => word_dec_enc w (h w hw)

/-- **الشمول:** كلُّ عددٍ رقمُ جملةٍ واحدة. -/
theorem sent_enc_dec (n : Nat) : sentEnc (sentDec n) = n := by
  simp only [sentEnc, sentDec, List.map_map]
  have : (decS n).map (wordEnc ∘ wordDec) = decS n := by
    conv => rhs; rw [← List.map_id (decS n)]
    exact List.map_congr_left fun y _ => (word_enc_dec y).2
  rw [this, encS_decS]

/-! ## تقطيعُ خانات الكلمة إلى مقاطعها: وحيدٌ ومبرهَن -/

def isSukunCell (y : Nat × Nat) : Bool := y.2 == 3

def grpAux : Nat → List (Nat × Nat) → List (List (Nat × Nat))
  | 0, _ => []
  | _ + 1, [] => []
  | f + 1, x :: t => (x :: t.takeWhile isSukunCell) :: grpAux f (t.dropWhile isSukunCell)

def grp (l : List (Nat × Nat)) : List (List (Nat × Nat)) := grpAux l.length l

def wordCells (w : List Syl) : List (Nat × Nat) := w.flatMap cellsOf

theorem cellsOf_shape (x : Syl) (h : Valid x) :
    ∃ hd tl, cellsOf x = hd :: tl ∧ isSukunCell hd = false ∧ ∀ y ∈ tl, isSukunCell y = true := by
  obtain ⟨t, o, k₁, k₂⟩ := x
  obtain ⟨ht, _, _, _⟩ := h
  have hm : o % 3 ≠ 3 := by omega
  match t, ht with
  | 0, _ | 1, _ | 2, _ | 3, _ | 4, _ | 5, _ =>
    exact ⟨_, _, rfl, by simp [isSukunCell, hm], by simp [isSukunCell]⟩

theorem take_drop (tl r : List (Nat × Nat)) (htl : ∀ y ∈ tl, isSukunCell y = true)
    (hr : ∀ y ∈ r.head?, isSukunCell y = false) :
    (tl ++ r).takeWhile isSukunCell = tl ∧ (tl ++ r).dropWhile isSukunCell = r := by
  induction tl with
  | nil =>
    cases r with
    | nil => simp
    | cons y r => have := hr y (by simp); simp [List.takeWhile, List.dropWhile, this]
  | cons y tl ih =>
    have hy := htl y (by simp)
    have := ih (fun z hz => htl z (by simp [hz]))
    simp [List.takeWhile, List.dropWhile, hy, this.1, this.2]

theorem wordCells_head (w : List Syl) (h : ∀ x ∈ w, Valid x) :
    ∀ y ∈ (wordCells w).head?, isSukunCell y = false := by
  cases w with
  | nil => simp [wordCells]
  | cons x w =>
    obtain ⟨hd, tl, he, hh, _⟩ := cellsOf_shape x (h x (by simp))
    intro y hy
    simp [wordCells, List.flatMap_cons, he] at hy
    rw [← hy]; exact hh

/-- **التقطيعُ وحيد:** خاناتُ الكلمة تنقسم إلى خانات مقاطعها بعينها. -/
theorem grp_wordCells : ∀ (w : List Syl), (∀ x ∈ w, Valid x) → ∀ f, (wordCells w).length ≤ f →
    grpAux f (wordCells w) = w.map cellsOf
  | [], _, f, _ => by cases f <;> simp [wordCells, grpAux]
  | x :: w, h, f, hf => by
    obtain ⟨hd, tl, he, _, htl⟩ := cellsOf_shape x (h x (by simp))
    have hw : ∀ y ∈ w, Valid y := fun y hy => h y (by simp [hy])
    obtain ⟨f', rfl⟩ : ∃ f', f = f' + 1 :=
      ⟨f - 1, by simp [wordCells, List.flatMap_cons, he] at hf; omega⟩
    have hwc : wordCells (x :: w) = hd :: (tl ++ wordCells w) := by
      simp [wordCells, List.flatMap_cons, he]
    have td := take_drop tl (wordCells w) htl (wordCells_head w hw)
    rw [hwc, grpAux, td.1, td.2, List.map_cons, he]
    congr 1
    apply grp_wordCells w hw f'
    simp [hwc] at hf; omega

/-- الكلمةُ من خاناتها. -/
def wordOfCells (l : List (Nat × Nat)) : Option (List Syl) :=
  (grp l).foldr (fun g acc => match sylOfCells g, acc with
    | some s, some a => some (s :: a)
    | _, _ => none) (some [])

theorem foldr_syls : ∀ (w : List Syl), (∀ x ∈ w, Valid x) →
    (w.map cellsOf).foldr (fun g acc => match sylOfCells g, acc with
      | some s, some a => some (s :: a)
      | _, _ => none) (some []) = some w
  | [], _ => rfl
  | x :: w, h => by
    simp only [List.map_cons, List.foldr_cons]
    rw [foldr_syls w (fun y hy => h y (by simp [hy])), syl_of_cells x (h x (by simp))]

/-- **فكُّ الكلمة من خاناتها:** الخاناتُ وحدَها تعيد مقاطعَ الكلمة بعينها. -/
theorem word_of_cells (w : List Syl) (h : ∀ x ∈ w, Valid x) : wordOfCells (wordCells w) = some w := by
  simp only [wordOfCells, grp]
  rw [grp_wordCells w h _ (Nat.le_refl _)]
  exact foldr_syls w h

/-! ## السلّمُ كلُّه -/

/-- **من رقم الجملة إلى المخارج، ومنها إلى رقم الجملة:** كلُّ جملةٍ صحيحة تُرقَّم، ورقمُها يُفكّ إلى
كلماتها فمقاطعها فخاناتها، وخاناتُ كلّ كلمةٍ تعيد مقاطعها، وكلُّ حاملٍ يعود إلى مخرجه ورتبته فيه. -/
theorem ladder (S : List (List Syl)) (h : ∀ w ∈ S, ∀ x ∈ w, Valid x) :
    sentDec (sentEnc S) = S ∧
    (∀ w ∈ S, wordOfCells (wordCells w) = some w) ∧
    (∀ w ∈ S, ∀ y ∈ wordCells w, y.1 < 29 →
      carrierEnc (carrierDec y.1).1 (carrierDec y.1).2 = y.1 ∧ cellDec (cellEnc y.1 y.2) = y) := by
  refine ⟨sent_dec_enc S h, fun w hw => word_of_cells w (h w hw), ?_⟩
  intro w hw y hy hc
  refine ⟨carrier_enc_dec y.1 hc, ?_⟩
  have : y.2 < 4 := by
    obtain ⟨x, hx, hyx⟩ := List.mem_flatMap.1 hy
    obtain ⟨t, o, k₁, k₂⟩ := x
    have hv := h w hw _ hx
    obtain ⟨ht, _, _, _⟩ := hv
    match t, ht with
    | 0, _ | 1, _ | 2, _ | 3, _ | 4, _ | 5, _ =>
      simp [cellsOf] at hyx <;> (try rcases hyx with rfl | rfl | rfl | rfl) <;>
        (try rcases hyx with rfl | rfl | rfl) <;> (try rcases hyx with rfl | rfl) <;>
        (try subst hyx) <;> simp <;> omega
  exact cell_dec_enc y.1 y.2 this

end SLGE
