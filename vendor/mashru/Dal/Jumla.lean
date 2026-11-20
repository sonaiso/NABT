/-
  Dal/Jumla.lean — الجملة في الوصل: تركيب سلاسل الكلمات على قانون المالك.

  القانون عند المالك: آلة الجملة `SLGE.Law.Msent` (الخانات وحدُّ الكلمة 116، والوقفُ على آخرها)، وسقوطُ همزة الوصل
  في الوصل بالإصلاح الأدنى الحافظ للوزن (SLGE/Hamza.lean): بعد متحرّك تسقط بلا إصلاح (`wasl_after_mover`)؛
  بعد مدٍّ يلتقي ساكنان فيُحذف المدّ (`wasl_after_madd`)؛ بعد ساكنٍ مُغلِق يلتقي ساكنان فيُحرَّك (`wasl_after_closed`)،
  واختيارُ الكسرة وسيطٌ معلَن.

  ما يُبنى هنا (تنفيذيّ، مبرهَن عليه):
  * `isqatHamza`: الكلمة التي أوّلها همزة وصل — ولا تكون إلّا قبل ساكن (Hamza.lean: «الكلمةُ التي أوّلُها ساكن») —
    تُوصل بما قبلها بحسب حالة القانون بعده؛ وما سوى الحالات الثلاث، أو كلمةٌ أوّلُها متحرّك، لا حكم (`isqat_ghayr_sakin`).
  * `rakkib`: الكلمة الأولى في صورة الابتداء (`ibtidaForm`)، وكلّ تالية إمّا بهمزة وصل فتسقط، وإمّا بحدّ الكلمة 116
    وآلةُ المالك تحكم عنده: ما آخره ساكنان لا يوصل (`laTusal`)، وما آخره مدٌّ ثمّ ساكنٌ معلَّقٌ على الإدغام يعبر الحدّ
    ولا يحيا إلّا بمتحرّكٍ من حامله أوّلَ الكلمة التالية (δ في Law.lean: 6+k ← 38+k؛ شاهده `shahid_idgham_hadd`)؛
    وأوّلُ موتٍ في السلسلة يُسمّى بكلمته (`Khalal`).
  * `qattaJumla`: تقطيع الجملة كلماتٍ صوتيّةً (`splitH` عند المالك) ومقاطعَ (`qatta`)؛ صحيحٌ بالبناء (`qattaJumla_sahih`)
    وواحدٌ بمبرهنة المالك `sentChain_inj` (`qattaJumla_wahid`).
  المبرهنات العامّة: `rakkib_abjadiyya` (لا رمز فوق 116)، `jumla_murakhkhasa` (ما رخّصه الوقف بعد التركيب مرخَّصٌ بآلة
  المالك `Msent` وله تقطيع — من `sent_structure`)، `isqat_mover`/`isqat_madd`/`isqat_closed` (إصلاحُنا هو إصلاح المالك
  بعينه، بمبرهناته). والشواهد: أمثلة المالك الثلاثة في Hamza.lean، وحدُّ الكلمة، والكلمة التي لا توصل.
-/
import Dal.Qanun

namespace Dal
open SLGE SLGE.Law

/-! ## ١. الكلمة والإصلاح -/

/-- كلمة كما يسلّمها القارئ: خلاياها بلا همزة الوصل، وهل أوّلها همزة وصل (أي يبدأ أصلها بساكن)،
وهل همزتها همزة «أل» (فحركتها في الابتداء فتحة — وسيط المالك `waslHaraka`). -/
structure Kalima where
  khalaya : List Nat
  wasl : Bool
  al : Bool := false
deriving DecidableEq, Repr

/-- همزة «أل» حين تكون اللام خليةً: أوّل الخلايا لامٌ ساكنة (وسيط معلَن؛ والقارئ يعلّمها أيضًا حين تُدغم اللام). -/
def isAl (l : List Nat) : Bool := l.head? == some (4 * 13 + 3)

/-- صورة الابتداء: تُزاد همزة الوصل بحركتها (`SLGE.Law.ibtidaForm`، `waslHaraka`) إن كانت الكلمة ذاتَ همزة وصل. -/
def ibtida (w : Kalima) : List Nat := if w.wasl then ibtidaForm w.al w.khalaya else w.khalaya

/-- حركة الساكن المُغلِق عند التقاء الساكنين بسقوط همزة الوصل: الكسرة — وسيط المالك المعلَن (Hamza.lean). -/
def harakatIltiqa : Nat := 2

theorem harakatIltiqa_lt : harakatIltiqa < 3 := by decide

/-- ما يفعله الوصل بهمزة الوصل. -/
inductive Islah
  | la          -- بعد متحرّك: تسقط بلا إصلاح
  | hadhfMadd   -- بعد مدّ: يُحذف المدّ
  | tahrik      -- بعد ساكن مُغلِق: يُحرَّك بالكسر
deriving DecidableEq, Repr

/-- أوّل الكلمة ساكن (خليةٌ حالتُها 3). -/
def sakinAwwal (v : List Nat) : Bool :=
  match v.head? with
  | some a => a < 116 && a % 4 == 3
  | none => false

/-- سقوط همزة الوصل: `l` ما قبلها مركَّبًا، و`v` خلايا الكلمة بلا همزتها (وأوّلها ساكن، وإلّا فلا حكم).
الحكم بحالة القانون بعد `l`. -/
def isqatHamza (l v : List Nat) : Option (List Nat × Islah) :=
  if !sakinAwwal v then none else
  let q := run 0 l
  if 1 ≤ q ∧ q ≤ 3 then some (l ++ v, .la)
  else if q = 4 then some (l.dropLast ++ v, .hadhfMadd)
  else if 67 ≤ q ∧ q < 96 then
    match l.getLast? with
    | some a => if a < 116 then some (l.dropLast ++ (4 * (a / 4) + harakatIltiqa) :: v, .tahrik) else none
    | none => none
  else none

/-! ## ٢. التركيب -/

/-- الخلل في التركيب باسمه، ورقمُ الكلمة من 1. -/
inductive Khalal
  | mayyita (i : Nat)   -- الكلمة i ممتنعة بالقانون في موضعها
  | laTusal (i : Nat)   -- الكلمة i لا توصل بما بعدها: آخرها ساكنان (الوقف لا الوصل؛ δ: 35/36 ثمّ 116 ← 96)
  | laHukm (i : Nat)    -- همزة وصل بعد حالةٍ ليس عند المالك إصلاحٌ لها
  | farigha             -- لا كلمات
deriving DecidableEq, Repr

structure Natija where
  silsila : List Nat := []
  islahat : List (Nat × Islah) := []
  khalal : Option Khalal := none
deriving DecidableEq, Repr

/-- التركيب من الكلمة الثانية: همزة وصل تسقط، أو حدّ الكلمة 116؛ ويُفحص بعد كلّ خطوة أنّ السلسلة حيّة. -/
def rakkibAux : List Nat → List (Nat × Islah) → Nat → List Kalima → Natija
  | l, ms, _, [] => { silsila := l, islahat := ms }
  | l, ms, i, w :: ws =>
    if w.wasl then
      match isqatHamza l w.khalaya with
      | none => { silsila := l, islahat := ms, khalal := some (.laHukm i) }
      | some (l', s) =>
        if run 0 l' = 96 then { silsila := l', islahat := ms ++ [(i, s)], khalal := some (.mayyita i) }
        else rakkibAux l' (ms ++ [(i, s)]) (i + 1) ws
    else if run 0 (l ++ [116]) = 96 then { silsila := l, islahat := ms, khalal := some (.laTusal (i - 1)) }
    else if run 0 (l ++ 116 :: w.khalaya) = 96 then
      { silsila := l ++ 116 :: w.khalaya, islahat := ms, khalal := some (.mayyita i) }
    else rakkibAux (l ++ 116 :: w.khalaya) ms (i + 1) ws

/-- تركيب الجملة في الوصل. -/
def rakkib : List Kalima → Natija
  | [] => { khalal := some .farigha }
  | w :: ws =>
    if run 0 (ibtida w) = 96 then { silsila := ibtida w, khalal := some (.mayyita 1) }
    else rakkibAux (ibtida w) [] 2 ws

/-- الكلمة الواحدة: صورةُ ابتدائها، بلا إصلاح. -/
theorem rakkib_wahida (w : Kalima) : (rakkib [w]).silsila = ibtida w ∧ (rakkib [w]).islahat = [] := by
  simp only [rakkib]
  split <;> exact ⟨rfl, rfl⟩

/-! ## ٣. الأبجدية: التركيب لا يُخرج رمزًا فوق آلة المالك -/

theorem ibtidaForm_lt (b : Bool) : ∀ (l : List Nat), (∀ a ∈ l, a < 116) → ∀ a ∈ ibtidaForm b l, a < 117
  | [], _ => fun a ha => by simp [ibtidaForm] at ha
  | [a], hl => fun x hx => Nat.lt_of_lt_of_le (hl x (by simpa [ibtidaForm] using hx)) (by omega)
  | a :: m :: rest, hl => by
    simp only [ibtidaForm]
    split
    · intro x hx
      simp only [List.mem_cons] at hx
      rcases hx with rfl | hx
      · have := waslHaraka_lt b m; omega
      · exact Nat.lt_of_lt_of_le (hl x (by simpa using hx)) (by omega)
    · intro x hx; exact Nat.lt_of_lt_of_le (hl x hx) (by omega)

theorem ibtida_lt (w : Kalima) (hw : ∀ a ∈ w.khalaya, a < 116) : ∀ a ∈ ibtida w, a < 117 := by
  unfold ibtida; split
  · exact ibtidaForm_lt _ _ hw
  · exact fun a ha => Nat.lt_of_lt_of_le (hw a ha) (by omega)

theorem isqatHamza_lt (l v : List Nat) (hl : ∀ a ∈ l, a < 117) (hv : ∀ a ∈ v, a < 116) (l' : List Nat)
    (s : Islah) (h : isqatHamza l v = some (l', s)) : ∀ a ∈ l', a < 117 := by
  have hd : ∀ a ∈ l.dropLast, a < 117 := fun a ha => hl a ((List.dropLast_sublist l).subset ha)
  have hv' : ∀ a ∈ v, a < 117 := fun a ha => Nat.lt_of_lt_of_le (hv a ha) (by omega)
  unfold isqatHamza at h
  simp only at h
  split at h
  · cases h
  split at h
  · cases h
    intro a ha; rw [List.mem_append] at ha
    exact ha.elim (hl a) (hv' a)
  · split at h
    · cases h
      intro a ha; rw [List.mem_append] at ha
      exact ha.elim (hd a) (hv' a)
    · split at h
      · split at h
        · split at h
          · cases h
            intro a ha; rw [List.mem_append, List.mem_cons] at ha
            rcases ha with ha | rfl | ha
            · exact hd a ha
            · have := harakatIltiqa_lt; omega
            · exact hv' a ha
          · cases h
        · cases h
      · cases h

theorem rakkibAux_lt : ∀ (ws : List Kalima) (l : List Nat) (ms : List (Nat × Islah)) (i : Nat),
    (∀ a ∈ l, a < 117) → (∀ w ∈ ws, ∀ a ∈ w.khalaya, a < 116) → ∀ a ∈ (rakkibAux l ms i ws).silsila, a < 117
  | [], l, ms, i, hl, _ => by simpa [rakkibAux] using hl
  | w :: ws, l, ms, i, hl, hws => by
    have hw : ∀ a ∈ w.khalaya, a < 116 := hws w (by simp)
    have hws' : ∀ w' ∈ ws, ∀ a ∈ w'.khalaya, a < 116 := fun w' h => hws w' (by simp [h])
    have hb : ∀ a ∈ l ++ 116 :: w.khalaya, a < 117 := by
      intro a ha
      simp only [List.mem_append, List.mem_cons] at ha
      rcases ha with ha | rfl | ha
      · exact hl a ha
      · omega
      · exact Nat.lt_of_lt_of_le (hw a ha) (by omega)
    simp only [rakkibAux]
    split
    · split
      · simpa using hl
      · rename_i l' s h
        have hl' := isqatHamza_lt l w.khalaya hl hw l' s h
        split
        · simpa using hl'
        · exact rakkibAux_lt ws l' _ (i + 1) hl' hws'
    · split
      · simpa using hl
      · split
        · simpa using hb
        · exact rakkibAux_lt ws _ ms (i + 1) hb hws'

/-- **الأبجدية:** سلسلة التركيب كلُّها رموزُ آلة المالك `Msent` (دون 117). -/
theorem rakkib_abjadiyya (ws : List Kalima) (hws : ∀ w ∈ ws, ∀ a ∈ w.khalaya, a < 116) :
    ∀ a ∈ (rakkib ws).silsila, a < 117 := by
  cases ws with
  | nil => simp [rakkib]
  | cons w ws =>
    have hw := ibtida_lt w (hws w (by simp))
    simp only [rakkib]
    split
    · simpa using hw
    · exact rakkibAux_lt ws _ [] 2 hw (fun w' h => hws w' (by simp [h]))

/-- **الترخيص:** ما رخّصه الوقفُ بعد التركيب مرخَّصٌ بآلة الجملة عند المالك، فله تقطيعٌ كلماتٍ ومقاطعَ (`sent_structure`). -/
theorem jumla_murakhkhasa (ws : List Kalima) (hws : ∀ w ∈ ws, ∀ a ∈ w.khalaya, a < 116)
    (hF : Fwaqf (run 0 (rakkib ws).silsila) = true) :
    Msent.Lic 0 (rakkib ws).silsila ∧ ∃ S, ValidS S ∧ sentChain S = (rakkib ws).silsila := by
  have hLic : Msent.Lic 0 (rakkib ws).silsila :=
    ⟨rakkib_abjadiyya ws hws, by show Msent.F (Msent.runL 0 _) = true; rw [Msent, mk_run]; exact hF⟩
  exact ⟨hLic, sent_structure _ hLic⟩

/-! ## ٤. التقطيع التنفيذيّ للجملة: صحيحٌ بالبناء، واحدٌ بمبرهنة المالك -/

def qattaKull : List (List Nat) → Option (List (List Syl))
  | [] => some []
  | p :: ps =>
    match qatta p, qattaKull ps with
    | some w, some S => some (w :: S)
    | _, _ => none

/-- تقطيع الجملة: كلماتها الصوتيّة بحدّ الكلمة (`splitH`) ثمّ مقاطع كلّ كلمة؛ ولا كلمة فارغة. -/
def qattaJumla (l : List Nat) : Option (List (List Syl)) :=
  if (splitH l).any (· == []) then none else qattaKull (splitH l)

/-- ضمّ الكلمات الصوتيّة بحدّ الكلمة — مرآة `sentChain` على السلاسل. -/
def joinH : List (List Nat) → List Nat
  | [] => []
  | [u] => u
  | u :: v :: us => u ++ 116 :: joinH (v :: us)

theorem sentChain_eq_joinH : ∀ S : List (List Syl), sentChain S = joinH (S.map wordChain)
  | [] => rfl
  | [_] => rfl
  | w :: v :: S => by
    simp only [sentChain, List.map, joinH]
    rw [sentChain_eq_joinH (v :: S)]; rfl

theorem splitH_ne_nil : ∀ l : List Nat, splitH l ≠ []
  | [] => by simp [splitH]
  | a :: l => by
    simp only [splitH]
    split
    · simp
    · split <;> simp

theorem joinH_cons_nil (ps : List (List Nat)) (h : ps ≠ []) : joinH ([] :: ps) = 116 :: joinH ps := by
  cases ps with
  | nil => exact absurd rfl h
  | cons v us => rfl

theorem joinH_cons_cons (a : Nat) (u : List Nat) (us : List (List Nat)) :
    joinH ((a :: u) :: us) = a :: joinH (u :: us) := by
  cases us <;> rfl

theorem joinH_splitH : ∀ l : List Nat, joinH (splitH l) = l
  | [] => rfl
  | a :: l => by
    have ih := joinH_splitH l
    simp only [splitH]
    split
    · rename_i h; subst h
      rw [joinH_cons_nil _ (splitH_ne_nil l), ih]
    · split
      · rename_i h; exact absurd h (splitH_ne_nil l)
      · rename_i u us h
        rw [joinH_cons_cons, ← h, ih]

theorem qattaKull_sahih : ∀ (ps : List (List Nat)) (S : List (List Syl)), qattaKull ps = some S →
    (∀ p ∈ ps, p ≠ []) → S.map wordChain = ps ∧ ValidS S
  | [], S, h, _ => by
    simp only [qattaKull, Option.some.injEq] at h
    subst h; exact ⟨rfl, fun v hv => by simp at hv⟩
  | p :: ps, S, h, hne => by
    simp only [qattaKull] at h
    split at h
    · rename_i w S' hw hS'
      cases h
      obtain ⟨hwc, hwv⟩ := qatta_sahih p w hw
      obtain ⟨ih1, ih2⟩ := qattaKull_sahih ps S' hS' (fun q hq => hne q (by simp [hq]))
      refine ⟨by simp [ih1, hwc], ?_⟩
      intro v hv
      simp only [List.mem_cons] at hv
      rcases hv with rfl | hv
      · refine ⟨?_, hwv⟩
        intro hnil; subst hnil
        exact hne p (by simp) (by simpa [wordChain] using hwc.symm)
      · exact ih2 v hv
    · cases h

/-- **صحّة التقطيع بالبناء:** ما قطّعه `qattaJumla` كلماتٌ صحيحةُ المقاطع تعيد السلسلة بعينها. -/
theorem qattaJumla_sahih (l : List Nat) (S : List (List Syl)) (h : qattaJumla l = some S) :
    ValidS S ∧ sentChain S = l := by
  unfold qattaJumla at h
  split at h
  · cases h
  · rename_i hany
    have hne : ∀ p ∈ splitH l, p ≠ [] := by
      intro p hp hpn
      apply hany
      rw [List.any_eq_true]
      exact ⟨p, hp, by simp [hpn]⟩
    obtain ⟨h1, h2⟩ := qattaKull_sahih _ _ h hne
    exact ⟨h2, by rw [sentChain_eq_joinH, h1, joinH_splitH]⟩

/-- **وحدانيّة التقطيع:** أيّ تقطيعٍ صحيحٍ آخر للجملة هو هو (مبرهنة المالك `sentChain_inj`). -/
theorem qattaJumla_wahid (l : List Nat) (S S' : List (List Syl)) (h : qattaJumla l = some S)
    (hS' : ValidS S') (hne : S' ≠ []) (hc : sentChain S' = l) : S' = S := by
  obtain ⟨hv, hl⟩ := qattaJumla_sahih l S h
  have hSne : S ≠ [] := by
    intro e; subst e
    have : l = [] := hl.symm
    subst this
    exact absurd h (by decide)
  exact sentChain_inj S' S hS' hv hne hSne (hc.trans hl.symm)

/-! ## ٥. الإصلاح هو إصلاح المالك بعينه — بمبرهناته في Hamza.lean -/

/-- **لا حكم لكلمةٍ أوّلها متحرّك:** همزة الوصل لا تكون إلّا قبل ساكن، فلا إصلاحَ لغيره. -/
theorem isqat_ghayr_sakin (l v : List Nat) (h : sakinAwwal v = false) : isqatHamza l v = none := by
  unfold isqatHamza; simp [h]

theorem sakinAwwal_cons (c m : Nat) (rest : List Nat) (hc : c < 29) :
    sakinAwwal ((4 * c + 3) :: m :: rest) = true := by
  simp only [sakinAwwal, List.head?_cons, Bool.and_eq_true, decide_eq_true_eq, beq_iff_eq]
  omega

/-- **بعد متحرّك:** تسقط بلا إصلاح، وحالُ السلسلة بعدها حالُ البدء بما بعد الساكن (`wasl_after_mover`). -/
theorem isqat_mover (l : List Nat) (h c m : Nat) (rest : List Nat) (hh : h < 3) (hl : run 0 l = 1 + h)
    (hc : c < 29) (hc2 : c ≠ 2) (hm : m < 116) (hm3 : m % 4 < 3) (hmA : m / 4 ≠ 2)
    (hcf : conflict c (m / 4) = false) :
    isqatHamza l ((4 * c + 3) :: m :: rest) = some (l ++ (4 * c + 3) :: m :: rest, .la) ∧
    run 0 (l ++ (4 * c + 3) :: m :: rest) = run 0 (m :: rest) := by
  constructor
  · unfold isqatHamza; simp only [hl, sakinAwwal_cons c m rest hc, Bool.not_true, Bool.false_eq_true, ite_false]
    split
    · rfl
    · omega
  · rw [run_append, hl]; exact wasl_after_mover h c m hh hc hc2 hm hm3 hmA hcf rest

/-- **بعد مدّ:** بلا حذفٍ يلتقي ساكنان فتموت السلسلة؛ وحذفُ المدّ إصلاحُ المالك (`wasl_after_madd`). -/
theorem isqat_madd (l : List Nat) (h c m : Nat) (rest : List Nat) (hh : h < 3) (hl : run 0 l = 1 + h)
    (hc : c < 29) (hc2 : c ≠ 2) (hm : m < 116) (hm3 : m % 4 < 3) (hmA : m / 4 ≠ 2)
    (hcf : conflict c (m / 4) = false) (hne : m / 4 ≠ c) :
    run 0 (l ++ (4 * SLGE.maddOf h + 3) :: (4 * c + 3) :: m :: rest) = 96 ∧
    isqatHamza (l ++ [4 * SLGE.maddOf h + 3]) ((4 * c + 3) :: m :: rest) =
      some (l ++ (4 * c + 3) :: m :: rest, .hadhfMadd) ∧
    run 0 (l ++ (4 * c + 3) :: m :: rest) = run 0 (m :: rest) := by
  obtain ⟨h1, _, _, h4⟩ := wasl_after_madd h c m hh hc hc2 hm hm3 hmA hcf hne rest
  have e := (fin_madd_edit h hh 3 (by omega)).1
  simp only [show ¬ (3 < 3) from by omega, ite_false] at e
  refine ⟨by rw [run_append, hl]; exact h1, ?_, by rw [run_append, hl]; exact h4⟩
  have hq : run 0 (l ++ [4 * SLGE.maddOf h + 3]) = 4 := by rw [run_append, hl]; simp only [run]; exact e
  unfold isqatHamza
  simp only [hq, List.dropLast_concat, sakinAwwal_cons c m rest hc, Bool.not_true, Bool.false_eq_true, ite_false]
  rfl

/-- **بعد ساكن مُغلِق:** بلا تحريكٍ يلتقي ساكنان فتموت؛ وتحريكُه بالكسر إصلاحُ المالك (`wasl_after_closed`). -/
theorem isqat_closed (l : List Nat) (h k c m : Nat) (rest : List Nat) (hh : h < 3) (hl : run 0 l = 1 + h)
    (hk : k < 29) (hkm : k ≠ SLGE.maddOf h) (hk2 : k ≠ 2) (hc : c < 29) (hc2 : c ≠ 2) (hm : m < 116)
    (hm3 : m % 4 < 3) (hmA : m / 4 ≠ 2) (hcf : conflict c (m / 4) = false) :
    run 0 (l ++ (4 * k + 3) :: (4 * c + 3) :: m :: rest) = 96 ∧
    isqatHamza (l ++ [4 * k + 3]) ((4 * c + 3) :: m :: rest) =
      some (l ++ (4 * k + harakatIltiqa) :: (4 * c + 3) :: m :: rest, .tahrik) ∧
    run 0 (l ++ (4 * k + harakatIltiqa) :: (4 * c + 3) :: m :: rest) = run 0 (m :: rest) := by
  obtain ⟨h1, _, h3⟩ := wasl_after_closed h k c m hh hk hkm hk2 hc hc2 hm hm3 hmA hcf rest
  have e := (fin_closed_edit h hh k hk hkm hk2 3 (by omega)).1
  simp only [show ¬ (3 < 3) from by omega, ite_false] at e
  refine ⟨by rw [run_append, hl]; exact h1, ?_, by rw [run_append, hl]; exact (h3 _ harakatIltiqa_lt).2⟩
  have hq : run 0 (l ++ [4 * k + 3]) = 67 + k := by rw [run_append, hl]; simp only [run]; exact e
  unfold isqatHamza
  simp only [hq, List.getLast?_concat, List.dropLast_concat, sakinAwwal_cons c m rest hc, Bool.not_true,
    Bool.false_eq_true, ite_false]
  have e4 : (4 * k + 3) / 4 = k := by omega
  rw [e4]
  split
  · omega
  · split
    · omega
    · split
      · split
        · rfl
        · omega
      · omega

/-! ## ٦. الشواهد: أمثلة المالك الثلاثة (Hamza.lean)، وحدُّ الكلمة، والكلمة التي لا توصل
الخلايا بأرقامها 4c+s على جدول المخارج: ق 7، ا 2، ل 13، ك 8، ت 18، ب 26، و 28، م 27، ي 11، ن 14. -/

def shQala : Kalima := ⟨[28, 11, 52], false, false⟩   -- قَالَ
def shUktub : Kalima := ⟨[35, 73, 107], true, false⟩  -- اكْتُبْ (بلا همزتها)
def shQalu : Kalima := ⟨[28, 11, 53, 115], false, false⟩  -- قَالُوا (الألف الفارقة لا تُنطق)
def shUktubu : Kalima := ⟨[35, 73, 105, 115], true, false⟩  -- اكْتُبُوا
def shQum : Kalima := ⟨[29, 111], false, false⟩       -- قُمْ
def shAllayla : Kalima := ⟨[55, 52, 47, 52], true, true⟩  -- اللَّيْلَ (لام التعريف مدغمة: لْ لَ يْ لَ)
def shMin : Kalima := ⟨[110, 59], false, false⟩       -- مِنْ
def shBaytin : Kalima := ⟨[104, 47, 74, 59], false, false⟩  -- بَيْتٍ (التنوين نون ساكنة)
def shBint : Kalima := ⟨[106, 59, 75], false, false⟩  -- بِنْتْ (موقوفٌ عليها بساكنين)
def shHajj : Kalima := ⟨[16, 11, 39], false, false⟩   -- حَاجْ (مدٌّ ثمّ ساكنٌ معلَّق على الإدغام) ح 4، ج 9
def shJaa : Kalima := ⟨[36, 11, 0], false, false⟩     -- جَاءَ

/-- «قَالَ اكْتُبْ» ← qāla-ktub: بعد متحرّك تسقط الهمزة بلا إصلاح؛ وصورة ابتداء «اكْتُبْ» بهمزة مضمومة. -/
theorem shahid_qala_uktub :
    rakkib [shQala, shUktub] = { silsila := [28, 11, 52, 35, 73, 107], islahat := [(2, .la)] } ∧
    Fwaqf (run 0 [28, 11, 52, 35, 73, 107]) = true ∧
    ibtida shUktub = [1, 35, 73, 107] ∧
    (qattaJumla [28, 11, 52, 35, 73, 107]).map (·.map (·.map nawMaqta)) = some [[.CVV, .CVC, .CVC]] := by
  decide +kernel

/-- «قَالُوا اكْتُبُوا» ← qālu-ktubū: بعد مدٍّ يُحذف المدّ؛ وبلا حذفٍ تموت السلسلة. -/
theorem shahid_qalu_uktubu :
    rakkib [shQalu, shUktubu] = { silsila := [28, 11, 53, 35, 73, 105, 115], islahat := [(2, .hadhfMadd)] } ∧
    Fwaqf (run 0 [28, 11, 53, 35, 73, 105, 115]) = true ∧
    run 0 [28, 11, 53, 115, 35, 73, 105, 115] = 96 ∧
    (qattaJumla [28, 11, 53, 35, 73, 105, 115]).map (·.map (·.map nawMaqta)) =
      some [[.CVV, .CVC, .CV, .CVV]] := by
  decide +kernel

/-- «قُمْ اللَّيْلَ» ← qumil-layla: بعد ساكنٍ مُغلِق يُحرَّك بالكسر؛ وبلا تحريكٍ تموت السلسلة. -/
theorem shahid_qum_allayla :
    rakkib [shQum, shAllayla] = { silsila := [29, 110, 55, 52, 47, 52], islahat := [(2, .tahrik)] } ∧
    Fwaqf (run 0 [29, 110, 55, 52, 47, 52]) = true ∧
    run 0 [29, 111, 55, 52, 47, 52] = 96 ∧
    (qattaJumla [29, 110, 55, 52, 47, 52]).map (·.map (·.map nawMaqta)) = some [[.CV, .CVC, .CVC, .CV]] := by
  decide +kernel

/-- «مِنْ بَيْتٍ»: لا همزة وصل فحدُّ الكلمة 116 بينهما، وكلمتان صوتيّتان؛ و«بِنْتْ» لا توصل (آخرها ساكنان). -/
theorem shahid_hadd :
    rakkib [shMin, shBaytin] = { silsila := [110, 59, 116, 104, 47, 74, 59] } ∧
    Fwaqf (run 0 [110, 59, 116, 104, 47, 74, 59]) = true ∧
    (qattaJumla [110, 59, 116, 104, 47, 74, 59]).map (·.map (·.map nawMaqta)) =
      some [[.CVC], [.CVC, .CVC]] ∧
    rakkib [shBint, shBaytin] = { silsila := [106, 59, 75], khalal := some (.laTusal 1) } := by
  decide +kernel

/-- **الإدغام يعبر حدّ الكلمة (آلة المالك):** «حَاجْ جَاءَ» يُرخَّص بإدغام الجيم في الجيم، و«حَاجْ قَالَ» يموت عند الثانية. -/
theorem shahid_idgham_hadd :
    rakkib [shHajj, shJaa] = { silsila := [16, 11, 39, 116, 36, 11, 0] } ∧
    Fwaqf (run 0 [16, 11, 39, 116, 36, 11, 0]) = true ∧
    rakkib [shHajj, shQala] = { silsila := [16, 11, 39, 116, 28, 11, 52], khalal := some (.mayyita 2) } := by
  decide +kernel

end Dal
