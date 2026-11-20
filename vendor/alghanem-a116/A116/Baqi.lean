import A116.Bawwabat

/-!
# المتبقّي: «لا حكم» إسقاطٌ من حسابٍ أغنى يحمل المطلوبَ بأسمائه وبدائله (ADR ١٢٢)

رفع المالك (2026-10-21 21:25) تحليلًا من غيره أوّلُه: «الحل هو أن نجعل «الحكم» إسقاطًا من حساب أغنى يحتفظ بالمتطلبات وأدلتها
وبدائل استكمالها.» وهنا يُكتب ذلك على قيم `Bawwabat` الثلاث (‎some true‎ مستوفًى، ‎some false‎ ممتنع، ‎none‎ لا حكم) وجدولَيها
`wa`/`aw` بأعيانهما، لا على `Phi` في Mashru (منفصلٌ، لا يُستورد منه).

* **الصيغة** `Sigha`: ثابتٌ، ممتنعٌ، ذرّةٌ مسمّاة برقمها، واقترانٌ وفصل. والأدلّةُ ‎e : ℕ → Q‎ قيمةٌ لكلّ ذرّة.
* **الحكم** `qima e f`: تقييمٌ ثلاثيٌّ بجدولَي `Bawwabat`.
* **الاستكمال** `takmil e T`: إثباتُ الذرّات المجهولة في ‎T‎ وحدَها؛ ولا يغيّر دليلًا قائمًا (`takmil_thabit`).
* **المطلوب** `matlub e f`: عائلةُ مجموعاتٍ كلٌّ منها خطّةُ استكمالٍ كافية، و`adna` يُبقي الدنيا منها بالاحتواء.

## ما يُبرهن لكلّ صيغةٍ ولكلّ أدلّة

* `kifaya` / `kifaya_adna`: كلُّ مجموعةٍ في المطلوب (والأدنى) تكفي.
* `shumul` / `shumul_adna`: كلُّ استكمالٍ ناجحٍ يحتوي مجموعةً من المطلوب (والأدنى).
* `adna_la_asghar`: لا مجموعةَ كافيةً أصغرُ بالاحتواء من مجموعةٍ في المطلوب الأدنى.
* `isqat` / `isqat_adna`: **إسقاطُ المطلوب (والأدنى) إلى الحكم هو الحكمُ نفسُه** — ‎[] ∈ M‎ مستوفًى، و‎M = []‎ ممتنع، وإلّا
  لا حكم؛ فالاقترانُ والفصل على العائلات يُسقطان على `wa` و`aw` (`isqat_wa`، `isqat_aw`).

## ولكلّ ‎k‎ على أدلّةٍ مجهولة، ولكلّ زوجَي دعم

* `adad_badail`: ‎(A₁∨B₁)∧…∧(A_k∨B_k)‎ تعطي ‎2^k‎ خطّةً قبل التدنية.
* `wa4_muttasiq`: الاقترانُ على زوج الدعم المتّسق يُسقط على `wa`.

## وعلى الشاهد

* `la_ism_min_U`: صيغتان بحكم «لا حكم» نفسِه ومطلوبين مختلفين؛ فاسمُ المطلوب لا يُستردّ من الحكم وحدَه.
* `taarud_la_yusqat`: تحويلُ تعارض الدليلين إلى «لا حكم» قبل الاقتران يغيّر الحكمَ في هذا الشاهد؛ فالتعارضُ يُرفض قبل الحكم
  (`TawrithBit.wahhid`) ولا يُسقط عليه.

الحدّ (معلن): الذرّاتُ مستقلّةٌ هنا، والصيغةُ موجبة (لا نفيَ داخلها)، والاستكمالُ إثباتٌ لا نفي؛ والذرّةُ رقمٌ لا قضيّةٌ بحججها
وسياقها؛ ولا قاعدةَ لغويّةَ مودَعة تُبنى عليها هنا.
-/

set_option autoImplicit false

namespace A116.Baqi

open A116.Bawwabat

/-! ## ١. الجدولان: ما يلزم منهما -/

theorem wa_true (x y : Q) : wa x y = some true ↔ x = some true ∧ y = some true := by
  rcases x with _ | _ | _ <;> rcases y with _ | _ | _ <;> simp [wa]

theorem wa_false (x y : Q) : wa x y = some false ↔ x = some false ∨ y = some false := by
  rcases x with _ | _ | _ <;> rcases y with _ | _ | _ <;> simp [wa]

theorem aw_true (x y : Q) : aw x y = some true ↔ x = some true ∨ y = some true := by
  rcases x with _ | _ | _ <;> rcases y with _ | _ | _ <;> simp [aw]

theorem aw_false (x y : Q) : aw x y = some false ↔ x = some false ∧ y = some false := by
  rcases x with _ | _ | _ <;> rcases y with _ | _ | _ <;> simp [aw]

/-! ## ٢. الصيغةُ والحكمُ والاستكمال -/

inductive Sigha
  | thabit
  | mumtani
  | dharra (a : Nat)
  | wa (p q : Sigha)
  | aw (p q : Sigha)
  deriving DecidableEq, Repr

def qima (e : Nat → Q) : Sigha → Q
  | .thabit => some true
  | .mumtani => some false
  | .dharra a => e a
  | .wa p q => Bawwabat.wa (qima e p) (qima e q)
  | .aw p q => Bawwabat.aw (qima e p) (qima e q)

/-- إثباتُ ما في ‎T‎ من المجهول وحدَه. -/
def takmil (e : Nat → Q) (T : List Nat) (a : Nat) : Q :=
  match e a with
  | none => if a ∈ T then some true else none
  | some b => some b

/-- **لا يُخترع دليلٌ ولا يُبدَّل:** ما كان معلومًا بقي بعينه. -/
theorem takmil_thabit (e : Nat → Q) (T : List Nat) (a : Nat) (b : Bool) (h : e a = some b) :
    takmil e T a = some b := by
  simp [takmil, h]

theorem takmil_nil (e : Nat → Q) : takmil e [] = e := by
  funext a; unfold takmil; cases e a <;> simp

/-- الاحتواء. -/
def Sub (S T : List Nat) : Prop := ∀ a ∈ S, a ∈ T

/-- كافيةٌ: استكمالُها يستوفي الصيغة. -/
def Kafiya (e : Nat → Q) (f : Sigha) (T : List Nat) : Prop := qima (takmil e T) f = some true

/-! ## ٣. المطلوب -/

/-- اتّحادٌ بلا تكرار ما في الأوّل. -/
def ittihad (X Y : List Nat) : List Nat := X ++ Y.filter (fun a => decide (a ∉ X))

theorem sub_ittihad (X Y T : List Nat) : Sub (ittihad X Y) T ↔ Sub X T ∧ Sub Y T := by
  unfold Sub ittihad
  constructor
  · intro h
    refine ⟨fun a ha => h a (List.mem_append_left _ ha), fun a ha => ?_⟩
    by_cases hx : a ∈ X
    · exact h a (List.mem_append_left _ hx)
    · exact h a (List.mem_append_right _ (List.mem_filter.2 ⟨ha, by simp [hx]⟩))
  · rintro ⟨h1, h2⟩ a ha
    rcases List.mem_append.1 ha with ha | ha
    · exact h1 a ha
    · exact h2 a (List.mem_filter.1 ha).1

theorem ittihad_nil (X Y : List Nat) : ittihad X Y = [] ↔ X = [] ∧ Y = [] := by
  unfold ittihad
  constructor
  · intro h
    have hx : X = [] := (List.append_eq_nil_iff.1 h).1
    subst hx
    have h2 := (List.append_eq_nil_iff.1 h).2
    simp only [List.filter_eq_nil_iff, List.not_mem_nil, not_false_eq_true, decide_true] at h2
    exact ⟨rfl, List.eq_nil_iff_forall_not_mem.2 (fun a ha => by simpa using h2 a ha)⟩
  · rintro ⟨rfl, rfl⟩; rfl

def matlub (e : Nat → Q) : Sigha → List (List Nat)
  | .thabit => [[]]
  | .mumtani => []
  | .dharra a =>
    match e a with
    | some true => [[]]
    | some false => []
    | none => [[a]]
  | .wa p q => (matlub e p).flatMap (fun X => (matlub e q).map (ittihad X))
  | .aw p q => matlub e p ++ matlub e q

theorem mem_wa (e : Nat → Q) (p q : Sigha) (S : List Nat) :
    S ∈ matlub e (.wa p q) ↔ ∃ X ∈ matlub e p, ∃ Y ∈ matlub e q, ittihad X Y = S := by
  simp [matlub, List.mem_flatMap, List.mem_map]

/-- **الكفاية:** كلُّ خطّةٍ في المطلوب تكفي، وكلُّ ما يحتويها. -/
theorem kifaya (e : Nat → Q) : ∀ (f : Sigha) (S : List Nat), S ∈ matlub e f →
    ∀ T, Sub S T → Kafiya e f T
  | .thabit, _, _, _, _ => rfl
  | .mumtani, _, h, _, _ => by simp [matlub] at h
  | .dharra a, S, h, T, hT => by
    unfold Kafiya qima takmil
    unfold matlub at h
    cases ha : e a with
    | none =>
      rw [ha] at h
      simp only [List.mem_singleton] at h
      subst h
      simp [hT a (List.mem_singleton_self a)]
    | some b =>
      cases b with
      | true => rfl
      | false => rw [ha] at h; simp at h
  | .wa p q, S, h, T, hT => by
    obtain ⟨X, hX, Y, hY, rfl⟩ := (mem_wa e p q S).1 h
    have ⟨h1, h2⟩ := (sub_ittihad X Y T).1 hT
    unfold Kafiya qima
    exact (wa_true _ _).2 ⟨kifaya e p X hX T h1, kifaya e q Y hY T h2⟩
  | .aw p q, S, h, T, hT => by
    unfold Kafiya qima
    rcases List.mem_append.1 h with h | h
    · exact (aw_true _ _).2 (Or.inl (kifaya e p S h T hT))
    · exact (aw_true _ _).2 (Or.inr (kifaya e q S h T hT))

/-- **الشمول:** كلُّ استكمالٍ ناجحٍ يحتوي خطّةً من المطلوب. -/
theorem shumul (e : Nat → Q) : ∀ (f : Sigha) (T : List Nat), Kafiya e f T →
    ∃ S ∈ matlub e f, Sub S T
  | .thabit, _, _ => ⟨[], by simp [matlub], fun _ h => by simp at h⟩
  | .mumtani, _, h => by simp [Kafiya, qima] at h
  | .dharra a, T, h => by
    unfold Kafiya qima takmil at h
    unfold matlub
    cases ha : e a with
    | none =>
      rw [ha] at h
      by_cases hm : a ∈ T
      · exact ⟨[a], by simp, fun x hx => by simp at hx; subst hx; exact hm⟩
      · simp [hm] at h
    | some b =>
      rw [ha] at h
      cases b with
      | true => exact ⟨[], by simp, fun _ h => by simp at h⟩
      | false => simp at h
  | .wa p q, T, h => by
    unfold Kafiya qima at h
    obtain ⟨h1, h2⟩ := (wa_true _ _).1 h
    obtain ⟨X, hX, sX⟩ := shumul e p T h1
    obtain ⟨Y, hY, sY⟩ := shumul e q T h2
    exact ⟨ittihad X Y, (mem_wa e p q _).2 ⟨X, hX, Y, hY, rfl⟩, (sub_ittihad X Y T).2 ⟨sX, sY⟩⟩
  | .aw p q, T, h => by
    unfold Kafiya qima at h
    rcases (aw_true _ _).1 h with h | h
    · obtain ⟨S, hS, sS⟩ := shumul e p T h
      exact ⟨S, List.mem_append_left _ hS, sS⟩
    · obtain ⟨S, hS, sS⟩ := shumul e q T h
      exact ⟨S, List.mem_append_right _ hS, sS⟩

/-! ## ٤. الإسقاطُ إلى الحكم -/

/-- **الاستيفاء:** الخطّةُ الفارغة في المطلوب ⟺ الحكمُ مستوفًى. -/
theorem istifa (e : Nat → Q) (f : Sigha) : [] ∈ matlub e f ↔ qima e f = some true := by
  constructor
  · intro h
    have := kifaya e f [] h [] (fun _ h => h)
    rwa [Kafiya, takmil_nil] at this
  · intro h
    obtain ⟨S, hS, sS⟩ := shumul e f [] (by rw [Kafiya, takmil_nil]; exact h)
    have : S = [] := by
      cases S with
      | nil => rfl
      | cons x xs => exact absurd (sS x (List.mem_cons_self ..)) (by simp)
    exact this ▸ hS

/-- **الامتناع:** لا خطّةَ ⟺ الحكمُ ممتنع. -/
theorem imtina (e : Nat → Q) : ∀ f : Sigha, matlub e f = [] ↔ qima e f = some false
  | .thabit => by simp [matlub, qima]
  | .mumtani => by simp [matlub, qima]
  | .dharra a => by
    unfold matlub qima
    cases ha : e a with
    | none => simp
    | some b => cases b <;> simp
  | .wa p q => by
    unfold qima
    rw [wa_false, ← imtina e p, ← imtina e q]
    show (matlub e p).flatMap (fun X => (matlub e q).map (ittihad X)) = [] ↔ _
    rw [List.flatMap_eq_nil_iff]
    constructor
    · intro h
      cases hp : matlub e p with
      | nil => exact Or.inl rfl
      | cons X xs =>
        right
        have := h X (by rw [hp]; exact List.mem_cons_self ..)
        simpa using this
    · rintro (h | h) X hX
      · rw [h] at hX; simp at hX
      · simp [h]
  | .aw p q => by
    show matlub e p ++ matlub e q = [] ↔ _
    unfold qima
    rw [aw_false, ← imtina e p, ← imtina e q, List.append_eq_nil_iff]

/-- الإسقاط: ‎[] ∈ M‎ مستوفًى، و‎M = []‎ ممتنع، وإلّا لا حكم. -/
def hukm (M : List (List Nat)) : Q :=
  if [] ∈ M then some true else if M = [] then some false else none

/-- **الحسابُ الأغنى يُسقط على الحكم بعينه.** -/
theorem isqat (e : Nat → Q) (f : Sigha) : hukm (matlub e f) = qima e f := by
  unfold hukm
  by_cases h1 : [] ∈ matlub e f
  · simp only [h1, ↓reduceIte, (istifa e f).1 h1]
  · simp only [h1, ↓reduceIte]
    by_cases h2 : matlub e f = []
    · simp only [h2, ↓reduceIte, (imtina e f).1 h2]
    · simp only [h2, ↓reduceIte]
      have a := mt (istifa e f).2 h1
      have b := mt (imtina e f).2 h2
      revert a b
      cases qima e f with
      | none => intros; rfl
      | some v => cases v <;> simp

/-- الاقترانُ على العائلات يُسقط على `wa`. -/
theorem isqat_wa (e : Nat → Q) (p q : Sigha) :
    hukm (matlub e (.wa p q)) = Bawwabat.wa (hukm (matlub e p)) (hukm (matlub e q)) := by
  rw [isqat, isqat, isqat]; rfl

/-- والفصلُ على `aw`. -/
theorem isqat_aw (e : Nat → Q) (p q : Sigha) :
    hukm (matlub e (.aw p q)) = Bawwabat.aw (hukm (matlub e p)) (hukm (matlub e q)) := by
  rw [isqat, isqat, isqat]; rfl

/-! ## ٥. التدنيةُ بالاحتواء -/

def subB (S T : List Nat) : Bool := S.all (fun a => decide (a ∈ T))

theorem subB_iff (S T : List Nat) : subB S T = true ↔ Sub S T := by
  simp [subB, Sub, List.all_eq_true]

/-- يُبقي من ‎M‎ ما لا يحتوي عنصرًا منها احتواءً تامًّا. -/
def adna (M : List (List Nat)) : List (List Nat) :=
  M.filter (fun S => !M.any (fun T => subB T S && !subB S T))

theorem adna_sub {M : List (List Nat)} {S : List Nat} (h : S ∈ adna M) : S ∈ M :=
  (List.mem_filter.1 h).1

theorem adna_min {M : List (List Nat)} {S T : List Nat} (h : S ∈ adna M) (hT : T ∈ M)
    (hTS : Sub T S) : Sub S T := by
  have h2 := (List.mem_filter.1 h).2
  simp only [Bool.not_eq_true', List.any_eq_false, Bool.and_eq_true, Bool.not_eq_true'] at h2
  have := h2 T hT
  rw [← subB_iff] at hTS ⊢
  cases hs : subB S T
  · exact absurd ⟨hTS, hs⟩ this
  · rfl

theorem countP_lt {α : Type} (p q : α → Bool) :
    ∀ l : List α, (∀ x ∈ l, p x = true → q x = true) → (∃ x ∈ l, q x = true ∧ p x = false) →
      l.countP p < l.countP q
  | [], _, ⟨_, h, _⟩ => by simp at h
  | y :: ys, hpq, ⟨x, hx, hq, hp⟩ => by
    have hle : ys.countP p ≤ ys.countP q :=
      List.countP_mono_left (fun z hz => hpq z (List.mem_cons_of_mem _ hz))
    rcases List.mem_cons.1 hx with rfl | hx
    · simp [hp, hq]; omega
    · have ih := countP_lt p q ys (fun z hz => hpq z (List.mem_cons_of_mem _ hz)) ⟨x, hx, hq, hp⟩
      simp only [List.countP_cons]
      cases hpy : p y
      · cases q y <;> simp <;> omega
      · simp [hpq y (List.mem_cons_self ..) hpy]; omega

theorem sub_trans {A B C : List Nat} (h1 : Sub A B) (h2 : Sub B C) : Sub A C :=
  fun a ha => h2 a (h1 a ha)

/-- **التدنيةُ لا تُفقد خطّة:** كلُّ عنصرٍ في ‎M‎ يحتوي عنصرًا في `adna M`. -/
theorem adna_ghita (M : List (List Nat)) :
    ∀ n (S : List Nat), M.countP (fun T => subB T S) = n → S ∈ M → ∃ T ∈ adna M, Sub T S := by
  intro n
  induction n using Nat.strongRecOn with
  | ind n ih =>
    intro S hn hS
    by_cases hm : S ∈ adna M
    · exact ⟨S, hm, fun _ h => h⟩
    · have : M.any (fun T => subB T S && !subB S T) = true := by
        have := mt (fun h => List.mem_filter.2 ⟨hS, h⟩) hm
        simpa using this
      obtain ⟨T, hT, hTS⟩ := List.any_eq_true.1 this
      simp only [Bool.and_eq_true, Bool.not_eq_true'] at hTS
      obtain ⟨hTS, hST⟩ := hTS
      have hlt : M.countP (fun U => subB U T) < M.countP (fun U => subB U S) :=
        countP_lt _ _ M
          (fun U _ hU => (subB_iff U S).2 (sub_trans ((subB_iff U T).1 hU) ((subB_iff T S).1 hTS)))
          ⟨S, hS, (subB_iff S S).2 (fun _ h => h), hST⟩
      obtain ⟨V, hV, hVT⟩ := ih _ (hn ▸ hlt) T rfl hT
      exact ⟨V, hV, sub_trans hVT ((subB_iff T S).1 hTS)⟩

/-- المطلوبُ الأدنى. -/
def matlubAdna (e : Nat → Q) (f : Sigha) : List (List Nat) := adna (matlub e f)

theorem kifaya_adna (e : Nat → Q) (f : Sigha) (S : List Nat) (h : S ∈ matlubAdna e f) :
    Kafiya e f S :=
  kifaya e f S (adna_sub h) S (fun _ h => h)

theorem shumul_adna (e : Nat → Q) (f : Sigha) (T : List Nat) (h : Kafiya e f T) :
    ∃ S ∈ matlubAdna e f, Sub S T := by
  obtain ⟨S, hS, sS⟩ := shumul e f T h
  obtain ⟨V, hV, sV⟩ := adna_ghita _ _ S rfl hS
  exact ⟨V, hV, sub_trans sV sS⟩

/-- التدنيةُ لا تغيّر الإسقاط، لكلّ عائلة. -/
theorem hukm_adna (M : List (List Nat)) : hukm (adna M) = hukm M := by
  have e1 : [] ∈ adna M ↔ [] ∈ M := by
    constructor
    · exact adna_sub
    · intro h
      obtain ⟨T, hT, sT⟩ := adna_ghita M _ [] rfl h
      have : T = [] := by
        cases T with
        | nil => rfl
        | cons x xs => exact absurd (sT x (List.mem_cons_self ..)) (by simp)
      exact this ▸ hT
  have e2 : adna M = [] ↔ M = [] := by
    constructor
    · intro h
      cases hM : M with
      | nil => rfl
      | cons S xs =>
        obtain ⟨T, hT, _⟩ := adna_ghita M _ S rfl (by rw [hM]; exact List.mem_cons_self ..)
        rw [h] at hT; simp at hT
    · intro h; subst h; rfl
  unfold hukm
  by_cases h1 : [] ∈ M
  · simp only [h1, e1.2 h1, ↓reduceIte]
  · have h1' : ¬ [] ∈ adna M := fun h => h1 (e1.1 h)
    by_cases h2 : M = []
    · subst h2; rfl
    · have h2' : ¬ adna M = [] := fun h => h2 (e2.1 h)
      simp only [h1, h1', h2, h2', ↓reduceIte]

/-- **وإسقاطُ المطلوب الأدنى هو الحكمُ نفسُه.** -/
theorem isqat_adna (e : Nat → Q) (f : Sigha) : hukm (matlubAdna e f) = qima e f := by
  rw [matlubAdna, hukm_adna, isqat]

/-- **لا أصغرَ كافٍ:** كلُّ كافيةٍ تحت خطّةٍ دنيا تحتويها. -/
theorem adna_la_asghar (e : Nat → Q) (f : Sigha) (S T : List Nat) (hS : S ∈ matlubAdna e f)
    (hT : Kafiya e f T) (hTS : Sub T S) : Sub S T := by
  obtain ⟨S', hS', sS'⟩ := shumul e f T hT
  have := adna_min hS hS' (sub_trans sS' hTS)
  exact sub_trans this sS'

/-! ## ٦. ما يُفقد بالإسقاط، وعددُ البدائل، والتعارض -/

/-- **«لا حكم» لا يحمل اسمَ المطلوب.** -/
theorem la_ism_min_U :
    qima (fun _ => none) (.dharra 0) = qima (fun _ => none) (.dharra 1) ∧
      matlub (fun _ => none) (.dharra 0) ≠ matlub (fun _ => none) (.dharra 1) := by
  decide

theorem length_wa (e : Nat → Q) (p q : Sigha) :
    (matlub e (.wa p q)).length = (matlub e p).length * (matlub e q).length := by
  show ((matlub e p).flatMap (fun X => (matlub e q).map (ittihad X))).length = _
  induction matlub e p with
  | nil => simp
  | cons X xs ih => simp [List.flatMap_cons, ih, Nat.succ_mul, Nat.add_comm]

/-- ‎(A₁∨B₁)∧…∧(A_k∨B_k)‎ بذرّاتٍ ‎2i‎ و‎2i+1‎. -/
def badail : Nat → Sigha
  | 0 => .thabit
  | k + 1 => .wa (badail k) (.aw (.dharra (2 * k)) (.dharra (2 * k + 1)))

/-- **البدائلُ أُسّيّة:** ‎2^k‎ خطّةً على أدلّةٍ مجهولة، لكلّ ‎k‎. -/
theorem adad_badail : ∀ k, (matlub (fun _ => none) (badail k)).length = 2 ^ k
  | 0 => rfl
  | k + 1 => by
    rw [badail, length_wa, adad_badail k, Nat.pow_succ]
    rfl

/-- الشاهد: ‎C ∧ (A ∨ B)‎ و‎C‎ ثابتٌ — بديلان لا قائمةٌ واحدة؛ و‎(A ∨ B) ∧ (A ∨ C)‎ أدناه ‎{A}، {B, C}‎. -/
theorem shahid_badail :
    matlubAdna (fun a => if a = 2 then some true else none)
      (.wa (.dharra 2) (.aw (.dharra 0) (.dharra 1))) = [[0], [1]] ∧
    matlubAdna (fun _ => none) (.wa (.aw (.dharra 0) (.dharra 1)) (.aw (.dharra 0) (.dharra 2)))
      = [[0], [1, 2]] := by
  decide

/-- الدعمُ زوجًا (موجب، سالب) واقترانُه. -/
def wa4 (x y : Bool × Bool) : Bool × Bool := (x.1 && y.1, x.2 || y.2)

def ilaQ : Bool × Bool → Q
  | (true, false) => some true
  | (false, true) => some false
  | _ => none

/-- **التعارضُ لا يُسقط على «لا حكم»:** ‎(1,1) ∧ (0,0) = (0,1)‎ ممتنع، وإسقاطُ التعارض قبل الاقتران يعطي «لا حكم». -/
theorem taarud_la_yusqat :
    ilaQ (wa4 (true, true) (false, false)) = some false ∧
      Bawwabat.wa (ilaQ (true, true)) (ilaQ (false, false)) = none := by
  decide

/-- وعلى الدعم المتّسق (لا زوجَ ‎(1,1)‎) الاقترانُ الرباعيّ يُسقط على `wa`. -/
theorem wa4_muttasiq (x y : Bool × Bool) (hx : x ≠ (true, true)) (hy : y ≠ (true, true)) :
    ilaQ (wa4 x y) = Bawwabat.wa (ilaQ x) (ilaQ y) := by
  obtain ⟨a, b⟩ := x; obtain ⟨c, d⟩ := y
  cases a <;> cases b <;> cases c <;> cases d <;> simp_all [wa4, ilaQ, Bawwabat.wa]

end A116.Baqi
