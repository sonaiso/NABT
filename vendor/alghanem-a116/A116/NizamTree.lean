import A116.NizamLine

/-!
# القانونُ على الأشجار: ترخيصُ الشجرة ترخيصُ تسطيحها بشروط حدودها (ADR ٣٠)

قرارُ المالك (2026-10-12): «الشجرةُ عناصرُ وأبناء. والحدُّ بين الأب والابن عنصرٌ موسوم. ويُبرهَن أنّ ترخيصَ الشجرة هو
ترخيصُ تسطيحها مع شروط الحدود، وأنّ السطرَ (`strictLineB`) حالةٌ منها بشجرةٍ عمقُها واحد. بذلك لا يُهدم شيءٌ عند النحو».

## البناء

* `Tree`/`Forest`: الشجرةُ ورقةٌ أو أبٌ له أبناء (غابةٌ مرتّبة) — عددُ الأبناء حرّ، فالثنائيّةُ حالةٌ لا قيد.
* `yieldT`: التسطيحُ — الأوراقُ بترتيب القراءة.
* `seamsT`: شروطُ الحدود **بنيويًّا**: لكلّ أبٍ، كلُّ ابنٍ سليمُ الحدود في نفسه، وبين كلّ ابنين متجاورين حدٌّ لا تقطعه قافيةُ مدّ
  (آخرُ ورقةٍ في الأوّل، أوّلُ ورقةٍ في الثاني) — والحدُّ بين الأب والابن عنصرٌ موسومٌ بعمق أبيه (`tagT`).

## المبرهَن

* `seamsT_eq`: شروطُ الحدود على الشجرة هي سلامةُ حدود تسطيحها (`NizamLine.seamsOK`) — لكلّ شجرة، بلا شرط.
* `tree_eq_line`: ترخيصُ الشجرة (`strictTreeB`) هو ترخيصُ سطر أوراقها (`strictLineB`) — **لا يُهدم شيءٌ عند النحو**.
* `regroup_invariant`: شجرتان بأوراقٍ واحدة ترخيصُهما واحد — البنيةُ (النحو) تُحمل ولا تُغيّر الترخيص.
* `line_is_depth_one`: السطرُ شجرةٌ عمقُها واحد.
* `tagT_forget`: الأزواجُ الموسومةُ بالعمق إذا نُسي العمقُ هي أزواجُ السطر الموسومة (`NizamLine.tagC`)؛ و`licWasl_comap`:
  نظامٌ يقرأ عنصرَه بدالّةٍ ترخيصُه ترخيصُ صورته — فـ`tree_is_nizam`: ترخيصُ الشجرة هو ترخيصُ نظام الأزواج الموسومة
  بالعمق (`haddT`) وشرطُ الطرف.
-/

namespace A116.NizamTree

open A116 A116.Stages A116.Ternary A116.Hadd A116.Nizam A116.NizamHadd A116.NizamLine

/-! ## ١. الشجرة -/

mutual
inductive Tree (β : Type) where
  | leaf : β → Tree β
  | node : Forest β → Tree β
inductive Forest (β : Type) where
  | nil : Forest β
  | cons : Tree β → Forest β → Forest β
end

mutual
def yieldT {β : Type} : Tree β → List β
  | .leaf b => [b]
  | .node f => yieldF f
def yieldF {β : Type} : Forest β → List β
  | .nil => []
  | .cons t f => yieldT t ++ yieldF f
end

/-- الغابةُ من قائمة أوراق. -/
def leaves {β : Type} : List β → Forest β
  | [] => .nil
  | b :: bs => .cons (.leaf b) (leaves bs)

theorem yield_leaves {β : Type} : ∀ bs : List β, yieldF (leaves bs) = bs
  | [] => rfl
  | b :: bs => by simp [leaves, yieldF, yieldT, yield_leaves bs]

/-! ## ٢. شروطُ الحدود بنيويًّا -/

/-- الحدُّ بين متتاليتين من الكلمات: آخرُ كلمةٍ في الأولى وأوّلُ كلمةٍ في الثانية. -/
def seam (A B : List (List Role)) : Bool :=
  match A.getLast?, B.head? with
  | some c, some d => !crossStr c d
  | _, _ => true

mutual
def seamsT : Tree (List Role) → Bool
  | .leaf _ => true
  | .node f => seamsF f
def seamsF : Forest (List Role) → Bool
  | .nil => true
  | .cons t f => seamsT t && seam (yieldT t) (yieldF f) && seamsF f
end

theorem seamsOK_cons_append : ∀ (c : List Role) (A B : List (List Role)),
    seamsOK ((c :: A) ++ B) = (seamsOK (c :: A) && seam (c :: A) B && seamsOK B)
  | c, [], [] => by simp [seam, seamsOK]
  | c, [], d :: B => by simp [seam, seamsOK]
  | c, a :: A, B => by
    have ih := seamsOK_cons_append a A B
    have e : seam (c :: a :: A) B = seam (a :: A) B := by
      simp only [seam, List.getLast?_cons_cons]
    simp only [List.cons_append, seamsOK] at ih ⊢
    rw [ih, e]
    simp only [Bool.and_assoc]

/-- **سلامةُ الحدود تتجزّأ على أيّ حدّ**: لكلّ متتاليتين. -/
theorem seamsOK_split (A B : List (List Role)) :
    seamsOK (A ++ B) = (seamsOK A && seam A B && seamsOK B) := by
  cases A with
  | nil => simp [seam, seamsOK]
  | cons c A => exact seamsOK_cons_append c A B

mutual
/-- **شروطُ الحدود على الشجرة هي سلامةُ حدود تسطيحها**، لكلّ شجرة. -/
theorem seamsT_eq : ∀ t : Tree (List Role), seamsT t = seamsOK (yieldT t)
  | .leaf _ => rfl
  | .node f => by simp only [seamsT, yieldT]; exact seamsF_eq f
theorem seamsF_eq : ∀ f : Forest (List Role), seamsF f = seamsOK (yieldF f)
  | .nil => rfl
  | .cons t f => by
    simp only [seamsF, yieldF]
    rw [seamsOK_split, seamsT_eq t, seamsF_eq f]
end

/-! ## ٣. الأدوارُ على الشجرة: أصنافُ السطر موصولًا تُوزَّع على الأوراق بترتيبها -/

theorem splitBy_append {β : Type} : ∀ (ns ms : List Nat) (p : List β),
    splitBy (ns ++ ms) p = splitBy ns p ++ splitBy ms (p.drop ns.sum)
  | [], ms, p => by simp [splitBy]
  | n :: ns, ms, p => by
    simp only [List.cons_append, splitBy, List.sum_cons, splitBy_append ns ms (p.drop n), List.drop_drop]

mutual
/-- توزيعُ أدوارٍ على أوراق الشجرة بأطوالها، والباقي. -/
def fillT : Tree (List Cell) → List Role → Tree (List Role) × List Role
  | .leaf w, p => (.leaf (p.take w.length), p.drop w.length)
  | .node f, p => (.node (fillF f p).1, (fillF f p).2)
def fillF : Forest (List Cell) → List Role → Forest (List Role) × List Role
  | .nil, p => (.nil, p)
  | .cons t f, p => (.cons (fillT t p).1 (fillF f (fillT t p).2).1, (fillF f (fillT t p).2).2)
end

mutual
theorem fillT_yield : ∀ (t : Tree (List Cell)) (p : List Role),
    yieldT (fillT t p).1 = splitBy ((yieldT t).map List.length) p ∧
      (fillT t p).2 = p.drop ((yieldT t).map List.length).sum
  | .leaf w, p => by simp [fillT, yieldT, splitBy]
  | .node f, p => by simp only [fillT, yieldT]; exact fillF_yield f p
theorem fillF_yield : ∀ (f : Forest (List Cell)) (p : List Role),
    yieldF (fillF f p).1 = splitBy ((yieldF f).map List.length) p ∧
      (fillF f p).2 = p.drop ((yieldF f).map List.length).sum
  | .nil, p => by simp [fillF, yieldF, splitBy]
  | .cons t f, p => by
    obtain ⟨h1, h2⟩ := fillT_yield t p
    obtain ⟨h3, h4⟩ := fillF_yield f (fillT t p).2
    simp only [fillF, yieldF, List.map_append, splitBy_append, List.sum_append]
    rw [h1, h3, h4, h2, List.drop_drop]
    exact ⟨rfl, rfl⟩
end

/-- أدوارُ الشجرة: الشجرةُ نفسُها، وكلُّ ورقةٍ أدوارُها من السطر موصولًا. -/
def rolesT (t : Tree (List Cell)) : Tree (List Role) := (fillT t (roles (yieldT t).flatten)).1

/-- **أوراقُ أدوار الشجرة هي أدوارُ سطرها مقطَّعةً** (`NizamLine.chunks`). -/
theorem yield_rolesT (t : Tree (List Cell)) : yieldT (rolesT t) = chunks (yieldT t) :=
  (fillT_yield t _).1

/-! ## ٤. ترخيصُ الشجرة -/

/-- **ترخيصُ الشجرة**: تسطيحُها مرخَّصٌ بقيد الحدّ، وشروطُ الحدود بنيويًّا عند كلّ أب. -/
def strictTreeB (t : Tree (List Cell)) : Bool := strictB (yieldT t).flatten && seamsT (rolesT t)

/-- وقفًا. -/
def strictTreePauseB (t : Tree (List Cell)) : Bool := strictPauseB (yieldT t).flatten && seamsT (rolesT t)

/-- **ترخيصُ الشجرة هو ترخيصُ سطر أوراقها** — لكلّ شجرة، بلا شرط: لا يُهدم شيءٌ عند النحو. -/
theorem tree_eq_line (t : Tree (List Cell)) : strictTreeB t = strictLineB (yieldT t) := by
  unfold strictTreeB strictLineB
  rw [seamsT_eq, yield_rolesT]

theorem tree_eq_line_pause (t : Tree (List Cell)) : strictTreePauseB t = strictLinePauseB (yieldT t) := by
  unfold strictTreePauseB strictLinePauseB
  rw [seamsT_eq, yield_rolesT]

/-- **إعادةُ التجميع لا تغيّر الترخيص**: شجرتان بأوراقٍ واحدة ترخيصُهما واحد، وصلًا ووقفًا. -/
theorem regroup_invariant (t u : Tree (List Cell)) (h : yieldT t = yieldT u) :
    strictTreeB t = strictTreeB u ∧ strictTreePauseB t = strictTreePauseB u := by
  simp only [tree_eq_line, tree_eq_line_pause, h, and_self]

/-- **السطرُ شجرةٌ عمقُها واحد**: أبٌ واحدٌ أبناؤه الكلمات. -/
theorem line_is_depth_one (ws : List (List Cell)) :
    strictTreeB (.node (leaves ws)) = strictLineB ws ∧
      strictTreePauseB (.node (leaves ws)) = strictLinePauseB ws := by
  simp only [tree_eq_line, tree_eq_line_pause, yieldT, yield_leaves, and_self]

/-- وفيها الحدُّ بين كلمتين: شجرةٌ من ورقتين هي `Hadd.strictJoinB` بعينه. -/
theorem tree_two (l r : List Cell) (hl : l ≠ []) (hr : r ≠ []) :
    strictTreeB (.node (leaves [l, r])) = strictJoinB l r := by
  rw [(line_is_depth_one [l, r]).1, line_two l r hl hr]

/-! ## ٥. الحدُّ موسومًا بعمق أبيه، والشجرةُ مثولٌ للنواة -/

/-- الزوجُ موسومًا: `none` داخلَ الكلمة، و`some d` على حدٍّ بين ابنين لأبٍ عمقُه `d`. -/
abbrev DEdge := Edge × Option Nat

/-- الحدُّ بين متتاليتين من الكلمات. -/
def crossW (A B : List (List Role)) : List TEdge :=
  match A.getLast?, B.head? with
  | some c, some d => crossE c d
  | _, _ => []

/-- الحدُّ موسومًا بعمق الأب. -/
def crossWd (d : Nat) (A B : List (List Role)) : List DEdge := (crossW A B).map (fun x => (x.1, some d))

mutual
/-- أزواجُ الشجرة موسومةً بعمق كلّ حدّ. -/
def edgesT : Nat → Tree (List Role) → List DEdge
  | _, .leaf c => (azwaj c).map (·, none)
  | d, .node f => edgesF d f
def edgesF : Nat → Forest (List Role) → List DEdge
  | _, .nil => []
  | d, .cons t f => edgesT (d + 1) t ++ crossWd d (yieldT t) (yieldF f) ++ edgesF d f
end

/-- نسيانُ العمق: الموسومُ بعمقٍ ما عابرٌ. -/
def forget (x : DEdge) : TEdge := (x.1, x.2.isSome)

theorem crossE_tagged : ∀ c d : List Role, (crossE c d).map (fun x => (x.1, true)) = crossE c d := by
  intro c d
  unfold crossE
  cases c.getLast? <;> cases d.head? <;> rfl

theorem crossW_tagged (A B : List (List Role)) : (crossW A B).map (fun x => (x.1, true)) = crossW A B := by
  unfold crossW
  split
  · exact crossE_tagged _ _
  · rfl

theorem forget_crossWd (d : Nat) (A B : List (List Role)) :
    (crossWd d A B).map forget = crossW A B := by
  unfold crossWd
  rw [List.map_map]
  exact crossW_tagged A B

theorem tagC_append : ∀ A B : List (List Role), tagC (A ++ B) = tagC A ++ crossW A B ++ tagC B
  | [], B => by simp [tagC, crossW]
  | [a], [] => by simp [tagC, crossW]
  | [a], b :: B => by simp [tagC, crossW]
  | a :: a' :: A, B => by
    have ih := tagC_append (a' :: A) B
    have e : crossW (a :: a' :: A) B = crossW (a' :: A) B := by
      simp only [crossW, List.getLast?_cons_cons]
    simp only [List.cons_append] at ih ⊢
    simp only [tagC, ih, e, List.append_assoc]

mutual
/-- **نسيانُ العمق يردّ أزواجَ السطر الموسومة** (`NizamLine.tagC`) — لكلّ شجرةٍ ولكلّ عمق. -/
theorem tagT_forget : ∀ (d : Nat) (t : Tree (List Role)), (edgesT d t).map forget = tagC (yieldT t)
  | _, .leaf c => by simp [edgesT, yieldT, tagC, forget, Function.comp_def]
  | d, .node f => by simp only [edgesT, yieldT]; exact tagF_forget d f
theorem tagF_forget : ∀ (d : Nat) (f : Forest (List Role)), (edgesF d f).map forget = tagC (yieldF f)
  | _, .nil => rfl
  | d, .cons t f => by
    simp only [edgesF, yieldF, List.map_append, tagC_append]
    rw [tagT_forget (d + 1) t, forget_crossWd, tagF_forget d f]
end

/-- نظامٌ يقرأ عنصرَه بدالّة. -/
def comap {α β : Type} (N : Nizam α) (g : β → α) : Nizam β where
  wujud x := N.wujud (g x)
  ibtida x := N.ibtida (g x)
  wasl x y := N.wasl (g x) (g y)
  waqf x y := N.waqf (g x) (g y)

theorem chain_comap {α β : Type} (N : Nizam α) (g : β → α) :
    ∀ (x : β) (L : List β), chain (comap N g) x L = chain N (g x) (L.map g)
  | _, [] => rfl
  | x, y :: L => by simp only [chain, List.map_cons, chain_comap N g y L]; rfl

theorem chainP_comap {α β : Type} (N : Nizam α) (g : β → α) :
    ∀ (x : β) (L : List β), chainP (comap N g) x L = chainP N (g x) (L.map g)
  | _, [] => rfl
  | _, [_] => rfl
  | x, y :: z :: L => by
    simp only [chainP, List.map_cons]
    rw [← List.map_cons, ← chainP_comap N g y (z :: L)]; rfl

/-- **ترخيصُ نظامٍ مقروءٍ بدالّة هو ترخيصُ صورته**، وصلًا ووقفًا. -/
theorem licWasl_comap {α β : Type} (N : Nizam α) (g : β → α) (L : List β) :
    licWasl (comap N g) L = licWasl N (L.map g) := by
  cases L with
  | nil => rfl
  | cons x L =>
    simp only [licWasl, List.map_cons, chain_comap, List.all_cons, List.all_map, Function.comp_def]
    rfl

theorem licWaqf_comap {α β : Type} (N : Nizam α) (g : β → α) (L : List β) :
    licWaqf (comap N g) L = licWaqf N (L.map g) := by
  cases L with
  | nil => rfl
  | cons x L =>
    simp only [licWaqf, List.map_cons, chainP_comap, List.all_cons, List.all_map, Function.comp_def]
    rfl

/-- نظامُ أزواج الشجرة الموسومة بالعمق. -/
def haddT : Nizam DEdge := comap haddJ forget

/-- **الجامع**: ترخيصُ الشجرة هو ترخيصُ `haddT` على أزواجها الموسومة بالعمق وشرطُ الطرف
(خارجَ مدّ الفرق، وطولُ السطر اثنان فأكثر — شرطا `strictLineB_is_nizam` نفسُهما). -/
theorem tree_is_nizam (t : Tree (List Cell)) (hne : ∀ w ∈ yieldT t, w ≠ [])
    (hf : isFarq (yieldT t).flatten = false) (hl : 2 ≤ (yieldT t).flatten.length) :
    strictTreeB t = (licWasl haddT (edgesT 0 (rolesT t)) && tarafWasl (roles (yieldT t).flatten)) := by
  rw [tree_eq_line, strictLineB_is_nizam _ hne hf hl, haddT, licWasl_comap, tagT_forget, yield_rolesT]

/-! ## ٦. الشواهد -/

/-- قُلِ ثمّ (قُلِ الْحَمْدُ) شجرةً عمقُها اثنان: مقبولة، وحدودُها موسومةٌ بعمقين؛ ويَا + الشَّافِعِينَ مرفوضٌ
مهما جُمِّع (ابنًا أعمقَ أو أخًا)، وتسطيحُه مقبول. -/
theorem witnesses :
    strictTreeB (.node (.cons (.leaf quli) (.cons (.node (leaves [quli, lhamdu])) .nil))) = true ∧
    ((edgesT 0 (rolesT (.node (.cons (.leaf quli) (.cons (.node (leaves [quli, lhamdu])) .nil))))).map
      Prod.snd).filter Option.isSome = [some 0, some 1] ∧
    strictB (ya ++ shshafiina) = true ∧
    strictTreeB (.node (leaves [ya, shshafiina])) = false ∧
    strictTreeB (.node (.cons (.leaf ya) (.cons (.node (leaves [shshafiina])) .nil))) = false := by
  decide +kernel

end A116.NizamTree
