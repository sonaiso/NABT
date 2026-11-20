import A116.Ladder

/-!
# مبرهناتُ «مونوغراف a116» التي لم تكن مبرهَنةً في Lean، والتي استُشهِد لها بغير مبرهنتها

* `admissible_map_carriers` (المبرهنة 1): أيُّ دالّةٍ على الحوامل — تبديلٌ أو غيرُه —
  تحفظ الترخيص؛ لأنّ الترخيصَ لا يقرأ إلّا السكون.
* `admissible_prefix` (المبرهنة 2): بادئةُ المرخَّص مرخَّصة. (المونوغرافُ استشهد لها بـ
  `step_depends_only_on_sukun`، وليست هي.)
* `admissible_append` (لبُّ المبرهنة 8): وصلُ مرخَّصٍ غيرِ فارغٍ بسلسلة ‎b‎ مرخَّصٌ إذا وفقط
  إذا: إن انتهى الأوّلُ بمتحرّكٍ فلا ساكنان متجاوران في ‎b‎، وإن انتهى بساكنٍ فـ‎b‎
  نفسُها مرخَّصة (لا تبدأ بساكن). فالوصلةُ لا تُفحَص إلّا عند موضعها.
* `U_by_patterns_upto_6` (المبرهنة 6 حتى الطول 6): ‎U(n) = Σ 87^{#M}·29^{#S}‎ على الأنماط
  الجائزة.
* `licensed_upto_4` (المبرهنة 11): ‎U(1)+…+U(4) = 122,052,735‎.
* `burnside_3` و`burnside_4` (المبرهنة 10، حسابُها): ‎(29³+2·29)/3 = 8,149‎ و
  ‎(29⁴+29²+2·29)/4 = 177,045‎، وقسمةُ المدارات بأطوالها.
-/

namespace A116.Junction

open A116 A116.Ladder A116.State

def mapCarriers (π : Fin carrierCount → Fin carrierCount) (w : List Cell) : List Cell :=
  w.map fun c => ⟨π c.carrier, c.haraka⟩

theorem pat_mapCarriers (π : Fin carrierCount → Fin carrierCount) (w : List Cell) :
    pat (mapCarriers π w) = pat w := by
  simp [pat, mapCarriers, Function.comp_def, Cell.isSukun]

theorem admissible_map_carriers (π : Fin carrierCount → Fin carrierCount) (w : List Cell) :
    Admissible (mapCarriers π w) ↔ Admissible w := by
  rw [← run_ne_fellOut_iff, ← run_ne_fellOut_iff,
    run_depends_only_on_pattern awaiting _ w (pat_mapCarriers π w)]

theorem run_append (q : State) (a b : List Cell) : run q (a ++ b) = run (run q a) b := by
  simp [run, List.foldl_append]

theorem admissible_prefix {a b : List Cell} (h : Admissible (a ++ b)) : Admissible a := by
  rw [← run_ne_fellOut_iff] at h ⊢
  intro ha
  rw [run_append, ha, run_fellOut] at h
  exact h rfl

/-- بعد سلسلةٍ لم تسقط وآخرُها ‎c‎: الحالةُ تُعيِّنها ‎c‎ وحدَها. -/
theorem run_snoc_of_ne (q : State) (w : List Cell) (c : Cell)
    (h : run q (w ++ [c]) ≠ fellOut) :
    run q (w ++ [c]) = if c.isSukun then awaiting else afterSeed := by
  rw [run_append] at h ⊢
  simp only [run_cons, run_nil] at h ⊢
  generalize run q w = x at h ⊢
  cases x <;> cases hs : c.isSukun <;> simp_all [step]

theorem admissible_append (a : List Cell) (c : Cell) (b : List Cell)
    (ha : Admissible (a ++ [c])) :
    Admissible ((a ++ [c]) ++ b) ↔
      (if c.isSukun then Admissible b else NoAdjacentSukun b) := by
  rw [← run_ne_fellOut_iff] at ha ⊢
  rw [run_append, run_snoc_of_ne awaiting a c ha]
  cases c.isSukun
  · simp only [Bool.false_eq_true, ↓reduceIte]; exact (run_ne_fellOut_aux b).1
  · simp only [↓reduceIte]; exact run_ne_fellOut_iff b

/-! ## الأعداد -/

def weight : List Bool → Nat
  | [] => 1
  | true :: t => 87 * weight t
  | false :: t => 29 * weight t

theorem U_by_patterns_upto_6 :
    ∀ n ∈ List.range 7,
      (((allPats n).filter admissibleB).map weight).sum = U n := by
  decide +kernel

theorem licensed_upto_4 : U 1 + U 2 + U 3 + U 4 = 122052735 := by decide

theorem burnside_3 : (29 ^ 3 + 2 * 29) / 3 = 8149 ∧ 29 + 3 * 8120 = 29 ^ 3 := by decide

theorem burnside_4 :
    (29 ^ 4 + 29 ^ 2 + 2 * 29) / 4 = 177045 ∧ 29 + 2 * 406 + 4 * 176610 = 29 ^ 4 ∧
      29 + 406 + 176610 = 177045 := by decide

end A116.Junction
