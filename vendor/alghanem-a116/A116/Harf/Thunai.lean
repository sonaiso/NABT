import A116.Harf.Maqta

/-!
# الترخيصُ الثنائيّ (`src/entry.py::licensed`) قيدًا على آلة المقاطع (ADR ٤)

`entry.licensed` لا يرى إلّا متحرّكًا وساكنًا: لا يبدأ بساكن ولا يتجاور ساكنان. نقلُه هنا بنصّه (`binB`)،
والحلّ: **الثنائيُّ هو الوصلُ مقصورًا على ما لا يتجاور فيه ساكنان** (`binB_eq`) — لا تكافؤ بل تقييدٌ مبرهَن:

* `binary_sound`: كلُّ ما يقبله الثنائيّ يقبله الوصل.
* `hajja_separates`: «حَاجَّ» مرخَّصةٌ وصلًا ومرفوضةٌ ثنائيًّا — فالقيدُ حقيقيّ.
* `binB_through_pattern` و`wasl_not_through_pattern`: الثنائيُّ دالّةٌ في نمط السكون وحدَه، والوصلُ ليس كذلك
  («حَاجَّ» و«حَبْجْجَ» نمطٌ واحد وترخيصان) — وهذا هو العمى عن المدّ.
-/

set_option autoImplicit false

namespace Harf

/-- لا ساكنان متجاوران، والسابقُ ساكنٌ إن كان `b`. -/
def noAdjFrom : Bool → List Khana → Bool
  | _, [] => true
  | b, x :: t => !(b && sakin x) && noAdjFrom (sakin x) t

/-- `src/entry.py::licensed` بنصّه: الفارغُ مقبول، ولا يبدأ بساكن، ولا يتجاور ساكنان. -/
def binB : List Khana → Bool
  | [] => true
  | x :: t => !sakin x && noAdjFrom (sakin x) t

def inBin : Hal → Bool
  | .hamzaAwwal | .farq | .nawah _ | .madd | .qasir | .tawilFarq => true
  | _ => false

def lastSakin : Hal → Bool
  | .farq | .madd | .qasir | .tawilFarq => true
  | _ => false

theorem bin_step : ∀ a ∈ Hal.all, inBin a = true → ∀ x ∈ Khana.all, (lastSakin a && sakin x) = false →
    inBin (wasl a x) = true ∧ lastSakin (wasl a x) = sakin x := by
  decide +kernel

theorem bin_acc : ∀ a ∈ Hal.all, inBin a = true → qabilWasl a = true := by decide

theorem bin_run : ∀ (a : Hal) (w : List Khana), inBin a = true → noAdjFrom (lastSakin a) w = true →
    qabilWasl (run wasl a w) = true
  | a, [], ha, _ => bin_acc a (Hal.mem_all a) ha
  | a, x :: t, ha, hn => by
    simp only [noAdjFrom, Bool.and_eq_true, Bool.not_eq_true'] at hn
    obtain ⟨h1, h2⟩ := bin_step a (Hal.mem_all a) ha x (Khana.mem_all x) hn.1
    exact bin_run _ t h1 (by rw [h2]; exact hn.2)

theorem bad'_step : ∀ x ∈ Khana.all, sakin x = false → inBin (wasl .bad' x) = true ∧
    lastSakin (wasl .bad' x) = false := by decide +kernel

theorem bad'_sakin : ∀ x ∈ Khana.all, sakin x = true → wasl .bad' x = .mayyit := by decide +kernel

/-- **الحلّ**: الثنائيُّ هو الوصلُ مقصورًا على ما لا يتجاور فيه ساكنان. -/
theorem binB_eq (w : List Khana) : binB w = (waslB w && noAdjFrom false w) := by
  match w with
  | [] => rfl
  | x :: t =>
    cases hx : sakin x
    · have hn : noAdjFrom false (x :: t) = noAdjFrom false t := by simp [noAdjFrom, hx]
      simp only [binB, hx, Bool.not_false, Bool.true_and, hn]
      cases ht : noAdjFrom false t
      · simp
      · obtain ⟨h1, h2⟩ := bad'_step x (Khana.mem_all x) hx
        have := bin_run _ t h1 (by rw [h2]; exact ht)
        simp [waslB, run, this]
    · have hm := bad'_sakin x (Khana.mem_all x) hx
      simp [binB, hx, waslB, run, hm, run_mayyit, qabilWasl]

theorem binary_sound (w : List Khana) (h : binB w = true) : waslB w = true := by
  rw [binB_eq] at h; simp only [Bool.and_eq_true] at h; exact h.1

theorem hajja_separates : waslB hajja = true ∧ binB hajja = false := by decide

def hajbja : List Khana := [k 'ح' .fath, k 'ب' .sukun, k 'ج' .sukun, k 'ج' .fath]

theorem binB_through_pattern : ∀ u v : List Khana, u.map sakin = v.map sakin → binB u = binB v := by
  intro u v h
  have key : ∀ (b : Bool) (u v : List Khana), u.map sakin = v.map sakin → noAdjFrom b u = noAdjFrom b v := by
    intro b u
    induction u generalizing b with
    | nil => intro v h; cases v <;> simp_all [noAdjFrom]
    | cons x t ih =>
      intro v h
      cases v with
      | nil => simp at h
      | cons y s =>
        simp only [List.map_cons, List.cons.injEq] at h
        simp only [noAdjFrom, h.1, ih _ s h.2]
  cases u with
  | nil => cases v <;> simp_all [binB]
  | cons x t =>
    cases v with
    | nil => simp at h
    | cons y s =>
      simp only [List.map_cons, List.cons.injEq] at h
      simp only [binB, h.1, key _ t s h.2]

theorem wasl_not_through_pattern :
    hajja.map sakin = hajbja.map sakin ∧ waslB hajja = true ∧ waslB hajbja = false := by decide

end Harf
