import A116.Ternary

/-!
# الدرجات: الترخيصُ الجبريُّ المتدرّج بعدد المقاطع — كلُّ درجةٍ من التي قبلها ومقطع

الدرجةُ k متتالياتُ k مقطعًا من مقاطع `Stages` الستّة (CV، CVV، CVC، CVVC، CVCC، CVVCC)، بقوانين الحدّ
الثلاثة:

* **الابتداء:** لا قطعةَ صادرة — المتتاليةُ تبدأ بمتحرّك (`parse … = some (.none, …)`)؛ فهو شرطُ الدرجات
  كلِّها لا جدولٌ ثالث.
* **الوصل** (`contGrade k`): مقاطعُها كلُّها من الأربعة الداخليّة (`inner`: CV، CVV، CVC، CVVC).
* **الوقف** (`pauseGrade k`): درجةُ الوصل k−1 ثمّ مقطعٌ طرفيٌّ من الستّة (`final`) — فـCVCC وCVVCC
  لا تقع إلّا آخرًا.

## المبرهنات (لكلّ k)

* `cont_succ`، `pause_succ` — **قانونُ التدرّج:** عنصرُ الدرجة k+1 عنصرٌ من الدرجة k ومعه مقطع،
  وبالعكس؛ والوقفُ في الدرجة k+1 وصلُ الدرجة k ومقطعٌ طرفيّ. لا عنصرَ في درجةٍ لم يمرّ بالتي قبلها.
* `mem_cont_iff`، `mem_pause_iff` — **التمام:** المتتاليةُ في درجة الوصل k إذا وفقط إذا كان طولُها k
  ومرخَّصةً وصلًا (`Ternary.continueB` على وصل مقاطعها)؛ وفي درجة الوقف k+1 إذا وفقط إذا كان طولُها
  k+1 ومرخَّصةً وقفًا (`Ternary.pauseB`). فالجدولُ هو الترخيصُ نفسُه، لا قائمةٌ بجانبه.
* `cont_nodup`، `pause_nodup` — لا تكرار: لكلّ عنصرٍ موضعٌ واحد، فرقمُه في جدوله (n) واحد.
* `cont_length`، `pause_length` — **العددُ لكلّ k:** ‎|وصل k| = 4ᵏ‎، ‎|وقف (k+1)| = 6·4ᵏ‎.
* `grade_table` — الأعدادُ بالحساب للدرجات 1..5 (مبرهَنٌ على الأطوال المذكورة).

## ما ليس هنا — باسمه

هذا على **أصناف المقاطع** (K)، لا على الخانات: عددُ الخانات في كلّ صنفٍ وقيدُ الحدّ (`Hadd`: CVVC لا
تُرخَّص وصلًا إلّا قبل مثلٍ مدغم) وبوّابةُ الاستنفاد (لا تُرخَّص الدرجةُ k+1 إلّا بعد تمام وظائف الدرجة k)
خطواتٌ تالية.
-/

namespace A116.Grade

open A116.Stages A116.Ternary

/-- مقاطعُ الوصل: ما يقع داخل الكلمة. -/
def inner : List Syl := [.CV, .CVV, .CVC, .CVVC]

/-- مقاطعُ الطرف وقفًا: الستّة. -/
def final : List Syl := [.CV, .CVV, .CVC, .CVVC, .CVCC, .CVVCC]

/-- درجةُ الوصل k. -/
def contGrade : Nat → List (List Syl)
  | 0 => [[]]
  | k + 1 => (contGrade k).flatMap fun ss => inner.map fun s => ss ++ [s]

/-- درجةُ الوقف k (‎k ≥ 1‎): وصلُ k−1 ثمّ مقطعٌ طرفيّ. -/
def pauseGrade : Nat → List (List Syl)
  | 0 => []
  | k + 1 => (contGrade k).flatMap fun ss => final.map fun s => ss ++ [s]

/-- مقاطعُ الوصل هي ما ليس طرفيًّا وقفًا. -/
theorem mem_inner (s : Syl) : s ∈ inner ↔ pauseOnly s = false := by cases s <;> decide

/-- كلُّ مقطعٍ من الستّة يقع طرفًا وقفًا. -/
theorem mem_final (s : Syl) : s ∈ final := by cases s <;> decide

/-! ## قانونُ التدرّج -/

/-- **قانونُ التدرّج (الوصل):** عنصرُ الدرجة k+1 عنصرٌ من الدرجة k ومعه مقطعٌ داخليّ، وبالعكس. -/
theorem cont_succ (k : Nat) (ss : List Syl) :
    ss ∈ contGrade (k + 1) ↔ ∃ t ∈ contGrade k, ∃ s ∈ inner, ss = t ++ [s] := by
  simp only [contGrade, List.mem_flatMap, List.mem_map]
  constructor
  · rintro ⟨t, ht, s, hs, rfl⟩; exact ⟨t, ht, s, hs, rfl⟩
  · rintro ⟨t, ht, s, hs, rfl⟩; exact ⟨t, ht, s, hs, rfl⟩

/-- **قانونُ التدرّج (الوقف):** الوقفُ في الدرجة k+1 وصلُ الدرجة k ومعه مقطعٌ طرفيّ، وبالعكس. -/
theorem pause_succ (k : Nat) (ss : List Syl) :
    ss ∈ pauseGrade (k + 1) ↔ ∃ t ∈ contGrade k, ∃ s ∈ final, ss = t ++ [s] := by
  simp only [pauseGrade, List.mem_flatMap, List.mem_map]
  constructor
  · rintro ⟨t, ht, s, hs, rfl⟩; exact ⟨t, ht, s, hs, rfl⟩
  · rintro ⟨t, ht, s, hs, rfl⟩; exact ⟨t, ht, s, hs, rfl⟩

/-! ## التمام: الجدولُ هو الترخيصُ نفسُه -/

/-- كلُّ متتاليةٍ غيرِ فارغة متتاليةٌ ومقطعٌ أخير. -/
theorem exists_concat : ∀ (ss : List Syl), ss ≠ [] → ∃ t s, ss = t ++ [s]
  | [], h => absurd rfl h
  | [s], _ => ⟨[], s, rfl⟩
  | a :: b :: r, _ => by
    obtain ⟨t, s, h⟩ := exists_concat (b :: r) (by simp)
    exact ⟨a :: t, s, by simp [h]⟩

/-- درجةُ الوصل k: الطولُ k وكلُّ مقطعٍ غيرُ طرفيّ. -/
theorem mem_cont_iff_all (k : Nat) (ss : List Syl) :
    ss ∈ contGrade k ↔ ss.length = k ∧ ∀ s ∈ ss, pauseOnly s = false := by
  induction k generalizing ss with
  | zero =>
    simp only [contGrade, List.mem_singleton]
    constructor
    · rintro rfl; simp
    · rintro ⟨h, _⟩; exact List.eq_nil_of_length_eq_zero h
  | succ k ih =>
    rw [cont_succ]
    constructor
    · rintro ⟨t, ht, s, hs, rfl⟩
      obtain ⟨hl, ha⟩ := (ih t).1 ht
      refine ⟨by simp [hl], fun x hx => ?_⟩
      rcases List.mem_append.1 hx with hx | hx
      · exact ha x hx
      · rw [List.mem_singleton.1 hx]; exact (mem_inner s).1 hs
    · rintro ⟨hl, ha⟩
      obtain ⟨t, s, rfl⟩ := exists_concat ss (by rintro rfl; simp at hl)
      refine ⟨t, (ih t).2 ⟨by simpa using hl, fun x hx => ha x (by simp [hx])⟩, s,
        (mem_inner s).2 (ha s (by simp)), rfl⟩

/-- الوصلُ على وصل المقاطع: لا مقطعَ طرفيّ. -/
theorem continueB_flat (ss : List Syl) :
    continueB (flat .none ss) = ss.all fun s => !(pauseOnly s) := by
  unfold continueB; rw [parse_flat]

/-- الوقفُ على وصل المقاطع: لا مقطعَ طرفيّ قبل الأخير. -/
theorem pauseB_flat (ss : List Syl) :
    pauseB (flat .none ss) = ss.dropLast.all fun s => !(pauseOnly s) := by
  unfold pauseB; rw [parse_flat]

/-- **التمام (الوصل):** في درجة الوصل k ⇔ طولُها k ومرخَّصةٌ وصلًا. -/
theorem mem_cont_iff (k : Nat) (ss : List Syl) :
    ss ∈ contGrade k ↔ ss.length = k ∧ continueB (flat .none ss) = true := by
  rw [mem_cont_iff_all, continueB_flat]
  simp

/-- **التمام (الوقف):** في درجة الوقف k+1 ⇔ طولُها k+1 ومرخَّصةٌ وقفًا. -/
theorem mem_pause_iff (k : Nat) (ss : List Syl) :
    ss ∈ pauseGrade (k + 1) ↔ ss.length = k + 1 ∧ pauseB (flat .none ss) = true := by
  rw [pause_succ, pauseB_flat]
  constructor
  · rintro ⟨t, ht, s, _, rfl⟩
    obtain ⟨hl, ha⟩ := (mem_cont_iff_all k t).1 ht
    refine ⟨by simp [hl], ?_⟩
    simpa [List.dropLast_concat] using ha
  · rintro ⟨hl, ha⟩
    obtain ⟨t, s, rfl⟩ := exists_concat ss (by rintro rfl; simp at hl)
    simp at ha
    exact ⟨t, (mem_cont_iff_all k t).2 ⟨by simpa using hl, ha⟩, s, mem_final s, rfl⟩

/-! ## لا تكرار، والعددُ لكلّ k -/

/-- إلحاقُ مقطعٍ تباين: يُستردّ منه الأصلُ والمقطع. -/
theorem append_single_inj {t t' : List Syl} {s s' : Syl} (h : t ++ [s] = t' ++ [s']) :
    t = t' ∧ s = s' := by
  have := List.append_inj' h rfl
  exact ⟨this.1, by simpa using this.2⟩

/-- صورةُ قائمةٍ بلا تكرار بدالّةٍ متباينة بلا تكرار. -/
theorem nodup_map_inj {α β : Type} (f : α → β) (hf : ∀ a b, f a = f b → a = b) :
    ∀ l : List α, l.Nodup → (l.map f).Nodup
  | [], _ => by simp
  | a :: l, h => by
    rw [List.nodup_cons] at h
    rw [List.map_cons, List.nodup_cons]
    refine ⟨fun hm => ?_, nodup_map_inj f hf l h.2⟩
    obtain ⟨b, hb, he⟩ := List.mem_map.1 hm
    exact h.1 (hf b a he ▸ hb)

/-- خطوةُ الدرجة تحفظ عدمَ التكرار. -/
theorem nodup_step (L : List (List Syl)) (S : List Syl) (hL : L.Nodup) (hS : S.Nodup) :
    (L.flatMap fun ss => S.map fun s => ss ++ [s]).Nodup := by
  induction L with
  | nil => simp
  | cons t L ih =>
    simp only [List.flatMap_cons]
    rw [List.nodup_append]
    refine ⟨nodup_map_inj (fun s => t ++ [s]) (fun a b h => (append_single_inj h).2) S hS,
      ih (List.nodup_cons.1 hL).2, ?_⟩
    intro x hx y hy hxy
    subst hxy
    obtain ⟨s, _, rfl⟩ := List.mem_map.1 hx
    obtain ⟨u, hu, s', _, h⟩ : ∃ u ∈ L, ∃ s' ∈ S, u ++ [s'] = t ++ [s] := by
      simpa [List.mem_flatMap] using hy
    exact (List.nodup_cons.1 hL).1 ((append_single_inj h).1 ▸ hu)

/-- **لا تكرار (الوصل):** لكلّ عنصرٍ موضعٌ واحد في جدول درجته. -/
theorem cont_nodup : ∀ k, (contGrade k).Nodup
  | 0 => by simp [contGrade]
  | k + 1 => nodup_step _ _ (cont_nodup k) (by decide)

/-- **لا تكرار (الوقف):** لكلّ عنصرٍ موضعٌ واحد في جدول درجته. -/
theorem pause_nodup : ∀ k, (pauseGrade k).Nodup
  | 0 => by simp [pauseGrade]
  | k + 1 => nodup_step _ _ (cont_nodup k) (by decide)

/-- عددُ خطوة الدرجة: عددُ ما قبلها في عدد المقاطع. -/
theorem length_step (L : List (List Syl)) (S : List Syl) :
    (L.flatMap fun ss => S.map fun s => ss ++ [s]).length = L.length * S.length := by
  induction L with
  | nil => simp
  | cons t L ih => simp [List.flatMap_cons, ih, Nat.succ_mul, Nat.add_comm]

/-- **العددُ لكلّ k (الوصل):** ‎4ᵏ‎. -/
theorem cont_length : ∀ k, (contGrade k).length = 4 ^ k
  | 0 => rfl
  | k + 1 => by
    rw [contGrade, length_step, cont_length k]
    simp [inner, Nat.pow_succ]

/-- **العددُ لكلّ k (الوقف):** ‎|وقف (k+1)| = 6·4ᵏ‎. -/
theorem pause_length (k : Nat) : (pauseGrade (k + 1)).length = 6 * 4 ^ k := by
  rw [pauseGrade, length_step, cont_length k]
  simp [final, Nat.mul_comm]

/-- الأعدادُ بالحساب للدرجات 1..5: (k، وصل، وقف). -/
theorem grade_table :
    (List.range 5).map (fun i => (i + 1, (contGrade (i + 1)).length, (pauseGrade (i + 1)).length)) =
      [(1, 4, 6), (2, 16, 24), (3, 64, 96), (4, 256, 384), (5, 1024, 1536)] := by
  simp [List.range, List.range.loop, cont_length, pause_length]

/-- الدرجةُ الأولى بعينها: المقاطعُ الستّة وقفًا، والأربعةُ الداخليّة وصلًا. -/
theorem grade_one :
    contGrade 1 = [[.CV], [.CVV], [.CVC], [.CVVC]] ∧
    pauseGrade 1 = [[.CV], [.CVV], [.CVC], [.CVVC], [.CVCC], [.CVVCC]] := by
  decide

end A116.Grade
