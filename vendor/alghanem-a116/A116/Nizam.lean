import A116.ContinueCount
import A116.Recovery
import A116.Ladder

/-!
# نظامُ الأنظمة: الهويّةُ والجوارُ والسجلّ — الأساسُ الجبريُّ المشترك (ADR ٢٣)

نصُّ المالك (2026-10-12): «نظامُ التسمية قائمٌ على علاقة الاسم والمسمّى بما قبلها وما بعدها وعلاقة ما قبلها بما
بعدها، وتبقى الهويّةُ العنصرَ المحايد المشترك لكلّ ثباتٍ أو تحوّل … وتُمنح رخصةُ الشيء ورخصةُ الخواصّ … وتُربط كلُّ
صفةٍ بزمنها ومكانها وفق قانون الابتداء وقانون الوصل وقانون الوقف؛ تتكوّن كلُّ هويّةٍ حاملًا/حالةً/موضعًا ولها سجلٌّ
يوثّق كلَّ انتقالٍ مرخَّص».

هذه الوحدةُ تستخرج من الأنظمة المبرهَنة في الشجرة **بنيةً واحدةً** تشترك فيها، وتبرهن قوانينَها مرّةً واحدة لكلّ نظام،
ثمّ تُثبت أنّ الأنظمة القائمة **مثولاتٌ** لها — لا تعريفاتٌ جديدةٌ موازية:

1. **الهويّة** (`Huwiyya`): حاملٌ، حالةٌ، موضع. الكلمةُ ↔ قائمةُ هويّاتها بلا فقد (`forget_huwiyyat`)، والموضعُ رقمُها
   (`mawdi_from`)، وما قبلها يُزيح مواضعَ ما بعدها بطوله وحدَه (`huwiyyat_append`).
2. **النظام** (`Nizam`): رخصةُ الشيء (`wujud`)، وقانونُ الابتداء على الأوّل (`ibtida`)، وعلاقةُ ما قبلُ بما بعدُ
   (`wasl`)، وما يُرخَّص في الطرف وحدَه وقفًا (`waqf`). ترخيصُ السلسلة وصلًا `licWasl` ووقفًا `licWaqf`. المبرهَنُ لكلّ
   نظام: الوصلُ ⇒ الوقف (`wasl_imp_waqf`)، الوقفُ ⇒ الابتداء (`waqf_imp_ibtida`)، **قانونُ الحدّ**: ترخيصُ سلسلتين
   موصولتين هو ترخيصُ الأولى وعلاقةُ آخرها بأوّل الثانية وترخيصُ الثانية **بلا ابتدائها** (`licWasl_append`)، وما سبق
   مرخَّصٌ مرخَّصٌ وحدَه (`licWasl_prefix`)، والفارغُ محايدُ الوصل (`licWasl_nil`).
3. **المثولات** — الأنظمةُ القائمة هي هذه البنيةُ بعينها:
   * الترخيصُ الثنائيّ (`Model.Admissible`) = `licWasl binary` (`admissible_iff_binary`): لا رخصةَ للخانة وحدَها
     فوق وجودها، والابتداءُ متحرّك، والجوارُ لا ساكنين.
   * الترخيصُ الثلاثيّ وصلًا (`Ternary.continueB`) = `licWasl ternary` (`continueB_local`) — **علاقةُ جوارٍ محضة**:
     الابتداءُ بمتحرّك، وكلُّ زوجٍ (قبل، بعد) من ستّة أزواجٍ مأذونة؛ ووقفًا (`Ternary.pauseB`) = `licWaqf ternary`
     (`pauseB_local`): الزوجُ (ساكن، ساكن) لا يُرخَّص إلّا طرفًا.
   * **الهويّةُ في النظام الثنائيّ** متتاليةُ الحالات: ما اتّفقت حالاتُه اتّفق ترخيصُه (`binary_depends_on_haraka`)،
     فإبدالُ الحامل انتقالٌ يحفظ الهويّة.
4. **السجلّ** (`Intiqal`، `runL`، `backL`): كلُّ انتقالٍ ذهابٌ وسجلٌّ وإيابٌ يردّ الأصل؛ والسلسلةُ تُردّ بالسجلّ كلِّه
   بالترتيب المعكوس (`sijill`)؛ وما حفظه كلُّ انتقالٍ — رخصةً (`sijill_lic`) أو هويّةً (`sijill_huwiyya`) — حفظته
   السلسلة؛ والسجلُّ الفارغ محايد (`runL_nil`). ومثولُه التعديلُ الموضعيّ (`edit`، على `Recovery.edit_roundtrip`) —
   وهو جنسُ قواعد الإعلال والإبدال والبقيّة كلِّها؛ وشاهدُه قَوَلَ ← قَالَ ← قَوَلَ (`qawala_qala`).
5. **نظامُ الأنظمة** (`lift`): عناصرُ النظام الأعلى سلاسلُ النظام الأدنى؛ رخصةُ العنصر وجودُ خاناته وجوارُها الداخليّ،
   وابتداؤه ابتداءُ أوّله، وجوارُ عنصرين جوارُ آخرِ الأوّل بأوّل الثاني. والمبرهَن: ترخيصُ الأعلى وصلًا هو ترخيصُ
   تسطيحه في الأدنى، كلّيًّا وفي الاتّجاهين (`lift_flatten`)؛ فيتكرّر بلا حدّ (`lift_lift`). والعنصرُ الأوسطُ لا يلزمه
   ابتداءٌ: «لْحَمْدُ» بعد «فِ» مرخَّصةٌ موصولةً لا وحدَها (`wasl_element_needs_no_ibtida`).

ولا يُبرهَن هنا شيءٌ عن الكون والإنسان والحياة: البنيةُ مبرهَنةٌ على الخانات والمقاطع والسلاسل، وما فوقها من مستويات
(الحكم، الأجناس، القابليّات) يدخلها مثولًا حين يُبرهَن مثولُه، لا قبل.
-/

namespace A116.Nizam

open A116 A116.Stages A116.Ternary

/-! ## ١. الهويّة: حاملٌ، حالةٌ، موضع -/

structure Huwiyya (H S : Type) where
  hamil : H
  hala : S
  mawdi : Nat
  deriving DecidableEq, Repr

abbrev HuwiyyaC := Huwiyya (Fin carrierCount) Haraka

/-- هويّاتُ الكلمة من الموضع `i`. -/
def huwiyyatFrom : Nat → List Cell → List HuwiyyaC
  | _, [] => []
  | i, c :: t => ⟨c.carrier, c.haraka, i⟩ :: huwiyyatFrom (i + 1) t

def huwiyyat (w : List Cell) : List HuwiyyaC := huwiyyatFrom 0 w

def cellOf (h : HuwiyyaC) : Cell := ⟨h.hamil, h.hala⟩

/-- **بلا فقد**: الكلمةُ هي هويّاتُها بلا مواضعها. -/
theorem forget_from : ∀ (i : Nat) (w : List Cell), (huwiyyatFrom i w).map cellOf = w
  | _, [] => rfl
  | i, c :: t => by simp [huwiyyatFrom, cellOf, forget_from (i + 1) t]

theorem forget_huwiyyat (w : List Cell) : (huwiyyat w).map cellOf = w := forget_from 0 w

theorem length_from : ∀ (i : Nat) (w : List Cell), (huwiyyatFrom i w).length = w.length
  | _, [] => rfl
  | i, _ :: t => by simp [huwiyyatFrom, length_from (i + 1) t]

/-- **الموضعُ رقمُها**: الهويّةُ ذاتُ الرقم k موضعُها ‎i + k‎. -/
theorem mawdi_from : ∀ (i : Nat) (w : List Cell) (k : Nat) (hk : k < (huwiyyatFrom i w).length),
    ((huwiyyatFrom i w)[k]).mawdi = i + k
  | _, [], _, hk => by simp [huwiyyatFrom] at hk
  | i, _ :: t, 0, _ => by simp [huwiyyatFrom]
  | i, _ :: t, k + 1, hk => by
    simp only [huwiyyatFrom, List.getElem_cons_succ]
    rw [mawdi_from (i + 1) t k (by simp [huwiyyatFrom] at hk; omega)]; omega

/-- **ما قبلها يُزيح ما بعدها بطوله وحدَه**: علاقةُ الهويّة بما قبلها. -/
theorem huwiyyat_append : ∀ (i : Nat) (a b : List Cell),
    huwiyyatFrom i (a ++ b) = huwiyyatFrom i a ++ huwiyyatFrom (i + a.length) b
  | i, [], b => by simp [huwiyyatFrom]
  | i, c :: t, b => by
    simp only [List.cons_append, huwiyyatFrom, huwiyyat_append (i + 1) t b, List.length_cons]
    rw [show i + 1 + t.length = i + (t.length + 1) by omega]

/-! ## ٢. النظام: رخصةُ الشيء، والابتداء، والجوار، والوقف -/

structure Nizam (α : Type) where
  /-- رخصةُ الشيء. -/
  wujud : α → Bool
  /-- قانونُ الابتداء على الأوّل. -/
  ibtida : α → Bool
  /-- علاقةُ ما قبلُ بما بعدُ (قانونُ الوصل). -/
  wasl : α → α → Bool
  /-- زوجٌ يُرخَّص في الطرف وحدَه (قانونُ الوقف). -/
  waqf : α → α → Bool

variable {α : Type} (N : Nizam α)

/-- الجوارُ وصلًا: كلُّ زوجٍ متجاور مأذون. -/
def chain : α → List α → Bool
  | _, [] => true
  | a, b :: t => N.wasl a b && chain b t

/-- الجوارُ وقفًا: كذلك، إلّا الزوجَ الأخيرَ فيجوز وقفًا. -/
def chainP : α → List α → Bool
  | _, [] => true
  | a, [b] => N.wasl a b || N.waqf a b
  | a, b :: c :: t => N.wasl a b && chainP b (c :: t)

def licWasl : List α → Bool
  | [] => true
  | a :: t => (a :: t).all N.wujud && N.ibtida a && chain N a t

def licWaqf : List α → Bool
  | [] => true
  | a :: t => (a :: t).all N.wujud && N.ibtida a && chainP N a t

/-- الفارغُ محايدُ الوصل. -/
theorem licWasl_nil : licWasl N [] = true := rfl

theorem chain_imp_chainP : ∀ (a : α) (t : List α), chain N a t = true → chainP N a t = true
  | _, [], _ => rfl
  | a, [b], h => by simp [chain, chainP] at h ⊢; exact Or.inl h
  | a, b :: c :: t, h => by
    simp only [chain, Bool.and_eq_true] at h
    simp only [chainP, Bool.and_eq_true]
    exact ⟨h.1, chain_imp_chainP b (c :: t) (by simpa [chain] using h.2)⟩

/-- **الوصلُ ⇒ الوقف**، في كلّ نظام. -/
theorem wasl_imp_waqf (w : List α) (h : licWasl N w = true) : licWaqf N w = true := by
  cases w with
  | nil => rfl
  | cons a t =>
    simp only [licWasl, licWaqf, Bool.and_eq_true] at h ⊢
    exact ⟨h.1, chain_imp_chainP N a t h.2⟩

/-- **الوقفُ ⇒ الابتداء**، في كلّ نظام. -/
theorem waqf_imp_ibtida (a : α) (t : List α) (h : licWaqf N (a :: t) = true) : N.ibtida a = true := by
  simp only [licWaqf, Bool.and_eq_true] at h; exact h.1.2

/-- الجوارُ على الوصل: جوارُ الأولى، ثمّ آخرُها بما بعده، ثمّ جوارُ الباقي. -/
theorem chain_append : ∀ (a : α) (l m : List α),
    chain N a (l ++ m) = (chain N a l && chain N ((a :: l).getLast (by simp)) m)
  | a, [], m => by simp [chain]
  | a, b :: l, m => by
    simp only [List.cons_append, chain, chain_append b l m, Bool.and_assoc]
    congr 2

/-- **قانونُ الحدّ**: سلسلتان موصولتان مرخَّصتان إذا وفقط إذا رُخّصت الأولى، وأُذن لآخرها بأوّل الثانية، ووُجدت الثانيةُ
بجوارها — **بلا ابتدائها**: الثانيةُ لا تُبتدأ، بل توصَل. -/
theorem licWasl_append (a : α) (l : List α) (b : α) (m : List α) :
    licWasl N ((a :: l) ++ (b :: m)) = (licWasl N (a :: l) &&
      N.wasl ((a :: l).getLast (by simp)) b && ((b :: m).all N.wujud && chain N b m)) := by
  simp only [List.cons_append, licWasl, List.all_cons, List.all_append, chain_append, chain]
  cases N.wujud a <;> cases N.ibtida a <;> cases (l.all N.wujud) <;> cases chain N a l <;>
    cases N.wujud b <;> cases m.all N.wujud <;> cases chain N b m <;> simp

/-- **ما سبق مرخَّصٌ وحدَه**. -/
theorem licWasl_prefix (u v : List α) (h : licWasl N (u ++ v) = true) : licWasl N u = true := by
  cases u with
  | nil => rfl
  | cons a l =>
    simp only [List.cons_append, licWasl, List.all_cons, List.all_append, chain_append,
      Bool.and_eq_true] at h ⊢
    exact ⟨⟨⟨h.1.1.1, h.1.1.2.1⟩, h.1.2⟩, h.2.1⟩

/-! ## ٣. المثولات: الثنائيُّ والثلاثيّ -/

theorem all_true {β : Type} : ∀ (l : List β), l.all (fun _ => true) = true
  | [] => rfl
  | _ :: t => by simp [all_true t]

/-- النظامُ الثنائيّ على الخانات. -/
def binary : Nizam Cell where
  wujud := fun _ => true
  ibtida := fun c => !c.isSukun
  wasl := fun a b => !(a.isSukun && b.isSukun)
  waqf := fun _ _ => false

theorem noAdj_iff : ∀ (a : Cell) (t : List Cell), NoAdjacentSukun (a :: t) ↔ chain binary a t = true
  | _, [] => by simp [NoAdjacentSukun, chain]
  | a, b :: t => by
    simp only [NoAdjacentSukun, chain, binary, Bool.and_eq_true, Bool.not_eq_true', noAdj_iff b t]
    cases a.isSukun <;> cases b.isSukun <;> simp

/-- **الترخيصُ الثنائيّ مثولٌ**: `Admissible` هو `licWasl binary` بعينه. -/
theorem admissible_iff_binary (w : List Cell) : Admissible w ↔ licWasl binary w = true := by
  cases w with
  | nil => simp [Admissible, HeadNotSukun, NoAdjacentSukun, licWasl]
  | cons a t =>
    simp only [Admissible, HeadNotSukun, licWasl]
    rw [noAdj_iff a t]
    simp [binary, List.all_eq_true]

/-- **الهويّةُ في النظام الثنائيّ متتاليةُ الحالات**: ما اتّفقت حالاتُه اتّفق ترخيصُه. -/
theorem chain_haraka : ∀ (a a' : Cell) (t t' : List Cell), a.haraka = a'.haraka →
    t.map Cell.haraka = t'.map Cell.haraka → chain binary a t = chain binary a' t'
  | _, _, [], [], _, _ => rfl
  | _, _, [], _ :: _, _, h => by simp at h
  | _, _, _ :: _, [], _, h => by simp at h
  | a, a', b :: t, b' :: t', ha, h => by
    simp only [List.map_cons, List.cons.injEq] at h
    simp only [chain]
    rw [chain_haraka b b' t t' h.1 h.2]
    simp [binary, Cell.isSukun, ha, h.1]

theorem binary_depends_on_haraka (w w' : List Cell) (h : w.map Cell.haraka = w'.map Cell.haraka) :
    licWasl binary w = licWasl binary w' := by
  cases w with
  | nil => cases w' with
    | nil => rfl
    | cons _ _ => simp at h
  | cons a t => cases w' with
    | nil => simp at h
    | cons a' t' =>
      simp only [List.map_cons, List.cons.injEq] at h
      simp only [licWasl]
      rw [chain_haraka a a' t t' h.1 h.2]
      simp [binary, Cell.isSukun, h.1, all_true]

/-- الأزواجُ المأذونةُ وصلًا على أصناف الذرّة: ستّة. -/
def waslK : K → K → Bool
  | .cv, _ => true
  | .v, .cv => true
  | .v, .c => true
  | .c, .cv => true
  | _, _ => false

/-- الزوجُ الوقفيّ: ساكنٌ بعد ساكن، طرفًا وحدَه. -/
def waqfK : K → K → Bool
  | .c, .c => true
  | _, _ => false

def ternary : Nizam K where
  wujud := fun _ => true
  ibtida := fun k => k == .cv
  wasl := waslK
  waqf := waqfK

theorem waslK_count :
    ([K.cv, .v, .c].flatMap fun a => [K.cv, .v, .c].filter (waslK a)).length = 6 := by decide

theorem accC_local : ∀ t : List K,
    accC .n t = chain ternary .cv t ∧ accC .nv t = chain ternary .v t ∧
    accC .nc t = chain ternary .c t ∧ accC .nvc t = chain ternary .c t
  | [] => ⟨rfl, rfl, rfl, rfl⟩
  | x :: t => by
    obtain ⟨h1, h2, h3, h4⟩ := accC_local t
    cases x <;> simp [accC, δC, δ, chain, ternary, waslK, h1, h2, h3, h4, accC_dead]

/-- **الوصلُ الثلاثيُّ علاقةُ جوارٍ محضة**: ابتداءٌ بمتحرّك، وكلُّ زوجٍ متجاورٍ من الستّة. -/
theorem continueB_local (k : List K) : continueB k = licWasl ternary k := by
  rw [continueB_eq_accC]
  cases k with
  | nil => rfl
  | cons a t =>
    cases a
    · simp [accC, δC, δ, licWasl, ternary, (accC_local t).1]
    · simp [accC, δC, δ, licWasl, ternary, accC_dead]
    · simp [accC, δC, δ, licWasl, ternary, accC_dead]

theorem acc_dead' : ∀ t, acc .dead t = false
  | [] => rfl
  | a :: t => by cases a <;> exact acc_dead' t

theorem acc_local : ∀ t : List K,
    acc .n t = chainP ternary .cv t ∧ acc .nv t = chainP ternary .v t ∧
    acc .nc t = chainP ternary .c t ∧ acc .nvc t = chainP ternary .c t
  | [] => ⟨rfl, rfl, rfl, rfl⟩
  | [x] => by cases x <;> decide
  | x :: y :: t => by
    obtain ⟨h1, h2, h3, h4⟩ := acc_local (y :: t)
    have e : ∀ s, acc s (x :: y :: t) = acc (δ s x) (y :: t) := fun _ => rfl
    have fin : acc .fin (y :: t) = false := by
      show acc (δ .fin y) t = false; cases y <;> exact acc_dead' t
    refine ⟨?_, ?_, ?_, ?_⟩ <;> rw [e] <;> cases x <;>
      simp only [δ, h1, h2, h3, h4, fin, acc_dead'] <;> simp [chainP, ternary, waslK]

/-- **والوقفُ كذلك**، إلّا أنّ (ساكن، ساكن) يُرخَّص طرفًا وحدَه. -/
theorem pauseB_local (k : List K) : pauseB k = licWaqf ternary k := by
  rw [pauseB_eq_acc]
  cases k with
  | nil => rfl
  | cons a t =>
    cases a
    · simp [acc, δ, licWaqf, ternary, (acc_local t).1]
    · simp [acc, δ, licWaqf, ternary, acc_dead']
    · simp [acc, δ, licWaqf, ternary, acc_dead']

/-! ## ٤. السجلّ: كلُّ انتقالٍ ذهابٌ وسجلٌّ وإياب -/

structure Intiqal (β R : Type) where
  go : β → β × R
  back : β → R → β
  law : ∀ x, back (go x).1 (go x).2 = x

def runL {β R : Type} : List (Intiqal β R) → β → β × List R
  | [], x => (x, [])
  | t :: ts, x => ((runL ts (t.go x).1).1, (t.go x).2 :: (runL ts (t.go x).1).2)

def backL {β R : Type} : List (Intiqal β R) → β → List R → β
  | [], x, _ => x
  | t :: ts, x, r :: rs => t.back (backL ts x rs) r
  | _ :: _, x, [] => x

/-- السجلُّ الفارغ محايد. -/
theorem runL_nil {β R : Type} (x : β) : runL ([] : List (Intiqal β R)) x = (x, []) := rfl

/-- **السجلّ**: سلسلةُ الانتقالات تُردّ بسجلّها كلِّه بالترتيب المعكوس. -/
theorem sijill {β R : Type} : ∀ (ts : List (Intiqal β R)) (x : β),
    backL ts (runL ts x).1 (runL ts x).2 = x
  | [], _ => rfl
  | t :: ts, x => by simp only [runL, backL, sijill ts (t.go x).1, t.law]

/-- ما حفظه كلُّ انتقالٍ من رخصةٍ حفظته السلسلة. -/
theorem sijill_lic {β R : Type} (P : β → Prop) : ∀ (ts : List (Intiqal β R)),
    (∀ t ∈ ts, ∀ x, P x → P (t.go x).1) → ∀ x, P x → P (runL ts x).1
  | [], _, _, hx => hx
  | t :: ts, h, x, hx =>
    sijill_lic P ts (fun t' ht' => h t' (List.mem_cons_of_mem _ ht')) _ (h t (by simp) x hx)

/-- **الهويّةُ الثابتةُ عبر التحوّل**: ما حفظه كلُّ انتقالٍ حفظته السلسلة. -/
theorem sijill_huwiyya {β R I : Type} (f : β → I) : ∀ (ts : List (Intiqal β R)),
    (∀ t ∈ ts, ∀ x, f (t.go x).1 = f x) → ∀ x, f (runL ts x).1 = f x
  | [], _, _ => rfl
  | t :: ts, h, x => by
    simp only [runL]
    rw [sijill_huwiyya f ts (fun t' ht' => h t' (List.mem_cons_of_mem _ ht')) _, h t (by simp) x]

/-- **التعديلُ الموضعيّ انتقالٌ بسجلّ**: يُبدَل ما طولُه `n` من الموضع `i` بـ`ins`، ويحفظ السجلُّ المحذوف
(`Recovery.EditRecord`)؛ وما جاوز الطولَ لا يُمسّ. جنسُ قواعد الإعلال والإبدال والبقيّة كلِّها. -/
def edit {β : Type} (i n : Nat) (ins : List β) : Intiqal (List β) (Recovery.EditRecord β) where
  go x := if i + n ≤ x.length then
      (x.take i ++ (ins ++ x.drop (i + n)), ⟨i, ins.length, (x.drop i).take n⟩)
    else (x, ⟨0, 0, []⟩)
  back := Recovery.restoreEdit
  law x := by
    by_cases h : i + n ≤ x.length
    · simp only [h, ite_true]
      have hl : (x.take i).length = i := by simp; omega
      have := Recovery.edit_roundtrip (x.take i) ((x.drop i).take n) ins (x.drop (i + n))
      rw [hl] at this
      rw [this, List.append_assoc]
      have : (x.drop i).take n ++ x.drop (i + n) = x.drop i := by
        rw [← List.drop_drop]; exact List.take_append_drop n (x.drop i)
      rw [this, List.take_append_drop]
    · simp only [h, ite_false]
      simp [Recovery.restoreEdit]

open A116.Ladder in
/-- شاهد: قَوَلَ ← قَالَ بتعديلٍ في الموضع 1، ويردّه السجلّ قَوَلَ (`Ilal` القاعدة ١). -/
theorem qawala_qala :
    let qawala := [atom 'ق' .fatha, atom 'و' .fatha, atom 'ل' .fatha]
    let qala := [atom 'ق' .fatha, atom 'ا' .sukun, atom 'ل' .fatha]
    ((edit 1 1 [atom 'ا' .sukun]).go qawala).1 = qala ∧
      backL [edit 1 1 [atom 'ا' .sukun]] (runL [edit 1 1 [atom 'ا' .sukun]] qawala).1
        (runL [edit 1 1 [atom 'ا' .sukun]] qawala).2 = qawala :=
  ⟨by decide, sijill _ _⟩

/-! ## ٥. نظامُ الأنظمة -/

/-- الجوارُ الداخليّ للعنصر بلا ابتدائه. -/
def inner : List α → Bool
  | [] => false
  | a :: t => (a :: t).all N.wujud && chain N a t

/-- **الرفع**: عناصرُ النظام الأعلى سلاسلُ الأدنى. -/
def lift : Nizam (List α) where
  wujud := inner N
  ibtida := fun u => match u with
    | [] => false
    | a :: _ => N.ibtida a
  wasl := fun u v => match u.getLast?, v.head? with
    | some x, some y => N.wasl x y
    | _, _ => false
  waqf := fun _ _ => false

theorem getLast?_cons_ne {a : α} {l : List α} :
    (a :: l).getLast? = some ((a :: l).getLast (by simp)) := List.getLast?_eq_some_getLast _

theorem lift_wujud : (lift N).wujud = inner N := rfl
theorem lift_ibtida (a : α) (l : List α) : (lift N).ibtida (a :: l) = N.ibtida a := rfl
theorem inner_cons (a : α) (l : List α) : inner N (a :: l) = ((a :: l).all N.wujud && chain N a l) := rfl

theorem lift_wasl (a : α) (l : List α) (b : α) (m : List α) :
    (lift N).wasl (a :: l) (b :: m) = N.wasl ((a :: l).getLast (by simp)) b := by
  simp only [lift, getLast?_cons_ne, List.head?_cons]

/-- اللمّة: جوارُ العناصر في الأعلى = جوارُ تسطيحها في الأدنى بعد آخر الأوّل. -/
theorem lift_chain : ∀ (a : α) (l : List α) (vs : List (List α)),
    (vs.all (inner N) = true ∧ chain (lift N) (a :: l) vs = true) ↔
      (vs.all (fun v => !v.isEmpty) = true ∧ vs.flatten.all N.wujud = true ∧
        chain N ((a :: l).getLast (by simp)) vs.flatten = true)
  | a, l, [] => by simp [chain]
  | a, l, [] :: vs => by simp [inner]
  | a, l, (b :: m) :: vs => by
    have ih := lift_chain b m vs
    simp only [List.all_cons, chain, List.flatten_cons, List.cons_append, List.all_append,
      chain_append, inner, Bool.and_eq_true, List.isEmpty_cons, Bool.not_false, true_and]
    rw [lift_wasl]
    constructor
    · rintro ⟨⟨⟨⟨hb, hm⟩, hc⟩, hvs⟩, hw, hch⟩
      obtain ⟨n1, n2, n3⟩ := ih.1 ⟨hvs, hch⟩
      exact ⟨n1, ⟨hb, hm, n2⟩, hw, hc, n3⟩
    · rintro ⟨n1, ⟨hb, hm, n2⟩, hw, hc, n3⟩
      obtain ⟨hvs, hch⟩ := ih.2 ⟨n1, n2, n3⟩
      exact ⟨⟨⟨⟨hb, hm⟩, hc⟩, hvs⟩, hw, hch⟩

/-- **ترخيصُ الأعلى هو ترخيصُ تسطيحه في الأدنى** — في الاتّجاهين، لكلّ نظام. -/
theorem lift_flatten (ws : List (List α)) :
    licWasl (lift N) ws = true ↔ (ws.all (fun v => !v.isEmpty) = true ∧ licWasl N ws.flatten = true) := by
  cases ws with
  | nil => simp [licWasl]
  | cons u vs =>
    cases u with
    | nil => simp [licWasl, lift, inner]
    | cons a l =>
      have h := lift_chain N a l vs
      simp only [licWasl, List.all_cons, List.flatten_cons, List.cons_append, List.all_append,
        chain_append, lift_wujud, lift_ibtida, inner_cons, Bool.and_eq_true, List.isEmpty_cons,
        Bool.not_false, true_and]
      constructor
      · rintro ⟨⟨⟨⟨⟨ha, hl⟩, hc⟩, hvs⟩, hi⟩, hch⟩
        obtain ⟨n1, n2, n3⟩ := h.1 ⟨hvs, hch⟩
        exact ⟨n1, ⟨⟨ha, hl, n2⟩, hi⟩, hc, n3⟩
      · rintro ⟨n1, ⟨⟨ha, hl, n2⟩, hi⟩, hc, n3⟩
        obtain ⟨hvs, hch⟩ := h.2 ⟨n1, n2, n3⟩
        exact ⟨⟨⟨⟨⟨ha, hl⟩, hc⟩, hvs⟩, hi⟩, hch⟩


/-- **ويتكرّر بلا حدّ**: الدرجةُ الثالثة تُسطَّح إلى الأولى. -/
theorem lift_lift (wss : List (List (List α))) :
    licWasl (lift (lift N)) wss = true ↔
      (wss.all (fun v => !v.isEmpty) = true ∧ wss.flatten.all (fun v => !v.isEmpty) = true ∧
        licWasl N wss.flatten.flatten = true) := by
  rw [lift_flatten, lift_flatten]

open A116.Ladder in
/-- **العنصرُ الأوسطُ لا يلزمه ابتداء**: «فِ» ثمّ «لْحَمْ» مرخَّصتان موصولتين في الأعلى، والثانيةُ وحدَها غيرُ
مرخَّصة — قانونُ همزة الوصل نظامًا. -/
theorem wasl_element_needs_no_ibtida :
    let fi := [atom 'ف' .kasra]
    let lham := [atom 'ل' .sukun, atom 'ح' .fatha, atom 'م' .sukun]
    licWasl (lift binary) [fi, lham] = true ∧ licWasl binary lham = false := by
  decide

end A116.Nizam
