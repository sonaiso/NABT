/-!
# الحصرُ عند المجهول المسمّى: حدّا العدّ مبرهَنان (ADR ٣٧)

قياسُ نسبةٍ على مرجعٍ محجوب قد يتوقّف على معاملٍ لا يشهده المرجع (تعديةُ فعلٍ لم يُعلَّم، تشكيلُ مثالٍ ملتبس).
لا يُخمَّن المعامل: يُحصر العدُّ بين حدّين يصحّان **لكلّ** قيمةٍ له، وهما محقَّقان بقيمتين بعينهما فلا حدَّ أضيق.

* `hasr`: لكلّ عنصرٍ إصابتان ممكنتان `a` و`b` (بحسب قيمة المعامل)، ولكلّ اختيارٍ `c`، عددُ الإصابات بين عدّ
  `a && b` وعدّ `a || b`.
* `hasr_tight_low`/`hasr_tight_high`: الحدّان يُبلَغان باختيارين مسمّيين.
* `countP_mono`: الإصابةُ مطّردةٌ في المتوقَّع — قاعدةٌ أوسعُ لا تُنقص الإصابة؛ فقواعدُ أمثلةٍ بين استخراجٍ صارمٍ
  وآخرَ مُرخًى تحصر الإصابةَ بين عدّيهما.
* `hasr_mono`: الحصران معًا — معاملٌ مجهولٌ وقاعدةٌ بين حدّين — حصرٌ واحد.

لا شيء هنا على اللغة: خواصُّ عدٍّ على قوائم، تُطبَّق في `tools/gen_lane.py` (`sensitivity`).
-/

namespace A116.Hasr

variable {α : Type}

/-- **الحصر**: لكلّ اختيارٍ للمعامل، عددُ الإصابات بين عدّ «كلاهما» وعدّ «أحدهما». -/
theorem hasr (a b c : α → Bool) (L : List α) :
    L.countP (fun x => a x && b x) ≤ L.countP (fun x => if c x then a x else b x) ∧
      L.countP (fun x => if c x then a x else b x) ≤ L.countP (fun x => a x || b x) := by
  induction L with
  | nil => simp
  | cons x L ih =>
    simp only [List.countP_cons]
    cases ha : a x <;> cases hb : b x <;> cases hc : c x <;> simp <;> omega

/-- الحدُّ الأدنى يُبلَغ: يُختار من الإصابتين أضعفُهما. -/
theorem hasr_tight_low (a b : α → Bool) (L : List α) :
    L.countP (fun x => if !a x then a x else b x) = L.countP (fun x => a x && b x) := by
  congr 1
  funext x
  cases a x <;> cases b x <;> rfl

/-- والأعلى يُبلَغ: يُختار أقواهما. -/
theorem hasr_tight_high (a b : α → Bool) (L : List α) :
    L.countP (fun x => if a x then a x else b x) = L.countP (fun x => a x || b x) := by
  congr 1
  funext x
  cases a x <;> cases b x <;> rfl

/-- **الاطّراد**: ما أصاب بالقاعدة الأضيق أصاب بالأوسع. -/
theorem countP_mono (p q : α → Bool) (h : ∀ x, p x = true → q x = true) (L : List α) :
    L.countP p ≤ L.countP q := by
  induction L with
  | nil => simp
  | cons x L ih =>
    simp only [List.countP_cons]
    cases hp : p x
    · cases q x <;> simp <;> omega
    · simp [h x hp]; omega

/-- **الحصران معًا**: معاملٌ مجهول (`c`) وقاعدةٌ بين صارمةٍ (`a₀`، `b₀`) ومُرخاةٍ (`a₁`، `b₁`). -/
theorem hasr_mono (a₀ b₀ a₁ b₁ c : α → Bool) (ha : ∀ x, a₀ x = true → a₁ x = true)
    (hb : ∀ x, b₀ x = true → b₁ x = true) (L : List α) :
    L.countP (fun x => a₀ x && b₀ x) ≤ L.countP (fun x => if c x then a₀ x else b₀ x) ∧
      L.countP (fun x => if c x then a₀ x else b₀ x) ≤ L.countP (fun x => if c x then a₁ x else b₁ x) ∧
      L.countP (fun x => if c x then a₁ x else b₁ x) ≤ L.countP (fun x => a₁ x || b₁ x) := by
  refine ⟨(hasr a₀ b₀ c L).1, countP_mono _ _ ?_ L, (hasr a₁ b₁ c L).2⟩
  intro x hx
  cases hc : c x
  · simp only [hc] at hx ⊢; exact hb x hx
  · simp only [hc] at hx ⊢; exact ha x hx

/-- **الحصرُ على قائمة مرشَّحين** — تعميمُ `hasr`: إن كان الحقُّ `t x` أحدَ المرشَّحين `C x` (تعديةٌ مجهولة، بابٌ
خفيّ، وزنٌ لا يُستردّ إلّا قائمةً)، فعددُ الإصابة الحقّ بين عدّ «كلُّ المرشَّحين يصيب» وعدّ «أحدُهم يصيب». -/
theorem hasr_list {β : Type} (C : α → List β) (t : α → β) (p : β → Bool)
    (ht : ∀ x, t x ∈ C x) (L : List α) :
    L.countP (fun x => (C x).all p) ≤ L.countP (fun x => p (t x)) ∧
      L.countP (fun x => p (t x)) ≤ L.countP (fun x => (C x).any p) := by
  refine ⟨countP_mono _ _ ?_ L, countP_mono _ _ ?_ L⟩
  · intro x h
    exact (List.all_eq_true.mp h) (t x) (ht x)
  · intro x h
    exact List.any_eq_true.mpr ⟨t x, ht x, h⟩

/-- **الشاهدُ يضيّق ولا يوسّع**: مرشَّحون أقلُّ (`D ⊆ C`، بشاهدٍ يُسقط بعضَهم) يرفعون الحدَّ الأدنى ويخفضون
الأعلى؛ فإن بقي الحقُّ فيهم فالحصرُ الأضيقُ صادقٌ أيضًا (`hasr_list`). -/
theorem hasr_refine {β : Type} (C D : α → List β) (hsub : ∀ x, ∀ b ∈ D x, b ∈ C x)
    (p : β → Bool) (L : List α) :
    L.countP (fun x => (C x).all p) ≤ L.countP (fun x => (D x).all p) ∧
      L.countP (fun x => (D x).any p) ≤ L.countP (fun x => (C x).any p) := by
  refine ⟨countP_mono _ _ ?_ L, countP_mono _ _ ?_ L⟩
  · intro x h
    exact List.all_eq_true.mpr fun b hb => (List.all_eq_true.mp h) b (hsub x b hb)
  · intro x h
    obtain ⟨b, hb, hp⟩ := List.any_eq_true.mp h
    exact List.any_eq_true.mpr ⟨b, hsub x b hb, hp⟩

/-- **التعيينُ بالتمايز** (ADR ٤٣): إن كان حقُّ بندٍ (`x`) من مرشَّحيه `A` وكان غيرَ حقِّ بندٍ آخرَ تعيّن (`b`) — بندان
مسمّيان في النصّ لا يكرّر أحدُهما الآخر — فهو من `A` بعد حذف `b`. -/
theorem pin_distinct {β : Type} [DecidableEq β] (A : List β) (b x : β) (hx : x ∈ A)
    (hne : x ≠ b) : x ∈ A.filter (fun y => decide (y ≠ b)) :=
  List.mem_filter.mpr ⟨hx, by simpa using hne⟩

/-- فإن بقي بعد الحذف مرشَّحٌ واحد فهو الحقّ. -/
theorem pin_unique {β : Type} [DecidableEq β] (A : List β) (b c x : β) (hx : x ∈ A)
    (hne : x ≠ b) (h : A.filter (fun y => decide (y ≠ b)) = [c]) : x = c := by
  have hm := pin_distinct A b x hx hne
  rw [h] at hm
  simpa using hm

end A116.Hasr
