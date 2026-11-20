import A116.Ternary

/-!
# عددُ المرخَّص وقفًا فيبوناتشي (ADR ١٠)

الوزنُ الصوتيّ للخانة: المتحرّكُ (`cv`) حرفٌ وحركة = 2، وحرفُ المدّ (`v`) والساكنُ (`c`) = 1. `kseqs n` كلُّ
قوائم الخانات المجرّدة بوزن `n`، بلا تكرار (`mem_kseqs`، `kseqs_nodup`). والمبرهَن:

* `pauseB_eq_acc`: الترخيصُ الوقفيّ (`pauseB`، على التقطيع المبرهَن في `Stages`) هو قبولُ آلةٍ منتهيةٍ من سبع
  حالات تقرأ الخانةَ بعد الخانة — كلّيًّا، بالاستقراء على الطول.
* `pause_count_fib`: **عددُ المرخَّص وقفًا بوزن `n` (لـ `n ≥ 2`) هو `fib n`** — لكلّ `n`، بالاستقراء القويّ على
  تكرار الآلة؛ فـ ‎Σ_{n=2}^{12} fib n = 375‎ (`pause_count_375`) عددٌ عن الترخيص المبرهَن نفسه.

والسببُ البنيويّ: المقاطعُ غيرُ الطرفيّة أوزانُها {2، 3، 3، 4} (CV، CVV، CVC، CVVC)، والطرفُ يزيد عليها CVCC وCVVCC
(4، 5)؛ ودالّتا التوليد تتحلّلان إلى ‎x²(1+x)/(1−x−x²)‎.
-/

namespace A116.Ternary

open A116.Stages K

/-- فيبوناتشي: ‎fib 0 = 0، fib 1 = 1‎. -/
def fib : Nat → Nat
  | 0 => 0
  | 1 => 1
  | n + 2 => fib n + fib (n + 1)

/-- الوزنُ الصوتيّ للخانة. -/
def kw : K → Nat
  | cv => 2
  | v => 1
  | c => 1

def weight (k : List K) : Nat := (k.map kw).sum

/-- كلُّ قوائم الخانات بوزن `n`. -/
def kseqs : Nat → List (List K)
  | 0 => [[]]
  | 1 => [[v], [c]]
  | n + 2 => (kseqs n).map (cv :: ·) ++ (kseqs (n + 1)).map (v :: ·) ++ (kseqs (n + 1)).map (c :: ·)

theorem mem_kseqs : ∀ (n : Nat) (k : List K), k ∈ kseqs n ↔ weight k = n
  | 0, k => by
    cases k with
    | nil => simp [kseqs, weight]
    | cons a t => cases a <;> simp [kseqs, weight, kw] <;> omega
  | 1, k => by
    match k with
    | [] => simp [kseqs, weight]
    | [a] => cases a <;> simp [kseqs, weight, kw]
    | a :: b :: t =>
      simp only [kseqs, List.mem_cons, List.mem_nil_iff, or_false, weight, List.map_cons,
        List.sum_cons]
      constructor
      · rintro (h | h) <;> simp at h
      · intro h; cases a <;> cases b <;> simp [kw] at h <;> omega
  | n + 2, k => by
    cases k with
    | nil => simp [kseqs, weight]
    | cons a t =>
      have ih0 := mem_kseqs n t
      have ih1 := mem_kseqs (n + 1) t
      cases a <;> simp [kseqs, weight, kw, List.mem_append, List.mem_map] at ih0 ih1 ⊢ <;>
        simp [ih0, ih1] <;> omega

theorem kseqs_nodup : ∀ n, (kseqs n).Nodup
  | 0 => by simp [kseqs]
  | 1 => by decide
  | n + 2 => by
    have h0 := kseqs_nodup n
    have h1 := kseqs_nodup (n + 1)
    simp only [kseqs, List.nodup_append]
    refine ⟨⟨List.Pairwise.map _ (fun _ _ h e => h (by simpa using e)) h0,
      List.Pairwise.map _ (fun _ _ h e => h (by simpa using e)) h1, ?_⟩,
      List.Pairwise.map _ (fun _ _ h e => h (by simpa using e)) h1, ?_⟩
    · intro a ha b hb; simp only [List.mem_map] at ha hb
      obtain ⟨_, _, rfl⟩ := ha; obtain ⟨_, _, rfl⟩ := hb; simp
    · intro a ha b hb; simp only [List.mem_append, List.mem_map] at ha hb
      obtain ⟨_, _, rfl⟩ := hb
      rcases ha with ⟨_, _, rfl⟩ | ⟨_, _, rfl⟩ <;> simp

/-! ## الآلة -/

/-- الحالات: البدء، بعد متحرّك، بعد مدّ، بعد ساكن، بعد مدٍّ فساكن، بعد ساكنَي الطرف، والميّتة. -/
inductive St where
  | start | n | nv | nc | nvc | fin | dead
  deriving DecidableEq, Repr

def δ : St → K → St
  | .start, cv => .n
  | .start, _ => .dead
  | .n, cv => .n
  | .n, v => .nv
  | .n, c => .nc
  | .nv, cv => .n
  | .nv, v => .dead
  | .nv, c => .nvc
  | .nc, cv => .n
  | .nc, v => .dead
  | .nc, c => .fin
  | .nvc, cv => .n
  | .nvc, v => .dead
  | .nvc, c => .fin
  | .fin, _ => .dead
  | .dead, _ => .dead

def acc : St → List K → Bool
  | s, [] => s != .dead
  | s, x :: t => acc (δ s x) t

/-! ## الآلةُ هي الترخيصُ الوقفيّ -/

theorem cv_not_mem_run : ∀ t : List K, cv ∉ (Stages.run t).1
  | [] => by simp [Stages.run]
  | cv :: t => by simp [Stages.run]
  | v :: t => by simp [Stages.run, cv_not_mem_run t]
  | c :: t => by simp [Stages.run, cv_not_mem_run t]

theorem startsCV_run : ∀ t : List K, StartsCV (Stages.run t).2
  | [] => trivial
  | cv :: t => rfl
  | v :: t => by simp only [Stages.run]; exact startsCV_run t
  | c :: t => by simp only [Stages.run]; exact startsCV_run t

theorem parse_of_startsCV {rest : List K} (h : StartsCV rest) :
    parse rest = (syls rest).map (fun ss => (.none, ss)) := by
  have hr : Stages.run rest = ([], rest) := by
    have := run_of_noCV (r := []) (by simp) h; simpa using this
  unfold parse; rw [hr]; simp only [leadOf]
  cases syls rest <;> rfl

theorem pauseB_of_startsCV {rest : List K} (h : StartsCV rest) :
    pauseB rest = match syls rest with
      | some ss => ss.dropLast.all fun s => !(pauseOnly s)
      | none => false := by
  unfold pauseB; rw [parse_of_startsCV h]; cases syls rest <;> rfl

theorem syls_eq_nil {k : List K} (h : syls k = some []) : k = [] := by
  have := flatMap_of_syls k [] h; simpa using this.symm

theorem pauseB_cons_cv (t : List K) :
    pauseB (cv :: t) = match sylOf (Stages.run t).1 with
      | some s => pauseB (Stages.run t).2 && ((Stages.run t).2.isEmpty || !(pauseOnly s))
      | none => false := by
  have hs : StartsCV (cv :: t) := rfl
  rw [pauseB_of_startsCV hs, pauseB_of_startsCV (startsCV_run t)]
  rw [syls]
  cases hr : sylOf (Stages.run t).1 with
  | none => simp
  | some s =>
    cases hss : syls (Stages.run t).2 with
    | none => simp
    | some ss =>
      simp only
      cases ss with
      | nil => simp [syls_eq_nil hss]
      | cons s' ss' =>
        have hne : (Stages.run t).2 ≠ [] := by
          intro he; rw [he] at hss; simp [syls] at hss
        have he : (Stages.run t).2.isEmpty = false := by
          cases h : (Stages.run t).2 <;> simp_all
        simp [List.dropLast_cons_cons, he, Bool.and_comm]

theorem pauseB_nil : pauseB [] = true := by
  have h := parse_flat .none []
  simp only [flat, Lead.atoms, List.flatMap_nil, List.append_nil] at h
  unfold pauseB; rw [h]; rfl

theorem pauseB_cons_noncv (a : K) (t : List K) (ha : a ≠ cv) : pauseB (a :: t) = false := by
  unfold pauseB parse
  cases a with
  | cv => exact absurd rfl ha
  | v =>
    simp only [Stages.run]
    cases h1 : leadOf (v :: (Stages.run t).1) with
    | none => simp
    | some l =>
      cases syls (Stages.run t).2 with
      | none => simp
      | some ss =>
        simp only
        cases l with
        | none => simp [leadOf] at h1; split at h1 <;> simp_all
        | _ => rfl
  | c =>
    simp only [Stages.run]
    cases h1 : leadOf (c :: (Stages.run t).1) with
    | none => simp
    | some l =>
      cases syls (Stages.run t).2 with
      | none => simp
      | some ss =>
        simp only
        cases l with
        | none => simp [leadOf] at h1; split at h1 <;> simp_all
        | _ => rfl

theorem acc_start_of_startsCV {rest : List K} (h : StartsCV rest) : acc .start rest = acc .n rest := by
  cases rest with
  | nil => rfl
  | cons a t => simp [StartsCV] at h; subst h; rfl

/-- الذيلُ بعد المتحرّك: آلةُ «بعد متحرّك» على ‎r ++ rest‎ (‎r‎ بلا متحرّك و‎rest‎ يبدأ بمتحرّك) هي صحّةُ ‎r‎ مقطعًا
وقبولُ ‎rest‎ وألّا يكون مقطعُ الطرف غيرَ طرف. -/
theorem acc_coda {r rest : List K} (hr : cv ∉ r) (hrest : StartsCV rest) :
    acc .n (r ++ rest) = match sylOf r with
      | some s => acc .start rest && (rest.isEmpty || !(pauseOnly s))
      | none => false := by
  have hs := acc_start_of_startsCV hrest
  have dead : ∀ t, acc .dead t = false := by
    intro t; induction t with
    | nil => rfl
    | cons a t ih => cases a <;> simpa [acc, δ] using ih
  have fin_rest : acc .fin rest = rest.isEmpty := by
    cases rest with
    | nil => rfl
    | cons a t => cases a <;> simp [acc, δ, dead]
  have q : ∀ q : St, q ≠ .dead → q ≠ .start → q ≠ .fin → acc q rest = acc .n rest := by
    intro q h1 h2 h3
    cases rest with
    | nil => cases q <;> first | rfl | simp_all
    | cons a t =>
      simp [StartsCV] at hrest; subst hrest
      cases q <;> simp_all [acc, δ]
  match r, hr with
  | [], _ => simp [sylOf, acc_start_of_startsCV hrest, pauseOnly]
  | [v], _ => simp [acc, δ, sylOf, pauseOnly, q .nv (by decide) (by decide) (by decide), hs]
  | [c], _ => simp [acc, δ, sylOf, pauseOnly, q .nc (by decide) (by decide) (by decide), hs]
  | [v, c], _ => simp [acc, δ, sylOf, pauseOnly, q .nvc (by decide) (by decide) (by decide), hs]
  | [c, c], _ => simp [acc, δ, sylOf, pauseOnly, fin_rest]; intro h; subst h; rfl
  | [v, c, c], _ => simp [acc, δ, sylOf, pauseOnly, fin_rest]; intro h; subst h; rfl
  | cv :: _, hr => simp at hr
  | [v, cv], hr | [c, cv], hr => simp at hr
  | v :: v :: t, _ => simp [acc, δ, dead, sylOf]
  | c :: v :: t, _ => simp [acc, δ, dead, sylOf]
  | v :: c :: v :: t, _ => simp [acc, δ, dead, sylOf]
  | v :: c :: cv :: t, hr => simp at hr
  | v :: c :: c :: x :: t, _ => simp [acc, δ, dead, sylOf]
  | c :: c :: x :: t, _ => simp [acc, δ, dead, sylOf]
  | v :: cv :: t, hr | c :: cv :: t, hr => simp at hr

/-- **الآلةُ هي الترخيصُ الوقفيّ**، لكلّ قائمة خانات. -/
theorem pauseB_eq_acc (k : List K) : pauseB k = acc .start k := by
  induction k using (measure List.length).wf.induction with
  | h k ih =>
    match k with
    | [] => rw [pauseB_nil]; rfl
    | v :: t => rw [pauseB_cons_noncv v t (by decide)]; simp [acc, δ]; exact acc_dead t
    | c :: t => rw [pauseB_cons_noncv c t (by decide)]; simp [acc, δ]; exact acc_dead t
    | cv :: t =>
      have hlt : (Stages.run t).2.length < (cv :: t).length := by
        have := run_length t; simp; omega
      have ih' := ih _ hlt
      have ht : t = (Stages.run t).1 ++ (Stages.run t).2 := (run_append t).symm
      rw [pauseB_cons_cv]
      show _ = acc .n t
      rw [ht, acc_coda (cv_not_mem_run t) (startsCV_run t), ← ht, ← ih']
where
  acc_dead : ∀ t, acc .dead t = false := by
    intro t; induction t with
    | nil => rfl
    | cons a t ih => cases a <;> simpa [acc, δ] using ih

/-! ## العدّ -/

def cnt (s : St) (n : Nat) : Nat := ((kseqs n).filter (acc s)).length

theorem filter_cons (s : St) (x : K) (l : List (List K)) :
    ((l.map (x :: ·)).filter (acc s)).length = (l.filter (acc (δ s x))).length := by
  rw [List.filter_map, List.length_map]; rfl

theorem cnt_zero (s : St) : cnt s 0 = if s = .dead then 0 else 1 := by
  cases s <;> rfl

theorem cnt_one (s : St) : cnt s 1 = cnt (δ s v) 0 + cnt (δ s c) 0 := by
  cases s <;> rfl

theorem cnt_succ_succ (s : St) (n : Nat) :
    cnt s (n + 2) = cnt (δ s cv) n + cnt (δ s v) (n + 1) + cnt (δ s c) (n + 1) := by
  unfold cnt
  simp only [kseqs, List.filter_append, List.length_append, filter_cons]

theorem cnt_dead : ∀ n, cnt .dead n = 0
  | 0 => rfl
  | 1 => rfl
  | n + 2 => by rw [cnt_succ_succ]; simp [δ, cnt_dead n, cnt_dead (n + 1)]

theorem cnt_fin : ∀ n, cnt .fin (n + 1) = 0
  | 0 => by rw [cnt_one]; simp [δ, cnt_zero]
  | n + 1 => by rw [cnt_succ_succ]; simp [δ, cnt_dead]

theorem cnt_nc (n : Nat) : cnt .nc (n + 2) = cnt .n n := by
  rw [cnt_succ_succ]; simp [δ, cnt_dead, cnt_fin]

theorem cnt_nvc (n : Nat) : cnt .nvc (n + 2) = cnt .n n := by
  rw [cnt_succ_succ]; simp [δ, cnt_dead, cnt_fin]

theorem cnt_nv (n : Nat) : cnt .nv (n + 2) = cnt .n n + cnt .nvc (n + 1) := by
  rw [cnt_succ_succ]; simp [δ, cnt_dead]

theorem fib_add_two (n : Nat) : fib (n + 2) = fib n + fib (n + 1) := rfl

/-- بعد متحرّك: ‎fib (n + 2)‎. -/
theorem cnt_n : ∀ n, cnt .n n = fib (n + 2)
  | 0 => by decide
  | 1 => by decide
  | 2 => by decide
  | n + 3 => by
    have e : cnt .n (n + 3) = cnt .n (n + 1) + cnt .nv (n + 2) + cnt .nc (n + 2) := by
      have := cnt_succ_succ .n (n + 1); simpa [δ] using this
    have hnc : cnt .nc (n + 2) = fib (n + 2) := by rw [cnt_nc, cnt_n n]
    have hnvc : cnt .nvc (n + 1) = fib (n + 1) := by
      cases n with
      | zero => decide
      | succ m => rw [cnt_nvc, cnt_n m]
    have hnv : cnt .nv (n + 2) = fib (n + 3) := by
      rw [cnt_nv, cnt_n n, hnvc, show fib (n + 3) = fib (n + 1) + fib (n + 2) from rfl]; omega
    have h1 : cnt .n (n + 1) = fib (n + 3) := cnt_n (n + 1)
    rw [e, h1, hnv, hnc,
      show fib (n + 3 + 2) = fib (n + 3) + fib (n + 4) from rfl,
      show fib (n + 4) = fib (n + 2) + fib (n + 3) from rfl]
    omega

/-- **عددُ المرخَّص وقفًا بوزن `n ≥ 2` هو `fib n`** (بالآلة)؛ وبوزن 1 لا شيء (ساكنٌ أو مدٌّ وحده). -/
theorem cnt_start (n : Nat) : cnt .start (n + 2) = fib (n + 2) := by
  rw [cnt_succ_succ]
  simp [δ, cnt_dead, cnt_n]

theorem cnt_start_one : cnt .start 1 = 0 := by decide

/-- **المبرهنة:** من كلّ قوائم الخانات بوزن `n ≥ 2`، المرخَّصةُ وقفًا (`pauseB`) عددُها `fib n`. -/
theorem pause_count_fib (n : Nat) (h : 2 ≤ n) : ((kseqs n).filter pauseB).length = fib n := by
  obtain ⟨m, rfl⟩ : ∃ m, n = m + 2 := ⟨n - 2, by omega⟩
  have : (kseqs (m + 2)).filter pauseB = (kseqs (m + 2)).filter (acc .start) := by
    congr 1; funext k; exact pauseB_eq_acc k
  rw [this]; exact cnt_start m

/-- الأطوالُ 2..12 مجموعُها 375. -/
theorem pause_count_375 :
    ((List.range 11).map (fun i => ((kseqs (i + 2)).filter pauseB).length)).sum = 375 := by
  simp only [List.range, List.range.loop, List.map]
  rw [pause_count_fib 2 (by omega), pause_count_fib 3 (by omega), pause_count_fib 4 (by omega),
    pause_count_fib 5 (by omega), pause_count_fib 6 (by omega), pause_count_fib 7 (by omega),
    pause_count_fib 8 (by omega), pause_count_fib 9 (by omega), pause_count_fib 10 (by omega),
    pause_count_fib 11 (by omega), pause_count_fib 12 (by omega)]
  rfl

end A116.Ternary
