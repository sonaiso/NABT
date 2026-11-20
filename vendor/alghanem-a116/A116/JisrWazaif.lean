import A116.Jisr
import A116.Qufl
import A116.NizamTree
import A116.Unicode

/-!
# ترخيصُ جسور الوظائف (ADR ٦٦، أمرُ المالك: «نفّذ برهانًا رياضيًّا يبرهن ترخيصَ جسور الوظائف SLGE بـLean»)

**الجسرُ المرخَّص** بين مستويين A (الأعلى) وB (الأدنى) أربعةُ أشياء، لا إعلان:

1. `enc : A → B` — الطيّ؛
2. `dec : B → Option A` و`radd : dec (enc a) = some a` — **لا ضياع**: ما يُطوى يُستردّ بعينه؛
3. `naql : licA a → licB (enc a)` — **نقلُ الترخيص** نزولًا: المرخَّصُ فوق مرخَّصٌ تحت؛
4. و`Tamm` إن عاد الترخيصُ صعودًا (⟺).

ثمّ: الجسرُ متباين (`enc_injective`)؛ وجسران يتركّبان جسرًا (`comp`، `comp_tamm`)؛ والجسرُ يُرفع إلى القوائم (`list`).

## الجسورُ المبنيّة على وظائف الشجرة

| الوظيفة | الجسر | لا ضياع | الترخيص |
|---|---|---|---|
| ترميز | نقطةُ يونيكود ← بايتات UTF-8 (`tarmiz`) | `Unicode.decode_encode` | تامّ |
| صوت/مقطع | مقاطع ← أصنافُ الخانة cv/v/c (`maqta`) | `Stages.parse_flat` | تامّ: `Hadd.continueB_flat` |
| اشتقاق | جذرٌ ثلاثيّ ← (خاناتُ الماضي، **الصفةُ بقيّةً**) (`ishtiqaq`) | `recover_madi` — **لكلّ جذر** صحيحًا ومعتلًّا | نزولًا: `Tasrif.madi_exhausted` |
| تركيب | كلمات ← (سطرٌ مسطَّح، **الأطوالُ بقيّةً**) (`tarkib`) | `split_flatten` | تامّ: `Nizam.lift_flatten` |
| جملة | جذورٌ ← كلماتٌ وصفاتٌ (`jumla` = `list ishtiqaq` ∘ `unzip`) | بالتركيب | نزولًا |

## وما لا يكون جسرًا بلا بقيّة — بمبرهنةٍ سالبة

* الاشتقاقُ **بلا الصفة** ليس جسرًا: «قَالَ» من قول وقيل خاناتٌ واحدة (`ishtiqaq_needs_sifa`).
* الشجرةُ ← السطر تنقل الترخيصَ بالضبط (`NizamTree.tree_eq_line`) لكنّها تُفقد التجميع (`tree_needs_shape`).
* الدلالةُ وراء الجسر: الدفترُ المقفول يقف عندها (`Qufl.locked _ .dalala`).
-/

namespace A116.JisrWazaif

open A116 A116.Stages A116.Ternary A116.Hadd A116.Wazn A116.Tasrif A116.Nizam

/-! ## ١. الجسرُ المرخَّص -/

structure Murakhkhas (A B : Type) where
  enc : A → B
  dec : B → Option A
  radd : ∀ a, dec (enc a) = some a
  licA : A → Prop
  licB : B → Prop
  naql : ∀ a, licA a → licB (enc a)

variable {A B C : Type}

/-- الجسرُ تامٌّ إذا عاد الترخيصُ صعودًا. -/
def Murakhkhas.Tamm (J : Murakhkhas A B) : Prop := ∀ a, J.licB (J.enc a) → J.licA a

/-- **لا ضياع ⇒ تباين.** -/
theorem enc_injective (J : Murakhkhas A B) (a a' : A) (h : J.enc a = J.enc a') : a = a' := by
  have h1 := J.radd a
  have h2 := J.radd a'
  rw [h, h2] at h1
  exact (Option.some.inj h1).symm

/-- **تركيبُ جسرين جسر**: بشرط أن يكون ترخيصُ أدنى الأوّل ترخيصَ أعلى الثاني. -/
def comp (J : Murakhkhas A B) (K : Murakhkhas B C) (hl : ∀ b, J.licB b → K.licA b) : Murakhkhas A C where
  enc a := K.enc (J.enc a)
  dec c := (K.dec c).bind J.dec
  radd a := by simp [K.radd, J.radd]
  licA := J.licA
  licB := K.licB
  naql a h := K.naql _ (hl _ (J.naql a h))

theorem comp_tamm (J : Murakhkhas A B) (K : Murakhkhas B C) (hl : ∀ b, J.licB b → K.licA b)
    (hl' : ∀ b, K.licA b → J.licB b) (hJ : J.Tamm) (hK : K.Tamm) : (comp J K hl).Tamm :=
  fun a h => hJ a (hl' _ (hK _ h))

/-- **الرفعُ إلى القوائم**: جسرُ العنصر جسرٌ للسلسلة. -/
def list (J : Murakhkhas A B) : Murakhkhas (List A) (List B) where
  enc := List.map J.enc
  dec bs := bs.mapM J.dec
  radd as := by
    induction as with
    | nil => rfl
    | cons a t ih => simp [List.mapM_cons, J.radd, ih]
  licA as := ∀ a ∈ as, J.licA a
  licB bs := ∀ b ∈ bs, J.licB b
  naql as h := by
    intro b hb
    obtain ⟨a, ha, rfl⟩ := List.mem_map.1 hb
    exact J.naql a (h a ha)

/-! ## ٢. الترميز: نقطةُ يونيكود ← بايتات UTF-8 -/

def tarmiz : Murakhkhas {c : Nat // c < 0x110000} (List Nat) where
  enc c := Unicode.utf8Encode c.1
  dec bs := match Unicode.utf8Decode bs with
    | some (c, []) => if h : c < 0x110000 then some ⟨c, h⟩ else none
    | _ => none
  radd c := by
    have := Unicode.decode_encode c.1 c.2 []
    simp only [List.append_nil] at this
    simp [this, c.2]
  licA _ := True
  licB bs := ∃ c, c < 0x110000 ∧ Unicode.utf8Decode bs = some (c, [])
  naql c _ := ⟨c.1, c.2, by simpa using Unicode.decode_encode c.1 c.2 []⟩

theorem tarmiz_tamm : tarmiz.Tamm := fun _ _ => trivial

/-! ## ٣. الصوت/المقطع: مقاطع ← أصنافُ الخانة -/

def maqta : Murakhkhas (List Syl) (List K) where
  enc ss := flat .none ss
  dec k := match parse k with
    | some (.none, ss) => some ss
    | _ => none
  radd ss := by simp [parse_flat]
  licA ss := (ss.all fun s => !Ternary.pauseOnly s) = true
  licB k := Ternary.continueB k = true
  naql ss h := by show Ternary.continueB (flat .none ss) = true; rw [continueB_flat]; exact h

/-- **تامّ**: سلسلةُ المقاطع مرخَّصةٌ وصلًا إذا وفقط إذا رُخّص تسطيحُها ثلاثيًّا. -/
theorem maqta_tamm : maqta.Tamm := fun ss h => by
  have h' : Ternary.continueB (flat .none ss) = true := h
  rw [continueB_flat] at h'
  exact h'

/-! ## ٤. الاشتقاق: جذرٌ ← خاناتُ الماضي، والصفةُ بقيّة -/

theorem sifa_get (r : Root 3) : ∀ i : Fin 3, (sifa r).get i = cls (r i)
  | ⟨0, _⟩ => rfl
  | ⟨1, _⟩ => rfl
  | ⟨2, _⟩ => rfl

/-- قالبُ الأصل يقيَّم بحامله نفسِه، أكان حرفًا ثابتًا بصنفه أم خانةً. -/
theorem eval_rad (r : Root 3) (i : Fin 3) (h : Haraka) : eval r (rad (sifa r) i h) = ⟨r i, h⟩ := by
  unfold rad
  rw [sifa_get]
  have hc := cls_carrier (r i)
  cases hk : (cls (r i)).carrier? with
  | none => rfl
  | some k =>
    simp only [hk, Option.all_some, beq_iff_eq] at hc
    simp [eval, hc]

/-- القالبُ يحمل في الموضع i قالبَ الأصل i، أيًّا كانت حركتُه. -/
def radAt (s : Sifa) (i : Fin 3) (c : CSym 3) : Bool := Haraka.all.any fun x => c == rad s i x

theorem mem_allCls : ∀ c : Cls, c ∈ allCls := by
  intro c; cases c <;> decide

theorem mem_hall : ∀ h : Haraka, h ∈ Haraka.all := by
  intro h; cases h <;> decide

/-- **فحصٌ على الصفات الـ250 والحركات**: كلُّ موضعٍ غيرُ معتلٍّ في الماضي يحمل قالبَ أصله. -/
theorem madi_rad_check :
    allCls.all (fun c0 => allCls.all fun c1 => allCls.all fun c2 => [true, false].all fun e =>
      Haraka.all.all fun a => Haraka.all.all fun h => [(0 : Fin 3), 1, 2].all fun i =>
        let s : Sifa := ⟨c0, c1, c2, e⟩
        (s.get i).weak || ((madi s a h)[i.1]?).any (radAt s i)) = true := by
  decide +kernel

theorem madi_cell (r : Root 3) (a h : Haraka) (i : Fin 3) (hw : (cls (r i)).weak = false) :
    ((fillC (madi (sifa r) a h) r)[i.1]?).map Cell.carrier = some (r i) := by
  have hc := madi_rad_check
  simp only [List.all_eq_true] at hc
  have hi : i ∈ [(0 : Fin 3), 1, 2] := by
    match i with
    | ⟨0, _⟩ => simp
    | ⟨1, _⟩ => simp
    | ⟨2, _⟩ => simp
  have := hc (sifa r).c0 (mem_allCls _) (sifa r).c1 (mem_allCls _) (sifa r).c2 (mem_allCls _)
    (sifa r).e12 (by cases (sifa r).e12 <;> simp) a (mem_hall a) h (mem_hall h) i hi
  have hs : (⟨(sifa r).c0, (sifa r).c1, (sifa r).c2, (sifa r).e12⟩ : Sifa) = sifa r := rfl
  rw [hs, sifa_get, hw] at this
  simp only [Bool.false_or] at this
  cases hm : (madi (sifa r) a h)[i.1]? with
  | none => rw [hm] at this; simp at this
  | some c =>
    rw [hm] at this
    simp only [Option.any_some, radAt, List.any_eq_true, beq_iff_eq] at this
    obtain ⟨x, _, rfl⟩ := this
    simp [fillC, List.getElem?_map, hm, eval_rad]

/-- الاسترجاع: الحرفُ الثابتُ بصنفه (واو، ياء، همزة، لام) من الصفة، والصحيحُ من خانته. -/
def recoverRoot (w : List Cell) (s : Sifa) : Root 3 := fun i =>
  match (s.get i).carrier? with
  | some k => k
  | none => ((w[i.1]?).map Cell.carrier).getD hamza

/-- **لا ضياع في الاشتقاق — لكلّ جذرٍ ثلاثيّ**، صحيحًا كان أو معتلًّا أو مهموزًا أو مضعَّفًا: من خانات الماضي والصفة يُستردّ
الجذرُ بعينه. -/
theorem recover_madi (r : Root 3) (a h : Haraka) :
    recoverRoot (fillC (madi (sifa r) a h) r) (sifa r) = r := by
  funext i
  unfold recoverRoot
  rw [sifa_get]
  have hc := cls_carrier (r i)
  cases hk : (cls (r i)).carrier? with
  | some k =>
    simp only [hk, Option.all_some, beq_iff_eq] at hc
    exact hc
  | none =>
    have hw : (cls (r i)).weak = false := by
      revert hk; generalize cls (r i) = c; intro hk; cases c <;> simp_all [Cls.carrier?, Cls.weak]
    simp only
    rw [madi_cell r a h i hw]
    rfl

def ishtiqaq (a : Haraka) (ha : a ∈ harakat3) : Murakhkhas (Root 3) (List Cell × Sifa) where
  enc r := (fillC (madi (sifa r) a .fatha) r, sifa r)
  dec p := some (recoverRoot p.1 p.2)
  radd r := by simp [recover_madi]
  licA r := NoAlif r
  licB p := strictB p.1 = true ∧ strictPauseB (Pause.pause p.1) = true
  naql r h := ⟨(madi_exhausted r h a ha).1, (madi_exhausted r h a ha).2.1⟩

/-- **الصفةُ بقيّةٌ لازمة**: بلاها لا جسر — قول وقيل جذران مختلفان بخاناتٍ واحدة. -/
theorem ishtiqaq_needs_sifa :
    ¬ ∃ J : Murakhkhas (Root 3) (List Cell), ∀ r, J.enc r = fillC (madi (sifa r) .fatha .fatha) r := by
  rintro ⟨J, hJ⟩
  apply Dal.qwl_ne_qyl
  apply enc_injective J
  rw [hJ, hJ]
  exact Dal.qala_same_cells

/-! ## ٥. التركيب: كلمات ← سطرٌ مسطَّح، والأطوالُ بقيّة -/

def split {α : Type} : List Nat → List α → List (List α)
  | [], _ => []
  | l :: ls, xs => xs.take l :: split ls (xs.drop l)

theorem split_flatten {α : Type} : ∀ ws : List (List α), split (ws.map List.length) ws.flatten = ws
  | [] => rfl
  | w :: ws => by simp [split, split_flatten ws]

theorem lengths_pos {α : Type} (ws : List (List α)) :
    ((ws.map List.length).all fun n => n != 0) = ws.all fun v => !v.isEmpty := by
  induction ws with
  | nil => rfl
  | cons w ws ih => cases w <;> simp [ih]

def tarkib {α : Type} (N : Nizam α) : Murakhkhas (List (List α)) (List α × List Nat) where
  enc ws := (ws.flatten, ws.map List.length)
  dec p := some (split p.2 p.1)
  radd ws := by simp [split_flatten]
  licA ws := licWasl (lift N) ws = true
  licB p := (p.2.all fun n => n != 0) = true ∧ licWasl N p.1 = true
  naql ws h := by
    have := (lift_flatten N ws).1 h
    exact ⟨by rw [lengths_pos]; exact this.1, this.2⟩

/-- **تامّ**: السطرُ مرخَّصٌ في الأعلى إذا وفقط إذا رُخّص تسطيحُه وكانت أطوالُ كلماته موجبة. -/
theorem tarkib_tamm {α : Type} (N : Nizam α) : (tarkib N).Tamm := fun ws h => by
  obtain ⟨h1, h2⟩ := h
  exact (lift_flatten N ws).2 ⟨by rw [← lengths_pos]; exact h1, h2⟩

/-! ## ٦. الشجرة ← السطر: ينقل الترخيص بالضبط ويُفقد التجميع -/

/-- شجرتان مختلفتان بأوراقٍ واحدة وحكمٍ واحد: الترخيصُ لا يرى التجميع، فالتجميعُ بقيّةٌ لا تُستردّ من السطر. -/
theorem tree_needs_shape (w : List Cell) :
    (NizamTree.Tree.leaf w ≠ NizamTree.Tree.node (.cons (.leaf w) .nil)) ∧
    NizamTree.yieldT (NizamTree.Tree.leaf w) = NizamTree.yieldT (NizamTree.Tree.node (.cons (.leaf w) .nil)) ∧
    NizamTree.strictTreeB (NizamTree.Tree.leaf w) =
      NizamTree.strictTreeB (NizamTree.Tree.node (.cons (.leaf w) .nil)) := by
  have hy : NizamTree.yieldT (NizamTree.Tree.leaf w) =
      NizamTree.yieldT (NizamTree.Tree.node (.cons (.leaf w) .nil)) := by
    simp [NizamTree.yieldT, NizamTree.yieldF]
  exact ⟨(fun h => nomatch h), hy, (NizamTree.regroup_invariant _ _ hy).1⟩

/-! ## ٧. الجملة: جذورٌ ← كلماتٌ وصفات، بالتركيب -/

/-- جسرُ الفكّ: قائمةُ أزواجٍ ← زوجُ قائمتين بطولٍ واحد. -/
def unzipJ {X S : Type} (P : X → Prop) : Murakhkhas (List (X × S)) (List X × List S) where
  enc l := l.unzip
  dec p := if p.1.length = p.2.length then some (p.1.zip p.2) else none
  radd l := by
    show (if l.unzip.1.length = l.unzip.2.length then some (l.unzip.1.zip l.unzip.2) else none) = some l
    split
    · rw [List.zip_unzip]
    · rename_i h; exact absurd (by simp) h
  licA l := ∀ x ∈ l, P x.1
  licB p := ∀ x ∈ p.1, P x
  naql l h := by
    intro x hx
    simp only [List.unzip_fst, List.mem_map] at hx
    obtain ⟨y, hy, rfl⟩ := hx
    exact h y hy

/-- **الجملةُ من أفعالٍ ماضية**: الجذورُ تُطوى كلماتٍ مرخَّصةً وصفاتٍ، وتُستردّ بعينها. -/
def jumla (a : Haraka) (ha : a ∈ harakat3) :
    Murakhkhas (List (Root 3)) (List (List Cell) × List Sifa) :=
  comp (list (ishtiqaq a ha))
    (unzipJ fun w => strictB w = true ∧ strictPauseB (Pause.pause w) = true)
    (fun _ h x hx => h x hx)

/-! ## ٨. الجامعة -/

/-- **ترخيصُ جسور الوظائف**: لكلّ وظيفةٍ من الدالّ جسرٌ مرخَّص — لا ضياع ونقلُ ترخيص — والتامُّ منها تامّ؛ والجسورُ
تتركّب؛ والاشتقاقُ لا يكون جسرًا إلّا بالصفة بقيّةً، والتركيبُ النحويّ لا يكون إلّا بالتجميع بقيّةً؛ والدلالةُ وراء الجسر. -/
theorem jusur_wazaif :
    -- ترميز
    tarmiz.Tamm ∧
    -- صوت/مقطع
    maqta.Tamm ∧
    -- اشتقاق: بلا ضياع لكلّ جذر، والترخيصُ ينتقل لكلّ جذرٍ بلا ألف، والصفةُ لازمة
    (∀ (a : Haraka) (ha : a ∈ harakat3) (r : Root 3), (ishtiqaq a ha).dec ((ishtiqaq a ha).enc r) = some r) ∧
    (∀ (a : Haraka) (ha : a ∈ harakat3) (r : Root 3), NoAlif r →
      strictB ((ishtiqaq a ha).enc r).1 = true ∧ strictPauseB (Pause.pause ((ishtiqaq a ha).enc r).1) = true) ∧
    (¬ ∃ J : Murakhkhas (Root 3) (List Cell), ∀ r, J.enc r = fillC (madi (sifa r) .fatha .fatha) r) ∧
    -- تركيب
    (∀ {α : Type} (N : Nizam α), (tarkib N).Tamm) ∧
    -- جملة: الجذورُ تُستردّ بعينها من كلماتها وصفاتها
    (∀ (a : Haraka) (ha : a ∈ harakat3) (rs : List (Root 3)), (jumla a ha).dec ((jumla a ha).enc rs) = some rs) ∧
    -- الشجرة: الحكمُ لا يرى التجميع
    (∀ w : List Cell, NizamTree.Tree.leaf w ≠ NizamTree.Tree.node (.cons (.leaf w) .nil) ∧
      NizamTree.strictTreeB (NizamTree.Tree.leaf w) =
        NizamTree.strictTreeB (NizamTree.Tree.node (.cons (.leaf w) .nil))) ∧
    -- الدلالة: وراء الجسر
    (∀ d, Qufl.locked d .dalala = .muallaq "DALALA_AT_DAL_MADLUL_BRIDGE") :=
  ⟨tarmiz_tamm, maqta_tamm, fun a ha r => (ishtiqaq a ha).radd r,
   fun a ha r h => (ishtiqaq a ha).naql r h, ishtiqaq_needs_sifa, fun N => tarkib_tamm N,
   fun a ha rs => (jumla a ha).radd rs, fun w => ⟨(tree_needs_shape w).1, (tree_needs_shape w).2.2⟩,
   fun _ => rfl⟩

/-! ## ٩. شواهدُ بأعيانها -/

/-- قَالَ وكَتَبَ ووَعَدَ ورَمَى: الجذرُ يُستردّ من خاناته وصفته، بالحساب. -/
theorem shawahid_radd :
    [r3 'ق' 'و' 'ل', r3 'ق' 'ي' 'ل', r3 'ك' 'ت' 'ب', r3 'و' 'ع' 'د', r3 'ر' 'م' 'ي', r3 'ء' 'خ' 'ذ', r3 'م' 'د' 'د'].all
      (fun r => (List.finRange 3).all fun i =>
        recoverRoot (fillC (madi (sifa r) .fatha .fatha) r) (sifa r) i == r i) = true := by
  decide +kernel

end A116.JisrWazaif
