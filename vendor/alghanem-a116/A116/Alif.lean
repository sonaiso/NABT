import A116.Hadd

/-!
# الألفُ لا تكون أبدًا إلّا ساكنة: شبكةُ الـ116 ثلاثٌ منها لا تُرخَّص

شبكةُ الخانات ‎29 × 4 = 116‎ (`cells_length`) تحوي الألفَ بالحركات الثلاث — (ا،فتح) (ا،ضم) (ا،كسر) — ولا
وجودَ لها في الكلام: الكتابُ لسيبويه (JK006989، مختومٌ في SLGE) «لأن الألف لا تكون أبدا إلا ساكنة» (س18101)،
«الألف لا تحرك أبدا» (س18156)، و«الألف لا بد لها من حرف قبلها مفتوح» (س17941). فالهمزةُ حاملٌ مستقلّ (`ء`)
وما كُتب ألفًا بحركةٍ فهو همزةٌ على كرسيّ (`A116.Hamza`)، والبوّابةُ ترفض الألفَ بحركةِ نفسها باسمها
(`BARE_ALIF_OWN_MARK_NOT_LICENSED` في `gate/contextual.py`) — وكان ذلك سياسةً في بايثون بلا تعريفٍ في Lean.

هنا: `alifVowelled` الثلاثُ بأعيانها، و`licensable` = الشبكةُ بدونها: **113** خانةً (`licensable_length`)،
بلا تكرار، والشبكةُ قسمةٌ تامّةٌ بينهما (`cells_partition`)؛ وما يُرخَّص من كلمةٍ لا يحمل ألفًا متحرّكة
(`licensable_no_vowelled_alif`). والمقيسُ (SLGE، `COVERAGE_INDEX`): المشهودُ في المصحف 113 من 113.
ولا يُبرهَن هنا أنّ الألفَ ساكنةٌ في العربيّة — ذلك مرويُّ الكتاب بموضعه؛ Lean يُبرهن خواصَّ التعريف.
-/

namespace A116.Alif

open A116 A116.Ladder

/-- الألفُ بالحركات الثلاث: خاناتٌ في الشبكة لا في الكلام. -/
def alifVowelled : List Cell := [atom 'ا' .fatha, atom 'ا' .damma, atom 'ا' .kasra]

/-- ما يُرخَّص من الشبكة: كلُّ خانةٍ ليست ألفًا متحرّكة. -/
def licensable : List Cell := cells.filter fun c => !(alifVowelled.contains c)

theorem alifVowelled_sub : alifVowelled.all (cells.contains ·) = true := by decide

theorem alifVowelled_length : alifVowelled.length = 3 := by rfl

theorem licensable_length : licensable.length = 113 := by decide

theorem licensable_nodup : licensable.Nodup := by decide

/-- الشبكةُ قسمةٌ تامّة: المرخَّصُ والألفُ المتحرّكة بلا تداخل، ومجموعُهما الـ116. -/
theorem cells_partition :
    licensable.length + alifVowelled.length = cells.length ∧
    licensable.all (fun c => !(alifVowelled.contains c)) = true := by
  decide

/-- الألفُ المتحرّكة ليست من المرخَّص. -/
theorem vowelled_alif_not_licensable (h : Haraka) (hh : h ≠ .sukun) :
    licensable.contains (atom 'ا' h) = false := by
  cases h <;> first | decide | exact absurd rfl hh

/-- الألفُ الساكنة (حرفُ المدّ) مرخَّصة. -/
theorem alif_sukun_licensable : licensable.contains (atom 'ا' .sukun) = true := by decide

/-- كلُّ خانةٍ مرخَّصة إمّا ليست ألفًا وإمّا ألفٌ ساكنة. -/
theorem licensable_no_vowelled_alif :
    licensable.all (fun c => c.carrier != carrierOf 'ا' || c.haraka == .sukun) = true := by
  decide

end A116.Alif
