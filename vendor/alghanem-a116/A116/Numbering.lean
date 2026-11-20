import A116.Count

/-!
# الترقيمُ العامّ وترتيبُ الجسر واقترانُ كانتور

منقولٌ من `tools/rasm_recovery/PROOF_AR.md` («جسر العدد»): هناك نثرٌ وفحصٌ
استقصائيٌّ حتى الطول ٢، وهنا مبرهَنٌ لكلّ طول.

## الترقيمُ العامّ هو الطيُّ بلا محجورين

`Fold.lean` برهن أنّ ‎off(|w|) + fold(w)‎ تقابلٌ من الجائزات إلى ℕ. وحين لا محجورَ
(‎b = 0‎) تصير كلُّ كلمةٍ جائزة (`valid_zero_iff`)، و‎S(n) = Bⁿ‎ (`S_zero_pow`)، و‎off(n)
= Σ_{j<n} Bʲ‎ (`off_zero_geo`)، و‎fold‎ هو قيمةُ الأرقام بالأساس ‎B‎ من الأعلى
(`fold_zero_eq_digits`). فالترقيمُ العامّ ‎F(a) = O(n) + v(a)‎ في الجسر **حالةٌ خاصّةٌ**
من الطيّ المبرهَن، لا ترقيمٌ آخر.

## ترتيبُ الجسر

`canonical116.bridge.A116` يرتّب الحواملَ بالهمزة أوّلًا والألفِ آخرًا، و`Cells.lean`
بالألف أوّلًا والهمزةِ آخرًا. فالفرقُ تبديلُ صفّين: `swapCarrier`. و`bridgeIndex` رقمُ
الخانة في ترتيب الجسر، ويُطابَق في CI بجدولٍ يطبعه `Main`.

## المبرهنات

* `atomNumber_injective`، `atomNumber_surjective`: ‎F‎ على سلاسل الخانات بترتيب الجسر
  تقابلٌ إلى ℕ كلِّها، بلا ترخيصٍ مقطعيّ (سلاسلُ الوقف ‎CVCC‎ داخلة).
* `pair_injective`، `pair_surjective`: اقترانُ كانتور ‎P(u, r) = T(u+r) + r‎ تقابلٌ
  ‎ℕ × ℕ → ℕ‎، فعددٌ واحدٌ يحمل رقمَ الذرّات ورتبةَ الليف معًا.
-/

namespace A116.Numbering

open A116.Fold

/-! ## الترقيمُ العامّ -/

theorem valid_zero_iff (f : Nat) : ∀ (o : Bool) (w : List Nat),
    Valid f 0 o w ↔ ∀ x ∈ w, x < f
  | _, [] => by simp [Valid]
  | o, x :: xs => by
    simp only [Valid, Nat.add_zero, List.mem_cons, forall_eq_or_imp]
    constructor
    · rintro ⟨hx, _, hv⟩
      rw [decide_eq_true hx] at hv
      exact ⟨hx, (valid_zero_iff f true xs).1 hv⟩
    · rintro ⟨hx, hxs⟩
      refine ⟨hx, fun h => absurd hx (Nat.not_lt.2 h), ?_⟩
      rw [decide_eq_true hx]
      exact (valid_zero_iff f true xs).2 hxs

theorem S_zero_pow (f : Nat) : ∀ n, S f 0 n true = f ^ n
  | 0 => rfl
  | n + 1 => by simp only [S, Nat.zero_mul, Nat.add_zero, S_zero_pow f n, Nat.pow_succ,
      Nat.mul_comm]

/-- ‎Σ_{j<n} Bʲ‎. -/
def geo (f : Nat) : Nat → Nat
  | 0 => 0
  | n + 1 => geo f n + f ^ n

theorem off_zero_geo (f : Nat) : ∀ n, off f 0 n = geo f n
  | 0 => rfl
  | n + 1 => by simp only [off, geo, T, S_zero_pow, off_zero_geo f n]

/-- قيمةُ الأرقام بالأساس ‎B‎ من الأعلى، كما في `fold_atoms`: ‎v ← B·v + d‎. -/
def digits (f : Nat) (w : List Nat) : Nat := w.foldl (fun acc d => f * acc + d) 0

private theorem foldl_shift (f : Nat) : ∀ (w : List Nat) (acc : Nat),
    w.foldl (fun a d => f * a + d) acc = acc * f ^ w.length + w.foldl (fun a d => f * a + d) 0
  | [], acc => by simp
  | d :: ds, acc => by
    simp only [List.foldl_cons, List.length_cons, Nat.mul_zero, Nat.zero_add]
    rw [foldl_shift f ds (f * acc + d), foldl_shift f ds d, Nat.pow_succ]
    rw [Nat.add_mul, Nat.mul_comm (f ^ ds.length) f, ← Nat.mul_assoc, Nat.mul_comm acc f,
      Nat.add_assoc]

theorem digits_cons (f d : Nat) (ds : List Nat) :
    digits f (d :: ds) = d * f ^ ds.length + digits f ds := by
  simp only [digits, List.foldl_cons, Nat.mul_zero, Nat.zero_add]
  exact foldl_shift f ds d

theorem fold_zero_eq_digits (f : Nat) : ∀ (w : List Nat), (∀ x ∈ w, x < f) →
    fold f 0 true w = digits f w
  | [], _ => rfl
  | x :: xs, h => by
    have hx : x < f := h x (by simp)
    rw [fold_cons_free f 0 hx, S_zero_pow, digits_cons,
      fold_zero_eq_digits f xs fun y hy => h y (by simp [hy])]

/-- ‎F(a) = O(n) + v(a)‎ بصيغته الصريحة. -/
theorem foldAny_zero_closed (f : Nat) (w : List Nat) (h : ∀ x ∈ w, x < f) :
    foldAny f 0 w = geo f w.length + digits f w := by
  rw [foldAny, off_zero_geo, fold_zero_eq_digits f w h]

/-! ## ترتيبُ الجسر -/

/-- الألفُ (0) والهمزة (28) يتبادلان، وسائرُ الحوامل في مواضعها. -/
def swapCarrier (i : Nat) : Nat := if i = 0 then 28 else if i = 28 then 0 else i

/-- رقمُ الخانة في `canonical116.bridge.A116`. -/
def bridgeIndex (c : Cell) : Nat := 4 * swapCarrier c.carrier.val + c.haraka.index

/-- الحالةُ برقمها في ترتيب `THE_HARAKAT`: فتحة، ضمّة، كسرة، سكون. -/
def harakaOf : Nat → Haraka
  | 0 => .fatha
  | 1 => .damma
  | 2 => .kasra
  | _ => .sukun

/-- الخانةُ ذاتُ الرقم في ترتيب الجسر. -/
def bridgeCell (k : Nat) : Cell :=
  ⟨⟨swapCarrier (k / 4) % 29, Nat.mod_lt _ (by decide)⟩, harakaOf (k % 4)⟩

theorem bridgeCell_bridgeIndex_on_cells : ∀ c ∈ cells, bridgeCell (bridgeIndex c) = c := by
  decide +kernel

theorem bridgeCell_bridgeIndex (c : Cell) : bridgeCell (bridgeIndex c) = c :=
  bridgeCell_bridgeIndex_on_cells c (mem_cells c)

theorem bridgeIndex_bridgeCell : ∀ k, k < 116 → bridgeIndex (bridgeCell k) = k := by
  decide +kernel

theorem bridgeIndex_lt_on_cells : ∀ c ∈ cells, bridgeIndex c < 116 := by decide +kernel

theorem bridgeIndex_lt (c : Cell) : bridgeIndex c < 116 :=
  bridgeIndex_lt_on_cells c (mem_cells c)

/-- ترتيبُ الجسر وترتيبُ `Cells` يختلفان في ثمانيةِ مواضعَ لا غير: صفّا الألف والهمزة. -/
theorem orders_differ_only_in_two_rows :
    ((cells.zipIdx).filter fun (c, i) => bridgeIndex c != i).length = 8 := by
  decide +kernel

theorem bridgeIndex_injective {c d : Cell} (h : bridgeIndex c = bridgeIndex d) : c = d := by
  rw [← bridgeCell_bridgeIndex c, h, bridgeCell_bridgeIndex]

/-- ‎F‎ على سلاسل الخانات بترتيب الجسر: الترقيمُ العامّ في `contextual.fold_atoms`. -/
def atomNumber (w : List Cell) : Nat := foldAny 116 0 (w.map bridgeIndex)

private theorem map_bridge_lt (w : List Cell) : ∀ x ∈ w.map bridgeIndex, x < 116 := by
  intro x hx
  obtain ⟨c, _, rfl⟩ := List.mem_map.1 hx
  exact bridgeIndex_lt c

theorem atomNumber_closed (w : List Cell) :
    atomNumber w = geo 116 w.length + digits 116 (w.map bridgeIndex) := by
  rw [atomNumber, foldAny_zero_closed 116 _ (map_bridge_lt w), List.length_map]

private theorem map_injective_of {w w' : List Cell}
    (h : w.map bridgeIndex = w'.map bridgeIndex) : w = w' := by
  have := congrArg (List.map bridgeCell) h
  simpa [List.map_map, Function.comp_def, bridgeCell_bridgeIndex] using this

/-- **التباين:** سلسلتان بعددٍ واحدٍ هما واحدة، بأيّ طول. -/
theorem atomNumber_injective {w w' : List Cell} (h : atomNumber w = atomNumber w') :
    w = w' :=
  map_injective_of <| foldAny_injective 116 0
    ((valid_zero_iff 116 true _).2 (map_bridge_lt w))
    ((valid_zero_iff 116 true _).2 (map_bridge_lt w')) h

/-- **الشمول:** كلُّ عددٍ طبيعيٍّ رقمُ سلسلةٍ واحدة. -/
theorem atomNumber_surjective (k : Nat) : ∃ w, atomNumber w = k := by
  obtain ⟨l, hv, hk⟩ := foldAny_surjective 116 0 (by decide) k
  have hl := (valid_zero_iff 116 true l).1 hv
  refine ⟨l.map bridgeCell, ?_⟩
  have : (l.map bridgeCell).map bridgeIndex = l := by
    rw [List.map_map]
    conv => rhs; rw [← List.map_id l]
    apply List.map_congr_left
    intro x hx
    exact bridgeIndex_bridgeCell x (hl x hx)
  rw [atomNumber, this, hk]

/-! ## اقترانُ كانتور -/

/-- ‎tri(s) = s(s+1)/2‎ مكتوبًا بالاستقراء. -/
def tri : Nat → Nat
  | 0 => 0
  | s + 1 => tri s + s + 1

/-- ‎P(u, r) = tri(u + r) + r‎. -/
def pair (u r : Nat) : Nat := tri (u + r) + r

theorem tri_mono {s t : Nat} (h : s ≤ t) : tri s ≤ tri t := by
  induction h with
  | refl => exact Nat.le_refl _
  | step _ ih => simp only [tri]; omega

theorem tri_closed (s : Nat) : 2 * tri s = s * (s + 1) := by
  induction s with
  | zero => rfl
  | succ s ih =>
    simp only [tri, Nat.mul_add, Nat.add_mul, Nat.mul_one, Nat.one_mul] at ih ⊢
    omega

/-- القطرُ يُعيَّن من العدد: ‎r ≤ s‎ يجعل ‎tri(s) ≤ P < tri(s+1)‎. -/
private theorem diag_eq {s t r q : Nat} (hr : r ≤ s) (hq : q ≤ t)
    (h : tri s + r = tri t + q) : s = t := by
  rcases Nat.lt_trichotomy s t with hst | hst | hst
  · have := tri_mono (Nat.succ_le_of_lt hst); simp only [tri] at this; omega
  · exact hst
  · have := tri_mono (Nat.succ_le_of_lt hst); simp only [tri] at this; omega

/-- **التباين.** -/
theorem pair_injective {u r u' r' : Nat} (h : pair u r = pair u' r') : u = u' ∧ r = r' := by
  unfold pair at h
  have hs := diag_eq (Nat.le_add_left r u) (Nat.le_add_left r' u') h
  rw [hs] at h
  omega

/-- **الشمول.** -/
theorem pair_surjective : ∀ z, ∃ u r, pair u r = z
  | 0 => ⟨0, 0, rfl⟩
  | z + 1 => by
    obtain ⟨u, r, h⟩ := pair_surjective z
    cases u with
    | zero => exact ⟨r + 1, 0, by simp only [pair, tri, Nat.zero_add, Nat.add_zero] at h ⊢; omega⟩
    | succ u => exact ⟨u, r + 1, by simp only [pair] at h ⊢; rw [show u + (r + 1) = u + 1 + r by omega]; omega⟩

/-- الصيغةُ المغلقةُ في `contextual.pair`: ‎(u+r)(u+r+1)/2 + r‎. -/
theorem pair_closed (u r : Nat) : pair u r = (u + r) * (u + r + 1) / 2 + r := by
  have := tri_closed (u + r)
  unfold pair
  omega

end A116.Numbering
