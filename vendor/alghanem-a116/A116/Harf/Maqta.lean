import A116.Harf.Khana

/-!
# آلةُ المقطع في Algebra: الترخيصُ وصلًا ووقفًا بحالاتٍ مسمّاةٍ لا بالتقطيع

تُقرأ الكلمةُ خانةً خانةً، والحالُ اسمُ ما انتهى إليه المقطعُ الجاري:

* `bad'`: لم يُقرأ شيء — والكلمةُ لا تبدأ بساكن.
* `nawah q`: نواةٌ قصيرةٌ مفتوحة (CV) حركتُها `q`.
* `madd`: نواةٌ طويلة (CVV): ساكنٌ هو حرفُ مدٍّ مجانسٌ لحركة ما قبله (`jins`).
* `qasir`: مقطعٌ قصيرٌ مغلق (CVC).
* `tawil k`: مقطعٌ طويلٌ مغلق (CVVC) — **التقاءُ الساكنين على حدّه**: لا يُوصَل إلّا والذي بعده متحرّكٌ حاملُه
  `k` نفسُه (المُغلِقُ أوّلُ مثلين: حَاجَّ)، ولا يكون آخرًا وصلًا.
* `hamzaAwwal`، `farq`، `tawilFarq`: **مدُّ الفرق** (ءَ اْ ل… أوّلَ الكلمة: آلْآنَ) — طويلٌ مغلقٌ بلا مثل.
* `khatm` (وقفًا وحدَه): ساكنان بعد النواة في الطرف (CVCC: بَحْرْ، CVVCC: تَامّْ — والثاني مثلُ الأوّل).
* `maddHadd` (في السطر وحدَه): مدٌّ آخرَ الكلمة قبل الحدّ — لا يليه ساكنٌ في الكلمة التالية (يَا + الشَّافِعِينَ).
* `mayyit`: لا يُرخَّص.

والوصلُ يرفض ساكنًا ثالثًا وساكنين بعد المغلق، والوقفُ يزيد الطرفَ وحدَه.
-/

set_option autoImplicit false

namespace Harf

inductive Hal where
  | bad'
  | hamzaAwwal
  | farq
  | nawah (q : Haal)
  | madd
  | qasir
  | tawilFarq
  | tawil (k : Hamil)
  | khatm
  | maddHadd
  | mayyit
  deriving DecidableEq, Repr

def Hal.all : List Hal :=
  [.bad', .hamzaAwwal, .farq] ++ Haal.all.map .nawah ++ [.madd, .qasir, .tawilFarq]
    ++ (List.finRange 29).map .tawil ++ [.khatm, .maddHadd, .mayyit]

theorem Hal.mem_all (a : Hal) : a ∈ Hal.all := by
  cases a with
  | nawah q => cases q <;> simp [Hal.all, Haal.all]
  | tawil k => simp [Hal.all]
  | _ => simp [Hal.all]

/-- بعد نواةٍ حركتُها `q`. -/
def baadNawah (q : Haal) (x : Khana) : Hal :=
  if x.haal ≠ .sukun then .nawah x.haal
  else if jins x.hamil = some q then .madd else .qasir

/-- خطوةُ الوصل. -/
def wasl : Hal → Khana → Hal
  | .bad', x =>
    if x.haal = .sukun then .mayyit
    else if x = k 'ء' .fath then .hamzaAwwal else .nawah x.haal
  | .hamzaAwwal, x => if x = k 'ا' .sukun then .farq else baadNawah .fath x
  | .farq, x =>
    if x.haal ≠ .sukun then .nawah x.haal
    else if x.hamil = lam then .tawilFarq else .tawil x.hamil
  | .nawah q, x => baadNawah q x
  | .madd, x => if x.haal ≠ .sukun then .nawah x.haal else .tawil x.hamil
  | .qasir, x => if x.haal ≠ .sukun then .nawah x.haal else .mayyit
  | .tawilFarq, x => if x.haal ≠ .sukun then .nawah x.haal else .mayyit
  | .tawil h, x => if x.haal ≠ .sukun ∧ x.hamil = h then .nawah x.haal else .mayyit
  | .khatm, _ => .mayyit
  | .maddHadd, x => if x.haal ≠ .sukun then .nawah x.haal else .mayyit
  | .mayyit, _ => .mayyit

/-- خطوةُ الوقف: كالوصل، ويُقبل ساكنٌ ثانٍ بعد المغلق طرفًا. -/
def waqf : Hal → Khana → Hal
  | .qasir, x => if x.haal ≠ .sukun then .nawah x.haal else .khatm
  | .tawilFarq, x => if x.haal ≠ .sukun then .nawah x.haal else .khatm
  | .tawil h, x =>
    if x.hamil = h then (if x.haal ≠ .sukun then .nawah x.haal else .khatm) else .mayyit
  | a, x => wasl a x

def qabilWasl : Hal → Bool
  | .tawil _ | .khatm | .mayyit => false
  | _ => true

def qabilWaqf : Hal → Bool
  | .mayyit => false
  | _ => true

def run (f : Hal → Khana → Hal) : Hal → List Khana → Hal
  | a, [] => a
  | a, x :: t => run f (f a x) t

/-- الكلمةُ مرخَّصةٌ وصلًا. -/
def waslB (w : List Khana) : Bool := qabilWasl (run wasl .bad' w)

/-- الكلمةُ مرخَّصةٌ وقفًا. -/
def waqfB (w : List Khana) : Bool := qabilWaqf (run waqf .bad' w)

/-! ## شواهد باليد -/

def hajja : List Khana := [k 'ح' .fath, k 'ا' .sukun, k 'ج' .sukun, k 'ج' .fath]
def qaaltu : List Khana := [k 'ق' .fath, k 'ا' .sukun, k 'ل' .sukun, k 'ت' .damm]
def qultu : List Khana := [k 'ق' .damm, k 'ل' .sukun, k 'ت' .damm]
def qaltu : List Khana := [k 'ق' .fath, k 'ل' .sukun, k 'ت' .damm]
def alaana : List Khana := [k 'ء' .fath, k 'ا' .sukun, k 'ل' .sukun, k 'ء' .fath, k 'ا' .sukun, k 'ن' .fath]
def bahr : List Khana := [k 'ب' .fath, k 'ح' .sukun, k 'ر' .sukun]
def tamm : List Khana := [k 'ت' .fath, k 'ا' .sukun, k 'م' .sukun, k 'م' .sukun]
def rahim : List Khana := [k 'ر' .fath, k 'ح' .kasr, k 'ي' .sukun, k 'م' .sukun]

theorem shawahid :
    waslB hajja ∧ waslB qultu ∧ waslB alaana ∧ !waslB qaaltu ∧
    !waslB bahr ∧ waqfB bahr ∧ !waslB tamm ∧ waqfB tamm ∧ !waslB rahim ∧ waqfB rahim ∧
    !waqfB qaaltu := by decide

theorem wasl_waqf_step : ∀ a ∈ Hal.all, ∀ x ∈ Khana.all,
    (wasl a x ≠ .mayyit → waqf a x = wasl a x) := by decide +kernel

theorem run_mayyit (t : List Khana) : run wasl .mayyit t = .mayyit := by
  induction t with
  | nil => rfl
  | cons x t ih => simpa [run, wasl] using ih

theorem run_wasl_waqf : ∀ (a : Hal) (w : List Khana),
    qabilWasl (run wasl a w) = true → run waqf a w = run wasl a w
  | a, [] => fun _ => rfl
  | a, x :: t => by
    intro h
    simp only [run] at h ⊢
    by_cases hm : wasl a x = .mayyit
    · rw [hm, run_mayyit] at h; simp [qabilWasl] at h
    · rw [wasl_waqf_step a (Hal.mem_all a) x (Khana.mem_all x) hm]
      exact run_wasl_waqf _ t h

/-- **الوصلُ يستلزم الوقف**: كلُّ ما تقبله آلةُ الوصل تقبله آلةُ الوقف. -/
theorem waslB_waqfB (w : List Khana) (h : waslB w = true) : waqfB w = true := by
  unfold waslB at h; unfold waqfB
  rw [run_wasl_waqf .bad' w h]
  revert h; cases run wasl .bad' w <;> simp [qabilWasl, qabilWaqf]

end Harf
