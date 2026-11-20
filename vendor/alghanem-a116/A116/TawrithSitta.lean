import A116.Tawrith
import A116.MakharijIdgham
import A116.NizamHadd

/-!
# القوانينُ الستّة، والولادةُ محسوبة، والتوريثُ بين الطبقات (ADR ٧٦)

أمرُ المالك (2026-10-16) بثلاثة مقترحات:

1. **مبرهنةُ الأطراف** (`atraf`): الابتداءُ توريثٌ بلا وراثة — يرث من القانون وحده (`bad`) ولا خطوةَ تورثه
   (`BadFresh`)؛ والوصلُ وراثةٌ وتوريث؛ والوقفُ وراثةٌ بلا توريث — ما يورثه الأخيرُ لا يرثه أحد بل يحكم فيه الطرف، وفي
   `Nizam` وقفًا ما بعد زوج الوقف منقطع (`waqf_yaqta`). فالوراثةُ والتوريثُ قانونان، والقوانينُ ستّة
   (`qawanin_sitta`): الابتداء، الوصل، الوقف، الفصل، الوراثة (يرث آخرَ ما قبله، `wiratha_akhir`)، التوريث (ما يورثه
   هو ما يرثه ما بعده، `run_append`).
2. **الولادةُ محسوبة**: السببُ والمانعُ في `MakharijIdgham.Rd` مستخرجان من الحرفين — `Rd` دالّةٌ في المفتاح
   (مثلٌ؟، سبب؟، الموانع) على الأزواج الـ841 كلّها (`rd_hukm`)، فطرفا مانعٍ على المفتاح (`Fasl.mani`) حكمُهما واحد
   (`rd_la_tafsil`)، ومكوّناتُ المفتاح الثلاثة كلٌّ لازم (`miftah_mukhtamal`)؛ والشرطُ موضعٌ وحركة: الإدغامُ يولد ⟺
   الشرطُ ∧ `R` (`wilada`)، و`R` هو `Rd` بلا المسكوت عنه (`R_eq_Rd_minus_maskut`).
3. **التوريثُ بين الطبقات**: الكلمةُ ترث حالةَ ما قبلها وتورث حالةَ آخرها (`liftT`)، فتوريثُ الكلمات توريثُ تسطيحها
   (`lic_lift`)، ثمّ السطرُ (`lift_lift`)؛ وبعنصر حدٍّ بين الكلمات (`liftH`) هو توريثُ السطر بحدوده (`lic_liftH`)؛
   وقيدُ الحدّ نفسُه توريثٌ على الأزواج بشرط الطرف (`strictB_is_tawrith`).
-/

namespace A116.TawrithSitta

open A116 A116.Nizam A116.Fasl A116.Tawrith

variable {α σ : Type}

/-! ## ١. الأطراف -/

/-- **لا خطوةَ تورث حالةَ الابتداء**: الابتداءُ يرث من القانون لا من سابق. -/
def BadFresh (T : Tawrith α σ) : Prop := ∀ s x, T.step s x ≠ some T.bad

theorem run_ne_bad (T : Tawrith α σ) (hb : BadFresh T) :
    ∀ (s : σ) (u : List α), u ≠ [] → ∀ s', Tawrith.run T s u = some s' → s' ≠ T.bad
  | _, [], hu, _, _ => absurd rfl hu
  | s, [x], _, s', hr => by
    simp only [Tawrith.run] at hr
    cases hx : T.step s x with
    | none => simp [hx] at hr
    | some s1 =>
      simp only [hx, Option.some.injEq] at hr
      intro e
      exact hb s x (by rw [hx, hr, e])
  | s, x :: y :: r, _, s', hr => by
    simp only [Tawrith.run] at hr
    cases hx : T.step s x with
    | none => simp [hx] at hr
    | some s1 =>
      simp only [hx] at hr
      exact run_ne_bad T hb s1 (y :: r) (by simp) s' (by simpa [Tawrith.run] using hr)

/-- **مبرهنةُ الأطراف**: الابتداءُ يرث من القانون ويورث؛ والوسطُ يرث من سابقٍ لا من الابتداء ويورث؛ والأخيرُ يرث
ولا يرث ما يورثه أحد — يحكم فيه الطرفُ وحدَه. -/
theorem atraf (T : Tawrith α σ) (hb : BadFresh T) :
    (∀ x v, lic T (x :: v) = true → ∃ s', T.step T.bad x = some s' ∧ talab T v s' = true) ∧
    (∀ u x v, u ≠ [] → lic T (u ++ x :: v) = true →
      ∃ s s', Tawrith.run T T.bad u = some s ∧ s ≠ T.bad ∧ T.step s x = some s' ∧ talab T v s' = true) ∧
    (∀ u x, lic T (u ++ [x]) = true ↔
      ∃ s s', Tawrith.run T T.bad u = some s ∧ T.step s x = some s' ∧ T.waqf s' = true) := by
  refine ⟨fun x v h => ?_, fun u x v hu h => ?_, fun u x => ?_⟩
  · obtain ⟨s, s', hs, hx, hv⟩ := (wasat T [] x v).1 h
    simp only [Tawrith.run, Option.some.injEq] at hs
    exact ⟨s', hs ▸ hx, hv⟩
  · obtain ⟨s, s', hs, hx, hv⟩ := (wasat T u x v).1 h
    exact ⟨s, s', hs, run_ne_bad T hb _ u hu s hs, hx, hv⟩
  · rw [wasat]
    rfl

theorem fresh_ofNizam (N : Nizam α) : BadFresh (ofNizam N) := by
  intro s x h
  cases s with
  | none =>
    change (if N.wujud x && N.ibtida x then some (some x) else none) = some none at h
    split at h <;> simp at h
  | some a =>
    change (if N.wujud x && N.wasl a x then some (some x) else none) = some none at h
    split at h <;> simp at h

theorem fresh_ofNizamWaqf (N : Nizam α) : BadFresh (ofNizamWaqf N) := by
  intro s x h
  obtain ⟨o, f⟩ := s
  cases o with
  | none =>
    change (if N.wujud x && N.ibtida x then some (some x, false) else none) = some (none, false) at h
    split at h <;> simp at h
  | some a =>
    cases f with
    | true => exact absurd h (by simp [waqf_la_yuwarrith])
    | false =>
      change (if N.wujud x then
        (if N.wasl a x then some (some x, false) else if N.waqf a x then some (some x, true) else none)
        else none) = some (none, false) at h
      split at h
      · split at h
        · simp at h
        · split at h <;> simp at h
      · simp at h

theorem fresh_hajah : BadFresh hajah := by
  intro s x h
  change Hajah.needStep s x = some none at h
  cases x <;> cases s <;> simp [Hajah.needStep] at h
  all_goals split at h <;> simp at h

/-- **الوقفُ وراثةٌ بلا توريث**: ما بعد زوج الوقف منقطعٌ كلُّه. -/
theorem waqf_yaqta (N : Nizam α) (a : α) (v : List α) (hv : v ≠ []) :
    Tawrith.run (ofNizamWaqf N) (some a, true) v = none := by
  cases v with
  | nil => exact absurd rfl hv
  | cons x v => exact mani_yaqta _ _ x (waqf_la_yuwarrith N a x) v

/-- **الوراثة**: ما يرثه الموضعُ في `Nizam` هو آخرُ ما قبله. -/
theorem wiratha_akhir (N : Nizam α) : ∀ (st : Option α) (u : List α) (s : Option α),
    Tawrith.run (ofNizam N) st u = some s → s = u.getLast?.or st
  | st, [], s, h => by simp [Tawrith.run] at h; simp [h]
  | st, x :: u, s, h => by
    have ih := wiratha_akhir N (some x) u s
    have key : (ofNizam N).step st x = none ∨ (ofNizam N).step st x = some (some x) := by
      cases st with
      | none =>
        change (if N.wujud x && N.ibtida x then some (some x) else none) = none ∨
          (if N.wujud x && N.ibtida x then some (some x) else none) = some (some x)
        split <;> simp
      | some a =>
        change (if N.wujud x && N.wasl a x then some (some x) else none) = none ∨
          (if N.wujud x && N.wasl a x then some (some x) else none) = some (some x)
        split <;> simp
    simp only [Tawrith.run] at h
    rcases key with hk | hk <;> simp only [hk] at h
    · cases h
    · rw [ih h]
      cases u with
      | nil => rfl
      | cons y u =>
        rw [List.getLast?_cons_cons]
        cases hz : (y :: u).getLast? with
        | none => simp at hz
        | some z => rfl

/-- **القوانينُ الستّة** لكلّ `Nizam`: الابتداء، والوصل، والوقف (ولا يورث)، والفصل، والوراثة (آخرُ ما قبله)،
والتوريث (ما يورثه هو ما يرثه ما بعده، ولا يورث أحدٌ حالةَ الابتداء). -/
theorem qawanin_sitta [DecidableEq α] (N : Nizam α) :
    (∀ x, lic (ofNizam N) [x] = (N.wujud x && N.ibtida x)) ∧
    (∀ w, lic (ofNizam N) w = licWasl N w) ∧
    ((∀ w, lic (ofNizamWaqf N) w = licWaqf N w) ∧
      ∀ a v, v ≠ [] → Tawrith.run (ofNizamWaqf N) (some a, true) v = none) ∧
    (∀ (S : List (List α)) a a',
      (a, a') ∈ mani (⟨Tawrith.run (ofNizam N) (ofNizam N).bad, S⟩ : Fasl (List α) (Option (Option α))) →
      ∀ b, licWasl N (a ++ b) = licWasl N (a' ++ b)) ∧
    (∀ u s, Tawrith.run (ofNizam N) none u = some s → s = u.getLast?) ∧
    ((∀ u v, Tawrith.run (ofNizam N) none (u ++ v) = (Tawrith.run (ofNizam N) none u).bind fun s => Tawrith.run (ofNizam N) s v) ∧
      BadFresh (ofNizam N)) := by
  obtain ⟨h1, h2, h3, _, h5⟩ := qawanin_khamsa N
  refine ⟨h1, h2, ⟨h3, waqf_yaqta N⟩, h5, fun u s h => ?_, ⟨fun u v => run_append _ _ u v, fresh_ofNizam N⟩⟩
  have := wiratha_akhir N none u s h
  cases hu : u.getLast? <;> simp_all

/-! ## ٢. الولادةُ محسوبة: السببُ والمانعُ من الحرفين -/

open A116.MakharijIdgham

/-- مفتاحُ الزوج: أمثلان؟ وهل له سبب؟ وموانعُه. -/
def miftah (a b : Char) : Bool × Bool × List Mani := (a == b, !(asbab a b).isEmpty, mawani a b)

/-- الحكمُ على المفتاح: المثلُ يُدغم إلّا بالهمزة والألف، وغيرُه بسببٍ بلا مانع. -/
def hukm : Bool × Bool × List Mani → Bool
  | (true, _, ms) => !(ms.contains .hamzaAlif)
  | (false, s, ms) => s && ms.isEmpty

/-- **`Rd` دالّةٌ في المفتاح** على الأزواج الـ841 كلّها. -/
theorem rd_hukm : allPairs.all (fun p => Rd p.1 p.2 == hukm (miftah p.1 p.2)) = true := by decide +kernel

/-- الفصلُ على الأزواج بالمفتاح. -/
def faslRd : Fasl (Char × Char) (Bool × Bool × List Mani) := ⟨fun p => miftah p.1 p.2, allPairs⟩

theorem hukm_factor {β γ : Type} [DecidableEq α] [DecidableEq β] (S : List α) (f : α → β) (g : α → γ)
    (h : β → γ) (hS : ∀ x ∈ S, g x = h (f x)) (x y : α) (hm : (x, y) ∈ mani (⟨f, S⟩ : Fasl α β)) :
    g x = g y := by
  obtain ⟨hx, hy, _, he⟩ := (mem_mani _ x y).1 hm
  rw [hS x hx, hS y hy]
  exact congrArg h he

/-- **طرفا مانعٍ على المفتاح حكمُهما واحد**: السببُ والمانعُ يكفيان. -/
theorem rd_la_tafsil (p q : Char × Char) (hm : (p, q) ∈ mani faslRd) : Rd p.1 p.2 = Rd q.1 q.2 := by
  have hS : ∀ x ∈ allPairs, Rd x.1 x.2 = hukm (miftah x.1 x.2) := by
    have := rd_hukm
    rw [List.all_eq_true] at this
    intro x hx
    simpa using this x hx
  exact hukm_factor allPairs (fun p => miftah p.1 p.2) (fun p => Rd p.1 p.2) hukm hS p q hm

/-- **ومكوّناتُ المفتاح الثلاثة كلٌّ لازم**: زوجان يتّفقان في اثنين ويختلف حكمُهما. -/
theorem miftah_mukhtamal :
    -- المثل: مَم ومَب يتّفقان في السبب والموانع
    ((miftah 'م' 'م').2 = (miftah 'م' 'ب').2 ∧ Rd 'م' 'م' ≠ Rd 'م' 'ب') ∧
    -- المانع: لر ومب يتّفقان في المثل والسبب
    ((miftah 'ل' 'ر').1 = (miftah 'م' 'ب').1 ∧ (miftah 'ل' 'ر').2.1 = (miftah 'م' 'ب').2.1 ∧
      Rd 'ل' 'ر' ≠ Rd 'م' 'ب') ∧
    -- السبب: لر وبك يتّفقان في المثل والموانع
    ((miftah 'ل' 'ر').1 = (miftah 'ب' 'ك').1 ∧ (miftah 'ل' 'ر').2.2 = (miftah 'ب' 'ك').2.2 ∧
      Rd 'ل' 'ر' ≠ Rd 'ب' 'ك') := by decide

/-- شرطُ الموضع: الثاني متحرّك، وما قبل الأوّل متحرّكٌ أو مدّ. -/
def shart (q : Qabl) (h : Haraka) : Bool := h != .sukun && (q == .mutaharrik || q == .madd)

/-- **الولادة**: الإدغامُ يولد ⟺ الشرطُ ∧ `R`. -/
theorem wilada (q : Qabl) (a b : Char) (h : Haraka) :
    idghamAt q a b h = .idgham (merged b h) ↔ shart q h = true ∧ R a b = true := by
  cases q <;> cases h <;> cases hr : R a b <;> simp [idghamAt, shart, hr]

/-- **و`R` هو `Rd` بلا المسكوت عنه**: السببُ والمانعُ يحكمان، والشاهدُ يرفع السكوت. -/
theorem R_eq_Rd_minus_maskut :
    allPairs.all (fun p => R p.1 p.2 == (Rd p.1 p.2 && qism p.1 p.2 != .maskut)) = true := by decide +kernel

/-! ## ٣. التوريثُ بين الطبقات -/

theorem run_cons (T : Tawrith α σ) (s : σ) (x : α) (r : List α) :
    Tawrith.run T s (x :: r) = (T.step s x).bind fun s' => Tawrith.run T s' r := by
  simp only [Tawrith.run]
  cases T.step s x <;> rfl

/-- **الكلمةُ ترث حالةَ ما قبلها وتورث حالةَ آخرها.** -/
def liftT (T : Tawrith α σ) : Tawrith (List α) σ where
  bad := T.bad
  step s w := Tawrith.run T s w
  waqf := T.waqf

theorem run_lift (T : Tawrith α σ) : ∀ (s : σ) (ws : List (List α)),
    Tawrith.run (liftT T) s ws = Tawrith.run T s ws.flatten
  | s, [] => rfl
  | s, w :: ws => by
    rw [List.flatten_cons, run_append]
    show (match Tawrith.run T s w with | some s' => Tawrith.run (liftT T) s' ws | none => none) = _
    cases Tawrith.run T s w with
    | none => rfl
    | some s' => exact run_lift T s' ws

/-- **توريثُ الكلمات توريثُ تسطيحها.** -/
theorem lic_lift (T : Tawrith α σ) (ws : List (List α)) : lic (liftT T) ws = lic T ws.flatten := by
  unfold lic
  rw [run_lift]
  rfl

/-- **ثمّ السطور**: بلا حدّ. -/
theorem lift_lift (T : Tawrith α σ) (wss : List (List (List α))) :
    lic (liftT (liftT T)) wss = lic T wss.flatten.flatten := by
  rw [lic_lift, lic_lift]

/-- السطرُ بعنصر حدٍّ `b` بين كلّ كلمتين. -/
def junc (b : α) : List (List α) → List α
  | [] => []
  | w :: ws => w ++ ws.flatMap (b :: ·)

/-- **الكلمةُ بحدّها**: الأولى ترث من الابتداء، وما بعدها يرث عبر الحدّ. -/
def liftH (T : Tawrith α σ) (b : α) : Tawrith (List α) (Bool × σ) where
  bad := (false, T.bad)
  step p w := if p.1 then (Tawrith.run T p.2 (b :: w)).map ((true, ·)) else (Tawrith.run T p.2 w).map ((true, ·))
  waqf p := T.waqf p.2

theorem run_liftH_true (T : Tawrith α σ) (b : α) : ∀ (s : σ) (ws : List (List α)),
    (Tawrith.run (liftH T b) (true, s) ws).map Prod.snd = Tawrith.run T s (ws.flatMap (b :: ·))
  | s, [] => rfl
  | s, w :: ws => by
    rw [List.flatMap_cons, run_append, run_cons (liftH T b)]
    rw [show (liftH T b).step (true, s) w = (Tawrith.run T s (b :: w)).map ((true, ·)) from rfl]
    cases Tawrith.run T s (b :: w) with
    | none => rfl
    | some s' => exact run_liftH_true T b s' ws


/-- **توريثُ السطر بحدوده**: الكلماتُ بعنصر الحدّ توريثُ سطرها. -/
theorem lic_liftH (T : Tawrith α σ) (b : α) (ws : List (List α)) :
    lic (liftH T b) ws = lic T (junc b ws) := by
  cases ws with
  | nil => rfl
  | cons w ws =>
    unfold lic
    rw [junc, run_append, run_cons (liftH T b)]
    rw [show (liftH T b).step (liftH T b).bad w = (Tawrith.run T T.bad w).map ((true, ·)) from rfl]
    cases Tawrith.run T T.bad w with
    | none => rfl
    | some s =>
      show qubul (liftH T b) (Tawrith.run (liftH T b) (true, s) ws) = qubul T (Tawrith.run T s _)
      rw [← run_liftH_true T b s ws]
      cases Tawrith.run (liftH T b) (true, s) ws <;> rfl

/-- **الشاهد**: الكلمةُ الثانية ترث آخرَ الأولى لا الابتداء — «cv» بعد «cv c» يُوصل، و«c» بعده لا. -/
theorem shahid_tabaqat :
    lic (liftT (ofNizam ternary)) [[.cv, .c], [.cv]] = true ∧
    lic (liftT (ofNizam ternary)) [[.cv, .c], [.c]] = false ∧
    lic (ofNizam ternary) [.c] = false := by
  refine ⟨?_, ?_, by decide⟩ <;> rw [lic_lift] <;> decide

/-! ## ٤. قيدُ الحدّ توريثًا -/

/-- `Nizam` وصلًا بشرط طرفٍ على الموروث الأخير. -/
def ofNizamTaraf (N : Nizam α) (q : Option α → Bool) : Tawrith α (Option α) :=
  { ofNizam N with waqf := q }

theorem run_taraf (N : Nizam α) (q : Option α → Bool) : ∀ (s : Option α) (w : List α),
    Tawrith.run (ofNizamTaraf N q) s w = Tawrith.run (ofNizam N) s w
  | _, [] => rfl
  | s, x :: w => by
    simp only [Tawrith.run]
    rw [show (ofNizamTaraf N q).step s x = (ofNizam N).step s x from rfl]
    cases (ofNizam N).step s x with
    | none => rfl
    | some s' => exact run_taraf N q s' w

/-- **الوصلُ بشرط الطرف توريث**: ترخيصُ `Nizam` وشرطُ الطرف على الآخر. -/
theorem lic_taraf (N : Nizam α) (q : Option α → Bool) (w : List α) :
    lic (ofNizamTaraf N q) w = (licWasl N w && q w.getLast?) := by
  rw [← nizam_wasl]
  unfold lic
  rw [run_taraf, show (ofNizamTaraf N q).bad = (ofNizam N).bad from rfl]
  cases hr : Tawrith.run (ofNizam N) (ofNizam N).bad w with
  | none => rfl
  | some s =>
    have := wiratha_akhir N none w s hr
    cases hl : w.getLast? <;> simp_all [qubul, ofNizamTaraf, ofNizam]

open A116.NizamHadd A116.Hadd in
/-- شرطُ الطرف على الزوج الأخير: لا مدَّ ثمّ مُغلِقًا. -/
def tarafEdge : Option (Role × Role) → Bool
  | some e => !(e.1.1 == .v && e.2.1 == .c)
  | none => true

open A116.NizamHadd in
theorem taraf_azwaj : ∀ l : List Role, 2 ≤ l.length → tarafWasl l = tarafEdge (azwaj l).getLast?
  | [], h => by simp at h
  | [_], h => by simp at h
  | [a, b], _ => rfl
  | a :: b :: c :: t, _ => by
    rw [show tarafWasl (a :: b :: c :: t) = tarafWasl (b :: c :: t) from rfl,
      taraf_azwaj (b :: c :: t) (by simp)]
    show _ = tarafEdge ((a, b) :: azwaj (b :: c :: t)).getLast?
    rw [show azwaj (b :: c :: t) = (b, c) :: azwaj (c :: t) from rfl, List.getLast?_cons_cons]

open A116.NizamHadd A116.Hadd in
/-- **قيدُ الحدّ توريث**: `strictB` ترخيصُ توريث الأزواج بشرط الطرف. -/
theorem strictB_is_tawrith (w : List Cell) (hf : isFarq w = false) (hl : 2 ≤ w.length) :
    strictB w = lic (ofNizamTaraf haddN tarafEdge) (azwaj (roles w)) := by
  have hlen : (roles w).length = w.length := by simp [roles, kindOf, kindGo_length]
  rw [strictB_is_nizam w hf hl, lic_taraf, taraf_azwaj _ (by omega)]

end A116.TawrithSitta
