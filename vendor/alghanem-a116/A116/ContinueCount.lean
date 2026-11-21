import A116.PauseCount

/-!
# عددُ المرخَّص وصلًا بالوزن (ADR ١١، تتمّةُ ADR ١٠)

الوصلُ (`continueB`) يرفض المقطعَ الوقفيَّ في كلّ موضع، فآلتُه آلةُ الوقف (`PauseCount.δ`) إلّا أنّ الساكنَ
الثاني بعد مقطعٍ مغلق ميّت لا طرف: `δC`. والمبرهَن:

* `continueB_eq_accC`: الترخيصُ وصلًا هو قبولُ هذه الآلة، كلّيًّا (بالاستقراء القويّ على الطول).
* `cntC_n_rec`: التكرارُ ‎a(m+4) = a(m+2) + 2·a(m+1) + a(m)‎ — المقاطعُ أوزانُها {2، 3، 3، 4}.
* **`continue_count_closed`**: عددُ المرخَّص وصلًا بوزن `n` هو ‎(fib (n+1) + χ n) / 2‎ حيث ‎χ‎ دوريٌّ
  بدورة 3 (‎1، −1، 0‎ لـ ‎n mod 3 = 0، 1، 2‎)، مكتوبًا في الطبيعيّات بلا طرح:
  ‎2·a(n) + [n mod 3 = 1] = fib (n+1) + [n mod 3 = 0]‎. والسببُ أنّ ‎x⁴ − x² − 2x − 1 = (x² − x − 1)(x² + x + 1)‎:
  عاملُ فيبوناتشي وعاملُ جذور الواحد التكعيبيّة.
* `pause_eq_continue_add`: ‎fib n = a(n) + a(n−4) + a(n−5)‎ — الوقفُ هو الوصلُ ومقطعٌ طرفيٌّ CVCC أو CVVCC.

فالوصلُ **ليس** فيبوناتشي، بل نصفُ فيبوناتشي مُزاحًا بحدٍّ دوريّ؛ والعلاقةُ مبرهنةٌ لا مسمّاةٌ مرآة.
-/

namespace A116.Ternary

open A116.Stages K

/-! ## آلةُ الوصل -/

def δC : St → K → St
  | .nc, c => .dead
  | .nvc, c => .dead
  | s, x => δ s x

def accC : St → List K → Bool
  | s, [] => s != .dead
  | s, x :: t => accC (δC s x) t

theorem accC_dead : ∀ t, accC .dead t = false
  | [] => rfl
  | a :: t => by cases a <;> exact accC_dead t

theorem continueB_of_startsCV {rest : List K} (h : StartsCV rest) :
    continueB rest = match syls rest with
      | some ss => ss.all fun s => !(pauseOnly s)
      | none => false := by
  unfold continueB; rw [parse_of_startsCV h]; cases syls rest <;> rfl

theorem continueB_cons_cv (t : List K) :
    continueB (cv :: t) = match sylOf (Stages.run t).1 with
      | some s => continueB (Stages.run t).2 && !(pauseOnly s)
      | none => false := by
  have hs : StartsCV (cv :: t) := rfl
  rw [continueB_of_startsCV hs, continueB_of_startsCV (startsCV_run t)]
  rw [syls]
  cases hr : sylOf (Stages.run t).1 with
  | none => simp
  | some s =>
    cases hss : syls (Stages.run t).2 with
    | none => simp
    | some ss => simp [Bool.and_comm]

theorem continueB_nil : continueB [] = true := by
  have h := parse_flat .none []
  simp only [flat, Lead.atoms, List.flatMap_nil, List.append_nil] at h
  unfold continueB; rw [h]; rfl

theorem continueB_cons_noncv (a : K) (t : List K) (ha : a ≠ cv) : continueB (a :: t) = false := by
  unfold continueB parse
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

theorem accC_start_of_startsCV {rest : List K} (h : StartsCV rest) :
    accC .start rest = accC .n rest := by
  cases rest with
  | nil => rfl
  | cons a t => simp [StartsCV] at h; subst h; rfl

theorem accC_coda {r rest : List K} (hr : cv ∉ r) (hrest : StartsCV rest) :
    accC .n (r ++ rest) = match sylOf r with
      | some s => accC .start rest && !(pauseOnly s)
      | none => false := by
  have hs := accC_start_of_startsCV hrest
  have q : ∀ q : St, q ≠ .dead → q ≠ .start → q ≠ .fin → accC q rest = accC .n rest := by
    intro q h1 h2 h3
    cases rest with
    | nil => cases q <;> first | rfl | simp_all
    | cons a t =>
      simp [StartsCV] at hrest; subst hrest
      cases q <;> simp_all [accC, δC, δ]
  match r, hr with
  | [], _ => simp [sylOf, accC_start_of_startsCV hrest, pauseOnly]
  | [v], _ => simp [accC, δC, δ, sylOf, pauseOnly, q .nv (by decide) (by decide) (by decide), hs]
  | [c], _ => simp [accC, δC, δ, sylOf, pauseOnly, q .nc (by decide) (by decide) (by decide), hs]
  | [v, c], _ =>
    simp [accC, δC, δ, sylOf, pauseOnly, q .nvc (by decide) (by decide) (by decide), hs]
  | [c, c], _ => simp [accC, δC, δ, sylOf, pauseOnly, accC_dead]
  | [v, c, c], _ => simp [accC, δC, δ, sylOf, pauseOnly, accC_dead]
  | cv :: _, hr => simp at hr
  | [v, cv], hr | [c, cv], hr => simp at hr
  | v :: v :: t, _ => simp [accC, δC, δ, accC_dead, sylOf]
  | c :: v :: t, _ => simp [accC, δC, δ, accC_dead, sylOf]
  | v :: c :: v :: t, _ => simp [accC, δC, δ, accC_dead, sylOf]
  | v :: c :: cv :: t, hr => simp at hr
  | v :: c :: c :: x :: t, _ => simp [accC, δC, δ, accC_dead, sylOf]
  | c :: c :: x :: t, _ => simp [accC, δC, δ, accC_dead, sylOf]
  | v :: cv :: t, hr | c :: cv :: t, hr => simp at hr

/-- **الآلةُ هي الترخيصُ وصلًا**، لكلّ قائمة خانات. -/
theorem continueB_eq_accC (k : List K) : continueB k = accC .start k := by
  induction k using (measure List.length).wf.induction with
  | h k ih =>
    match k with
    | [] => rw [continueB_nil]; rfl
    | v :: t => rw [continueB_cons_noncv v t (by decide)]; simp [accC, δC, δ, accC_dead]
    | c :: t => rw [continueB_cons_noncv c t (by decide)]; simp [accC, δC, δ, accC_dead]
    | cv :: t =>
      have hlt : (Stages.run t).2.length < (cv :: t).length := by
        have := run_length t; simp; omega
      have ih' := ih _ hlt
      have ht : t = (Stages.run t).1 ++ (Stages.run t).2 := (run_append t).symm
      rw [continueB_cons_cv]
      show _ = accC .n t
      rw [ht, accC_coda (cv_not_mem_run t) (startsCV_run t), ← ht, ← ih']

/-! ## العدّ -/

def cntC (s : St) (n : Nat) : Nat := ((kseqs n).filter (accC s)).length

theorem filterC_cons (s : St) (x : K) (l : List (List K)) :
    ((l.map (x :: ·)).filter (accC s)).length = (l.filter (accC (δC s x))).length := by
  rw [List.filter_map, List.length_map]; rfl

theorem cntC_succ_succ (s : St) (n : Nat) :
    cntC s (n + 2) = cntC (δC s cv) n + cntC (δC s v) (n + 1) + cntC (δC s c) (n + 1) := by
  unfold cntC
  simp only [kseqs, List.filter_append, List.length_append, filterC_cons]

theorem cntC_dead : ∀ n, cntC .dead n = 0
  | 0 => rfl
  | 1 => rfl
  | n + 2 => by rw [cntC_succ_succ]; simp [δC, δ, cntC_dead n, cntC_dead (n + 1)]

theorem cntC_nc (n : Nat) : cntC .nc (n + 2) = cntC .n n := by
  rw [cntC_succ_succ]; simp [δC, δ, cntC_dead]

theorem cntC_nvc (n : Nat) : cntC .nvc (n + 2) = cntC .n n := by
  rw [cntC_succ_succ]; simp [δC, δ, cntC_dead]

theorem cntC_nv (n : Nat) : cntC .nv (n + 2) = cntC .n n + cntC .nvc (n + 1) := by
  rw [cntC_succ_succ]; simp [δC, δ, cntC_dead]

/-- التكرار: ‎a(m+4) = a(m+2) + 2·a(m+1) + a(m)‎ (من حالة «بعد متحرّك»). -/
theorem cntC_n_rec (m : Nat) :
    cntC .n (m + 4) = cntC .n (m + 2) + 2 * cntC .n (m + 1) + cntC .n m := by
  have e : cntC .n (m + 4) = cntC .n (m + 2) + cntC .nv (m + 3) + cntC .nc (m + 3) := by
    have := cntC_succ_succ .n (m + 2); simpa [δC, δ] using this
  rw [e, cntC_nv (m + 1), cntC_nvc m, cntC_nc (m + 1)]
  omega

/-- الشكلُ المغلق من حالة «بعد متحرّك»: ‎2·cntC .n m + [m%3=2] = fib (m+3) + [m%3=1]‎. -/
theorem cntC_n_closed : ∀ m, 2 * cntC .n m + (if m % 3 = 2 then 1 else 0)
    = fib (m + 3) + (if m % 3 = 1 then 1 else 0)
  | 0 => by decide
  | 1 => by decide
  | 2 => by decide
  | 3 => by decide
  | m + 4 => by
    have h0 := cntC_n_closed m
    have h1 := cntC_n_closed (m + 1)
    have h2 := cntC_n_closed (m + 2)
    have r := cntC_n_rec m
    have f5 : fib (m + 5) = fib (m + 3) + fib (m + 4) := rfl
    have f6 : fib (m + 6) = fib (m + 4) + fib (m + 5) := rfl
    have f7 : fib (m + 4 + 3) = fib (m + 5) + fib (m + 6) := rfl
    rw [f7]
    simp only [show m + 1 + 3 = m + 4 from rfl, show m + 2 + 3 = m + 5 from rfl] at h1 h2
    split <;> split <;> split at h0 <;> split at h0 <;> split at h1 <;> split at h1 <;>
      split at h2 <;> split at h2 <;> omega

theorem cntC_start (n : Nat) : cntC .start (n + 2) = cntC .n n := by
  rw [cntC_succ_succ]; simp [δC, δ, cntC_dead]

/-- **المبرهنة:** من كلّ قوائم الخانات بوزن `n`، المرخَّصةُ وصلًا عددُها ‎a‎ حيث
‎2·a + [n%3=1] = fib (n+1) + [n%3=0]‎ — لكلّ `n` (والوزنان 0 و1: ‎a = 1، 0‎). -/
theorem continue_count_closed (n : Nat) :
    2 * ((kseqs n).filter continueB).length + (if n % 3 = 1 then 1 else 0)
      = fib (n + 1) + (if n % 3 = 0 then 1 else 0) := by
  have e : (kseqs n).filter continueB = (kseqs n).filter (accC .start) := by
    congr 1; funext k; exact continueB_eq_accC k
  rw [e]
  match n with
  | 0 => decide
  | 1 => decide
  | m + 2 =>
    show 2 * cntC .start (m + 2) + _ = _
    rw [cntC_start]
    have h := cntC_n_closed m
    simp only [show m + 2 + 1 = m + 3 from rfl]
    split <;> split <;> split at h <;> split at h <;> omega

/-- **الشكلُ المغلق بالصحاح** (ADR ١٢): ‎a(n) = (fib(n+1) + [n≡0] − [n≡1]) / 2‎ مضروبًا في 2 — نتيجةٌ
مباشرةٌ لـ`continue_count_closed`. والوحدة: متتالياتُ أصنافٍ بالوزن، لا سلاسلُ غلاف. -/
theorem continue_count_closed_form (n : Nat) :
    (2 : Int) * ((kseqs n).filter continueB).length
      = (fib (n + 1) : Int) + (if n % 3 = 0 then 1 else 0) - (if n % 3 = 1 then 1 else 0) := by
  have h := continue_count_closed n
  have hr : n % 3 = 0 ∨ n % 3 = 1 ∨ n % 3 = 2 := by omega
  rcases hr with hr | hr | hr <;> simp [hr] at h ⊢ <;> omega

/-- الوقفُ هو الوصلُ ومقطعٌ طرفيٌّ CVCC أو CVVCC: ‎fib (m+5) = a(m+5) + a(m+1) + a(m)‎. -/
theorem pause_eq_continue_add (m : Nat) :
    ((kseqs (m + 5)).filter pauseB).length
      = ((kseqs (m + 5)).filter continueB).length + ((kseqs (m + 1)).filter continueB).length
        + ((kseqs m).filter continueB).length := by
  have a := continue_count_closed (m + 5)
  have b := continue_count_closed (m + 1)
  have c0 := continue_count_closed m
  rw [pause_count_fib (m + 5) (by omega)]
  have f6 : fib (m + 6) = fib (m + 4) + fib (m + 5) := rfl
  have f5 : fib (m + 5) = fib (m + 3) + fib (m + 4) := rfl
  have f4 : fib (m + 4) = fib (m + 2) + fib (m + 3) := rfl
  have f3 : fib (m + 3) = fib (m + 1) + fib (m + 2) := rfl
  simp only [show m + 5 + 1 = m + 6 from rfl, show m + 1 + 1 = m + 2 from rfl] at a b
  split at a <;> split at a <;> split at b <;> split at b <;> split at c0 <;> split at c0 <;> omega

/-- الأطوالُ 2..12 وصلًا مجموعُها 304 (والوقفُ 375). -/
theorem continue_count_304 :
    ((List.range 11).map (fun i => ((kseqs (i + 2)).filter continueB).length)).sum = 304 := by
  simp only [List.range, List.range.loop, List.map, List.sum_cons, List.sum_nil]
  have e2 : ((kseqs 2).filter continueB).length = 1 := by
    have h := continue_count_closed 2; simp [fib] at h; omega
  have e3 : ((kseqs 3).filter continueB).length = 2 := by
    have h := continue_count_closed 3; simp [fib] at h; omega
  have e4 : ((kseqs 4).filter continueB).length = 2 := by
    have h := continue_count_closed 4; simp [fib] at h; omega
  have e5 : ((kseqs 5).filter continueB).length = 4 := by
    have h := continue_count_closed 5; simp [fib] at h; omega
  have e6 : ((kseqs 6).filter continueB).length = 7 := by
    have h := continue_count_closed 6; simp [fib] at h; omega
  have e7 : ((kseqs 7).filter continueB).length = 10 := by
    have h := continue_count_closed 7; simp [fib] at h; omega
  have e8 : ((kseqs 8).filter continueB).length = 17 := by
    have h := continue_count_closed 8; simp [fib] at h; omega
  have e9 : ((kseqs 9).filter continueB).length = 28 := by
    have h := continue_count_closed 9; simp [fib] at h; omega
  have e10 : ((kseqs 10).filter continueB).length = 44 := by
    have h := continue_count_closed 10; simp [fib] at h; omega
  have e11 : ((kseqs 11).filter continueB).length = 72 := by
    have h := continue_count_closed 11; simp [fib] at h; omega
  have e12 : ((kseqs 12).filter continueB).length = 117 := by
    have h := continue_count_closed 12; simp [fib] at h; omega
  rw [e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12]
  rfl

end A116.Ternary
