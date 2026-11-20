import A116.Fasl
import A116.Hajah

/-!
# قانونُ التوريث: يرث ما قبله ويورث ما بعده (ADR ٧٥)

نصُّ المالك (2026-10-16): «ما ينقص هو قانونان: الأوّلُ قانونُ الفصل، والثاني قانونُ التوريث: أن يرث ما قبلَ ويورث ما
بعدَه، ويربط ما قبلَ بما بعده بعلاقة، ويربط ما بعده بما قبله بعلاقة، ويرتبط بما قبله بعلاقة، ويرتبط هو بما بعده
بعلاقة».

`Nizam` يحكم على السلسلة بالأوّل والمتجاورَين والطرف، و`Fasl` (ADR ٧٤) على عنصرين في مجال. والتوريثُ هو ما يحمله
الموضعُ من قبله إلى بعده:

* **البنية** (`Tawrith`): ما يرثه الأوّل (`bad` — الابتداء)، والخطوةُ (`step`): العنصرُ يرث حالةَ ما قبله ويورث حالةً
  لما بعده، أو يُمنع (`none` — **المانعُ يقطع التوريث**)، وقبولُ الطرف (`waqf`).
* **العلاقاتُ الأربع**، كلٌّ مبرهَنةٌ لكلّ نظامٍ كذلك:
  1. **ما قبلُ بما بعدُ**: ترخيصُ ‎a ++ b‎ لا يرى من `a` إلّا الحالةَ الموروثة (`lic_append`)، فما ورّث حالةً واحدةً لا
     يفترق ما بعده (`qabl_bad`).
  2. **ما بعدُ بما قبلُ**: اللاحقُ طلبٌ على الحالة (`talab`) يُسحب عبر كلّ خطوةٍ إلى ما قبلها (`talab_append`)، وما طلب
     طلبًا واحدًا لا يفترق ما قبله (`bad_qabl`).
  3. **العنصرُ بما قبله وبما بعده**: الموضعُ الأوسطُ مرخَّصٌ ⟺ يرث حالةً من قبله ويورث حالةً يقبلها ما بعده
     (`wasat`).
  4. **التركيب**: الوراثةُ عبر سلسلتين وراثةٌ عبر الأولى ثمّ الثانية (`run_append`).
* **السببُ والشرطُ والمانع**: الحالةُ الموروثةُ سببُ الفصل بالسياق — طرفا مانعِها (`Fasl.mani` على `run`) لا يفصلهما
  لاحقٌ (`tawrith_la_tafsil`)، وما فصله لاحقٌ فحالتاهما مختلفتان (`siyaq_fasl`)، وما فصلته الحالةُ في مجالٍ تعيّن منها
  (`tayin_bil_tawrith`)؛ والمانعُ يقطع كلَّ ما بعده (`mani_yaqta`).
* **المثولات** — الأنظمةُ القائمةُ توريثٌ بعينه:
  * `Nizam` وصلًا (`nizam_wasl`): الموروثُ العنصرُ الأخير، والابتداءُ أوّلُ خطوة (`nizam_ibtida`).
  * `Nizam` وقفًا (`nizam_waqf`): الموروثُ العنصرُ الأخيرُ وعلامةُ «وُقف»، و**الوقفُ لا يورث** (`waqf_la_yuwarrith`).
  * **قانونُ الحاجة** (`Hajah`): خطوتُه `needStep` بعينها (`hajah_law`)، و`Hajah.before_after` حالةٌ من `qabl_bad`
    (`hajah_before_after`).
* **الجامع** (`qawanin_khamsa`): لكلّ `Nizam` الابتداءُ والوصلُ والوقفُ والفصلُ والتوريثُ قوانينُ بنيةٍ واحدة.
-/

namespace A116.Tawrith

open A116 A116.Nizam A116.Fasl

/-! ## ١. البنية -/

/-- **قانونُ التوريث**: ما يرثه الأوّل، والخطوةُ ترث وتورث أو تُمنع، وقبولُ الطرف. -/
structure Tawrith (α σ : Type) where
  bad : σ
  step : σ → α → Option σ
  waqf : σ → Bool

variable {α σ : Type}

/-- الحالةُ الموروثةُ بعد سلسلة، أو الانقطاع. -/
def run (T : Tawrith α σ) : σ → List α → Option σ
  | s, [] => some s
  | s, x :: r => match T.step s x with
    | some s' => run T s' r
    | none => none

/-- قبولُ ما انتهى إليه التوريث. -/
def qubul (T : Tawrith α σ) : Option σ → Bool
  | some s => T.waqf s
  | none => false

/-- **طلبُ ما بعدُ**: الحالاتُ التي يقبل منها اللاحق. -/
def talab (T : Tawrith α σ) : List α → σ → Bool
  | [], s => T.waqf s
  | x :: r, s => match T.step s x with
    | some s' => talab T r s'
    | none => false

/-- ترخيصُ السلسلة: من الابتداء إلى الطرف. -/
def lic (T : Tawrith α σ) (w : List α) : Bool := qubul T (run T T.bad w)

/-! ## ٢. العلاقاتُ الأربع -/

/-- **التركيب**: ما ورثته `b` هو ما أورثته `a`. -/
theorem run_append (T : Tawrith α σ) : ∀ (s : σ) (a b : List α),
    run T s (a ++ b) = (run T s a).bind fun s' => run T s' b
  | s, [], b => rfl
  | s, x :: a, b => by
    simp only [List.cons_append, run]
    cases T.step s x with
    | none => rfl
    | some s' => exact run_append T s' a b

/-- الطلبُ هو التوريثُ مقروءًا من الطرف. -/
theorem talab_eq (T : Tawrith α σ) : ∀ (w : List α) (s : σ), talab T w s = qubul T (run T s w)
  | [], s => rfl
  | x :: r, s => by
    simp only [talab, run]
    cases T.step s x with
    | none => rfl
    | some s' => exact talab_eq T r s'

/-- **ما بعدُ بما قبلُ**: طلبُ ‎a ++ b‎ هو طلبُ `b` مسحوبًا عبر `a`. -/
theorem talab_append (T : Tawrith α σ) (a b : List α) (s : σ) :
    talab T (a ++ b) s = match run T s a with
      | some s' => talab T b s'
      | none => false := by
  rw [talab_eq, run_append]
  cases run T s a with
  | none => rfl
  | some s' => exact (talab_eq T b s').symm

/-- **ما قبلُ بما بعدُ**: ترخيصُ ‎a ++ b‎ هو طلبُ `b` على ما ورّثته `a` — العلاقةُ تمرّ بالحالة وحدها. -/
theorem lic_append (T : Tawrith α σ) (a b : List α) :
    lic T (a ++ b) = match run T T.bad a with
      | some s => talab T b s
      | none => false := by
  unfold lic
  rw [run_append]
  cases run T T.bad a with
  | none => rfl
  | some s => exact (talab_eq T b s).symm

/-- **ما ورّث حالةً واحدةً لا يفترق ما بعده.** -/
theorem qabl_bad (T : Tawrith α σ) (a a' b : List α) (h : run T T.bad a = run T T.bad a') :
    lic T (a ++ b) = lic T (a' ++ b) := by
  rw [lic_append, lic_append, h]

/-- **وما طلب طلبًا واحدًا لا يفترق ما قبله.** -/
theorem bad_qabl (T : Tawrith α σ) (a b b' : List α) (h : ∀ s, talab T b s = talab T b' s) :
    lic T (a ++ b) = lic T (a ++ b') := by
  rw [lic_append, lic_append]
  cases run T T.bad a with
  | none => rfl
  | some s => exact h s

/-- **العنصرُ بما قبله وبما بعده**: الموضعُ الأوسطُ مرخَّصٌ ⟺ يرث حالةً ويورث حالةً يقبلها ما بعده. -/
theorem wasat (T : Tawrith α σ) (u : List α) (x : α) (v : List α) :
    lic T (u ++ x :: v) = true ↔
      ∃ s s', run T T.bad u = some s ∧ T.step s x = some s' ∧ talab T v s' = true := by
  rw [lic_append]
  cases hu : run T T.bad u with
  | none => simp
  | some s =>
    simp only [talab]
    cases hx : T.step s x with
    | none => simp [hx]
    | some s' => simp [hx]

/-- **المانعُ يقطع التوريث**: ما بعده كلُّه منقطع. -/
theorem mani_yaqta (T : Tawrith α σ) (s : σ) (x : α) (h : T.step s x = none) (v : List α) :
    run T s (x :: v) = none := by
  simp only [run, h]

theorem mani_yaqta_lic (T : Tawrith α σ) (u : List α) (s : σ) (x : α) (hu : run T T.bad u = some s)
    (h : T.step s x = none) (v : List α) : lic T (u ++ x :: v) = false := by
  rw [lic_append, hu]
  simp only [talab, h]

/-! ## ٣. التوريثُ والفصل -/

section fasl
variable [DecidableEq α] [DecidableEq σ]

/-- **طرفا المانع على الحالة الموروثة لا يفصلهما لاحق.** -/
theorem tawrith_la_tafsil (T : Tawrith α σ) (S : List (List α)) (a a' : List α)
    (h : (a, a') ∈ mani (⟨run T T.bad, S⟩ : Fasl (List α) (Option σ))) (b : List α) :
    lic T (a ++ b) = lic T (a' ++ b) := by
  obtain ⟨_, _, _, he⟩ := (mem_mani _ a a').1 h
  exact qabl_bad T a a' b he

omit [DecidableEq α] [DecidableEq σ] in
/-- **ما فصله لاحقٌ فحالتاهما مختلفتان**: الحالةُ الموروثةُ سببُ الفصل بالسياق. -/
theorem siyaq_fasl (T : Tawrith α σ) (a a' b : List α) (h : lic T (a ++ b) ≠ lic T (a' ++ b)) :
    run T T.bad a ≠ run T T.bad a' := fun he => h (qabl_bad T a a' b he)

/-- **وما فصلته الحالةُ في مجالٍ تعيّن منها.** -/
theorem tayin_bil_tawrith (T : Tawrith α σ) (S : List (List α))
    (h : fasl (⟨run T T.bad, S⟩ : Fasl (List α) (Option σ)) = true) (a : List α) (ha : a ∈ S) :
    tayin (⟨run T T.bad, S⟩ : Fasl (List α) (Option σ)) (run T T.bad a) = some a :=
  tayin_of_fasl _ h a ha

end fasl

/-! ## ٤. المثولات -/

/-- `Nizam` وصلًا: الموروثُ آخرُ عنصر. -/
def ofNizam (N : Nizam α) : Tawrith α (Option α) where
  bad := none
  step
    | none, x => if N.wujud x && N.ibtida x then some (some x) else none
    | some a, x => if N.wujud x && N.wasl a x then some (some x) else none
  waqf _ := true

theorem ofNizam_chain (N : Nizam α) : ∀ (a : α) (t : List α),
    qubul (ofNizam N) (run (ofNizam N) (some a) t) = (t.all N.wujud && chain N a t)
  | a, [] => rfl
  | a, b :: t => by
    have hs : (ofNizam N).step (some a) b = if N.wujud b && N.wasl a b then some (some b) else none := rfl
    simp only [run, hs, List.all_cons, chain]
    cases hw : N.wujud b <;> cases hl : N.wasl a b <;>
      simp only [Bool.true_and, Bool.false_and, Bool.and_false, Bool.and_true, ite_true, ite_false, Bool.false_eq_true]
    all_goals first | rfl | exact ofNizam_chain N b t

/-- **الوصلُ توريث**: ترخيصُ `Nizam` وصلًا هو ترخيصُ توريثه. -/
theorem nizam_wasl (N : Nizam α) (w : List α) : lic (ofNizam N) w = licWasl N w := by
  cases w with
  | nil => rfl
  | cons a t =>
    have hs : (ofNizam N).step (ofNizam N).bad a =
        if N.wujud a && N.ibtida a then some (some a) else none := rfl
    unfold lic
    simp only [run, licWasl, List.all_cons, hs]
    cases hw : N.wujud a <;> cases hi : N.ibtida a <;>
      simp only [Bool.true_and, Bool.false_and, Bool.and_false, Bool.and_true, ite_true, ite_false, Bool.false_eq_true]
    all_goals first | rfl | exact ofNizam_chain N a t

/-- **الابتداءُ أوّلُ خطوة.** -/
theorem nizam_ibtida (N : Nizam α) (x : α) : lic (ofNizam N) [x] = (N.wujud x && N.ibtida x) := by
  rw [nizam_wasl]
  simp [licWasl, chain]

/-- `Nizam` وقفًا: الموروثُ آخرُ عنصرٍ وعلامةُ الوقف. -/
def ofNizamWaqf (N : Nizam α) : Tawrith α (Option α × Bool) where
  bad := (none, false)
  step
    | (none, _), x => if N.wujud x && N.ibtida x then some (some x, false) else none
    | (some _, true), _ => none
    | (some a, false), x =>
      if N.wujud x then
        (if N.wasl a x then some (some x, false) else if N.waqf a x then some (some x, true) else none)
      else none
  waqf _ := true

/-- **الوقفُ لا يورث**: ما بعد زوج الوقف ممنوع. -/
theorem waqf_la_yuwarrith (N : Nizam α) (a x : α) : (ofNizamWaqf N).step (some a, true) x = none := rfl

theorem ofNizamWaqf_chainP (N : Nizam α) : ∀ (a : α) (t : List α),
    qubul (ofNizamWaqf N) (run (ofNizamWaqf N) (some a, false) t) = (t.all N.wujud && chainP N a t)
  | a, [] => rfl
  | a, [b] => by
    have hs : (ofNizamWaqf N).step (some a, false) b = if N.wujud b then
        (if N.wasl a b then some (some b, false) else if N.waqf a b then some (some b, true) else none)
        else none := rfl
    simp only [run, hs, List.all_cons, List.all_nil, chainP]
    cases hw : N.wujud b <;> cases hl : N.wasl a b <;> cases hq : N.waqf a b <;> rfl
  | a, b :: c :: t => by
    have hs : (ofNizamWaqf N).step (some a, false) b = if N.wujud b then
        (if N.wasl a b then some (some b, false) else if N.waqf a b then some (some b, true) else none)
        else none := rfl
    have ih := ofNizamWaqf_chainP N b (c :: t)
    simp only [run, hs, List.all_cons, chainP]
    cases hw : N.wujud b <;> cases hl : N.wasl a b <;> cases hq : N.waqf a b <;>
      simp only [Bool.false_and, Bool.and_false, Bool.true_and, ite_true, ite_false, Bool.false_eq_true]
    all_goals first
      | rfl
      | (simp only [run] at ih ⊢; rw [ih]; simp [List.all_cons])

/-- **الوقفُ توريث**: ترخيصُ `Nizam` وقفًا هو ترخيصُ توريثه. -/
theorem nizam_waqf (N : Nizam α) (w : List α) : lic (ofNizamWaqf N) w = licWaqf N w := by
  cases w with
  | nil => rfl
  | cons a t =>
    have hs : (ofNizamWaqf N).step (ofNizamWaqf N).bad a =
        if N.wujud a && N.ibtida a then some (some a, false) else none := rfl
    unfold lic
    simp only [run, licWaqf, List.all_cons, hs]
    cases hw : N.wujud a <;> cases hi : N.ibtida a <;>
      simp only [Bool.true_and, Bool.false_and, Bool.and_false, Bool.and_true, ite_true, ite_false, Bool.false_eq_true]
    all_goals first | rfl | exact ofNizamWaqf_chainP N a t

/-- قانونُ الحاجة توريثًا: خطوتُه `needStep` بعينها. -/
def hajah : Tawrith Stages.K Hajah.St := ⟨none, Hajah.needStep, fun _ => true⟩

theorem hajah_run : ∀ (st : Hajah.St) (k : List Stages.K), qubul hajah (run hajah st k) = Hajah.needRun st k
  | st, [] => rfl
  | st, x :: r => by
    simp only [run, Hajah.needRun]
    rw [show hajah.step st x = Hajah.needStep st x from rfl]
    cases Hajah.needStep st x with
    | none => rfl
    | some s' => exact hajah_run s' r

theorem hajah_state : ∀ (st : Hajah.St) (k : List Stages.K), Hajah.needState st k = run hajah st k
  | st, [] => rfl
  | st, x :: r => by
    simp only [run, Hajah.needState]
    rw [show hajah.step st x = Hajah.needStep st x from rfl]
    cases Hajah.needStep st x with
    | none => rfl
    | some s' => exact hajah_state s' r

/-- **قانونُ الحاجة توريث.** -/
theorem hajah_law (k : List Stages.K) : lic hajah k = true ↔ Hajah.NeedLaw k := by
  unfold lic Hajah.NeedLaw
  rw [hajah_run]
  rfl

/-- **و`Hajah.before_after` حالةٌ من `qabl_bad`.** -/
theorem hajah_before_after (a a' b : List Stages.K) (st : Hajah.St) (h : Hajah.needState none a = some st)
    (h' : Hajah.needState none a' = some st) :
    Hajah.needRun none (a ++ b) = Hajah.needRun none (a' ++ b) := by
  rw [hajah_state] at h h'
  have := qabl_bad hajah a a' b (h.trans h'.symm)
  unfold lic at this
  rwa [hajah_run, hajah_run] at this

/-! ## ٥. الشواهد على النظام الثلاثيّ -/

/-- **ما قبلُ لا يصل إلى ما بعدُ إلّا بحالته**: «cv c» و«cv v c» ورّثتا حالةً واحدة. -/
theorem shahid_qabl :
    run (ofNizam ternary) none [.cv, .c] = run (ofNizam ternary) none [.cv, .v, .c] ∧
    ∀ b, licWasl ternary ([.cv, .c] ++ b) = licWasl ternary ([.cv, .v, .c] ++ b) := by
  refine ⟨by decide, fun b => ?_⟩
  rw [← nizam_wasl, ← nizam_wasl]
  exact qabl_bad _ _ _ b (by decide)

/-- **والحالتان المختلفتان يفصلهما لاحق**: «c» بعد «cv» مرخَّص وبعد «cv c» ممنوع. -/
theorem shahid_fasl :
    licWasl ternary ([.cv] ++ [.c]) = true ∧ licWasl ternary ([.cv, .c] ++ [.c]) = false := by decide

/-- **طلبُ ما بعدُ**: «c» يطلب حالةً متحرّكةً أو مدًّا قبله، ولا يقبل ساكنًا. -/
theorem shahid_talab :
    talab (ofNizam ternary) [.c] (some .cv) = true ∧ talab (ofNizam ternary) [.c] (some .v) = true ∧
    talab (ofNizam ternary) [.c] (some .c) = false := by decide

/-- **الوقفُ لا يورث**: «cv c c» مرخَّصٌ وقفًا، ولا يُوصل بعده شيء. -/
theorem shahid_waqf :
    licWaqf ternary [.cv, .c, .c] = true ∧ licWasl ternary [.cv, .c, .c] = false ∧
    licWaqf ternary ([.cv, .c, .c] ++ [.cv]) = false := by decide

/-! ## ٦. الجامع -/

/-- **القوانينُ الخمسة** لكلّ `Nizam`: الابتداءُ أوّلُ خطوة، والوصلُ والوقفُ توريث، والتوريثُ علاقةُ ما قبلُ بما بعدُ
عبر الحالة، والفصلُ بالسياق لا يقع بين ما ورّث حالةً واحدة. -/
theorem qawanin_khamsa [DecidableEq α] (N : Nizam α) :
    (∀ x, lic (ofNizam N) [x] = (N.wujud x && N.ibtida x)) ∧
    (∀ w, lic (ofNizam N) w = licWasl N w) ∧
    (∀ w, lic (ofNizamWaqf N) w = licWaqf N w) ∧
    (∀ a b, lic (ofNizam N) (a ++ b) = match run (ofNizam N) (ofNizam N).bad a with
      | some s => talab (ofNizam N) b s | none => false) ∧
    (∀ (S : List (List α)) a a',
      (a, a') ∈ mani (⟨run (ofNizam N) (ofNizam N).bad, S⟩ : Fasl (List α) (Option (Option α))) →
      ∀ b, licWasl N (a ++ b) = licWasl N (a' ++ b)) :=
  ⟨nizam_ibtida N, nizam_wasl N, nizam_waqf N, fun a b => by rw [lic_append]; cases run (ofNizam N) (ofNizam N).bad a <;> rfl, fun S a a' h b => by
    rw [← nizam_wasl, ← nizam_wasl]; exact tawrith_la_tafsil (ofNizam N) S a a' h b⟩

end A116.Tawrith
