import A116.Pause
import A116.Recovery

/-!
# الإعلالُ والإبدال — SLGE لحروف العلّة والحروف المبدَلة

الإعلالُ والإبدالُ **تعديلاتٌ موضعيّةٌ على الخانات**: الصورةُ الظاهرة (قَالَ) = الأصلُ (قَوَلَ) بعد
تعديلٍ مسمًّى في موضعٍ معلوم، وسجلُّ التعديل يردّ الأصلَ بعينه. فلكلّ قاعدةٍ هنا مبرهنتان:
**الردّ** (مثولٌ لـ`Recovery.edit_roundtrip`) و**الإغلاق** (الصورةُ مرخَّصةٌ إذا كان الأصلُ أو
جوارُه مرخَّصًا) — وفي قاعدةٍ واحدة **الإلزام**: الأصلُ نفسُه غيرُ مرخَّصٍ فالتعديلُ واجب.

## الأدوات العامّة (على ‎δ*‎ في `Model`)

* `admissible_replace_carrier`: إبدالُ حاملٍ بحاملٍ مع بقاء الحالة لا يغيّر الترخيص (نمطُ السكون واحد).
* `vowelled_to_sukun_between_vowelled`: قلبُ متحرّكٍ ساكنًا بين متحرّكين يحفظ الترخيص.
* `swap_sukun_vowel`: نقلُ الحركة من الثاني إلى الأوّل (ساكنٌ ثمّ متحرّك ← متحرّكٌ ثمّ ساكن) يحفظه
  إن سبقه متحرّكٌ (مرخَّصٌ قبله) وتلاه متحرّك.
* `delete_sukun_after_vowelled`: حذفُ ساكنٍ بعد متحرّك يحفظه.
* `two_sukun_not_admissible`: ساكنان متجاوران = لا ترخيص.

## القواعد المودَعة

| # | القاعدة | الأصل ← الصورة | الأداة |
|---|---|---|---|
| 1 | قلبُ عين الأجوف ألفًا | قَوَلَ ← قَالَ | قلبُ متحرّكٍ ساكنًا |
| 2 | حذفُ عين الأجوف لالتقاء الساكنين | قَالْتُ ← قُلْتُ | **إلزام**: الأصلُ غيرُ مرخَّص |
| 3 | نقلُ حركة العين إلى الساكن قبلها | يَقْوُلُ ← يَقُولُ | نقل |
| 4 | قلبُ لام الناقص ألفًا | دَعَوَ ← دَعَا | قلبُ متحرّكٍ ساكنًا (في الآخر) |
| 5 | حذفُ لام الناقص قبل واو الجماعة | دَعَوُوْا ← دَعَوْا | حذفُ متحرّكٍ قبل ساكن مع نقل |
| 6 | حذفُ واو المثال في المضارع | يَوْعِدُ ← يَعِدُ | حذفُ ساكنٍ بعد متحرّك |
| 7 | الهمزةُ الساكنةُ بعد همزةٍ مدًّا | ءَءْمَنَ ← آمَنَ | إبدالُ حامل |
| 8 | تاءُ الافتعال طاءً بعد الإطباق | اصْتَبَرَ ← اصْطَبَرَ | إبدالُ حامل |
| 9 | تاءُ الافتعال دالًا بعد د/ذ/ز | ازْتَادَ ← ازْدَادَ | إبدالُ حامل |
| 10 | فاءُ الافتعال الواويّة تاءً | اوْتَصَلَ ← اتْتَصَلَ | إبدالُ حامل (ثمّ إدغامٌ رسميّ) |
| 11 | الواوُ الساكنة بعد كسرة ياءً | مِوْزَان ← مِيزَان | إبدالُ حامل |
| 12 | الياءُ الساكنة بعد ضمّة واوًا | مُيْقِن ← مُوقِن | إبدالُ حامل |

ولا يُبرهَن هنا أنّ `gate/mabni_verbs.py` يطبّق هذه القواعد بعينها (ذلك مقيسٌ على MASAQ)، ولا أنّ
شروطَ انطباقها (أيُّ جذرٍ أجوف، أيُّ ياءٍ أصليّة) صحيحةٌ لغويًّا: الشرطُ معلَن، والأثرُ مبرهَن.
-/

namespace A116.Ilal

open A116 A116.Junction A116.Ladder A116.Recovery A116.State

/-! ## الأدوات العامّة -/

theorem admissible_of_pat_eq {w w' : List Cell} (h : pat w = pat w') :
    Admissible w ↔ Admissible w' := by
  rw [← run_ne_fellOut_iff, ← run_ne_fellOut_iff, run_depends_only_on_pattern awaiting w w' h]

/-- إبدالُ حاملٍ مع بقاء الحالة: الترخيصُ واحد. -/
theorem admissible_replace_carrier (a b : List Cell) (c : Cell) (k : Fin carrierCount) :
    Admissible (a ++ [⟨k, c.haraka⟩] ++ b) ↔ Admissible (a ++ [c] ++ b) :=
  admissible_of_pat_eq (by simp [pat, Cell.isSukun])

theorem step_vowelled (q : State) (hq : q ≠ fellOut) (c : Cell) (hc : c.isSukun = false) :
    step q c = afterSeed := by
  cases q with
  | fellOut => exact absurd rfl hq
  | awaiting => simp [step, hc]
  | afterSeed => simp [step, hc]

theorem step_sukun_afterSeed (c : Cell) (hc : c.isSukun = true) : step afterSeed c = awaiting := by
  simp [step, hc]

theorem step_sukun_awaiting (c : Cell) (hc : c.isSukun = true) : step awaiting c = fellOut := by
  simp [step, hc]

theorem run3 (q : State) (x y z : Cell) : run q [x, y, z] = step (step (step q x) y) z := rfl
theorem run2 (q : State) (x z : Cell) : run q [x, z] = step (step q x) z := rfl

theorem run_three (q : State) (hq : q ≠ fellOut) (x y z : Cell)
    (hx : x.isSukun = false) (hz : z.isSukun = false) :
    run q [x, y, z] = afterSeed := by
  rw [run3, step_vowelled q hq x hx]
  cases hy : y.isSukun
  · rw [step_vowelled afterSeed (by decide) y hy, step_vowelled afterSeed (by decide) z hz]
  · rw [step_sukun_afterSeed y hy, step_vowelled awaiting (by decide) z hz]

/-- قلبُ متحرّكٍ ساكنًا بين متحرّكين (قَوَلَ ← قَالَ) يحفظ الترخيص. -/
theorem vowelled_to_sukun_between_vowelled (a b : List Cell) (x y z : Cell) (k : Fin carrierCount)
    (hx : x.isSukun = false) (hz : z.isSukun = false) :
    Admissible (a ++ [x, y, z] ++ b) ↔ Admissible (a ++ [x, ⟨k, .sukun⟩, z] ++ b) := by
  rw [← run_ne_fellOut_iff, ← run_ne_fellOut_iff, run_append, run_append, run_append, run_append]
  by_cases hq : run awaiting a = fellOut
  · rw [hq, run3, run3]; simp [step]
  · rw [run_three _ hq x y z hx hz, run_three _ hq x _ z hx hz]

/-- نقلُ الحركة (يَقْوُلُ ← يَقُولُ): ساكنٌ ثمّ متحرّكٌ ثمّ متحرّك ← متحرّكٌ ثمّ ساكنٌ ثمّ متحرّك. -/
theorem swap_sukun_vowel (a b : List Cell) (x y z : Cell)
    (ha : run awaiting a = afterSeed)
    (hx : x.isSukun = true) (hy : y.isSukun = false) (hz : z.isSukun = false) :
    Admissible (a ++ [x, y, z] ++ b) ↔
      Admissible (a ++ [⟨x.carrier, y.haraka⟩, ⟨y.carrier, .sukun⟩, z] ++ b) := by
  rw [← run_ne_fellOut_iff, ← run_ne_fellOut_iff, run_append, run_append, run_append, run_append,
    ha]
  have hx1 : (⟨x.carrier, y.haraka⟩ : Cell).isSukun = false := hy
  have hy1 : (⟨y.carrier, .sukun⟩ : Cell).isSukun = true := rfl
  have h1 : run afterSeed [x, y, z] = afterSeed := by
    rw [run3, step_sukun_afterSeed x hx, step_vowelled awaiting (by decide) y hy,
      step_vowelled afterSeed (by decide) z hz]
  have h2 : run afterSeed [⟨x.carrier, y.haraka⟩, ⟨y.carrier, .sukun⟩, z] = afterSeed := by
    rw [run3, step_vowelled afterSeed (by decide) _ hx1, step_sukun_afterSeed _ hy1,
      step_vowelled awaiting (by decide) z hz]
  rw [h1, h2]

/-- حذفُ ساكنٍ بعد متحرّك (يَوْعِدُ ← يَعِدُ) يحفظ الترخيص إن تلاه متحرّك. -/
theorem delete_sukun_after_vowelled (a b : List Cell) (x s z : Cell)
    (hx : x.isSukun = false) (hz : z.isSukun = false) :
    Admissible (a ++ [x, s, z] ++ b) ↔ Admissible (a ++ [x, z] ++ b) := by
  rw [← run_ne_fellOut_iff, ← run_ne_fellOut_iff, run_append, run_append, run_append, run_append]
  by_cases hq : run awaiting a = fellOut
  · rw [hq, run3, run2]; simp [step]
  · rw [run_three _ hq x s z hx hz, run2, step_vowelled _ hq x hx,
      step_vowelled afterSeed (by decide) z hz]

/-- ساكنان متجاوران: لا ترخيص. -/
theorem two_sukun_not_admissible (a b : List Cell) (s t : Cell)
    (hs : s.isSukun = true) (ht : t.isSukun = true) : ¬ Admissible (a ++ [s, t] ++ b) := by
  rw [← run_ne_fellOut_iff, run_append, run_append, run2]
  cases run awaiting a with
  | fellOut => simp [step]
  | awaiting => rw [step_sukun_awaiting s hs]; simp [step]
  | afterSeed => rw [step_sukun_afterSeed s hs, step_sukun_awaiting t ht]; simp

/-! ## القواعد: الردُّ بالسجلّ (مثولاتُ `edit_roundtrip`) -/

/-- 1. قلبُ العين ألفًا: الأصلُ ‎(و/ي، فتحة)‎ يُردّ من السجلّ. -/
theorem qalb_ayn_restore (l r : List Cell) (ayn : Cell) :
    restoreEdit (l ++ ([atom 'ا' .sukun] ++ r)) ⟨l.length, 1, [ayn]⟩ = l ++ [ayn] ++ r :=
  edit_roundtrip l _ _ r

/-- 2. حذفُ العين لالتقاء الساكنين، مع نقل حركة الفاء: يُردّ الأصل. -/
theorem hadhf_ayn_restore (l r : List Cell) (fa fa' ayn : Cell) :
    restoreEdit (l ++ ([fa'] ++ r)) ⟨l.length, 1, [fa, ayn]⟩ = l ++ [fa, ayn] ++ r :=
  edit_roundtrip l _ _ r

/-- 2′. **الإلزام**: الأصلُ (عينٌ ساكنةٌ ثمّ ساكن) غيرُ مرخَّصٍ أصلًا، فالحذفُ واجب. -/
theorem hadhf_ayn_forced (l r : List Cell) (fa ayn t : Cell)
    (hayn : ayn.isSukun = true) (ht : t.isSukun = true) :
    ¬ Admissible (l ++ [fa] ++ [ayn, t] ++ r) := by
  have := two_sukun_not_admissible (l ++ [fa]) r ayn t hayn ht
  simpa [List.append_assoc] using this

/-- 3. النقل: يُردّ الأصل. -/
theorem naql_restore (l r : List Cell) (x y : Cell) :
    restoreEdit (l ++ ([⟨x.carrier, y.haraka⟩, ⟨y.carrier, .sukun⟩] ++ r)) ⟨l.length, 2, [x, y]⟩ =
      l ++ [x, y] ++ r :=
  edit_roundtrip l _ _ r

/-- 4. قلبُ لام الناقص ألفًا: يُردّ الأصل. -/
theorem qalb_lam_restore (l : List Cell) (lam : Cell) :
    restoreEdit (l ++ ([atom 'ا' .sukun] ++ [])) ⟨l.length, 1, [lam]⟩ = l ++ [lam] ++ [] :=
  edit_roundtrip l _ _ []

/-- 5. حذفُ لام الناقص قبل واو الجماعة (دَعَوُوْا ← دَعَوْا): يُردّ الأصل. -/
theorem hadhf_lam_restore (l r : List Cell) (lam waw : Cell) :
    restoreEdit (l ++ ([waw] ++ r)) ⟨l.length, 1, [lam, waw]⟩ = l ++ [lam, waw] ++ r :=
  edit_roundtrip l _ _ r

/-- 6. حذفُ واو المثال: يُردّ الأصل. -/
theorem hadhf_waw_restore (l r : List Cell) (waw : Cell) :
    restoreEdit (l ++ ([] ++ r)) ⟨l.length, 0, [waw]⟩ = l ++ [waw] ++ r :=
  edit_roundtrip l _ _ r

/-- 7–12. الإبدالُ (حاملٌ بحامل): يُردّ الأصل. -/
theorem ibdal_restore (l r : List Cell) (c : Cell) (k : Fin carrierCount) :
    restoreEdit (l ++ ([⟨k, c.haraka⟩] ++ r)) ⟨l.length, 1, [c]⟩ = l ++ [c] ++ r :=
  edit_roundtrip l _ _ r

/-! ## الشواهد المسمّاة بالحساب -/

/-- قَوَلَ ← قَالَ: الأصلُ والصورةُ كلاهما مرخَّص (القلبُ حافظ). -/
theorem qala_witness :
    Admissible [atom 'ق' .fatha, atom 'و' .fatha, atom 'ل' .fatha] ∧
    Admissible [atom 'ق' .fatha, atom 'ا' .sukun, atom 'ل' .fatha] := by
  constructor <;> (rw [← run_ne_fellOut_iff]; decide)

/-- قَالْتُ ← قُلْتُ: الأصلُ غيرُ مرخَّصٍ والصورةُ مرخَّصة (الحذفُ ملزَم). -/
theorem qultu_witness :
    ¬ Admissible [atom 'ق' .fatha, atom 'ا' .sukun, atom 'ل' .sukun, atom 'ت' .damma] ∧
    Admissible [atom 'ق' .damma, atom 'ل' .sukun, atom 'ت' .damma] := by
  constructor
  · rw [← run_ne_fellOut_iff]; decide
  · rw [← run_ne_fellOut_iff]; decide

/-- يَقْوُلُ ← يَقُولُ: كلاهما مرخَّص (النقلُ حافظ). -/
theorem yaqulu_witness :
    Admissible [atom 'ي' .fatha, atom 'ق' .sukun, atom 'و' .damma, atom 'ل' .damma] ∧
    Admissible [atom 'ي' .fatha, atom 'ق' .damma, atom 'و' .sukun, atom 'ل' .damma] := by
  constructor <;> (rw [← run_ne_fellOut_iff]; decide)

end A116.Ilal
