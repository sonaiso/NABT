import A116.Stages
import A116.Ladder

/-!
# الترخيصُ الثلاثيّ: CV · V · C بدل M · S

النموذجُ الثنائيُّ المعلن (`Admissible`) لا يرى إلّا متحرّكًا (M) أو ساكنًا (S)، فالمدُّ
والإغلاقُ عنده نمطٌ واحد (MS)، ويمنع ساكنين متجاورين في كلّ موضع. فيرفض ما هو عربيٌّ
صحيح: «حَاجَّ» (`حَ اْ جْ جَ`) مدٌّ قبل مضعَّف، و«بَحْرْ» وقفًا. وقد ثبت ذلك على نصٍّ
مشكولٍ خارجَ القرآن (`corpora/tashkeela-fadel-test.txt`).

والترخيصُ الثلاثيُّ يُبنى على التقطيع المبرهَن في `Stages` (وحيدٌ ومعكوسُه الوصل):

* `ContinueLicensed k`: تُقطَّع بلا قطعةٍ صادرة، ولا CVCC ولا CVVCC في مقاطعها.
* `PauseLicensed k`: كذلك، إلّا أنّ المقطعَ الأخيرَ وحدَه يجوز أن يكون CVCC أو CVVCC
  (بَحْرْ، تَامّْ).

## المبرهنات

* `binary_is_continue`: كلُّ ما يقبله النموذجُ الثنائيّ (بإسقاط V وC على S) يقبله
  الوصلُ الثلاثيّ، ومقاطعُه من CV وCVV وCVC وحدها.
* `continue_strictly_extends_binary`: «حَاجَّ» (CVVC + CV) مرخَّصةٌ وصلًا ومرفوضةٌ ثنائيًّا.
* `continue_is_pause`: كلُّ مرخَّصٍ وصلًا مرخَّصٌ وقفًا.
* `pause_strictly_extends_continue`: «بَحْرْ» (CVCC) مرخَّصةٌ وقفًا لا وصلًا.
* `tamm_is_pause_only`: «تَامّْ» (CVVCC) مرخَّصةٌ وقفًا لا وصلًا.
* `admissible_iff_admissibleB` و`binOK_eq_admissibleB`: `binOK` هو `Admissible` نفسُه بعد
  الإسقاط — فالمبرهنةُ الأولى عن النموذج المبرهَن في `Model.lean` لا عن نسخةٍ منه.
* `binary_is_blind_to_madd`: «مَا» و«مِنْ» نمطٌ ثنائيٌّ واحد ومقطعان مختلفان (CVV ≠ CVC):
  البتُّ الذي يفتقده النموذجُ الثنائيّ.
-/

namespace A116.Ternary

open A116.Stages K

/-- المقطعُ الذي لا يقع إلّا طرفًا موقوفًا عليه: ساكنان بعد النواة. -/
def pauseOnly : Syl → Bool
  | .CVCC | .CVVCC => true
  | _ => false

def ContinueLicensed (k : List K) : Prop :=
  ∃ ss, parse k = some (.none, ss) ∧ ∀ s ∈ ss, pauseOnly s = false

def PauseLicensed (k : List K) : Prop :=
  ∃ ss, parse k = some (.none, ss) ∧ ∀ s ∈ ss.dropLast, pauseOnly s = false

/-- الإسقاطُ الثنائيّ: المتحرّكُ M (`true`)، والمدُّ والإغلاقُ كلاهما S (`false`). -/
def proj (k : List K) : List Bool := k.map (· == cv)

/-- لا غيرُ متحرّكَين متجاورين. -/
def noPair : List K → Bool
  | a :: b :: t => (a == cv || b == cv) && noPair (b :: t)
  | _ => true

/-- قبولُ النموذج الثنائيّ: يبدأ بمتحرّكٍ (أو فارغ)، ولا ساكنان متجاوران. -/
def binOK : List K → Bool
  | [] => true
  | a :: t => (a == cv) && noPair (a :: t)

/-- التقطيعُ الجشع على مقبول النموذج الثنائيّ. -/
def greedy : List K → List Syl
  | cv :: v :: t => .CVV :: greedy t
  | cv :: c :: t => .CVC :: greedy t
  | _ :: t => .CV :: greedy t
  | [] => []

def Small (s : Syl) : Prop := s = .CV ∨ s = .CVV ∨ s = .CVC

theorem greedy_spec : ∀ k : List K, binOK k = true →
    flat .none (greedy k) = k ∧ ∀ s ∈ greedy k, Small s
  | [] => fun _ => ⟨rfl, by simp [greedy]⟩
  | [a] => by
    intro h; cases a <;> simp_all [binOK, noPair, greedy, flat, Syl.atoms, Syl.coda,
      Lead.atoms, Small]
  | a :: b :: t => by
    intro h
    cases a <;> simp [binOK, noPair] at h
    cases b with
    | cv =>
      have ih := greedy_spec (cv :: t) (by simpa [binOK] using h)
      simp only [greedy]
      refine ⟨?_, ?_⟩
      · simpa [flat, Syl.atoms, Syl.coda, Lead.atoms] using ih.1
      · intro s hs; simp at hs; rcases hs with rfl | hs
        · left; rfl
        · exact ih.2 s hs
    | v =>
      cases t with
      | nil => simp [greedy, flat, Syl.atoms, Syl.coda, Lead.atoms, Small]
      | cons d t =>
        cases d <;> simp [noPair] at h
        have ih := greedy_spec (cv :: t) (by simpa [binOK] using h)
        simp only [greedy]
        refine ⟨?_, ?_⟩
        · simpa [flat, Syl.atoms, Syl.coda, Lead.atoms] using ih.1
        · intro s hs; simp at hs; rcases hs with rfl | hs
          · right; left; rfl
          · exact ih.2 s hs
    | c =>
      cases t with
      | nil => simp [greedy, flat, Syl.atoms, Syl.coda, Lead.atoms, Small]
      | cons d t =>
        cases d <;> simp [noPair] at h
        have ih := greedy_spec (cv :: t) (by simpa [binOK] using h)
        simp only [greedy]
        refine ⟨?_, ?_⟩
        · simpa [flat, Syl.atoms, Syl.coda, Lead.atoms] using ih.1
        · intro s hs; simp at hs; rcases hs with rfl | hs
          · right; right; rfl
          · exact ih.2 s hs

theorem binary_is_continue (k : List K) (h : binOK k = true) :
    ContinueLicensed k ∧ ∃ ss, parse k = some (.none, ss) ∧ ∀ s ∈ ss, Small s := by
  obtain ⟨hf, hs⟩ := greedy_spec k h
  have hp : parse k = some (.none, greedy k) := by
    conv => lhs; rw [← hf]
    exact parse_flat _ _
  refine ⟨⟨greedy k, hp, ?_⟩, greedy k, hp, hs⟩
  intro s hm
  rcases hs _ hm with h1 | h1 | h1 <;> subst h1 <;> rfl

/-- كلُّ تقطيعٍ لسلسلةٍ هو تقطيعُها الوحيد. -/
theorem parse_eq_of_flat {k : List K} {ss : List Syl} (h : flat .none ss = k)
    {l : Lead} {ss' : List Syl} (h' : parse k = some (l, ss')) : l = .none ∧ ss' = ss := by
  rw [← h, parse_flat] at h'
  simp at h'
  exact ⟨h'.1.symm, h'.2.symm⟩

def hajja : List K := [cv, v, c, cv]

theorem continue_strictly_extends_binary : ContinueLicensed hajja ∧ binOK hajja = false := by
  refine ⟨⟨[.CVVC, .CV], parse_flat .none [.CVVC, .CV], by decide⟩, rfl⟩

theorem continue_is_pause {k : List K} (h : ContinueLicensed k) : PauseLicensed k := by
  obtain ⟨ss, hp, hn⟩ := h
  exact ⟨ss, hp, fun s hm => hn s (List.dropLast_subset ss hm)⟩

def bahr : List K := [cv, c, c]

theorem pause_strictly_extends_continue : PauseLicensed bahr ∧ ¬ ContinueLicensed bahr := by
  refine ⟨⟨[.CVCC], parse_flat .none [.CVCC], by decide⟩, ?_⟩
  rintro ⟨ss, hp, hn⟩
  have := (parse_eq_of_flat (k := bahr) (ss := [.CVCC]) rfl hp).2
  subst this
  exact absurd (hn .CVCC (by decide)) (by decide)

def tamm : List K := [cv, v, c, c]

theorem tamm_is_pause_only : PauseLicensed tamm ∧ ¬ ContinueLicensed tamm := by
  refine ⟨⟨[.CVVCC], parse_flat .none [.CVVCC], by decide⟩, ?_⟩
  rintro ⟨ss, hp, hn⟩
  have := (parse_eq_of_flat (k := tamm) (ss := [.CVVCC]) rfl hp).2
  subst this
  exact absurd (hn .CVVCC (by decide)) (by decide)

def ma : List K := [cv, v]
def min : List K := [cv, c]

theorem binary_is_blind_to_madd :
    proj ma = proj min ∧ parse ma = some (.none, [.CVV]) ∧ parse min = some (.none, [.CVC]) :=
  ⟨rfl, parse_flat .none [.CVV], parse_flat .none [.CVC]⟩

/-! ## صيغتان قابلتان للحساب، تُطابَقان بالبايثون في CI -/

def continueB (k : List K) : Bool :=
  match parse k with
  | some (.none, ss) => ss.all fun s => !(pauseOnly s)
  | _ => false

def pauseB (k : List K) : Bool :=
  match parse k with
  | some (.none, ss) => ss.dropLast.all fun s => !(pauseOnly s)
  | _ => false

theorem continueB_iff (k : List K) : continueB k = true ↔ ContinueLicensed k := by
  unfold continueB ContinueLicensed
  split
  · rename_i ss h; simp [h]
  · rename_i h
    constructor
    · intro h'; cases h'
    · rintro ⟨ss, hp, _⟩; exact absurd hp (h ss)

theorem pauseB_iff (k : List K) : pauseB k = true ↔ PauseLicensed k := by
  unfold pauseB PauseLicensed
  split
  · rename_i ss h; simp [h]
  · rename_i h
    constructor
    · intro h'; cases h'
    · rintro ⟨ss, hp, _⟩; exact absurd hp (h ss)

/-! ## `binOK` هو `Admissible` بعد الإسقاط -/

open A116 A116.Ladder in
theorem noAdjacent_iff_noSS : ∀ w : List Cell,
    NoAdjacentSukun w ↔ admissibleB.noSS (pat w) = true
  | [] => by simp [NoAdjacentSukun, pat, admissibleB.noSS]
  | [a] => by simp [NoAdjacentSukun, pat, admissibleB.noSS]
  | a :: b :: t => by
    have ih := noAdjacent_iff_noSS (b :: t)
    simp only [pat, List.map_cons] at ih ⊢
    simp only [NoAdjacentSukun, admissibleB.noSS, Bool.and_eq_true, ih]
    cases a.isSukun <;> cases b.isSukun <;> simp

open A116 A116.Ladder in
theorem admissible_iff_admissibleB (w : List Cell) :
    Admissible w ↔ admissibleB (pat w) = true := by
  cases w with
  | nil => simp [Admissible, HeadNotSukun, NoAdjacentSukun, pat, admissibleB]
  | cons a t =>
    have := noAdjacent_iff_noSS (a :: t)
    simp only [pat, List.map_cons] at this ⊢
    simp only [Admissible, HeadNotSukun, admissibleB, Bool.and_eq_true, this]
    cases a.isSukun <;> simp

theorem noPair_eq_noSS : ∀ k : List K, noPair k = A116.Ladder.admissibleB.noSS (proj k)
  | [] => rfl
  | [a] => rfl
  | a :: b :: t => by
    have ih := noPair_eq_noSS (b :: t)
    simp only [proj, List.map_cons] at ih ⊢
    simp only [noPair, A116.Ladder.admissibleB.noSS, ih]

theorem binOK_eq_admissibleB (k : List K) : binOK k = A116.Ladder.admissibleB (proj k) := by
  cases k with
  | nil => rfl
  | cons a t =>
    have := noPair_eq_noSS (a :: t)
    simp only [proj, List.map_cons] at this ⊢
    simp only [binOK, A116.Ladder.admissibleB, this]

end A116.Ternary
