import A116.Tasrif

/-!
# دوالُّ الخانات لا تفصل المعاني: التكافؤُ «دالّ ↔ مدلول» ليس دالّةً في الخانات

التقريرُ الوارد (2026-10-12) جعل `Slge.licensed_iff` شاهدًا على «التكافؤ بين الدالّ والمدلول عند الترميز»، ثمّ عدّ التكافؤَ
الصوريَّ دَينًا (D-DELTA). وهنا البرهانُ على أنّ الوسمَ الأوّلَ فوق سنده: `licensed_iff` تكافؤٌ بين ترخيصين **كلاهما دالّةٌ في
الخانات**، و**لا دالّةَ في الخانات تفصل جذرين مختلفين صورتاهما خاناتٌ واحدة**:

* `qala_same_cells`: قَالَ من (ق و ل) ومن (ق ي ل) خاناتٌ واحدة: قَ اْ لَ (والجذران مختلفان: `qwl_ne_qyl`).
* `no_cell_function_separates`: لكلّ دالّةٍ P على الخانات، ‎P(قَالَ من قول) = P(قَالَ من قيل)‎.
* `no_cell_function_recovers_root`: لا دالّةَ من الخانات إلى الجذور تردّ كلَّ صيغةٍ إلى جذرها — فالجذرُ (ومعه ما يتعلّق به من
  دلالةٍ في المقاييس) **ليس دالّةً في الخانات**؛ وما يردّه (`gate.recover`) يردّه قراءاتٍ متعدّدة، كما يشهد استرجاعُ قَالَ ← قول، قيل.

فالمبرهَنُ في الترميز تكافؤٌ دالٌّ–دالّ؛ وتكافؤُ Δ لا يكون دالّةً في الخانات وحدَها — يحتاج معطًى غيرَها مودَعًا (المادّة ١٧).
ونظيرُه في الأسماء `Certificate.cells_forget_rank` (عَلَى/عَلَا).
-/

set_option autoImplicit false

namespace A116.Dal

open A116 A116.Wazn A116.Tasrif

def qwl : Root 3 := r3 'ق' 'و' 'ل'
def qyl : Root 3 := r3 'ق' 'ي' 'ل'

/-- الماضي فَعَلَ 3MS بالقالب على الجذر. -/
def qala (r : Root 3) : List Cell := fillC (madi (sifa r) .fatha .fatha) r

theorem qwl_ne_qyl : qwl ≠ qyl := by
  intro h
  have := congrFun h 1
  exact absurd this (by decide)

theorem qala_same_cells : qala qwl = qala qyl := by decide +kernel

/-- **لا دالّةَ في الخانات تفصلهما.** -/
theorem no_cell_function_separates {β : Type} (P : List Cell → β) : P (qala qwl) = P (qala qyl) := by
  rw [qala_same_cells]

/-- **لا ردَّ من الخانات وحدَها إلى الجذر.** -/
theorem no_cell_function_recovers_root :
    ¬ ∃ f : List Cell → Root 3, f (qala qwl) = qwl ∧ f (qala qyl) = qyl := by
  rintro ⟨f, h1, h2⟩
  apply qwl_ne_qyl
  rw [← h1, ← h2, qala_same_cells]

end A116.Dal
