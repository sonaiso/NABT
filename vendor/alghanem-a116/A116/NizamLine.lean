import A116.NizamHadd

/-!
# الحدُّ بين كلمتين مثولًا للنواة: الترخيصُ من الخانة إلى السطر (ADR ٢٧)

قرارُ المالك (2026-10-12): «الخطوة التالية جعلُ الحدّ بين كلمتين حالةً من النواة، وهو نفسه `lift` على `haddN`. بذلك يكتمل
الترخيصُ من الخانة إلى السطر، قبل الانتقال إلى طبقة الحكم. موافق».

## ما وجدتُه قبل الكتابة

`Hadd.strictJoinB l r = strictB (l ++ r) && !straddles l r`: الكلمتان موصولتين مرخَّصتان، ولا قافيةَ مدٍّ يقطعها الحدّ —
لا مدٌّ آخرَ الأولى يليه مُغلِقٌ أوّلَ الثانية، ولا (مدّ، مُغلِق) آخرَ الأولى يليه أوّلُ الثانية. و`Nizam.lift` **حرفيًّا** لا يكفي:
عناصرُ `haddN` أزواجٌ، والزوجُ العابرُ (آخرُ الأولى، أوّلُ الثانية) ليس في أزواج أيٍّ من الكلمتين. فالرفعُ هنا رفعٌ **بعنصر الحدّ**:
السطرُ أزواجُ كلماته، وبين كلّ كلمتين زوجٌ عابرٌ موسومٌ بالعبور (`tagC`) — «الحدُّ نفسُه عنصرٌ في النظام الأعلى».

## المبرهَن

* `haddJ`: نظامُ الأزواج الموسومة — هو `haddN` وشرطان على العبور: الزوجُ العابرُ ليس (مدّ، مُغلِق)، ولا يسبقه (مدّ، مُغلِق).
  `licWasl_haddJ`: ترخيصُه هو ترخيصُ `haddN` على الأزواج بلا وسم، وشرطُ العبور `crossOK` — لكلّ قائمة.
* `tagC_fst`: أزواجُ السطر بلا وسم هي أزواجُ تسطيحه (`azwaj`)، و`crossOK_tagC`: شرطُ العبور هو سلامةُ كلّ حدٍّ (`seamsOK`).
* **الجامع** `strictLineB_is_nizam`: ترخيصُ السطر (`strictLineB`: تسطيحُه مرخَّصٌ بقيد الحدّ ولا حدَّ تقطعه قافيةُ مدّ) هو
  ترخيصُ `haddJ` على أزواجه الموسومة وشرطُ الطرف — لكلّ سطرٍ بكلماتٍ غيرِ فارغة (غيرِ مدّ الفرق).
* **الحدّان مثولٌ للقائم**: `line_two`: سطرٌ من كلمتين هو `Hadd.strictJoinB` بعينه؛ وشواهدُه (`witnesses`): يَا + الشَّافِعِينَ
  مرفوضٌ سطرًا، وقُلِ + ضَالِّينَ وقُلِ + الْحَمْدُ مقبولان.
* `seamsOK_append`: سطرٌ موصولٌ بسطرٍ سلامةُ حدوده سلامةُ حدود السطرين وحدِّهما — فالبنيةُ تتكرّر بلا حدّ.
* `line_two_pause`، `strictLinePauseB_split`: وقفًا كذلك (`Hadd.strictJoinPauseB`).
-/

namespace A116.NizamLine

open A116 A116.Stages A116.Ternary A116.Hadd A116.Nizam A116.NizamHadd

abbrev Edge := Role × Role
/-- الزوجُ موسومًا بعبوره حدًّا بين كلمتين. -/
abbrev TEdge := Edge × Bool

/-- (مدّ، مُغلِق). -/
def isVC (e : Edge) : Bool := e.1.1 == .v && e.2.1 == .c

/-! ## ١. نظامُ الأزواج الموسومة -/

def haddJ : Nizam TEdge where
  wujud x := haddN.wujud x.1 && !(x.2 && isVC x.1)
  ibtida x := haddN.ibtida x.1
  wasl x y := haddN.wasl x.1 y.1 && !(y.2 && isVC x.1)
  waqf _ _ := false

/-- شرطُ العبور: الزوجُ العابرُ ليس (مدّ، مُغلِق)، وما قبل العابر ليس (مدّ، مُغلِق). -/
def crossOK : List TEdge → Bool
  | [] => true
  | [x] => !(x.2 && isVC x.1)
  | x :: y :: t => !(x.2 && isVC x.1) && !(y.2 && isVC x.1) && crossOK (y :: t)

theorem chainJ : ∀ (x : TEdge) (t : List TEdge),
    ((x :: t).all haddJ.wujud = true ∧ chain haddJ x t = true) ↔
      (((x :: t).map Prod.fst).all haddN.wujud = true ∧ chain haddN x.1 (t.map Prod.fst) = true ∧
        crossOK (x :: t) = true)
  | x, [] => by simp [haddJ, chain, crossOK]
  | x, y :: t => by
    have ih := chainJ y t
    simp only [List.all_cons, List.map_cons, chain, Bool.and_eq_true] at ih ⊢
    simp only [crossOK, Bool.and_eq_true]
    simp only [haddJ, Bool.and_eq_true] at ih ⊢
    constructor
    · rintro ⟨⟨⟨hx, hxc⟩, ⟨hy, hyc⟩, ht⟩, ⟨hw, hwc⟩, hch⟩
      obtain ⟨⟨_, n2⟩, n3, n4⟩ := ih.1 ⟨⟨⟨hy, hyc⟩, ht⟩, hch⟩
      exact ⟨⟨hx, hy, n2⟩, ⟨hw, n3⟩, ⟨hxc, hwc⟩, n4⟩
    · rintro ⟨⟨hx, hy, n2⟩, ⟨hw, n3⟩, ⟨hxc, hwc⟩, n4⟩
      have hyc : (!(y.2 && isVC y.1)) = true := by
        cases t with
        | nil => simpa [crossOK] using n4
        | cons z t => simp only [crossOK, Bool.and_eq_true] at n4; exact n4.1.1
      obtain ⟨⟨⟨_, _⟩, ht⟩, hch⟩ := ih.2 ⟨⟨hy, n2⟩, n3, n4⟩
      exact ⟨⟨⟨hx, hxc⟩, ⟨hy, hyc⟩, ht⟩, ⟨hw, hwc⟩, hch⟩

/-- **ترخيصُ الأزواج الموسومة هو ترخيصُ `haddN` على الأزواج وشرطُ العبور**، لكلّ قائمة. -/
theorem licWasl_haddJ (L : List TEdge) :
    licWasl haddJ L = (licWasl haddN (L.map Prod.fst) && crossOK L) := by
  cases L with
  | nil => rfl
  | cons x t =>
    have h := chainJ x t
    apply Bool.eq_iff_iff.2
    simp only [licWasl, List.map_cons, Bool.and_eq_true] at h ⊢
    have hi : haddJ.ibtida x = haddN.ibtida x.1 := rfl
    rw [hi]
    constructor
    · rintro ⟨⟨ha, hi⟩, hc⟩
      obtain ⟨n1, n2, n3⟩ := h.1 ⟨ha, hc⟩
      exact ⟨⟨⟨n1, hi⟩, n2⟩, n3⟩
    · rintro ⟨⟨⟨n1, hi⟩, n2⟩, n3⟩
      obtain ⟨ha, hc⟩ := h.2 ⟨n1, n2, n3⟩
      exact ⟨⟨ha, hi⟩, hc⟩

/-! ## ٢. شرطُ العبور بالتراكم: ما قبل كلّ عنصرٍ يحمل خبرَه -/

/-- الشرطُ نفسُه بحاملٍ لما قبله: `p` = أكان الزوجُ السابقُ (مدّ، مُغلِق). -/
def crossFrom : Bool → List TEdge → Bool
  | _, [] => true
  | p, x :: t => !(x.2 && isVC x.1) && !(x.2 && p) && crossFrom (isVC x.1) t

theorem crossOK_eq : ∀ L : List TEdge, crossOK L = crossFrom false L
  | [] => rfl
  | [x] => by simp [crossOK, crossFrom]
  | x :: y :: t => by
    have ih := crossOK_eq (y :: t)
    simp only [crossOK, crossFrom] at ih ⊢
    rw [ih]
    cases x.2 <;> cases isVC x.1 <;> cases y.2 <;> cases isVC y.1 <;> simp

/-- خبرُ آخر القائمة. -/
def lastVC (p : Bool) (A : List TEdge) : Bool :=
  match A.getLast? with
  | some x => isVC x.1
  | none => p

theorem crossFrom_append : ∀ (p : Bool) (A B : List TEdge),
    crossFrom p (A ++ B) = (crossFrom p A && crossFrom (lastVC p A) B)
  | p, [], B => by simp [crossFrom, lastVC]
  | p, x :: A, B => by
    simp only [List.cons_append, crossFrom, crossFrom_append (isVC x.1) A B, Bool.and_assoc]
    congr 3
    cases A with
    | nil => simp [lastVC]
    | cons y A =>
      have e : (y :: A).getLast? = some ((y :: A).getLast (by simp)) := List.getLast?_eq_some_getLast _
      have e2 : (x :: y :: A).getLast? = some ((y :: A).getLast (by simp)) := by
        rw [List.getLast?_cons_cons]; exact e
      simp only [lastVC, e, e2]

/-- الأزواجُ بلا وسم لا تمسّ شرطَ العبور. -/
theorem crossFrom_untagged : ∀ (p : Bool) (E : List Edge), crossFrom p (E.map (·, false)) = true
  | _, [] => rfl
  | _, e :: E => by simp [crossFrom, crossFrom_untagged _ E]

/-! ## ٣. السطرُ كلماتٍ: أزواجُ كلّ كلمة، والزوجُ العابرُ بينها -/

/-- آخرُ أزواج الكلمة (مدّ، مُغلِق). -/
def endsVC (c : List Role) : Bool :=
  match (azwaj c).getLast? with
  | some e => isVC e
  | none => false

/-- الزوجُ العابرُ بين كلمتين. -/
def crossE (c d : List Role) : List TEdge :=
  match c.getLast?, d.head? with
  | some x, some y => [((x, y), true)]
  | _, _ => []

/-- الحدُّ تقطعه قافيةُ مدّ: مدٌّ آخرَ الأولى ومُغلِقٌ أوّلَ الثانية، أو (مدّ، مُغلِق) آخرَ الأولى (`Hadd.straddles`). -/
def crossStr (c d : List Role) : Bool :=
  match c.getLast?, d.head? with
  | some x, some y => isVC (x, y) || endsVC c
  | _, _ => false

def seamsOK : List (List Role) → Bool
  | c :: d :: rest => !crossStr c d && seamsOK (d :: rest)
  | _ => true

/-- أزواجُ السطر موسومة: داخلَ الكلمة بلا وسم، وبين كلمتين زوجٌ عابر. -/
def tagC : List (List Role) → List TEdge
  | [] => []
  | [c] => (azwaj c).map (·, false)
  | c :: d :: rest => (azwaj c).map (·, false) ++ crossE c d ++ tagC (d :: rest)

theorem azwaj_append (a : Role) (l : List Role) (b : Role) (m : List Role) :
    azwaj ((a :: l) ++ (b :: m)) = azwaj (a :: l) ++ ((a :: l).getLast (by simp), b) :: azwaj (b :: m) := by
  induction l generalizing a with
  | nil => rfl
  | cons x l ih =>
    simp only [List.cons_append] at ih ⊢
    simp only [azwaj, ih x, List.cons_append, List.getLast_cons_cons]

theorem tagC_fst : ∀ cs : List (List Role), (∀ c ∈ cs, c ≠ []) →
    (tagC cs).map Prod.fst = azwaj cs.flatten
  | [], _ => rfl
  | [c], _ => by simp [tagC, Function.comp_def]
  | c :: d :: rest, h => by
    have ih := tagC_fst (d :: rest) (fun x hx => h x (List.mem_cons_of_mem _ hx))
    obtain ⟨a, l, rfl⟩ : ∃ a l, c = a :: l := by
      cases c with
      | nil => exact absurd rfl (h [] (by simp))
      | cons a l => exact ⟨a, l, rfl⟩
    obtain ⟨b, m, rfl⟩ : ∃ b m, d = b :: m := by
      cases d with
      | nil => exact absurd rfl (h [] (by simp))
      | cons b m => exact ⟨b, m, rfl⟩
    have hf : ((b :: m) :: rest).flatten = b :: (m ++ rest.flatten) := by simp
    show List.map Prod.fst (tagC ((a :: l) :: (b :: m) :: rest)) = azwaj ((a :: l) ++ (b :: (m ++ rest.flatten)))
    rw [azwaj_append, ← hf, ← ih]
    have e : (a :: l).getLast? = some ((a :: l).getLast (by simp)) := List.getLast?_eq_some_getLast _
    simp [tagC, crossE, e, Function.comp_def]

theorem lastVC_untagged (a : Role) (l : List Role) :
    lastVC false ((azwaj (a :: l)).map (·, false)) = endsVC (a :: l) := by
  simp only [lastVC, endsVC, List.getLast?_map]
  cases (azwaj (a :: l)).getLast? <;> rfl

/-- **شرطُ العبور هو سلامةُ كلّ حدّ.** -/
theorem crossOK_tagC : ∀ cs : List (List Role), (∀ c ∈ cs, c ≠ []) → crossOK (tagC cs) = seamsOK cs
  | [], _ => rfl
  | [c], _ => by rw [crossOK_eq]; simp [tagC, seamsOK, crossFrom_untagged]
  | c :: d :: rest, h => by
    have ih := crossOK_tagC (d :: rest) (fun x hx => h x (List.mem_cons_of_mem _ hx))
    rw [crossOK_eq] at ih ⊢
    obtain ⟨a, l, rfl⟩ : ∃ a l, c = a :: l := by
      cases c with
      | nil => exact absurd rfl (h [] (by simp))
      | cons a l => exact ⟨a, l, rfl⟩
    obtain ⟨b, m, rfl⟩ : ∃ b m, d = b :: m := by
      cases d with
      | nil => exact absurd rfl (h [] (by simp))
      | cons b m => exact ⟨b, m, rfl⟩
    have e : (a :: l).getLast? = some ((a :: l).getLast (by simp)) := List.getLast?_eq_some_getLast _
    simp only [tagC, e, List.append_assoc, crossFrom_append, crossFrom_untagged, Bool.true_and,
      lastVC_untagged, crossE, List.head?_cons, List.singleton_append,
      crossFrom, seamsOK, crossStr]
    rw [← ih]
    cases hx : isVC ((a :: l).getLast (by simp), b) <;> cases endsVC (a :: l) <;> simp

/-! ## ٤. السطر: الجامع والحدّان -/

/-- تقطيعُ قائمةٍ بأطوال. -/
def splitBy {β : Type} : List Nat → List β → List (List β)
  | [], _ => []
  | n :: ns, p => p.take n :: splitBy ns (p.drop n)

theorem splitBy_flatten {β : Type} : ∀ (ns : List Nat) (p : List β), ns.sum = p.length →
    (splitBy ns p).flatten = p
  | [], p, h => by simp at h; simp [splitBy, List.eq_nil_of_length_eq_zero h.symm]
  | n :: ns, p, h => by
    simp only [List.sum_cons] at h
    simp only [splitBy, List.flatten_cons]
    rw [splitBy_flatten ns (p.drop n) (by rw [List.length_drop]; omega), List.take_append_drop]

theorem splitBy_ne {β : Type} : ∀ (ns : List Nat) (p : List β), ns.sum = p.length → (∀ n ∈ ns, 0 < n) →
    ∀ c ∈ splitBy ns p, c ≠ []
  | [], _, _, _, c, hc => by simp [splitBy] at hc
  | n :: ns, p, h, hp, c, hc => by
    simp only [List.sum_cons] at h
    simp only [splitBy, List.mem_cons] at hc
    rcases hc with rfl | hc
    · have := hp n (by simp); intro he
      have h2 := congrArg List.length he; rw [List.length_take, List.length_nil] at h2; omega
    · exact splitBy_ne ns (p.drop n) (by rw [List.length_drop]; omega) (fun m hm => hp m (by simp [hm])) c hc

/-- أدوارُ السطر مقطَّعةً كلماتٍ — الأصنافُ من السطر موصولًا. -/
def chunks (ws : List (List Cell)) : List (List Role) :=
  splitBy (ws.map List.length) (roles ws.flatten)

/-- **ترخيصُ السطر**: تسطيحُه مرخَّصٌ بقيد الحدّ، ولا حدَّ بين كلمتين تقطعه قافيةُ مدّ. -/
def strictLineB (ws : List (List Cell)) : Bool := strictB ws.flatten && seamsOK (chunks ws)

theorem roles_length (w : List Cell) : (roles w).length = w.length := by
  simp [roles, kindOf, kindGo_length]

theorem sum_lengths (ws : List (List Cell)) : (ws.map List.length).sum = ws.flatten.length := by
  induction ws with
  | nil => rfl
  | cons w ws ih => rw [List.map_cons, List.sum_cons, List.flatten_cons, List.length_append, ih]

theorem chunks_flatten (ws : List (List Cell)) : (chunks ws).flatten = roles ws.flatten :=
  splitBy_flatten _ _ (by rw [roles_length, sum_lengths])

theorem chunks_ne (ws : List (List Cell)) (h : ∀ w ∈ ws, w ≠ []) : ∀ c ∈ chunks ws, c ≠ [] :=
  splitBy_ne _ _ (by rw [roles_length, sum_lengths]) (by
    intro n hn; simp only [List.mem_map] at hn; obtain ⟨w, hw, rfl⟩ := hn
    cases w with
    | nil => exact absurd rfl (h [] hw)
    | cons _ _ => simp)

/-- **الجامع**: ترخيصُ السطر هو ترخيصُ `haddJ` على أزواجه الموسومة وشرطُ الطرف. -/
theorem strictLineB_is_nizam (ws : List (List Cell)) (hne : ∀ w ∈ ws, w ≠ [])
    (hf : isFarq ws.flatten = false) (hl : 2 ≤ ws.flatten.length) :
    strictLineB ws = (licWasl haddJ (tagC (chunks ws)) && tarafWasl (roles ws.flatten)) := by
  unfold strictLineB
  rw [strictB_is_nizam _ hf hl, licWasl_haddJ, tagC_fst _ (chunks_ne ws hne), chunks_flatten,
    crossOK_tagC _ (chunks_ne ws hne)]
  cases licWasl haddN (azwaj (roles ws.flatten)) <;> cases tarafWasl (roles ws.flatten) <;>
    cases seamsOK (chunks ws) <;> rfl

/-- **سطرٌ موصولٌ بسطرٍ هو السطران وحدُّهما**: سلامةُ الحدود تتجزّأ على الحدّ بينهما. -/
theorem seamsOK_append : ∀ (A : List (List Role)) (c d : List Role) (B : List (List Role)),
    seamsOK (A ++ c :: d :: B) = (seamsOK (A ++ [c]) && !crossStr c d && seamsOK (d :: B))
  | [], c, d, B => by simp [seamsOK]
  | [a], c, d, B => by simp [seamsOK, Bool.and_assoc]
  | a :: a' :: A, c, d, B => by
    have ih := seamsOK_append (a' :: A) c d B
    simp only [List.cons_append] at ih ⊢
    simp only [seamsOK, ih, Bool.and_assoc]

/-! ## ٥. الحدُّ بين كلمتين: `Hadd.strictJoinB` مثولٌ -/

/-- شرطُ `Hadd.straddles` على الأصناف بموضع الحدّ `b`. -/
def straddlesK (k : List K) (b : Nat) : Bool :=
  (decide (1 ≤ b) && k[b - 1]? == some .v && k[b]? == some .c) ||
    (decide (2 ≤ b) && k[b - 2]? == some .v && k[b - 1]? == some .c)

theorem straddles_eq (l r : List Cell) : straddles l r = straddlesK (kindOf (l ++ r)) l.length := rfl

theorem azwaj_concat (a : Role) (l : List Role) (x : Role) :
    azwaj ((a :: l) ++ [x]) = azwaj (a :: l) ++ [((a :: l).getLast (by simp), x)] :=
  azwaj_append a l x []

theorem endsVC_concat (l : List Role) (w x : Role) : endsVC (l ++ [w, x]) = isVC (w, x) := by
  cases l with
  | nil => rfl
  | cons a l =>
    have h : a :: l ++ [w, x] = (a :: (l ++ [w])) ++ [x] := by simp
    rw [h, endsVC, azwaj_concat]
    have hw : (a :: (l ++ [w])).getLast (by simp) = w := by rw [List.getLast_cons (by simp)]; simp
    simp [hw]

/-- **موضعُ الحدّ**: قطعُ أدوار السطر عند `b` يجعل `crossStr` شرطَ `straddles` بعينه. -/
theorem crossStr_split (p : List Role) (b : Nat) (h1 : 1 ≤ b) (h2 : b < p.length) :
    crossStr (p.take b) (p.drop b) = straddlesK (p.map Prod.fst) b := by
  obtain ⟨c, d, hp, hc⟩ : ∃ c d, p = c ++ d ∧ c.length = b :=
    ⟨p.take b, p.drop b, (List.take_append_drop b p).symm, by rw [List.length_take]; omega⟩
  subst hp
  have hd : d ≠ [] := by intro e; subst e; simp at h2; omega
  obtain ⟨y, d', rfl⟩ : ∃ y d', d = y :: d' := by
    cases d with
    | nil => exact absurd rfl hd
    | cons y d' => exact ⟨y, d', rfl⟩
  obtain ⟨c', x, rfl⟩ : ∃ c' x, c = c' ++ [x] := by
    rcases List.eq_nil_or_concat c with e | ⟨c', x, e⟩
    · subst e; simp at hc; omega
    · exact ⟨c', x, by simpa using e⟩
  simp only [List.length_append, List.length_singleton] at hc
  subst hc
  have ht : (c' ++ [x] ++ y :: d').take (c'.length + 1) = c' ++ [x] := by
    simp only [List.append_assoc, List.singleton_append]; rw [List.take_append]
    simp [List.take_of_length_le (show c'.length ≤ c'.length + 1 by omega)]
  have hdr : (c' ++ [x] ++ y :: d').drop (c'.length + 1) = y :: d' := by
    simp only [List.append_assoc, List.singleton_append]; rw [List.drop_append]; simp
  have e1 : ((c' ++ [x] ++ y :: d').map Prod.fst)[c'.length + 1 - 1]? = some x.1 := by simp
  have e2 : ((c' ++ [x] ++ y :: d').map Prod.fst)[c'.length + 1]? = some y.1 := by
    rw [List.getElem?_map]
    simp only [List.append_assoc, List.singleton_append]; rw [List.getElem?_append_right (by simp)]; simp
  have hl : (c' ++ [x]).getLast? = some x := by simp
  rw [ht, hdr]
  unfold crossStr straddlesK
  rw [hl, List.head?_cons, e1, e2]
  rcases List.eq_nil_or_concat c' with e | ⟨c'', w, e⟩
  · subst e; simp [endsVC, azwaj, isVC]
  · have e' : c' = c'' ++ [w] := by simpa using e
    subst e'
    have e3 : ((c'' ++ [w] ++ [x] ++ y :: d').map Prod.fst)[(c'' ++ [w]).length + 1 - 2]? = some w.1 := by
      simp
    rw [e3, show c'' ++ [w] ++ [x] = c'' ++ [w, x] by simp, endsVC_concat]
    have h2 : 2 ≤ (c'' ++ [w]).length + 1 := by simp
    simp only [isVC, h2, decide_true, Bool.true_and]
    cases x.1 <;> cases y.1 <;> cases w.1 <;> simp

/-- **سطرٌ من كلمتين هو `Hadd.strictJoinB` بعينه.** -/
theorem line_two (l r : List Cell) (hl : l ≠ []) (hr : r ≠ []) : strictLineB [l, r] = strictJoinB l r := by
  have hb1 : 1 ≤ l.length := by cases l <;> simp_all
  have hr1 : 1 ≤ r.length := by cases r <;> simp_all
  have hp : (roles (l ++ r)).length = l.length + r.length := by rw [roles_length]; simp
  unfold strictLineB strictJoinB
  have hf : [l, r].flatten = l ++ r := by simp
  simp only [hf, chunks, List.map_cons, List.map_nil, splitBy, seamsOK, Bool.and_true]
  have e : List.take r.length (List.drop l.length (roles (l ++ r))) = List.drop l.length (roles (l ++ r)) :=
    List.take_of_length_le (by rw [List.length_drop]; omega)
  rw [e, crossStr_split _ _ hb1 (by omega), roles_fst, straddles_eq]

/-! ## ٦. الوقفُ على السطر، والشواهد -/

/-- ترخيصُ السطر وقفًا: تسطيحُه مرخَّصٌ بقيد الحدّ وقفًا، ولا حدَّ تقطعه قافيةُ مدّ. -/
def strictLinePauseB (ws : List (List Cell)) : Bool := strictPauseB ws.flatten && seamsOK (chunks ws)

/-- وقفًا: الجوارُ الثلاثيُّ وقفًا، والنافذة، وشرطُ العبور على الأزواج الموسومة. -/
theorem strictLinePauseB_split (ws : List (List Cell)) (hne : ∀ w ∈ ws, w ≠ [])
    (hf : isFarq ws.flatten = false) :
    strictLinePauseB ws =
      (licWaqf ternary (kindOf ws.flatten) && win3 hR (roles ws.flatten) && crossOK (tagC (chunks ws))) := by
  unfold strictLinePauseB
  rw [strictPauseB_split _ hf, crossOK_tagC _ (chunks_ne ws hne)]

/-- وسطرٌ من كلمتين وقفًا هو `Hadd.strictJoinPauseB` بعينه. -/
theorem line_two_pause (l r : List Cell) (hl : l ≠ []) (hr : r ≠ []) :
    strictLinePauseB [l, r] = strictJoinPauseB l r := by
  have hb1 : 1 ≤ l.length := by cases l <;> simp_all
  have hr1 : 1 ≤ r.length := by cases r <;> simp_all
  have hp : (roles (l ++ r)).length = l.length + r.length := by rw [roles_length]; simp
  unfold strictLinePauseB strictJoinPauseB
  have hf : [l, r].flatten = l ++ r := by simp
  simp only [hf, chunks, List.map_cons, List.map_nil, splitBy, seamsOK, Bool.and_true]
  have e : List.take r.length (List.drop l.length (roles (l ++ r))) = List.drop l.length (roles (l ++ r)) :=
    List.take_of_length_le (by rw [List.length_drop]; omega)
  rw [e, crossStr_split _ _ hb1 (by omega), roles_fst, straddles_eq]

/-- شواهد: يَا + الشَّافِعِينَ مرفوضٌ سطرًا (مقبولٌ تسطيحُه)، وقُلِ + ضَالِّينَ وقُلِ + الْحَمْدُ مقبولان، وسطرٌ من ثلاثٍ مقبول. -/
theorem witnesses :
    strictB (ya ++ shshafiina) = true ∧ strictLineB [ya, shshafiina] = false ∧
    strictLineB [quli, dallina] = true ∧ strictLineB [quli, lhamdu] = true ∧
    strictLineB [quli, quli, lhamdu] = true := by
  decide +kernel

end A116.NizamLine
