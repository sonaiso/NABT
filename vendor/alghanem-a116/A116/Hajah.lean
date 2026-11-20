import A116.Hadd
import A116.Grade
import A116.ExhaustPause

/-!
# قانونُ الحاجة المتبادلة: c يحتاج v، وv تحتاج c — تحت قانون «ا و ا و ا» (الابتداء والوصل والوقف)

نصُّ المالك (2026-10-12): «اكتب أنت قانونَه من تحليل الـ116 جبريًّا: c يحتاج v وكذلك v تحتاج c، **ويحكمها** قانونُ الابتداء
وقانونُ الوصل وقانونُ [الوقف]، وهذه مبرهناتٌ وفق قانون الاستنفاد بالحدّ الأدنى المكتمل … وتجعل ترخيصَ الانتقال قانونَ وراثةٍ
للأعلى من آبائه الأدنى، وعلاقةَ n بما قبلها وما بعدها وعلاقةَ ما قبلها بما بعدها». و«ا و ا و ا» نفسُه عرّفته `ExhaustPause.awa`
بنصّ المالك هناك: الابتداءُ والوصلُ والوقف (ADR ١٨). فهذه الوحدةُ **القانونُ الذي يحكمه «ا و ا و ا»**: حاجةُ الساكن إلى
المتحرّك وحاجةُ الحركة إلى حاملها، تعريفٌ مكتوبٌ بأمر المالك (لا نصَّ له في المستودعات الستّة)، والمبرهناتُ عليه.

## الخانةُ حاملٌ وحالةٌ وموضع

الخانةُ (`Cell`) حاملٌ وحالة؛ و**الموضعُ مشتقٌّ لا مستقلّ** (Algebra، `algebraic_recovery_proof.md` R6؛ hamil،
`rasm_bridge_proof.md` ج6 — نثرٌ هناك، ومبرهنٌ هنا): دورُ الموضع (`cv | v | c`) دالّةٌ في خانته وحالةِ ما قبله وحدَها
(`kindOf_append`، `role_is_local`).

## القانون

* **v تحتاج c**: الحركةُ لا تقوم إلّا على حامل — في الخانة بالبناء (`Cell` حاملٌ وحالة)؛ والمدُّ `v` حاملٌ ساكنٌ لا
  يقوم إلّا بعد حركته المجانسة مباشرةً (`v_needs_its_vowel`).
* **c يحتاج v**: الساكنُ `c` لا يقوم إلّا بعد متحرّكٍ في مقطعه — ذيلُ المقطع حتى هو مقبول (`needStep`).
* **الأبُ**: المتحرّكُ `cv` يقضي حاجتَه بنفسه ويقيم مقطعًا جديدًا؛ وكلُّ ساكنٍ ابنٌ لأقرب متحرّكٍ قبله.

`NeedLaw k`: كلُّ موضعٍ قُضيت حاجتُه. والحالاتُ سبعٌ لا ثامنَ لها (لا أبَ بعد، أو ذيلٌ من ستّة): **جبرٌ مغلق**
(`need_states_closed`: 7 × 3 = 21 انتقالًا كلُّها داخل السبع أو رفض).

## ما يُبرهَن

* `need_law_iff_parse`: **قانونُ الحاجة هو التقطيعُ نفسُه** — `NeedLaw k ⟺ ∃ ss, parse k = some (.none, ss)`،
  لكلّ طول. فالمقطعُ **الحدُّ الأدنى المكتمل**: أبٌ واحدٌ وأبناؤه (`one_parent_per_syllable`)، وأصغرُ مرخَّصٍ
  غيرِ فارغٍ `[cv]` وحدَه (`minimal_complete`).
* **«ا و ا و ا» يحكمه** (`need_of_awa_wasl`، `need_of_awa_waqf`، `awa_ibtida_of_need`): الوصلُ والوقفُ كلاهما يستلزمان
  القانون، والقانونُ يستلزم الابتداء؛ ويفترق الوصلُ عن الوقف في الطرف وحدَه (`need_not_continue`).
* **الوصلُ وراثةً** (`need_append`): ترخيصُ `a ++ b` = ترخيصُ `a` ثمّ ترخيصُ `b` من **حالةٍ واحدة** تورَث من `a` — فلا يرى
  الأعلى من آبائه الأدنى إلّا تلك الحالة (ذيلَ المقطع المفتوح، ثلاثةُ مواضع على الأكثر: `state_le_three`).
* **ما قبل وما بعد** (`before_after`): الموضعُ n يقرأ ما قبله بالحالة الموروثة، ويُسلّم ما بعده حالتَه؛ وما قبله لا يصل إلى
  ما بعده إلّا عبره.

ولا يُدّعى أنّ هذا كلُّ ما أراده المالك: التعريفُ معلنٌ بنصّ أمره، والمبرهناتُ عليه.
-/

set_option autoImplicit false

namespace A116.Hajah

open A116 A116.Stages A116.Ternary A116.Hadd

/-! ## ١. الموضعُ مشتقّ: الدورُ دالّةٌ في الخانة وحالةِ ما قبلها -/

theorem kindGo_append : ∀ (p : Option Haraka) (a b : List Cell),
    kindGo p (a ++ b) = kindGo p a ++ kindGo ((a.getLast?.map (·.haraka)).or p) b
  | _, [], _ => by simp [kindGo]
  | p, [x], b => by simp [kindGo]
  | p, x :: y :: t, b => by
    have ih := kindGo_append (some x.haraka) (y :: t) b
    simp only [List.cons_append, kindGo] at ih ⊢
    rw [ih]
    simp only [List.getLast?_cons_cons]
    cases h : (y :: t).getLast? with
    | none => simp at h
    | some z => simp

theorem kindOf_append (a b : List Cell) :
    kindOf (a ++ b) = kindOf a ++ kindGo (a.getLast?.map (·.haraka)) b := by
  simp [kindOf, kindGo_append]

/-- **دورُ الموضع محلّيّ**: دورُ الخانة x بعد a لا يقرأ من a إلّا حالةَ آخرِها. -/
theorem role_is_local (a a' : List Cell) (x : Cell) (b : List Cell)
    (h : a.getLast?.map (·.haraka) = a'.getLast?.map (·.haraka)) :
    kindGo (a.getLast?.map (·.haraka)) (x :: b) = kindGo (a'.getLast?.map (·.haraka)) (x :: b) := by
  rw [h]

/-! ## ٢. القانون -/

/-- حالةُ الحاجة: `none` لا أبَ بعد؛ `some t` بعد متحرّكٍ وذيلُ مقطعه حتى الآن `t`. -/
abbrev St := Option (List K)

/-- خطوةُ القانون: المتحرّكُ يقيم أبًا؛ والساكنُ يحتاج أبًا وذيلًا مقبولًا؛ وإلّا رفض (`none`). -/
def needStep : St → K → Option St
  | _, .cv => some (some [])
  | none, _ => none
  | some t, x => if (sylOf (t ++ [x])).isSome then some (some (t ++ [x])) else none

def needRun : St → List K → Bool
  | _, [] => true
  | st, x :: r => match needStep st x with
    | some st' => needRun st' r
    | none => false

/-- **قانونُ الحاجة المتبادلة**: من الابتداء، كلُّ موضعٍ قُضيت حاجتُه. -/
def NeedLaw (k : List K) : Prop := needRun none k = true

instance (k : List K) : Decidable (NeedLaw k) := inferInstanceAs (Decidable (_ = true))

/-- الحالاتُ السبع. -/
def states : List St :=
  [none, some [], some [.v], some [.c], some [.v, .c], some [.c, .c], some [.v, .c, .c]]

/-- **جبرٌ مغلق**: كلُّ انتقالٍ من السبع بأيّ دورٍ يعود إلى السبع أو يرفض. -/
theorem need_states_closed :
    states.all (fun st => [K.cv, K.v, K.c].all fun x =>
      match needStep st x with
      | some st' => states.contains st'
      | none => true) = true := by decide

theorem states_length : states.length = 7 := rfl

/-- **v تحتاج حركتَها**: المدُّ لا يقوم إلّا بعد متحرّكٍ مباشرة (الذيلُ فارغ). -/
theorem v_needs_its_vowel (t : List K) (h : t ≠ []) (ht : (sylOf t).isSome) :
    needStep (some t) .v = none := by
  match t, ht with
  | [], _ => exact absurd rfl h
  | [.v], _ => rfl
  | [.c], _ => rfl
  | [.v, .c], _ => rfl
  | [.c, .c], _ => rfl
  | [.v, .c, .c], _ => rfl

/-- **الابتداء**: لا ابتداءَ بساكن. -/
theorem need_start {x : K} {r : List K} (h : NeedLaw (x :: r)) : x = .cv := by
  cases x with
  | cv => rfl
  | v => simp [NeedLaw, needRun, needStep] at h
  | c => simp [NeedLaw, needRun, needStep] at h

/-! ## ٣. القانونُ هو التقطيع: الحدُّ الأدنى المكتمل -/

theorem coda_prefixes_ok (s : Syl) (r : List K) :
    needRun (some []) (s.coda ++ r) = needRun (some s.coda) r := by
  cases s <;> simp [Syl.coda, needRun, needStep, sylOf]

theorem needRun_flat_any (st : St) (ss : List Syl) :
    needRun st (flat .none ss) = needRun (some []) (flat .none ss) := by
  cases ss with
  | nil => simp [flat, Lead.atoms, needRun]
  | cons s t => simp [flat, Lead.atoms, Syl.atoms, needRun, needStep]

theorem needRun_flat : ∀ (ss : List Syl) (st : St), needRun st (flat .none ss) = true
  | [], _ => by simp [flat, Lead.atoms, needRun]
  | s :: t, st => by
    have e : flat .none (s :: t) = .cv :: (s.coda ++ flat .none t) := by
      simp [flat, Lead.atoms, Syl.atoms]
    rw [e]
    simp only [needRun, needStep]
    rw [coda_prefixes_ok, needRun_flat_any]
    exact needRun_flat t (some [])

theorem needRun_some_flat : ∀ (k t : List K) (s0 : Syl), sylOf t = some s0 →
    needRun (some t) k = true → ∃ ss, .cv :: t ++ k = flat .none (s0 :: ss) ∨
      ∃ s ss', .cv :: t ++ k = flat .none (s :: ss')
  | [], t, s0, hs, _ => ⟨[], Or.inl (by simp [flat, Lead.atoms, Syl.atoms, coda_of_sylOf hs])⟩
  | .cv :: r, t, s0, hs, h => by
    simp only [needRun, needStep] at h
    obtain ⟨ss, hss⟩ := needRun_some_flat r [] .CV rfl h
    have hr : ∃ s ss', .cv :: r = flat .none (s :: ss') := by
      rcases hss with e | ⟨s, ss', e⟩
      · exact ⟨.CV, ss, by simpa using e⟩
      · exact ⟨s, ss', by simpa using e⟩
    obtain ⟨s, ss', e⟩ := hr
    refine ⟨s :: ss', Or.inl ?_⟩
    have : flat .none (s0 :: s :: ss') = .cv :: s0.coda ++ flat .none (s :: ss') := by
      simp [flat, Lead.atoms, Syl.atoms]
    rw [this, ← e, coda_of_sylOf hs]
  | .v :: r, t, s0, hs, h => by
    simp only [needRun, needStep] at h
    by_cases hok : (sylOf (t ++ [.v])).isSome = true
    · simp only [hok, ↓reduceIte] at h
      obtain ⟨s1, hs1⟩ := Option.isSome_iff_exists.1 hok
      obtain ⟨ss, hss⟩ := needRun_some_flat r (t ++ [.v]) s1 hs1 h
      refine ⟨ss, Or.inr ?_⟩
      rcases hss with e | ⟨s, ss', e⟩
      · exact ⟨s1, ss, by simpa using e⟩
      · exact ⟨s, ss', by simpa using e⟩
    · simp [hok] at h
  | .c :: r, t, s0, hs, h => by
    simp only [needRun, needStep] at h
    by_cases hok : (sylOf (t ++ [.c])).isSome = true
    · simp only [hok, ↓reduceIte] at h
      obtain ⟨s1, hs1⟩ := Option.isSome_iff_exists.1 hok
      obtain ⟨ss, hss⟩ := needRun_some_flat r (t ++ [.c]) s1 hs1 h
      refine ⟨ss, Or.inr ?_⟩
      rcases hss with e | ⟨s, ss', e⟩
      · exact ⟨s1, ss, by simpa using e⟩
      · exact ⟨s, ss', by simpa using e⟩
    · simp [hok] at h

/-- **قانونُ الحاجة هو التقطيعُ نفسُه**، لكلّ طول. -/
theorem need_law_iff_parse (k : List K) : NeedLaw k ↔ ∃ ss, parse k = some (.none, ss) := by
  constructor
  · intro h
    match k, h with
    | [], _ => exact ⟨[], parse_flat .none []⟩
    | .cv :: r, h =>
      simp only [NeedLaw, needRun, needStep] at h
      obtain ⟨ss, hss⟩ := needRun_some_flat r [] .CV rfl h
      rcases hss with e | ⟨s, ss', e⟩
      · exact ⟨.CV :: ss, by rw [show (K.cv :: r) = _ from by simpa using e]; exact parse_flat _ _⟩
      · exact ⟨s :: ss', by rw [show (K.cv :: r) = _ from by simpa using e]; exact parse_flat _ _⟩
    | .v :: r, h => simp [NeedLaw, needRun, needStep] at h
    | .c :: r, h => simp [NeedLaw, needRun, needStep] at h
  · rintro ⟨ss, hp⟩
    rw [← flat_parse hp]
    exact needRun_flat ss none

/-- **أبٌ واحدٌ لكلّ مقطع**: في وصل المقاطع، عددُ المتحرّكات هو عددُ المقاطع. -/
theorem one_parent_per_syllable (ss : List Syl) :
    ((flat .none ss).filter (· == .cv)).length = ss.length := by
  induction ss with
  | nil => rfl
  | cons s t ih =>
    have e : flat .none (s :: t) = s.atoms ++ flat .none t := by simp [flat, Lead.atoms]
    rw [e, List.filter_append, List.length_append, ih]
    cases s <;> simp [Syl.atoms, Syl.coda] <;> omega

/-- **الحدُّ الأدنى المكتمل**: أصغرُ مرخَّصٍ غيرِ فارغٍ متحرّكٌ واحد. -/
theorem minimal_complete (k : List K) (h : NeedLaw k) (hl : k.length = 1) : k = [.cv] := by
  match k, hl with
  | [x], _ => rw [need_start h]

/-! ## ٤. الوصلُ والوراثة: الأعلى لا يرى من آبائه الأدنى إلّا حالةً واحدة -/

/-- الحالةُ بعد سلسلة (أو الرفض). -/
def needState : St → List K → Option St
  | st, [] => some st
  | st, x :: r => (needStep st x).bind fun st' => needState st' r

/-- **قانونُ الوراثة**: ترخيصُ `a ++ b` = ترخيصُ `a`، ثمّ `b` من الحالة الموروثة. -/
theorem need_append : ∀ (st : St) (a b : List K),
    needRun st (a ++ b) = true ↔ ∃ st', needState st a = some st' ∧ needRun st' b = true
  | st, [], b => by simp [needState]
  | st, x :: a, b => by
    simp only [List.cons_append, needRun, needState]
    cases h : needStep st x with
    | none => simp
    | some st' => simpa using need_append st' a b

/-- الحالةُ الموروثةُ ذيلٌ مقبولٌ أو «لا أب»: ثلاثةُ مواضع على الأكثر — فالوراثةُ محدودة. -/
theorem state_mem : ∀ (st : St) (a : List K) (st' : St), st ∈ states →
    needState st a = some st' → st' ∈ states
  | st, [], st', hs, h => by simp [needState] at h; rw [← h]; exact hs
  | st, x :: a, st', hs, h => by
    simp only [needState] at h
    cases hx : needStep st x with
    | none => rw [hx] at h; simp at h
    | some s1 =>
      rw [hx] at h
      simp only [Option.bind_some] at h
      have hc := need_states_closed
      simp only [List.all_eq_true] at hc
      have := hc st (List.elem_iff.mp (by simpa using List.elem_iff.mpr hs)) x (by cases x <;> simp)
      rw [hx] at this
      exact state_mem s1 a st' (by simpa using this) h

theorem state_le_three (a : List K) (t : List K) (h : needState none a = some (some t)) :
    t.length ≤ 3 := by
  have := state_mem none a (some t) (by simp [states]) h
  simp [states] at this
  rcases this with rfl | rfl | rfl | rfl | rfl | rfl <;> simp

/-- **ما قبل وما بعد**: سلسلتان قبل الموضع بحالةٍ موروثةٍ واحدة لا يفترق ما بعدهما. -/
theorem before_after (a a' b : List K) (st : St) (h : needState none a = some st)
    (h' : needState none a' = some st) :
    needRun none (a ++ b) = needRun none (a' ++ b) := by
  cases e : needRun none (a ++ b) <;> cases e' : needRun none (a' ++ b) <;> try rfl
  · exact absurd ((need_append none a' b).1 e') (by
      rintro ⟨s2, h2, hb⟩; rw [h'] at h2; cases h2
      exact absurd ((need_append none a b).2 ⟨st, h, hb⟩) (by simp [e]))
  · exact absurd ((need_append none a b).1 e) (by
      rintro ⟨s2, h2, hb⟩; rw [h] at h2; cases h2
      exact absurd ((need_append none a' b).2 ⟨st, h', hb⟩) (by simp [e']))

/-! ## ٥. الوصلُ والوقفُ والخانات -/

theorem continue_needs (k : List K) (h : continueB k = true) : NeedLaw k := by
  obtain ⟨ss, hp, _⟩ := (continueB_iff k).1 h
  exact (need_law_iff_parse k).2 ⟨ss, hp⟩

theorem pause_needs (k : List K) (h : pauseB k = true) : NeedLaw k := by
  obtain ⟨ss, hp, _⟩ := (pauseB_iff k).1 h
  exact (need_law_iff_parse k).2 ⟨ss, hp⟩

/-- القانونُ لا يكفي للوصل: بَحْرْ تقضي حاجاتِها ولا تُرخَّص إلّا وقفًا — الطرفُ وحدَه يفرّق. -/
theorem need_not_continue : NeedLaw [.cv, .c, .c] ∧ continueB [.cv, .c, .c] = false := by
  refine ⟨by decide, ?_⟩
  have : ([.cv, .c, .c] : List K) = flat .none [.CVCC] := rfl
  rw [this, Grade.continueB_flat]; rfl

/-- **على الخانات**: كلُّ كلمةٍ مرخَّصةٍ بقيد الحدّ تحقّق قانونَ الحاجة على أدوارها. -/
theorem strict_need (w : List Cell) (h : strictB w = true) : NeedLaw (kindOf w) := by
  simp only [strictB, Bool.and_eq_true] at h
  exact continue_needs _ h.1

/-! ## ٦. «ا و ا و ا» يحكم القانون (`ExhaustPause.awa`، ADR ١٨) -/

/-- الوصلُ يستلزم القانون. -/
theorem need_of_awa_wasl (w : List Cell) (h : ExhaustPause.awa .wasl w = true) : NeedLaw (kindOf w) :=
  strict_need w h

/-- الوقفُ يستلزم القانون. -/
theorem need_of_awa_waqf (w : List Cell) (h : ExhaustPause.awa .waqf w = true) : NeedLaw (kindOf w) := by
  simp only [ExhaustPause.awa, strictPauseB, Bool.and_eq_true] at h
  exact pause_needs _ h.1

/-- القانونُ يستلزم الابتداء: ما قُضيت حاجاتُه لا يبدأ بساكن. -/
theorem awa_ibtida_of_need (w : List Cell) (h : NeedLaw (kindOf w)) :
    ExhaustPause.awa .ibtida w = true := by
  cases w with
  | nil => rfl
  | cons x t =>
    have hk : kindOf (x :: t) = kindOne none x :: kindGo (some x.haraka) t := rfl
    rw [hk] at h
    have h0 := need_start h
    simp only [ExhaustPause.awa, Boundary.initialSukun, Bool.not_eq_true']
    cases hs : x.haraka with
    | sukun => simp [kindOne, hs] at h0
    | fatha => simp [Cell.isSukun, hs, Haraka.isSukun]
    | damma => simp [Cell.isSukun, hs, Haraka.isSukun]
    | kasra => simp [Cell.isSukun, hs, Haraka.isSukun]

/-- الطفرةُ المرفوضة: مدٌّ بعد مُغلِق (c v) لا تُقضى حاجتُه. -/
theorem madd_after_closer_refused : ¬ NeedLaw [.cv, .c, .v] := by decide

end A116.Hajah
