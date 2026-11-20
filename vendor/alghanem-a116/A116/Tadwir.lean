/-!
# الضياعُ الصفريّ: إزالةُ الازدواج ثمّ الردُّ هويّة

السؤال (فحصُ التقرير الوارد، 2026-10-12): «الضياعُ الصفريّ للمدوَّر: كلُّ زائدةٍ مدوَّرةٍ لها قانونيٌّ بالبصمة نفسها». والدعوى
كما وردت فحصٌ في شجرةٍ ليست في المستودعات؛ وهنا **مبرهنتُها العامّة**: إزالةُ الازدواج (`dedupBy`) تُخرج قائمةً قانونيّة
وفهرسًا، والردُّ (`restore`) يعيد المدخلَ بعينه — بأيّ علاقةٍ يُعرف بها المكرَّر، **بشرط** أن تكون صادقةً على المدخل
(ما تطابقه العلاقةُ متساوٍ فعلًا).

* `restore_dedupBy`: الردُّ هويّة، لكلّ قائمة.
* `dedupBy_nodup`: القانونيُّ بلا تكرار (إن كانت العلاقةُ انعكاسيّة).
* `dedupBy_length_le`، `mem_dedupBy`: لا يزيد على المدخل، وعناصرُه عناصرُه.
* مثولان: المساواةُ نفسُها (`dedup`) بلا شرط، والبصمةُ (`dedupKey`) **بشرط** أن لا تتصادم بصمتان على المدخل
  (`restore_dedupKey`) — والشرطُ لازم: `collision_loses` شاهدٌ على أنّ التصادم يُضيع.

فالبرهانُ يحمل حدَّه: «لا ضياع» مبرهَنٌ للدالّة، و«لا تصادم على هذا المودَع» يُقاس على بايتاته؛ ولا «يقينَ مطلق» بينهما.
-/

set_option autoImplicit false

namespace A116.Tadwir

variable {α : Type}

/-- الردّ: كلُّ رقمٍ في الفهرس إلى عنصره من القانونيّ. -/
def restore (u : List α) (ix : List Nat) : List α := ix.filterMap fun i => u[i]?

/-- خطوةٌ: إن طابقت العلاقةُ عنصرًا في القانونيّ أُحيل إليه، وإلّا أُلحق. -/
def stepBy (r : α → α → Bool) (s : List α × List Nat) (x : α) : List α × List Nat :=
  match s.1.findIdx? (fun y => r y x) with
  | some i => (s.1, s.2 ++ [i])
  | none => (s.1 ++ [x], s.2 ++ [s.1.length])

def dedupBy (r : α → α → Bool) (l : List α) : List α × List Nat := l.foldl (stepBy r) ([], [])

/-- الثابت: الفهرسُ داخلَ القانونيّ، والردُّ هو المقروءُ حتى الآن، والقانونيُّ منه. -/
structure Inv (p : List α) (s : List α × List Nat) : Prop where
  lt : ∀ i ∈ s.2, i < s.1.length
  back : restore s.1 s.2 = p
  sub : ∀ y ∈ s.1, y ∈ p

theorem restore_append_left (u v : List α) (ix : List Nat) (h : ∀ i ∈ ix, i < u.length) :
    restore (u ++ v) ix = restore u ix := by
  induction ix with
  | nil => rfl
  | cons i t ih =>
    have hi : i < u.length := h i (by simp)
    have ht := ih (fun j hj => h j (by simp [hj]))
    simp only [restore, List.filterMap_cons] at ht ⊢
    rw [List.getElem?_append_left hi, ht]

theorem step_inv (r : α → α → Bool) (L : List α) (hr : ∀ a ∈ L, ∀ b ∈ L, r a b = true → a = b)
    (p : List α) (s : List α × List Nat) (x : α) (hp : ∀ z ∈ p, z ∈ L) (hx : x ∈ L) (h : Inv p s) :
    Inv (p ++ [x]) (stepBy r s x) := by
  unfold stepBy
  split
  · rename_i i hi
    obtain ⟨hlt, hrx, _⟩ := List.findIdx?_eq_some_iff_getElem.1 hi
    have hy : s.1[i] ∈ L := hp _ (h.sub _ (List.getElem_mem hlt))
    have heq : s.1[i] = x := hr _ hy _ hx hrx
    refine ⟨?_, ?_, ?_⟩
    · intro j hj
      rcases List.mem_append.1 hj with hj | hj
      · exact h.lt j hj
      · simp at hj; subst hj; exact hlt
    · have hb := h.back
      simp only [restore] at hb ⊢
      rw [List.filterMap_append, hb]
      simp [List.getElem?_eq_getElem hlt, heq]
    · intro y hy'; exact List.mem_append_left _ (h.sub y hy')
  · refine ⟨?_, ?_, ?_⟩
    · intro j hj
      rcases List.mem_append.1 hj with hj | hj
      · have := h.lt j hj; simp; omega
      · simp at hj; subst hj; simp
    · simp only [restore, List.filterMap_append]
      have h1 := restore_append_left s.1 [x] s.2 h.lt
      simp only [restore] at h1
      rw [h1]
      have h2 := h.back
      simp only [restore] at h2
      rw [h2]
      simp
    · intro y hy'
      rcases List.mem_append.1 hy' with hy' | hy'
      · exact List.mem_append_left _ (h.sub y hy')
      · simp at hy'; subst hy'; simp

theorem fold_inv (r : α → α → Bool) (L : List α) (hr : ∀ a ∈ L, ∀ b ∈ L, r a b = true → a = b) :
    ∀ (t p : List α) (s : List α × List Nat), (∀ z ∈ p ++ t, z ∈ L) → Inv p s →
      Inv (p ++ t) (t.foldl (stepBy r) s)
  | [], p, s, _, h => by simpa using h
  | x :: t, p, s, hL, h => by
    rw [List.foldl_cons]
    have hx : x ∈ L := hL x (by simp)
    have hp : ∀ z ∈ p, z ∈ L := fun z hz => hL z (List.mem_append_left _ hz)
    have h' := step_inv r L hr p s x hp hx h
    have := fold_inv r L hr t (p ++ [x]) (stepBy r s x) (by simpa using hL) h'
    simpa using this

/-- **الضياعُ الصفريّ**: الردُّ بعد إزالة الازدواج هويّة، متى صدقت العلاقةُ على المدخل. -/
theorem restore_dedupBy (r : α → α → Bool) (l : List α)
    (hr : ∀ a ∈ l, ∀ b ∈ l, r a b = true → a = b) :
    restore (dedupBy r l).1 (dedupBy r l).2 = l := by
  have := fold_inv r l hr l [] ([], []) (by simp) ⟨by simp, by simp [restore], by simp⟩
  simpa [dedupBy] using this.back

theorem mem_dedupBy (r : α → α → Bool) (l : List α) (hr : ∀ a ∈ l, ∀ b ∈ l, r a b = true → a = b)
    (y : α) (hy : y ∈ (dedupBy r l).1) : y ∈ l := by
  have := fold_inv r l hr l [] ([], []) (by simp) ⟨by simp, by simp [restore], by simp⟩
  simpa using this.sub y hy

theorem stepBy_nodup (r : α → α → Bool) (hrefl : ∀ a, r a a = true) (s : List α × List Nat) (x : α)
    (h : s.1.Nodup) : (stepBy r s x).1.Nodup := by
  unfold stepBy
  split
  · exact h
  · rename_i hn
    have hnot := List.findIdx?_eq_none_iff.1 hn
    refine List.nodup_append.2 ⟨h, by simp, ?_⟩
    intro a ha b hb hab
    simp at hb; subst hb; subst hab
    have := hnot a ha
    rw [hrefl] at this
    exact absurd this (by decide)

/-- **القانونيُّ بلا تكرار** لكلّ علاقةٍ انعكاسيّة. -/
theorem dedupBy_nodup (r : α → α → Bool) (hrefl : ∀ a, r a a = true) (l : List α) :
    (dedupBy r l).1.Nodup := by
  unfold dedupBy
  suffices ∀ (t : List α) (s : List α × List Nat), s.1.Nodup → (t.foldl (stepBy r) s).1.Nodup from
    this l _ List.nodup_nil
  intro t
  induction t with
  | nil => intro s h; exact h
  | cons x t ih => intro s h; exact ih _ (stepBy_nodup r hrefl s x h)

theorem stepBy_length (r : α → α → Bool) (s : List α × List Nat) (x : α) :
    (stepBy r s x).1.length ≤ s.1.length + 1 := by
  unfold stepBy; split <;> simp

/-- **لا يزيد القانونيُّ على المدخل.** -/
theorem dedupBy_length_le (r : α → α → Bool) (l : List α) : (dedupBy r l).1.length ≤ l.length := by
  unfold dedupBy
  suffices ∀ (t : List α) (s : List α × List Nat), (t.foldl (stepBy r) s).1.length ≤ s.1.length + t.length
    from by simpa using this l ([], [])
  intro t
  induction t with
  | nil => intro s; simp
  | cons x t ih =>
    intro s
    have := ih (stepBy r s x)
    have := stepBy_length r s x
    simp only [List.foldl_cons, List.length_cons]
    omega

/-! ## المثولان: المساواةُ والبصمة -/

section
variable [DecidableEq α]

def dedup (l : List α) : List α × List Nat := dedupBy (fun a b => decide (a = b)) l

/-- بالمساواة: لا ضياعَ بلا شرط، والقانونيُّ بلا تكرار. -/
theorem restore_dedup (l : List α) : restore (dedup l).1 (dedup l).2 = l :=
  restore_dedupBy _ l fun _ _ _ _ h => of_decide_eq_true h

theorem dedup_nodup (l : List α) : (dedup l).1.Nodup :=
  dedupBy_nodup (fun a b => decide (a = b)) (fun _ => decide_eq_true rfl) l

end

section
variable {β : Type} [DecidableEq β]

/-- بالبصمة: يُعرف المكرَّرُ بتساوي البصمتين. -/
def dedupKey (k : α → β) (l : List α) : List α × List Nat := dedupBy (fun a b => decide (k a = k b)) l

/-- **لا ضياعَ بالبصمة إن لم تتصادم على المدخل** — الشرطُ يُقاس على المودَع، والأثرُ مبرهَن. -/
theorem restore_dedupKey (k : α → β) (l : List α) (hk : ∀ a ∈ l, ∀ b ∈ l, k a = k b → a = b) :
    restore (dedupKey k l).1 (dedupKey k l).2 = l :=
  restore_dedupBy _ l fun a ha b hb h => hk a ha b hb (of_decide_eq_true h)

end

/-- **والشرطُ لازم**: بصمةٌ تتصادم (كلُّ شيءٍ إلى صفر) تُضيع — ‎[1, 2]‎ يُردّ ‎[1, 1]‎. -/
theorem collision_loses :
    restore (dedupKey (fun _ : Nat => (0 : Nat)) [1, 2]).1 (dedupKey (fun _ : Nat => (0 : Nat)) [1, 2]).2 =
      [1, 1] := by
  decide

end A116.Tadwir
