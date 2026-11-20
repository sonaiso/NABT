import A116.Model
import A116.Fold

/-!
# عددُ السلاسل التي يقبلها النموذج — بالتقابل لا بالتعداد

يجمع هذا الملفّ المبرهنتين: توصيفَ النموذج (`run_ne_fellOut_iff` في `Model.lean`)
وتقابلَ الطيّ والفكّ (`Fold.lean`)، على الـ116 بعينها.

## الترميز

الخاناتُ المتحرّكةُ ‎29 × 3 = 87‎ أحرار، وخاناتُ السكون ‎29‎ محجورون:

* متحرّكة: ‎code(ℓ, h) = 3ℓ + h‎ حيث ‎h ∈ {0, 1, 2}‎ للفتحة والضمّة والكسرة.
* ساكنة: ‎code(ℓ, سكون) = 87 + ℓ‎.

و`code` تقابلٌ بين الخانات و‎{0, …, 115}‎ (`decode_code` و`code_decode`).

## المبرهنات

* `admissible_iff_valid`: سلسلةٌ مقبولةٌ في النموذج **إذا وفقط إذا** كانت صورتُها
  كلمةً جائزةً لا تبدأ بمحجور (‎f = 87، b = 29، open = false‎).
* `cellFold_lt` و`cellFold_injective` و`cellFold_surjective`: **التقابل** بين
  المقبولات الطولِ `n` و‎{0, …, U(n) − 1}‎.
* `U_zero` و`U_one` و`U_succ_succ`: ‎U(0) = 1‎ و‎U(1) = 87‎ و
  ‎U(n+2) = 87·U(n+1) + 87·29·U(n)‎. فهذا عددُ ما يقبله النموذج، **مبرهَنًا لكلّ طول**.
* `hamil_ladder`: سلّمُ الأجيال في مستودع hamil (‎112، 11,760، …‎) هو ‎T(n)‎ نفسُه
  بـ‎f = 84، b = 28‎ على حقل الـ112، مفحوصًا إلى الجيل السادس.
-/

namespace A116

open Fold

/-- رقمُ الحالة غيرِ الساكنة. -/
def vowelOf : Nat → Haraka
  | 0 => .fatha
  | 1 => .damma
  | _ => .kasra

/-- الترميز: المتحرّكاتُ أوّلًا (أحرار)، ثمّ السواكن (محجورون). -/
def code : Cell → Nat
  | ⟨l, .fatha⟩ => 3 * l.val
  | ⟨l, .damma⟩ => 3 * l.val + 1
  | ⟨l, .kasra⟩ => 3 * l.val + 2
  | ⟨l, .sukun⟩ => 87 + l.val

/-- فكُّ الترميز؛ وهو معكوسُه على ‎{0, …, 115}‎. -/
def decode (x : Nat) : Cell :=
  if x < 87 then ⟨⟨(x / 3) % 29, Nat.mod_lt _ (by decide)⟩, vowelOf (x % 3)⟩
  else ⟨⟨(x - 87) % 29, Nat.mod_lt _ (by decide)⟩, .sukun⟩

theorem decode_code_on_cells : ∀ c ∈ cells, decode (code c) = c := by decide +kernel

theorem decode_code (c : Cell) : decode (code c) = c :=
  decode_code_on_cells c (mem_cells c)

theorem code_decode : ∀ x, x < 116 → code (decode x) = x := by decide +kernel

theorem code_lt (c : Cell) : code c < 87 + 29 := by
  obtain ⟨l, hh⟩ := c
  have h : l.val < 29 := l.isLt
  cases hh <;> simp only [code] <;> omega

theorem code_lt_87_iff (c : Cell) : code c < 87 ↔ c.isSukun = false := by
  obtain ⟨l, hh⟩ := c
  have h : l.val < 29 := l.isLt
  cases hh <;> simp [code, Cell.isSukun, Haraka.isSukun] <;> omega

theorem decide_code_lt (c : Cell) : decide (code c < 87) = !c.isSukun := by
  cases h : c.isSukun
  · simp [(code_lt_87_iff c).2 h]
  · have : ¬ code c < 87 := fun h' => by rw [(code_lt_87_iff c).1 h'] at h; cases h
    simp [this]

/-! ## النموذجُ والجواز -/

/-- اللمّةُ الجامعة، على منوال `run_ne_fellOut_aux`. -/
theorem admissible_iff_valid_aux (w : List Cell) :
    (NoAdjacentSukun w ↔ Valid 87 29 true (w.map code)) ∧
      (Admissible w ↔ Valid 87 29 false (w.map code)) := by
  induction w with
  | nil => simp [Admissible, HeadNotSukun, NoAdjacentSukun, Valid]
  | cons a t ih =>
    obtain ⟨ih₁, ih₂⟩ := ih
    have hlt := code_lt a
    cases ha : a.isSukun
    · have h87 : code a < 87 := (code_lt_87_iff a).2 ha
      have hdec : decide (code a < 87) = true := decide_eq_true h87
      have hno : NoAdjacentSukun (a :: t) ↔ NoAdjacentSukun t := by
        cases t with
        | nil => simp [NoAdjacentSukun]
        | cons b t' => simp [NoAdjacentSukun, ha]
      have hv : ∀ o, Valid 87 29 o (code a :: t.map code) ↔ Valid 87 29 true (t.map code) := by
        intro o
        simp only [Valid, hdec]
        constructor
        · exact fun h => h.2.2
        · exact fun h => ⟨hlt, fun h' => absurd h' (Nat.not_le_of_lt h87), h⟩
      refine ⟨?_, ?_⟩
      · rw [List.map_cons, hv, hno]; exact ih₁
      · rw [List.map_cons, hv, ← ih₁]
        simp [Admissible, HeadNotSukun, ha, hno]
    · have h87 : ¬ code a < 87 := fun h => by rw [(code_lt_87_iff a).1 h] at ha; cases ha
      have hdec : decide (code a < 87) = false := decide_eq_false h87
      refine ⟨?_, ?_⟩
      · rw [List.map_cons]
        simp only [Valid, hdec]
        rw [← ih₂]
        cases t with
        | nil => simp [Admissible, HeadNotSukun, NoAdjacentSukun, hlt]
        | cons b t' =>
          simp only [Admissible, HeadNotSukun, NoAdjacentSukun, ha, true_and]
          cases hb : b.isSukun <;> simp_all
      · rw [List.map_cons]
        simp only [Valid, hdec, Admissible, HeadNotSukun, ha]
        constructor
        · intro h; cases h.1
        · intro h; exact absurd (h.2.1 (Nat.le_of_not_lt h87)) (by decide)

/-- **السلسلةُ مقبولةٌ في النموذج ⟺ صورتُها جائزةٌ لا تبدأ بمحجور.** -/
theorem admissible_iff_valid (w : List Cell) : Admissible w ↔ Valid 87 29 false (w.map code) :=
  (admissible_iff_valid_aux w).2

/-- والآلةُ نفسُها: لا تسقط السلسلةُ ⟺ صورتُها جائزة. -/
theorem run_ne_fellOut_iff_valid (w : List Cell) :
    run .awaiting w ≠ .fellOut ↔ Valid 87 29 false (w.map code) :=
  (run_ne_fellOut_iff w).trans (admissible_iff_valid w)

/-! ## التقابلُ على الـ116 -/

/-- ‎U(n)‎: عددُ السلاسل الطولِ `n` التي يقبلها النموذج. -/
def U (n : Nat) : Nat := S 87 29 n false

/-- طيُّ سلسلةٍ من الخانات. -/
def cellFold (w : List Cell) : Nat := fold 87 29 false (w.map code)

/-- فكٌّ إلى خانات. -/
def cellUnfold (n k : Nat) : List Cell := (unfold 87 29 n false k).map decode

theorem cellFold_lt {w : List Cell} (h : Admissible w) : cellFold w < U w.length := by
  have := fold_lt 87 29 _ false ((admissible_iff_valid w).1 h)
  rwa [List.length_map] at this

theorem map_code_injective {w w' : List Cell} (h : w.map code = w'.map code) : w = w' := by
  have := congrArg (List.map decode) h
  simp only [List.map_map] at this
  have hid : decode ∘ code = id := funext decode_code
  rw [hid, List.map_id, List.map_id] at this
  exact this

/-- **متباين:** مقبولتان بطولٍ واحدٍ وطيٍّ واحدٍ هما واحدة. -/
theorem cellFold_injective {w w' : List Cell} (hw : Admissible w) (hw' : Admissible w')
    (hlen : w.length = w'.length) (h : cellFold w = cellFold w') : w = w' :=
  map_code_injective <|
    fold_injective 87 29 ((admissible_iff_valid w).1 hw) ((admissible_iff_valid w').1 hw')
      (by simpa using hlen) h

theorem map_code_decode : ∀ (l : List Nat) (o : Bool), Valid 87 29 o l →
    (l.map decode).map code = l
  | [], _, _ => rfl
  | x :: xs, _, ⟨hx, _, hv⟩ => by
    simp only [List.map_cons, code_decode x hx, map_code_decode xs _ hv]

/-- **شامل:** كلُّ عددٍ دون ‎U(n)‎ طيُّ سلسلةٍ مقبولةٍ بطول `n`. -/
theorem cellFold_surjective {n k : Nat} (hk : k < U n) :
    ∃ w : List Cell, w.length = n ∧ Admissible w ∧ cellFold w = k := by
  obtain ⟨hv, hlen, hfold⟩ := unfold_spec 87 29 n false k hk
  have hround := map_code_decode _ false hv
  refine ⟨cellUnfold n k, ?_, ?_, ?_⟩
  · simp [cellUnfold, hlen]
  · rw [admissible_iff_valid, cellUnfold, hround]; exact hv
  · rw [cellFold, cellUnfold, hround]; exact hfold

/-! ## العدد -/

theorem U_zero : U 0 = 1 := rfl

theorem U_one : U 1 = 87 := rfl

/-- **‎U(n+2) = 87·U(n+1) + 87·29·U(n)‎ لكلّ ‎n‎.** -/
theorem U_succ_succ (n : Nat) : U (n + 2) = 87 * U (n + 1) + 87 * 29 * U n := by
  simp only [U, S]
  omega

/-- أوّلُ الأعداد؛ ويقابلها CI بالعدّ المباشر في البايثون حتى الطول 2. -/
theorem U_values : (List.range 5).map U = [1, 87, 10092, 1097505, 120945051] := by
  decide +kernel

/-- **سلّمُ hamil** (`burhan/THE-PROOF.md`): ‎T(n)‎ على حقل الـ112 بـ‎f = 84، b = 28‎. -/
theorem hamil_ladder :
    (List.range 6).map (fun n => T 84 28 (n + 1)) =
      [112, 11760, 1251264, 132765696, 14095291392, 1496269393920] := by
  decide +kernel

end A116
