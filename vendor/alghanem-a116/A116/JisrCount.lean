import A116.Jisr

/-!
# العدُّ على السحب لكلّ طول (ADR ٦٨): عددُ الأعلى = مجموعٌ على مسارات الأدنى لحاصل ضرب أحجام الألياف

لنظامٍ `M` على أبجديّةٍ `A` بلا تكرار، وإسقاطٍ `f : β → α`، وحروفٍ `S` كلُّ حرفٍ موجودٍ منها صورتُه في `A`:
عددُ المرخَّص في السحب `comap M f` بطول n على `S` يساوي، **لكلّ n**، مجموعَ حاصل ضرب أحجام الألياف على كلّ مسارٍ مرخَّصٍ
في `M` بطول n على `A` (`count_comap`). والبرهانُ بالاستقراء على n بوزنٍ يتبع آخرَ الصورة (`weighted`): خطوةُ `gen` تعتمد على
آخر السلسلة وحدَه (`licWasl_snoc`)، والجمعُ على حروف `S` يُعاد تجميعُه على أليافها (`regroup`).
-/

namespace A116.JisrCount

open A116 A116.Nizam A116.Jisr

variable {α β : Type}

/-! ## ١. أدواتُ الجمع -/

def sumN : List Nat → Nat
  | [] => 0
  | x :: t => x + sumN t

theorem sumN_append : ∀ (l m : List Nat), sumN (l ++ m) = sumN l + sumN m
  | [], m => by simp [sumN]
  | x :: l, m => by simp [sumN, sumN_append l m, Nat.add_assoc]

theorem sumN_flatMap {γ δ : Type} (g : δ → Nat) (h : γ → List δ) : ∀ (l : List γ),
    sumN ((l.flatMap h).map g) = sumN (l.map fun x => sumN ((h x).map g))
  | [] => rfl
  | x :: l => by simp [List.flatMap_cons, sumN_append, sumN, sumN_flatMap g h l]

theorem sumN_congr {γ : Type} (g g' : γ → Nat) : ∀ (l : List γ), (∀ x ∈ l, g x = g' x) →
    sumN (l.map g) = sumN (l.map g')
  | [], _ => rfl
  | x :: l, h => by
    simp only [List.map_cons, sumN]
    rw [h x (by simp), sumN_congr g g' l (fun y hy => h y (by simp [hy]))]

theorem sumN_mul {γ : Type} (g : γ → Nat) (c : Nat) : ∀ (l : List γ),
    sumN (l.map g) * c = sumN (l.map fun x => g x * c)
  | [] => by simp [sumN]
  | x :: l => by simp [sumN, Nat.add_mul, sumN_mul g c l]

theorem sumN_add {γ : Type} (g g' : γ → Nat) : ∀ (l : List γ),
    sumN (l.map fun x => g x + g' x) = sumN (l.map g) + sumN (l.map g')
  | [] => rfl
  | x :: l => by simp [sumN, sumN_add g g' l]; omega

theorem sumN_zero {γ : Type} : ∀ (l : List γ), sumN (l.map fun _ => 0) = 0
  | [] => rfl
  | _ :: l => by simp [sumN, sumN_zero l]

theorem sumN_filter_map {γ δ : Type} (p : γ → Bool) (e : γ → δ) (g : δ → Nat) : ∀ (l : List γ),
    sumN (((l.filter p).map e).map g) = sumN (l.map fun x => if p x then g (e x) else 0)
  | [] => rfl
  | x :: l => by
    have ih := sumN_filter_map p e g l
    by_cases hx : p x = true
    · rw [List.filter_cons_of_pos hx]; simp only [List.map_cons, sumN, ih, hx, ite_true]
    · rw [List.filter_cons_of_neg hx]; simp only [List.map_cons, sumN, ih]; simp [hx]

theorem sumN_ones {γ : Type} : ∀ (l : List γ), sumN (l.map fun _ => 1) = l.length
  | [] => rfl
  | _ :: l => by simp [sumN, sumN_ones l]; omega

/-! ## ٢. خطوةُ الترخيص تعتمد على الآخر وحدَه -/

/-- إذنُ إلحاق حرفٍ بعد سلسلة: ابتداءً إن كانت فارغة، ووصلًا بآخرها إن لم تكن. -/
def step (N : Nizam α) : Option α → α → Bool
  | none, b => N.wujud b && N.ibtida b
  | some a, b => N.wujud b && N.wasl a b

theorem chain_snoc (N : Nizam α) : ∀ (a : α) (t : List α) (b : α),
    chain N a (t ++ [b]) = (chain N a t && N.wasl ((a :: t).getLast (by simp)) b)
  | a, [], b => by simp [chain]
  | a, c :: t, b => by
    simp only [List.cons_append, chain, chain_snoc N c t b, Bool.and_assoc]
    rfl

theorem licWasl_snoc (N : Nizam α) (w : List α) (b : α) (hw : licWasl N w = true) :
    licWasl N (w ++ [b]) = step N w.getLast? b := by
  cases w with
  | nil => simp [licWasl, step, chain]
  | cons a t =>
    simp only [licWasl, Bool.and_eq_true, List.all_eq_true] at hw
    have hlast : (a :: t).getLast? = some ((a :: t).getLast (by simp)) := rfl
    simp only [List.cons_append, licWasl, List.all_cons, List.all_append, chain_snoc, hlast, step]
    have h1 : (t.all N.wujud) = true := List.all_eq_true.2 (fun x hx => hw.1.1 x (by simp [hx]))
    have h0 : N.wujud a = true := hw.1.1 a (by simp)
    simp [h0, h1, hw.1.2, hw.2]

theorem step_comap (M : Nizam α) (f : β → α) (o : Option β) (b : β) :
    step (comap M f) o b = step M (o.map f) (f b) := by
  cases o <;> rfl

/-! ## ٣. إعادةُ التجميع على الألياف -/

variable [DecidableEq α]

/-- حجمُ الليف: حروفُ `S` التي صورتُها `a`. -/
def fiberOf (f : β → α) (S : List β) (a : α) : Nat := (S.filter fun b => f b == a).length

theorem sum_indicator (h : α → Nat) (x : α) : ∀ (A : List α), A.Nodup →
    sumN (A.map fun a => if x = a then h a else 0) = if x ∈ A then h x else 0
  | [], _ => by simp [sumN]
  | a :: A, hA => by
    have hA' := List.nodup_cons.1 hA
    simp only [List.map_cons, sumN, sum_indicator h x A hA'.2]
    by_cases hx : x = a
    · subst hx; simp [hA'.1]
    · simp [hx]

/-- **إعادةُ التجميع**: الجمعُ على الحروف = الجمعُ على صور الألياف مضروبةً في أحجامها، إن انعدم الوزنُ خارج `A`. -/
theorem regroup (f : β → α) (h : α → Nat) (A : List α) (hA : A.Nodup) : ∀ (S : List β),
    (∀ b ∈ S, h (f b) ≠ 0 → f b ∈ A) →
    sumN (S.map fun b => h (f b)) = sumN (A.map fun a => fiberOf f S a * h a)
  | [], _ => by simp [sumN, fiberOf, sumN_zero]
  | b :: S, hS => by
    have ih := regroup f h A hA S (fun x hx => hS x (by simp [hx]))
    have e : (fun a => fiberOf f (b :: S) a * h a) =
        (fun a => (if f b = a then h a else 0) + fiberOf f S a * h a) := by
      funext a
      by_cases hb : f b = a
      · simp [fiberOf, hb, Nat.add_mul, Nat.add_comm]
      · simp [fiberOf, hb]
    simp only [List.map_cons, sumN, ih, e, sumN_add, sum_indicator h (f b) A hA]
    by_cases hm : f b ∈ A
    · simp [hm]
    · have : h (f b) = 0 := by
        rcases Nat.eq_zero_or_pos (h (f b)) with h0 | hpos
        · exact h0
        · exact absurd (hS b (by simp) (Nat.pos_iff_ne_zero.1 hpos)) hm
      simp [hm, this]

/-! ## ٤. المبرهنة -/

/-- حاصلُ ضرب أحجام الألياف على مسار. -/
def prodF (f : β → α) (S : List β) : List α → Nat
  | [] => 1
  | a :: u => fiberOf f S a * prodF f S u

theorem prodF_snoc (f : β → α) (S : List β) : ∀ (u : List α) (a : α),
    prodF f S (u ++ [a]) = prodF f S u * fiberOf f S a
  | [], a => by simp [prodF]
  | x :: u, a => by simp [prodF, prodF_snoc f S u a, Nat.mul_assoc]

theorem getLast?_snoc {γ : Type} (w : List γ) (b : γ) : (w ++ [b]).getLast? = some b := by simp

/-- **الموزون**: لكلّ وزنٍ يتبع آخرَ الصورة، الجمعُ على مرخَّص السحب = الجمعُ على مرخَّص الأدنى بحاصل ضرب الألياف. -/
theorem weighted (M : Nizam α) (f : β → α) (S : List β) (A : List α) (hA : A.Nodup)
    (hS : ∀ b ∈ S, M.wujud (f b) = true → f b ∈ A) : ∀ (n : Nat) (φ : Option α → Nat),
    sumN ((gen (comap M f) S n).map fun w => φ ((w.map f).getLast?)) =
      sumN ((gen M A n).map fun u => φ u.getLast? * prodF f S u)
  | 0, φ => by simp [gen, sumN, prodF]
  | n + 1, φ => by
    -- الوزنُ الجديد: ما يضيفه حرفٌ واحدٌ بعد آخرٍ صورتُه o.
    let ψ : Option α → Nat := fun o =>
      sumN (A.map fun a => if step M o a then fiberOf f S a * φ (some a) else 0)
    -- الجانبُ الأيسر
    have hL : sumN ((gen (comap M f) S (n + 1)).map fun w => φ ((w.map f).getLast?)) =
        sumN ((gen (comap M f) S n).map fun w => ψ ((w.map f).getLast?)) := by
      simp only [gen]
      rw [sumN_flatMap]
      apply sumN_congr
      intro w hw
      have hlw := ((mem_gen _ S n w).1 hw).2.2
      rw [sumN_filter_map]
      have e1 : ∀ b, licWasl (comap M f) (w ++ [b]) = step M ((w.map f).getLast?) (f b) := by
        intro b
        rw [licWasl_snoc _ w b hlw, step_comap, List.getLast?_map]
      simp only [e1, List.map_append, List.map_cons, List.map_nil, getLast?_snoc]
      show sumN (S.map fun b => (fun a => if step M ((w.map f).getLast?) a = true then φ (some a)
        else 0) (f b)) = _
      refine (regroup f (fun a => if step M ((w.map f).getLast?) a = true then φ (some a) else 0)
        A hA S ?_).trans ?_
      · intro b hb hne
        apply hS b hb
        cases hwj : M.wujud (f b)
        · exfalso; apply hne
          cases hl : (w.map f).getLast? <;> simp [step, hwj]
        · rfl
      · apply sumN_congr; intro a _
        simp only [List.getLast?_map]
        by_cases hs : step M (w.getLast?.map f) a = true <;> simp [hs]
    -- الجانبُ الأيمن
    have hR : sumN ((gen M A (n + 1)).map fun u => φ u.getLast? * prodF f S u) =
        sumN ((gen M A n).map fun u => ψ u.getLast? * prodF f S u) := by
      simp only [gen]
      rw [sumN_flatMap]
      apply sumN_congr
      intro u hu
      have hlu := ((mem_gen _ A n u).1 hu).2.2
      rw [sumN_filter_map]
      simp only [licWasl_snoc M u _ hlu, getLast?_snoc, prodF_snoc]
      show _ = sumN (A.map fun a => if step M u.getLast? a = true then fiberOf f S a * φ (some a) else 0)
        * prodF f S u
      rw [sumN_mul]
      apply sumN_congr; intro a _
      by_cases hs : step M u.getLast? a = true
      · simp only [hs, ite_true]; ac_rfl
      · simp [hs]
    rw [hL, hR, weighted M f S A hA hS n ψ]

/-- **العدُّ على السحب لكلّ طول**. -/
theorem count_comap (M : Nizam α) (f : β → α) (S : List β) (A : List α) (hA : A.Nodup)
    (hS : ∀ b ∈ S, M.wujud (f b) = true → f b ∈ A) (n : Nat) :
    (gen (comap M f) S n).length = sumN ((gen M A n).map (prodF f S)) := by
  have := weighted M f S A hA hS n (fun _ => 1)
  simp only [sumN_ones, Nat.one_mul] at this
  exact this

end A116.JisrCount
