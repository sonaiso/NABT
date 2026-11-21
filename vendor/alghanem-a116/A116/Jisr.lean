import A116.Nizam
import A116.Dal

/-!
# جسورُ اللغة: البرجُ على `Nizam` — الإسقاط، والجسر، وذهابًا وإيابًا، والاستنفاد (ADR ٦٥)

أرفق المالك (2026-10-15) برهانًا كتبه وكيلٌ آخر في الدردشة: «SLGE برجٌ من الأنظمة المحلّيّة، والدالّةُ الممتدّة حاصلُ
ضربه»، بتعريف المستوى (Σ, I, R, F) وإسقاطٍ π : Σ′ → Σ يحفظ الثلاثة، وخمس مبرهنات. وطلب: «حلّل واستنتج وابنِ برهانًا
يبني جسورًا للغة». هذه الوحدةُ تكتب ما يصحّ منه على `A116.Nizam` بعينه، وتسمّي ما لا يصحّ بمبرهنةٍ سالبة.

## ما تثبته

1. **الإسقاطُ حرفًا بحرف** (التعريف ٢ في المرفق): سحبُ النظام على f يطابق ترخيصَ الصورة (`licWasl_comap`، ⟺)؛
   والإسقاطُ الحافظُ للثلاثة سليمٌ نزولًا (`proj_sound`، لمّا ١) **وليس تامًّا صعودًا** (`proj_not_complete`).
2. **الجسر**: البرجُ في المستودع ليس إسقاطَ حرفٍ على حرف بل **حرفُ الأعلى سلسلةٌ من الأدنى** (`Nizam.lift`)؛
   فالجسرُ h : β → List α، وترخيصُه ترخيصُ تسطيح الصورة (`pull_flatten`، على `Nizam.lift_flatten`)، وجسرٌ فوق جسرٍ جسرٌ
   واحد (`pull_pull`) — وهذا «البرجُ» بعينه، لكلّ عمق.
3. **ذهابًا وإيابًا**: صنفُ `Nizam` **غيرُ مغلقٍ** تحت قلب السلسلة (`reverse_not_nizam`)، لأنّ الابتداءَ أحاديٌّ على الأوّل
   ولا أحاديَّ على الآخر؛ والنظامُ ذو الطرفين (`Taraf`: ابتداءٌ وختم) مغلقٌ تحته بالمنقول (`taraf_reverse`) و`Nizam`
   داخلٌ فيه (`ofNizam_licT`). فالمبرهنةُ ١ في المرفق صادقةٌ على نموذجه، لا على `Nizam` إلّا بعد هذا التوسيع.
4. **الاستنفاد**: المولِّدُ `gen` يعدّد بالضبط المرخَّصَ بطول n على أبجديّةٍ منتهية (`mem_gen`، ⟺)، وتمامُه من أنّ
   الترخيصَ مغلقٌ على السوابق (`Nizam.licWasl_prefix`)؛ ومطابقٌ لعدٍّ مستقلٍّ على النظام الثلاثيّ (`gen_ternary_agrees`).
5. **الحدّ**: الإسقاطُ غيرُ المتباين لا يُستردّ منه الأصل — «قَالَ» من قول وقيل (`Dal.no_cell_function_recovers_root`).
-/

namespace A116.Jisr

open A116 A116.Nizam

variable {α β γ : Type}

/-! ## ١. الإسقاطُ حرفًا بحرف -/

/-- سحبُ نظامٍ على إسقاط f : β → α: يُحكم على الحرف الأعلى بحكم صورته. -/
def comap (N : Nizam α) (f : β → α) : Nizam β where
  wujud b := N.wujud (f b)
  ibtida b := N.ibtida (f b)
  wasl b c := N.wasl (f b) (f c)
  waqf b c := N.waqf (f b) (f c)

theorem chain_comap (N : Nizam α) (f : β → α) : ∀ (a : β) (t : List β),
    chain (comap N f) a t = chain N (f a) (t.map f)
  | _, [] => rfl
  | a, b :: t => by
    simp only [chain, List.map_cons]
    rw [chain_comap N f b t]
    rfl

/-- **السحبُ يطابق الصورة**، في الاتّجاهين. -/
theorem licWasl_comap (N : Nizam α) (f : β → α) (w : List β) :
    licWasl (comap N f) w = licWasl N (w.map f) := by
  cases w with
  | nil => rfl
  | cons a t =>
    simp only [licWasl, List.map_cons, chain_comap, List.all_cons, List.all_map]
    rfl

/-- إسقاطٌ يحفظ الرخصةَ والابتداءَ والوصل (التعريف ٢ في المرفق، بالرخصة زيادةً). -/
structure Hafiz (M : Nizam β) (N : Nizam α) (f : β → α) : Prop where
  wujud : ∀ b, M.wujud b = true → N.wujud (f b) = true
  ibtida : ∀ b, M.ibtida b = true → N.ibtida (f b) = true
  wasl : ∀ b c, M.wasl b c = true → N.wasl (f b) (f c) = true

theorem chain_mono {M : Nizam β} {N : Nizam α} {f : β → α} (h : Hafiz M N f) :
    ∀ (a : β) (t : List β), chain M a t = true → chain N (f a) (t.map f) = true
  | _, [], _ => rfl
  | a, b :: t, hc => by
    simp only [chain, Bool.and_eq_true] at hc
    simp only [List.map_cons, chain, Bool.and_eq_true]
    exact ⟨h.wasl a b hc.1, chain_mono h b t hc.2⟩

/-- **لمّا ١ (سليمٌ نزولًا)**: صورةُ المرخَّص في الأعلى مرخَّصةٌ في الأدنى. -/
theorem proj_sound {M : Nizam β} {N : Nizam α} {f : β → α} (h : Hafiz M N f) (w : List β)
    (hw : licWasl M w = true) : licWasl N (w.map f) = true := by
  cases w with
  | nil => rfl
  | cons a t =>
    simp only [licWasl, Bool.and_eq_true, List.all_eq_true] at hw
    simp only [List.map_cons, licWasl, Bool.and_eq_true, List.all_eq_true, List.mem_cons, List.mem_map]
    refine ⟨⟨?_, h.ibtida a hw.1.2⟩, chain_mono h a t hw.2⟩
    rintro x (rfl | ⟨y, hy, rfl⟩)
    · exact h.wujud a (hw.1.1 a (List.mem_cons_self))
    · exact h.wujud y (hw.1.1 y (List.mem_cons_of_mem a hy))

/-- نظامٌ يرخّص كلَّ شيء، ونظامٌ لا يبتدئ بشيء. -/
def kull : Nizam Bool := ⟨fun _ => true, fun _ => true, fun _ _ => true, fun _ _ => true⟩
def laIbtida : Nizam Bool := ⟨fun _ => true, fun _ => false, fun _ _ => true, fun _ _ => true⟩

/-- **وليس تامًّا صعودًا**: إسقاطٌ حافظٌ، وصورةٌ مرخَّصةٌ في الأدنى، وأصلُها غيرُ مرخَّصٍ في الأعلى. فالبرجُ بالإسقاط
يحكم نزولًا ولا يولّد صعودًا: ما فوق الخانة يحتاج قانونَه هو، لا يُستخرج من الخانة. -/
theorem proj_not_complete :
    Hafiz laIbtida kull id ∧ licWasl kull ([true].map id) = true ∧ licWasl laIbtida [true] = false :=
  ⟨⟨fun _ _ => rfl, fun _ _ => rfl, fun _ _ _ => rfl⟩, rfl, rfl⟩

/-! ## ٢. الجسر: حرفُ الأعلى سلسلةٌ من الأدنى -/

/-- الجسرُ h : β → List α: الحرفُ الأعلى صورتُه سلسلةٌ في الأدنى، والحكمُ عليه حكمُ الرفع `Nizam.lift` على صورته. -/
def pull (N : Nizam α) (h : β → List α) : Nizam β := comap (lift N) h

/-- **الجسرُ ترخيصُ التسطيح**: سلسلةٌ في الأعلى مرخَّصةٌ إذا وفقط إذا كانت صورُ حروفها غيرَ فارغةٍ وتسطيحُها مرخَّصٌ
في الأدنى — في الاتّجاهين، لكلّ نظامٍ ولكلّ جسر. -/
theorem pull_flatten (N : Nizam α) (h : β → List α) (bs : List β) :
    licWasl (pull N h) bs = true ↔
      ((bs.map h).all (fun v => !v.isEmpty) = true ∧ licWasl N (bs.map h).flatten = true) := by
  rw [pull, licWasl_comap, lift_flatten]

/-- **جسرٌ فوق جسرٍ جسرٌ واحد**: البرجُ (كلمة ← مقطع ← خانة…) يُسطَّح إلى الأدنى بالتركيب، لكلّ عمق. -/
theorem pull_pull (N : Nizam α) (h : β → List α) (g : γ → List β) (cs : List γ) :
    licWasl (pull (pull N h) g) cs = true ↔
      ((cs.map g).all (fun v => !v.isEmpty) = true ∧
        ((cs.map g).flatten.map h).all (fun v => !v.isEmpty) = true ∧
        licWasl N ((cs.map g).flatten.map h).flatten = true) := by
  rw [pull_flatten, pull_flatten]

/-! ## ٣. ذهابًا وإيابًا -/

/-- جوارُ كلّ زوجٍ متجاور. -/
def adj (r : α → α → Bool) : List α → Bool
  | [] => true
  | [_] => true
  | a :: b :: t => r a b && adj r (b :: t)

theorem chain_eq_adj (N : Nizam α) : ∀ (a : α) (t : List α), chain N a t = adj N.wasl (a :: t)
  | _, [] => rfl
  | a, b :: t => by simp only [chain, adj, chain_eq_adj N b t]

theorem adj_cons_cons (r : α → α → Bool) (a b : α) (t : List α) :
    adj r (a :: b :: t) = (r a b && adj r (b :: t)) := rfl

theorem adj_snoc (r : α → α → Bool) : ∀ (l : List α) (x : α),
    adj r (l ++ [x]) = (adj r l && match l.getLast? with | none => true | some y => r y x)
  | [], _ => rfl
  | [a], x => by simp [adj]
  | a :: b :: t, x => by
    have ih := adj_snoc r (b :: t) x
    simp only [List.cons_append] at ih ⊢
    rw [adj_cons_cons, ih, adj_cons_cons, List.getLast?_cons_cons, Bool.and_assoc]

/-- **الجوارُ مقروءًا من الجهة الأخرى** هو الجوارُ بالعلاقة المقلوبة. -/
theorem adj_reverse (r : α → α → Bool) : ∀ l : List α, adj (fun a b => r b a) l.reverse = adj r l
  | [] => rfl
  | [_] => rfl
  | a :: b :: t => by
    have ih := adj_reverse r (b :: t)
    rw [List.reverse_cons, adj_snoc, ih, List.getLast?_reverse, List.head?_cons, adj_cons_cons]
    simp only [Bool.and_comm]

/-- نظامٌ بطرفين: قانونُ ابتداءٍ على الأوّل، وقانونُ ختمٍ على الآخر. -/
structure Taraf (α : Type) where
  wujud : α → Bool
  ibtida : α → Bool
  wasl : α → α → Bool
  khatm : α → Bool

def licT (T : Taraf α) (w : List α) : Bool :=
  w.all T.wujud && adj T.wasl w &&
    (match w.head? with | none => true | some a => T.ibtida a) &&
    (match w.getLast? with | none => true | some z => T.khatm z)

/-- القلب: الابتداءُ ختم، والختمُ ابتداء، والوصلُ مقلوب. -/
def Taraf.rev (T : Taraf α) : Taraf α := ⟨T.wujud, T.khatm, fun a b => T.wasl b a, T.ibtida⟩

/-- **المبرهنةُ ١ في المرفق على صنفٍ مغلق**: السلسلةُ مرخَّصةٌ إذا وفقط إذا رُخّص قلبُها في النظام المقلوب. -/
theorem taraf_reverse (T : Taraf α) (w : List α) : licT T.rev w.reverse = licT T w := by
  simp only [licT, Taraf.rev, List.all_reverse, adj_reverse, List.head?_reverse, List.getLast?_reverse]
  cases w.all T.wujud <;> cases adj T.wasl w <;>
    cases (match w.head? with | none => true | some a => T.ibtida a) <;>
    cases (match w.getLast? with | none => true | some z => T.khatm z) <;> rfl

/-- `Nizam` نظامٌ بطرفين ختمُه مفتوح. -/
def ofNizam (N : Nizam α) : Taraf α := ⟨N.wujud, N.ibtida, N.wasl, fun _ => true⟩

theorem ofNizam_licT (N : Nizam α) (w : List α) : licT (ofNizam N) w = licWasl N w := by
  cases w with
  | nil => rfl
  | cons a t =>
    simp only [licT, ofNizam, licWasl, List.head?_cons, chain_eq_adj]
    cases (a :: t).getLast? <;> simp [Bool.and_assoc, Bool.and_comm, Bool.and_left_comm]

/-- ما يبتدئ بـ`true`. -/
def yabdaTrue : Nizam Bool := ⟨fun _ => true, fun a => a, fun _ _ => true, fun _ _ => false⟩

/-- **`Nizam` غيرُ مغلقٍ تحت القلب**: لا نظامَ يرخّص بالضبط مقلوباتِ ما يرخّصه `yabdaTrue` (ما يُختم بـ`true`). فقراءةُ
النصّ «يمينًا ويسارًا» تحتاج قانونَ ختمٍ ليس في `Nizam`. -/
theorem reverse_not_nizam : ¬ ∃ M : Nizam Bool, ∀ w, licWasl M w = licWasl yabdaTrue w.reverse := by
  rintro ⟨M, hM⟩
  have h1 := hM [false, true]
  have h2 := hM [false]
  simp [licWasl, chain, yabdaTrue] at h1 h2
  simp_all

/-! ## ٤. الاستنفاد: مولِّدٌ جامعٌ مانع -/

/-- كلُّ مرخَّصٍ بطول n على الأبجديّة S، بالتمديد حرفًا حرفًا. -/
def gen (N : Nizam α) (S : List α) : Nat → List (List α)
  | 0 => [[]]
  | n + 1 => (gen N S n).flatMap fun w =>
      (S.filter fun b => licWasl N (w ++ [b])).map fun b => w ++ [b]

/-- **الجامعُ المانع**: ما يعدّده المولِّد هو بالضبط المرخَّصُ بطول n من حروف S. وتمامُه من أنّ الترخيصَ مغلقٌ على
السوابق (`Nizam.licWasl_prefix`): كلُّ مرخَّصٍ يُبلغ من سابقه المرخَّص. -/
theorem mem_gen (N : Nizam α) (S : List α) : ∀ (n : Nat) (w : List α),
    w ∈ gen N S n ↔ (w.length = n ∧ (∀ x ∈ w, x ∈ S) ∧ licWasl N w = true)
  | 0, w => by
    cases w with
    | nil => simp [gen, licWasl]
    | cons a t => simp [gen]
  | n + 1, w => by
    simp only [gen, List.mem_flatMap, List.mem_map, List.mem_filter]
    constructor
    · rintro ⟨u, hu, b, ⟨hbS, hb⟩, rfl⟩
      obtain ⟨hl, hS, _⟩ := (mem_gen N S n u).1 hu
      refine ⟨by simp [hl], ?_, hb⟩
      intro x hx
      rcases List.mem_append.1 hx with hx | hx
      · exact hS x hx
      · simp at hx; exact hx ▸ hbS
    · rintro ⟨hl, hS, hw⟩
      rcases List.eq_nil_or_concat w with rfl | ⟨u, b, rfl⟩
      · simp at hl
      simp only [List.concat_eq_append] at hl hS hw ⊢
      · refine ⟨u, (mem_gen N S n u).2 ⟨?_, fun x hx => hS x (by simp [hx]), licWasl_prefix N u [b] hw⟩,
          b, ⟨hS b (by simp), hw⟩, rfl⟩
        simpa using hl

/-! ### شاهدٌ مستقلّ: النظامُ الثلاثيّ على أصناف الخانة -/

/-- كلُّ السلاسل بطول n، تعدادًا ساذجًا مستقلًّا عن `gen`. -/
def allWords (S : List α) : Nat → List (List α)
  | 0 => [[]]
  | n + 1 => (allWords S n).flatMap fun w => S.map fun b => w ++ [b]

def kinds : List Stages.K := [.cv, .v, .c]

/-- المولِّدُ يطابق العدَّ الساذج بالتصفية على `Nizam.ternary` للأطوال 1..7. -/
theorem gen_ternary_agrees :
    (List.range 8).all (fun n =>
      (gen ternary kinds n).length == ((allWords kinds n).filter (licWasl ternary)).length) = true := by
  decide +kernel

/-- العددُ بالطول على `Nizam.ternary`: 1، 1، 3، 6، 13، 28، 60، 129 للأطوال 0..7 (الطولُ الأوّل `cv` وحدَه: الابتداءُ
بمتحرّك). العددُ للأصناف لا للخانات. -/
theorem gen_ternary_counts :
    (List.range 8).map (fun n => (gen ternary kinds n).length) = [1, 1, 3, 6, 13, 28, 60, 129] := by
  decide +kernel

/-! ## ٥. الجامعة -/

/-- **جسورُ اللغة على `Nizam`**، في عبارةٍ واحدة: الإسقاطُ يطابق الصورة، وسليمٌ نزولًا لا تامٌّ صعودًا؛ الجسرُ ترخيصُ
التسطيح، وجسرٌ فوق جسرٍ جسر؛ القلبُ مغلقٌ في ذي الطرفين و`Nizam` داخلُه وغيرُ مغلقٍ وحدَه؛ المولِّدُ جامعٌ مانع؛ والإسقاطُ
غيرُ المتباين لا يردّ «قَالَ» إلى جذره. -/
theorem jisr :
    (∀ (N : Nizam α) (f : β → α) (w : List β), licWasl (comap N f) w = licWasl N (w.map f)) ∧
    (∀ (M : Nizam β) (N : Nizam α) (f : β → α), Hafiz M N f → ∀ w, licWasl M w = true → licWasl N (w.map f) = true) ∧
    (Hafiz laIbtida kull id ∧ licWasl kull ([true].map id) = true ∧ licWasl laIbtida [true] = false) ∧
    (∀ (N : Nizam α) (h : β → List α) (bs : List β), licWasl (pull N h) bs = true ↔
      ((bs.map h).all (fun v => !v.isEmpty) = true ∧ licWasl N (bs.map h).flatten = true)) ∧
    (∀ (T : Taraf α) (w : List α), licT T.rev w.reverse = licT T w) ∧
    (∀ (N : Nizam α) (w : List α), licT (ofNizam N) w = licWasl N w) ∧
    (¬ ∃ M : Nizam Bool, ∀ w, licWasl M w = licWasl yabdaTrue w.reverse) ∧
    (∀ (N : Nizam α) (S : List α) (n : Nat) (w : List α),
      w ∈ gen N S n ↔ (w.length = n ∧ (∀ x ∈ w, x ∈ S) ∧ licWasl N w = true)) ∧
    (¬ ∃ f : List Cell → Wazn.Root 3, f (Dal.qala Dal.qwl) = Dal.qwl ∧ f (Dal.qala Dal.qyl) = Dal.qyl) :=
  ⟨licWasl_comap, fun _ _ _ h w hw => proj_sound h w hw, proj_not_complete, pull_flatten,
   taraf_reverse, ofNizam_licT, reverse_not_nizam, mem_gen, Dal.no_cell_function_recovers_root⟩

end A116.Jisr
