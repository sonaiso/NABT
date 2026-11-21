import A116.Qarar

/-!
# بوّابةُ المنهج: سلسلةُ القرار مبرهنةً على كلّ سلسلة (ADR ٥٨)

يبني على `A116.Qarar` ولا يغيّره. ثلاثةُ أمور:

1. **التسليمُ المبنيُّ على المحسوس** (ج1 س45: «أم واقعاً مسلَّماً به أنه موجود في الخارج، تسليماً مبنياً على واقع
   محسوس»؛ س86: «فإن دليله نقلي… متوقفاً على ثبوت كونه دليلاً بالدليل العقلي»؛ س87: «الإيمان بالملائكة دليله
   نقلي»). `Qarar.judge1` يطلب الحسَّ في كلّ دعوى، فيحكم على وجود الملائكة بـ«لا حكم» (`judge1_refuses_s87`).
   و`judgeT` يقبل دعوى لا يُحسّ واقعُها **إذا كان لها أصولٌ** وكانت صائبة؛ ويطابق `judge1` على كلّ محسوس
   (`judgeT_of_mahsus`) وعلى شاهدَي `Qarar` كلَّيهما (`qarar_witnesses_unchanged`).
2. **لا مدخلَ ثالث** (`roots_mahsus`): في كلّ سلسلة، كلُّ دعوى صائبة تنتهي أصولُها كلُّها — بأيّ طريق — إلى دعاوى
   محسوسة. فالمدخلُ النقليُّ المستقلّ (بلا حسٍّ ولا أصل) لا يكون صائبًا أبدًا.
3. **الأقفال مبرهنةً لكلّ سلسلة لا مفحوصةً على أمثلة:**
   * السقوطُ يسري (`closed_reach`): كلُّ ما تبلغه دعوى صائبة (أو قطعيّة) بالأصول صائبٌ (أو قطعيّ). فالحارسُ
     يكفيه أن يفحص حكمَ القرار الذي تعلنه الوحدة، لا شجرتَه.
   * الامتحانُ المضادّ (`monotone`): حذفُ سندٍ أو زرعُ معارضٍ في أيّ موضعٍ من أيّ سلسلة لا يرفع حكمًا في أيّ
     موضع: ما صار صائبًا كان صائبًا، وما صار قطعيًّا كان قطعيًّا.
   * الزرعُ يُسقط (`plant_khata`، `fallen_premise_saqit`): معارضٌ مودَعٌ على دعوى قائمةٍ يجعلها خاطئة، وما بُني عليها
     ساقط.

والحقولُ (الحسّ، المعارض، الوجود) مدخلٌ بعدُ (`QARAR_FIELDS_ARE_INPUT`): المبرهَنُ ما يلزم عنها لا صدقُها.
-/

set_option autoImplicit false

namespace A116.Manhaj

open A116.Qarar

/-! ## الحكمُ بالتسليم المبنيّ على المحسوس -/

/-- كـ`judge1` إلّا أنّ «لا حكم» لما لا يُحسّ ولا أصلَ له، لا لكلّ ما لا يُحسّ. -/
def judgeT (p : List (Nat × Hukm)) (c : Daawa) : Hukm :=
  if (premises p c).any (·.isNone) then .dawr
  else if (premises p c).any (fun o => o.any Hukm.fallen) then .saqit
  else if (premises p c).any (· == some .laHukm) || (!c.mahsus && c.usul.isEmpty) then .laHukm
  else if c.muarid then .khata
  else if c.wujud && (premises p c).all (· == some .qati) then .qati
  else .zanni

theorem judgeT_of_mahsus (p : List (Nat × Hukm)) (c : Daawa) (h : c.mahsus = true) :
    judgeT p c = judge1 p c := by
  simp [judgeT, judge1, h]

/-- خيارُ الأصل: موجودٌ، غيرُ ساقط، وله حكم ⟺ صائب. -/
theorem opt_ok (o : Option Hukm) :
    (o.isNone = false ∧ o.any Hukm.fallen = false ∧ (o == some .laHukm) = false) ↔
      ∃ k, o = some k ∧ k.sawab = true := by
  cases o with
  | none => simp
  | some k => cases k <;> simp [Hukm.fallen, Hukm.sawab]

theorem prem_ok (p : List (Nat × Hukm)) (c : Daawa) :
    ((premises p c).any (·.isNone) = false ∧ (premises p c).any (fun o => o.any Hukm.fallen) = false ∧
      (premises p c).any (· == some .laHukm) = false) ↔
      ∀ u ∈ c.usul, ∃ k, p.lookup u = some k ∧ k.sawab = true := by
  simp only [premises, List.any_eq_false, List.mem_map]
  constructor
  · rintro ⟨h1, h2, h3⟩ u hu
    exact (opt_ok _).1 ⟨by simpa using h1 _ ⟨u, hu, rfl⟩, by simpa using h2 _ ⟨u, hu, rfl⟩,
      by simpa using h3 _ ⟨u, hu, rfl⟩⟩
  · intro h
    refine ⟨?_, ?_, ?_⟩ <;> rintro _ ⟨u, hu, rfl⟩ <;>
      have := (opt_ok (p.lookup u)).2 (h u hu) <;> simp_all

theorem sawabT_iff (p : List (Nat × Hukm)) (c : Daawa) :
    (judgeT p c).sawab = true ↔
      (∀ u ∈ c.usul, ∃ k, p.lookup u = some k ∧ k.sawab = true) ∧
        (c.mahsus = true ∨ c.usul ≠ []) ∧ c.muarid = false := by
  rw [← prem_ok]
  unfold judgeT
  by_cases h1 : (premises p c).any (·.isNone) = true
  · simp [h1, Hukm.sawab]
  by_cases h2 : (premises p c).any (fun o => o.any Hukm.fallen) = true
  · simp [h1, h2, Hukm.sawab]
  by_cases h3 : (premises p c).any (· == some .laHukm) = true
  · simp [h1, h2, h3, Hukm.sawab]
  have g : ∀ b : Bool, b ≠ true → b = false := by decide
  have h1' := g _ h1; have h2' := g _ h2; have h3' := g _ h3
  by_cases h4 : (!c.mahsus && c.usul.isEmpty) = true
  · simp only [Bool.and_eq_true, Bool.not_eq_true', List.isEmpty_iff] at h4
    simp [h1', h2', h3', h4, Hukm.sawab]
  have h4' : c.mahsus = true ∨ c.usul ≠ [] := by
    cases hm : c.mahsus <;> cases hu : c.usul <;> simp_all
  have h4f : (!c.mahsus && c.usul.isEmpty) = false := g _ h4
  by_cases h5 : c.muarid = true
  · simp [h1', h2', h3', h4f, h5, Hukm.sawab]
  have h5' := g _ h5
  by_cases h6 : (c.wujud && (premises p c).all (· == some .qati)) = true
  · simp [h1', h2', h3', h4f, h5', h6, Hukm.sawab, h4']
  · simp [h1', h2', h3', h4f, h5', g _ h6, Hukm.sawab, h4']

theorem qatiT_iff (p : List (Nat × Hukm)) (c : Daawa) :
    judgeT p c = .qati ↔
      (∀ u ∈ c.usul, p.lookup u = some .qati) ∧ (c.mahsus = true ∨ c.usul ≠ []) ∧
        c.muarid = false ∧ c.wujud = true := by
  constructor
  · intro h
    have hs : (judgeT p c).sawab = true := by rw [h]; rfl
    obtain ⟨_, hm, hn⟩ := (sawabT_iff p c).1 hs
    have hq : c.wujud = true ∧ (premises p c).all (· == some .qati) = true := by
      unfold judgeT at h
      by_cases h6 : (c.wujud && (premises p c).all (· == some .qati)) = true
      · simpa using h6
      · have g : ∀ b : Bool, b ≠ true → b = false := by decide
        simp only [g _ h6, Bool.false_eq_true, ↓reduceIte] at h
        split at h <;> (try split at h) <;> (try split at h) <;> (try split at h) <;> cases h
    refine ⟨?_, hm, hn, hq.1⟩
    intro u hu
    have := List.all_eq_true.1 hq.2 _ (List.mem_map.2 ⟨u, hu, rfl⟩)
    simpa using this
  · rintro ⟨hq, hm, hn, hw⟩
    have hs : (judgeT p c).sawab = true :=
      (sawabT_iff p c).2 ⟨fun u hu => ⟨_, hq u hu, rfl⟩, hm, hn⟩
    have hall : (premises p c).all (· == some .qati) = true := by
      simp only [premises, List.all_map, List.all_eq_true, Function.comp_def]
      intro u hu; simp [hq u hu]
    unfold judgeT at hs ⊢
    split at hs
    · simp [Hukm.sawab] at hs
    · split at hs
      · simp [Hukm.sawab] at hs
      · split at hs
        · simp [Hukm.sawab] at hs
        · rename_i a b c'
          simp [a, b, c', hn, hw, hall]

/-! ## الزرعُ يُسقط -/

/-- معارضٌ مودَعٌ على دعوى أصولُها قائمةٌ وفيها حسٌّ أو أصلٌ: خاطئة. -/
theorem plant_khata (p : List (Nat × Hukm)) (c : Daawa)
    (hp : ∀ u ∈ c.usul, ∃ k, p.lookup u = some k ∧ k.sawab = true)
    (hg : c.mahsus = true ∨ c.usul ≠ []) (hm : c.muarid = true) : judgeT p c = .khata := by
  have h := (prem_ok p c).2 hp
  have h4 : (!c.mahsus && c.usul.isEmpty) = false := by
    cases hs : c.mahsus <;> cases hu : c.usul <;> simp_all
  simp [judgeT, h.1, h.2.1, h.2.2, h4, hm]

/-- أصلٌ ساقطٌ (خاطئٌ أو ساقطٌ أو دور) وكلُّ الأصول سابقة: ساقط. -/
theorem fallen_premise_saqit (p : List (Nat × Hukm)) (c : Daawa) (u : Nat) (k : Hukm)
    (hu : u ∈ c.usul) (hk : p.lookup u = some k) (hf : k.fallen = true)
    (hall : ∀ v ∈ c.usul, (p.lookup v).isSome = true) : judgeT p c = .saqit := by
  have h1 : (premises p c).any (·.isNone) = false := by
    simp only [premises, List.any_eq_false, List.mem_map]
    rintro _ ⟨v, hv, rfl⟩; have := hall v hv; cases hl : p.lookup v <;> simp_all
  have h2 : (premises p c).any (fun o => o.any Hukm.fallen) = true :=
    List.any_eq_true.2 ⟨_, List.mem_map.2 ⟨u, hu, rfl⟩, by simp [hk, hf]⟩
  simp [judgeT, h1, h2]

/-! ## السلسلةُ مع دعاويها -/

abbrev Judge := List (Nat × Hukm) → Daawa → Hukm

def ids (out : List (Daawa × Hukm)) : List (Nat × Hukm) := out.map fun x => (x.1.id, x.2)

def runDAux (J : Judge) : List (Daawa × Hukm) → List Daawa → List (Daawa × Hukm)
  | acc, [] => acc
  | acc, c :: cs => runDAux J (acc ++ [(c, J (ids acc) c)]) cs

def runD (J : Judge) (cs : List Daawa) : List (Daawa × Hukm) := runDAux J [] cs

theorem ids_append (a b : List (Daawa × Hukm)) : ids (a ++ b) = ids a ++ ids b := by
  simp [ids]

theorem runDAux_judge1 (acc : List (Daawa × Hukm)) (cs : List Daawa) :
    ids (runDAux judge1 acc cs) = runAux (ids acc) cs := by
  induction cs generalizing acc with
  | nil => rfl
  | cons c cs ih => simp only [runDAux, runAux]; rw [ih, ids_append]; rfl

/-- السلسلةُ مع دعاويها هي سلسلةُ `Qarar.run` بعينها. -/
theorem runD_judge1 (cs : List Daawa) : ids (runD judge1 cs) = run cs :=
  runDAux_judge1 [] cs

theorem lookup_append_some (l₁ l₂ : List (Nat × Hukm)) (u : Nat) (k : Hukm)
    (h : l₁.lookup u = some k) : (l₁ ++ l₂).lookup u = some k := by
  induction l₁ with
  | nil => simp at h
  | cons x xs ih =>
    obtain ⟨i, v⟩ := x
    by_cases e : u = i
    · subst e; simpa [List.lookup] using h
    · have : (u == i) = false := by simpa using e
      simp only [List.cons_append, List.lookup, this] at h ⊢
      exact ih h

/-- ما يصدق على كلّ دعوى وحكمِها في موضعه يصدق على السلسلة كلّها. -/
theorem local_runD (J : Judge) (Q : Daawa → Hukm → Prop) (hJ : ∀ p c, Q c (J p c))
    (cs : List Daawa) : ∀ x ∈ runD J cs, Q x.1 x.2 := by
  suffices ∀ acc, (∀ x ∈ acc, Q x.1 x.2) → ∀ x ∈ runDAux J acc cs, Q x.1 x.2 from
    this [] (by simp)
  induction cs with
  | nil => intro acc h; exact h
  | cons c cs ih =>
    intro acc h
    apply ih
    intro x hx
    rcases List.mem_append.1 hx with hx | hx
    · exact h x hx
    · simp at hx; subst hx; exact hJ _ _

/-! ## السقوطُ يسري -/

/-- مغلقٌ على `P`: كلُّ دعوى حكمُها `P` أصولُها كلُّها في السلسلة وأحكامُها `P`. -/
def Closed (P : Hukm → Bool) (out : List (Daawa × Hukm)) : Prop :=
  ∀ x ∈ out, P x.2 = true → ∀ u ∈ x.1.usul, ∃ k, (ids out).lookup u = some k ∧ P k = true

theorem closed_runD (J : Judge) (P : Hukm → Bool)
    (hJ : ∀ p c, P (J p c) = true → ∀ u ∈ c.usul, ∃ k, p.lookup u = some k ∧ P k = true)
    (cs : List Daawa) : Closed P (runD J cs) := by
  suffices ∀ acc, Closed P acc → Closed P (runDAux J acc cs) from this [] (by simp [Closed])
  induction cs with
  | nil => intro acc h; exact h
  | cons c cs ih =>
    intro acc h
    apply ih
    intro x hx hp u hu
    rw [ids_append]
    rcases List.mem_append.1 hx with hx | hx
    · obtain ⟨k, hk, hk'⟩ := h x hx hp u hu
      exact ⟨k, lookup_append_some _ _ _ _ hk, hk'⟩
    · simp at hx; subst hx
      obtain ⟨k, hk, hk'⟩ := hJ _ _ hp u hu
      exact ⟨k, lookup_append_some _ _ _ _ hk, hk'⟩

def find (out : List (Daawa × Hukm)) (a : Nat) : Option (Daawa × Hukm) :=
  out.find? fun x => x.1.id == a

theorem lookup_ids (out : List (Daawa × Hukm)) (a : Nat) :
    (ids out).lookup a = (find out a).map (·.2) := by
  induction out with
  | nil => rfl
  | cons x xs ih =>
    by_cases e : x.1.id = a
    · simp [ids, find, e]
    · have e' : (a == x.1.id) = false := by rw [beq_eq_false_iff_ne]; exact fun h => e h.symm
      have e'' : (x.1.id == a) = false := by simpa using e
      simp only [ids, find, List.map_cons, List.lookup, e', List.find?_cons, e''] at ih ⊢
      exact ih

/-- الطريقُ بالأصول: من دعوى إلى أصلٍ من أصولها، ثمّ إلى أصلِ أصلها… -/
inductive Reach (out : List (Daawa × Hukm)) : Nat → Nat → Prop
  | refl (a : Nat) : Reach out a a
  | step {a u b : Nat} {x : Daawa × Hukm} :
      find out a = some x → u ∈ x.1.usul → Reach out u b → Reach out a b

/-- **السقوطُ يسري**: كلُّ ما تبلغه دعوى حكمُها `P` بالأصول حكمُه `P`. -/
theorem closed_reach (P : Hukm → Bool) (out : List (Daawa × Hukm)) (h : Closed P out)
    {a b : Nat} (hr : Reach out a b) :
    ∀ x, find out a = some x → P x.2 = true → ∃ y, find out b = some y ∧ P y.2 = true := by
  induction hr with
  | refl a => intro x hx hp; exact ⟨x, hx, hp⟩
  | @step a u b x' hf hu _ ih =>
    intro x hx hp
    rw [hf] at hx; cases hx
    obtain ⟨k, hk, hk'⟩ := h _ (List.mem_of_find?_eq_some hf) hp _ hu
    rw [lookup_ids] at hk
    cases hy : find out u with
    | none => rw [hy] at hk; cases hk
    | some y =>
      rw [hy] at hk; cases hk
      exact ih y hy hk'

theorem judgeT_sawab_premises (p : List (Nat × Hukm)) (c : Daawa)
    (h : (judgeT p c).sawab = true) : ∀ u ∈ c.usul, ∃ k, p.lookup u = some k ∧ k.sawab = true :=
  ((sawabT_iff p c).1 h).1

def isQati (h : Hukm) : Bool := h == .qati

theorem judgeT_qati_premises (p : List (Nat × Hukm)) (c : Daawa)
    (h : isQati (judgeT p c) = true) : ∀ u ∈ c.usul, ∃ k, p.lookup u = some k ∧ isQati k = true :=
  fun u hu => ⟨_, ((qatiT_iff p c).1 (by simpa [isQati] using h)).1 u hu, rfl⟩

theorem judge1_qati_premises (p : List (Nat × Hukm)) (c : Daawa)
    (h : isQati (judge1 p c) = true) : ∀ u ∈ c.usul, ∃ k, p.lookup u = some k ∧ isQati k = true :=
  fun u hu => ⟨_, (qati_needs_wujud p c (by simpa [isQati] using h)).2 u hu, rfl⟩

/-- الصوابُ والقطعُ يسريان إلى الأصول في السلسلتين: `judge1` و`judgeT`. -/
theorem closed_all (cs : List Daawa) :
    Closed Hukm.sawab (runD judge1 cs) ∧ Closed isQati (runD judge1 cs) ∧
      Closed Hukm.sawab (runD judgeT cs) ∧ Closed isQati (runD judgeT cs) :=
  ⟨closed_runD _ _ sawab_needs_sawab_premises cs, closed_runD _ _ judge1_qati_premises cs,
   closed_runD _ _ judgeT_sawab_premises cs, closed_runD _ _ judgeT_qati_premises cs⟩

/-! ## لا مدخلَ ثالث -/

/-- **لا مدخلَ ثالث**: كلُّ أصلٍ بلا أصول تبلغه دعوى صائبةٌ في `judgeT` محسوس. -/
theorem roots_mahsus (cs : List Daawa) {a b : Nat} (hr : Reach (runD judgeT cs) a b)
    (x : Daawa × Hukm) (hx : find (runD judgeT cs) a = some x) (hs : x.2.sawab = true)
    (y : Daawa × Hukm) (hy : find (runD judgeT cs) b = some y) (hroot : y.1.usul = []) :
    y.1.mahsus = true := by
  obtain ⟨y', hy', hs'⟩ := closed_reach _ _ (closed_all cs).2.2.1 hr x hx hs
  rw [hy] at hy'; cases hy'
  have hloc := local_runD judgeT
    (fun c h => h.sawab = true → c.mahsus = true ∨ c.usul ≠ [])
    (fun p c hs => ((sawabT_iff p c).1 hs).2.1) cs y (List.mem_of_find?_eq_some hy) hs'
  rcases hloc with h | h
  · exact h
  · exact absurd hroot h

/-! ## الامتحانُ المضادّ لكلّ سلسلة -/

/-- `c'` أضعفُ معلومًا من `c`: سندٌ حُذف أو معارضٌ زُرع، والباقي هو هو. -/
structure Weaker (c' c : Daawa) : Prop where
  id : c'.id = c.id
  wujud : c'.wujud = c.wujud
  usul : c'.usul = c.usul
  mahsus : c'.mahsus = true → c.mahsus = true
  muarid : c.muarid = true → c'.muarid = true

/-- الحكمُ الأوّل لا يعلو الثاني: صوابُه صوابٌ هناك وقطعُه قطع. -/
def Hle (h' h : Hukm) : Prop := (h'.sawab = true → h.sawab = true) ∧ (h' = .qati → h = .qati)

inductive Pw : List (Nat × Hukm) → List (Nat × Hukm) → Prop
  | nil : Pw [] []
  | cons {i : Nat} {h' h : Hukm} {l' l : List (Nat × Hukm)} : Hle h' h → Pw l' l →
      Pw ((i, h') :: l') ((i, h) :: l)

inductive PwD : List Daawa → List Daawa → Prop
  | nil : PwD [] []
  | cons {c' c : Daawa} {l' l : List Daawa} : Weaker c' c → PwD l' l → PwD (c' :: l') (c :: l)

theorem Pw.append {a' a b' b : List (Nat × Hukm)} (h₁ : Pw a' a) (h₂ : Pw b' b) :
    Pw (a' ++ b') (a ++ b) := by
  induction h₁ with
  | nil => exact h₂
  | cons hh _ ih => exact Pw.cons hh ih

theorem Pw.lookup {l' l : List (Nat × Hukm)} (h : Pw l' l) (u : Nat) (k' : Hukm)
    (hk : l'.lookup u = some k') : ∃ k, l.lookup u = some k ∧ Hle k' k := by
  induction h with
  | nil => simp at hk
  | @cons i h' h _ _ hh _ ih =>
    by_cases e : u = i
    · subst e; simp [List.lookup] at hk; subst hk; exact ⟨h, by simp [List.lookup], hh⟩
    · have e' : (u == i) = false := by simpa using e
      simp only [List.lookup, e'] at hk ⊢
      exact ih hk

theorem step_monotone (p' p : List (Nat × Hukm)) (c' c : Daawa) (hp : Pw p' p) (hc : Weaker c' c) :
    Hle (judgeT p' c') (judgeT p c) := by
  constructor
  · intro hs
    obtain ⟨hpr, hm, hn⟩ := (sawabT_iff p' c').1 hs
    refine (sawabT_iff p c).2 ⟨?_, ?_, ?_⟩
    · intro u hu
      rw [← hc.usul] at hu
      obtain ⟨k', hk', hs'⟩ := hpr u hu
      obtain ⟨k, hk, hle⟩ := hp.lookup u k' hk'
      exact ⟨k, hk, hle.1 hs'⟩
    · rcases hm with hm | hm
      · exact Or.inl (hc.mahsus hm)
      · exact Or.inr (hc.usul ▸ hm)
    · cases e : c.muarid
      · rfl
      · rw [hc.muarid e] at hn; cases hn
  · intro hq
    obtain ⟨hpr, hm, hn, hw⟩ := (qatiT_iff p' c').1 hq
    refine (qatiT_iff p c).2 ⟨?_, ?_, ?_, hc.wujud ▸ hw⟩
    · intro u hu
      rw [← hc.usul] at hu
      obtain ⟨k, hk, hle⟩ := hp.lookup u _ (hpr u hu)
      rw [hle.2 rfl] at hk; exact hk
    · rcases hm with hm | hm
      · exact Or.inl (hc.mahsus hm)
      · exact Or.inr (hc.usul ▸ hm)
    · cases e : c.muarid
      · rfl
      · rw [hc.muarid e] at hn; cases hn

/-- **الامتحانُ المضادّ مبرهنًا**: حذفُ أيّ سندٍ وزرعُ أيّ معارضٍ في أيّ سلسلةٍ لا يرفع حكمًا في أيّ موضع. -/
theorem monotone (cs' cs : List Daawa) (h : PwD cs' cs) :
    Pw (ids (runD judgeT cs')) (ids (runD judgeT cs)) := by
  suffices ∀ acc' acc, Pw (ids acc') (ids acc) →
      Pw (ids (runDAux judgeT acc' cs')) (ids (runDAux judgeT acc cs)) from this [] [] Pw.nil
  induction h with
  | nil => intro acc' acc ha; exact ha
  | @cons c' c _ _ hc _ ih =>
    intro acc' acc ha
    apply ih
    rw [ids_append, ids_append]
    refine ha.append ?_
    simp only [ids, List.map_cons, List.map_nil, hc.id]
    exact Pw.cons (step_monotone _ _ _ _ ha hc) Pw.nil

/-! ## الشواهد -/

/-- سلسلةُ المدخل الثالث (ج1 س45، س86، س87، س348). -/
def taslim : List Daawa :=
  [ d 41 true true false,          -- القرآنُ مدرَكٌ محسوسٌ وإعجازُه محسوس (س87)
    d 42 true true false [41],     -- القرآنُ دليلٌ ثبت كونُه دليلًا بالعقل (س86)
    d 43 true false false [42],    -- الملائكةُ موجودون: دليلُه نقليّ (س87)
    d 44 true false true,          -- مدخلٌ نقليٌّ مستقلّ بلا أصل — يعارضه س86
    d 45 false true false,         -- خبرُ آحادٍ بعينه صحيح: النصُّ محسوس والصحّةُ ظنّ (س348)
    d 46 true false false [45],    -- غيبٌ بخبر الآحاد
    d 47 true true false [44] ]    -- ما بُني على المدخل المستقلّ

theorem taslim_verdicts : (ids (runD judgeT taslim)).map (·.2) =
    [.qati, .qati, .qati, .laHukm, .zanni, .zanni, .laHukm] := by decide

/-- `Qarar.judge1` يحكم على وجود الملائكة (س87) وعلى غيب الآحاد بـ«لا حكم». -/
theorem judge1_refuses_s87 : (run taslim).map (·.2) =
    [.qati, .qati, .laHukm, .laHukm, .zanni, .laHukm, .laHukm] := by decide

/-- على شاهدَي `Qarar` الحكمان واحد. -/
theorem qarar_witnesses_unchanged :
    ids (runD judgeT sealL0) = run sealL0 ∧ ids (runD judgeT jamid) = run jamid := by decide

end A116.Manhaj
