import A116.Junction

/-!
# البديلُ لما لم يغطّه المونوغراف: المبرهنة 6 لكلّ n، وترخيصُ الوقف ومشغّلُه

## المبرهنة 6 لكلّ طول

`pats n o` تولّد الأنماطَ الجائزةَ وحدَها (و`o` = أكان السابقُ متحرّكًا فيجوز الساكن):
* `mem_pats`: ‎l ∈ pats n false ⇔ |l| = n ∧ admissibleB l‎ — توليدٌ جامعٌ مانع.
* `U_by_patterns`: ‎U(n) = Σ_{l ∈ pats n false} 87^{#M}·29^{#S}‎ **لكلّ n**.

## الوقف

النموذجُ المعلن (`Admissible`) نموذجُ وصل: يمنع ساكنين متجاورين في كلّ موضع. والوقفُ
يُسكِّن الآخر، فيجتمع ساكنان في الطرف (بَحْرٌ ← `بَ حْ رْ`، حِسَابٍ ← `حِ سَ اْ بْ`)؛
فيرفض النموذجُ صورَ الوقف الصحيحة. والبديل:

* `PauseAdmissible w`: ‎w = v ++ [c]‎ و‎c‎ ساكنة و‎v‎ مرخَّصةٌ غيرُ فارغة — فالطرفُ وحدَه
  مُعفًى من منع التجاور.
* `pause`: مشغّلُ الوقف ‎W‎ على الخانات: يُسكِّن الأخيرة.
* `pause_admissible`: وقفُ كلِّ مرخَّصٍ طولُه ≥ 2 مرخَّصٌ وقفًا.
* `pause_strictly_extends`: «بَحْرْ» مرخَّصةٌ وقفًا وغيرُ مرخَّصةٍ وصلًا.
-/

namespace A116.Pause

open A116 A116.Ladder A116.Junction A116.State

/-! ## المبرهنة 6 لكلّ n -/

def pats : Nat → Bool → List (List Bool)
  | 0, _ => [[]]
  | n + 1, o => (pats n true).map (true :: ·) ++ (if o then (pats n false).map (false :: ·) else [])

def okB : Bool → List Bool → Bool
  | _, [] => true
  | _, true :: t => okB true t
  | o, false :: t => o && okB false t

theorem mem_pats : ∀ (n : Nat) (o : Bool) (l : List Bool),
    l ∈ pats n o ↔ l.length = n ∧ okB o l = true
  | 0, o, l => by cases l <;> simp [pats, okB]
  | n + 1, o, [] => by simp [pats]
  | n + 1, o, b :: t => by
    cases b <;> cases o <;> simp [pats, okB, mem_pats n]

private theorem noSS_eq_okB : ∀ (a : Bool) (t : List Bool),
    admissibleB.noSS (a :: t) = okB a t
  | _, [] => by simp [admissibleB.noSS, okB]
  | a, true :: t => by
    simp only [admissibleB.noSS, okB, Bool.or_true, Bool.true_and]; exact noSS_eq_okB true t
  | a, false :: t => by
    simp only [admissibleB.noSS, okB, Bool.or_false]; rw [noSS_eq_okB false t]

theorem admissibleB_eq_okB (l : List Bool) : admissibleB l = okB false l := by
  cases l with
  | nil => rfl
  | cons b t =>
    cases b
    · simp [admissibleB, okB]
    · simp [admissibleB, okB, noSS_eq_okB]

theorem mem_pats_iff (n : Nat) (l : List Bool) :
    l ∈ pats n false ↔ l.length = n ∧ admissibleB l = true := by
  rw [mem_pats, admissibleB_eq_okB]

private theorem sum_true (L : List (List Bool)) :
    ((L.map (true :: ·)).map weight).sum = 87 * (L.map weight).sum := by
  induction L with
  | nil => rfl
  | cons x xs ih => simp only [List.map_cons, List.sum_cons, weight] at ih ⊢; rw [ih, Nat.mul_add]

private theorem sum_false (L : List (List Bool)) :
    ((L.map (false :: ·)).map weight).sum = 29 * (L.map weight).sum := by
  induction L with
  | nil => rfl
  | cons x xs ih => simp only [List.map_cons, List.sum_cons, weight] at ih ⊢; rw [ih, Nat.mul_add]

theorem weights_eq_S : ∀ (n : Nat) (o : Bool),
    ((pats n o).map weight).sum = Fold.S 87 29 n o
  | 0, o => by cases o <;> rfl
  | n + 1, true => by
    simp only [pats, ↓reduceIte, List.map_append, List.sum_append, sum_true, sum_false,
      weights_eq_S n, Fold.S]
  | n + 1, false => by
    simp only [pats, Bool.false_eq_true, ↓reduceIte, List.append_nil, sum_true,
      weights_eq_S n, Fold.S]

theorem U_by_patterns (n : Nat) : ((pats n false).map weight).sum = U n :=
  weights_eq_S n false

/-! ## الوقف -/

def PauseAdmissible (w : List Cell) : Prop :=
  ∃ v c, w = v ++ [c] ∧ c.isSukun = true ∧ v ≠ [] ∧ Admissible v

/-- مشغّلُ الوقف ‎W‎: الخانةُ الأخيرةُ تُسكَّن، وما قبلها كما هو. -/
def pause : List Cell → List Cell
  | [] => []
  | [c] => [⟨c.carrier, .sukun⟩]
  | c :: d :: t => c :: pause (d :: t)

theorem pause_snoc : ∀ (v : List Cell) (c : Cell),
    pause (v ++ [c]) = v ++ [⟨c.carrier, .sukun⟩]
  | [], c => rfl
  | [a], c => rfl
  | a :: b :: t, c => by
    show pause (a :: (b :: t ++ [c])) = a :: (b :: t ++ [⟨c.carrier, .sukun⟩])
    have := pause_snoc (b :: t) c
    simp only [List.cons_append] at this ⊢
    rw [← this]; rfl

theorem pause_admissible (v : List Cell) (c : Cell) (hv : v ≠ [])
    (h : Admissible (v ++ [c])) : PauseAdmissible (pause (v ++ [c])) :=
  ⟨v, ⟨c.carrier, .sukun⟩, pause_snoc v c, rfl, hv, admissible_prefix h⟩

def bahr : List Cell :=
  [atom 'ب' .fatha, atom 'ح' .sukun, atom 'ر' .sukun]

theorem pause_strictly_extends : PauseAdmissible bahr ∧ ¬ Admissible bahr := by
  refine ⟨⟨[atom 'ب' .fatha, atom 'ح' .sukun], atom 'ر' .sukun, rfl, rfl, by simp, ?_⟩, ?_⟩
  · rw [← run_ne_fellOut_iff]; decide
  · rw [← run_ne_fellOut_iff]; decide

end A116.Pause
