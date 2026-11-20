import A116.Cells

/-!
# النموذجُ المقطعيُّ المُعلَن على الـ116 — إغلاقُه وتوصيفُه لجميع الأطوال

النظيرُ البايثونيُّ: `a116_bridge_licence.SyllableState` و`step` و
`run_declared_model` و`fixpoint_reading` و`FixpointReading.closes_all_lengths`.

## المسلّمة المُعلَنة

* **م٣ (النموذج):** بذرةٌ متحرّكةٌ تفتح المقطع، وساكنٌ واحدٌ يُغلقه، ولا يبتدئ
  مقطعٌ بساكن. وهو مُعلَنٌ ضيّقًا **عمدًا**؛ فما خرج عنه حالةٌ مُسمّاة
  (`fellOut`) لا امتناعٌ في العربيّة.

## المبرهنات

* **المبرهنة ١ (الإغلاق، كما في البايثون):** الإشباعُ من حالة البدء يستقرّ في
  درجةٍ واحدة على مجموعةٍ `Sstar` مغلقةٍ تحت `step` على كلّ خانات الـ116، فأثرُ
  **كلّ** سلسلةٍ بأيّ طولٍ واقعٌ فيها (`run_mem_Sstar`).
  **تنبيهٌ صريح:** `Sstar` هي الحالاتُ الثلاثُ كلُّها (`Sstar_complete`)، فهذه
  المبرهنةُ تلزم من **تمام** `step` وحدَه، وتصحّ لأيّ انتقالٍ تامّ. فهي صحيحةٌ
  لكنّها لا تقول شيئًا عن اللغة؛ وتُثبَت هنا لأنّ البايثون يدّعيها، ويُسمّى
  خواؤها لئلّا يُقرأ فيها أكثرُ ممّا فيها.
* **المبرهنة ٢ (التوصيف، وهي المبرهنةُ ذاتُ المحتوى):** لكلّ سلسلةٍ `w` بأيّ طول،
  لا تسقط `w` من النموذج **إذا وفقط إذا** لم تبدأ بساكنٍ ولم يتجاور فيها ساكنان
  (`run_ne_fellOut_iff`). والطرفُ الأيمنُ مُعرَّفٌ تعريفًا تقريريًّا مستقلًّا عن
  `step`، فالمبرهنةُ ربطٌ بين آلةٍ ومواصفةٍ لا مطابقةُ الآلة لنفسها.
* **المبرهنة ٣ (العمى عن الحامل):** `step` لا يقرأ من الخانة إلّا كونَها سكونًا
  (`step_depends_only_on_sukun`). فالنموذجُ على الـ116 هو في حقيقته نموذجٌ على
  صنفين: ساكن وغيرُ ساكن. وهذا حدٌّ للنموذج يُعلَن، لا عيبٌ يُخفى.
* **السقوطُ ماصّ:** من سقط لم يعُد (`run_fellOut`).
-/

namespace A116

/-- حالاتُ النموذج؛ والسقوطُ حالةٌ مُسمّاةٌ لا استثناء. -/
inductive State where
  /-- منتظرٌ بذرةً متحرّكة (`AWAITING_AN_ONSET`). -/
  | awaiting
  /-- بعد بذرةٍ متحرّكة (`AFTER_A_VOWELLED_SEED`). -/
  | afterSeed
  /-- خارجَ النموذج (`FELL_OUT_OF_THE_MODEL`). -/
  | fellOut
  deriving DecidableEq, Repr

namespace State

def all : List State := [awaiting, afterSeed, fellOut]

theorem mem_all (q : State) : q ∈ all := by
  cases q <;> simp [all]

/-- اسمُ الحالة كما في `SyllableState` بالبايثون؛ لجدول المطابقة وحدَه. -/
def pyName : State → String
  | awaiting => "AWAITING_AN_ONSET"
  | afterSeed => "AFTER_A_VOWELLED_SEED"
  | fellOut => "FELL_OUT_OF_THE_MODEL"

end State

open State

/-- الانتقالُ التامّ: لكلّ حالةٍ وخانةٍ صورة، ولا موضعَ بلا انتقال. -/
def step : State → Cell → State
  | fellOut, _ => fellOut
  | awaiting, c => if c.isSukun then fellOut else afterSeed
  | afterSeed, c => if c.isSukun then awaiting else afterSeed

/-- الأثرُ ‎δ*‎ من حالةٍ على سلسلة؛ وهو `run_declared_model` حين تكون الحالةُ `awaiting`. -/
def run (q : State) (w : List Cell) : State := w.foldl step q

@[simp] theorem run_nil (q : State) : run q [] = q := rfl

@[simp] theorem run_cons (q : State) (c : Cell) (w : List Cell) :
    run q (c :: w) = run (step q c) w := rfl

/-! ## المبرهنة ٣ — العمى عن الحامل -/

theorem step_depends_only_on_sukun (q : State) (c c' : Cell)
    (h : c.isSukun = c'.isSukun) : step q c = step q c' := by
  cases q <;> simp [step, h]

/-! ## السقوطُ ماصّ -/

@[simp] theorem run_fellOut (w : List Cell) : run fellOut w = fellOut := by
  induction w with
  | nil => rfl
  | cons c w ih => simpa [step] using ih

/-! ## المبرهنة ١ — الإشباعُ ونقطةُ الاستقرار -/

/-- ضمُّ عنصرٍ إن لم يكن حاضرًا؛ فالقائمةُ تبقى بلا تكرار. -/
def insertNew (acc : List State) (q : State) : List State :=
  if q ∈ acc then acc else acc ++ [q]

/-- درجةُ إشباعٍ واحدة: ‎S ∪ {δ(q, c) : q ∈ S, c ∈ A₁₁₆}‎. -/
def grow (S : List State) : List State :=
  (S.flatMap fun q => cells.map (step q)).foldl insertNew S

/-- الإشباعُ بوقودٍ معلَن؛ ويقف عند أوّل درجةٍ لا تزيد. -/
def saturate : Nat → List State → List State
  | 0, S => S
  | n + 1, S =>
    let S' := grow S
    if S'.length = S.length then S else saturate n S'

/-- المجموعةُ المستقرّة من حالة البدء. والوقودُ `|Q| = 3` يكفي، إذ كلُّ درجةٍ
لا تقف تزيد عنصرًا على الأقلّ. -/
def Sstar : List State := saturate State.all.length [awaiting]

/-- درجاتُ الإشباع كما في `fixpoint_reading().rungs`: ‎(1, 3)‎، ثمّ لا زيادة. -/
theorem saturation_rungs :
    [awaiting].length = 1 ∧ (grow [awaiting]).length = 3 ∧
      (grow (grow [awaiting])).length = 3 := by
  decide +kernel

/-- **الإغلاقُ مفحوصٌ استقصاءً:** ‎|Sstar| × 116 = 348‎ انتقالًا، كلُّها داخلَ `Sstar`. -/
theorem Sstar_closed_on_cells :
    ∀ q ∈ Sstar, ∀ c ∈ cells, step q c ∈ Sstar := by
  decide +kernel

/-- والإغلاقُ على كلّ خانةٍ ممكنة، لا على المعدودة فحسب، بتمام التعداد. -/
theorem Sstar_closed (q : State) (hq : q ∈ Sstar) (c : Cell) : step q c ∈ Sstar :=
  Sstar_closed_on_cells q hq c (mem_cells c)

theorem awaiting_mem_Sstar : awaiting ∈ Sstar := by decide +kernel

/-- **المبرهنة ١:** أثرُ كلّ سلسلةٍ بأيّ طولٍ واقعٌ في `Sstar`. والبرهانُ استقراءٌ
على السلسلة: الأساسُ حالةُ البدء، والخطوةُ الإغلاق. -/
theorem run_mem_Sstar (w : List Cell) : run awaiting w ∈ Sstar := by
  suffices h : ∀ q, q ∈ Sstar → run q w ∈ Sstar from h awaiting awaiting_mem_Sstar
  induction w with
  | nil => intro q hq; simpa using hq
  | cons c w ih => intro q hq; simpa using ih (step q c) (Sstar_closed q hq c)

/-- **خواءُ المبرهنة ١ مُعلَنًا:** `Sstar` هي الحالاتُ كلُّها. -/
theorem Sstar_complete (q : State) : q ∈ Sstar := by
  cases q <;> decide +kernel

/-! ## المبرهنة ٢ — التوصيفُ لجميع الأطوال -/

/-- لا تبدأ السلسلةُ بساكن. -/
def HeadNotSukun : List Cell → Prop
  | [] => True
  | c :: _ => c.isSukun = false

/-- لا يتجاور ساكنان في السلسلة. -/
def NoAdjacentSukun : List Cell → Prop
  | [] => True
  | [_] => True
  | a :: b :: t => ¬ (a.isSukun = true ∧ b.isSukun = true) ∧ NoAdjacentSukun (b :: t)

/-- **المواصفةُ التقريريّة:** سلسلةٌ مقبولةٌ في النموذج المُعلَن (م٣). -/
def Admissible (w : List Cell) : Prop := HeadNotSukun w ∧ NoAdjacentSukun w

/-- اللمّةُ الجامعة: توصيفُ الحالتين غيرِ الساقطتين معًا، بالاستقراء على السلسلة. -/
theorem run_ne_fellOut_aux (w : List Cell) :
    (run afterSeed w ≠ fellOut ↔ NoAdjacentSukun w) ∧
      (run awaiting w ≠ fellOut ↔ Admissible w) := by
  induction w with
  | nil => simp [Admissible, HeadNotSukun, NoAdjacentSukun]
  | cons a t ih =>
    obtain ⟨ih₁, ih₂⟩ := ih
    cases ha : a.isSukun
    · -- خانةٌ متحرّكة: الحالتان تصيران `afterSeed`.
      have hstep₁ : step afterSeed a = afterSeed := by simp [step, ha]
      have hstep₂ : step awaiting a = afterSeed := by simp [step, ha]
      have hno : NoAdjacentSukun (a :: t) ↔ NoAdjacentSukun t := by
        cases t with
        | nil => simp [NoAdjacentSukun]
        | cons b t' => simp [NoAdjacentSukun, ha]
      refine ⟨?_, ?_⟩
      · rw [run_cons, hstep₁, hno]; exact ih₁
      · rw [run_cons, hstep₂, ih₁]
        simp [Admissible, HeadNotSukun, ha, hno]
    · -- خانةُ سكون: بعد البذرة تُغلق المقطع، وفي الانتظار تُسقِط.
      have hstep₁ : step afterSeed a = awaiting := by simp [step, ha]
      have hstep₂ : step awaiting a = fellOut := by simp [step, ha]
      refine ⟨?_, ?_⟩
      · rw [run_cons, hstep₁, ih₂]
        cases t with
        | nil => simp [Admissible, HeadNotSukun, NoAdjacentSukun]
        | cons b t' =>
          simp only [Admissible, HeadNotSukun, NoAdjacentSukun, ha, true_and]
          cases hb : b.isSukun <;> simp
      · rw [run_cons, hstep₂, run_fellOut]
        simp [Admissible, HeadNotSukun, ha]

/-- **المبرهنة ٢:** سلسلةٌ لا تسقط من النموذج **إذا وفقط إذا** كانت مقبولةً
بالمواصفة التقريريّة؛ لكلّ طول. -/
theorem run_ne_fellOut_iff (w : List Cell) : run awaiting w ≠ fellOut ↔ Admissible w :=
  (run_ne_fellOut_aux w).2

/-- صيغةُ النقض: تسقط السلسلةُ إذا وفقط إذا بدأت بساكنٍ أو تجاور فيها ساكنان. -/
theorem run_eq_fellOut_iff (w : List Cell) : run awaiting w = fellOut ↔ ¬ Admissible w := by
  rw [← run_ne_fellOut_iff]; exact Classical.not_not.symm

end A116
